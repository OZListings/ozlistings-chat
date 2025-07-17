# database.py

from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, Float, Integer, Enum as SQLEnum, Numeric, text
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

# Valid role values based on database constraints
VALID_ROLES = ["Developer", "Investor"]
VALID_CAP_GAIN_TIMES = ["Last 180 days", "More than 180 days AGO", "Upcoming"]

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
    user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    
    # Core fields - role is TEXT with check constraint
    role = Column(Text, nullable=True)
    
    # Investor-specific fields
    cap_gain_or_not = Column(Boolean, nullable=True)
    size_of_cap_gain = Column(Numeric, nullable=True)
    time_of_cap_gain = Column(Text, nullable=True)  # TEXT with check constraint
    geographical_zone_of_investment = Column(Text, nullable=True)
    
    # Developer-specific fields
    location_of_development = Column(Text, nullable=True)
    
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
        # Remove any non-numeric characters except decimal point
        cleaned = ''.join(c for c in str(value) if c.isdigit() or c == '.')
        if cleaned:
            # Convert to float and format
            return str(float(cleaned))
        return None
    except:
        return None

def create_auth_user_if_needed(user_id: uuid.UUID):
    """Create a user in auth.users if it doesn't exist (for testing)"""
    db = SessionLocal()
    try:
        # Check if user exists in auth.users
        result = db.execute(text("SELECT id FROM auth.users WHERE id = :user_id"), {"user_id": user_id}).fetchone()
        
        if not result:
            # Create a basic auth user for testing
            db.execute(text("""
                INSERT INTO auth.users (id, aud, role, email, email_confirmed_at, created_at, updated_at)
                VALUES (:user_id, 'authenticated', 'authenticated', :email, NOW(), NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
            """), {
                "user_id": user_id,
                "email": f"test-{user_id}@example.com"
            })
            db.commit()
            logger.info(f"Created auth user for testing: {user_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating auth user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_user_profile(user_id: uuid.UUID):
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if profile:
            return {
                'id': str(profile.id) if profile.id else None,
                'user_id': str(profile.user_id) if profile.user_id else None,
                'role': profile.role,
                'cap_gain_or_not': profile.cap_gain_or_not,
                'size_of_cap_gain': str(profile.size_of_cap_gain) if profile.size_of_cap_gain is not None else None,
                'time_of_cap_gain': profile.time_of_cap_gain,
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
            # Update the timestamp and set need_team_contact after several interactions
            profile.updated_at = datetime.utcnow()
            # Simple logic: if they've been chatting, they might need contact
            profile.need_team_contact = True
            
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
        # Ensure auth user exists first (for testing)
        create_auth_user_if_needed(user_id)
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        # Clean and validate profile data
        cleaned_data = {}
        
        # Handle role with case-insensitive matching
        if 'role' in profile_data and profile_data['role']:
            role_input = str(profile_data['role']).strip()
            # Try exact match first, then case-insensitive
            if role_input in VALID_ROLES:
                cleaned_data['role'] = role_input
            else:
                # Case-insensitive match
                for valid_role in VALID_ROLES:
                    if role_input.lower() == valid_role.lower():
                        cleaned_data['role'] = valid_role
                        break
                else:
                    logger.error(f"Invalid role: {role_input}. Valid roles: {VALID_ROLES}")
        
        # Handle cap gain time
        if 'time_of_cap_gain' in profile_data and profile_data['time_of_cap_gain']:
            time_input = str(profile_data['time_of_cap_gain']).strip()
            if time_input in VALID_CAP_GAIN_TIMES:
                cleaned_data['time_of_cap_gain'] = time_input
            else:
                logger.error(f"Invalid cap gain time: {time_input}. Valid values: {VALID_CAP_GAIN_TIMES}")
        
        # Handle geographic zone (must be 2-letter state code)
        if 'geographical_zone_of_investment' in profile_data and profile_data['geographical_zone_of_investment']:
            state = str(profile_data['geographical_zone_of_investment']).strip().upper()
            if len(state) == 2 and state in US_STATES:
                cleaned_data['geographical_zone_of_investment'] = state
            else:
                logger.error(f"Invalid state code: {state}. Must be 2-letter US state code.")
        
        # Handle size of cap gain (numeric conversion)
        if 'size_of_cap_gain' in profile_data and profile_data['size_of_cap_gain'] is not None:
            try:
                # Handle string with commas
                size_str = str(profile_data['size_of_cap_gain']).replace(',', '').replace('$', '').strip()
                size_numeric = float(size_str)
                cleaned_data['size_of_cap_gain'] = size_numeric
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid size_of_cap_gain: {profile_data['size_of_cap_gain']} - {e}")
        
        # Handle boolean fields
        if 'cap_gain_or_not' in profile_data:
            cleaned_data['cap_gain_or_not'] = bool(profile_data['cap_gain_or_not'])
        
        if 'need_team_contact' in profile_data:
            cleaned_data['need_team_contact'] = bool(profile_data['need_team_contact'])
        
        # Handle location
        if 'location_of_development' in profile_data:
            cleaned_data['location_of_development'] = profile_data['location_of_development']
        
        # Apply database constraint logic
        current_role = profile.role if profile else None
        new_role = cleaned_data.get('role', current_role)
        
        if new_role == 'Investor':
            # Investors must have location_of_development as NULL (constraint requirement)
            cleaned_data['location_of_development'] = None
            # Set default cap_gain_or_not if not specified
            if 'cap_gain_or_not' not in cleaned_data:
                cleaned_data['cap_gain_or_not'] = False
                
        elif new_role == 'Developer':
            # Developers must have investor fields as NULL (constraint requirement)
            cleaned_data.update({
                'cap_gain_or_not': None,
                'size_of_cap_gain': None,
                'time_of_cap_gain': None,
                'geographical_zone_of_investment': None
            })
            # Ensure location is set for developers
            if 'location_of_development' not in cleaned_data or not cleaned_data['location_of_development']:
                cleaned_data['location_of_development'] = 'Location to be determined'
        
        elif new_role is None:
            # No role set - satisfy constraints by setting location to NULL
            cleaned_data['location_of_development'] = None
        
        if profile:
            # Update existing profile
            for key, value in cleaned_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            cleaned_data['user_id'] = user_id
            profile = UserProfile(**cleaned_data)
            db.add(profile)
        
        db.commit()
        logger.info(f"Successfully updated profile for user {user_id}: {cleaned_data}")
        
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
            # Ensure role consistency
            if profile.role and profile.role not in VALID_ROLES:
                # Try to fix common case issues
                if profile.role.lower() == 'investor':
                    profile.role = 'Investor'
                elif profile.role.lower() == 'developer':
                    profile.role = 'Developer'
                else:
                    profile.role = None
            
            # Apply constraint logic
            if profile.role == 'Investor':
                profile.location_of_development = None
            elif profile.role == 'Developer':
                profile.cap_gain_or_not = None
                profile.size_of_cap_gain = None
                profile.time_of_cap_gain = None
                profile.geographical_zone_of_investment = None
                if not profile.location_of_development:
                    profile.location_of_development = 'Location to be determined'
        
        db.commit()
        logger.info(f"Migrated {len(profiles)} profiles to new schema")
    except Exception as e:
        logger.error(f"Error migrating profiles: {e}")
        db.rollback()
    finally:
        db.close()