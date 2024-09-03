import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load configurations from .env
OPT_IN_ROLE_NAME = os.getenv('OPT_IN_ROLE_NAME')
FEEDBACK_BASE_DIR = os.getenv('FEEDBACK_BASE_DIR')
USER_USER_INTERACTIONS_DIR = os.path.join(FEEDBACK_BASE_DIR, os.getenv('USER_USER_INTERACTIONS_DIR', '')) if FEEDBACK_BASE_DIR else None
USER_BOT_INTERACTIONS_DIR = os.path.join(FEEDBACK_BASE_DIR, os.getenv('USER_BOT_INTERACTIONS_DIR', '')) if FEEDBACK_BASE_DIR else None

try:
    CONVERSATION_TIMEOUT = timedelta(minutes=int(os.getenv('CONVERSATION_TIMEOUT_MINUTES', '0')))
except ValueError:
    CONVERSATION_TIMEOUT = timedelta(minutes=0)

try:
    RESPONSE_TIMEOUT = int(os.getenv('RESPONSE_TIMEOUT_SECONDS', '0'))
except ValueError:
    RESPONSE_TIMEOUT = 0

# Set up your OpenAI API key securely
openai_api_key = os.getenv('OPENAI_API_KEY')  # Ensure you have set this in your environment
discord_token = os.getenv('DISCORD_BOT_TOKEN')  # Ensure you have set this in your environment# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load configurations from .env
OPT_IN_ROLE_NAME = os.getenv('OPT_IN_ROLE_NAME')
FEEDBACK_BASE_DIR = os.getenv('FEEDBACK_BASE_DIR')
USER_USER_INTERACTIONS_DIR = os.path.join(FEEDBACK_BASE_DIR, os.getenv('USER_USER_INTERACTIONS_DIR', '')) if FEEDBACK_BASE_DIR else None
USER_BOT_INTERACTIONS_DIR = os.path.join(FEEDBACK_BASE_DIR, os.getenv('USER_BOT_INTERACTIONS_DIR', '')) if FEEDBACK_BASE_DIR else None

try:
    CONVERSATION_TIMEOUT = timedelta(minutes=int(os.getenv('CONVERSATION_TIMEOUT_MINUTES', '0')))
except ValueError:
    CONVERSATION_TIMEOUT = timedelta(minutes=0)

try:
    RESPONSE_TIMEOUT = int(os.getenv('RESPONSE_TIMEOUT_SECONDS', '0'))
except ValueError:
    RESPONSE_TIMEOUT = 0

# Set up your OpenAI API key securely
openai_api_key = os.getenv('OPENAI_API_KEY')  # Ensure you have set this in your environment
discord_token = os.getenv('DISCORD_BOT_TOKEN')  # Ensure you have set this in your environment