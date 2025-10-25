from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import logging
from contextlib import asynccontextmanager

from database import get_db, engine, Base
from models import User, Medication, Task, Notification, CPCReport
from schemas import (
    UserCreate, UserResponse, MedicationCreate, MedicationResponse,
    TaskCreate, TaskResponse, TaskUpdate, NotificationCreate,
    CPCReportCreate, CPCReportResponse, AIRecommendationCreate
)
from services import (
    UserService, MedicationService, TaskService, 
    NotificationService, CPCReportService, AIService
)
from auth import get_current_user, create_access_token, verify_token
from notification_scheduler import NotificationScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize notification scheduler
notification_scheduler = NotificationScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    await notification_scheduler.start()
    logger.info("Backend started successfully")
    yield
    # Shutdown
    await notification_scheduler.stop()
    logger.info("Backend shutdown complete")

app = FastAPI(
    title="PerryOps Backend API",
    description="Medication notification system for surgical procedures",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Dependency to get current user
async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    return await get_current_user(credentials.credentials, db)

# ==================== USER ENDPOINTS ====================

@app.post("/users/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (patient or CPC staff)"""
    user_service = UserService(db)
    return await user_service.create_user(user_data)

@app.post("/users/login")
async def login_user(email: str, password: str, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user_service = UserService(db)
    user = await user_service.authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

# ==================== AI RECOMMENDATION ENDPOINTS ====================

@app.post("/ai/recommendations", response_model=CPCReportResponse)
async def process_ai_recommendation(
    recommendation: AIRecommendationCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Process AI recommendation report and create medication tasks"""
    ai_service = AIService(db)
    cpc_service = CPCReportService(db)
    task_service = TaskService(db)
    
    # Create CPC report from AI recommendation
    cpc_report = await cpc_service.create_report(recommendation, current_user.id)
    
    # Process AI recommendations and create tasks
    tasks = await ai_service.process_recommendations(recommendation, current_user.id)
    
    # Create tasks in database
    created_tasks = []
    for task_data in tasks:
        task = await task_service.create_task(task_data)
        created_tasks.append(task)
    
    return cpc_report

# ==================== TASK ENDPOINTS ====================

@app.get("/tasks", response_model=List[TaskResponse])
async def get_user_tasks(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all tasks for the current user, ordered by priority"""
    task_service = TaskService(db)
    return await task_service.get_user_tasks(current_user.id)

@app.get("/tasks/pending-approval", response_model=List[TaskResponse])
async def get_pending_approval_tasks(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get tasks pending CPC staff approval"""
    if current_user.user_type != "cpc_staff":
        raise HTTPException(status_code=403, detail="Access denied")
    
    task_service = TaskService(db)
    return await task_service.get_pending_approval_tasks()

@app.put("/tasks/{task_id}/approve")
async def approve_task(
    task_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Approve a task (CPC staff only)"""
    if current_user.user_type != "cpc_staff":
        raise HTTPException(status_code=403, detail="Access denied")
    
    task_service = TaskService(db)
    return await task_service.approve_task(task_id, current_user.id)

@app.put("/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Mark a task as completed by patient"""
    task_service = TaskService(db)
    return await task_service.complete_task(task_id, current_user.id)

@app.get("/tasks/priority", response_model=List[TaskResponse])
async def get_priority_tasks(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get tasks that need immediate attention based on time and priority"""
    task_service = TaskService(db)
    return await task_service.get_priority_tasks(current_user.id)

# ==================== NOTIFICATION ENDPOINTS ====================

@app.post("/notifications/send")
async def send_notification(
    notification_data: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Send push notification to user"""
    notification_service = NotificationService(db)
    return await notification_service.send_notification(notification_data, current_user.id)

@app.get("/notifications", response_model=List[dict])
async def get_user_notifications(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all notifications for the current user"""
    notification_service = NotificationService(db)
    return await notification_service.get_user_notifications(current_user.id)

# ==================== CPC STAFF ENDPOINTS ====================

@app.get("/cpc/patient-status/{patient_id}")
async def get_patient_status(
    patient_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get patient optimization status for CPC staff"""
    if current_user.user_type != "cpc_staff":
        raise HTTPException(status_code=403, detail="Access denied")
    
    task_service = TaskService(db)
    return await task_service.get_patient_optimization_status(patient_id)

@app.get("/cpc/all-patients")
async def get_all_patients_status(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all patients and their optimization status for CPC staff"""
    if current_user.user_type != "cpc_staff":
        raise HTTPException(status_code=403, detail="Access denied")
    
    task_service = TaskService(db)
    return await task_service.get_all_patients_status()

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
