#!/usr/bin/env python3
"""
Fixed Gold Learning Trader - เวอร์ชันที่แก้ไขปัญหาแล้ว
แก้ไข: Import errors, Error handling, Infinite loops, Missing dependencies
"""

import os
import sys
import time
import json
import requests
import traceback
from datetime import datetime, timedelta

# Add Python directory to path
sys.path.append('Python')

# Import required libraries
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Import AI Learning components with fallback
AI_COMPONENTS_AVAILABLE = {}

try:
    from performance_monitor import PerformanceMonitor
    AI_COMPONENTS_AVAILABLE['performance_monitor'] = True
except ImportError:
    AI_COMPONENTS_AVAILABLE['performance_monitor'] = False
    print("⚠️ PerformanceMonitor not available - running without performance monitoring")

try:
    from model_manager import ModelManager, ModelType
    AI_COMPONENTS_AVAILABLE['model_manager'] = True
except ImportError:
    AI_COMPONENTS_AVAILABLE['model_manager'] = False
    print("⚠️ ModelManager not available - running without model management")

try:
    from learning_coordinator import LearningCoordinator, LearningTrigger
    AI_COMPONENTS_AVAILABLE['learning_coordinator'] = True
except ImportError:
    AI_COMPONENTS_AVAILABLE['learning_coordinator'] = False
    print("⚠️ LearningCoordinator not available - running without learning coordination")

class FixedGoldLearningTrader:
    """Fixed version ของ Gold Learning Trader"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        print("🧠 Initializing Fixed Gold Learning Trader...")
        
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
        self.max_martingale_levels = 3
        self.martingale_distance = 150
        
        # AI Learning settings
        self.enable_learning = True
        self.learning_interval_hours = 24
        self.performance_threshold = 0.7
        self.min_samples_for_learning = 50
        
        # AI Learning components (with fallback)
        self.performance_monitor = None
        self.model_manager = None
        self.learning_coordinator = None
        
        # Current model
        self.current_model = None
        self.current_model_id = None
        self.current_model_version = None
        self.scaler = StandardScaler()
        
        # Trading data
        self.signals_sent = []
        self.orders_placed = []
        self.learning_data = []
        self.last_learning_time = None
        
        self.performance_data = {
            'total_signals': 0,
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'total_profit': 0.0,
            'learning_cycles': 0,
            'model_updates': 0
        }
        
        print("✅ Fixed Gold Learning Trader initialized")
    
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
            print("🔌 Connecting to MT5...")
            
            if not mt5.initialize():
                print("❌ MT5 initialization failed")
                return False
            
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Cannot get account info")
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
    
    def initialize_learning_system(self):
        """เริ่มต้นระบบ AI Learning (with fallback)"""
        try:
            print("🧠 Initializing AI Learning System...")
            
            success_count = 0
            
            # Performance Monitor
            if AI_COMPONENTS_AVAILABLE.get('performance_monitor', False):
                try:
                    self.performance_monitor = PerformanceMonitor()
                    print("✅ Performance Monitor initialized")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ Performance Monitor failed: {e}")
            
            # Model Manager
            if AI_COMPONENTS_AVAILABLE.get('model_manager', False):
                try:
                    self.model_manager = ModelManager()
                    print("✅ Model Manager initialized")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ Model Manager failed: {e}")
            
            # Learning Coordinator
            if AI_COMPONENTS_AVAILABLE.get('learning_coordinator', False):
                try:
                    self.learning_coordinator = LearningCoordinator()
                    print("✅ Learning Coordinator initialized")
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ Learning Coordinator failed: {e}")
            
            if success_count > 0:
                print(f"✅ Learning system initialized ({success_count} components)")
                return True
            else:
                print("⚠️ Learning system running in basic mode")
                return False
            
        except Exception as e:
            print(f"⚠️ Learning system initialization failed: {e}")
            return False
    
    def train_model(self):
        """เทรนโมเดล AI"""
        print("🤖 Training AI model...")
        
        try:
            # เก็บข้อมูลสำหรับเทรน
            all_features = []
            all_labels = []
            
            for i, timeframe in enumerate(self.timeframes):
                tf_name = self.timeframe_names[i]
                print(f"   📊 Processing {tf_name} data...")
                
                df = self.get_gold_data(timeframe, 300)
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
                    print(f"   ✅ {tf_name}: {len(df_clean)} samples")
            
            if not all_features:
                print("❌ No training data available")
                return False
            
            X_combined = np.vstack(all_features)
            y_combined = np.hstack(all_labels)
            
            print(f"📊 Total training samples: {len(X_combined)}")
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X_combined)
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_scaled, y_combined)
            accuracy = model.score(X_scaled, y_combined)
            
            self.current_model = model
            self.performance_data['model_updates'] += 1
            
            print(f"✅ Model trained! Accuracy: {accuracy:.2%}")
            
            # บันทึกโมเดลด้วย Model Manager (ถ้ามี)
            if self.model_manager:
                try:
                    performance_metrics = {'accuracy': accuracy}
                    model_version = self.model_manager.save_model(
                        model=model,
                        model_name="Fixed_Gold_Learning_Model",
                        model_type=ModelType.CLASSIFICATION,
                        performance_metrics=performance_metrics,
                        metadata={
                            'symbol': self.symbol,
                            'timeframes': self.timeframe_names,
                            'training_samples': len(X_combined)
                        }
                    )
                    
                    if model_version:
                        self.current_model_id = model_version.model_id
                        self.current_model_version = model_version.version
                        print(f"✅ Model saved: {model_version.model_id} v{model_version.version}")
                
                except Exception as e:
                    print(f"⚠️ Could not save to Model Manager: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Model training error: {e}")
            return False
    
    def make_prediction(self):
        """ทำนายสัญญาณด้วยโมเดลปัจจุบัน"""
        if self.current_model is None:
            return None
        
        try:
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
            
            return {
                'symbol': self.symbol,
                'signal': final_signal,
                'confidence': avg_confidence,
                'timeframe_votes': f"{buy_votes} BUY, {sell_votes} SELL",
                'current_price': current_price,
                'timestamp': datetime.now(),
                'model_id': self.current_model_id,
                'model_version': self.current_model_version
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return None
    
    def get_active_positions(self):
        """ดึง positions ที่เปิดอยู่"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            return list(positions) if positions else []
        except:
            return []
    
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
    
    def place_order(self, signal, confidence):
        """เปิด order"""
        try:
            if not self.enable_auto_trading:
                print("⚠️ Auto trading disabled")
                return None
            
            positions = self.get_active_positions()
            if len(positions) >= self.max_positions:
                print(f"⚠️ Max positions reached: {len(positions)}/{self.max_positions}")
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
            lot_size = self.base_lot_size
            if confidence > 0.8:
                lot_size *= 1.5
            
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
                "comment": f"Fixed Gold Learning {signal}",
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
                    'timestamp': datetime.now()
                }
                
                self.orders_placed.append(order_info)
                self.performance_data['total_orders'] += 1
                self.performance_data['successful_orders'] += 1
                
                print(f"✅ Order placed: Ticket {result.order}")
                return order_info
            else:
                print(f"❌ Order failed: {result.comment if result else 'Unknown error'}")
                self.performance_data['failed_orders'] += 1
                return None
                
        except Exception as e:
            print(f"❌ Place order error: {e}")
            return None
    
    def format_telegram_message(self, prediction, order_info=None):
        """จัดรูปแบบข้อความ Telegram"""
        signal = prediction['signal']
        confidence = prediction['confidence']
        price = prediction['current_price']
        votes = prediction['timeframe_votes']
        
        emoji = "🟢📈" if signal == "BUY" else "🔴📉"
        action = "ซื้อ" if signal == "BUY" else "ขาย"
        
        tp, sl = self.calculate_tp_sl(signal, price)
        
        message = f"""
🧠 <b>FIXED GOLD LEARNING SIGNAL</b> 🧠

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
✅ <b>Status:</b> Executed
"""
        
        message += f"""
📊 <b>Performance:</b>
• Total Orders: {self.performance_data['total_orders']}
• Success Rate: {(self.performance_data['successful_orders'] / max(1, self.performance_data['total_orders'])) * 100:.1f}%
• Model Updates: {self.performance_data['model_updates']}

⏰ <b>เวลา:</b> {prediction['timestamp'].strftime('%H:%M:%S')}

<i>🧠 Fixed Gold Learning Trader</i>
        """.strip()
        
        return message
    
    def run_trading_session(self, duration_minutes=60, signal_interval_minutes=15):
        """รันเซสชันเทรด"""
        print(f"🧠 Starting Fixed Gold Learning Trading Session ({duration_minutes} minutes)")
        
        # เชื่อมต่อ MT5
        if not self.connect_mt5():
            return False
        
        # เริ่มต้นระบบ Learning
        learning_initialized = self.initialize_learning_system()
        
        # เทรนโมเดลถ้ายังไม่มี
        if self.current_model is None:
            if not self.train_model():
                print("❌ Cannot train model")
                return False
        
        # ส่งข้อความเริ่มต้น
        start_message = f"""
🧠 <b>FIXED GOLD LEARNING TRADER STARTED</b> 🧠

🤖 <b>AI Model:</b> {'Trained' if self.current_model else 'Not Available'}
📊 <b>Symbol:</b> {self.symbol}
⏰ <b>Duration:</b> {duration_minutes} minutes
📡 <b>Signal Interval:</b> {signal_interval_minutes} minutes
🧠 <b>Learning System:</b> {'Enabled' if learning_initialized else 'Basic Mode'}

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
                    print(f"\n⏰ {current_time.strftime('%H:%M:%S')} - Analyzing market...")
                    
                    prediction = self.make_prediction()
                    
                    if prediction and prediction['confidence'] > 0.65:
                        print(f"🤖 AI Signal: {prediction['signal']} ({prediction['confidence']:.1%})")
                        
                        # เปิด order
                        order_info = self.place_order(prediction['signal'], prediction['confidence'])
                        
                        if order_info:
                            message = self.format_telegram_message(prediction, order_info)
                            if self.send_telegram_message(message):
                                signals_sent += 1
                                self.signals_sent.append(prediction)
                                self.performance_data['total_signals'] += 1
                                print(f"✅ Signal sent: {prediction['signal']}")
                    else:
                        if prediction:
                            print(f"⏭️ Signal confidence too low: {prediction['confidence']:.1%}")
                        else:
                            print("⏭️ No prediction available")
                    
                    last_signal_time = current_time
                
                # รอ 1 นาที
                time.sleep(60)
        
        except KeyboardInterrupt:
            print("\n⏹️ Stopped by user")
        
        # ส่งสรุปผล
        positions = self.get_active_positions()
        
        summary_message = f"""
🏁 <b>TRADING SESSION COMPLETED</b> 🏁

📊 <b>Session Summary:</b>
• Signals Sent: {signals_sent}
• Orders Placed: {self.performance_data['total_orders']}
• Success Rate: {(self.performance_data['successful_orders'] / max(1, self.performance_data['total_orders'])) * 100:.1f}%
• Model Updates: {self.performance_data['model_updates']}
• Active Positions: {len(positions)}

<i>🧠 Fixed Gold Learning Trader</i>
        """.strip()
        
        self.send_telegram_message(summary_message)
        
        print(f"\n🏁 Trading session completed!")
        print(f"📊 Signals sent: {signals_sent}")
        print(f"💼 Orders placed: {self.performance_data['total_orders']}")
        
        return True

def main():
    """ฟังก์ชันหลัก"""
    print("🧠 Fixed Gold Learning Trader")
    print("=" * 60)
    
    try:
        # สร้าง trader
        trader = FixedGoldLearningTrader()
        
        # แสดงการตั้งค่า
        print(f"\n⚙️ Configuration:")
        print(f"   💰 Base Lot Size: {trader.base_lot_size}")
        print(f"   🎯 TP: {trader.tp_points} points")
        print(f"   🛡️ SL: {trader.sl_points} points")
        print(f"   🧠 AI Learning: {trader.enable_learning}")
        print(f"   🤖 Auto Trading: {trader.enable_auto_trading}")
        
        # รันเทรด
        duration = int(input("\nTrading duration (minutes, default 60): ") or "60")
        interval = int(input("Signal interval (minutes, default 15): ") or "15")
        
        success = trader.run_trading_session(duration, interval)
        
        if success:
            print("\n🎉 Trading session completed successfully!")
        else:
            print("\n❌ Trading session failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print(f"Error details: {traceback.format_exc()}")
    
    finally:
        try:
            mt5.shutdown()
            print("🔌 MT5 connection closed")
        except:
            pass

if __name__ == "__main__":
    main()