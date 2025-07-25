import unittest
from src.okx_client import OKXClient

class TestOKXClientSwapQuotePlaceholder(unittest.TestCase):

    def test_get_swap_quote_is_placeholder(self):
        """Test that get_swap_quote returns the 'Not implemented' error."""
        client = OKXClient()
        result = client.get_swap_quote(
            from_token='any', 
            to_token='any', 
            amount='any'
        )
        self.assertEqual(result, {"error": "Not implemented"})

if __name__ == '__main__':
    unittest.main()
