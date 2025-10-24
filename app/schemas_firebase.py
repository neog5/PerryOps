from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    PATIENT = "patient"
    CPC_STAFF = "cpc_staff"
    ADMIN = "admin"

class RecommendationStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class ReminderStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    MISSED = "missed"

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole
    device_token: Optional[str] = None  # For push notifications

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Patient Schemas
class PatientBase(BaseModel):
    user_id: str
    condition: Optional[str] = None
    notes: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Surgery Schemas
class SurgeryBase(BaseModel):
    patient_id: str
    surgery_date: datetime
    surgery_type: Optional[str] = None
    surgeon_name: Optional[str] = None
    hospital_name: Optional[str] = None

class SurgeryCreate(SurgeryBase):
    pass

class Surgery(SurgeryBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Model Recommendation Schemas
class ModelRecommendationBase(BaseModel):
    patient_id: str
    condition: str
    data: Dict[str, Any]  # JSON data from AI model

class ModelRecommendationCreate(ModelRecommendationBase):
    pass

class ModelRecommendation(ModelRecommendationBase):
    id: str
    status: RecommendationStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Reminder Schemas
class ReminderBase(BaseModel):
    patient_id: str
    medicine: str
    dosage: str
    time: str  # HH:MM format
    date: Optional[datetime] = None

class ReminderCreate(ReminderBase):
    pass

class Reminder(ReminderBase):
    id: str
    sent: bool
    status: ReminderStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

# Response Schemas
class PatientSchedule(BaseModel):
    patient_id: str
    reminders: List[Reminder]
    surgery_date: Optional[datetime] = None
    is_optimized: bool

class ApprovalResponse(BaseModel):
    status: str
    created_reminders: int
    message: str

class NotificationRequest(BaseModel):
    patient_id: str
    title: str
    body: str
    data: Optional[Dict[str, str]] = None
