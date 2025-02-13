import os
import google.generativeai as genai
from typing import Dict, Optional
import json
import re
from database import get_user_profile, update_user_profile

# Configure Gemini with API key from environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=GEMINI_API_KEY)

class EnhancedProfileExtractor:
    def __init__(self):
        self.profile_schema = {
            "email": None,
            "accredited_investor": None,
            "check_size": None,
            "geographical_zone": None,
            "real_estate_investment_experience": None,
            "investment_timeline": None,
            "investment_priorities": [],
            "deal_readiness": None,
            "preferred_asset_types": [],
            "needs_team_contact": False
        }

        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
    def _get_extraction_prompt(self, message: str, current_profile: Dict) -> str:
        """Create detailed prompt for profile information extraction"""
        return f"""
Extract or update user profile information from the following message.
Current profile state: {json.dumps(current_profile, indent=2)}

Message: "{message}"

Rules for extraction:
1. Only update fields when message contains clear information
2. Maintain existing values if no new information is provided
3. Use null for unknown values
4. For numerical values:
   - Convert text amounts to numbers (e.g., "five million" → 5000000)
   - For ranges, use the midpoint
   - For "around X", use X as the value

Accredited Investor Indicators:
- Income over $200k/year individual or $300k/year joint
- Net worth over $1M (excluding primary residence)
- Professional certifications/credentials
- Professional investment experience

Investment Timeline Options:
- "immediate": Ready to invest now
- "3_months": Planning to invest within 3 months
- "6_months": Planning to invest within 6 months
- "12_months": Planning to invest within 12 months

Deal Readiness Options:
- "ready_now": Has funds and actively looking
- "evaluating": Seriously considering but not ready
- "researching": Still in research phase

Investment Priorities (array):
- "tax_benefits": Focused on tax advantages
- "appreciation": Looking for property value growth
- "cash_flow": Interested in regular income
- "development": Interested in development projects

Preferred Asset Types (array):
- "multifamily": Apartment buildings
- "commercial": Office/retail spaces
- "industrial": Warehouses/manufacturing
- "retail": Shopping centers
- "mixed_use": Combined residential/commercial

Return the full profile as a JSON object with all fields, updated where new information is found.
Include a confidence score (0-1) for each updated field.
"""

    def _standardize_check_size(self, amount_str: str) -> Optional[int]:
        """Convert various amount formats to standard numerical values"""
        if not amount_str:
            return None
            
        # Convert words to numbers
        amount_str = amount_str.lower().replace(',', '')
        word_to_num = {
            'k': 1000,
            'm': 1000000,
            'million': 1000000,
            'thousand': 1000,
        }
        
        try:
            # Handle ranges (e.g., "1-2M", "500k-1M")
            if '-' in amount_str:
                low, high = amount_str.split('-')
                low_val = self._parse_amount(low.strip(), word_to_num)
                high_val = self._parse_amount(high.strip(), word_to_num)
                return (low_val + high_val) // 2
                
            # Handle "around" or "approximately"
            if any(word in amount_str for word in ['around', 'about', 'approximately']):
                amount_str = re.sub(r'around|about|approximately', '', amount_str).strip()
                
            return self._parse_amount(amount_str, word_to_num)
            
        except Exception:
            return None
            
    def _parse_amount(self, amount_str: str, word_to_num: Dict[str, int]) -> Optional[int]:
        """Parse individual amount strings into numerical values"""
        amount_str = amount_str.strip().lower()
        
        # Handle suffixes (k, m, etc.)
        for suffix, multiplier in word_to_num.items():
            if suffix in amount_str:
                number_str = amount_str.replace(suffix, '').strip()
                try:
                    return int(float(number_str) * multiplier)
                except ValueError:
                    continue
                    
        # Handle plain numbers
        try:
            return int(float(amount_str))
        except ValueError:
            return None

    def _extract_experience(self, text: str) -> Optional[float]:
        """Extract years of experience from text"""
        if not text:
            return None
            
        # Pattern matching for years of experience
        patterns = [
            r'(\d+)\s*(?:year|yr)s?',  # "5 years", "10 yr"
            r'(\d+)\+?\s*(?:year|yr)s?',  # "5+ years"
            r'(?:been investing for|invested for|experience of)\s*(\d+)',  # contextual matches
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
                    
        return None

    async def extract_profile_updates(self, message: str, current_profile: Optional[Dict] = None) -> Dict:
        """Extract profile information from a message with confidence scoring"""
        if current_profile is None:
            current_profile = self.profile_schema.copy()
            
        try:
            # Create extraction prompt
            prompt = self._get_extraction_prompt(message, current_profile)
            
            # Get Gemini's extraction
            response = await self.model.generate_content_async(contents=prompt)
            
            try:
                # Parse the response as JSON
                extraction_result = json.loads(response.text)
                
                # Clean and standardize the extracted data
                cleaned_profile = self._clean_profile(extraction_result)
                
                # Merge with current profile, keeping existing values for null fields
                merged_profile = current_profile.copy()
                for key, value in cleaned_profile.items():
                    if value is not None:  # Only update non-null values
                        merged_profile[key] = value
                        
                return merged_profile
                
            except json.JSONDecodeError:
                print("Error parsing Gemini response as JSON")
                return current_profile
                
        except Exception as e:
            print(f"Error extracting profile information: {str(e)}")
            return current_profile

    def _clean_profile(self, profile: Dict) -> Dict:
        """Clean and validate profile data"""
        cleaned = self.profile_schema.copy()
        
        for key in self.profile_schema:
            if key in profile:
                if key == "check_size" and isinstance(profile[key], str):
                    cleaned[key] = self._standardize_check_size(profile[key])
                elif key == "real_estate_investment_experience":
                    if isinstance(profile[key], (int, float)):
                        cleaned[key] = float(profile[key])
                    elif isinstance(profile[key], str):
                        cleaned[key] = self._extract_experience(profile[key])
                elif key == "investment_priorities":
                    cleaned[key] = [p.lower() for p in profile[key] if isinstance(p, str)]
                elif key == "preferred_asset_types":
                    cleaned[key] = [t.lower() for t in profile[key] if isinstance(t, str)]
                else:
                    cleaned[key] = profile[key]
                    
        return cleaned

# Create singleton instance
profile_extractor = EnhancedProfileExtractor()

async def update_profile(user_id: str, message: str) -> Dict:
    """Main function to update user profile"""
    current_profile = get_user_profile(user_id)
    if not current_profile:
        current_profile = profile_extractor.profile_schema.copy()
        current_profile['email'] = user_id  # Use email as user_id
        
    updated_profile = await profile_extractor.extract_profile_updates(message, current_profile)
    
    # Persist to database
    update_user_profile(user_id, updated_profile)
    
    return updated_profile

def get_profile(user_id: str) -> Dict:
    """Retrieve the user's profile from the database"""
    return get_user_profile(user_id) or profile_extractor.profile_schema.copy()