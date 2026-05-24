#!/usr/bin/env python3
"""
Debug script to analyze why bot is not entering trades
วิเคราะห์ว่าทำไมบอทไม่เข้าเทรด
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime

try:
    from working_scalping_trader import WorkingGoldScalpingTrader
    import MetaTrader5 as mt5
    
    def debug_signal_conditions():
        """วิเคราะห์เงื่อนไขสัญญาณแบบละเอียด"""
        print("🔍 DEBUGGING SIGNAL CONDITIONS")
        print("=" * 50)
        
        # สร้าง trader
        trader = WorkingGoldScalpingTrader()
        
        # เชื่อมต่อ MT5
        if not trader.connect_mt5():
            print("❌ Cannot connect to MT5")
            return
        
        print("✅ MT5 connected")
        
        # ดึงข้อมูลตลาด
        df = trader.get_gold_data(trader.main_timeframe, 100)
        if df is None:
            print("❌ Cannot get market data")
            return
        
        print(f"✅ Market data retrieved: {len(df)} bars")
        
        # คำนวณ indicators
        df = trader.calculate_simple_indicators(df)
        if df is None:
            print("❌ Cannot calculate indicators")
            return
        
        print("✅ Indicators calculated")
        
        latest = df.iloc[-1]
        
        # แสดงข้อมูลตลาดปัจจุบัน
        print(f"\n📊 CURRENT MARKET CONDITIONS:")
        print(f"   💰 Price: ${latest['close']:.2f}")
        print(f"   📈 RSI: {latest['rsi']:.1f}")
        print(f"   🔴 BB Upper: ${latest['bb_upper']:.2f}")
        print(f"   🟢 BB Lower: ${latest['bb_lower']:.2f}")
        print(f"   📏 ATR: {latest['atr']:.3f}")
        print(f"   📊 EMA10: ${latest['ema_10']:.2f}")
        print(f"   📉 EMA20: ${latest['ema_20']:.2f}")
        print(f"   ⚡ Trend Strength: {latest['trend_strength']:.2f}")
        
        # คำนวณ BB position และ width
        bb_range = latest['bb_upper'] - latest['bb_lower']
        bb_position = (latest['close'] - latest['bb_lower']) / bb_range if bb_range > 0 else 0.5
        bb_width = bb_range / latest['close'] if latest['close'] > 0 else 0
        
        print(f"   📏 BB Position: {bb_position:.3f} (0=lower, 1=upper)")
        print(f"   📐 BB Width: {bb_width:.4f}")
        
        # ตรวจสอบเงื่อนไขแต่ละข้อ
        print(f"\n🎯 BUY SIGNAL CONDITIONS CHECK:")
        buy_conditions = {
            f"BB Position ≤ 0.18": bb_position <= 0.18,
            f"RSI ≤ 30": latest['rsi'] <= 30,
            f"Trend Strength ≥ 0.5": latest['trend_strength'] >= 0.5,
            f"BB Width ≥ 0.001": bb_width >= 0.001,
            f"EMA Uptrend": latest['ema_10'] > latest['ema_20'],
            f"No Strong Trend": latest['trend_strength'] <= trader.strong_trend_threshold
        }
        
        for condition, result in buy_conditions.items():
            status = "✅" if result else "❌"
            print(f"   {status} {condition}: {result}")
        
        print(f"\n🎯 SELL SIGNAL CONDITIONS CHECK:")
        sell_conditions = {
            f"BB Position ≥ 0.82": bb_position >= 0.82,
            f"RSI ≥ 70": latest['rsi'] >= 70,
            f"Trend Strength ≥ 0.5": latest['trend_strength'] >= 0.5,
            f"BB Width ≥ 0.001": bb_width >= 0.001,
            f"EMA Downtrend": latest['ema_10'] < latest['ema_20'],
            f"No Strong Trend": latest['trend_strength'] <= trader.strong_trend_threshold
        }
        
        for condition, result in sell_conditions.items():
            status = "✅" if result else "❌"
            print(f"   {status} {condition}: {result}")
        
        # ตรวจสอบ market conditions
        print(f"\n🔍 MARKET CONDITIONS CHECK:")
        market_ok, market_msg = trader.check_simple_market_conditions()
        print(f"   Market Status: {'✅ OK' if market_ok else '❌ BLOCKED'}")
        print(f"   Message: {market_msg}")
        
        # แนะนำการแก้ไข
        print(f"\n💡 RECOMMENDATIONS:")
        
        all_buy_pass = all(buy_conditions.values())
        all_sell_pass = all(sell_conditions.values())
        
        if not all_buy_pass and not all_sell_pass:
            print("   🔧 Current conditions don't meet signal criteria")
            
            # หาเงื่อนไขที่ใกล้เคียงที่สุด
            if bb_position < 0.5:  # ใกล้ lower band
                print("   📊 Price near lower band - check BUY conditions:")
                if latest['rsi'] > 30:
                    print(f"      • RSI too high: {latest['rsi']:.1f} (need ≤30)")
                if bb_position > 0.18:
                    print(f"      • BB position too high: {bb_position:.3f} (need ≤0.18)")
                if latest['ema_10'] <= latest['ema_20']:
                    print(f"      • Need EMA uptrend: {latest['ema_10']:.2f} vs {latest['ema_20']:.2f}")
            else:  # ใกล้ upper band
                print("   📊 Price near upper band - check SELL conditions:")
                if latest['rsi'] < 70:
                    print(f"      • RSI too low: {latest['rsi']:.1f} (need ≥70)")
                if bb_position < 0.82:
                    print(f"      • BB position too low: {bb_position:.3f} (need ≥0.82)")
                if latest['ema_10'] >= latest['ema_20']:
                    print(f"      • Need EMA downtrend: {latest['ema_10']:.2f} vs {latest['ema_20']:.2f}")
            
            # เสนอการปรับเงื่อนไข
            print(f"\n🔧 SUGGESTED ADJUSTMENTS (for testing):")
            print(f"   • Relax RSI: BUY ≤35, SELL ≥65")
            print(f"   • Relax BB position: BUY ≤0.25, SELL ≥0.75")
            print(f"   • Remove EMA trend requirement temporarily")
            
        elif market_ok:
            print("   ✅ Conditions look good - signal should generate soon")
        else:
            print(f"   ⚠️ Market conditions blocking: {market_msg}")
        
        # ทดสอบสร้างสัญญาณ
        print(f"\n🎯 TESTING SIGNAL GENERATION:")
        signal = trader.generate_bb_zigzag_ai_signal()
        
        if signal:
            print("   ✅ Signal generated!")
            print(f"      Type: {signal['signal']}")
            print(f"      Confidence: {signal['confidence']:.1%}")
            print(f"      Reasons: {', '.join(signal['entry_reasons'])}")
        else:
            print("   ❌ No signal generated")
        
        mt5.shutdown()

    if __name__ == "__main__":
        debug_signal_conditions()
        
except Exception as e:
    print(f"❌ Debug error: {e}")
    import traceback
    traceback.print_exc()
