"""
ML Service for Playlist Recommendations
Provides machine learning-based playlist recommendations using collaborative filtering
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Playlist Recommendation ML Service", version="1.0.0")

# Sample data for demonstration
# In production, this would come from a database
USERS_DATA = {
    "user1": {"playlists": [1, 2, 3], "genres": ["rock", "pop", "indie"]},
    "user2": {"playlists": [2, 3, 4], "genres": ["pop", "indie", "electronic"]},
    "user3": {"playlists": [1, 4, 5], "genres": ["rock", "electronic", "jazz"]},
    "user4": {"playlists": [3, 5, 6], "genres": ["indie", "jazz", "classical"]},
}

PLAYLISTS_DATA = {
    1: {"name": "Rock Classics", "genre": "rock", "tracks": 50, "popularity": 0.9},
    2: {"name": "Pop Hits 2024", "genre": "pop", "tracks": 40, "popularity": 0.95},
    3: {"name": "Indie Vibes", "genre": "indie", "tracks": 35, "popularity": 0.85},
    4: {"name": "Electronic Dreams", "genre": "electronic", "tracks": 45, "popularity": 0.88},
    5: {"name": "Jazz Evenings", "genre": "jazz", "tracks": 30, "popularity": 0.82},
    6: {"name": "Classical Masterpieces", "genre": "classical", "tracks": 60, "popularity": 0.87},
}


class RecommendationRequest(BaseModel):
    user_id: str
    num_recommendations: int = 3


class RecommendationResponse(BaseModel):
    user_id: str
    recommendations: List[Dict]
    algorithm: str


class HealthResponse(BaseModel):
    status: str
    service: str


def create_user_item_matrix():
    """Create user-item interaction matrix for collaborative filtering"""
    users = list(USERS_DATA.keys())
    playlists = list(PLAYLISTS_DATA.keys())
    
    matrix = np.zeros((len(users), len(playlists)))
    
    for i, user in enumerate(users):
        user_playlists = USERS_DATA[user]["playlists"]
        for playlist_id in user_playlists:
            j = playlists.index(playlist_id)
            matrix[i][j] = 1
    
    return matrix, users, playlists


def get_recommendations_collaborative(user_id: str, num_recommendations: int = 3):
    """Generate recommendations using collaborative filtering"""
    matrix, users, playlists = create_user_item_matrix()
    
    if user_id not in users:
        # For new users, return most popular playlists
        sorted_playlists = sorted(
            PLAYLISTS_DATA.items(),
            key=lambda x: x[1]["popularity"],
            reverse=True
        )
        return [
            {
                "playlist_id": pid,
                "name": pdata["name"],
                "genre": pdata["genre"],
                "score": pdata["popularity"],
            }
            for pid, pdata in sorted_playlists[:num_recommendations]
        ]
    
    # Calculate user similarity
    user_idx = users.index(user_id)
    user_similarities = cosine_similarity(matrix)[user_idx]
    
    # Get weighted recommendations
    weighted_ratings = np.zeros(len(playlists))
    for i, similarity in enumerate(user_similarities):
        if i != user_idx:
            weighted_ratings += similarity * matrix[i]
    
    # Filter out already listened playlists
    user_playlists = USERS_DATA[user_id]["playlists"]
    for playlist_id in user_playlists:
        playlist_idx = playlists.index(playlist_id)
        weighted_ratings[playlist_idx] = 0
    
    # Get top recommendations
    top_indices = np.argsort(weighted_ratings)[::-1][:num_recommendations]
    
    recommendations = []
    for idx in top_indices:
        playlist_id = playlists[idx]
        playlist_data = PLAYLISTS_DATA[playlist_id]
        recommendations.append({
            "playlist_id": playlist_id,
            "name": playlist_data["name"],
            "genre": playlist_data["genre"],
            "score": float(weighted_ratings[idx]),
        })
    
    return recommendations


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ML Recommendation Service"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ML Recommendation Service"}


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    """
    Generate playlist recommendations for a user
    """
    try:
        logger.info(f"Generating recommendations for user: {request.user_id}")
        
        recommendations = get_recommendations_collaborative(
            request.user_id,
            request.num_recommendations
        )
        
        return {
            "user_id": request.user_id,
            "recommendations": recommendations,
            "algorithm": "collaborative_filtering"
        }
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/playlists")
async def get_playlists():
    """Get all available playlists"""
    return {
        "playlists": [
            {"id": pid, **pdata}
            for pid, pdata in PLAYLISTS_DATA.items()
        ]
    }


@app.get("/users")
async def get_users():
    """Get all users (for testing)"""
    return {"users": list(USERS_DATA.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
