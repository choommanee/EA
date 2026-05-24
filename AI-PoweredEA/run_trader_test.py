#!/usr/bin/env python3
"""
Simple test runner for Gold Scalping Trader
รันทดสอบระบบ AI Trading แบบง่าย
"""

import sys
import os

def run_trader_test():
    """รันทดสอบ trader"""
    print("🚀 TESTING GOLD SCALPING TRADER")
    print("=" * 40)
    
    try:
        # Import trader
        from working_scalping_trader import WorkingGoldScalpingTrader
        print("✅ Trader imported successfully")
        
        # Create instance
        trader = WorkingGoldScalpingTrader()
        print("✅ Trader instance created")
        
        # Show settings
        print(f"\n📊 Trader Settings:")
        print(f"   Symbol: {trader.symbol}")
        print(f"   Max Positions: {trader.max_positions}")
        print(f"   Risk/Reward: {trader.tp_risk_reward_ratio}")
        print(f"   Confidence Threshold: {trader.confidence_threshold:.0%}")
        
        # Test MT5 connection
        print(f"\n🔌 Testing MT5 connection...")
        if trader.connect_mt5():
            print("✅ MT5 connected successfully")
            
            # Test data retrieval
            print(f"\n📊 Testing data retrieval...")
            df = trader.get_gold_data(trader.main_timeframe, 50)
            if df is not None and len(df) > 0:
                print(f"✅ Data retrieved: {len(df)} bars")
                print(f"   Latest price: ${df['close'].iloc[-1]:.2f}")
                
                # Test indicators
                print(f"\n📈 Testing indicators...")
                df_indicators = trader.calculate_simple_indicators(df)
                if df_indicators is not None:
                    latest = df_indicators.iloc[-1]
                    print("✅ Indicators calculated:")
                    print(f"   RSI: {latest['rsi']:.1f}")
                    print(f"   BB Upper: ${latest['bb_upper']:.2f}")
                    print(f"   BB Lower: ${latest['bb_lower']:.2f}")
                    
                    # Test signal generation
                    print(f"\n🎯 Testing signal generation...")
                    signal = trader.generate_simple_signal()
                    if signal:
                        print("✅ Signal generated:")
                        print(f"   Type: {signal['signal']}")
                        print(f"   Confidence: {signal['confidence']:.1%}")
                        print(f"   Price: ${signal['price']:.2f}")
                    else:
                        print("⚪ No signal (normal - waiting for optimal conditions)")
                    
                    print(f"\n🎉 ALL TESTS PASSED!")
                    print(f"\n🚀 Ready to run live session!")
                    print(f"Run: python working_scalping_trader.py")
                    
                else:
                    print("❌ Indicators calculation failed")
            else:
                print("❌ Data retrieval failed")
        else:
            print("❌ MT5 connection failed")
            print("💡 Please ensure:")
            print("   - MetaTrader 5 is running")
            print("   - Connected to broker")
            print("   - GOLDm# symbol is available")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Check if all required libraries are installed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_trader_test()
