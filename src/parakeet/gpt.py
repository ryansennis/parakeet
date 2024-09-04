import discord
from typing import Callable
from .shared import logger

async def process_gpt_message(message: discord.Message, message_func: Callable) -> None:
    """
    Process a GPT message.
    Args:
        message (discord.Message): The message to process.
        message_func (Callable): Function to handle the message.
    Returns:
        None
    """
    try:
        await message_func(message)    
    except Exception as e:
        logger.error(f"Error processing GPT message: {e}", exc_info=True)