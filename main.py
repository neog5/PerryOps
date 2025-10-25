from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cpc_staff, patient_app
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PerryOps - Preoperative Optimization API",
    description="API for managing preoperative optimization recommendations and medication reminders",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cpc_staff.router)
app.include_router(patient_app.router)

@app.get("/")
def read_root():
    return {"message": "PerryOps API - Preoperative Optimization System"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Start the notification scheduler when the server starts"""
    try:
        from app.services.notification_scheduler import start_notification_scheduler
        logger.info("🚀 Starting notification scheduler...")
        asyncio.create_task(start_notification_scheduler())
        logger.info("✅ Notification scheduler started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start notification scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the notification scheduler when the server shuts down"""
    try:
        from app.services.notification_scheduler import stop_notification_scheduler
        logger.info("🛑 Stopping notification scheduler...")
        stop_notification_scheduler()
        logger.info("✅ Notification scheduler stopped successfully")
    except Exception as e:
        logger.error(f"❌ Failed to stop notification scheduler: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
