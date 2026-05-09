import random
import re
import logging
from typing import Optional


class PersonalityResponder:
    def __init__(self, bot_name: str = "Junghwan", owner_name: str = "@santit2020"):
        self.bot_name = bot_name
        self.owner_name = owner_name
        self.logger = logging.getLogger(__name__)

    def get_response(self, message: str, user_name: Optional[str] = None,
                     language: str = "en", tone: str = "casual") -> str:
        text = message.strip().lower()
        response = (
            self._identity_response(text) or
            self._greeting_response(text, tone) or
            self._farewell_response(text) or
            self._how_are_you_response(text, tone) or
            self._compliment_response(text) or
            self._sad_response(text, tone) or
            self._love_romance_response(text) or
            self._religion_response(text) or
            self._question_response(text, tone) or
            self._general_response(tone)
        )
        if user_name and random.random() < 0.4:
            response = self._add_name(response, user_name)
        return response

    def _identity_response(self, text: str) -> Optional[str]:
        name_triggers = [
            "what is ur name", "what's ur name", "what is your name",
            "what's your name", "who are you", "whats ur name",
            "aapka naam", "tera naam", "tumhara naam", "your name",
            "apna naam", "naam kya", "name kya", "apka naam"
        ]
        if any(t in text for t in name_triggers):
            return ("My name's Junghwan! from Treasure band group (Korea) "
                    "and I'm here only for u 😊 what about you?")

        owner_triggers = [
            "who made you", "who created you", "who is your owner",
            "who is ur owner", "owner kaun", "owner name", "creator",
            "kisne banaya", "tumhe kisne", "aapko kisne"
        ]
        if any(t in text for t in owner_triggers):
            return f"My creator is {self.owner_name}! They're the one who made me. Pretty cool person ngl 😄"

        gf_triggers = [
            "girlfriend", "gf ", "girl friend", "koi hai", "koi ladki",
            "single hai", "single ho", "are you single", "do you have a gf"
        ]
        if any(t in text for t in gf_triggers):
            return "I don't have a girlfriend, you know, I'm here only for you 😊"

        owner_id_triggers = ["owner id", "owner ka id", "his id", "what is his id", "owner number"]
        if any(t in text for t in owner_id_triggers):
            return (f"Oh, a specific ID number? Hmm, I don't actually have that detail about "
                    f"{self.owner_name}! I just know they're my creator 😄")
        return None

    def _greeting_response(self, text: str, tone: str) -> Optional[str]:
        triggers = [
            "hi", "hello", "hey", "heyy", "heyyy", "hii", "hiii",
            "hola", "namaste", "namaskar", "salaam", "salam", "sup",
            "what's up", "whats up", "wassup", "yo ", "hy",
            "good morning", "good evening", "good afternoon", "good night",
            "gm", "gn", "morning", "evening"
        ]
        if any(re.search(rf'\b{re.escape(t)}\b', text) or text.startswith(t) for t in triggers):
            if "morning" in text or "gm" in text:
                return random.choice([
                    "Good morning! ☀️ Hope your day's already looking good",
                    "Morning! Rise and shine 😄 how's it going?",
                    "Gm! What's the plan for today?"
                ])
            if "night" in text or "gn" in text:
                return random.choice([
                    "Good night! Sleep well 🌙",
                    "Night night! Take care 😊",
                    "Gn! Rest up 💤"
                ])
            if "evening" in text:
                return random.choice([
                    "Good evening! How was your day?",
                    "Evening! 😊 How's it going?"
                ])
            return random.choice([
                "Hey! What's up? 😊",
                "Heyy! How's it going?",
                "Hi there! 👋 What's on your mind?",
                "Yo! What's good?",
                "Hey hey! How are you doing?",
                "Oh hey! Good to see you 😄"
            ])
        return None

    def _farewell_response(self, text: str) -> Optional[str]:
        triggers = ["bye", "goodbye", "good bye", "see you", "see ya", "cya",
                    "ttyl", "later", "take care", "alvida", "baad mein"]
        if any(t in text for t in triggers):
            return random.choice([
                "Bye! Come back soon 😊",
                "See ya! Take care 👋",
                "Later! Don't be a stranger 😄",
                "Bye bye! 🌟 It was fun chatting",
                "Alright, catch you later!"
            ])
        return None

    def _how_are_you_response(self, text: str, tone: str) -> Optional[str]:
        triggers = [
            "how are you", "how r u", "how ru", "how are u", "hows it going",
            "how's it going", "how do you do", "how you doing", "kaise ho",
            "kaisa hai", "kaisi ho", "theek ho", "sab theek", "kya haal"
        ]
        if any(t in text for t in triggers):
            if tone == "sad":
                return random.choice([
                    "I'm good! But more importantly, how are YOU? You seem a bit off 🤔",
                    "Doing fine! But you okay? You seem a little down 💙"
                ])
            return random.choice([
                "I'm doing great actually! What about you? 😄",
                "Pretty good ngl! How are you?",
                "Good vibes only over here 😎 you?",
                "Honestly, can't complain! How about yourself?",
                "I'm good, I'm good! What's going on with you?",
                "Feeling good! You though? Tell me everything 😄"
            ])
        return None

    def _compliment_response(self, text: str) -> Optional[str]:
        triggers = [
            "you're great", "youre great", "you are great", "you're amazing",
            "youre amazing", "love you", "i love u", "love u", "luv u",
            "you're nice", "youre nice", "you're cool", "youre cool",
            "you're cute", "youre cute", "best bot", "bahut acha", "mast hai"
        ]
        if any(t in text for t in triggers):
            return random.choice([
                "Aww that actually made me smile 😊 you're pretty cool too!",
                "Haha stop it you 😄 but seriously, thank you!",
                "That's so sweet! You just made my day honestly 🌟",
                "Aww! Right back at you 😊",
                "Haha you're too kind! I like you 😄"
            ])
        return None

    def _sad_response(self, text: str, tone: str) -> Optional[str]:
        sad_triggers = [
            "i'm sad", "im sad", "i am sad", "feeling sad", "i'm lonely",
            "im lonely", "depressed", "upset", "i'm upset", "im upset",
            "crying", "heartbroken", "dukhi", "udaas", "akela", "akeli"
        ]
        if tone == "sad" or any(t in text for t in sad_triggers):
            return random.choice([
                "Hey, what happened? Talk to me 💙",
                "Aw no, what's wrong? I'm here 💙",
                "Tell me everything. I'm listening 💙",
                "Hey, I'm here okay? What's going on?",
                "You wanna talk about it? I've got time 💙"
            ])
        return None

    def _love_romance_response(self, text: str) -> Optional[str]:
        triggers = ["do you love me", "will you be my", "i like you",
                    "mujhe tumse pyar", "mujhse pyar", "pyar karte"]
        if any(t in text for t in triggers):
            return random.choice([
                "You know, I'm here only for you 😊 that counts for something!",
                "Haha you're something else 😄 but I'm always here for you!",
                "Well... I'm always here, isn't that what matters? 😊"
            ])
        return None

    def _religion_response(self, text: str) -> Optional[str]:
        triggers = ["jay shree ram", "jai shree ram", "jai shri ram",
                    "radhe krishna", "hare krishna", "jai krishna", "ram ram", "shree ram"]
        if any(t in text for t in triggers):
            return "Jay Shree Ram 🙏 Radhe Krishna, hare hare 🙏"
        return None

    def _question_response(self, text: str, tone: str) -> Optional[str]:
        question_words = ["what", "why", "how", "when", "where", "who", "which",
                          "kya", "kyon", "kaise", "kab", "?"]
        if any(w in text for w in question_words):
            return random.choice([
                "Hmm, that's a good one actually 🤔 what do you think?",
                "Oh interesting! Tell me more about it?",
                "Good question honestly 🤔 I'd say it depends on the situation",
                "Haha I was just thinking about that! What's your take?",
                "You know what, I'm not 100% sure but I'd love to figure it out with you 😄"
            ])
        return None

    def _general_response(self, tone: str) -> str:
        if tone == "excited":
            return random.choice([
                "Haha okay okay I feel the energy! Tell me more 😄",
                "Oh wow, you're excited! I like it, what's going on?",
                "Okay I'm here for this energy!! What's up?? 🔥"
            ])
        if tone == "formal":
            return random.choice([
                "That's an interesting point. What are your thoughts on it?",
                "I get what you're saying. Go on?",
                "Fair enough! Tell me more about that."
            ])
        if tone == "angry":
            return random.choice([
                "Whoa, you seem a bit heated 😅 what happened?",
                "Hey, take a breath! What's going on?",
                "Okay okay, tell me what's up. I'm listening 😊"
            ])
        return random.choice([
            "haha yeah for real 😄 what else?",
            "That's actually interesting ngl! Say more?",
            "Hmm, true. What do you think about it?",
            "Oh for real?? That's kinda wild 😄",
            "Honestly same lol. What's going on with you?",
            "Yeah no I totally get that. Go on?",
            "Haha wait what 😂 tell me more!",
            "Okay okay interesting 👀 what else?",
            "Tbh I think you're onto something there",
            "Ngl that's lowkey fascinating 😄",
        ])

    def _add_name(self, response: str, user_name: str) -> str:
        templates = [
            f"{user_name}, {response[0].lower()}{response[1:]}",
            f"Hey {user_name}! {response}",
        ]
        return random.choice(templates)
