from sqlalchemy import create_engine, Column, String, Boolean, Integer, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DB_USER = os.environ.get("DATABASE_USER")
DB_PASSWORD = os.environ.get("DATABASE_USER_PASSWORD")
DB_HOST = os.environ.get("CLOUD_SQL_PUBLIC_IP")
DB_NAME = os.environ.get("DATABASE_ADMIN_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)
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

# Test function to check database connection and table creation
def test_db_connection():
    try:
        init_db() # Initialize tables
        db = SessionLocal()
        db.execute("SELECT 1") # Simple query to test connection
        print("Database connection successful and tables initialized.")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()