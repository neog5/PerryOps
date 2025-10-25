from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.firebase_client import get_firestore_client
import logging

class TaskPriorityService:
    """
    Service for managing task priorities based purely on time before surgery
    """
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def calculate_task_priority(self, schedule_item: Dict[str, Any]) -> int:
        """
        Calculate priority score for a schedule item based on time before surgery
        Higher score = higher priority (tasks further from surgery = higher priority)
        """
        now = datetime.now()
        scheduled_time = schedule_item.get("scheduled_date")
        
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.fromisoformat(scheduled_time)
        
        # Get surgery date for this patient
        patient_id = schedule_item.get("patient_id")
        surgery_date = self._get_surgery_date(patient_id)
        
        if not surgery_date:
            # If no surgery date, use current time as reference
            surgery_date = now
        
        # Calculate days before surgery
        days_before_surgery = (surgery_date - scheduled_time).days
        
        # Priority: More days before surgery = higher priority
        # This ensures medications that need to be held 5 days before surgery
        # appear higher than those that need to be held 3 days before surgery
        priority_score = days_before_surgery * 100
        
        # Add time-based urgency (tasks due soon get slight boost)
        time_diff = (scheduled_time - now).total_seconds() / 3600  # hours
        
        if time_diff <= 0:  # Overdue
            priority_score += 1000
        elif time_diff <= 2:  # Due within 2 hours
            priority_score += 500
        elif time_diff <= 24:  # Due within 24 hours
            priority_score += 200
        
        return int(priority_score)
    
    def _get_surgery_date(self, patient_id: str) -> datetime:
        """
        Get surgery date for a patient
        """
        try:
            surgery_docs = self.db.collection("surgeries").where("patient_id", "==", patient_id).order_by("surgery_date", direction="DESCENDING").limit(1).stream()
            
            for doc in surgery_docs:
                surgery_data = doc.to_dict()
                surgery_date = surgery_data.get("surgery_date")
                
                if isinstance(surgery_date, str):
                    return datetime.fromisoformat(surgery_date)
                return surgery_date
        except Exception as e:
            logging.error(f"Error getting surgery date for patient {patient_id}: {e}")
        
        return None
    
    def get_priority_tasks(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks ordered by priority for a patient
        """
        # Get all schedule items for patient
        items_docs = self.db.collection("schedule_items").where("patient_id", "==", patient_id).stream()
        
        tasks = []
        surgery_date = self._get_surgery_date(patient_id)
        
        for doc in items_docs:
            item_data = doc.to_dict()
            item_data["id"] = doc.id
            
            # Calculate priority
            priority_score = self.calculate_task_priority(item_data)
            item_data["priority_score"] = priority_score
            
            # Add time until due
            scheduled_time = item_data.get("scheduled_date")
            if isinstance(scheduled_time, str):
                scheduled_time = datetime.fromisoformat(scheduled_time)
            
            time_until_due = (scheduled_time - datetime.now()).total_seconds() / 3600
            item_data["hours_until_due"] = round(time_until_due, 1)
            
            # Add days before surgery
            if surgery_date:
                days_before_surgery = (surgery_date - scheduled_time).days
                item_data["days_before_surgery"] = days_before_surgery
            else:
                item_data["days_before_surgery"] = None
            
            tasks.append(item_data)
        
        # Sort by priority score (highest first)
        # This will show tasks that need to be done further from surgery first
        tasks.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return tasks
    
    def get_urgent_tasks(self, patient_id: str, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Get tasks that are urgent (due within specified hours)
        """
        all_tasks = self.get_priority_tasks(patient_id)
        now = datetime.now()
        
        urgent_tasks = []
        for task in all_tasks:
            scheduled_time = task.get("scheduled_date")
            if isinstance(scheduled_time, str):
                scheduled_time = datetime.fromisoformat(scheduled_time)
            
            # Check if task is due within the specified hours
            if scheduled_time <= now + timedelta(hours=hours_ahead):
                urgent_tasks.append(task)
        
        return urgent_tasks
    
    def update_task_priority(self, task_id: str):
        """
        Update priority for a specific task
        """
        task_doc = self.db.collection("schedule_items").document(task_id).get()
        if not task_doc.exists:
            return None
        
        task_data = task_doc.to_dict()
        priority_score = self.calculate_task_priority(task_data)
        
        # Update priority in database
        self.db.collection("schedule_items").document(task_id).update({
            "priority_score": priority_score,
            "updated_at": datetime.now()
        })
        
        return priority_score
