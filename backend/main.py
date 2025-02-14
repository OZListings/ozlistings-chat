from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import get_response_from_gemini # Import rag function
from profiling import update_profile, get_profile # Import profiling functions

app = FastAPI(title="Ozlistings AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

class ProfileUpdateRequest(BaseModel):
    user_id: str
    message: str

class ProfileUpdateResponse(BaseModel):
    profile: dict

@app.get("/")
def read_root():
    return {"message": "Welcome to Ozlistings AI Agent!"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_req: ChatRequest):
    try:
        response_text = await get_response_from_gemini(chat_req.user_id, chat_req.message) # Use rag function
        await update_profile(chat_req.user_id, chat_req.message) # Update profile on every chat message
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profile", response_model=ProfileUpdateResponse)
async def profile_endpoint(profile_req: ProfileUpdateRequest):
    try:
        updated_profile = await update_profile(profile_req.user_id, profile_req.message) # Use profiling function
        return {"profile": updated_profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profile/{user_id}")
def get_profile_endpoint(user_id: str):
    profile = get_profile(user_id) # Use profiling function
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile