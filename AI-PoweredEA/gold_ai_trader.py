"""
Gold AI Trader - ระบบเทรดทองด้วย AI + Telegram
ใช้ระบบ AI ที่พัฒนาไว้แล้ว + MT5 + Telegram
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

# Import AI components
try:
    from performance_monitor import PerformanceMonitor
    from model_manager import ModelManager, ModelType
    from learning_metrics_collector import LearningMetricsCollector
    from learning_notification_system import LearningNotificationSystem
except ImportError as e:
    print(f"Warning: Could not import AI components: {e}")
    print("Running in standalone mode...")

class GoldAITrader:
    """ระบบเทรดทองด้วย AI + Telegram"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        # Telegram settings
        self.telegram_token = telegram_token or "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
        self.chat_id = chat_id or "-1002852894581"  # Updated supergroup chat ID
        
        # Trading settings
        self.symbol = "GOLDm#"  # Gold symbol in MT5
        self.timeframes = [mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M15, mt5.TIMEFRAME_M30, mt5.TIMEFRAME_H1]
        self.timeframe_names = ["M5", "M15", "M30", "H1"]
        self.lot_size = 0.01
        self.max_spread = 50  # points
        
        # Risk Management settings
        self.tp_points = 200    # Take Profit in points (20 pips for Gold)
        self.sl_points = 100    # Stop Loss in points (10 pips for Gold)
        self.enable_auto_trading = True  # เปิด/ปิดการเทรดอัตโนมัติ
        self.max_positions = 5  # จำนวน position สูงสุดที่เปิดได้
        
        # Martingale settings
        self.enable_martingale = True   # เปิด/ปิด Martingale
        self.martingale_multiplier = 2.0  # ตัวคูณ lot (2 เท่า)
        self.max_martingale_levels = 4   # ระดับ Martingale สูงสุด (0.1, 0.2, 0.4, 0.8)
        self.martingale_distance = 150   # ระยะห่างเปิด Martingale (points)
        
        # Trailing Stop settings
        self.enable_trailing_stop = True  # เปิด/ปิด Trailing Stop
        self.trailing_start = 100         # เริ่ม trailing เมื่อกำไร 100 points
        self.trailing_step = 50           # ระยะ trailing (points)
        
        # Position tracking
        self.position_groups = {}  # เก็บกลุม positions ตาม signal
        self.last_signal_direction = None
        self.current_martingale_level = 0
        
        # AI components
        self.model = None
        self.scaler = StandardScaler()
        self.performance_monitor = None
        self.model_manager = None
        self.metrics_collector = None
        
        # Trading data
        self.signals_sent = []
        self.orders_placed = []
        self.performance_data = {
            'total_signals': 0,
            'correct_signals': 0,
            'total_profit': 0.0,
            'accuracy': 0.0,
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0
        }
        
        print("🥇 Gold AI Trader initialized")
    
    def send_telegram_message(self, message):
        """ส่งข้อความไป Telegram"""
        try:
            print(f"📱 Sending to Telegram...")
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            print(f"🔗 URL: {url}")
            print(f"📊 Chat ID: {self.chat_id}")
            
            response = requests.post(url, data=data, timeout=10)
            
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Telegram message sent successfully!")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
            return False
    
    def connect_mt5(self):
        """เชื่อมต่อ MT5"""
        try:
            if not mt5.initialize():
                print("❌ MT5 connection failed")
                return False
            
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Cannot get account info")
                return False
            
            print(f"✅ MT5 connected - Account: {account_info.login}")
            print(f"💰 Balance: ${account_info.balance:.2f}")
            
            # ตรวจสอบ symbol ทองที่ใช้ได้
            gold_symbols = ["XAUUSD", "GOLD", "GOLDm#", "GOLD#", "XAU/USD"]
            found_symbol = None
            
            for symbol in gold_symbols:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is not None:
                    found_symbol = symbol
                    self.symbol = symbol
                    break
            
            if found_symbol is None:
                print("❌ No Gold symbol found")
                return False
            
            # ดูข้อมูล symbol และราคาปัจจุบัน
            symbol_info = mt5.symbol_info(self.symbol)
            tick_info = mt5.symbol_info_tick(self.symbol)
            
            print(f"🥇 Gold symbol: {self.symbol}")
            print(f"💰 Current price: ${tick_info.bid:.2f}")
            print(f"📊 Spread: {symbol_info.spread} points")
            return True
            
        except Exception as e:
            print(f"❌ MT5 connection error: {e}")
            return False
    
    def get_gold_data(self, timeframe, count=100):
        """ดึงข้อมูลทองจาก MT5"""
        try:
            # ตรวจสอบการเชื่อมต่อ MT5
            if not mt5.terminal_info():
                print("❌ MT5 not connected")
                return None
            
            # ดึงข้อมูลจาก MT5
            rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                print(f"❌ No data available for {self.symbol}")
                return None
            
            # แปลงเป็น DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # แสดงข้อมูลล่าสุด
            latest_price = df['close'].iloc[-1]
            print(f"✅ Got {len(df)} bars - Latest: ${latest_price:.2f}")
            
            return df
            
        except Exception as e:
            print(f"❌ Data retrieval error: {e}")
            return None
    
    def calculate_indicators(self, df):
        """คำนวณ Technical Indicators สำหรับทอง"""
        try:
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
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
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
            
            # ATR (Average True Range) - สำคัญสำหรับทอง
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            df['atr'] = df['true_range'].rolling(window=14).mean()
            
            # Volume ratio
            df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
            
            return df
            
        except Exception as e:
            print(f"❌ Indicator calculation error: {e}")
            return None
    
    def create_training_data(self):
        """สร้างข้อมูลเทรนโมเดลจากหลาย timeframe"""
        print("🧠 Creating training data for Gold...")
        
        all_features = []
        all_labels = []
        
        for i, timeframe in enumerate(self.timeframes):
            tf_name = self.timeframe_names[i]
            print(f"   📊 Processing {tf_name} data...")
            
            # ดึงข้อมูล
            df = self.get_gold_data(timeframe, 500)
            if df is None:
                continue
            
            # คำนวณ indicators
            df = self.calculate_indicators(df)
            if df is None:
                continue
            
            # สร้าง labels (1=BUY, 0=SELL)
            # ใช้การเปลี่ยนแปลงราคาในอนาคต
            future_bars = 5 if timeframe <= mt5.TIMEFRAME_M15 else 3
            df['future_return'] = df['close'].shift(-future_bars) / df['close'] - 1
            
            # กำหนด threshold ตาม timeframe
            if timeframe == mt5.TIMEFRAME_M5:
                threshold = 0.0005  # 0.05%
            elif timeframe == mt5.TIMEFRAME_M15:
                threshold = 0.001   # 0.1%
            elif timeframe == mt5.TIMEFRAME_M30:
                threshold = 0.0015  # 0.15%
            else:  # H1
                threshold = 0.002   # 0.2%
            
            df['label'] = np.where(df['future_return'] > threshold, 1, 0)
            
            # เลือก features
            features = ['rsi', 'macd', 'macd_histogram', 'bb_position', 'ema_signal', 'atr', 'volume_ratio']
            
            # ลบ NaN
            df_clean = df[features + ['label']].dropna()
            
            if len(df_clean) > 50:
                X = df_clean[features].values
                y = df_clean['label'].values
                
                all_features.append(X)
                all_labels.append(y)
                
                print(f"   ✅ {tf_name}: {len(X)} samples")
        
        if not all_features:
            print("❌ No training data available")
            return None, None
        
        # รวมข้อมูลทั้งหมด
        X_combined = np.vstack(all_features)
        y_combined = np.hstack(all_labels)
        
        print(f"✅ Total training samples: {len(X_combined)}")
        return X_combined, y_combined
    
    def train_gold_model(self):
        """เทรนโมเดล AI สำหรับทอง"""
        print("🧠 Training Gold AI model...")
        
        # สร้างข้อมูลเทรน
        X, y = self.create_training_data()
        if X is None:
            return False
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # สร้างและเทรนโมเดล
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_scaled, y)
        
        # ทดสอบโมเดล
        accuracy = self.model.score(X_scaled, y)
        
        print(f"✅ Gold model trained successfully!")
        print(f"📊 Training accuracy: {accuracy:.2%}")
        print(f"📈 Features: RSI, MACD, BB, EMA, ATR, Volume")
        
        # บันทึกโมเดลด้วย Model Manager (ถ้ามี)
        try:
            if self.model_manager:
                performance_metrics = {'accuracy': accuracy}
                self.model_manager.save_model(
                    model=self.model,
                    model_name="Gold_AI_Model",
                    model_type=ModelType.CLASSIFICATION,
                    performance_metrics=performance_metrics,
                    metadata={'symbol': self.symbol, 'timeframes': self.timeframe_names}
                )
                print("✅ Model saved to Model Manager")
        except Exception as e:
            print(f"⚠️ Could not save to Model Manager: {e}")
        
        return True
    
    def get_current_features(self, timeframe):
        """ดึง features ปัจจุบันสำหรับทำนาย"""
        try:
            df = self.get_gold_data(timeframe, 100)
            if df is None:
                return None
            
            df = self.calculate_indicators(df)
            if df is None:
                return None
            
            # เลือก features ล่าสุด
            features = ['rsi', 'macd', 'macd_histogram', 'bb_position', 'ema_signal', 'atr', 'volume_ratio']
            latest_data = df[features].iloc[-1:].values
            
            # ตรวจสอบ NaN
            if np.isnan(latest_data).any():
                return None
            
            return latest_data
            
        except Exception as e:
            print(f"❌ Feature extraction error: {e}")
            return None
    
    def make_gold_prediction(self):
        """ทำนายสัญญาณทอง"""
        if self.model is None:
            print("❌ No model available")
            return None
        
        print("🔮 Analyzing Gold market...")
        
        predictions = {}
        
        # วิเคราะห์ทุก timeframe
        for i, timeframe in enumerate(self.timeframes):
            tf_name = self.timeframe_names[i]
            
            # ดึง features
            features = self.get_current_features(timeframe)
            if features is None:
                continue
            
            # Normalize
            features_scaled = self.scaler.transform(features)
            
            # ทำนาย
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            confidence = max(probability)
            
            signal = "BUY" if prediction == 1 else "SELL"
            
            predictions[tf_name] = {
                'signal': signal,
                'confidence': confidence,
                'probability': probability
            }
            
            print(f"   📊 {tf_name}: {signal} ({confidence:.1%})")
        
        if not predictions:
            return None
        
        # รวมสัญญาณจากทุก timeframe
        buy_votes = sum(1 for p in predictions.values() if p['signal'] == 'BUY')
        sell_votes = len(predictions) - buy_votes
        
        # คำนวณ confidence รวม
        avg_confidence = np.mean([p['confidence'] for p in predictions.values()])
        
        # ตัดสินใจสัญญาณรวม
        if buy_votes > sell_votes:
            final_signal = "BUY"
            signal_strength = buy_votes / len(predictions)
        else:
            final_signal = "SELL"
            signal_strength = sell_votes / len(predictions)
        
        # ดูราคาปัจจุบัน
        tick = mt5.symbol_info_tick(self.symbol)
        current_price = tick.bid if tick else 0
        
        result = {
            'symbol': self.symbol,
            'signal': final_signal,
            'confidence': avg_confidence,
            'signal_strength': signal_strength,
            'timeframe_votes': f"{buy_votes} BUY, {sell_votes} SELL",
            'current_price': current_price,
            'predictions': predictions,
            'timestamp': datetime.now()
        }
        
        return result
    
    def format_telegram_message(self, prediction, order_info=None):
        """จัดรูปแบบข้อความ Telegram"""
        signal = prediction['signal']
        confidence = prediction['confidence']
        price = prediction['current_price']
        votes = prediction['timeframe_votes']
        
        # เลือก emoji
        if signal == "BUY":
            emoji = "🟢📈"
            action = "ซื้อ"
        else:
            emoji = "🔴📉"
            action = "ขาย"
        
        # ประเมินความแข็งแกร่งของสัญญาณ
        if confidence > 0.8:
            strength = "แข็งแกร่งมาก 💪"
        elif confidence > 0.7:
            strength = "แข็งแกร่ง 👍"
        elif confidence > 0.6:
            strength = "ปานกลาง ⚖️"
        else:
            strength = "อ่อน ⚠️"
        
        # คำนวณ TP/SL สำหรับแสดง
        tp, sl = self.calculate_tp_sl(signal, price)
        
        message = f"""
🥇 <b>GOLD AI SIGNAL</b> 🥇

{emoji} <b>สัญญาณ: {action} ({signal})</b>
� <b>Tราคาเข้า:</b> ${price:.2f}
🎯 <b>Take Profit:</b> ${tp:.2f} (+{self.tp_points} points)
🛡️ <b>Stop Loss:</b> ${sl:.2f} (-{self.sl_points} points)
�  <b>ความมั่นใจ:</b> {confidence:.1%}
💪 <b>ความแข็งแกร่ง:</b> {strength}
📈 <b>Timeframe Votes:</b> {votes}
"""
        
        # เพิ่มข้อมูล order ถ้ามี
        if order_info:
            message += f"""
💼 <b>ORDER PLACED:</b>
🎫 <b>Ticket:</b> {order_info['ticket']}
📊 <b>Volume:</b> {order_info['volume']} lots
✅ <b>Status:</b> Executed
"""
        else:
            message += f"""
⚠️ <b>SIGNAL ONLY</b> (Auto trading disabled)
"""
        
        message += f"""
⏰ <b>เวลา:</b> {prediction['timestamp'].strftime('%H:%M:%S')}
📅 <b>วันที่:</b> {prediction['timestamp'].strftime('%d/%m/%Y')}

<i>🤖 สร้างโดย Gold AI Trader</i>
        """.strip()
        
        return message
    
    def check_spread(self):
        """ตรวจสอบ spread ของทอง"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            symbol_info = mt5.symbol_info(self.symbol)
            
            if tick and symbol_info:
                spread = (tick.ask - tick.bid) / symbol_info.point
                return spread <= self.max_spread
            
            return False
            
        except Exception as e:
            print(f"❌ Spread check error: {e}")
            return False
    
    def calculate_tp_sl(self, signal, entry_price):
        """คำนวณ Take Profit และ Stop Loss"""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                return None, None
            
            point = symbol_info.point
            
            if signal == "BUY":
                tp = entry_price + (self.tp_points * point)
                sl = entry_price - (self.sl_points * point)
            else:  # SELL
                tp = entry_price - (self.tp_points * point)
                sl = entry_price + (self.sl_points * point)
            
            return tp, sl
            
        except Exception as e:
            print(f"❌ TP/SL calculation error: {e}")
            return None, None
    
    def get_active_positions(self):
        """ดึงรายการ position ที่เปิดอยู่"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if positions is None:
                return []
            
            return list(positions)
            
        except Exception as e:
            print(f"❌ Get positions error: {e}")
            return []
    
    def place_order(self, signal, confidence, is_martingale=False, martingale_level=0):
        """เปิด order ใน MT5 พร้อม Martingale support"""
        try:
            if not self.enable_auto_trading:
                print("⚠️ Auto trading disabled")
                return None
            
            # ตรวจสอบจำนวน position ที่เปิดอยู่
            active_positions = self.get_active_positions()
            if len(active_positions) >= self.max_positions:
                print(f"⚠️ Maximum positions reached: {len(active_positions)}/{self.max_positions}")
                return None
            
            # ดึงข้อมูล symbol และราคา
            symbol_info = mt5.symbol_info(self.symbol)
            tick = mt5.symbol_info_tick(self.symbol)
            
            if not symbol_info or not tick:
                print("❌ Cannot get symbol info or tick")
                return None
            
            # กำหนดประเภท order และราคา
            if signal == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            else:  # SELL
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            
            # คำนวณ TP/SL
            tp, sl = self.calculate_tp_sl(signal, price)
            if tp is None or sl is None:
                print("❌ Cannot calculate TP/SL")
                return None
            
            # กำหนด lot size
            if is_martingale:
                # ใช้ Martingale lot size
                adjusted_lot_size = self.calculate_martingale_lot_size(martingale_level)
                order_comment = f"Gold AI {signal} Martingale L{martingale_level}"
            else:
                # ปรับ lot size ตาม confidence (ยิ่งมั่นใจมาก lot ยิ่งใหญ่)
                adjusted_lot_size = self.lot_size
                if confidence > 0.8:
                    adjusted_lot_size = self.lot_size * 1.5
                elif confidence > 0.9:
                    adjusted_lot_size = self.lot_size * 2.0
                order_comment = f"Gold AI {signal} - Conf:{confidence:.1%}"
            
            # ปรับให้เป็น lot size ที่ถูกต้อง
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            lot_step = symbol_info.volume_step
            
            adjusted_lot_size = max(min_lot, min(max_lot, adjusted_lot_size))
            adjusted_lot_size = round(adjusted_lot_size / lot_step) * lot_step
            
            # สร้าง order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": adjusted_lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": order_comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            print(f"📋 Order Request:")
            print(f"   Signal: {signal}")
            print(f"   Price: ${price:.2f}")
            print(f"   Volume: {adjusted_lot_size}")
            print(f"   TP: ${tp:.2f}")
            print(f"   SL: ${sl:.2f}")
            if is_martingale:
                print(f"   Martingale Level: {martingale_level}")
            else:
                print(f"   Confidence: {confidence:.1%}")
            
            # ส่ง order
            result = mt5.order_send(request)
            
            if result is None:
                print("❌ Order send failed - No result")
                return None
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"❌ Order failed: {result.retcode} - {result.comment}")
                return None
            
            # Order สำเร็จ
            order_info = {
                'ticket': result.order,
                'signal': signal,
                'price': price,
                'volume': adjusted_lot_size,
                'tp': tp,
                'sl': sl,
                'confidence': confidence,
                'is_martingale': is_martingale,
                'martingale_level': martingale_level,
                'timestamp': datetime.now(),
                'retcode': result.retcode,
                'deal': result.deal
            }
            
            self.orders_placed.append(order_info)
            self.performance_data['total_orders'] += 1
            self.performance_data['successful_orders'] += 1
            
            # อัพเดท unified SL หลังจากเปิด order
            if is_martingale:
                self.update_unified_sl_for_group(signal)
            
            print(f"✅ Order placed successfully!")
            print(f"   Ticket: {result.order}")
            print(f"   Deal: {result.deal}")
            
            return order_info
            
        except Exception as e:
            print(f"❌ Place order error: {e}")
            self.performance_data['failed_orders'] += 1
            return None
    
    def close_position(self, ticket):
        """ปิด position"""
        try:
            # ดึงข้อมูล position
            position = mt5.positions_get(ticket=ticket)
            if not position:
                print(f"❌ Position {ticket} not found")
                return False
            
            position = position[0]
            
            # กำหนดประเภท order สำหรับปิด position
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(self.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(self.symbol).ask
            
            # สร้าง close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Gold AI Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # ส่ง close order
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Position {ticket} closed successfully")
                return True
            else:
                print(f"❌ Failed to close position {ticket}")
                return False
                
        except Exception as e:
            print(f"❌ Close position error: {e}")
            return False
    
    def calculate_martingale_lot_size(self, level):
        """คำนวณ lot size สำหรับ Martingale"""
        try:
            # เริ่มจาก base lot size แล้วคูณตาม level
            # Level 0: 0.01, Level 1: 0.02, Level 2: 0.04, Level 3: 0.08
            martingale_lot = self.lot_size * (self.martingale_multiplier ** level)
            
            # ตรวจสอบขีดจำกัด
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info:
                min_lot = symbol_info.volume_min
                max_lot = symbol_info.volume_max
                lot_step = symbol_info.volume_step
                
                martingale_lot = max(min_lot, min(max_lot, martingale_lot))
                martingale_lot = round(martingale_lot / lot_step) * lot_step
            
            return martingale_lot
            
        except Exception as e:
            print(f"❌ Martingale lot calculation error: {e}")
            return self.lot_size
    
    def should_open_martingale(self, signal_direction):
        """ตรวจสอบว่าควรเปิด Martingale หรือไม่"""
        try:
            if not self.enable_martingale:
                return False, 0
            
            # ดึง positions ปัจจุบันในทิศทางเดียวกัน
            positions = self.get_active_positions()
            same_direction_positions = []
            
            for pos in positions:
                pos_direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                if pos_direction == signal_direction:
                    same_direction_positions.append(pos)
            
            if not same_direction_positions:
                return True, 0  # เปิด position แรก
            
            # ตรวจสอบว่า positions ที่มีอยู่ขาดทุนหรือไม่
            losing_positions = [pos for pos in same_direction_positions if pos.profit < 0]
            
            if not losing_positions:
                return False, 0  # ไม่มี position ขาดทุน ไม่ต้อง Martingale
            
            # ตรวจสอบระดับ Martingale ปัจจุบัน
            current_level = len(same_direction_positions)
            
            if current_level >= self.max_martingale_levels:
                return False, current_level  # ถึงระดับสูงสุดแล้ว
            
            # ตรวจสอบระยะห่างจาก position ล่าสุด
            latest_position = max(same_direction_positions, key=lambda x: x.time)
            current_price = mt5.symbol_info_tick(self.symbol).bid
            
            price_distance = abs(current_price - latest_position.price_open)
            symbol_info = mt5.symbol_info(self.symbol)
            distance_points = price_distance / symbol_info.point
            
            if distance_points >= self.martingale_distance:
                return True, current_level
            
            return False, current_level
            
        except Exception as e:
            print(f"❌ Martingale check error: {e}")
            return False, 0
    
    def update_trailing_stops(self):
        """อัพเดท Trailing Stop สำหรับ positions ที่กำไร"""
        try:
            if not self.enable_trailing_stop:
                return
            
            positions = self.get_active_positions()
            symbol_info = mt5.symbol_info(self.symbol)
            
            for pos in positions:
                # ตรวจสอบว่ากำไรเพียงพอสำหรับ trailing หรือไม่
                if pos.profit < (self.trailing_start * symbol_info.point * pos.volume * 100):
                    continue
                
                current_price = mt5.symbol_info_tick(self.symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(self.symbol).ask
                
                # คำนวณ trailing stop ใหม่
                if pos.type == mt5.POSITION_TYPE_BUY:
                    # BUY position: เลื่อน SL ขึ้น
                    new_sl = current_price - (self.trailing_step * symbol_info.point)
                    if new_sl > pos.sl:
                        self.modify_position_sl(pos.ticket, new_sl)
                        print(f"📈 Trailing SL updated for BUY {pos.ticket}: ${new_sl:.2f}")
                else:
                    # SELL position: เลื่อน SL ลง
                    new_sl = current_price + (self.trailing_step * symbol_info.point)
                    if new_sl < pos.sl:
                        self.modify_position_sl(pos.ticket, new_sl)
                        print(f"📉 Trailing SL updated for SELL {pos.ticket}: ${new_sl:.2f}")
            
        except Exception as e:
            print(f"❌ Trailing stop update error: {e}")
    
    def modify_position_sl(self, ticket, new_sl):
        """แก้ไข Stop Loss ของ position"""
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
            
            position = position[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": self.symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                return True
            else:
                print(f"❌ Failed to modify SL for {ticket}: {result.comment if result else 'No result'}")
                return False
                
        except Exception as e:
            print(f"❌ Modify SL error: {e}")
            return False
    
    def update_unified_sl_for_group(self, signal_direction):
        """อัพเดท SL ให้เป็นแบบ unified สำหรับกลุม positions"""
        try:
            positions = self.get_active_positions()
            same_direction_positions = []
            
            # หา positions ในทิศทางเดียวกัน
            for pos in positions:
                pos_direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                if pos_direction == signal_direction:
                    same_direction_positions.append(pos)
            
            if len(same_direction_positions) <= 1:
                return  # ไม่ต้อง unified ถ้ามี position เดียว
            
            # หา position ล่าสุด (SL ล่าสุด)
            latest_position = max(same_direction_positions, key=lambda x: x.time)
            unified_sl = latest_position.sl
            
            # อัพเดท SL ของ positions อื่นให้เป็น unified SL
            for pos in same_direction_positions:
                if pos.ticket != latest_position.ticket and pos.sl != unified_sl:
                    if self.modify_position_sl(pos.ticket, unified_sl):
                        print(f"🔄 Unified SL updated for {pos.ticket}: ${unified_sl:.2f}")
            
            # ส่งแจ้งเตือน
            message = f"""
🔄 <b>UNIFIED STOP LOSS</b> 🔄

📊 <b>Direction:</b> {signal_direction}
🛡️ <b>New SL:</b> ${unified_sl:.2f}
📈 <b>Positions:</b> {len(same_direction_positions)}

<i>🤖 Gold AI Trader</i>
            """.strip()
            
            self.send_telegram_message(message)
            
        except Exception as e:
            print(f"❌ Unified SL update error: {e}")
    
    def update_performance(self, prediction, actual_result=None, profit_loss=None):
        """อัพเดทประสิทธิภาพ"""
        try:
            self.performance_data['total_signals'] += 1
            
            if actual_result == 'WIN':
                self.performance_data['correct_signals'] += 1
            
            if profit_loss:
                self.performance_data['total_profit'] += profit_loss
            
            # คำนวณ accuracy
            if self.performance_data['total_signals'] > 0:
                self.performance_data['accuracy'] = (
                    self.performance_data['correct_signals'] / 
                    self.performance_data['total_signals']
                )
            
            # บันทึกด้วย Performance Monitor (ถ้ามี)
            if self.performance_monitor and actual_result:
                signal_data = {
                    'signal_type': prediction['signal'],
                    'confidence': prediction['confidence'],
                    'timestamp': prediction['timestamp'].isoformat()
                }
                
                outcome = {
                    'actual_result': 1.0 if actual_result == 'WIN' else 0.0,
                    'predicted_result': 1.0 if prediction['signal'] == 'BUY' else 0.0,
                    'is_correct': actual_result == 'WIN',
                    'profit_loss': profit_loss or 0.0
                }
                
                self.performance_monitor.track_signal_outcome(
                    "gold_model", "v1.0", signal_data, outcome
                )
            
        except Exception as e:
            print(f"❌ Performance update error: {e}")
    
    def test_signal_now(self):
        """ทดสอบส่งสัญญาณทันที"""
        print("🧪 Testing signal generation...")
        
        # เชื่อมต่อ MT5
        if not self.connect_mt5():
            return False
        
        # เทรนโมเดล
        if not self.train_gold_model():
            return False
        
        # ทำนายสัญญาณ
        prediction = self.make_gold_prediction()
        
        if prediction:
            print(f"🔮 Generated signal: {prediction['signal']} ({prediction['confidence']:.1%})")
            
            # เปิด order ใน MT5 (ถ้าเปิดใช้งาน)
            order_info = None
            if self.enable_auto_trading and prediction['confidence'] > 0.6:
                print("💼 Placing test order in MT5...")
                order_info = self.place_order(prediction['signal'], prediction['confidence'])
                
                if order_info:
                    print(f"✅ Test order placed: Ticket {order_info['ticket']}")
                else:
                    print("❌ Failed to place test order")
            
            # ส่งสัญญาณไป Telegram
            message = self.format_telegram_message(prediction, order_info)
            
            if self.send_telegram_message(message):
                print("✅ Test signal sent successfully!")
                return True
            else:
                print("❌ Failed to send test signal")
                return False
        else:
            print("❌ No signal generated")
            return False
    
    def run_gold_trader(self, duration_minutes=60, signal_interval_minutes=15):
        """รันระบบเทรดทอง"""
        print(f"🚀 Starting Gold AI Trader ({duration_minutes} minutes)")
        print(f"📊 Signal interval: {signal_interval_minutes} minutes")
        
        # เชื่อมต่อ MT5
        if not self.connect_mt5():
            return False
        
        # เทรนโมเดล
        if not self.train_gold_model():
            return False
        
        # ส่งข้อความเริ่มต้น
        start_message = f"""
🥇 <b>Gold AI Trader Started</b> 🥇

🤖 <b>AI Model:</b> Trained & Ready
📊 <b>Symbol:</b> {self.symbol}
⏰ <b>Duration:</b> {duration_minutes} minutes
📡 <b>Signal Interval:</b> {signal_interval_minutes} minutes
🎯 <b>Timeframes:</b> {', '.join(self.timeframe_names)}

<i>🚀 Ready to analyze Gold market!</i>
        """.strip()
        
        self.send_telegram_message(start_message)
        
        # เริ่มลูปการทำงาน
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        last_signal_time = datetime.now() - timedelta(minutes=signal_interval_minutes + 1)  # เพิ่ม 1 นาทีเพื่อให้ส่งทันที
        
        signals_sent = 0
        
        # ส่งสัญญาณแรกทันที
        print("\n🔮 Generating first signal...")
        first_prediction = self.make_gold_prediction()
        if first_prediction and first_prediction['confidence'] > 0.5:  # ลด threshold สำหรับสัญญาณแรก
            message = self.format_telegram_message(first_prediction)
            if self.send_telegram_message(message):
                signals_sent += 1
                self.signals_sent.append(first_prediction)
                last_signal_time = datetime.now()  # อัพเดทเวลาสัญญาณล่าสุด
                print(f"✅ First signal sent: {first_prediction['signal']} ({first_prediction['confidence']:.1%})")
            else:
                print("❌ Failed to send first signal")
        
        try:
            while datetime.now() < end_time:
                current_time = datetime.now()
                
                # ตรวจสอบว่าถึงเวลาส่งสัญญาณหรือยัง
                time_since_last_signal = (current_time - last_signal_time).total_seconds()
                print(f"🕐 Time since last signal: {time_since_last_signal/60:.1f} minutes (need {signal_interval_minutes} minutes)")
                
                if time_since_last_signal >= signal_interval_minutes * 60:
                    
                    print(f"\n⏰ {current_time.strftime('%H:%M:%S')} - Analyzing Gold...")
                    
                    # ตรวจสอบ spread
                    if not self.check_spread():
                        print("⚠️ Spread too high, skipping...")
                        time.sleep(60)
                        continue
                    
                    # ทำนายสัญญาณ
                    prediction = self.make_gold_prediction()
                    
                    if prediction:
                        print(f"🔮 Prediction: {prediction['signal']} (confidence: {prediction['confidence']:.1%})")
                        
                        if prediction['confidence'] > 0.6:
                            # เปิด order ใน MT5 (ถ้าเปิดใช้งาน)
                            order_info = None
                            if self.enable_auto_trading:
                                print("💼 Placing order in MT5...")
                                order_info = self.place_order(prediction['signal'], prediction['confidence'])
                                
                                if order_info:
                                    print(f"✅ Order placed: Ticket {order_info['ticket']}")
                                else:
                                    print("❌ Failed to place order")
                            
                            # ส่งสัญญาณไป Telegram
                            message = self.format_telegram_message(prediction, order_info)
                            
                            if self.send_telegram_message(message):
                                signals_sent += 1
                                self.signals_sent.append(prediction)
                                last_signal_time = current_time
                                
                                print(f"✅ Signal sent: {prediction['signal']} ({prediction['confidence']:.1%})")
                                
                                # อัพเดทประสิทธิภาพ
                                self.update_performance(prediction)
                            else:
                                print("❌ Failed to send Telegram message")
                        else:
                            print(f"⏭️ Signal confidence too low: {prediction['confidence']:.1%} (need > 60%)")
                    else:
                        print("❌ No prediction generated")
                    
                    # อัพเดทเวลาสัญญาณล่าสุดแม้ไม่ส่ง (เพื่อไม่ให้ติดลูป)
                    last_signal_time = current_time
                
                else:
                    print(f"⏳ Waiting... {(signal_interval_minutes * 60 - time_since_last_signal)/60:.1f} minutes remaining")
                
                # รอ 1 นาที
                time.sleep(60)
        
        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user")
        
        # ส่งสรุปผล
        end_message = f"""
🏁 <b>Gold AI Trader Finished</b> 🏁

📊 <b>Summary:</b>
• Signals sent: {signals_sent}
• Duration: {duration_minutes} minutes
• Accuracy: {self.performance_data['accuracy']:.1%}
• Total P&L: ${self.performance_data['total_profit']:.2f}

<i>🤖 Gold AI Trader session completed</i>
        """.strip()
        
        self.send_telegram_message(end_message)
        
        print(f"\n🏁 Gold trading session completed!")
        print(f"📊 Signals sent: {signals_sent}")
        print(f"🎯 Performance: {self.performance_data['accuracy']:.1%} accuracy")
        
        return True
    
    def get_positions_summary(self):
        """ดูสรุป positions ปัจจุบัน"""
        try:
            positions = self.get_active_positions()
            
            if not positions:
                return "ไม่มี position เปิดอยู่"
            
            summary = f"📊 Active Positions ({len(positions)}):\n"
            total_profit = 0
            
            for pos in positions:
                profit = pos.profit
                total_profit += profit
                
                summary += f"🎫 {pos.ticket}: {pos.type_str} {pos.volume} lots "
                summary += f"@ ${pos.price_open:.2f} "
                summary += f"(P&L: ${profit:.2f})\n"
            
            summary += f"💰 Total P&L: ${total_profit:.2f}"
            return summary
            
        except Exception as e:
            print(f"❌ Positions summary error: {e}")
            return "ไม่สามารถดู positions ได้"
    
    def monitor_positions(self):
        """ติดตาม positions และส่งอัพเดท"""
        try:
            positions = self.get_active_positions()
            
            for pos in positions:
                # ตรวจสอบ positions ที่กำไร/ขาดทุนมาก
                if pos.profit > 100:  # กำไรมากกว่า $100
                    message = f"""
🎉 <b>PROFIT ALERT</b> 🎉

🎫 <b>Ticket:</b> {pos.ticket}
📈 <b>Type:</b> {pos.type_str}
💰 <b>Profit:</b> ${pos.profit:.2f}
📊 <b>Volume:</b> {pos.volume} lots

<i>🤖 Gold AI Trader</i>
                    """.strip()
                    
                    self.send_telegram_message(message)
                
                elif pos.profit < -50:  # ขาดทุนมากกว่า $50
                    message = f"""
⚠️ <b>LOSS ALERT</b> ⚠️

🎫 <b>Ticket:</b> {pos.ticket}
📉 <b>Type:</b> {pos.type_str}
💸 <b>Loss:</b> ${pos.profit:.2f}
📊 <b>Volume:</b> {pos.volume} lots

<i>🤖 Gold AI Trader</i>
                    """.strip()
                    
                    self.send_telegram_message(message)
            
        except Exception as e:
            print(f"❌ Position monitoring error: {e}")
    
    def initialize_ai_components(self):
        """เริ่มต้นคอมโพเนนต์ AI"""
        try:
            print("🧠 Initializing AI components...")
            
            # Performance Monitor
            self.performance_monitor = PerformanceMonitor()
            print("✅ Performance Monitor initialized")
            
            # Model Manager
            self.model_manager = ModelManager()
            print("✅ Model Manager initialized")
            
            # Metrics Collector
            self.metrics_collector = LearningMetricsCollector()
            self.metrics_collector.start_collection()
            print("✅ Metrics Collector initialized")
            
            return True
            
        except Exception as e:
            print(f"⚠️ AI components initialization failed: {e}")
            print("Running in standalone mode...")
            return False


def main():
    """ฟังก์ชันหลัก"""
    print("🥇 Gold AI Trader with Telegram")
    print("=" * 50)
    
    # ตั้งค่า Telegram (ใส่ token และ chat_id จริง)
    telegram_token = input("Enter Telegram Bot Token (or press Enter for default): ").strip()
    chat_id = input("Enter Chat ID (or press Enter for default): ").strip()
    
    if not telegram_token:
        telegram_token = "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
    if not chat_id:
        chat_id = "-1002852894581"
    
    # สร้าง trader
    trader = GoldAITrader(telegram_token, chat_id)
    
    # เริ่มต้นคอมโพเนนต์ AI
    trader.initialize_ai_components()
    
    # ตั้งค่าการเทรด
    print("\n⚙️ Trading Settings:")
    auto_trade = input("Enable Auto Trading? (y/n, default n): ").strip().lower()
    trader.enable_auto_trading = auto_trade == 'y'
    
    if trader.enable_auto_trading:
        print("✅ Auto trading ENABLED - Orders will be placed in MT5")
        
        # ตั้งค่า TP/SL
        tp_points = input(f"Take Profit points (default {trader.tp_points}): ").strip()
        if tp_points:
            trader.tp_points = int(tp_points)
        
        sl_points = input(f"Stop Loss points (default {trader.sl_points}): ").strip()
        if sl_points:
            trader.sl_points = int(sl_points)
        
        lot_size = input(f"Lot size (default {trader.lot_size}): ").strip()
        if lot_size:
            trader.lot_size = float(lot_size)
        
        print(f"📊 TP: {trader.tp_points} points, SL: {trader.sl_points} points, Lot: {trader.lot_size}")
    else:
        print("⚠️ Auto trading DISABLED - Signals only")
    
    # เลือกโหมดการทำงาน
    print("\n🎯 Select Mode:")
    print("1. Test Signal Now (ทดสอบส่งสัญญาณทันที)")
    print("2. Run Continuous Trading (รันเทรดต่อเนื่อง)")
    print("3. Check Current Positions (ดู positions ปัจจุบัน)")
    
    mode = input("Enter choice (1-3, default 1): ").strip() or "1"
    
    try:
        if mode == "1":
            # ทดสอบส่งสัญญาณทันที
            print("\n🧪 Testing signal generation...")
            success = trader.test_signal_now()
            
            if success:
                print("\n🎉 Test signal sent successfully!")
            else:
                print("\n❌ Test signal failed")
        
        elif mode == "2":
            # รันเทรดต่อเนื่อง
            print("\n📊 Trading Settings:")
            duration = int(input("Duration (minutes, default 60): ") or "60")
            interval = int(input("Signal interval (minutes, default 15): ") or "15")
            
            success = trader.run_gold_trader(duration, interval)
            
            if success:
                print("\n🎉 Gold trading completed successfully!")
                
                # แสดงสรุปผล
                print(f"\n📊 Final Summary:")
                print(f"   Signals sent: {trader.performance_data['total_signals']}")
                print(f"   Orders placed: {trader.performance_data['total_orders']}")
                print(f"   Successful orders: {trader.performance_data['successful_orders']}")
                print(f"   Failed orders: {trader.performance_data['failed_orders']}")
                
                # ดู positions ปัจจุบัน
                positions_summary = trader.get_positions_summary()
                print(f"\n{positions_summary}")
            else:
                print("\n❌ Gold trading failed")
        
        elif mode == "3":
            # ดู positions ปัจจุบัน
            print("\n📊 Checking current positions...")
            if trader.connect_mt5():
                positions_summary = trader.get_positions_summary()
                print(f"\n{positions_summary}")
                
                # ส่งไป Telegram ด้วย
                message = f"""
📊 <b>GOLD POSITIONS SUMMARY</b> 📊

{positions_summary}

⏰ <b>เวลา:</b> {datetime.now().strftime('%H:%M:%S')}
📅 <b>วันที่:</b> {datetime.now().strftime('%d/%m/%Y')}

<i>🤖 Gold AI Trader</i>
                """.strip()
                
                trader.send_telegram_message(message)
            else:
                print("❌ Cannot connect to MT5")
        
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    finally:
        # ปิดการเชื่อมต่อ MT5
        mt5.shutdown()
        print("🔌 MT5 connection closed")


if __name__ == "__main__":
    main()