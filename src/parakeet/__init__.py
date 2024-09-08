from typing import List
import discord
from discord.ext import commands

# Local imports
from .config import discord_token, OPT_IN_ROLE_NAME, COMMAND_PREFIX, openai_api_key, MAX_DISCORD_MESSAGE_LENGTH
from .logger import logger
from .models import BotQuery, GPTModel
from .utils import has_opt_in_role