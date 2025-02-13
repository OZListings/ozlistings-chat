from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import stub functions from our modules
from rag import get_response_from_rag
from profiling import update_profile

app = FastAPI(title="Ozlistings AI Agent")

# Configure CORS to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your actual domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and response models for the /chat endpoint
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

# Request and response models for the /profile endpoint
class ProfileUpdateRequest(BaseModel):
    user_id: str
    message: str

class ProfileUpdateResponse(BaseModel):
    profile: dict

@app.get("/")
def read_root():
    return {"message": "Welcome to Ozlistings AI Agent!"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(chat_req: ChatRequest):
    """
    Endpoint to handle chat messages.
    Calls the RAG pipeline to generate a response.
    """
    try:
        response_text = get_response_from_rag(chat_req.user_id, chat_req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"response": response_text}

@app.post("/profile", response_model=ProfileUpdateResponse)
def profile_endpoint(profile_req: ProfileUpdateRequest):
    """
    Endpoint to update and retrieve the user's profile.
    """
    try:
        updated_profile = update_profile(profile_req.user_id, profile_req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"profile": updated_profile}