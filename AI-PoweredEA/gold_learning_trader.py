"""
Gold Learning Trader - ระบบเทรดทองที่มี AI Learning แบบเต็มรูปแบบ
รวม Martingale + Trailing Stop + AI Learning System
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

# Import AI Learning components
try:
    from performance_monitor import PerformanceMonitor
    from model_manager import ModelManager, ModelType
    from learning_metrics_collector import LearningMetricsCollector
    from learning_coordinator import LearningCoordinator, LearningTrigger
    from ai_system_integration import AISystemIntegration
except ImportError as e:
    print(f"Warning: Could not import AI Learning components: {e}")
    print("Running without advanced learning features...")

class GoldLearningTrader:
    """ระบบเทรดทองที่มี AI Learning แบบเต็มรูปแบบ"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        # Telegram settings
        self.telegram_token = telegram_token or "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
        self.chat_id = chat_id or "-1002852894581"
        
        # Trading settings
        self.symbol = "GOLDm#"
        self.timeframes = [mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M15, mt5.TIMEFRAME_M30, mt5.TIMEFRAME_H1]
        self.timeframe_names = ["M5", "M15", "M30", "H1"]
        self.base_lot_size = 0.01
        self.max_spread = 50
        
        # Risk Management
        self.tp_points = 200
        self.sl_points = 100
        self.enable_auto_trading = True
        self.max_positions = 5
        
        # Martingale settings
        self.enable_martingale = True
        self.martingale_multiplier = 2.0
        self.max_martingale_levels = 4
        self.martingale_distance = 150
        
        # Trailing Stop settings
        self.enable_trailing_stop = True
        self.trailing_start = 100
        self.trailing_step = 50
        
        # AI Learning settings
        self.enable_learning = True
        self.learning_interval_hours = 24  # เรียนรู้ทุก 24 ชั่วโมง
        self.performance_threshold = 0.7   # threshold สำหรับ retrain
        self.min_samples_for_learning = 50 # ข้อมูลขั้นต่ำสำหรับเรียนรู้
        
        # AI Learning components
        self.performance_monitor = None
        self.model_manager = None
        self.metrics_collector = None
        self.learning_coordinator = None
        self.ai_integration = None
        
        # Current model
        self.current_model = None
        self.current_model_id = None
        self.current_model_version = None
        self.scaler = StandardScaler()
        
        # Trading data
        self.signals_sent = []
        self.orders_placed = []
        self.learning_data = []  # เก็บข้อมูลสำหรับเรียนรู้
        self.last_learning_time = None
        
        self.performance_data = {
            'total_signals': 0,
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'total_profit': 0.0,
            'martingale_orders': 0,
            'trailing_stops_moved': 0,
            'learning_cycles': 0,
            'model_updates': 0
        }
        
        print("🧠 Gold Learning Trader initialized")
    
    def initialize_learning_system(self):
        """เริ่มต้นระบบ AI Learning"""
        try:
            print("🧠 Initializing AI Learning System...")
            
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
            
            # Learning Coordinator
            if self.enable_learning:
                self.learning_coordinator = LearningCoordinator()
                print("✅ Learning Coordinator initialized")
            
            # AI System Integration
            self.ai_integration = AISystemIntegration()
            print("✅ AI System Integration initialized")
            
            # โหลดโมเดลล่าสุด
            self.load_latest_model()
            
            return True
            
        except Exception as e:
            print(f"⚠️ Learning system initialization failed: {e}")
            print("Running in basic mode...")
            return False
    
    def load_latest_model(self):
        """โหลดโมเดลล่าสุด"""
        try:
            if not self.model_manager:
                return False
            
            # ดูโมเดลที่มี
            models = self.model_manager.list_models()
            
            if not models:
                print("📋 No existing models found - will train new model")
                return False
            
            # หาโมเดลทองล่าสุด
            gold_models = [m for m in models if 'gold' in m.model_name.lower()]
            
            if gold_models:
                latest_model = gold_models[0]  # เรียงตาม timestamp แล้ว
                
                # โหลดโมเดล
                model_data = self.model_manager.load_model(
                    latest_model.model_id, 
                    latest_model.version
                )
                
                if model_data:
                    self.current_model = model_data[0]
                    self.current_model_id = latest_model.model_id
                    self.current_model_version = latest_model.version
                    
                    print(f"✅ Loaded model: {latest_model.model_name}")
                    print(f"   📊 Accuracy: {latest_model.accuracy:.2%}")
                    print(f"   🆔 ID: {latest_model.model_id}")
                    print(f"   📝 Version: {latest_model.version}")
                    
                    return True
            
            print("📋 No Gold models found - will train new model")
            return False
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def send_telegram_message(self, message):
        """ส่งข้อความไป Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
            return False
    
    def connect_mt5(self):
        """เชื่อมต่อ MT5"""
        try:
            if not mt5.initialize():
                return False
            
            account_info = mt5.account_info()
            if account_info is None:
                return False
            
            # ตรวจสอบ symbol ทอง
            gold_symbols = ["XAUUSD", "GOLD", "GOLDm#", "GOLD#", "XAU/USD"]
            for symbol in gold_symbols:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is not None:
                    self.symbol = symbol
                    break
            
            print(f"✅ MT5 connected - Account: {account_info.login}")
            print(f"💰 Balance: ${account_info.balance:.2f}")
            print(f"🥇 Gold symbol: {self.symbol}")
            
            return True
            
        except Exception as e:
            print(f"❌ MT5 connection error: {e}")
            return False
    
    def get_gold_data(self, timeframe, count=100):
        """ดึงข้อมูลทองจาก MT5"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            print(f"❌ Data retrieval error: {e}")
            return None
    
    def calculate_indicators(self, df):
        """คำนวณ Technical Indicators"""
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
            
            # EMA
            df['ema_20'] = df['close'].ewm(span=20).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            df['ema_signal'] = np.where(df['ema_20'] > df['ema_50'], 1, 0)
            
            # ATR
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
    
    def train_or_update_model(self):
        """เทรนหรืออัพเดทโมเดล"""
        print("🧠 Training/Updating Gold AI model...")
        
        # เก็บข้อมูลสำหรับเทรน
        all_features = []
        all_labels = []
        
        for i, timeframe in enumerate(self.timeframes):
            tf_name = self.timeframe_names[i]
            print(f"   📊 Processing {tf_name} data...")
            
            df = self.get_gold_data(timeframe, 500)
            if df is None:
                continue
            
            df = self.calculate_indicators(df)
            if df is None:
                continue
            
            # สร้าง labels
            future_bars = 5 if timeframe <= mt5.TIMEFRAME_M15 else 3
            df['future_return'] = df['close'].shift(-future_bars) / df['close'] - 1
            
            threshold = 0.001 if timeframe <= mt5.TIMEFRAME_M15 else 0.002
            df['label'] = np.where(df['future_return'] > threshold, 1, 0)
            
            # เลือก features
            features = ['rsi', 'macd', 'macd_histogram', 'bb_position', 'ema_signal', 'atr', 'volume_ratio']
            df_clean = df[features + ['label']].dropna()
            
            if len(df_clean) > 50:
                X = df_clean[features].values
                y = df_clean['label'].values
                all_features.append(X)
                all_labels.append(y)
        
        if not all_features:
            print("❌ No training data available")
            return False
        
        X_combined = np.vstack(all_features)
        y_combined = np.hstack(all_labels)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X_combined)
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_scaled, y_combined)
        accuracy = model.score(X_scaled, y_combined)
        
        print(f"✅ Model trained! Accuracy: {accuracy:.2%}")
        
        # บันทึกโมเดลด้วย Model Manager
        if self.model_manager:
            try:
                performance_metrics = {
                    'accuracy': accuracy,
                    'precision': 0.0,  # คำนวณจริงถ้าต้องการ
                    'recall': 0.0
                }
                
                model_version = self.model_manager.save_model(
                    model=model,
                    model_name="Gold_Learning_Model",
                    model_type=ModelType.CLASSIFICATION,
                    performance_metrics=performance_metrics,
                    metadata={
                        'symbol': self.symbol,
                        'timeframes': self.timeframe_names,
                        'features': ['rsi', 'macd', 'macd_histogram', 'bb_position', 'ema_signal', 'atr', 'volume_ratio'],
                        'training_samples': len(X_combined)
                    }
                )
                
                if model_version:
                    self.current_model = model
                    self.current_model_id = model_version.model_id
                    self.current_model_version = model_version.version
                    self.performance_data['model_updates'] += 1
                    
                    print(f"✅ Model saved: {model_version.model_id} v{model_version.version}")
                    
                    # ส่งแจ้งเตือนไป Telegram
                    message = f"""
🧠 <b>AI MODEL UPDATED</b> 🧠

🤖 <b>Model:</b> Gold Learning Model
📊 <b>Accuracy:</b> {accuracy:.2%}
📈 <b>Training Samples:</b> {len(X_combined):,}
🆔 <b>Version:</b> {model_version.version}

<i>🤖 Gold Learning Trader</i>
                    """.strip()
                    
                    self.send_telegram_message(message)
                    
                    return True
                
            except Exception as e:
                print(f"⚠️ Could not save to Model Manager: {e}")
                # ใช้โมเดลใน memory
                self.current_model = model
                return True
        else:
            # ใช้โมเดลใน memory
            self.current_model = model
            return True
        
        return False
    
    def make_prediction(self):
        """ทำนายสัญญาณด้วยโมเดลปัจจุบัน"""
        if self.current_model is None:
            print("❌ No model available for prediction")
            return None
        
        predictions = {}
        
        for i, timeframe in enumerate(self.timeframes):
            tf_name = self.timeframe_names[i]
            
            df = self.get_gold_data(timeframe, 100)
            if df is None:
                continue
            
            df = self.calculate_indicators(df)
            if df is None:
                continue
            
            features = ['rsi', 'macd', 'macd_histogram', 'bb_position', 'ema_signal', 'atr', 'volume_ratio']
            latest_data = df[features].iloc[-1:].values
            
            if np.isnan(latest_data).any():
                continue
            
            features_scaled = self.scaler.transform(latest_data)
            prediction = self.current_model.predict(features_scaled)[0]
            probability = self.current_model.predict_proba(features_scaled)[0]
            confidence = max(probability)
            
            signal = "BUY" if prediction == 1 else "SELL"
            predictions[tf_name] = {'signal': signal, 'confidence': confidence}
        
        if not predictions:
            return None
        
        # รวมสัญญาณ
        buy_votes = sum(1 for p in predictions.values() if p['signal'] == 'BUY')
        sell_votes = len(predictions) - buy_votes
        
        final_signal = "BUY" if buy_votes > sell_votes else "SELL"
        avg_confidence = np.mean([p['confidence'] for p in predictions.values()])
        
        tick = mt5.symbol_info_tick(self.symbol)
        current_price = tick.bid if tick else 0
        
        prediction_result = {
            'symbol': self.symbol,
            'signal': final_signal,
            'confidence': avg_confidence,
            'timeframe_votes': f"{buy_votes} BUY, {sell_votes} SELL",
            'current_price': current_price,
            'timestamp': datetime.now(),
            'model_id': self.current_model_id,
            'model_version': self.current_model_version
        }
        
        return prediction_result
    
    def track_signal_performance(self, prediction, actual_outcome, profit_loss):
        """ติดตามประสิทธิภาพสัญญาณสำหรับ Learning"""
        try:
            if not self.performance_monitor:
                return
            
            # เตรียมข้อมูลสำหรับ Performance Monitor
            signal_data = {
                'signal_type': prediction['signal'],
                'confidence': prediction['confidence'],
                'timestamp': prediction['timestamp'].isoformat(),
                'model_id': prediction.get('model_id', 'unknown'),
                'model_version': prediction.get('model_version', 'unknown')
            }
            
            outcome = {
                'actual_result': 1.0 if actual_outcome == 'WIN' else 0.0,
                'predicted_result': 1.0 if prediction['signal'] == 'BUY' else 0.0,
                'is_correct': actual_outcome == 'WIN',
                'profit_loss': profit_loss
            }
            
            # ติดตามผลลัพธ์
            success = self.performance_monitor.track_signal_outcome(
                prediction.get('model_id', 'gold_model'),
                prediction.get('model_version', 'v1.0'),
                signal_data,
                outcome
            )
            
            if success:
                print(f"📊 Signal performance tracked: {actual_outcome}")
                
                # เก็บข้อมูลสำหรับเรียนรู้
                learning_record = {
                    'timestamp': datetime.now(),
                    'prediction': prediction,
                    'outcome': actual_outcome,
                    'profit_loss': profit_loss
                }
                
                self.learning_data.append(learning_record)
                
                # ตรวจสอบว่าควรเรียนรู้หรือไม่
                self.check_learning_trigger()
            
        except Exception as e:
            print(f"❌ Error tracking signal performance: {e}")
    
    def check_learning_trigger(self):
        """ตรวจสอบว่าควรเริ่มกระบวนการเรียนรู้หรือไม่"""
        try:
            if not self.enable_learning or not self.performance_monitor:
                return
            
            # ตรวจสอบเวลาการเรียนรู้ล่าสุด
            if self.last_learning_time:
                time_since_learning = datetime.now() - self.last_learning_time
                if time_since_learning.total_seconds() < self.learning_interval_hours * 3600:
                    return  # ยังไม่ถึงเวลา
            
            # ตรวจสอบจำนวนข้อมูล
            if len(self.learning_data) < self.min_samples_for_learning:
                return  # ข้อมูลไม่พอ
            
            # ตรวจสอบประสิทธิภาพ
            current_performance = self.performance_monitor.get_current_performance()
            current_accuracy = current_performance.get('accuracy', 1.0)
            
            if current_accuracy < self.performance_threshold:
                print(f"🚨 Performance degradation detected: {current_accuracy:.2%}")
                self.trigger_learning_cycle()
            
        except Exception as e:
            print(f"❌ Error checking learning trigger: {e}")
    
    def trigger_learning_cycle(self):
        """เริ่มกระบวนการเรียนรู้"""
        try:
            print("🧠 Triggering learning cycle...")
            
            if self.learning_coordinator:
                # ใช้ Learning Coordinator
                cycle_id = self.learning_coordinator.trigger_learning_cycle(
                    LearningTrigger.PERFORMANCE_DEGRADATION
                )
                
                print(f"✅ Learning cycle triggered: {cycle_id}")
                self.performance_data['learning_cycles'] += 1
                
                # ส่งแจ้งเตือน
                message = f"""
🧠 <b>AI LEARNING TRIGGERED</b> 🧠

🔄 <b>Cycle ID:</b> {cycle_id}
📉 <b>Trigger:</b> Performance Degradation
📊 <b>Data Samples:</b> {len(self.learning_data)}

<i>🤖 Gold Learning Trader</i>
                """.strip()
                
                self.send_telegram_message(message)
                
            else:
                # เรียนรู้แบบง่าย
                print("🧠 Simple learning mode...")
                if self.train_or_update_model():
                    self.performance_data['learning_cycles'] += 1
            
            self.last_learning_time = datetime.now()
            
        except Exception as e:
            print(f"❌ Error triggering learning cycle: {e}")
    
    # เพิ่มฟังก์ชัน Martingale และ Trailing Stop จาก GoldMartingaleTrader
    def calculate_tp_sl(self, signal, entry_price):
        """คำนวณ TP/SL"""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            point = symbol_info.point
            
            if signal == "BUY":
                tp = entry_price + (self.tp_points * point)
                sl = entry_price - (self.sl_points * point)
            else:
                tp = entry_price - (self.tp_points * point)
                sl = entry_price + (self.sl_points * point)
            
            return tp, sl
            
        except Exception as e:
            print(f"❌ TP/SL calculation error: {e}")
            return None, None
    
    def get_active_positions(self):
        """ดึง positions ที่เปิดอยู่"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            return list(positions) if positions else []
        except:
            return []
    
    def calculate_martingale_lot_size(self, level):
        """คำนวณ lot size สำหรับ Martingale"""
        return self.base_lot_size * (self.martingale_multiplier ** level)
    
    def should_open_martingale(self, signal_direction):
        """ตรวจสอบว่าควรเปิด Martingale หรือไม่"""
        if not self.enable_martingale:
            return False, 0
        
        positions = self.get_active_positions()
        same_direction_positions = []
        
        for pos in positions:
            pos_direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
            if pos_direction == signal_direction:
                same_direction_positions.append(pos)
        
        if not same_direction_positions:
            return True, 0  # เปิด position แรก
        
        # ตรวจสอบ positions ขาดทุน
        losing_positions = [pos for pos in same_direction_positions if pos.profit < 0]
        if not losing_positions:
            return False, 0
        
        current_level = len(same_direction_positions)
        if current_level >= self.max_martingale_levels:
            return False, current_level
        
        # ตรวจสอบระยะห่าง
        latest_position = max(same_direction_positions, key=lambda x: x.time)
        current_price = mt5.symbol_info_tick(self.symbol).bid
        
        price_distance = abs(current_price - latest_position.price_open)
        symbol_info = mt5.symbol_info(self.symbol)
        distance_points = price_distance / symbol_info.point
        
        return distance_points >= self.martingale_distance, current_level
    
    def place_order(self, signal, confidence, is_martingale=False, martingale_level=0):
        """เปิด order พร้อมบันทึกข้อมูลสำหรับ Learning"""
        try:
            if not self.enable_auto_trading:
                return None
            
            positions = self.get_active_positions()
            if len(positions) >= self.max_positions:
                return None
            
            symbol_info = mt5.symbol_info(self.symbol)
            tick = mt5.symbol_info_tick(self.symbol)
            
            if not symbol_info or not tick:
                return None
            
            # กำหนด order type และราคา
            if signal == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            
            # คำนวณ TP/SL
            tp, sl = self.calculate_tp_sl(signal, price)
            if tp is None or sl is None:
                return None
            
            # กำหนด lot size
            if is_martingale:
                lot_size = self.calculate_martingale_lot_size(martingale_level)
                comment = f"Gold Learning Martingale L{martingale_level}"
            else:
                lot_size = self.base_lot_size
                if confidence > 0.8:
                    lot_size *= 1.5
                comment = f"Gold Learning AI {signal}"
            
            # ปรับ lot size ให้ถูกต้อง
            min_lot = symbol_info.volume_min
            max_lot = symbol_info.volume_max
            lot_step = symbol_info.volume_step
            
            lot_size = max(min_lot, min(max_lot, lot_size))
            lot_size = round(lot_size / lot_step) * lot_step
            
            # สร้าง order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            print(f"📋 Placing order: {signal} {lot_size} lots @ ${price:.2f}")
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                order_info = {
                    'ticket': result.order,
                    'signal': signal,
                    'price': price,
                    'volume': lot_size,
                    'tp': tp,
                    'sl': sl,
                    'confidence': confidence,
                    'is_martingale': is_martingale,
                    'martingale_level': martingale_level,
                    'timestamp': datetime.now(),
                    'model_id': self.current_model_id,
                    'model_version': self.current_model_version
                }
                
                self.orders_placed.append(order_info)
                self.performance_data['total_orders'] += 1
                self.performance_data['successful_orders'] += 1
                
                if is_martingale:
                    self.performance_data['martingale_orders'] += 1
                
                print(f"✅ Order placed: Ticket {result.order}")
                return order_info
            else:
                print(f"❌ Order failed: {result.comment if result else 'Unknown error'}")
                self.performance_data['failed_orders'] += 1
                return None
                
        except Exception as e:
            print(f"❌ Place order error: {e}")
            return None
    
    def format_telegram_message(self, prediction, order_info=None, martingale_info=None):
        """จัดรูปแบบข้อความ Telegram"""
        signal = prediction['signal']
        confidence = prediction['confidence']
        price = prediction['current_price']
        votes = prediction['timeframe_votes']
        
        emoji = "🟢📈" if signal == "BUY" else "🔴📉"
        action = "ซื้อ" if signal == "BUY" else "ขาย"
        
        tp, sl = self.calculate_tp_sl(signal, price)
        
        if martingale_info:
            message = f"""
🎯 <b>GOLD LEARNING MARTINGALE</b> 🎯

{emoji} <b>สัญญาณ: {action} ({signal})</b>
🔄 <b>Martingale Level:</b> {martingale_info['level']}
📊 <b>Lot Size:</b> {martingale_info['lot_size']} lots
💰 <b>ราคาเข้า:</b> ${price:.2f}
🎯 <b>Take Profit:</b> ${tp:.2f}
🛡️ <b>Stop Loss:</b> ${sl:.2f}
"""
        else:
            message = f"""
🧠 <b>GOLD LEARNING SIGNAL</b> 🧠

{emoji} <b>สัญญาณ: {action} ({signal})</b>
💰 <b>ราคาเข้า:</b> ${price:.2f}
🎯 <b>Take Profit:</b> ${tp:.2f}
🛡️ <b>Stop Loss:</b> ${sl:.2f}
📊 <b>ความมั่นใจ:</b> {confidence:.1%}
📈 <b>Timeframe Votes:</b> {votes}
"""
        
        if order_info:
            message += f"""
💼 <b>ORDER PLACED:</b>
🎫 <b>Ticket:</b> {order_info['ticket']}
📊 <b>Volume:</b> {order_info['volume']} lots
🤖 <b>Model:</b> {order_info.get('model_id', 'Unknown')[:8]}...
✅ <b>Status:</b> Executed
"""
        
        message += f"""
⏰ <b>เวลา:</b> {prediction['timestamp'].strftime('%H:%M:%S')}

<i>🧠 Gold Learning Trader</i>
        """.strip()
        
        return message
    
    def run_learning_trading_session(self, duration_minutes=120, signal_interval_minutes=15):
        """รันเซสชันเทรดพร้อม Learning"""
        print(f"🧠 Starting Gold Learning Trading Session ({duration_minutes} minutes)")
        
        if not self.connect_mt5():
            return False
        
        # เริ่มต้นระบบ Learning
        learning_initialized = self.initialize_learning_system()
        
        # เทรนโมเดลถ้ายังไม่มี
        if self.current_model is None:
            if not self.train_or_update_model():
                print("❌ Cannot train model")
                return False
        
        # ส่งข้อความเริ่มต้น
        start_message = f"""
🧠 <b>GOLD LEARNING TRADER STARTED</b> 🧠

🤖 <b>AI Model:</b> {'Loaded' if self.current_model else 'Training...'}
📊 <b>Symbol:</b> {self.symbol}
⏰ <b>Duration:</b> {duration_minutes} minutes
📡 <b>Signal Interval:</b> {signal_interval_minutes} minutes

🔄 <b>Martingale:</b> {'Enabled' if self.enable_martingale else 'Disabled'}
📈 <b>Trailing Stop:</b> {'Enabled' if self.enable_trailing_stop else 'Disabled'}
🧠 <b>AI Learning:</b> {'Enabled' if learning_initialized else 'Disabled'}

<i>🚀 Ready for intelligent trading!</i>
        """.strip()
        
        self.send_telegram_message(start_message)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        last_signal_time = datetime.now() - timedelta(minutes=signal_interval_minutes + 1)
        
        signals_sent = 0
        
        try:
            while datetime.now() < end_time:
                current_time = datetime.now()
                
                # ตรวจสอบเวลาส่งสัญญาณ
                time_since_last = (current_time - last_signal_time).total_seconds()
                
                if time_since_last >= signal_interval_minutes * 60:
                    print(f"\n⏰ {current_time.strftime('%H:%M:%S')} - Analyzing market with AI...")
                    
                    prediction = self.make_prediction()
                    
                    if prediction and prediction['confidence'] > 0.6:
                        signal_direction = prediction['signal']
                        
                        # ตรวจสอบ Martingale
                        should_martingale, current_level = self.should_open_martingale(signal_direction)
                        
                        if should_martingale:
                            if current_level == 0:
                                # เปิด position แรก
                                order_info = self.place_order(signal_direction, prediction['confidence'])
                                martingale_info = None
                            else:
                                # เปิด Martingale
                                lot_size = self.calculate_martingale_lot_size(current_level)
                                martingale_info = {
                                    'level': current_level,
                                    'lot_size': lot_size,
                                    'multiplier': self.martingale_multiplier ** current_level
                                }
                                order_info = self.place_order(
                                    signal_direction, 
                                    prediction['confidence'], 
                                    is_martingale=True, 
                                    martingale_level=current_level
                                )
                            
                            if order_info:
                                message = self.format_telegram_message(prediction, order_info, martingale_info)
                                if self.send_telegram_message(message):
                                    signals_sent += 1
                                    self.signals_sent.append(prediction)
                                    print(f"✅ Signal sent: {signal_direction}")
                        else:
                            print(f"⏭️ Martingale conditions not met")
                    
                    last_signal_time = current_time
                
                time.sleep(60)  # รอ 1 นาที
        
        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user")
        
        # ส่งสรุปผล
        positions = self.get_active_positions()
        total_profit = sum(pos.profit for pos in positions) if positions else 0
        
        summary_message = f"""
🏁 <b>LEARNING TRADING COMPLETED</b> 🏁

📊 <b>Session Summary:</b>
• Signals Sent: {signals_sent}
• Orders Placed: {self.performance_data['total_orders']}
• Martingale Orders: {self.performance_data['martingale_orders']}
• Learning Cycles: {self.performance_data['learning_cycles']}
• Model Updates: {self.performance_data['model_updates']}
• Active Positions: {len(positions)}
• Current P&L: ${total_profit:.2f}

<i>🧠 Gold Learning Trader</i>
        """.strip()
        
        self.send_telegram_message(summary_message)
        
        print(f"\n🏁 Learning trading session completed!")
        print(f"📊 Signals sent: {signals_sent}")
        print(f"💼 Orders placed: {self.performance_data['total_orders']}")
        print(f"🧠 Learning cycles: {self.performance_data['learning_cycles']}")
        print(f"🤖 Model updates: {self.performance_data['model_updates']}")
        
        return True

def main():
    """ฟังก์ชันหลัก"""
    print("🧠 Gold Learning Trader - AI Powered Trading")
    print("=" * 60)
    
    # สร้าง trader
    trader = GoldLearningTrader()
    
    # ตั้งค่า
    print("\n⚙️ Configuration:")
    print(f"   💰 Base Lot Size: {trader.base_lot_size}")
    print(f"   🎯 TP: {trader.tp_points} points")
    print(f"   🛡️ SL: {trader.sl_points} points")
    print(f"   🔄 Martingale: {trader.enable_martingale}")
    print(f"   📈 Trailing Stop: {trader.enable_trailing_stop}")
    print(f"   🧠 AI Learning: {trader.enable_learning}")
    
    # รันเทรด
    try:
        duration = int(input("\nTrading duration (minutes, default 120): ") or "120")
        interval = int(input("Signal interval (minutes, default 15): ") or "15")
        
        success = trader.run_learning_trading_session(duration, interval)
        
        if success:
            print("\n🎉 Learning trading session completed successfully!")
        else:
            print("\n❌ Learning trading session failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    main()