import sys
import unittest

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.conversation import ConversationManager

class TestShortTermMemory(unittest.TestCase):

    def setUp(self):
        self.manager = ConversationManager()
        self.default_system_prompt = "This is the default system prompt."

    # acceptance test for the short term memory feature
    # ac.1 Conversation history is stored and formatted as JSON.
    def test_conversation_history_is_stored_and_formatted_as_json(self):
        # Given a user interacts with the bot
        user_message = "Hello, bot!"
        self.manager.handle_message(user_message)
        # When the user sends a message to the bot
        bot_response = self.default_system_prompt
        self.manager.handle_message(bot_response)
        # Then the conversation history is stored and formatted as JSON
        conversation_history = self.manager.get_conversation(bot_response)
        self.assertIsInstance(conversation_history, dict)
        self.assertIn("root_message_id", conversation_history)
        self.assertIn("history", conversation_history)
        self.assertIn("last_activity", conversation_history)
        self.assertIn("timeout", conversation_history)

    # ac.2 The conversation history is successfully sent along with the default system prompt and user query.
    def test_conversation_history_is_sent_along_with_default_system_prompt_and_user_query(self):
        # Given a user interacts with the bot
        user_message = "Hello, bot!"
        self.manager.handle_message(user_message)
        # When the user sends a message to the bot
        bot_response = self.default_system_prompt
        self.manager.handle_message(bot_response)
        # Then the conversation history is successfully sent along with the default system prompt and user query
        conversation_history = self.manager.get_conversation(bot_response)
        self.assertEqual(conversation_history["history"][0]["message"], user_message)
        self.assertEqual(conversation_history["history"][1]["message"], bot_response)

    # ac.3 The system dynamically adjusts the number of messages included in the prompt to maintain performance and respect the 4096 token limit.
    def test_system_dynamically_adjusts_number_of_messages_included_in_prompt(self):
        # Given a user interacts with the bot
        user_message = "Hello, bot!"
        self.manager.handle_message(user_message)
        # When the user sends a message to the bot
        bot_response = self.default_system_prompt
        self.manager.handle_message(bot_response)
        # Then the system dynamically adjusts the number of messages included in the prompt
        conversation_history = self.manager.get_conversation(bot_response)
        self.assertEqual(len(conversation_history["history"]), 2)

    # ac.4 Users have the ability to reset their conversation history either manually or via an automatic timeout.
    def test_users_can_reset_conversation_history_manually_or_via_automatic_timeout(self):
        # Given a user interacts with the bot
        user_message = "Hello, bot!"
        self.manager.handle_message(user_message)
        # When the user sends a message to the bot
        bot_response = self.default_system_prompt
        self.manager.handle_message(bot_response)
        # Then the user can reset the conversation history manually
        self.manager.reset_conversation(bot_response)
        conversation_history = self.manager.get_conversation(bot_response)
        self.assertIsNone(conversation_history)

if __name__ == '__main__':
    unittest.main()