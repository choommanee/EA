#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Balanced Gold Strategy - Optimized but practical
กลยุทธ์ที่สมดุลระหว่างคุณภาพและความถี่ของสัญญาณ
"""

import pandas as pd
import numpy as np

def run_balanced_strategy():
    """รัน backtest ด้วยกลยุทธ์ที่สมดุล"""
    print("⚖️ BALANCED GOLD STRATEGY BACKTEST")
    print("="*60)
    
    # Load data
    csv_file = 'data-gold/HISTDATA_COM_MT_XAUUSD_M1202503/DAT_MT_XAUUSD_M1_202503.csv'
    print(f'📊 Loading {csv_file}...')
    
    df = pd.read_csv(csv_file, header=None, names=['date', 'time', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert to numeric
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna()
    df = df.tail(3000)  # Last 3000 candles
    print(f'📊 Using {len(df)} candles for backtest')
    
    # Calculate indicators
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
    df['ema_10'] = df['close'].ewm(span=10).mean()
    df['ema_20'] = df['close'].ewm(span=20).mean()
    
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(window=14).mean()
    
    df['momentum'] = df['close'].pct_change(5) * 100
    
    print('🔧 Indicators calculated')
    
    # Analyze signal potential first
    df_clean = df.dropna()
    
    print(f'\n📊 Signal Analysis:')
    print(f'   RSI range: {df_clean["rsi"].min():.1f} - {df_clean["rsi"].max():.1f}')
    print(f'   BB position range: {df_clean["bb_position"].min():.3f} - {df_clean["bb_position"].max():.3f}')
    
    # Count potential signals
    balanced_buy_count = ((df_clean['bb_position'] <= 0.18) & 
                         (df_clean['rsi'] <= 30) & 
                         (df_clean['bb_width'] >= 0.001) & 
                         (df_clean['ema_10'] > df_clean['ema_20'])).sum()
    
    balanced_sell_count = ((df_clean['bb_position'] >= 0.82) & 
                          (df_clean['rsi'] >= 70) & 
                          (df_clean['bb_width'] >= 0.001) & 
                          (df_clean['ema_10'] < df_clean['ema_20'])).sum()
    
    print(f'   Potential BUY signals: {balanced_buy_count}')
    print(f'   Potential SELL signals: {balanced_sell_count}')
    
    # Backtest with balanced conditions
    balance = 10000
    initial_balance = balance
    trades = []
    lot_size = 0.1
    spread_points = 30
    
    for i in range(50, len(df_clean)-20):
        current = df_clean.iloc[i]
        
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
        
        # BALANCED BUY CONDITIONS
        if (bb_pos <= 0.18 and 
            rsi <= 30 and 
            bb_width >= 0.001 and 
            ema_10 > ema_20):
            
            signal = 'BUY'
            confidence = min(0.95, 0.65 + (35 - rsi) / 100 + (0.2 - bb_pos) * 2)
        
        # BALANCED SELL CONDITIONS
        elif (bb_pos >= 0.82 and 
              rsi >= 70 and 
              bb_width >= 0.001 and 
              ema_10 < ema_20):
            
            signal = 'SELL'
            confidence = min(0.95, 0.65 + (rsi - 65) / 100 + (bb_pos - 0.8) * 2)
        
        # Use confidence threshold of 80% (balanced)
        if signal and confidence >= 0.80 and len(trades) < 100:
            
            # Calculate SL/TP
            sl_distance = max(70, atr * 45) / 10000  # Balanced SL
            tp_distance = sl_distance * 1.8  # 1:1.8 risk/reward
            
            entry_price = price
            
            if signal == 'BUY':
                entry_price += spread_points / 10000
                sl_price = entry_price - sl_distance
                tp_price = entry_price + tp_distance
            else:
                entry_price -= spread_points / 10000
                sl_price = entry_price + sl_distance
                tp_price = entry_price - tp_distance
            
            # Simulate trade
            trade_closed = False
            exit_price = None
            exit_reason = None
            
            for j in range(i+1, min(i+21, len(df_clean))):
                future_price = df_clean.iloc[j]['close']
                
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
            
            # Time-based exit if not closed
            if not trade_closed and i+20 < len(df_clean):
                exit_price = df_clean.iloc[i+20]['close']
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
                    'bb_pos': bb_pos
                })
    
    # Results Analysis
    print(f'\n📊 BALANCED STRATEGY RESULTS')
    print('='*60)
    
    if trades:
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['profit'] > 0])
        win_rate = winning_trades / total_trades
        total_profit = balance - initial_balance
        
        profits = [t['profit'] for t in trades if t['profit'] > 0]
        losses = [abs(t['profit']) for t in trades if t['profit'] < 0]
        profit_factor = sum(profits) / sum(losses) if losses else float('inf')
        
        print(f'💰 Initial Balance: ${initial_balance:,.2f}')
        print(f'💰 Final Balance: ${balance:,.2f}')
        print(f'📈 Total Profit: ${total_profit:,.2f} ({(total_profit/initial_balance)*100:.2f}%)')
        print(f'📊 Total Trades: {total_trades}')
        print(f'✅ Winning Trades: {winning_trades}')
        print(f'🎯 Win Rate: {win_rate:.1%}')
        print(f'⚖️ Profit Factor: {profit_factor:.2f}')
        
        if trades:
            print(f'📊 Average Trade: ${total_profit/total_trades:.2f}')
            print(f'🏆 Best Trade: ${max([t["profit"] for t in trades]):.2f}')
            print(f'💔 Worst Trade: ${min([t["profit"] for t in trades]):.2f}')
        
        # Signal breakdown
        buy_trades = [t for t in trades if t['type'] == 'BUY']
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        
        if buy_trades:
            buy_wins = len([t for t in buy_trades if t['profit'] > 0])
            buy_profit = sum([t['profit'] for t in buy_trades])
            print(f'\n🔵 BUY: {len(buy_trades)} trades, {buy_wins/len(buy_trades):.1%} win rate, ${buy_profit:.2f} profit')
        
        if sell_trades:
            sell_wins = len([t for t in sell_trades if t['profit'] > 0])
            sell_profit = sum([t['profit'] for t in sell_trades])
            print(f'🔴 SELL: {len(sell_trades)} trades, {sell_wins/len(sell_trades):.1%} win rate, ${sell_profit:.2f} profit')
        
        # Exit analysis
        sl_exits = len([t for t in trades if t['exit_reason'] == 'SL'])
        tp_exits = len([t for t in trades if t['exit_reason'] == 'TP'])
        time_exits = len([t for t in trades if t['exit_reason'] == 'TIME'])
        
        print(f'\n📊 Exit Analysis:')
        print(f'   TP Hits: {tp_exits} ({tp_exits/total_trades:.1%})')
        print(f'   SL Hits: {sl_exits} ({sl_exits/total_trades:.1%})')
        print(f'   Time Exits: {time_exits} ({time_exits/total_trades:.1%})')
        
        # Performance comparison
        print(f'\n📈 STRATEGY COMPARISON:')
        print(f'   Original: 58.0% win rate, $138 profit (50 trades)')
        print(f'   Balanced: {win_rate:.1%} win rate, ${total_profit:.2f} profit ({total_trades} trades)')
        
        if total_profit > 138:
            improvement = ((total_profit - 138) / 138) * 100
            print(f'   Improvement: +{improvement:.1f}% profit')
        else:
            decline = ((138 - total_profit) / 138) * 100
            print(f'   Change: -{decline:.1f}% profit')
        
        print(f'\n🤖 AI INSIGHTS:')
        avg_conf = np.mean([t['confidence'] for t in trades])
        print(f'   Average Confidence: {avg_conf:.1%}')
        
        winning_rsi = [t['rsi'] for t in trades if t['profit'] > 0]
        losing_rsi = [t['rsi'] for t in trades if t['profit'] <= 0]
        
        if winning_rsi and losing_rsi:
            print(f'   Winning RSI avg: {np.mean(winning_rsi):.1f}')
            print(f'   Losing RSI avg: {np.mean(losing_rsi):.1f}')
        
        print(f'\n💡 FINAL STRATEGY RECOMMENDATIONS:')
        if win_rate >= 0.65:
            print('   ✅ Excellent strategy - ready for live trading')
        elif win_rate >= 0.6:
            print('   ✅ Good strategy - minor tweaks recommended')
        elif win_rate >= 0.55:
            print('   ⚠️ Acceptable strategy - monitor closely')
        else:
            print('   ❌ Strategy needs significant improvement')
        
        print('\n🎯 OPTIMIZED PARAMETERS FOR LIVE TRADING:')
        print('   • BUY: BB position ≤ 0.18, RSI ≤ 30, EMA trend up')
        print('   • SELL: BB position ≥ 0.82, RSI ≥ 70, EMA trend down')
        print('   • Confidence threshold: ≥ 80%')
        print('   • Risk/Reward: 1:1.8')
        print('   • BB width filter: ≥ 0.001 (volatility check)')
        
    else:
        print('❌ No trades executed - conditions too strict')
    
    print('='*60)
    return trades, balance

if __name__ == "__main__":
    run_balanced_strategy()
