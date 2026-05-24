#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Gold Data Loading
ทดสอบการโหลดข้อมูล Gold
"""

import pandas as pd
import numpy as np
import os

def test_data_loading():
    """ทดสอบการโหลดข้อมูล"""
    print("🧪 Testing Gold Data Loading...")
    
    # Check if data-gold exists
    if not os.path.exists('data-gold'):
        print("❌ data-gold folder not found")
        return False
    
    # Find CSV files
    csv_files = []
    for root, dirs, files in os.walk('data-gold'):
        for file in files:
            if file.endswith('.csv') and 'XAUUSD' in file and not file.startswith('._'):
                csv_files.append(os.path.join(root, file))
    
    print(f"📁 Found {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"   - {f}")
    
    if not csv_files:
        print("❌ No valid CSV files found")
        return False
    
    # Test loading first file
    csv_file = csv_files[0]
    print(f"\n📊 Testing {csv_file}...")
    
    try:
        # Read sample data
        df = pd.read_csv(csv_file, nrows=10, header=None)
        print(f"✅ File readable - {len(df)} sample rows")
        print("Sample data:")
        print(df.head(3))
        
        # Test full load with proper columns
        df_full = pd.read_csv(csv_file, header=None, names=[
            'date', 'time', 'open', 'high', 'low', 'close', 'volume'
        ])
        
        print(f"\n📈 Full file: {len(df_full)} rows")
        print(f"Date range: {df_full['date'].min()} to {df_full['date'].max()}")
        
        # Test timestamp creation
        df_full['timestamp'] = pd.to_datetime(df_full['date'] + ' ' + df_full['time'])
        print(f"✅ Timestamps created successfully")
        
        # Test numeric conversion
        for col in ['open', 'high', 'low', 'close']:
            df_full[col] = pd.to_numeric(df_full[col], errors='coerce')
        
        df_clean = df_full.dropna()
        print(f"📊 Clean data: {len(df_clean)} rows")
        
        # Test M5 conversion
        df_clean.set_index('timestamp', inplace=True)
        m5_data = df_clean.resample('5T').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min', 
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        print(f"🔄 M5 conversion: {len(m5_data)} candles")
        print(f"Price range: ${m5_data['low'].min():.2f} - ${m5_data['high'].max():.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return False

def run_mini_backtest():
    """รัน backtest ขนาดเล็ก"""
    print("\n⚡ Running Mini Backtest...")
    
    # Load data
    csv_file = None
    for root, dirs, files in os.walk('data-gold'):
        for file in files:
            if file.endswith('.csv') and 'XAUUSD' in file and not file.startswith('._'):
                csv_file = os.path.join(root, file)
                break
        if csv_file:
            break
    
    if not csv_file:
        print("❌ No CSV file found")
        return
    
    # Load and process data
    df = pd.read_csv(csv_file, header=None, names=[
        'date', 'time', 'open', 'high', 'low', 'close', 'volume'
    ])
    
    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna()
    
    # Convert to M5
    df.set_index('timestamp', inplace=True)
    m5_data = df.resample('5T').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    m5_data.reset_index(inplace=True)
    
    # Take last 500 candles for quick test
    m5_data = m5_data.tail(500)
    
    print(f"📊 Using {len(m5_data)} M5 candles")
    print(f"📅 Period: {m5_data['timestamp'].iloc[0]} to {m5_data['timestamp'].iloc[-1]}")
    
    # Calculate simple RSI
    delta = m5_data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    m5_data['rsi'] = 100 - (100 / (1 + rs))
    
    # Simple strategy: Buy when RSI < 30, Sell when RSI > 70
    signals = 0
    profitable_signals = 0
    
    for i in range(20, len(m5_data)-1):  # Leave room for exit
        current_rsi = m5_data.iloc[i]['rsi']
        entry_price = m5_data.iloc[i]['close']
        exit_price = m5_data.iloc[i+1]['close']  # Exit next candle
        
        signal_type = None
        profit = 0
        
        if current_rsi < 30:  # Buy signal
            signal_type = 'BUY'
            profit = (exit_price - entry_price) * 100  # Simplified profit calc
            signals += 1
        elif current_rsi > 70:  # Sell signal
            signal_type = 'SELL' 
            profit = (entry_price - exit_price) * 100
            signals += 1
        
        if signal_type and profit > 0:
            profitable_signals += 1
    
    if signals > 0:
        win_rate = profitable_signals / signals
        print(f"🎯 Simple RSI Strategy Results:")
        print(f"   Total Signals: {signals}")
        print(f"   Profitable Signals: {profitable_signals}")
        print(f"   Win Rate: {win_rate:.1%}")
        
        if win_rate >= 0.6:
            print("   ✅ Good potential - strategy shows promise")
        elif win_rate >= 0.5:
            print("   ⚠️ Moderate potential - needs optimization")
        else:
            print("   ❌ Poor performance - major improvements needed")
    else:
        print("❌ No signals generated")

def main():
    """Main function"""
    print("🥇 GOLD DATA TESTING SYSTEM")
    print("="*50)
    
    # Test data loading
    if test_data_loading():
        print("✅ Data loading successful")
        
        # Run mini backtest
        run_mini_backtest()
        
        print("\n💡 NEXT STEPS:")
        print("   1. Data is ready for full backtesting")
        print("   2. Can implement more sophisticated strategies")
        print("   3. AI learning system can be trained on this data")
        print("   4. Ready for comprehensive analysis")
        
    else:
        print("❌ Data loading failed")
    
    print("="*50)

if __name__ == "__main__":
    main()
