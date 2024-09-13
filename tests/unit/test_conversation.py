import sys
from datetime import datetime, timedelta, timezone
import unittest
from unittest import TestCase
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from unittest.mock import MagicMock, patch
import discord
import logging

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.conversation import ConversationHistory, ConversationManager

class TestConversationHistory(TestCase):

    def setUp(self):
        self.mock_user = MagicMock(spec=discord.User)
        self.mock_user.bot = False

        self.root_message: discord.Message = MagicMock(spec=discord.Message)
        self.root_message.id = 12345
        self.timeout_seconds: int = 600
        self.root_message.author = self.mock_user
        self.root_message.content = "Hello, world!"

        self.conversation_history: ConversationHistory = ConversationHistory(self.root_message, self.timeout_seconds)

    def test_initialization(self):
        self.assertEqual(self.conversation_history.root_message, self.root_message)
        self.assertEqual(self.conversation_history.last_message, self.root_message)
        self.assertEqual(len(self.conversation_history.history), 1)
        self.assertEqual(self.conversation_history.history[0], {"role": "user", "content": self.root_message.content})
        self.assertAlmostEqual(self.conversation_history.last_activity, datetime.now(timezone.utc), delta=timedelta(seconds=1))
        self.assertEqual(self.conversation_history.timeout, timedelta(seconds=self.timeout_seconds))

    @patch('parakeet.conversation.logger')
    def test_add_message(self, mock_logger):
        mock_user = MagicMock(spec=discord.User)
        mock_user.bot = True

        mock_message = MagicMock(spec=discord.Message)
        mock_message.content = "Hello, world!"
        mock_message.id = 67890
        mock_message.author = mock_user

        self.conversation_history.add_message(mock_message)

        self.assertEqual(len(self.conversation_history.history), 2)
        self.assertEqual(self.conversation_history.history[1], {"role": "assistant", "content": "Hello, world!"})
        self.assertEqual(self.conversation_history.last_message, mock_message)
        self.assertAlmostEqual(self.conversation_history.last_activity, datetime.now(timezone.utc), delta=timedelta(seconds=1))
        mock_logger.info.assert_called_with(f"Added message to conversation history for root_message: {self.root_message.id}")

    @patch('parakeet.conversation.logger')
    def test_is_expired(self, mock_logger):
        self.conversation_history.last_activity = datetime.now(timezone.utc) - timedelta(seconds=self.timeout_seconds + 1)
        self.assertTrue(self.conversation_history.is_expired())
        mock_logger.info.assert_called_with(f"Conversation history for root_message.id: {self.root_message.id} has expired")

        self.conversation_history.last_activity = datetime.now(timezone.utc)
        self.assertFalse(self.conversation_history.is_expired())

    @patch('parakeet.conversation.logger')
    def test_reset(self, mock_logger):
        mock_message = MagicMock(spec=discord.Message)
        mock_message.id = 54321
        self.conversation_history.reset(mock_message)
        self.assertEqual(self.conversation_history.history, [])
        self.assertEqual(self.conversation_history.last_activity, datetime.now(timezone.utc))
        self.assertEqual(self.conversation_history.root_message, mock_message)
        mock_logger.info.assert_called_with(f"Reset conversation history for root_message.id: {self.conversation_history.root_message.id}")

class TestConversationManager(TestCase):

    def setUp(self):
        self.manager = ConversationManager()

        self.user = MagicMock(spec=discord.User)
        self.user.id = 2
        self.user.bot = False

        self.mock_message = MagicMock(spec=discord.Message)
        self.mock_message.id = 12345
        self.mock_message.reference = None
        self.mock_message.author = self.user

        self.bot_user = MagicMock(spec=discord.User)
        self.bot_user.id = 1
        self.bot_user.bot = True

        self.bot_message = MagicMock(spec=discord.Message)
        self.bot_message.id = 67890
        self.bot_message.reference.resolve = self.mock_message
        self.bot_message.reference.message_id = self.mock_message.id

    def test_initialization(self):
        self.assertEqual(self.manager.conversation_histories, [])
        self.assertIsInstance(self.manager.scheduler, AsyncIOScheduler)

    @patch('parakeet.conversation.logger')
    def test_create_conversation(self, mock_logger):
        self.manager.create_conversation(self.mock_message, 600)
        self.assertEqual(len(self.manager.conversation_histories), 1)
        self.assertEqual(self.manager.conversation_histories[0].root_message.id, 12345)
        mock_logger.info.assert_called_with('Created conversation with root_message.id: 12345')

    @patch('parakeet.conversation.logger')
    def test_get_conversation(self, mock_logger):
        # Create a conversation with the mock message
        self.manager.create_conversation(self.mock_message, 600)
        
        # Retrieve the conversation
        conversation = self.manager.get_conversation(self.mock_message)
        
        # Assertions
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.last_message.id, 12345)
        mock_logger.info.assert_called_with("Found conversation with last_message.id: 12345")

    @patch('parakeet.conversation.logger')
    def test_handle_message_create_new(self, mock_logger):
        self.manager.handle_message(self.mock_message, self.bot_user)
        self.assertEqual(len(self.manager.conversation_histories), 1, "Conversation history should have one entry")
        self.assertEqual(self.manager.conversation_histories[0].root_message.id, 12345, "Root message ID should be 12345")
        mock_logger.info.assert_called_with("Created new conversation history for message 12345")

    @patch('parakeet.conversation.logger')
    def test_handle_message_add_to_existing(self, mock_logger):
        self.manager.create_conversation(self.mock_message, 600)
        
        # Verify conversation creation
        self.assertEqual(len(self.manager.conversation_histories), 1, "Conversation should be created")
        self.bot_message.content = "Bot reply"  # Ensure content is set
    
        self.manager.handle_message(self.bot_message, self.bot_user)
        
        # Verify message handling
        conversation = self.manager.get_conversation(self.mock_message)
        self.assertIsNotNone(conversation, "Conversation should not be None")
        self.assertEqual(len(conversation.history), 2, "Conversation history should have 2 messages")
        self.assertEqual(conversation.history[1]['content'], self.bot_message.content)
        mock_logger.info.assert_any_call(f"Using existing conversation history for message {self.bot_message.id}")
        mock_logger.info.assert_any_call(f"Added message to conversation history for message {self.bot_message.id}")

    @patch('parakeet.conversation.logger')
    def test_add_message_to_conversation(self, mock_logger):
        self.manager.create_conversation(self.mock_message, 600)
    
        mock_new_message = MagicMock(spec=discord.Message)
        mock_new_message.content = "Goodbye, world!"
        mock_new_message.id = 54321
    
        self.manager.add_message_to_conversation(self.mock_message, mock_new_message)
        conversation = self.manager.get_conversation(self.mock_message)
        self.assertEqual(len(conversation.history), 2)
        self.assertEqual(conversation.history[0].get('content'), "Hello, world!")
        self.assertEqual(conversation.history[1].get('content'), "Goodbye, world!")
        mock_logger.info.assert_called_with('Found conversation with last_message.id: 67890')

    @patch('parakeet.conversation.logger')
    def test_delete_conversation(self, mock_logger):
        mock_message = MagicMock(spec=discord.Message)
        mock_message.id = 12345


        self.manager.create_conversation(mock_message, 600)
        self.manager.delete_conversation(mock_message)
        self.assertIsNone(self.manager.get_conversation(mock_message))
        mock_logger.info.assert_called_with("Deleted conversation history for message.id: 12345")

    @patch('parakeet.conversation.logger')
    def test_expire_conversation(self, mock_logger):
        mock_message = MagicMock(spec=discord.Message)
        mock_message.id = 12345
        self.manager.create_conversation(mock_message, 1)  

        conversation = self.manager.get_conversation(mock_message)
        conversation.last_activity = datetime.now(timezone.utc) - timedelta(seconds=2)
        self.manager._expire_conversation(conversation)
        self.assertIsNone(self.manager.get_conversation(mock_message))
        mock_logger.info.assert_called_with("Expired conversation history for message.id: 12345")

    @patch('parakeet.conversation.logger')
    def test_handle_message_from_bot(self, mock_logger):
        mock_message = MagicMock()
        mock_message.id = 12345
        mock_message.reference = None
        mock_message.author.bot = True
        mock_message.author.id = 1

        bot_user = MagicMock()
        bot_user.id = 1

        self.manager.handle_message(mock_message, bot_user)
        self.assertEqual(len(self.manager.conversation_histories), 0, "No conversation history should be created for bot messages")
        mock_logger.info.assert_called_with("The message is a root message from the bot, message will not be added to conversation history")

    @patch('parakeet.conversation.logger')
    def test_handle_message_no_reference(self, mock_logger):
        self.manager.create_conversation(12345, 600)
        mock_message = MagicMock()
        mock_message.id = 67890
        mock_message.reference = None
        mock_message.author.bot = False
        mock_message.author.id = 2

        bot_user = MagicMock()
        bot_user.id = 1

        self.manager.handle_message(mock_message, bot_user)
        self.assertEqual(len(self.manager.conversation_histories), 2, "A new conversation history should be created")
        self.assertEqual(self.manager.conversation_histories[1].root_message_id, 67890, "Root message ID should be 67890")
        mock_logger.info.assert_called_with("Created new conversation history for message 67890")

    @patch('parakeet.conversation.logger')
    def test_handle_message_existing(self, mock_logger):
        mock_root_message = MagicMock(spec=discord.Message)
        mock_root_message.id = 12345
        mock_root_message.reference = None
        mock_root_message.author.id = 2
        mock_root_message.author.bot = False

        self.manager.create_conversation(mock_root_message, 600)

        mock_message = MagicMock(spec=discord.Message)
        mock_message.id = 67890
        mock_message.reference = mock_root_message
        mock_message.author.id = 1
        mock_message.author.bot = True

        bot_user = MagicMock(spec=discord.User)
        bot_user.id = 1

        self.manager.handle_message(mock_message, bot_user)
        conversation = self.manager.get_conversation(mock_message)
        assert conversation is not None
        self.assertEqual(len(conversation.history), 1)
        self.assertEqual(conversation.history[0]['content'], mock_message.content)
        mock_logger.info.assert_any_call("Found conversation history for root_message_id: 12345")
        mock_logger.info.assert_any_call("Added message to conversation history for message 67890")

    @patch('parakeet.conversation.logger')
    def test_handle_message_bot_reply_to_user(self, mock_logger):
        # mock discord guild
        guild = MagicMock()
        guild.roles = []
        guild.system_channel = MagicMock()
        guild.system_channel.send = MagicMock()
        guild.roles = []
        guild.id = 1
        guild.name = "Test Guild"

        # mock message
        mock_message = MagicMock()
        mock_message.id = 12345
        mock_message.reference = MagicMock()
        mock_message.reference.message_id = 67890
        mock_message.channel = MagicMock()
        mock_message.channel.fetch_message = MagicMock()
        mock_message.channel.fetch_message.return_value = mock_message
        mock_message.author.id = 1
        mock_message.author.bot = True

        bot_user = MagicMock()
        bot_user.id = 1
        
        self.manager.handle_message(mock_message, bot_user)
        mock_logger.info.assert_called_with("Message is a reply to the bot's message")
      
if __name__ == '__main__':
    unittest.main()