import tiktoken
from pathlib import Path
from typing import Callable
from .logging_config import logger
from .models import BotQuery, GPTModel

async def process_gpt_message(query: BotQuery, message_func: Callable) -> None:
    """
    Process a GPT message.
    Args:
        message (discord.Message): The message to process.
        message_func (Callable): Function to handle the message.
    Returns:
        None
    """
    try:
        await message_func(query)
    except Exception as e:
        logger.error(f"Error processing GPT message: {e}", exc_info=True)

def count_tokens(messages: list[dict] | dict | str, model: GPTModel) -> int:
    """
    Count the number of tokens in a message or a list of messages.
    Args:
        messages (list[dict] | dict | str): The messages to count tokens for. Can be a string, a dictionary with the format {"role": "user", "content": query.content}, or a list of such dictionaries.
        model (str): The model to use for tokenization.
    Returns:
        int: The number of tokens in the messages.
    """
    
    # Ensure messages is a list
    if not isinstance(messages, list):
        messages = [messages]
    
    total_tokens = 0
    
    # Get the encoding for the specified model
    encoding = tiktoken.encoding_for_model(model_name=model.value)
    
    for message in messages:
        # Check if the message is a dictionary and extract the content
        if isinstance(message, dict):
            content = message.get('content', '')
        else:
            content = message
        
        # Ensure content is a string
        if not isinstance(content, str):
            content = str(content)
        
        # Encode the content to get the tokens
        tokens = encoding.encode(content)
        total_tokens += len(tokens)
    
    return total_tokens