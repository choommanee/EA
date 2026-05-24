"""
Test Scalping System - ทดสอบระบบ Scalping
"""

import sys
sys.path.append('.')

from gold_scalping_trader import GoldScalpingTrader
import MetaTrader5 as mt5
import time

def test_scalping_system():
    """ทดสอบระบบ Scalping"""
    print("⚡ Testing Gold Scalping System")
    print("=" * 40)
    
    # สร้าง trader
    trader = GoldScalpingTrader()
    
    # ตั้งค่าสำหรับทดสอบ
    trader.enable_auto_trading = True
    trader.tp_points = 50      # 5 pips TP
    trader.sl_points = 30      # 3 pips SL
    trader.max_positions = 2   # จำกัด 2 positions
    trader.max_daily_trades = 10  # จำกัด 10 trades สำหรับทดสอบ
    trader.signal_interval_seconds = 10  # ตรวจทุก 10 วินาที
    
    print(f"⚙️ Test Settings:")
    print(f"   🎯 TP: {trader.tp_points} points ({trader.tp_points/10} pips)")
    print(f"   🛡️ SL: {trader.sl_points} points ({trader.sl_points/10} pips)")
    print(f"   📊 Max Positions: {trader.max_positions}")
    print(f"   📈 Max Trades: {trader.max_daily_trades}")
    print(f"   ⏰ Signal Interval: {trader.signal_interval_seconds} seconds")
    
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
        
        # ตรวจสอบสภาพตลาด
        print("\n🔍 Testing market conditions...")
        market_ok, market_msg = trader.check_market_conditions()
        print(f"   Market Status: {'✅ OK' if market_ok else '❌ Not Ready'}")
        print(f"   Message: {market_msg}")
        
        if not market_ok:
            print("⚠️ Market conditions not suitable for scalping")
            return
        
        # เทรนโมเดล
        print("\n⚡ Training scalping model...")
        if not trader.train_scalping_model():
            print("❌ Model training failed")
            return
        
        # ทดสอบการทำนาย
        print("\n🔮 Testing scalping prediction...")
        prediction = trader.make_scalping_prediction()
        
        if not prediction:
            print("❌ No prediction generated")
            return
        
        print(f"✅ Prediction: {prediction['signal']} ({prediction['confidence']:.1%})")
        print(f"   Current price: ${prediction['current_price']:.2f}")
        print(f"   Trend direction: {prediction['trend_direction']:+d}")
        print(f"   ATR: {prediction['atr']:.6f}")
        print(f"   RSI Fast: {prediction['rsi_fast']:.1f}")
        print(f"   MACD Fast: {prediction['macd_fast']:.6f}")
        
        # ทดสอบเปิด order
        if prediction['confidence'] > 0.7:
            print(f"\n💼 Testing scalping order placement...")
            
            order_info = trader.place_scalping_order(
                prediction['signal'], 
                prediction['confidence'],
                prediction
            )
            
            if order_info:
                print("✅ Scalping order placed successfully!")
                print(f"   Ticket: {order_info['ticket']}")
                print(f"   Signal: {order_info['signal']}")
                print(f"   Volume: {order_info['volume']} lots")
                print(f"   Price: ${order_info['price']:.2f}")
                print(f"   TP: ${order_info['tp']:.2f}")
                print(f"   SL: ${order_info['sl']:.2f}")
                print(f"   Expected Profit: ${order_info['expected_profit']:.2f}")
                print(f"   Max Loss: ${order_info['max_loss']:.2f}")
                
                # ส่งข้อความไป Telegram
                message = trader.format_scalping_message(prediction, order_info)
                if trader.send_telegram_message(message):
                    print("✅ Telegram notification sent!")
                
                # รอสักครู่แล้วจัดการ position
                print(f"\n⏳ Waiting 30 seconds to test position management...")
                time.sleep(30)
                
                print(f"\n📊 Testing position management...")
                trader.manage_scalping_positions()
                
                # ถามว่าจะปิด order ทันทีหรือไม่
                close_now = input(f"\nClose order immediately? (y/n): ").strip().lower()
                if close_now == 'y':
                    if trader.close_position(order_info['ticket'], "Manual test"):
                        print("✅ Order closed successfully!")
                    else:
                        print("❌ Failed to close order")
                
            else:
                print("❌ Failed to place scalping order")
        else:
            print(f"⏭️ Confidence too low for scalping: {prediction['confidence']:.1%}")
        
        # แสดง positions สุดท้าย
        print(f"\n📊 Final positions:")
        positions = trader.get_active_positions()
        total_profit = 0
        
        if positions:
            for pos in positions:
                total_profit += pos.profit
                print(f"   🎫 {pos.ticket}: {pos.type_str} {pos.volume} lots @ ${pos.price_open:.2f}")
                print(f"      P&L: ${pos.profit:.2f}, TP: ${pos.tp:.2f}, SL: ${pos.sl:.2f}")
            
            print(f"\n💰 Total P&L: ${total_profit:.2f}")
        else:
            print("   ไม่มี positions เปิดอยู่")
        
        # แสดงสถิติ
        print(f"\n📊 Performance Stats:")
        print(f"   Total Trades: {trader.performance_data['total_trades']}")
        print(f"   Winning Trades: {trader.performance_data['winning_trades']}")
        print(f"   Losing Trades: {trader.performance_data['losing_trades']}")
        print(f"   Win Rate: {trader.performance_data['win_rate']:.1%}")
        print(f"   Total Profit: ${trader.performance_data['total_profit']:.2f}")
        print(f"   Avg Profit/Trade: ${trader.performance_data['avg_profit_per_trade']:.2f}")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

def quick_scalping_test():
    """ทดสอบ scalping แบบเร็ว (5 นาที)"""
    print("⚡ Quick Scalping Test (5 minutes)")
    print("=" * 40)
    
    trader = GoldScalpingTrader()
    trader.max_daily_trades = 5
    trader.signal_interval_seconds = 15
    
    try:
        success = trader.run_scalping_session(5)  # รัน 5 นาที
        
        if success:
            print("✅ Quick scalping test completed!")
        else:
            print("❌ Quick scalping test failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Test stopped by user")
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    print("⚡ Gold Scalping Test Options:")
    print("1. Full System Test")
    print("2. Quick 5-minute Test")
    
    choice = input("Enter choice (1-2, default 1): ").strip() or "1"
    
    if choice == "1":
        test_scalping_system()
    elif choice == "2":
        quick_scalping_test()
    else:
        print("❌ Invalid choice")