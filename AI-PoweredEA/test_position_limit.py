#!/usr/bin/env python3
"""
ทดสอบระบบจำกัด positions ไม่เกิน 2 รายการ
"""

import sys
import time
from working_scalping_trader import WorkingGoldScalpingTrader

def test_position_limit():
    """ทดสอบการจำกัด positions"""
    print("🧪 Testing Position Limit System")
    print("="*50)
    
    # สร้าง trader
    trader = WorkingGoldScalpingTrader()
    
    # ตั้งค่าสำหรับทดสอบ
    trader.confidence_threshold = 0.5  # ลดเพื่อให้ออกสัญญาณง่าย
    trader.signal_interval_seconds = 5  # ตรวจทุก 5 วินาที
    trader.max_daily_trades = 10  # จำกัดสำหรับทดสอบ
    
    print(f"⚙️ Test Settings:")
    print(f"   🎯 Confidence Threshold: {trader.confidence_threshold:.0%}")
    print(f"   ⏰ Signal Interval: {trader.signal_interval_seconds} seconds")
    print(f"   💼 Max Positions: 2 (จำกัดไม่ให้เข้าเยอะเกินไป)")
    print(f"   📈 Max Daily Trades: {trader.max_daily_trades}")
    print()
    
    # เชื่อมต่อ MT5
    if not trader.connect_mt5():
        print("❌ Cannot connect to MT5")
        return False
    
    # แสดงสถานะ positions ปัจจุบัน
    print("📊 Current Status:")
    trader.show_positions_status()
    print()
    
    # ทดสอบการตรวจสอบสภาพตลาด
    print("🔍 Testing Market Conditions...")
    market_ok, market_msg = trader.check_simple_market_conditions()
    print(f"   Market Status: {'✅' if market_ok else '❌'} {market_msg}")
    print()
    
    # ทดสอบการสร้างสัญญาณ
    print("🎯 Testing Signal Generation...")
    for i in range(3):
        print(f"\n--- Test Signal #{i+1} ---")
        
        # ตรวจสอบจำนวน positions ปัจจุบัน
        active_positions = trader.get_active_positions()
        positions_count = len(active_positions)
        
        print(f"💼 Current Positions: {positions_count}/2")
        
        if positions_count >= 2:
            print("⚠️ Position limit reached - No new signals will be processed")
            break
        
        # สร้างสัญญาณ
        signal_data = trader.generate_simple_signal()
        
        if signal_data:
            print(f"🎯 Signal Generated: {signal_data['signal']} ({signal_data['confidence']:.1%})")
            print(f"💰 Price: ${signal_data['price']:.2f}")
            print(f"📋 Reasons: {', '.join(signal_data['entry_reasons'])}")
            
            # จำลองการเปิด position (ไม่เปิดจริง)
            print("📝 Simulating order placement...")
            print("   ✅ Order would be placed (simulation)")
            
        else:
            print("❌ No signal generated")
        
        time.sleep(2)
    
    print("\n" + "="*50)
    print("🏁 Position Limit Test Completed")
    
    # แสดงสถานะสุดท้าย
    trader.show_positions_status()
    
    return True

if __name__ == "__main__":
    try:
        test_position_limit()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")