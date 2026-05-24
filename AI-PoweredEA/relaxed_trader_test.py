#!/usr/bin/env python3
"""
Relaxed version for testing - เงื่อนไขหลวมขึ้นเพื่อทดสอบ
"""

import sys
from working_scalping_trader import WorkingGoldScalpingTrader

class RelaxedGoldTrader(WorkingGoldScalpingTrader):
    """Version ที่เงื่อนไขหลวมขึ้นเพื่อทดสอบ"""
    
    def __init__(self):
        super().__init__()
        # ปรับเงื่อนไขให้หลวมขึ้น
        self.max_spread = 50  # เพิ่ม spread limit
        
    def generate_bb_zigzag_ai_signal(self):
        """เงื่อนไขหลวมขึ้นเพื่อทดสอบ"""
        try:
            df = self.get_gold_data(self.main_timeframe, 100)
            if df is None:
                return None
            
            df = self.calculate_simple_indicators(df)
            if df is None:
                return None
            
            latest = df.iloc[-1]
            
            if pd.isna(latest['rsi']) or pd.isna(latest['bb_upper']) or pd.isna(latest['bb_lower']):
                return None
            
            bb_range = latest['bb_upper'] - latest['bb_lower']
            if bb_range <= 0:
                return None
            
            bb_position = (latest['close'] - latest['bb_lower']) / bb_range
            bb_width = bb_range / latest['close']
            
            print(f"📊 Current: RSI={latest['rsi']:.1f}, BB_pos={bb_position:.3f}, BB_width={bb_width:.4f}")
            print(f"📈 EMA: {latest['ema_10']:.2f} vs {latest['ema_20']:.2f}, Trend={latest['trend_strength']:.2f}")
            
            # เงื่อนไขหลวมขึ้น
            buy_signal = (
                bb_position <= 0.25 and        # หลวมขึ้น จาก 0.18
                latest['rsi'] <= 35 and        # หลวมขึ้น จาก 30
                bb_width >= 0.0005             # หลวมขึ้น จาก 0.001
                # ลบ EMA และ trend requirements ชั่วคราว
            )
            
            sell_signal = (
                bb_position >= 0.75 and        # หลวมขึ้น จาก 0.82
                latest['rsi'] >= 65 and        # หลวมขึ้น จาก 70
                bb_width >= 0.0005             # หลวมขึ้น จาก 0.001
                # ลบ EMA และ trend requirements ชั่วคราว
            )
            
            if buy_signal:
                print("🟢 BUY signal conditions met!")
                signal_type = "BUY"
                confidence = 0.75
                entry_reasons = [
                    f"BB Lower area (pos: {bb_position:.3f})",
                    f"Oversold RSI ({latest['rsi']:.1f})",
                    f"Sufficient volatility ({bb_width:.4f})"
                ]
            elif sell_signal:
                print("🔴 SELL signal conditions met!")
                signal_type = "SELL"
                confidence = 0.75
                entry_reasons = [
                    f"BB Upper area (pos: {bb_position:.3f})",
                    f"Overbought RSI ({latest['rsi']:.1f})",
                    f"Sufficient volatility ({bb_width:.4f})"
                ]
            else:
                print("⚪ No signal - conditions not met")
                return None
            
            return {
                'signal': signal_type,
                'confidence': confidence,
                'price': latest['close'],
                'rsi': latest['rsi'],
                'atr': latest['atr'],
                'bb_upper': latest['bb_upper'],
                'bb_lower': latest['bb_lower'],
                'bb_position': bb_position,
                'bb_width': bb_width,
                'ema_10': latest['ema_10'],
                'ema_20': latest['ema_20'],
                'trend_strength': latest['trend_strength'],
                'strong_trend_detected': False,
                'entry_reasons': entry_reasons,
                'base_confidence': confidence,
                'zigzag_data': {
                    'peak': latest.get('zigzag_peak', 0),
                    'trough': latest.get('zigzag_trough', 0)
                }
            }
            
        except Exception as e:
            print(f"❌ Relaxed signal error: {e}")
            return None

def test_relaxed_trader():
    """ทดสอบ trader เงื่อนไขหลวม"""
    print("🧪 TESTING RELAXED TRADER")
    print("=" * 40)
    
    trader = RelaxedGoldTrader()
    
    if not trader.connect_mt5():
        print("❌ Cannot connect to MT5")
        return
    
    print("✅ MT5 connected")
    
    # ทดสอบสร้างสัญญาณ
    for i in range(3):
        print(f"\n🔍 Test {i+1}:")
        signal = trader.generate_bb_zigzag_ai_signal()
        
        if signal:
            print(f"✅ Signal: {signal['signal']} @ ${signal['price']:.2f}")
            print(f"   Confidence: {signal['confidence']:.1%}")
            print(f"   Reasons: {', '.join(signal['entry_reasons'])}")
            break
        else:
            print("⚪ No signal")
        
        import time
        time.sleep(5)
    
    print("\n💡 If still no signals, market conditions are very neutral")
    print("   Try during more volatile market hours or news events")

if __name__ == "__main__":
    test_relaxed_trader()
