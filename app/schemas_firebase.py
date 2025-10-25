from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    CPC_STAFF = "cpc_staff"
    PATIENT = "patient"

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
    device_token: Optional[str] = None

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
    condition: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# CPC Report Schema
class CPCReportBase(BaseModel):
    patient_id: str
    uploaded_by: str
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

# Reminder Schema (Main model - populated directly from AI)
class ReminderBase(BaseModel):
    patient_id: str
    medicine: Optional[str] = None
    action: str  # "hold", "continue", "start_fasting", etc.
    scheduled_date: datetime
    scheduled_time: str  # HH:MM format

class ReminderCreate(ReminderBase):
    pass

class Reminder(ReminderBase):
    id: str
    status: ReminderStatus = ReminderStatus.PENDING
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Patient Schedule View
class PatientSchedule(BaseModel):
    patient_id: str
    surgery_date: Optional[datetime] = None
    reminders: List[Reminder]
    total_reminders: int
    completed_reminders: int
    is_optimized: bool

# CPC Dashboard
class CPCDashboard(BaseModel):
    total_patients: int
    pending_reports: int
    processed_reports: int
    total_reminders: int

# Notification Request
class NotificationRequest(BaseModel):
    patient_id: str
    title: str
    body: str
    data: Optional[Dict[str, str]] = None

# Authentication Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: UserRole
    access_token: str
    token_type: str = "bearer"
