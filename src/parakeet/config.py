import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load configurations from .env
OPT_IN_ROLE_NAME = os.getenv('OPT_IN_ROLE_NAME')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX')
MAX_DISCORD_MESSAGE_LENGTH = os.getenv('MAX_DISCORD_MESSAGE_LENGTH')

# Set up your API keys securely
openai_api_key = os.getenv('OPENAI_API_KEY')  # Ensure you have set this in your environment
discord_token = os.getenv('DISCORD_BOT_TOKEN')  # Ensure you have set this in your environment