#!/usr/bin/env python3
"""
Database migration script to add message_count and last_session_at fields
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
    """Run the database migration to add message counting fields"""
    print("🚀 Starting database migration for message counting...")
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # 1. Add message_count column
                print("📝 Adding message_count column...")
                conn.execute(text("""
                    ALTER TABLE ozzie_user_profiles 
                    ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0;
                """))
                
                # 2. Add last_session_at column
                print("📝 Adding last_session_at column...")
                conn.execute(text("""
                    ALTER TABLE ozzie_user_profiles 
                    ADD COLUMN IF NOT EXISTS last_session_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                """))
                
                # 3. Set default values for existing rows
                print("📝 Setting default values for existing rows...")
                conn.execute(text("""
                    UPDATE ozzie_user_profiles 
                    SET message_count = 0 
                    WHERE message_count IS NULL;
                """))
                
                conn.execute(text("""
                    UPDATE ozzie_user_profiles 
                    SET last_session_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
                    WHERE last_session_at IS NULL;
                """))
                
                # 4. Reset any profiles that have need_team_contact=True but message_count=0
                # This fixes the issue where need_team_contact was set immediately
                print("📝 Resetting need_team_contact for profiles with 0 message count...")
                conn.execute(text("""
                    UPDATE ozzie_user_profiles 
                    SET need_team_contact = FALSE 
                    WHERE message_count = 0 AND need_team_contact = TRUE;
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

def verify_migration():
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    try:
        with engine.connect() as conn:
            # Check that new columns exist
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'ozzie_user_profiles' 
                AND column_name IN ('message_count', 'last_session_at')
                ORDER BY column_name;
            """))
            
            columns = result.fetchall()
            
            if len(columns) == 2:
                print("✅ New columns added successfully:")
                for col in columns:
                    print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}) default: {col[3]}")
            else:
                print(f"❌ Expected 2 new columns, found {len(columns)}")
                return False
            
            # Check existing data
            count_result = conn.execute(text("""
                SELECT COUNT(*) as total_profiles,
                       COUNT(CASE WHEN message_count IS NOT NULL THEN 1 END) as with_message_count,
                       COUNT(CASE WHEN last_session_at IS NOT NULL THEN 1 END) as with_session_time
                FROM ozzie_user_profiles;
            """))
            
            stats = count_result.fetchone()
            print(f"\n📊 Profile statistics:")
            print(f"  - Total profiles: {stats[0]}")
            print(f"  - Profiles with message_count: {stats[1]}")
            print(f"  - Profiles with last_session_at: {stats[2]}")
            
            if stats[0] == stats[1] == stats[2]:
                print("✅ All profiles have the new fields!")
            else:
                print("⚠️  Some profiles missing new field values")
            
            return True
                
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    print("🗃️  Database Migration: Add Message Counting Fields")
    print("=" * 60)
    
    run_migration()
    verify_migration()
    
    print("\n✅ Migration complete! The system now supports:")
    print("  - Proper message counting per user session")
    print("  - Session timeout (30 minutes of inactivity)")
    print("  - Calendar auto-trigger after 4 messages")
    print("  - Fixed need_team_contact logic")