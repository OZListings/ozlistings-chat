from json import load
from sqlalchemy import create_engine, Column, String, Boolean, Integer, JSON, DateTime, Text, Float, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid

# Adding env variables for database connection
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

print(f"Constructed DATABASE_URL: postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}") 

# Updated for Supabase connection with SSL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}?sslmode=require"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    # Updated to match Supabase table structure exactly
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, unique=True, index=True)  # This will be the Supabase user UUID
    accredited_investor = Column(Boolean, nullable=True)
    check_size = Column(Text, nullable=True)
    geographical_zone = Column(Text, nullable=True)
    real_estate_investment_experience = Column(Float, nullable=True)
    investment_timeline = Column(Text, nullable=True)
    investment_priorities = Column(ARRAY(Text), nullable=True)
    deal_readiness = Column(Text, nullable=True)
    preferred_asset_types = Column(ARRAY(Text), nullable=True)
    needs_team_contact = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    print("--- init_db() function called ---")
    try:
        # Don't create tables since they already exist in Supabase
        # Base.metadata.create_all(bind=engine)
        print("--- Using existing Supabase tables ---")
    except Exception as e:
        print(f"Error in init_db(): {e}")
    print("--- init_db() function finished ---")

# Updated utility functions to work with individual columns
def get_user_profile(user_id: str):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            # Convert SQLAlchemy object to dict for compatibility with existing code
            return {
                'accredited_investor': profile.accredited_investor,
                'check_size': profile.check_size,
                'geographical_zone': profile.geographical_zone,
                'real_estate_investment_experience': profile.real_estate_investment_experience,
                'investment_timeline': profile.investment_timeline,
                'investment_priorities': profile.investment_priorities,
                'deal_readiness': profile.deal_readiness,
                'preferred_asset_types': profile.preferred_asset_types,
                'needs_team_contact': profile.needs_team_contact
            }
        return None
    finally:
        db.close()

def update_user_profile(user_id: str, profile_data: dict):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            # Update existing profile
            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            profile = UserProfile(
                user_id=user_id,
                accredited_investor=profile_data.get('accredited_investor'),
                check_size=profile_data.get('check_size'),
                geographical_zone=profile_data.get('geographical_zone'),
                real_estate_investment_experience=profile_data.get('real_estate_investment_experience'),
                investment_timeline=profile_data.get('investment_timeline'),
                investment_priorities=profile_data.get('investment_priorities'),
                deal_readiness=profile_data.get('deal_readiness'),
                preferred_asset_types=profile_data.get('preferred_asset_types'),
                needs_team_contact=profile_data.get('needs_team_contact')
            )
            db.add(profile)
        db.commit()
    finally:
        db.close()

# **Enhanced Test Function to Check Database Connection**
def test_db_connection():
    print("--- Testing Supabase Database Connection ---")
    print(f"DATABASE_URL: {DATABASE_URL}")
    try:
        engine.connect()
        print("Supabase database connection successful!")
        print("Using existing tables.")
        return True
    except Exception as e:
        print(f"Supabase database connection failed!\nError: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()