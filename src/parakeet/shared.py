import discord
import logging
import openai
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def generate_response(query: discord.Message) -> str:
    """
    Generate response using OpenAI.

    Args:
        query (discord.Message): The message object from the user.

    Returns:
        str: The generated response message.

    Raises:
        Exception: If there is an error generating the response.
    """
    try:
        mention_name = query.author.name
        
        messages = [
            {"role": "system", "content": f"You are a Discord bot tasked with assiting memebers of the server you are in. You can mention the user with @{mention_name}."},
            {"role": "user", "content": query.content},
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=4096
        )
        
        response_message = response.choices[0].message['content'].strip()
        
        return response_message
    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)