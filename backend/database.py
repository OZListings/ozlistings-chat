from json import load
from sqlalchemy import create_engine, Column, String, Boolean, Integer, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id = Column(String, primary_key=True, index=True)
    profile_data = Column(JSON)

class ChatLog(Base):
    __tablename__ = "chat_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    sender = Column(String)  # 'user' or 'agent'
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

# Utility functions for profile handling
def get_user_profile(user_id: str):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        return profile.profile_data if profile else None
    finally:
        db.close()

def update_user_profile(user_id: str, profile_data: dict):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            profile.profile_data = profile_data
        else:
            profile = UserProfile(user_id=user_id, profile_data=profile_data)
            db.add(profile)
        db.commit()
    finally:
        db.close()

# Utility function for chat log persistence
def add_chat_log(user_id: str, sender: str, message: str):
    db = SessionLocal()
    try:
        chat_log = ChatLog(user_id=user_id, sender=sender, message=message)
        db.add(chat_log)
        db.commit()
    finally:
        db.close()

# **Enhanced Test Function to Check Database Connection**
def test_db_connection():
    print("--- Testing Database Connection ---")
    print(f"DATABASE_URL: {DATABASE_URL}") # Print the constructed DATABASE_URL for debugging
    try:
        engine.connect() # Try to establish a connection
        print("Database connection successful!")
        init_db() # Initialize tables (if not already created)
        print("Tables initialized (if needed).")
        return True
    except Exception as e:
        print(f"Database connection failed!\nError: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()