from . import commands
from .logger import logger

class ConversationEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def on_expire(self, root_message_id: int):
        logger.info(f"Handling expiration for conversation history with root_message_id: {root_message_id}")
        self.bot.dispatch('expire', root_message_id)

async def setup(bot):
    await bot.add_cog(ConversationEvents(bot))