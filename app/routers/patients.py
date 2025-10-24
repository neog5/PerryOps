from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.firebase_client import get_firestore_client
from app.schemas_firebase import Patient, PatientCreate, PatientSchedule, Reminder
from datetime import datetime

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=Patient)
def create_patient(patient: PatientCreate):
    """Create a new patient"""
    db = get_firestore_client()
    
    # Create patient record
    patient_data = patient.dict()
    patient_data["created_at"] = datetime.now()
    
    doc_ref = db.collection("patients").add(patient_data)
    patient_id = doc_ref[1].id
    
    # Get the created patient
    patient_doc = db.collection("patients").document(patient_id).get()
    if not patient_doc.exists:
        raise HTTPException(status_code=400, detail="Failed to create patient")
    
    patient_data = patient_doc.to_dict()
    patient_data["id"] = patient_id
    return patient_data

@router.get("/", response_model=List[Patient])
def get_patients():
    """Get all patients"""
    db = get_firestore_client()
    
    patients = []
    docs = db.collection("patients").stream()
    
    for doc in docs:
        patient_data = doc.to_dict()
        patient_data["id"] = doc.id
        patients.append(patient_data)
    
    return patients

@router.get("/{patient_id}", response_model=Patient)
def get_patient(patient_id: str):
    """Get a specific patient"""
    db = get_firestore_client()
    
    patient_doc = db.collection("patients").document(patient_id).get()
    
    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient_data = patient_doc.to_dict()
    patient_data["id"] = patient_id
    return patient_data

@router.get("/{patient_id}/schedule", response_model=PatientSchedule)
def get_patient_schedule(patient_id: str):
    """Get patient's medication schedule"""
    db = get_firestore_client()
    
    # Get patient's reminders
    reminders = []
    reminders_docs = db.collection("reminders").where("patient_id", "==", patient_id).stream()
    
    for doc in reminders_docs:
        reminder_data = doc.to_dict()
        reminder_data["id"] = doc.id
        reminders.append(reminder_data)
    
    # Get surgery date
    surgeries = []
    surgeries_docs = db.collection("surgeries").where("patient_id", "==", patient_id).order_by("surgery_date", direction="DESCENDING").limit(1).stream()
    
    for doc in surgeries_docs:
        surgery_data = doc.to_dict()
        surgeries.append(surgery_data)
    
    surgery_date = surgeries[0]["surgery_date"] if surgeries else None
    
    # Calculate if patient is optimized
    total_reminders = len(reminders)
    completed_reminders = len([r for r in reminders if r.get("status") == "completed"])
    is_optimized = total_reminders > 0 and completed_reminders == total_reminders
    
    return PatientSchedule(
        patient_id=patient_id,
        reminders=reminders,
        surgery_date=surgery_date,
        is_optimized=is_optimized
    )
