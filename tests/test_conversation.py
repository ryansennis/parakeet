import sys
from datetime import datetime, timedelta, timezone
import unittest
from unittest import TestCase
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.conversation import ConversationHistory, ConversationManager

class TestConversationHistory(TestCase):

    def setUp(self):
        self.root_message_id = 12345
        self.timeout_seconds = 600
        self.conversation_history = ConversationHistory(self.root_message_id, self.timeout_seconds)

    def test_initialization(self):
        self.assertEqual(self.conversation_history.root_message_id, self.root_message_id)
        self.assertEqual(self.conversation_history.last_message_id, self.root_message_id)
        self.assertEqual(self.conversation_history.history, [])
        self.assertAlmostEqual(self.conversation_history.last_activity, datetime.now(timezone.utc), delta=timedelta(seconds=1))
        self.assertEqual(self.conversation_history.timeout, timedelta(seconds=self.timeout_seconds))

    @patch('parakeet.conversation.logger')
    def test_add_message(self, mock_logger):
        mock_message = MagicMock()
        mock_message.content = "Hello, world!"
        mock_message.id = 67890

        self.conversation_history.add_message("user", mock_message)

        self.assertEqual(len(self.conversation_history.history), 1)
        self.assertEqual(self.conversation_history.history[0], {"role": "user", "content": "Hello, world!"})
        self.assertEqual(self.conversation_history.last_message_id, mock_message.id)
        self.assertAlmostEqual(self.conversation_history.last_activity, datetime.now(timezone.utc), delta=timedelta(seconds=1))
        mock_logger.info.assert_called_with(f"Added message to conversation history for root_message_id: {self.root_message_id}")

    @patch('parakeet.conversation.logger')
    def test_is_expired(self, mock_logger):
        self.conversation_history.last_activity = datetime.now(timezone.utc) - timedelta(seconds=self.timeout_seconds + 1)
        self.assertTrue(self.conversation_history.is_expired())
        mock_logger.info.assert_called_with(f"Conversation history for root_message_id: {self.root_message_id} has expired")

        self.conversation_history.last_activity = datetime.now(timezone.utc)
        self.assertFalse(self.conversation_history.is_expired())

class TestConversationManager(TestCase):

    def setUp(self):
        self.manager = ConversationManager()

    def test_initialization(self):
        self.assertEqual(self.manager.conversation_histories, [])
        self.assertIsInstance(self.manager.scheduler, AsyncIOScheduler)

    @patch('parakeet.conversation.logger')
    def test_create_conversation(self, mock_logger):
        self.manager.create_conversation(12345, 600)
        self.assertEqual(len(self.manager.conversation_histories), 1)
        self.assertEqual(self.manager.conversation_histories[0].root_message_id, 12345)
        mock_logger.info.assert_called_with('Initialized ConversationHistory with root_message_id: 12345')

    @patch('parakeet.conversation.logger')
    def test_get_conversation(self, mock_logger):
        self.manager.create_conversation(12345, 600)
        conversation = self.manager.get_conversation(12345)
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.root_message_id, 12345)
        mock_logger.info.assert_called_with("Found conversation history for root_message_id: 12345")

    @patch('parakeet.conversation.logger')
    def test_handle_message_create_new(self, mock_logger):
        mock_message = MagicMock()
        mock_message.id = 12345
        mock_message.reference = None
        mock_message.author.bot = False

        self.manager.handle_message(mock_message, mock_message.author)
        self.assertEqual(len(self.manager.conversation_histories), 1)
        self.assertEqual(self.manager.conversation_histories[0].root_message_id, 12345)
        mock_logger.info.assert_called_with("Created new conversation history for message 12345")

    @patch('parakeet.conversation.logger')
    def test_handle_message_add_to_existing(self, mock_logger):
        self.manager.create_conversation(12345, 600)
        mock_message = MagicMock()
        mock_message.id = 67890
        mock_message.reference.message_id = 12345
        mock_message.author.id = 2
        mock_message.author.bot = False

        bot_user = MagicMock()
        bot_user.id = 1

        self.manager.handle_message(mock_message, bot_user)
        conversation = self.manager.get_conversation(12345)
        self.assertEqual(len(conversation.history), 1)
        self.assertEqual(conversation.history[0]['content'], mock_message.content)
        mock_logger.info.assert_any_call("Found conversation history for root_message_id: 12345")
        mock_logger.info.assert_any_call("Added message to conversation history for message 67890")

    @patch('parakeet.conversation.logger')
    def test_add_message_to_conversation(self, mock_logger):
        self.manager.create_conversation(12345, 600)
        mock_message = MagicMock()
        mock_message.content = "Hello, world!"
        mock_message.id = 67890

        self.manager.add_message_to_conversation(12345, "user", mock_message)
        conversation = self.manager.get_conversation(12345)
        self.assertEqual(len(conversation.history), 1)
        self.assertEqual(conversation.history[0]['content'], "Hello, world!")
        mock_logger.info.assert_called_with('Found conversation history for root_message_id: 12345')

    @patch('parakeet.conversation.logger')
    def test_delete_conversation(self, mock_logger):
        self.manager.create_conversation(12345, 600)
        self.manager.delete_conversation(12345)
        self.assertIsNone(self.manager.get_conversation(12345))
        mock_logger.info.assert_called_with("Deleted conversation history for root_message_id: 12345")

    @patch('parakeet.conversation.logger')
    def test_expire_conversation(self, mock_logger):
        self.manager.create_conversation(12345, 1)
        conversation = self.manager.get_conversation(12345)
        conversation.last_activity = datetime.now(timezone.utc) - timedelta(seconds=2)
        self.manager._expire_conversation(conversation)
        self.assertIsNone(self.manager.get_conversation(12345))
        mock_logger.info.assert_called_with("Expired conversation history for root_message_id: 12345")

if __name__ == '__main__':
    unittest.main()