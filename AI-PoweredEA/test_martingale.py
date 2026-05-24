"""
Test Martingale System - ทดสอบระบบ Martingale + Trailing Stop
"""

import sys
sys.path.append('.')

from gold_martingale_trader import GoldMartingaleTrader
import MetaTrader5 as mt5

def test_martingale_system():
    """ทดสอบระบบ Martingale"""
    print("🧪 Testing Martingale System")
    print("=" * 40)
    
    # สร้าง trader
    trader = GoldMartingaleTrader()
    
    # ตั้งค่าสำหรับทดสอบ
    trader.enable_auto_trading = True
    trader.enable_martingale = True
    trader.enable_trailing_stop = True
    trader.base_lot_size = 0.01
    trader.tp_points = 150
    trader.sl_points = 75
    trader.max_martingale_levels = 3
    trader.martingale_distance = 100
    trader.trailing_start = 50
    trader.trailing_step = 25
    
    print(f"⚙️ Test Settings:")
    print(f"   Base Lot: {trader.base_lot_size}")
    print(f"   TP: {trader.tp_points} points")
    print(f"   SL: {trader.sl_points} points")
    print(f"   Max Martingale Levels: {trader.max_martingale_levels}")
    print(f"   Martingale Distance: {trader.martingale_distance} points")
    print(f"   Trailing Start: {trader.trailing_start} points")
    print(f"   Trailing Step: {trader.trailing_step} points")
    
    try:
        # เชื่อมต่อ MT5
        if not trader.connect_mt5():
            print("❌ Cannot connect to MT5")
            return
        
        # ดู positions ปัจจุบัน
        print("\n📊 Current positions:")
        positions = trader.get_active_positions()
        if positions:
            for pos in positions:
                print(f"   🎫 {pos.ticket}: {pos.type_str} {pos.volume} lots @ ${pos.price_open:.2f} (P&L: ${pos.profit:.2f})")
        else:
            print("   ไม่มี positions เปิดอยู่")
        
        # เทรนโมเดล
        print("\n🧠 Training model...")
        if not trader.train_model():
            print("❌ Model training failed")
            return
        
        # ทดสอบการทำนาย
        print("\n🔮 Testing prediction...")
        prediction = trader.make_prediction()
        
        if not prediction:
            print("❌ No prediction generated")
            return
        
        print(f"✅ Prediction: {prediction['signal']} ({prediction['confidence']:.1%})")
        print(f"   Current price: ${prediction['current_price']:.2f}")
        print(f"   Votes: {prediction['timeframe_votes']}")
        
        # ทดสอบ Martingale logic
        print(f"\n🔄 Testing Martingale logic for {prediction['signal']}...")
        should_martingale, current_level = trader.should_open_martingale(prediction['signal'])
        
        print(f"   Should open Martingale: {should_martingale}")
        print(f"   Current level: {current_level}")
        
        if should_martingale:
            lot_size = trader.calculate_martingale_lot_size(current_level)
            print(f"   Lot size for level {current_level}: {lot_size}")
            
            # ทดสอบเปิด order
            if prediction['confidence'] > 0.5:
                print(f"\n💼 Testing order placement...")
                
                if current_level == 0:
                    print("   Opening first position...")
                    order_info = trader.place_order(prediction['signal'], prediction['confidence'])
                else:
                    print(f"   Opening Martingale level {current_level}...")
                    order_info = trader.place_order(
                        prediction['signal'], 
                        prediction['confidence'], 
                        is_martingale=True, 
                        martingale_level=current_level
                    )
                
                if order_info:
                    print("✅ Order placed successfully!")
                    print(f"   Ticket: {order_info['ticket']}")
                    print(f"   Volume: {order_info['volume']} lots")
                    print(f"   Price: ${order_info['price']:.2f}")
                    print(f"   TP: ${order_info['tp']:.2f}")
                    print(f"   SL: ${order_info['sl']:.2f}")
                    
                    # ส่งข้อความไป Telegram
                    if current_level > 0:
                        martingale_info = {
                            'level': current_level,
                            'lot_size': order_info['volume'],
                            'multiplier': trader.martingale_multiplier ** current_level
                        }
                    else:
                        martingale_info = None
                    
                    message = trader.format_telegram_message(prediction, order_info, martingale_info)
                    if trader.send_telegram_message(message):
                        print("✅ Telegram notification sent!")
                    
                    # ทดสอบ Trailing Stop
                    print(f"\n📈 Testing Trailing Stop...")
                    trader.update_trailing_stops()
                    
                    # ทดสอบ Unified SL
                    if current_level > 0:
                        print(f"\n🔄 Testing Unified SL...")
                        trader.update_unified_sl_for_group(prediction['signal'])
                    
                else:
                    print("❌ Failed to place order")
            else:
                print(f"⏭️ Confidence too low: {prediction['confidence']:.1%}")
        else:
            print("   No Martingale needed")
        
        # แสดง positions หลังทดสอบ
        print(f"\n📊 Final positions:")
        positions = trader.get_active_positions()
        total_profit = 0
        
        if positions:
            for pos in positions:
                total_profit += pos.profit
                print(f"   🎫 {pos.ticket}: {pos.type_str} {pos.volume} lots @ ${pos.price_open:.2f}")
                print(f"      P&L: ${pos.profit:.2f}, TP: ${pos.tp:.2f}, SL: ${pos.sl:.2f}")
            
            print(f"\n💰 Total P&L: ${total_profit:.2f}")
            
            # ส่งสรุปไป Telegram
            summary_message = f"""
📊 <b>MARTINGALE TEST SUMMARY</b> 📊

🎫 <b>Active Positions:</b> {len(positions)}
💰 <b>Total P&L:</b> ${total_profit:.2f}
📈 <b>Orders Placed:</b> {trader.performance_data['total_orders']}
🔄 <b>Martingale Orders:</b> {trader.performance_data['martingale_orders']}

<i>🧪 Martingale Test Completed</i>
            """.strip()
            
            trader.send_telegram_message(summary_message)
        else:
            print("   ไม่มี positions เปิดอยู่")
        
        # ถามว่าจะปิด positions หรือไม่
        if positions:
            close_all = input(f"\nClose all {len(positions)} positions? (y/n): ").strip().lower()
            if close_all == 'y':
                for pos in positions:
                    if trader.close_position(pos.ticket):
                        print(f"✅ Closed position {pos.ticket}")
                    else:
                        print(f"❌ Failed to close position {pos.ticket}")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    test_martingale_system()