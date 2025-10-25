from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.firebase_client import get_firestore_client, send_push_notification
from app.schemas_firebase import (
    Patient, PatientSchedule, Reminder, 
    NotificationRequest
)
from app.services.task_priority_service import TaskPriorityService
from datetime import datetime, timedelta

router = APIRouter(prefix="/patient", tags=["patient-app"])

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

@router.get("/{patient_id}/priority-tasks")
def get_priority_tasks(patient_id: str):
    """Get tasks ordered by priority for the patient"""
    priority_service = TaskPriorityService()
    tasks = priority_service.get_priority_tasks(patient_id)
    
    return {
        "patient_id": patient_id,
        "tasks": tasks,
        "total_tasks": len(tasks),
        "urgent_tasks": len([t for t in tasks if t.get("hours_until_due", 0) <= 24])
    }

@router.get("/{patient_id}/urgent-tasks")
def get_urgent_tasks(patient_id: str, hours_ahead: int = 24):
    """Get urgent tasks (due within specified hours)"""
    priority_service = TaskPriorityService()
    urgent_tasks = priority_service.get_urgent_tasks(patient_id, hours_ahead)
    
    return {
        "patient_id": patient_id,
        "urgent_tasks": urgent_tasks,
        "count": len(urgent_tasks),
        "hours_ahead": hours_ahead
    }

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
        
        # Check if reminder is upcoming
        scheduled_datetime = reminder_data["scheduled_date"]
        if isinstance(scheduled_datetime, str):
            scheduled_datetime = datetime.fromisoformat(scheduled_datetime)
        
        if now <= scheduled_datetime <= future_time and reminder_data.get("status") == "pending":
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