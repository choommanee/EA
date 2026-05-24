#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Data Backtest System
ระบบ backtest ใช้ข้อมูล Gold จาก data-gold folder
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob
from backtest_system import BacktestSystem

class GoldDataBacktest(BacktestSystem):
    def __init__(self):
        super().__init__()
        self.data_folder = "data-gold"
        self.gold_data = None
    
    def load_gold_csv_data(self):
        """โหลดข้อมูล Gold จาก CSV files ใน data-gold folder"""
        try:
            print("🔍 Scanning data-gold folder...")
            
            # Find all CSV files
            csv_files = []
            for root, dirs, files in os.walk(self.data_folder):
                for file in files:
                    if file.endswith('.csv') and 'XAUUSD_M1' in file:
                        csv_files.append(os.path.join(root, file))
            
            if not csv_files:
                print("❌ No XAUUSD CSV files found in data-gold folder")
                return None
            
            print(f"📁 Found {len(csv_files)} CSV files:")
            for file in csv_files:
                print(f"   - {os.path.basename(file)}")
            
            # Load and combine all CSV files
            all_data = []
            
            for csv_file in csv_files:
                print(f"📊 Loading {os.path.basename(csv_file)}...")
                
                try:
                    # Read CSV with proper column names
                    df = pd.read_csv(csv_file, header=None, names=[
                        'date', 'time', 'open', 'high', 'low', 'close', 'volume'
                    ])
                    
                    # Combine date and time
                    df['timestamp'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                    
                    # Keep only necessary columns
                    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                    
                    # Convert to numeric
                    for col in ['open', 'high', 'low', 'close']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Remove invalid data
                    df = df.dropna()
                    
                    if len(df) > 0:
                        all_data.append(df)
                        print(f"   ✅ Loaded {len(df)} candles")
                    else:
                        print(f"   ⚠️ No valid data in {os.path.basename(csv_file)}")
                        
                except Exception as e:
                    print(f"   ❌ Error loading {os.path.basename(csv_file)}: {e}")
                    continue
            
            if not all_data:
                print("❌ No valid data loaded from any CSV file")
                return None
            
            # Combine all data
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Sort by timestamp and remove duplicates
            combined_df = combined_df.sort_values('timestamp').drop_duplicates(subset=['timestamp']).reset_index(drop=True)
            
            print(f"✅ Combined data: {len(combined_df)} total candles")
            print(f"📅 Date range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")
            
            # Convert M1 to M5 data
            m5_data = self.convert_m1_to_m5(combined_df)
            
            return m5_data
            
        except Exception as e:
            print(f"❌ Error loading gold data: {e}")
            return None
    
    def convert_m1_to_m5(self, m1_data):
        """แปลงข้อมูล M1 เป็น M5"""
        try:
            print("🔄 Converting M1 to M5 data...")
            
            # Set timestamp as index
            m1_data.set_index('timestamp', inplace=True)
            
            # Resample to 5-minute intervals
            m5_data = m1_data.resample('5T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # Reset index
            m5_data.reset_index(inplace=True)
            
            print(f"✅ Converted to M5: {len(m5_data)} candles")
            
            return m5_data
            
        except Exception as e:
            print(f"❌ M1 to M5 conversion error: {e}")
            return None
    
    def run_gold_backtest(self, days_back=None, max_candles=2000):
        """รัน backtest บนข้อมูล Gold"""
        try:
            print("🚀 Starting Gold Data Backtest")
            print("="*60)
            
            # Load gold data
            df = self.load_gold_csv_data()
            if df is None:
                return None, None
            
            # Limit data if specified
            if days_back:
                cutoff_date = df['timestamp'].max() - pd.Timedelta(days=days_back)
                df = df[df['timestamp'] >= cutoff_date]
                print(f"📅 Using last {days_back} days of data")
            
            if len(df) > max_candles:
                df = df.tail(max_candles)
                print(f"📊 Limited to last {max_candles} candles")
            
            # Calculate indicators
            print("🔧 Calculating indicators...")
            df = self.calculate_indicators(df)
            if df is None:
                return None, None
            
            print(f"✅ Data prepared: {len(df)} candles with indicators")
            
            # Split data for training and testing
            split_point = int(len(df) * 0.7)
            train_df = df.iloc[:split_point]
            test_df = df.iloc[split_point:]
            
            print(f"\n📈 Training period: {train_df['timestamp'].iloc[0]} to {train_df['timestamp'].iloc[-1]}")
            print(f"   Candles: {len(train_df)}")
            print(f"🧪 Testing period: {test_df['timestamp'].iloc[0]} to {test_df['timestamp'].iloc[-1]}")
            print(f"   Candles: {len(test_df)}")
            
            # Run training backtest
            print("\n🎯 Running training backtest...")
            train_trades, train_performance = self.run_backtest(train_df)
            
            if train_trades:
                print(f"✅ Training completed: {len(train_trades)} trades")
                print(f"   Win Rate: {train_performance.get('win_rate', 0):.1%}")
                print(f"   Profit: ${train_performance.get('total_profit', 0):.2f}")
            
            # Train AI model
            print("\n🤖 Training AI model...")
            ai_trained = self.train_ai_model()
            
            # Run testing backtest
            print("\n🧪 Running testing backtest...")
            test_trades, test_performance = self.run_backtest(test_df)
            
            if test_trades:
                print(f"✅ Testing completed: {len(test_trades)} trades")
            
            return {
                'train_trades': train_trades,
                'train_performance': train_performance,
                'test_trades': test_trades,
                'test_performance': test_performance,
                'ai_trained': ai_trained
            }, df
            
        except Exception as e:
            print(f"❌ Gold backtest error: {e}")
            return None, None
    
    def print_comprehensive_results(self, results):
        """แสดงผลลัพธ์ครบถ้วน"""
        if not results:
            print("❌ No results to display")
            return
        
        train_performance = results['train_performance']
        test_performance = results['test_performance']
        train_trades = results['train_trades']
        test_trades = results['test_trades']
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE GOLD BACKTEST RESULTS")
        print("="*80)
        
        # Training Results
        print("\n🎯 TRAINING RESULTS:")
        if train_performance:
            self.print_performance_summary(train_performance, "TRAINING")
        
        # Testing Results
        print("\n🧪 TESTING RESULTS:")
        if test_performance:
            self.print_performance_summary(test_performance, "TESTING")
        
        # Comparison
        if train_performance and test_performance:
            print("\n⚖️ PERFORMANCE COMPARISON:")
            print(f"   Training Win Rate: {train_performance.get('win_rate', 0):.1%}")
            print(f"   Testing Win Rate:  {test_performance.get('win_rate', 0):.1%}")
            
            train_profit = train_performance.get('total_profit', 0)
            test_profit = test_performance.get('total_profit', 0)
            print(f"   Training Profit: ${train_profit:.2f}")
            print(f"   Testing Profit:  ${test_profit:.2f}")
            
            # Consistency check
            train_wr = train_performance.get('win_rate', 0)
            test_wr = test_performance.get('win_rate', 0)
            
            if test_wr >= train_wr * 0.8:
                print("   ✅ Good consistency between training and testing")
            else:
                print("   ⚠️ Performance degradation in testing - possible overfitting")
        
        # AI Insights
        print("\n🤖 AI LEARNING INSIGHTS:")
        insights = self.generate_ai_insights()
        if insights:
            for insight in insights:
                print(insight)
        else:
            print("   No AI insights available")
        
        # Recommendations
        print("\n💡 STRATEGY RECOMMENDATIONS:")
        if train_performance and test_performance:
            avg_win_rate = (train_performance.get('win_rate', 0) + test_performance.get('win_rate', 0)) / 2
            avg_profit_factor = (train_performance.get('profit_factor', 0) + test_performance.get('profit_factor', 0)) / 2
            
            if avg_win_rate >= 0.6:
                print("   ✅ Strategy shows good win rate - consider live testing")
            elif avg_win_rate >= 0.5:
                print("   ⚠️ Strategy shows moderate performance - optimize parameters")
            else:
                print("   ❌ Strategy needs significant improvement")
            
            if avg_profit_factor >= 1.5:
                print("   ✅ Good profit factor - risk management is effective")
            elif avg_profit_factor >= 1.2:
                print("   ⚠️ Acceptable profit factor - monitor closely")
            else:
                print("   ❌ Poor profit factor - review SL/TP settings")
        
        print("\n📈 NEXT STEPS:")
        print("   1. Analyze AI insights to optimize entry conditions")
        print("   2. Adjust confidence thresholds based on results")
        print("   3. Fine-tune SL/TP parameters")
        print("   4. Test with different market conditions")
        print("   5. Consider forward testing on demo account")
        
        print("="*80)
    
    def print_performance_summary(self, performance, label):
        """แสดงสรุปผลการดำเนินงาน"""
        print(f"   💰 Initial Balance: ${self.initial_balance:,.2f}")
        print(f"   💰 Final Balance: ${performance.get('final_balance', 0):,.2f}")
        print(f"   📈 Total Profit: ${performance.get('total_profit', 0):,.2f} ({performance.get('total_profit_pct', 0):.2f}%)")
        print(f"   📊 Total Trades: {performance.get('total_trades', 0)}")
        print(f"   ✅ Win Rate: {performance.get('win_rate', 0):.1%}")
        print(f"   ⚖️ Profit Factor: {performance.get('profit_factor', 0):.2f}")
        print(f"   📊 Avg Trade: ${performance.get('avg_trade', 0):.2f}")
        print(f"   🏆 Best Trade: ${performance.get('best_trade', 0):.2f}")
        print(f"   💔 Worst Trade: ${performance.get('worst_trade', 0):.2f}")


def main():
    """รันการทดสอบหลัก"""
    print("🥇 GOLD DATA BACKTESTING SYSTEM")
    print("="*60)
    
    # Initialize backtest system
    backtest = GoldDataBacktest()
    
    # Run comprehensive backtest
    results, data = backtest.run_gold_backtest(days_back=30, max_candles=2000)
    
    if results:
        # Show comprehensive results
        backtest.print_comprehensive_results(results)
        
        # Show data statistics
        if data is not None:
            print(f"\n📊 DATA STATISTICS:")
            print(f"   Total Candles: {len(data)}")
            print(f"   Date Range: {data['timestamp'].min()} to {data['timestamp'].max()}")
            print(f"   Price Range: ${data['low'].min():.2f} - ${data['high'].max():.2f}")
            print(f"   Average ATR: {data['atr'].mean():.3f}")
    else:
        print("❌ Backtest failed")

if __name__ == "__main__":
    main()
