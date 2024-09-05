import sys
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta, timezone
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.messaging import ConversationHistory

class TestConversationHistory(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        """
        Set up the test case by initializing the ConversationHistory object and its dependencies.
        """
        self.root_message_id = 1
        self.default_timeout_seconds = 10  # Default timeout

        # Create a comprehensive mock of the bot``
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

if __name__ == '__main__':
    unittest.main()