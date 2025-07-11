from google import genai
from google.genai import types
from typing import Dict, Optional, List
import json
import os
import logging

from database import get_user_profile, update_user_profile

# Configure logging
logger = logging.getLogger(__name__)

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

        # Define the function schema for the Gemini function calling API
        self.function_schema = {
            "name": "update_user_profile_json",
            "description": "Updates the user profile with extracted information. Always use this function to respond with profile updates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accredited_investor": {"type": "boolean", "description": "Whether the user is an accredited investor"},
                    "check_size": {"type": "string", "description": "Investment check size or amount"},
                    "geographical_zone": {"type": "string", "description": "Preferred geographical areas for investment"},
                    "real_estate_investment_experience": {"type": "number", "description": "Years of real estate investment experience"},
                    "investment_timeline": {"type": "string", "description": "Investment timeline or urgency"},
                    "investment_priorities": {"type": "array", "items": {"type": "string"}, "description": "Investment priorities and goals"},
                    "deal_readiness": {"type": "string", "description": "Current deal readiness status"},
                    "preferred_asset_types": {"type": "array", "items": {"type": "string"}, "description": "Preferred real estate asset types"},
                    "needs_team_contact": {"type": "boolean", "description": "Whether the user needs team contact or assistance"}
                },
                "required": self.profile_keys,
            },
        }

        # Initialize the NEW SDK client and config
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.tools = types.Tool(function_declarations=[self.function_schema])
        self.config = types.GenerateContentConfig(tools=[self.tools])



    def _get_extraction_prompt(self, message: str, current_profile: Dict) -> str:
        profile_fields_str = ", ".join(self.profile_keys)
        
        return (
            f"You are an expert profile extractor. Analyze the user message and update the user profile.\n"
            f"Current profile state: {json.dumps(current_profile, indent=2)}\n\n"
            f"User Message: \"{message}\"\n\n"
            f"Instructions:\n"
            f"1. Extract information for the following profile fields: {profile_fields_str}.\n"
            f"2. If information for a field is not found, use null or the appropriate default value according to the schema.\n"
            f"3. Return ALL profile fields, even if unchanged.\n"
            f"4. ALWAYS respond by calling the `update_user_profile_json` function with the extracted profile data.\n"
            f"5. Ensure all required fields are included in the function call.\n"
            f"Begin profile extraction now."
        )

    async def extract_profile_updates(self, message: str, current_profile: Optional[Dict] = None) -> Dict:
        if current_profile is None:
            current_profile = {key: None for key in self.profile_schema}

        try:
            prompt = self._get_extraction_prompt(message, current_profile)
            
            # NEW SDK API call
            contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=self.config
            )

            # Check if the response contains function calls (NEW SDK way)
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        if function_call.name == "update_user_profile_json":
                            # Extract the arguments from the function call
                            function_args = dict(function_call.args)
                            
                            cleaned_profile = self._clean_profile(function_args)
                            return cleaned_profile
                        else:
                            logger.warning(f"Unexpected function call: {function_call.name}")
                            return current_profile
                    elif hasattr(part, 'text') and part.text:
                        # Fallback: try to parse text response as JSON
                        try:
                            text_response = part.text.strip()
                            if text_response.startswith("```json") and text_response.endswith("```"):
                                text_response = text_response[7:-3].strip()
                            
                            response_json = json.loads(text_response)
                            if isinstance(response_json, dict):
                                cleaned_profile = self._clean_profile(response_json)
                                return cleaned_profile
                        except json.JSONDecodeError:
                            pass
                
                logger.warning("No valid function call or parsable JSON found in response.")
                return current_profile
            else:
                logger.error("No response candidates found.")
                return current_profile

        except Exception as e:
            logger.error(f"Error during profile extraction: {e}")
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
                        elif hasattr(expected_type, '__origin__') and expected_type.__origin__ == list:
                            # Handle List[str] type
                            if isinstance(value, str):
                                if ',' in value:
                                    cleaned[key] = [item.strip() for item in value.split(',')]
                                else:
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
                        logger.warning(f"Error cleaning field '{key}': {e}. Keeping raw value: {value}")
                        cleaned[key] = value
                else:
                    cleaned[key] = None
            else:
                cleaned[key] = None
        return cleaned

profile_extractor = ProfileExtractor()

async def update_profile(user_id: str, message: str) -> Dict:
    current_profile_db = get_user_profile(user_id)
    current_profile = current_profile_db if current_profile_db else {}
    updated_profile = await profile_extractor.extract_profile_updates(message, current_profile)
    update_user_profile(user_id, updated_profile)
    return updated_profile

def get_profile(user_id: str) -> Dict:
    profile_data = get_user_profile(user_id)
    return profile_data if profile_data else {}