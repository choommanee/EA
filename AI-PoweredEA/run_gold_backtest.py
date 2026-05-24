#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Backtest Runner - Direct execution
รันการทดสอบ backtest จากข้อมูล Gold ที่มีอยู่
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import sqlite3

def load_gold_data():
    """โหลดข้อมูล Gold จาก CSV files"""
    print("🔍 Loading Gold data...")
    
    # Find all CSV files
    csv_files = []
    data_dir = "data-gold"
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.csv') and 'XAUUSD_M1' in file and not file.startswith('._'):
                csv_files.append(os.path.join(root, file))
    
    print(f"📁 Found {len(csv_files)} CSV files")
    
    if not csv_files:
        return None
    
    # Load first file for testing
    csv_file = csv_files[0]
    print(f"📊 Loading: {os.path.basename(csv_file)}")
    
    df = pd.read_csv(csv_file, header=None, names=[
        'date', 'time', 'open', 'high', 'low', 'close', 'volume'
    ])
    
    # Create timestamp
    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
    
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
    print(f"📅 Period: {m5_data['timestamp'].min()} to {m5_data['timestamp'].max()}")
    
    return m5_data

def calculate_indicators(df):
    """คำนวณ technical indicators"""
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
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
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
    df['ema_separation'] = np.abs(df['ema_10'] - df['ema_20'])
    
    # Momentum
    df['momentum'] = df['close'].pct_change(5) * 100
    
    return df.dropna()

def generate_signal(data, i):
    """สร้างสัญญาณการซื้อขาย"""
    current = data.iloc[i]
    
    # Basic conditions
    rsi = current['rsi']
    bb_pos = current['bb_position']
    trend_strength = current['trend_strength']
    momentum = current['momentum']
    bb_width = current['bb_width']
    
    # Signal conditions based on working_scalping_trader logic
    confidence = 0.5
    signal_type = None
    
    # BUY Signal conditions
    if (bb_pos <= 0.15 and  # Near lower BB
        rsi <= 35 and       # Oversold
        trend_strength >= 0.5 and  # Strong trend
        bb_width >= 0.002 and      # Sufficient volatility
        momentum < -0.1):           # Downward momentum (for reversal)
        
        signal_type = 'BUY'
        confidence = min(0.95, 0.65 + (40 - rsi) / 100 + trend_strength / 5)
    
    # SELL Signal conditions  
    elif (bb_pos >= 0.85 and  # Near upper BB
          rsi >= 65 and       # Overbought
          trend_strength >= 0.5 and  # Strong trend
          bb_width >= 0.002 and      # Sufficient volatility
          momentum > 0.1):            # Upward momentum (for reversal)
        
        signal_type = 'SELL'
        confidence = min(0.95, 0.65 + (rsi - 60) / 100 + trend_strength / 5)
    
    if signal_type and confidence >= 0.75:  # Minimum confidence threshold
        return {
            'signal': signal_type,
            'confidence': confidence,
            'rsi': rsi,
            'bb_position': bb_pos,
            'trend_strength': trend_strength,
            'momentum': momentum
        }
    
    return None

def run_backtest(df, max_trades=50):
    """รัน backtest"""
    print("⚡ Running backtest...")
    
    initial_balance = 10000
    balance = initial_balance
    lot_size = 0.1
    spread_points = 30  # 3 pips spread
    
    trades = []
    open_positions = []
    
    for i in range(50, min(len(df), len(df) - 10)):  # Leave room for exits
        current_price = df.iloc[i]['close']
        current_time = df.iloc[i]['timestamp']
        current_atr = df.iloc[i]['atr']
        
        # Check existing positions for SL/TP
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
                'confidence': pos['confidence'],
                'rsi': pos['rsi'],
                'bb_position': pos['bb_position'],
                'trend_strength': pos['trend_strength']
            })
            open_positions.remove(pos)
        
        # Generate new signals (max 2 positions)
        if len(open_positions) < 2 and len(trades) < max_trades:
            signal = generate_signal(df, i)
            
            if signal:
                entry_price = current_price
                
                # Calculate SL/TP based on ATR
                sl_distance = max(60, current_atr * 40) / 10000  # Min 60 points
                tp_distance = sl_distance * 1.5  # 1:1.5 risk/reward
                
                if signal['signal'] == 'BUY':
                    entry_price += spread_points / 10000  # Add spread
                    sl_price = entry_price - sl_distance
                    tp_price = entry_price + tp_distance
                else:  # SELL
                    entry_price -= spread_points / 10000  # Subtract spread
                    sl_price = entry_price + sl_distance
                    tp_price = entry_price - tp_distance
                
                position = {
                    'entry_time': current_time,
                    'type': signal['signal'],
                    'entry_price': entry_price,
                    'sl': sl_price,
                    'tp': tp_price,
                    'confidence': signal['confidence'],
                    'rsi': signal['rsi'],
                    'bb_position': signal['bb_position'],
                    'trend_strength': signal['trend_strength']
                }
                open_positions.append(position)
    
    return trades, balance

def analyze_results(trades, final_balance):
    """วิเคราะห์ผลลัพธ์"""
    initial_balance = 10000
    
    if not trades:
        print("❌ No trades executed")
        return
    
    print("\n" + "="*60)
    print("📊 GOLD BACKTEST RESULTS")
    print("="*60)
    
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['profit'] > 0])
    win_rate = winning_trades / total_trades
    total_profit = final_balance - initial_balance
    
    profits = [t['profit'] for t in trades if t['profit'] > 0]
    losses = [abs(t['profit']) for t in trades if t['profit'] < 0]
    profit_factor = sum(profits) / sum(losses) if losses else float('inf')
    
    print(f"💰 Initial Balance: ${initial_balance:,.2f}")
    print(f"💰 Final Balance: ${final_balance:,.2f}")
    print(f"📈 Total Profit: ${total_profit:,.2f} ({(total_profit/initial_balance)*100:.2f}%)")
    print(f"📊 Total Trades: {total_trades}")
    print(f"✅ Winning Trades: {winning_trades}")
    print(f"❌ Losing Trades: {total_trades - winning_trades}")
    print(f"🎯 Win Rate: {win_rate:.1%}")
    print(f"⚖️ Profit Factor: {profit_factor:.2f}")
    
    if trades:
        print(f"📊 Average Trade: ${total_profit/total_trades:.2f}")
        print(f"🏆 Best Trade: ${max([t['profit'] for t in trades]):.2f}")
        print(f"💔 Worst Trade: ${min([t['profit'] for t in trades]):.2f}")
    
    # Signal Analysis
    buy_trades = [t for t in trades if t['type'] == 'BUY']
    sell_trades = [t for t in trades if t['type'] == 'SELL']
    
    if buy_trades:
        buy_wins = len([t for t in buy_trades if t['profit'] > 0])
        print(f"\n🔵 BUY Signals: {len(buy_trades)} trades, {buy_wins/len(buy_trades):.1%} win rate")
    
    if sell_trades:
        sell_wins = len([t for t in sell_trades if t['profit'] > 0])
        print(f"🔴 SELL Signals: {len(sell_trades)} trades, {sell_wins/len(sell_trades):.1%} win rate")
    
    # Exit Analysis
    sl_exits = len([t for t in trades if t['exit_reason'] == 'SL'])
    tp_exits = len([t for t in trades if t['exit_reason'] == 'TP'])
    
    print(f"\n📊 Exit Analysis:")
    print(f"   SL Hits: {sl_exits} ({sl_exits/total_trades:.1%})")
    print(f"   TP Hits: {tp_exits} ({tp_exits/total_trades:.1%})")
    
    # AI Insights
    print(f"\n🤖 AI INSIGHTS:")
    
    # Confidence analysis
    high_conf_trades = [t for t in trades if t['confidence'] >= 0.85]
    if high_conf_trades:
        high_conf_wins = len([t for t in high_conf_trades if t['profit'] > 0])
        print(f"   High Confidence (≥85%): {len(high_conf_trades)} trades, {high_conf_wins/len(high_conf_trades):.1%} win rate")
    
    # RSI analysis
    winning_rsi = [t['rsi'] for t in trades if t['profit'] > 0]
    losing_rsi = [t['rsi'] for t in trades if t['profit'] <= 0]
    
    if winning_rsi and losing_rsi:
        print(f"   Winning RSI avg: {np.mean(winning_rsi):.1f}")
        print(f"   Losing RSI avg: {np.mean(losing_rsi):.1f}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if sl_exits > tp_exits:
        print("   • Consider wider SL or stricter entry conditions")
    if win_rate < 0.6:
        print("   • Increase confidence threshold to 85%+")
    print("   • Focus on RSI extremes (<30 for BUY, >70 for SELL)")
    print("   • Ensure BB position <0.2 for BUY, >0.8 for SELL")
    
    print("="*60)

def main():
    """Main execution"""
    print("🥇 GOLD BACKTEST SYSTEM")
    print("="*50)
    
    # Load data
    df = load_gold_data()
    if df is None:
        print("❌ Failed to load data")
        return
    
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Limit data for reasonable execution time
    df = df.tail(2000)  # Last 2000 candles
    print(f"📊 Using {len(df)} candles for backtest")
    
    # Run backtest
    trades, final_balance = run_backtest(df, max_trades=100)
    
    # Analyze results
    analyze_results(trades, final_balance)
    
    print(f"\n✅ Backtest completed successfully!")
    print(f"📈 Ready for live trading optimization")

if __name__ == "__main__":
    main()
