import os
import json
import requests
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class TradingSignal:
    signal_type: SignalType
    symbol: str
    stop_price: float
    target_price: float
    confidence: float
    timestamp: str
    reasoning: str

class DeepSeekSignalGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1"  # Assuming this is the API endpoint
        self.model = "deepseek-chat"  # Adjust based on available models
        
        if not self.api_key:
            logger.warning("DeepSeek API key not provided. Set DEEPSEEK_API_KEY environment variable.")
    
    def _prepare_prompt(self, market_data: Dict) -> str:
        """Prepare the trading prompt for DeepSeek"""
        prompt_template = """
        Analyze the following market data and provide a trading signal:
        
        Symbol: {symbol}
        Current Price: {current_price}
        24h High: {high_24h}
        24h Low: {low_24h}
        24h Volume: {volume_24h}
        RSI: {rsi}
        MACD: {macd}
        Moving Average (50): {ma_50}
        Moving Average (200): {ma_200}
        
        Please provide your analysis in the following JSON format:
        {{
            "signal": "BUY/SELL/HOLD",
            "stop_price": number,
            "target_price": number,
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
        
        Be precise with price levels and provide realistic risk-reward ratios.
        """
        
        return prompt_template.format(**market_data)
    
    def _parse_signal_response(self, response_text: str) -> Optional[TradingSignal]:
        """Parse DeepSeek's response into a structured signal"""
        try:
            # Extract JSON from response (might be wrapped in text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            signal_data = json.loads(json_str)
            
            return TradingSignal(
                signal_type=SignalType(signal_data['signal']),
                symbol=signal_data.get('symbol', 'UNKNOWN'),
                stop_price=float(signal_data['stop_price']),
                target_price=float(signal_data['target_price']),
                confidence=float(signal_data['confidence']),
                timestamp=signal_data.get('timestamp', ''),
                reasoning=signal_data['reasoning']
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse signal response: {e}")
            logger.error(f"Response text: {response_text}")
            return None
    
    def generate_signal(self, market_data: Dict) -> Optional[TradingSignal]:
        """
        Generate trading signal based on market data
        
        Args:
            market_data: Dictionary containing market information
                Required keys: symbol, current_price, high_24h, low_24h, volume_24h
                Optional keys: rsi, macd, ma_50, ma_200, etc.
        
        Returns:
            TradingSignal object or None if failed
        """
        if not self.api_key:
            logger.error("API key not available")
            return None
        
        prompt = self._prepare_prompt(market_data)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,  # Low temperature for consistent outputs
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            
            signal = self._parse_signal_response(content)
            
            if signal:
                logger.info(f"Generated signal: {signal.signal_type.value} for {signal.symbol}")
                logger.info(f"Stop: {signal.stop_price}, Target: {signal.target_price}")
            
            return signal
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

# Example usage and test function
def test_signal_generator():
    """Test function to demonstrate usage"""
    
    # Mock market data - replace with real data
    market_data = {
        "symbol": "BTCUSDT",
        "current_price": 42000.50,
        "high_24h": 42500.75,
        "low_24h": 41800.25,
        "volume_24h": 1500000000,
        "rsi": 62.5,
        "macd": 150.25,
        "ma_50": 41500.00,
        "ma_200": 40000.00
    }
    
    # Initialize generator
    generator = DeepSeekSignalGenerator()
    
    # Generate signal
    signal = generator.generate_signal(market_data)
    
    if signal:
        print(f"Signal: {signal.signal_type.value}")
        print(f"Symbol: {signal.symbol}")
        print(f"Stop Price: {signal.stop_price}")
        print(f"Target Price: {signal.target_price}")
        print(f"Confidence: {signal.confidence}")
        print(f"Reasoning: {signal.reasoning}")
    else:
        print("Failed to generate signal")

if __name__ == "__main__":
    test_signal_generator()
