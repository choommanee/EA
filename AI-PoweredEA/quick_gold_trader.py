"""
Quick Gold Trader - รันระบบเทรดทองแบบง่ายๆ
ใช้ระบบ AI ที่พัฒนาไว้ + MT5 + Telegram
"""

import os
import sys
import time
import json
import requests
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Add Python directory to path
sys.path.append('Python')

class QuickGoldTrader:
    """ระบบเทรดทองแบบง่ายๆ"""
    
    def __init__(self):
        # Trading settings
        self.symbol = "GOLDm#"
        self.timeframes = [mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M15, mt5.TIMEFRAME_M30, mt5.TIMEFRAME_H1]
        self.tf_names = ["M5", "M15", "M30", "H1"]
        
        # AI model
        self.model = None
        self.scaler = StandardScaler()
        
        # Telegram (demo mode)
        self.telegram_enabled = False
        
        print("🥇 Quick Gold Trader initialized")
    
    def send_telegram(self, message):
        """ส่งข้อความ Telegram (demo mode)"""
        print(f"📱 Telegram: {message}")
        return True
    
    def connect_mt5(self):
        """เชื่อมต่อ MT5 และตรวจสอบ symbol ทอง"""
        try:
            print("🔌 Connecting to MT5...")
            
            if not mt5.initialize():
                print("❌ Cannot initialize MT5")
                print("💡 Please make sure:")
                print("   - MT5 is running")
                print("   - Allow automated trading is enabled")
                print("   - Python is allowed in MT5 settings")
                return False
            
            # ตรวจสอบข้อมูลบัญชี
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Cannot get account info")
                return False
            
            print(f"✅ MT5 connected successfully!")
            print(f"📊 Account: {account_info.login}")
            print(f"💰 Balance: ${account_info.balance:.2f}")
            print(f"🏢 Broker: {account_info.company}")
            
            # ตรวจสอบ symbol ทอง
            gold_symbol = self.check_gold_symbol()
            if gold_symbol:
                self.symbol = gold_symbol
                
                # ดูข้อมูล symbol
                symbol_info = mt5.symbol_info(self.symbol)
                tick_info = mt5.symbol_info_tick(self.symbol)
                
                if symbol_info and tick_info:
                    print(f"🥇 Gold Symbol: {self.symbol}")
                    print(f"💰 Current Price: ${tick_info.bid:.2f}")
                    print(f"📊 Spread: {symbol_info.spread} points")
                    return True
                else:
                    print(f"❌ Cannot get {self.symbol} info")
                    return False
            else:
                print("❌ No Gold symbol available")
                return False
                
        except Exception as e:
            print(f"❌ MT5 connection error: {e}")
            return False
    
    def check_gold_symbol(self):
        """ตรวจสอบ symbol ทองที่ใช้ได้"""
        gold_symbols = ["XAUUSD", "GOLD", "GOLDm#", "GOLD#", "XAU/USD"]
        
        for symbol in gold_symbols:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is not None:
                print(f"✅ Found Gold symbol: {symbol}")
                return symbol
        
        print("❌ No Gold symbol found in MT5")
        return None
    
    def get_gold_data(self, timeframe, timeframe_name):
        """ดึงข้อมูลทองจาก MT5 จริง"""
        try:
            # ตรวจสอบว่า MT5 เชื่อมต่ออยู่
            if not mt5.terminal_info():
                print(f"❌ MT5 not connected for {timeframe_name}")
                return None
            
            # ดึงข้อมูลจาก MT5
            rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, 100)
            
            if rates is None or len(rates) == 0:
                print(f"❌ No data for {self.symbol} on {timeframe_name}")
                return None
            
            # แปลงเป็น DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            print(f"✅ Got {len(df)} bars for {timeframe_name} - Latest price: ${df['close'].iloc[-1]:.2f}")
            return df
            
        except Exception as e:
            print(f"❌ Error getting {timeframe_name} data: {e}")
            return None
    
    def calculate_indicators(self, df):
        """คำนวณ indicators"""
        try:
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
            
            # EMA
            df['ema_20'] = df['close'].ewm(span=20).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            df['ema_signal'] = np.where(df['ema_20'] > df['ema_50'], 1, 0)
            
            # Volume
            df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
            
            return df
            
        except Exception as e:
            print(f"❌ Indicator calculation error: {e}")
            return None
    
    def train_model(self):
        """เทรนโมเดล AI"""
        print("🧠 Training Gold AI model...")
        
        all_X = []
        all_y = []
        
        # รวมข้อมูลจากทุก timeframe
        for i, timeframe in enumerate(self.timeframes):
            tf_name = self.tf_names[i]
            print(f"   📊 Processing {tf_name}...")
            
            # ดึงข้อมูล
            df = self.get_gold_data(timeframe, tf_name)
            if df is None:
                continue
            
            # คำนวณ indicators
            df = self.calculate_indicators(df)
            if df is None:
                continue
            
            # สร้าง labels
            df['future_return'] = df['close'].shift(-3) / df['close'] - 1
            threshold = 0.001  # 0.1%
            df['label'] = np.where(df['future_return'] > threshold, 1, 0)
            
            # เลือก features
            features = ['rsi', 'macd', 'bb_position', 'ema_signal', 'volume_ratio']
            
            # ลบ NaN
            df_clean = df[features + ['label']].dropna()
            
            if len(df_clean) > 20:
                X = df_clean[features].values
                y = df_clean['label'].values
                
                all_X.append(X)
                all_y.append(y)
        
        if not all_X:
            print("❌ No training data")
            return False
        
        # รวมข้อมูล
        X_combined = np.vstack(all_X)
        y_combined = np.hstack(all_y)
        
        # Normalize
        X_scaled = self.scaler.fit_transform(X_combined)
        
        # เทรนโมเดล
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.model.fit(X_scaled, y_combined)
        
        # ทดสอบ
        accuracy = self.model.score(X_scaled, y_combined)
        
        print(f"✅ Model trained - Accuracy: {accuracy:.1%}")
        return True
    
    def make_prediction(self):
        """ทำนายสัญญาณ"""
        if self.model is None:
            return None
        
        print("🔮 Analyzing Gold market...")
        
        predictions = {}
        
        # วิเคราะห์ทุก timeframe
        for i, timeframe in enumerate(self.timeframes):
            tf_name = self.tf_names[i]
            
            # ดึงข้อมูล
            df = self.get_gold_data(timeframe, tf_name)
            if df is None:
                continue
            
            # คำนวณ indicators
            df = self.calculate_indicators(df)
            if df is None:
                continue
            
            # เตรียม features
            features = ['rsi', 'macd', 'bb_position', 'ema_signal', 'volume_ratio']
            latest_data = df[features].iloc[-1:].values
            
            if np.isnan(latest_data).any():
                continue
            
            # Normalize และทำนาย
            features_scaled = self.scaler.transform(latest_data)
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            confidence = max(probability)
            
            signal = "BUY" if prediction == 1 else "SELL"
            predictions[tf_name] = {'signal': signal, 'confidence': confidence}
            
            print(f"   📊 {tf_name}: {signal} ({confidence:.1%})")
        
        if not predictions:
            return None
        
        # รวมสัญญาณ
        buy_votes = sum(1 for p in predictions.values() if p['signal'] == 'BUY')
        total_votes = len(predictions)
        
        final_signal = "BUY" if buy_votes > total_votes/2 else "SELL"
        avg_confidence = np.mean([p['confidence'] for p in predictions.values()])
        
        # ราคาปัจจุบันจาก MT5
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            current_price = tick.bid if tick else 0.0
        except:
            current_price = 0.0
        
        return {
            'signal': final_signal,
            'confidence': avg_confidence,
            'votes': f"{buy_votes}/{total_votes} BUY",
            'price': current_price,
            'timestamp': datetime.now()
        }
    
    def format_telegram_message(self, prediction):
        """จัดรูปแบบข้อความ"""
        signal = prediction['signal']
        confidence = prediction['confidence']
        price = prediction['price']
        votes = prediction['votes']
        
        emoji = "🟢📈" if signal == "BUY" else "🔴📉"
        action = "ซื้อ" if signal == "BUY" else "ขาย"
        
        if confidence > 0.8:
            strength = "แข็งแกร่งมาก 💪"
        elif confidence > 0.7:
            strength = "แข็งแกร่ง 👍"
        else:
            strength = "ปานกลาง ⚖️"
        
        message = f"""
🥇 GOLD AI SIGNAL 🥇

{emoji} สัญญาณ: {action} ({signal})
💰 ราคา: ${price:.2f}
🎯 ความมั่นใจ: {confidence:.1%}
💪 ความแข็งแกร่ง: {strength}
📊 Timeframe Votes: {votes}
⏰ เวลา: {prediction['timestamp'].strftime('%H:%M:%S')}

🤖 สร้างโดย Quick Gold AI Trader
        """.strip()
        
        return message
    
    def run_quick_trader(self, duration_minutes=30, interval_minutes=10):
        """รันระบบเทรดแบบง่าย"""
        print(f"🚀 Starting Quick Gold Trader")
        print(f"⏰ Duration: {duration_minutes} minutes")
        print(f"📡 Signal interval: {interval_minutes} minutes")
        
        # เชื่อมต่อ MT5
        mt5_connected = self.connect_mt5()
        
        # เทรนโมเดล
        if not self.train_model():
            print("❌ Cannot train model")
            return False
        
        # ส่งข้อความเริ่มต้น
        start_msg = f"""
🥇 Quick Gold Trader Started 🥇

🤖 AI Model: Ready
📊 Symbol: {self.symbol}
⏰ Duration: {duration_minutes} minutes
📡 Interval: {interval_minutes} minutes
🎯 Timeframes: {', '.join(self.tf_names)}
🔌 MT5: {'Connected' if mt5_connected else 'Demo Mode'}

🚀 Ready to analyze Gold!
        """.strip()
        
        self.send_telegram(start_msg)
        
        # เริ่มลูป
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        last_signal_time = datetime.now() - timedelta(minutes=interval_minutes)
        
        signals_sent = 0
        
        try:
            while datetime.now() < end_time:
                current_time = datetime.now()
                
                # ตรวจสอบเวลา
                if (current_time - last_signal_time).total_seconds() >= interval_minutes * 60:
                    
                    print(f"\n⏰ {current_time.strftime('%H:%M:%S')} - Analyzing...")
                    
                    # ทำนาย
                    prediction = self.make_prediction()
                    
                    if prediction and prediction['confidence'] > 0.6:
                        # ส่งสัญญาณ
                        message = self.format_telegram_message(prediction)
                        
                        if self.send_telegram(message):
                            signals_sent += 1
                            last_signal_time = current_time
                            
                            print(f"✅ Signal sent: {prediction['signal']} ({prediction['confidence']:.1%})")
                    else:
                        print("⏭️ No strong signal")
                
                # รอ 1 นาที
                time.sleep(60)
        
        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user")
        
        # สรุปผล
        end_msg = f"""
🏁 Quick Gold Trader Finished 🏁

📊 Summary:
• Signals sent: {signals_sent}
• Duration: {duration_minutes} minutes
• Status: Completed

🤖 Quick Gold Trader session ended
        """.strip()
        
        self.send_telegram(end_msg)
        
        print(f"\n🏁 Trading session completed!")
        print(f"📊 Signals sent: {signals_sent}")
        
        return True


def main():
    """ฟังก์ชันหลัก"""
    print("🥇 Quick Gold Trader")
    print("=" * 40)
    
    # สร้าง trader
    trader = QuickGoldTrader()
    
    # ตั้งค่า
    print("\n📊 Quick Settings:")
    duration = int(input("Duration (minutes, default 30): ") or "30")
    interval = int(input("Signal interval (minutes, default 10): ") or "10")
    
    print(f"\n🚀 Starting trader for {duration} minutes...")
    print("Press Ctrl+C to stop anytime")
    
    try:
        success = trader.run_quick_trader(duration, interval)
        
        if success:
            print("\n🎉 Trading completed successfully!")
        else:
            print("\n❌ Trading failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    finally:
        # ปิด MT5
        try:
            mt5.shutdown()
            print("🔌 MT5 connection closed")
        except:
            pass


if __name__ == "__main__":
    main()