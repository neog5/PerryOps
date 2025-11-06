"""
Data models for API requests and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    """Patient information model."""
    age: Optional[int] = None
    sex: Optional[str] = None
    bmi: Optional[float] = None


class SurgeryDetails(BaseModel):
    """Surgery details model."""
    procedure: Optional[str] = None
    date: Optional[str] = Field(None, description="Surgery date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Surgery time in HH:MM format")


class MedicationInstruction(BaseModel):
    """Medication instruction model."""
    medication: Optional[str] = None
    pre_op_action: Optional[str] = None


class GeneralPreOpInstructions(BaseModel):
    """General pre-operative instructions model."""
    fasting: Optional[str] = None
    bathing: Optional[str] = None
    substance_use: Optional[str] = None


class StructuredData(BaseModel):
    """Complete structured medical report data."""
    patient_info: Optional[PatientInfo] = None
    surgery_details: Optional[SurgeryDetails] = None
    medications_instructions: List[MedicationInstruction] = []
    general_pre_op_instructions: Optional[GeneralPreOpInstructions] = None


class ComplianceIssue(BaseModel):
    """Individual compliance issue with old entry, suggested new entry, and explanation."""
    item_type: str
    name: str
    old_entry: Dict[str, Any] = Field(..., description="Complete original entry")
    suggested_entry: Dict[str, Any] = Field(..., description="Complete corrected entry")
    explanation: str = Field(..., description="One line explanation of what changed and why")
    issue: Optional[str] = Field(None, description="Description of the compliance issue")
    guideline_heading: Optional[str] = None
    guideline_page: Optional[int] = None


class ComplianceResponse(BaseModel):
    """Response from compliance checking."""
    compliance_summary: str
    flagged_items: List[ComplianceIssue] = []


class PatientAction(BaseModel):
    """Individual patient action."""
    task: str
    stop_time: Optional[str] = None
    note: str
    medication: Optional[str] = None


class PatientActionPlan(BaseModel):
    """Complete patient action plan."""
    patient_info: Optional[PatientInfo] = None
    surgery_details: Optional[SurgeryDetails] = None
    actions: List[PatientAction] = []
    compliance_report: Optional[ComplianceResponse] = None


class UploadResponse(BaseModel):
    """Response from file upload."""
    session_id: str
    message: str
    files_uploaded: List[str]


class ExtractResponse(BaseModel):
    """Response from data extraction."""
    session_id: str
    structured_data: Dict[str, Any]


class ComplianceCheckResponse(BaseModel):
    """Response from compliance check."""
    session_id: str
    compliance_report: ComplianceResponse
    awaiting_corrections: bool = True


class MergeRequest(BaseModel):
    """Request to merge compliance corrections."""
    session_id: str
    flagged_items: List[ComplianceIssue] = Field(
        ..., 
        description="List of flagged items from compliance check with suggested corrections"
    )


class MergeResponse(BaseModel):
    """Response from merge operation."""
    session_id: str
    updated_data: Dict[str, Any]
    message: str


class ActionPlanResponse(BaseModel):
    """Final action plan response."""
    session_id: str
    action_plan: PatientActionPlan
