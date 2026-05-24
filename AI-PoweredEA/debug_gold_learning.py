#!/usr/bin/env python3
"""
Debug Gold Learning Trader - เวอร์ชันที่มี debug information เพิ่มเติม
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

print("🔍 Starting Gold Learning Trader Debug Version...")
print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")

# Test imports step by step
print("\n📦 Testing imports...")

try:
    import MetaTrader5 as mt5
    print("✅ MetaTrader5 imported")
except ImportError as e:
    print(f"❌ MetaTrader5 import failed: {e}")
    sys.exit(1)

try:
    import pandas as pd
    import numpy as np
    print("✅ Pandas and NumPy imported")
except ImportError as e:
    print(f"❌ Pandas/NumPy import failed: {e}")
    sys.exit(1)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    print("✅ Scikit-learn imported")
except ImportError as e:
    print(f"❌ Scikit-learn import failed: {e}")
    sys.exit(1)

# Test AI components imports
ai_components_available = {}

try:
    from performance_monitor import PerformanceMonitor
    ai_components_available['performance_monitor'] = True
    print("✅ PerformanceMonitor imported")
except ImportError as e:
    ai_components_available['performance_monitor'] = False
    print(f"⚠️ PerformanceMonitor import failed: {e}")

try:
    from model_manager import ModelManager, ModelType
    ai_components_available['model_manager'] = True
    print("✅ ModelManager imported")
except ImportError as e:
    ai_components_available['model_manager'] = False
    print(f"⚠️ ModelManager import failed: {e}")

try:
    from learning_coordinator import LearningCoordinator, LearningTrigger
    ai_components_available['learning_coordinator'] = True
    print("✅ LearningCoordinator imported")
except ImportError as e:
    ai_components_available['learning_coordinator'] = False
    print(f"⚠️ LearningCoordinator import failed: {e}")

class DebugGoldLearningTrader:
    """Debug version ของ Gold Learning Trader"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        print("\n🧠 Initializing Debug Gold Learning Trader...")
        
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
        self.enable_auto_trading = False  # ปิดไว้ก่อนสำหรับ debug
        self.max_positions = 5
        
        # AI Learning settings
        self.enable_learning = True
        self.learning_interval_hours = 24
        self.performance_threshold = 0.7
        self.min_samples_for_learning = 50
        
        # AI Learning components
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
        
        print("✅ Debug Gold Learning Trader initialized")
    
    def test_telegram_connection(self):
        """ทดสอบการเชื่อมต่อ Telegram"""
        print("\n📱 Testing Telegram connection...")
        
        try:
            test_message = f"""
🔍 <b>TELEGRAM CONNECTION TEST</b> 🔍

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 <b>System:</b> Debug Gold Learning Trader

<i>If you see this message, Telegram connection is working!</i>
            """.strip()
            
            result = self.send_telegram_message(test_message)
            
            if result:
                print("✅ Telegram connection successful")
                return True
            else:
                print("❌ Telegram connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Telegram test error: {e}")
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
    
    def test_mt5_connection(self):
        """ทดสอบการเชื่อมต่อ MT5"""
        print("\n🔌 Testing MT5 connection...")
        
        try:
            if not mt5.initialize():
                print("❌ MT5 initialization failed")
                return False
            
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Cannot get account info")
                return False
            
            print(f"✅ MT5 connected - Account: {account_info.login}")
            print(f"💰 Balance: ${account_info.balance:.2f}")
            
            # ตรวจสอบ symbol ทอง
            gold_symbols = ["XAUUSD", "GOLD", "GOLDm#", "GOLD#", "XAU/USD"]
            found_symbol = None
            
            for symbol in gold_symbols:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is not None:
                    self.symbol = symbol
                    found_symbol = symbol
                    print(f"✅ Gold symbol found: {symbol}")
                    break
            
            if not found_symbol:
                print("⚠️ No gold symbol found - using default")
            
            return True
            
        except Exception as e:
            print(f"❌ MT5 connection error: {e}")
            print(f"Error details: {traceback.format_exc()}")
            return False
    
    def test_data_retrieval(self):
        """ทดสอบการดึงข้อมูล"""
        print("\n📊 Testing data retrieval...")
        
        try:
            for i, timeframe in enumerate(self.timeframes):
                tf_name = self.timeframe_names[i]
                print(f"   Testing {tf_name} data...")
                
                rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, 100)
                
                if rates is None or len(rates) == 0:
                    print(f"   ❌ No {tf_name} data available")
                    continue
                
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                print(f"   ✅ {tf_name}: {len(df)} bars retrieved")
                print(f"      Latest: {df.iloc[-1]['time']}")
                print(f"      Price: {df.iloc[-1]['close']:.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Data retrieval error: {e}")
            print(f"Error details: {traceback.format_exc()}")
            return False
    
    def initialize_learning_system_debug(self):
        """เริ่มต้นระบบ AI Learning แบบ debug"""
        print("\n🧠 Initializing AI Learning System (Debug Mode)...")
        
        success_count = 0
        total_components = 0
        
        # Performance Monitor
        if ai_components_available.get('performance_monitor', False):
            try:
                print("   Initializing Performance Monitor...")
                self.performance_monitor = PerformanceMonitor()
                print("   ✅ Performance Monitor initialized")
                success_count += 1
            except Exception as e:
                print(f"   ❌ Performance Monitor failed: {e}")
                print(f"   Error details: {traceback.format_exc()}")
        else:
            print("   ⚠️ Performance Monitor not available")
        total_components += 1
        
        # Model Manager
        if ai_components_available.get('model_manager', False):
            try:
                print("   Initializing Model Manager...")
                self.model_manager = ModelManager()
                print("   ✅ Model Manager initialized")
                success_count += 1
            except Exception as e:
                print(f"   ❌ Model Manager failed: {e}")
                print(f"   Error details: {traceback.format_exc()}")
        else:
            print("   ⚠️ Model Manager not available")
        total_components += 1
        
        # Learning Coordinator
        if ai_components_available.get('learning_coordinator', False):
            try:
                print("   Initializing Learning Coordinator...")
                self.learning_coordinator = LearningCoordinator()
                print("   ✅ Learning Coordinator initialized")
                success_count += 1
            except Exception as e:
                print(f"   ❌ Learning Coordinator failed: {e}")
                print(f"   Error details: {traceback.format_exc()}")
        else:
            print("   ⚠️ Learning Coordinator not available")
        total_components += 1
        
        print(f"\n📊 Learning System Status: {success_count}/{total_components} components initialized")
        
        if success_count > 0:
            print("✅ Learning system partially initialized")
            return True
        else:
            print("❌ Learning system initialization failed")
            return False
    
    def test_model_training(self):
        """ทดสอบการเทรนโมเดล"""
        print("\n🤖 Testing model training...")
        
        try:
            # ดึงข้อมูลสำหรับเทรน
            print("   Collecting training data...")
            
            all_features = []
            all_labels = []
            
            for i, timeframe in enumerate(self.timeframes[:2]):  # ใช้แค่ 2 timeframes สำหรับทดสอบ
                tf_name = self.timeframe_names[i]
                print(f"   Processing {tf_name} data...")
                
                rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, 200)
                if rates is None or len(rates) == 0:
                    continue
                
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                # คำนวณ indicators แบบง่าย
                df['rsi'] = 50.0  # dummy RSI
                df['macd'] = 0.0  # dummy MACD
                df['bb_position'] = 0.5  # dummy BB position
                
                # สร้าง labels แบบง่าย
                df['future_return'] = df['close'].shift(-5) / df['close'] - 1
                df['label'] = np.where(df['future_return'] > 0.001, 1, 0)
                
                # เลือก features
                features = ['rsi', 'macd', 'bb_position']
                df_clean = df[features + ['label']].dropna()
                
                if len(df_clean) > 10:
                    X = df_clean[features].values
                    y = df_clean['label'].values
                    all_features.append(X)
                    all_labels.append(y)
                    print(f"   ✅ {tf_name}: {len(df_clean)} samples")
            
            if not all_features:
                print("   ❌ No training data available")
                return False
            
            X_combined = np.vstack(all_features)
            y_combined = np.hstack(all_labels)
            
            print(f"   📊 Total training samples: {len(X_combined)}")
            
            # เทรนโมเดล
            print("   Training model...")
            X_scaled = self.scaler.fit_transform(X_combined)
            
            model = RandomForestClassifier(
                n_estimators=50,  # น้อยกว่าปกติสำหรับทดสอบ
                max_depth=10,
                random_state=42,
                n_jobs=1
            )
            
            model.fit(X_scaled, y_combined)
            accuracy = model.score(X_scaled, y_combined)
            
            self.current_model = model
            
            print(f"   ✅ Model trained successfully!")
            print(f"   📊 Training accuracy: {accuracy:.2%}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Model training error: {e}")
            print(f"   Error details: {traceback.format_exc()}")
            return False
    
    def run_debug_session(self, duration_minutes=5):
        """รันเซสชัน debug"""
        print(f"\n🔍 Starting Debug Session ({duration_minutes} minutes)")
        print("=" * 60)
        
        # ทดสอบการเชื่อมต่อ
        if not self.test_mt5_connection():
            print("❌ Cannot continue without MT5 connection")
            return False
        
        # ทดสอบการดึงข้อมูล
        if not self.test_data_retrieval():
            print("❌ Cannot continue without data")
            return False
        
        # ทดสอบ Telegram
        self.test_telegram_connection()
        
        # ทดสอบระบบ Learning
        learning_ok = self.initialize_learning_system_debug()
        
        # ทดสอบการเทรนโมเดล
        model_ok = self.test_model_training()
        
        # ส่งข้อความเริ่มต้น
        start_message = f"""
🔍 <b>DEBUG SESSION STARTED</b> 🔍

⏰ <b>Duration:</b> {duration_minutes} minutes
📊 <b>Symbol:</b> {self.symbol}
🧠 <b>Learning System:</b> {'OK' if learning_ok else 'Failed'}
🤖 <b>Model:</b> {'Trained' if model_ok else 'Failed'}

<i>🔍 Running in debug mode...</i>
        """.strip()
        
        self.send_telegram_message(start_message)
        
        # รันลูปหลัก
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        iteration = 0
        
        try:
            while datetime.now() < end_time:
                iteration += 1
                current_time = datetime.now()
                
                print(f"\n🔄 Debug Iteration {iteration} - {current_time.strftime('%H:%M:%S')}")
                
                # ทดสอบการดึงข้อมูลล่าสุด
                try:
                    rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 10)
                    if rates is not None and len(rates) > 0:
                        latest_price = rates[-1]['close']
                        print(f"   📊 Latest price: ${latest_price:.2f}")
                    else:
                        print("   ⚠️ No recent data available")
                except Exception as e:
                    print(f"   ❌ Data error: {e}")
                
                # ทดสอบการทำนาย (ถ้ามีโมเดล)
                if self.current_model is not None:
                    try:
                        # สร้างข้อมูลทดสอบ
                        test_features = np.array([[50.0, 0.0, 0.5]])  # dummy features
                        test_scaled = self.scaler.transform(test_features)
                        prediction = self.current_model.predict(test_scaled)[0]
                        probability = self.current_model.predict_proba(test_scaled)[0]
                        confidence = max(probability)
                        
                        signal = "BUY" if prediction == 1 else "SELL"
                        print(f"   🤖 AI Prediction: {signal} (confidence: {confidence:.1%})")
                        
                    except Exception as e:
                        print(f"   ❌ Prediction error: {e}")
                
                # รอ 30 วินาที
                print("   ⏳ Waiting 30 seconds...")
                time.sleep(30)
        
        except KeyboardInterrupt:
            print("\n⏹️ Debug session stopped by user")
        
        # ส่งสรุปผล
        summary_message = f"""
🏁 <b>DEBUG SESSION COMPLETED</b> 🏁

⏰ <b>Duration:</b> {duration_minutes} minutes
🔄 <b>Iterations:</b> {iteration}
🧠 <b>Learning System:</b> {'OK' if learning_ok else 'Failed'}
🤖 <b>Model:</b> {'OK' if model_ok else 'Failed'}

<i>🔍 Debug session completed</i>
        """.strip()
        
        self.send_telegram_message(summary_message)
        
        print(f"\n🏁 Debug session completed!")
        print(f"🔄 Total iterations: {iteration}")
        
        return True

def main():
    """ฟังก์ชันหลัก"""
    print("🔍 Debug Gold Learning Trader")
    print("=" * 60)
    
    try:
        # สร้าง trader
        trader = DebugGoldLearningTrader()
        
        # รันเซสชัน debug
        duration = int(input("\nDebug duration (minutes, default 5): ") or "5")
        
        success = trader.run_debug_session(duration)
        
        if success:
            print("\n🎉 Debug session completed successfully!")
        else:
            print("\n❌ Debug session failed")
    
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