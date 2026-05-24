#!/usr/bin/env python3
"""
Fixed Gold Scalping Trader - แก้ไขปัญหา Risk/Reward และ Overtrading
แก้ไข: TP < SL, Spread สูง, Overtrading, Position Management
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

class FixedGoldScalpingTrader:
    """Fixed version ของ Gold Scalping Trader"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        # Telegram settings
        self.telegram_token = telegram_token or "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
        self.chat_id = chat_id or "-1002852894581"
        
        # Trading settings
        self.symbol = "GOLDm#"
        self.main_timeframe = mt5.TIMEFRAME_M1
        self.confirm_timeframes = [mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M15]
        self.base_lot_size = 0.2
        
        # FIXED Risk Management - แก้ไขปัญหาหลัก (เพิ่มขึ้นให้ทำกำไรได้มากขึ้น)
        self.tp_points = 200        # Take Profit 20 pips (เพิ่มจาก 15 pips)
        self.sl_points = 120        # Stop Loss 12 pips (เพิ่มจาก 10 pips)
        self.max_spread = 20        # ลด spread tolerance
        self.max_positions = 3      # ลดจำนวน positions
        self.max_daily_trades = 30  # ลดจำนวนเทรดต่อวัน
        
        # FIXED Scalping Strategy Settings
        self.enable_auto_trading = True
        self.scalping_mode = True
        self.quick_exit_enabled = True
        self.breakeven_points = 120      # เลื่อน SL ไป breakeven (12 pips)
        self.partial_close_points = 150  # ปิดครึ่งที่ 15 pips
        self.adaptive_mode = False       # ปิด adaptive เพื่อความสม่ำเสมอ
        
        # FIXED Timing settings
        self.signal_interval_seconds = 60   # เพิ่มช่วงเวลา (ลดความถี่)
        self.max_hold_minutes = 30          # เพิ่มเวลาถือให้เหมาะกับ TP ที่ใหญ่ขึ้น
        self.cooldown_seconds = 120         # เพิ่ม cooldown
        self.avoid_news_minutes = 30
        
        # ENHANCED Market condition filters (เข้มงวดมากขึ้นเพื่อลด SL)
        self.min_volatility = 0.5       # เพิ่มมากขึ้น - ต้องการ movement ชัดเจน
        self.max_volatility = 1.8       # ลดลง - หลีกเลี่ยง noise สูง
        self.confidence_threshold = 0.85 # เพิ่มเป็น 85% - เข้มงวดมาก
        self.min_trend_strength = 0.7   # เพิ่ม - ต้องมี trend ชัดเจน
        self.trend_strength_threshold = 0.6
        
        # AI components
        self.model = None
        self.scaler = StandardScaler()
        
        # Trading data
        self.signals_sent = []
        self.orders_placed = []
        self.daily_trades = 0
        self.daily_profit = 0.0
        self.last_trade_time = None
        
        # Signal balance tracking
        self.daily_buy_signals = 0
        self.daily_sell_signals = 0
        
        # AI Model performance tracking
        self.model_predictions = []
        self.model_accuracy = 0.0
        self.last_model_evaluation = None
        
        self.performance_data = {
            'total_signals': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'avg_profit_per_trade': 0.0,
            'risk_reward_ratio': self.tp_points / self.sl_points,
            'breakeven_rate': self.sl_points / (self.tp_points + self.sl_points),
            'dynamic_tp_used': 0,
            'static_tp_used': 0,
            'avg_tp_points': 0,
            'avg_sl_points': 0,
            'tp_hit_rate': 0.0,
            'sl_hit_rate': 0.0
        }
        
        print("⚡ Fixed Gold Scalping Trader initialized")
        print(f"📊 Risk/Reward Ratio: 1:{self.performance_data['risk_reward_ratio']:.2f}")
        print(f"📈 Breakeven Win Rate: {self.performance_data['breakeven_rate']:.1%}")
    
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
            if df is None or len(df) < 30:
                return None
            
            # Fast RSI (7 periods)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
            rs = gain / loss
            df['rsi_fast'] = 100 - (100 / (1 + rs))
            
            # Standard RSI (14 periods)
            gain_std = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss_std = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs_std = gain_std / loss_std
            df['rsi'] = 100 - (100 / (1 + rs_std))
            
            # Fast MACD (8,21,5)
            exp1_fast = df['close'].ewm(span=8).mean()
            exp2_fast = df['close'].ewm(span=21).mean()
            df['macd_fast'] = exp1_fast - exp2_fast
            df['macd_signal_fast'] = df['macd_fast'].ewm(span=5).mean()
            df['macd_histogram_fast'] = df['macd_fast'] - df['macd_signal_fast']
            
            # Fast Bollinger Bands (15 periods)
            df['bb_middle_fast'] = df['close'].rolling(window=15).mean()
            bb_std_fast = df['close'].rolling(window=15).std()
            df['bb_upper_fast'] = df['bb_middle_fast'] + (bb_std_fast * 2)
            df['bb_lower_fast'] = df['bb_middle_fast'] - (bb_std_fast * 2)
            df['bb_position_fast'] = (df['close'] - df['bb_lower_fast']) / (df['bb_upper_fast'] - df['bb_lower_fast'])
            
            # Fast EMAs
            df['ema_10'] = df['close'].ewm(span=10).mean()
            df['ema_25'] = df['close'].ewm(span=25).mean()
            df['ema_signal'] = np.where(df['ema_10'] > df['ema_25'], 1, 0)
            
            # Price momentum
            df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
            df['momentum_10'] = df['close'] / df['close'].shift(10) - 1
            
            # Volatility (ATR)
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            df['atr'] = df['true_range'].rolling(window=14).mean()
            
            # Volume analysis
            df['volume_sma'] = df['tick_volume'].rolling(window=15).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
            
            # Price action patterns
            df['candle_body'] = abs(df['close'] - df['open'])
            df['candle_type'] = np.where(df['close'] > df['open'], 1, -1)
            
            # ZigZag calculation for peak/trough detection
            df = self.calculate_zigzag(df)
            
            # Bollinger Bands touch detection
            df['bb_upper_touch'] = (df['high'] >= df['bb_upper_fast'] * 0.999).astype(int)
            df['bb_lower_touch'] = (df['low'] <= df['bb_lower_fast'] * 1.001).astype(int)
            
            # BB + ZigZag reversal signals
            df['bb_zigzag_sell_signal'] = 0
            df['bb_zigzag_buy_signal'] = 0
            
            for i in range(2, len(df)):
                # SELL Signal: BB Upper touch + ZigZag peak
                if (df['bb_upper_touch'].iloc[i] == 1 and 
                    df['zigzag_peak'].iloc[i] == 1):
                    df.loc[df.index[i], 'bb_zigzag_sell_signal'] = 1
                
                # BUY Signal: BB Lower touch + ZigZag trough  
                if (df['bb_lower_touch'].iloc[i] == 1 and 
                    df['zigzag_trough'].iloc[i] == 1):
                    df.loc[df.index[i], 'bb_zigzag_buy_signal'] = 1
            
            return df
            
        except Exception as e:
            print(f"❌ Scalping indicator calculation error: {e}")
            return None
    
    def calculate_zigzag(self, df, deviation_percent=0.5):
        """คำนวณ ZigZag indicator สำหรับหา peaks และ troughs"""
        try:
            if df is None or len(df) < 10:
                return df
            
            # Initialize ZigZag columns
            df['zigzag_peak'] = 0
            df['zigzag_trough'] = 0
            df['zigzag_level'] = np.nan
            
            # Convert deviation to actual price difference
            avg_price = df['close'].mean()
            min_deviation = avg_price * (deviation_percent / 100)
            
            # Find local peaks and troughs
            highs = df['high'].values
            lows = df['low'].values
            
            # Track current trend and last significant point
            last_peak_idx = 0
            last_trough_idx = 0
            last_peak_price = highs[0]
            last_trough_price = lows[0]
            
            for i in range(1, len(df)):
                current_high = highs[i]
                current_low = lows[i]
                
                # Check for new peak
                if current_high > last_peak_price + min_deviation:
                    # Mark previous peak if significant
                    if i - last_peak_idx > 3:  # At least 3 bars apart
                        df.loc[df.index[last_peak_idx], 'zigzag_peak'] = 1
                        df.loc[df.index[last_peak_idx], 'zigzag_level'] = last_peak_price
                    
                    last_peak_idx = i
                    last_peak_price = current_high
                
                # Check for new trough
                if current_low < last_trough_price - min_deviation:
                    # Mark previous trough if significant
                    if i - last_trough_idx > 3:  # At least 3 bars apart
                        df.loc[df.index[last_trough_idx], 'zigzag_trough'] = 1
                        df.loc[df.index[last_trough_idx], 'zigzag_level'] = last_trough_price
                    
                    last_trough_idx = i
                    last_trough_price = current_low
                
                # Update last significant prices
                if current_high > last_peak_price:
                    last_peak_price = current_high
                    last_peak_idx = i
                
                if current_low < last_trough_price:
                    last_trough_price = current_low
                    last_trough_idx = i
            
            # Mark the most recent peak/trough
            if last_peak_idx > 0:
                df.loc[df.index[last_peak_idx], 'zigzag_peak'] = 1
                df.loc[df.index[last_peak_idx], 'zigzag_level'] = last_peak_price
            
            if last_trough_idx > 0:
                df.loc[df.index[last_trough_idx], 'zigzag_trough'] = 1
                df.loc[df.index[last_trough_idx], 'zigzag_level'] = last_trough_price
            
            return df
            
        except Exception as e:
            print(f"❌ ZigZag calculation error: {e}")
            return df
    
    def analyze_bb_zigzag_signals(self, df):
        """วิเคราะห์สัญญาณ Bollinger Bands + ZigZag"""
        try:
            if df is None or len(df) < 10:
                return {}
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            signals = {
                'bb_upper_touch': False,
                'bb_lower_touch': False,
                'zigzag_peak': False,
                'zigzag_trough': False,
                'bb_zigzag_sell': False,
                'bb_zigzag_buy': False,
                'bb_position': latest['bb_position_fast'],
                'trend_after_touch': 'NEUTRAL'
            }
            
            # ตรวจสอบ BB touches
            if latest['bb_upper_touch'] == 1:
                signals['bb_upper_touch'] = True
                print("🔴 Bollinger Upper Band touched!")
            
            if latest['bb_lower_touch'] == 1:
                signals['bb_lower_touch'] = True
                print("🟢 Bollinger Lower Band touched!")
            
            # ตรวจสอบ ZigZag peaks/troughs
            if latest['zigzag_peak'] == 1:
                signals['zigzag_peak'] = True
                print(f"📈 ZigZag Peak detected at ${latest['zigzag_level']:.2f}")
            
            if latest['zigzag_trough'] == 1:
                signals['zigzag_trough'] = True
                print(f"📉 ZigZag Trough detected at ${latest['zigzag_level']:.2f}")
            
            # ตรวจสอบ combined signals
            if latest['bb_zigzag_sell_signal'] == 1:
                signals['bb_zigzag_sell'] = True
                print("🔴 BB + ZigZag SELL Signal!")
            
            if latest['bb_zigzag_buy_signal'] == 1:
                signals['bb_zigzag_buy'] = True
                print("🟢 BB + ZigZag BUY Signal!")
            
            # วิเคราะห์ trend หลัง touch BB
            if signals['bb_upper_touch'] or signals['bb_lower_touch']:
                # ดูว่าหลังจาก touch BB แล้ว price เคลื่อนไหวไปทางไหน
                price_movement = latest['close'] - prev['close']
                
                if signals['bb_upper_touch']:
                    if price_movement < 0:
                        signals['trend_after_touch'] = 'REVERSAL_DOWN'
                        print("📉 Price reversing down after BB upper touch")
                    else:
                        signals['trend_after_touch'] = 'BREAKOUT_UP'
                        print("📈 Price breaking out above BB upper")
                
                if signals['bb_lower_touch']:
                    if price_movement > 0:
                        signals['trend_after_touch'] = 'REVERSAL_UP'
                        print("📈 Price reversing up after BB lower touch")
                    else:
                        signals['trend_after_touch'] = 'BREAKOUT_DOWN'
                        print("📉 Price breaking down below BB lower")
            
            return signals
            
        except Exception as e:
            print(f"❌ BB ZigZag analysis error: {e}")
            return {}
    
    def combine_ai_bb_zigzag_signals(self, ai_signal, ai_confidence, bb_zigzag_signals):
        """รวมสัญญาณ AI + Bollinger Bands + ZigZag"""
        try:
            print(f"🧠 Combining AI + BB + ZigZag signals...")
            print(f"   🤖 AI Signal: {ai_signal} (Confidence: {ai_confidence:.1%})")
            
            # ตรวจสอบ BB + ZigZag signals
            bb_sell_signal = bb_zigzag_signals.get('bb_zigzag_sell', False)
            bb_buy_signal = bb_zigzag_signals.get('bb_zigzag_buy', False)
            bb_upper_touch = bb_zigzag_signals.get('bb_upper_touch', False)
            bb_lower_touch = bb_zigzag_signals.get('bb_lower_touch', False)
            zigzag_peak = bb_zigzag_signals.get('zigzag_peak', False)
            zigzag_trough = bb_zigzag_signals.get('zigzag_trough', False)
            trend_after_touch = bb_zigzag_signals.get('trend_after_touch', 'NEUTRAL')
            
            # Strategy: BB + ZigZag Reversal
            final_signal = None
            final_confidence = ai_confidence
            entry_reason = []
            
            # SELL Conditions: BB Upper + ZigZag Peak + Reversal
            if (bb_upper_touch or zigzag_peak) and trend_after_touch == 'REVERSAL_DOWN':
                final_signal = "SELL"
                final_confidence *= 1.3  # เพิ่ม confidence
                entry_reason.append("BB Upper + ZigZag Peak + Reversal Down")
                
                # ถ้า AI เห็นด้วย ให้ confidence เพิ่ม
                if ai_signal == "SELL":
                    final_confidence *= 1.2
                    entry_reason.append("AI Confirms SELL")
                else:
                    final_confidence *= 0.9
                    entry_reason.append("AI Disagrees")
            
            # BUY Conditions: BB Lower + ZigZag Trough + Reversal  
            elif (bb_lower_touch or zigzag_trough) and trend_after_touch == 'REVERSAL_UP':
                final_signal = "BUY"
                final_confidence *= 1.3  # เพิ่ม confidence
                entry_reason.append("BB Lower + ZigZag Trough + Reversal Up")
                
                # ถ้า AI เห็นด้วย ให้ confidence เพิ่ม
                if ai_signal == "BUY":
                    final_confidence *= 1.2
                    entry_reason.append("AI Confirms BUY")
                else:
                    final_confidence *= 0.9
                    entry_reason.append("AI Disagrees")
            
            # Pure BB + ZigZag signals (ไม่ต้องรอ reversal)
            elif bb_sell_signal:
                final_signal = "SELL"
                final_confidence *= 1.1
                entry_reason.append("BB + ZigZag SELL Signal")
                
                if ai_signal == "SELL":
                    final_confidence *= 1.1
                    entry_reason.append("AI Confirms")
            
            elif bb_buy_signal:
                final_signal = "BUY"
                final_confidence *= 1.1
                entry_reason.append("BB + ZigZag BUY Signal")
                
                if ai_signal == "BUY":
                    final_confidence *= 1.1
                    entry_reason.append("AI Confirms")
            
            # ถ้าไม่มี BB + ZigZag signal ใช้ AI อย่างเดียว (แต่ confidence ต้องสูงมาก)
            elif ai_confidence > 0.9:
                final_signal = ai_signal
                final_confidence = ai_confidence
                entry_reason.append(f"High Confidence AI Signal ({ai_confidence:.1%})")
            
            # ตรวจสอบ final confidence
            final_confidence = min(final_confidence, 1.0)
            
            if final_signal is None:
                print(f"   ❌ No qualifying signals found")
                return None
            
            if final_confidence < self.confidence_threshold:
                print(f"   ❌ Final confidence too low: {final_confidence:.1%} < {self.confidence_threshold:.1%}")
                return None
            
            print(f"   ✅ Final Signal: {final_signal} (Confidence: {final_confidence:.1%})")
            print(f"   📋 Entry Reasons: {', '.join(entry_reason)}")
            
            return {
                'signal': final_signal,
                'confidence': final_confidence,
                'entry_reasons': entry_reason,
                'bb_zigzag_data': bb_zigzag_signals
            }
            
        except Exception as e:
            print(f"❌ Signal combination error: {e}")
            return None
    
    def check_market_conditions(self):
        """ตรวจสอบสภาพตลาดสำหรับ scalping (รันได้ตลอด 24/7)"""
        try:
            # ดึงข้อมูล M1 ล่าสุด
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 50)
            if df_m1 is None:
                return False, "No M1 data"
            
            df_m1 = self.calculate_scalping_indicators(df_m1)
            if df_m1 is None:
                return False, "Cannot calculate indicators"
            
            latest = df_m1.iloc[-1]
            
            # ตรวจสอบ spread (เข้มงวดขึ้น)
            tick = mt5.symbol_info_tick(self.symbol)
            symbol_info = mt5.symbol_info(self.symbol)
            
            spread_points = 0
            if tick and symbol_info:
                spread_points = (tick.ask - tick.bid) / symbol_info.point
                if spread_points > self.max_spread:
                    return False, f"Spread too high: {spread_points:.1f} points (max: {self.max_spread})"
            
            # ตรวจสอบ volatility (เข้มงวดขึ้น)
            current_atr = latest['atr']
            if current_atr < self.min_volatility:
                return False, f"Volatility too low: {current_atr:.3f} (min: {self.min_volatility})"
            elif current_atr > self.max_volatility:
                return False, f"Volatility too high: {current_atr:.3f} (max: {self.max_volatility})"
            
            # ตรวจสอบ cooldown (เพิ่มขึ้น)
            if self.last_trade_time:
                current_time = datetime.now()
                time_since_last = (current_time - self.last_trade_time).total_seconds()
                if time_since_last < self.cooldown_seconds:
                    return False, f"Cooldown: {self.cooldown_seconds-time_since_last:.0f}s remaining"
            
            # ตรวจสอบจำนวนเทรดต่อวัน (รีเซ็ตทุกวัน)
            current_time = datetime.now()
            if hasattr(self, 'last_reset_date'):
                if self.last_reset_date != current_time.date():
                    self.daily_trades = 0
                    self.daily_profit = 0.0
                    self.last_reset_date = current_time.date()
                    print(f"🔄 Daily stats reset for {current_time.date()}")
            else:
                self.last_reset_date = current_time.date()
            
            if self.daily_trades >= self.max_daily_trades:
                return False, f"Daily trade limit reached: {self.daily_trades}/{self.max_daily_trades}"
            
            # ตรวจสอบ RSI ไม่ extreme และมี momentum ชัดเจน
            if latest['rsi_fast'] < 20 or latest['rsi_fast'] > 80:
                return False, f"RSI too extreme: {latest['rsi_fast']:.1f}"
            
            # ตรวจสอบ MACD momentum
            if abs(latest['macd_histogram_fast']) < 0.1:
                return False, f"MACD momentum too weak: {latest['macd_histogram_fast']:.3f}"
            
            # ตรวจสอบ volume
            if latest['volume_ratio'] < 1.2:
                return False, f"Volume too low: {latest['volume_ratio']:.2f}"
            
            # ตรวจสอบ candle body (ต้องมี movement ชัดเจน)
            if latest['candle_body'] < latest['atr'] * 0.3:
                return False, f"Candle body too small: {latest['candle_body']:.2f}"
            
            # แสดงข้อมูลสภาพตลาด
            market_info = f"ATR: {current_atr:.3f}, Spread: {spread_points:.1f}pts, RSI: {latest['rsi_fast']:.1f}"
            return True, f"Market OK - {market_info}"
            
        except Exception as e:
            print(f"❌ Market condition check error: {e}")
            return False, str(e)
    
    def train_scalping_model(self):
        """เทรนโมเดลสำหรับ scalping (ปรับปรุง)"""
        print("⚡ Training Fixed Scalping AI model...")
        
        # ดึงข้อมูล M1 จำนวนมาก (เพิ่มขึ้นเพื่อให้ได้ข้อมูลมากขึ้น)
        df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 2000)
        if df_m1 is None:
            print("❌ Cannot get M1 data - trying M5 data instead")
            # Fallback: ใช้ M5 data แทน
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M5, 1000)
            if df_m1 is None:
                return False
            print("✅ Using M5 data as fallback")
        
        df_m1 = self.calculate_scalping_indicators(df_m1)
        if df_m1 is None:
            return False
        
        # สร้าง labels ที่เหมาะกับ TP/SL ใหม่
        future_bars = 10  # ดู 10 นาทีข้างหน้า
        df_m1['future_high'] = df_m1['high'].shift(-future_bars).rolling(window=future_bars).max()
        df_m1['future_low'] = df_m1['low'].shift(-future_bars).rolling(window=future_bars).min()
        
        # คำนวณผลตอบแทนที่เป็นไปได้
        df_m1['potential_buy_profit'] = (df_m1['future_high'] - df_m1['close']) / df_m1['close']
        df_m1['potential_sell_profit'] = (df_m1['close'] - df_m1['future_low']) / df_m1['close']
        
        # กำหนด threshold ที่ผ่อนปรนกว่าเพื่อให้ได้ข้อมูลมากขึ้น
        profit_threshold = 0.0005   # 10 pips (ลดจาก 15 pips)
        loss_threshold = 0.0008     # 16 pips loss (เพิ่มขึ้นเพื่อหลีกเลี่ยง noise)
        
        # สร้าง labels แบบผ่อนปรนเพื่อให้ได้ข้อมูลมากขึ้น
        conditions = [
            # BUY conditions - ผ่อนปรนกว่า
            (df_m1['potential_buy_profit'] > profit_threshold) & 
            (df_m1['potential_buy_profit'] > df_m1['potential_sell_profit'] * 1.1) &  # BUY ต้องดีกว่า SELL 10% (ลดจาก 20%)
            ((df_m1['close'] - df_m1['future_low']) / df_m1['close'] < loss_threshold),
            
            # SELL conditions - ผ่อนปรนกว่า
            (df_m1['potential_sell_profit'] > profit_threshold) & 
            (df_m1['potential_sell_profit'] > df_m1['potential_buy_profit'] * 1.1) &  # SELL ต้องดีกว่า BUY 10% (ลดจาก 20%)
            ((df_m1['future_high'] - df_m1['close']) / df_m1['close'] < loss_threshold)
        ]
        choices = [1, 0]
        df_m1['label'] = np.select(conditions, choices, default=-1)
        
        # เลือกเฉพาะ samples ที่มี signal ชัดเจน
        df_clean = df_m1[df_m1['label'] != -1].copy()
        
        # ตรวจสอบสมดุลของข้อมูล
        buy_samples = len(df_clean[df_clean['label'] == 1])
        sell_samples = len(df_clean[df_clean['label'] == 0])
        total_samples = len(df_clean)
        
        print(f"📊 Training data balance:")
        print(f"   🟢 BUY samples: {buy_samples} ({buy_samples/total_samples*100:.1f}%)")
        print(f"   🔴 SELL samples: {sell_samples} ({sell_samples/total_samples*100:.1f}%)")
        
        # ถ้าข้อมูลไม่สมดุลมาก ให้ balance
        if abs(buy_samples - sell_samples) > total_samples * 0.3:  # ห่างกันเกิน 30%
            print("⚖️ Balancing training data...")
            min_samples = min(buy_samples, sell_samples)
            
            df_buy = df_clean[df_clean['label'] == 1].sample(n=min_samples, random_state=42)
            df_sell = df_clean[df_clean['label'] == 0].sample(n=min_samples, random_state=42)
            
            df_clean = pd.concat([df_buy, df_sell]).sample(frac=1, random_state=42).reset_index(drop=True)
            
            print(f"✅ Balanced to {len(df_clean)} samples ({min_samples} each)")
        
        # เลือก features ที่ดีที่สุด
        scalping_features = [
            'rsi_fast', 'rsi', 'macd_fast', 'macd_histogram_fast',
            'bb_position_fast', 'ema_signal', 'momentum_5', 'momentum_10',
            'atr', 'volume_ratio', 'candle_body', 'candle_type'
        ]
        
        # ลบ NaN
        df_final = df_clean[scalping_features + ['label']].dropna()
        
        if len(df_final) < 50:
            print("❌ Not enough quality training data")
            return False
        elif len(df_final) < 200:
            print(f"⚠️ Limited training data: {len(df_final)} samples (recommended: 200+)")
            print("🔄 Proceeding with available data...")
        
        X = df_final[scalping_features].values
        y = df_final['label'].values
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model ที่เหมาะกับ scalping
        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=3,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_scaled, y)
        accuracy = self.model.score(X_scaled, y)
        
        # เก็บ model performance
        self.model_accuracy = accuracy
        self.last_model_evaluation = datetime.now()
        
        print(f"✅ Enhanced Scalping model trained!")
        print(f"📊 Training accuracy: {accuracy:.2%}")
        print(f"📈 Training samples: {len(X)}")
        print(f"⚡ Quality samples: {len(df_final)}")
        print(f"🎯 Model ready for high-confidence predictions")
        
        # ส่งแจ้งเตือนไป Telegram
        model_message = f"""
🤖 <b>AI MODEL TRAINED</b> 🤖

📊 <b>Training Accuracy:</b> {accuracy:.2%}
📈 <b>Training Samples:</b> {len(X):,}
⚡ <b>Quality Samples:</b> {len(df_final):,}
🎯 <b>Confidence Threshold:</b> {self.confidence_threshold:.1%}

<i>🧠 Enhanced Scalping AI ready!</i>
        """.strip()
        
        self.send_telegram_message(model_message)
        
        return True
    
    def make_scalping_prediction(self):
        """ทำนายสัญญาณ scalping (ปรับปรุง)"""
        if self.model is None:
            print("🔧 Using Technical Analysis mode (AI not available)")
            return self.make_technical_prediction()
        
        try:
            # ดึงข้อมูล M1 ล่าสุด
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 50)
            if df_m1 is None:
                return None
            
            df_m1 = self.calculate_scalping_indicators(df_m1)
            if df_m1 is None:
                return None
            
            # ดึงข้อมูล M5 และ M15 เพื่อยืนยันทิศทางแบบสมดุล
            df_m5 = self.get_gold_data(mt5.TIMEFRAME_M5, 30)
            df_m15 = self.get_gold_data(mt5.TIMEFRAME_M15, 20)
            
            trend_direction = 0
            trend_signals = []
            
            # วิเคราะห์ M5
            if df_m5 is not None and len(df_m5) > 20:
                df_m5 = self.calculate_scalping_indicators(df_m5)
                if df_m5 is not None:
                    m5_latest = df_m5.iloc[-1]
                    m5_prev = df_m5.iloc[-2]
                    
                    # EMA Trend
                    if m5_latest['ema_signal'] == 1:
                        trend_signals.append(1)
                    elif m5_latest['ema_signal'] == 0:
                        trend_signals.append(-1)
                    
                    # Price momentum
                    if m5_latest['close'] > m5_prev['close']:
                        trend_signals.append(1)
                    else:
                        trend_signals.append(-1)
                    
                    # RSI trend
                    if 40 < m5_latest['rsi'] < 60:  # Neutral zone - follow momentum
                        if m5_latest['rsi'] > m5_prev['rsi']:
                            trend_signals.append(1)
                        else:
                            trend_signals.append(-1)
                    elif m5_latest['rsi'] < 35:  # Oversold - bullish
                        trend_signals.append(1)
                    elif m5_latest['rsi'] > 65:  # Overbought - bearish
                        trend_signals.append(-1)
            
            # วิเคราะห์ M15
            if df_m15 is not None and len(df_m15) > 15:
                df_m15 = self.calculate_scalping_indicators(df_m15)
                if df_m15 is not None:
                    m15_latest = df_m15.iloc[-1]
                    
                    # M15 trend (weight มากกว่า)
                    if m15_latest['ema_signal'] == 1:
                        trend_signals.extend([1, 1])  # Double weight
                    elif m15_latest['ema_signal'] == 0:
                        trend_signals.extend([-1, -1])  # Double weight
            
            # คำนวณ trend direction แบบสมดุล
            if trend_signals:
                trend_sum = sum(trend_signals)
                if trend_sum > 1:
                    trend_direction = 1
                elif trend_sum < -1:
                    trend_direction = -1
                else:
                    trend_direction = 0
            
            # วิเคราะห์ BB + ZigZag signals
            bb_zigzag_signals = self.analyze_bb_zigzag_signals(df_m1)
            
            # เลือก features ล่าสุดจาก M1 (เพิ่ม BB + ZigZag features)
            scalping_features = [
                'rsi_fast', 'rsi', 'macd_fast', 'macd_histogram_fast',
                'bb_position_fast', 'ema_signal', 'momentum_5', 'momentum_10',
                'atr', 'volume_ratio', 'candle_body', 'candle_type',
                'bb_upper_touch', 'bb_lower_touch', 'zigzag_peak', 'zigzag_trough'
            ]
            
            latest_data = df_m1[scalping_features].iloc[-1:].values
            
            if np.isnan(latest_data).any():
                return None
            
            # Normalize และทำนาย
            features_scaled = self.scaler.transform(latest_data)
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            confidence = max(probability)
            
            # แปลงเป็นสัญญาณ (AI prediction)
            ai_signal = "BUY" if prediction == 1 else "SELL"
            
            # รวม AI + BB ZigZag signals
            final_signal = self.combine_ai_bb_zigzag_signals(ai_signal, confidence, bb_zigzag_signals)
            
            if final_signal is None:
                return None
            
            signal = final_signal['signal']
            confidence = final_signal['confidence']
            
            # ENHANCED Technical Analysis - เข้มงวดมากขึ้น
            latest_candle = df_m1.iloc[-1]
            prev_candle = df_m1.iloc[-2]
            
            # วิเคราะห์ RSI แบบเข้มงวด
            rsi_signal = 0
            rsi_momentum = latest_candle['rsi_fast'] - prev_candle['rsi_fast']
            
            if latest_candle['rsi_fast'] < 25 and rsi_momentum > 0:
                rsi_signal = 2  # Strong oversold with momentum - Strong BUY
            elif latest_candle['rsi_fast'] < 35 and rsi_momentum > 1:
                rsi_signal = 1  # Oversold with momentum - BUY
            elif latest_candle['rsi_fast'] > 75 and rsi_momentum < 0:
                rsi_signal = -2  # Strong overbought with momentum - Strong SELL
            elif latest_candle['rsi_fast'] > 65 and rsi_momentum < -1:
                rsi_signal = -1  # Overbought with momentum - SELL
            
            # วิเคราะห์ MACD แบบเข้มงวด
            macd_signal = 0
            macd_momentum = latest_candle['macd_histogram_fast'] - prev_candle['macd_histogram_fast']
            
            if (latest_candle['macd_fast'] > latest_candle['macd_signal_fast'] and 
                latest_candle['macd_histogram_fast'] > 0 and macd_momentum > 0):
                macd_signal = 2  # Strong bullish momentum
            elif latest_candle['macd_histogram_fast'] > 0:
                macd_signal = 1  # Bullish
            elif (latest_candle['macd_fast'] < latest_candle['macd_signal_fast'] and 
                  latest_candle['macd_histogram_fast'] < 0 and macd_momentum < 0):
                macd_signal = -2  # Strong bearish momentum
            elif latest_candle['macd_histogram_fast'] < 0:
                macd_signal = -1  # Bearish
            
            # วิเคราะห์ Bollinger Bands แบบเข้มงวด
            bb_signal = 0
            bb_squeeze = (latest_candle['bb_upper_fast'] - latest_candle['bb_lower_fast']) / latest_candle['bb_middle_fast']
            
            if latest_candle['bb_position_fast'] < 0.1 and bb_squeeze > 0.02:
                bb_signal = 2  # Strong oversold with volatility
            elif latest_candle['bb_position_fast'] < 0.2:
                bb_signal = 1  # Near lower band
            elif latest_candle['bb_position_fast'] > 0.9 and bb_squeeze > 0.02:
                bb_signal = -2  # Strong overbought with volatility
            elif latest_candle['bb_position_fast'] > 0.8:
                bb_signal = -1  # Near upper band
            
            # วิเคราะห์ Price Action
            price_action_signal = 0
            price_change = (latest_candle['close'] - prev_candle['close']) / prev_candle['close']
            
            if price_change > 0.001 and latest_candle['candle_type'] == 1:  # Strong bullish candle
                price_action_signal = 1
            elif price_change < -0.001 and latest_candle['candle_type'] == -1:  # Strong bearish candle
                price_action_signal = -1
            
            # รวมสัญญาณทั้งหมดแบบ weighted
            technical_signals = [
                rsi_signal * 0.3,      # RSI weight 30%
                macd_signal * 0.3,     # MACD weight 30%
                bb_signal * 0.2,       # BB weight 20%
                trend_direction * 0.15, # Trend weight 15%
                price_action_signal * 0.05  # Price action weight 5%
            ]
            technical_score = sum(technical_signals)
            
            # เข้มงวดมาก - ต้องมี technical score สูง
            min_technical_score = 1.5 if signal == "BUY" else -1.5
            
            if signal == "BUY" and technical_score < min_technical_score:
                print(f"❌ BUY signal rejected: Technical score {technical_score:.2f} < {min_technical_score}")
                return None
            elif signal == "SELL" and technical_score > -min_technical_score:
                print(f"❌ SELL signal rejected: Technical score {technical_score:.2f} > {-min_technical_score}")
                return None
            
            # ปรับ confidence แบบเข้มงวด
            original_confidence = confidence
            
            if abs(technical_score) > 2.0:
                confidence *= 1.2  # Very strong technical support
            elif abs(technical_score) > 1.5:
                confidence *= 1.1  # Strong technical support
            elif abs(technical_score) < 1.0:
                confidence *= 0.8  # Weak technical support
            
            # แสดงการวิเคราะห์แบบละเอียด
            print(f"🔍 Enhanced Technical Analysis:")
            print(f"   RSI: {rsi_signal:+.1f} (RSI: {latest_candle['rsi_fast']:.1f}, Momentum: {rsi_momentum:+.1f})")
            print(f"   MACD: {macd_signal:+.1f} (Hist: {latest_candle['macd_histogram_fast']:.3f})")
            print(f"   BB: {bb_signal:+.1f} (Pos: {latest_candle['bb_position_fast']:.2f})")
            print(f"   Trend: {trend_direction:+d}, Price Action: {price_action_signal:+d}")
            print(f"   📊 Technical Score: {technical_score:.2f} (Min: {min_technical_score})")
            print(f"   📊 Signal: {signal}, Conf: {original_confidence:.1%} → {confidence:.1%}")
            
            confidence = min(confidence, 1.0)
            
            # ตรวจสอบ confidence threshold
            if confidence < self.confidence_threshold:
                return None
            
            # ดูราคาปัจจุบัน
            tick = mt5.symbol_info_tick(self.symbol)
            current_price = tick.bid if tick else 0
            
            # ข้อมูลเพิ่มเติมสำหรับ result (latest_candle ถูกใช้แล้วข้างบน)
            
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
    
    def make_technical_prediction(self):
        """ทำนายด้วย Technical Analysis เมื่อ AI ไม่พร้อม"""
        try:
            print("🔧 Making Technical Analysis prediction...")
            
            # ดึงข้อมูล M1 ล่าสุด
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 50)
            if df_m1 is None:
                return None
            
            df_m1 = self.calculate_scalping_indicators(df_m1)
            if df_m1 is None:
                return None
            
            latest = df_m1.iloc[-1]
            prev = df_m1.iloc[-2]
            
            # วิเคราะห์ BB + ZigZag signals ก่อน
            bb_zigzag_signals = self.analyze_bb_zigzag_signals(df_m1)
            
            # Technical Analysis Score
            technical_score = 0
            reasons = []
            
            # เพิ่มคะแนนจาก BB + ZigZag (weight สูงสุด)
            if bb_zigzag_signals.get('bb_zigzag_sell', False):
                technical_score -= 4  # Strong SELL signal
                reasons.append("BB + ZigZag SELL")
            elif bb_zigzag_signals.get('bb_zigzag_buy', False):
                technical_score += 4  # Strong BUY signal
                reasons.append("BB + ZigZag BUY")
            elif bb_zigzag_signals.get('bb_upper_touch', False) and bb_zigzag_signals.get('trend_after_touch') == 'REVERSAL_DOWN':
                technical_score -= 3  # Strong reversal SELL
                reasons.append("BB Upper + Reversal Down")
            elif bb_zigzag_signals.get('bb_lower_touch', False) and bb_zigzag_signals.get('trend_after_touch') == 'REVERSAL_UP':
                technical_score += 3  # Strong reversal BUY
                reasons.append("BB Lower + Reversal Up")
            
            # 1. RSI Analysis
            if latest['rsi_fast'] < 30:
                technical_score += 2
                reasons.append("RSI Oversold")
            elif latest['rsi_fast'] > 70:
                technical_score -= 2
                reasons.append("RSI Overbought")
            elif 40 < latest['rsi_fast'] < 60:
                rsi_momentum = latest['rsi_fast'] - prev['rsi_fast']
                if rsi_momentum > 1:
                    technical_score += 1
                    reasons.append("RSI Bullish Momentum")
                elif rsi_momentum < -1:
                    technical_score -= 1
                    reasons.append("RSI Bearish Momentum")
            
            # 2. MACD Analysis
            if latest['macd_fast'] > latest['macd_signal_fast'] and latest['macd_histogram_fast'] > 0:
                if latest['macd_histogram_fast'] > prev['macd_histogram_fast']:
                    technical_score += 2
                    reasons.append("MACD Strong Bullish")
                else:
                    technical_score += 1
                    reasons.append("MACD Bullish")
            elif latest['macd_fast'] < latest['macd_signal_fast'] and latest['macd_histogram_fast'] < 0:
                if latest['macd_histogram_fast'] < prev['macd_histogram_fast']:
                    technical_score -= 2
                    reasons.append("MACD Strong Bearish")
                else:
                    technical_score -= 1
                    reasons.append("MACD Bearish")
            
            # 3. EMA Analysis
            if latest['ema_signal'] == 1:
                technical_score += 1
                reasons.append("EMA Bullish")
            else:
                technical_score -= 1
                reasons.append("EMA Bearish")
            
            # 4. Bollinger Bands
            if latest['bb_position_fast'] < 0.2:
                technical_score += 1
                reasons.append("BB Oversold")
            elif latest['bb_position_fast'] > 0.8:
                technical_score -= 1
                reasons.append("BB Overbought")
            
            # 5. Volume Confirmation
            if latest['volume_ratio'] > 1.5:
                if technical_score > 0:
                    technical_score += 1
                    reasons.append("High Volume Confirms Bullish")
                elif technical_score < 0:
                    technical_score -= 1
                    reasons.append("High Volume Confirms Bearish")
            
            # กำหนดสัญญาณ
            if technical_score >= 3:
                signal = "BUY"
                confidence = min(0.9, 0.6 + (technical_score - 3) * 0.1)
            elif technical_score <= -3:
                signal = "SELL"
                confidence = min(0.9, 0.6 + (abs(technical_score) - 3) * 0.1)
            else:
                print(f"🔧 Technical score too weak: {technical_score} (need ±3)")
                return None
            
            # ดูราคาปัจจุบัน
            tick = mt5.symbol_info_tick(self.symbol)
            current_price = tick.bid if tick else 0
            
            result = {
                'symbol': self.symbol,
                'signal': signal,
                'confidence': confidence,
                'current_price': current_price,
                'trend_direction': 1 if technical_score > 0 else -1,
                'atr': latest['atr'],
                'rsi_fast': latest['rsi_fast'],
                'macd_fast': latest['macd_fast'],
                'bb_position_fast': latest['bb_position_fast'],
                'volume_ratio': latest['volume_ratio'],
                'timestamp': datetime.now(),
                'technical_score': technical_score,
                'reasons': reasons,
                'mode': 'Technical Analysis'
            }
            
            print(f"🔧 Technical Analysis: Score={technical_score}, Signal={signal}, Conf={confidence:.1%}")
            print(f"🔧 Reasons: {', '.join(reasons)}")
            
            return result
            
        except Exception as e:
            print(f"❌ Technical prediction error: {e}")
            return None
    
    def calculate_dynamic_tp_sl(self, signal, entry_price, confidence=0.7):
        """คำนวณ TP/SL แบบ dynamic สำหรับ scalping"""
        try:
            # ดึงข้อมูลล่าสุดเพื่อคำนวณ ATR และ volatility
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 50)
            if df_m1 is None:
                return self.calculate_static_tp_sl(signal, entry_price)
            
            df_m1 = self.calculate_scalping_indicators(df_m1)
            if df_m1 is None:
                return self.calculate_static_tp_sl(signal, entry_price)
            
            latest = df_m1.iloc[-1]
            symbol_info = mt5.symbol_info(self.symbol)
            point = symbol_info.point
            
            # คำนวณ ATR ในหน่วย points
            atr_points = latest['atr'] / point
            
            # คำนวณ volatility factor
            volatility_factor = min(max(atr_points / 100, 0.5), 3.0)  # จำกัดระหว่าง 0.5-3.0
            
            # คำนวณ confidence factor
            confidence_factor = min(max(confidence, 0.5), 1.0)
            
            # Enhanced Base TP/SL (ปรับตาม market analysis)
            base_tp = 180   # 18 pips - เพิ่มขึ้นเพื่อหลีกเลี่ยง noise
            base_sl = 90    # 9 pips - ลดลงเล็กน้อยแต่เพิ่ม quality
            
            # ปรับตาม volatility
            dynamic_tp = base_tp * volatility_factor
            dynamic_sl = base_sl * volatility_factor
            
            # ปรับตาม confidence แบบเข้มงวด (confidence สูง = TP สูงมาก, SL ต่ำ)
            if confidence > 0.9:
                dynamic_tp *= 1.5  # เพิ่ม TP มาก
                dynamic_sl *= 0.8  # ลด SL มาก
            elif confidence > 0.85:
                dynamic_tp *= 1.3  # เพิ่ม TP
                dynamic_sl *= 0.85  # ลด SL
            elif confidence > 0.8:
                dynamic_tp *= 1.1
                dynamic_sl *= 0.9
            else:
                # ถ้า confidence ไม่ถึง 80% ไม่ควรเทรด (แต่ถ้าผ่านมาถึงจุดนี้แล้ว)
                dynamic_tp *= 0.9
                dynamic_sl *= 1.0
            
            # ปรับตาม RSI (oversold/overbought = TP สูงขึ้น)
            rsi = latest['rsi_fast']
            if rsi < 30 or rsi > 70:  # Extreme levels
                dynamic_tp *= 1.2
            elif rsi < 40 or rsi > 60:  # Strong levels
                dynamic_tp *= 1.1
            
            # ปรับตาม MACD momentum
            if abs(latest['macd_histogram_fast']) > 0.5:  # Strong momentum
                dynamic_tp *= 1.15
                dynamic_sl *= 0.95
            
            # จำกัดค่าสูงสุด/ต่ำสุด แบบ smart (ปรับตาม ATR)
            min_tp = max(150, int(atr_points * 1.5))  # TP ขั้นต่ำ 15 pips หรือ 1.5x ATR
            max_tp = min(600, int(atr_points * 5.0))  # TP สูงสุด 60 pips หรือ 5x ATR
            min_sl = max(60, int(atr_points * 0.8))   # SL ขั้นต่ำ 6 pips หรือ 0.8x ATR  
            max_sl = min(200, int(atr_points * 2.0))  # SL สูงสุด 20 pips หรือ 2x ATR
            
            final_tp = max(min_tp, min(max_tp, int(dynamic_tp)))
            final_sl = max(min_sl, min(max_sl, int(dynamic_sl)))
            
            # ตรวจสอบ Risk/Reward ratio แบบเข้มงวด (ต้องมากกว่า 1:1.8)
            risk_reward = final_tp / final_sl
            if risk_reward < 1.8:
                final_tp = int(final_sl * 2.0)  # ปรับให้ R/R = 2.0 (เข้มงวดมาก)
                # ตรวจสอบว่า TP ไม่เกิน max
                if final_tp > max_tp:
                    final_sl = int(max_tp / 2.0)  # ลด SL แทน
                    final_tp = max_tp
            
            # คำนวณราคา TP/SL
            if signal == "BUY":
                tp = entry_price + (final_tp * point)
                sl = entry_price - (final_sl * point)
            else:
                tp = entry_price - (final_tp * point)
                sl = entry_price + (final_sl * point)
            
            # Log การคำนวณ
            print(f"📊 Enhanced Dynamic TP/SL: ATR={atr_points:.1f}pts, Vol={volatility_factor:.2f}, Conf={confidence:.2%}")
            print(f"   🎯 TP: {final_tp}pts ({final_tp/10:.1f}pips), 🛡️ SL: {final_sl}pts ({final_sl/10:.1f}pips), R/R: 1:{risk_reward:.2f}")
            print(f"   💰 Expected Profit Range: {final_tp/10:.1f}-{final_tp/10*1.5:.1f} pips")
            
            return tp, sl, final_tp, final_sl
            
        except Exception as e:
            print(f"❌ Dynamic TP/SL calculation error: {e}")
            return self.calculate_static_tp_sl(signal, entry_price)
    
    def calculate_static_tp_sl(self, signal, entry_price):
        """คำนวณ TP/SL แบบ static (fallback)"""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            point = symbol_info.point
            
            if signal == "BUY":
                tp = entry_price + (self.tp_points * point)
                sl = entry_price - (self.sl_points * point)
            else:
                tp = entry_price - (self.tp_points * point)
                sl = entry_price + (self.sl_points * point)
            
            return tp, sl, self.tp_points, self.sl_points
            
        except Exception as e:
            print(f"❌ Static TP/SL calculation error: {e}")
            return None, None, None, None
    
    def calculate_scalping_tp_sl(self, signal, entry_price, confidence=0.7):
        """คำนวณ TP/SL สำหรับ scalping (รองรับทั้ง dynamic และ static)"""
        result = self.calculate_dynamic_tp_sl(signal, entry_price, confidence)
        if result and len(result) >= 2:
            return result[:2]  # return เฉพาะ tp, sl
        else:
            static_result = self.calculate_static_tp_sl(signal, entry_price)
            return static_result[:2] if static_result else (None, None)
    
    def final_entry_confirmation(self, signal, confidence, tp_points, sl_points):
        """การยืนยันขั้นสุดท้ายก่อนเข้า order"""
        try:
            print(f"🔍 Final Entry Confirmation for {signal}...")
            
            # 1. ตรวจสอบ confidence ขั้นสุดท้าย
            if confidence < 0.85:
                print(f"   ❌ Confidence too low: {confidence:.1%} < 85%")
                return False
            
            # 2. ตรวจสอบ Risk/Reward
            rr_ratio = tp_points / sl_points
            if rr_ratio < 1.8:
                print(f"   ❌ Risk/Reward too low: 1:{rr_ratio:.2f} < 1:1.8")
                return False
            
            # 3. ตรวจสอบ market conditions ล่าสุด
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 10)
            if df_m1 is None:
                print(f"   ❌ Cannot get latest market data")
                return False
            
            df_m1 = self.calculate_scalping_indicators(df_m1)
            if df_m1 is None:
                print(f"   ❌ Cannot calculate latest indicators")
                return False
            
            latest = df_m1.iloc[-1]
            
            # 4. ตรวจสอบ spread ล่าสุด
            tick = mt5.symbol_info_tick(self.symbol)
            symbol_info = mt5.symbol_info(self.symbol)
            
            if tick and symbol_info:
                current_spread = (tick.ask - tick.bid) / symbol_info.point
                if current_spread > self.max_spread:
                    print(f"   ❌ Spread too high: {current_spread:.1f} > {self.max_spread}")
                    return False
            
            # 5. ตรวจสอบ momentum ล่าสุด
            if abs(latest['macd_histogram_fast']) < 0.1:
                print(f"   ❌ MACD momentum too weak: {latest['macd_histogram_fast']:.3f}")
                return False
            
            # 6. ตรวจสอบ RSI ไม่ extreme
            if latest['rsi_fast'] < 20 or latest['rsi_fast'] > 80:
                print(f"   ❌ RSI too extreme: {latest['rsi_fast']:.1f}")
                return False
            
            # 7. ตรวจสอบ volume
            if latest['volume_ratio'] < 1.2:
                print(f"   ❌ Volume too low: {latest['volume_ratio']:.2f}")
                return False
            
            print(f"   ✅ All final confirmations passed")
            print(f"   📊 Spread: {current_spread:.1f}pts, RSI: {latest['rsi_fast']:.1f}")
            print(f"   📊 MACD: {latest['macd_histogram_fast']:.3f}, Vol: {latest['volume_ratio']:.2f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Final confirmation error: {e}")
            return False
    
    def get_active_positions(self):
        """ดึง positions ที่เปิดอยู่"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            return list(positions) if positions else []
        except:
            return []
    
    def place_scalping_order(self, signal, confidence, prediction_data):
        """เปิด order สำหรับ scalping (ปรับปรุง)"""
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
            
            # คำนวณ TP/SL แบบ dynamic
            tp_sl_result = self.calculate_dynamic_tp_sl(signal, price, confidence)
            if tp_sl_result and len(tp_sl_result) >= 4:
                tp, sl, tp_points, sl_points = tp_sl_result
                self.performance_data['dynamic_tp_used'] += 1
                print(f"🧠 Using Dynamic TP/SL: {tp_points}pts/{sl_points}pts")
            else:
                tp, sl, tp_points, sl_points = self.calculate_static_tp_sl(signal, price)
                self.performance_data['static_tp_used'] += 1
                print(f"📊 Using Static TP/SL: {tp_points}pts/{sl_points}pts")
            
            if tp is None or sl is None:
                return None
            
            # กำหนด lot size (conservative)
            lot_size = self.base_lot_size
            
            # เพิ่ม lot เฉพาะเมื่อ confidence สูงมาก
            if confidence > 0.9:
                lot_size *= 1.3
            elif confidence > 0.85:
                lot_size *= 1.1
            
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
                "deviation": 15,
                "magic": 234002,  # magic number ใหม่
                "comment": f"Fixed Scalping {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Final confirmation check
            final_check_passed = self.final_entry_confirmation(signal, confidence, tp_points, sl_points)
            if not final_check_passed:
                print(f"❌ Final confirmation failed - Order cancelled")
                return None
            
            print(f"⚡ CONFIRMED Enhanced Scalping order: {signal} {lot_size} lots @ ${price:.2f}")
            print(f"   🎯 TP: ${tp:.2f} (+{tp_points} points = +{tp_points/10:.1f} pips)")
            print(f"   🛡️ SL: ${sl:.2f} (-{sl_points} points = -{sl_points/10:.1f} pips)")
            print(f"   📊 Confidence: {confidence:.1%}")
            print(f"   📈 Risk/Reward: 1:{tp_points/sl_points:.2f}")
            print(f"   💰 Potential Profit: ${tp_points * symbol_info.point * lot_size * 100:.2f}")
            print(f"   ✅ All confirmations passed")
            
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
                    'expected_profit': tp_points * symbol_info.point * lot_size * 100,
                    'max_loss': sl_points * symbol_info.point * lot_size * 100,
                    'tp_points': tp_points,
                    'sl_points': sl_points
                }
                
                self.orders_placed.append(order_info)
                self.daily_trades += 1
                self.last_trade_time = datetime.now()
                self.performance_data['total_trades'] += 1
                
                print(f"✅ Fixed Scalping order placed: Ticket {result.order}")
                return order_info
            else:
                print(f"❌ Scalping order failed: {result.comment if result else 'Unknown error'}")
                return None
                
        except Exception as e:
            print(f"❌ Place scalping order error: {e}")
            return None
    
    def manage_scalping_positions(self):
        """จัดการ positions สำหรับ scalping (ปรับปรุง)"""
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
                
                # Improved position management
                if pos.profit > 0:
                    symbol_info = mt5.symbol_info(self.symbol)
                    profit_points = pos.profit / (symbol_info.point * pos.volume * 100)
                    
                    # Dynamic breakeven management
                    # คำนวณ breakeven threshold แบบ dynamic (50-70% ของ TP)
                    original_tp_points = abs((pos.tp - pos.price_open) / symbol_info.point)
                    dynamic_breakeven = max(30, int(original_tp_points * 0.6))  # 60% ของ TP
                    
                    if profit_points >= dynamic_breakeven:
                        if pos.type == mt5.POSITION_TYPE_BUY:
                            new_sl = pos.price_open + (10 * symbol_info.point)  # breakeven + 1 pip
                            if new_sl > pos.sl:
                                self.modify_position_sl(pos.ticket, new_sl)
                                print(f"📈 Dynamic breakeven moved: {pos.ticket} at +{profit_points:.0f}pts")
                        else:
                            new_sl = pos.price_open - (10 * symbol_info.point)  # breakeven - 1 pip
                            if new_sl < pos.sl:
                                self.modify_position_sl(pos.ticket, new_sl)
                                print(f"📉 Dynamic breakeven moved: {pos.ticket} at +{profit_points:.0f}pts")
                    
                    # Dynamic partial close (80% ของ TP)
                    dynamic_partial = max(50, int(original_tp_points * 0.8))  # 80% ของ TP
                    
                    if profit_points >= dynamic_partial and pos.volume > symbol_info.volume_min * 2:
                        partial_volume = pos.volume / 2
                        partial_volume = round(partial_volume / symbol_info.volume_step) * symbol_info.volume_step
                        
                        if partial_volume >= symbol_info.volume_min:
                            print(f"📊 Dynamic partial close: {pos.ticket} - {partial_volume} lots at +{profit_points:.0f}pts (threshold: {dynamic_partial}pts)")
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
                "deviation": 15,
                "magic": 234002,
                "comment": f"Fixed Scalping Close - {reason}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                # วิเคราะห์ว่าปิดที่ TP หรือ SL
                symbol_info = mt5.symbol_info(self.symbol)
                close_price = price
                entry_price = position.price_open
                tp_price = position.tp
                sl_price = position.sl
                
                # ตรวจสอบว่าปิดใกล้ TP หรือ SL
                tp_distance = abs(close_price - tp_price) if tp_price > 0 else float('inf')
                sl_distance = abs(close_price - sl_price) if sl_price > 0 else float('inf')
                
                hit_tp = tp_distance < sl_distance and tp_distance < (20 * symbol_info.point)
                hit_sl = sl_distance < tp_distance and sl_distance < (20 * symbol_info.point)
                
                # อัพเดทสถิติ
                if position.profit > 0:
                    self.performance_data['winning_trades'] += 1
                    if hit_tp:
                        self.performance_data['tp_hit_rate'] = (self.performance_data.get('tp_hits', 0) + 1) / (self.performance_data['winning_trades'] + self.performance_data['losing_trades'])
                        self.performance_data['tp_hits'] = self.performance_data.get('tp_hits', 0) + 1
                else:
                    self.performance_data['losing_trades'] += 1
                    if hit_sl:
                        self.performance_data['sl_hit_rate'] = (self.performance_data.get('sl_hits', 0) + 1) / (self.performance_data['winning_trades'] + self.performance_data['losing_trades'])
                        self.performance_data['sl_hits'] = self.performance_data.get('sl_hits', 0) + 1
                
                self.performance_data['total_profit'] += position.profit
                self.daily_profit += position.profit
                
                # คำนวณ win rate
                total_closed = self.performance_data['winning_trades'] + self.performance_data['losing_trades']
                if total_closed > 0:
                    self.performance_data['win_rate'] = self.performance_data['winning_trades'] / total_closed
                    self.performance_data['avg_profit_per_trade'] = self.performance_data['total_profit'] / total_closed
                
                # คำนวณ TP/SL points ที่ใช้จริง
                if tp_price > 0:
                    actual_tp_points = abs(tp_price - entry_price) / symbol_info.point
                    current_avg_tp = self.performance_data.get('avg_tp_points', 0)
                    self.performance_data['avg_tp_points'] = (current_avg_tp * (total_closed - 1) + actual_tp_points) / total_closed
                
                if sl_price > 0:
                    actual_sl_points = abs(sl_price - entry_price) / symbol_info.point
                    current_avg_sl = self.performance_data.get('avg_sl_points', 0)
                    self.performance_data['avg_sl_points'] = (current_avg_sl * (total_closed - 1) + actual_sl_points) / total_closed
                
                close_type = "TP" if hit_tp else "SL" if hit_sl else "Manual"
                
                # ติดตาม AI prediction accuracy
                self.track_prediction_accuracy(ticket, position.profit > 0, close_type)
                
                print(f"✅ Position closed: {ticket} - P&L: ${position.profit:.2f} ({close_type}) - {reason}")
                return True
            else:
                print(f"❌ Failed to close position {ticket}")
                return False
                
        except Exception as e:
            print(f"❌ Close position error: {e}")
            return False
    
    def track_prediction_accuracy(self, ticket, is_profitable, close_type):
        """ติดตาม accuracy ของ AI predictions"""
        try:
            # หา prediction ที่เกี่ยวข้องกับ ticket นี้
            for order in self.orders_placed:
                if order.get('ticket') == ticket:
                    prediction_data = {
                        'ticket': ticket,
                        'predicted_signal': order.get('signal'),
                        'confidence': order.get('confidence', 0),
                        'is_profitable': is_profitable,
                        'close_type': close_type,
                        'timestamp': datetime.now()
                    }
                    
                    self.model_predictions.append(prediction_data)
                    
                    # คำนวณ accuracy ล่าสุด (100 predictions ล่าสุด)
                    recent_predictions = self.model_predictions[-100:]
                    if len(recent_predictions) >= 10:
                        correct_predictions = sum(1 for p in recent_predictions if p['is_profitable'])
                        current_accuracy = correct_predictions / len(recent_predictions)
                        
                        print(f"🤖 AI Accuracy: {current_accuracy:.1%} (last {len(recent_predictions)} trades)")
                        
                        # ถ้า accuracy ต่ำมาก ให้เตือน
                        if current_accuracy < 0.4 and len(recent_predictions) >= 20:
                            warning_message = f"""
⚠️ <b>AI PERFORMANCE WARNING</b> ⚠️

🤖 <b>Current Accuracy:</b> {current_accuracy:.1%}
📊 <b>Sample Size:</b> {len(recent_predictions)} trades
🎯 <b>Target Accuracy:</b> >60%

<i>⚠️ AI model may need retraining</i>
                            """.strip()
                            
                            self.send_telegram_message(warning_message)
                    
                    break
                    
        except Exception as e:
            print(f"❌ Error tracking prediction accuracy: {e}")
    
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
                "deviation": 15,
                "magic": 234002,
                "comment": "Fixed Scalping Partial Close",
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
        
        # ใช้ dynamic TP/SL calculation
        tp_sl_result = self.calculate_dynamic_tp_sl(signal, price, confidence)
        if tp_sl_result and len(tp_sl_result) >= 4:
            tp, sl, tp_points, sl_points = tp_sl_result
        else:
            tp, sl, tp_points, sl_points = self.calculate_static_tp_sl(signal, price)
        
        # ถ้ามี order_info ใช้ค่าจริงจาก order
        if order_info:
            tp_points = order_info.get('tp_points', tp_points)
            sl_points = order_info.get('sl_points', sl_points)
        
        message = f"""
⚡ <b>ENHANCED DYNAMIC SCALPING SIGNAL</b> ⚡

{emoji} <b>สัญญาณ: {action} ({signal})</b>
💰 <b>ราคาเข้า:</b> ${price:.2f}
🎯 <b>Take Profit:</b> ${tp:.2f} (+{tp_points} points = +{tp_points/10} pips)
🛡️ <b>Stop Loss:</b> ${sl:.2f} (-{sl_points} points = -{sl_points/10} pips)
📊 <b>ความมั่นใจ:</b> {confidence:.1%}
� <b>RiDsk/Reward:</b> 1:{tp_points/sl_points:.2f}
📈 <b>Trend:</b> {prediction.get('trend_direction', 0):+d}
⚡ <b>ATR:</b> {prediction.get('atr', 0):.6f}
🧠 <b>TP/SL Type:</b> {'Dynamic' if tp_sl_result and len(tp_sl_result) >= 4 else 'Static'}
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
• Breakeven Rate: {self.performance_data['breakeven_rate']:.1%}

⏰ <b>เวลา:</b> {prediction['timestamp'].strftime('%H:%M:%S')}

<i>⚡ Dynamic Gold Scalping Trader</i>
        """.strip()
        
        return message
    
    def run_continuous_scalping(self):
        """รันเซสชัน scalping แบบต่อเนื่อง 24/7"""
        print(f"⚡ Starting Continuous Gold Scalping (24/7 Mode)")
        
        if not self.connect_mt5():
            return False
        
        ai_ready = self.train_scalping_model()
        if not ai_ready:
            print("⚠️ AI Model not ready - switching to Technical Analysis mode")
            self.model = None  # ใช้ technical analysis แทน
        
        # ส่งข้อความเริ่มต้น
        ai_mode = "AI Model Ready" if ai_ready else "Technical Analysis Mode"
        start_message = f"""
⚡ <b>CONTINUOUS GOLD SCALPING STARTED</b> ⚡

🤖 <b>Analysis Mode:</b> {ai_mode}
📊 <b>Symbol:</b> {self.symbol}
⏰ <b>Mode:</b> 24/7 Continuous Trading
📡 <b>Signal Check:</b> Every {self.signal_interval_seconds} seconds

🎯 <b>Target:</b> +{self.tp_points} points ({self.tp_points/10} pips)
🛡️ <b>Risk:</b> -{self.sl_points} points ({self.sl_points/10} pips)
📈 <b>Risk/Reward:</b> 1:{self.tp_points/self.sl_points:.2f}
📊 <b>Breakeven Rate:</b> {self.performance_data['breakeven_rate']:.1%}
📊 <b>Max Trades:</b> {self.max_daily_trades}/day (resets daily)
⚡ <b>Max Hold:</b> {self.max_hold_minutes} minutes
🔒 <b>Confidence Threshold:</b> {self.confidence_threshold:.1%}

<i>🚀 Ready for 24/7 profitable scalping!</i>
        """.strip()
        
        self.send_telegram_message(start_message)
        
        signals_sent = 0
        session_start = datetime.now()
        last_daily_report = datetime.now().date()
        
        try:
            while True:  # รันต่อเนื่องไม่มีที่สิ้นสุด
                current_time = datetime.now()
                
                # ส่งรายงานรายวัน
                if current_time.date() != last_daily_report:
                    self.send_daily_report()
                    last_daily_report = current_time.date()
                    # รีเซ็ตสถิติสัญญาณรายวัน
                    self.daily_buy_signals = 0
                    self.daily_sell_signals = 0
                
                # จัดการ positions ที่มีอยู่
                self.manage_scalping_positions()
                
                # ตรวจสอบสภาพตลาด
                market_ok, market_msg = self.check_market_conditions()
                
                if market_ok:
                    # ทำนายสัญญาณ
                    prediction = self.make_scalping_prediction()
                    
                    if prediction:  # confidence ถูกตรวจสอบใน make_scalping_prediction แล้ว
                        print(f"⚡ Enhanced Scalping signal: {prediction['signal']} ({prediction['confidence']:.1%}) - Trend: {prediction.get('trend_direction', 0):+d}")
                        
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
                                self.performance_data['total_signals'] += 1
                                
                                # นับสัญญาณ BUY/SELL
                                if prediction['signal'] == 'BUY':
                                    self.daily_buy_signals += 1
                                else:
                                    self.daily_sell_signals += 1
                                
                                print(f"✅ Enhanced Scalping signal sent: {prediction['signal']} (Trend: {prediction.get('trend_direction', 0):+d})")
                                print(f"📊 Daily signals: BUY={self.daily_buy_signals}, SELL={self.daily_sell_signals}")
                    else:
                        print(f"⏭️ No high-quality signal available")
                else:
                    print(f"⏳ Market not ready: {market_msg}")
                
                # รอตามช่วงเวลาที่กำหนด
                time.sleep(self.signal_interval_seconds)
        
        except KeyboardInterrupt:
            print("\n⏹️ Continuous Scalping stopped by user")
            
            # ปิด positions ที่เหลือ
            positions = self.get_active_positions()
            for pos in positions:
                self.close_position(pos.ticket, "Manual stop")
            
            # ส่งสรุปผล
            session_duration = datetime.now() - session_start
            final_positions = self.get_active_positions()
            
            summary_message = f"""
🏁 <b>CONTINUOUS SCALPING STOPPED</b> 🏁

📊 <b>Session Summary:</b>
• Session Duration: {session_duration}
• Signals Sent: {signals_sent}
• Total Trades: {self.daily_trades}
• Winning Trades: {self.performance_data['winning_trades']}
• Losing Trades: {self.performance_data['losing_trades']}
• Win Rate: {self.performance_data['win_rate']:.1%}
• Daily P&L: ${self.daily_profit:.2f}
• Avg Profit/Trade: ${self.performance_data['avg_profit_per_trade']:.2f}
• Risk/Reward Ratio: 1:{self.tp_points/self.sl_points:.2f}
• Remaining Positions: {len(final_positions)}

<i>⚡ Continuous Gold Scalping Trader</i>
            """.strip()
            
            self.send_telegram_message(summary_message)
            
            print(f"\n🏁 Continuous Scalping session stopped!")
            print(f"⚡ Total signals sent: {signals_sent}")
            print(f"💼 Total trades: {self.daily_trades}")
            print(f"🎯 Win rate: {self.performance_data['win_rate']:.1%}")
            print(f"💰 Daily P&L: ${self.daily_profit:.2f}")
            print(f"📈 Risk/Reward: 1:{self.tp_points/self.sl_points:.2f}")
            
            return True
        
        except Exception as e:
            print(f"❌ Continuous scalping error: {e}")
            
            # ส่งแจ้งเตือนข้อผิดพลาด
            error_message = f"""
❌ <b>CONTINUOUS SCALPING ERROR</b> ❌

🚨 <b>Error:</b> {str(e)}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 <b>Trades Today:</b> {self.daily_trades}
💰 <b>Daily P&L:</b> ${self.daily_profit:.2f}

<i>⚠️ System will attempt to restart...</i>
            """.strip()
            
            self.send_telegram_message(error_message)
            return False
    
    def send_daily_report(self):
        """ส่งรายงานรายวัน"""
        try:
            positions = self.get_active_positions()
            
            daily_report = f"""
📊 <b>DAILY DYNAMIC SCALPING REPORT</b> 📊

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

📈 <b>Trading Performance:</b>
• Total Trades: {self.daily_trades}/{self.max_daily_trades}
• Winning Trades: {self.performance_data['winning_trades']}
• Losing Trades: {self.performance_data['losing_trades']}
• Win Rate: {self.performance_data['win_rate']:.1%}
• Daily P&L: ${self.daily_profit:.2f}
• Avg Profit/Trade: ${self.performance_data['avg_profit_per_trade']:.2f}

📊 <b>Signal Balance:</b>
• BUY Signals: {self.daily_buy_signals} ({self.daily_buy_signals/(self.daily_buy_signals+self.daily_sell_signals)*100:.1f}% if self.daily_buy_signals+self.daily_sell_signals > 0 else 0)
• SELL Signals: {self.daily_sell_signals} ({self.daily_sell_signals/(self.daily_buy_signals+self.daily_sell_signals)*100:.1f}% if self.daily_buy_signals+self.daily_sell_signals > 0 else 0)
• Balance Ratio: {self.daily_buy_signals}:{self.daily_sell_signals}

🎯 <b>TP/SL Analysis:</b>
• Avg TP Used: {self.performance_data.get('avg_tp_points', 0):.1f} points
• Avg SL Used: {self.performance_data.get('avg_sl_points', 0):.1f} points
• TP Hit Rate: {self.performance_data.get('tp_hit_rate', 0):.1%}
• SL Hit Rate: {self.performance_data.get('sl_hit_rate', 0):.1%}
• Dynamic TP/SL: {self.performance_data.get('dynamic_tp_used', 0)} times
• Static TP/SL: {self.performance_data.get('static_tp_used', 0)} times

🤖 <b>AI Performance:</b>
• Model Accuracy: {(sum(1 for p in self.model_predictions[-50:] if p['is_profitable']) / len(self.model_predictions[-50:]) * 100) if len(self.model_predictions[-50:]) > 0 else 0:.1f}%
• Predictions Made: {len(self.model_predictions)}
• High Confidence Trades: {sum(1 for p in self.model_predictions if p.get('confidence', 0) > 0.9)}
• Last Model Training: {self.last_model_evaluation.strftime('%H:%M') if self.last_model_evaluation else 'N/A'}

💼 <b>Current Status:</b>
• Active Positions: {len(positions)}
• Base Risk/Reward: 1:{self.tp_points/self.sl_points:.2f}
• Actual Avg R/R: 1:{self.performance_data.get('avg_tp_points', self.tp_points)/self.performance_data.get('avg_sl_points', self.sl_points):.2f}
• System Status: Running 24/7

<i>⚡ Dynamic Gold Scalping Trader</i>
            """.strip()
            
            self.send_telegram_message(daily_report)
            print(f"📊 Daily report sent for {datetime.now().date()}")
            
        except Exception as e:
            print(f"❌ Daily report error: {e}")
    
    def run_scalping_session(self, duration_minutes=None):
        """รันเซสชัน scalping (รองรับทั้งแบบจำกัดเวลาและต่อเนื่อง)"""
        if duration_minutes is None or duration_minutes <= 0:
            # รันแบบต่อเนื่อง
            return self.run_continuous_scalping()
        
        # รันแบบจำกัดเวลา (เก่า)
        print(f"⚡ Starting Fixed Gold Scalping Session ({duration_minutes} minutes)")
        
        if not self.connect_mt5():
            return False
        
        if not self.train_scalping_model():
            return False
        
        # ส่งข้อความเริ่มต้น
        start_message = f"""
⚡ <b>FIXED GOLD SCALPING TRADER STARTED</b> ⚡

🤖 <b>AI Model:</b> Fixed Scalping Optimized
📊 <b>Symbol:</b> {self.symbol}
⏰ <b>Duration:</b> {duration_minutes} minutes
📡 <b>Signal Check:</b> Every {self.signal_interval_seconds} seconds

🎯 <b>Target:</b> +{self.tp_points} points ({self.tp_points/10} pips)
🛡️ <b>Risk:</b> -{self.sl_points} points ({self.sl_points/10} pips)
📈 <b>Risk/Reward:</b> 1:{self.tp_points/self.sl_points:.2f}
📊 <b>Breakeven Rate:</b> {self.performance_data['breakeven_rate']:.1%}
📊 <b>Max Trades:</b> {self.max_daily_trades}/day
⚡ <b>Max Hold:</b> {self.max_hold_minutes} minutes
🔒 <b>Confidence Threshold:</b> {self.confidence_threshold:.1%}

<i>🚀 Ready for profitable scalping!</i>
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
                
                # ตรวจสอบสภาพตลาด
                market_ok, market_msg = self.check_market_conditions()
                
                if market_ok:
                    # ทำนายสัญญาณ
                    prediction = self.make_scalping_prediction()
                    
                    if prediction:  # confidence ถูกตรวจสอบใน make_scalping_prediction แล้ว
                        print(f"⚡ Fixed Scalping signal: {prediction['signal']} ({prediction['confidence']:.1%})")
                        
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
                                print(f"✅ Fixed Scalping signal sent: {prediction['signal']}")
                    else:
                        print(f"⏭️ No high-quality signal available")
                else:
                    print(f"⏳ Market not ready: {market_msg}")
                
                # รอตามช่วงเวลาที่กำหนด
                time.sleep(self.signal_interval_seconds)
        
        except KeyboardInterrupt:
            print("\n⏹️ Fixed Scalping stopped by user")
        
        # ปิด positions ที่เหลือ
        positions = self.get_active_positions()
        for pos in positions:
            self.close_position(pos.ticket, "Session end")
        
        # ส่งสรุปผล
        final_positions = self.get_active_positions()
        
        summary_message = f"""
🏁 <b>FIXED SCALPING SESSION COMPLETED</b> 🏁

📊 <b>Session Summary:</b>
• Signals Sent: {signals_sent}
• Total Trades: {self.daily_trades}
• Winning Trades: {self.performance_data['winning_trades']}
• Losing Trades: {self.performance_data['losing_trades']}
• Win Rate: {self.performance_data['win_rate']:.1%}
• Session P&L: ${self.daily_profit:.2f}
• Avg Profit/Trade: ${self.performance_data['avg_profit_per_trade']:.2f}
• Risk/Reward Ratio: 1:{self.tp_points/self.sl_points:.2f}
• Remaining Positions: {len(final_positions)}

<i>⚡ Fixed Gold Scalping Trader</i>
        """.strip()
        
        self.send_telegram_message(summary_message)
        
        print(f"\n🏁 Fixed Scalping session completed!")
        print(f"⚡ Signals sent: {signals_sent}")
        print(f"💼 Total trades: {self.daily_trades}")
        print(f"🎯 Win rate: {self.performance_data['win_rate']:.1%}")
        print(f"💰 Session P&L: ${self.daily_profit:.2f}")
        print(f"📈 Risk/Reward: 1:{self.tp_points/self.sl_points:.2f}")
        
        return True

def main():
    """ฟังก์ชันหลัก"""
    print("⚡ Fixed Gold Scalping Trader - 24/7 Profitable Scalping")
    print("=" * 60)
    
    # สร้าง trader
    trader = FixedGoldScalpingTrader()
    
    # แสดงการตั้งค่า
    print(f"\n⚙️ Fixed Scalping Configuration:")
    print(f"   ⚡ Timeframe: M1 (1 minute)")
    print(f"   🎯 Take Profit: {trader.tp_points} points ({trader.tp_points/10} pips)")
    print(f"   🛡️ Stop Loss: {trader.sl_points} points ({trader.sl_points/10} pips)")
    print(f"   📈 Risk/Reward: 1:{trader.tp_points/trader.sl_points:.2f}")
    print(f"   📊 Breakeven Rate: {trader.performance_data['breakeven_rate']:.1%}")
    print(f"   📊 Max Spread: {trader.max_spread} points")
    print(f"   💼 Max Positions: {trader.max_positions}")
    print(f"   📈 Max Daily Trades: {trader.max_daily_trades}")
    print(f"   ⏰ Max Hold Time: {trader.max_hold_minutes} minutes")
    print(f"   📡 Signal Interval: {trader.signal_interval_seconds} seconds")
    print(f"   🔒 Confidence Threshold: {trader.confidence_threshold:.1%}")
    
    # เลือกโหมด
    print(f"\n🚀 Select Trading Mode:")
    print(f"   1. Continuous Trading (24/7) - รันต่อเนื่องไม่มีที่สิ้นสุด")
    print(f"   2. Timed Session - รันตามเวลาที่กำหนด")
    
    try:
        mode = input(f"\nSelect mode (1 or 2, default 1): ").strip() or "1"
        
        if mode == "1":
            print(f"\n⚡ Starting 24/7 Continuous Trading Mode")
            print(f"⚠️ This will run indefinitely until you press Ctrl+C")
            print(f"📊 Daily stats will reset automatically at midnight")
            
            confirm = input(f"\nContinue? (y/n, default y): ").strip().lower() or "y"
            if confirm == "y":
                success = trader.run_scalping_session(None)  # None = continuous mode
            else:
                print("❌ Cancelled by user")
                return
        else:
            duration = int(input(f"\nScalping duration (minutes, default 60): ") or "60")
            success = trader.run_scalping_session(duration)
        
        if success:
            print("\n🎉 Scalping session completed successfully!")
        else:
            print("\n❌ Scalping session failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

if __name__ == "__main__":
    main()