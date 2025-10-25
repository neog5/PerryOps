from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.firebase_client import get_firestore_client
from app.schemas_firebase import Patient, PatientCreate
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

