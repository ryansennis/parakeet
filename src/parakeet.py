import discord
import openai
import os
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Initialize Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
intents.reactions = True  # Enable reactions intent

# Create a Discord client instance
client = discord.Client(intents=intents)

# Load configurations from .env
OPT_IN_ROLE_NAME = os.getenv('OPT_IN_ROLE_NAME')
FEEDBACK_BASE_DIR = os.getenv('FEEDBACK_BASE_DIR')
USER_USER_INTERACTIONS_DIR = os.path.join(FEEDBACK_BASE_DIR, os.getenv('USER_USER_INTERACTIONS_DIR'))
USER_BOT_INTERACTIONS_DIR = os.path.join(FEEDBACK_BASE_DIR, os.getenv('USER_BOT_INTERACTIONS_DIR'))
CONVERSATION_TIMEOUT = timedelta(minutes=int(os.getenv('CONVERSATION_TIMEOUT_MINUTES')))
RESPONSE_TIMEOUT = int(os.getenv('RESPONSE_TIMEOUT_SECONDS'))

# Set up your OpenAI API key securely
openai.api_key = os.getenv('OPENAI_API_KEY')  # Ensure you have set this in your environment
discord_token = os.getenv('DISCORD_BOT_TOKEN')  # Ensure you have set this in your environment

# Dictionary to hold conversation history per user
conversation_histories = {}
message_histories = {}

def ensure_directory_exists(path):
    """Ensure the directory exists, and if not, create it."""
    if not os.path.exists(path):
        os.makedirs(path)

def store_feedback(user_id, server_id, message_id, feedback_type, interaction_details):
    """Store user feedback on the bot's response in a file for each user and server."""
    
    # Define the directory for storing server and user feedback
    user_dir = os.path.join(USER_BOT_INTERACTIONS_DIR, "users", str(user_id))
    server_dir = os.path.join(USER_BOT_INTERACTIONS_DIR, "servers", str(server_id))

    # Ensure the directories exist
    ensure_directory_exists(user_dir)
    ensure_directory_exists(server_dir)

    # Define file paths
    user_file_path = os.path.join(user_dir, "interaction_log.txt")
    server_file_path = os.path.join(server_dir, "interaction_log.txt")

    # Write to the user's interaction file
    with open(user_file_path, "a") as user_file:
        user_file.write(f"Message ID: {message_id}, Feedback: {feedback_type}, Interaction: {interaction_details}\n")
    
    # Write to the server's interaction file
    with open(server_file_path, "a") as server_file:
        server_file.write(f"User ID: {user_id}, Message ID: {message_id}, Feedback: {feedback_type}, Interaction: {interaction_details}\n")
    
    logging.info(f"Feedback stored: User {user_id} gave a {feedback_type} on message {message_id} in server {server_id}")

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}.')

    for guild in client.guilds:
        # Check if the "AI Trainer" role exists
        role = discord.utils.get(guild.roles, name=OPT_IN_ROLE_NAME)
        if role is None:
            # If the role doesn't exist, create it
            try:
                await guild.create_role(name=OPT_IN_ROLE_NAME, reason="Role created by bot for AI training opt-in. See privacy policy with 'gpt:privacy' command for more.")
                logging.info(f'Created "{OPT_IN_ROLE_NAME}" role in guild: {guild.name}')
            except Exception as e:
                logging.error(f'Failed to create "{OPT_IN_ROLE_NAME}" role in guild: {guild.name}. Error: {e}')
        else:
            logging.info(f'"{OPT_IN_ROLE_NAME}" role already exists in guild: {guild.name}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = message.author.id

    # Check if the user wants to see the help message
    if message.content.startswith('gpt:help'):
        await message.channel.send(get_help_message())
        return
    
    # Check if the user wants to see the privacy policy
    if message.content.startswith('gpt:privacy'):
        await send_privacy_policy(message.channel)
        return

    # Check if the user wants to end the conversation
    if message.content.startswith('gpt:end'):
        if user_id in conversation_histories:
            del conversation_histories[user_id]
        await message.channel.send("Your conversation has been ended.")
        return

    # Check if the user wants to clear the conversation and delete messages
    if message.content.startswith('gpt:clear'):
        await clear_conversation_and_messages(user_id, message.channel)
        await message.channel.send("Your conversation and related messages have been cleared.")
        return

    # Handle user-user interaction logging
    if message.reference:
        # Check if this message is a reply to another user
        replied_message = await message.channel.fetch_message(message.reference.message_id)
        if replied_message.author != client.user:
            await handle_user_user_interaction(replied_message, message)
        return

    # Check if the message starts with the prefix 'gpt:'
    if message.content.startswith('gpt:'):
        # Remove the prefix to get the actual user message
        user_message = message.content[len('gpt:'):].strip()

        # Check if the user has the opt-in role
        if has_opt_in_role(message.author):
            # Update or create the user's conversation history
            update_conversation_history(user_id, message.author, user_message)

            # Send a message indicating that the response is being generated
            generating_message = await message.channel.send("Generating Response...")

            # Generate the response asynchronously
            metrics = await generate_response(user_id)
            
            # Update the message with the generated response and metrics
            await update_with_response(generating_message, metrics)
            
            # Track the sent message ID for later clearing if needed
            track_sent_messages(user_id, [generating_message.id])
        else:
            await message.channel.send("You need to opt in to interact with the bot. Ask a moderator for the AI Trainer role.")
    else:
        return

async def handle_user_user_interaction(original_message, reply_message):
    """Handle logging of user-to-user interactions."""
    if has_opt_in_role(reply_message.author):
        user_dir = os.path.join(USER_USER_INTERACTIONS_DIR, str(reply_message.author.id))
        ensure_directory_exists(user_dir)
        interaction_log = os.path.join(user_dir, "interaction_log.txt")
        
        with open(interaction_log, "a") as log_file:
            log_file.write(f"Original Message by {original_message.author.display_name} ({original_message.author.id}): {original_message.content}\n")
            log_file.write(f"Reply by {reply_message.author.display_name} ({reply_message.author.id}): {reply_message.content}\n")
            log_file.write("-" * 20 + "\n")
        
        logging.info(f"Logged user-user interaction between {original_message.author.id} and {reply_message.author.id}")

def has_opt_in_role(user):
    """Check if the user has the opt-in role."""
    for role in user.roles:
        if role.name == OPT_IN_ROLE_NAME:
            return True
    return False

def update_conversation_history(user_id, user, user_message):
    """Update the user's conversation history or start a new one."""
    now = datetime.now()
    if user_id not in conversation_histories or now - conversation_histories[user_id]['timestamp'] > CONVERSATION_TIMEOUT:
        conversation_histories[user_id] = {
            'messages': [{"role": "system", "content": "You are a helpful assistant."}],
            'timestamp': now
        }
    conversation_histories[user_id]['messages'].append({"role": "user", "content": f"The following message is from a Discord member named {user.display_name} ({user.mention}): '{user_message}'."})
    conversation_histories[user_id]['timestamp'] = now
    logging.info(f"Conversation history updated for user {user_id}.")

async def generate_response(user_id):
    """Generate a response using OpenAI's chat model, continuing the conversation."""
    try:
        conversation_history = conversation_histories[user_id]['messages']
        start_time = datetime.now()

        response = await asyncio.to_thread(openai.ChatCompletion.create,
            model="gpt-4o",  # Using GPT-4o model as requested
            messages=conversation_history,
            max_tokens=4096,
            temperature=0.7,
            n=1,
            stop=None
        )
        
        response_chunk = response['choices'][0]['message']['content'].strip()
        conversation_histories[user_id]['messages'].append({"role": "assistant", "content": response_chunk})

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        metrics = {
            "response": response_chunk,
            "tokens": response['usage']['total_tokens'],
            "duration": duration
        }

        logging.info(f"Response generated for user {user_id} in {duration:.2f} seconds using {metrics['tokens']} tokens.")
        return metrics
    
    except Exception as e:
        logging.error(f"Error generating response for user {user_id}: {e}")
        return {"response": f"Error generating response: {e}", "tokens": 0, "duration": 0}

async def update_with_response(generating_message, metrics):
    """Update the 'Generating Response...' message with the final response and metrics."""
    final_content = (
        f"{metrics['response']}\n\n"
        f"**Metrics:**\n"
        f"Tokens used: {metrics['tokens']}\n"
        f"Time taken: {metrics['duration']:.2f} seconds"
    )
    
    # Send the final message as an embedded message and add reactions
    embed = discord.Embed(description=final_content)
    final_message = await generating_message.channel.send(embed=embed)
    
    # Add thumbs up and thumbs down reactions
    await final_message.add_reaction("👍")
    await final_message.add_reaction("👎")

    # Track the sent message ID for later clearing if needed
    track_sent_messages(generating_message.author.id, [final_message.id])
    logging.info(f"Response updated and reactions added for message {final_message.id}.")

@client.event
async def on_reaction_add(reaction, user):
    """Handle user reactions to rate the bot's response."""
    if user.bot:
        return  # Ignore reactions from bots
    
    message = reaction.message
    server_id = message.guild.id if message.guild else "DM"
    
    if reaction.emoji == "👍":
        await message.channel.send(f"{user.display_name} liked the response!")
        store_feedback(user.id, server_id, message.id, "upvote", message.content)
    elif reaction.emoji == "👎":
        await message.channel.send(f"{user.display_name} disliked the response.")
        store_feedback(user.id, server_id, message.id, "downvote", message.content)

def track_sent_messages(user_id, message_ids):
    """Track messages sent by the bot to a specific user."""
    if user_id not in message_histories:
        message_histories[user_id] = []
    message_histories[user_id].extend(message_ids)
    logging.info(f"Tracked sent messages for user {user_id}: {message_ids}")

async def clear_conversation_and_messages(user_id, channel):
    """Clear the user's conversation history and delete related messages."""
    if user_id in message_histories:
        for message_id in message_histories[user_id]:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.delete()
                logging.info(f"Deleted message {message_id} for user {user_id}.")
            except discord.NotFound:
                logging.warning(f"Message {message_id} for user {user_id} not found (likely already deleted).")
        del message_histories[user_id]

    if user_id in conversation_histories:
        del conversation_histories[user_id]
        logging.info(f"Cleared conversation history for user {user_id}.")

async def send_privacy_policy(channel):
    """Send the privacy policy to the specified channel."""
    try:
        with open("privacy_policy.txt", "r") as file:
            privacy_policy = file.read()

        if len(privacy_policy) <= 2000:
            await channel.send(privacy_policy)
        else:
            for i in range(0, len(privacy_policy), 2000):
                await channel.send(privacy_policy[i:i+2000])
    except FileNotFoundError:
        await channel.send("Sorry, the privacy policy file could not be found.")
        logging.error("Privacy policy file not found.")
    except Exception as e:
        await channel.send("An error occurred while trying to retrieve the privacy policy.")
        logging.error(f"Error sending privacy policy: {e}")

def get_help_message():
    """Return a help message describing the available commands."""
    help_message = (
        "**gpt:help** - Shows this help message.\n"
        "**gpt:end** - Ends the current conversation with the AI and clears the conversation history.\n"
        "**gpt:clear** - Deletes all messages related to your conversation and clears the conversation history.\n"
        "**gpt:[your message]** - Sends a message to the AI and receives a response. You must have the 'AI Trainer' role to use this command.\n"
        "\n"
        "*Example usage:* `gpt: What is the weather like today?`\n"
        "\n"
        "To interact with the bot, make sure you have the 'AI Trainer' role. You can request the role from a server moderator."
    )
    return help_message

async def clear_conversation_history_periodically():
    """Periodically clear old conversation histories."""
    while True:
        now = datetime.now()
        to_delete = [user_id for user_id, data in conversation_histories.items() if now - data['timestamp'] > CONVERSATION_TIMEOUT]
        for user_id in to_delete:
            await clear_conversation_and_messages(user_id, None)
        await asyncio.sleep(60)  # Check every minute

async def main():
    """Main entry point for running the bot."""
    # Start the periodic cleanup task
    asyncio.create_task(clear_conversation_history_periodically())

    # Run the Discord bot
    await client.start(discord_token)

# Run the bot using asyncio.run()
asyncio.run(main())