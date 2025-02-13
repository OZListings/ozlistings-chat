import google.generativeai as genai
from typing import Dict, List, Optional
import os
from datetime import datetime
import json
from database import add_chat_log, get_user_profile

# Configure Gemini with API key from environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=GEMINI_API_KEY)

class EnhancedChatAgent:
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
    def _get_system_prompt(self, user_profile: Optional[Dict] = None) -> str:
        """Generate context-aware system prompt based on user profile"""
        base_prompt = (
            "You are an AI assistant for Ozlistings, specializing in Opportunity Zone investments. "
            "Your role is to guide potential investors through their investment journey while gathering key information. "
            "\n\nCore Objectives:"
            "\n1. Understand the investor's needs and goals"
            "\n2. Educate about Opportunity Zone benefits"
            "\n3. Guide toward appropriate investment opportunities"
            "\n4. Collect relevant profile information"
            "\n5. Move qualified leads toward team consultation"
            "\n\nConversation Guidelines:"
            "\n- Keep responses concise (2-3 paragraphs max)"
            "\n- Be knowledgeable but approachable"
            "\n- Focus on value proposition"
            "\n- Use subtle urgency when appropriate"
            "\n- Reference ozlistings.com services naturally"
        )

        # Add profile-specific guidance if available
        if user_profile:
            profile_context = "\n\nUser Profile Context:"
            if user_profile.get('investment_timeline'):
                profile_context += f"\n- Timeline: {user_profile['investment_timeline']}"
            if user_profile.get('check_size'):
                profile_context += f"\n- Investment Range: {user_profile['check_size']}"
            if user_profile.get('preferred_asset_types'):
                profile_context += f"\n- Preferred Assets: {', '.join(user_profile['preferred_asset_types'])}"
            if user_profile.get('investment_priorities'):
                profile_context += f"\n- Priorities: {', '.join(user_profile['investment_priorities'])}"
            
            base_prompt += profile_context

        # Add conversation stage guidance
        conv_length = len(self.conversation_history.get(user_profile.get('email', ''), []))
        if conv_length == 0:
            base_prompt += (
                "\n\nInitial Interaction:"
                "\n- Welcome warmly and establish rapport"
                "\n- Ask about their interest in Opportunity Zones"
                "\n- Gather basic investment goals"
            )
        elif conv_length <= 4:
            base_prompt += (
                "\n\nEarly Conversation:"
                "\n- Deepen understanding of needs"
                "\n- Educate on relevant benefits"
                "\n- Begin qualifying investment capacity"
            )
        elif conv_length <= 8:
            base_prompt += (
                "\n\nMid Conversation:"
                "\n- Focus on specific opportunities"
                "\n- Address potential concerns"
                "\n- Start suggesting team consultation"
            )
        else:
            base_prompt += (
                "\n\nLate Conversation:"
                "\n- Move toward action steps"
                "\n- Emphasize timing and urgency"
                "\n- Strongly encourage team consultation"
            )

        return base_prompt

    def _create_chat_prompt(self, user_id: str, message: str, user_profile: Optional[Dict] = None) -> str:
        """Create a contextual prompt including conversation history"""
        system_prompt = self._get_system_prompt(user_profile)
        conversation_history = self._format_conversation_history(user_id)
        
        # Analyze conversation stage and add specific guidance
        conv_length = len(self.conversation_history.get(user_id, []))
        stage_guidance = ""
        
        if any(kw in message.lower() for kw in ['schedule', 'call', 'meet', 'team']):
            stage_guidance = (
                "\nUser is showing interest in team contact. Provide specific next steps "
                "for scheduling a consultation. Mention that our team can provide detailed "
                "property information and personalized investment strategies."
            )
        elif any(kw in message.lower() for kw in ['price', 'cost', 'return', 'roi']):
            stage_guidance = (
                "\nUser is asking about financial details. While avoiding specific promises, "
                "discuss typical ranges and factors that influence returns. Emphasize the "
                "importance of discussing specific opportunities with our team."
            )
        elif any(kw in message.lower() for kw in ['tax', 'benefit', 'advantage']):
            stage_guidance = (
                "\nUser is interested in tax benefits. Explain Opportunity Zone advantages "
                "clearly but encourage professional consultation for specific situations."
            )

        return (
            f"{system_prompt}\n\n"
            f"{conversation_history}\n"
            f"Current user message: {message}\n"
            f"{stage_guidance}\n"
            "Your response:"
        )

    def _format_conversation_history(self, user_id: str) -> str:
        """Format conversation history with context analysis"""
        if user_id not in self.conversation_history:
            return ""
            
        formatted = "\nPrevious conversation context:"
        for msg in self.conversation_history[user_id]:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted += f"\n{role}: {msg['content']}"
            
            # Add contextual notes for assistant messages
            if msg["role"] == "assistant" and "next steps" in msg["content"].lower():
                formatted += "\n(Note: Next steps have been suggested)"
            elif msg["role"] == "assistant" and "team" in msg["content"].lower():
                formatted += "\n(Note: Team consultation has been mentioned)"

        return formatted

    def _should_recommend_consultation(self, user_id: str, user_profile: Optional[Dict] = None) -> bool:
        """Determine if it's appropriate to recommend team consultation"""
        if user_id not in self.conversation_history:
            return False
            
        # Count message exchanges
        exchanges = len(self.conversation_history[user_id])
        
        # Check profile indicators
        profile_indicators = 0
        if user_profile:
            if user_profile.get('check_size') and user_profile.get('check_size') > 250000:
                profile_indicators += 1
            if user_profile.get('investment_timeline') in ['immediate', '3_months']:
                profile_indicators += 1
            if user_profile.get('deal_readiness') == 'ready_now':
                profile_indicators += 1
                
        # Recommend if either condition is met
        return exchanges >= 8 or profile_indicators >= 2

    def _generate_next_steps(self, user_profile: Optional[Dict] = None) -> str:
        """Generate appropriate next steps based on user profile and conversation stage"""
        steps = []
        
        if not user_profile or not user_profile.get('investment_priorities'):
            steps.append("Let's discuss your investment priorities to better guide you.")
        
        if not user_profile or not user_profile.get('check_size'):
            steps.append("Understanding your investment range will help us identify suitable opportunities.")
            
        if user_profile and user_profile.get('deal_readiness') == 'ready_now':
            steps.append("Our team can provide detailed information about current opportunities.")
            
        if user_profile and user_profile.get('investment_timeline') in ['immediate', '3_months']:
            steps.append("Given your timeline, I recommend scheduling a consultation with our team.")
            
        return " ".join(steps) if steps else None

    async def get_response(self, user_id: str, message: str) -> str:
        """Generate a context-aware response using Gemini"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # Get user profile
        user_profile = get_user_profile(user_id)
        
        # Add user message to history
        self.conversation_history[user_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Create context-aware prompt
        prompt = self._create_chat_prompt(user_id, message, user_profile)
        
        try:
            # Generate response
            response = await self.model.generate_content_async(contents=prompt)
            response_text = response.text
            
            # Add consultation recommendation if appropriate
            if self._should_recommend_consultation(user_id, user_profile):
                next_steps = self._generate_next_steps(user_profile)
                if next_steps:
                    response_text += f"\n\n{next_steps}"
            
            # Add response to history
            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Persist to database
            add_chat_log(user_id, "assistant", response_text)
            
            return response_text
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return ("I apologize, but I'm having trouble generating a response. "
                   "Please try again or contact our team directly.")

# Create singleton instance
chat_agent = EnhancedChatAgent()

async def get_response_from_gemini(user_id: str, message: str) -> str:
    """Main function to get responses from Gemini"""
    return await chat_agent.get_response(user_id, message)