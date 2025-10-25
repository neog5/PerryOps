from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.firebase_client import get_firestore_client, send_push_notification
from app.schemas_workflow import (
    Patient, PatientScheduleView, ScheduleItem, 
    NotificationRequest, NotificationResponse
)
from app.services.task_priority_service import TaskPriorityService
from datetime import datetime, timedelta

router = APIRouter(prefix="/patient", tags=["patient-app"])

@router.get("/{patient_id}/schedule", response_model=PatientScheduleView)
def get_patient_schedule(patient_id: str):
    """Get patient's preoperative schedule"""
    db = get_firestore_client()
    
    # Get patient's surgery info
    surgery_docs = db.collection("surgeries").where("patient_id", "==", patient_id).order_by("surgery_date", direction="DESCENDING").limit(1).stream()
    surgery_data = None
    for doc in surgery_docs:
        surgery_data = doc.to_dict()
        break
    
    if not surgery_data:
        raise HTTPException(status_code=404, detail="No surgery found for patient")
    
    # Get schedule items
    schedule_items = []
    items_docs = db.collection("schedule_items").where("patient_id", "==", patient_id).stream()
    
    for doc in items_docs:
        item_data = doc.to_dict()
        item_data["id"] = doc.id
        schedule_items.append(item_data)
    
    # Calculate completion status
    total_items = len(schedule_items)
    completed_items = len([item for item in schedule_items if item.get("patient_completed", False)])
    pending_items = total_items - completed_items
    is_optimized = total_items > 0 and completed_items == total_items
    
    return PatientScheduleView(
        patient_id=patient_id,
        surgery_date=surgery_data["surgery_date"],
        surgery_time=surgery_data.get("surgery_time", "08:00"),
        schedule_items=schedule_items,
        total_items=total_items,
        completed_items=completed_items,
        pending_items=pending_items,
        is_optimized=is_optimized
    )

@router.post("/{patient_id}/complete-schedule-item/{item_id}")
def complete_schedule_item(patient_id: str, item_id: str):
    """Mark a schedule item as completed by patient"""
    db = get_firestore_client()
    
    # Update schedule item
    item_doc = db.collection("schedule_items").document(item_id).get()
    if not item_doc.exists:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    item_data = item_doc.to_dict()
    if item_data["patient_id"] != patient_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.collection("schedule_items").document(item_id).update({
        "patient_completed": True,
        "completed_at": datetime.now()
    })
    
    return {"message": "Schedule item marked as completed"}

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
    
    # Get upcoming schedule items
    upcoming_items = []
    items_docs = db.collection("schedule_items").where("patient_id", "==", patient_id).stream()
    
    for doc in items_docs:
        item_data = doc.to_dict()
        item_data["id"] = doc.id
        
        # Check if item is upcoming
        scheduled_datetime = item_data["scheduled_date"]
        if isinstance(scheduled_datetime, str):
            scheduled_datetime = datetime.fromisoformat(scheduled_datetime)
        
        if now <= scheduled_datetime <= future_time and not item_data.get("patient_completed", False):
            upcoming_items.append(item_data)
    
    return {
        "patient_id": patient_id,
        "upcoming_items": upcoming_items,
        "count": len(upcoming_items)
    }

@router.post("/{patient_id}/send-notification", response_model=NotificationResponse)
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
        return NotificationResponse(
            success=False,
            error="Patient device token not found"
        )
    
    # Send push notification
    result = send_push_notification(
        device_token=device_token,
        title=notification.title,
        body=notification.body,
        data=notification.data
    )
    
    if result["success"]:
        return NotificationResponse(
            success=True,
            message_id=result["message_id"]
        )
    else:
        return NotificationResponse(
            success=False,
            error=result["error"]
        )

@router.get("/{patient_id}/optimization-status")
def get_optimization_status(patient_id: str):
    """Get patient's optimization status for surgery"""
    db = get_firestore_client()
    
    # Get schedule items
    schedule_items = []
    items_docs = db.collection("schedule_items").where("patient_id", "==", patient_id).stream()
    
    for doc in items_docs:
        item_data = doc.to_dict()
        schedule_items.append(item_data)
    
    # Calculate status
    total_items = len(schedule_items)
    completed_items = len([item for item in schedule_items if item.get("patient_completed", False)])
    missed_items = len([item for item in schedule_items if not item.get("patient_completed", False) and item["scheduled_date"] < datetime.now()])
    
    completion_rate = (completed_items / total_items * 100) if total_items > 0 else 0
    is_optimized = total_items > 0 and completed_items == total_items
    needs_reschedule = missed_items > 0
    
    return {
        "patient_id": patient_id,
        "total_schedule_items": total_items,
        "completed_items": completed_items,
        "missed_items": missed_items,
        "completion_rate": completion_rate,
        "is_optimized": is_optimized,
        "needs_reschedule": needs_reschedule,
        "status": "optimized" if is_optimized else "not_optimized" if needs_reschedule else "in_progress"
    }

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
