from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from . import discord, logger

class ConversationHistory:
    def __init__(self, root_message_id: int, timeout_seconds: int = 600):
        try:
            self.root_message_id: int = root_message_id
            self.last_message_id: int = root_message_id
            self.history: List[Dict[str, str]] = []
            self.last_activity: datetime = datetime.now(timezone.utc)
            self.timeout: timedelta = timedelta(seconds=timeout_seconds)
            logger.info(f"Initialized ConversationHistory with root_message_id: {root_message_id}")
        except Exception as e:
            logger.error(f"Error occurred in ConversationHistory initialization: {str(e)}")

    def add_message(self, role: str, message: discord.Message) -> None:
        try:
            self.history.append({"role": role, "content": message.content})
            self.last_message_id = message.id
            self.last_activity = datetime.now(timezone.utc)
            logger.info(f"Added message to conversation history for root_message_id: {self.root_message_id}")
        except Exception as e:
            logger.error(f"Error occurred while adding message to conversation history: {str(e)}")

    def is_expired(self) -> bool:
        try:
            expired: bool = datetime.now(timezone.utc) - self.last_activity > self.timeout
            if expired:
                logger.info(f"Conversation history for root_message_id: {self.root_message_id} has expired")
            return expired
        except Exception as e:
            logger.error(f"Error occurred while checking conversation expiration: {str(e)}")
            return False
    
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
                conversation_key = message.reference.message_id
                logger.info(f"Using existing conversation history for message {message.id}")
            else:
                if message.author == bot_user:
                    logger.info("The message is a root message from the bot, message will not be added to conversation history")
                    return

                conversation_key = message.id
                self.create_conversation(
                    root_message_id=message.id,
                    timeout_seconds=600
                )
                logger.info(f"Created new conversation history for message {message.id}")
                return

            # Find the conversation history by key using get_conversation method
            conversation_history = self.get_conversation(conversation_key)

            if conversation_history:
                role = "assistant" if message.author.bot else "user"
                conversation_history.add_message(role, message)
                logger.info(f"Added message to conversation history for message {message.id}")
            else:
                logger.error(f"Conversation history not found for message {message.id}")
        except Exception as e:
            logger.error(f"An error occurred while handling message: {e}")

    def create_conversation(self, root_message_id: int, timeout_seconds: int = 600) -> None:
        try:
            new_history: ConversationHistory = ConversationHistory(
                root_message_id=root_message_id,
                timeout_seconds=timeout_seconds
            )
            self._add_conversation(new_history)
        except Exception as e:
            logger.error(f"Error occurred while creating conversation: {str(e)}")

    def get_conversation(self, root_message_id: int) -> ConversationHistory | None:
        try:
            conversation_history: ConversationHistory | None = next((history for history in self.conversation_histories if history.root_message_id == root_message_id), None)
            if conversation_history:
                logger.info(f"Found conversation history for root_message_id: {root_message_id}")
            return conversation_history
        except Exception as e:
            logger.error(f"Error occurred while getting conversation history: {str(e)}")
            return None
        
    def add_message_to_conversation(self, message_id: int, role: str, message: discord.Message) -> None:
        try:
            conversation_history: ConversationHistory | None = self.get_conversation(message_id)
            if conversation_history:
                conversation_history.add_message(role, message)
            else:
                logger.error(f"Conversation history not found for message_id: {message_id}")
        except Exception as e:
            logger.error(f"Error occurred while adding message to conversation history: {str(e)}")

    def delete_conversation(self, root_message_id: int) -> None:
        try:
            conversation_history: ConversationHistory | None = self.get_conversation(root_message_id)
            if conversation_history:
                self.conversation_histories.remove(conversation_history)
                logger.info(f"Deleted conversation history for root_message_id: {root_message_id}")
            else:
                logger.error(f"Conversation history not found for root_message_id: {root_message_id}")
                return None
        except Exception as e:
            logger.error(f"Error occurred while deleting conversation history: {str(e)}")

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
                logger.info(f"Expired conversation history for root_message_id: {conversation_history.root_message_id}")
        except Exception as e:
            logger.error(f"Error occurred while expiring conversation history: {str(e)}")