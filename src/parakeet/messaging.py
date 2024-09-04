import os
import discord
from .shared import logger
from .shared import generate_response

async def send_message(channel: discord.TextChannel, message_content: str) -> None:
    chunk_size = 2000
    for i in range(0, len(message_content), chunk_size):
        try:
            chunk = message_content[i:i + chunk_size]
            message = await channel.send(chunk)  # Capture the message object
            await add_feedback_reactions(message)  # Pass the message object
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)

async def send_reply(message: discord.Message, reply_content: str) -> None:
    """
    Sends a reply to a Discord message.

    Args:
        message (discord.Message): The message to reply to.
        reply_content (str): The content of the reply.

    Raises:
        Exception: If there is an error sending the reply.

    Returns:
        None
    """
    chunk_size = 2000
    for i in range(0, len(reply_content), chunk_size):
        try:
            chunk = reply_content[i:i + chunk_size]
            reply_message = await message.reply(chunk)  # Capture the reply message object
            await add_feedback_reactions(reply_message)  # Pass the reply message object
        except Exception as e:
            logger.error(f"Error sending reply: {e}", exc_info=True)

async def send_privacy_policy(channel: discord.TextChannel) -> None:
    """
    Sends the privacy policy to the specified channel.

    Parameters:
    - channel (discord.TextChannel): The channel to send the privacy policy to.

    Returns:
    - None
    """
    privacy_policy_path = os.path.join(os.path.dirname(__file__), 'privacy_policy.txt')
    try:
        with open(privacy_policy_path, "r") as file:
            privacy_policy = file.read()
        await send_message(channel, privacy_policy)
    except Exception as e:
        logger.error(f"Error sending privacy policy: {e}", exc_info=True)

async def send_help_message(channel: discord.TextChannel) -> None:
    """
    Sends a help message to the specified channel.

    Parameters:
    - channel (discord.TextChannel): The channel to send the help message to.

    Returns:
    - None
    """
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
    """
    Adds feedback reactions to the given response message.

    Parameters:
    - response: The response message to add reactions to.

    Raises:
    - discord.errors.HTTPException: If there is an error adding the reactions.

    Returns:
    - None
    """
    try:
        await response.add_reaction("👍")
        await response.add_reaction("👎")
    except discord.errors.HTTPException as e:
        logger.error(f"Error adding feedback reactions: {e}", exc_info=True)

async def bot_respond(message):
    """
    Generate a response to a given message and send it to the channel.

    Parameters:
        message (discord.Message): The message to generate a response for.

    Raises:
        Exception: If an error occurs while generating the response.

    Returns:
        None
    """
    try:
        response = await generate_response(message)
        await send_message(message.channel, response)
    except Exception as e:
        logger.error(f"Error generating response message: {e}", exc_info=True)

async def bot_reply(message: discord.Message):
    """
    Generates a response reply based on the given message.
    Parameters:
    - message (discord.Message): The message to generate a response reply for.
    Returns:
    - None
    Raises:
    - Exception: If an error occurs while generating the response reply.
    """
    
    try:
        reference = message.reference
        original_message = reference.resolved
        response = await generate_response(original_message)
        # Send the response as a reply to the original message
        await send_message(message.channel, response)
    except Exception as e:
        logger.error(f"Error generating response reply: {e}", exc_info=True)