from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

from . import discord, logger

class ConversationHistory:
    def __init__(self, root_message: discord.Message, timeout_seconds: int = 600):
        try:
            if not isinstance(timeout_seconds, int):
                raise TypeError("timeout_seconds must be an integer")
            if not isinstance(root_message, discord.Message):
                raise TypeError("root_message must be a discord.Message instance")
            if timeout_seconds <= 0:
                raise ValueError("timeout_seconds must be greater than 0")

            self.root_message: discord.Message = root_message
            self.last_message: discord.Message = root_message
            self.history: List[Dict[str, str]] = []
            self.last_activity: datetime = datetime.now(timezone.utc)
            self.timeout: timedelta = timedelta(seconds=timeout_seconds)
            logger.info(f"Initialized ConversationHistory with root_message.id: {root_message.id}")
        except Exception as e:
            logger.error(f"Error occurred in ConversationHistory initialization: {str(e)}")

    def add_message(self, message: discord.Message) -> None:
        try:
            role = "assistant" if message.author.bot else "user"
            self.history.append({"role": role, "content": message.content})
            self.last_message = message
            self.last_activity = datetime.now(timezone.utc)
            logger.info(f"Added message to conversation history for root_message: {self.root_message.id}")
        except Exception as e:
            logger.error(f"Error occurred while adding message to conversation history: {str(e)}")

    def is_expired(self) -> bool:
        try:
            expired: bool = datetime.now(timezone.utc) - self.last_activity > self.timeout
            if expired:
                logger.info(f"Conversation history for root_message.id: {self.root_message.id} has expired")
            return expired
        except Exception as e:
            logger.error(f"Error occurred while checking conversation expiration: {str(e)}")
            return False
        
    def reset(self, root_message: discord.Message) -> None:
        try:
            self.history = []
            self.last_activity = datetime.now(timezone.utc)
            self.root_message = root_message
            logger.info(f"Reset conversation history for root_message.id: {self.root_message.id}")
        except Exception as e:
            logger.error(f"Error occurred while resetting conversation history: {str(e)}")
    
class ConversationManager:
    def __init__(self):
        try:
            self.conversation_histories: List[ConversationHistory] = []
            self.scheduler: AsyncIOScheduler = AsyncIOScheduler()
            self.scheduler.start()
        except Exception as e:
            logger.error(f"Error occurred in ConversationManager initialization: {str(e)}")

    def handle_message(self, message: discord.Message, bot_user: discord.User) -> None:
        try:
            if message.reference is not None:
                ref_message = message.reference.resolved
                logger.info(f"Using existing conversation history for message {message.id}")
            else:
                if message.author.id == bot_user.id:
                    logger.info("The message is a root message from the bot, message will not be added to conversation history")
                    return

                ref_message = message
                self.create_conversation(
                    root_message=message,
                    timeout_seconds=600
                )
                logger.info(f"Created new conversation history for message {message.id}")
                return

            # Find the conversation history by key using get_conversation method
            conversation_history = self.get_conversation(ref_message)

            if conversation_history:
                conversation_history.add_message(message)
                logger.info(f"Added message to conversation history for message {message.id}")
            else:
                logger.error(f"Conversation history not found for message {message.id}")
        except Exception as e:
            logger.error(f"An error occurred while handling message: {e}")

    def create_conversation(self, root_message: discord.Message, timeout_seconds: int = 600) -> None:
        try:
            if not isinstance(root_message, discord.Message):
                raise TypeError("root_message must be a discord.Message instance")
            if timeout_seconds <= 0:
                raise ValueError("timeout_seconds must be greater than 0")

            new_history: ConversationHistory = ConversationHistory(
                root_message=root_message,
                timeout_seconds=timeout_seconds
            )
            self._add_conversation(new_history)
            logger.info(f"Created conversation with root_message.id: {root_message.id}")
        except Exception as e:
            logger.error(f"Error occurred while creating conversation: {str(e)}")

    def get_conversation(self, message: discord.Message) -> Optional[ConversationHistory]:
        try:
            conversation_history: Optional[ConversationHistory] = next(
                (history for history in self.conversation_histories if history.root_message.id == message.id), None
            )
            if conversation_history:
                logger.info(f"Found conversation with root_message.id: {message.id}")  # Debugging print
            else:
                logger.info(f"No conversation found with root_message.id: {message.id}")  # Debugging print
            return conversation_history
        except Exception as e:
            logger.error(f"Error occurred while getting conversation history: {str(e)}")
            return None
        
    def add_message_to_conversation(self, last_message: discord.Message, next_message: discord.Message) -> None:
        try:
            conversation_history: Optional[ConversationHistory] = self.get_conversation(last_message.id)
            if conversation_history:
                conversation_history.add_message(next_message)
            else:
                logger.error(f"Conversation history not found for message_id: {last_message.id}")
        except Exception as e:
            logger.error(f"Error occurred while adding message to conversation history: {str(e)}")

    def delete_conversation(self, root_message: discord.Message) -> None:
        try:
            conversation_history: Optional[ConversationHistory] = self.get_conversation(root_message.id)
            if conversation_history:
                self.conversation_histories.remove(conversation_history)
                logger.info(f"Deleted conversation history for root_message.id: {root_message.id}")
            else:
                logger.error(f"Conversation history not found for root_message.id: {root_message.id}")
        except Exception as e:
            logger.error(f"Error occurred while deleting conversation history: {str(e)}")

    def reset_conversation(self, message_id: int) -> None:
        try:
            conversation_history: Optional[ConversationHistory] = self.get_conversation(message_id)
            if conversation_history:
                self.conversation_histories.remove(conversation_history)
                logger.info(f"Reset conversation history for root_message.id: {message_id}")
            else:
                logger.error(f"Conversation history not found for root_message.id: {message_id}")
        except Exception as e:
            logger.error(f"Error occurred while resetting conversation history: {str(e)}")

    def _add_conversation(self, conversation_history: ConversationHistory) -> None:
        try:
            self.conversation_histories.append(conversation_history)
            self._schedule_expiration(conversation_history)
        except Exception as e:
            logger.error(f"Error occurred while adding conversation history: {str(e)}")

    def _schedule_expiration(self, conversation_history: ConversationHistory) -> None:
        try:
            expiration_time = conversation_history.last_activity + conversation_history.timeout
            self.scheduler.add_job(self._expire_conversation, 'date', run_date=expiration_time, args=[conversation_history])
        except Exception as e:
            logger.error(f"Error occurred while scheduling conversation expiration: {str(e)}")

    def _expire_conversation(self, conversation_history: ConversationHistory) -> None:
        try:
            if conversation_history.is_expired():
                self.conversation_histories.remove(conversation_history)
                logger.info(f"Expired conversation history for root_message.id: {conversation_history.root_message.id}")
        except Exception as e:
            logger.error(f"Error occurred while expiring conversation history: {str(e)}")