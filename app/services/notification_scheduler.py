#!/usr/bin/env python3
"""
Notification Scheduler for PerryOps
Handles both single-time and recurring reminders
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from app.firebase_client import get_firestore_client
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class NotificationScheduler:
    def __init__(self):
        self.db = get_firestore_client()
        self.notification_service = NotificationService()
        self.running = False
        
    async def start_scheduler(self):
        """Start the notification scheduler"""
        self.running = True
        logger.info("🚀 Notification scheduler started")
        
        while self.running:
            try:
                await self.check_and_send_notifications()
                # Check every 5 minutes
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                await asyncio.sleep(60)
    
    def stop_scheduler(self):
        """Stop the notification scheduler"""
        self.running = False
        logger.info("🛑 Notification scheduler stopped")
    
    async def check_and_send_notifications(self):
        """Check for due notifications and send them"""
        try:
            now = datetime.utcnow()
            logger.info(f"🔍 Checking notifications at {now}")
            
            # Get all pending reminders
            reminders = self.get_pending_reminders()
            
            for reminder in reminders:
                await self.process_reminder(reminder, now)
                
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
    
    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Get all pending reminders from database"""
        try:
            reminders = []
            docs = self.db.collection("reminders").where("status", "==", "pending").stream()
            
            for doc in docs:
                reminder_data = doc.to_dict()
                reminder_data["id"] = doc.id
                reminders.append(reminder_data)
            
            logger.info(f"📋 Found {len(reminders)} pending reminders")
            return reminders
            
        except Exception as e:
            logger.error(f"Error getting reminders: {e}")
            return []
    
    async def process_reminder(self, reminder: Dict[str, Any], current_time: datetime):
        """Process a single reminder and send notifications if due"""
        try:
            reminder_id = reminder["id"]
            action = reminder.get("action", "")
            patient_id = reminder.get("patient_id")
            
            # Case 1: Continue medications - send immediately (reminder_datetime is null)
            # But only if it hasn't been sent yet (no sent_at timestamp)
            if action == "continue" and not reminder.get("reminder_datetime") and not reminder.get("sent_at"):
                logger.info(f"⏰ Sending continue reminder for patient {patient_id}: {reminder['medicine']} - {reminder['action']}")
                await self.send_reminder_notification(reminder)
            
            # Case 2: Hold/other reminders - send at scheduled time
            elif reminder.get("reminder_datetime"):
                reminder_datetime_str = reminder.get("reminder_datetime")
                if isinstance(reminder_datetime_str, str):
                    # Parse as UTC datetime
                    reminder_datetime = datetime.fromisoformat(reminder_datetime_str.replace('Z', '+00:00'))
                else:
                    reminder_datetime = reminder_datetime_str
                
                # Ensure both datetimes are timezone-aware for comparison
                if reminder_datetime.tzinfo is None:
                    reminder_datetime = reminder_datetime.replace(tzinfo=timezone.utc)
                if current_time.tzinfo is None:
                    current_time = current_time.replace(tzinfo=timezone.utc)
                
                # Check if it's time to send (within 4 minute tolerance)
                time_diff = (reminder_datetime - current_time).total_seconds()
                
                if 0 <= time_diff <= 240:  # Due within 4 minutes
                    logger.info(f"⏰ Sending scheduled reminder for patient {patient_id}: {reminder['medicine']} - {reminder['action']}")
                    await self.send_reminder_notification(reminder)
                        
        except Exception as e:
            logger.error(f"Error processing reminder {reminder.get('id', 'unknown')}: {e}")
    
    async def send_reminder_notification(self, reminder: Dict[str, Any], schedule_time: datetime = None):
        """Send notification for a reminder"""
        try:
            reminder_id = reminder["id"]
            patient_id = reminder["patient_id"]
            
            # Use the notification service to send the reminder
            result = self.notification_service.send_reminder(reminder_id)
            
            if result.get("success"):
                logger.info(f"✅ Notification sent successfully for reminder {reminder_id}")
                
                # Update reminder status
                self.update_reminder_status(reminder_id, "sent", schedule_time)
            else:
                logger.error(f"❌ Failed to send notification: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error sending reminder notification: {e}")
    
    def update_reminder_status(self, reminder_id: str, status: str, schedule_time: datetime = None):
        """Update reminder status in database"""
        try:
            update_data = {
                "status": status,
                "sent_at": datetime.utcnow()
            }
            
            if schedule_time:
                update_data["last_sent_schedule"] = schedule_time.isoformat()
            
            self.db.collection("reminders").document(reminder_id).update(update_data)
            logger.info(f"📝 Updated reminder {reminder_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Error updating reminder status: {e}")
# Global scheduler instance
scheduler = NotificationScheduler()

async def start_notification_scheduler():
    """Start the notification scheduler"""
    await scheduler.start_scheduler()

def stop_notification_scheduler():
    """Stop the notification scheduler"""
    scheduler.stop_scheduler()
