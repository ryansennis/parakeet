import sys
import unittest
from unittest.mock import AsyncMock, patch, call

# Add the src directory to the Python path
sys.path.insert(0, './src')

from parakeet.messaging import send_message, MAX_DISCORD_MESSAGE_LENGTH

class TestSendMessage(unittest.IsolatedAsyncioTestCase):

    @patch('parakeet.messaging.logger')
    async def test_send_message_channel_none(self, mock_logger):
        await send_message(None, "Test content")
        mock_logger.error.assert_called_once_with("Channel is None, cannot send message.")

if __name__ == '__main__':
    unittest.main()