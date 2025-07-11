from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Float, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}?sslmode=require"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, unique=True, index=True)
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
    try:
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

def get_user_profile(user_id: str):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
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
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None
    finally:
        db.close()

def update_user_profile(user_id: str, profile_data: dict):
    db = SessionLocal()
    try:
        if 'preferred_asset_types' in profile_data:
            value = profile_data['preferred_asset_types']
            if isinstance(value, str):
                profile_data['preferred_asset_types'] = [item.strip() for item in value.split(',')]
            elif not isinstance(value, list):
                profile_data['preferred_asset_types'] = [str(value)] if value else []
        
        if 'investment_priorities' in profile_data:
            value = profile_data['investment_priorities']
            if isinstance(value, str):
                profile_data['investment_priorities'] = [item.strip() for item in value.split(',')]
            elif not isinstance(value, list):
                profile_data['investment_priorities'] = [str(value)] if value else []

        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
        else:
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
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.rollback()
    finally:
        db.close()