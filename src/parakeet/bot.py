from parakeet.gpt import process_gpt_message
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands
from parakeet.config import discord_token, OPT_IN_ROLE_NAME
from parakeet.messaging import send_help_message, send_privacy_policy
from parakeet.utils import log_user_user_interaction, record_reaction


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

# Create a bot instance with the specified command prefix and intents
bot = commands.Bot(command_prefix='gpt:', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged into {len(bot.guilds)} server(s).')

@bot.event
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

@bot.event
async def on_message(message: discord.Message) -> None:
    """
    Handle incoming user messages from Discord.

    Parameters:
    - message: The message object received from Discord.

    Returns:
    None

    Raises:
    None
    """
    # dont respond to self
    if message.author == bot.user:
        return

    # get the command in lowercase
    command = message.content.lower()

    # check if the command is a GPT command
    if command.startswith('gpt:'):
        dm_channel = await message.author.create_dm()
        switch = {
            'gpt:help': send_help_message,
            'gpt:privacy': send_privacy_policy,
        }
        action = switch.get(command)
        if action:
            await action(dm_channel)
        elif message.reference:
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            if replied_message.author == bot.user:
                await process_gpt_message(message)
            else:
                await log_user_user_interaction(replied_message, message)
        else:
            await process_gpt_message(message)

@bot.event
async def on_message_edit(after):
    if after.author == bot.user:
        return

    if after.content.startswith('gpt:'):
        await process_gpt_message(after)

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return

    message = reaction.message
    # Check if the bot has the manage_messages permission
    if message.guild:
        bot_member = message.guild.get_member(bot.user.id)
        if not bot_member.guild_permissions.manage_messages:
            await message.channel.send("I need the 'Manage Messages' permission to handle reactions.")

    # Update the message content
    new_content = message.content.replace("Add a reaction to provide feedback on the response.", "Thank you for your feedback!")
    await message.edit(content=new_content)

    # Log the feedback
    logging.info(f"User {user.id} reacted with {reaction.emoji} to message {message.id}")

# Start the bot
bot.run(discord_token)