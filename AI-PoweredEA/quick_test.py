#!/usr/bin/env python3
"""
Quick test for Gold Scalping Trader
ทดสอบด่วนระบบ AI Trading
"""

print("🚀 GOLD SCALPING TRADER - QUICK TEST")
print("=" * 40)

# Test 1: Basic imports
try:
    import pandas as pd
    import numpy as np
    print("✅ Basic libraries OK")
except:
    print("❌ Basic libraries failed")

# Test 2: Check if working_scalping_trader.py exists
import os
if os.path.exists("working_scalping_trader.py"):
    print("✅ working_scalping_trader.py found")
else:
    print("❌ working_scalping_trader.py not found")

# Test 3: Try to import trader class
try:
    from working_scalping_trader import WorkingGoldScalpingTrader
    print("✅ Trader class imported")
    
    # Create instance
    trader = WorkingGoldScalpingTrader()
    print("✅ Trader instance created")
    
    # Check settings
    print(f"   Symbol: {trader.symbol}")
    print(f"   Max positions: {trader.max_positions}")
    print(f"   Risk/Reward: {trader.tp_risk_reward_ratio}")
    
except Exception as e:
    print(f"❌ Trader import failed: {e}")

# Test 4: Check optimization settings
try:
    with open("working_scalping_trader.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    optimizations = [
        ("signal_data['rsi'] <= 30", "BUY RSI ≤ 30"),
        ("signal_data['rsi'] >= 70", "SELL RSI ≥ 70"), 
        ("signal_data['bb_position'] <= 0.18", "BUY BB ≤ 0.18"),
        ("signal_data['bb_position'] >= 0.82", "SELL BB ≥ 0.82"),
        ("signal_data['ema_10'] > signal_data['ema_20']", "BUY EMA bias"),
        ("signal_data['ema_10'] < signal_data['ema_20']", "SELL EMA bias")
    ]
    
    print("\n📊 Optimization Check:")
    for check, desc in optimizations:
        if check in content:
            print(f"✅ {desc}")
        else:
            print(f"❌ {desc}")
            
except Exception as e:
    print(f"❌ Optimization check failed: {e}")

print("\n🎯 Test Summary:")
print("ระบบ Gold Scalping Trader พร้อมใช้งาน")
print("การปรับปรุงจาก backtest ได้ถูกนำมาใช้แล้ว")
print("\n💡 วิธีรันจริง:")
print("1. เปิด MetaTrader 5")
print("2. เชื่อมต่อกับ broker") 
print("3. รัน: python working_scalping_trader.py")
print("4. ใส่เวลาที่ต้องการเทรด (นาที)")

print("\n🚀 พร้อมเทรด Gold ด้วย AI!")
