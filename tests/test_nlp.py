import unittest
from unittest.mock import patch, MagicMock
from src.nlp import NLPClient
import os

class TestNLPClient(unittest.TestCase):

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    @patch('google.generativeai.GenerativeModel')
    def test_parse_intent_get_price(self, mock_gen_model):
        """Test parsing a 'get_price' intent."""
        # Mock the response from the Gemini API
        mock_response = MagicMock()
        mock_response.text = '{"intent": "get_price", "entities": {"symbol": "BTC"}}'
        
        # Configure the mock model instance to return the mock response
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_gen_model.return_value = mock_model_instance

        nlp_client = NLPClient()
        result = nlp_client.parse_intent("what is the price of btc?")

        self.assertEqual(result['intent'], 'get_price')
        self.assertEqual(result['entities']['symbol'], 'BTC')

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    @patch('google.generativeai.GenerativeModel')
    def test_parse_intent_buy_token(self, mock_gen_model):
        """Test parsing a 'buy_token' intent."""
        mock_response = MagicMock()
        mock_response.text = '{"intent": "buy_token", "entities": {"amount": "0.5", "symbol": "ETH", "currency": "USDT"}}'
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_gen_model.return_value = mock_model_instance

        nlp_client = NLPClient()
        result = nlp_client.parse_intent("buy 0.5 ETH with USDT")

        self.assertEqual(result['intent'], 'buy_token')
        self.assertEqual(result['entities']['amount'], '0.5')
        self.assertEqual(result['entities']['symbol'], 'ETH')
        self.assertEqual(result['entities']['currency'], 'USDT')

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"})
    @patch('google.generativeai.GenerativeModel')
    def test_parse_intent_unknown(self, mock_gen_model):
        """Test handling of an unknown intent."""
        mock_response = MagicMock()
        mock_response.text = '{"intent": "unknown", "entities": {}}'
        
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_gen_model.return_value = mock_model_instance

        nlp_client = NLPClient()
        result = nlp_client.parse_intent("some random text")

        self.assertEqual(result['intent'], 'unknown')

    @patch.dict(os.environ, clear=True)
    def test_init_no_api_key(self):
        """Test that NLPClient raises an error if the API key is missing."""
        with self.assertRaises(ValueError):
            NLPClient()

if __name__ == '__main__':
    unittest.main()
