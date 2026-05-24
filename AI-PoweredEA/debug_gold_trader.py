"""
Debug Gold Trader - ตรวจสอบปัญหาการส่งสัญญาณ
"""

import sys
sys.path.append('.')

from gold_ai_trader import GoldAITrader
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time

def debug_gold_trader():
    """ตรวจสอบปัญหาการส่งสัญญาณ"""
    print("🔍 Debug Gold AI Trader")
    print("=" * 40)
    
    # สร้าง trader
    trader = GoldAITrader()
    
    try:
        print("1. Testing MT5 connection...")
        if trader.connect_mt5():
            print("✅ MT5 connected successfully")
        else:
            print("❌ MT5 connection failed")
            return
        
        print("\n2. Testing model training...")
        if trader.train_gold_model():
            print("✅ Model trained successfully")
        else:
            print("❌ Model training failed")
            return
        
        print("\n3. Testing prediction generation...")
        prediction = trader.make_gold_prediction()
        if prediction:
            print(f"✅ Prediction generated: {prediction['signal']} ({prediction['confidence']:.1%})")
            print(f"   Current price: ${prediction['current_price']:.2f}")
            print(f"   Timeframe votes: {prediction['timeframe_votes']}")
        else:
            print("❌ No prediction generated")
            return
        
        print("\n4. Testing Telegram message formatting...")
        message = trader.format_telegram_message(prediction)
        print("✅ Message formatted:")
        print(message)
        
        print("\n5. Testing Telegram send...")
        if trader.send_telegram_message(message):
            print("✅ Telegram message sent successfully!")
        else:
            print("❌ Telegram message failed")
        
        print("\n6. Testing timing logic...")
        current_time = datetime.now()
        last_signal_time = current_time - timedelta(minutes=16)  # 16 นาทีที่แล้ว
        signal_interval_minutes = 15
        
        time_since_last_signal = (current_time - last_signal_time).total_seconds()
        print(f"   Current time: {current_time.strftime('%H:%M:%S')}")
        print(f"   Last signal time: {last_signal_time.strftime('%H:%M:%S')}")
        print(f"   Time since last signal: {time_since_last_signal/60:.1f} minutes")
        print(f"   Signal interval: {signal_interval_minutes} minutes")
        print(f"   Should send signal: {time_since_last_signal >= signal_interval_minutes * 60}")
        
        print("\n7. Testing spread check...")
        if trader.check_spread():
            print("✅ Spread is acceptable")
        else:
            print("⚠️ Spread too high")
        
        print("\n🎉 Debug completed!")
        
    except Exception as e:
        print(f"\n❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # ปิดการเชื่อมต่อ MT5
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    debug_gold_trader()