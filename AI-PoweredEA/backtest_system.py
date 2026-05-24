#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtesting System for Gold Scalping Trader
ระบบ backtest และ AI learning สำหรับปรับปรุงจุดเข้า
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import MetaTrader5 as mt5

class BacktestSystem:
    def __init__(self, symbol="GOLDm#"):
        self.symbol = symbol
        self.db_path = "Data/backtest_results.db"
        self.initial_balance = 10000
        self.lot_size = 0.1
        self.spread_points = 30
        
        # AI Learning
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
        self.setup_databases()
    
    def setup_databases(self):
        """สร้าง database tables สำหรับ backtest"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    open REAL, high REAL, low REAL, close REAL,
                    volume INTEGER, timeframe TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_time DATETIME, exit_time DATETIME,
                    signal_type TEXT, entry_price REAL, exit_price REAL,
                    sl_price REAL, tp_price REAL, lot_size REAL,
                    profit_loss REAL, profit_pips REAL, confidence REAL,
                    exit_reason TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_learning_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME, signal_type TEXT, confidence REAL,
                    rsi REAL, macd REAL, bb_position REAL, trend_strength REAL,
                    momentum REAL, atr REAL, ema_10 REAL, ema_20 REAL,
                    outcome INTEGER, profit_pips REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Backtest databases initialized")
            
        except Exception as e:
            print(f"❌ Database setup error: {e}")
    
    def collect_historical_data(self, days=30):
        """เก็บข้อมูลประวัติศาสตร์จาก MT5"""
        try:
            if not mt5.initialize():
                print("❌ MT5 initialization failed")
                return False
            
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            rates_m5 = mt5.copy_rates_range(self.symbol, mt5.TIMEFRAME_M5, start_time, end_time)
            if rates_m5 is None:
                print("❌ Failed to get M5 data")
                return False
            
            conn = sqlite3.connect(self.db_path)
            for rate in rates_m5:
                timestamp = datetime.fromtimestamp(rate['time'])
                conn.execute('''
                    INSERT OR REPLACE INTO historical_data 
                    (timestamp, open, high, low, close, volume, timeframe)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (timestamp, rate['open'], rate['high'], rate['low'], 
                     rate['close'], rate['tick_volume'], 'M5'))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Collected {len(rates_m5)} M5 candles")
            mt5.shutdown()
            return True
            
        except Exception as e:
            print(f"❌ Data collection error: {e}")
            return False
    
    def load_historical_data(self, timeframe='M5', limit=5000):
        """โหลดข้อมูลประวัติศาสตร์จาก database"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data 
                WHERE timeframe = ?
                ORDER BY timestamp DESC LIMIT ?
            '''
            df = pd.read_sql_query(query, conn, params=(timeframe, limit))
            conn.close()
            
            if df.empty:
                print(f"❌ No {timeframe} data found")
                return None
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            print(f"✅ Loaded {len(df)} {timeframe} candles")
            return df
            
        except Exception as e:
            print(f"❌ Data loading error: {e}")
            return None
    
    def calculate_indicators(self, df):
        """คำนวณ indicators สำหรับ backtest"""
        try:
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            
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
            df['momentum'] = df['close'].pct_change(periods=5) * 100
            
            return df.dropna()
            
        except Exception as e:
            print(f"❌ Indicator calculation error: {e}")
            return None
    
    def generate_simple_signal(self, data):
        """สร้างสัญญาณง่ายๆ สำหรับ backtest"""
        try:
            latest = data.iloc[-1]
            
            # BB + RSI strategy
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
            
        except Exception as e:
            return None
    
    def run_backtest(self, df, start_date=None, end_date=None):
        """รัน backtest บนข้อมูลประวัติศาสตร์"""
        try:
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
            
            print(f"🔄 Running backtest on {len(df)} candles...")
            
            balance = self.initial_balance
            open_positions = []
            trades = []
            
            for i in range(50, len(df)):
                current_time = df.iloc[i]['timestamp']
                current_data = df.iloc[i-49:i+1]
                
                # Check existing positions for SL/TP
                positions_to_close = []
                for pos in open_positions:
                    current_price = df.iloc[i]['close']
                    
                    if pos['type'] == 'BUY':
                        if current_price <= pos['sl'] or current_price >= pos['tp']:
                            exit_reason = 'SL' if current_price <= pos['sl'] else 'TP'
                            profit = (current_price - pos['entry_price']) * pos['lot_size'] * 100
                            positions_to_close.append((pos, current_price, exit_reason, profit))
                    else:  # SELL
                        if current_price >= pos['sl'] or current_price <= pos['tp']:
                            exit_reason = 'SL' if current_price >= pos['sl'] else 'TP'
                            profit = (pos['entry_price'] - current_price) * pos['lot_size'] * 100
                            positions_to_close.append((pos, current_price, exit_reason, profit))
                
                # Close positions
                for pos, exit_price, exit_reason, profit in positions_to_close:
                    balance += profit
                    
                    trade = {
                        'entry_time': pos['entry_time'],
                        'exit_time': current_time,
                        'type': pos['type'],
                        'entry_price': pos['entry_price'],
                        'exit_price': exit_price,
                        'sl': pos['sl'],
                        'tp': pos['tp'],
                        'lot_size': pos['lot_size'],
                        'profit': profit,
                        'profit_pips': abs(exit_price - pos['entry_price']) * 10,
                        'exit_reason': exit_reason,
                        'confidence': pos['confidence']
                    }
                    trades.append(trade)
                    open_positions.remove(pos)
                    
                    # Store AI learning data
                    self.store_ai_learning_data(pos, trade, current_data.iloc[-1])
                
                # Generate new signals
                if len(open_positions) < 2:
                    signal = self.generate_simple_signal(current_data)
                    
                    if signal and signal.get('confidence', 0) >= 0.75:
                        entry_price = df.iloc[i]['close']
                        
                        # Calculate SL/TP
                        atr = current_data.iloc[-1]['atr']
                        sl_distance = max(60, atr * 40) / 10000
                        tp_distance = sl_distance * 1.5
                        
                        if signal['signal'] == 'BUY':
                            sl_price = entry_price - sl_distance
                            tp_price = entry_price + tp_distance
                            entry_price += self.spread_points / 10000
                        else:
                            sl_price = entry_price + sl_distance
                            tp_price = entry_price - tp_distance
                            entry_price -= self.spread_points / 10000
                        
                        position = {
                            'entry_time': current_time,
                            'type': signal['signal'],
                            'entry_price': entry_price,
                            'sl': sl_price,
                            'tp': tp_price,
                            'lot_size': self.lot_size,
                            'confidence': signal['confidence']
                        }
                        open_positions.append(position)
            
            # Calculate performance
            performance = self.calculate_performance(trades, balance)
            self.store_backtest_results(trades, performance, df.iloc[0]['timestamp'], df.iloc[-1]['timestamp'])
            
            return trades, performance
            
        except Exception as e:
            print(f"❌ Backtest error: {e}")
            return [], {}
    
    def store_ai_learning_data(self, position, trade, market_data):
        """เก็บข้อมูลสำหรับ AI learning"""
        try:
            conn = sqlite3.connect(self.db_path)
            outcome = 1 if trade['profit'] > 0 else 0
            
            conn.execute('''
                INSERT INTO ai_learning_data 
                (timestamp, signal_type, confidence, rsi, macd, bb_position, 
                 trend_strength, momentum, atr, ema_10, ema_20, outcome, profit_pips)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position['entry_time'].strftime('%Y-%m-%d %H:%M:%S'), position['type'], position['confidence'],
                market_data.get('rsi', 0), market_data.get('macd', 0), market_data.get('bb_position', 0),
                market_data.get('trend_strength', 0), market_data.get('momentum', 0), market_data.get('atr', 0),
                market_data.get('ema_10', 0), market_data.get('ema_20', 0),
                outcome, trade['profit_pips']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ AI learning data storage error: {e}")
    
    def calculate_performance(self, trades, final_balance):
        """คำนวณ performance metrics"""
        try:
            if not trades:
                return {}
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t['profit'] > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            total_profit = final_balance - self.initial_balance
            
            profits = [t['profit'] for t in trades if t['profit'] > 0]
            losses = [abs(t['profit']) for t in trades if t['profit'] < 0]
            profit_factor = sum(profits) / sum(losses) if losses else float('inf')
            
            performance = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'total_profit_pct': (total_profit / self.initial_balance) * 100,
                'profit_factor': profit_factor,
                'avg_trade': total_profit / total_trades if total_trades > 0 else 0,
                'best_trade': max([t['profit'] for t in trades]) if trades else 0,
                'worst_trade': min([t['profit'] for t in trades]) if trades else 0,
                'final_balance': final_balance
            }
            
            return performance
            
        except Exception as e:
            print(f"❌ Performance calculation error: {e}")
            return {}
    
    def store_backtest_results(self, trades, performance, start_date, end_date):
        """เก็บผลลัพธ์ backtest"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            for trade in trades:
                conn.execute('''
                    INSERT INTO backtest_trades 
                    (entry_time, exit_time, signal_type, entry_price, exit_price, 
                     sl_price, tp_price, lot_size, profit_loss, profit_pips, 
                     confidence, exit_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade['entry_time'].strftime('%Y-%m-%d %H:%M:%S'), 
                    trade['exit_time'].strftime('%Y-%m-%d %H:%M:%S'), 
                    trade['type'], trade['entry_price'], trade['exit_price'], 
                    trade['sl'], trade['tp'], trade['lot_size'], trade['profit'], 
                    trade['profit_pips'], trade['confidence'], trade['exit_reason']
                ))
            
            conn.commit()
            conn.close()
            print("✅ Backtest results stored")
            
        except Exception as e:
            print(f"❌ Results storage error: {e}")
    
    def train_ai_model(self):
        """ฝึก AI model จากข้อมูล backtest"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT rsi, macd, bb_position, trend_strength, momentum, atr, 
                       ema_10, ema_20, confidence, outcome
                FROM ai_learning_data 
                WHERE rsi IS NOT NULL AND outcome IS NOT NULL
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) < 50:
                print("❌ Not enough data for AI training")
                return False
            
            feature_columns = ['rsi', 'macd', 'bb_position', 'trend_strength', 
                             'momentum', 'atr', 'ema_10', 'ema_20', 'confidence']
            
            X = df[feature_columns].values
            y = df['outcome'].values
            X = np.nan_to_num(X)
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            self.model.fit(X_train_scaled, y_train)
            
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            print(f"✅ AI Model trained - Accuracy: {accuracy:.2%}")
            print(f"📊 Training data: {len(X_train)} samples")
            
            # Feature importance
            feature_importance = self.model.feature_importances_
            for i, feature in enumerate(feature_columns):
                print(f"   {feature}: {feature_importance[i]:.3f}")
            
            return True
            
        except Exception as e:
            print(f"❌ AI training error: {e}")
            return False
    
    def generate_ai_insights(self):
        """สร้าง insights จาก AI analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT 
                    signal_type,
                    AVG(CASE WHEN outcome = 1 THEN rsi END) as win_avg_rsi,
                    AVG(CASE WHEN outcome = 0 THEN rsi END) as loss_avg_rsi,
                    AVG(CASE WHEN outcome = 1 THEN bb_position END) as win_avg_bb,
                    AVG(CASE WHEN outcome = 0 THEN bb_position END) as loss_avg_bb,
                    COUNT(*) as total_signals,
                    SUM(outcome) as winning_signals
                FROM ai_learning_data 
                GROUP BY signal_type
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            insights = []
            
            for _, row in df.iterrows():
                signal_type = row['signal_type']
                win_rate = row['winning_signals'] / row['total_signals'] if row['total_signals'] > 0 else 0
                
                insights.append(f"\n🎯 {signal_type} SIGNALS:")
                insights.append(f"   Win Rate: {win_rate:.1%} ({row['winning_signals']}/{row['total_signals']})")
                
                if row['win_avg_rsi'] and row['loss_avg_rsi']:
                    insights.append(f"   RSI: Win={row['win_avg_rsi']:.1f} vs Loss={row['loss_avg_rsi']:.1f}")
                
                if row['win_avg_bb'] and row['loss_avg_bb']:
                    insights.append(f"   BB Position: Win={row['win_avg_bb']:.2f} vs Loss={row['loss_avg_bb']:.2f}")
            
            return insights
            
        except Exception as e:
            print(f"❌ AI insights error: {e}")
            return []
    
    def print_backtest_summary(self, performance):
        """แสดงสรุปผล backtest"""
        print("\n" + "="*60)
        print("📊 BACKTEST RESULTS SUMMARY")
        print("="*60)
        
        if not performance:
            print("❌ No performance data available")
            return
        
        print(f"💰 Initial Balance: ${self.initial_balance:,.2f}")
        print(f"💰 Final Balance: ${performance.get('final_balance', 0):,.2f}")
        print(f"📈 Total Profit: ${performance.get('total_profit', 0):,.2f} ({performance.get('total_profit_pct', 0):.2f}%)")
        print(f"📊 Total Trades: {performance.get('total_trades', 0)}")
        print(f"✅ Winning Trades: {performance.get('winning_trades', 0)}")
        print(f"❌ Losing Trades: {performance.get('losing_trades', 0)}")
        print(f"🎯 Win Rate: {performance.get('win_rate', 0):.1%}")
        print(f"⚖️ Profit Factor: {performance.get('profit_factor', 0):.2f}")
        print(f"📊 Average Trade: ${performance.get('avg_trade', 0):.2f}")
        print(f"🏆 Best Trade: ${performance.get('best_trade', 0):.2f}")
        print(f"💔 Worst Trade: ${performance.get('worst_trade', 0):.2f}")
        
        # AI Insights
        insights = self.generate_ai_insights()
        if insights:
            print("\n🤖 AI INSIGHTS:")
            for insight in insights:
                print(insight)
        
        print("="*60)


if __name__ == "__main__":
    # Example usage
    backtest = BacktestSystem()
    
    # Collect data
    print("🔄 Collecting historical data...")
    backtest.collect_historical_data(days=7)
    
    # Load and prepare data
    df = backtest.load_historical_data()
    if df is not None:
        df = backtest.calculate_indicators(df)
        
        if df is not None:
            # Run backtest
            trades, performance = backtest.run_backtest(df)
            
            # Show results
            backtest.print_backtest_summary(performance)
            
            # Train AI
            if trades:
                print("\n🤖 Training AI model...")
                backtest.train_ai_model()
