#!/usr/bin/env python3
"""
ทดสอบการแสดงผล positions ที่แก้ไขแล้ว
"""

import sys
from working_scalping_trader import WorkingGoldScalpingTrader

def test_positions_display():
    """ทดสอบการแสดงผล positions"""
    print("🧪 Testing Positions Display Fix")
    print("="*50)
    
    # สร้าง trader
    trader = WorkingGoldScalpingTrader()
    
    # เชื่อมต่อ MT5
    if not trader.connect_mt5():
        print("❌ Cannot connect to MT5")
        return False
    
    print("✅ MT5 Connected successfully")
    print()
    
    # ทดสอบการแสดงผล positions
    print("📊 Testing Position Status Display:")
    trader.show_positions_status()
    print()
    
    # ทดสอบการดึงข้อมูล positions
    print("🔍 Testing Get Active Positions:")
    positions = trader.get_active_positions()
    
    if positions:
        print(f"✅ Found {len(positions)} active positions")
        
        for i, pos in enumerate(positions, 1):
            print(f"\n📋 Position #{i} Details:")
            print(f"   Ticket: {pos.ticket}")
            print(f"   Symbol: {pos.symbol}")
            print(f"   Type: {pos.type} ({'BUY' if pos.type == 0 else 'SELL'})")
            print(f"   Volume: {pos.volume}")
            print(f"   Open Price: ${pos.price_open:.2f}")
            print(f"   Current Price: ${pos.price_current:.2f}")
            print(f"   SL: ${pos.sl:.2f}")
            print(f"   TP: ${pos.tp:.2f}")
            print(f"   Profit: ${pos.profit:.2f}")
            print(f"   Swap: ${pos.swap:.2f}")
            print(f"   Comment: {pos.comment}")
            
            # คำนวณ profit ใน pips
            symbol_info = trader.mt5.symbol_info(pos.symbol)
            if symbol_info:
                profit_pips = pos.profit / (symbol_info.point * 10)
                print(f"   Profit (pips): {profit_pips:.1f}")
    else:
        print("📝 No active positions found")
    
    print("\n" + "="*50)
    print("🏁 Position Display Test Completed")
    
    return True

if __name__ == "__main__":
    try:
        test_positions_display()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()