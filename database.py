# database.py

from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Float, Integer, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid
import logging
import enum

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

# Enums for strict validation
class UserRole(enum.Enum):
    DEVELOPER = "Developer"
    INVESTOR = "Investor"

class CapGainTime(enum.Enum):
    LAST_180_DAYS = "Last 180 days"
    MORE_THAN_180_DAYS = "More than 180 days AGO"
    INCOMING = "Upcoming"

# US State codes for validation
US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
]

class UserProfile(Base):
    __tablename__ = "ozzie_user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), unique=True, index=True)
    
    # Core fields
    role = Column(SQLEnum(UserRole, name="userrole"), nullable=True)
    
    # Investor-specific fields
    cap_gain_or_not = Column(Boolean, nullable=True)
    size_of_cap_gain = Column(Numeric, nullable=True) # Changed from String to Numeric
    time_of_cap_gain = Column(SQLEnum(CapGainTime, name="capgaintime"), nullable=True)
    geographical_zone_of_investment = Column(String, nullable=True)
    
    # Developer-specific fields
    location_of_development = Column(Text, nullable=True)  # Address or coordinates
    
    # Common fields
    need_team_contact = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

def validate_state_code(state_code: str) -> bool:
    """Validate US state code"""
    return state_code.upper() in US_STATES

def format_currency(value: str) -> str:
    """Format currency value to standard format (e.g., 100,000)"""
    try:
        # Remove any non-numeric characters
        cleaned = ''.join(filter(str.isdigit, value))
        if cleaned:
            # Format with commas
            return f"{int(cleaned):,}"
        return None
    except:
        return None

def get_user_profile(user_id: uuid.UUID):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if profile:
            return {
                'id': str(profile.id) if profile.id else None,
                'user_id': str(profile.user_id) if profile.user_id else None,
                'role': profile.role.value if profile.role else None,
                'cap_gain_or_not': profile.cap_gain_or_not,
                'size_of_cap_gain': str(profile.size_of_cap_gain) if profile.size_of_cap_gain is not None else None,
                'time_of_cap_gain': profile.time_of_cap_gain.value if profile.time_of_cap_gain else None,
                'geographical_zone_of_investment': profile.geographical_zone_of_investment,
                'location_of_development': profile.location_of_development,
                'need_team_contact': profile.need_team_contact,
                'created_at': profile.created_at.isoformat() if profile.created_at else None,
                'updated_at': profile.updated_at.isoformat() if profile.updated_at else None
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None
    finally:
        db.close()

def increment_message_count(user_id: uuid.UUID):
    """Increment message count and update last session time"""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if profile:
            # For now, just update the need_team_contact flag after a few interactions
            # Since we don't have message_count in the current schema
            profile.need_team_contact = True
            profile.updated_at = datetime.utcnow()
            
            db.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error incrementing message count: {e}")
        return False
    finally:
        db.close()

def update_user_profile(user_id: uuid.UUID, profile_data: dict):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        # Validate and clean data based on role
        if 'role' in profile_data and profile_data['role']:
            try:
                profile_data['role'] = UserRole(profile_data['role'])
            except ValueError:
                logger.error(f"Invalid role: {profile_data['role']}")
                del profile_data['role']
        
        # Handle investor-specific fields
        if profile and profile.role == UserRole.INVESTOR or (not profile and profile_data.get('role') == 'Investor'):
            if 'geographical_zone_of_investment' in profile_data:
                state = profile_data['geographical_zone_of_investment']
                if state and not validate_state_code(state):
                    logger.error(f"Invalid state code: {state}")
                    del profile_data['geographical_zone_of_investment']
                else:
                    profile_data['geographical_zone_of_investment'] = state.upper()
            
            if 'size_of_cap_gain' in profile_data and profile_data['size_of_cap_gain'] is not None:
                # Convert string to numeric for database
                try:
                    # Remove commas and convert to float
                    value_str = str(profile_data['size_of_cap_gain']).replace(',', '')
                    numeric_value = float(value_str)
                    profile_data['size_of_cap_gain'] = numeric_value
                except (ValueError, TypeError):
                    logger.error(f"Invalid size_of_cap_gain value: {profile_data['size_of_cap_gain']}")
                    del profile_data['size_of_cap_gain']
            
            if 'time_of_cap_gain' in profile_data:
                try:
                    profile_data['time_of_cap_gain'] = CapGainTime(profile_data['time_of_cap_gain'])
                except ValueError:
                    logger.error(f"Invalid cap gain time: {profile_data['time_of_cap_gain']}")
                    del profile_data['time_of_cap_gain']
        
        # Handle role-specific constraints
        current_role = profile.role if profile else None
        new_role = profile_data.get('role')
        role_to_check = new_role if new_role else current_role
        
        if role_to_check:
            if role_to_check == UserRole.DEVELOPER:
                # For developers, ensure location_of_development is set
                if 'location_of_development' not in profile_data or not profile_data.get('location_of_development'):
                    profile_data['location_of_development'] = 'Location to be determined'
                # Clear investor-specific fields
                profile_data.update({
                    'cap_gain_or_not': None,
                    'size_of_cap_gain': None,
                    'time_of_cap_gain': None,
                    'geographical_zone_of_investment': None
                })
            elif role_to_check == UserRole.INVESTOR:
                # For investors, ensure cap_gain_or_not is set and location is NULL
                if 'cap_gain_or_not' not in profile_data:
                    profile_data['cap_gain_or_not'] = False
                # Clear developer-specific fields - this is required by constraint
                profile_data['location_of_development'] = None
        else:
            # If no role is set, ensure location is NULL to satisfy constraint
            profile_data['location_of_development'] = None
        
        if profile:
            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
        else:
            # Create new profile, ensuring UUID is passed correctly
            profile_data['user_id'] = user_id
            profile = UserProfile(
                **profile_data
            )
            db.add(profile)
        
        db.commit()
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.rollback()
    finally:
        db.close()

def migrate_existing_profiles():
    """Migrate existing profiles to new schema"""
    db = SessionLocal()
    try:
        # Get all existing profiles
        profiles = db.query(UserProfile).all()
        
        for profile in profiles:
            # Attempt to infer role from existing data
            if hasattr(profile, 'preferred_asset_types') and profile.preferred_asset_types:
                # If they have asset preferences, likely an investor
                profile.role = UserRole.INVESTOR
            elif hasattr(profile, 'deal_readiness') and profile.deal_readiness:
                # Could be either, default to investor
                profile.role = UserRole.INVESTOR
            
            # Reset message count
            profile.message_count = 0
            profile.needs_team_contact = False
            
            # Clear old fields by setting to None (you might need to drop columns in production)
        
        db.commit()
        logger.info(f"Migrated {len(profiles)} profiles to new schema")
    except Exception as e:
        logger.error(f"Error migrating profiles: {e}")
        db.rollback()
    finally:
        db.close()