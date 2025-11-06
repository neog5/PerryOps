"""
Main pipeline for processing medical reports and generating patient action plans.
"""

import json
import argparse
from pathlib import Path
from src.pdf_processor import extract_text_from_pdf
from src.bedrock_client import structure_data_with_bedrock
from src.action_generator import generate_actions_from_json_one_by_one
from src.guideline_extractor import extract_bold_headings, collect_sections_for_level
from src.compliance_checker import check_guideline_compliance


def extract_structured_data_from_pdf(pdf_path, model_or_profile="qwen32b"):
    """
    Extract and structure data from a medical report PDF.
    
    Args:
        pdf_path: Path to the PDF file
        model_or_profile: Model preset key, ID, or ARN to use
        
    Returns:
        dict: Structured data extracted from the PDF, or None if extraction fails
    """
    print(f"Processing PDF: {pdf_path}")
    
    extracted_text = extract_text_from_pdf(pdf_path)
    if extracted_text:
        print("Text extracted successfully. Structuring data with AWS Bedrock (Converse)...")
        structured_json = structure_data_with_bedrock(extracted_text, model_or_profile)
        
        if structured_json:
            print("Data structured successfully.")
            return structured_json
        else:
            print("Failed to structure data.")
            return None
    else:
        print("Failed to extract text from PDF.")
        return None


def generate_patient_action_plan(pdf_path, guideline_pdf=None, model="qwen32b", compliance_model=None):
    """
    Complete pipeline to generate a patient action plan from a medical report.
    
    Args:
        pdf_path: Path to the medical report PDF
        guideline_pdf: Optional path to clinical guidelines PDF for compliance checking
        model: Model to use for data extraction and action generation
        compliance_model: Optional model to use for compliance checking (defaults to local Ollama)
        
    Returns:
        dict: Complete patient action plan with structured data, actions, and compliance report
    """
    # Step 1: Extract structured data from PDF
    structured_data = extract_structured_data_from_pdf(pdf_path, model)
    
    if not structured_data:
        print("Failed to extract structured data from PDF.")
        return None
    
    print(f"\nStructured Data extracted successfully.")
    
    # Step 2: Generate patient-facing actions
    print("\nGenerating patient-facing actions...")
    actions = generate_actions_from_json_one_by_one(structured_data, model=model)
    print(f"Generated {len(actions)} actions.")
    
    # Step 3: Build patient action plan
    patient_action_plan = {
        "patient_info": structured_data.get("patient_info"),
        "surgery_details": structured_data.get("surgery_details"),
        "actions": actions
    }
    
    # Step 4: Optional compliance checking
    compliance_report = None
    if guideline_pdf:
        print(f"\nExtracting guidelines from: {guideline_pdf}")
        guideline_headings = extract_bold_headings(guideline_pdf)
        level_two_sections = collect_sections_for_level(
            guideline_pdf, 
            headings=guideline_headings, 
            target_level=2
        )
        
        print(f"Extracted {len(level_two_sections)} guideline sections.")
        print("\nChecking compliance...")
        
        compliance_model = compliance_model or "amsaravi/medgemma-4b-it:q8"
        compliance_report = check_guideline_compliance(
            structured_data, 
            level_two_sections,
            model_name=compliance_model
        )
        
        print(f"\n{compliance_report.get('compliance_summary')}")
        
        patient_action_plan["compliance_report"] = compliance_report
    
    return patient_action_plan


def main():
    """Command-line interface for the PerryOps pipeline."""
    parser = argparse.ArgumentParser(
        description="Process medical reports and generate patient action plans."
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the medical report PDF file"
    )
    parser.add_argument(
        "-g", "--guidelines",
        help="Path to clinical guidelines PDF for compliance checking",
        default=None
    )
    parser.add_argument(
        "-m", "--model",
        help="Model preset key or ID for data extraction (default: qwen32b)",
        default="qwen32b"
    )
    parser.add_argument(
        "-c", "--compliance-model",
        help="Model for compliance checking (default: amsaravi/medgemma-4b-it:q8)",
        default=None
    )
    parser.add_argument(
        "-o", "--output",
        help="Output JSON file path (default: stdout)",
        default=None
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output"
    )
    
    args = parser.parse_args()
    
    # Validate PDF path
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1
    
    # Validate guidelines path if provided
    guideline_pdf = None
    if args.guidelines:
        guideline_pdf = Path(args.guidelines)
        if not guideline_pdf.exists():
            print(f"Error: Guidelines PDF not found: {guideline_pdf}")
            return 1
    
    # Run pipeline
    result = generate_patient_action_plan(
        str(pdf_path),
        guideline_pdf=str(guideline_pdf) if guideline_pdf else None,
        model=args.model,
        compliance_model=args.compliance_model
    )
    
    if not result:
        print("\nFailed to generate patient action plan.")
        return 1
    
    # Output results
    indent = 2 if args.pretty else None
    json_output = json.dumps(result, indent=indent)
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json_output, encoding='utf-8')
        print(f"\nResults written to: {output_path}")
    else:
        print("\n" + "="*60)
        print("PATIENT ACTION PLAN")
        print("="*60)
        print(json_output)
    
    return 0


if __name__ == "__main__":
    exit(main())
