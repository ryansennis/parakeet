import openai

from . import logger, BotQuery, discord

def generate_system_prompt(query: BotQuery) -> list[dict]:
    try:
        # Unpack the message and model
        message, model = query.unpack()
        message_content = message.content
        mention_name = message.author.mention

        if isinstance(model, str):
            raise TypeError("Model should not be a string. Ensure it is the correct type.")

        # Check if the message is in a DM
        if message.guild is None:
            bot_mention = "Parakeet"
        else:
            # Get bot's mention name
            bot_mention = message.guild.me.mention

        system_prompt = [
            {"role": "system", "content": f"You are a general purpose Discord bot, named @{bot_mention}. Your job is to help the user @{mention_name} with their queries."},
            {"role": "assistant", "content": f"You are to engage in a conversation with the other user's in chat. Keep it informal and be prepared to engage in idle chat."},
            {"role": "user", "content": message_content}
        ]

        return system_prompt
    except Exception as e:
        logger.error(f"Error generating system prompt: {e}", exc_info=True)
        return None

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
        messages: list[dict] = generate_system_prompt(query).append(message.content)
        
        await message.channel.typing()

        response = await openai.ChatCompletion.create(
            model=model.value,
            messages=messages,
            max_tokens=4096
        )
        
        response_message = response.choices[0].message['content'].strip()
        
        return response_message
    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)
        return "Sorry, I couldn't generate a response."