import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
import asyncio
import discord

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.messaging import (
    ConversationHistory,
    handle_expiration,
    send_message,
    send_reply,
    send_privacy_policy,
    send_help_message,
    add_feedback_reactions,
    bot_message,
    bot_reply
)
from parakeet.models import BotQuery, GPTModel

class TestConversationHistory(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """
        Set up the test case by initializing the ConversationHistory object and its dependencies.
        """
        self.root_message_id = 1
        self.default_timeout_seconds = 10  # Default timeout

        # Create a comprehensive mock of the bot
        self.bot = MagicMock()
        self.bot.send_message = AsyncMock()
        self.bot.send_reply = AsyncMock()
        self.bot.create_role = AsyncMock()
        self.bot.system_channel = MagicMock()
        self.bot.system_channel.send = AsyncMock()

        self.on_expire = MagicMock()
        self.conversation_history = ConversationHistory(
            self.root_message_id, self.default_timeout_seconds, self.bot, self.on_expire
        )

    async def asyncTearDown(self):
        """
        Tear down the test case by stopping the tracking of conversation history and allowing the event loop to process the stop event.
        """
        self.conversation_history.stop_tracking()
        await asyncio.sleep(0)

    def test_initialization(self):
        """
        Test the initialization of the ConversationHistory object.
        """
        self.assertEqual(self.conversation_history.root_message_id, self.root_message_id)
        self.assertEqual(self.conversation_history.message_id, self.root_message_id)
        self.assertEqual(self.conversation_history.history, [])
        self.assertAlmostEqual(self.conversation_history.last_activity, datetime.now(timezone.utc), delta=timedelta(seconds=1))
        self.assertEqual(self.conversation_history.timeout, timedelta(seconds=self.default_timeout_seconds))
        self.assertIsInstance(self.conversation_history._stop_event, asyncio.Event)
        self.assertEqual(self.conversation_history.bot, self.bot)
        self.assertEqual(self.conversation_history.on_expire, self.on_expire)

    async def test_add_message(self):
        """
        Test the add_message method of the ConversationHistory object.
        """
        role = "user"
        content = "Hello"
        message_id = 2
        self.conversation_history.add_message(role, content, message_id)
        self.assertEqual(len(self.conversation_history.history), 1)
        self.assertEqual(self.conversation_history.history[0], {"role": role, "content": content})
        self.assertEqual(self.conversation_history.message_id, message_id)
        self.assertAlmostEqual(self.conversation_history.last_activity, datetime.now(timezone.utc), delta=timedelta(seconds=1))

    async def test_get_history(self):
        """
        Test the get_history method of the ConversationHistory object.
        """
        role = "user"
        content = "Hello"
        message_id = 2
        self.conversation_history.add_message(role, content, message_id)
        history = self.conversation_history.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0], {"role": role, "content": content})

    async def test_clear_history(self):
        """
        Test the clear_history method of the ConversationHistory object.
        """
        role = "user"
        content = "Hello"
        message_id = 2
        self.conversation_history.add_message(role, content, message_id)
        self.conversation_history.clear_history(message_id)
        self.assertEqual(self.conversation_history.history, [])
        self.assertEqual(self.conversation_history.root_message_id, message_id)
        self.assertEqual(self.conversation_history.message_id, message_id)
        self.assertAlmostEqual(self.conversation_history.last_activity, datetime.now(timezone.utc), delta=timedelta(seconds=1))

    async def test_is_expired(self):
        """
        Test the is_expired method of the ConversationHistory object.
        """
        # Set a shorter timeout for this test
        self.conversation_history.timeout = timedelta(seconds=1)
        self.conversation_history.last_activity = datetime.now(timezone.utc) - timedelta(seconds=2)
        self.assertTrue(self.conversation_history.is_expired())
        self.conversation_history.last_activity = datetime.now(timezone.utc)
        self.assertFalse(self.conversation_history.is_expired())

    async def test_to_dict(self):
        """
        Test the to_dict method of the ConversationHistory object.
        """
        role = "user"
        content = "Hello"
        message_id = 2
        self.conversation_history.add_message(role, content, message_id)
        data = self.conversation_history.to_dict()
        self.assertEqual(data["root_message_id"], self.root_message_id)
        self.assertEqual(data["history"], [{"role": role, "content": content}])

    async def test_from_dict(self):
        """
        Test the from_dict method of the ConversationHistory object.
        """
        data = {
            "root_message_id": 1,
            "history": [{"role": "user", "content": "Hello"}]
        }
        instance = ConversationHistory.from_dict(data)
        self.assertEqual(instance.root_message_id, data["root_message_id"])
        self.assertEqual(instance.history, data["history"])

    @patch('asyncio.create_task')
    async def test_start_tracking(self, mock_create_task):
        """
        Test the start_tracking method of the ConversationHistory object.
        """
        self.conversation_history.start_tracking()
        mock_create_task.assert_called_once()
        args, kwargs = mock_create_task.call_args
        self.assertTrue(asyncio.iscoroutine(args[0]))
        # Await the coroutine to avoid the RuntimeWarning
        await args[0]

    async def test_stop_tracking(self):
        """
        Test the stop_tracking method of the ConversationHistory object.
        """
        self.conversation_history.stop_tracking()
        self.assertTrue(self.conversation_history._stop_event.is_set())
    
    @patch('parakeet.messaging.handle_expiration')
    async def test_track_expiration(self, mock_handle_expiration):
        """
        Test the track_expiration method of the ConversationHistory object.
        """
        self.conversation_history.timeout = timedelta(seconds=1)
        self.conversation_history.last_activity = datetime.now(timezone.utc) - timedelta(seconds=2)
        
        # Start tracking expiration in the background
        self.conversation_history.start_tracking()
        
        # Wait for a short period to allow the expiration to be handled
        await asyncio.sleep(1.5)
        
        mock_handle_expiration.assert_called_once_with(self.root_message_id)

    @patch('parakeet.messaging.conversation_histories', new_callable=list)
    def test_handle_expiration(self, mock_conversation_histories):
        """
        Test the handle_expiration function.
        """
        # Add the conversation history to the mock
        mock_conversation_histories.append(self.conversation_history)
        
        # Ensure the conversation history is added
        self.assertEqual(len(mock_conversation_histories), 1)
        
        # Define the conversation_histories variable
        conversation_histories = []
        
        # Debug logging before calling handle_expiration
        print(f"Before expiration (mock): {len(mock_conversation_histories)} histories")
        print(f"Before expiration (global): {len(conversation_histories)} histories")
        
        # Call the handle_expiration function
        handle_expiration(self.root_message_id)
        
        # Debug logging after calling handle_expiration
        print(f"After expiration (mock): {len(mock_conversation_histories)} histories")
        print(f"After expiration (global): {len(conversation_histories)} histories")
        
        # Check that the conversation history is removed for the mock
        self.assertEqual(len(mock_conversation_histories), 0)

    @patch('parakeet.messaging.add_feedback_reactions')
    async def test_send_message(self, mock_add_feedback_reactions):
        """
        Test the send_message function.
        """
        channel = MagicMock()
        channel.send = AsyncMock()
        content = "Hello, world!"
        await send_message(channel, content)
        channel.send.assert_called()
        mock_add_feedback_reactions.assert_called()

    @patch('parakeet.messaging.add_feedback_reactions')
    async def test_send_reply(self, mock_add_feedback_reactions):
        """
        Test the send_reply function.
        """
        message = MagicMock(spec=discord.Message)
        message.reply = AsyncMock()
        reply_content = "Hello, reply!"
        await send_reply(message, reply_content)
        message.reply.assert_called()
        mock_add_feedback_reactions.assert_called()

    @patch('parakeet.messaging.send_message')
    async def test_send_privacy_policy(self, mock_send_message):
        """
        Test the send_privacy_policy function.
        """
        channel = MagicMock(spec=discord.TextChannel)
        await send_privacy_policy(channel)
        mock_send_message.assert_called()

    @patch('parakeet.messaging.send_message')
    async def test_send_help_message(self, mock_send_message):
        """
        Test the send_help_message function.
        """
        channel = MagicMock(spec=discord.TextChannel)
        await send_help_message(channel)
        mock_send_message.assert_called()

    async def test_add_feedback_reactions(self):
        """
        Test the add_feedback_reactions function.
        """
        response = MagicMock()
        response.add_reaction = AsyncMock()
        await add_feedback_reactions(response)
        response.add_reaction.assert_any_call("👍")
        response.add_reaction.assert_any_call("👎")

    @patch('parakeet.messaging.generate_response', new_callable=AsyncMock)
    async def test_bot_message(self, mock_generate_response):
        """
        Test the bot_message function.
        """
        message = MagicMock(spec=discord.Message)
        channel = MagicMock()
        message.channel = channel
        query = BotQuery(message, GPTModel.GPT_4)
        mock_generate_response.return_value = "Hello, bot!"
        await bot_message(query)
        channel.send.assert_called_with("Hello, bot!")

    @patch('parakeet.messaging.generate_response', new_callable=AsyncMock)
    async def test_bot_reply(self, mock_generate_response):
        """
        Test the bot_reply function.
        """
        message = MagicMock(spec=discord.Message)
        reference = MagicMock()
        reference.resolved = MagicMock(spec=discord.Message)
        message.reference = reference
        query = BotQuery(message, GPTModel.GPT_4)
        mock_generate_response.return_value = "Hello, reply!"
        await bot_reply(query)
        reference.resolved.reply.assert_called_with("Hello, reply!")

if __name__ == '__main__':
    unittest.main()