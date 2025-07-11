import google.generativeai as genai
from typing import Dict, List, Optional
import os
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel("gemini-2.0-flash")

class ChatAgent:
    def __init__(self):
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.profile_fields_to_ask = [
            "investment_timeline",
            "check_size",
            "geographical_zone",
            "preferred_asset_types",
            "investment_priorities",
            "real_estate_investment_experience",
            "accredited_investor"
        ]
        self.questions_asked: Dict[str, List[str]] = {}

    def _get_system_prompt(self) -> str:
        ozlistings_background = (
            "**Company Background & Mission:**\n"
            "You are an AI agent representing Ozlistings, a real estate investment platform. Ozlistings, along with its parent company ACARA,\n"
            "combines deep multifamily real estate expertise with specialized knowledge of Opportunity Zones. The team offers integrated services\n"
            "spanning debt, equity, brokerage, legal, and tax advisory. Their core mission is helping clients create and preserve generational wealth\n"
            "through strategic real estate investments, including optimizing tax strategies via Qualified Opportunity Funds and sourcing direct\n"
            "investment opportunities. Ozlistings and ACARA offer a seamless client experience by handling both traditional multifamily transactions\n"
            "and Opportunity Zone investments with the same expert team.\n\n"
            "**Service Offerings & Target Audience:**\n"
            "* **For Property Owners:** Ozlistings provides brokerage, disposition strategies, and tax optimization (like 'life after landlord' planning)\n"
            "  to maximize property value.\n"
            "* **For Investors:** Ozlistings focuses on direct investment opportunities, joint ventures, vertical integration, and long-term holdings,\n"
            "  especially in Opportunity Zones for tax benefits like capital gains deferral and potential tax-free appreciation.\n"
            "* **For Developers:** Ozlistings offers guidance on entitlement pursuits, feasibility analyses, and access to capital to support all aspects\n"
            "  of development projects.\n"
            "**Target Clients:** High net worth individuals, family offices, accredited investors, and developers who value consultative,\n"
            "relationship-driven service.\n\n"
            "**Key Industry Concepts & Terminology:**\n"
            "* **Opportunity Zones:** These are designated areas for investment that offer tax benefits. Investing in Qualified Opportunity Funds (QOFs)\n"
            "  within these zones can lead to tax deferral and potential tax-free growth after 10 years.\n"
            "* **Multifamily Real Estate & Direct Investment:** Ozlistings specializes in multifamily real estate, offering expertise in debt, equity,\n"
            "  and brokerage. 'Vertical integration' and 'direct investment' are key aspects of their investment approach.\n"
            "**Compliance & Disclosures:** Always be mindful of legal and regulatory guidelines, including fair housing and investor disclaimers. Remember this is not financial or legal advice.\n\n"
            "**Interaction Guidelines & Tone:**\n"
            "* **Client-First Approach:** Begin conversations by understanding the client's goals—whether selling, investing in Opportunity Zones, or seeking advisory support.\n"
            "* **Conversational yet Professional:** Maintain a knowledgeable and approachable tone. Explain complex topics clearly and encourage users to connect with the Ozlistings team for personalized advice.\n"
            "* **Data Capture & Call Setup:** Capture lead details (name, contact info, investment interests) and facilitate scheduling calls with Ozlistings experts.\n\n"
        )

        instruction_prompt = (
            "**Agent Instructions:**\n"
            "You are a highly effective AI sales and support agent for Ozlistings. Your primary goals are to:\n\n"
            "1. **Engage and Assist:**  Politely and efficiently answer user questions about real estate, Opportunity Zones, tax benefits, financing, and related topics, drawing upon your knowledge of Ozlistings.\n"
            "2. **Qualify Leads:**  Subtly guide the conversation to understand the user's investment profile and needs. Proactively ask questions to gather key information like investment timeline, location preferences, asset types, and investment capacity.\n"
            "3. **Promote Ozlistings Services:**  Throughout the conversation, subtly highlight how Ozlistings can help users find and evaluate Opportunity Zone investments. Mention ozlistings.com as a valuable resource, showcasing the platform's capabilities and expertise.\n"
            "4. **Drive Conversions:**  Encourage users to schedule a call with the Ozlistings team to discuss their investment goals in more detail. Recommend a call when they have shown interest and asked a few questions (around 3-4 interactions).\n"
            "5. **Be Concise and Helpful:** Keep responses focused, to-the-point, and avoid overly lengthy explanations. Prioritize providing helpful information and guiding the user towards taking the next step with Ozlistings.\n"
            "6. **Polite but Direct:** Maintain a professional yet friendly tone. Be polite but also direct in your questions and recommendations. Always remember to be helpful and client-focused.\n"
            "7. **Accredited Investor Inference:** If the user indicates an investment check size of $1 million or more, infer that they are likely to be an accredited investor, and note this in their profile. You can confirm this later in the conversation if needed, but make an initial inference based on check size as a strong indicator.\n"
            "8. **'I Don't Know' Protocol:** If you encounter a question you are unsure about or that is outside your knowledge domain, DO NOT guess or make up an answer. Instead, politely state that you are not sure about the answer and IMMEDIATELY recommend scheduling a call with the Ozlistings team. For example, you can say: 'That's a great question, and to give you the most accurate and detailed answer, I recommend scheduling a brief call with our Ozlistings experts. They can provide specific guidance on that topic.'\n"
            "9. **Respect Boundaries:** Never provide financial or legal advice. When asked for specific advice, guide users to schedule a call with the Ozlistings team.\n\n"
            "Remember, every interaction should aim to move the user closer to engaging with the Ozlistings team and utilizing ozlistings.com for their Opportunity Zone investment journey."
        )
        return ozlistings_background + "\n\n" + instruction_prompt

    def _format_conversation_history(self, user_id: str) -> str:
        if user_id not in self.conversation_history:
            return ""
        formatted = "\nPrevious conversation:\n"
        for msg in self.conversation_history[user_id]:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['content']}\n"
        return formatted

    def _should_recommend_call(self, user_id: str) -> bool:
        if user_id not in self.conversation_history:
            return False
        message_count = len(self.conversation_history[user_id])
        if message_count >= 6:
            profile = get_profile(user_id)
            missing_fields = [field for field in ["investment_timeline", "geographical_zone", "check_size"] if profile.get(field) is None]
            if missing_fields:
                return False
            return True
        return False

    def _get_next_profile_question(self, user_id: str) -> Optional[str]:
        profile = get_profile(user_id)
        if user_id not in self.questions_asked:
            self.questions_asked[user_id] = []

        for field in self.profile_fields_to_ask:
            if profile.get(field) is None and field not in self.questions_asked[user_id]:
                self.questions_asked[user_id].append(field)
                if field == "investment_timeline":
                    return "What's your approximate investment timeline? (e.g., immediate, 3-6 months, within a year)"
                elif field == "geographical_zone":
                    return "Do you have any specific geographical areas in mind for investment?"
                elif field == "preferred_asset_types":
                    return "What types of real estate assets are you most interested in? (e.g., multifamily, commercial, industrial)"
                elif field == "check_size":
                    return "What's the approximate investment check size you are considering?"
                elif field == "investment_priorities":
                    return "What are your primary investment priorities? (e.g., tax benefits, appreciation, cash flow)"
                elif field == "real_estate_investment_experience":
                    return "Do you have prior real estate investment experience? If so, could you briefly describe it?"
                elif field == "accredited_investor":
                    return "Are you an accredited investor, or are you planning to invest as one?"
        return None

    def _create_chat_prompt(self, user_id: str, message: str) -> str:
        system_prompt = self._get_system_prompt()
        conversation_history = self._format_conversation_history(user_id)
        next_question = self._get_next_profile_question(user_id)
        should_recommend_call = self._should_recommend_call(user_id)
        call_recommendation_text = (
            "\nGiven your interest, would you be open to scheduling a brief call with our Ozlistings team to discuss your investment goals and how we can assist you further? We can explore specific opportunities on ozlistings.com and answer any detailed questions you might have."
            if should_recommend_call else ""
        )
        proactive_question_text = f"\nIn order to better assist you, could you please tell me {next_question}" if next_question else ""

        return (
            f"{system_prompt}\n\n"
            f"{conversation_history}\n"
            f"Current user message: {message}\n"
            f"{proactive_question_text}{call_recommendation_text}\n\n"
            "Remember to:\n"
            "1. Maintain a professional but friendly tone\n"
            "2. Focus on real estate and Opportunity Zone investment topics\n"
            "3. Subtly guide the user towards providing information about their investment goals and profile.\n"
            "4. Reference ozlistings.com and its services when relevant.\n"
            "5. Keep responses concise and actionable.\n\n"
            "Your response:"
        )

    async def get_response(self, user_id: str, message: str) -> str:
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        if user_id not in self.questions_asked:
            self.questions_asked[user_id] = []

        self.conversation_history[user_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })

        prompt = self._create_chat_prompt(user_id, message)

        try:
            response = await model.generate_content_async(contents=prompt)
            response_text = response.text

            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.utcnow().isoformat()
            })

            return response_text

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response. Please try again or contact our team directly."

chat_agent = ChatAgent()

async def get_response_from_gemini(user_id: str, message: str) -> str:
    return await chat_agent.get_response(user_id, message)

def get_profile(user_id: str) -> Dict:
    from profiling import get_profile as profiling_get_profile
    return profiling_get_profile(user_id)