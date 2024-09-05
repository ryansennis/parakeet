# This file contains the functions for processing GPT messages.
from typing import Callable

from parakeet.shared import generate_system_prompt
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
        system_prompt = generate_system_prompt(query)

        # Add the user's message to the history
        history.add_message("user", query.message, query.message.id)
        
        # Get the conversation history
        conversation_history = history.get_history()

        # Create the prompt with the system prompt, conversation history, and current query
        prompt = [system_prompt] + conversation_history + [{"role": "user", "content": query.message.content}]

        # update query with new prompt
        query.set_message(prompt)
        
        # Call the message function with the updated prompt
        await message_func(query)
    except Exception as e:
        logger.error(f"Error processing GPT message: {e}", exc_info=True)