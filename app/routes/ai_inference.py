from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.db.crud import camera as camera_crud
from app.db.models.camera import Camera
import httpx
import os

# Create router for AI inference integration
router = APIRouter(
    prefix="/api/v1/ai-inference",
    tags=["AI Inference"]
)

# AI inference service configuration
AI_INFERENCE_URL = os.getenv("AI_INFERENCE_URL", "http://ai_inference:8001")

async def get_ai_inference_client():
    """Get HTTP client for AI inference service"""
    async with httpx.AsyncClient() as client:
        yield client

@router.get("/test-connection/")
async def test_ai_inference_connection(client: httpx.AsyncClient = Depends(get_ai_inference_client)):
    """Test connection to AI inference service"""
    try:
        # Try to connect to the root endpoint first
        response = await client.get(f"{AI_INFERENCE_URL}/")
        root_response = response.json()
        
        # Try to connect to the models endpoint
        models_response = await client.get(f"{AI_INFERENCE_URL}/models")
        models_data = models_response.json()
        
        return {
            "status": "connected",
            "ai_inference_url": AI_INFERENCE_URL,
            "root_endpoint": root_response,
            "models_endpoint": models_data
        }
    except httpx.ConnectError as e:
        return {
            "status": "connection_failed",
            "ai_inference_url": AI_INFERENCE_URL,
            "error": f"Connection error: {str(e)}",
            "suggestion": "Check if ai_inference service is running and accessible"
        }
    except httpx.TimeoutException as e:
        return {
            "status": "timeout",
            "ai_inference_url": AI_INFERENCE_URL,
            "error": f"Timeout error: {str(e)}",
            "suggestion": "AI inference service is not responding"
        }
    except Exception as e:
        return {
            "status": "failed",
            "ai_inference_url": AI_INFERENCE_URL,
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.get("/health/")
async def ai_inference_health(client: httpx.AsyncClient = Depends(get_ai_inference_client)):
    """Check AI inference service health"""
    try:
        response = await client.get(f"{AI_INFERENCE_URL}/")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI inference service unavailable: {str(e)}")

@router.get("/models/")
async def get_available_models(client: httpx.AsyncClient = Depends(get_ai_inference_client)):
    """Get list of available AI models"""
    try:
        response = await client.get(f"{AI_INFERENCE_URL}/models")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get available models: {str(e)}")

@router.post("/camera/{camera_id}/detect/")
async def detect_objects_in_camera_image(
    camera_id: int,
    object_name: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    client: httpx.AsyncClient = Depends(get_ai_inference_client)
):
    """Detect objects in an image from a specific camera"""
    # Verify camera exists
    camera = camera_crud.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    try:
        # Forward request to AI inference service
        files = {"image": (image.filename, image.file, image.content_type)}
        data = {"object_name": object_name}
        
        response = await client.post(f"{AI_INFERENCE_URL}/inference/detection", data=data, files=files)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run object detection: {str(e)}")

@router.post("/detect/")
async def detect_objects(
    object_name: str = Form(...),
    image: UploadFile = File(...),
    client: httpx.AsyncClient = Depends(get_ai_inference_client)
):
    """Detect objects in an uploaded image"""
    try:
        # Forward request to AI inference service
        files = {"image": (image.filename, image.file, image.content_type)}
        data = {"object_name": object_name}
        
        response = await client.post(f"{AI_INFERENCE_URL}/inference/detection", data=data, files=files)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run object detection: {str(e)}") 