#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Gold Test - Minimal backtest
"""

import pandas as pd
import numpy as np
import os

def main():
    print("🥇 SIMPLE GOLD BACKTEST")
    print("="*40)
    
    # Load CSV data
    csv_file = "data-gold/HISTDATA_COM_MT_XAUUSD_M1202503/DAT_MT_XAUUSD_M1_202503.csv"
    
    if not os.path.exists(csv_file):
        print("❌ CSV file not found")
        return
    
    print(f"📊 Loading {csv_file}...")
    
    # Read CSV with proper column names
    df = pd.read_csv(csv_file, header=None, names=[
        'date', 'time', 'open', 'high', 'low', 'close', 'volume'
    ])
    
    print(f"✅ Loaded {len(df)} M1 candles")
    
    # Take sample for quick test
    df_sample = df.tail(1000)  # Last 1000 candles
    
    # Convert to numeric
    for col in ['open', 'high', 'low', 'close']:
        df_sample[col] = pd.to_numeric(df_sample[col], errors='coerce')
    
    df_sample = df_sample.dropna()
    
    print(f"📈 Price range: ${df_sample['low'].min():.2f} - ${df_sample['high'].max():.2f}")
    
    # Simple RSI calculation
    delta = df_sample['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_sample['rsi'] = 100 - (100 / (1 + rs))
    
    # Simple strategy test
    signals = 0
    profitable = 0
    
    for i in range(20, len(df_sample)-5):
        rsi = df_sample.iloc[i]['rsi']
        entry_price = df_sample.iloc[i]['close']
        
        # Simple exit after 5 candles
        exit_price = df_sample.iloc[i+5]['close']
        
        if pd.notna(rsi):
            if rsi < 30:  # Buy signal
                profit = exit_price - entry_price
                signals += 1
                if profit > 0:
                    profitable += 1
            elif rsi > 70:  # Sell signal
                profit = entry_price - exit_price
                signals += 1
                if profit > 0:
                    profitable += 1
    
    if signals > 0:
        win_rate = profitable / signals
        print(f"\n📊 RESULTS:")
        print(f"   Total Signals: {signals}")
        print(f"   Profitable: {profitable}")
        print(f"   Win Rate: {win_rate:.1%}")
        
        if win_rate >= 0.6:
            print("   ✅ Good potential!")
        elif win_rate >= 0.5:
            print("   ⚠️ Moderate potential")
        else:
            print("   ❌ Needs improvement")
    else:
        print("❌ No signals generated")
    
    print("\n✅ Test completed!")
    print("💡 Data is ready for full backtesting system")

if __name__ == "__main__":
    main()
