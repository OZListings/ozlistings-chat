from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import logging
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
    user_id: str
    message: str

    class Config:
        min_anystr_length = 1
        max_anystr_length = 1000

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, chat_req: ChatRequest):
    try:
        logger.info(f"Chat request received - user_id: {chat_req.user_id}, message: {chat_req.message[:100]}...")
        response_text = await get_response_from_gemini(chat_req.user_id, chat_req.message)
        await update_profile(chat_req.user_id, chat_req.message)
        return {"response": response_text}
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

class ProfileUpdateRequest(BaseModel):
    user_id: str
    message: str

    class Config:
        min_anystr_length = 1
        max_anystr_length = 1000

class ProfileUpdateResponse(BaseModel):
    profile: dict

@app.post("/profile", response_model=ProfileUpdateResponse)
@limiter.limit("10/minute")
async def profile_endpoint(request: Request, profile_req: ProfileUpdateRequest):
    try:
        logger.info(f"Profile request received - user_id: {profile_req.user_id}, message: {profile_req.message[:100]}...")
        updated_profile = await update_profile(profile_req.user_id, profile_req.message)
        return {"profile": updated_profile}
    except Exception as e:
        logger.error(f"Profile endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/profile/{user_id}")
@limiter.limit("30/minute")
def get_profile_endpoint(request: Request, user_id: str):
    try:
        profile = get_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")