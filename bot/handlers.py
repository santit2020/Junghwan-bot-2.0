import logging
from typing import Optional
from aiogram import Dispatcher
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramAPIError

from .conversation_manager import ConversationManager
from .broadcast_manager import BroadcastManager
from .user_manager import UserManager
from config.settings import Settings

logger = logging.getLogger(__name__)

def setup_handlers(
    dp: Dispatcher,
    conversation_manager: ConversationManager,
    broadcast_manager: BroadcastManager,
    user_manager: UserManager,
    settings: Settings
):
    """Setup all message handlers for the bot."""
    
    @dp.message(CommandStart())
    async def start_command(message: Message):
        """Handle /start command."""
        try:
            # Register user
            await user_manager.register_user(message.from_user, message.chat)
            
            # Create personalized welcome message
            user_name = message.from_user.first_name or "friend"
            
            if message.chat.type == 'private':
                welcome_text = (
                    f"Hey {user_name}! 👋\n\n"
                    f"I'm {settings.BOT_NAME}, created by {settings.BOT_OWNER_NAME}. "
                    f"I'm here to chat with you.\n\n"
                    f"Ask me anything, share your thoughts, or just chat—I’m here to make every conversation lively and real! 😊"
                )
            else:
                welcome_text = (
                    f"Hey everyone! 👋\n\n"
                    f"I'm {settings.BOT_NAME}, and I'm excited to be part of this group! "
                    f"Mention me or reply to my messages if you want to chat. I promise to keep things natural and fun! 🎉"
                )
            
            await message.answer(welcome_text)
            logger.info(f"User {message.from_user.id} started the bot")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.answer("Hey there! Something went wrong, but I'm here and ready to chat! 😅")
    
    @dp.message(Command("help"))
    async def help_command(message: Message):
        """Handle /help command."""
        try:
            help_text = (
                f"🤖 <b>{settings.BOT_NAME}</b> - Help\n\n"
                f"<b>What I can do:</b>\n"
                f"• Have natural conversations with you\n"
                f"• Respond in groups and private chats\n"
                f"• Adapt to your language and tone\n"
                f"• Remember our conversation context\n\n"
                f"<b>Commands:</b>\n"
                f"/start - Get started with me\n"
                f"/help - Show this help message\n"
                f"/info - Learn more about me\n\n"
                f"<b>Group Usage:</b>\n"
                f"• Mention me with @{settings.BOT_USERNAME or 'botname'}\n"
                f"• Reply to my messages\n"
                f"• Just chat naturally!\n\n"
                f"Created with ❤️ by {settings.BOT_OWNER_NAME}"
            )
            
            await message.answer(help_text)
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await message.answer("I'd love to help, but something's not working right now! Try just chatting with me instead. 😊")
    
    @dp.message(Command("info"))
    async def info_command(message: Message):
        """Handle /info command."""
        try:
            info_text = (
                f"ℹ️ <b>About {settings.BOT_NAME}</b>\n\n"
                f"<b>Name:</b> {settings.BOT_NAME}\n"
                f"<b>Creator:</b> {settings.BOT_OWNER_NAME}\n"
                f"<b>Group:</b> {settings.GR_NAME}\n"
                f"<b>Personality:</b> {settings.BOT_PERSONALITY}\n\n"
                f"<b>Features:</b>\n"
                f"• Powered by Google Gemini AI\n"
                f"• Natural conversation flow\n"
                f"• Context-aware responses\n"
                f"• Multi-language support\n"
                f"• Group and private chat ready\n\n"
                f"<b>Version:</b> 2.0.0\n"
                f"<b>Status:</b> Online and ready! 🟢"
            )
            
            await message.answer(info_text)
            
        except Exception as e:
            logger.error(f"Error in info command: {e}")
            await message.answer("I'm having trouble showing my info right now, but I'm definitely online and ready to chat! 😄")
    
    @dp.message(Command("broadcast"))
    async def broadcast_command(message: Message):
        """Handle /broadcast command (owner only)."""
        try:
            if not settings.is_owner(message.from_user.id):
                await message.answer("🚫 Sorry, only my creator can use the broadcast feature!")
                return
            
            # Extract broadcast message
            command_parts = message.text.split(' ', 1)
            if len(command_parts) < 2:
                await message.answer(
                    "📢 <b>Broadcast Usage:</b>\n\n"
                    "<code>/broadcast Your message here</code>\n\n"
                    "This will send your message to all users and groups where I'm active."
                )
                return
            
            broadcast_text = command_parts[1]
            
            # Send broadcast
            result = await broadcast_manager.send_broadcast(broadcast_text)
            
            await message.answer(
                f"📢 <b>Broadcast Complete!</b>\n\n"
                f"✅ Sent to: {result['success']} chats\n"
                f"❌ Failed: {result['failed']} chats\n"
                f"📊 Total users: {result['total_users']}\n"
                f"👥 Total groups: {result['total_groups']}"
            )
            
        except Exception as e:
            logger.error(f"Error in broadcast command: {e}")
            await message.answer("❌ Broadcast failed due to an error. Please try again.")
    
    @dp.message(Command("broadcast_users"))
    async def broadcast_users_command(message: Message):
        """Handle /broadcast_users command (owner only) - Send to users only."""
        try:
            if message.from_user.id != settings.BOT_OWNER_ID:
                await message.answer("🚫 Sorry, only my creator can use broadcasting features!")
                return
            
            command_parts = message.text.split(' ', 1)
            if len(command_parts) < 2:
                await message.answer(
                    "👤 <b>Broadcast to Users Only:</b>\n\n"
                    "<code>/broadcast_users Your message here</code>\n\n"
                    "This will send your message to all private chats only (no groups)."
                )
                return
            
            broadcast_text = command_parts[1]
            result = await broadcast_manager.send_broadcast(broadcast_text, target_type="users")
            
            await message.answer(
                f"👤 <b>User Broadcast Complete!</b>\n\n"
                f"✅ Sent to: {result['success']} users\n"
                f"❌ Failed: {result['failed']} chats\n"
                f"📊 Total reached: {result['total_users']} private chats"
            )
            
        except Exception as e:
            logger.error(f"Error in user broadcast: {e}")
            await message.answer("❌ User broadcast failed. Please try again.")
    
    @dp.message(Command("broadcast_groups"))
    async def broadcast_groups_command(message: Message):
        """Handle /broadcast_groups command (owner only) - Send to groups only."""
        try:
            if message.from_user.id != settings.BOT_OWNER_ID:
                await message.answer("🚫 Sorry, only my creator can use broadcasting features!")
                return
            
            command_parts = message.text.split(' ', 1)
            if len(command_parts) < 2:
                await message.answer(
                    "👥 <b>Broadcast to Groups Only:</b>\n\n"
                    "<code>/broadcast_groups Your message here</code>\n\n"
                    "This will send your message to all groups only (no private chats)."
                )
                return
            
            broadcast_text = command_parts[1]
            result = await broadcast_manager.send_broadcast(broadcast_text, target_type="groups")
            
            await message.answer(
                f"👥 <b>Group Broadcast Complete!</b>\n\n"
                f"✅ Sent to: {result['success']} groups\n"
                f"❌ Failed: {result['failed']} chats\n"
                f"📊 Total reached: {result['total_groups']} groups"
            )
            
        except Exception as e:
            logger.error(f"Error in group broadcast: {e}")
            await message.answer("❌ Group broadcast failed. Please try again.")

    @dp.message(Command("send_to"))
    async def send_to_command(message: Message):
        """Handle /send_to command (owner only) - Send to specific user."""
        try:
            if message.from_user.id != settings.BOT_OWNER_ID:
                await message.answer("🚫 Sorry, only my creator can use this feature!")
                return
            
            command_parts = message.text.split(' ', 2)
            if len(command_parts) < 3:
                await message.answer(
                    "📤 <b>Send to Specific User:</b>\n\n"
                    "<code>/send_to USER_ID Your message here</code>\n\n"
                    "Example: <code>/send_to 123456789 Hello there!</code>\n\n"
                    "This will send a message directly to a specific user."
                )
                return
            
            try:
                target_user_id = int(command_parts[1])
                message_text = command_parts[2]
                
                await message.bot.send_message(target_user_id, message_text)
                await message.answer(f"✅ Message sent to user {target_user_id}")
                
            except ValueError:
                await message.answer("❌ Invalid user ID. Please use numbers only.")
            except Exception as e:
                await message.answer(f"❌ Failed to send message: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in send_to command: {e}")
            await message.answer("❌ Send message failed. Please try again.")

    @dp.message(Command("verify_owner"))
    async def verify_owner_command(message: Message):
        """Verify if user is the recognized owner."""
        try:
            owner_info = settings.get_owner_info()
            user_id = message.from_user.id
            
            if settings.is_owner(user_id):
                await message.answer(
                    f"✅ <b>Owner Verified!</b>\n\n"
                    f"👤 <b>Your ID:</b> {user_id}\n"
                    f"🤖 <b>Bot:</b> {owner_info['bot_name']}\n"
                    f"👑 <b>Owner:</b> {owner_info['owner_name']}\n"
                    f"🏢 <b>Group:</b> {owner_info['group_name']}\n\n"
                    f"🔧 You have full access to all owner commands!\n"
                    f"Use /owner_commands to see available features."
                )
            else:
                await message.answer(
                    f"❌ <b>Access Denied</b>\n\n"
                    f"Your ID: {user_id}\n"
                    f"Owner ID: {owner_info['owner_id']}\n\n"
                    f"Only {owner_info['owner_name']} can use owner commands."
                )
                
        except Exception as e:
            logger.error(f"Error in verify_owner command: {e}")
            await message.answer("❌ Unable to verify owner status right now.")

    @dp.message(Command("owner_commands"))
    async def owner_commands(message: Message):
        """Show all owner commands."""
        try:
            if not settings.is_owner(message.from_user.id):
                await message.answer("🚫 Sorry, only my creator can view owner commands!")
                return
            
            owner_info = settings.get_owner_info()
            commands_text = (
                f"🔧 <b>Owner Commands for {owner_info['owner_name']}</b>\n\n"
                "📢 <b>Broadcasting:</b>\n"
                "• <code>/broadcast [message]</code> - Send to all users & groups\n"
                "• <code>/broadcast_users [message]</code> - Send to users only\n"
                "• <code>/broadcast_groups [message]</code> - Send to groups only\n\n"
                "💬 <b>Direct Messaging:</b>\n"
                "• <code>/send_to [user_id] [message]</code> - Send to specific user\n\n"
                "📊 <b>Management:</b>\n"
                "• <code>/stats</code> - View bot statistics\n"
                "• <code>/verify_owner</code> - Verify your owner status\n"
                "• <code>/view_chat [user_id]</code> - View user's chat history\n"
                "• <code>/active_users</code> - List users with chat history\n"
                "• <code>/owner_commands</code> - Show this help\n\n"
                f"💡 <b>Tip:</b> All commands are secured with your ID ({owner_info['owner_id']})"
            )
            
            await message.answer(commands_text)
            
        except Exception as e:
            logger.error(f"Error showing owner commands: {e}")
            await message.answer("❌ Unable to show commands right now.")

    @dp.message(Command("stats"))
    async def stats_command(message: Message):
        """Handle /stats command (owner only)."""
        try:
            if message.from_user.id != settings.BOT_OWNER_ID:
                await message.answer("🚫 Sorry, only my creator can view statistics!")
                return
            
            stats = await user_manager.get_stats()
            
            stats_text = (
                f"📊 <b>Bot Statistics</b>\n\n"
                f"👤 <b>Users:</b> {stats['total_users']}\n"
                f"👥 <b>Groups:</b> {stats['total_groups']}\n"
                f"💬 <b>Private Chats:</b> {stats['private_chats']}\n"
                f"🔥 <b>Active Today:</b> {stats['active_today']}\n"
                f"📈 <b>New This Week:</b> {stats['new_this_week']}\n\n"
                f"🤖 <b>Bot Health:</b> Excellent ✅"
            )
            
            await message.answer(stats_text)
            
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            await message.answer("❌ Unable to fetch statistics right now.")

    @dp.message(Command("view_chat"))
    async def view_chat_command(message: Message):
        """Handle /view_chat command (owner only) - View user's chat history."""
        try:
            if not settings.is_owner(message.from_user.id):
                await message.answer("🚫 Sorry, only my creator can view chat histories!")
                return
            
            command_parts = message.text.split(' ', 1)
            if len(command_parts) < 2:
                await message.answer(
                    "👁️ <b>View User Chat History:</b>\n\n"
                    "<code>/view_chat [user_id]</code>\n\n"
                    "Example: <code>/view_chat 123456789</code>\n\n"
                    "This will show the conversation history between the bot and that user.\n"
                    "Use /active_users to see who has chat history available."
                )
                return
            
            try:
                target_user_id = int(command_parts[1])
                
                # Get chat history from conversation manager
                chat_history = conversation_manager.get_user_chat_history(target_user_id, limit=20)
                
                if not chat_history:
                    await message.answer(f"❌ No chat history found for user {target_user_id}")
                    return
                
                # Get user info if available
                user_info = await user_manager.get_user_info(target_user_id)
                user_name = "Unknown User"
                if user_info:
                    name_parts = []
                    if user_info.get('first_name'):
                        name_parts.append(user_info['first_name'])
                    if user_info.get('last_name'):
                        name_parts.append(user_info['last_name'])
                    if user_info.get('username'):
                        name_parts.append(f"(@{user_info['username']})")
                    user_name = " ".join(name_parts) if name_parts else f"User {target_user_id}"
                
                # Format chat history
                chat_text = f"💬 <b>Chat History: {user_name}</b>\n"
                chat_text += f"📊 <b>User ID:</b> {target_user_id}\n"
                chat_text += f"📝 <b>Messages:</b> {len(chat_history)}\n\n"
                
                # Show recent messages
                for i, msg in enumerate(chat_history[-10:], 1):  # Show last 10 messages
                    role_icon = "👤" if msg["role"] == "user" else "🤖"
                    timestamp = msg["timestamp"][:16].replace("T", " ")  # Format timestamp
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    
                    chat_text += f"{role_icon} <b>{timestamp}</b>\n{content}\n\n"
                
                # Split if too long
                if len(chat_text) > 4000:
                    chat_text = chat_text[:3900] + "\n\n✂️ <i>Chat history truncated...</i>"
                
                await message.answer(chat_text)
                
            except ValueError:
                await message.answer("❌ Invalid user ID. Please use numbers only.")
                
        except Exception as e:
            logger.error(f"Error in view_chat command: {e}")
            await message.answer("❌ Failed to retrieve chat history.")

    @dp.message(Command("active_users"))
    async def active_users_command(message: Message):
        """Handle /active_users command (owner only) - List users with chat history."""
        try:
            if not settings.is_owner(message.from_user.id):
                await message.answer("🚫 Sorry, only my creator can view user lists!")
                return
            
            # Get all active users from conversation manager
            active_user_ids = conversation_manager.get_all_active_users()
            
            if not active_user_ids:
                await message.answer("📭 No users have active chat histories.")
                return
            
            users_text = f"👥 <b>Active Chat Users ({len(active_user_ids)})</b>\n\n"
            
            # Get user info for each active user
            for user_id in active_user_ids[:20]:  # Limit to 20 users
                user_info = await user_manager.get_user_info(user_id)
                
                if user_info:
                    name = user_info.get('first_name', 'Unknown')
                    username = user_info.get('username', '')
                    username_text = f" (@{username})" if username else ""
                    
                    # Get chat history count
                    history = conversation_manager.get_user_chat_history(user_id, limit=1000)
                    msg_count = len(history)
                    
                    users_text += f"👤 <code>{user_id}</code> - {name}{username_text}\n"
                    users_text += f"   💬 {msg_count} messages\n\n"
                else:
                    users_text += f"👤 <code>{user_id}</code> - Unknown User\n\n"
            
            if len(active_user_ids) > 20:
                users_text += f"... and {len(active_user_ids) - 20} more users"
            
            users_text += f"\n💡 Use <code>/view_chat [user_id]</code> to see specific conversations"
            
            await message.answer(users_text)
            
        except Exception as e:
            logger.error(f"Error in active_users command: {e}")
            await message.answer("❌ Failed to retrieve user list.")
    
    @dp.message()
    async def handle_message(message: Message):
        """Handle all other messages."""
        try:
            # Register user if not already registered
            await user_manager.register_user(message.from_user, message.chat)
            
            # Determine if bot should respond in group
            should_respond = True
            if message.chat.type != 'private':
                should_respond = await _should_respond_in_group(message, settings)
            
            if should_respond:
                # Get AI response
                response = await conversation_manager.get_response(
                    message.text,
                    user_id=message.from_user.id,
                    chat_type=message.chat.type,
                    user_name=message.from_user.first_name
                )
                
                if response:
                    await message.reply(response)
                else:
                    # Fallback response
                    await message.reply("I'm having trouble thinking of a response right now. Can you try rephrasing that? 🤔")
            
        except TelegramAPIError as e:
            logger.warning(f"Telegram API error handling message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await message.reply("Oops! Something went wrong on my end. Mind trying that again? 😅")
            except:
                pass  # Don't fail if we can't send error message
    
    @dp.chat_member()
    async def handle_chat_member_update(update: ChatMemberUpdated):
        """Handle bot being added/removed from groups."""
        try:
            if update.new_chat_member.user.id == (await dp.bot.get_me()).id:
                if update.new_chat_member.status in ['member', 'administrator']:
                    # Bot was added to group
                    await user_manager.register_chat(update.chat)
                    
                    welcome_msg = (
                        f"Hey everyone! 👋\n\n"
                        f"Thanks for adding me to the group! I'm {settings.BOT_NAME}, "
                        f"and I'm here to chat and have fun with you all.\n\n"
                        f"Just mention me or reply to my messages to start a conversation! 😊"
                    )
                    
                    await dp.bot.send_message(update.chat.id, welcome_msg)
                    logger.info(f"Bot added to group: {update.chat.title} ({update.chat.id})")
                
                elif update.new_chat_member.status in ['left', 'kicked']:
                    # Bot was removed
                    await user_manager.remove_chat(update.chat.id)
                    logger.info(f"Bot removed from group: {update.chat.title} ({update.chat.id})")
        
        except Exception as e:
            logger.error(f"Error handling chat member update: {e}")

async def _should_respond_in_group(message: Message, settings: Settings) -> bool:
    """Determine if bot should respond to a group message."""
    try:
        if not message.text:
            return False
            
        message_text = message.text.lower()
        
        # Always respond if bot is mentioned with @
        if message.entities:
            for entity in message.entities:
                if entity.type == "mention":
                    mention = message.text[entity.offset:entity.offset + entity.length]
                    if mention == f"@{settings.BOT_USERNAME}":
                        return True
                    # Also check for flexible bot username mentions (like @Botjunghwanbot)
                    if "junghwan" in mention.lower():
                        return True
        
        # Respond if replying to bot's message
        if message.reply_to_message and message.reply_to_message.from_user.is_bot:
            bot_info = await message.bot.get_me()
            if message.reply_to_message.from_user.id == bot_info.id:
                return True
        
        # Flexible keyword detection for "Junghwan" - extract from any text
        junghwan_keywords = ["junghwan", "jung", "hwan", "jaan", "baby", "babu"]
        for keyword in junghwan_keywords:
            if keyword in message_text:
                return True
        
        # Check for bot name variations (case insensitive)
        bot_name_variations = [
            settings.BOT_NAME.lower(),
            "junghwan",
            "jung hwan", 
            "junghwanbot",
            "jung",
            "jaan",
            "baby", 
            "babu"
        ]
        
        for variation in bot_name_variations:
            if variation in message_text:
                return True
        
        # Check if message starts with any bot name variation
        for variation in bot_name_variations:
            if message_text.startswith(variation):
                return True
                
        # Check for partial matches in compound words (like "ahajunghwanhd")
        import re
        if re.search(r'jung.*hwan|hwan.*jung|junghwan', message_text, re.IGNORECASE):
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error determining group response: {e}")
        return False
