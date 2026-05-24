"""
Real AI Trader - ระบบเทรด AI ที่ใช้งานได้จริง
เชื่อมต่อกับ MT5 และเทรดได้จริง
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class RealAITrader:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_connected = False
        self.account_info = None
        self.trading_pairs = ["EURUSD", "GBPUSD", "USDJPY"]
        self.lot_size = 0.01  # ขนาดการเทรด
        self.max_spread = 20  # spread สูงสุดที่ยอมรับได้ (points)
        
    def connect_mt5(self):
        """เชื่อมต่อกับ MT5"""
        print("🔌 กำลังเชื่อมต่อ MT5...")
        
        if not mt5.initialize():
            print("❌ ไม่สามารถเชื่อมต่อ MT5 ได้")
            print("💡 กรุณาตรวจสอบ:")
            print("   - เปิด MT5 แล้วหรือยัง")
            print("   - อนุญาต Algo Trading ใน Tools > Options > Expert Advisors")
            return False
        
        # ดูข้อมูลบัญชี
        account_info = mt5.account_info()
        if account_info is None:
            print("❌ ไม่สามารถดูข้อมูลบัญชีได้")
            return False
        
        self.account_info = account_info._asdict()
        self.is_connected = True
        
        print("✅ เชื่อมต่อ MT5 สำเร็จ!")
        print(f"📊 บัญชี: {self.account_info['login']}")
        print(f"💰 ยอดเงิน: ${self.account_info['balance']:.2f}")
        print(f"🏢 โบรกเกอร์: {self.account_info['company']}")
        
        return True
    
    def get_market_data(self, symbol, timeframe=mt5.TIMEFRAME_H1, count=100):
        """ดึงข้อมูลตลาดจาก MT5"""
        if not self.is_connected:
            print("❌ ยังไม่ได้เชื่อมต่อ MT5")
            return None
        
        # ดึงข้อมูลราคา
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        
        if rates is None:
            print(f"❌ ไม่สามารถดึงข้อมูล {symbol} ได้")
            return None
        
        # แปลงเป็น DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df
    
    def calculate_indicators(self, df):
        """คำนวณ Technical Indicators"""
        if df is None or len(df) < 50:
            return None
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Moving Averages
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        df['ema_signal'] = np.where(df['ema_20'] > df['ema_50'], 1, 0)
        
        # Volume (ใช้ tick_volume แทน)
        df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
        
        return df
    
    def prepare_features(self, df):
        """เตรียมข้อมูลสำหรับโมเดล"""
        if df is None:
            return None
        
        # เลือก features
        features = ['rsi', 'macd', 'bb_position', 'ema_signal', 'volume_ratio']
        
        # ตรวจสอบว่ามี features ครบ
        for feature in features:
            if feature not in df.columns:
                print(f"❌ ไม่มี feature: {feature}")
                return None
        
        # ดึงข้อมูลล่าสุด
        latest_data = df[features].iloc[-1:].values
        
        # ตรวจสอบ NaN
        if np.isnan(latest_data).any():
            print("⚠️ มีข้อมูลที่เป็น NaN")
            return None
        
        return latest_data
    
    def create_training_data(self, symbol):
        """สร้างข้อมูลสำหรับเทรนโมเดล"""
        print(f"📊 กำลังสร้างข้อมูลเทรนสำหรับ {symbol}...")
        
        # ดึงข้อมูลย้อนหลัง 1000 bars
        df = self.get_market_data(symbol, count=1000)
        if df is None:
            return None, None
        
        # คำนวณ indicators
        df = self.calculate_indicators(df)
        if df is None:
            return None, None
        
        # สร้าง labels (1 = BUY, 0 = SELL)
        # ใช้การเปลี่ยนแปลงราคาในอนาคต 5 bars
        df['future_return'] = df['close'].shift(-5) / df['close'] - 1
        df['label'] = np.where(df['future_return'] > 0.0001, 1, 0)  # 1 pip = 0.0001
        
        # เลือก features
        features = ['rsi', 'macd', 'bb_position', 'ema_signal', 'volume_ratio']
        
        # ลบ NaN
        df_clean = df[features + ['label']].dropna()
        
        if len(df_clean) < 100:
            print(f"❌ ข้อมูลไม่เพียงพอสำหรับ {symbol}")
            return None, None
        
        X = df_clean[features].values
        y = df_clean['label'].values
        
        print(f"✅ สร้างข้อมูลเทรนสำเร็จ: {len(X)} samples")
        return X, y
    
    def train_model(self):
        """เทรนโมเดล AI"""
        print("🧠 กำลังเทรนโมเดล AI...")
        
        all_X = []
        all_y = []
        
        # รวมข้อมูลจากทุกคู่เงิน
        for symbol in self.trading_pairs:
            X, y = self.create_training_data(symbol)
            if X is not None and y is not None:
                all_X.append(X)
                all_y.append(y)
        
        if not all_X:
            print("❌ ไม่มีข้อมูลสำหรับเทรนโมเดล")
            return False
        
        # รวมข้อมูลทั้งหมด
        X_combined = np.vstack(all_X)
        y_combined = np.hstack(all_y)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X_combined)
        
        # สร้างและเทรนโมเดล
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_scaled, y_combined)
        
        # ทดสอบโมเดล
        accuracy = self.model.score(X_scaled, y_combined)
        
        print(f"✅ เทรนโมเดลสำเร็จ!")
        print(f"📊 Accuracy: {accuracy:.2%}")
        print(f"📈 Training samples: {len(X_combined)}")
        
        return True
    
    def get_prediction(self, symbol):
        """ทำนายสัญญาณการเทรด"""
        if self.model is None:
            print("❌ ยังไม่ได้เทรนโมเดล")
            return None
        
        # ดึงข้อมูลปัจจุบัน
        df = self.get_market_data(symbol)
        if df is None:
            return None
        
        # คำนวณ indicators
        df = self.calculate_indicators(df)
        if df is None:
            return None
        
        # เตรียม features
        features = self.prepare_features(df)
        if features is None:
            return None
        
        # Normalize
        features_scaled = self.scaler.transform(features)
        
        # ทำนาย
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        confidence = max(probability)
        
        signal = "BUY" if prediction == 1 else "SELL"
        
        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'probability': probability,
            'current_price': df['close'].iloc[-1]
        }
    
    def check_spread(self, symbol):
        """ตรวจสอบ spread"""
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return False
        
        spread = (tick.ask - tick.bid) / mt5.symbol_info(symbol).point
        return spread <= self.max_spread
    
    def place_order(self, symbol, order_type, volume=None):
        """ส่งคำสั่งเทรด"""
        if not self.is_connected:
            print("❌ ยังไม่ได้เชื่อมต่อ MT5")
            return False
        
        if volume is None:
            volume = self.lot_size
        
        # ตรวจสอบ spread
        if not self.check_spread(symbol):
            print(f"⚠️ Spread ของ {symbol} สูงเกินไป")
            return False
        
        # ดูข้อมูล symbol
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ ไม่พบข้อมูล {symbol}")
            return False
        
        # ดูราคาปัจจุบัน
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"❌ ไม่สามารถดูราคา {symbol} ได้")
            return False
        
        # กำหนดราคา
        if order_type == "BUY":
            price = tick.ask
            mt5_order_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            mt5_order_type = mt5.ORDER_TYPE_SELL
        
        # สร้างคำสั่ง
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "deviation": 20,
            "magic": 12345,
            "comment": "AI Trader",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # ส่งคำสั่ง
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ ส่งคำสั่งไม่สำเร็จ: {result.comment}")
            return False
        
        print(f"✅ ส่งคำสั่งสำเร็จ: {order_type} {volume} {symbol} @ {price}")
        print(f"📋 Order ID: {result.order}")
        
        return True
    
    def get_positions(self):
        """ดู positions ปัจจุบัน"""
        positions = mt5.positions_get()
        if positions is None:
            return []
        
        return [pos._asdict() for pos in positions]
    
    def close_position(self, ticket):
        """ปิด position"""
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            print(f"❌ ไม่พบ position {ticket}")
            return False
        
        position = positions[0]
        
        # กำหนดประเภทคำสั่งปิด
        if position.type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(position.symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(position.symbol).ask
        
        # สร้างคำสั่งปิด
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 12345,
            "comment": "AI Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ ปิด position ไม่สำเร็จ: {result.comment}")
            return False
        
        print(f"✅ ปิด position สำเร็จ: {position.symbol}")
        return True
    
    def run_trading_session(self, duration_minutes=60):
        """รันเซสชันการเทรด"""
        print(f"🚀 เริ่มเซสชันการเทรด ({duration_minutes} นาที)")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        trades_made = 0
        
        while datetime.now() < end_time:
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
            
            # วิเคราะห์แต่ละคู่เงิน
            for symbol in self.trading_pairs:
                print(f"\n📊 วิเคราะห์ {symbol}...")
                
                prediction = self.get_prediction(symbol)
                if prediction is None:
                    continue
                
                print(f"🎯 สัญญาณ: {prediction['signal']}")
                print(f"💪 ความมั่นใจ: {prediction['confidence']:.1%}")
                print(f"💰 ราคาปัจจุบัน: {prediction['current_price']}")
                
                # เทรดถ้า confidence สูงพอ
                if prediction['confidence'] > 0.7:
                    print(f"✅ ส่งคำสั่งเทรด {prediction['signal']} {symbol}")
                    
                    success = self.place_order(symbol, prediction['signal'])
                    if success:
                        trades_made += 1
                else:
                    print("⏭️ ข้าม - confidence ต่ำเกินไป")
            
            # ดู positions ปัจจุบัน
            positions = self.get_positions()
            if positions:
                print(f"\n📋 Positions ปัจจุบัน: {len(positions)}")
                for pos in positions:
                    profit = pos['profit']
                    print(f"   {pos['symbol']} {pos['type']} - P&L: {profit:+.2f}")
            
            # รอ 5 นาที
            print("\n⏳ รอ 5 นาที...")
            time.sleep(300)  # 5 minutes
        
        print(f"\n🏁 เซสชันเสร็จสิ้น!")
        print(f"📊 จำนวนเทรดที่ทำ: {trades_made}")
        
        # สรุปผล
        final_positions = self.get_positions()
        if final_positions:
            total_profit = sum(pos['profit'] for pos in final_positions)
            print(f"💰 กำไร/ขาดทุนรวม: {total_profit:+.2f}")

def main():
    """ฟังก์ชันหลัก"""
    print("🤖 Real AI Trader - ระบบเทรด AI จริง")
    print("=" * 50)
    
    # สร้าง trader
    trader = RealAITrader()
    
    # เชื่อมต่อ MT5
    if not trader.connect_mt5():
        print("\n❌ ไม่สามารถเชื่อมต่อ MT5 ได้")
        print("💡 วิธีแก้ไข:")
        print("1. เปิด MT5")
        print("2. ไป Tools > Options > Expert Advisors")
        print("3. เปิด 'Allow automated trading'")
        print("4. เปิด 'Allow DLL imports'")
        return
    
    # เทรนโมเดล
    if not trader.train_model():
        print("\n❌ ไม่สามารถเทรนโมเดลได้")
        return
    
    # ทดสอบการทำนาย
    print("\n🔮 ทดสอบการทำนาย...")
    for symbol in trader.trading_pairs:
        prediction = trader.get_prediction(symbol)
        if prediction:
            print(f"{symbol}: {prediction['signal']} ({prediction['confidence']:.1%})")
    
    # ถามผู้ใช้ว่าต้องการเทรดจริงไหม
    print("\n" + "=" * 50)
    choice = input("🚨 ต้องการเทรดด้วยเงินจริงไหม? (y/N): ").lower()
    
    if choice == 'y':
        print("⚠️ กำลังเทรดด้วยเงินจริง!")
        duration = int(input("⏰ ระยะเวลาการเทรด (นาที): ") or "60")
        trader.run_trading_session(duration)
    else:
        print("✅ ยกเลิกการเทรด - ปลอดภัย!")
        print("💡 คุณสามารถทดสอบการทำนายได้โดยไม่เทรดจริง")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ หยุดการทำงานโดยผู้ใช้")
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # ปิดการเชื่อมต่อ MT5
        mt5.shutdown()
        print("🔌 ปิดการเชื่อมต่อ MT5 แล้ว")