from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import os
from ..database import get_db
from ..db.models.camera import Camera as CameraModel
from ..db.schemas.camera import CameraCreate, CameraUpdate, CameraInDB
from ..db.crud import camera as camera_crud

router = APIRouter(
    prefix="/api/v1/cameras",
    tags=["cameras"]
)

# Video pipeline service configuration
VIDEO_PIPELINE_URL = os.getenv("VIDEO_PIPELINE_URL", "http://video-pipeline:8002")

async def get_video_pipeline_client():
    """Get HTTP client for video pipeline service"""
    async with httpx.AsyncClient() as client:
        yield client

@router.get("/", response_model=List[CameraInDB])
def list_cameras(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all cameras
    """
    return camera_crud.get_cameras(db, skip=skip, limit=limit)

@router.post("/", response_model=dict)
async def create_camera(
    camera: CameraCreate,
    db: Session = Depends(get_db),
    client: httpx.AsyncClient = Depends(get_video_pipeline_client)
):
    """
    Create a new camera and validate the video stream (get video info only)
    """
    # First, create the camera in the database with inactive status
    camera_data = camera.model_dump()
    camera_data['is_active'] = False  # Ensure camera is created as inactive
    db_camera = camera_crud.create_camera(db=db, camera=CameraCreate(**camera_data))
    
    # Convert SQLAlchemy model to Pydantic schema for serialization
    camera_schema = CameraInDB.model_validate(db_camera)
    
    # Initialize response with camera data
    response = {
        "camera": camera_schema,
        "video_validation": {
            "status": "pending",
            "video_info": None,
            "errors": []
        }
    }
    
    # Get video information if RTSP URL is provided
    if camera.rtsp_url:
        try:
            print(f"🔍 Getting video info for camera {db_camera.id}: {camera.rtsp_url}")
            
            # Get video information only (no decoding)
            try:
                video_info_data = {"url": camera.rtsp_url}
                print(f"Video info data: {video_info_data}")
                video_info_response = await client.post(
                    f"{VIDEO_PIPELINE_URL}/api/v1/video-pipeline/video-info-url/",
                    data=video_info_data,
                    timeout=30.0
                )
                print(f"Video info response: {video_info_response}")
                if video_info_response.status_code == 200:
                    video_info = video_info_response.json()
                    response["video_validation"]["video_info"] = video_info
                    response["video_validation"]["status"] = "validated"
                    
                    # Save video info to database
                    camera_crud.update_camera(
                        db=db, 
                        camera_id=db_camera.id, 
                        camera_update=CameraUpdate(video_info=video_info)
                    )
                    
                    print(f"✅ Video info retrieved and saved for camera {db_camera.id}")
                else:
                    response["video_validation"]["errors"].append(f"Failed to get video info: {video_info_response.status_code}")
                    print(f"❌ Failed to get video info for camera {db_camera.id}")
                    
            except httpx.TimeoutException:
                response["video_validation"]["errors"].append("Video info request timed out")
                print(f"⏰ Video info request timed out for camera {db_camera.id}")
            except Exception as e:
                response["video_validation"]["errors"].append(f"Video info error: {str(e)}")
                print(f"❌ Video info error for camera {db_camera.id}: {str(e)}")
                
        except Exception as e:
            response["video_validation"]["errors"].append(f"Video validation failed: {str(e)}")
            print(f"❌ Video validation failed for camera {db_camera.id}: {str(e)}")
    
    return response

@router.get("/{camera_id}", response_model=CameraInDB)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific camera by ID
    """
    db_camera = camera_crud.get_camera(db, camera_id=camera_id)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return CameraInDB.model_validate(db_camera)

@router.put("/{camera_id}", response_model=CameraInDB)
def update_camera(
    camera_id: int,
    camera_update: CameraUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a camera
    """
    db_camera = camera_crud.update_camera(db, camera_id=camera_id, camera_update=camera_update)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return CameraInDB.model_validate(db_camera)

@router.delete("/{camera_id}")
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a camera
    """
    success = camera_crud.delete_camera(db, camera_id=camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": "Camera deleted successfully"}

@router.post("/{camera_id}/validate-video/")
async def validate_camera_video(
    camera_id: int,
    db: Session = Depends(get_db),
    client: httpx.AsyncClient = Depends(get_video_pipeline_client)
):
    """
    Manually validate video stream for an existing camera
    """
    # Get the camera from database
    db_camera = camera_crud.get_camera(db, camera_id=camera_id)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Initialize response
    response = {
        "camera_id": camera_id,
        "rtsp_url": db_camera.rtsp_url,
        "validation": {
            "status": "pending",
            "video_info": None,
            "decode_status": None,
            "errors": []
        }
    }
    
    # Validate the video stream if RTSP URL is provided
    if db_camera.rtsp_url:
        try:
            print(f"🔍 Validating video stream for camera {camera_id}: {db_camera.rtsp_url}")
            
            # Step 1: Get video information
            try:
                video_info_data = {"url": db_camera.rtsp_url}
                video_info_response = await client.post(
                    f"{VIDEO_PIPELINE_URL}/api/v1/video-pipeline/video-info-url/",
                    data=video_info_data,
                    timeout=30.0
                )
                
                if video_info_response.status_code == 200:
                    video_info = video_info_response.json()
                    response["validation"]["video_info"] = video_info
                    response["validation"]["status"] = "validated"
                    print(f"✅ Video info retrieved for camera {camera_id}")
                else:
                    response["validation"]["errors"].append(f"Failed to get video info: {video_info_response.status_code}")
                    print(f"❌ Failed to get video info for camera {camera_id}")
                    
            except httpx.TimeoutException:
                response["validation"]["errors"].append("Video info request timed out")
                print(f"⏰ Video info request timed out for camera {camera_id}")
            except Exception as e:
                response["validation"]["errors"].append(f"Video info error: {str(e)}")
                print(f"❌ Video info error for camera {camera_id}: {str(e)}")
            
            # Step 2: Start video decoding (extract frames)
            try:
                decode_data = {
                    "url": db_camera.rtsp_url,
                    "fps": 1,  # Extract 1 frame per second for validation
                    "force_format": "none"  # Use software decoding for validation
                }
                decode_response = await client.post(
                    f"{VIDEO_PIPELINE_URL}/api/v1/video-pipeline/decode/",
                    data=decode_data,
                    timeout=60.0  # Longer timeout for decoding
                )
                
                if decode_response.status_code == 200:
                    decode_result = decode_response.json()
                    response["validation"]["decode_status"] = decode_result
                    response["validation"]["status"] = "decoding_started"
                    print(f"✅ Video decoding started for camera {camera_id}")
                else:
                    response["validation"]["errors"].append(f"Failed to start decoding: {decode_response.status_code}")
                    print(f"❌ Failed to start decoding for camera {camera_id}")
                    
            except httpx.TimeoutException:
                response["validation"]["errors"].append("Decode request timed out")
                print(f"⏰ Decode request timed out for camera {camera_id}")
            except Exception as e:
                response["validation"]["errors"].append(f"Decode error: {str(e)}")
                print(f"❌ Decode error for camera {camera_id}: {str(e)}")
                
        except Exception as e:
            response["validation"]["errors"].append(f"Video validation failed: {str(e)}")
            print(f"❌ Video validation failed for camera {camera_id}: {str(e)}")
    else:
        response["validation"]["errors"].append("No RTSP URL provided for camera")
    
    return response

@router.post("/{camera_id}/activate/")
async def activate_camera(
    camera_id: int,
    fps: Optional[int] = 1,
    force_format: Optional[str] = None,
    db: Session = Depends(get_db),
    client: httpx.AsyncClient = Depends(get_video_pipeline_client)
):
    """
    Activate a camera by starting video decoding
    """
    # Get the camera from database
    db_camera = camera_crud.get_camera(db, camera_id=camera_id)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    if not db_camera.rtsp_url:
        raise HTTPException(status_code=400, detail="Camera has no RTSP URL")
    
    # Initialize response
    response = {
        "camera_id": camera_id,
        "rtsp_url": db_camera.rtsp_url,
        "activation": {
            "status": "pending",
            "decode_status": None,
            "errors": []
        }
    }
    
    try:
        print(f"🚀 Activating camera {camera_id}: {db_camera.rtsp_url}")
        
        # Start video decoding
        decode_data = {
            "url": db_camera.rtsp_url,
            "fps": fps,
            "force_format": force_format or "none"
        }
        decode_response = await client.post(
            f"{VIDEO_PIPELINE_URL}/api/v1/video-pipeline/decode/",
            data=decode_data,
            timeout=60.0  # Longer timeout for decoding
        )
        
        if decode_response.status_code == 200:
            decode_result = decode_response.json()
            response["activation"]["decode_status"] = decode_result
            response["activation"]["status"] = "activated"
            
            # Update camera status to active
            camera_crud.update_camera(
                db=db, 
                camera_id=camera_id, 
                camera_update=CameraUpdate(is_active=True)
            )
            
            print(f"✅ Camera {camera_id} activated successfully")
        else:
            response["activation"]["errors"].append(f"Failed to start decoding: {decode_response.status_code}")
            print(f"❌ Failed to activate camera {camera_id}")
            
    except httpx.TimeoutException:
        response["activation"]["errors"].append("Activation request timed out")
        print(f"⏰ Activation request timed out for camera {camera_id}")
    except Exception as e:
        response["activation"]["errors"].append(f"Activation error: {str(e)}")
        print(f"❌ Activation error for camera {camera_id}: {str(e)}")
    
    return response

# @router.put("/{camera_id}/analytics", response_model=CameraRead)
# def set_camera_analytics(camera_id: int, analytics_config: dict, db: Session = Depends(get_db)):
#     return crud_camera.update_camera_analytics(db, camera_id, analytics_config)
