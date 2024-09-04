import asyncio
import unittest
import openai
from unittest.mock import MagicMock
from src.parakeet.shared import generate_response

class SharedTestCase(unittest.TestCase):
    def test_generate_response(self):
        # Create a mock query message object
        query = MagicMock()
        query.author.name = "John"
        query.content = "Hello, Parakeet!"

        # Mock the openai.ChatCompletion.create method
        openai.ChatCompletion.create = MagicMock()
        openai.ChatCompletion.create.return_value.choices[0].message['content'].strip.return_value = "Hi, John! How can I assist you?"

        # Call the generate_response function and run the coroutine
        response = asyncio.run(generate_response(query))

        # Assert the response message
        self.assertEqual(response, "Hi, John! How can I assist you?")

if __name__ == "__main__":
    unittest.main()