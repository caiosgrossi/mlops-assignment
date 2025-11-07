"""
Backend API Service
Acts as API Gateway and aggregates data from ML service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Playlist Recommendation Backend API", version="1.0.0")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ML Service URL - can be overridden via environment variable
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://localhost:8000")


class RecommendationRequest(BaseModel):
    user_id: str
    num_recommendations: Optional[int] = 3


class HealthResponse(BaseModel):
    status: str
    service: str
    ml_service_status: Optional[str] = None


async def check_ml_service():
    """Check if ML service is healthy"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ML_SERVICE_URL}/health", timeout=5.0)
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"ML service health check failed: {str(e)}")
        return False


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health status"""
    ml_healthy = await check_ml_service()
    return {
        "status": "healthy",
        "service": "Backend API",
        "ml_service_status": "healthy" if ml_healthy else "unavailable"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    ml_healthy = await check_ml_service()
    return {
        "status": "healthy",
        "service": "Backend API",
        "ml_service_status": "healthy" if ml_healthy else "unavailable"
    }


@app.post("/api/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Get playlist recommendations for a user
    Forwards request to ML service
    """
    try:
        logger.info(f"Fetching recommendations for user: {request.user_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/recommend",
                json={
                    "user_id": request.user_id,
                    "num_recommendations": request.num_recommendations
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="ML service error"
                )
            
            return response.json()
            
    except httpx.RequestError as e:
        logger.error(f"Error connecting to ML service: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="ML service unavailable"
        )
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/playlists")
async def get_playlists():
    """
    Get all available playlists
    Forwards request to ML service
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ML_SERVICE_URL}/playlists",
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="ML service error"
                )
            
            return response.json()
            
    except httpx.RequestError as e:
        logger.error(f"Error connecting to ML service: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="ML service unavailable"
        )
    except Exception as e:
        logger.error(f"Error getting playlists: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users")
async def get_users():
    """
    Get all users (for testing)
    Forwards request to ML service
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ML_SERVICE_URL}/users",
                timeout=10.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="ML service error"
                )
            
            return response.json()
            
    except httpx.RequestError as e:
        logger.error(f"Error connecting to ML service: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="ML service unavailable"
        )
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
