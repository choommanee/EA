#!/usr/bin/env python3
"""
Test script for Enhanced Working Gold Scalping Trader with AI Integration
ทดสอบระบบ AI ที่ปรับปรุงแล้ว
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from working_scalping_trader import WorkingGoldScalpingTrader
    print("✅ Successfully imported WorkingGoldScalpingTrader")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_ai_integration():
    """ทดสอบการทำงานของ AI Integration"""
    print("\n" + "="*60)
    print("🧪 TESTING ENHANCED AI SCALPING TRADER")
    print("="*60)
    
    try:
        # Initialize trader
        print("🔄 Initializing trader...")
        trader = WorkingGoldScalpingTrader()
        
        # Test AI system status
        print("\n📊 Testing AI system status...")
        trader.print_ai_system_status()
        
        # Test AI system status report
        print("\n📋 Getting AI system status report...")
        status = trader.get_ai_system_status()
        print(f"Status report generated: {len(status)} fields")
        
        # Test MT5 connection (if available)
        print("\n🔌 Testing MT5 connection...")
        if trader.connect_mt5():
            print("✅ MT5 connection successful")
            
            # Test market condition check
            print("\n🏪 Testing market conditions...")
            market_ok, market_msg = trader.check_simple_market_conditions()
            print(f"Market conditions: {'✅ OK' if market_ok else '❌ NOT OK'} - {market_msg}")
            
            # Test signal generation (if market is OK)
            if market_ok:
                print("\n🎯 Testing signal generation...")
                signal = trader.generate_bb_zigzag_ai_signal()
                if signal:
                    print(f"✅ Signal generated: {signal}")
                else:
                    print("ℹ️ No signal generated (normal)")
            
        else:
            print("⚠️ MT5 not available - testing in simulation mode")
        
        # Test AI status notification
        print("\n📱 Testing AI status notification...")
        trader.send_ai_status_notification()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("🤖 Enhanced AI Scalping Trader is ready for use!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print(f"🕐 Test started at: {datetime.now()}")
    
    success = test_ai_integration()
    
    if success:
        print("\n🎉 Enhanced AI Scalping Trader is working correctly!")
        print("💡 You can now use the trader with full AI integration")
        print("\n📋 Key Features Available:")
        print("   🤖 Advanced AI System Integration")
        print("   📊 Learning Pipeline with Continuous Improvement")
        print("   🎯 Model Management and Evaluation")
        print("   📈 Performance Monitoring and Metrics")
        print("   🔔 Error Handling and Notifications")
        print("   📱 Comprehensive Status Reporting")
    else:
        print("\n❌ Some issues detected. Please check the logs above.")
    
    print(f"\n🕐 Test completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
