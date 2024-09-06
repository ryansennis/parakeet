import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Callable

from . import discord, commands, logger, BotQuery, MAX_DISCORD_MESSAGE_LENGTH
from .shared import generate_response


class ConversationHistory:
    """
    Represents a conversation history for a bot.
    Args:
        root_message_id (int): The ID of the root message in the conversation.
        timeout_seconds (int, optional): The timeout duration in seconds. Defaults to 600.
        bot (commands.Bot, optional): The bot instance associated with the conversation. Defaults to None.
        on_expire (Callable[[int], None], optional): A callback function to be called when the conversation expires. Defaults to None.
    Attributes:
        root_message_id (int): The ID of the root message in the conversation.
        message_id (int): The ID of the last message in the conversation.
        history (List[Dict[str, str]]): The list of messages in the conversation history.
        last_activity (datetime): The timestamp of the last activity in the conversation.
        timeout (timedelta): The timeout duration for the conversation.
        _stop_event (asyncio.Event): An event to stop the expiration tracking.
        bot (commands.Bot): The bot instance associated with the conversation.
        on_expire (Callable[[int], None]): A callback function to be called when the conversation expires.
    Methods:
        add_message(role: str, content: str, message_id: int) -> None:
            Adds a message to the conversation history.
        get_history() -> List[Dict[str, str]]:
            Returns the conversation history.
        clear_history() -> None:
            Clears the conversation history.
        is_expired() -> bool:
            Checks if the conversation has expired.
        to_dict() -> Dict:
            Returns a dictionary representation of the conversation history.
        from_dict(data: Dict) -> ConversationHistory:
            Creates a ConversationHistory instance from a dictionary.
        track_expiration() -> None:
            Tracks the expiration of the conversation.
        start_tracking() -> None:
            Starts tracking the expiration of the conversation.
        stop_tracking() -> None:
            Stops tracking the expiration of the conversation.
    """
    
    def __init__(self, root_message_id: int, timeout_seconds: int = 600, bot: commands.Bot = None, on_expire: Callable[[int], None] = None):
        self.root_message_id = root_message_id
        self.message_id = root_message_id
        self.history = []
        self.last_activity = datetime.now(timezone.utc)  # Use timezone.utc here
        self.timeout = timedelta(seconds=timeout_seconds)  # Ensure timeout is a timedelta
        self._stop_event = asyncio.Event()
        self.bot = bot
        self.on_expire = on_expire
        logger.info(f"Initialized ConversationHistory with root_message_id: {root_message_id}")
        self.start_tracking()
    
    def add_message(self, role: str, content: str, message_id: int):
        """
        Adds a message to the history.

        Args:
            role (str): The role associated with the message.
            content (str): The content of the message.
            message_id (int): The ID of the message.

        Returns:
            None
        """
        self.history.append({"role": role, "content": content})
        self.message_id = message_id
        self.last_activity = datetime.now(timezone.utc)
        logger.info(f"Added message to history: role={role}, message_id={message_id}")

    def get_history(self) -> List[Dict[str, str]]:
        """
        Retrieves the conversation history for the current instance of the Parakeet class.

        Returns:
            A list of dictionaries representing the conversation history. Each dictionary contains
            key-value pairs where the keys are strings representing the message attributes and the
            values are also strings representing the corresponding attribute values.
        """
        logger.info(f"Getting conversation history for root_message_id: {self.root_message_id}")
        return list(self.history)
    
    def clear_history(self, message_id: int):
        """
        Clears the conversation history for the current instance of the Parakeet messaging class.

        This method clears the history list and logs a message indicating the root message ID for which the history was cleared.
        """
        self.history.clear()
        self.root_message_id = message_id
        self.message_id = message_id
        self.last_activity = datetime.now(timezone.utc)
        logger.info(f"Cleared conversation history for root_message_id: {self.root_message_id}")

    def is_expired(self) -> bool:
        """
        Check if the conversation is expired based on the last activity and timeout.

        Returns:
            bool: True if the conversation is expired, False otherwise.
        """
        expired = datetime.now(timezone.utc) - self.last_activity > self.timeout
        if expired:
            logger.info(f"Conversation history for root_message_id: {self.root_message_id} has expired")
        return expired

    def to_dict(self) -> Dict:
        """
        Converts the `Messaging` object to a dictionary.

        Returns:
            dict: A dictionary representation of the `Messaging` object.
                The dictionary contains the following keys:
                - "root_message_id": The root message ID.
                - "history": A list of messages in the history.
        """
        return {
            "root_message_id": self.root_message_id,
            "history": list(self.history)
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationHistory':
        """
        Create a ConversationHistory instance from a dictionary.

        Parameters:
        - data (Dict): A dictionary containing the data for the ConversationHistory instance.

        Returns:
        - ConversationHistory: An instance of the ConversationHistory class.

        Example:
            data = {
                "root_message_id": 123,
                "history": ["message1", "message2"]
            }
            history = ConversationHistory.from_dict(data)
        """
        instance = cls(data["root_message_id"])
        instance.history = data["history"]
        return instance

    async def track_expiration(self):
        """
        Tracks the expiration of a message and triggers the on_expire callback when expired.

        This method runs in an infinite loop until the stop_event is set. It checks if the message is expired
        and if so, calls the on_expire callback passing the root_message_id as an argument. After that, it stops
        tracking the expiration. The method then waits for the specified timeout period before checking again.

        Returns:
            None
        """
        while not self._stop_event.is_set():
            await asyncio.sleep(1)
            if self.is_expired():
                self.on_expire(self.root_message_id)
                self.stop_tracking()

    def start_tracking(self):
        """
        Starts tracking the expiration of the object asynchronously.

        This method creates a new task using asyncio.create_task() to track the expiration of the object.
        The expiration tracking is performed in the background, allowing the program to continue executing
        other tasks concurrently.

        Returns:
            None
        """
        asyncio.create_task(self.track_expiration())

    def stop_tracking(self):
        """
        Stops the tracking process.

        Sets the internal stop event, which will cause the tracking process to stop.
        """
        self._stop_event.set()

conversation_histories: List[ConversationHistory] = []

def handle_expiration(root_message_id: int):
    logger.info(f"Handling expiration for conversation history with root_message_id: {root_message_id}")
    global conversation_histories
    logger.info(f"Before expiration: {len(conversation_histories)} histories")
    conversation_histories = [history for history in conversation_histories if history.root_message_id != root_message_id]
    logger.info(f"After expiration: {len(conversation_histories)} histories")
    logger.info(f"Deleted expired conversation history with root_message_id: {root_message_id}")
    # todo: add the conversation history to a database

async def send_message(channel, content):
    if channel is None:
        logger.error("Channel is None, cannot send message.")
        return

    chunk_size = int(MAX_DISCORD_MESSAGE_LENGTH)
    for i in range(0, len(content), chunk_size):
        try:
            chunk = content[i:i + chunk_size]
            message = await channel.send(chunk)  # Capture the message object
            await add_feedback_reactions(message)  # Pass the message object
        except discord.HTTPException as http_err:
            logger.error(f"HTTP error occurred while sending message: {http_err}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error occurred while sending message: {e}", exc_info=True)

async def send_reply(message: discord.Message, reply_content: str) -> None:
    chunk_size = int(MAX_DISCORD_MESSAGE_LENGTH)
    for i in range(0, len(reply_content), chunk_size):
        try:
            chunk = reply_content[i:i + chunk_size]
            reply_message = await message.reply(chunk)  # Capture the reply message object
            await add_feedback_reactions(reply_message)  # Pass the reply message object
        except Exception as e:
            logger.error(f"Error sending reply: {e}", exc_info=True)

async def send_privacy_policy(channel: discord.TextChannel) -> None:
    privacy_policy_path = os.path.join(os.path.dirname(__file__), 'privacy_policy.txt')
    try:
        with open(privacy_policy_path, "r") as file:
            privacy_policy = file.read()
        await send_message(channel, privacy_policy)
    except Exception as e:
        logger.error(f"Error sending privacy policy: {e}", exc_info=True)

async def send_help_message(channel: discord.TextChannel) -> None:
    try:
        help_message = (
            "Here are the commands you can use:\n"
            "1. `gpt:help` - Show this help message\n"
            "2. `gpt:privacy` - Show the privacy policy\n"
            "5. `gpt:<your message>` - Send a message to the AI bot\n"
        )
        await send_message(channel, help_message)
    except Exception as e:
        logger.error(f"Error sending help message: {e}", exc_info=True)

async def add_feedback_reactions(response):
    try:
        await response.add_reaction("👍")
        await response.add_reaction("👎")
    except discord.errors.HTTPException as e:
        logger.error(f"Error adding feedback reactions: {e}", exc_info=True)

async def bot_message(query: BotQuery) -> None:
    try:
        message, _ = query.unpack()
        channel = message.channel
    except Exception as e:
        logger.error(f"Error unpacking query: {e}", exc_info=True)
        return
    try:
        response = await generate_response(query)
        await send_message(channel, response)
    except Exception as e:
        logger.error(f"Error generating response message: {e}", exc_info=True)
        await send_message(channel, "An error occurred while generating the response. Please try again later.")

async def bot_reply(query: BotQuery) -> None:
    from .gpt import generate_response
    try:
        message, model = query.unpack()
        reference = message.reference

        if reference is None or reference.resolved is None:
            logger.debug("Reference or resolved message is None, sending message to channel.")
            response = await generate_response(query)
            await send_message(message.channel, response)
        else:
            original_message = reference.resolved
            query = BotQuery(message=original_message, model=model)
            response = await generate_response(query)
            await send_reply(original_message, response)
            logger.debug(f"Replied to original message with: {response}")
    except Exception as e:
        logger.error(f"Error generating response reply: {e}", exc_info=True)