from deepseek_signal.signalGen import DeepSeekSignalGenerator

def main():
    print("🚀 DeepSeek Signal Generator Running on Railway")
    print("=" * 50)
    
    generator = DeepSeekSignalGenerator()
    
    # Test with Bitcoin
    print("📊 Fetching BTC/USD data from Kraken...")
    signal = generator.generate_signal("XBTUSD")
    
    if signal:
        print(f"\n✅ Signal Generated:")
        print(f"   Type: {signal['signal']}")
        print(f"   Symbol: {signal['symbol']}")
        print(f"   Current Price: ${signal['current_price']:,.2f}")
        print(f"   Stop Price: ${signal['stop_price']:,.2f}")
        print(f"   Target Price: ${signal['target_price']:,.2f}")
        print(f"   Reasoning: {signal['reasoning']}")
    else:
        print("❌ Failed to generate signal")

if __name__ == "__main__":
    main()
