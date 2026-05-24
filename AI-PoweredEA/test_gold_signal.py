"""
Test Gold Signal - ทดสอบส่งสัญญาณทองทันที
"""

import sys
sys.path.append('.')

from gold_ai_trader import GoldAITrader
import MetaTrader5 as mt5

def test_gold_signal():
    """ทดสอบส่งสัญญาณทองทันที"""
    print("🧪 Testing Gold AI Signal")
    print("=" * 40)
    
    # สร้าง trader
    trader = GoldAITrader()
    
    try:
        # ทดสอบส่งสัญญาณ
        success = trader.test_signal_now()
        
        if success:
            print("\n✅ Signal test completed successfully!")
        else:
            print("\n❌ Signal test failed")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # ปิดการเชื่อมต่อ MT5
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    test_gold_signal()