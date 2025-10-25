from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.firebase_client import get_firestore_client, send_push_notification
from app.schemas_firebase import (
    Patient, PatientSchedule, Reminder, 
    NotificationRequest, LoginRequest, LoginResponse
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

@router.get("/{patient_id}/schedule", response_model=PatientSchedule)
def get_patient_schedule(patient_id: str):
    """Get patient's preoperative schedule"""
    db = get_firestore_client()
    
    # Get patient's reminders
    reminders = []
    docs = db.collection("reminders").where("patient_id", "==", patient_id).stream()
    
    for doc in docs:
        reminder_data = doc.to_dict()
        reminder_data["id"] = doc.id
        reminders.append(reminder_data)
    
    # Calculate completion status
    total_reminders = len(reminders)
    completed_reminders = len([r for r in reminders if r.get("status") == "completed"])
    is_optimized = total_reminders > 0 and completed_reminders == total_reminders
    
    # Get surgery date from the earliest reminder
    surgery_date = None
    if reminders:
        earliest_reminder = min(reminders, key=lambda x: x.get("scheduled_date", datetime.max))
        surgery_date = earliest_reminder.get("scheduled_date")
    
    return PatientSchedule(
        patient_id=patient_id,
        surgery_date=surgery_date,
        reminders=reminders,
        total_reminders=total_reminders,
        completed_reminders=completed_reminders,
        is_optimized=is_optimized
    )

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

@router.get("/{patient_id}/upcoming-reminders")
def get_upcoming_reminders(patient_id: str, hours_ahead: int = 24):
    """Get upcoming reminders for the next N hours"""
    db = get_firestore_client()
    
    now = datetime.now()
    future_time = now + timedelta(hours=hours_ahead)
    
    # Get upcoming reminders
    upcoming_reminders = []
    docs = db.collection("reminders").where("patient_id", "==", patient_id).stream()
    
    for doc in docs:
        reminder_data = doc.to_dict()
        reminder_data["id"] = doc.id
        
        # Check if reminder is upcoming using reminder_datetime
        reminder_datetime = reminder_data.get("reminder_datetime")
        if isinstance(reminder_datetime, str):
            reminder_datetime = datetime.fromisoformat(reminder_datetime)
        
        # Only include pending reminders that are within the time window
        if (reminder_datetime and 
            now <= reminder_datetime <= future_time and 
            reminder_data.get("status") == "pending"):
            upcoming_reminders.append(reminder_data)
    
    return {
        "patient_id": patient_id,
        "upcoming_reminders": upcoming_reminders,
        "count": len(upcoming_reminders)
    }

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

@router.post("/{patient_id}/send-notification")
def send_notification_to_patient(patient_id: str, notification: NotificationRequest):
    """Send push notification to patient"""
    db = get_firestore_client()
    
    # Get patient's device token
    patient_doc = db.collection("patients").document(patient_id).get()
    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient_data = patient_doc.to_dict()
    device_token = patient_data.get("device_token")
    
    if not device_token:
        return {"success": False, "error": "Patient device token not found"}
    
    # Send push notification
    result = send_push_notification(
        device_token=device_token,
        title=notification.title,
        body=notification.body,
        data=notification.data
    )
    
    return result

@router.post("/{patient_id}/update-device-token")
def update_device_token(patient_id: str, device_token: str):
    """Update patient's device token for push notifications"""
    db = get_firestore_client()
    
    patient_doc = db.collection("patients").document(patient_id).get()
    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db.collection("patients").document(patient_id).update({
        "device_token": device_token,
        "token_updated_at": datetime.now()
    })
    
    return {"message": "Device token updated successfully"}