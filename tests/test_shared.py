import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.shared import generate_system_prompt, generate_response, BotQuery

class TestGenerateSystemPrompt(unittest.TestCase):

    def setUp(self):
        self.query = MagicMock(spec=BotQuery)
        self.message = MagicMock()
        self.model = MagicMock()

    def test_generate_system_prompt_valid(self):
        """
        Test case for the `generate_system_prompt` function.
        This test verifies that the `generate_system_prompt` function correctly generates the system prompt based on the provided message and model.
        The test sets up a mock message object with a content of "Hello, bot!", an author mention of "user", and a guild object. It also sets up a mock model object.
        The expected prompt is a list of dictionaries, where each dictionary represents a role in the conversation (system, assistant, user) and their corresponding content.
        The `generate_system_prompt` function is then called with the query object, and the result is compared to the expected prompt using the `assertEqual` method.
        This test ensures that the `generate_system_prompt` function produces the expected output and handles the provided input correctly.
        """
        self.message.content = "Hello, bot!"
        self.message.author.mention = "user"
        self.message.guild = MagicMock()
        self.message.guild.me.mention = "bot"
        self.query.unpack.return_value = (self.message, self.model)

        expected_prompt = [
            {"role": "system", "content": "You are a general purpose Discord bot, named @bot. Your job is to help the user @user with their queries."},
            {"role": "assistant", "content": "You are to engage in a conversation with the other user's in chat. Keep it informal and be prepared to engage in idle chat."},
            {"role": "user", "content": "Hello, bot!"}
        ]

        result = generate_system_prompt(self.query)
        self.assertEqual(result, expected_prompt)

    def test_generate_system_prompt_invalid_model(self):
        """
        Test case for the `generate_system_prompt` function when an invalid model is provided.
        The function should return None when an invalid model is passed to the `generate_system_prompt` function.
        Steps:
        1. Set up the test environment by creating a mock message object.
        2. Set the content of the message to "Hello, bot!".
        3. Set the mention of the message author to "user".
        4. Create a mock guild object and set the mention of the guild's bot to "bot".
        5. Set the return value of the `unpack` method of the query object to be the mock message and "invalid_model".
        6. Call the `generate_system_prompt` function with the query object.
        7. Assert that the result is None.
        """
        self.message.content = "Hello, bot!"
        self.message.author.mention = "user"
        self.message.guild = MagicMock()
        self.message.guild.me.mention = "bot"
        self.query.unpack.return_value = (self.message, "invalid_model")

        result = generate_system_prompt(self.query)
        self.assertIsNone(result)

    def test_generate_system_prompt_dm_message(self):
        """
        Test case for the `generate_system_prompt` function when a direct message is received.
        This test verifies that the `generate_system_prompt` function correctly generates the system prompt message for a direct message scenario.
        Steps:
        1. Set up the test environment by creating a mock message object and unpacking the query.
        2. Set the content of the message to "Hello, bot!" and the mention of the author to "user".
        3. Set the guild of the message to None.
        4. Define the expected system prompt message as a list of dictionaries, each representing a role and content.
        5. Call the `generate_system_prompt` function with the query.
        6. Assert that the result matches the expected system prompt message.
        """
        self.message.content = "Hello, bot!"
        self.message.author.mention = "user"
        self.message.guild = None
        self.query.unpack.return_value = (self.message, self.model)

        expected_prompt = [
            {"role": "system", "content": "You are a general purpose Discord bot, named @Parakeet. Your job is to help the user @user with their queries."},
            {"role": "assistant", "content": "You are to engage in a conversation with the other user's in chat. Keep it informal and be prepared to engage in idle chat."},
            {"role": "user", "content": "Hello, bot!"}
        ]

        result = generate_system_prompt(self.query)
        self.assertEqual(result, expected_prompt)

    def test_generate_system_prompt_exception(self):
        """
        Test case for the generate_system_prompt function when an exception is raised.
        This test case verifies that the generate_system_prompt function handles exceptions correctly.
        It mocks the unpack method of the query object to raise an Exception with a custom message.
        The function is expected to return None.
        """
        self.query.unpack.side_effect = Exception("Test exception")

        result = generate_system_prompt(self.query)
        self.assertIsNone(result)

class TestGenerateResponse(unittest.TestCase):

    def setUp(self):
        self.query = MagicMock(spec=BotQuery)
        self.message = MagicMock()
        self.model = MagicMock()
        self.query.unpack.return_value = (self.message, self.model)

    @patch('parakeet.shared.openai.ChatCompletion.create', new_callable=AsyncMock)
    async def test_generate_response_valid(self, mock_create):
        """
        Test case for the `generate_response` function.
        This test verifies that the `generate_response` function correctly generates a response based on the provided query.
        """
        self.message.content = "Hello, bot!"
        self.message.channel.typing = AsyncMock()
        mock_create.return_value = AsyncMock(choices=[AsyncMock(message={'content': 'Hello, user!'})])

        result = await generate_response(self.query)
        self.assertEqual(result, "Hello, user!")

    @patch('parakeet.shared.openai.ChatCompletion.create', new_callable=AsyncMock)
    async def test_generate_response_invalid_model(self, mock_create):
        """
        Test case for the `generate_response` function when an invalid model is provided.
        The function should return an error message when an invalid model is passed to the `generate_response` function.
        """
        self.message.content = "Hello, bot!"
        self.message.channel.typing = AsyncMock()
        self.query.unpack.return_value = (self.message, "invalid_model")

        result = await generate_response(self.query)
        self.assertEqual(result, "Sorry, I couldn't generate a response.")

    @patch('parakeet.shared.openai.ChatCompletion.create', new_callable=AsyncMock)
    async def test_generate_response_exception(self, mock_create):
        """
        Test case for the `generate_response` function when an exception is raised.
        This test verifies that the `generate_response` function handles exceptions correctly.
        """
        self.message.content = "Hello, bot!"
        self.message.channel.typing = AsyncMock()
        mock_create.side_effect = Exception("Test exception")

        result = await generate_response(self.query)
        self.assertEqual(result, "Sorry, I couldn't generate a response.")

if __name__ == '__main__':
    unittest.main()