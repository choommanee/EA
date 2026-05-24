"""
Test Gold Order - ทดสอบการเปิด order ทองใน MT5
"""

import sys
sys.path.append('.')

from gold_ai_trader import GoldAITrader
import MetaTrader5 as mt5

def test_gold_order():
    """ทดสอบการเปิด order ทอง"""
    print("🧪 Testing Gold Order Placement")
    print("=" * 40)
    
    # สร้าง trader พร้อมเปิด auto trading
    trader = GoldAITrader()
    trader.enable_auto_trading = True
    trader.tp_points = 150  # 15 pips TP
    trader.sl_points = 75   # 7.5 pips SL
    trader.lot_size = 0.01  # 0.01 lot
    
    try:
        # เชื่อมต่อ MT5
        if not trader.connect_mt5():
            print("❌ Cannot connect to MT5")
            return
        
        # ดู positions ปัจจุบัน
        print("\n📊 Current positions:")
        positions_summary = trader.get_positions_summary()
        print(positions_summary)
        
        # เทรนโมเดล
        print("\n🧠 Training model...")
        if not trader.train_gold_model():
            print("❌ Model training failed")
            return
        
        # ทำนายสัญญาณ
        print("\n🔮 Generating prediction...")
        prediction = trader.make_gold_prediction()
        
        if not prediction:
            print("❌ No prediction generated")
            return
        
        print(f"✅ Prediction: {prediction['signal']} ({prediction['confidence']:.1%})")
        
        # ทดสอบเปิด order
        if prediction['confidence'] > 0.5:  # ลด threshold สำหรับทดสอบ
            print("\n💼 Testing order placement...")
            
            order_info = trader.place_order(prediction['signal'], prediction['confidence'])
            
            if order_info:
                print("✅ Order placed successfully!")
                print(f"   Ticket: {order_info['ticket']}")
                print(f"   Signal: {order_info['signal']}")
                print(f"   Price: ${order_info['price']:.2f}")
                print(f"   TP: ${order_info['tp']:.2f}")
                print(f"   SL: ${order_info['sl']:.2f}")
                print(f"   Volume: {order_info['volume']} lots")
                
                # ส่งข้อความไป Telegram
                message = trader.format_telegram_message(prediction, order_info)
                if trader.send_telegram_message(message):
                    print("✅ Telegram notification sent!")
                
                # ถามว่าจะปิด order ทันทีหรือไม่
                close_now = input("\nClose order immediately? (y/n): ").strip().lower()
                if close_now == 'y':
                    if trader.close_position(order_info['ticket']):
                        print("✅ Order closed successfully!")
                    else:
                        print("❌ Failed to close order")
                
            else:
                print("❌ Failed to place order")
        else:
            print(f"⏭️ Confidence too low for testing: {prediction['confidence']:.1%}")
        
        # ดู positions หลังทดสอบ
        print("\n📊 Final positions:")
        positions_summary = trader.get_positions_summary()
        print(positions_summary)
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # ปิดการเชื่อมต่อ MT5
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    test_gold_order()