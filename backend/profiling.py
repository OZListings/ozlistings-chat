import google.generativeai as genai
from typing import Dict, Optional, List
import json
import asyncio
import os

from database import get_user_profile, update_user_profile # Import database functions

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel("gemini-2.0-flash")

class ProfileExtractor:
    def __init__(self):
        self.profile_schema = {
            "accredited_investor": bool,
            "check_size": str,
            "geographical_zone": str,
            "real_estate_investment_experience": float,
            "investment_timeline": str,
            "investment_priorities": List[str],
            "deal_readiness": str,
            "preferred_asset_types": List[str],
            "needs_team_contact": bool
        }
        self.profile_keys = list(self.profile_schema.keys())

        self.profile_tool = {
            "name": "update_user_profile_json",
            "description": "Updates the user profile with extracted information. Always use this function to respond with profile updates.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    key: {"type": self._python_type_to_json_type(value), "description": key}
                    for key, value in self.profile_schema.items()
                },
                "required": self.profile_keys,
            },
        }
        self.tools = [self.profile_tool]

    def _python_type_to_json_type(self, python_type):
        if python_type == str:
            return "STRING"
        elif python_type == int or python_type == float:
            return "NUMBER"
        elif python_type == bool:
            return "BOOLEAN"
        elif python_type == list:
            return "ARRAY"
        else:
            return "STRING"

    def _get_extraction_prompt(self, message: str, current_profile: Dict) -> str:
        profile_fields_str = ", ".join(self.profile_keys)
        return (
            f"You are an expert profile extractor. Analyze the user message and update the user profile in JSON format.\n"
            f"Current profile state: {json.dumps(current_profile, indent=2)}\n\n"
            f"User Message: \"{message}\"\n\n"
            f"Instructions:\n"
            f"1. Extract information for the following profile fields: {profile_fields_str}.\n"
            f"2. If information for a field is not found, use null or the appropriate default value according to the schema.\n"
            f"3. Return ALL profile fields in the JSON, even if unchanged.\n"
            f"4. Importantly, ALWAYS respond by calling the `update_user_profile_json` function with the extracted profile data as parameters in JSON format.\n"
            f"5. Do not provide any conversational text or explanations, just the function call, and make sure the JSON is valid and parsable.\n"
            f"Enclose your ENTIRE response in a JSON code block, starting with ```json and ending with ```.\n"
            f"Example function call response format:\n"
            f"```json\n"
            f"{{\n"
            f"  \"tool_calls\": [\n    {{\n      \"function\": {{\n        \"name\": \"update_user_profile_json\",\n        \"parameters\": {{ ...profile data in JSON format... }}\n      }}\n    }}\n  ]\n}}\n```\n"
            f"Begin profile extraction now."
        )

    async def extract_profile_updates(self, message: str, current_profile: Optional[Dict] = None) -> Dict:
        if current_profile is None:
            current_profile = {key: None for key in self.profile_schema}

        try:
            prompt = self._get_extraction_prompt(message, current_profile)
            response = await model.generate_content_async(
                contents=prompt,
                tools=self.tools
            )

            text_response = response.candidates[0].content.parts[0].text

            if text_response.startswith("```json") and text_response.endswith("```"):
                text_response = text_response[7:-3].strip()

            try:
                response_json = json.loads(text_response)
                tool_calls = response_json.get("tool_calls", [])
                if tool_calls:
                    function_call_data = tool_calls[0].get("function", {})
                    function_name = function_call_data.get("name")
                    profile_args_str = function_call_data.get("parameters")

                    if function_name == "update_user_profile_json" and profile_args_str:
                        try:
                            updated_profile = json.loads(json.dumps(profile_args_str))
                            cleaned_profile = self._clean_profile(updated_profile)
                            return cleaned_profile
                        except json.JSONDecodeError as e:
                            print(f"Error parsing function call arguments JSON: {e}")
                            print(f"Raw arguments string: {profile_args_str}")
                            return current_profile
                    else:
                        print("Function call structure invalid or incorrect function name.")
                        return current_profile
                else:
                    print("No tool_calls found in Gemini JSON response.")
                    return current_profile
            except json.JSONDecodeError as e:
                print(f"Error parsing Gemini response TEXT as JSON: {e}")
                print(f"Raw response text causing JSON error: {text_response}")
                return current_profile

        except Exception as e:
            print(f"Error during profile extraction or function call handling: {e}")
            return current_profile

    def _clean_profile(self, profile: Dict) -> Dict:
        cleaned = {}
        for key, expected_type in self.profile_schema.items():
            if key in profile:
                value = profile[key]
                if value is not None:
                    try:
                        if expected_type == bool:
                            cleaned[key] = bool(value)
                        elif expected_type == float:
                            cleaned[key] = float(value)
                        elif expected_type == list:
                            if isinstance(value, str):
                                cleaned[key] = [value]
                            elif isinstance(value, list):
                                cleaned[key] = value
                            else:
                                cleaned[key] = []
                        elif expected_type == str:
                            cleaned[key] = str(value)
                        else:
                            cleaned[key] = value
                    except (ValueError, TypeError) as e:
                        print(f"Error cleaning field '{key}': {e}. Keeping raw value: {value}")
                        cleaned[key] = value
                else:
                    cleaned[key] = None
            else:
                cleaned[key] = None
        return cleaned

    def _standardize_check_size(self, check_size: str) -> str:
        return check_size

    def _extract_years(self, experience: str):
        return None

profile_extractor = ProfileExtractor()

async def update_profile(user_id: str, message: str) -> Dict:
    """Main function to update user profile - now using database"""
    current_profile_db = get_user_profile(user_id) # Fetch current profile from database
    current_profile = current_profile_db if current_profile_db else {} # Use DB profile or default to empty dict
    updated_profile = await profile_extractor.extract_profile_updates(message, current_profile)
    update_user_profile(user_id, updated_profile) # Update profile in database
    return updated_profile

def get_profile(user_id: str) -> Dict:
    """Retrieve the user's profile from the database"""
    profile_data = get_user_profile(user_id) # Fetch profile from database
    return profile_data if profile_data else {} # Return profile or empty dict if not found


async def test_profile_functionality(): # Test function remains mostly the same
    test_user_id = "test_user_db_123" # Different user ID for DB test
    initial_profile = get_profile(test_user_id)
    print(f"Initial profile (from DB): {initial_profile}") # Should be empty initially

    test_message = "I'm interested in investing around $500k in multifamily properties in Florida. I am an accredited investor."
    await update_profile(test_user_id, test_message)
    updated_profile = get_profile(test_user_id)
    print(f"Updated profile (from DB): {updated_profile}") # Should be updated based on message

    if updated_profile and updated_profile != initial_profile and updated_profile.get('accredited_investor') == True and 'multifamily' in updated_profile.get('preferred_asset_types', []):
        print("Profile update functionality test with database: PASS!")
        return True
    else:
        print("Profile update functionality test with database: FAIL!")
        return False

if __name__ == "__main__":
    asyncio.run(test_profile_functionality())