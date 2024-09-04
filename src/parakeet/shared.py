import discord
import openai
from .config import openai_api_key
from .gpt import count_tokens
from .logging_config import logger
from .models import BotQuery

openai.api_key = openai_api_key

async def generate_response(query: BotQuery) -> str:
    """
    Generate a response to a query.

    Args:
        query: The query object containing the message details.
        model: The model to use for generating the response.

    Returns:
        str: The generated response message.

    Raises:
        Exception: If there is an error generating the response.
    """
    try:
        # get user mention name
        message, model = query.unpack()
        mention_name = message.author.mention

        if isinstance(model, str):
            raise TypeError("Model should not be a string. Ensure it is the correct type.")

        # Check if the message is in a DM
        if message.guild is None:
            bot_mention = "Parakeet"
        else:
            # get bot's mention name
            bot_mention = message.guild.me.mention
        
        messages = [
            {"role": "system", "content": f"You are a general purpose Discord bot, named @{bot_mention}. Your job is to help the user @{mention_name} with their queries."},
            {"role": "user", "content": message.content},
        ]

        token_count: int = count_tokens(messages, model)
        
        await message.channel.typing()

        response = openai.ChatCompletion.create(
            model=model.value,
            messages=messages,
            max_tokens=10*token_count
        )
        
        response_message = response.choices[0].message['content'].strip()
        
        return response_message
    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)
        return "Sorry, I couldn't generate a response."