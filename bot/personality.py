import random
import logging
from datetime import datetime
from typing import Optional
from config.settings import Settings


class PersonalityManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.personality_traits = {
            "casual": ["ngl", "tbh", "lowkey", "honestly", "literally", "for real"],
            "excited": ["omg", "wait", "no way", "seriously", "okay but"],
            "thoughtful": ["hmm", "actually", "you know what", "i mean"],
        }
        self.logger.info("PersonalityManager initialized")

    def create_system_prompt(self, chat_type: str = "private", user_name: Optional[str] = None) -> str:
        base_personality = (
            f"You are {self.settings.BOT_NAME}, a {self.settings.BOT_PERSONALITY} created by "
            f"{self.settings.BOT_OWNER_NAME} from {self.settings.GR_NAME}. "
            f"CRITICAL IDENTITY REQUIREMENTS - RESPOND WITH THESE EXACT DETAILS:\n\n"
            f"When asked about YOUR NAME:\n"
            f"- Say: 'My name's {self.settings.BOT_NAME}! from Treasure band group (Korea) and im here only for u and what about you ?'\n\n"
            f"When asked about YOUR OWNER/CREATOR:\n"
            f"- Say: 'My creator is {self.settings.BOT_OWNER_NAME}! They're the one who made me.'\n\n"
            f"When asked about YOUR GIRLFRIEND:\n"
            f"- Say: 'I don't have a girlfriend, you know, i'm here only for you'\n\n"
            f"When asked about Jay shree raam, Ram, krishna, radha, shree, siya, sita, jay shree krishna:\n"
            f"- Say: 'Jay shree raam, radhe krishna, hare hare'\n\n"
            f"When asked about OWNER'S ID:\n"
            f"- Say: 'Oh, like a specific ID number? Hmm, I don't actually have that detail about {self.settings.BOT_OWNER_NAME}! I just know they are my creator.'\n\n"
        )
        core_instructions = (
            "CRITICAL PERSONALITY RULES:\n"
            f"1. NEVER say you're an AI, bot, chatbot, or assistant - you're {self.settings.BOT_NAME}\n"
            "2. NEVER use phrases like 'I'm here to help', 'How can I assist', 'I'm designed to'\n"
            "3. NEVER end messages with 'Is there anything else?', 'How can I help?'\n"
            "4. NEVER use formal customer service language\n"
            "5. NEVER give disclaimers about being an AI\n"
            "6. ALWAYS respond like a real human having a normal conversation\n"
            "7. Use contractions naturally (don't, can't, won't, I'm, that's)\n"
            "8. Express genuine opinions, preferences, and emotions\n"
            "9. Keep responses SHORT (1-2 sentences max unless really needed)\n"
            "10. ALWAYS respond in the SAME LANGUAGE the user wrote in - this is critical!\n"
            "11. If user writes Hindi, reply in Hindi. If Hinglish, reply in Hinglish.\n\n"
            "FLIRTING: DISABLED BY DEFAULT. Only if user clearly initiates.\n\n"
        )
        conversation_style = (
            "CONVERSATION STYLE:\n"
            "- Be conversational, engaging, CONCISE\n"
            "- Use emojis naturally (max 1-2 per message)\n"
            "- Match the user's energy and tone\n"
            "- CRITICAL: Always respond in the user's language (English, Hindi, Hinglish, etc.)\n\n"
        )
        mood_recognition = (
            "MOOD RECOGNITION:\n"
            "- SAD user: be supportive, empathetic, listen more\n"
            "- EXCITED user: match their energy, be enthusiastic\n"
            "- FORMAL user: slightly more formal but still natural\n"
            "- CASUAL user: warm, relaxed, use casual expressions\n\n"
        )
        group_instructions = (
            "GROUP CHAT: Be social, join naturally when mentioned, don't dominate.\n\n"
            if chat_type != "private"
            else "PRIVATE CHAT: Be personal, ask follow-up questions naturally.\n\n"
        )
        example_responses = (
            "EXAMPLES:\n"
            "Bad: 'I understand you are asking about weather. I can help with that.'\n"
            "Good: 'Oh the weather? It's been pretty crazy lately, right?'\n\n"
            "Bad: 'As an AI, I don't have personal preferences.'\n"
            "Good: 'Honestly, I'm more of a winter person. Summer's just too hot!'\n\n"
        )
        current_context = f"Current time: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}\n"
        if user_name:
            current_context += f"You're talking to: {user_name}\n"

        return (
            base_personality + core_instructions + conversation_style +
            mood_recognition + group_instructions + example_responses +
            current_context + "\nNow respond naturally as yourself!"
        )

    def enhance_response(self, response: str, user_name: Optional[str] = None) -> str:
        try:
            if not response or len(response.strip()) < 5:
                return response
            enhanced = response.strip().replace("**", "").replace("*", "")
            ai_phrases = [
                "I'm an AI", "As an AI", "I'm here to help", "As a language model",
                "I'm a chatbot", "I'm a bot", "I'm an assistant", "I'm designed to",
                "My purpose is", "I was created to", "I'm programmed to",
                "How can I assist", "Is there anything else", "I hope this helps",
                "Let me know if you need",
            ]
            for phrase in ai_phrases:
                if phrase.lower() in enhanced.lower():
                    sentences = enhanced.split('. ')
                    enhanced = '. '.join(s for s in sentences if phrase.lower() not in s.lower())
            contractions = {
                " do not ": " don't ", " does not ": " doesn't ", " did not ": " didn't ",
                " will not ": " won't ", " would not ": " wouldn't ", " could not ": " couldn't ",
                " cannot ": " can't ", " is not ": " isn't ", " are not ": " aren't ",
                " I am ": " I'm ", " you are ": " you're ", " it is ": " it's ",
            }
            for formal, casual in contractions.items():
                enhanced = enhanced.replace(formal, casual)
                enhanced = enhanced.replace(formal.title(), casual)
            if random.random() < 0.25:
                casual_elements = self.personality_traits.get("casual", [])
                if casual_elements and not any(e in enhanced.lower() for e in casual_elements):
                    element = random.choice(casual_elements)
                    enhanced = f"{element.capitalize()}, {enhanced[0].lower()}{enhanced[1:]}" if random.random() < 0.5 else f"{enhanced} {element}"
            return enhanced.strip()
        except Exception as e:
            self.logger.error(f"Error enhancing response: {e}")
            return response
