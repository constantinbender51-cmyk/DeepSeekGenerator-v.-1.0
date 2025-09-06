import requests
import logging
import json
import os
import time
from typing import Dict, Optional, List
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.max_retries = 3
        self.retry_delay = 2
    
    def _fetch_ohlc_data(self, symbol: str = "XBTUSD", interval: int = 60, count: int = 50) -> Optional[List[Dict]]:
        """Fetch multiple OHLC data points from Kraken public API"""
        try:
            url = "https://api.kraken.com/0/public/OHLC"
            params = {
                'pair': symbol,
                'interval': interval,
                'count': count
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data['error']:
                logger.error(f"Kraken API error: {data['error']}")
                return None
            
            # Get all OHLC data points
            ohlc_list = data['result'][list(data['result'].keys())[0]]
            
            formatted_data = []
            for ohlc in ohlc_list:
                formatted_data.append({
                    'timestamp': ohlc[0],
                    'open': float(ohlc[1]),
                    'high': float(ohlc[2]),
                    'low': float(ohlc[3]),
                    'close': float(ohlc[4]),
                    'volume': float(ohlc[6]),
                    'trades': int(ohlc[7]) if len(ohlc) > 7 else 0
                })
            
            logger.info(f"Fetched {len(formatted_data)} OHLC data points for {symbol}")
            return formatted_data
            
        except Exception as e:
            logger.error(f"Failed to fetch OHLC data: {e}")
            return None
    
    def _prepare_prompt(self, ohlc_data: List[Dict], symbol: str) -> str:
        """Prepare comprehensive prompt for DeepSeek"""
        
        # Format recent data for the prompt
        recent_data = ohlc_data[-10:]  # Last 10 data points
        
        data_lines = []
        for data in recent_data:
            data_lines.append(
                f"Time: {data['timestamp']}, "
                f"O: {data['open']:.2f}, "
                f"H: {data['high']:.2f}, "
                f"L: {data['low']:.2f}, "
                f"C: {data['close']:.2f}, "
                f"V: {data['volume']:.2f}"
            )
        
        # Calculate some basic statistics
        current_price = ohlc_data[-1]['close']
        high_24h = max(data['high'] for data in ohlc_data)
        low_24h = min(data['low'] for data in ohlc_data)
        volume_24h = sum(data['volume'] for data in ohlc_data)
        price_change = ((current_price - ohlc_data[0]['open']) / ohlc_data[0]['open']) * 100
        
        prompt = f"""
        You are an expert cryptocurrency trading analyst. Analyze the following OHLC data for {symbol} and provide a trading signal.

        RECENT OHLC DATA (last 10 periods):
        {chr(10).join(data_lines)}

        SUMMARY STATISTICS:
        - Current Price: {current_price:.2f}
        - 24h High: {high_24h:.2f}
        - 24h Low: {low_24h:.2f}
        - 24h Volume: {volume_24h:.2f}
        - Price Change: {price_change:.2f}%

        Please provide your analysis in the following JSON format:
        {{
            "signal": "BUY|SELL|HOLD",
            "stop_price": number,
            "target_price": number,
            "confidence": number (0-100),
            "timeframe": "string (e.g., 1-4 hours)",
            "reasoning": "detailed technical analysis reasoning"
        }}

        Considerations:
        1. Analyze price action and trends
        2. Identify support/resistance levels
        3. Consider volume patterns
        4. Assess risk/reward ratio
        5. Current market conditions

        Provide ONLY valid JSON output, no additional text.
        """
        
        return prompt
    
    def _call_deepseek_api(self, prompt: str) -> Optional[Dict]:
        """Call DeepSeek API with retry logic"""
        
        if not self.api_key:
            logger.error("DeepSeek API key not found. Set DEEPSEEK_API_KEY environment variable.")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert cryptocurrency trading analyst. Provide trading signals in exact JSON format as requested. Only respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Calling DeepSeek API (attempt {attempt + 1}/{self.max_retries})...")
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # Handle rate limiting and errors
                if response.status_code == 429:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code in [401, 403]:
                    logger.error("Authentication failed. Check your API key.")
                    return None
                
                response.raise_for_status()
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON response
                signal_data = json.loads(content)
                
                # Validate response structure
                required_fields = ["signal", "stop_price", "target_price", "reasoning"]
                if all(field in signal_data for field in required_fields):
                    logger.info("Successfully received signal from DeepSeek")
                    return signal_data
                else:
                    logger.error(f"Invalid response format: {signal_data}")
                    return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                continue
        
        logger.error("All DeepSeek API attempts failed")
        return None
    
    def generate_signal(self, symbol: str = "XBTUSD") -> Optional[Dict]:
        """
        Generate trading signal using DeepSeek AI
        
        Returns:
            Dict with signal data or None if failed
        """
        # Fetch OHLC data from Kraken
        ohlc_data = self._fetch_ohlc_data(symbol, count=50)
        if not ohlc_data:
            logger.error("Failed to fetch market data")
            return None
        
        current_price = ohlc_data[-1]['close']
        logger.info(f"Current {symbol} price: {current_price:.2f}")
        
        # Prepare prompt and call DeepSeek
        prompt = self._prepare_prompt(ohlc_data, symbol)
        deepseek_response = self._call_deepseek_api(prompt)
        
        if deepseek_response:
            # Combine with market data
            signal_data = {
                "signal": deepseek_response.get("signal", "HOLD"),
                "symbol": symbol,
                "current_price": current_price,
                "stop_price": deepseek_response.get("stop_price", 0),
                "target_price": deepseek_response.get("target_price", 0),
                "confidence": deepseek_response.get("confidence", 0),
                "timeframe": deepseek_response.get("timeframe", "N/A"),
                "timestamp": ohlc_data[-1]['timestamp'],
                "reasoning": deepseek_response.get("reasoning", ""),
                "source": "deepseek-ai"
            }
            
            # Calculate risk/reward ratio
            if (signal_data['signal'] in ['BUY', 'SELL'] and 
                signal_data['stop_price'] and signal_data['target_price']):
                
                if signal_data['signal'] == 'BUY':
                    risk = current_price - signal_data['stop_price']
                    reward = signal_data['target_price'] - current_price
                else:  # SELL
                    risk = signal_data['stop_price'] - current_price
                    reward = current_price - signal_data['target_price']
                
                if risk > 0:
                    signal_data['risk_reward_ratio'] = round(reward / risk, 2)
            
            return signal_data
        else:
            logger.warning("DeepSeek API failed, falling back to mock signal")
            return self._generate_mock_signal(ohlc_data[-1], symbol)
    
    def _generate_mock_signal(self, ohlc_data: Dict, symbol: str) -> Dict:
        """Generate mock signal as fallback"""
        close = ohlc_data['close']
        
        # Simple mock logic
        if close > ohlc_data['open']:
            signal = "BUY"
            stop_price = close * 0.98
            target_price = close * 1.04
            reasoning = "Bullish candle with higher close"
        elif close < ohlc_data['open']:
            signal = "SELL"
            stop_price = close * 1.02
            target_price = close * 0.96
            reasoning = "Bearish candle with lower close"
        else:
            signal = "HOLD"
            stop_price = 0
            target_price = 0
            reasoning = "Neutral price action"
        
        return {
            "signal": signal,
            "symbol": symbol,
            "current_price": close,
            "stop_price": stop_price,
            "target_price": target_price,
            "confidence": 50,
            "timeframe": "1-4 hours",
            "timestamp": ohlc_data['timestamp'],
            "reasoning": reasoning,
            "source": "mock-fallback"
        }

# Test function
def test_signal_generation():
    """Test the signal generation"""
    generator = DeepSeekSignalGenerator()
    
    print("Testing DeepSeek signal generation...")
    print("=" * 60)
    
    signal = generator.generate_signal("XBTUSD")
    
    if signal:
        print(f"✅ Signal Generated: {signal['signal']}")
        print(f"Symbol: {signal['symbol']}")
        print(f"Current Price: {signal['current_price']:.2f}")
        print(f"Stop Price: {signal['stop_price']:.2f}")
        print(f"Target Price: {signal['target_price']:.2f}")
        print(f"Confidence: {signal['confidence']}%")
        print(f"Timeframe: {signal['timeframe']}")
        if 'risk_reward_ratio' in signal:
            print(f"Risk/Reward: 1:{signal['risk_reward_ratio']:.2f}")
        print(f"Source: {signal['source']}")
        print(f"\nReasoning: {signal['reasoning']}")
    else:
        print("❌ Failed to generate signal")
    
    print("=" * 60)

if __name__ == "__main__":
    test_signal_generation()
