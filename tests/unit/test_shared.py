import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import discord

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.shared import generate_response, BotQuery
from parakeet.models import GPTModel

class TestGenerateResponse(unittest.TestCase):

    def setUp(self):
        self.query = MagicMock(spec=BotQuery)
        self.message = MagicMock()
        self.model = MagicMock()
        self.query.unpack.return_value = (self.message, self.model)

    @patch('parakeet.messaging.generate_response', new_callable=AsyncMock)
    async def test_generate_response_valid(self, mock_generate_response):
        """
        Test case for the `generate_response` function.
        This test verifies that the `generate_response` function correctly generates a response based on the provided query.
        """
        message = MagicMock(spec=discord.Message)
        query = BotQuery(message, GPTModel.GPT_4)
        mock_generate_response.return_value = "Hello, valid!"
        response = await generate_response(query)
        self.assertEqual(response, "Hello, valid!")

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