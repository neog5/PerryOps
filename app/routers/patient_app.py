from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.firebase_client import get_firestore_client
from app.schemas_firebase import (
    Patient, PatientSchedule, Reminder, 
    LoginRequest, LoginResponse, DeviceTokenRequest
)
from app.services.auth_service import AuthService
from datetime import datetime, timedelta

router = APIRouter(prefix="/patient", tags=["patient-app"])

@router.post("/login", response_model=LoginResponse)
def patient_login(login_request: LoginRequest):
    """Login for patients"""
    auth_service = AuthService()
    login_response = auth_service.login(login_request)
    
    if not login_response:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if user is a patient
    if login_response.role != "patient":
        raise HTTPException(status_code=403, detail="Access denied. Patients only.")
    
    return login_response

@router.post("/{patient_id}/register-device-token")
def register_device_token(patient_id: str, device_request: DeviceTokenRequest):
    """Register device token for push notifications"""
    try:
        db = get_firestore_client()
        
        # Update patient with device token
        db.collection("patients").document(patient_id).update({
            "device_token": device_request.device_token,
            "device_token_updated_at": datetime.utcnow()
        })
        
        return {"message": "Device token registered successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register device token: {str(e)}")

@router.get("/{patient_id}/schedule")
def get_patient_schedule(patient_id: str):
    """Get patient's preoperative schedule"""
    db = get_firestore_client()
    
    # Get patient's reminders
    reminders = []
    docs = db.collection("reminders").where("patient_id", "==", patient_id).stream()
    
    for doc in docs:
        reminder_data = doc.to_dict()
        reminder_data["id"] = doc.id
        
        # Convert Firestore datetime objects to strings for JSON serialization
        if reminder_data.get("reminder_datetime"):
            if hasattr(reminder_data["reminder_datetime"], 'timestamp'):
                reminder_data["reminder_datetime"] = datetime.fromtimestamp(reminder_data["reminder_datetime"].timestamp()).isoformat()
            else:
                reminder_data["reminder_datetime"] = reminder_data["reminder_datetime"].isoformat()
        
        if reminder_data.get("created_at"):
            if hasattr(reminder_data["created_at"], 'timestamp'):
                reminder_data["created_at"] = datetime.fromtimestamp(reminder_data["created_at"].timestamp()).isoformat()
            else:
                reminder_data["created_at"] = reminder_data["created_at"].isoformat()
        
        if reminder_data.get("completed_at"):
            if hasattr(reminder_data["completed_at"], 'timestamp'):
                reminder_data["completed_at"] = datetime.fromtimestamp(reminder_data["completed_at"].timestamp()).isoformat()
            else:
                reminder_data["completed_at"] = reminder_data["completed_at"].isoformat()
        
        reminders.append(reminder_data)
    
    # Calculate completion status
    total_reminders = len(reminders)
    completed_reminders = len([r for r in reminders if r.get("status") == "completed"])
    is_optimized = total_reminders > 0 and completed_reminders == total_reminders
    
    # Get surgery date from surgeries collection
    surgery_date = None
    try:
        # Get all surgeries for this patient and find the latest one
        surgery_docs = db.collection("surgeries").where("patient_id", "==", patient_id).stream()
        latest_surgery = None
        latest_date = None
        
        for doc in surgery_docs:
            surgery_data = doc.to_dict()
            current_date = surgery_data.get("surgery_date")
            
            # Convert Firestore timestamp to datetime
            if hasattr(current_date, 'timestamp'):
                current_datetime = datetime.utcfromtimestamp(current_date.timestamp())
            else:
                current_datetime = current_date
            
            # Keep track of the latest surgery
            if latest_date is None or current_datetime > latest_date:
                latest_date = current_datetime
                latest_surgery = current_date
        
        surgery_date = latest_surgery
        if hasattr(surgery_date, 'timestamp'):
            surgery_date = datetime.utcfromtimestamp(surgery_date.timestamp())
            
    except Exception as e:
        print(f"Error getting surgery date: {e}")
        surgery_date = None
    
    return {
        "patient_id": patient_id,
        "surgery_date": surgery_date,
        "reminders": reminders,  # Show all reminders
        "total_reminders": total_reminders,
        "completed_reminders": completed_reminders,
        "is_optimized": is_optimized
    }

@router.post("/{patient_id}/complete-reminder/{reminder_id}")
def complete_reminder(patient_id: str, reminder_id: str):
    """Mark a reminder as completed by the patient"""
    db = get_firestore_client()
    
    # Update reminder status
    reminder_doc = db.collection("reminders").document(reminder_id).get()
    if not reminder_doc.exists:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    reminder_data = reminder_doc.to_dict()
    if reminder_data["patient_id"] != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.collection("reminders").document(reminder_id).update({
        "status": "completed",
        "completed_at": datetime.now()
    })
    
    return {"message": "Reminder marked as completed"}


@router.get("/{patient_id}/status")
def get_patient_status(patient_id: str):
    """Get patient's optimization status"""
    db = get_firestore_client()
    
    # Get patient's reminders
    reminders = []
    docs = db.collection("reminders").where("patient_id", "==", patient_id).stream()
    
    for doc in docs:
        reminder_data = doc.to_dict()
        reminders.append(reminder_data)
    
    # Calculate status
    total_reminders = len(reminders)
    completed_reminders = len([r for r in reminders if r.get("status") == "completed"])
    missed_reminders = len([r for r in reminders if r.get("status") == "missed"])
    
    completion_rate = (completed_reminders / total_reminders * 100) if total_reminders > 0 else 0
    is_optimized = total_reminders > 0 and completed_reminders == total_reminders
    needs_reschedule = missed_reminders > 0
    
    return {
        "patient_id": patient_id,
        "total_reminders": total_reminders,
        "completed_reminders": completed_reminders,
        "missed_reminders": missed_reminders,
        "completion_rate": completion_rate,
        "is_optimized": is_optimized,
        "needs_reschedule": needs_reschedule,
        "status": "optimized" if is_optimized else "not_optimized" if needs_reschedule else "in_progress"
    }
@router.post("/{patient_id}/update-device-token")
def update_device_token(patient_id: str, device_token: str):
    """Update patient's device token for push notifications"""
    try:
        db = get_firestore_client()
        
        # Check if patient exists
        patient_doc = db.collection("patients").document(patient_id).get()
        if not patient_doc.exists:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Update device token
        db.collection("patients").document(patient_id).update({
            "device_token": device_token,
            "token_updated_at": datetime.utcnow()
        })
        
        return {"message": "Device token updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update device token: {str(e)}")
