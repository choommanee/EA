"""
Gold Trader Quick - รันเทรดทองแบบเร็ว (ส่งสัญญาณทุก 5 นาที)
"""

import sys
sys.path.append('.')

from gold_ai_trader import GoldAITrader
import MetaTrader5 as mt5

def run_quick_gold_trader():
    """รันเทรดทองแบบเร็ว"""
    print("🚀 Quick Gold AI Trader")
    print("=" * 40)
    
    # สร้าง trader
    trader = GoldAITrader()
    
    # เริ่มต้นคอมโพเนนต์ AI
    trader.initialize_ai_components()
    
    try:
        # รันเทรด 30 นาที, ส่งสัญญาณทุก 5 นาที
        print("🎯 Running 30 minutes, signals every 5 minutes")
        success = trader.run_gold_trader(duration_minutes=30, signal_interval_minutes=5)
        
        if success:
            print("\n✅ Quick trading completed successfully!")
        else:
            print("\n❌ Quick trading failed")
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # ปิดการเชื่อมต่อ MT5
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    run_quick_gold_trader()