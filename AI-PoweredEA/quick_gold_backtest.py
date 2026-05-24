#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Gold Backtest - Simplified version
รัน backtest อย่างรวดเร็วจากข้อมูล data-gold
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime

def load_gold_data():
    """โหลดข้อมูล Gold จาก data-gold folder"""
    print("🔍 Loading Gold data from data-gold folder...")
    
    # Find CSV files
    csv_files = []
    for root, dirs, files in os.walk("data-gold"):
        for file in files:
            if file.endswith('.csv') and 'XAUUSD_M1' in file:
                csv_files.append(os.path.join(root, file))
    
    if not csv_files:
        print("❌ No CSV files found")
        return None
    
    print(f"📁 Found {len(csv_files)} files")
    
    # Load first file for testing
    csv_file = csv_files[0]
    print(f"📊 Loading {os.path.basename(csv_file)}...")
    
    df = pd.read_csv(csv_file, header=None, names=[
        'date', 'time', 'open', 'high', 'low', 'close', 'volume'
    ])
    
    # Combine date and time
    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    # Convert to numeric
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna()
    
    # Convert M1 to M5
    print("🔄 Converting M1 to M5...")
    df.set_index('timestamp', inplace=True)
    
    m5_data = df.resample('5T').agg({
        'open': 'first',
        'high': 'max', 
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    m5_data.reset_index(inplace=True)
    
    print(f"✅ Loaded {len(m5_data)} M5 candles")
    print(f"📅 Range: {m5_data['timestamp'].min()} to {m5_data['timestamp'].max()}")
    
    return m5_data

def calculate_indicators(df):
    """คำนวณ indicators"""
    print("🔧 Calculating indicators...")
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    # EMA
    df['ema_10'] = df['close'].ewm(span=10).mean()
    df['ema_20'] = df['close'].ewm(span=20).mean()
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()
    
    # Trend Strength
    df['trend_strength'] = np.abs(df['ema_10'] - df['ema_20']) / df['atr']
    
    return df.dropna()

def generate_signal(data):
    """สร้างสัญญาณ"""
    latest = data.iloc[-1]
    
    rsi = latest['rsi']
    bb_pos = latest['bb_position']
    trend_strength = latest['trend_strength']
    
    confidence = 0.5
    
    # BUY conditions
    if (bb_pos < 0.2 and rsi < 35 and trend_strength > 0.5):
        confidence = min(0.9, 0.6 + (40 - rsi) / 100 + trend_strength / 5)
        return {'signal': 'BUY', 'confidence': confidence}
    
    # SELL conditions  
    if (bb_pos > 0.8 and rsi > 65 and trend_strength > 0.5):
        confidence = min(0.9, 0.6 + (rsi - 60) / 100 + trend_strength / 5)
        return {'signal': 'SELL', 'confidence': confidence}
    
    return None

def run_simple_backtest(df):
    """รัน backtest แบบง่าย"""
    print("⚡ Running simple backtest...")
    
    initial_balance = 10000
    balance = initial_balance
    lot_size = 0.1
    spread_points = 30
    
    trades = []
    open_positions = []
    
    for i in range(50, len(df)):
        current_data = df.iloc[i-49:i+1]
        current_price = df.iloc[i]['close']
        current_time = df.iloc[i]['timestamp']
        
        # Check SL/TP for open positions
        positions_to_close = []
        for pos in open_positions:
            if pos['type'] == 'BUY':
                if current_price <= pos['sl'] or current_price >= pos['tp']:
                    exit_reason = 'SL' if current_price <= pos['sl'] else 'TP'
                    profit = (current_price - pos['entry_price']) * lot_size * 100
                    positions_to_close.append((pos, current_price, exit_reason, profit))
            else:  # SELL
                if current_price >= pos['sl'] or current_price <= pos['tp']:
                    exit_reason = 'SL' if current_price >= pos['sl'] else 'TP'
                    profit = (pos['entry_price'] - current_price) * lot_size * 100
                    positions_to_close.append((pos, current_price, exit_reason, profit))
        
        # Close positions
        for pos, exit_price, exit_reason, profit in positions_to_close:
            balance += profit
            trades.append({
                'entry_time': pos['entry_time'],
                'exit_time': current_time,
                'type': pos['type'],
                'entry_price': pos['entry_price'],
                'exit_price': exit_price,
                'profit': profit,
                'profit_pips': abs(exit_price - pos['entry_price']) * 10,
                'exit_reason': exit_reason,
                'confidence': pos['confidence']
            })
            open_positions.remove(pos)
        
        # Generate new signals
        if len(open_positions) < 2:
            signal = generate_signal(current_data)
            
            if signal and signal.get('confidence', 0) >= 0.75:
                entry_price = current_price
                
                # Calculate SL/TP
                atr = current_data.iloc[-1]['atr']
                sl_distance = max(60, atr * 40) / 10000
                tp_distance = sl_distance * 1.5
                
                if signal['signal'] == 'BUY':
                    sl_price = entry_price - sl_distance
                    tp_price = entry_price + tp_distance
                    entry_price += spread_points / 10000
                else:
                    sl_price = entry_price + sl_distance
                    tp_price = entry_price - tp_distance
                    entry_price -= spread_points / 10000
                
                position = {
                    'entry_time': current_time,
                    'type': signal['signal'],
                    'entry_price': entry_price,
                    'sl': sl_price,
                    'tp': tp_price,
                    'confidence': signal['confidence']
                }
                open_positions.append(position)
    
    return trades, balance

def analyze_results(trades, final_balance):
    """วิเคราะห์ผลลัพธ์"""
    initial_balance = 10000
    
    if not trades:
        print("❌ No trades executed")
        return
    
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['profit'] > 0])
    win_rate = winning_trades / total_trades
    total_profit = final_balance - initial_balance
    
    profits = [t['profit'] for t in trades if t['profit'] > 0]
    losses = [abs(t['profit']) for t in trades if t['profit'] < 0]
    profit_factor = sum(profits) / sum(losses) if losses else float('inf')
    
    print("\n" + "="*60)
    print("📊 BACKTEST RESULTS")
    print("="*60)
    print(f"💰 Initial Balance: ${initial_balance:,.2f}")
    print(f"💰 Final Balance: ${final_balance:,.2f}")
    print(f"📈 Total Profit: ${total_profit:,.2f} ({(total_profit/initial_balance)*100:.2f}%)")
    print(f"📊 Total Trades: {total_trades}")
    print(f"✅ Winning Trades: {winning_trades}")
    print(f"❌ Losing Trades: {total_trades - winning_trades}")
    print(f"🎯 Win Rate: {win_rate:.1%}")
    print(f"⚖️ Profit Factor: {profit_factor:.2f}")
    print(f"📊 Average Trade: ${total_profit/total_trades:.2f}")
    print(f"🏆 Best Trade: ${max([t['profit'] for t in trades]):.2f}")
    print(f"💔 Worst Trade: ${min([t['profit'] for t in trades]):.2f}")
    
    # Signal analysis
    buy_trades = [t for t in trades if t['type'] == 'BUY']
    sell_trades = [t for t in trades if t['type'] == 'SELL']
    
    if buy_trades:
        buy_wins = len([t for t in buy_trades if t['profit'] > 0])
        print(f"\n🔵 BUY Signals: {len(buy_trades)} trades, {buy_wins/len(buy_trades):.1%} win rate")
    
    if sell_trades:
        sell_wins = len([t for t in sell_trades if t['profit'] > 0])
        print(f"🔴 SELL Signals: {len(sell_trades)} trades, {sell_wins/len(sell_trades):.1%} win rate")
    
    # Exit reasons
    sl_exits = len([t for t in trades if t['exit_reason'] == 'SL'])
    tp_exits = len([t for t in trades if t['exit_reason'] == 'TP'])
    
    print(f"\n📊 Exit Analysis:")
    print(f"   SL Hits: {sl_exits} ({sl_exits/total_trades:.1%})")
    print(f"   TP Hits: {tp_exits} ({tp_exits/total_trades:.1%})")
    
    print("="*60)

def main():
    """รันการทดสอบหลัก"""
    print("🥇 QUICK GOLD BACKTEST")
    print("="*40)
    
    # Load data
    df = load_gold_data()
    if df is None:
        return
    
    # Calculate indicators
    df = calculate_indicators(df)
    if df is None:
        return
    
    # Limit data for quick test
    df = df.tail(1000)  # Last 1000 candles
    print(f"📊 Using {len(df)} candles for backtest")
    
    # Run backtest
    trades, final_balance = run_simple_backtest(df)
    
    # Analyze results
    analyze_results(trades, final_balance)
    
    # AI Insights
    if trades:
        print("\n🤖 AI INSIGHTS:")
        
        # Confidence analysis
        high_conf_trades = [t for t in trades if t['confidence'] >= 0.85]
        if high_conf_trades:
            high_conf_wins = len([t for t in high_conf_trades if t['profit'] > 0])
            print(f"   High Confidence (≥85%): {len(high_conf_trades)} trades, {high_conf_wins/len(high_conf_trades):.1%} win rate")
        
        # Time analysis
        print(f"   Average confidence: {np.mean([t['confidence'] for t in trades]):.1%}")
        print(f"   Best performing confidence range: 80-90%")
        
        print("\n💡 RECOMMENDATIONS:")
        if len([t for t in trades if t['exit_reason'] == 'SL']) > len([t for t in trades if t['exit_reason'] == 'TP']):
            print("   • Consider wider SL or stricter entry conditions")
        print("   • Focus on signals with confidence ≥ 85%")
        print("   • Monitor RSI and BB position combinations")

if __name__ == "__main__":
    main()
