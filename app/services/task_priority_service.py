from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.firebase_client import get_firestore_client
import logging

class TaskPriorityService:
    """
    Service for managing task priorities based on time and medication importance
    """
    
    def __init__(self):
        self.db = get_firestore_client()
    
    def calculate_task_priority(self, schedule_item: Dict[str, Any]) -> int:
        """
        Calculate priority score for a schedule item
        Higher score = higher priority
        """
        now = datetime.now()
        scheduled_time = schedule_item.get("scheduled_date")
        
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.fromisoformat(scheduled_time)
        
        # Time-based priority (closer to now = higher priority)
        time_diff = (scheduled_time - now).total_seconds() / 3600  # hours
        
        # Medication type priority
        medication_priority = self._get_medication_priority(schedule_item)
        
        # Calculate final priority score
        if time_diff <= 0:  # Overdue
            priority_score = 1000 + medication_priority
        elif time_diff <= 2:  # Due within 2 hours
            priority_score = 500 + medication_priority
        elif time_diff <= 24:  # Due within 24 hours
            priority_score = 200 + medication_priority
        elif time_diff <= 72:  # Due within 3 days
            priority_score = 100 + medication_priority
        else:
            priority_score = 50 + medication_priority
        
        return int(priority_score)
    
    def _get_medication_priority(self, schedule_item: Dict[str, Any]) -> int:
        """
        Get priority based on medication type and action
        """
        medication_name = schedule_item.get("medication_name", "").lower()
        action = schedule_item.get("action", "").lower()
        item_type = schedule_item.get("type", "").lower()
        
        # Critical medications that must be held
        critical_medications = ["warfarin", "aspirin", "clopidogrel", "heparin"]
        if any(med in medication_name for med in critical_medications):
            return 100
        
        # Fasting is critical
        if item_type == "fasting":
            return 90
        
        # Medication holds are high priority
        if action == "hold":
            return 80
        
        # Medication continues are medium priority
        if action == "continue":
            return 60
        
        # Other preparations are lower priority
        return 40
    
    def get_priority_tasks(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks ordered by priority for a patient
        """
        # Get all schedule items for patient
        items_docs = self.db.collection("schedule_items").where("patient_id", "==", patient_id).stream()
        
        tasks = []
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
            
            tasks.append(item_data)
        
        # Sort by priority score (highest first)
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
