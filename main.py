import time
import logging
from datetime import datetime
from deepseek_signal.signalGen import DeepSeekSignalGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_bot():
    """Main trading bot loop"""
    generator = DeepSeekSignalGenerator()
    symbols = ["XBTUSD", "ETHUSD"]  # Add more symbols as needed
    
    logger.info("🤖 Starting Trading Bot")
    logger.info(f"Monitoring symbols: {symbols}")
    
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"⏰ Cycle started at {current_time}")
            
            for symbol in symbols:
                logger.info(f"📊 Analyzing {symbol}...")
                
                signal = generator.generate_signal(symbol)
                
                if signal:
                    logger.info(f"✅ {symbol} Signal: {signal['signal']}")
                    logger.info(f"   Price: ${signal['current_price']:,.2f}")
                    logger.info(f"   Stop: ${signal['stop_price']:,.2f}")
                    logger.info(f"   Target: ${signal['target_price']:,.2f}")
                    
                    # Here we would execute the trade (part 2)
                    # execute_trade(signal)
                    
                else:
                    logger.warning(f"❌ Failed to generate signal for {symbol}")
                
                # Small delay between symbols
                time.sleep(2)
            
            logger.info("♻️ Cycle completed. Waiting for next cycle...")
            time.sleep(180)  # Wait 3 minutes between full cycles
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}")
            time.sleep(30)  # Wait before retrying after error

if __name__ == "__main__":
    run_bot()
