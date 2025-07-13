#!/usr/bin/env python3
"""
Database migration script to fix schema mismatches
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    print("❌ Error: Database environment variables not set")
    print("Please set DB_USER, DB_PASSWORD, DB_HOST, and DB_NAME in your .env file")
    sys.exit(1)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}?sslmode=require"
engine = create_engine(DATABASE_URL)

def run_migration():
    """Run the database migration"""
    print("🚀 Starting database migration...")
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # 1. Add missing email column
                print("📝 Adding email column...")
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE;
                """))
                
                # 2. Create index on email column
                print("📝 Creating email index...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_user_profiles_email 
                    ON user_profiles (email);
                """))
                
                # 3. Change user_id from UUID to VARCHAR
                print("📝 Converting user_id to VARCHAR...")
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    ALTER COLUMN user_id TYPE VARCHAR USING user_id::VARCHAR;
                """))
                
                # 4. Fix column name: geographical_zone_of_investment -> geographical_zone_of_investor
                print("📝 Renaming geographical_zone_of_investment...")
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    RENAME COLUMN geographical_zone_of_investment TO geographical_zone_of_investor;
                """))
                
                # 5. Fix column name: need_team_contact -> needs_team_contact
                print("📝 Renaming need_team_contact...")
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    RENAME COLUMN need_team_contact TO needs_team_contact;
                """))
                
                # 6. Add missing message_count column
                print("📝 Adding message_count column...")
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
                """))
                
                # 7. Add missing last_session_at column
                print("📝 Adding last_session_at column...")
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    ADD COLUMN IF NOT EXISTS last_session_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """))
                
                # 8. Change size_of_cap_gain from NUMERIC to VARCHAR
                print("📝 Converting size_of_cap_gain to VARCHAR...")
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    ALTER COLUMN size_of_cap_gain TYPE VARCHAR USING size_of_cap_gain::VARCHAR;
                """))
                
                # 9. Update geographical_zone_of_investor to be VARCHAR(2)
                print("📝 Setting geographical_zone_of_investor to VARCHAR(2)...")
                conn.execute(text("""
                    ALTER TABLE user_profiles 
                    ALTER COLUMN geographical_zone_of_investor TYPE VARCHAR(2);
                """))
                
                # 10. Set default values for existing rows
                print("📝 Setting default values for existing rows...")
                conn.execute(text("""
                    UPDATE user_profiles 
                    SET message_count = 0 
                    WHERE message_count IS NULL;
                """))
                
                conn.execute(text("""
                    UPDATE user_profiles 
                    SET last_session_at = CURRENT_TIMESTAMP 
                    WHERE last_session_at IS NULL;
                """))
                
                conn.execute(text("""
                    UPDATE user_profiles 
                    SET needs_team_contact = false 
                    WHERE needs_team_contact IS NULL;
                """))
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)

def verify_schema():
    """Verify the migration was successful"""
    print("\n🔍 Verifying schema...")
    
    try:
        with engine.connect() as conn:
            # Get column information
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'user_profiles' 
                ORDER BY ordinal_position;
            """))
            
            columns = result.fetchall()
            
            print("\n📊 Current database schema:")
            for col in columns:
                print(f"  {col[0]}: {col[1]} (nullable: {col[2]}) default: {col[3]}")
                
            # Check for required columns
            required_columns = [
                'id', 'user_id', 'email', 'role', 'cap_gain_or_not',
                'size_of_cap_gain', 'time_of_cap_gain', 'geographical_zone_of_investor',
                'location_of_development', 'needs_team_contact', 'message_count',
                'created_at', 'updated_at', 'last_session_at'
            ]
            
            existing_columns = [col[0] for col in columns]
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                print(f"\n❌ Missing columns: {missing_columns}")
            else:
                print(f"\n✅ All required columns present!")
                
    except Exception as e:
        print(f"❌ Schema verification error: {e}")

if __name__ == "__main__":
    run_migration()
    verify_schema() 