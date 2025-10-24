from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.firebase_client import get_firestore_client, send_push_notification
from app.schemas_firebase import Reminder, ReminderCreate, NotificationRequest
from datetime import datetime

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.get("/patient/{patient_id}", response_model=List[Reminder])
def get_patient_reminders(patient_id: str):
    """Get all reminders for a patient"""
    db = get_firestore_client()
    
    reminders = []
    docs = db.collection("reminders").where("patient_id", "==", patient_id).order_by("time").stream()
    
    for doc in docs:
        reminder_data = doc.to_dict()
        reminder_data["id"] = doc.id
        reminders.append(reminder_data)
    
    return reminders

@router.post("/{reminder_id}/complete")
def mark_reminder_complete(reminder_id: str):
    """Mark a reminder as completed by the patient"""
    db = get_firestore_client()
    
    # Update reminder status
    reminder_doc = db.collection("reminders").document(reminder_id).get()
    
    if not reminder_doc.exists:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    db.collection("reminders").document(reminder_id).update({
        "status": "completed",
        "sent": True,
        "completed_at": datetime.now()
    })
    
    return {"message": "Reminder marked as completed"}

@router.get("/patient/{patient_id}/status")
def get_reminder_status(patient_id: str):
    """Get patient's reminder completion status"""
    db = get_firestore_client()
    
    reminders = []
    docs = db.collection("reminders").where("patient_id", "==", patient_id).stream()
    
    for doc in docs:
        reminder_data = doc.to_dict()
        reminders.append(reminder_data)
    
    total_reminders = len(reminders)
    completed_reminders = len([r for r in reminders if r.get("status") == "completed"])
    pending_reminders = len([r for r in reminders if r.get("status") == "pending"])
    missed_reminders = len([r for r in reminders if r.get("status") == "missed"])
    
    return {
        "patient_id": patient_id,
        "total_reminders": total_reminders,
        "completed_reminders": completed_reminders,
        "pending_reminders": pending_reminders,
        "missed_reminders": missed_reminders,
        "completion_rate": (completed_reminders / total_reminders * 100) if total_reminders > 0 else 0,
        "is_optimized": total_reminders > 0 and completed_reminders == total_reminders
    }

@router.post("/send-notification")
def send_notification(notification: NotificationRequest):
    """Send push notification to patient"""
    db = get_firestore_client()
    
    # Get patient's device token
    patient_doc = db.collection("patients").document(notification.patient_id).get()
    if not patient_doc.exists:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    patient_data = patient_doc.to_dict()
    device_token = patient_data.get("device_token")
    
    if not device_token:
        raise HTTPException(status_code=400, detail="Patient device token not found")
    
    # Send push notification
    result = send_push_notification(
        device_token=device_token,
        title=notification.title,
        body=notification.body,
        data=notification.data
    )
    
    return result
