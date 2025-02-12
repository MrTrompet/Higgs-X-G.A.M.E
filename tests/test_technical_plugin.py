# tests/test_technical_plugin.py
import unittest
import pandas as pd
from plugins.technical_plugin import calculate_indicators

class TestTechnicalPlugin(unittest.TestCase):
    def setUp(self):
        # Create a simple dummy DataFrame with sample data
        self.data = pd.DataFrame({
            'timestamp': pd.date_range(start='2025-01-01', periods=5, freq='H'),
            'open': [100, 102, 101, 103, 104],
            'high': [102, 103, 102, 105, 106],
            'low': [99, 100, 100, 102, 103],
            'close': [101, 102, 101, 104, 105],
            'volume': [1000, 1100, 1050, 1150, 1200]
        })
    
    def test_calculate_indicators(self):
        indicators = calculate_indicators(self.data)
        # Check that the indicators dictionary contains the expected keys
        expected_keys = ['price', 'rsi', 'adx', 'macd', 'macd_signal', 'sma_10', 'sma_25', 'sma_50', 'cmf', 'volume_level', 'bb_low', 'bb_medium', 'bb_high', 'prev_close']
        for key in expected_keys:
            self.assertIn(key, indicators)

if __name__ == "__main__":
    unittest.main()