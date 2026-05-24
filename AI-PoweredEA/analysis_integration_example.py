#!/usr/bin/env python3
"""
ตัวอย่างการใช้งาน Enhanced Analysis System
แสดงวิธีการรวมระบบการวิเคราะห์เข้ากับ Trading Bot
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import MetaTrader5 as mt5

# Import the enhanced analysis system
from enhanced_analysis_system import EnhancedAnalysisSystem

class TradingBotWithAnalysis:
    """Trading Bot ที่มีระบบการวิเคราะห์และการเรียนรู้แบบครอบคลุม"""
    
    def __init__(self):
        # Initialize enhanced analysis system
        self.analysis_system = EnhancedAnalysisSystem()
        
        # Trading settings
        self.symbol = "GOLDm#"
        self.timeframe = mt5.TIMEFRAME_M1
        
        print("🚀 Trading Bot with Enhanced Analysis System initialized")
        print("📊 Analysis and Learning features enabled")
    
    def check_signal_with_comprehensive_analysis(self):
        """ตรวจสอบสัญญาณพร้อมการวิเคราะห์ครอบคลุม"""
        try:
            print("\n" + "="*70)
            print("🎯 SIGNAL CHECK WITH COMPREHENSIVE ANALYSIS")
            print("="*70)
            
            # 1. Get market data
            df = self.get_market_data()
            if df is None:
                print("❌ No market data available")
                return None
            
            # 2. Generate comprehensive analysis report
            analysis_report = self.analysis_system.generate_comprehensive_analysis_report(df)
            
            # 3. Display analysis report
            self.analysis_system.display_analysis_report(analysis_report)
            
            # 4. Check for trading signals
            signal = self.check_trading_signals(df)
            
            # 5. If signal found, display signal analysis
            if signal:
                self.analysis_system.display_signal_analysis_summary(signal, df)
                
                # Store prediction data for learning
                self.analysis_system.store_prediction_data(
                    signal.get('signal', 'UNKNOWN'),
                    signal.get('confidence', 0.5),
                    df.iloc[-1].to_dict()
                )
                
                # 6. Update and display learning progress
                self.analysis_system.update_learning_progress_display()
            else:
                print("\n📊 NO TRADING SIGNAL GENERATED")
                print("   Waiting for better market conditions...")
            
            print("\n" + "="*70)
            return signal
            
        except Exception as e:
            print(f"❌ Signal check with analysis error: {e}")
            return None
    
    def get_market_data(self):
        """ดึงข้อมูลตลาดและคำนวณ indicators"""
        try:
            # Mock data for demonstration - replace with actual MT5 data
            dates = pd.date_range(start='2024-01-01', periods=100, freq='1min')
            
            # Generate sample OHLC data
            np.random.seed(42)
            base_price = 2000.0
            prices = []
            
            for i in range(100):
                if i == 0:
                    price = base_price
                else:
                    change = np.random.normal(0, 0.5)  # Random price change
                    price = prices[-1] + change
                prices.append(price)
            
            df = pd.DataFrame({
                'time': dates,
                'open': prices,
                'high': [p + abs(np.random.normal(0, 0.3)) for p in prices],
                'low': [p - abs(np.random.normal(0, 0.3)) for p in prices],
                'close': prices,
                'tick_volume': [np.random.randint(100, 1000) for _ in range(100)]
            })
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            return df
            
        except Exception as e:
            print(f"❌ Market data error: {e}")
            return None
    
    def calculate_indicators(self, df):
        """คำนวณ technical indicators"""
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
            
            # EMAs
            df['ema_10'] = df['close'].ewm(span=10).mean()
            df['ema_20'] = df['close'].ewm(span=20).mean()
            
            # Bollinger Bands
            bb_middle = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = bb_middle + (bb_std * 2)
            df['bb_lower'] = bb_middle - (bb_std * 2)
            df['bb_width'] = df['bb_upper'] - df['bb_lower']
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # BB Touch Detection
            df['bb_upper_touch'] = (df['high'] >= df['bb_upper'] * 0.99).astype(int)
            df['bb_lower_touch'] = (df['low'] <= df['bb_lower'] * 1.01).astype(int)
            
            # ZigZag (simplified)
            df['zigzag_peak'] = 0
            df['zigzag_trough'] = 0
            
            # Add some peaks and troughs for demonstration
            for i in range(5, len(df)-5, 20):
                if np.random.random() > 0.5:
                    df.loc[df.index[i], 'zigzag_peak'] = 1
                else:
                    df.loc[df.index[i], 'zigzag_trough'] = 1
            
            # Momentum
            df['momentum'] = df['close'] / df['close'].shift(5) - 1
            df['momentum_strength'] = abs(df['momentum'])
            df['momentum_acceleration'] = df['momentum'] - df['momentum'].shift(1)
            
            # ATR
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            df['atr'] = df['true_range'].rolling(window=14).mean()
            
            # Trend strength
            df['trend_strength'] = abs(df['ema_10'] - df['ema_20']) / df['atr']
            
            # Fill NaN values
            df = df.fillna(method='bfill').fillna(method='ffill')
            
            return df
            
        except Exception as e:
            print(f"❌ Indicator calculation error: {e}")
            return df
    
    def check_trading_signals(self, df):
        """ตรวจสอบสัญญาณการเทรด"""
        try:
            latest = df.iloc[-1]
            
            # Simple signal logic for demonstration
            signal = None
            
            # SELL Signal: RSI > 70 AND BB Upper Touch
            if (latest['rsi'] > 70 and 
                latest['bb_upper_touch'] == 1 and 
                latest['bb_position'] > 0.8):
                
                signal = {
                    'signal': 'SELL',
                    'confidence': 0.75,
                    'reasons': [
                        'RSI Overbought (>70)',
                        'BB Upper Band Touch',
                        'BB Position > 80%'
                    ],
                    'ai_signal': 'SELL',
                    'ai_confidence': 0.72
                }
            
            # BUY Signal: RSI < 30 AND BB Lower Touch
            elif (latest['rsi'] < 30 and 
                  latest['bb_lower_touch'] == 1 and 
                  latest['bb_position'] < 0.2):
                
                signal = {
                    'signal': 'BUY',
                    'confidence': 0.78,
                    'reasons': [
                        'RSI Oversold (<30)',
                        'BB Lower Band Touch',
                        'BB Position < 20%'
                    ],
                    'ai_signal': 'BUY',
                    'ai_confidence': 0.76
                }
            
            return signal
            
        except Exception as e:
            print(f"❌ Signal check error: {e}")
            return None
    
    def run_continuous_analysis(self, iterations=5):
        """รันการวิเคราะห์อย่างต่อเนื่อง"""
        try:
            print("\n🔄 STARTING CONTINUOUS ANALYSIS MODE")
            print(f"📊 Running {iterations} analysis cycles...")
            
            for i in range(iterations):
                print(f"\n🔄 Analysis Cycle {i+1}/{iterations}")
                print("-" * 50)
                
                # Check signal with comprehensive analysis
                signal = self.check_signal_with_comprehensive_analysis()
                
                if signal:
                    print(f"✅ Signal Generated: {signal['signal']} (Confidence: {signal['confidence']:.1%})")
                else:
                    print("📊 No signal - Market analysis completed")
                
                # Simulate some time passing
                import time
                time.sleep(1)  # 1 second delay for demonstration
            
            print("\n🏁 CONTINUOUS ANALYSIS COMPLETED")
            print("📈 Analysis Summary:")
            print(f"   Total Cycles: {iterations}")
            print(f"   Predictions Stored: {len(self.analysis_system.recent_predictions)}")
            print(f"   Learning Trend: {self.analysis_system.learning_trend}")
            
        except Exception as e:
            print(f"❌ Continuous analysis error: {e}")

def main():
    """ฟังก์ชันหลักสำหรับทดสอบระบบ"""
    print("🚀 ENHANCED ANALYSIS SYSTEM DEMONSTRATION")
    print("="*60)
    
    # Initialize trading bot with analysis
    bot = TradingBotWithAnalysis()
    
    # Run single analysis
    print("\n1️⃣ SINGLE SIGNAL CHECK WITH ANALYSIS")
    signal = bot.check_signal_with_comprehensive_analysis()
    
    # Run continuous analysis
    print("\n2️⃣ CONTINUOUS ANALYSIS MODE")
    bot.run_continuous_analysis(iterations=3)
    
    print("\n✅ DEMONSTRATION COMPLETED")
    print("💡 This shows how comprehensive analysis and learning")
    print("   are displayed every time signals are checked!")

if __name__ == "__main__":
    main()
