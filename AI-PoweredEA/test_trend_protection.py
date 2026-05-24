#!/usr/bin/env python3
"""
ทดสอบระบบป้องกันการเทรดย้อนเทรน
"""

import sys
import time
from working_scalping_trader import WorkingGoldScalpingTrader

def test_trend_protection():
    """ทดสอบการป้องกันเทรน"""
    print("🧪 Testing Trend Protection System")
    print("="*60)
    
    # สร้าง trader
    trader = WorkingGoldScalpingTrader()
    
    # ตั้งค่าสำหรับทดสอบ
    trader.confidence_threshold = 0.5  # ลดเพื่อให้ออกสัญญาณง่าย
    trader.enable_trend_protection = True  # เปิดการป้องกันเทรน
    
    print(f"⚙️ Test Settings:")
    print(f"   🎯 Confidence Threshold: {trader.confidence_threshold:.0%}")
    print(f"   🚨 Trend Protection: {'ON' if trader.enable_trend_protection else 'OFF'}")
    print(f"   📊 Strong Trend Threshold: {trader.strong_trend_threshold}")
    print(f"   📈 Max Consecutive Candles: {trader.max_consecutive_candles}")
    print(f"   ⚡ Trend Momentum Limit: {trader.trend_momentum_limit:.3f}")
    print(f"   📏 EMA Separation Limit: ${trader.ema_separation_limit}")
    print()
    
    # เชื่อมต่อ MT5
    if not trader.connect_mt5():
        print("❌ Cannot connect to MT5")
        return False
    
    # ทดสอบการตรวจสอบเทรน
    print("🔍 Testing Trend Detection...")
    
    # ดึงข้อมูลสำหรับทดสอบ
    df_m1 = trader.get_gold_data(trader.main_timeframe, 100)
    if df_m1 is None:
        print("❌ Cannot get market data")
        return False
    
    df_m1 = trader.calculate_simple_indicators(df_m1)
    if df_m1 is None:
        print("❌ Cannot calculate indicators")
        return False
    
    latest = df_m1.iloc[-1]
    
    # แสดงข้อมูลตลาดปัจจุบัน
    print(f"📊 Current Market Data:")
    print(f"   💰 Price: ${latest['close']:.2f}")
    print(f"   📈 EMA 10: ${latest['ema_10']:.2f}")
    print(f"   📉 EMA 20: ${latest['ema_20']:.2f}")
    print(f"   📏 EMA Separation: ${abs(latest['ema_10'] - latest['ema_20']):.2f}")
    print(f"   📊 Trend Strength: {latest['trend_strength']:.2f}")
    print(f"   ⚡ Momentum: {latest['momentum']:.4f}")
    print(f"   💪 Momentum Strength: {latest['momentum_strength']:.4f}")
    print(f"   📈 Consecutive Up: {latest['consecutive_up']}")
    print(f"   📉 Consecutive Down: {latest['consecutive_down']}")
    print()
    
    # ทดสอบการตรวจสอบเทรน
    print("🔍 Trend Analysis:")
    is_strong_trend, trend_reason, trend_direction = trader.detect_strong_trend(df_m1)
    
    if is_strong_trend:
        print(f"   🚨 STRONG {trend_direction} TREND DETECTED!")
        print(f"   🚨 Reason: {trend_reason}")
        print(f"   🚨 Counter-trend trading will be BLOCKED")
        
        if trend_direction == "UP":
            print(f"   ❌ SELL signals will be blocked")
            print(f"   ✅ BUY signals may still be allowed")
        else:
            print(f"   ❌ BUY signals will be blocked")
            print(f"   ✅ SELL signals may still be allowed")
    else:
        print(f"   ✅ No strong trend detected")
        print(f"   ✅ Both BUY and SELL signals allowed")
        print(f"   📝 Reason: {trend_reason}")
    
    print()
    
    # ทดสอบการสร้างสัญญาณ
    print("🎯 Testing Signal Generation with Trend Protection...")
    
    for i in range(3):
        print(f"\n--- Test Signal #{i+1} ---")
        
        # สร้างสัญญาณ
        signal_data = trader.generate_bb_zigzag_ai_signal()
        
        if signal_data:
            print(f"✅ Signal Generated: {signal_data['signal']} ({signal_data['confidence']:.1%})")
            print(f"💰 Price: ${signal_data['price']:.2f}")
            print(f"📋 Reasons: {', '.join(signal_data['entry_reasons'])}")
        else:
            print(f"❌ No signal generated (may be blocked by trend protection)")
        
        time.sleep(2)
    
    print("\n" + "="*60)
    print("🏁 Trend Protection Test Completed")
    
    # สรุปผล
    print(f"\n📋 Summary:")
    print(f"   🚨 Trend Protection: {'ACTIVE' if trader.enable_trend_protection else 'INACTIVE'}")
    print(f"   📊 Current Trend: {trend_direction if is_strong_trend else 'NEUTRAL'}")
    print(f"   🛡️ Protection Status: {'PROTECTING' if is_strong_trend else 'ALLOWING ALL SIGNALS'}")
    
    return True

def test_trend_settings():
    """ทดสอบการปรับ settings ของ trend protection"""
    print("\n🔧 Testing Trend Protection Settings")
    print("="*40)
    
    trader = WorkingGoldScalpingTrader()
    
    # ทดสอบ settings ต่างๆ
    test_cases = [
        {"name": "Conservative", "trend_threshold": 1.0, "momentum_limit": 0.003, "consecutive": 3, "ema_limit": 0.5},
        {"name": "Moderate", "trend_threshold": 1.5, "momentum_limit": 0.005, "consecutive": 4, "ema_limit": 0.8},
        {"name": "Aggressive", "trend_threshold": 2.0, "momentum_limit": 0.008, "consecutive": 5, "ema_limit": 1.2},
    ]
    
    for case in test_cases:
        print(f"\n📊 {case['name']} Settings:")
        print(f"   Trend Threshold: {case['trend_threshold']}")
        print(f"   Momentum Limit: {case['momentum_limit']:.3f}")
        print(f"   Max Consecutive: {case['consecutive']}")
        print(f"   EMA Separation: ${case['ema_limit']}")
        
        # อัพเดท settings
        trader.strong_trend_threshold = case['trend_threshold']
        trader.trend_momentum_limit = case['momentum_limit']
        trader.max_consecutive_candles = case['consecutive']
        trader.ema_separation_limit = case['ema_limit']
        
        print(f"   ✅ Settings applied")

if __name__ == "__main__":
    try:
        test_trend_protection()
        test_trend_settings()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")