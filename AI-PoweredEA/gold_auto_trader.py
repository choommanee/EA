"""
Gold Auto Trader - รันเทรดทองแบบอัตโนมัติพร้อมเปิด order
"""

import sys
sys.path.append('.')

from gold_ai_trader import GoldAITrader
import MetaTrader5 as mt5

def run_auto_gold_trader():
    """รันเทรดทองแบบอัตโนมัติ"""
    print("🤖 Gold Auto Trader")
    print("=" * 40)
    
    # สร้าง trader พร้อมตั้งค่า
    trader = GoldAITrader()
    
    # ตั้งค่าการเทรดอัตโนมัติ
    trader.enable_auto_trading = True
    trader.tp_points = 200      # 20 pips TP
    trader.sl_points = 100      # 10 pips SL
    trader.lot_size = 0.01      # 0.01 lot
    trader.max_positions = 2    # เปิดได้สูงสุด 2 positions
    
    print(f"⚙️ Auto Trading Settings:")
    print(f"   TP: {trader.tp_points} points")
    print(f"   SL: {trader.sl_points} points")
    print(f"   Lot Size: {trader.lot_size}")
    print(f"   Max Positions: {trader.max_positions}")
    
    # เริ่มต้นคอมโพเนนต์ AI
    trader.initialize_ai_components()
    
    try:
        # รันเทรด 60 นาที, ส่งสัญญาณทุก 10 นาที
        print("\n🚀 Starting auto trading...")
        print("   Duration: 60 minutes")
        print("   Signal interval: 10 minutes")
        print("   Auto trading: ENABLED")
        
        success = trader.run_gold_trader(duration_minutes=60, signal_interval_minutes=10)
        
        if success:
            print("\n🎉 Auto trading completed successfully!")
            
            # แสดงสรุปผลการเทรด
            print(f"\n📊 Trading Summary:")
            print(f"   Total signals: {trader.performance_data['total_signals']}")
            print(f"   Total orders: {trader.performance_data['total_orders']}")
            print(f"   Successful orders: {trader.performance_data['successful_orders']}")
            print(f"   Failed orders: {trader.performance_data['failed_orders']}")
            print(f"   Total profit: ${trader.performance_data['total_profit']:.2f}")
            
            # ดู positions ที่เหลือ
            positions_summary = trader.get_positions_summary()
            print(f"\n{positions_summary}")
            
            # ส่งสรุปไป Telegram
            summary_message = f"""
🏁 <b>AUTO TRADING COMPLETED</b> 🏁

📊 <b>Trading Summary:</b>
• Total Signals: {trader.performance_data['total_signals']}
• Orders Placed: {trader.performance_data['total_orders']}
• Successful Orders: {trader.performance_data['successful_orders']}
• Failed Orders: {trader.performance_data['failed_orders']}
• Total P&L: ${trader.performance_data['total_profit']:.2f}

📈 <b>Current Positions:</b>
{positions_summary}

<i>🤖 Gold Auto Trader</i>
            """.strip()
            
            trader.send_telegram_message(summary_message)
            
        else:
            print("\n❌ Auto trading failed")
            
    except KeyboardInterrupt:
        print("\n⏹️ Auto trading stopped by user")
        
        # ส่งข้อความแจ้งหยุด
        stop_message = f"""
⏹️ <b>AUTO TRADING STOPPED</b> ⏹️

📊 <b>Partial Results:</b>
• Signals Sent: {trader.performance_data['total_signals']}
• Orders Placed: {trader.performance_data['total_orders']}

{trader.get_positions_summary()}

<i>🤖 Gold Auto Trader</i>
        """.strip()
        
        trader.send_telegram_message(stop_message)
        
    except Exception as e:
        print(f"\n❌ Auto trading error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # ปิดการเชื่อมต่อ MT5
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    run_auto_gold_trader()