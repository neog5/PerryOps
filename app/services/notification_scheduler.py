from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.firebase_client import get_firestore_client, send_push_notification
import logging

class NotificationScheduler:
    """
    Service for scheduling and sending push notifications to patients
    """
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def schedule_notifications_for_approved_recommendation(self, recommendation_id: str):
        """
        Schedule notifications for all schedule items in an approved recommendation
        """
        # Get all schedule items for this recommendation
        items_docs = self.db.collection("schedule_items").where("recommendation_id", "==", recommendation_id).stream()
        
        scheduled_notifications = []
        
        for doc in items_docs:
            item_data = doc.to_dict()
            item_data["id"] = doc.id
            
            # Calculate notification time (1 hour before scheduled time)
            scheduled_datetime = item_data["scheduled_date"]
            if isinstance(scheduled_datetime, str):
                scheduled_datetime = datetime.fromisoformat(scheduled_datetime)
            
            notification_time = scheduled_datetime - timedelta(hours=1)
            
            # Create notification record
            notification_data = {
                "patient_id": item_data["patient_id"],
                "schedule_item_id": doc.id,
                "title": "Preoperative Reminder",
                "body": item_data["instructions"],
                "scheduled_time": notification_time,
                "sent": False,
                "created_at": datetime.now()
            }
            
            # Store notification
            notif_doc_ref = self.db.collection("scheduled_notifications").add(notification_data)
            scheduled_notifications.append(notif_doc_ref[1].id)
        
        return scheduled_notifications
    
    def send_due_notifications(self):
        """
        Send notifications that are due now
        """
        now = datetime.now()
        
        # Get due notifications
        due_notifications = self.db.collection("scheduled_notifications").where("scheduled_time", "<=", now).where("sent", "==", False).stream()
        
        sent_count = 0
        failed_count = 0
        
        for notif_doc in due_notifications:
            notif_data = notif_doc.to_dict()
            
            # Get patient's device token
            patient_doc = self.db.collection("patients").document(notif_data["patient_id"]).get()
            if not patient_doc.exists:
                logging.error(f"Patient {notif_data['patient_id']} not found")
                failed_count += 1
                continue
            
            patient_data = patient_doc.to_dict()
            device_token = patient_data.get("device_token")
            
            if not device_token:
                logging.error(f"Device token not found for patient {notif_data['patient_id']}")
                failed_count += 1
                continue
            
            # Send notification
            result = send_push_notification(
                device_token=device_token,
                title=notif_data["title"],
                body=notif_data["body"],
                data={"schedule_item_id": notif_data["schedule_item_id"]}
            )
            
            if result["success"]:
                # Mark notification as sent
                self.db.collection("scheduled_notifications").document(notif_doc.id).update({
                    "sent": True,
                    "sent_at": datetime.now(),
                    "message_id": result["message_id"]
                })
                sent_count += 1
            else:
                logging.error(f"Failed to send notification: {result['error']}")
                failed_count += 1
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "total_processed": sent_count + failed_count
        }
    
    def get_patient_notifications(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get all notifications for a patient
        """
        notifications = []
        docs = self.db.collection("scheduled_notifications").where("patient_id", "==", patient_id).order_by("scheduled_time").stream()
        
        for doc in docs:
            notif_data = doc.to_dict()
            notif_data["id"] = doc.id
            notifications.append(notif_data)
        
        return notifications
    
    def mark_notification_sent(self, notification_id: str):
        """
        Mark a notification as sent
        """
        self.db.collection("scheduled_notifications").document(notification_id).update({
            "sent": True,
            "sent_at": datetime.now()
        })
    
    def create_immediate_notification(self, patient_id: str, title: str, body: str, data: Dict[str, str] = None):
        """
        Create and send an immediate notification
        """
        # Get patient's device token
        patient_doc = self.db.collection("patients").document(patient_id).get()
        if not patient_doc.exists:
            return {"success": False, "error": "Patient not found"}
        
        patient_data = patient_doc.to_dict()
        device_token = patient_data.get("device_token")
        
        if not device_token:
            return {"success": False, "error": "Device token not found"}
        
        # Send notification
        result = send_push_notification(
            device_token=device_token,
            title=title,
            body=body,
            data=data or {}
        )
        
        if result["success"]:
            # Store notification record
            notification_data = {
                "patient_id": patient_id,
                "title": title,
                "body": body,
                "scheduled_time": datetime.now(),
                "sent": True,
                "sent_at": datetime.now(),
                "message_id": result["message_id"],
                "created_at": datetime.now()
            }
            
            self.db.collection("scheduled_notifications").add(notification_data)
        
        return result
