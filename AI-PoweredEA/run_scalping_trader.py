"""
Run Scalping Trader - รันระบบ Scalping แบบต่อเนื่อง
"""

import sys
sys.path.append('.')

from gold_scalping_trader import GoldScalpingTrader
import MetaTrader5 as mt5
from datetime import datetime

def run_scalping_trader():
    """รันระบบ Scalping Trader"""
    print("⚡ Gold Scalping Trader - Continuous Mode")
    print("=" * 50)
    
    # สร้าง trader
    trader = GoldScalpingTrader()
    
    # ตั้งค่าระบบ
    print("\n⚙️ Scalping Configuration:")
    
    # Basic settings
    tp_points = int(input(f"Take Profit points (default {trader.tp_points}): ") or trader.tp_points)
    sl_points = int(input(f"Stop Loss points (default {trader.sl_points}): ") or trader.sl_points)
    max_spread = int(input(f"Max spread points (default {trader.max_spread}): ") or trader.max_spread)
    
    # Position management
    max_positions = int(input(f"Max positions (default {trader.max_positions}): ") or trader.max_positions)
    max_daily_trades = int(input(f"Max daily trades (default {trader.max_daily_trades}): ") or trader.max_daily_trades)
    max_hold_minutes = int(input(f"Max hold time minutes (default {trader.max_hold_minutes}): ") or trader.max_hold_minutes)
    
    # Timing settings
    signal_interval = int(input(f"Signal check interval seconds (default {trader.signal_interval_seconds}): ") or trader.signal_interval_seconds)
    
    # Risk management
    breakeven_points = int(input(f"Breakeven trigger points (default {trader.breakeven_points}): ") or trader.breakeven_points)
    partial_close_points = int(input(f"Partial close points (default {trader.partial_close_points}): ") or trader.partial_close_points)
    
    # Session duration
    duration = int(input("Trading duration (minutes, default 120): ") or "120")
    
    # Apply settings
    trader.tp_points = tp_points
    trader.sl_points = sl_points
    trader.max_spread = max_spread
    trader.max_positions = max_positions
    trader.max_daily_trades = max_daily_trades
    trader.max_hold_minutes = max_hold_minutes
    trader.signal_interval_seconds = signal_interval
    trader.breakeven_points = breakeven_points
    trader.partial_close_points = partial_close_points
    
    # แสดงการตั้งค่าสุดท้าย
    print(f"\n📋 Final Configuration:")
    print(f"   ⚡ Timeframe: M1 (1 minute)")
    print(f"   🎯 Take Profit: {trader.tp_points} points ({trader.tp_points/10:.1f} pips)")
    print(f"   🛡️ Stop Loss: {trader.sl_points} points ({trader.sl_points/10:.1f} pips)")
    print(f"   📊 Max Spread: {trader.max_spread} points")
    print(f"   💼 Max Positions: {trader.max_positions}")
    print(f"   📈 Max Daily Trades: {trader.max_daily_trades}")
    print(f"   ⏰ Max Hold Time: {trader.max_hold_minutes} minutes")
    print(f"   📡 Signal Check: Every {trader.signal_interval_seconds} seconds")
    print(f"   📈 Breakeven: At +{trader.breakeven_points} points")
    print(f"   📊 Partial Close: At +{trader.partial_close_points} points")
    print(f"   ⏰ Duration: {duration} minutes")
    
    # คำนวณสถิติที่คาดหวัง
    max_signals = (duration * 60) // signal_interval
    expected_profit_per_trade = (tp_points / 10) * trader.base_lot_size * 100  # USD per 0.01 lot
    max_loss_per_trade = (sl_points / 10) * trader.base_lot_size * 100
    
    print(f"\n📊 Expected Statistics:")
    print(f"   📡 Max Possible Signals: ~{max_signals}")
    print(f"   💰 Expected Profit/Trade: ${expected_profit_per_trade:.2f}")
    print(f"   ⚠️ Max Loss/Trade: ${max_loss_per_trade:.2f}")
    print(f"   🎯 Risk/Reward Ratio: 1:{tp_points/sl_points:.1f}")
    
    # ยืนยันการเริ่มต้น
    confirm = input(f"\nStart scalping with these settings? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Scalping cancelled")
        return
    
    try:
        # รันระบบ
        print(f"\n⚡ Starting Scalping System...")
        success = trader.run_scalping_session(duration)
        
        if success:
            print(f"\n🎉 Scalping session completed successfully!")
            
            # แสดงสถิติสุดท้าย
            positions = trader.get_active_positions()
            
            print(f"\n📊 Final Statistics:")
            print(f"   📡 Signals Sent: {len(trader.signals_sent)}")
            print(f"   💼 Total Trades: {trader.performance_data['total_trades']}")
            print(f"   ✅ Winning Trades: {trader.performance_data['winning_trades']}")
            print(f"   ❌ Losing Trades: {trader.performance_data['losing_trades']}")
            print(f"   🎯 Win Rate: {trader.performance_data['win_rate']:.1%}")
            print(f"   💰 Total Profit: ${trader.performance_data['total_profit']:.2f}")
            print(f"   📊 Avg Profit/Trade: ${trader.performance_data['avg_profit_per_trade']:.2f}")
            print(f"   🔥 Current Streak: {trader.performance_data['current_streak']}")
            print(f"   🎫 Active Positions: {len(positions)}")
            
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
                print(f"💵 Total Realized + Unrealized: ${trader.performance_data['total_profit'] + total_unrealized:.2f}")
                
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
                        if trader.close_position(pos.ticket, "Session end - close all"):
                            print(f"✅ Closed position {pos.ticket}")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                elif choice == "3":
                    # ปิดเฉพาะ positions ขาดทุน
                    losing_positions = [pos for pos in positions if pos.profit < 0]
                    for pos in losing_positions:
                        if trader.close_position(pos.ticket, "Session end - close losing"):
                            print(f"✅ Closed losing position {pos.ticket} (${pos.profit:.2f})")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                elif choice == "4":
                    # ปิดเฉพาะ positions กำไร
                    profitable_positions = [pos for pos in positions if pos.profit > 0]
                    for pos in profitable_positions:
                        if trader.close_position(pos.ticket, "Session end - close profitable"):
                            print(f"✅ Closed profitable position {pos.ticket} (${pos.profit:.2f})")
                        else:
                            print(f"❌ Failed to close position {pos.ticket}")
                
                else:
                    print("📋 All positions kept open")
            
            # คำนวณ efficiency
            if trader.performance_data['total_trades'] > 0:
                efficiency = (trader.performance_data['winning_trades'] / trader.performance_data['total_trades']) * 100
                avg_hold_time = duration / max(trader.performance_data['total_trades'], 1)
                trades_per_hour = trader.performance_data['total_trades'] / (duration / 60)
                
                print(f"\n⚡ Scalping Efficiency:")
                print(f"   📊 Trading Efficiency: {efficiency:.1f}%")
                print(f"   ⏰ Avg Hold Time: {avg_hold_time:.1f} minutes")
                print(f"   📈 Trades per Hour: {trades_per_hour:.1f}")
                
                if trader.performance_data['total_profit'] > 0:
                    profit_per_minute = trader.performance_data['total_profit'] / duration
                    print(f"   💰 Profit per Minute: ${profit_per_minute:.3f}")
        else:
            print(f"\n❌ Scalping session failed")
    
    except KeyboardInterrupt:
        print(f"\n⏹️ Scalping stopped by user")
        
        # ส่งข้อความแจ้งหยุด
        positions = trader.get_active_positions()
        
        stop_message = f"""
⏹️ <b>SCALPING STOPPED BY USER</b> ⏹️

📊 <b>Session Results:</b>
• Signals Sent: {len(trader.signals_sent)}
• Total Trades: {trader.performance_data['total_trades']}
• Win Rate: {trader.performance_data['win_rate']:.1%}
• Session P&L: ${trader.performance_data['total_profit']:.2f}
• Active Positions: {len(positions)}

<i>⚡ Gold Scalping Trader</i>
        """.strip()
        
        trader.send_telegram_message(stop_message)
    
    except Exception as e:
        print(f"\n❌ Scalping error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    run_scalping_trader()