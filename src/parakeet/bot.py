from . import (
    discord,
    commands,
    logger,
    BotQuery,
    GPTModel,
    COMMAND_PREFIX,
    OPT_IN_ROLE_NAME,
    discord_token
)

from .gpt import process_gpt_message
from .messaging import (
    bot_message,
    bot_reply,
    send_help_message,
    send_privacy_policy
)
from .conversation import ConversationManager

class ParakeetBot:
    def __init__(self):
        # Initialize Discord intents
        intents = discord.Intents.default()
        intents.message_content = True  # Enable the message content intent
        intents.reactions = True  # Enable reactions intent
        intents.dm_messages = True  # Enable DM messages intent

        # Create a bot instance with the specified command prefix and intents
        self.bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
        self.conversation_manager = ConversationManager()

        # Register event handlers
        self.bot.event(self.on_ready)
        self.bot.event(self.on_guild_join)
        self.bot.event(self.on_message)

        # Remove default help command before registering our own
        self.bot.remove_command('help')

    async def on_ready(self):
        logger.info(f'Logged into {len(self.bot.guilds)} server(s).')

    async def on_guild_join(self, guild: discord.Guild):
        logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')

        # Check the server for the opt in role and add it if it doesn't exist
        opt_in_role = discord.utils.get(guild.roles, name=OPT_IN_ROLE_NAME)
        if not opt_in_role:
            await guild.create_role(name=OPT_IN_ROLE_NAME)
            await guild.system_channel.send(f'Created opt-in role: {OPT_IN_ROLE_NAME}')

            # Send a gpt message introducing the bot to the server
            introduction_prompt: str = "You have just joined a new server. Please introduce yourself to the members of the server."
            message = discord.Message()
            message.content = introduction_prompt
            query = BotQuery(message=message, model=GPTModel.GPT_4O)
            await process_gpt_message(query, bot_message)

    @commands.command(name='help')
    async def send_help(self, ctx: commands.Context):
        await send_help_message(ctx.channel)

    @commands.command(name='privacy')
    async def send_privacy(self, ctx: commands.Context):
        await send_privacy_policy(ctx.channel)

    async def on_message(self, message: discord.Message):
        try:
            if not isinstance(message, discord.Message):
                raise(TypeError("message must be an instance of discord.Message"))

            logger.info(f"Received message: {message.content} from {message.author}")

            is_reply_to_bot = False
            if message.reference:
                self.conversation_manager.handle_message(message, self.bot.user)
                ref_message = await message.channel.fetch_message(message.reference.message_id)
                if ref_message.author == self.bot.user:
                    is_reply_to_bot = True
                    logger.info(f"Message is a reply to the bot's message")

            bot_was_mentioned = False
            if self.bot.user.mentioned_in(message):
                bot_was_mentioned = True
                logger.info(f"Bot was mentioned in the message")

            query = BotQuery(message=message, model=GPTModel.GPT_4O)

            # Check if the message is from a guild and if the user has the opt-in role
            has_opt_in_role = True
            if message.guild is not None and isinstance(message.author, discord.Member):
                has_opt_in_role = discord.utils.get(message.author.roles, name=OPT_IN_ROLE_NAME) is not None

            if not has_opt_in_role and message.author != self.bot.user:
                logger.info(f"User does not have the opt-in role, ignoring message")
                return

            if is_reply_to_bot:
                # check to see if bot sent message
                if message.author == self.bot.user:
                    return

                logger.info(f"Processing message as a reply to bot")
                await process_gpt_message(query, bot_reply)
            elif bot_was_mentioned:
                logger.info(f"Processing message as a mention of bot")
                await process_gpt_message(query, bot_reply)
            elif message.channel.type == discord.ChannelType.private and message.author != self.bot.user:
                logger.info(f"Processing message in a private channel")
                await process_gpt_message(query, bot_message)
            else:
                logger.info(f"Message is neither a reply to bot nor a mention of bot, ignoring")
                return
        except Exception as e:
            logger.error(f"Error occured in parakeet.on_message: {e}")

    async def run(self):
        await self.bot.start(discord_token)

# Run the bot
if __name__ == '__main__':
    import asyncio
    bot_instance = ParakeetBot()
    asyncio.run(bot_instance.run())