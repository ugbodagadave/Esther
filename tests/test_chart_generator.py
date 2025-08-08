import unittest
from unittest.mock import patch
from src.chart_generator import generate_price_chart

class TestChartGenerator(unittest.TestCase):

    def test_generate_price_chart(self):
        """
        Tests that the price chart is generated correctly.
        """
        historical_data = [
            {"price": "100", "ts": "1672531200000"},
            {"price": "110", "ts": "1672617600000"},
            {"price": "105", "ts": "1672704000000"}
        ]
        token_symbol = "BTC"
        period = "3d"

        with patch('matplotlib.pyplot.show'):
            chart_image = generate_price_chart(historical_data, token_symbol, period)

        self.assertIsInstance(chart_image, bytes)
        self.assertTrue(len(chart_image) > 0)

if __name__ == '__main__':
    unittest.main()
