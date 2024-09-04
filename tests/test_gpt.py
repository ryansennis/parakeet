import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import discord
from src.parakeet.gpt import process_gpt_message

class TestProcessGptMessage(unittest.IsolatedAsyncioTestCase):
    
    async def test_process_gpt_message_success(self):
        # Arrange
        mock_message = MagicMock(spec=discord.Message)
        mock_message_func = AsyncMock()
        
        # Act
        await process_gpt_message(mock_message, mock_message_func)
        
        # Assert
        mock_message_func.assert_awaited_once_with(mock_message)
    
    @patch('src.parakeet.gpt.logger')
    async def test_process_gpt_message_exception(self, mock_logger):
        # Arrange
        mock_message = MagicMock(spec=discord.Message)
        mock_message_func = AsyncMock(side_effect=Exception("Test Exception"))
        
        # Act
        await process_gpt_message(mock_message, mock_message_func)
        
        # Assert
        mock_message_func.assert_awaited_once_with(mock_message)
        mock_logger.error.assert_called_once()
        self.assertIn("Error processing GPT message: Test Exception", mock_logger.error.call_args[0][0])

if __name__ == '__main__':
    unittest.main()