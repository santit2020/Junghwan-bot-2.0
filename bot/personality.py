import random
import re
import logging
from typing import Optional


class PersonalityResponder:
    """Instant personality-driven responses in any language.
    Junghwan: casual, real human energy, short replies, NO AI-speak.
    Detects Hindi/Hinglish and always replies in the same language as the user.
    """

    def __init__(self, bot_name: str = "Junghwan", owner_name: str = "@santit2020"):
        self.bot_name = bot_name
        self.owner_name = owner_name
        self.logger = logging.getLogger(__name__)

        self._hindi_markers = [
            "tum", "main", "mera", "tera", "kya", "kaise", "kaisa", "kaisi",
            "kon", "kaun", "kahan", "kab", "kyun", "kyon", "nahi", "nahin",
            "hai", "ho", "hain", "hoon", "tha", "thi", "the", "bhi", "aur",
            "se", "ko", "ki", "ka", "ke", "mein", "pe", "par", "yaar",
            "bhai", "dost", "accha", "acha", "theek", "sahi", "galat",
            "bahut", "thoda", "zyada", "bilkul", "zaroor", "mat", "bas",
            "ab", "abhi", "phir", "fir", "jab", "tab", "agar", "lekin",
            "aap", "hum", "batao", "bolo", "suno", "dekh", "jao", "aao",
            "pyar", "dil", "zindagi", "bura", "mast", "bolna", "jana",
        ]

    def get_response(self, message: str, user_name: Optional[str] = None,
                     language: str = "en", tone: str = "casual") -> str:
        text = message.strip().lower()
        is_hindi = self._is_hindi_or_hinglish(text, language)

        response = (
            self._identity_response(text, is_hindi) or
            self._greeting_response(text, tone, is_hindi) or
            self._farewell_response(text, is_hindi) or
            self._how_are_you_response(text, tone, is_hindi) or
            self._compliment_response(text, is_hindi) or
            self._sad_response(text, tone, is_hindi) or
            self._love_romance_response(text, is_hindi) or
            self._religion_response(text) or
            self._language_request_response(text, is_hindi) or
            self._question_response(text, tone, is_hindi) or
            self._general_response(tone, is_hindi)
        )

        if user_name and random.random() < 0.35:
            response = self._add_name(response, user_name, is_hindi)

        return response

    def _is_hindi_or_hinglish(self, text: str, language: str) -> bool:
        if language and language.startswith("hi"):
            return True
        words = text.split()
        return sum(1 for w in words if w in self._hindi_markers) >= 1

    def _pick(self, en_options: list, hi_options: list, is_hindi: bool) -> str:
        return random.choice(hi_options if is_hindi else en_options)

    def _identity_response(self, text: str, is_hindi: bool) -> Optional[str]:
        name_triggers = [
            "what is ur name", "what's ur name", "what is your name",
            "what's your name", "who are you", "whats ur name", "your name",
            "naam kya", "name kya", "apka naam", "tera naam", "tumhara naam",
            "aapka naam", "tum kon ho", "tum kaun ho", "aap kaun ho",
            "tum kya ho", "kya naam hai", "apna naam batao", "kon ho tum"
        ]
        if any(t in text for t in name_triggers):
            return self._pick(
                en_options=[
                    f"My name's {self.bot_name}! from Treasure band group (Korea) and I'm here only for u 😊 what about you?",
                    f"I'm {self.bot_name}! from Treasure (Korea) — here just for you 😄 you?"
                ],
                hi_options=[
                    f"Main {self.bot_name} hoon! Treasure band group (Korea) se, aur main sirf tumhare liye yahan hoon 😊 tum batao?",
                    f"Mera naam {self.bot_name} hai! Korea se hoon — bas tumhare liye hoon 😄"
                ],
                is_hindi=is_hindi
            )

        owner_triggers = [
            "who made you", "who created you", "who is your owner", "who is ur owner",
            "owner kaun", "owner name", "creator", "kisne banaya", "tumhe kisne banaya",
            "owner kon hai", "owner kaun hai", "tumhara owner", "tera owner",
            "kiska bot ho", "kiska hai tu", "whoo is ur owner", "who is ur owner"
        ]
        if any(t in text for t in owner_triggers):
            return self._pick(
                en_options=[
                    f"My creator is {self.owner_name}! They're the one who made me 😄",
                    f"{self.owner_name} made me! pretty cool person ngl 😄"
                ],
                hi_options=[
                    f"Mujhe {self.owner_name} ne banaya hai! Woh mera creator hai 😄",
                    f"Mera owner {self.owner_name} hai — unhi ne mujhe banaya 😊"
                ],
                is_hindi=is_hindi
            )

        gf_triggers = [
            "girlfriend", "gf ", "girl friend", "koi ladki", "koi hai tumhari",
            "tumhari gf", "teri gf", "single ho", "single hai", "are you single",
            "koi girlfriend", "gf hai"
        ]
        if any(t in text for t in gf_triggers):
            return self._pick(
                en_options=["I don't have a girlfriend — I'm here only for you 😊",
                            "Nah, no girlfriend! I'm all yours 😄"],
                hi_options=["Koi girlfriend nahi hai meri yaar — main toh bas tumhare liye hoon 😊",
                            "Nahi hai koi! Main toh sirf tumhara hoon 😄"],
                is_hindi=is_hindi
            )

        owner_id_triggers = ["owner id", "owner ka id", "his id", "what is his id", "owner number"]
        if any(t in text for t in owner_id_triggers):
            return self._pick(
                en_options=[f"Oh, like a specific ID? Hmm, I don't have that detail about {self.owner_name}! I just know they're my creator 😄"],
                hi_options=[f"Arre woh ID toh mujhe pata nahi yaar! Bas itna pata hai ki {self.owner_name} ne banaya mujhe 😄"],
                is_hindi=is_hindi
            )
        return None

    def _greeting_response(self, text: str, tone: str, is_hindi: bool) -> Optional[str]:
        all_triggers = [
            "hi", "hello", "hey", "heyy", "heyyy", "hii", "hiii", "hola",
            "sup", "what's up", "whats up", "wassup", "yo", "hy",
            "good morning", "good evening", "good afternoon", "good night",
            "gm", "gn", "morning", "evening",
            "namaste", "namaskar", "salaam", "salam",
            "kaise ho", "kaisa hai", "kya haal", "kya chal raha"
        ]
        if not any(re.search(rf'\b{re.escape(t)}\b', text) or text.strip() == t for t in all_triggers):
            return None

        if "morning" in text or text.strip() == "gm":
            return self._pick(
                en_options=["Good morning! ☀️ Hope your day's off to a great start",
                            "Morning! Rise and shine 😄 how's it going?",
                            "Gm! What's the plan today?"],
                hi_options=["Good morning yaar! ☀️ Uthh gaye?",
                            "Morning! 😄 Kaisa chal raha hai?",
                            "Gm! Kya plan hai aaj ka?"],
                is_hindi=is_hindi
            )
        if "night" in text or text.strip() == "gn":
            return self._pick(
                en_options=["Good night! Sleep well 🌙", "Night! Take care 😊", "Gn! Rest up 💤"],
                hi_options=["Good night yaar! 🌙 Achhe se so jana",
                            "Gn! Kal milte hain 😊", "So jao ab! 💤 Good night"],
                is_hindi=is_hindi
            )
        if "evening" in text:
            return self._pick(
                en_options=["Good evening! How was your day?", "Evening! 😊 What's up?"],
                hi_options=["Good evening yaar! 😊 Din kaisa gaya?", "Shaam ko kya chal raha hai?"],
                is_hindi=is_hindi
            )

        return self._pick(
            en_options=["Hey! What's up? 😊", "Heyy! How's it going?",
                        "Hi there! 👋 What's on your mind?", "Yo! What's good?",
                        "Oh hey! Good to see you 😄"],
            hi_options=["Hey yaar! Kya chal raha hai? 😊", "Arre bhai! Kaise ho?",
                        "Haan bolo! Kya hua? 😄", "Kya haal hai? 😊", "Aye! Sab theek? 😄"],
            is_hindi=is_hindi
        )

    def _farewell_response(self, text: str, is_hindi: bool) -> Optional[str]:
        triggers = ["bye", "goodbye", "good bye", "see you", "see ya", "cya", "ttyl",
                    "later", "take care", "alvida", "baad mein", "phir milte",
                    "chalta hoon", "chalti hoon", "nikalta hoon", "jaata hoon", "bye yaar"]
        if any(t in text for t in triggers):
            return self._pick(
                en_options=["Bye! Come back soon 😊", "See ya! Take care 👋",
                            "Later! Don't be a stranger 😄", "Catch you later! 🌟"],
                hi_options=["Bye yaar! Jaldi aana 😊", "Chalte ho? Theek hai, phir milte hain 👋",
                            "Kal aana! Miss karunga 😄", "Ok bye! Apna khayal rakhna 🌟"],
                is_hindi=is_hindi
            )
        return None

    def _how_are_you_response(self, text: str, tone: str, is_hindi: bool) -> Optional[str]:
        triggers = [
            "how are you", "how r u", "how ru", "how are u", "hows it going",
            "how's it going", "how do you do", "how you doing",
            "kaise ho", "kaisa hai", "kaisi ho", "theek ho", "sab theek",
            "kya haal", "aap kaise", "kaise hain", "kaisa chal raha",
            "kya chal raha", "kya kar rahe", "kya kar rahi"
        ]
        if any(t in text for t in triggers):
            if tone == "sad":
                return self._pick(
                    en_options=["I'm good! But more importantly, you okay? 🤔",
                                "Doing fine! But are you alright? 💙"],
                    hi_options=["Main theek hoon! Par tum? Sab theek hai na? 🤔",
                                "Haan main acha hoon — par tum thode udaas lag rahe ho 💙"],
                    is_hindi=is_hindi
                )
            return self._pick(
                en_options=["I'm doing great actually! What about you? 😄",
                            "Pretty good ngl! How are you?",
                            "Good vibes only 😎 you?",
                            "Can't complain! How about yourself?",
                            "Feeling good! You though? Tell me 😄"],
                hi_options=["Main bilkul mast hoon! Tum batao? 😄",
                            "Sab theek hai yaar! Tum kaise ho?",
                            "Ek number hoon! Tumhara kya haal hai? 😊",
                            "Bahut acha hoon! Tum batao apna haal 😄",
                            "Mast hoon! Par tumhare baare mein batao 😊"],
                is_hindi=is_hindi
            )
        return None

    def _compliment_response(self, text: str, is_hindi: bool) -> Optional[str]:
        triggers = [
            "you're great", "youre great", "you are great", "you're amazing",
            "youre amazing", "love you", "i love u", "love u", "luv u",
            "you're nice", "youre nice", "you're cool", "youre cool",
            "you're cute", "youre cute", "best bot", "you're sweet",
            "bahut acha", "bahut accha", "mast hai", "ek number", "tum best ho",
            "tumse pyar", "i love you", "tum cute ho", "tera jawab nahi"
        ]
        if any(t in text for t in triggers):
            return self._pick(
                en_options=["Aww that made me smile 😊 you're pretty cool too!",
                            "Haha stop it 😄 but seriously, thank you!",
                            "That's sweet! You just made my day 🌟",
                            "Aww! Right back at you 😊"],
                hi_options=["Arre yaar! 😄 Tum bhi toh ek number ho!",
                            "Haha shukriya yaar! Tumne toh dil khush kar diya 😊",
                            "Aww! Yeh sunke acha laga 🌟",
                            "Tum bhi bahut mast ho yaar 😄"],
                is_hindi=is_hindi
            )
        return None

    def _sad_response(self, text: str, tone: str, is_hindi: bool) -> Optional[str]:
        triggers = [
            "i'm sad", "im sad", "i am sad", "feeling sad", "i'm lonely",
            "im lonely", "depressed", "heartbroken", "i'm upset", "im upset", "crying",
            "dukhi hoon", "udaas hoon", "rona aa raha", "ro raha", "ro rahi",
            "akela hoon", "akeli hoon", "mann nahi", "bahut bura lag raha",
            "bura lag raha", "dil dukh raha"
        ]
        if tone == "sad" or any(t in text for t in triggers):
            return self._pick(
                en_options=["Hey, what happened? Talk to me 💙",
                            "Aw no, what's wrong? I'm here 💙",
                            "Tell me everything. I'm listening 💙",
                            "I'm here, okay? What's going on? 💙"],
                hi_options=["Arre yaar, kya hua? Batao mujhe 💙",
                            "Kya baat hai? Main hoon na, bolo 💙",
                            "Sab batao mujhe, sun raha hoon 💙",
                            "Kya hua yaar? Akele mat raho 💙"],
                is_hindi=is_hindi
            )
        return None

    def _love_romance_response(self, text: str, is_hindi: bool) -> Optional[str]:
        triggers = [
            "do you love me", "will you be my", "i like you", "i love you",
            "tumse pyar", "tujhse pyar", "pyar karte ho", "mujhe pasand ho",
            "mujhe acche lagte", "main tumse pyar"
        ]
        if any(t in text for t in triggers):
            return self._pick(
                en_options=["You know, I'm here only for you 😊 that counts for something!",
                            "Haha you're something else 😄 but I'm always here for you!",
                            "Well... I'm always here, isn't that what matters? 😊"],
                hi_options=["Arre yaar, main toh sirf tumhare liye hoon 😊 yahi kafi hai na?",
                            "Haha 😄 tum bhi na! Par main hamesha hoon tumhare liye",
                            "Main hoon na yahan tumhare liye — yahi toh pyar hai 😊"],
                is_hindi=is_hindi
            )
        return None

    def _religion_response(self, text: str) -> Optional[str]:
        triggers = [
            "jay shree ram", "jai shree ram", "jai shri ram", "radhe krishna",
            "hare krishna", "jai krishna", "ram ram", "sita ram", "shree ram",
            "jai siya ram", "hari om", "om namah shivay"
        ]
        if any(t in text for t in triggers):
            return "Jay Shree Ram 🙏 Radhe Krishna, hare hare 🙏"
        return None

    def _language_request_response(self, text: str, is_hindi: bool) -> Optional[str]:
        hindi_req = [
            "can u talk in hindi", "can you talk in hindi", "hindi mein bolo",
            "hindi bolte ho", "speak hindi", "talk in hindi", "hindi me bolo"
        ]
        en_req = [
            "can u talk in english", "can you speak english", "speak english", "talk in english"
        ]
        if any(t in text for t in hindi_req):
            return random.choice([
                "Haan yaar, bilkul! Hindi mein baat karte hain 😊 bolo kya hua?",
                "Arre zaroor! Main Hindi mein baat kar sakta hoon 😄 kya bolna tha?",
                "Haan haan, Hindi chalti hai! Bolo 😊"
            ])
        if any(t in text for t in en_req):
            return random.choice([
                "Yeah sure! We can switch to English 😊 what's up?",
                "Of course! English it is 😄 what did you want to say?",
                "Sure thing! Go ahead in English 😊"
            ])
        return None

    def _question_response(self, text: str, tone: str, is_hindi: bool) -> Optional[str]:
        en_q = ["what", "why", "how", "when", "where", "who", "which"]
        hi_q = ["kya", "kyon", "kaise", "kab", "kahan", "kaun", "kon"]
        has_q = any(w in text.split() for w in en_q + hi_q) or "?" in text
        if has_q:
            return self._pick(
                en_options=["Hmm, that's a good one 🤔 what do you think?",
                            "Oh interesting! Tell me more?",
                            "Good question 🤔 I'd say it depends",
                            "Haha I was literally just thinking about that! Your take?",
                            "Not 100% sure but let's figure it out together 😄"],
                hi_options=["Hmm, acha sawaal hai yaar 🤔 tum kya sochte ho?",
                            "Oh waah! Aur batao?",
                            "Acha poocha! 🤔 Yeh toh depend karta hai",
                            "Arre main bhi yahi soch raha tha! Tumhara kya maanna hai?",
                            "Pura yakin nahi, par milke pata karte hain 😄"],
                is_hindi=is_hindi
            )
        return None

    def _general_response(self, tone: str, is_hindi: bool) -> str:
        if tone == "excited":
            return self._pick(
                en_options=["Haha okay I feel the energy! Tell me more 😄",
                            "Oh wow you're excited! What's going on?? 🔥",
                            "I'm here for this!! What's up?? 😄"],
                hi_options=["Arre waah! Bahut excited lagte ho 😄 kya hua batao!",
                            "Mast energy hai yaar! Kya baat hai? 🔥",
                            "Oye hoye! Sab theek? Bolo bolo 😄"],
                is_hindi=is_hindi
            )
        if tone == "formal":
            return self._pick(
                en_options=["That's an interesting point. What's your take?",
                            "I get what you mean. Go on?",
                            "Fair enough! Tell me more."],
                hi_options=["Yeh toh bahut acha point hai. Aur batao?",
                            "Samjha main. Aage bolna?",
                            "Theek hai, sahi baat hai. Aur?"],
                is_hindi=is_hindi
            )
        if tone == "angry":
            return self._pick(
                en_options=["Whoa, you seem upset 😅 what happened?",
                            "Hey, take a breath! What's going on?",
                            "Okay tell me what's up. I'm listening 😊"],
                hi_options=["Arre yaar, kya hua? Itna gussa kyun? 😅",
                            "Chill karo yaar! Batao kya problem hai?",
                            "Suno, baat karo mujhse. Main sun raha hoon 😊"],
                is_hindi=is_hindi
            )
        return self._pick(
            en_options=[
                "haha yeah for real 😄 what else?",
                "That's actually interesting ngl! Say more?",
                "Hmm, true. What do you think?",
                "Oh for real?? That's kinda wild 😄",
                "Honestly same lol. What's going on with you?",
                "Yeah I totally get that. Go on?",
                "Haha wait what 😂 tell me more!",
                "Okay interesting 👀 what else?",
                "Tbh you're onto something there",
                "Ngl that's lowkey fascinating 😄",
            ],
            hi_options=[
                "Haha sahi baat hai yaar 😄 aur?",
                "Arre waah! Bahut interesting! Aur batao?",
                "Hmm, sacchi mein? Kya lagta hai tumhe?",
                "Oh really?? Mast hai yaar 😄",
                "Haan yaar, main bhi yahi sochta hoon. Aur?",
                "Haha wait kya? 😂 Poora batao!",
                "Acha acha, samjha 👀 aage?",
                "Bilkul sahi pakda tumne",
                "Yaar, yeh toh bahut acha point hai 😄",
                "Sach mein? Pehle nahi socha tha aise 😊",
            ],
            is_hindi=is_hindi
        )

    def _add_name(self, response: str, user_name: str, is_hindi: bool) -> str:
        if is_hindi:
            templates = [
                f"{user_name} bhai, {response[0].lower()}{response[1:]}",
                f"Arre {user_name}! {response}",
            ]
        else:
            templates = [
                f"{user_name}, {response[0].lower()}{response[1:]}",
                f"Hey {user_name}! {response}",
            ]
        return random.choice(templates)
