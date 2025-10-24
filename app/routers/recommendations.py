from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.firebase_client import get_firestore_client
from app.schemas_firebase import ModelRecommendation, ModelRecommendationCreate, ApprovalResponse
from app.services.ai_processor import AIProcessor
from datetime import datetime

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("/generate", response_model=ModelRecommendation)
def generate_recommendations(patient_data: Dict[str, Any]):
    """Generate AI recommendations for a patient"""
    db = get_firestore_client()
    ai_processor = AIProcessor()
    
    # Process patient data and generate recommendations
    recommendations_data = ai_processor.generate_recommendations(patient_data)
    
    # Store in database
    recommendation_data = {
        "patient_id": recommendations_data["patient_id"],
        "condition": recommendations_data["condition"],
        "data": recommendations_data,
        "status": "pending_approval",
        "created_at": datetime.now()
    }
    
    doc_ref = db.collection("model_recommendations").add(recommendation_data)
    recommendation_id = doc_ref[1].id
    
    # Get the created recommendation
    rec_doc = db.collection("model_recommendations").document(recommendation_id).get()
    if not rec_doc.exists:
        raise HTTPException(status_code=400, detail="Failed to generate recommendations")
    
    rec_data = rec_doc.to_dict()
    rec_data["id"] = recommendation_id
    return rec_data

@router.get("/pending", response_model=List[ModelRecommendation])
def get_pending_recommendations():
    """Get all pending recommendations for CPC staff review"""
    db = get_firestore_client()
    
    recommendations = []
    docs = db.collection("model_recommendations").where("status", "==", "pending_approval").stream()
    
    for doc in docs:
        rec_data = doc.to_dict()
        rec_data["id"] = doc.id
        recommendations.append(rec_data)
    
    return recommendations

@router.post("/{recommendation_id}/approve", response_model=ApprovalResponse)
def approve_recommendation(recommendation_id: str, approved_by: str):
    """Approve a recommendation and create reminders"""
    db = get_firestore_client()
    
    # Get the recommendation
    rec_doc = db.collection("model_recommendations").document(recommendation_id).get()
    
    if not rec_doc.exists:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    recommendation = rec_doc.to_dict()
    
    # Update recommendation status
    db.collection("model_recommendations").document(recommendation_id).update({
        "status": "approved",
        "approved_by": approved_by,
        "approved_at": datetime.now()
    })
    
    # Create reminders for each medication
    reminders_created = 0
    recommendations_data = recommendation["data"]
    
    for med in recommendations_data.get("recommendations", []):
        reminder_data = {
            "patient_id": recommendation["patient_id"],
            "medicine": med["medicine"],
            "dosage": med["dosage"],
            "time": med["time"],
            "sent": False,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        db.collection("reminders").add(reminder_data)
        reminders_created += 1
    
    return ApprovalResponse(
        status="approved",
        created_reminders=reminders_created,
        message=f"Recommendation approved and {reminders_created} reminders created"
    )

@router.post("/{recommendation_id}/reject")
def reject_recommendation(recommendation_id: str, rejected_by: str):
    """Reject a recommendation"""
    db = get_firestore_client()
    
    rec_doc = db.collection("model_recommendations").document(recommendation_id).get()
    if not rec_doc.exists:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    db.collection("model_recommendations").document(recommendation_id).update({
        "status": "rejected",
        "approved_by": rejected_by,
        "approved_at": datetime.now()
    })
    
    return {"status": "rejected", "message": "Recommendation rejected"}
