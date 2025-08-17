import logging
import asyncio
from typing import Dict, List, Set
from datetime import datetime
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from .user_manager import UserManager

class BroadcastManager:
    """Manages broadcasting messages to all users and groups."""
    
    def __init__(self, bot: Bot, user_manager: UserManager, owner_id: int):
        self.bot = bot
        self.user_manager = user_manager
        self.owner_id = owner_id
        self.logger = logging.getLogger(__name__)
        
        # Broadcast statistics
        self.last_broadcast = None
        self.broadcast_history: List[Dict] = []
        
        self.logger.info("BroadcastManager initialized")
    
    async def send_broadcast(self, message: str, target_type: str = "all") -> Dict:
        """
        Send broadcast message to users/groups.
        
        Args:
            message: Message to broadcast
            target_type: "all", "users", or "groups"
        
        Returns:
            Dictionary with broadcast results
        """
        try:
            self.logger.info(f"Starting broadcast to {target_type}: {message[:50]}...")
            
            # Get target chats
            targets = await self._get_broadcast_targets(target_type)
            
            if not targets:
                self.logger.warning("No targets found for broadcast")
                return {
                    "success": 0,
                    "failed": 0,
                    "total_users": 0,
                    "total_groups": 0,
                    "message": "No targets found"
                }
            
            # Prepare message with broadcast header
            broadcast_message = self._prepare_broadcast_message(message)
            
            # Send to all targets with rate limiting
            results = await self._send_to_targets(targets, broadcast_message)
            
            # Update statistics
            broadcast_record = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "target_type": target_type,
                "results": results
            }
            
            self.broadcast_history.append(broadcast_record)
            self.last_broadcast = datetime.now()
            
            # Keep only last 50 broadcasts in memory
            if len(self.broadcast_history) > 50:
                self.broadcast_history = self.broadcast_history[-50:]
            
            self.logger.info(f"Broadcast completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in broadcast: {e}")
            return {
                "success": 0,
                "failed": 0,
                "total_users": 0,
                "total_groups": 0,
                "error": str(e)
            }
    
    async def _get_broadcast_targets(self, target_type: str) -> List[Dict]:
        """Get list of chat IDs to broadcast to."""
        try:
            all_chats = await self.user_manager.get_all_chats()
            targets = []
            
            for chat_data in all_chats:
                chat_id = chat_data.get("chat_id")
                chat_type = chat_data.get("chat_type", "private")
                
                if not chat_id:
                    continue
                
                # Filter based on target type
                if target_type == "users" and chat_type != "private":
                    continue
                elif target_type == "groups" and chat_type == "private":
                    continue
                
                targets.append({
                    "chat_id": chat_id,
                    "chat_type": chat_type,
                    "title": chat_data.get("title", "Private Chat")
                })
            
            return targets
            
        except Exception as e:
            self.logger.error(f"Error getting broadcast targets: {e}")
            return []
    
    def _prepare_broadcast_message(self, message: str) -> str:
        """Prepare the broadcast message with appropriate formatting."""
        # Return message as-is to make it look like a normal bot message
        return message
    
    async def _send_to_targets(self, targets: List[Dict], message: str) -> Dict:
        """Send message to all targets with proper rate limiting."""
        success_count = 0
        failed_count = 0
        user_count = 0
        group_count = 0
        
        # Rate limiting for responsible API usage
        semaphore = asyncio.Semaphore(20)
        
        async def send_to_chat(target: Dict):
            nonlocal success_count, failed_count, user_count, group_count
            
            # Rate limiting for API protection
            async with semaphore:
                try:
                    chat_id = target["chat_id"]
                    chat_type = target["chat_type"]
                    
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="HTML"
                    )
                    
                    success_count += 1
                    if chat_type == "private":
                        user_count += 1
                    else:
                        group_count += 1
                    
                    self.logger.debug(f"Broadcast sent to {chat_id} ({chat_type})")
                    
                    # Small delay to prevent API flooding
                    await asyncio.sleep(0.05)
                    
                except TelegramAPIError as e:
                    failed_count += 1
                    self.logger.warning(f"Failed to send broadcast to {target['chat_id']}: {e}")
                    
                    # Remove inactive chats
                    if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        await self.user_manager.remove_chat(target["chat_id"])
                        
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Unexpected error sending to {target['chat_id']}: {e}")
        
        # Execute all sends concurrently
        tasks = [send_to_chat(target) for target in targets]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "success": success_count,
            "failed": failed_count,
            "total_users": user_count,
            "total_groups": group_count,
            "total_targets": len(targets)
        }
    
    async def send_owner_notification(self, message: str):
        """Send notification to bot owner."""
        try:
            await self.bot.send_message(
                chat_id=self.owner_id,
                text=f"🔔 <b>Bot Notification</b>\n\n{message}",
                parse_mode="HTML"
            )
            self.logger.info("Owner notification sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send owner notification: {e}")
    
    def get_broadcast_stats(self) -> Dict:
        """Get broadcast statistics."""
        total_broadcasts = len(self.broadcast_history)
        
        if total_broadcasts == 0:
            return {
                "total_broadcasts": 0,
                "last_broadcast": None,
                "average_success_rate": 0
            }
        
        # Calculate average success rate
        total_attempts = sum(b["results"].get("success", 0) + b["results"].get("failed", 0) 
                           for b in self.broadcast_history)
        total_successes = sum(b["results"].get("success", 0) for b in self.broadcast_history)
        
        avg_success_rate = (total_successes / max(total_attempts, 1)) * 100
        
        return {
            "total_broadcasts": total_broadcasts,
            "last_broadcast": self.last_broadcast.isoformat() if self.last_broadcast else None,
            "average_success_rate": round(avg_success_rate, 2),
            "recent_broadcasts": self.broadcast_history[-5:] if self.broadcast_history else []
        }
    
    async def test_broadcast(self) -> bool:
        """Test broadcast functionality by sending to owner only."""
        try:
            test_message = "🧪 <b>Broadcast Test</b>\n\nThis is a test of the broadcast system."
            
            await self.bot.send_message(
                chat_id=self.owner_id,
                text=test_message,
                parse_mode="HTML"
            )
            
            self.logger.info("Broadcast test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Broadcast test failed: {e}")
            return False
