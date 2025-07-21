# main.py - Updated without breaking existing frontend

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, validator
from contextlib import asynccontextmanager
import logging
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from rag import get_response_from_gemini
from profiling import update_profile, get_profile
from database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate required environment variables
required_env_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME", "GEMINI_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization complete.")
    yield

app = FastAPI(lifespan=lifespan, title="Ozlistings AI Agent")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Ozlistings AI Agent!"}

class ChatRequest(BaseModel):
    user_id: uuid.UUID
    message: str

    @validator('user_id', pre=True)
    def validate_user_id(cls, v):
        try:
            return uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid user_id format')

    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message too long (max 1000 characters)')
        return v.strip()

# UNCHANGED: Keep the same response model to avoid breaking frontend
class ChatResponse(BaseModel):
    response: str
    profile_updated: bool = False
    actions_triggered: Optional[list] = None

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, chat_req: ChatRequest):
    try:
        logger.info(f"Chat request received - user_id: {chat_req.user_id}, message: {chat_req.message[:100]}...")
        
        # This call now returns enhanced responses with better calendar formatting
        result = await get_response_from_gemini(chat_req.user_id, chat_req.message)
        
        response_text = result["response_text"]
        profile_result = result["profile_result"]
        
        # Check for security flags
        if profile_result.get('status') == 'security_warning':
            logger.warning(f"Security warning for user {chat_req.user_id}")
            # Continue with response but log the attempt
        
        # Return SAME structure as before - no breaking changes
        return {
            "response": response_text,
            "profile_updated": bool(profile_result.get('updates')),
            "actions_triggered": profile_result.get('actions', [])
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# UNCHANGED: All other endpoints remain exactly the same
class ProfileUpdateRequest(BaseModel):
    user_id: uuid.UUID
    message: str

    @validator('user_id', pre=True)
    def validate_user_id(cls, v):
        try:
            return uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid user_id format')

    @validator('message')
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        return v.strip()

class ProfileUpdateResponse(BaseModel):
    profile: Dict[str, Any]
    status: str
    message_count: Optional[int] = None

@app.post("/profile", response_model=ProfileUpdateResponse)
@limiter.limit("10/minute")
async def profile_endpoint(request: Request, profile_req: ProfileUpdateRequest):
    try:
        logger.info(f"Profile request received - user_id: {profile_req.user_id}, message: {profile_req.message[:100]}...")
        
        # Update profile based on message
        result = await update_profile(profile_req.user_id, profile_req.message)
        
        # Get updated profile
        updated_profile = get_profile(profile_req.user_id)
        
        return {
            "profile": updated_profile,
            "status": result.get('status', 'success'),
            "message_count": result.get('message_count')
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Profile endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/profile/{user_id}")
@limiter.limit("30/minute")
def get_profile_endpoint(request: Request, user_id: str):
    try:
        # Validate user_id
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        
        profile = get_profile(user_uuid)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.1"  # Updated version for UX improvements
    }