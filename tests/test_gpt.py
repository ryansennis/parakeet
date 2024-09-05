import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.gpt import process_gpt_message
from parakeet.models import BotQuery
from parakeet.messaging import ConversationHistory

class TestProcessGptMessage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.query = MagicMock(spec=BotQuery)
        self.query.message = MagicMock()
        self.message_func = AsyncMock()
        self.history = MagicMock(spec=ConversationHistory)
        self.system_prompt = "System prompt"

    @patch('parakeet.gpt.generate_system_prompt', return_value="System prompt")
    async def test_process_gpt_message_success(self, mock_generate_system_prompt):
        # Setup
        self.query.message.content = "Hello"
        self.query.message.id = 1
        self.history.get_history.return_value = [{"role": "user", "content": "Previous message"}]

        # Call the function
        await process_gpt_message(self.query, self.message_func, self.history)

        # Assertions
        self.history.add_message.assert_called_once_with("user", self.query.message, self.query.message.id)
        self.history.get_history.assert_called_once()
        self.query.set_message.assert_called_once_with([
            "System prompt",
            {"role": "user", "content": "Previous message"},
            {"role": "user", "content": self.query.message.content}
        ])
        self.message_func.assert_awaited_once_with(self.query)

    
    @patch('parakeet.logger.logger')
    @patch('parakeet.gpt.generate_system_prompt', return_value="System prompt")
    async def test_process_gpt_message_exception(self, mock_generate_system_prompt, mock_logger):
        # Setup
        self.query.message.content = "Hello"
        self.query.message.id = 1
        self.history.get_history.side_effect = Exception("Test exception")

        # Call the function
        with self.assertLogs('parakeet.logger', level='ERROR') as log:
            await process_gpt_message(self.query, self.message_func, self.history)

        # Assertions
        self.history.add_message.assert_called_once_with("user", self.query.message, self.query.message.id)
        self.history.get_history.assert_called_once()
        self.message_func.assert_not_awaited()
        self.assertIn("Error processing GPT message: Test exception", log.output[0])

if __name__ == '__main__':
    unittest.main()