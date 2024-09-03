import discord
import openai
import os
from dotenv import load_dotenv  # Optional: For loading environment variables

# Load environment variables from a .env file (optional but recommended)
load_dotenv()

# Initialize Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent

# Create a Discord client instance
client = discord.Client(intents=intents)

# Replace with the actual role name that users must have to opt in
OPT_IN_ROLE_NAME = "AI Trainer"

# Set up your OpenAI API key securely
openai.api_key = os.getenv('OPENAI_API_KEY')  # Ensure you have set this in your environment
discord_token = os.getenv('DISCORD_BOT_TOKEN')  # Ensure you have set this in your environment

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check if the message starts with the prefix 'gpt:'
    if message.content.startswith('gpt:'):
        # Remove the prefix to get the actual user message
        user_message = message.content[len('gpt:'):].strip()

        # Check if the user has the opt-in role
        if has_opt_in_role(message.author):
            # Save the message content to a file
            save_message(user_message)

            # Generate a response using OpenAI's chat model
            response = generate_response(user_message, message.author.name)
            
            # Send the response back to the Discord channel
            await send_long_message(message.channel, response)
        else:
            await message.channel.send("You need to opt in to interact with the bot. Ask a moderator for the AI Trainer role.")
    else:
        return

def has_opt_in_role(user):
    """Check if the user has the opt-in role."""
    for role in user.roles:
        if role.name == OPT_IN_ROLE_NAME:
            return True
    return False

def save_message(content):
    """Save the message content to a file."""
    with open("opted_in_messages.txt", "a") as f:
        f.write(content + "\n")

def generate_response(user_message, username):
    """Generate a response using OpenAI's chat model."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # You can use "gpt-4" if you have access to it
            messages=[
                {"role": "user", "content": f"The following message is from a Discord member named {username}: '{user_message}'. Please do whatever it is they asked for."}
            ],
            max_tokens=150,
            temperature=0.7,
            n=1,
            stop=None
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error generating response: {e}"
    
async def send_long_message(channel, message):
    """Send a long message in chunks, respecting Discord's character limit."""
    if len(message) <= 2000:
        await channel.send(message)
    else:
        for i in range(0, len(message), 2000):
            await channel.send(message[i:i+2000])

client.run(discord_token)