from . import (
    discord,
    List,
    commands,
    bot,
    logger,
    BotQuery,
    GPTModel,
    COMMAND_PREFIX,
    OPT_IN_ROLE_NAME,
    discord_token,
    ConversationHistory
)
from .gpt import process_gpt_message
from .messaging import (
    bot_message,
    bot_reply,
    handle_expiration,
    send_help_message,
    send_privacy_policy
)

# Initialize Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
intents.reactions = True  # Enable reactions intent
intents.dm_messages = True  # Enable DM messages intent

# Create a bot instance with the specified command prefix and intents
bot: commands.Bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Initialize the conversation history
conversation_histories: List[ConversationHistory] = []

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
        introduction_prompt: str = "You have just joined a new server. Please introduce yourself to the members of the server."
        query = BotQuery(message=introduction_prompt, model=GPTModel.GPT_4O)
        await process_gpt_message(query, bot_message, None)

# remove default help command before registering our own
bot.remove_command('help')

@bot.command(name='help')
async def send_help(ctx):
    await send_help_message(ctx.message)

@bot.command(name='privacy')
async def send_privacy(ctx):
    await send_privacy_policy(ctx.message)

# default on_message behavior, if no commands are invoked
@bot.event
async def on_message(message: discord.Message) -> None:
    try:
        assert isinstance(message, discord.Message)

        logger.info(f"Received message: {message.content} from {message.author}")

        # Determine the conversation history key or quit if the root message is from the bot
        if message.reference:
            conversation_key = message.reference.message_id
            logger.info(f"Using existing conversation history for message {message.id}")
        else:
            if message.author == bot.user:
                logger.info("Ignoring message from bot")
                return
            
            conversation_key = message.id
            new_history = ConversationHistory(
                root_message_id=message.id,
                bot=bot,
                on_expire=handle_expiration
            )
            new_history.start_tracking()
            conversation_histories.append(new_history)
            logger.info(f"Created new conversation history for message {message.id}")

        # Find the conversation history by key
        conversation_history = next((history for history in conversation_histories if history.message_id == conversation_key), None)

        if conversation_history:
            if conversation_history.is_expired():
                conversation_history.clear_history()
                logger.info(f"Cleared expired conversation history for message {message.id}")

            role = "assistant" if message.author.bot else "user"
            conversation_history.add_message(role, message.content, message.id)
            logger.info(f"Added message to conversation history for message {message.id}")
        else:
            logger.error(f"Conversation history not found for message {message.id}")

        if message.content.startswith('gpt:'):
            logger.info(f"Message starts with 'gpt:', processing with GPT model")
            query = BotQuery(message=message, model=GPTModel.GPT_4O)
            await process_gpt_message(query, bot_reply, conversation_history)
        else:
            is_reply_to_bot = False
            if message.reference:
                ref_message = await message.channel.fetch_message(message.reference.message_id)
                if ref_message.author == bot.user:
                    is_reply_to_bot = True
                    logger.info(f"Message is a reply to the bot's message")

            bot_was_mentioned = False
            if bot.user.mentioned_in(message):
                bot_was_mentioned = True
                logger.info(f"Bot was mentioned in the message")
    
            query = BotQuery(message=message, model=GPTModel.GPT_4O)

            if is_reply_to_bot:
                logger.info(f"Processing message as a reply to bot")
                await process_gpt_message(query, bot_reply, conversation_history)
            elif bot_was_mentioned:
                logger.info(f"Processing message as a mention of bot")
                await process_gpt_message(query, bot_message, conversation_history)
            else:
                logger.info(f"Message is neither a reply to bot nor a mention of bot, ignoring")
                return
    except Exception as e:
        logger.error(f"An error occurred: {e}")

@bot.event
async def on_expire(root_message_id: int):
    handle_expiration(root_message_id)

async def main():
    # Load the ConversationEvents cog
    await bot.load_extension('parakeet.events')

    # Start the bot
    await bot.start(discord_token)

# Run the main function
import asyncio
asyncio.run(main())