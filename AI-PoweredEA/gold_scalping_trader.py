"""
Gold Scalping Trader - ระบบ Scalping ทองแบบกำไรเล็กๆ แต่บ่อยๆ
เน้น M1 timeframe, เข้า-ออกเร็ว, กำไร 5-10 pips ต่อรอบ
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
except ImportError as e:
    print(f"Warning: Could not import AI components: {e}")
    print("Running in standalone mode...")

class GoldScalpingTrader:
    """ระบบ Scalping ทองแบบกำไรเล็กๆ แต่บ่อยๆ"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        # Telegram settings
        self.telegram_token = telegram_token or "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
        self.chat_id = chat_id or "-1002852894581"
        
        # Trading settings
        self.symbol = "GOLDm#"
        self.main_timeframe = mt5.TIMEFRAME_M1  # หลัก M1 สำหรับ scalping
        self.confirm_timeframes = [mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M15]  # ยืนยันทิศทาง
        self.base_lot_size = 0.01
        self.max_spread = 30  # spread แน่นสำหรับ scalping
        
        # Scalping Risk Management
        self.tp_points = 120    # Take Profit 5 pips (เล็กๆ)
        self.sl_points = 150    # Stop Loss 3 pips (แน่น)
        self.max_positions = 10 # จำกัด positions
        self.max_daily_trades = 100  # จำกัดเทรดต่อวัน
        
        # Scalping Strategy Settings
        self.enable_auto_trading = True
        self.scalping_mode = True
        self.quick_exit_enabled = True  # ออกเร็วเมื่อกำไร
        self.breakeven_points = 100      # เลื่อน SL ไป breakeven เมื่อกำไร 2 pips
        self.partial_close_points = 60  # ปิดครึ่งเมื่อกำไร 4 pips
        self.adaptive_mode = True       # ปรับการตั้งค่าตาม market conditions
        
        # Timing settings
        self.signal_interval_seconds = 30  # ตรวจสัญญาณทุก 30 วินาที
        self.max_hold_minutes = 10         # ถือสูงสุด 10 นาที
        self.avoid_news_minutes = 30       # หลีกเลี่ยงข่าว 30 นาทีก่อน-หลัง
        
        # Market condition filters (ปรับให้เหมาะกับทองจริง)
        self.min_volatility = 0.1     # volatility ขั้นต่ำ (ทองต้องมีการเคลื่อนไหว)
        self.max_volatility = 2.0     # volatility สูงสุด (ยอมรับได้สำหรับทอง)
        self.trend_strength_threshold = 0.6
        
        # AI components
        self.model = None
        self.scaler = StandardScaler()
        self.performance_monitor = None
        
        # Trading data
        self.signals_sent = []
        self.orders_placed = []
        self.daily_trades = 0
        self.daily_profit = 0.0
        self.last_trade_time = None
        
        self.performance_data = {
            'total_signals': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'avg_profit_per_trade': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'current_streak': 0,
            'scalping_efficiency': 0.0
        }
        
        print("⚡ Gold Scalping Trader initialized")
    
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
            print(f"⚡ Gold symbol: {self.symbol}")
            
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
    
    def calculate_scalping_indicators(self, df):
        """คำนวณ indicators สำหรับ scalping"""
        try:
            if df is None or len(df) < 20:
                return None
            
            # Fast RSI (5 periods สำหรับ scalping)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=5).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=5).mean()
            rs = gain / loss
            df['rsi_fast'] = 100 - (100 / (1 + rs))
            
            # Standard RSI (14 periods)
            gain_std = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss_std = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs_std = gain_std / loss_std
            df['rsi'] = 100 - (100 / (1 + rs_std))
            
            # Fast MACD (5,13,4 สำหรับ scalping)
            exp1_fast = df['close'].ewm(span=5).mean()
            exp2_fast = df['close'].ewm(span=13).mean()
            df['macd_fast'] = exp1_fast - exp2_fast
            df['macd_signal_fast'] = df['macd_fast'].ewm(span=4).mean()
            df['macd_histogram_fast'] = df['macd_fast'] - df['macd_signal_fast']
            
            # Standard MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            
            # Fast Bollinger Bands (10 periods)
            df['bb_middle_fast'] = df['close'].rolling(window=10).mean()
            bb_std_fast = df['close'].rolling(window=10).std()
            df['bb_upper_fast'] = df['bb_middle_fast'] + (bb_std_fast * 1.5)
            df['bb_lower_fast'] = df['bb_middle_fast'] - (bb_std_fast * 1.5)
            df['bb_position_fast'] = (df['close'] - df['bb_lower_fast']) / (df['bb_upper_fast'] - df['bb_lower_fast'])
            
            # Fast EMAs
            df['ema_8'] = df['close'].ewm(span=8).mean()
            df['ema_21'] = df['close'].ewm(span=21).mean()
            df['ema_signal'] = np.where(df['ema_8'] > df['ema_21'], 1, 0)
            
            # Price momentum
            df['momentum_3'] = df['close'] / df['close'].shift(3) - 1
            df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
            
            # Volatility (ATR)
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            df['atr'] = df['true_range'].rolling(window=10).mean()
            
            # Volume analysis
            df['volume_sma'] = df['tick_volume'].rolling(window=10).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
            
            # Price action patterns
            df['candle_body'] = abs(df['close'] - df['open'])
            df['candle_wick_upper'] = df['high'] - np.maximum(df['open'], df['close'])
            df['candle_wick_lower'] = np.minimum(df['open'], df['close']) - df['low']
            df['candle_type'] = np.where(df['close'] > df['open'], 1, -1)  # 1=bullish, -1=bearish
            
            return df
            
        except Exception as e:
            print(f"❌ Scalping indicator calculation error: {e}")
            return None
    
    def check_market_conditions(self):
        """ตรวจสอบสภาพตลาดสำหรับ scalping"""
        try:
            # ดึงข้อมูล M1 ล่าสุด
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 50)
            if df_m1 is None:
                return False, "No M1 data"
            
            df_m1 = self.calculate_scalping_indicators(df_m1)
            if df_m1 is None:
                return False, "Cannot calculate indicators"
            
            latest = df_m1.iloc[-1]
            
            # ตรวจสอบ spread
            tick = mt5.symbol_info_tick(self.symbol)
            symbol_info = mt5.symbol_info(self.symbol)
            
            spread_points = 0
            if tick and symbol_info:
                spread_points = (tick.ask - tick.bid) / symbol_info.point
                if spread_points > self.max_spread:
                    return False, f"Spread too high: {spread_points:.1f} points (max: {self.max_spread})"
            
            # ตรวจสอบ volatility (ATR)
            current_atr = latest['atr']
            if current_atr < self.min_volatility:
                return False, f"Volatility too low: {current_atr:.3f} (min: {self.min_volatility})"
            elif current_atr > self.max_volatility:
                return False, f"Volatility too high: {current_atr:.3f} (max: {self.max_volatility}) - Market too volatile for scalping"
            
            # ตรวจสอบเวลาเทรด (หลีกเลี่ยงช่วงข่าว)
            current_time = datetime.now()
            
            # หลีกเลี่ยงช่วงเปิด-ปิดตลาด (ใช้เวลาท้องถิ่น)
            local_hour = current_time.hour
            if local_hour < 6 or local_hour > 23:  # ปรับตามเวลาท้องถิ่น
                return False, f"Outside trading hours: {local_hour}:00 (trade: 06:00-23:00)"
            
            # ตรวจสอบว่าเพิ่งมีเทรดหรือไม่ (cooldown)
            if self.last_trade_time:
                time_since_last = (current_time - self.last_trade_time).total_seconds()
                if time_since_last < 60:  # รอ 1 นาทีหลังเทรดล่าสุด
                    return False, f"Cooldown: {60-time_since_last:.0f}s remaining"
            
            # ตรวจสอบจำนวนเทรดต่อวัน
            if self.daily_trades >= self.max_daily_trades:
                return False, f"Daily trade limit reached: {self.daily_trades}/{self.max_daily_trades}"
            
            # แสดงข้อมูลสภาพตลาด
            market_info = f"ATR: {current_atr:.3f}, Spread: {spread_points:.1f}pts, RSI: {latest['rsi_fast']:.1f}"
            return True, f"Market OK - {market_info}"
            
        except Exception as e:
            print(f"❌ Market condition check error: {e}")
            return False, str(e)
    
    def get_market_analysis(self):
        """วิเคราะห์สภาพตลาดแบบละเอียด"""
        try:
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 50)
            if df_m1 is None:
                return None
            
            df_m1 = self.calculate_scalping_indicators(df_m1)
            if df_m1 is None:
                return None
            
            latest = df_m1.iloc[-1]
            tick = mt5.symbol_info_tick(self.symbol)
            symbol_info = mt5.symbol_info(self.symbol)
            
            analysis = {
                'current_price': tick.bid if tick else 0,
                'atr': latest['atr'],
                'atr_status': 'Normal' if self.min_volatility <= latest['atr'] <= self.max_volatility else 'Out of range',
                'spread_points': (tick.ask - tick.bid) / symbol_info.point if tick and symbol_info else 0,
                'spread_status': 'OK' if ((tick.ask - tick.bid) / symbol_info.point if tick and symbol_info else 999) <= self.max_spread else 'Too high',
                'rsi_fast': latest['rsi_fast'],
                'rsi_status': 'Oversold' if latest['rsi_fast'] < 30 else 'Overbought' if latest['rsi_fast'] > 70 else 'Normal',
                'macd_fast': latest['macd_fast'],
                'macd_status': 'Bullish' if latest['macd_fast'] > 0 else 'Bearish',
                'bb_position': latest['bb_position_fast'],
                'bb_status': 'Lower band' if latest['bb_position_fast'] < 0.2 else 'Upper band' if latest['bb_position_fast'] > 0.8 else 'Middle',
                'volume_ratio': latest['volume_ratio'],
                'volume_status': 'High' if latest['volume_ratio'] > 1.5 else 'Low' if latest['volume_ratio'] < 0.8 else 'Normal',
                'daily_trades': self.daily_trades,
                'daily_profit': self.daily_profit
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Market analysis error: {e}")
            return None
    
    def adapt_to_market_conditions(self):
        """ปรับการตั้งค่าตามสภาพตลาด"""
        if not self.adaptive_mode:
            return
        
        try:
            analysis = self.get_market_analysis()
            if not analysis:
                return
            
            current_atr = analysis['atr']
            
            # ปรับ volatility range อัตโนมัติ
            if current_atr > self.max_volatility:
                new_max = current_atr * 1.2
                print(f"🔧 Adapting max volatility: {self.max_volatility:.1f} → {new_max:.1f}")
                self.max_volatility = new_max
            
            # ปรับ TP/SL ตาม volatility
            if current_atr > 1.5:  # Very high volatility
                self.tp_points = 100  # 10 pips
                self.sl_points = 60   # 6 pips
                print(f"🔧 High volatility mode: TP={self.tp_points}, SL={self.sl_points}")
            elif current_atr > 1.0:  # High volatility
                self.tp_points = 80   # 8 pips
                self.sl_points = 50   # 5 pips
                print(f"🔧 Medium-high volatility mode: TP={self.tp_points}, SL={self.sl_points}")
            elif current_atr < 0.3:  # Low volatility
                self.tp_points = 30   # 3 pips
                self.sl_points = 20   # 2 pips
                print(f"🔧 Low volatility mode: TP={self.tp_points}, SL={self.sl_points}")
            
            # ปรับ spread tolerance
            current_spread = analysis['spread_points']
            if current_spread > self.max_spread:
                new_max_spread = current_spread * 1.3
                print(f"🔧 Adapting max spread: {self.max_spread} → {new_max_spread:.0f}")
                self.max_spread = int(new_max_spread)
            
        except Exception as e:
            print(f"❌ Adaptation error: {e}")
    
    def train_scalping_model(self):
        """เทรนโมเดลสำหรับ scalping"""
        print("⚡ Training Scalping AI model...")
        
        # ดึงข้อมูล M1 จำนวนมาก
        df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 2000)
        if df_m1 is None:
            return False
        
        df_m1 = self.calculate_scalping_indicators(df_m1)
        if df_m1 is None:
            return False
        
        # สร้าง labels สำหรับ scalping (กำไร 5 pips ใน 5 นาที)
        future_bars = 5  # ดู 5 นาทีข้างหน้า
        df_m1['future_high'] = df_m1['high'].shift(-future_bars).rolling(window=future_bars).max()
        df_m1['future_low'] = df_m1['low'].shift(-future_bars).rolling(window=future_bars).min()
        
        # คำนวณผลตอบแทนที่เป็นไปได้
        df_m1['potential_buy_profit'] = (df_m1['future_high'] - df_m1['close']) / df_m1['close']
        df_m1['potential_sell_profit'] = (df_m1['close'] - df_m1['future_low']) / df_m1['close']
        
        # กำหนด threshold สำหรับ scalping (0.0005 = 5 pips สำหรับทอง)
        scalping_threshold = 0.0005
        
        # สร้าง labels: 1=BUY, 0=SELL, -1=NO_TRADE
        conditions = [
            (df_m1['potential_buy_profit'] > scalping_threshold) & (df_m1['potential_buy_profit'] > df_m1['potential_sell_profit']),
            (df_m1['potential_sell_profit'] > scalping_threshold) & (df_m1['potential_sell_profit'] > df_m1['potential_buy_profit'])
        ]
        choices = [1, 0]
        df_m1['label'] = np.select(conditions, choices, default=-1)
        
        # เลือกเฉพาะ samples ที่มี signal ชัดเจน
        df_clean = df_m1[df_m1['label'] != -1].copy()
        
        # เลือก features สำหรับ scalping
        scalping_features = [
            'rsi_fast', 'rsi', 'macd_fast', 'macd_histogram_fast', 'macd',
            'bb_position_fast', 'ema_signal', 'momentum_3', 'momentum_5',
            'atr', 'volume_ratio', 'candle_body', 'candle_type'
        ]
        
        # ลบ NaN
        df_final = df_clean[scalping_features + ['label']].dropna()
        
        if len(df_final) < 100:
            print("❌ Not enough scalping training data")
            return False
        
        X = df_final[scalping_features].values
        y = df_final['label'].values
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model สำหรับ scalping
        self.model = RandomForestClassifier(
            n_estimators=100,  # น้อยกว่าปกติเพื่อความเร็ว
            max_depth=10,
            min_samples_split=3,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_scaled, y)
        accuracy = self.model.score(X_scaled, y)
        
        print(f"✅ Scalping model trained!")
        print(f"📊 Training accuracy: {accuracy:.2%}")
        print(f"📈 Training samples: {len(X)}")
        print(f"⚡ Features: {len(scalping_features)}")
        
        return True
    
    def make_scalping_prediction(self):
        """ทำนายสัญญาณ scalping"""
        if self.model is None:
            return None
        
        try:
            # ดึงข้อมูล M1 ล่าสุด
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 50)
            if df_m1 is None:
                return None
            
            df_m1 = self.calculate_scalping_indicators(df_m1)
            if df_m1 is None:
                return None
            
            # ดึงข้อมูล M5 และ M15 เพื่อยืนยันทิศทาง
            df_m5 = self.get_gold_data(mt5.TIMEFRAME_M5, 20)
            df_m15 = self.get_gold_data(mt5.TIMEFRAME_M15, 10)
            
            # คำนวณทิศทางจาก timeframe ใหญ่
            trend_direction = 0  # 0=neutral, 1=bullish, -1=bearish
            
            if df_m5 is not None and len(df_m5) > 10:
                df_m5 = self.calculate_scalping_indicators(df_m5)
                if df_m5 is not None:
                    m5_ema_signal = df_m5['ema_signal'].iloc[-1]
                    if m5_ema_signal == 1:
                        trend_direction += 1
                    else:
                        trend_direction -= 1
            
            if df_m15 is not None and len(df_m15) > 10:
                df_m15 = self.calculate_scalping_indicators(df_m15)
                if df_m15 is not None:
                    m15_ema_signal = df_m15['ema_signal'].iloc[-1]
                    if m15_ema_signal == 1:
                        trend_direction += 1
                    else:
                        trend_direction -= 1
            
            # เลือก features ล่าสุดจาก M1
            scalping_features = [
                'rsi_fast', 'rsi', 'macd_fast', 'macd_histogram_fast', 'macd',
                'bb_position_fast', 'ema_signal', 'momentum_3', 'momentum_5',
                'atr', 'volume_ratio', 'candle_body', 'candle_type'
            ]
            
            latest_data = df_m1[scalping_features].iloc[-1:].values
            
            if np.isnan(latest_data).any():
                return None
            
            # Normalize และทำนาย
            features_scaled = self.scaler.transform(latest_data)
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            confidence = max(probability)
            
            # แปลงเป็นสัญญาณ
            signal = "BUY" if prediction == 1 else "SELL"
            
            # ปรับ confidence ตาม trend direction
            if trend_direction > 0 and signal == "BUY":
                confidence *= 1.1  # เพิ่ม confidence ถ้าสอดคล้องกับ trend
            elif trend_direction < 0 and signal == "SELL":
                confidence *= 1.1
            elif trend_direction > 0 and signal == "SELL":
                confidence *= 0.9  # ลด confidence ถ้าขัด trend
            elif trend_direction < 0 and signal == "BUY":
                confidence *= 0.9
            
            confidence = min(confidence, 1.0)  # จำกัดไม่เกิน 1.0
            
            # ดูราคาปัจจุบัน
            tick = mt5.symbol_info_tick(self.symbol)
            current_price = tick.bid if tick else 0
            
            # ดูข้อมูลเพิ่มเติม
            latest_candle = df_m1.iloc[-1]
            
            result = {
                'symbol': self.symbol,
                'signal': signal,
                'confidence': confidence,
                'current_price': current_price,
                'trend_direction': trend_direction,
                'atr': latest_candle['atr'],
                'rsi_fast': latest_candle['rsi_fast'],
                'macd_fast': latest_candle['macd_fast'],
                'bb_position_fast': latest_candle['bb_position_fast'],
                'volume_ratio': latest_candle['volume_ratio'],
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Scalping prediction error: {e}")
            return None
    
    def calculate_scalping_tp_sl(self, signal, entry_price):
        """คำนวณ TP/SL สำหรับ scalping"""
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
            print(f"❌ Scalping TP/SL calculation error: {e}")
            return None, None
    
    def get_active_positions(self):
        """ดึง positions ที่เปิดอยู่"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            return list(positions) if positions else []
        except:
            return []
    
    def place_scalping_order(self, signal, confidence, prediction_data):
        """เปิด order สำหรับ scalping"""
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
            tp, sl = self.calculate_scalping_tp_sl(signal, price)
            if tp is None or sl is None:
                return None
            
            # กำหนด lot size (เล็กสำหรับ scalping)
            lot_size = self.base_lot_size
            
            # เพิ่ม lot ถ้า confidence สูงมาก
            if confidence > 0.9:
                lot_size *= 1.5
            elif confidence > 0.8:
                lot_size *= 1.2
            
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
                "deviation": 10,  # deviation เล็กสำหรับ scalping
                "magic": 234001,  # magic number ต่างจาก systems อื่น
                "comment": f"Gold Scalping {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            print(f"⚡ Scalping order: {signal} {lot_size} lots @ ${price:.2f}")
            print(f"   🎯 TP: ${tp:.2f} (+{self.tp_points} points)")
            print(f"   🛡️ SL: ${sl:.2f} (-{self.sl_points} points)")
            print(f"   📊 Confidence: {confidence:.1%}")
            
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
                    'timestamp': datetime.now(),
                    'prediction_data': prediction_data,
                    'expected_profit': self.tp_points * symbol_info.point * lot_size * 100,
                    'max_loss': self.sl_points * symbol_info.point * lot_size * 100
                }
                
                self.orders_placed.append(order_info)
                self.daily_trades += 1
                self.last_trade_time = datetime.now()
                self.performance_data['total_trades'] += 1
                
                print(f"✅ Scalping order placed: Ticket {result.order}")
                return order_info
            else:
                print(f"❌ Scalping order failed: {result.comment if result else 'Unknown error'}")
                return None
                
        except Exception as e:
            print(f"❌ Place scalping order error: {e}")
            return None
    
    def manage_scalping_positions(self):
        """จัดการ positions สำหรับ scalping"""
        try:
            positions = self.get_active_positions()
            
            for pos in positions:
                # ตรวจสอบเวลาที่ถือ position
                position_age = datetime.now() - datetime.fromtimestamp(pos.time)
                
                # ปิดถ้าถือนานเกินไป
                if position_age.total_seconds() > self.max_hold_minutes * 60:
                    print(f"⏰ Closing position {pos.ticket} - held too long ({position_age})")
                    self.close_position(pos.ticket, "Time limit")
                    continue
                
                # Breakeven management
                if pos.profit > 0:
                    symbol_info = mt5.symbol_info(self.symbol)
                    profit_points = pos.profit / (symbol_info.point * pos.volume * 100)
                    
                    # เลื่อน SL ไป breakeven
                    if profit_points >= self.breakeven_points:
                        if pos.type == mt5.POSITION_TYPE_BUY:
                            new_sl = pos.price_open + (5 * symbol_info.point)  # breakeven + 0.5 pip
                            if new_sl > pos.sl:
                                self.modify_position_sl(pos.ticket, new_sl)
                                print(f"📈 Moved SL to breakeven+: {pos.ticket}")
                        else:
                            new_sl = pos.price_open - (5 * symbol_info.point)  # breakeven - 0.5 pip
                            if new_sl < pos.sl:
                                self.modify_position_sl(pos.ticket, new_sl)
                                print(f"📉 Moved SL to breakeven+: {pos.ticket}")
                    
                    # Partial close
                    if profit_points >= self.partial_close_points and pos.volume > symbol_info.volume_min * 2:
                        partial_volume = pos.volume / 2
                        partial_volume = round(partial_volume / symbol_info.volume_step) * symbol_info.volume_step
                        
                        if partial_volume >= symbol_info.volume_min:
                            print(f"📊 Partial close: {pos.ticket} - {partial_volume} lots")
                            self.partial_close_position(pos.ticket, partial_volume)
            
        except Exception as e:
            print(f"❌ Position management error: {e}")
    
    def close_position(self, ticket, reason="Manual"):
        """ปิด position"""
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
            
            position = position[0]
            
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(self.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(self.symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 10,
                "magic": 234001,
                "comment": f"Scalping Close - {reason}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                # อัพเดทสถิติ
                if position.profit > 0:
                    self.performance_data['winning_trades'] += 1
                    self.performance_data['current_streak'] = max(0, self.performance_data['current_streak']) + 1
                else:
                    self.performance_data['losing_trades'] += 1
                    self.performance_data['current_streak'] = min(0, self.performance_data['current_streak']) - 1
                
                self.performance_data['total_profit'] += position.profit
                self.daily_profit += position.profit
                
                # คำนวณ win rate
                total_closed = self.performance_data['winning_trades'] + self.performance_data['losing_trades']
                if total_closed > 0:
                    self.performance_data['win_rate'] = self.performance_data['winning_trades'] / total_closed
                    self.performance_data['avg_profit_per_trade'] = self.performance_data['total_profit'] / total_closed
                
                print(f"✅ Position closed: {ticket} - P&L: ${position.profit:.2f}")
                return True
            else:
                print(f"❌ Failed to close position {ticket}")
                return False
                
        except Exception as e:
            print(f"❌ Close position error: {e}")
            return False
    
    def modify_position_sl(self, ticket, new_sl):
        """แก้ไข Stop Loss"""
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
            return result and result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            print(f"❌ Modify SL error: {e}")
            return False
    
    def partial_close_position(self, ticket, close_volume):
        """ปิด position บางส่วน"""
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
            
            position = position[0]
            
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(self.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(self.symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": close_volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 10,
                "magic": 234001,
                "comment": "Scalping Partial Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            return result and result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            print(f"❌ Partial close error: {e}")
            return False
    
    def format_scalping_message(self, prediction, order_info=None):
        """จัดรูปแบบข้อความ Telegram สำหรับ scalping"""
        signal = prediction['signal']
        confidence = prediction['confidence']
        price = prediction['current_price']
        
        emoji = "⚡🟢" if signal == "BUY" else "⚡🔴"
        action = "ซื้อ" if signal == "BUY" else "ขาย"
        
        tp, sl = self.calculate_scalping_tp_sl(signal, price)
        
        message = f"""
⚡ <b>GOLD SCALPING SIGNAL</b> ⚡

{emoji} <b>สัญญาณ: {action} ({signal})</b>
💰 <b>ราคาเข้า:</b> ${price:.2f}
🎯 <b>Take Profit:</b> ${tp:.2f} (+{self.tp_points} points)
🛡️ <b>Stop Loss:</b> ${sl:.2f} (-{self.sl_points} points)
📊 <b>ความมั่นใจ:</b> {confidence:.1%}
📈 <b>Trend:</b> {prediction.get('trend_direction', 0):+d}
⚡ <b>ATR:</b> {prediction.get('atr', 0):.6f}
"""
        
        if order_info:
            expected_profit = order_info.get('expected_profit', 0)
            max_loss = order_info.get('max_loss', 0)
            
            message += f"""
💼 <b>ORDER PLACED:</b>
🎫 <b>Ticket:</b> {order_info['ticket']}
📊 <b>Volume:</b> {order_info['volume']} lots
💵 <b>Expected Profit:</b> ${expected_profit:.2f}
⚠️ <b>Max Loss:</b> ${max_loss:.2f}
✅ <b>Status:</b> Executed
"""
        
        message += f"""
📊 <b>Daily Stats:</b>
• Trades: {self.daily_trades}/{self.max_daily_trades}
• Win Rate: {self.performance_data['win_rate']:.1%}
• Daily P&L: ${self.daily_profit:.2f}

⏰ <b>เวลา:</b> {prediction['timestamp'].strftime('%H:%M:%S')}

<i>⚡ Gold Scalping Trader</i>
        """.strip()
        
        return message
    
    def run_scalping_session(self, duration_minutes=60):
        """รันเซสชัน scalping"""
        print(f"⚡ Starting Gold Scalping Session ({duration_minutes} minutes)")
        
        if not self.connect_mt5():
            return False
        
        if not self.train_scalping_model():
            return False
        
        # ส่งข้อความเริ่มต้น
        start_message = f"""
⚡ <b>GOLD SCALPING TRADER STARTED</b> ⚡

🤖 <b>AI Model:</b> Scalping Optimized
📊 <b>Symbol:</b> {self.symbol}
⏰ <b>Duration:</b> {duration_minutes} minutes
📡 <b>Signal Check:</b> Every {self.signal_interval_seconds} seconds

🎯 <b>Target:</b> +{self.tp_points} points ({self.tp_points/10} pips)
🛡️ <b>Risk:</b> -{self.sl_points} points ({self.sl_points/10} pips)
📊 <b>Max Trades:</b> {self.max_daily_trades}/day
⚡ <b>Max Hold:</b> {self.max_hold_minutes} minutes

<i>🚀 Ready for high-frequency scalping!</i>
        """.strip()
        
        self.send_telegram_message(start_message)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        signals_sent = 0
        
        try:
            while datetime.now() < end_time:
                current_time = datetime.now()
                
                # จัดการ positions ที่มีอยู่
                self.manage_scalping_positions()
                
                # ปรับการตั้งค่าตามสภาพตลาด
                if current_time.second == 0:  # ปรับทุกนาที
                    self.adapt_to_market_conditions()
                
                # ตรวจสอบสภาพตลาด
                market_ok, market_msg = self.check_market_conditions()
                
                if market_ok:
                    # ทำนายสัญญาณ
                    prediction = self.make_scalping_prediction()
                    
                    if prediction and prediction['confidence'] > 0.7:  # threshold สูงสำหรับ scalping
                        print(f"⚡ Scalping signal: {prediction['signal']} ({prediction['confidence']:.1%})")
                        
                        # เปิด order
                        order_info = self.place_scalping_order(
                            prediction['signal'], 
                            prediction['confidence'],
                            prediction
                        )
                        
                        if order_info:
                            message = self.format_scalping_message(prediction, order_info)
                            if self.send_telegram_message(message):
                                signals_sent += 1
                                self.signals_sent.append(prediction)
                                print(f"✅ Scalping signal sent: {prediction['signal']}")
                    else:
                        if prediction:
                            print(f"⏭️ Signal confidence too low: {prediction['confidence']:.1%}")
                else:
                    print(f"⏳ Market not ready: {market_msg}")
                
                # รอตามช่วงเวลาที่กำหนด
                time.sleep(self.signal_interval_seconds)
        
        except KeyboardInterrupt:
            print("\n⏹️ Scalping stopped by user")
        
        # ปิด positions ที่เหลือ
        positions = self.get_active_positions()
        for pos in positions:
            self.close_position(pos.ticket, "Session end")
        
        # ส่งสรุปผล
        final_positions = self.get_active_positions()
        
        summary_message = f"""
🏁 <b>SCALPING SESSION COMPLETED</b> 🏁

📊 <b>Session Summary:</b>
• Signals Sent: {signals_sent}
• Total Trades: {self.daily_trades}
• Winning Trades: {self.performance_data['winning_trades']}
• Losing Trades: {self.performance_data['losing_trades']}
• Win Rate: {self.performance_data['win_rate']:.1%}
• Session P&L: ${self.daily_profit:.2f}
• Avg Profit/Trade: ${self.performance_data['avg_profit_per_trade']:.2f}
• Remaining Positions: {len(final_positions)}

<i>⚡ Gold Scalping Trader</i>
        """.strip()
        
        self.send_telegram_message(summary_message)
        
        print(f"\n🏁 Scalping session completed!")
        print(f"⚡ Signals sent: {signals_sent}")
        print(f"💼 Total trades: {self.daily_trades}")
        print(f"🎯 Win rate: {self.performance_data['win_rate']:.1%}")
        print(f"💰 Session P&L: ${self.daily_profit:.2f}")
        
        return True

def main():
    """ฟังก์ชันหลัก"""
    print("⚡ Gold Scalping Trader - High Frequency Trading")
    print("=" * 60)
    
    # สร้าง trader
    trader = GoldScalpingTrader()
    
    # แสดงการตั้งค่า
    print(f"\n⚙️ Scalping Configuration:")
    print(f"   ⚡ Timeframe: M1 (1 minute)")
    print(f"   🎯 Take Profit: {trader.tp_points} points ({trader.tp_points/10} pips)")
    print(f"   🛡️ Stop Loss: {trader.sl_points} points ({trader.sl_points/10} pips)")
    print(f"   📊 Max Spread: {trader.max_spread} points")
    print(f"   💼 Max Positions: {trader.max_positions}")
    print(f"   📈 Max Daily Trades: {trader.max_daily_trades}")
    print(f"   ⏰ Max Hold Time: {trader.max_hold_minutes} minutes")
    print(f"   📡 Signal Interval: {trader.signal_interval_seconds} seconds")
    
    # รันเซสชัน
    try:
        duration = int(input(f"\nScalping duration (minutes, default 60): ") or "60")
        
        success = trader.run_scalping_session(duration)
        
        if success:
            print("\n🎉 Scalping session completed successfully!")
        else:
            print("\n❌ Scalping session failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    main()