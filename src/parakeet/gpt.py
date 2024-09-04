import datetime
import discord
import logging
import openai
from typing import Union
from parakeet.config import OPT_IN_ROLE_NAME
from utils import (
    conversation_histories,
    has_opt_in_role,
    load_conversation_histories,
    save_conversation_histories,
    track_sent_messages,
    update_conversation_history,
)
from messaging import generate_response_message, generate_response_reply, send_message

async def generate_response(query: discord.Message) -> dict:
    """
    Generate response using OpenAI.

    Args:
        query (discord.Message): The message object from the user.

    Returns:
        dict: A dictionary containing the generated response metrics, including the response message,
              response time, and number of tokens.

    Raises:
        Exception: If there is an error generating the response.
    """
    try:
        server_id = query.guild.id if query.guild else "DM"
        user_id = query.author.id

        # Load conversation histories from file
        load_conversation_histories(server_id, user_id)

        # Store the message in the conversation history
        track_sent_messages(user_id, query)
        
        conversation_history = conversation_histories[server_id][user_id]['messages']
        start_time = datetime.datetime.now()
        user_nickname = query.author.nick if query.guild else query.author.name
        
        messages = [
            *conversation_history,  # Include the conversation history as background context
            {"role": "user", "content": query.content},
            {"role": "system", "content": f"You can mention the user with @{user_nickname}."},
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=4096
        )
        
        end_time = datetime.datetime.now()
        response_time = (end_time - start_time).total_seconds()
        response_message = response.choices[0].message['content'].strip()
        
        conversation_histories[server_id][user_id]['messages'].append({"role": "assistant", "content": response_message})
        save_conversation_histories(server_id, user_id)
        
        metrics = {
            "response": response_message,
            "response_time": response_time
        }
        
        return metrics
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        raise e

async def process_gpt_message(message: discord.Message) -> None:
    """
    Process a GPT message.
    Args:
        message (discord.Message): The message to process.
    Returns:
        None
    """
    try:
        user_id: int = message.author.id
        server_id: Union[int, str] = message.guild.id if message.guild else "DM"
        is_reply: bool = message.reference is not None

        user_message: str = message.content[len('gpt:'):].strip()

        if message.guild is None or has_opt_in_role(message.author, OPT_IN_ROLE_NAME):
            update_conversation_history(server_id, user_id, message.author, user_message)
            if is_reply:
                await generate_response_reply(message)
            else:
                await generate_response_message(message)
        else:
            await send_message(message.channel, "You need to opt in to interact with the bot. Ask a moderator for the `AI Trainer` role.")
    except Exception as e:
        logging.error(f"Error processing GPT message: {e}")
        await message.reply("Sorry, there was an error processing the message.")