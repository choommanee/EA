#!/usr/bin/env python3
"""
Simple direct run of Gold Scalping Trader
รันตรงๆ ไม่ผ่าน input
"""

# Import และรันตรงๆ
try:
    print("🚀 Starting Gold Scalping Trader...")
    
    from working_scalping_trader import WorkingGoldScalpingTrader
    
    # สร้าง trader
    trader = WorkingGoldScalpingTrader()
    print("✅ Trader created")
    
    # รันเซสชัน 3 นาที
    print("⚡ Running 3-minute test session...")
    success = trader.run_scalping_session(3)
    
    if success:
        print("✅ Test session completed!")
    else:
        print("❌ Test session failed!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
