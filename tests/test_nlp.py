import unittest
from unittest.mock import patch, MagicMock
from src.nlp import NLPClient
import os

class TestNLPClient(unittest.TestCase):

    @patch('google.generativeai.GenerativeModel')
    def test_parse_intent_get_price_flash(self, mock_gen_model):
        """Test parsing a 'get_price' intent using the flash model."""
        # This setup mocks the behavior of genai.GenerativeModel('gemini-2.5-flash')
        mock_flash_instance = MagicMock()
        mock_flash_instance.generate_content.return_value = MagicMock(text='{"intent": "get_price", "entities": {"symbol": "BTC"}}')
        
        # When GenerativeModel is called, we return the correct mock based on the model name
        def model_side_effect(model_name):
            if 'flash' in model_name:
                return mock_flash_instance
            return MagicMock() # Return a generic mock for other models like 'pro'
        
        mock_gen_model.side_effect = model_side_effect

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            nlp_client = NLPClient()
            result = nlp_client.parse_intent("what is the price of btc?", model_type='flash')

        self.assertEqual(result['intent'], 'get_price')
        self.assertEqual(result['entities']['symbol'], 'BTC')
        mock_flash_instance.generate_content.assert_called_once()

    @patch('google.generativeai.GenerativeModel')
    def test_parse_intent_buy_token_pro(self, mock_gen_model):
        """Test parsing a 'buy_token' intent using the pro model."""
        mock_pro_instance = MagicMock()
        mock_pro_instance.generate_content.return_value = MagicMock(text='{"intent": "buy_token", "entities": {"amount": "0.5", "symbol": "ETH", "currency": "USDT"}}')

        def model_side_effect(model_name):
            if 'pro' in model_name:
                return mock_pro_instance
            return MagicMock()
        
        mock_gen_model.side_effect = model_side_effect

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            nlp_client = NLPClient()
            result = nlp_client.parse_intent("buy 0.5 ETH with USDT", model_type='pro')

        self.assertEqual(result['intent'], 'buy_token')
        self.assertEqual(result['entities']['amount'], '0.5')
        mock_pro_instance.generate_content.assert_called_once()

    @patch('google.generativeai.GenerativeModel')
    def test_parse_intent_unknown(self, mock_gen_model):
        """Test handling of an unknown intent."""
        mock_flash_instance = MagicMock()
        mock_flash_instance.generate_content.return_value = MagicMock(text='{"intent": "unknown", "entities": {}}')

        def model_side_effect(model_name):
            if 'flash' in model_name:
                return mock_flash_instance
            return MagicMock()
            
        mock_gen_model.side_effect = model_side_effect

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            nlp_client = NLPClient()
            result = nlp_client.parse_intent("some random text")

        self.assertEqual(result['intent'], 'unknown')

    @patch.dict(os.environ, clear=True)
    def test_init_no_api_key(self):
        """Test that NLPClient raises an error if the API key is missing."""
        with self.assertRaises(ValueError):
            NLPClient()

    @patch('google.generativeai.GenerativeModel')
    def test_parse_intent_set_stop_loss(self, mock_gen_model):
        """Test parsing a 'set_stop_loss' intent."""
        mock_pro_instance = MagicMock()
        mock_pro_instance.generate_content.return_value = MagicMock(text='{"intent": "set_stop_loss", "entities": {"symbol": "BTC", "price": "60000"}}')

        def model_side_effect(model_name):
            if 'pro' in model_name:
                return mock_pro_instance
            return MagicMock()
        
        mock_gen_model.side_effect = model_side_effect

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            nlp_client = NLPClient()
            result = nlp_client.parse_intent("set a stop-loss for BTC at 60000", model_type='pro')

        self.assertEqual(result['intent'], 'set_stop_loss')
        self.assertEqual(result['entities']['symbol'], 'BTC')
        self.assertEqual(result['entities']['price'], '60000')
        mock_pro_instance.generate_content.assert_called_once()

    @patch('google.generativeai.GenerativeModel')
    def test_parse_intent_set_take_profit(self, mock_gen_model):
        """Test parsing a 'set_take_profit' intent."""
        mock_pro_instance = MagicMock()
        mock_pro_instance.generate_content.return_value = MagicMock(text='{"intent": "set_take_profit", "entities": {"symbol": "ETH", "price": "3000"}}')

        def model_side_effect(model_name):
            if 'pro' in model_name:
                return mock_pro_instance
            return MagicMock()
        
        mock_gen_model.side_effect = model_side_effect

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            nlp_client = NLPClient()
            result = nlp_client.parse_intent("set a take-profit for ETH at 3000", model_type='pro')

        self.assertEqual(result['intent'], 'set_take_profit')
        self.assertEqual(result['entities']['symbol'], 'ETH')
        self.assertEqual(result['entities']['price'], '3000')
        mock_pro_instance.generate_content.assert_called_once()

if __name__ == '__main__':
    unittest.main()
