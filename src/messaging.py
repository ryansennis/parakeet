import os

async def send_message(channel, message_content):
    """Send a message in chunks of 2000 characters."""
    chunk_size = 2000
    for i in range(0, len(message_content), chunk_size):
        await channel.send(message_content[i:i + chunk_size])

async def send_privacy_policy(channel):
    """Send privacy policy."""
    privacy_policy_path = os.path.join(os.path.dirname(__file__), 'privacy_policy.txt')
    with open(privacy_policy_path, "r") as file:
        privacy_policy = file.read()
    await send_message(channel, privacy_policy)

async def send_help_message(channel):
    """Send help message."""
    help_message = (
        "Here are the commands you can use:\n"
        "1. `gpt:help` - Show this help message\n"
        "2. `gpt:privacy` - Show the privacy policy\n"
        "5. `gpt:<your message>` - Send a message to the AI bot\n"
    )
    await send_message(channel, help_message)

async def update_with_response(message, metrics):
    """Update the message with the generated response."""
    response = metrics.get("response", "Sorry, I couldn't generate a response.")
    response_time = metrics.get("response_time", 0)
    await message.edit(content=f"{response}\nResponse generated in {response_time:.2f} seconds.")