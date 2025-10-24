from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cpc_staff, patient_app

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
