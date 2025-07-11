import google.generativeai as genai
from typing import Dict, Optional, List
import json
import os
import logging

from database import get_user_profile, update_user_profile

# Configure logging
logger = logging.getLogger(__name__)

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
            f"  \"tool_calls\": [\n    {{\n"
            f"      \"function\": {{\n"
            f"        \"name\": \"update_user_profile_json\",\n"
            f"        \"parameters\": {{ ...profile data in JSON format... }}\n"
            f"      }}\n"
            f"    }}\n"
            f"  ]\n"
            f"}}\n```\n"
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
                            logger.error(f"Error parsing function call arguments JSON: {e}")
                            return current_profile
                    else:
                        logger.warning("Function call structure invalid or incorrect function name.")
                        return current_profile
                else:
                    logger.warning("No tool_calls found in Gemini JSON response.")
                    return current_profile
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Gemini response TEXT as JSON: {e}")
                return current_profile

        except Exception as e:
            logger.error(f"Error during profile extraction or function call handling: {e}")
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