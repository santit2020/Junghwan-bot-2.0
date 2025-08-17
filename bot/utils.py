import logging
import re
from typing import Tuple
from langdetect import detect, DetectorFactory

# Set seed for consistent language detection
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

def detect_language_and_tone(text: str) -> Tuple[str, str]:
    """
    Detect language and tone from text.
    
    Returns:
        Tuple of (language_code, tone)
    """
    try:
        # Default values
        language = "en"
        tone = "casual"
        
        # Detect language
        try:
            detected_lang = detect(text)
            if detected_lang:
                language = detected_lang
        except:
            # Fallback to English if detection fails
            language = "en"
        
        # Detect tone through pattern analysis
        tone = detect_tone(text)
        
        return language, tone
        
    except Exception as e:
        logger.error(f"Error detecting language and tone: {e}")
        return "en", "casual"

def detect_tone(text: str) -> str:
    """
    Detect tone/style from text patterns.
    
    Returns:
        Tone identifier: formal, casual, excited, sad, angry, etc.
    """
    try:
        text_lower = text.lower()
        
        # Formal indicators
        formal_patterns = [
            r'\b(sir|madam|please|kindly|would you|could you|may i)\b',
            r'\b(thank you very much|i would appreciate|i am writing to)\b',
            r'\b(furthermore|however|nevertheless|therefore)\b'
        ]
        
        # Casual indicators
        casual_patterns = [
            r'\b(lol|haha|omg|wtf|tbh|ngl|btw|imo|afaik)\b',
            r'\b(yeah|yep|nah|gonna|wanna|gotta)\b',
            r'[!]{2,}|[?]{2,}',  # Multiple punctuation
        ]
        
        # Excited indicators
        excited_patterns = [
            r'[!]{1,}',
            r'\b(awesome|amazing|fantastic|great|love|excited|yay)\b',
            r'[A-Z]{3,}',  # CAPS
        ]
        
        # Sad/concerned indicators
        sad_patterns = [
            r'\b(sad|sorry|worried|concerned|upset|disappointed)\b',
            r'[.]{3,}',  # Ellipsis
        ]
        
        # Angry indicators
        angry_patterns = [
            r'\b(angry|mad|furious|hate|stupid|idiot|damn)\b',
            r'[!@#$%^&*]',  # Special characters
        ]
        
        # Count pattern matches
        formal_score = sum(len(re.findall(pattern, text_lower)) for pattern in formal_patterns)
        casual_score = sum(len(re.findall(pattern, text_lower)) for pattern in casual_patterns)
        excited_score = sum(len(re.findall(pattern, text_lower)) for pattern in excited_patterns)
        sad_score = sum(len(re.findall(pattern, text_lower)) for pattern in sad_patterns)
        angry_score = sum(len(re.findall(pattern, text_lower)) for pattern in angry_patterns)
        
        # Determine dominant tone
        scores = {
            "formal": formal_score,
            "casual": casual_score,
            "excited": excited_score,
            "sad": sad_score,
            "angry": angry_score
        }
        
        # Get highest scoring tone
        max_score = max(scores.values())
        if max_score > 0:
            tone = max(scores, key=scores.get)
        else:
            tone = "casual"  # Default
        
        return tone
        
    except Exception as e:
        logger.error(f"Error detecting tone: {e}")
        return "casual"

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    try:
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{3,}', '!!', text)
        text = re.sub(r'[?]{3,}', '??', text)
        text = re.sub(r'[.]{4,}', '...', text)
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error cleaning text: {e}")
        return text

def format_message_for_chat(message: str, chat_type: str) -> str:
    """Format message appropriately for chat type."""
    try:
        if chat_type == "private":
            # Private chats can be more personal
            return message
        else:
            # Group chats should be more concise
            if len(message) > 500:
                # Truncate long messages in groups
                sentences = message.split('. ')
                truncated = []
                char_count = 0
                
                for sentence in sentences:
                    if char_count + len(sentence) > 400:
                        break
                    truncated.append(sentence)
                    char_count += len(sentence)
                
                if truncated:
                    message = '. '.join(truncated)
                    if not message.endswith('.'):
                        message += '.'
                else:
                    message = message[:400] + "..."
            
            return message
            
    except Exception as e:
        logger.error(f"Error formatting message: {e}")
        return message

def extract_command_args(text: str) -> Tuple[str, str]:
    """Extract command and arguments from message."""
    try:
        parts = text.strip().split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        return command, args
        
    except Exception as e:
        logger.error(f"Error extracting command args: {e}")
        return text, ""

def is_mention(text: str, bot_username: str) -> bool:
    """Check if text contains a mention of the bot."""
    try:
        if not bot_username:
            return False
        
        mention_pattern = f"@{bot_username.lower()}"
        return mention_pattern in text.lower()
        
    except Exception as e:
        logger.error(f"Error checking mention: {e}")
        return False

def get_safe_name(user, fallback: str = "friend") -> str:
    """Get safe display name for user."""
    try:
        if hasattr(user, 'first_name') and user.first_name:
            return user.first_name
        elif hasattr(user, 'username') and user.username:
            return user.username
        else:
            return fallback
    except:
        return fallback

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    try:
        if len(text) <= max_length:
            return text
        
        truncated = text[:max_length-3]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.7:  # If we can find a good break point
            truncated = truncated[:last_space]
        
        return truncated + "..."
        
    except Exception as e:
        logger.error(f"Error truncating text: {e}")
        return text
