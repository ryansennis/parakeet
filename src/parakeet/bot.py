import discord
from discord.ext import commands
from .config import discord_token, OPT_IN_ROLE_NAME, COMMAND_PREFIX
from .messaging import send_help_message, send_privacy_policy, bot_reply, bot_message
from .shared import logger
from .gpt import process_gpt_message
from .models import BotQuery, GPTModel

# Initialize Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
intents.reactions = True  # Enable reactions intent
intents.dm_messages = True  # Enable DM messages intent

# Create a bot instance with the specified command prefix and intents
bot: commands.Bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready() -> None:
    logger.info(f'Logged into {len(bot.guilds)} server(s).')

@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')

    # Check the server for the opt in role and add it if it doesn't exist
    opt_in_role = discord.utils.get(guild.roles, name=OPT_IN_ROLE_NAME)
    if not opt_in_role:
        await guild.create_role(name=OPT_IN_ROLE_NAME)
        await guild.system_channel.send(f'Created opt-in role: {OPT_IN_ROLE_NAME}')

        # Send a gpt message introducing the bot to the server
        introduction_prompt = "You have just joined a new server. Please introduce yourself to the members of the server."
        query = BotQuery(message=introduction_prompt, model=GPTModel.GPT_4O.value)
        await process_gpt_message(query, bot_message)

# remove default help command before registering our own
bot.remove_command('help')

@bot.command(name='help')
async def send_help(ctx):
    await send_help_message(ctx.message)

@bot.command(name='privacy')
async def send_privacy(ctx):
    await send_privacy_policy(ctx.message)

# discord.ext.commands.Bot does not work with this logic
@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return

    # Check if the message is a reply to the bot
    is_reply_to_bot = message.reference and message.reference.cached_message and message.reference.cached_message.author == bot.user

    # Create a BotQuery instance using the message and the gpt-4o-mini model
    query = BotQuery(message=message, model=GPTModel.GPT_4O_MINI)

    # Process the message
    if is_reply_to_bot:
        await process_gpt_message(query, bot_reply)
    else:
        await process_gpt_message(query, bot_message)

# Start the bot
bot.run(discord_token)
