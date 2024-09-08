import os

from . import discord, logger, BotQuery, MAX_DISCORD_MESSAGE_LENGTH
from .shared import generate_response

async def send_message(channel, content):
    last_message: discord.Message = None

    if channel is None:
        logger.error("Channel is None, cannot send message.")
        return

    chunk_size = int(MAX_DISCORD_MESSAGE_LENGTH)
    for i in range(0, len(content), chunk_size):
        try:
            chunk = content[i:i + chunk_size]
            last_message = await channel.send(chunk)
        except discord.HTTPException as http_err:
            logger.error(f"HTTP error occurred while sending message: {http_err}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error occurred while sending message: {e}", exc_info=True)

    
    await add_feedback_reactions(last_message)

async def send_reply(message: discord.Message, reply_content: str) -> None:
    last_message: discord.Message = None

    chunk_size = int(MAX_DISCORD_MESSAGE_LENGTH)
    for i in range(0, len(reply_content), chunk_size):
        try:
            chunk = reply_content[i:i + chunk_size]
            last_message = await message.reply(chunk)  # Capture the reply message object
        except Exception as e:
            logger.error(f"Error sending reply: {e}", exc_info=True)
    
    await add_feedback_reactions(last_message)

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