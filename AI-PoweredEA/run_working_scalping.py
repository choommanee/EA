#!/usr/bin/env python3
"""
Run Working Scalping Trader - รันระบบที่ทำงานได้จริง
แก้ไขปัญหา: ไม่ออกสัญญาณ
"""

import sys
sys.path.append('.')

from working_scalping_trader import WorkingGoldScalpingTrader
import MetaTrader5 as mt5
from datetime import datetime

def main():
    """รันระบบ Working Scalping Trader"""
    print("🎯 BB + ZigZag + AI Gold Scalping Trader")
    print("=" * 60)
    
    # สร้าง trader
    trader = WorkingGoldScalpingTrader()
    
    print("\n🎯 BB + ZigZag + AI Strategy Settings:")
    print(f"   📏 Dynamic SL/TP: M5 BB Width-based")
    print(f"   🛡️ SL: M5 BB Width reduced by {trader.bb_sl_reduction:.0%}")
    print(f"   🎯 TP Multiplier: {trader.bb_tp_multiplier:.1f}x of SL")
    print(f"   📊 SL Range: {trader.min_sl_points/10:.1f}-{trader.max_sl_points/10:.1f} pips")
    print(f"   📈 Max Spread: {trader.max_spread} points")
    print(f"   🎯 Confidence Threshold: {trader.confidence_threshold:.0%}")
    print(f"   ⏰ Signal Interval: {trader.signal_interval_seconds} seconds")
    print(f"   💼 Max Positions: {trader.max_positions}")
    print(f"   📊 Max Daily Trades: {trader.max_daily_trades}")
    
    print(f"\n🎯 Trading Strategy Components:")
    print(f"   📊 Bollinger Bands (20 period, 2 std)")
    print(f"   📈 ZigZag Peak/Trough Detection")
    print(f"   🤖 AI ML Prediction & Confirmation")
    print(f"   📉 Trend Reversal Analysis")
    
    # ตัวเลือกการรัน
    print(f"\n🚀 Running Options:")
    print("1. Quick Test (5 minutes)")
    print("2. Short Session (15 minutes)")
    print("3. Standard Session (30 minutes)")
    print("4. Long Session (60 minutes)")
    print("5. Extended Session (120 minutes)")
    print("6. Custom Duration")
    
    choice = input("\nSelect option (1-6, default 2): ").strip() or "2"
    
    duration_map = {
        "1": 5,
        "2": 15,
        "3": 30,
        "4": 60,
        "5": 120
    }
    
    if choice in duration_map:
        duration = duration_map[choice]
    elif choice == "6":
        duration = int(input("Enter custom duration (minutes): "))
    else:
        duration = 15  # default
    
    print(f"\n⚡ Starting {duration}-minute scalping session...")
    
    # คำนวณสถิติที่คาดหวัง
    max_signals = (duration * 60) // trader.signal_interval_seconds
    expected_trades = max_signals * 0.3  # คาดว่า 30% ของสัญญาณจะกลายเป็นเทรด
    
    print(f"\n📊 Expected Statistics:")
    print(f"   📡 Max Possible Signals: ~{max_signals}")
    print(f"   📈 Expected Trades: ~{expected_trades:.0f}")
    print(f"   💰 Profit Range/Trade: ${(trader.min_sl_points*1.5/10) * trader.base_lot_size * 100:.2f}-${(trader.max_sl_points*2/10) * trader.base_lot_size * 100:.2f}")
    print(f"   ⚠️ Loss Range/Trade: ${(trader.min_sl_points/10) * trader.base_lot_size * 100:.2f}-${(trader.max_sl_points/10) * trader.base_lot_size * 100:.2f}")
    print(f"   📏 SL/TP: Adaptive to BB Width")
    
    # ยืนยันการเริ่มต้น
    confirm = input(f"\nStart scalping session? (y/n, default y): ").strip().lower()
    if confirm == 'n':
        print("❌ Session cancelled")
        return
    
    try:
        # รันระบบ
        print(f"\n🚀 Starting Working Scalping System...")
        success = trader.run_scalping_session(duration)
        
        if success:
            print(f"\n🎉 Scalping session completed successfully!")
            
            # แสดงสถิติสุดท้าย
            positions = trader.get_active_positions()
            
            print(f"\n📊 Final Statistics:")
            print(f"   📡 Orders Placed: {len(trader.orders_placed)}")
            print(f"   💼 Active Positions: {len(positions)}")
            print(f"   📈 Daily Trades: {trader.daily_trades}")
            
            # แสดงรายละเอียด positions
            if positions:
                print(f"\n📋 Active Positions:")
                total_unrealized = 0
                for i, pos in enumerate(positions, 1):
                    pos_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                    hold_time = datetime.now() - datetime.fromtimestamp(pos.time)
                    total_unrealized += pos.profit
                    
                    print(f"   {i}. 🎫 {pos.ticket}: {pos_type} {pos.volume} lots")
                    print(f"      💰 Entry: ${pos.price_open:.2f}")
                    print(f"      🎯 TP: ${pos.tp:.2f}")
                    print(f"      🛡️ SL: ${pos.sl:.2f}")
                    print(f"      📊 P&L: ${pos.profit:.2f}")
                    print(f"      ⏰ Hold Time: {str(hold_time).split('.')[0]}")
                
                print(f"\n💰 Total Unrealized P&L: ${total_unrealized:.2f}")
                
                # ถามว่าจะปิด positions หรือไม่
                print(f"\nWhat to do with {len(positions)} active positions?")
                print("1. Keep all positions open")
                print("2. Close all positions")
                print("3. Close only losing positions")
                print("4. Close only profitable positions")
                
                close_choice = input("Enter choice (1-4, default 1): ").strip() or "1"
                
                if close_choice == "2":
                    # ปิดทุก positions
                    for pos in positions:
                        if trader.close_position(pos.ticket, "Session end - close all"):
                            print(f"✅ Closed position {pos.ticket}")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                elif close_choice == "3":
                    # ปิดเฉพาะ positions ขาดทุน
                    losing_positions = [pos for pos in positions if pos.profit < 0]
                    for pos in losing_positions:
                        if trader.close_position(pos.ticket, "Session end - close losing"):
                            print(f"✅ Closed losing position {pos.ticket} (${pos.profit:.2f})")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                elif close_choice == "4":
                    # ปิดเฉพาะ positions กำไร
                    profitable_positions = [pos for pos in positions if pos.profit > 0]
                    for pos in profitable_positions:
                        if trader.close_position(pos.ticket, "Session end - close profitable"):
                            print(f"✅ Closed profitable position {pos.ticket} (${pos.profit:.2f})")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                else:
                    print("📋 All positions kept open")
            else:
                print("📋 No active positions")
            
            # แสดงสรุปประสิทธิภาพ
            if len(trader.orders_placed) > 0:
                avg_confidence = sum([order['confidence'] for order in trader.orders_placed]) / len(trader.orders_placed)
                trades_per_hour = len(trader.orders_placed) / (duration / 60)
                
                print(f"\n⚡ Session Performance:")
                print(f"   📊 Average Signal Confidence: {avg_confidence:.1%}")
                print(f"   📈 Trades per Hour: {trades_per_hour:.1f}")
                print(f"   ⏰ Session Duration: {duration} minutes")
                
                # แสดง entry reasons ที่ใช้บ่อย
                all_reasons = []
                for order in trader.orders_placed:
                    all_reasons.extend(order['reasons'])
                
                if all_reasons:
                    from collections import Counter
                    reason_counts = Counter(all_reasons)
                    print(f"\n📋 Most Common Entry Reasons:")
                    for reason, count in reason_counts.most_common(3):
                        print(f"   • {reason}: {count} times")
        else:
            print(f"\n❌ Scalping session failed")
    
    except KeyboardInterrupt:
        print(f"\n⏹️ Scalping stopped by user")
        
        # แสดงสถิติสุดท้าย
        positions = trader.get_active_positions()
        
        print(f"\n📊 Session Statistics (Interrupted):")
        print(f"   📡 Orders Placed: {len(trader.orders_placed)}")
        print(f"   💼 Active Positions: {len(positions)}")
        print(f"   📈 Daily Trades: {trader.daily_trades}")
    
    except Exception as e:
        print(f"\n❌ Scalping error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    main()