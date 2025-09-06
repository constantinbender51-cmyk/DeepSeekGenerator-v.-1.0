import requests
import logging
from typing import Dict, Optional
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class DeepSeekSignalGenerator:
    def __init__(self):
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
    
    def _fetch_ohlc_data(self, symbol: str = "XBTUSD", interval: int = 60) -> Optional[Dict]:
        """Fetch OHLC data from Kraken public API"""
        try:
            url = f"https://api.kraken.com/0/public/OHLC"
            params = {
                'pair': symbol,
                'interval': interval
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['error']:
                logger.error(f"Kraken API error: {data['error']}")
                return None
            
            # Get the latest OHLC data (last array in the result)
            ohlc_data = data['result'][list(data['result'].keys())[0]][-1]
            
            return {
                'timestamp': ohlc_data[0],
                'open': float(ohlc_data[1]),
                'high': float(ohlc_data[2]),
                'low': float(ohlc_data[3]),
                'close': float(ohlc_data[4]),
                'volume': float(ohlc_data[6])
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch OHLC data: {e}")
            return None
    
    def _prepare_prompt(self, ohlc_data: Dict, symbol: str) -> str:
        """Prepare simple prompt with only OHLC data"""
        return f"""
        Analyze this OHLC data for {symbol} and provide a trading signal:
        
        Time: {ohlc_data['timestamp']}
        Open: {ohlc_data['open']}
        High: {ohlc_data['high']}
        Low: {ohlc_data['low']}
        Close: {ohlc_data['close']}
        Volume: {ohlc_data['volume']}
        
        Respond with ONLY JSON in this format:
        {{
            "signal": "BUY|SELL|HOLD",
            "stop_price": number,
            "target_price": number,
            "reasoning": "brief explanation"
        }}
        """
    
    def generate_signal(self, symbol: str = "XBTUSD") -> Optional[Dict]:
        """
        Generate trading signal for given symbol
        
        Returns:
            Dict with signal data or None if failed
        """
        # First fetch OHLC data from Kraken
        ohlc_data = self._fetch_ohlc_data(symbol)
        if not ohlc_data:
            logger.error("Failed to fetch market data")
            return None
        
        logger.info(f"Fetched OHLC data for {symbol}: {ohlc_data['close']}")
        
        # For now, return mock signal (we'll integrate DeepSeek later)
        return self._generate_mock_signal(ohlc_data, symbol)
    
    def _generate_mock_signal(self, ohlc_data: Dict, symbol: str) -> Dict:
        """Generate mock signal for testing"""
        close = ohlc_data['close']
        
        # Simple mock logic based on price action
        if close > ohlc_data['open']:  # Green candle
            signal = "BUY"
            stop_price = close * 0.98  # 2% stop loss
            target_price = close * 1.04  # 4% target
        elif close < ohlc_data['open']:  # Red candle
            signal = "SELL"
            stop_price = close * 1.02  # 2% stop loss
            target_price = close * 0.96  # 4% target
        else:
            signal = "HOLD"
            stop_price = 0
            target_price = 0
        
        return {
            "signal": signal,
            "symbol": symbol,
            "current_price": close,
            "stop_price": stop_price,
            "target_price": target_price,
            "timestamp": ohlc_data['timestamp'],
            "reasoning": "Mock signal based on OHLC data"
        }

# Simple test
if __name__ == "__main__":
    generator = DeepSeekSignalGenerator()
    
    print("Fetching OHLC data and generating signal...")
    signal = generator.generate_signal("XBTUSD")
    
    if signal:
        print(f"\nSignal: {signal['signal']}")
        print(f"Symbol: {signal['symbol']}")
        print(f"Price: {signal['current_price']}")
        print(f"Stop: {signal['stop_price']}")
        print(f"Target: {signal['target_price']}")
        print(f"Reason: {signal['reasoning']}")
    else:
        print("Failed to generate signal")
