import logging
import json
import os
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from aiogram.types import User, Chat

class UserManager:
    """Manages user and chat data with persistent storage."""
    
    def __init__(self, data_file: str = "user_data.json"):
        self.data_file = data_file
        self.logger = logging.getLogger(__name__)
        
        # In-memory storage
        self.users: Dict[int, Dict] = {}
        self.chats: Dict[int, Dict] = {}
        self.user_activity: Dict[int, datetime] = {}
        
        # Load existing data
        self._load_data()
        
        self.logger.info(f"UserManager initialized with {len(self.users)} users and {len(self.chats)} chats")
    
    async def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user information by user ID."""
        return self.users.get(user_id)
    
    async def register_user(self, user: User, chat: Chat):
        """Register a user and their chat."""
        try:
            user_id = user.id
            chat_id = chat.id
            
            # Update user data
            self.users[user_id] = {
                "user_id": user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "language_code": user.language_code,
                "is_bot": user.is_bot,
                "first_seen": self.users.get(user_id, {}).get("first_seen", datetime.now().isoformat()),
                "last_seen": datetime.now().isoformat(),
                "message_count": self.users.get(user_id, {}).get("message_count", 0) + 1
            }
            
            # Update chat data
            await self.register_chat(chat)
            
            # Update activity
            self.user_activity[user_id] = datetime.now()
            
            # Save to file
            self._save_data()
            
            self.logger.debug(f"Registered user {user_id} in chat {chat_id}")
            
        except Exception as e:
            self.logger.error(f"Error registering user {user.id}: {e}")
    
    async def register_chat(self, chat: Chat):
        """Register a chat."""
        try:
            chat_id = chat.id
            
            self.chats[chat_id] = {
                "chat_id": chat_id,
                "chat_type": chat.type,
                "title": getattr(chat, 'title', None),
                "username": getattr(chat, 'username', None),
                "description": getattr(chat, 'description', None),
                "first_added": self.chats.get(chat_id, {}).get("first_added", datetime.now().isoformat()),
                "last_activity": datetime.now().isoformat(),
                "is_active": True
            }
            
            self._save_data()
            self.logger.debug(f"Registered chat {chat_id} ({chat.type})")
            
        except Exception as e:
            self.logger.error(f"Error registering chat {chat.id}: {e}")
    
    async def remove_chat(self, chat_id: int):
        """Remove a chat (when bot is removed from group)."""
        try:
            if chat_id in self.chats:
                self.chats[chat_id]["is_active"] = False
                self.chats[chat_id]["removed_date"] = datetime.now().isoformat()
                self._save_data()
                self.logger.info(f"Removed chat {chat_id}")
            
        except Exception as e:
            self.logger.error(f"Error removing chat {chat_id}: {e}")
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data by ID."""
        return self.users.get(user_id)
    
    async def get_chat(self, chat_id: int) -> Optional[Dict]:
        """Get chat data by ID."""
        return self.chats.get(chat_id)
    
    async def get_all_users(self) -> List[Dict]:
        """Get all registered users."""
        return list(self.users.values())
    
    async def get_all_chats(self) -> List[Dict]:
        """Get all active chats."""
        return [chat for chat in self.chats.values() if chat.get("is_active", True)]
    
    async def get_stats(self) -> Dict:
        """Get user and chat statistics."""
        try:
            now = datetime.now()
            today = now.date()
            week_ago = now - timedelta(days=7)
            
            # Total counts
            total_users = len(self.users)
            total_chats = len([c for c in self.chats.values() if c.get("is_active", True)])
            
            # Chat type breakdown
            private_chats = len([c for c in self.chats.values() 
                               if c.get("chat_type") == "private" and c.get("is_active", True)])
            group_chats = total_chats - private_chats
            
            # Activity stats
            active_today = len([uid for uid, last_activity in self.user_activity.items()
                              if last_activity.date() == today])
            
            new_this_week = len([u for u in self.users.values()
                               if datetime.fromisoformat(u.get("first_seen", now.isoformat())) > week_ago])
            
            return {
                "total_users": total_users,
                "total_groups": group_chats,
                "private_chats": private_chats,
                "active_today": active_today,
                "new_this_week": new_this_week,
                "total_chats": total_chats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {
                "total_users": len(self.users),
                "total_groups": 0,
                "private_chats": 0,
                "active_today": 0,
                "new_this_week": 0,
                "total_chats": len(self.chats)
            }
    
    async def update_user_activity(self, user_id: int):
        """Update user activity timestamp."""
        self.user_activity[user_id] = datetime.now()
        
        # Update message count
        if user_id in self.users:
            self.users[user_id]["message_count"] = self.users[user_id].get("message_count", 0) + 1
            self.users[user_id]["last_seen"] = datetime.now().isoformat()
    
    def _load_data(self):
        """Load user and chat data from file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.users = data.get("users", {})
                self.chats = data.get("chats", {})
                
                # Convert string keys to int for user/chat IDs
                self.users = {int(k): v for k, v in self.users.items()}
                self.chats = {int(k): v for k, v in self.chats.items()}
                
                # Load activity data (if available)
                activity_data = data.get("user_activity", {})
                for user_id_str, timestamp_str in activity_data.items():
                    try:
                        self.user_activity[int(user_id_str)] = datetime.fromisoformat(timestamp_str)
                    except:
                        pass  # Skip invalid timestamps
                
                self.logger.info(f"Loaded data: {len(self.users)} users, {len(self.chats)} chats")
                
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            self.users = {}
            self.chats = {}
            self.user_activity = {}
    
    def _save_data(self):
        """Save user and chat data to file."""
        try:
            # Convert datetime objects to ISO strings for activity
            activity_data = {
                str(user_id): timestamp.isoformat()
                for user_id, timestamp in self.user_activity.items()
            }
            
            data = {
                "users": {str(k): v for k, v in self.users.items()},
                "chats": {str(k): v for k, v in self.chats.items()},
                "user_activity": activity_data,
                "last_updated": datetime.now().isoformat()
            }
            
            # Create backup of existing file
            if os.path.exists(self.data_file):
                backup_file = f"{self.data_file}.backup"
                os.rename(self.data_file, backup_file)
            
            # Write new data
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Remove backup on successful write
            backup_file = f"{self.data_file}.backup"
            if os.path.exists(backup_file):
                os.remove(backup_file)
                
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            
            # Restore backup if write failed
            backup_file = f"{self.data_file}.backup"
            if os.path.exists(backup_file):
                os.rename(backup_file, self.data_file)
    
    async def cleanup_inactive_chats(self, days: int = 30):
        """Remove chats that have been inactive for specified days."""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            removed_count = 0
            
            for chat_id, chat_data in list(self.chats.items()):
                last_activity = chat_data.get("last_activity")
                if last_activity:
                    try:
                        last_active = datetime.fromisoformat(last_activity)
                        if last_active < cutoff:
                            chat_data["is_active"] = False
                            removed_count += 1
                    except:
                        pass  # Skip invalid dates
            
            if removed_count > 0:
                self._save_data()
                self.logger.info(f"Marked {removed_count} chats as inactive")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up inactive chats: {e}")
            return 0
