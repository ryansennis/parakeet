from . import discord
from .logger import logger
from enum import Enum

# import discord message object


class GPTModel(Enum):
    """
    Enum class representing different GPT models.

    Attributes:
        GPT_4O (str): Represents the GPT-4O model.
        GPT_4O_MINI (str): Represents the GPT-4O Mini model.
        GPT_3_5_TURBO (str): Represents the GPT-3.5 Turbo model.
    """
    GPT_4O = "gpt-4o"
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
    def __init__(self, message, model):
        if not isinstance(message, discord.Message):
            raise TypeError("message must be an instance of discord.Message")
        if not isinstance(model, GPTModel):
            raise TypeError("model must be an instance of GPTModel")
        self.message = message
        self.model = model

    def unpack(self) -> tuple[discord.Message, GPTModel]:
        return self.message, self.model
    
    def set_message(self, message: discord.Message) -> None:
        self.message = message