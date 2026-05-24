#!/usr/bin/env python3
"""
BTC Analysis Bot - บอทวิเคราะห์ BTCUSD# แบบครบครัน
วิเคราะห์เทคนิค, กำหนด TP/SL, จุดเข้า และส่งไป Telegram
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

class BTCAnalysisBot:
    """บอทวิเคราะห์ Bitcoin แบบครบครัน"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        # Telegram settings
        self.telegram_token = telegram_token or "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
        self.chat_id = chat_id or "-1002852894581"
        
        # BTC settings
        self.symbol = "BTCUSD#"
        self.timeframes = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        
        # AI Model
        self.model = None
        self.scaler = StandardScaler()
        
        # Analysis data
        self.analysis_results = {}
        self.technical_levels = {}
        self.ai_prediction = {}
        
        print("₿ BTC Analysis Bot initialized")
    
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
            
            # ตรวจสอบ BTC symbols
            btc_symbols = ["BTCUSD#", "BTCUSD", "BTC/USD", "BITCOIN"]
            for symbol in btc_symbols:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is not None:
                    self.symbol = symbol
                    break
            
            print(f"✅ MT5 connected - Account: {account_info.login}")
            print(f"₿ BTC symbol: {self.symbol}")
            
            return True
            
        except Exception as e:
            print(f"❌ MT5 connection error: {e}")
            return False
    
    def get_btc_data(self, timeframe, count=500):
        """ดึงข้อมูล BTC จาก MT5"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            print(f"❌ BTC data retrieval error: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """คำนวณ Technical Indicators ครบครัน"""
        try:
            if df is None or len(df) < 100:
                return None
            
            # Moving Averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['sma_100'] = df['close'].rolling(window=100).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
            
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            df['ema_200'] = df['close'].ewm(span=200).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Stochastic
            low_14 = df['low'].rolling(window=14).min()
            high_14 = df['high'].rolling(window=14).max()
            df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
            df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            # ATR
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            df['atr'] = df['true_range'].rolling(window=14).mean()
            
            # Volume indicators
            df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
            
            # Price patterns
            df['doji'] = np.where(abs(df['close'] - df['open']) <= (df['high'] - df['low']) * 0.1, 1, 0)
            df['hammer'] = np.where(
                (df['close'] > df['open']) & 
                ((df['close'] - df['open']) / (df['high'] - df['low']) < 0.3) &
                ((df['open'] - df['low']) / (df['high'] - df['low']) > 0.6), 1, 0
            )
            
            # Support/Resistance levels
            df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
            df['resistance_1'] = 2 * df['pivot'] - df['low']
            df['support_1'] = 2 * df['pivot'] - df['high']
            df['resistance_2'] = df['pivot'] + (df['high'] - df['low'])
            df['support_2'] = df['pivot'] - (df['high'] - df['low'])
            
            return df
            
        except Exception as e:
            print(f"❌ Technical indicator calculation error: {e}")
            return None
    
    def identify_support_resistance(self, df, window=20):
        """ระบุ Support และ Resistance levels"""
        try:
            if df is None or len(df) < window * 2:
                return {}
            
            levels = {}
            
            # หา local highs และ lows
            highs = df['high'].rolling(window=window, center=True).max()
            lows = df['low'].rolling(window=window, center=True).min()
            
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(df) - window):
                if df['high'].iloc[i] == highs.iloc[i]:
                    resistance_levels.append(df['high'].iloc[i])
                if df['low'].iloc[i] == lows.iloc[i]:
                    support_levels.append(df['low'].iloc[i])
            
            # เอาเฉพาะ levels ที่สำคัญ
            current_price = df['close'].iloc[-1]
            
            # Resistance levels above current price
            resistance_above = [r for r in resistance_levels if r > current_price]
            resistance_above.sort()
            
            # Support levels below current price
            support_below = [s for s in support_levels if s < current_price]
            support_below.sort(reverse=True)
            
            levels = {
                'current_price': current_price,
                'nearest_resistance': resistance_above[:3] if resistance_above else [],
                'nearest_support': support_below[:3] if support_below else [],
                'pivot_point': df['pivot'].iloc[-1],
                'resistance_1': df['resistance_1'].iloc[-1],
                'support_1': df['support_1'].iloc[-1],
                'resistance_2': df['resistance_2'].iloc[-1],
                'support_2': df['support_2'].iloc[-1]
            }
            
            return levels
            
        except Exception as e:
            print(f"❌ Support/Resistance identification error: {e}")
            return {}
    
    def analyze_trend(self, df):
        """วิเคราะห์เทรนด์"""
        try:
            if df is None or len(df) < 50:
                return {}
            
            latest = df.iloc[-1]
            
            # Moving Average Trend
            ma_trend = "NEUTRAL"
            if latest['close'] > latest['sma_20'] > latest['sma_50'] > latest['sma_200']:
                ma_trend = "STRONG_BULLISH"
            elif latest['close'] > latest['sma_20'] > latest['sma_50']:
                ma_trend = "BULLISH"
            elif latest['close'] < latest['sma_20'] < latest['sma_50'] < latest['sma_200']:
                ma_trend = "STRONG_BEARISH"
            elif latest['close'] < latest['sma_20'] < latest['sma_50']:
                ma_trend = "BEARISH"
            
            # EMA Trend
            ema_trend = "NEUTRAL"
            if latest['ema_12'] > latest['ema_26'] > latest['ema_50'] > latest['ema_200']:
                ema_trend = "STRONG_BULLISH"
            elif latest['ema_12'] > latest['ema_26']:
                ema_trend = "BULLISH"
            elif latest['ema_12'] < latest['ema_26'] < latest['ema_50'] < latest['ema_200']:
                ema_trend = "STRONG_BEARISH"
            elif latest['ema_12'] < latest['ema_26']:
                ema_trend = "BEARISH"
            
            # Price momentum
            price_change_1h = (latest['close'] - df['close'].iloc[-12]) / df['close'].iloc[-12] * 100
            price_change_4h = (latest['close'] - df['close'].iloc[-48]) / df['close'].iloc[-48] * 100
            price_change_24h = (latest['close'] - df['close'].iloc[-288]) / df['close'].iloc[-288] * 100 if len(df) > 288 else 0
            
            trend_analysis = {
                'ma_trend': ma_trend,
                'ema_trend': ema_trend,
                'price_change_1h': price_change_1h,
                'price_change_4h': price_change_4h,
                'price_change_24h': price_change_24h,
                'overall_trend': ma_trend if ma_trend != "NEUTRAL" else ema_trend
            }
            
            return trend_analysis
            
        except Exception as e:
            print(f"❌ Trend analysis error: {e}")
            return {}
    
    def analyze_momentum(self, df):
        """วิเคราะห์ Momentum"""
        try:
            if df is None or len(df) < 50:
                return {}
            
            latest = df.iloc[-1]
            
            # RSI Analysis
            rsi_status = "NEUTRAL"
            if latest['rsi'] > 70:
                rsi_status = "OVERBOUGHT"
            elif latest['rsi'] < 30:
                rsi_status = "OVERSOLD"
            elif latest['rsi'] > 60:
                rsi_status = "BULLISH"
            elif latest['rsi'] < 40:
                rsi_status = "BEARISH"
            
            # MACD Analysis
            macd_status = "NEUTRAL"
            if latest['macd'] > latest['macd_signal'] and latest['macd_histogram'] > 0:
                macd_status = "BULLISH"
            elif latest['macd'] < latest['macd_signal'] and latest['macd_histogram'] < 0:
                macd_status = "BEARISH"
            
            # Stochastic Analysis
            stoch_status = "NEUTRAL"
            if latest['stoch_k'] > 80 and latest['stoch_d'] > 80:
                stoch_status = "OVERBOUGHT"
            elif latest['stoch_k'] < 20 and latest['stoch_d'] < 20:
                stoch_status = "OVERSOLD"
            elif latest['stoch_k'] > latest['stoch_d'] and latest['stoch_k'] > 50:
                stoch_status = "BULLISH"
            elif latest['stoch_k'] < latest['stoch_d'] and latest['stoch_k'] < 50:
                stoch_status = "BEARISH"
            
            momentum_analysis = {
                'rsi': latest['rsi'],
                'rsi_status': rsi_status,
                'macd': latest['macd'],
                'macd_signal': latest['macd_signal'],
                'macd_histogram': latest['macd_histogram'],
                'macd_status': macd_status,
                'stoch_k': latest['stoch_k'],
                'stoch_d': latest['stoch_d'],
                'stoch_status': stoch_status
            }
            
            return momentum_analysis
            
        except Exception as e:
            print(f"❌ Momentum analysis error: {e}")
            return {}
    
    def train_ai_model(self):
        """เทรน AI Model สำหรับ BTC"""
        print("🤖 Training BTC AI model...")
        
        try:
            # ดึงข้อมูลจากหลาย timeframes
            all_features = []
            all_labels = []
            
            for tf_name, tf_value in [('H1', mt5.TIMEFRAME_H1), ('H4', mt5.TIMEFRAME_H4)]:
                print(f"   📊 Processing {tf_name} data...")
                
                df = self.get_btc_data(tf_value, 1000)
                if df is None:
                    continue
                
                df = self.calculate_technical_indicators(df)
                if df is None:
                    continue
                
                # สร้าง labels สำหรับ BTC (volatility สูง)
                future_bars = 12 if tf_value == mt5.TIMEFRAME_H1 else 6
                df['future_high'] = df['high'].shift(-future_bars).rolling(window=future_bars).max()
                df['future_low'] = df['low'].shift(-future_bars).rolling(window=future_bars).min()
                
                # คำนวณผลตอบแทนที่เป็นไปได้
                df['potential_buy_profit'] = (df['future_high'] - df['close']) / df['close']
                df['potential_sell_profit'] = (df['close'] - df['future_low']) / df['close']
                
                # กำหนด threshold สำหรับ BTC (2% profit, 1% loss)
                profit_threshold = 0.02
                loss_threshold = 0.01
                
                # สร้าง labels
                conditions = [
                    (df['potential_buy_profit'] > profit_threshold) & 
                    (df['potential_buy_profit'] > df['potential_sell_profit']) &
                    ((df['close'] - df['future_low']) / df['close'] < loss_threshold),
                    
                    (df['potential_sell_profit'] > profit_threshold) & 
                    (df['potential_sell_profit'] > df['potential_buy_profit']) &
                    ((df['future_high'] - df['close']) / df['close'] < loss_threshold)
                ]
                choices = [1, 0]
                df['label'] = np.select(conditions, choices, default=-1)
                
                # เลือก features
                features = [
                    'rsi', 'macd', 'macd_histogram', 'bb_position', 'bb_width',
                    'stoch_k', 'stoch_d', 'atr', 'volume_ratio',
                    'sma_20', 'sma_50', 'ema_12', 'ema_26'
                ]
                
                # Normalize features
                for feature in ['sma_20', 'sma_50', 'ema_12', 'ema_26']:
                    df[feature] = df[feature] / df['close']
                
                df_clean = df[features + ['label']].dropna()
                df_final = df_clean[df_clean['label'] != -1].copy()
                
                if len(df_final) > 50:
                    X = df_final[features].values
                    y = df_final['label'].values
                    all_features.append(X)
                    all_labels.append(y)
                    print(f"   ✅ {tf_name}: {len(df_final)} quality samples")
            
            if not all_features:
                print("❌ No training data available")
                return False
            
            X_combined = np.vstack(all_features)
            y_combined = np.hstack(all_labels)
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X_combined)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=3,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_scaled, y_combined)
            accuracy = self.model.score(X_scaled, y_combined)
            
            print(f"✅ BTC AI model trained!")
            print(f"📊 Training accuracy: {accuracy:.2%}")
            print(f"📈 Training samples: {len(X_combined)}")
            
            return True
            
        except Exception as e:
            print(f"❌ AI model training error: {e}")
            return False
    
    def make_ai_prediction(self):
        """ทำนายด้วย AI"""
        if self.model is None:
            return {}
        
        try:
            # ดึงข้อมูล H1 ล่าสุด
            df = self.get_btc_data(mt5.TIMEFRAME_H1, 200)
            if df is None:
                return {}
            
            df = self.calculate_technical_indicators(df)
            if df is None:
                return {}
            
            features = [
                'rsi', 'macd', 'macd_histogram', 'bb_position', 'bb_width',
                'stoch_k', 'stoch_d', 'atr', 'volume_ratio',
                'sma_20', 'sma_50', 'ema_12', 'ema_26'
            ]
            
            # Normalize price-based features
            latest_data = df.iloc[-1:].copy()
            for feature in ['sma_20', 'sma_50', 'ema_12', 'ema_26']:
                latest_data[feature] = latest_data[feature] / latest_data['close']
            
            feature_values = latest_data[features].values
            
            if np.isnan(feature_values).any():
                return {}
            
            # Normalize และทำนาย
            features_scaled = self.scaler.transform(feature_values)
            prediction = self.model.predict(features_scaled)[0]
            probability = self.model.predict_proba(features_scaled)[0]
            confidence = max(probability)
            
            signal = "BUY" if prediction == 1 else "SELL"
            
            ai_prediction = {
                'signal': signal,
                'confidence': confidence,
                'probability_buy': probability[1] if len(probability) > 1 else 0,
                'probability_sell': probability[0] if len(probability) > 0 else 0,
                'model_accuracy': 'High' if confidence > 0.8 else 'Medium' if confidence > 0.6 else 'Low'
            }
            
            return ai_prediction
            
        except Exception as e:
            print(f"❌ AI prediction error: {e}")
            return {}
    
    def calculate_entry_levels(self, df, signal):
        """คำนวณจุดเข้าและ TP/SL"""
        try:
            if df is None:
                return {}
            
            latest = df.iloc[-1]
            current_price = latest['close']
            atr = latest['atr']
            
            levels = {}
            
            if signal == "BUY":
                # Entry levels
                entry_1 = current_price  # Market entry
                entry_2 = latest['support_1']  # Support entry
                
                # Take Profit levels
                tp1 = current_price + (atr * 1.5)  # Conservative TP
                tp2 = current_price + (atr * 3.0)  # Aggressive TP
                
                # Stop Loss levels
                sl1 = current_price - (atr * 1.0)  # Tight SL
                sl2 = latest['support_1'] - (atr * 0.5)  # Support-based SL
                
                levels = {
                    'signal': 'BUY',
                    'entry_1': entry_1,
                    'entry_2': entry_2,
                    'tp1': tp1,
                    'tp2': tp2,
                    'sl1': sl1,
                    'sl2': sl2,
                    'risk_reward_1': (tp1 - entry_1) / (entry_1 - sl1),
                    'risk_reward_2': (tp2 - entry_1) / (entry_1 - sl1)
                }
                
            else:  # SELL
                # Entry levels
                entry_1 = current_price  # Market entry
                entry_2 = latest['resistance_1']  # Resistance entry
                
                # Take Profit levels
                tp1 = current_price - (atr * 1.5)  # Conservative TP
                tp2 = current_price - (atr * 3.0)  # Aggressive TP
                
                # Stop Loss levels
                sl1 = current_price + (atr * 1.0)  # Tight SL
                sl2 = latest['resistance_1'] + (atr * 0.5)  # Resistance-based SL
                
                levels = {
                    'signal': 'SELL',
                    'entry_1': entry_1,
                    'entry_2': entry_2,
                    'tp1': tp1,
                    'tp2': tp2,
                    'sl1': sl1,
                    'sl2': sl2,
                    'risk_reward_1': (entry_1 - tp1) / (sl1 - entry_1),
                    'risk_reward_2': (entry_1 - tp2) / (sl1 - entry_1)
                }
            
            return levels
            
        except Exception as e:
            print(f"❌ Entry levels calculation error: {e}")
            return {}
    
    def generate_analysis_reason(self, trend_analysis, momentum_analysis, ai_prediction, levels):
        """สร้างเหตุผลการวิเคราะห์"""
        reasons = []
        
        # Trend reasons
        if trend_analysis.get('overall_trend') == 'STRONG_BULLISH':
            reasons.append("📈 เทรนด์ขาขึ้นแรง - MA และ EMA เรียงตัวขาขึ้น")
        elif trend_analysis.get('overall_trend') == 'BULLISH':
            reasons.append("📈 เทรนด์ขาขึ้น - ราคาเหนือ MA หลัก")
        elif trend_analysis.get('overall_trend') == 'STRONG_BEARISH':
            reasons.append("📉 เทรนด์ขาลงแรง - MA และ EMA เรียงตัวขาลง")
        elif trend_analysis.get('overall_trend') == 'BEARISH':
            reasons.append("📉 เทรนด์ขาลง - ราคาต่ำกว่า MA หลัก")
        
        # Momentum reasons
        rsi = momentum_analysis.get('rsi', 50)
        if rsi > 70:
            reasons.append(f"⚠️ RSI Overbought ({rsi:.1f}) - แรงขายเพิ่ม")
        elif rsi < 30:
            reasons.append(f"💪 RSI Oversold ({rsi:.1f}) - แรงซื้อเพิ่ม")
        elif rsi > 60:
            reasons.append(f"📈 RSI Bullish ({rsi:.1f}) - momentum ขาขึ้น")
        elif rsi < 40:
            reasons.append(f"📉 RSI Bearish ({rsi:.1f}) - momentum ขาลง")
        
        # MACD reasons
        macd_status = momentum_analysis.get('macd_status', 'NEUTRAL')
        if macd_status == 'BULLISH':
            reasons.append("📈 MACD Bullish - เส้น MACD เหนือ Signal")
        elif macd_status == 'BEARISH':
            reasons.append("📉 MACD Bearish - เส้น MACD ต่ำกว่า Signal")
        
        # AI reasons
        confidence = ai_prediction.get('confidence', 0)
        if confidence > 0.8:
            reasons.append(f"🤖 AI มั่นใจสูง ({confidence:.1%}) - โมเดลแนะนำ {ai_prediction.get('signal', 'NEUTRAL')}")
        elif confidence > 0.6:
            reasons.append(f"🤖 AI มั่นใจปานกลาง ({confidence:.1%}) - โมเดลแนะนำ {ai_prediction.get('signal', 'NEUTRAL')}")
        
        # Risk/Reward reasons
        rr1 = levels.get('risk_reward_1', 0)
        if rr1 > 2:
            reasons.append(f"💰 Risk/Reward ดี (1:{rr1:.1f}) - คุ้มค่าการเสี่ยง")
        elif rr1 > 1.5:
            reasons.append(f"💰 Risk/Reward พอใช้ (1:{rr1:.1f})")
        
        return reasons
    
    def format_analysis_message(self, analysis_data):
        """จัดรูปแบบข้อความวิเคราะห์"""
        try:
            current_price = analysis_data.get('current_price', 0)
            trend = analysis_data.get('trend_analysis', {})
            momentum = analysis_data.get('momentum_analysis', {})
            ai_pred = analysis_data.get('ai_prediction', {})
            levels = analysis_data.get('entry_levels', {})
            reasons = analysis_data.get('reasons', [])
            
            signal = ai_pred.get('signal', 'NEUTRAL')
            confidence = ai_pred.get('confidence', 0)
            
            emoji = "🟢📈" if signal == "BUY" else "🔴📉" if signal == "SELL" else "🟡⚖️"
            action = "ซื้อ" if signal == "BUY" else "ขาย" if signal == "SELL" else "รอดู"
            
            message = f"""
₿ <b>BTC ANALYSIS REPORT</b> ₿

{emoji} <b>สัญญาณ: {action} ({signal})</b>
💰 <b>ราคาปัจจุบัน:</b> ${current_price:,.2f}
🤖 <b>AI Confidence:</b> {confidence:.1%}

📊 <b>TECHNICAL ANALYSIS:</b>
• <b>Trend:</b> {trend.get('overall_trend', 'NEUTRAL')}
• <b>RSI:</b> {momentum.get('rsi', 0):.1f} ({momentum.get('rsi_status', 'NEUTRAL')})
• <b>MACD:</b> {momentum.get('macd_status', 'NEUTRAL')}
• <b>Stochastic:</b> {momentum.get('stoch_status', 'NEUTRAL')}

📈 <b>PRICE MOMENTUM:</b>
• <b>1H:</b> {trend.get('price_change_1h', 0):+.2f}%
• <b>4H:</b> {trend.get('price_change_4h', 0):+.2f}%
• <b>24H:</b> {trend.get('price_change_24h', 0):+.2f}%
"""
            
            if levels:
                message += f"""
🎯 <b>ENTRY & EXIT LEVELS:</b>
• <b>Entry 1 (Market):</b> ${levels.get('entry_1', 0):,.2f}
• <b>Entry 2 (Level):</b> ${levels.get('entry_2', 0):,.2f}

• <b>TP1 (Conservative):</b> ${levels.get('tp1', 0):,.2f}
• <b>TP2 (Aggressive):</b> ${levels.get('tp2', 0):,.2f}

• <b>SL1 (Tight):</b> ${levels.get('sl1', 0):,.2f}
• <b>SL2 (Safe):</b> ${levels.get('sl2', 0):,.2f}

📊 <b>Risk/Reward:</b> 1:{levels.get('risk_reward_1', 0):.1f} | 1:{levels.get('risk_reward_2', 0):.1f}
"""
            
            if reasons:
                message += f"""
🔍 <b>ANALYSIS REASONS:</b>
"""
                for reason in reasons[:5]:  # แสดงแค่ 5 เหตุผลแรก
                    message += f"• {reason}\n"
            
            message += f"""
⏰ <b>เวลาวิเคราะห์:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>₿ BTC Analysis Bot - AI Powered</i>
            """.strip()
            
            return message
            
        except Exception as e:
            print(f"❌ Message formatting error: {e}")
            return "❌ Error formatting analysis message"
    
    def run_btc_analysis(self):
        """รันการวิเคราะห์ BTC แบบครบครัน"""
        print("₿ Starting BTC Comprehensive Analysis...")
        
        if not self.connect_mt5():
            return False
        
        # เทรน AI Model
        if not self.train_ai_model():
            print("⚠️ AI model training failed, continuing with technical analysis only")
        
        try:
            # ดึงข้อมูล H1 สำหรับวิเคราะห์หลัก
            df_h1 = self.get_btc_data(mt5.TIMEFRAME_H1, 500)
            if df_h1 is None:
                print("❌ Cannot get BTC data")
                return False
            
            df_h1 = self.calculate_technical_indicators(df_h1)
            if df_h1 is None:
                print("❌ Cannot calculate technical indicators")
                return False
            
            print("📊 Analyzing BTC market conditions...")
            
            # วิเคราะห์ต่างๆ
            current_price = df_h1['close'].iloc[-1]
            support_resistance = self.identify_support_resistance(df_h1)
            trend_analysis = self.analyze_trend(df_h1)
            momentum_analysis = self.analyze_momentum(df_h1)
            ai_prediction = self.make_ai_prediction()
            
            # กำหนดสัญญาณหลัก
            main_signal = ai_prediction.get('signal', 'NEUTRAL')
            if not main_signal or main_signal == 'NEUTRAL':
                # ใช้ technical analysis เป็นหลัก
                if trend_analysis.get('overall_trend') in ['STRONG_BULLISH', 'BULLISH']:
                    main_signal = 'BUY'
                elif trend_analysis.get('overall_trend') in ['STRONG_BEARISH', 'BEARISH']:
                    main_signal = 'SELL'
                else:
                    main_signal = 'NEUTRAL'
            
            # คำนวณ Entry levels
            entry_levels = self.calculate_entry_levels(df_h1, main_signal)
            
            # สร้างเหตุผล
            reasons = self.generate_analysis_reason(trend_analysis, momentum_analysis, ai_prediction, entry_levels)
            
            # รวมข้อมูลทั้งหมด
            analysis_data = {
                'current_price': current_price,
                'support_resistance': support_resistance,
                'trend_analysis': trend_analysis,
                'momentum_analysis': momentum_analysis,
                'ai_prediction': ai_prediction,
                'entry_levels': entry_levels,
                'reasons': reasons,
                'timestamp': datetime.now()
            }
            
            # จัดรูปแบบและส่งข้อความ
            message = self.format_analysis_message(analysis_data)
            
            print("📱 Sending analysis to Telegram...")
            success = self.send_telegram_message(message)
            
            if success:
                print("✅ BTC analysis sent successfully!")
                
                # แสดงสรุปใน console
                print(f"\n₿ BTC Analysis Summary:")
                print(f"   💰 Current Price: ${current_price:,.2f}")
                print(f"   📊 Signal: {main_signal}")
                print(f"   🤖 AI Confidence: {ai_prediction.get('confidence', 0):.1%}")
                print(f"   📈 Trend: {trend_analysis.get('overall_trend', 'NEUTRAL')}")
                print(f"   📊 RSI: {momentum_analysis.get('rsi', 0):.1f}")
                
                if entry_levels:
                    print(f"   🎯 TP1: ${entry_levels.get('tp1', 0):,.2f}")
                    print(f"   🛡️ SL1: ${entry_levels.get('sl1', 0):,.2f}")
                    print(f"   📊 R/R: 1:{entry_levels.get('risk_reward_1', 0):.1f}")
                
                return True
            else:
                print("❌ Failed to send analysis to Telegram")
                return False
                
        except Exception as e:
            print(f"❌ BTC analysis error: {e}")
            return False

def main():
    """ฟังก์ชันหลัก"""
    print("₿ BTC Analysis Bot - Comprehensive Technical Analysis")
    print("=" * 60)
    
    try:
        # สร้าง bot
        bot = BTCAnalysisBot()
        
        # รันการวิเคราะห์
        success = bot.run_btc_analysis()
        
        if success:
            print("\n🎉 BTC analysis completed successfully!")
        else:
            print("\n❌ BTC analysis failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    finally:
        try:
            mt5.shutdown()
            print("🔌 MT5 connection closed")
        except:
            pass

if __name__ == "__main__":
    main()