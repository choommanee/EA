"""
Run Martingale Trader - รันระบบ Martingale แบบเต็มรูปแบบ
"""

import sys
sys.path.append('.')

from gold_martingale_trader import GoldMartingaleTrader
import MetaTrader5 as mt5

def run_martingale_trader():
    """รันระบบ Martingale Trader"""
    print("🎯 Gold Martingale Trader - Full System")
    print("=" * 50)
    
    # สร้าง trader
    trader = GoldMartingaleTrader()
    
    # ตั้งค่าระบบ
    print("\n⚙️ System Configuration:")
    
    # Base settings
    base_lot = float(input(f"Base lot size (default {trader.base_lot_size}): ") or trader.base_lot_size)
    tp_points = int(input(f"Take Profit points (default {trader.tp_points}): ") or trader.tp_points)
    sl_points = int(input(f"Stop Loss points (default {trader.sl_points}): ") or trader.sl_points)
    
    # Martingale settings
    enable_martingale = input("Enable Martingale? (y/n, default y): ").strip().lower() != 'n'
    
    if enable_martingale:
        max_levels = int(input(f"Max Martingale levels (default {trader.max_martingale_levels}): ") or trader.max_martingale_levels)
        martingale_distance = int(input(f"Martingale distance points (default {trader.martingale_distance}): ") or trader.martingale_distance)
        multiplier = float(input(f"Martingale multiplier (default {trader.martingale_multiplier}): ") or trader.martingale_multiplier)
    
    # Trailing Stop settings
    enable_trailing = input("Enable Trailing Stop? (y/n, default y): ").strip().lower() != 'n'
    
    if enable_trailing:
        trailing_start = int(input(f"Trailing start points (default {trader.trailing_start}): ") or trader.trailing_start)
        trailing_step = int(input(f"Trailing step points (default {trader.trailing_step}): ") or trader.trailing_step)
    
    # Trading duration
    duration = int(input("Trading duration (minutes, default 120): ") or "120")
    interval = int(input("Signal interval (minutes, default 10): ") or "10")
    
    # Apply settings
    trader.base_lot_size = base_lot
    trader.tp_points = tp_points
    trader.sl_points = sl_points
    trader.enable_martingale = enable_martingale
    trader.enable_trailing_stop = enable_trailing
    
    if enable_martingale:
        trader.max_martingale_levels = max_levels
        trader.martingale_distance = martingale_distance
        trader.martingale_multiplier = multiplier
    
    if enable_trailing:
        trader.trailing_start = trailing_start
        trader.trailing_step = trailing_step
    
    # แสดงการตั้งค่าสุดท้าย
    print(f"\n📋 Final Configuration:")
    print(f"   💰 Base Lot Size: {trader.base_lot_size}")
    print(f"   🎯 Take Profit: {trader.tp_points} points")
    print(f"   🛡️ Stop Loss: {trader.sl_points} points")
    print(f"   🔄 Martingale: {'Enabled' if trader.enable_martingale else 'Disabled'}")
    
    if trader.enable_martingale:
        print(f"      • Max Levels: {trader.max_martingale_levels}")
        print(f"      • Distance: {trader.martingale_distance} points")
        print(f"      • Multiplier: {trader.martingale_multiplier}x")
        print(f"      • Lot Progression: ", end="")
        for i in range(trader.max_martingale_levels):
            lot = trader.base_lot_size * (trader.martingale_multiplier ** i)
            print(f"{lot:.2f}", end=" → " if i < trader.max_martingale_levels - 1 else "\n")
    
    print(f"   📈 Trailing Stop: {'Enabled' if trader.enable_trailing_stop else 'Disabled'}")
    
    if trader.enable_trailing_stop:
        print(f"      • Start: {trader.trailing_start} points profit")
        print(f"      • Step: {trader.trailing_step} points")
    
    print(f"   ⏰ Duration: {duration} minutes")
    print(f"   📡 Signal Interval: {interval} minutes")
    
    # ยืนยันการเริ่มต้น
    confirm = input(f"\nStart trading with these settings? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Trading cancelled")
        return
    
    try:
        # รันระบบ
        print(f"\n🚀 Starting Martingale Trading System...")
        success = trader.run_trading_session(duration, interval)
        
        if success:
            print(f"\n🎉 Trading session completed successfully!")
            
            # แสดงสถิติสุดท้าย
            positions = trader.get_active_positions()
            total_profit = sum(pos.profit for pos in positions) if positions else 0
            
            print(f"\n📊 Final Statistics:")
            print(f"   📡 Signals Sent: {len(trader.signals_sent)}")
            print(f"   💼 Total Orders: {trader.performance_data['total_orders']}")
            print(f"   ✅ Successful Orders: {trader.performance_data['successful_orders']}")
            print(f"   ❌ Failed Orders: {trader.performance_data['failed_orders']}")
            print(f"   🔄 Martingale Orders: {trader.performance_data['martingale_orders']}")
            print(f"   📈 Trailing Stops Moved: {trader.performance_data['trailing_stops_moved']}")
            print(f"   🎫 Active Positions: {len(positions)}")
            print(f"   💰 Current P&L: ${total_profit:.2f}")
            
            # แสดงรายละเอียด positions
            if positions:
                print(f"\n📋 Active Positions:")
                for i, pos in enumerate(positions, 1):
                    pos_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                    print(f"   {i}. 🎫 {pos.ticket}: {pos_type} {pos.volume} lots")
                    print(f"      💰 Entry: ${pos.price_open:.2f}")
                    print(f"      🎯 TP: ${pos.tp:.2f}")
                    print(f"      🛡️ SL: ${pos.sl:.2f}")
                    print(f"      📊 P&L: ${pos.profit:.2f}")
                    print(f"      ⏰ Time: {datetime.fromtimestamp(pos.time).strftime('%H:%M:%S')}")
                
                # ถามว่าจะปิด positions หรือไม่
                close_option = input(f"\nWhat to do with {len(positions)} active positions?\n")
                print("1. Keep all positions open")
                print("2. Close all positions")
                print("3. Close only losing positions")
                print("4. Close only profitable positions")
                
                choice = input("Enter choice (1-4, default 1): ").strip() or "1"
                
                if choice == "2":
                    # ปิดทุก positions
                    for pos in positions:
                        if trader.close_position(pos.ticket):
                            print(f"✅ Closed position {pos.ticket}")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                elif choice == "3":
                    # ปิดเฉพาะ positions ขาดทุน
                    losing_positions = [pos for pos in positions if pos.profit < 0]
                    for pos in losing_positions:
                        if trader.close_position(pos.ticket):
                            print(f"✅ Closed losing position {pos.ticket} (${pos.profit:.2f})")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                elif choice == "4":
                    # ปิดเฉพาะ positions กำไร
                    profitable_positions = [pos for pos in positions if pos.profit > 0]
                    for pos in profitable_positions:
                        if trader.close_position(pos.ticket):
                            print(f"✅ Closed profitable position {pos.ticket} (${pos.profit:.2f})")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                else:
                    print("📋 All positions kept open")
        else:
            print(f"\n❌ Trading session failed")
    
    except KeyboardInterrupt:
        print(f"\n⏹️ Trading stopped by user")
        
        # ส่งข้อความแจ้งหยุด
        positions = trader.get_active_positions()
        total_profit = sum(pos.profit for pos in positions) if positions else 0
        
        stop_message = f"""
⏹️ <b>MARTINGALE TRADING STOPPED</b> ⏹️

📊 <b>Session Results:</b>
• Signals Sent: {len(trader.signals_sent)}
• Orders Placed: {trader.performance_data['total_orders']}
• Martingale Orders: {trader.performance_data['martingale_orders']}
• Active Positions: {len(positions)}
• Current P&L: ${total_profit:.2f}

<i>🤖 Gold Martingale Trader</i>
        """.strip()
        
        trader.send_telegram_message(stop_message)
    
    except Exception as e:
        print(f"\n❌ Trading error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    from datetime import datetime
    run_martingale_trader()