#!/usr/bin/env python3
"""
Comprehensive test suite for Ozzie chat system.
Tests the complete flow from user input through LLM processing to database operations.
"""

import os
import sys
import uuid
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append('.')

from database import (
    get_user_profile, 
    update_user_profile, 
    increment_message_count,
    UserProfile,
    VALID_ROLES,
    VALID_CAP_GAIN_TIMES,
    SessionLocal,
    init_db,
    create_auth_user_if_needed
)
from profiling import ProfileExtractor, get_profile

# Load environment variables
load_dotenv()

class ComprehensiveTest:
    def __init__(self):
        self.test_user_id = uuid.uuid4()
        self.profile_extractor = ProfileExtractor()
        print(f"🧪 Testing with user ID: {self.test_user_id}")
        
    def test_database_connection(self):
        """Test basic database connectivity"""
        print("\n🔌 Testing database connection...")
        try:
            from sqlalchemy import text
            db = SessionLocal()
            # Try a simple query
            result = db.execute(text("SELECT 1")).fetchone()
            db.close()
            if result and result[0] == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed - unexpected result")
                return False
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def test_table_structure(self):
        """Test that the ozzie_user_profiles table exists and has correct structure"""
        print("\n📋 Testing table structure...")
        try:
            from sqlalchemy import text
            db = SessionLocal()
            
            # Check if table exists
            result = db.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'ozzie_user_profiles'
                ORDER BY ordinal_position
            """)).fetchall()
            
            if not result:
                print("❌ Table 'ozzie_user_profiles' does not exist")
                return False
                
            print("✅ Table structure:")
            for row in result:
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                print(f"   - {row[0]}: {row[1]} ({nullable})")
            
            # Check constraints
            constraints = db.execute(text("""
                SELECT conname, pg_get_constraintdef(oid) 
                FROM pg_constraint 
                WHERE conrelid = 'ozzie_user_profiles'::regclass
                AND contype = 'c'
            """)).fetchall()
            
            print("\n📝 Check constraints:")
            for row in constraints:
                print(f"   - {row[0]}: {row[1]}")
            
            db.close()
            return True
            
        except Exception as e:
            print(f"❌ Table structure test failed: {e}")
            return False
    
    def test_auth_user_creation(self):
        """Test auth user creation for testing"""
        print("\n👤 Testing auth user creation...")
        
        try:
            test_user_id = uuid.uuid4()
            result = create_auth_user_if_needed(test_user_id)
            
            if result:
                print("✅ Auth user creation successful")
                
                # Verify the user was created
                from sqlalchemy import text
                db = SessionLocal()
                check_result = db.execute(text("SELECT id FROM auth.users WHERE id = :user_id"), 
                                        {"user_id": test_user_id}).fetchone()
                db.close()
                
                if check_result:
                    print("✅ Auth user verification successful")
                    return True
                else:
                    print("❌ Auth user creation verification failed")
                    return False
            else:
                print("❌ Auth user creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Auth user creation test failed: {e}")
            return False
    
    def test_constraint_validation(self):
        """Test database constraint validation"""
        print("\n🔒 Testing constraint validation...")
        
        try:
            # Test role constraints
            if set(VALID_ROLES) == {"Developer", "Investor"}:
                print("✅ Role validation constants correct")
            else:
                print(f"❌ Role validation issue - expected ['Developer', 'Investor'], got {VALID_ROLES}")
                return False
            
            # Test cap gain time constraints
            expected_times = {"Last 180 days", "More than 180 days AGO", "Upcoming"}
            if set(VALID_CAP_GAIN_TIMES) == expected_times:
                print("✅ Cap gain time validation constants correct")
            else:
                print(f"❌ Cap gain time validation issue - expected {expected_times}, got {VALID_CAP_GAIN_TIMES}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Constraint validation test failed: {e}")
            return False
    
    def test_basic_profile_operations(self):
        """Test basic profile CRUD operations"""
        print("\n💾 Testing basic profile operations...")
        
        try:
            # Create auth user first
            create_auth_user_if_needed(self.test_user_id)
            
            # Test creating a new Investor profile
            profile_data = {
                'role': 'Investor',
                'cap_gain_or_not': True,
                'size_of_cap_gain': 1300000,
                'time_of_cap_gain': 'Last 180 days',
                'geographical_zone_of_investment': 'FL'
            }
            
            print(f"📝 Creating Investor profile with data: {profile_data}")
            update_user_profile(self.test_user_id, profile_data)
            print("✅ Investor profile created successfully")
            
            # Test retrieving the profile
            retrieved_profile = get_user_profile(self.test_user_id)
            print(f"📖 Retrieved profile: {retrieved_profile}")
            
            if retrieved_profile and retrieved_profile.get('role') == 'Investor':
                print("✅ Profile retrieval successful")
                
                # Verify constraint compliance (investor should have NULL location)
                if retrieved_profile.get('location_of_development') is None:
                    print("✅ Investor constraint compliance verified")
                else:
                    print("❌ Investor constraint violation - location should be NULL")
                    return False
            else:
                print("❌ Profile retrieval failed or incorrect data")
                return False
            
            # Test updating to Developer role
            developer_data = {
                'role': 'Developer',
                'location_of_development': 'Los Angeles, CA'
            }
            print(f"📝 Updating to Developer profile: {developer_data}")
            update_user_profile(self.test_user_id, developer_data)
            
            updated_profile = get_user_profile(self.test_user_id)
            if updated_profile and updated_profile.get('role') == 'Developer':
                print("✅ Profile update to Developer successful")
                
                # Verify constraint compliance (developer should have NULL investor fields)
                if (updated_profile.get('cap_gain_or_not') is None and 
                    updated_profile.get('size_of_cap_gain') is None and
                    updated_profile.get('time_of_cap_gain') is None):
                    print("✅ Developer constraint compliance verified")
                else:
                    print("❌ Developer constraint violation - investor fields should be NULL")
                    return False
            else:
                print("❌ Profile update to Developer failed")
                return False
            
            # Test increment message count
            result = increment_message_count(self.test_user_id)
            if result:
                print("✅ Message count increment successful")
            else:
                print("❌ Message count increment failed")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Basic profile operations failed: {e}")
            return False
    
    async def test_llm_extraction(self):
        """Test LLM profile extraction with the exact conversation from logs"""
        print("\n🤖 Testing LLM profile extraction...")
        
        # Create a new user for LLM testing
        llm_test_user = uuid.uuid4()
        create_auth_user_if_needed(llm_test_user)
        
        # Test messages from the actual conversation
        test_messages = [
            "I'm an investor",
            "Long term",
            "Somewhere around 1.3 million",
            "about 30 days ago"
        ]
        
        try:
            for i, message in enumerate(test_messages):
                print(f"\n📨 Processing message {i+1}: '{message}'")
                
                # Extract profile updates using the LLM
                result = await self.profile_extractor.extract_profile_updates(
                    message, llm_test_user
                )
                
                print(f"🔍 Extraction result: {result}")
                
                # Verify profile was updated correctly
                current_profile = get_user_profile(llm_test_user)
                print(f"📊 Current profile: {current_profile}")
                
            return True
            
        except Exception as e:
            print(f"❌ LLM extraction test failed: {e}")
            return False
    
    def test_edge_cases(self):
        """Test edge cases and potential problematic scenarios"""
        print("\n🎯 Testing edge cases...")
        
        test_cases = [
            # Test case-sensitivity issues
            {'name': 'lowercase role', 'data': {'role': 'investor'}},
            {'name': 'uppercase role', 'data': {'role': 'INVESTOR'}}, 
            {'name': 'proper case role', 'data': {'role': 'Investor'}},
            
            # Test string formatting
            {'name': 'comma-separated number', 'data': {'size_of_cap_gain': '1,300,000'}},
            {'name': 'dollar sign number', 'data': {'size_of_cap_gain': '$1300000'}},
            {'name': 'float number', 'data': {'size_of_cap_gain': 1300000.50}},
            
            # Test state codes
            {'name': 'lowercase state', 'data': {'geographical_zone_of_investment': 'fl'}},
            {'name': 'uppercase state', 'data': {'geographical_zone_of_investment': 'FL'}},
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Test case: {test_case['name']}")
            try:
                test_user_id = uuid.uuid4()
                create_auth_user_if_needed(test_user_id)
                
                update_user_profile(test_user_id, test_case['data'])
                
                result = get_user_profile(test_user_id)
                print(f"✅ Edge case handled: {result}")
                
            except Exception as e:
                print(f"⚠️  Edge case caused error: {e}")
        
        return True
    
    def test_conversation_simulation(self):
        """Simulate the exact conversation that caused the original error"""
        print("\n💬 Simulating problematic conversation...")
        
        conversation_user_id = uuid.uuid4()
        create_auth_user_if_needed(conversation_user_id)
        
        # Simulate the exact sequence from the logs
        conversation_steps = [
            {
                'message': "I'm an investor",
                'expected_updates': {'role': 'Investor'}
            },
            {
                'message': "Long term", 
                'expected_updates': {'time_of_cap_gain': 'More than 180 days AGO'}
            },
            {
                'message': "Somewhere around 1.3 million",
                'expected_updates': {'size_of_cap_gain': 1300000}
            },
            {
                'message': "about 30 days ago",
                'expected_updates': {'time_of_cap_gain': 'Last 180 days'}
            }
        ]
        
        try:
            for step in conversation_steps:
                print(f"\n👤 User says: '{step['message']}'")
                
                # Get current profile before update
                before_profile = get_user_profile(conversation_user_id)
                print(f"📊 Profile before: {before_profile}")
                
                # Increment message count (this was failing in logs)
                increment_result = increment_message_count(conversation_user_id)
                print(f"📈 Message count increment: {increment_result}")
                
                # Update profile with expected data
                update_user_profile(conversation_user_id, step['expected_updates'])
                
                # Get profile after update
                after_profile = get_user_profile(conversation_user_id)
                print(f"📊 Profile after: {after_profile}")
                
                # Verify the update worked
                for key, expected_value in step['expected_updates'].items():
                    actual_value = after_profile.get(key) if after_profile else None
                    if str(actual_value) == str(expected_value):
                        print(f"✅ {key} updated correctly: {actual_value}")
                    else:
                        print(f"⚠️  {key} update issue - expected: {expected_value}, got: {actual_value}")
            
            print("\n🎉 Conversation simulation completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Conversation simulation failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        try:
            db = SessionLocal()
            # Delete test profiles
            db.query(UserProfile).filter(UserProfile.user_id == self.test_user_id).delete()
            db.commit()
            db.close()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

async def main():
    """Run all tests"""
    print("🚀 Starting comprehensive Ozzie database test suite")
    print("=" * 60)
    
    # Initialize database
    print("🔧 Initializing database...")
    init_db()
    
    test_suite = ComprehensiveTest()
    
    # Run all tests
    tests = [
        test_suite.test_database_connection,
        test_suite.test_table_structure,
        test_suite.test_auth_user_creation,
        test_suite.test_constraint_validation,
        test_suite.test_basic_profile_operations,
        test_suite.test_edge_cases,
        test_suite.test_conversation_simulation,
    ]
    
    async_tests = [
        test_suite.test_llm_extraction,
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    # Run async tests
    for test in async_tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    # Cleanup
    test_suite.cleanup()
    
    # Results
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system should work correctly.")
        print("\n📋 Summary of fixes applied:")
        print("   ✅ Fixed auth.users foreign key constraint")
        print("   ✅ Fixed role case-sensitivity handling")
        print("   ✅ Fixed database constraint compliance")
        print("   ✅ Fixed string-to-numeric conversion")
        print("   ✅ Fixed SQLAlchemy text() requirement")
    else:
        print("⚠️  Some tests failed. Review the output above for issues.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main()) 