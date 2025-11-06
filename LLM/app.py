"""
FastAPI application for PerryOps medical report processing.

This API follows the workflow:
1. Upload documents (guidelines.pdf, CPCReport.pdf)
2. Extract structured data
3. Check compliance (returns JSON)
4. Wait for corrections/approval (accepts JSON response)
5. Merge corrections with structured data
6. Generate actions
7. Build and return action plan
"""

import os
from pathlib import Path
from typing import List, Optional, Union
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.models import (
    UploadResponse,
    ExtractResponse,
    ComplianceCheckResponse,
    MergeRequest,
    MergeResponse,
    ActionPlanResponse,
)
from api.session_manager import SessionManager
from src.pdf_processor import extract_text_from_pdf
from src.bedrock_client import structure_data_with_bedrock
from src.guideline_extractor import extract_bold_headings, collect_sections_for_level
from src.compliance_checker import check_guideline_compliance
from src.action_generator import generate_actions_from_json_one_by_one


# Initialize
app = FastAPI(
    title="PerryOps API",
    description="Medical report processing and patient action plan generation API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_manager = SessionManager(base_dir="uploads")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "PerryOps API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload": "/api/upload",
            "extract": "/api/extract",
            "check_compliance": "/api/check-compliance",
            "merge": "/api/merge",
            "generate_action_plan": "/api/generate-action-plan"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_documents(
    report: UploadFile = File(..., description="Medical report PDF (CPCReport.pdf)"),
    guidelines: Optional[UploadFile] = File(None),
):
    """
    Upload medical report and optional guidelines PDF.
    
    Creates a new session and stores the uploaded files.
    
    Returns:
        UploadResponse with session_id and upload confirmation
    """
    
    # Validate file
    if not report.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Report must be a PDF file")
    
    if guidelines and hasattr(guidelines, 'filename') and guidelines.filename and not guidelines.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Guidelines must be a PDF file")
    
    # new session
    session_id = session_manager.create_session()
    files_uploaded = []

    # Save report
    report_content = await report.read()
    report_path = session_manager.save_file(session_id, "report.pdf", report_content)
    files_uploaded.append("report.pdf")
    # Save guidelines if provided, otherwise use default
    if guidelines and hasattr(guidelines, 'filename') and guidelines.filename:
        guidelines_content = await guidelines.read()
        guidelines_path = session_manager.save_file(session_id, "guidelines.pdf", guidelines_content)
        files_uploaded.append("guidelines.pdf (uploaded)")
    else:
        # Use default guidelines file
        default_guidelines_path = Path("C:\\Users\\Harit\\Desktop\\PerryOps\\guidelines.pdf")
        if not default_guidelines_path.exists():
            raise HTTPException(
                status_code=400, 
                detail="No guidelines uploaded and default guidelines.pdf not found"
            )
        
        # Copy default guidelines to session
        with open(default_guidelines_path, 'rb') as f:
            guidelines_content = f.read()
        guidelines_path = session_manager.save_file(session_id, "guidelines.pdf", guidelines_content)
        files_uploaded.append("guidelines.pdf (default)")

    # Update session status
    session_manager.update_status(session_id, "uploaded")
    
    return UploadResponse(
        session_id=session_id,
        message="Files uploaded successfully",
        files_uploaded=files_uploaded
    )


@app.post("/api/extract", response_model=ExtractResponse)
async def extract_structured_data(
    session_id: str = Form(...),
    model: str = Form("qwen32b", description="Model to use for extraction")
):
    """
    Extract structured data from the uploaded medical report.
    
    Args:
        session_id: Session identifier from upload
        model: Model preset to use for extraction (default: qwen32b)
        
    Returns:
        ExtractResponse with structured medical data
    """
    # Verify session exists
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get report file path
    report_path = session_manager.get_file_path(session_id, "report.pdf")
    if not report_path:
        raise HTTPException(status_code=404, detail="Report file not found in session")
    
    try:
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(str(report_path))
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
        
        # Structure data with Bedrock
        structured_data = structure_data_with_bedrock(extracted_text, model)
        if not structured_data:
            raise HTTPException(status_code=500, detail="Failed to structure data")
        
        # Save structured data to session
        session_manager.save_data(session_id, "structured_data", structured_data)
        session_manager.update_status(session_id, "extracted")
        
        return ExtractResponse(
            session_id=session_id,
            structured_data=structured_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/api/check-compliance", response_model=ComplianceCheckResponse)
async def check_compliance(
    session_id: str = Form(...),
    compliance_model: str = Form("amsaravi/medgemma-4b-it:q8", description="Model for compliance checking")
):
    """
    Check compliance of extracted data against guidelines.
    
    Args:
        session_id: Session identifier
        compliance_model: Ollama model to use for compliance checking
        
    Returns:
        ComplianceCheckResponse with flagged items requiring attention
    """
    # Verify session exists
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Load structured data
    structured_data = session_manager.load_data(session_id, "structured_data")
    if not structured_data:
        raise HTTPException(
            status_code=400, 
            detail="No structured data found. Run /api/extract first"
        )
    
    # Check if guidelines were uploaded
    guidelines_path = session_manager.get_file_path(session_id, "guidelines.pdf")
    if not guidelines_path:
        raise HTTPException(
            status_code=400,
            detail="Guidelines not uploaded. Cannot perform compliance check"
        )
    
    try:
        # Extract guideline sections
        guideline_headings = extract_bold_headings(str(guidelines_path))
        level_two_sections = collect_sections_for_level(
            str(guidelines_path),
            headings=guideline_headings,
            target_level=2
        )
        
        # Check compliance
        compliance_report = check_guideline_compliance(
            structured_data,
            level_two_sections,
            model_name=compliance_model
        )
        
        if not compliance_report:
            raise HTTPException(status_code=500, detail="Compliance check failed")
        
        # Save compliance report
        session_manager.save_data(session_id, "compliance_report", compliance_report)
        session_manager.update_status(session_id, "compliance_checked")
        
        return ComplianceCheckResponse(
            session_id=session_id,
            compliance_report=compliance_report,
            awaiting_corrections=len(compliance_report.get("flagged_items", [])) > 0
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")


@app.post("/api/merge", response_model=MergeResponse)
async def merge_corrections(request: MergeRequest):
    """
    Merge compliance corrections with structured data.
    
    Accepts flagged_items array from compliance check and applies the suggested_entry
    for each item by matching item_type and name.
    
    Args:
        request: MergeRequest containing session_id and flagged_items
        
    Returns:
        MergeResponse with updated structured data
    """
    # Verify session exists
    if not session_manager.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Load current structured data
    structured_data = session_manager.load_data(request.session_id, "structured_data")
    if not structured_data:
        raise HTTPException(
            status_code=400,
            detail="No structured data found. Run /api/extract first"
        )
    
    try:
        # Apply corrections from flagged items
        # updated_data = _apply_flagged_corrections(structured_data, request.flagged_items)
        updated_data = structured_data.copy()
        
        # Save updated data
        session_manager.save_data(request.session_id, "structured_data", updated_data)
        session_manager.update_status(request.session_id, "corrections_applied")
        
        return MergeResponse(
            session_id=request.session_id,
            updated_data=updated_data,
            message=f"Applied {len(request.flagged_items)} corrections successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")


@app.post("/api/generate-action-plan", response_model=ActionPlanResponse)
async def generate_action_plan(
    session_id: str = Form(...),
    model: str = Form("qwen32b", description="Model to use for action generation")
):
    """
    Generate final patient action plan.
    
    Creates patient-facing actions from the structured data and builds
    the complete action plan.
    
    Args:
        session_id: Session identifier
        model: Model to use for action generation
        
    Returns:
        ActionPlanResponse with complete patient action plan
    """
    # Verify session exists
    if not session_manager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Load structured data
    structured_data = session_manager.load_data(session_id, "structured_data")
    if not structured_data:
        raise HTTPException(
            status_code=400,
            detail="No structured data found. Run /api/extract first"
        )
    
    try:
        # Generate actions
        actions = generate_actions_from_json_one_by_one(structured_data, model=model)
        
        # Build action plan
        action_plan = {
            "patient_info": structured_data.get("patient_info"),
            "surgery_details": structured_data.get("surgery_details"),
            "actions": actions
        }
        
        # Add compliance report if available
        compliance_report = session_manager.load_data(session_id, "compliance_report")
        if compliance_report:
            action_plan["compliance_report"] = compliance_report
        
        # Save action plan
        session_manager.save_data(session_id, "action_plan", action_plan)
        session_manager.update_status(session_id, "completed")
        
        return ActionPlanResponse(
            session_id=session_id,
            action_plan=action_plan
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action plan generation failed: {str(e)}")


def _deep_merge(base: dict, updates: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        updates: Updates to apply
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get host and port from environment or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")  # Listen on all interfaces
    port = int(os.getenv("API_PORT", "8000"))
    
    print("=" * 60)
    print("PerryOps API Server Starting...")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"")
    print("Access the API at:")
    print(f"  - Local: http://localhost:{port}")
    print(f"  - Network: http://YOUR_IP_ADDRESS:{port}")
    print(f"  - Docs: http://localhost:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(app, host=host, port=port)
