#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Backtest and AI Learning System
รันระบบ backtest และ AI learning
"""

from backtest_system import BacktestSystem
from datetime import datetime, timedelta

def main():
    print("🚀 Starting Backtest and AI Learning System")
    print("="*60)
    
    # Initialize backtest system
    backtest = BacktestSystem()
    
    # Step 1: Collect historical data
    print("\n📊 Step 1: Collecting historical data from MT5...")
    success = backtest.collect_historical_data(days=14)  # 2 weeks of data
    
    if not success:
        print("❌ Failed to collect data. Make sure MT5 is running.")
        return
    
    # Step 2: Load and prepare data
    print("\n🔧 Step 2: Loading and preparing data...")
    df = backtest.load_historical_data(timeframe='M5', limit=3000)
    
    if df is None:
        print("❌ No data available for backtesting")
        return
    
    # Calculate indicators
    df = backtest.calculate_indicators(df)
    if df is None:
        print("❌ Failed to calculate indicators")
        return
    
    print(f"✅ Data prepared: {len(df)} candles with indicators")
    
    # Step 3: Run backtest
    print("\n⚡ Step 3: Running backtest...")
    
    # Split data for different periods
    total_candles = len(df)
    split_point = int(total_candles * 0.7)  # 70% for training, 30% for testing
    
    train_df = df.iloc[:split_point]
    test_df = df.iloc[split_point:]
    
    print(f"📈 Training period: {train_df['timestamp'].iloc[0]} to {train_df['timestamp'].iloc[-1]}")
    print(f"🧪 Testing period: {test_df['timestamp'].iloc[0]} to {test_df['timestamp'].iloc[-1]}")
    
    # Run training backtest
    print("\n🎯 Running training backtest...")
    train_trades, train_performance = backtest.run_backtest(train_df)
    
    print(f"✅ Training completed: {len(train_trades)} trades")
    if train_performance:
        print(f"   Win Rate: {train_performance.get('win_rate', 0):.1%}")
        print(f"   Profit: ${train_performance.get('total_profit', 0):.2f}")
    
    # Step 4: Train AI model
    print("\n🤖 Step 4: Training AI model...")
    ai_trained = backtest.train_ai_model()
    
    if ai_trained:
        print("✅ AI model trained successfully")
    else:
        print("⚠️ AI training failed - continuing with basic strategy")
    
    # Step 5: Run testing backtest
    print("\n🧪 Step 5: Running testing backtest...")
    test_trades, test_performance = backtest.run_backtest(test_df)
    
    print(f"✅ Testing completed: {len(test_trades)} trades")
    
    # Step 6: Show results
    print("\n📊 Step 6: Results Analysis")
    print("\n🎯 TRAINING RESULTS:")
    backtest.print_backtest_summary(train_performance)
    
    print("\n🧪 TESTING RESULTS:")
    backtest.print_backtest_summary(test_performance)
    
    # Step 7: Generate AI insights
    print("\n🤖 Step 7: AI Learning Insights")
    insights = backtest.generate_ai_insights()
    
    if insights:
        print("\n💡 KEY INSIGHTS FOR ENTRY OPTIMIZATION:")
        for insight in insights:
            print(insight)
        
        print("\n🎯 RECOMMENDATIONS:")
        print("   • Focus on signals with higher confidence scores")
        print("   • Optimize RSI and BB position thresholds based on winning patterns")
        print("   • Consider trend strength as a key filter")
        print("   • Use AI insights to improve entry timing")
    
    # Summary
    print("\n" + "="*60)
    print("🏁 BACKTEST AND AI LEARNING COMPLETED")
    print("="*60)
    
    total_train_trades = len(train_trades)
    total_test_trades = len(test_trades)
    
    if train_performance and test_performance:
        print(f"📊 Total Analysis:")
        print(f"   Training Trades: {total_train_trades}")
        print(f"   Testing Trades: {total_test_trades}")
        print(f"   Training Win Rate: {train_performance.get('win_rate', 0):.1%}")
        print(f"   Testing Win Rate: {test_performance.get('win_rate', 0):.1%}")
        print(f"   Training Profit: ${train_performance.get('total_profit', 0):.2f}")
        print(f"   Testing Profit: ${test_performance.get('total_profit', 0):.2f}")
        
        # Performance comparison
        train_win_rate = train_performance.get('win_rate', 0)
        test_win_rate = test_performance.get('win_rate', 0)
        
        if test_win_rate >= train_win_rate * 0.8:  # Within 20% of training performance
            print("✅ Model shows good generalization")
        else:
            print("⚠️ Model may be overfitting - consider adjusting parameters")
    
    print("\n💾 All data stored in: Data/backtest_results.db")
    print("🤖 AI learning data available for strategy optimization")

if __name__ == "__main__":
    main()
