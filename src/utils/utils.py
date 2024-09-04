import os
import json
import logging
import discord
from datetime import datetime
from config import USER_BOT_INTERACTIONS_DIR, CONVERSATION_TIMEOUT

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary to hold conversation history per server and user
conversation_histories = {}
message_histories = {}

USER_USER_INTERACTIONS_FILE = os.path.join(USER_BOT_INTERACTIONS_DIR, "user_user_interactions.json")

USER_DATA_DIR = os.path.join(USER_BOT_INTERACTIONS_DIR, "user_data")

def ensure_directory_exists(path):
    """Ensure the directory exists, and if not, create it."""
    if not os.path.exists(path):
        os.makedirs(path)

def save_conversation_histories(server_id, user_id):
    """Save conversation history for a specific user to a file."""
    ensure_directory_exists(USER_DATA_DIR)
    user_file = os.path.join(USER_DATA_DIR, f"{server_id}_{user_id}.json")
    
    with open(user_file, "w") as file:
        json.dump(conversation_histories[server_id][user_id], file, indent=4)

def load_conversation_histories(server_id, user_id):
    """Load conversation history for a specific user from a file."""
    user_file = os.path.join(USER_DATA_DIR, f"{server_id}_{user_id}.json")
    
    if os.path.exists(user_file):
        with open(user_file, "r") as file:
            conversation_histories[server_id][user_id] = json.load(file)
    else:
        conversation_histories[server_id][user_id] = {"messages": [], "timestamp": ""}

def update_conversation_history(server_id, user_id, user, user_message):
    now = datetime.now()
    if server_id not in conversation_histories:
        conversation_histories[server_id] = {}
    if user_id not in conversation_histories[server_id] or not conversation_histories[server_id][user_id].get('timestamp') or now - datetime.fromisoformat(conversation_histories[server_id][user_id]['timestamp']) > CONVERSATION_TIMEOUT:
        conversation_histories[server_id][user_id] = {
            'messages': [{"role": "system", "content": "Try to act like another user in the server. Be infromal with your grammar, like someone engaging an a casual internet conversation. Match the style and the tone of the user you're talking to."}],
            'timestamp': now.isoformat()
        }
    conversation_histories[server_id][user_id]['messages'].append({"role": "user", "content": f"The following message is from a Discord member named {user.display_name} ({user.mention}): '{user_message}'."})
    conversation_histories[server_id][user_id]['timestamp'] = now.isoformat()

    save_conversation_histories(server_id, user_id)
    logger.info(f"Conversation history updated for user {user_id} in server {server_id}.")

async def reset_user_conversation(server_id, user_id, channel):
    """Clear conversation and message history for a user."""
    if server_id in conversation_histories and user_id in conversation_histories[server_id]:
        del conversation_histories[server_id][user_id]
        user_file = os.path.join(USER_DATA_DIR, f"{server_id}_{user_id}.json")
        if os.path.exists(user_file):
            os.remove(user_file)
        logger.info(f"Cleared conversation history for user {user_id} in server {server_id}")
    if user_id in message_histories:
        del message_histories[user_id]
        logger.info(f"Cleared message history for user {user_id}")
    if channel:
        await channel.send(f"Cleared conversation history for user {user_id} in server {server_id}.")

async def clear_conversation_and_messages(server_id, user_id, channel):
    """Clear conversation and delete messages."""
    if user_id in message_histories:
        for message_id in message_histories[user_id]:
            try:
                msg = await channel.fetch_message(message_id)
                await msg.delete()
                logger.info(f"Deleted message {message_id} for user {user_id}.")
            except discord.NotFound:
                logger.warning(f"Message {message_id} for user {user_id} not found (likely already deleted).")
        del message_histories[user_id]

    if server_id in conversation_histories and user_id in conversation_histories[server_id]:
        del conversation_histories[server_id][user_id]
        save_conversation_histories()
        logger.info(f"Cleared conversation history for user {user_id} in server {server_id}.")

def track_sent_messages(user_id, messages):
    """Track sent messages."""
    if user_id not in message_histories:
        message_histories[user_id] = []
    message_ids = [message.id for message in messages]
    message_histories[user_id].extend(message_ids)
    logger.info(f"Tracked sent messages for user {user_id}: {message_ids}")

def log_user_user_interaction(replied_message, message):
    """Log user-to-user interaction."""
    logger.info(f"User {message.author.id} replied to user {replied_message.author.id} with message: {message.content}")

    # Prepare the interaction data
    interaction_data = {
        "replied_to_user_id": replied_message.author.id,
        "replied_to_user_name": replied_message.author.display_name,
        "replied_to_message": replied_message.content,
        "replying_user_id": message.author.id,
        "replying_user_name": message.author.display_name,
        "replying_message": message.content,
        "timestamp": datetime.now().isoformat()
    }

    # Ensure the directory exists
    ensure_directory_exists(USER_BOT_INTERACTIONS_DIR)

    # Read existing interactions from the file
    if os.path.exists(USER_USER_INTERACTIONS_FILE):
        with open(USER_USER_INTERACTIONS_FILE, "r") as file:
            interactions = json.load(file)
    else:
        interactions = []

    # Append the new interaction
    interactions.append(interaction_data)

    # Write the updated interactions back to the file
    with open(USER_USER_INTERACTIONS_FILE, "w") as file:
        json.dump(interactions, file, indent=4)

def store_feedback(user_id, server_id, message_id, feedback_type, message_content):
    """Store feedback from users."""
    feedback_data = {
        "user_id": user_id,
        "server_id": server_id,
        "message_id": message_id,
        "feedback_type": feedback_type,
        "message_content": message_content,
        "timestamp": datetime.now().isoformat()
    }
    feedback_file = os.path.join(USER_BOT_INTERACTIONS_DIR, "feedback.json")
    ensure_directory_exists(USER_BOT_INTERACTIONS_DIR)
    
    if os.path.exists(feedback_file):
        with open(feedback_file, "r") as file:
            feedback_list = json.load(file)
    else:
        feedback_list = []

    feedback_list.append(feedback_data)

    with open(feedback_file, "w") as file:
        json.dump(feedback_list, file, indent=4)
    
    logger.info(f"Stored feedback: {feedback_data}")

def has_opt_in_role(user, role_name):
    """Check if a user has a specific role."""
    return any(role.name == role_name for role in user.roles)

def record_reaction(user_id, message_id, reaction_type):
    """Record user reactions to messages."""
    reaction_data = {
        "user_id": user_id,
        "message_id": message_id,
        "reaction_type": reaction_type,
        "timestamp": datetime.now().isoformat()
    }
    reactions_file = os.path.join(USER_BOT_INTERACTIONS_DIR, "reactions.json")
    ensure_directory_exists(USER_BOT_INTERACTIONS_DIR)
    
    if os.path.exists(reactions_file):
        with open(reactions_file, "r") as file:
            reactions_list = json.load(file)
    else:
        reactions_list = []

    reactions_list.append(reaction_data)

    with open(reactions_file, "w") as file:
        json.dump(reactions_list, file, indent=4)
    
    logger.info(f"Recorded reaction: {reaction_data}")