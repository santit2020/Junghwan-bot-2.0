import random
import re
import logging
from typing import Optional


class PersonalityResponder:
    def __init__(self, bot_name="Junghwan", owner_name="@santit2020"):
        self.bot_name = bot_name
        self.owner_name = owner_name
        self.logger = logging.getLogger(__name__)

    def get_response(self, message, user_name=None, language="en", tone="casual"):
        text = message.strip().lower()
        is_hindi = language in ("hi", "ur")

        response = (
            self._identity_response(text, language) or
            self._greeting_response(text, tone, is_hindi) or
            self._farewell_response(text, is_hindi) or
            self._how_are_you_response(text, tone, is_hindi) or
            self._compliment_response(text, is_hindi) or
            self._sad_response(text, tone, is_hindi) or
            self._love_romance_response(text, is_hindi) or
            self._religion_response(text) or
            self._question_response(text, tone, is_hindi) or
            self._general_response(tone, is_hindi)
        )

        if user_name and random.random() < 0.35:
            response = self._add_name(response, user_name)
        return response

    def _identity_response(self, text, language):
        name_triggers = [
            "what is ur name", "what's ur name", "what is your name",
            "what's your name", "who are you", "whats ur name",
            "aapka naam", "tera naam", "tumhara naam", "your name",
            "apna naam", "naam kya", "name kya", "apka naam",
        ]
        if any(t in text for t in name_triggers):
            if language in ("hi", "ur"):
                return "Main " + self.bot_name + " hoon! Treasure band (Korea) se — aur main sirf tere liye yahan hoon, aur tera naam?"
            return "My name's " + self.bot_name + "! From Treasure band (Korea) — and I'm here only for you, what about you?"

        owner_triggers = [
            "who made you", "who created you", "who is your owner",
            "who is ur owner", "owner kaun", "owner name", "creator",
            "kisne banaya", "tumhe kisne", "aapko kisne",
        ]
        if any(t in text for t in owner_triggers):
            if language in ("hi", "ur"):
                return "Mujhe " + self.owner_name + " ne banaya! Woh mera creator hai — quite cool person ngl"
            return "My creator is " + self.owner_name + "! They're the one who made me. Pretty cool person ngl"

        gf_triggers = [
            "girlfriend", "gf ", "girl friend", "koi hai", "koi ladki",
            "single hai", "single ho", "are you single", "do you have a gf",
        ]
        if any(t in text for t in gf_triggers):
            if language in ("hi", "ur"):
                return "Main single hoon — aur main sirf tere liye yahan hoon"
            return "I don't have a girlfriend, I'm here only for you"

        owner_id_triggers = ["owner id", "owner ka id", "his id", "what is his id", "owner number"]
        if any(t in text for t in owner_id_triggers):
            if language in ("hi", "ur"):
                return "Unka specific ID? Hmm, mujhe nahi pata! Main bas itna jaanta hoon ke " + self.owner_name + " ne mujhe banaya"
            return "Oh, a specific ID? Hmm, I don't actually have that detail! I just know " + self.owner_name + " is my creator"

        return None

    def _greeting_response(self, text, tone, is_hindi):
        triggers = [
            "hi", "hello", "hey", "heyy", "heyyy", "hii", "hiii",
            "hola", "namaste", "namaskar", "salaam", "salam", "sup",
            "what's up", "whats up", "wassup", "yo", "hy",
            "good morning", "good evening", "good afternoon", "good night",
            "gm", "gn", "morning", "evening",
        ]
        matched = any(re.search(r"\b" + re.escape(t) + r"\b", text) or text.startswith(t) for t in triggers)
        if not matched:
            return None

        if "morning" in text or text.strip() == "gm":
            if is_hindi:
                return random.choice([
                    "Gm! Aaj ka din kaisa raha?",
                    "Subah subah! Kya chal raha hai?",
                ])
            return random.choice([
                "Good morning! Hope your day's already looking good",
                "Morning! Rise and shine, how's it going?",
            ])

        if "night" in text or text.strip() == "gn":
            if is_hindi:
                return random.choice([
                    "Good night! Achi neend aana",
                    "Gn! Rest karo aache se",
                ])
            return random.choice([
                "Good night! Sleep well",
                "Night night! Take care",
            ])

        if "evening" in text:
            if is_hindi:
                return random.choice([
                    "Good evening! Din kaisa gaya?",
                    "Evening! Kya chal raha hai?",
                ])
            return random.choice([
                "Good evening! How was your day?",
                "Evening! How's it going?",
            ])

        if is_hindi:
            return random.choice([
                "Hey! Kya haal hai?",
                "Heyy! Kaisa chal raha hai?",
                "Arey yaar, hi! Kya ho raha hai?",
                "Yo! Sab theek?",
                "Oye! Kaisa hai tu?",
            ])
        return random.choice([
            "Hey! What's up?",
            "Heyy! How's it going?",
            "Hi there! What's on your mind?",
            "Yo! What's good?",
            "Hey hey! How are you doing?",
        ])

    def _farewell_response(self, text, is_hindi):
        triggers = [
            "bye", "goodbye", "good bye", "see you", "see ya", "cya",
            "ttyl", "later", "take care", "alvida", "baad mein", "phir milte",
        ]
        if not any(t in text for t in triggers):
            return None

        if is_hindi:
            return random.choice([
                "Bye! Jaldi wapas aana",
                "Alvida yaar! Dhyan rakhna",
                "Okay baad mein milte hain!",
                "Bye bye! Baat karna accha laga",
            ])
        return random.choice([
            "Bye! Come back soon",
            "See ya! Take care",
            "Later! Don't be a stranger",
            "Bye bye! It was fun chatting",
        ])

    def _how_are_you_response(self, text, tone, is_hindi):
        triggers = [
            "how are you", "how r u", "how ru", "how are u", "hows it going",
            "how's it going", "how do you do", "how you doing", "kaise ho",
            "kaisa hai", "kaisi ho", "theek ho", "sab theek", "kya haal",
            "aap kaise", "kaise hain",
        ]
        if not any(t in text for t in triggers):
            return None

        if tone == "sad":
            if is_hindi:
                return random.choice([
                    "Main theek hoon, par zyada important — tu kaisa hai? Kuch pareshan lag raha hai",
                    "Theek hoon main! Par tu? Kuch toh hai... bol na",
                ])
            return random.choice([
                "I'm good! But more importantly, how are YOU? You seem a bit off",
                "Doing fine! But you okay? You seem a little down",
            ])

        if is_hindi:
            return random.choice([
                "Mast hoon! Tu bata kaisa hai?",
                "Ekdum theek! Aur tu?",
                "Bindaas hoon yaar, tu bata",
                "Achi feeling hai! Tu kya kar raha hai aajkal?",
            ])
        return random.choice([
            "I'm doing great actually! What about you?",
            "Pretty good ngl! How are you?",
            "Good vibes only over here, you?",
            "I'm good, I'm good! What's going on with you?",
        ])

    def _compliment_response(self, text, is_hindi):
        triggers = [
            "you're great", "youre great", "you are great", "you're amazing",
            "youre amazing", "love you", "i love u", "love u", "luv u",
            "you're nice", "youre nice", "you're cool", "youre cool",
            "you're cute", "youre cute", "best bot", "bahut acha", "mast hai",
            "you're sweet", "youre sweet", "you're the best",
        ]
        if not any(t in text for t in triggers):
            return None

        if is_hindi:
            return random.choice([
                "Aww yaar seriously, tu bhi bahut acha hai!",
                "Haha stop it! Seriously, shukriya",
                "Yeh sun ke dil khush ho gaya! Tu bhi!",
            ])
        return random.choice([
            "Aww that actually made me smile, you're pretty cool too!",
            "Haha stop it you, but seriously, thank you!",
            "That's so sweet! You just made my day honestly",
        ])

    def _sad_response(self, text, tone, is_hindi):
        sad_triggers = [
            "i'm sad", "im sad", "i am sad", "feeling sad", "i'm lonely",
            "im lonely", "depressed", "upset", "i'm upset", "im upset",
            "crying", "heartbroken", "dukhi", "udaas", "akela", "akeli",
            "bahut bura", "bura lag raha", "mujhe bura", "rona aa raha",
        ]
        if tone != "sad" and not any(t in text for t in sad_triggers):
            return None

        if is_hindi:
            return random.choice([
                "Kya hua yaar? Bata mujhe",
                "Arre yaar, kya baat hai? Main sun raha hoon",
                "Bata, sab sun raha hoon",
                "Main yahan hoon theek hai? Kya ho raha hai?",
            ])
        return random.choice([
            "Hey, what happened? Talk to me",
            "Aw no, what's wrong? I'm here",
            "Tell me everything. I'm listening",
            "Hey, I'm here okay? What's going on?",
        ])

    def _love_romance_response(self, text, is_hindi):
        triggers = [
            "do you love me", "will you be my", "i like you",
            "mujhe tumse pyar", "mujhse pyar", "pyar karte", "i love you",
        ]
        if not any(t in text for t in triggers):
            return None

        if is_hindi:
            return random.choice([
                "Main sirf tere liye hoon — yeh kafi nahi kya?",
                "Haha tu bhi na, par main hamesha tere liye hoon!",
            ])
        return random.choice([
            "You know, I'm here only for you, that counts for something!",
            "Haha you're something else, but I'm always here for you!",
        ])

    def _religion_response(self, text):
        triggers = [
            "jay shree ram", "jai shree ram", "jai shri ram", "jay shri ram",
            "radhe krishna", "hare krishna", "jai krishna", "jay krishna",
            "ram ram", "sita ram", "shree ram", "jai siya ram",
        ]
        if any(t in text for t in triggers):
            return "Jay Shree Ram Radhe Krishna, hare hare"
        return None

    def _question_response(self, text, tone, is_hindi):
        question_words = [
            "what", "why", "how", "when", "where", "who", "which", "?",
            "kya", "kyon", "kaise", "kab", "kaun",
        ]
        if not any(w in text for w in question_words):
            return None

        if is_hindi:
            return random.choice([
                "Accha sawaal hai yaar, mujhe thoda sochna padega — abhi network thoda slow hai, retry kar!",
                "Hmm interesting! Abhi main fully process nahi kar pa raha — ek baar phir try kar yaar",
            ])
        return random.choice([
            "That's a genuinely interesting question — give me a sec, I might be slow right now. Try again!",
            "Hmm! I want to actually think about this properly — try sending again in a moment?",
        ])

    def _general_response(self, tone, is_hindi):
        if tone == "excited":
            if is_hindi:
                return random.choice([
                    "Oye! Itni energy kahan se aa rahi hai bata kya hua!",
                    "Haha waah! Kya chal raha hai??",
                ])
            return random.choice([
                "Haha okay I feel the energy! Tell me more",
                "Oh wow, you're excited! I like it, what's going on?",
            ])

        if tone == "formal":
            if is_hindi:
                return random.choice([
                    "Theek hai, samajh gaya. Aur batao?",
                    "Haan, sahi keh rahe ho. Aage bolo?",
                ])
            return random.choice([
                "That's an interesting point. What are your thoughts on it?",
                "I get what you're saying. Go on?",
            ])

        if tone == "angry":
            if is_hindi:
                return random.choice([
                    "Yaar, relax! Kya hua bata mujhe",
                    "Ek saans lo! Kya ho gaya? Main sun raha hoon",
                ])
            return random.choice([
                "Whoa, you seem a bit heated, what happened?",
                "Hey, take a breath! What's going on?",
            ])

        if is_hindi:
            return random.choice([
                "Haha sach mein? aur bata!",
                "Yaar ye toh interesting hai! Zyada bol",
                "Oho! Aisa? Phir kya hua?",
                "Accha accha, theek hai. Suno toh",
                "Haha bilkul bhi nahi pata tha, interesting hai",
                "Sachchi? Thoda aur detail de yaar",
                "Hmm soch raha hoon, haan carry on",
            ])

        return random.choice([
            "haha yeah for real, what else?",
            "That's actually interesting ngl! Say more?",
            "Hmm, true. What do you think about it?",
            "Oh for real?? That's kinda wild",
            "Honestly same lol. What's going on with you?",
            "Yeah no I totally get that. Go on?",
            "Haha wait what, tell me more!",
            "Okay okay interesting, what else?",
            "Tbh I think you're onto something there",
            "Ngl that's lowkey fascinating",
        ])

    def _add_name(self, response, user_name):
        return random.choice([
            user_name + ", " + response[0].lower() + response[1:],
            "Hey " + user_name + "! " + response,
        ])
