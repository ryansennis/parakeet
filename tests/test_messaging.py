import unittest
from unittest.mock import MagicMock, AsyncMock, patch, mock_open
import discord
from src.parakeet.messaging import (
    send_message, 
    add_feedback_reactions, 
    send_reply, 
    send_privacy_policy,
    send_help_message,
    bot_reply,
    bot_respond
)

class MessagingTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_send_message(self):
        # Create a mock text channel
        channel = MagicMock(spec=discord.TextChannel)

        # Create a mock message content
        message_content = "This is a test message."

        # Mock the channel.send method
        channel.send = AsyncMock()

        # Call the send_message function
        await send_message(channel, message_content)

        # Assert that the channel.send method was called with the correct arguments
        channel.send.assert_called_once_with(message_content)

    async def test_add_feedback_reactions(self):
        # Create a mock response message
        response = MagicMock()

        # Mock the response.add_reaction method
        response.add_reaction = AsyncMock()

        # Call the add_feedback_reactions function
        await add_feedback_reactions(response)

        # Assert that the response.add_reaction method was called with the correct arguments
        response.add_reaction.assert_any_call("👍")
        response.add_reaction.assert_any_call("👎")

    async def test_send_reply(self):
        # Create a mock message
        message = MagicMock(spec=discord.Message)

        # Create a mock reply content
        reply_content = "This is a test reply."

        # Mock the message.reply method
        message.reply = AsyncMock()

        # Call the send_reply function
        await send_reply(message, reply_content)

        # Assert that the message.reply method was called with the correct arguments
        message.reply.assert_called_once_with(reply_content)

    @patch("src.parakeet.messaging.send_message", new_callable=AsyncMock)
    @patch("builtins.open", new_callable=mock_open, read_data="This is the privacy policy.")
    @patch("os.path.join", return_value="privacy_policy.txt")
    async def test_send_privacy_policy(self, mock_path_join, mock_open, mock_send_message):
        # Create a mock text channel
        channel = MagicMock(spec=discord.TextChannel)

        # Call the send_privacy_policy function
        await send_privacy_policy(channel)

        # Assert that the privacy policy file was read
        mock_open.assert_called_once_with("privacy_policy.txt", "r")

        # Assert that the send_message function was called with the correct arguments
        mock_send_message.assert_called_once_with(channel, "This is the privacy policy.")

    @patch("src.parakeet.messaging.logger.error")
    @patch("builtins.open", side_effect=Exception("File read error"))
    @patch("os.path.join", return_value="privacy_policy.txt")
    async def test_send_privacy_policy_file_read_error(self, mock_path_join, mock_open, mock_logger_error):
        # Create a mock text channel
        channel = MagicMock(spec=discord.TextChannel)

        # Call the send_privacy_policy function
        await send_privacy_policy(channel)

        # Assert that the logger.error method was called due to the file read error
        mock_logger_error.assert_called_once_with("Error sending privacy policy: File read error", exc_info=True)

    @patch("src.parakeet.messaging.send_message", new_callable=AsyncMock)
    async def test_send_help_message_success(self, mock_send_message):
        # Create a mock text channel
        channel = MagicMock(spec=discord.TextChannel)

        # Call the send_help_message function
        await send_help_message(channel)

        # Assert that the send_message function was called with the correct arguments
        expected_help_message = (
            "Here are the commands you can use:\n"
            "1. `gpt:help` - Show this help message\n"
            "2. `gpt:privacy` - Show the privacy policy\n"
            "5. `gpt:<your message>` - Send a message to the AI bot\n"
        )
        mock_send_message.assert_called_once_with(channel, expected_help_message)

    @patch("src.parakeet.messaging.logger.error")
    @patch("src.parakeet.messaging.send_message", new_callable=AsyncMock, side_effect=Exception("Send message error"))
    async def test_send_help_message_error(self, mock_send_message, mock_logger_error):
        # Create a mock text channel
        channel = MagicMock(spec=discord.TextChannel)

        # Call the send_help_message function
        await send_help_message(channel)

        # Assert that the logger.error method was called due to the send message error
        mock_logger_error.assert_called_once_with("Error sending help message: Send message error", exc_info=True)

class BotRespondTestCase(unittest.IsolatedAsyncioTestCase):
    @patch("src.parakeet.messaging.generate_response", new_callable=AsyncMock)
    @patch("src.parakeet.messaging.send_message", new_callable=AsyncMock)
    async def test_bot_respond_success(self, mock_send_message, mock_generate_response):
        # Create a mock message
        message = MagicMock(spec=discord.Message)
        message.channel = MagicMock(spec=discord.TextChannel)

        # Define the mock response
        mock_response = "This is a test response."
        mock_generate_response.return_value = mock_response

        # Call the bot_respond function
        await bot_respond(message)

        # Assert that generate_response was called with the correct arguments
        mock_generate_response.assert_called_once_with(message)

        # Assert that send_message was called with the correct arguments
        mock_send_message.assert_called_once_with(message.channel, mock_response)

    @patch("src.parakeet.messaging.logger.error")
    @patch("src.parakeet.messaging.generate_response", new_callable=AsyncMock, side_effect=Exception("Generate response error"))
    async def test_bot_respond_generate_response_error(self, mock_generate_response, mock_logger_error):
        # Create a mock message
        message = MagicMock(spec=discord.Message)
        message.channel = MagicMock(spec=discord.TextChannel)

        # Call the bot_respond function
        await bot_respond(message)

        # Assert that generate_response was called with the correct arguments
        mock_generate_response.assert_called_once_with(message)

        # Assert that the logger.error method was called due to the generate response error
        mock_logger_error.assert_called_once_with("Error generating response message: Generate response error", exc_info=True)

class BotReplyTestCase(unittest.IsolatedAsyncioTestCase):
    @patch("src.parakeet.messaging.generate_response", new_callable=AsyncMock)
    @patch("src.parakeet.messaging.send_message", new_callable=AsyncMock)
    async def test_bot_reply_success(self, mock_send_message, mock_generate_response):
        # Create a mock original message
        original_message = MagicMock(spec=discord.Message)
        original_message.content = "Original message content"

        # Create a mock message with a reference to the original message
        message = MagicMock(spec=discord.Message)
        message.reference = MagicMock()
        message.reference.resolved = original_message
        message.channel = MagicMock(spec=discord.TextChannel)

        # Define the mock response
        mock_response = "This is a test response."
        mock_generate_response.return_value = mock_response

        # Call the bot_reply function
        await bot_reply(message)

        # Assert that generate_response was called with the correct arguments
        mock_generate_response.assert_called_once_with(original_message)

        # Assert that send_message was called with the correct arguments
        mock_send_message.assert_called_once_with(message.channel, mock_response)

    @patch("src.parakeet.messaging.logger.error")
    @patch("src.parakeet.messaging.generate_response", new_callable=AsyncMock, side_effect=Exception("Generate response error"))
    async def test_bot_reply_generate_response_error(self, mock_generate_response, mock_logger_error):
        # Create a mock original message
        original_message = MagicMock(spec=discord.Message)
        original_message.content = "Original message content"

        # Create a mock message with a reference to the original message
        message = MagicMock(spec=discord.Message)
        message.reference = MagicMock()
        message.reference.resolved = original_message
        message.channel = MagicMock(spec=discord.TextChannel)

        # Call the bot_reply function
        await bot_reply(message)

        # Assert that generate_response was called with the correct arguments
        mock_generate_response.assert_called_once_with(original_message)

        # Assert that the logger.error method was called due to the generate response error
        mock_logger_error.assert_called_once_with("Error generating response reply: Generate response error", exc_info=True)

if __name__ == "__main__":
    unittest.main()