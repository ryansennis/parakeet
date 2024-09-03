import discord
import os
import openai
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime
from config import discord_token, openai_api_key, OPT_IN_ROLE_NAME
from utils import record_reaction, log_user_user_interaction, store_feedback, update_conversation_history, has_opt_in_role, track_sent_messages, clear_conversation_and_messages, load_conversation_histories, save_conversation_histories, conversation_histories
from messaging import send_message, send_privacy_policy, send_help_message, update_with_response

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Initialize Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
intents.reactions = True  # Enable reactions intent
intents.dm_messages = True  # Enable DM messages intent

# Create a Discord client instance
client = discord.Client(intents=intents)

# Set up your OpenAI API key securely
openai.api_key = openai_api_key

async def generate_response(server_id, user_id, user_message):
    """Generate response using OpenAI.
    Args:
        server_id (str): The ID of the server.
        user_id (str): The ID of the user.
        user_message (str): The message from the user.
    Returns:
        dict: A dictionary containing the generated response metrics, including the response message,
              response time, and number of tokens.
    Raises:
        Exception: If there is an error generating the response.
    """
    """Generate response using OpenAI."""
    try:
        # Load conversation histories from file
        load_conversation_histories(server_id, user_id)
        
        conversation_history = conversation_histories[server_id][user_id]['messages']
        start_time = datetime.now()
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an LLM bot whose job it is to help people in the server."},
                *conversation_history,  # Include the conversation history as background context
                {"role": "user", "content": user_message},
                {"role": "system", "content": f"You can mention the user with <@{user_id}>. Only do it if it is necessary."}
            ],
            max_tokens=4096
        )
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        response_message = response.choices[0].message['content'].strip()
        num_tokens = response.choices[0].message['content'].count(' ') + 1
        conversation_histories[server_id][user_id]['messages'].append({"role": "assistant", "content": response_message})
        save_conversation_histories(server_id, user_id)
        metrics = {
            "response": response_message,
            "response_time": response_time,
            "num_tokens": num_tokens
        }
        return metrics
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return None
    
async def process_gpt_message(message, user_id, server_id, is_reply):
    user_message = message.content[len('gpt:'):].strip() if message.content.startswith('gpt:') else message.content

    if message.guild is None or has_opt_in_role(message.author, OPT_IN_ROLE_NAME):
        update_conversation_history(server_id, user_id, message.author, user_message)

        if is_reply:
            metrics = await generate_response(server_id, user_id, user_message)
            if metrics:
                response = metrics.get("response", "Sorry, I couldn't generate a response.")
                num_tokens = metrics.get("num_tokens", 0)
                await message.reply(response)
                logging.info(f"Replied to user {user_id} in server {server_id} with message: {response}")
                # Save num_tokens to user info
                track_sent_messages(user_id, [message.id])
                store_feedback(user_id, server_id, message.id, "num_tokens", num_tokens)
        else:
            generating_message = await message.channel.send("Generating Response...")
            metrics = await generate_response(server_id, user_id, user_message)
            response = metrics.get("response", "Sorry, I couldn't generate a response.")
            num_tokens = metrics.get("num_tokens", 0)
            await generating_message.edit(content=f"{response}\nAdd a reaction to provide feedback on the response.")
            track_sent_messages(user_id, [generating_message.id])
            store_feedback(user_id, server_id, generating_message.id, "num_tokens", num_tokens)

            # Add thumbs up and thumbs down reactions
            await generating_message.add_reaction('👍')
            await generating_message.add_reaction('👎')
    else:
        await send_message(message.channel, "You need to opt in to interact with the bot. Ask a moderator for the `AI Trainer` role.")

@client.event
async def on_ready():
    logger.info(f'Logged into {len(client.guilds)} server(s).')

@client.event
async def on_guild_join(guild):
    logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')

    # Create the opt-in role if it doesn't exist
    role_name = OPT_IN_ROLE_NAME
    existing_role = discord.utils.get(guild.roles, name=role_name)
    if existing_role is None:
        try:
            await guild.create_role(name=role_name, permissions=discord.Permissions(permissions=0), reason="Role for interacting with the AI bot")
            logger.info(f'Created role "{role_name}" in guild "{guild.name}"')
        except discord.Forbidden:
            logger.error(f'Permission denied to create role "{role_name}" in guild "{guild.name}"')
        except discord.HTTPException as e:
            logger.error(f'Failed to create role "{role_name}" in guild "{guild.name}": {e}')

    # Send a welcome message to the system channel if it exists
    if guild.system_channel:
        welcome_message = (
            f"Hello {guild.name}! I'm your new AI assistant bot. To interact with me, assign yourself the '{role_name}' role. "
            "Use `gpt:help` to see the available commands."
        )
        await guild.system_channel.send(welcome_message)
        logger.info(f'Sent welcome message to guild "{guild.name}"')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = message.author.id
    server_id = message.guild.id if message.guild else "DM"

    if message.content.startswith('gpt:help'):
        dm_channel = await message.author.create_dm()
        await send_help_message(dm_channel)
        return

    if message.content.startswith('gpt:privacy'):
        dm_channel = await message.author.create_dm()
        await send_privacy_policy(dm_channel)
        return

    if message.reference:
        replied_message = await message.channel.fetch_message(message.reference.message_id)
        if replied_message.author == client.user:
            await process_gpt_message(message, user_id, server_id, True)
        else:
            await log_user_user_interaction(replied_message, message)
        return

    if message.content.startswith('gpt:'):
        await process_gpt_message(message, user_id, server_id, False)
    else:
        return

@client.event
async def on_message_edit(before, after):
    if after.author == client.user:
        return

    user_id = after.author.id
    server_id = after.guild.id if after.guild else "DM"

    if after.content.startswith('gpt:'):
        await process_gpt_message(after, user_id, server_id, False)

@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return
    
    if reaction.emoji == '👍':
        reaction_type = 'thumbs_up'
    elif reaction.emoji == '👎':
        reaction_type = 'thumbs_down'
    else:
        return

    message = reaction.message
    # Check if the bot has the manage_messages permission
    if message.guild:
        bot_member = message.guild.get_member(client.user.id)
        if not bot_member.guild_permissions.manage_messages:
            await message.channel.send("I need the 'Manage Messages' permission to handle reactions.")
            return

    # Remove the user-added thumbs up and thumbs down reactions
    for reaction in message.reactions:
        if reaction.emoji in ['👍', '👎'] or reaction.me:
            await reaction.clear()

    # Update the message content
    new_content = message.content.replace("Add a reaction to provide feedback on the response.", "Thank you for your feedback!")
    await message.edit(content=new_content)

    record_reaction(user.id, message.id, reaction_type)

    # Log the feedback
    logging.info(f"User {user.id} reacted with {reaction.emoji} to message {message.id}")

# Start the bot
client.run(discord_token)