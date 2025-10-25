import asyncio
import logging
from datetime import datetime, timedelta
from app.services.notification_scheduler import NotificationScheduler
from app.services.task_priority_service import TaskPriorityService
from app.firebase_client import get_firestore_client

class BackgroundTaskManager:
    """
    Manages background tasks for notifications and priority updates
    """
    
    def __init__(self):
        self.notification_scheduler = NotificationScheduler()
        self.task_priority_service = TaskPriorityService()
        self.db = get_firestore_client()
        self.running = False
    
    async def start(self):
        """Start background task manager"""
        self.running = True
        logging.info("Background task manager started")
        
        # Start notification scheduler
        asyncio.create_task(self._notification_loop())
        
        # Start priority updater
        asyncio.create_task(self._priority_update_loop())
        
        # Start overdue task checker
        asyncio.create_task(self._overdue_task_loop())
    
    async def stop(self):
        """Stop background task manager"""
        self.running = False
        logging.info("Background task manager stopped")
    
    async def _notification_loop(self):
        """Send notifications every minute"""
        while self.running:
            try:
                # Send due notifications
                result = self.notification_scheduler.send_due_notifications()
                if result["sent"] > 0 or result["failed"] > 0:
                    logging.info(f"Notifications: {result['sent']} sent, {result['failed']} failed")
                
                # Check for urgent tasks that need immediate notifications
                await self._check_urgent_tasks()
                
            except Exception as e:
                logging.error(f"Error in notification loop: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _priority_update_loop(self):
        """Update task priorities every 5 minutes"""
        while self.running:
            try:
                # Get all patients
                patients_docs = self.db.collection("patients").stream()
                
                for patient_doc in patients_docs:
                    patient_id = patient_doc.id
                    
                    # Get all tasks for this patient
                    items_docs = self.db.collection("schedule_items").where("patient_id", "==", patient_id).stream()
                    
                    for item_doc in items_docs:
                        # Update priority for each task
                        self.task_priority_service.update_task_priority(item_doc.id)
                
                logging.info("Task priorities updated")
                
            except Exception as e:
                logging.error(f"Error in priority update loop: {e}")
            
            await asyncio.sleep(300)  # Update every 5 minutes
    
    async def _overdue_task_loop(self):
        """Check for overdue tasks every 10 minutes"""
        while self.running:
            try:
                now = datetime.now()
                
                # Get all incomplete tasks
                items_docs = self.db.collection("schedule_items").where("patient_completed", "==", False).stream()
                
                overdue_count = 0
                for item_doc in items_docs:
                    item_data = item_doc.to_dict()
                    scheduled_time = item_data.get("scheduled_date")
                    
                    if isinstance(scheduled_time, str):
                        scheduled_time = datetime.fromisoformat(scheduled_time)
                    
                    # Check if task is overdue (more than 1 hour past scheduled time)
                    if scheduled_time < now - timedelta(hours=1):
                        # Mark as overdue
                        self.db.collection("schedule_items").document(item_doc.id).update({
                            "is_overdue": True,
                            "overdue_since": now
                        })
                        overdue_count += 1
                
                if overdue_count > 0:
                    logging.warning(f"Found {overdue_count} overdue tasks")
                
            except Exception as e:
                logging.error(f"Error in overdue task loop: {e}")
            
            await asyncio.sleep(600)  # Check every 10 minutes
    
    async def _check_urgent_tasks(self):
        """Check for urgent tasks and send immediate notifications"""
        try:
            # Get all patients
            patients_docs = self.db.collection("patients").stream()
            
            for patient_doc in patients_docs:
                patient_id = patient_doc.id
                patient_data = patient_doc.to_dict()
                
                # Get urgent tasks for this patient
                urgent_tasks = self.task_priority_service.get_urgent_tasks(patient_id, hours_ahead=2)
                
                for task in urgent_tasks:
                    # Check if notification already sent for this task
                    if not task.get("urgent_notification_sent", False):
                        # Send urgent notification
                        device_token = patient_data.get("device_token")
                        if device_token:
                            from app.firebase_client import send_push_notification
                            
                            result = send_push_notification(
                                device_token=device_token,
                                title="🚨 URGENT: Medication Reminder",
                                body=f"Time to {task.get('action', 'take action')}: {task.get('instructions', '')}",
                                data={"task_id": task["id"], "urgent": "true"}
                            )
                            
                            if result["success"]:
                                # Mark urgent notification as sent
                                self.db.collection("schedule_items").document(task["id"]).update({
                                    "urgent_notification_sent": True,
                                    "urgent_notification_sent_at": datetime.now()
                                })
                                
                                logging.info(f"Urgent notification sent to patient {patient_id}")
        
        except Exception as e:
            logging.error(f"Error checking urgent tasks: {e}")

# Global instance
background_manager = BackgroundTaskManager()
