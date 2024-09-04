# Parakeet Bot

Parakeet Bot is a Discord bot that leverages OpenAI's GPT models to interact with users, provide help, and manage server roles.

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/parakeet-bot.git
    cd parakeet-bot
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the `src` directory and add your configuration variables:
    ```sh
    cp src/.env.example src/.env
    ```

## Configuration

Ensure you have the following variables set in your `.env` file:

```env
OPENAI_API_KEY
DISCORD_BOT_TOKEN
OPT_IN_ROLE_NAME
FEEDBACK_BASE_DIR
COMMAND_PREFIX
MAX_DISCORD_MESSAGE_LENGTH
```