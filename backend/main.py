from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from rag import get_response_from_gemini
from profiling import update_profile, get_profile
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run before the app starts
    print("--- Running database initialization (lifespan startup) ---")
    init_db()
    print("--- Database initialization complete (lifespan startup) ---")
    yield
    # Shutdown: Run after the app finishes (optional)
    print("--- Lifespan shutdown event (optional) ---")

app = FastAPI(lifespan=lifespan, title="Ozlistings AI Agent")

frontend_url = "https://ozlistings-chat-frontend-1098767556937.us-central1.run.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
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

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_req: ChatRequest):
    try:
        response_text = await get_response_from_gemini(chat_req.user_id, chat_req.message)
        await update_profile(chat_req.user_id, chat_req.message)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProfileUpdateRequest(BaseModel):
    user_id: str
    message: str

class ProfileUpdateResponse(BaseModel):
    profile: dict

@app.post("/profile", response_model=ProfileUpdateResponse)
async def profile_endpoint(profile_req: ProfileUpdateRequest):
    try:
        updated_profile = await update_profile(profile_req.user_id, profile_req.message)
        return {"profile": updated_profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profile/{user_id}")
def get_profile_endpoint(user_id: str):
    profile = get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile