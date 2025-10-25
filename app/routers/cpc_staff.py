from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Dict, Any
from app.firebase_client import get_firestore_client
from app.schemas_firebase import (
    Patient, PatientCreate, CPCReport, CPCReportCreate, 
    Reminder, ReminderCreate, CPCDashboard
)
from app.services.ai_processor import AIProcessor
from datetime import datetime
import uuid

router = APIRouter(prefix="/cpc", tags=["cpc-staff"])

@router.get("/patients", response_model=List[Patient])
def get_all_patients():
    """Get all patients for CPC staff dropdown"""
    db = get_firestore_client()
    
    patients = []
    docs = db.collection("patients").stream()
    
    for doc in docs:
        patient_data = doc.to_dict()
        patient_data["id"] = doc.id
        patients.append(patient_data)
    
    return patients

@router.post("/patients", response_model=Patient)
def create_patient(patient: PatientCreate):
    """Create a new patient"""
    db = get_firestore_client()
    
    patient_data = patient.dict()
    patient_data["created_at"] = datetime.now()
    
    doc_ref = db.collection("patients").add(patient_data)
    patient_id = doc_ref[1].id
    
    patient_doc = db.collection("patients").document(patient_id).get()
    patient_data = patient_doc.to_dict()
    patient_data["id"] = patient_id
    return patient_data

@router.post("/upload-report", response_model=CPCReport)
async def upload_cpc_report(
    patient_id: str,
    uploaded_by: str,
    file: UploadFile = File(...)
):
    """Upload CPC report for a patient"""
    db = get_firestore_client()
    
    # Save file (in production, use Firebase Storage)
    file_path = f"cpc_reports/{patient_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create CPC report record
    report_data = {
        "patient_id": patient_id,
        "uploaded_by": uploaded_by,
        "original_filename": file.filename,
        "file_path": file_path,
        "uploaded_at": datetime.now(),
        "is_processed": False
    }
    
    doc_ref = db.collection("cpc_reports").add(report_data)
    report_id = doc_ref[1].id
    
    report_doc = db.collection("cpc_reports").document(report_id).get()
    report_data = report_doc.to_dict()
    report_data["id"] = report_id
    return report_data

@router.post("/process-report/{report_id}", response_model=List[Reminder])
def process_cpc_report(report_id: str, surgery_date: datetime):
    """Process CPC report and generate reminders directly"""
    db = get_firestore_client()
    ai_processor = AIProcessor()
    
    # Get the CPC report
    report_doc = db.collection("cpc_reports").document(report_id).get()
    if not report_doc.exists:
        raise HTTPException(status_code=404, detail="CPC report not found")
    
    report_data = report_doc.to_dict()
    
    # Generate AI recommendations
    ai_response = ai_processor.generate_recommendations({
        "patient_id": report_data["patient_id"],
        "surgery_date": surgery_date.isoformat(),
        "cpc_data": "processed_cpc_data"  # In real implementation, parse the uploaded file
    })
    
    # Create reminders directly from AI response
    reminders_created = []
    for item in ai_response["recommendations"]:
        # Calculate scheduled date
        from datetime import timedelta
        scheduled_date = surgery_date
        if item.get("days_before_surgery"):
            scheduled_date = surgery_date - timedelta(days=item["days_before_surgery"])
        elif item.get("hours_before_surgery"):
            scheduled_date = surgery_date - timedelta(hours=item["hours_before_surgery"])
        
        reminder_data = {
            "patient_id": report_data["patient_id"],
            "medicine": item.get("medication_name"),
            "action": item["action"],
            "scheduled_date": scheduled_date,
            "scheduled_time": item.get("specific_time", "08:00"),
            "status": "pending",
            "created_at": datetime.now()
        }
        
        doc_ref = db.collection("reminders").add(reminder_data)
        reminder_id = doc_ref[1].id
        
        reminder_doc = db.collection("reminders").document(reminder_id).get()
        reminder_data = reminder_doc.to_dict()
        reminder_data["id"] = reminder_id
        reminders_created.append(reminder_data)
    
    # Mark report as processed
    db.collection("cpc_reports").document(report_id).update({
        "is_processed": True,
        "processed_at": datetime.now()
    })
    
    return reminders_created

@router.get("/reports", response_model=List[CPCReport])
def get_cpc_reports():
    """Get all CPC reports"""
    db = get_firestore_client()
    
    reports = []
    docs = db.collection("cpc_reports").order_by("uploaded_at", direction="DESCENDING").stream()
    
    for doc in docs:
        report_data = doc.to_dict()
        report_data["id"] = doc.id
        reports.append(report_data)
    
    return reports

@router.get("/dashboard", response_model=CPCDashboard)
def get_cpc_dashboard():
    """Get CPC staff dashboard data"""
    db = get_firestore_client()
    
    # Get counts
    patients_count = len(list(db.collection("patients").stream()))
    pending_reports = len(list(db.collection("cpc_reports").where("is_processed", "==", False).stream()))
    processed_reports = len(list(db.collection("cpc_reports").where("is_processed", "==", True).stream()))
    total_reminders = len(list(db.collection("reminders").stream()))
    
    return CPCDashboard(
        total_patients=patients_count,
        pending_reports=pending_reports,
        processed_reports=processed_reports,
        total_reminders=total_reminders
    )

@router.get("/patients/optimization-status")
def get_all_patients_optimization_status():
    """Get optimization status for all patients"""
    db = get_firestore_client()
    
    patients_status = []
    patients_docs = db.collection("patients").stream()
    
    for patient_doc in patients_docs:
        patient_data = patient_doc.to_dict()
        patient_id = patient_doc.id
        
        # Get patient's schedule items
        schedule_items = []
        items_docs = db.collection("schedule_items").where("patient_id", "==", patient_id).stream()
        
        for item_doc in items_docs:
            item_data = item_doc.to_dict()
            schedule_items.append(item_data)
        
        # Calculate optimization status
        total_items = len(schedule_items)
        completed_items = len([item for item in schedule_items if item.get("patient_completed", False)])
        missed_items = len([item for item in schedule_items if not item.get("patient_completed", False) and item["scheduled_date"] < datetime.now()])
        
        completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
        is_optimized = total_items > 0 and completed_items == total_items
        needs_reschedule = missed_items > 0
        
        patients_status.append({
            "patient_id": patient_id,
            "patient_name": patient_data.get("name", "Unknown"),
            "patient_email": patient_data.get("email", ""),
            "total_schedule_items": total_items,
            "completed_items": completed_items,
            "missed_items": missed_items,
            "completion_rate": round(completion_rate, 1),
            "is_optimized": is_optimized,
            "needs_reschedule": needs_reschedule,
            "status": "optimized" if is_optimized else "not_optimized" if needs_reschedule else "in_progress"
        })
    
    return {
        "patients": patients_status,
        "total_patients": len(patients_status),
        "optimized_patients": len([p for p in patients_status if p["is_optimized"]]),
        "in_progress_patients": len([p for p in patients_status if p["status"] == "in_progress"]),
        "not_optimized_patients": len([p for p in patients_status if p["status"] == "not_optimized"])
    }

@router.get("/patients/{patient_id}/detailed-status")
def get_patient_detailed_status(patient_id: str):
    """Get detailed optimization status for a specific patient"""
    db = get_firestore_client()
    
    # Get patient info
    patient_doc = db.collection("patients").document(patient_id).get()
    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient_data = patient_doc.to_dict()
    
    # Get schedule items
    schedule_items = []
    items_docs = db.collection("schedule_items").where("patient_id", "==", patient_id).stream()
    
    for item_doc in items_docs:
        item_data = item_doc.to_dict()
        item_data["id"] = item_doc.id
        schedule_items.append(item_data)
    
    # Get surgery info
    surgery_docs = db.collection("surgeries").where("patient_id", "==", patient_id).order_by("surgery_date", direction="DESCENDING").limit(1).stream()
    surgery_data = None
    for doc in surgery_docs:
        surgery_data = doc.to_dict()
        break
    
    # Calculate detailed status
    total_items = len(schedule_items)
    completed_items = len([item for item in schedule_items if item.get("patient_completed", False)])
    pending_items = len([item for item in schedule_items if not item.get("patient_completed", False) and item["scheduled_date"] > datetime.now()])
    missed_items = len([item for item in schedule_items if not item.get("patient_completed", False) and item["scheduled_date"] < datetime.now()])
    
    completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
    is_optimized = total_items > 0 and completed_items == total_items
    needs_reschedule = missed_items > 0
    
    return {
        "patient": {
            "id": patient_id,
            "name": patient_data.get("name", "Unknown"),
            "email": patient_data.get("email", ""),
            "phone": patient_data.get("phone", "")
        },
        "surgery": surgery_data,
        "schedule_items": schedule_items,
        "optimization_status": {
            "total_schedule_items": total_items,
            "completed_items": completed_items,
            "pending_items": pending_items,
            "missed_items": missed_items,
            "completion_rate": round(completion_rate, 1),
            "is_optimized": is_optimized,
            "needs_reschedule": needs_reschedule,
            "status": "optimized" if is_optimized else "not_optimized" if needs_reschedule else "in_progress"
        }
    }
