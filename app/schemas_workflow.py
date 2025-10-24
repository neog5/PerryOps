from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    CPC_STAFF = "cpc_staff"
    PATIENT = "patient"

class RecommendationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ScheduleItemType(str, Enum):
    MEDICATION_HOLD = "medication_hold"
    MEDICATION_CONTINUE = "medication_continue"
    FASTING = "fasting"
    OTHER = "other"

class NotificationStatus(str, Enum):
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
    name: str
    email: EmailStr
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None

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

# CPC Report Schemas
class CPCReportBase(BaseModel):
    patient_id: str
    uploaded_by: str  # CPC staff user_id
    original_filename: str
    file_path: Optional[str] = None

class CPCReportCreate(CPCReportBase):
    pass

class CPCReport(CPCReportBase):
    id: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    is_processed: bool = False
    
    class Config:
        from_attributes = True

# AI Agent Response Schema
class AIRecommendationItem(BaseModel):
    type: ScheduleItemType
    medication_name: Optional[str] = None
    action: str  # "hold", "continue", "start_fasting", etc.
    days_before_surgery: Optional[int] = None
    hours_before_surgery: Optional[int] = None
    specific_time: Optional[str] = None  # "08:00", "20:00", etc.
    instructions: str
    priority: int = 1  # 1 = high, 2 = medium, 3 = low

class AIRecommendationResponse(BaseModel):
    surgery_date: datetime
    surgery_time: str
    recommendations: List[AIRecommendationItem]
    generated_at: datetime
    agent_version: str = "v1.0"

# Recommendation Schemas
class RecommendationBase(BaseModel):
    patient_id: str
    cpc_report_id: str
    surgery_id: str
    ai_response: AIRecommendationResponse
    status: RecommendationStatus = RecommendationStatus.PENDING

class RecommendationCreate(RecommendationBase):
    pass

class Recommendation(RecommendationBase):
    id: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Schedule Item Schemas (for approved recommendations)
class ScheduleItemBase(BaseModel):
    patient_id: str
    recommendation_id: str
    type: ScheduleItemType
    medication_name: Optional[str] = None
    action: str
    scheduled_date: datetime
    scheduled_time: str  # HH:MM format
    instructions: str
    priority: int = 1

class ScheduleItemCreate(ScheduleItemBase):
    pass

class ScheduleItem(ScheduleItemBase):
    id: str
    notification_sent: bool = False
    patient_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Patient Schedule View Schema
class PatientScheduleView(BaseModel):
    patient_id: str
    surgery_date: datetime
    surgery_time: str
    schedule_items: List[ScheduleItem]
    total_items: int
    completed_items: int
    pending_items: int
    is_optimized: bool

# CPC Staff Dashboard Schema
class CPCDashboard(BaseModel):
    total_patients: int
    pending_recommendations: int
    approved_recommendations: int
    rejected_recommendations: int
    recent_uploads: List[CPCReport]

# Notification Schemas
class NotificationRequest(BaseModel):
    patient_id: str
    title: str
    body: str
    data: Optional[Dict[str, str]] = None
    scheduled_time: Optional[datetime] = None

class NotificationResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
