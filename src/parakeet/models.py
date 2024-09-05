from . import discord
from .logger import logger
from enum import Enum
from typing import NamedTuple

# import discord message object


class GPTModel(Enum):
    """
    Enum class representing different GPT models.

    Attributes:
        GPT_4O (str): Represents the GPT-4O model.
        GPT_4O_MINI (str): Represents the GPT-4O Mini model.
        GPT_3_5_TURBO (str): Represents the GPT-3.5 Turbo model.
    """
    GPT_4O = "gpt-4o-"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

class BotQuery:
    """
    Represents a query for the bot.
    Attributes:
        message (discord.Message): The message associated with the query.
        model (GPTModel): The GPT model used for processing the query.
    Methods:
        unpack() -> tuple[discord.Message, GPTModel]: Unpacks the query into a tuple of message and model.
    """
    def __init__(self, message: discord.Message, model: GPTModel):
        try:
            if not isinstance(message, discord.Message):
                raise TypeError("The 'message' parameter must be an instance of the 'discord.Message' class.")
            if not isinstance(model, GPTModel):
                raise TypeError("The 'model' parameter must be an instance of the 'GPTModel' enum.")
            
            self.message = message
            self.model = model
        except Exception as e:
            logger.error(f"Error initializing BotQuery: {e}")

    def unpack(self) -> tuple[discord.Message, GPTModel]:
        return self.message, self.model
    
    def set_message(self, message: discord.Message) -> None:
        self.message = message