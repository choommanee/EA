#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized Gold Strategy - Based on backtest results
กลยุทธ์ที่ปรับปรุงจากผลการทดสอบ
"""

import pandas as pd
import numpy as np
import os

def optimized_backtest():
    """รัน backtest ด้วยกลยุทธ์ที่ปรับปรุงแล้ว"""
    print("🚀 OPTIMIZED GOLD STRATEGY BACKTEST")
    print("="*60)
    
    # Load data
    csv_file = 'data-gold/HISTDATA_COM_MT_XAUUSD_M1202503/DAT_MT_XAUUSD_M1_202503.csv'
    print(f'📊 Loading {csv_file}...')
    
    df = pd.read_csv(csv_file, header=None, names=['date', 'time', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert to numeric
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna()
    
    # Use last 3000 candles for more comprehensive test
    df = df.tail(3000)
    print(f'📊 Using {len(df)} candles for optimized backtest')
    
    # Calculate indicators
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
    
    # EMA for trend
    df['ema_10'] = df['close'].ewm(span=10).mean()
    df['ema_20'] = df['close'].ewm(span=20).mean()
    
    # ATR for volatility
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()
    
    # Momentum
    df['momentum'] = df['close'].pct_change(5) * 100
    
    print("🔧 Indicators calculated")
    
    # Optimized backtest parameters
    balance = 10000
    initial_balance = balance
    trades = []
    lot_size = 0.1
    spread_points = 30  # 3 pips
    
    # OPTIMIZED SIGNAL CONDITIONS based on backtest results
    for i in range(50, len(df)-20):  # Leave room for exits
        current = df.iloc[i]
        
        if pd.isna(current['rsi']) or pd.isna(current['bb_position']):
            continue
            
        rsi = current['rsi']
        bb_pos = current['bb_position']
        bb_width = current['bb_width']
        price = current['close']
        atr = current['atr']
        momentum = current['momentum']
        ema_10 = current['ema_10']
        ema_20 = current['ema_20']
        
        signal = None
        confidence = 0.5
        
        # OPTIMIZED BUY CONDITIONS (Based on 60.9% win rate)
        if (bb_pos <= 0.15 and          # More extreme BB position
            rsi <= 25 and              # More extreme RSI (was 35)
            bb_width >= 0.002 and      # Sufficient volatility
            momentum < -0.2 and        # Strong downward momentum
            ema_10 > ema_20):          # Uptrend bias
            
            signal = 'BUY'
            confidence = min(0.95, 0.70 + (30 - rsi) / 100 + (0.15 - bb_pos) * 2)
        
        # OPTIMIZED SELL CONDITIONS (Stricter due to lower win rate)
        elif (bb_pos >= 0.85 and        # More extreme BB position
              rsi >= 75 and            # More extreme RSI (was 65)
              bb_width >= 0.002 and    # Sufficient volatility
              momentum > 0.2 and       # Strong upward momentum
              ema_10 < ema_20):        # Downtrend bias
            
            signal = 'SELL'
            confidence = min(0.95, 0.70 + (rsi - 70) / 100 + (bb_pos - 0.85) * 2)
        
        # Higher confidence threshold based on results
        if signal and confidence >= 0.85 and len(trades) < 100:
            
            # Dynamic SL/TP based on ATR
            sl_distance = max(80, atr * 50) / 10000  # Wider SL
            tp_distance = sl_distance * 2.0  # Better risk/reward (1:2)
            
            entry_price = price
            
            if signal == 'BUY':
                entry_price += spread_points / 10000
                sl_price = entry_price - sl_distance
                tp_price = entry_price + tp_distance
            else:
                entry_price -= spread_points / 10000
                sl_price = entry_price + sl_distance
                tp_price = entry_price - tp_distance
            
            # Simulate trade with proper SL/TP
            trade_closed = False
            exit_price = None
            exit_reason = None
            
            # Check next 20 candles for SL/TP
            for j in range(i+1, min(i+21, len(df))):
                future_price = df.iloc[j]['close']
                
                if signal == 'BUY':
                    if future_price <= sl_price:
                        exit_price = sl_price
                        exit_reason = 'SL'
                        trade_closed = True
                        break
                    elif future_price >= tp_price:
                        exit_price = tp_price
                        exit_reason = 'TP'
                        trade_closed = True
                        break
                else:  # SELL
                    if future_price >= sl_price:
                        exit_price = sl_price
                        exit_reason = 'SL'
                        trade_closed = True
                        break
                    elif future_price <= tp_price:
                        exit_price = tp_price
                        exit_reason = 'TP'
                        trade_closed = True
                        break
            
            # If not closed by SL/TP, close at market after 20 candles
            if not trade_closed and i+20 < len(df):
                exit_price = df.iloc[i+20]['close']
                exit_reason = 'TIME'
            
            if exit_price:
                if signal == 'BUY':
                    profit = (exit_price - entry_price) * lot_size * 100
                else:
                    profit = (entry_price - exit_price) * lot_size * 100
                
                balance += profit
                
                trades.append({
                    'type': signal,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit': profit,
                    'profit_pips': abs(exit_price - entry_price) * 10,
                    'exit_reason': exit_reason,
                    'confidence': confidence,
                    'rsi': rsi,
                    'bb_pos': bb_pos,
                    'momentum': momentum
                })
    
    # Results Analysis
    print(f"\n📊 OPTIMIZED BACKTEST RESULTS")
    print("="*60)
    
    if trades:
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['profit'] > 0])
        win_rate = winning_trades / total_trades
        total_profit = balance - initial_balance
        
        profits = [t['profit'] for t in trades if t['profit'] > 0]
        losses = [abs(t['profit']) for t in trades if t['profit'] < 0]
        profit_factor = sum(profits) / sum(losses) if losses else float('inf')
        
        print(f"💰 Initial Balance: ${initial_balance:,.2f}")
        print(f"💰 Final Balance: ${balance:,.2f}")
        print(f"📈 Total Profit: ${total_profit:,.2f} ({(total_profit/initial_balance)*100:.2f}%)")
        print(f"📊 Total Trades: {total_trades}")
        print(f"✅ Winning Trades: {winning_trades}")
        print(f"🎯 Win Rate: {win_rate:.1%}")
        print(f"⚖️ Profit Factor: {profit_factor:.2f}")
        
        if trades:
            print(f"📊 Average Trade: ${total_profit/total_trades:.2f}")
            print(f"🏆 Best Trade: ${max([t['profit'] for t in trades]):.2f}")
            print(f"💔 Worst Trade: ${min([t['profit'] for t in trades]):.2f}")
        
        # Signal breakdown
        buy_trades = [t for t in trades if t['type'] == 'BUY']
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        
        if buy_trades:
            buy_wins = len([t for t in buy_trades if t['profit'] > 0])
            buy_profit = sum([t['profit'] for t in buy_trades])
            print(f"\n🔵 BUY Signals: {len(buy_trades)} trades, {buy_wins/len(buy_trades):.1%} win rate, ${buy_profit:.2f} profit")
        
        if sell_trades:
            sell_wins = len([t for t in sell_trades if t['profit'] > 0])
            sell_profit = sum([t['profit'] for t in sell_trades])
            print(f"🔴 SELL Signals: {len(sell_trades)} trades, {sell_wins/len(sell_trades):.1%} win rate, ${sell_profit:.2f} profit")
        
        # Exit analysis
        sl_exits = len([t for t in trades if t['exit_reason'] == 'SL'])
        tp_exits = len([t for t in trades if t['exit_reason'] == 'TP'])
        time_exits = len([t for t in trades if t['exit_reason'] == 'TIME'])
        
        print(f"\n📊 Exit Analysis:")
        print(f"   TP Hits: {tp_exits} ({tp_exits/total_trades:.1%})")
        print(f"   SL Hits: {sl_exits} ({sl_exits/total_trades:.1%})")
        print(f"   Time Exits: {time_exits} ({time_exits/total_trades:.1%})")
        
        # Performance comparison
        print(f"\n📈 PERFORMANCE COMPARISON:")
        print(f"   Original Strategy: 58.0% win rate, $138 profit")
        print(f"   Optimized Strategy: {win_rate:.1%} win rate, ${total_profit:.2f} profit")
        
        improvement = ((total_profit - 138) / 138) * 100 if total_profit > 0 else -100
        print(f"   Improvement: {improvement:+.1f}%")
        
        print(f"\n🤖 AI OPTIMIZATION INSIGHTS:")
        avg_conf = np.mean([t['confidence'] for t in trades])
        print(f"   Average Confidence: {avg_conf:.1%}")
        
        winning_rsi = [t['rsi'] for t in trades if t['profit'] > 0]
        losing_rsi = [t['rsi'] for t in trades if t['profit'] <= 0]
        
        if winning_rsi and losing_rsi:
            print(f"   Winning RSI avg: {np.mean(winning_rsi):.1f}")
            print(f"   Losing RSI avg: {np.mean(losing_rsi):.1f}")
        
        print(f"\n💡 FINAL RECOMMENDATIONS:")
        if win_rate >= 0.65:
            print("   ✅ Optimized strategy shows excellent potential")
        elif win_rate >= 0.6:
            print("   ✅ Good improvement achieved")
        else:
            print("   ⚠️ Further optimization needed")
        
        print("   • Use extreme RSI levels: <25 for BUY, >75 for SELL")
        print("   • Maintain BB position: <0.15 for BUY, >0.85 for SELL")
        print("   • Keep confidence threshold ≥85%")
        print("   • Use 1:2 risk/reward ratio")
        print("   • Focus on BUY signals (historically better performance)")
        
    else:
        print("❌ No trades executed with optimized parameters")
    
    print("="*60)
    return trades, balance

if __name__ == "__main__":
    optimized_backtest()
