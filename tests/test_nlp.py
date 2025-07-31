import unittest
from unittest.mock import patch, MagicMock
import os

from src.nlp import NLPClient

class TestNLPClient(unittest.TestCase):

    def setUp(self):
        """Set up environment variables for testing."""
        os.environ["GEMINI_API_KEY"] = "test_key"

    @patch('src.nlp.genai.GenerativeModel')
    def test_parse_intent_flash_model(self, MockGenerativeModel):
        """Test that the correct model is called and intent is parsed (Flash)."""
        # Arrange
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = '{"intent": "get_price"}'
        MockGenerativeModel.return_value = mock_model_instance
        
        client = NLPClient()
        
        # Act
        result = client.parse_intent("price of btc", model_type='flash')
        
        # Assert
        MockGenerativeModel.assert_called_once_with('gemini-2.5-flash')
        self.assertEqual(result, {"intent": "get_price"})

    @patch('src.nlp.genai.GenerativeModel')
    def test_parse_intent_pro_model(self, MockGenerativeModel):
        """Test that the correct model is called and intent is parsed (Pro)."""
        # Arrange
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = '{"intent": "buy_token"}'
        MockGenerativeModel.return_value = mock_model_instance
        
        client = NLPClient()
        
        # Act
        result = client.parse_intent("buy 1 eth with usdc", model_type='pro')
        
        # Assert
        MockGenerativeModel.assert_called_once_with('gemini-2.5-pro')
        self.assertEqual(result, {"intent": "buy_token"})

    @patch('src.nlp.genai.GenerativeModel')
    def test_lazy_loading(self, MockGenerativeModel):
        """Test that models are only initialized when first used."""
        client = NLPClient()
        
        # At this point, no models should be initialized
        MockGenerativeModel.assert_not_called()
        
        # Access the flash model
        _ = client.flash_model
        MockGenerativeModel.assert_called_once_with('gemini-2.5-flash')
        
        # Access the pro model
        _ = client.pro_model
        MockGenerativeModel.assert_called_with('gemini-2.5-pro')
        self.assertEqual(MockGenerativeModel.call_count, 2)

    def test_parse_intent_add_wallet(self):
        """Test parsing of the 'add_wallet' intent."""
        with patch('src.nlp.genai.GenerativeModel') as MockGenerativeModel:
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value.text = '{"intent": "add_wallet", "entities": {}}'
            MockGenerativeModel.return_value = mock_model_instance
            
            client = NLPClient()
            parsed_intent = client.parse_intent("I want to add a wallet")
            
            self.assertEqual(parsed_intent['intent'], 'add_wallet')

    def test_parse_intent_show_portfolio(self):
        """Test parsing of the 'show_portfolio' intent."""
        with patch('src.nlp.genai.GenerativeModel') as MockGenerativeModel:
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value.text = '{"intent": "show_portfolio", "entities": {}}'
            MockGenerativeModel.return_value = mock_model_instance
            
            client = NLPClient()
            parsed_intent = client.parse_intent("show me my portfolio")
            
            self.assertEqual(parsed_intent['intent'], 'show_portfolio')

    def test_parse_intent_get_insights(self):
        """Test parsing of the 'get_insights' intent."""
        with patch('src.nlp.genai.GenerativeModel') as MockGenerativeModel:
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value.text = '{"intent": "get_insights", "entities": {}}'
            MockGenerativeModel.return_value = mock_model_instance
            
            client = NLPClient()
            parsed_intent = client.parse_intent("give me market insights")
            
            self.assertEqual(parsed_intent['intent'], 'get_insights')

if __name__ == '__main__':
    unittest.main()
