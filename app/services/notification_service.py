#!/usr/bin/env python3
"""
Firebase Cloud Messaging notification service
"""

import firebase_admin
from firebase_admin import messaging
from app.firebase_client import get_firestore_client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.db = get_firestore_client()
    
    def send_reminder(self, reminder_id: str):
        """Send any reminder notification - simplified single function"""
        # Get the reminder from database
        reminder_doc = self.db.collection("reminders").document(reminder_id).get()
        if not reminder_doc.exists:
            return {"success": False, "error": "Reminder not found"}
        
        reminder_data = reminder_doc.to_dict()
        patient_id = reminder_data.get("patient_id")
        
        # Get patient's device token
        patient_doc = self.db.collection("patients").document(patient_id).get()
        if not patient_doc.exists:
            return {"success": False, "error": "Patient not found"}
        
        patient_data = patient_doc.to_dict()
        device_token = patient_data.get("device_token")
        
        if not device_token:
            return {"success": False, "error": "No device token found for patient"}
        
        # Create notification content from reminder data
        reminder_type = reminder_data.get("type", "general")
        medicine = reminder_data.get("medicine")
        action = reminder_data.get("action", "")
        notes = reminder_data.get("notes", "")
        
        # Simple title and body based on reminder content
        if medicine:
            if action == "hold":
                title = f"⏸️ Hold {medicine}"
                body = notes
            elif action == "continue":
                title = f"💊 Continue {medicine}"
                body = notes
            else:
                title = f"💊 {medicine} Reminder"
                body = notes
        else:
            # General reminders (fasting, bathing, etc.)
            if reminder_type == "fasting":
                title = "🍽️ Fasting Reminder"
            elif reminder_type == "bathing":
                title = "🛁 Bathing Reminder"
            elif reminder_type == "substance_use":
                title = "🚫 Substance Use Reminder"
            else:
                title = "📋 Preoperative Reminder"
            body = notes
        
        # Send notification directly
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data={
                    "patient_id": patient_id,
                    "reminder_id": reminder_id,
                    "type": reminder_type,
                    "medicine": medicine or "",
                    "action": action
                },
                token=device_token
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent reminder: {response}")
            result = {"success": True, "message_id": response}
            
        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            result = {"success": False, "error": str(e)}
        
        # Update reminder status to "sent" if successful
        if result.get("success"):
            self.db.collection("reminders").document(reminder_id).update({
                "status": "sent",
                "sent_at": datetime.utcnow()
            })
        
        return result
