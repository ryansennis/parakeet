import discord
from discord.ext import commands
from .config import discord_token
from .messaging import send_help_message, send_privacy_policy, bot_reply, bot_respond
from .shared import logger
from .gpt import process_gpt_message

# Initialize Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
intents.reactions = True  # Enable reactions intent
intents.dm_messages = True  # Enable DM messages intent

# Create a bot instance with the specified command prefix and intents
bot: commands.Bot = commands.Bot(command_prefix='gpt:', intents=intents)

@bot.event
async def on_ready() -> None:
    logger.info(f'Logged into {len(bot.guilds)} server(s).')

@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')

    # todo: Create the opt-in role if it doesn't exist

# remove default help command before registering our own
bot.remove_command('help')

@bot.command(name='help')
async def send_help(ctx):
    await send_help_message(ctx.message)

@bot.command(name='privacy')
async def send_privacy(ctx):
    await send_privacy_policy(ctx.message)

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return

    # Check if the message is a reply to the bot
    is_reply = message.reference and message.reference.cached_message and message.reference.cached_message.author == bot.user

    if is_reply:
        await process_gpt_message(message, bot_reply)
    else:
        await process_gpt_message(message, bot_respond)

# Start the bot
bot.run(discord_token)
