#!/usr/bin/env python3
"""
Test Working Scalping Trader - ทดสอบระบบที่แก้ไขแล้ว
"""

import sys
sys.path.append('.')

from working_scalping_trader import WorkingGoldScalpingTrader
import MetaTrader5 as mt5
from datetime import datetime

def test_connection():
    """ทดสอบการเชื่อมต่อ MT5"""
    print("🔌 Testing MT5 Connection...")
    
    trader = WorkingGoldScalpingTrader()
    
    if trader.connect_mt5():
        print("✅ MT5 connection successful!")
        
        # ทดสอบดึงข้อมูล
        df = trader.get_gold_data(mt5.TIMEFRAME_M1, 20)
        if df is not None:
            print(f"✅ Data retrieval successful! Got {len(df)} bars")
            print(f"   Latest price: ${df.iloc[-1]['close']:.2f}")
        else:
            print("❌ Data retrieval failed!")
        
        mt5.shutdown()
        return True
    else:
        print("❌ MT5 connection failed!")
        return False

def test_indicators():
    """ทดสอบการคำนวณ indicators"""
    print("\n📊 Testing Indicator Calculations...")
    
    trader = WorkingGoldScalpingTrader()
    
    if not trader.connect_mt5():
        print("❌ Cannot connect to MT5")
        return False
    
    # ดึงข้อมูลและคำนวณ indicators
    df = trader.get_gold_data(mt5.TIMEFRAME_M1, 50)
    if df is None:
        print("❌ Cannot get data")
        mt5.shutdown()
        return False
    
    df = trader.calculate_simple_indicators(df)
    if df is None:
        print("❌ Cannot calculate indicators")
        mt5.shutdown()
        return False
    
    latest = df.iloc[-1]
    
    print("✅ Indicators calculated successfully!")
    print(f"   RSI: {latest['rsi']:.1f}")
    print(f"   MACD: {latest['macd']:.4f}")
    print(f"   EMA10: ${latest['ema_10']:.2f}")
    print(f"   EMA20: ${latest['ema_20']:.2f}")
    print(f"   BB Upper: ${latest['bb_upper']:.2f}")
    print(f"   BB Lower: ${latest['bb_lower']:.2f}")
    print(f"   ATR: {latest['atr']:.3f}")
    print(f"   Momentum: {latest['momentum']:.4f}")
    
    mt5.shutdown()
    return True

def test_market_conditions():
    """ทดสอบการตรวจสอบสภาพตลาด"""
    print("\n🌍 Testing Market Condition Checks...")
    
    trader = WorkingGoldScalpingTrader()
    
    if not trader.connect_mt5():
        print("❌ Cannot connect to MT5")
        return False
    
    market_ok, market_msg = trader.check_simple_market_conditions()
    
    if market_ok:
        print(f"✅ Market conditions OK: {market_msg}")
    else:
        print(f"⚠️ Market conditions not ideal: {market_msg}")
    
    mt5.shutdown()
    return True

def test_signal_generation():
    """ทดสอบการสร้างสัญญาณ BB + ZigZag + AI"""
    print("\n🎯 Testing BB + ZigZag + AI Signal Generation...")
    
    trader = WorkingGoldScalpingTrader()
    
    if not trader.connect_mt5():
        print("❌ Cannot connect to MT5")
        return False
    
    # ทดสอบสร้างสัญญาณ 5 ครั้ง
    signals_generated = 0
    bb_signals = 0
    zigzag_signals = 0
    ai_signals = 0
    
    for i in range(5):
        print(f"\n   Test #{i+1}:")
        
        signal_data = trader.generate_bb_zigzag_ai_signal()
        
        if signal_data:
            signals_generated += 1
            print(f"   ✅ Signal: {signal_data['signal']}")
            print(f"      Confidence: {signal_data['confidence']:.1%}")
            print(f"      Price: ${signal_data['price']:.2f}")
            print(f"      BB Upper: ${signal_data.get('bb_upper', 0):.2f}")
            print(f"      BB Lower: ${signal_data.get('bb_lower', 0):.2f}")
            
            # นับประเภทสัญญาณ
            reasons = signal_data['entry_reasons']
            if any('BB' in reason for reason in reasons):
                bb_signals += 1
            if any('ZigZag' in reason for reason in reasons):
                zigzag_signals += 1
            if any('AI' in reason for reason in reasons):
                ai_signals += 1
                
            print(f"      Reasons: {', '.join(reasons)}")
        else:
            print(f"   ❌ No signal generated")
    
    print(f"\n📊 BB + ZigZag + AI Signal Results:")
    print(f"   Total Signals: {signals_generated}/5")
    print(f"   BB Signals: {bb_signals}")
    print(f"   ZigZag Signals: {zigzag_signals}")
    print(f"   AI Signals: {ai_signals}")
    print(f"   Success Rate: {signals_generated/5*100:.0f}%")
    
    if signals_generated > 0:
        print("✅ BB + ZigZag + AI signal generation working!")
    else:
        print("❌ No signals generated - check settings")
    
    mt5.shutdown()
    return signals_generated > 0

def test_telegram():
    """ทดสอบการส่ง Telegram"""
    print("\n📱 Testing Telegram Messaging...")
    
    trader = WorkingGoldScalpingTrader()
    
    test_message = f"""
🧪 <b>SCALPING SYSTEM TEST</b>

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
🔧 <b>Status:</b> Testing Telegram Integration

<i>⚡ Working Gold Scalping Trader</i>
    """.strip()
    
    success = trader.send_telegram_message(test_message)
    
    if success:
        print("✅ Telegram message sent successfully!")
    else:
        print("❌ Telegram message failed!")
    
    return success

def run_quick_test():
    """รันการทดสอบแบบเร็ว"""
    print("\n🚀 Running Quick Scalping Test (2 minutes)...")
    
    trader = WorkingGoldScalpingTrader()
    
    # ปรับการตั้งค่าสำหรับทดสอบ
    trader.signal_interval_seconds = 10  # ทุก 10 วินาที
    trader.confidence_threshold = 0.5    # ลดเป็น 50%
    
    success = trader.run_scalping_session(2)  # 2 นาที
    
    if success:
        print("✅ Quick test completed!")
        print(f"   Orders placed: {len(trader.orders_placed)}")
    else:
        print("❌ Quick test failed!")
    
    return success

def main():
    """ฟังก์ชันหลัก"""
    print("🧪 BB + ZigZag + AI Gold Scalping Trader - System Test")
    print("=" * 60)
    
    # รันการทดสอบทีละขั้น
    tests = [
        ("MT5 Connection", test_connection),
        ("Indicator Calculations", test_indicators),
        ("Market Conditions", test_market_conditions),
        ("Signal Generation", test_signal_generation),
        ("Telegram Messaging", test_telegram)
    ]
    
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    # สรุปผลการทดสอบ
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed_tests}/{len(tests)} tests passed")
    
    if passed_tests == len(tests):
        print("🎉 All tests passed! System is ready to use.")
        
        # เสนอให้รันทดสอบจริง
        run_test = input("\nRun quick scalping test? (y/n, default n): ").strip().lower()
        if run_test == 'y':
            run_quick_test()
    else:
        print("⚠️ Some tests failed. Please check the issues before using.")
    
    print("\n🏁 Testing completed!")

if __name__ == "__main__":
    main()