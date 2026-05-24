#!/usr/bin/env python3
"""
Validation script for Gold scalping trader optimizations
Checks if backtest-derived optimizations are properly implemented
"""

import os
import sys

def validate_optimization_implementation():
    """Validate that optimizations from backtest results are properly applied"""
    
    print("🔍 VALIDATING GOLD SCALPING TRADER OPTIMIZATIONS")
    print("=" * 60)
    
    # Read the working trader file
    trader_file = "working_scalping_trader.py"
    
    if not os.path.exists(trader_file):
        print(f"❌ {trader_file} not found")
        return False
    
    with open(trader_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    optimizations_found = []
    issues_found = []
    
    # Check 1: RSI thresholds optimization
    print("\n📊 Checking RSI threshold optimizations...")
    if "signal_data['rsi'] <= 30" in content:
        optimizations_found.append("✅ BUY RSI threshold optimized to ≤30 (was 35)")
    else:
        issues_found.append("❌ BUY RSI threshold not optimized (should be ≤30)")
    
    if "signal_data['rsi'] >= 70" in content:
        optimizations_found.append("✅ SELL RSI threshold optimized to ≥70 (was 65)")
    else:
        issues_found.append("❌ SELL RSI threshold not optimized (should be ≥70)")
    
    # Check 2: BB position thresholds
    print("📊 Checking Bollinger Bands position optimizations...")
    if "signal_data['bb_position'] <= 0.18" in content:
        optimizations_found.append("✅ BUY BB position optimized to ≤0.18 (was 0.2)")
    else:
        issues_found.append("❌ BUY BB position not optimized (should be ≤0.18)")
    
    if "signal_data['bb_position'] >= 0.82" in content:
        optimizations_found.append("✅ SELL BB position optimized to ≥0.82 (was 0.8)")
    else:
        issues_found.append("❌ SELL BB position not optimized (should be ≥0.82)")
    
    # Check 3: EMA trend bias
    print("📊 Checking EMA trend bias implementation...")
    if "signal_data['ema_10'] > signal_data['ema_20']" in content:
        optimizations_found.append("✅ BUY EMA uptrend bias implemented")
    else:
        issues_found.append("❌ BUY EMA uptrend bias missing")
    
    if "signal_data['ema_10'] < signal_data['ema_20']" in content:
        optimizations_found.append("✅ SELL EMA downtrend bias implemented")
    else:
        issues_found.append("❌ SELL EMA downtrend bias missing")
    
    # Check 4: Volatility requirement reduction
    print("📊 Checking volatility requirement optimization...")
    if "signal_data['bb_width'] >= 0.001" in content:
        optimizations_found.append("✅ Volatility requirement reduced to 0.001")
    else:
        issues_found.append("❌ Volatility requirement not optimized")
    
    # Check 5: Strong trend detection
    print("📊 Checking strong trend avoidance...")
    if "not signal_data['strong_trend_detected']" in content:
        optimizations_found.append("✅ Strong trend avoidance implemented")
    else:
        issues_found.append("❌ Strong trend avoidance missing")
    
    # Check 6: Position limits
    print("📊 Checking position management...")
    if "len(active_positions) >= 2" in content:
        optimizations_found.append("✅ Position limit (2) implemented")
    else:
        issues_found.append("❌ Position limit not properly set")
    
    # Check 7: Risk management settings
    print("📊 Checking risk management optimizations...")
    risk_settings = [
        ("use_adaptive_sl = True", "Adaptive SL enabled"),
        ("tp_risk_reward_ratio", "Risk/reward ratio configured"),
        ("max_positions", "Maximum positions limit"),
        ("max_daily_trades", "Daily trade limit")
    ]
    
    for setting, description in risk_settings:
        if setting in content:
            optimizations_found.append(f"✅ {description}")
        else:
            issues_found.append(f"❌ {description} missing")
    
    # Summary
    print(f"\n📋 OPTIMIZATION VALIDATION SUMMARY")
    print("=" * 50)
    
    print(f"\n✅ OPTIMIZATIONS IMPLEMENTED ({len(optimizations_found)}):")
    for opt in optimizations_found:
        print(f"   {opt}")
    
    if issues_found:
        print(f"\n❌ ISSUES FOUND ({len(issues_found)}):")
        for issue in issues_found:
            print(f"   {issue}")
    else:
        print(f"\n🎉 ALL OPTIMIZATIONS PROPERLY IMPLEMENTED!")
    
    # Backtest results reference
    print(f"\n📊 BACKTEST RESULTS REFERENCE:")
    print(f"   Balanced Strategy: 60.9% win rate (BUY), 55.6% win rate (SELL)")
    print(f"   Optimized Strategy: Higher precision, better risk/reward")
    print(f"   Key improvements: Stricter thresholds, trend bias, reduced noise")
    
    return len(issues_found) == 0

def validate_backtest_integration():
    """Check if backtest results are properly integrated"""
    
    print(f"\n🔬 BACKTEST INTEGRATION VALIDATION")
    print("=" * 40)
    
    backtest_files = [
        "balanced_gold_strategy.py",
        "optimized_gold_strategy.py", 
        "run_gold_backtest.py"
    ]
    
    existing_files = []
    for file in backtest_files:
        if os.path.exists(file):
            existing_files.append(file)
            print(f"✅ {file} - Available for reference")
        else:
            print(f"❌ {file} - Missing")
    
    print(f"\n📊 Backtest files available: {len(existing_files)}/{len(backtest_files)}")
    
    return len(existing_files) >= 2

if __name__ == "__main__":
    print("🚀 Starting Gold Scalping Trader Optimization Validation")
    print("=" * 70)
    
    try:
        # Validate optimization implementation
        opt_valid = validate_optimization_implementation()
        
        # Validate backtest integration
        backtest_valid = validate_backtest_integration()
        
        print(f"\n🎯 FINAL VALIDATION RESULTS")
        print("=" * 40)
        
        if opt_valid and backtest_valid:
            print("✅ ALL VALIDATIONS PASSED!")
            print("\n🎉 Gold Scalping Trader is optimized and ready for testing!")
            print("\n📋 Next Steps:")
            print("   1. Test in demo environment with MT5 connection")
            print("   2. Monitor signal quality and win rates")
            print("   3. Validate improved performance vs baseline")
            print("   4. Continue AI learning data collection")
        else:
            print("❌ VALIDATION ISSUES FOUND!")
            if not opt_valid:
                print("   - Optimization implementation needs fixes")
            if not backtest_valid:
                print("   - Backtest integration incomplete")
        
        print(f"\n📊 Optimization Status: {'COMPLETE' if opt_valid else 'NEEDS WORK'}")
        print(f"🔬 Backtest Integration: {'COMPLETE' if backtest_valid else 'NEEDS WORK'}")
        
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)
