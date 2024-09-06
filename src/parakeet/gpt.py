# This file contains the functions for processing GPT messages.
from typing import Callable

from .logger import logger
from .models import BotQuery
from .messaging import ConversationHistory

async def process_gpt_message(query: BotQuery, message_func: Callable, history: ConversationHistory) -> None:
    """
    Process a GPT message.
    Args:
        query (BotQuery): The query to process.
        message_func (Callable): Function to handle the message.
        history (ConversationHistory): The conversation history.
    Returns:
        None
    """
    try:
        # Call the message function with the updated prompt
        await message_func(query)
    except Exception as e:
        logger.error(f"Error processing GPT message: {e}", exc_info=True)