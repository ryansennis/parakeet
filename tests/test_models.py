import sys
import unittest
import discord
from unittest.mock import MagicMock

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.models import BotQuery, GPTModel

class TestBotQuery(unittest.TestCase):

    def setUp(self):
        self.mock_message = MagicMock(spec=discord.Message)
        self.model = GPTModel.GPT_4

    def test_initialization_valid(self):
        query = BotQuery(self.mock_message, self.model)
        self.assertEqual(query.message, self.mock_message)
        self.assertEqual(query.model, self.model)

    def test_initialization_invalid_message(self):
        with self.assertRaises(TypeError):
            BotQuery("invalid_message", self.model)

    def test_initialization_invalid_model(self):
        with self.assertRaises(TypeError):
            BotQuery(self.mock_message, "invalid_model")

    def test_unpack(self):
        query = BotQuery(self.mock_message, self.model)
        unpacked_message, unpacked_model = query.unpack()
        self.assertEqual(unpacked_message, self.mock_message)
        self.assertEqual(unpacked_model, self.model)

    def test_set_message(self):
        query = BotQuery(self.mock_message, self.model)
        new_mock_message = MagicMock(spec=discord.Message)
        query.set_message(new_mock_message)
        self.assertEqual(query.message, new_mock_message)

if __name__ == '__main__':
    unittest.main()