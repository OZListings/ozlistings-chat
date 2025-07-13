#!/usr/bin/env python3

import asyncio
import os
import sys
import json
import uuid
from typing import Dict, List
from dotenv import load_dotenv

# Add parent directory to Python path to import profiling module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import the profile extraction logic
from profiling import ProfileExtractor, profile_extractor
from database import engine
from sqlalchemy import text

class ProfileExtractionTester:
    def __init__(self):
        self.test_cases = [
            {
                "name": "Basic Investment Info",
                "message": "I'm looking to invest $500K in multifamily properties in Austin, Texas within the next 6 months. I'm an accredited investor with 5 years of real estate experience.",
                "expected_fields": ["check_size", "preferred_asset_types", "geographical_zone", "investment_timeline", "accredited_investor", "real_estate_investment_experience"]
            },
            {
                "name": "Investment Priorities",
                "message": "My main priorities are cash flow and tax benefits. I want to build passive income streams.",
                "expected_fields": ["investment_priorities"]
            },
            {
                "name": "Deal Readiness",
                "message": "I'm ready to make an investment immediately. I have my funding secured and I'm looking for the right opportunity.",
                "expected_fields": ["deal_readiness", "investment_timeline"]
            },
            {
                "name": "Asset Types and Experience",
                "message": "I'm interested in commercial real estate, specifically office buildings and industrial properties. I've done 3 deals before.",
                "expected_fields": ["preferred_asset_types", "real_estate_investment_experience"]
            },
            {
                "name": "Complex Mixed Message",
                "message": "I'm a non-accredited investor looking to invest around $100K-200K in residential properties in California or Arizona. I want appreciation and some cash flow. I'm new to real estate but plan to invest within 3-6 months. I definitely need help from your team.",
                "expected_fields": ["accredited_investor", "check_size", "preferred_asset_types", "geographical_zone", "investment_priorities", "real_estate_investment_experience", "investment_timeline", "needs_team_contact"]
            },
            {
                "name": "Minimal Information",
                "message": "I want to invest in real estate.",
                "expected_fields": []  # Should handle minimal info gracefully
            }
        ]
    
    def print_header(self, text: str):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}")
    
    def print_test_case(self, test_case: Dict):
        print(f"\n🧪 Test Case: {test_case['name']}")
        print(f"💬 Message: \"{test_case['message']}\"")
        print(f"📋 Expected fields to extract: {test_case['expected_fields']}")
    
    def print_results(self, extracted_profile: Dict, expected_fields: List[str]):
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"{'='*40}")
        
        extracted_fields = []
        for key, value in extracted_profile.items():
            if value is not None and value != [] and value != "":
                extracted_fields.append(key)
                if isinstance(value, list):
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
        
        print(f"\n✅ Fields extracted: {extracted_fields}")
        
        if expected_fields:
            matched_fields = set(extracted_fields) & set(expected_fields)
            missed_fields = set(expected_fields) - set(extracted_fields)
            
            print(f"🎯 Expected fields matched: {list(matched_fields)}")
            if missed_fields:
                print(f"⚠️  Expected fields missed: {list(missed_fields)}")
            else:
                print(f"✅ All expected fields found!")
        
        return extracted_fields
    
    async def create_test_user(self, user_id: str):
        """Create a test user in auth.users table"""
        try:
            with engine.connect() as conn:
                conn.execute(text(f"""
                    INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, created_at, updated_at)
                    VALUES ('{user_id}', 'test-{user_id}@example.com', '', NOW(), NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """))
                conn.commit()
        except Exception as e:
            print(f"Error creating test user: {e}")

    async def cleanup_test_user(self, user_id: str):
        """Clean up test user data"""
        try:
            with engine.connect() as conn:
                # Clean up profile
                conn.execute(text(f"DELETE FROM user_profiles WHERE user_id = '{user_id}'"))
                # Clean up auth user
                conn.execute(text(f"DELETE FROM auth.users WHERE id = '{user_id}'"))
                conn.commit()
        except Exception as e:
            print(f"Error cleaning up test user: {e}")

    async def run_single_test(self, test_case: Dict) -> Dict:
        """Run a single test case"""
        self.print_test_case(test_case)
        
        # Use a test user ID
        test_user_id = str(uuid.uuid4())
        
        # Create test user
        await self.create_test_user(test_user_id)
        
        try:
            # Extract profile information
            extracted_profile = await profile_extractor.extract_profile_updates(
                test_case["message"], 
                test_user_id
            )
            
            extracted_fields = self.print_results(extracted_profile, test_case["expected_fields"])
            
            return {
                "test_name": test_case["name"],
                "success": True,
                "extracted_profile": extracted_profile,
                "extracted_fields": extracted_fields,
                "expected_fields": test_case["expected_fields"]
            }
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {
                "test_name": test_case["name"],
                "success": False,
                "error": str(e),
                "extracted_fields": [],
                "expected_fields": test_case["expected_fields"]
            }
        finally:
            # Clean up test user
            await self.cleanup_test_user(test_user_id)
    
    async def run_all_tests(self):
        """Run all test cases"""
        self.print_header("PROFILE EXTRACTION TEST SUITE")
        
        # Check if API key is configured
        if not os.getenv('GEMINI_API_KEY'):
            print("❌ ERROR: GEMINI_API_KEY not found in environment variables")
            print("Please set your Gemini API key in your .env file")
            return
        
        print(f"🔑 API Key configured: ✅")
        print(f"🧪 Running {len(self.test_cases)} test cases...")
        
        results = []
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n{'-'*60}")
            print(f"Test {i}/{len(self.test_cases)}")
            
            result = await self.run_single_test(test_case)
            results.append(result)
            
            # Add a small delay between tests
            await asyncio.sleep(1)
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results: List[Dict]):
        self.print_header("TEST SUMMARY")
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
        print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test.get('error', 'Unknown error')}")
        
        # Field extraction analysis
        all_fields = set()
        for result in successful_tests:
            all_fields.update(result["extracted_fields"])
        
        print(f"\n📊 FIELD EXTRACTION ANALYSIS:")
        print(f"Fields successfully extracted across all tests: {sorted(list(all_fields))}")
        
        # Show which fields were extracted most frequently
        field_counts = {}
        for result in successful_tests:
            for field in result["extracted_fields"]:
                field_counts[field] = field_counts.get(field, 0) + 1
        
        if field_counts:
            print(f"\n🔥 Most frequently extracted fields:")
            for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {field}: {count}/{len(successful_tests)} tests")

async def main():
    """Main function to run the tests"""
    tester = ProfileExtractionTester()
    
    print("🚀 Starting Profile Extraction Tests...")
    print("This will test the AI's ability to extract profile information from user messages.")
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    
    print(f"\n✅ Testing complete!")

if __name__ == "__main__":
    asyncio.run(main()) 