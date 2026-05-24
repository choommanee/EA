#!/usr/bin/env python3
"""
Working Gold Scalping Trader - ระบบที่ทำงานได้จริงพร้อม AI Integration
แก้ไขปัญหา: ไม่ออกสัญญาณ, Risk/Reward, Overtrading
เพิ่ม: AI Learning Pipeline, Model Management, Performance Monitoring
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

# Add Python folder to path for AI components
sys.path.append('Python')

# Import AI System Components
try:
    from Python.ai_system_integration import AISystemIntegration
    from Python.ai_learning_pipeline_integration import AILearningPipelineIntegration, SignalData, SignalOutcome
    from Python.model_manager import ModelManager, ModelStatus, ModelType
    from Python.performance_monitor import PerformanceMonitor
    from Python.model_evaluator import ModelEvaluator
    from Python.learning_metrics_collector import LearningMetricsCollector
    from Python.learning_notification_system import LearningNotificationSystem
    from Python.learning_configuration import LearningConfiguration
    from Python.error_handling_integration import ErrorHandlingIntegration
    from Python.learning_data_collector import LearningDataCollector
    AI_COMPONENTS_AVAILABLE = True
    print("✅ All AI components loaded successfully")
except ImportError as e:
    AI_COMPONENTS_AVAILABLE = False
    print(f"⚠️ AI components not available: {e}")
    print("🔄 Running in basic mode without advanced AI features")

class WorkingGoldScalpingTrader:
    """Working version ของ Gold Scalping Trader ที่ออกสัญญาณได้จริง"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        # Telegram settings
        self.telegram_token = telegram_token or "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
        self.chat_id = chat_id or "-1002852894581"
        
        # Timeframe settings - เปลี่ยนเป็น M5 เพื่อลด noise และเห็น trend ชัดขึ้น
        self.timeframe = mt5.TIMEFRAME_M5       # Main analysis timeframe
        self.main_timeframe = mt5.TIMEFRAME_M5  # Main timeframe (alias for compatibility)
        self.signal_timeframe = mt5.TIMEFRAME_M5 # Signal generation timeframe
        self.trend_timeframe = mt5.TIMEFRAME_M15 # Higher timeframe for trend confirmation
        
        # Trading settings
        self.symbol = "GOLDm#"
        self.base_lot_size = 0.2
        
        # ADAPTIVE Risk Management - ปรับปรุง SL ให้เหมาะสมกับความผันผวนของตลาด
        self.use_adaptive_sl = True     # ใช้ SL แบบปรับตัวตาม ATR และ BB Width
        self.min_sl_points = 400        # Minimum SL (40 pips) - เพิ่มขึ้น
        self.max_sl_points = 600        # Maximum SL (60 pips) - เพิ่มขึ้น
        self.tp_risk_reward_ratio = 2.0 # Risk/Reward ratio for TP calculation
        self.sl_safety_buffer = 200     # Safety buffer added to calculated SL - เพิ่มขึ้น
        self.atr_sl_multiplier = 8.0    # ATR multiplier for SL calculation - เพิ่มขึ้น
        self.bb_sl_multiplier = 2.5     # BB width multiplier for SL (250%) - เพิ่มขึ้น
        
        # Volatility thresholds for adaptive SL
        self.min_volatility = 0.4  # Minimum ATR for trading
        self.max_volatility = 1.8  # Maximum ATR for trading
        
        # OPTIMIZED SL/TP Settings - เพิ่ม SL ลด TP เพื่อลด SL hits
        self.sl_atr_multiplier = 4.0        # SL = 4.0x ATR (เพิ่มจาก 2.5)
        self.tp_atr_multiplier = 6.0        # TP = 6.0x ATR (เพิ่มจาก 5.0)
        self.bb_width_sl_factor = 0.8       # SL = 80% ของ BB Width (เพิ่มจาก 60%)
        self.bb_width_tp_factor = 1.0       # TP = 100% ของ BB Width (ลดจาก 120%)
        self.min_sl_pips = 60.0             # SL ขั้นต่ำ (เพิ่มจาก 40)
        self.max_sl_pips = 80.0             # SL สูงสุด (เพิ่มจาก 60)
        self.min_tp_pips = 80.0             # TP ขั้นต่ำ (คงเดิม)
        self.max_tp_pips = 120.0            # TP สูงสุด (คงเดิม)
        self.sl_safety_buffer = 30.0        # เพิ่ม buffer 30 pips (เพิ่มจาก 20)
        self.risk_reward_ratio = 1.5        # TP = 1.5x SL (ลดจาก 2.0)
        self.confidence_threshold = 0.85  # Minimum confidence for signals (เพิ่มจาก 75%)
        
        # WORKING Strategy Settings - ปรับให้ออกสัญญาณง่ายขึ้น
        self.enable_auto_trading = True
        self.scalping_mode = True
        self.quick_exit_enabled = True
        self.breakeven_points = 80       # ลด breakeven
        self.partial_close_points = 120  # ลด partial close
        
        # WORKING Timing settings - ลดข้อจำกัด
        self.max_hold_minutes = 20          # ลดเวลาถือ
        self.avoid_news_minutes = 15
        self.max_spread = 30                # Maximum spread in points
        self.signal_interval_seconds = 30   # Check signals every 30 seconds
        
        # STRICT Market condition filters - เข้มงวดมากขึ้นเพื่อลด SL hits
        self.min_trend_strength = 0.7   # เพิ่มขึ้นเพื่อสัญญาณที่แข็งแกร่งมาก
        self.trend_strength_threshold = 0.6 # เพิ่มขึ้นอีก
        
        # ENHANCED TREND PROTECTION - ป้องกันการเทรดย้อนเทรนแบบเข้มงวด
        self.enable_trend_protection = True     # เปิดการป้องกันเทรน
        self.strong_trend_threshold = 0.8       # เทรนแรงเมื่อ trend_strength > 0.8 (ลดลงเพื่อป้องกันมากขึ้น)
        self.max_consecutive_candles = 2        # ไม่เทรดถ้ามี candles ติดต่อกันเกิน 2 แท่ง (เข้มงวดขึ้น)
        self.trend_momentum_limit = 0.002       # ไม่เทรดถ้า momentum แรงเกิน 0.2% (เข้มงวดขึ้น)
        self.ema_separation_limit = 0.4         # ไม่เทรดถ้า EMA ห่างกันเกิน 0.4 USD (เข้มงวดขึ้น)
        
        # AI components
        self.model = None
        self.scaler = StandardScaler()
        
        # Position Management
        self.max_positions = 3              # Maximum concurrent positions
        self.max_daily_trades = 30          # Maximum trades per day
        self.daily_trades = 0               # Daily trade counter (bot trades only)
        self.last_trade_time = None         # Track last trade time
        self.orders_placed = []             # Track placed orders
        
        # Bot Trade Identification
        self.bot_magic_number = 987654321   # Unique magic number for bot trades
        self.bot_comment_prefix = "AI-BOT"  # Prefix for bot trade comments
        self.manual_trades_detected = 0     # Counter for manual trades (for info only)
        
        # Signal cooldown system
        self.signal_cooldown_seconds = 60   # Cooldown between signals
        self.last_signal_time = None        # Track last signal time
        self.duplicate_threshold = 0.01     # 1% price difference for duplicate detection
        
        # Martingale Recovery System
        self.enable_martingale_recovery = True  # เปิดระบบแก้ไขเมื่อเข้าผิดทาง
        self.martingale_lot_sequence = [0.1, 0.2, 0.4]  # Progressive lot sizing
        self.martingale_sl_multiplier = 3.0     # SL = latest_entry_price + (3x buffer)
        self.recovery_positions = {}            # Track recovery positions by symbol
        self.max_recovery_levels = 3            # Maximum recovery levels
        
        # TREND FOLLOWING Settings
        self.enable_trend_following = True   # เปิดการเทรดตามเทรน
        self.trend_following_threshold = 0.8 # เทรนชัดเจนเมื่อ trend_strength > 0.8
        self.trend_tp_extension = 1.5        # ขยาย TP เป็น 1.5x เมื่อเทรดตามเทรน
        self.trend_sl_buffer = 1.2           # เพิ่ม SL buffer 20% เมื่อเทรดตามเทรน
        
        # DYNAMIC TP/SL Management
        self.enable_dynamic_tpsl = True      # เปิดการปรับ TP/SL แบบ dynamic
        self.profit_trail_threshold = 30     # เริ่ม trail เมื่อกำไร 30 pips
        self.trail_step = 10                 # เลื่อน SL ทีละ 10 pips
        self.tp_extension_step = 20          # ขยาย TP ทีละ 20 pips
        
        # AI Dynamic SL Management
        self.enable_ai_sl_management = True
        self.ai_sl_trail_threshold = 0.8    # AI confidence threshold for trailing SL
        self.ai_breakeven_confidence = 0.85  # Move to breakeven when AI confidence high
        
        # Trading data
        self.signals_sent = []
        self.orders_placed = []
        self.daily_trades = 0
        self.daily_profit = 0.0
        self.last_trade_time = None
        
        # Signal balance tracking
        self.daily_buy_signals = 0
        self.daily_sell_signals = 0
        
        # AI Learning Data Storage
        self.learning_data = []
        self.trade_results = []
        self.signal_history = []
        self.market_conditions_history = []
        
        # Performance tracking
        self.performance_data = {
            'total_signals': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'avg_profit_per_trade': 0.0,
            'risk_reward_ratio': 1.5,
            'current_streak': 0,
            'bb_touch_accuracy': 0.0,
            'zigzag_accuracy': 0.0,
            'ai_prediction_accuracy': 0.0,
            'false_signal_rate': 0.0
        }
        
        # AI Learning Parameters - Continuous Learning
        self.learning_enabled = True
        self.min_learning_samples = 30  # ลดลงเพื่อเริ่ม learning เร็วขึ้น
        self.retrain_frequency = 10     # retrain ทุก 10 trades (บ่อยขึ้น)
        self.learning_features = [
            'rsi', 'macd', 'ema_10', 'ema_20', 'bb_position', 
            'momentum', 'momentum_strength', 'momentum_acceleration', 'atr', 'volume_ratio', 'trend_strength',
            'bb_upper_touch', 'bb_lower_touch', 'zigzag_peak', 'zigzag_trough',
            'consecutive_up', 'consecutive_down', 'candle_body_pct',
            'hour_of_day', 'day_of_week', 'market_session'
        ]
        
        # Continuous Learning Tracking
        self.learning_sessions = []
        self.model_versions = []
        self.current_model_version = 0
        self.last_learning_report = None
        self.learning_improvements = []
        
        # Real-time Learning Metrics
        self.real_time_accuracy = 0.0
        self.recent_predictions = []  # เก็บ predictions ล่าสุด 20 ครั้ง
        self.learning_trend = "IMPROVING"  # IMPROVING, STABLE, DECLINING
        
        # Analysis and Learning Display Data
        self.analysis_history = []
        self.learning_improvements = []
        self.signal_analysis_cache = {}
        self.market_condition_analysis = {}
        self.ai_learning_insights = []
        
        # Initialize AI System Components
        self.ai_system = None
        self.learning_pipeline = None
        self.model_manager = None
        self.performance_monitor = None
        self.model_evaluator = None
        self.metrics_collector = None
        self.notification_system = None
        self.error_handler = None
        self.data_collector = None
        
        # Initialize AI components if available
        if AI_COMPONENTS_AVAILABLE:
            self._initialize_ai_components()
        
        print("⚡ Enhanced Gold Scalping Trader initialized")
        print(f"📏 ADAPTIVE SL/TP: ATR + BB Width based (2.5x ATR, 60% BB Width)")
        print(f"🎯 Risk/Reward Ratio: 1:{self.tp_risk_reward_ratio:.1f} (TP = {self.tp_risk_reward_ratio}x SL)")
        print(f"🎯 Confidence Threshold: {self.confidence_threshold:.0%} (เข้มงวดขึ้น)")
        print(f"🛡️ SL Range: {self.min_sl_points/10:.1f}-{self.max_sl_points/10:.1f} pips (ขยายช่วง)")
        print(f"🔧 Safety Buffer: +{self.sl_safety_buffer/10:.1f} pips")
        print(f"💼 Max Positions: {self.max_positions} (ควบคุมความเสี่ยง)")
        print(f"📊 Max Daily Trades: {self.max_daily_trades} (เน้นคุณภาพ)")
        print(f"🚨 Trend Protection: {'ON' if self.enable_trend_protection else 'OFF'}")
        if self.enable_trend_protection:
            print(f"   📊 Strong Trend Threshold: {self.strong_trend_threshold}")
            print(f"   📈 Max Consecutive Candles: {self.max_consecutive_candles}")
            print(f"   ⚡ Trend Momentum Limit: {self.trend_momentum_limit}")
            print(f"   📏 EMA Separation Limit: ${self.ema_separation_limit}")
        print(f"🎯 Trend Following: {'ENABLED' if self.enable_trend_following else 'DISABLED'}")
        if self.enable_trend_following:
            print(f"   📈 Trend Threshold: {self.trend_following_threshold}")
            print(f"   🎯 TP Extension: {self.trend_tp_extension}x")
            print(f"   🛡️ SL Buffer: {self.trend_sl_buffer}x")
        print(f"⚡ Dynamic TP/SL: {'ENABLED' if self.enable_dynamic_tpsl else 'DISABLED'}")
        if self.enable_dynamic_tpsl:
            print(f"   💰 Trail Threshold: {self.profit_trail_threshold} pips")
            print(f"   📏 Trail Step: {self.trail_step} pips")
            print(f"   🎯 TP Extension: {self.tp_extension_step} pips")
        
        # Show AI system status
        if AI_COMPONENTS_AVAILABLE and self.ai_system:
            print(f"🤖 AI System: ACTIVE")
            print(f"📊 Learning Pipeline: {'ENABLED' if self.learning_pipeline else 'DISABLED'}")
            print(f"🎯 Model Manager: {'ACTIVE' if self.model_manager else 'INACTIVE'}")
            print(f"📈 Performance Monitor: {'RUNNING' if self.performance_monitor else 'STOPPED'}")
        else:
            print(f"🤖 AI System: BASIC MODE (Advanced features disabled)")
        
        # Initialize analysis tracking
        self.initialize_analysis_tracking()
    
    def initialize_analysis_tracking(self):
        """Initialize analysis tracking variables"""
        try:
            # Analysis tracking
            self.analysis_history = []
            self.recent_predictions = []
            self.learning_trend = "IMPROVING"
            self.current_model_version = 1
            
            # Performance tracking
            self.total_signals_generated = 0
            self.successful_predictions = 0
            self.failed_predictions = 0
            
            # Learning metrics
            self.learning_metrics = {
                'accuracy_trend': [],
                'confidence_scores': [],
                'market_conditions': [],
                'signal_outcomes': []
            }
            
            print("✅ Analysis tracking initialized")
            
        except Exception as e:
            print(f"❌ Analysis tracking initialization error: {e}")
    
    def _initialize_ai_components(self):
        """Initialize all AI system components"""
        try:
            print("🔄 Initializing AI system components...")
            
            # Initialize AI System Integration
            self.ai_system = AISystemIntegration(
                db_path="Data/forex_trading.db",
                models_directory="Models"
            )
            
            # Initialize Learning Pipeline
            self.learning_pipeline = AILearningPipelineIntegration(
                db_path="Data/ai_learning_integration.db"
            )
            
            # Initialize Model Manager
            self.model_manager = ModelManager(
                db_path="Data/forex_trading.db",
                models_directory="Models"
            )
            
            # Initialize Performance Monitor
            self.performance_monitor = PerformanceMonitor(
                db_path="Data/forex_trading.db"
            )
            
            # Initialize Model Evaluator
            self.model_evaluator = ModelEvaluator(
                db_path="Data/forex_trading.db"
            )
            
            # Initialize Metrics Collector
            self.metrics_collector = LearningMetricsCollector(
                db_path="Data/ai_learning_integration.db"
            )
            
            # Initialize Notification System
            self.notification_system = LearningNotificationSystem()
            
            # Initialize Error Handler
            self.error_handler = ErrorHandlingIntegration(
                db_path="Data/forex_trading.db"
            )
            
            # Initialize Data Collector
            self.data_collector = LearningDataCollector(
                db_path="Data/ai_learning_integration.db"
            )
            
            # Start AI system
            if hasattr(self.ai_system, 'start'):
                self.ai_system.start()
                
            return True
            
        except Exception as e:
            print(f"❌ AI components initialization error: {e}")
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
    
    def calculate_simple_indicators(self, df):
        """คำนวณ indicators รวม Bollinger Bands + ZigZag + AI features"""
        try:
            if df is None or len(df) < 30:
                return None
            
            # Simple RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Simple MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Simple EMAs
            df['ema_10'] = df['close'].ewm(span=10).mean()
            df['ema_20'] = df['close'].ewm(span=20).mean()
            
            # Bollinger Bands - เฉพาะ Upper และ Lower เท่านั้น (20 period, 2 std)
            bb_middle = df['close'].rolling(window=20).mean()  # ใช้แค่คำนวณ ไม่เก็บ
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = bb_middle + (bb_std * 2)
            df['bb_lower'] = bb_middle - (bb_std * 2)
            df['bb_width'] = df['bb_upper'] - df['bb_lower']
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Bollinger Band Touch Detection - เข้มงวดขึ้น (95-100% ของ BB)
            df['bb_upper_touch'] = (df['high'] >= df['bb_upper'] * 0.95).astype(int)
            df['bb_lower_touch'] = (df['low'] <= df['bb_lower'] * 1.05).astype(int)
            
            # BB Close Touch - ต้องแตะจริงๆ (98-100%)
            df['bb_upper_close_touch'] = (df['close'] >= df['bb_upper'] * 0.98).astype(int)
            df['bb_lower_close_touch'] = (df['close'] <= df['bb_lower'] * 1.02).astype(int)
            
            # ZigZag Calculation
            df = self.calculate_zigzag_peaks_troughs(df)
            
            # Price momentum - หลายระยะเวลา
            df['momentum'] = df['close'] / df['close'].shift(5) - 1
            df['momentum_3'] = df['close'] / df['close'].shift(3) - 1
            df['momentum_1'] = df['close'] / df['close'].shift(1) - 1
            
            # Momentum strength และ acceleration
            df['momentum_strength'] = abs(df['momentum'])
            df['momentum_acceleration'] = df['momentum'] - df['momentum'].shift(1)
            
            # Candle strength analysis
            df['candle_body_pct'] = abs(df['close'] - df['open']) / (df['high'] - df['low'])
            df['candle_upper_shadow'] = df['high'] - df[['close', 'open']].max(axis=1)
            df['candle_lower_shadow'] = df[['close', 'open']].min(axis=1) - df['low']
            
            # Consecutive candles in same direction
            df['candle_direction'] = np.where(df['close'] > df['open'], 1, -1)
            df['consecutive_up'] = 0
            df['consecutive_down'] = 0
            
            # คำนวณ consecutive candles
            for i in range(1, len(df)):
                if df['candle_direction'].iloc[i] == 1:  # Up candle
                    if df['candle_direction'].iloc[i-1] == 1:
                        df.loc[df.index[i], 'consecutive_up'] = df['consecutive_up'].iloc[i-1] + 1
                    else:
                        df.loc[df.index[i], 'consecutive_up'] = 1
                else:  # Down candle
                    if df['candle_direction'].iloc[i-1] == -1:
                        df.loc[df.index[i], 'consecutive_down'] = df['consecutive_down'].iloc[i-1] + 1
                    else:
                        df.loc[df.index[i], 'consecutive_down'] = 1
            
            # ATR
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = np.abs(df['high'] - df['close'].shift())
            df['low_close'] = np.abs(df['low'] - df['close'].shift())
            df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            df['atr'] = df['true_range'].rolling(window=14).mean()
            
            # Volume analysis
            df['volume_sma'] = df['tick_volume'].rolling(window=10).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
            
            # Trend strength
            df['trend_strength'] = abs(df['ema_10'] - df['ema_20']) / df['atr']
            
            return df
            
        except Exception as e:
            print(f"❌ Indicator calculation error: {e}")
            return None

    def calculate_zigzag_peaks_troughs(self, df):
        """คำนวณ ZigZag peaks และ troughs"""
        try:
            if df is None or len(df) < 10:
                return df
            
            # Simple ZigZag calculation
            df['zigzag_peak'] = 0
            df['zigzag_trough'] = 0
            
            # Find local peaks and troughs
            for i in range(2, len(df) - 2):
                # Peak detection
                if (df['high'].iloc[i] > df['high'].iloc[i-1] and 
                    df['high'].iloc[i] > df['high'].iloc[i+1] and
                    df['high'].iloc[i] > df['high'].iloc[i-2] and 
                    df['high'].iloc[i] > df['high'].iloc[i+2]):
                    df.loc[df.index[i], 'zigzag_peak'] = 1
                
                # Trough detection
                if (df['low'].iloc[i] < df['low'].iloc[i-1] and 
                    df['low'].iloc[i] < df['low'].iloc[i+1] and
                    df['low'].iloc[i] < df['low'].iloc[i-2] and 
                    df['low'].iloc[i] < df['low'].iloc[i+2]):
                    df.loc[df.index[i], 'zigzag_trough'] = 1
            
            return df
            
        except Exception as e:
            print(f"❌ ZigZag calculation error: {e}")
            # Add default columns if calculation fails
            df['zigzag_peak'] = 0
            df['zigzag_trough'] = 0
            return df

    def get_simple_ai_prediction(self, df):
        """Simple AI prediction สำหรับ SL/TP calculation"""
        try:
            if df is None or len(df) < 10:
                return 'HOLD', 0.5
            
            latest = df.iloc[-1]
            
            # Simple prediction based on RSI and EMA trend
            if latest['rsi'] < 30 and latest['ema_10'] > latest['ema_20']:
                return 'BUY', 0.7
            elif latest['rsi'] > 70 and latest['ema_10'] < latest['ema_20']:
                return 'SELL', 0.7
            elif latest['rsi'] < 40 and latest['ema_10'] > latest['ema_20']:
                return 'BUY', 0.6
            elif latest['rsi'] > 60 and latest['ema_10'] < latest['ema_20']:
                return 'SELL', 0.6
            else:
                return 'HOLD', 0.5
                
        except Exception as e:
            print(f"❌ Simple AI prediction error: {e}")
            return 'HOLD', 0.5

    def calculate_adaptive_sl_tp(self, df, signal, ai_signal, ai_confidence):
        """คำนวณ SL/TP แบบ adaptive ตาม market conditions"""
        try:
            if df is None or len(df) < 10:
                return self.min_sl_points, self.min_sl_points * 2
            
            latest = df.iloc[-1]
            
            # Base SL/TP from ATR and BB Width
            atr = latest.get('atr', 0.5)
            bb_upper = latest.get('bb_upper', 0)
            bb_lower = latest.get('bb_lower', 0)
            bb_width = abs(bb_upper - bb_lower) if bb_upper and bb_lower else atr
            
            # Calculate base SL from ATR (more conservative)
            base_sl_points = max(self.min_sl_points, int(atr * 100 * 1.5))  # 1.5x ATR
            
            # Adjust based on BB Width
            if bb_width > 0:
                bb_sl_points = max(self.min_sl_points, int(bb_width * 100 * 0.8))  # 80% of BB width
                sl_points = min(base_sl_points, bb_sl_points)  # Use smaller of the two
            else:
                sl_points = base_sl_points
            
            # Adjust based on AI confidence
            if ai_confidence > 0.8:
                sl_points = int(sl_points * 0.9)  # Tighter SL for high confidence
            elif ai_confidence < 0.6:
                sl_points = int(sl_points * 1.2)  # Wider SL for low confidence
            
            # Adjust based on trend strength
            trend_strength = latest.get('trend_strength', 0.5)
            if trend_strength > 0.8:  # Strong trend
                tp_points = int(sl_points * 2.5)  # Higher TP for trend following
            else:
                tp_points = int(sl_points * 2.0)  # Standard TP
            
            # Apply limits
            sl_points = max(self.min_sl_points, min(sl_points, self.max_sl_points))
            tp_points = max(sl_points * 1.5, min(tp_points, self.max_sl_points * 3))
            
            print(f"📊 Adaptive SL/TP:")
            print(f"   ATR: {atr:.3f}, BB Width: {bb_width:.3f}")
            print(f"   AI Confidence: {ai_confidence:.1%}")
            print(f"   Trend Strength: {trend_strength:.2f}")
            print(f"   SL: {sl_points} points, TP: {tp_points} points")
            print(f"   Risk/Reward: 1:{tp_points/sl_points:.1f}")
            
            return sl_points, tp_points
            
        except Exception as e:
            print(f"❌ Adaptive SL/TP calculation error: {e}")
            return self.min_sl_points, self.min_sl_points * 2
    
    def get_higher_timeframe_trend(self):
        """ตรวจสอบเทรนจาก M15 timeframe เพื่อยืนยันทิศทาง"""
        try:
            df_m15 = self.get_gold_data(self.trend_timeframe, 50)
            if df_m15 is None or len(df_m15) < 20:
                return "NEUTRAL", 0.0, "No M15 data"
            
            # คำนวณ EMA สำหรับ M15
            df_m15['ema_10'] = df_m15['close'].ewm(span=10).mean()
            df_m15['ema_20'] = df_m15['close'].ewm(span=20).mean()
            df_m15['ema_50'] = df_m15['close'].ewm(span=50).mean()
            
            latest = df_m15.iloc[-1]
            prev_10 = df_m15.iloc[-11:-1]
            
            # ตรวจสอบ EMA alignment
            ema_bullish = latest['ema_10'] > latest['ema_20'] > latest['ema_50']
            ema_bearish = latest['ema_10'] < latest['ema_20'] < latest['ema_50']
            
            # คำนวณ trend strength
            ema_separation = abs(latest['ema_10'] - latest['ema_50']) / latest['close']
            price_vs_ema = (latest['close'] - latest['ema_20']) / latest['close']
            
            # ตรวจสอบ consecutive candles
            recent_closes = df_m15['close'].iloc[-5:].values
            up_candles = sum(1 for i in range(1, len(recent_closes)) if recent_closes[i] > recent_closes[i-1])
            down_candles = sum(1 for i in range(1, len(recent_closes)) if recent_closes[i] < recent_closes[i-1])
            
            if ema_bullish and price_vs_ema > 0.001 and up_candles >= 3:
                return "STRONG_UP", ema_separation, f"M15 Strong Uptrend: EMA aligned, {up_candles}/4 up candles"
            elif ema_bearish and price_vs_ema < -0.001 and down_candles >= 3:
                return "STRONG_DOWN", ema_separation, f"M15 Strong Downtrend: EMA aligned, {down_candles}/4 down candles"
            elif latest['ema_10'] > latest['ema_20']:
                return "UP", ema_separation, "M15 Uptrend"
            elif latest['ema_10'] < latest['ema_20']:
                return "DOWN", ema_separation, "M15 Downtrend"
            else:
                return "NEUTRAL", ema_separation, "M15 Sideways"
                
        except Exception as e:
            print(f"❌ M15 trend analysis error: {e}")
            return "NEUTRAL", 0.0, "M15 analysis error"

    def detect_strong_trend(self, df):
        """ตรวจสอบเทรนแรง - ป้องกันการเทรดย้อนเทรน"""
        try:
            if df is None or len(df) < 20:
                return False, "No trend data", "NEUTRAL"
            
            latest = df.iloc[-1]
            prev_5 = df.iloc[-6:-1]  # 5 candles ก่อนหน้า
            
            # 1. ตรวจสอบ EMA separation (ระยะห่างระหว่าง EMA)
            ema_separation = abs(latest['ema_10'] - latest['ema_20'])
            if ema_separation > self.ema_separation_limit:
                trend_direction = "UP" if latest['ema_10'] > latest['ema_20'] else "DOWN"
                return True, f"Strong EMA separation: ${ema_separation:.2f}", trend_direction
            
            # 2. ตรวจสอบ Trend Strength
            if latest['trend_strength'] > self.strong_trend_threshold:
                trend_direction = "UP" if latest['ema_10'] > latest['ema_20'] else "DOWN"
                return True, f"High trend strength: {latest['trend_strength']:.2f}", trend_direction
            
            # 3. ตรวจสอบ Momentum แรง
            if latest['momentum_strength'] > self.trend_momentum_limit:
                trend_direction = "UP" if latest['momentum'] > 0 else "DOWN"
                return True, f"Strong momentum: {latest['momentum_strength']:.4f}", trend_direction
            
            # 4. ตรวจสอบ Consecutive Candles
            if latest['consecutive_up'] > self.max_consecutive_candles:
                return True, f"Too many up candles: {latest['consecutive_up']}", "UP"
            
            if latest['consecutive_down'] > self.max_consecutive_candles:
                return True, f"Too many down candles: {latest['consecutive_down']}", "DOWN"
            
            # 5. ตรวจสอบ ATR สูงเกินไป (ตลาดผันผวนมาก)
            if latest['atr'] > 1.5:
                return True, f"High volatility ATR: {latest['atr']:.3f}", "VOLATILE"
            
            # 6. ตรวจสอบ RSI extreme levels
            if latest['rsi'] > 80 or latest['rsi'] < 20:
                direction = "OVERBOUGHT" if latest['rsi'] > 80 else "OVERSOLD"
                return True, f"RSI extreme: {latest['rsi']:.1f}", direction
            
            return False, "No strong trend detected", "NEUTRAL"
            
        except Exception as e:
            print(f"❌ Trend detection error: {e}")
            return False, "Trend detection error", "NEUTRAL"
    
    def detect_trend_following_opportunity(self, df):
        """ตรวจสอบโอกาสเทรดตามเทรน"""
        try:
            if df is None or len(df) < 20:
                return False, "No data", "NEUTRAL", 0.0
            
            latest = df.iloc[-1]
            
            # ตรวจสอบเทรนที่ชัดเจน
            trend_strength = latest.get('trend_strength', 0)
            if trend_strength < self.trend_following_threshold:
                return False, f"Weak trend: {trend_strength:.2f}", "NEUTRAL", trend_strength
            
            # ตรวจสอบทิศทางเทรน
            ema_10 = latest.get('ema_10', 0)
            ema_20 = latest.get('ema_20', 0)
            
            if ema_10 > ema_20:
                trend_direction = "UP"
                # ตรวจสอบ pullback สำหรับ entry
                rsi = latest.get('rsi', 50)
                if 40 <= rsi <= 60:  # RSI ไม่ extreme
                    return True, f"Uptrend following opportunity: {trend_strength:.2f}", trend_direction, trend_strength
            elif ema_10 < ema_20:
                trend_direction = "DOWN"
                # ตรวจสอบ pullback สำหรับ entry
                rsi = latest.get('rsi', 50)
                if 40 <= rsi <= 60:  # RSI ไม่ extreme
                    return True, f"Downtrend following opportunity: {trend_strength:.2f}", trend_direction, trend_strength
            
            return False, "No clear trend direction", "NEUTRAL", trend_strength
            
        except Exception as e:
            print(f"❌ Trend following detection error: {e}")
            return False, "Detection error", "NEUTRAL", 0.0
    
    def _store_prediction_data(self, signal, confidence, market_data):
        """เก็บข้อมูลการพยากรณ์สำหรับ learning"""
        try:
            prediction_data = {
                'timestamp': datetime.now(),
                'signal': signal,
                'confidence': confidence,
                'price': market_data['close'],
                'rsi': market_data.get('rsi', 0),
                'bb_position': market_data.get('bb_position', 0),
                'momentum': market_data.get('momentum', 0),
                'trend_strength': market_data.get('trend_strength', 0)
            }
            
            self.recent_predictions.append(prediction_data)
            
            # Keep only last 20 predictions
            if len(self.recent_predictions) > 20:
                self.recent_predictions = self.recent_predictions[-20:]
                
        except Exception as e:
            print(f"❌ Prediction data storage error: {e}")
    
    def generate_comprehensive_analysis_report(self):
        """สร้างรายงานการวิเคราะห์ครอบคลุมทุกครั้งที่มีการตรวจสอบสัญญาณ"""
        try:
            print("\n📊 GENERATING COMPREHENSIVE ANALYSIS REPORT")
            print("="*50)
            
            # Get current market data
            df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 100)
            if df_m1 is None:
                return {"error": "No market data available"}
            
            df_m1 = self.calculate_simple_indicators(df_m1)
            if df_m1 is None:
                return {"error": "Indicator calculation failed"}
            
            latest = df_m1.iloc[-1]
            prev_5 = df_m1.iloc[-6:-1]
            
            # Generate comprehensive analysis
            analysis_report = {
                'timestamp': datetime.now(),
                'market_overview': self._analyze_market_overview(latest, prev_5),
                'technical_analysis': self._analyze_technical_indicators(latest, df_m1),
                'trend_analysis': self._analyze_trend_conditions(latest, prev_5),
                'volatility_analysis': self._analyze_volatility_conditions(latest, prev_5),
                'bb_analysis': self._analyze_bollinger_bands(latest, prev_5),
                'zigzag_analysis': self._analyze_zigzag_patterns(latest, df_m1),
                'momentum_analysis': self._analyze_momentum_conditions(latest, prev_5),
                'ai_analysis': self._analyze_ai_predictions(latest),
                'risk_analysis': self._analyze_risk_conditions(latest),
                'learning_insights': self._generate_learning_insights()
            }
            
            # Store in analysis history
            self.analysis_history.append(analysis_report)
            if len(self.analysis_history) > 50:  # Keep last 50 analyses
                self.analysis_history = self.analysis_history[-50:]
            
            return analysis_report
            
        except Exception as e:
            print(f"❌ Comprehensive analysis error: {e}")
            return {"error": str(e)}
    
    def display_analysis_report(self, analysis_report):
        """แสดงรายงานการวิเคราะห์แบบละเอียด"""
        try:
            if "error" in analysis_report:
                print(f"❌ Analysis Error: {analysis_report['error']}")
                return
            
            print("\n🔍 MARKET ANALYSIS SUMMARY")
            print("-" * 40)
            
            # Market Overview
            market = analysis_report['market_overview']
            print(f"💰 Current Price: ${market['current_price']:.2f}")
            print(f"📊 Market Status: {market['market_status']}")
            print(f"🎯 Trading Zone: {market['trading_zone']}")
            print(f"⚡ Volatility Level: {market['volatility_level']}")
            
            # Technical Analysis
            tech = analysis_report['technical_analysis']
            print(f"\n📈 TECHNICAL INDICATORS")
            print(f"   RSI: {tech['rsi']:.1f} ({tech['rsi_status']})")
            print(f"   MACD: {tech['macd']:.4f} ({tech['macd_status']})")
            print(f"   BB Position: {tech['bb_position']:.1%} ({tech['bb_status']})")
            print(f"   ATR: {tech['atr']:.3f} ({tech['atr_status']})")
            
            # Trend Analysis
            trend = analysis_report['trend_analysis']
            print(f"\n📊 TREND ANALYSIS")
            print(f"   Direction: {trend['direction']} (Strength: {trend['strength']:.2f})")
            print(f"   EMA 10/20: {trend['ema_relationship']}")
            print(f"   Momentum: {trend['momentum_direction']} ({trend['momentum_strength']:.4f})")
            print(f"   Trend Quality: {trend['trend_quality']}")
            
            # Bollinger Bands Analysis
            bb = analysis_report['bb_analysis']
            print(f"\n🎯 BOLLINGER BANDS ANALYSIS")
            print(f"   Width: {bb['width']:.3f} ({bb['width_status']})")
            print(f"   Position: {bb['position']:.1%} ({bb['position_status']})")
            print(f"   Touch Status: {bb['touch_status']}")
            print(f"   Squeeze: {bb['squeeze_status']}")
            
            # ZigZag Analysis
            zz = analysis_report['zigzag_analysis']
            print(f"\n📈 ZIGZAG PATTERN ANALYSIS")
            print(f"   Current Pattern: {zz['current_pattern']}")
            print(f"   Last Peak/Trough: {zz['last_significant_point']}")
            print(f"   Pattern Strength: {zz['pattern_strength']}")
            
            # AI Analysis
            ai = analysis_report['ai_analysis']
            print(f"\n🤖 AI ANALYSIS")
            print(f"   Model Status: {ai['model_status']}")
            print(f"   Prediction Confidence: {ai['prediction_confidence']:.1%}")
            print(f"   Learning Progress: {ai['learning_progress']}")
            print(f"   Recent Accuracy: {ai['recent_accuracy']:.1%}")
            
            # Risk Analysis
            risk = analysis_report['risk_analysis']
            print(f"\n⚠️ RISK ANALYSIS")
            print(f"   Risk Level: {risk['risk_level']}")
            print(f"   Spread Condition: {risk['spread_condition']}")
            print(f"   Market Hours: {risk['market_hours_status']}")
            print(f"   Position Limit: {risk['position_limit_status']}")
            
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Analysis display error: {e}")
    
    def display_signal_analysis_summary(self, signal, df):
        """แสดงสรุปการวิเคราะห์สัญญาณที่เกิดขึ้น"""
        try:
            print("\n" + "="*60)
            print("🎯 SIGNAL ANALYSIS SUMMARY")
            print("="*60)
            
            latest = df.iloc[-1]
            
            print(f"📊 SIGNAL DETAILS:")
            print(f"   Signal Type: {signal.get('signal', 'UNKNOWN')}")
            print(f"   Confidence: {signal.get('confidence', 0):.1%}")
            print(f"   Entry Price: ${latest['close']:.2f}")
            
            # Calculate SL/TP
            sl_points, tp_points = self.calculate_adaptive_sl_tp(
                df, signal.get('signal'), 
                signal.get('ai_signal'), 
                signal.get('ai_confidence', 0.5)
            )
            
            print(f"\n💰 RISK MANAGEMENT:")
            print(f"   Stop Loss: {sl_points/10:.1f} pips (${latest['close'] - sl_points/10000:.2f})")
            print(f"   Take Profit: {tp_points/10:.1f} pips (${latest['close'] + tp_points/10000:.2f})")
            print(f"   Risk/Reward: 1:{tp_points/sl_points:.1f}")
            
            # Signal reasoning
            reasons = signal.get('reasons', [])
            if reasons:
                print(f"\n🔍 SIGNAL REASONING:")
                for i, reason in enumerate(reasons, 1):
                    print(f"   {i}. {reason}")
            
            # Market conditions at signal time
            print(f"\n📊 MARKET CONDITIONS:")
            print(f"   RSI: {latest['rsi']:.1f}")
            print(f"   BB Position: {latest['bb_position']:.1%}")
            print(f"   Momentum: {latest['momentum']:.4f}")
            print(f"   ATR: {latest['atr']:.3f}")
            print(f"   Trend Strength: {latest['trend_strength']:.2f}")
            
            # AI contribution
            if 'ai_signal' in signal and 'ai_confidence' in signal:
                print(f"\n🤖 AI CONTRIBUTION:")
                print(f"   AI Signal: {signal['ai_signal']}")
                print(f"   AI Confidence: {signal['ai_confidence']:.1%}")
                print(f"   AI Agreement: {'✅ YES' if signal['ai_signal'] == signal['signal'] else '❌ NO'}")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ Signal analysis summary error: {e}")
    
    def update_learning_progress_display(self):
        """อัพเดทและแสดงความก้าวหน้าของการเรียนรู้ AI"""
        try:
            print("\n" + "="*60)
            print("🧠 AI LEARNING PROGRESS UPDATE")
            print("="*60)
            
            # Calculate recent performance
            recent_accuracy = self._calculate_recent_accuracy()
            learning_trend = self._determine_learning_trend()
            
            print(f"📊 LEARNING METRICS:")
            print(f"   Recent Accuracy: {recent_accuracy:.1%}")
            print(f"   Learning Trend: {learning_trend}")
            print(f"   Total Predictions: {len(self.recent_predictions)}")
            print(f"   Model Version: {self.current_model_version}")
            
            # Learning improvements
            improvements = self._generate_learning_improvements()
            if improvements:
                print(f"\n🚀 RECENT IMPROVEMENTS:")
                for improvement in improvements[-3:]:  # Show last 3
                    print(f"   • {improvement}")
            
            # Learning insights
            insights = self._generate_current_learning_insights()
            if insights:
                print(f"\n💡 LEARNING INSIGHTS:")
                for insight in insights:
                    print(f"   • {insight}")
            
            # Next learning actions
            next_actions = self._suggest_next_learning_actions()
            if next_actions:
                print(f"\n🎯 NEXT LEARNING ACTIONS:")
                for action in next_actions:
                    print(f"   • {action}")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ Learning progress display error: {e}")
    
    def check_simple_market_conditions(self):
        """ตรวจสอบสภาพตลาดพื้นฐาน"""
        try:
            # Get current data
            df = self.get_gold_data(self.main_timeframe, 50)
            if df is None:
                return False, "No market data"
            
            df = self.calculate_simple_indicators(df)
            if df is None:
                return False, "Indicator calculation failed"
            
            latest = df.iloc[-1]
            
            # Check spread
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                return False, "Symbol info not available"
            
            # Calculate spread correctly for Gold (2 decimal places)
            spread_points = (symbol_info.ask - symbol_info.bid) / symbol_info.point
            if spread_points > self.max_spread:
                return False, f"Spread too high: {spread_points:.1f} points"
            
            # Check ATR
            current_atr = latest.get('atr', 0.5)
            if current_atr < 0.2:
                return False, f"ATR too low: {current_atr:.3f}"
            
            # Check positions
            active_positions = self.get_active_positions()
            positions_count = len(active_positions)
            
            market_info = f"ATR: {current_atr:.3f}, Spread: {spread_points:.1f}pts, RSI: {latest['rsi']:.1f}, Positions: {positions_count}/{self.max_positions}"
            return True, f"Market OK - {market_info}"
            
        except Exception as e:
            print(f"❌ Market condition check error: {e}")
            return False, str(e)
    
    def get_ai_system_status(self):
        """รายงานสถานะของ AI System ทั้งหมด"""
        try:
            status_report = {
                'timestamp': datetime.now(),
                'ai_components_available': AI_COMPONENTS_AVAILABLE,
                'basic_model_active': self.model is not None,
                'components_status': {}
            }
            
            if AI_COMPONENTS_AVAILABLE:
                # Check each AI component status
                components = {
                    'ai_system': self.ai_system,
                    'learning_pipeline': self.learning_pipeline,
                    'model_manager': self.model_manager,
                    'performance_monitor': self.performance_monitor,
                    'model_evaluator': self.model_evaluator,
                    'metrics_collector': self.metrics_collector,
                    'notification_system': self.notification_system,
                    'error_handler': self.error_handler,
                    'data_collector': self.data_collector
                }
                
                for name, component in components.items():
                    if component:
                        try:
                            # Try to get status from component if available
                            if hasattr(component, 'get_status'):
                                component_status = component.get_status()
                            elif hasattr(component, 'status'):
                                component_status = component.status
                            else:
                                component_status = 'ACTIVE'
                            
                            status_report['components_status'][name] = {
                                'status': component_status,
                                'initialized': True,
                                'last_activity': getattr(component, 'last_activity', 'Unknown')
                            }
                        except Exception as e:
                            status_report['components_status'][name] = {
                                'status': 'ERROR',
                                'initialized': True,
                                'error': str(e)
                            }
                    else:
                        status_report['components_status'][name] = {
                            'status': 'NOT_INITIALIZED',
                            'initialized': False
                        }
            
            # Add performance metrics
            status_report['performance_metrics'] = self.performance_data.copy()
            status_report['learning_metrics'] = {
                'learning_enabled': self.learning_enabled,
                'learning_data_samples': len(self.learning_data),
                'recent_predictions': len(self.recent_predictions),
                'learning_trend': self.learning_trend,
                'real_time_accuracy': self.real_time_accuracy,
                'current_model_version': self.current_model_version
            }
            
            return status_report
            
        except Exception as e:
            print(f"❌ AI system status check error: {e}")
            return {'error': str(e), 'timestamp': datetime.now()}
    
    def print_ai_system_status(self):
        """แสดงสถานะ AI System แบบละเอียด"""
        try:
            status = self.get_ai_system_status()
            
            print("\n" + "="*60)
            print("🤖 AI SYSTEM STATUS REPORT")
            print("="*60)
            print(f"📅 Timestamp: {status['timestamp']}")
            print(f"🔧 AI Components Available: {'✅ YES' if status['ai_components_available'] else '❌ NO'}")
            print(f"🧠 Basic Model Active: {'✅ YES' if status['basic_model_active'] else '❌ NO'}")
            
            if 'components_status' in status:
                print("\n📊 COMPONENT STATUS:")
                for name, info in status['components_status'].items():
                    status_icon = "✅" if info['status'] in ['ACTIVE', 'CONNECTED'] else "❌"
                    print(f"   {status_icon} {name.upper()}: {info['status']}")
                    if 'error' in info:
                        print(f"      ⚠️ Error: {info['error']}")
            
            if 'performance_metrics' in status:
                print("\n📈 PERFORMANCE METRICS:")
                perf = status['performance_metrics']
                print(f"   🎯 Total Signals: {perf['total_signals']}")
                print(f"   💼 Total Trades: {perf['total_trades']}")
                print(f"   🏆 Win Rate: {perf['win_rate']:.1%}")
                print(f"   💰 Total Profit: ${perf['total_profit']:.2f}")
                print(f"   📊 AI Accuracy: {perf['ai_prediction_accuracy']:.1%}")
            
            if 'learning_metrics' in status:
                print("\n🧠 LEARNING METRICS:")
                learn = status['learning_metrics']
                print(f"   📚 Learning Enabled: {'✅ YES' if learn['learning_enabled'] else '❌ NO'}")
                print(f"   📊 Learning Samples: {learn['learning_data_samples']}")
                print(f"   🔮 Recent Predictions: {learn['recent_predictions']}")
                print(f"   📈 Learning Trend: {learn['learning_trend']}")
                print(f"   🎯 Real-time Accuracy: {learn['real_time_accuracy']:.1%}")
                print(f"   🔧 Model Version: {learn['current_model_version']}")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error printing AI system status: {e}")
    
    def send_ai_status_notification(self):
        """ส่งการแจ้งเตือนสถานะ AI System ไป Telegram"""
        try:
            status = self.get_ai_system_status()
            
            # Create status message
            message = "🤖 <b>AI System Status Report</b>\n\n"
            
            if status['ai_components_available']:
                message += "✅ <b>Advanced AI System: ACTIVE</b>\n"
                
                # Count active components
                active_components = 0
                total_components = 0
                
                if 'components_status' in status:
                    for name, info in status['components_status'].items():
                        total_components += 1
                        if info['status'] in ['ACTIVE', 'CONNECTED']:
                            active_components += 1
                
                message += f"📊 Components: {active_components}/{total_components} Active\n\n"
                
                # Performance summary
                if 'performance_metrics' in status:
                    perf = status['performance_metrics']
                    message += f"📈 <b>Performance:</b>\n"
                    message += f"• Win Rate: {perf['win_rate']:.1%}\n"
                    message += f"• Total Profit: ${perf['total_profit']:.2f}\n"
                    message += f"• AI Accuracy: {perf['ai_prediction_accuracy']:.1%}\n\n"
                
                # Learning summary
                if 'learning_metrics' in status:
                    learn = status['learning_metrics']
                    message += f"🧠 <b>Learning:</b>\n"
                    message += f"• Samples: {learn['learning_data_samples']}\n"
                    message += f"• Trend: {learn['learning_trend']}\n"
                    message += f"• Model v{learn['current_model_version']}\n"
            else:
                message += "⚠️ <b>Basic Mode: Advanced AI Disabled</b>\n"
                message += f"🧠 Basic Model: {'Active' if status['basic_model_active'] else 'Inactive'}\n"
            
            message += f"\n⏰ {status['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Send notification
            if self.notification_system:
                self.notification_system.send_status_update(message)
            else:
                self.send_telegram_message(message)
                
        except Exception as e:
            print(f"❌ Error sending AI status notification: {e}")
    
    def update_trade_outcome_with_ai_learning(self, ticket, outcome, profit_pips, hold_time, exit_reason):
        """อัปเดตผลลัพธ์เทรดพร้อม AI Learning Integration"""
        try:
            # Update basic learning data
            self.update_trade_outcome(ticket, outcome, profit_pips, hold_time, exit_reason)
            
            # Update advanced AI components if available
            if self.learning_pipeline:
                # Create signal outcome for learning pipeline
                signal_outcome = SignalOutcome(
                    signal_id=f"trade_{ticket}",
                    timestamp=datetime.now(),
                    outcome=outcome,
                    profit_loss=profit_pips,
                    duration_minutes=hold_time,
                    metadata={
                        'exit_reason': exit_reason,
                        'ticket': ticket
                    }
                )
                
                # Record outcome in learning pipeline
                self.learning_pipeline.record_outcome(signal_outcome)
            
            # Update performance monitor
            if self.performance_monitor:
                self.performance_monitor.record_trade_result(
                    outcome=outcome,
                    profit_loss=profit_pips,
                    duration=hold_time,
                    exit_reason=exit_reason
                )
            
            # Collect metrics
            if self.metrics_collector:
                self.metrics_collector.record_trade_metrics({
                    'ticket': ticket,
                    'outcome': outcome,
                    'profit_pips': profit_pips,
                    'hold_time': hold_time,
                    'exit_reason': exit_reason,
                    'timestamp': datetime.now()
                })
            
            # Check if model evaluation is needed
            if self.model_evaluator and len(self.trade_results) % 20 == 0:
                print("🔍 Running model evaluation...")
                evaluation_result = self.model_evaluator.evaluate_current_model()
                if evaluation_result:
                    print(f"📊 Model evaluation completed: {evaluation_result}")
            
        except Exception as e:
            print(f"❌ Error updating trade outcome with AI learning: {e}")
            if self.error_handler:
                self.error_handler.handle_error("trade_outcome_update", str(e))
    
    def collect_learning_data(self, signal_data, market_data):
        """เก็บข้อมูลสำหรับ AI Learning"""
        try:
            current_time = datetime.now()
            
            # เก็บข้อมูล signal ณ เวลานั้น
            learning_sample = {
                'timestamp': current_time,
                'signal': signal_data['signal'] if signal_data else None,
                'confidence': signal_data['confidence'] if signal_data else 0,
                'entry_reasons': signal_data['entry_reasons'] if signal_data else [],
                
                # Market conditions
                'price': market_data['close'],
                'rsi': market_data['rsi'],
                'macd': market_data['macd'],
                'bb_position': market_data['bb_position'],
                'bb_upper': market_data['bb_upper'],
                'bb_lower': market_data['bb_lower'],
                'atr': market_data['atr'],
                'volume_ratio': market_data.get('volume_ratio', 1.0),
                'zigzag_peak': market_data.get('zigzag_peak', 0),
                'zigzag_trough': market_data.get('zigzag_trough', 0),
                
                # Time features
                'hour_of_day': current_time.hour,
                'day_of_week': current_time.weekday(),
                'market_session': self.get_market_session(current_time),
                
                # Future outcome (will be filled later)
                'outcome': None,  # 'WIN', 'LOSS', 'BREAKEVEN'
                'profit_pips': None,
                'hold_time_minutes': None,
                'exit_reason': None
            }
            
            self.learning_data.append(learning_sample)
            
            # เก็บไว้แค่ 1000 samples ล่าสุด
            if len(self.learning_data) > 1000:
                self.learning_data = self.learning_data[-1000:]
            
            print(f"📚 Learning data collected: {len(self.learning_data)} samples")
            
        except Exception as e:
            print(f"❌ Learning data collection error: {e}")
    
    def update_trade_outcome(self, ticket, outcome, profit_pips, hold_time, exit_reason):
        """อัปเดตผลลัพธ์ของเทรดสำหรับ AI Learning"""
        try:
            # หา learning sample ที่ตรงกับ ticket นี้
            for sample in reversed(self.learning_data):
                if (sample['outcome'] is None and 
                    sample['timestamp'] > datetime.now() - timedelta(hours=1)):
                    
                    sample['outcome'] = outcome
                    sample['profit_pips'] = profit_pips
                    sample['hold_time_minutes'] = hold_time
                    sample['exit_reason'] = exit_reason
                    
                    print(f"📊 Trade outcome updated: {outcome}, {profit_pips:.1f} pips")
                    break
            
            # Continuous Learning - retrain บ่อยขึ้น
            completed_samples = [s for s in self.learning_data if s['outcome'] is not None]
            if (len(completed_samples) >= self.min_learning_samples and 
                len(completed_samples) % self.retrain_frequency == 0):
                
                print(f"🧠 Continuous Learning: Retraining with {len(completed_samples)} samples...")
                self.retrain_ai_model_continuous()
                self.send_learning_report()
            
        except Exception as e:
            print(f"❌ Trade outcome update error: {e}")
    
    def retrain_ai_model(self):
        """Retrain AI model ด้วยข้อมูลใหม่"""
        try:
            completed_samples = [s for s in self.learning_data if s['outcome'] is not None]
            
            if len(completed_samples) < self.min_learning_samples:
                print(f"❌ Not enough samples for retraining: {len(completed_samples)}")
                return False
            
            print(f"🧠 Retraining AI model with {len(completed_samples)} samples...")
            
            # เตรียมข้อมูล
            X = []
            y = []
            
            for sample in completed_samples:
                features = []
                for feature in self.learning_features:
                    if feature in sample:
                        features.append(sample[feature])
                    else:
                        features.append(0)
                
                X.append(features)
                y.append(1 if sample['outcome'] == 'WIN' else 0)
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train improved model
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import cross_val_score
            
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=3,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_scaled, y)
            
            # Cross-validation score
            cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
            accuracy = cv_scores.mean()
            
            # Update performance metrics
            self.performance_data['ai_prediction_accuracy'] = accuracy
            
            # Feature importance analysis
            feature_importance = self.model.feature_importances_
            important_features = []
            for i, importance in enumerate(feature_importance):
                if importance > 0.05:  # 5% threshold
                    important_features.append((self.learning_features[i], importance))
            
            important_features.sort(key=lambda x: x[1], reverse=True)
            
            print(f"✅ AI model retrained!")
            print(f"📊 Cross-validation accuracy: {accuracy:.2%}")
            print(f"🔍 Top features:")
            for feature, importance in important_features[:5]:
                print(f"   {feature}: {importance:.3f}")
            
            # Save learning progress
            self.save_learning_progress()
            
            return True
            
        except Exception as e:
            print(f"❌ AI retraining error: {e}")
            return False
    
    def get_market_session(self, timestamp):
        """ระบุ market session"""
        hour = timestamp.hour
        
        # GMT time
        if 8 <= hour < 17:
            return 'LONDON'
        elif 13 <= hour < 22:
            return 'NEW_YORK'
        elif 22 <= hour or hour < 8:
            return 'ASIAN'
        else:
            return 'OVERLAP'
    
    def save_learning_progress(self):
        """บันทึกความคืบหน้าการเรียนรู้"""
        try:
            learning_summary = {
                'timestamp': datetime.now().isoformat(),
                'total_samples': len(self.learning_data),
                'completed_samples': len([s for s in self.learning_data if s['outcome'] is not None]),
                'win_rate': self.performance_data['win_rate'],
                'ai_accuracy': self.performance_data['ai_prediction_accuracy'],
                'performance_data': self.performance_data
            }
            
            with open('ai_learning_progress.json', 'w') as f:
                json.dump(learning_summary, f, indent=2)
            
            print(f"💾 Learning progress saved")
            
        except Exception as e:
            print(f"❌ Save learning progress error: {e}")
    
    def analyze_learning_patterns(self):
        """วิเคราะห์ patterns จากการเรียนรู้"""
        try:
            completed_samples = [s for s in self.learning_data if s['outcome'] is not None]
            
            if len(completed_samples) < 20:
                return
            
            print(f"\n📊 AI Learning Analysis ({len(completed_samples)} samples):")
            
            # Win rate by signal type
            buy_wins = len([s for s in completed_samples if s['signal'] == 'BUY' and s['outcome'] == 'WIN'])
            buy_total = len([s for s in completed_samples if s['signal'] == 'BUY'])
            sell_wins = len([s for s in completed_samples if s['signal'] == 'SELL' and s['outcome'] == 'WIN'])
            sell_total = len([s for s in completed_samples if s['signal'] == 'SELL'])
            
            if buy_total > 0:
                print(f"   🟢 BUY Win Rate: {buy_wins/buy_total:.1%} ({buy_wins}/{buy_total})")
            if sell_total > 0:
                print(f"   🔴 SELL Win Rate: {sell_wins/sell_total:.1%} ({sell_wins}/{sell_total})")
            
            # Win rate by market session
            sessions = ['LONDON', 'NEW_YORK', 'ASIAN', 'OVERLAP']
            for session in sessions:
                session_samples = [s for s in completed_samples if s['market_session'] == session]
                if len(session_samples) > 5:
                    session_wins = len([s for s in session_samples if s['outcome'] == 'WIN'])
                    print(f"   🕐 {session} Win Rate: {session_wins/len(session_samples):.1%} ({session_wins}/{len(session_samples)})")
            
            # Average hold time
            hold_times = [s['hold_time_minutes'] for s in completed_samples if s['hold_time_minutes']]
            if hold_times:
                avg_hold = sum(hold_times) / len(hold_times)
                print(f"   ⏰ Average Hold Time: {avg_hold:.1f} minutes")
            
            # Best performing conditions
            winning_samples = [s for s in completed_samples if s['outcome'] == 'WIN']
            if len(winning_samples) > 10:
                avg_bb_pos_win = sum([s['bb_position'] for s in winning_samples]) / len(winning_samples)
                avg_rsi_win = sum([s['rsi'] for s in winning_samples]) / len(winning_samples)
                print(f"   🎯 Winning BB Position: {avg_bb_pos_win:.1%}")
                print(f"   📈 Winning RSI: {avg_rsi_win:.1f}")
            
        except Exception as e:
            print(f"❌ Learning analysis error: {e}")
    
    def retrain_ai_model_continuous(self):
        """Continuous Learning - Retrain model พร้อม tracking"""
        try:
            completed_samples = [s for s in self.learning_data if s['outcome'] is not None]
            
            if len(completed_samples) < self.min_learning_samples:
                print(f"❌ Not enough samples for continuous learning: {len(completed_samples)}")
                return False
            
            print(f"🧠 Continuous AI Learning Session #{len(self.learning_sessions) + 1}")
            print(f"📊 Training with {len(completed_samples)} samples...")
            
            # เก็บ accuracy ก่อน retrain
            old_accuracy = self.performance_data.get('ai_prediction_accuracy', 0.0)
            
            # เตรียมข้อมูล
            X = []
            y = []
            
            for sample in completed_samples:
                features = []
                for feature in self.learning_features:
                    if feature in sample:
                        features.append(sample[feature])
                    else:
                        features.append(0)
                
                X.append(features)
                y.append(1 if sample['outcome'] == 'WIN' else 0)
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train improved model with better parameters
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import cross_val_score, train_test_split
            
            # Split data for validation
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
            
            self.model = RandomForestClassifier(
                n_estimators=150,  # เพิ่มขึ้น
                max_depth=12,
                min_samples_split=3,
                min_samples_leaf=2,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate performance
            train_accuracy = self.model.score(X_train, y_train)
            test_accuracy = self.model.score(X_test, y_test)
            cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
            cv_accuracy = cv_scores.mean()
            
            # Update performance metrics
            self.performance_data['ai_prediction_accuracy'] = cv_accuracy
            self.current_model_version += 1
            
            # Track learning progress
            learning_session = {
                'version': self.current_model_version,
                'timestamp': datetime.now(),
                'samples_used': len(completed_samples),
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'cv_accuracy': cv_accuracy,
                'old_accuracy': old_accuracy,
                'improvement': cv_accuracy - old_accuracy,
                'feature_count': len(self.learning_features)
            }
            
            self.learning_sessions.append(learning_session)
            
            # Determine learning trend
            if len(self.learning_sessions) >= 3:
                recent_improvements = [s['improvement'] for s in self.learning_sessions[-3:]]
                avg_improvement = sum(recent_improvements) / len(recent_improvements)
                
                if avg_improvement > 0.02:
                    self.learning_trend = "IMPROVING"
                elif avg_improvement > -0.02:
                    self.learning_trend = "STABLE"
                else:
                    self.learning_trend = "DECLINING"
            
            # Feature importance analysis
            feature_importance = self.model.feature_importances_
            important_features = []
            for i, importance in enumerate(feature_importance):
                if importance > 0.03:  # 3% threshold
                    important_features.append((self.learning_features[i], importance))
            
            important_features.sort(key=lambda x: x[1], reverse=True)
            
            # Store model version info
            model_info = {
                'version': self.current_model_version,
                'accuracy': cv_accuracy,
                'improvement': cv_accuracy - old_accuracy,
                'top_features': important_features[:5],
                'timestamp': datetime.now()
            }
            self.model_versions.append(model_info)
            
            print(f"✅ AI Model v{self.current_model_version} trained!")
            print(f"📊 Accuracy: {old_accuracy:.2%} → {cv_accuracy:.2%} ({cv_accuracy-old_accuracy:+.2%})")
            print(f"📈 Learning Trend: {self.learning_trend}")
            print(f"🔍 Top 3 Features:")
            for feature, importance in important_features[:3]:
                print(f"   {feature}: {importance:.3f}")
            
            # Save learning progress
            self.save_continuous_learning_progress()
            
            return True
            
        except Exception as e:
            print(f"❌ Continuous AI learning error: {e}")
            return False
    
    def send_learning_report(self):
        """ส่งรายงานการเรียนรู้ไป Telegram"""
        try:
            if not self.learning_sessions:
                return
            
            latest_session = self.learning_sessions[-1]
            completed_samples = [s for s in self.learning_data if s['outcome'] is not None]
            
            # คำนวณ win rate ล่าสุด
            recent_outcomes = [s['outcome'] for s in completed_samples[-20:]]
            recent_wins = recent_outcomes.count('WIN')
            recent_win_rate = recent_wins / len(recent_outcomes) if recent_outcomes else 0
            
            # สร้างรายงาน
            improvement_emoji = "📈" if latest_session['improvement'] > 0 else "📉" if latest_session['improvement'] < 0 else "➡️"
            trend_emoji = {"IMPROVING": "🚀", "STABLE": "⚖️", "DECLINING": "⚠️"}[self.learning_trend]
            
            learning_report = f"""
🧠 <b>AI LEARNING REPORT v{latest_session['version']}</b>

📊 <b>Model Performance:</b>
• Accuracy: {latest_session['old_accuracy']:.1%} → {latest_session['cv_accuracy']:.1%} {improvement_emoji}
• Improvement: {latest_session['improvement']:+.1%}
• Learning Trend: {self.learning_trend} {trend_emoji}

📈 <b>Recent Performance:</b>
• Win Rate (Last 20): {recent_win_rate:.1%}
• Total Samples: {len(completed_samples)}
• Training Data: {latest_session['samples_used']} samples

🔍 <b>Top Features:</b>
{chr(10).join([f"• {feat}: {imp:.3f}" for feat, imp in self.model_versions[-1]['top_features'][:3]])}

🎯 <b>Next Actions:</b>
• Continue learning every {self.retrain_frequency} trades
• Target accuracy: {latest_session['cv_accuracy'] + 0.05:.1%}
• Focus on {self.learning_trend.lower()} trend

<i>🤖 AI Learning System v{self.current_model_version}</i>
            """.strip()
            
            self.send_telegram_message(learning_report)
            self.last_learning_report = datetime.now()
            
            print(f"📱 Learning report sent to Telegram")
            
        except Exception as e:
            print(f"❌ Send learning report error: {e}")
    
    def track_prediction_accuracy(self, prediction, actual_outcome):
        """ติดตาม accuracy ของ predictions แบบ real-time"""
        try:
            # เก็บ prediction result
            prediction_result = {
                'prediction': prediction,
                'actual': actual_outcome,
                'correct': prediction == actual_outcome,
                'timestamp': datetime.now()
            }
            
            self.recent_predictions.append(prediction_result)
            
            # เก็บแค่ 20 predictions ล่าสุด
            if len(self.recent_predictions) > 20:
                self.recent_predictions = self.recent_predictions[-20:]
            
            # คำนวณ real-time accuracy
            if len(self.recent_predictions) >= 5:
                correct_predictions = sum([p['correct'] for p in self.recent_predictions])
                self.real_time_accuracy = correct_predictions / len(self.recent_predictions)
                
                print(f"🎯 Real-time AI Accuracy: {self.real_time_accuracy:.1%} (last {len(self.recent_predictions)} predictions)")
            
        except Exception as e:
            print(f"❌ Track prediction accuracy error: {e}")
    
    def save_continuous_learning_progress(self):
        """บันทึกความคืบหน้าการเรียนรู้แบบต่อเนื่อง"""
        try:
            learning_progress = {
                'timestamp': datetime.now().isoformat(),
                'current_model_version': self.current_model_version,
                'learning_trend': self.learning_trend,
                'total_learning_sessions': len(self.learning_sessions),
                'total_samples': len(self.learning_data),
                'completed_samples': len([s for s in self.learning_data if s['outcome'] is not None]),
                'real_time_accuracy': self.real_time_accuracy,
                'performance_data': self.performance_data,
                'recent_sessions': self.learning_sessions[-5:],  # เก็บ 5 sessions ล่าสุด
                'model_versions': self.model_versions[-3:]       # เก็บ 3 versions ล่าสุด
            }
            
            with open('continuous_learning_progress.json', 'w') as f:
                json.dump(learning_progress, f, indent=2, default=str)
            
            print(f"💾 Continuous learning progress saved (v{self.current_model_version})")
            
        except Exception as e:
            print(f"❌ Save continuous learning progress error: {e}")
    
    def get_learning_status_summary(self):
        """สรุปสถานะการเรียนรู้สำหรับแสดงผล"""
        try:
            completed_samples = [s for s in self.learning_data if s['outcome'] is not None]
            
            if not self.learning_sessions:
                return "🧠 AI Learning: Initializing..."
            
            latest_session = self.learning_sessions[-1]
            
            status = f"""
🧠 AI Learning Status:
   Model Version: v{self.current_model_version}
   Accuracy: {latest_session['cv_accuracy']:.1%}
   Trend: {self.learning_trend}
   Samples: {len(completed_samples)}
   Real-time: {self.real_time_accuracy:.1%}
            """.strip()
            
            return status
            
        except Exception as e:
            print(f"❌ Get learning status error: {e}")
            return "🧠 AI Learning: Error getting status"
    
    def combine_bb_zigzag_ai_signals(self, bb_sell, bb_buy, ai_signal, ai_confidence, latest):
        """รวมสัญญาณ BB + ZigZag + AI"""
        try:
            print(f"🧠 Combining BB + ZigZag + AI signals...")
            
            final_signal = None
            final_confidence = 0.5
            final_reasons = []
            
            # Priority 1: BB + ZigZag signals
            if bb_sell and bb_sell['confidence'] > 0.7:
                final_signal = "SELL"
                final_confidence = bb_sell['confidence']
                final_reasons.extend(bb_sell['reasons'])
                
                # AI confirmation bonus
                if ai_signal == "SELL" and ai_confidence > 0.6:
                    final_confidence = min(final_confidence * 1.2, 1.0)
                    final_reasons.append("AI Confirms SELL")
                    print("   ✅ AI confirms SELL signal!")
                
            elif bb_buy and bb_buy['confidence'] > 0.7:
                final_signal = "BUY"
                final_confidence = bb_buy['confidence']
                final_reasons.extend(bb_buy['reasons'])
                
                # AI confirmation bonus
                if ai_signal == "BUY" and ai_confidence > 0.6:
                    final_confidence = min(final_confidence * 1.2, 1.0)
                    final_reasons.append("AI Confirms BUY")
                    print("   ✅ AI confirms BUY signal!")
            
            # Priority 2: Strong AI signals (if no BB+ZigZag)
            elif ai_signal and ai_confidence > 0.8:
                final_signal = ai_signal
                final_confidence = ai_confidence
                final_reasons.append(f"High Confidence AI {ai_signal}")
                print(f"   🤖 Using high confidence AI signal: {ai_signal}")
            
            # Check final confidence
            if final_confidence < self.confidence_threshold:
                print(f"   ❌ Final confidence too low: {final_confidence:.1%} < {self.confidence_threshold:.1%}")
                return None
            
            if final_signal is None:
                print(f"   ❌ No qualifying signals found")
                return None
            
            print(f"   ✅ Final Signal: {final_signal} (Confidence: {final_confidence:.1%})")
            print(f"   📋 Reasons: {', '.join(final_reasons)}")
            
            return {
                'signal': final_signal,
                'confidence': final_confidence,
                'entry_reasons': final_reasons,
                'price': latest['close'],
                'rsi': latest['rsi'],
                'macd': latest['macd'],
                'atr': latest['atr'],
                'bb_upper': latest['bb_upper'],
                'bb_lower': latest['bb_lower'],
                'zigzag_data': {
                    'peak': latest['zigzag_peak'],
                    'trough': latest['zigzag_trough']
                }
            }
            
        except Exception as e:
            print(f"❌ Signal combination error: {e}")
            return None
    
    def is_duplicate_signal(self, signal_data):
        """ตรวจสอบว่าเป็น signal ซ้ำหรือไม่"""
        try:
            current_time = datetime.now()
            
            # ตรวจสอบ cooldown period
            if self.last_signal_time:
                time_diff = (current_time - self.last_signal_time).total_seconds()
                if time_diff < self.signal_cooldown_seconds:
                    return True, f"Cooldown active: {time_diff:.0f}s < {self.signal_cooldown_seconds}s"
            
            # ตรวจสอบ duplicate signal data
            if self.last_signal_data:
                price_diff = abs(signal_data['price'] - self.last_signal_data['price']) / signal_data['price']
                same_signal = signal_data['signal'] == self.last_signal_data['signal']
                
                if same_signal and price_diff < self.duplicate_threshold:
                    return True, f"Duplicate signal: same {signal_data['signal']}, price diff {price_diff:.4f} < {self.duplicate_threshold}"
            
            return False, "New unique signal"
            
        except Exception as e:
            print(f"❌ Duplicate check error: {e}")
            return False, "Check error - allowing signal"

    def generate_bb_zigzag_ai_signal(self):
        """สร้างสัญญาณ BB + ZigZag + AI แบบปรับปรุงตาม backtest results"""
        try:
            # ดึงข้อมูลตลาด
            df = self.get_gold_data(self.main_timeframe, 100)
            if df is None:
                return None
            
            # คำนวณ indicators
            df = self.calculate_simple_indicators(df)
            if df is None:
                return None
            
            latest = df.iloc[-1]
            
            # ตรวจสอบเงื่อนไขพื้นฐาน
            if pd.isna(latest['rsi']) or pd.isna(latest['bb_upper']) or pd.isna(latest['bb_lower']):
                return None
            
            # คำนวณ BB position
            bb_range = latest['bb_upper'] - latest['bb_lower']
            if bb_range <= 0:
                return None
            
            bb_position = (latest['close'] - latest['bb_lower']) / bb_range
            bb_width = bb_range / latest['close']
            
            # ตรวจสอบเทรนจาก M15 timeframe
            m15_trend, m15_strength, m15_msg = self.get_higher_timeframe_trend()
            print(f"📈 M15 Trend: {m15_trend} (strength: {m15_strength:.4f}) - {m15_msg}")
            
            # ตรวจสอบเทรนแรง
            strong_trend_detected = False
            if latest['trend_strength'] > self.strong_trend_threshold:
                strong_trend_detected = True
            
            # เงื่อนไขสัญญาณ BUY - เพิ่ม M15 trend confirmation
            buy_signal = (
                bb_position <= 0.20 and                                   # BB position ≤ 0.20 (เข้มงวดขึ้น)
                latest['rsi'] <= 30 and                                   # RSI ≤ 30 (เข้มงวดขึ้น)
                latest['trend_strength'] >= 0.4 and                      # Trend strength
                bb_width >= 0.0008 and                                   # Volatility requirement
                latest['ema_10'] > latest['ema_20'] and                  # M5 uptrend
                m15_trend in ["UP", "STRONG_UP"] and                     # M15 trend confirmation
                not strong_trend_detected
            )
            
            # เงื่อนไขสัญญาณ SELL - เพิ่ม M15 trend confirmation  
            sell_signal = (
                bb_position >= 0.80 and                                  # BB position ≥ 0.80 (เข้มงวดขึ้น)
                latest['rsi'] >= 70 and                                  # RSI ≥ 70 (เข้มงวดขึ้น)
                latest['trend_strength'] >= 0.4 and                     # Trend strength
                bb_width >= 0.0008 and                                  # Volatility requirement
                latest['ema_10'] < latest['ema_20'] and                 # M5 downtrend
                m15_trend in ["DOWN", "STRONG_DOWN"] and                # M15 trend confirmation
                not strong_trend_detected
            )
            
            # สร้างสัญญาณ
            if buy_signal:
                confidence = min(0.95, 0.7 + (35 - latest['rsi']) / 100 + (0.2 - bb_position) * 2)
                signal_type = "BUY"
                entry_reasons = [
                    f"BB Lower Touch (pos: {bb_position:.3f})",
                    f"Oversold RSI ({latest['rsi']:.1f})",
                    f"M5 EMA Uptrend ({latest['ema_10']:.2f} > {latest['ema_20']:.2f})",
                    f"M15 Trend Confirmation: {m15_trend}",
                    f"Good Volatility ({bb_width:.4f})"
                ]
            elif sell_signal:
                confidence = min(0.95, 0.7 + (latest['rsi'] - 65) / 100 + (bb_position - 0.8) * 2)
                signal_type = "SELL"
                entry_reasons = [
                    f"BB Upper Touch (pos: {bb_position:.3f})",
                    f"Overbought RSI ({latest['rsi']:.1f})",
                    f"M5 EMA Downtrend ({latest['ema_10']:.2f} < {latest['ema_20']:.2f})",
                    f"M15 Trend Confirmation: {m15_trend}",
                    f"Good Volatility ({bb_width:.4f})"
                ]
            else:
                return None
            
            # สร้าง signal data
            signal_data = {
                'signal': signal_type,
                'confidence': confidence,
                'price': latest['close'],
                'rsi': latest['rsi'],
                'macd': latest.get('macd', 0),
                'atr': latest['atr'],
                'bb_upper': latest['bb_upper'],
                'bb_lower': latest['bb_lower'],
                'bb_position': bb_position,
                'bb_width': bb_width,
                'ema_10': latest['ema_10'],
                'ema_20': latest['ema_20'],
                'trend_strength': latest['trend_strength'],
                'strong_trend_detected': strong_trend_detected,
                'entry_reasons': entry_reasons,
                'base_confidence': confidence,
                'zigzag_data': {
                    'peak': latest.get('zigzag_peak', 0),
                    'trough': latest.get('zigzag_trough', 0)
                }
            }
            
            # ตรวจสอบ duplicate signal
            is_duplicate, duplicate_msg = self.is_duplicate_signal(signal_data)
            if is_duplicate:
                print(f"   🔄 Skip duplicate signal: {duplicate_msg}")
                return None
            
            # บันทึก signal ล่าสุด
            self.last_signal_time = datetime.now()
            self.last_signal_data = signal_data.copy()
            
            return signal_data
            
        except Exception as e:
            print(f"❌ BB ZigZag AI signal error: {e}")
            return None

    def generate_simple_signal(self):
        """สร้างสัญญาณ - ใช้ BB + ZigZag + AI strategy"""
        return self.generate_bb_zigzag_ai_signal()
    
    def get_m5_bb_width(self):
        """ดึง BB Width จาก M5 timeframe"""
        try:
            # ดึงข้อมูล M5
            df_m5 = self.get_gold_data(mt5.TIMEFRAME_M5, 30)
            if df_m5 is None:
                return None
            
            # คำนวณ BB สำหรับ M5
            bb_middle = df_m5['close'].rolling(window=20).mean()
            bb_std = df_m5['close'].rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            # BB Width ล่าสุด
            latest_bb_width = bb_upper.iloc[-1] - bb_lower.iloc[-1]
            
            print(f"📊 M5 BB Width: ${latest_bb_width:.2f}")
            
            return latest_bb_width
            
        except Exception as e:
            print(f"❌ M5 BB Width error: {e}")
            return None
    
    def calculate_bb_based_sl_tp(self, signal_data):
        """คำนวณ SL และ TP จาก BB Width M5 (ลบ 25%)"""
        try:
            # ใช้ BB Width จาก M5 timeframe
            if self.use_m5_bb_width:
                bb_width = self.get_m5_bb_width()
                if bb_width is None:
                    # Fallback ใช้ M1 BB Width
                    bb_upper = signal_data.get('bb_upper', 0)
                    bb_lower = signal_data.get('bb_lower', 0)
                    if bb_upper == 0 or bb_lower == 0:
                        return self.min_sl_points, self.min_sl_points * 2
                    bb_width = bb_upper - bb_lower
                    print(f"⚠️ Using M1 BB Width as fallback: ${bb_width:.2f}")
            else:
                # ใช้ BB Width จาก M1 (เดิม)
                bb_upper = signal_data.get('bb_upper', 0)
                bb_lower = signal_data.get('bb_lower', 0)
                if bb_upper == 0 or bb_lower == 0:
                    return self.min_sl_points, self.min_sl_points * 2
                bb_width = bb_upper - bb_lower
            
            # แปลงเป็น points (1 pip = 10 points สำหรับ Gold)
            bb_width_points = bb_width * 10
            
            # ใช้ BB Width เต็มจำนวน + safety buffer
            calculated_sl = bb_width_points * (1 - self.bb_sl_reduction) + self.sl_safety_buffer
            
            # ปรับ SL ให้เหมาะสม - ไม่ให้แน่นเกินไป
            if calculated_sl < self.min_sl_points:
                sl_points = self.min_sl_points
                print(f"   📊 BB Width too small ({calculated_sl:.0f}), using minimum SL: {sl_points:.0f} points")
            elif calculated_sl > self.max_sl_points:
                sl_points = self.max_sl_points
                print(f"   📊 BB Width too large ({calculated_sl:.0f}), using maximum SL: {sl_points:.0f} points")
            else:
                sl_points = calculated_sl
                print(f"   ✅ Using BB Width-based SL: {sl_points:.0f} points")
            
            # คำนวณ TP
            tp_points = sl_points * self.bb_tp_multiplier
            
            print(f"📊 Improved M5 BB-based SL/TP calculation:")
            print(f"   M5 BB Width: ${bb_width:.2f} ({bb_width_points:.0f} points)")
            print(f"   Calculated SL: {calculated_sl:.0f} points (BB + {self.sl_safety_buffer} buffer)")
            print(f"   Final SL: {sl_points:.0f} points ({sl_points/10:.1f} pips)")
            print(f"   Final TP: {tp_points:.0f} points ({tp_points/10:.1f} pips)")
            print(f"   Risk/Reward: 1:{tp_points/sl_points:.1f}")
            
            # แสดงคำแนะนำ
            if sl_points < 60:
                print(f"   ⚠️ Tight SL - Good for low volatility")
            elif sl_points > 120:
                print(f"   📊 Wide SL - Suitable for high volatility")
            else:
                print(f"   ✅ Balanced SL - Good risk management")
            
            return sl_points, tp_points
            
        except Exception as e:
            print(f"❌ M5 BB SL/TP calculation error: {e}")
            return self.min_sl_points, self.min_sl_points * 2
    
    def place_scalping_order(self, signal_data):
        """วางออเดอร์ scalping ด้วย BB-based SL/TP"""
        try:
            signal = signal_data['signal']
            confidence = signal_data['confidence']
            price = signal_data['price']
            
            # ดึงข้อมูล symbol
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                return False, "Symbol info not available"
            
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return False, "Tick data not available"
            
            # คำนวณ lot size
            lot_size = self.base_lot_size
            
            # คำนวณ SL และ TP แบบ AI-Enhanced Adaptive
            if self.use_adaptive_sl:
                # ดึงข้อมูล M1 สำหรับ adaptive calculation
                df_m1 = self.get_gold_data(mt5.TIMEFRAME_M1, 50)
                if df_m1 is not None:
                    df_m1 = self.calculate_simple_indicators(df_m1)
                    # Get AI prediction for SL/TP calculation
                    ai_signal, ai_confidence = self.get_simple_ai_prediction(df_m1)
                    sl_points, tp_points = self.calculate_adaptive_sl_tp(df_m1, signal, ai_signal, ai_confidence)
                else:
                    # Fallback to default
                    sl_points = self.min_sl_points
                    tp_points = sl_points * self.tp_risk_reward_ratio
            elif self.use_bb_width_sl:
                sl_points, tp_points = self.calculate_bb_based_sl_tp(signal_data)
            else:
                sl_points = self.min_sl_points
                tp_points = sl_points * self.tp_risk_reward_ratio
            
            # คำนวณ TP และ SL prices
            point = symbol_info.point
            
            if signal == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                entry_price = tick.ask
                tp_price = entry_price + (tp_points * point)
                sl_price = entry_price - (sl_points * point)
            else:  # SELL
                order_type = mt5.ORDER_TYPE_SELL
                entry_price = tick.bid
                tp_price = entry_price - (tp_points * point)
                sl_price = entry_price + (sl_points * point)
            
            # สร้าง request with bot identification
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lot_size,
                "type": order_type,
                "price": entry_price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 20,
                "magic": self.bot_magic_number,  # Bot-specific magic number
                "comment": f"{self.bot_comment_prefix}-{signal}-{confidence:.0%}",  # Bot-specific comment
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # ส่งออเดอร์
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return False, f"Order failed: {result.retcode} - {result.comment}"
            
            # บันทึกข้อมูล
            self.orders_placed.append({
                'ticket': result.order,
                'signal': signal,
                'confidence': confidence,
                'entry_price': entry_price,
                'tp_price': tp_price,
                'sl_price': sl_price,
                'sl_points': sl_points,
                'tp_points': tp_points,
                'bb_width': signal_data.get('bb_upper', 0) - signal_data.get('bb_lower', 0),
                'lot_size': lot_size,
                'timestamp': datetime.now(),
                'reasons': signal_data['entry_reasons']
            })
            
            # อัพเดท daily trade counter (เฉพาะบอท)
            self.daily_trades = self.count_daily_bot_trades()
            self.last_trade_time = datetime.now()
            
            return True, f"Order placed: {result.order}"
            
        except Exception as e:
            print(f"❌ Order placement error: {e}")
            return False, str(e)
    
    def get_active_positions(self):
        """ดึงรายการ positions ที่เปิดอยู่"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            return positions if positions is not None else []
        except Exception as e:
            print(f"❌ Get positions error: {e}")
            return []
    
    def get_bot_positions_only(self):
        """ดึงเฉพาะ positions ที่เปิดโดยบอท"""
        try:
            all_positions = mt5.positions_get(symbol=self.symbol)
            if all_positions is None:
                return []
            
            # กรองเฉพาะ positions ที่มี magic number ของบอท
            bot_positions = [pos for pos in all_positions if pos.magic == self.bot_magic_number]
            return bot_positions
        except Exception as e:
            print(f"❌ Get bot positions error: {e}")
            return []
    
    def count_daily_bot_trades(self):
        """นับจำนวนเทรดของบอทในวันนี้"""
        try:
            # ดึงประวัติการเทรดในวันนี้
            from datetime import date
            today = date.today()
            
            # ดึงประวัติ deals ในวันนี้
            deals = mt5.history_deals_get(
                date_from=today,
                date_to=today
            )
            
            if deals is None:
                return 0
            
            # นับเฉพาะ deals ที่มี magic number ของบอทและเป็น entry orders
            bot_trades = 0
            for deal in deals:
                if (deal.magic == self.bot_magic_number and 
                    deal.symbol == self.symbol and
                    deal.entry == mt5.DEAL_ENTRY_IN):  # เฉพาะ entry trades
                    bot_trades += 1
            
            return bot_trades
        except Exception as e:
            print(f"❌ Count daily bot trades error: {e}")
            return 0
    
    def get_manual_trades_info(self):
        """ดึงข้อมูลเทรดที่เปิดมือ (ไม่ใช่บอท)"""
        try:
            all_positions = mt5.positions_get(symbol=self.symbol)
            if all_positions is None:
                return []
            
            # กรองเฉพาะ positions ที่ไม่ใช่ของบอท
            manual_positions = [pos for pos in all_positions if pos.magic != self.bot_magic_number]
            return manual_positions
        except Exception as e:
            print(f"❌ Get manual trades info error: {e}")
            return []
    
    def show_positions_status(self):
        """แสดงสถานะ positions ปัจจุบัน (แยกบอทและมือ)"""
        try:
            all_positions = self.get_active_positions()
            bot_positions = self.get_bot_positions_only()
            manual_positions = self.get_manual_trades_info()
            
            if not all_positions:
                print("💼 No active positions")
                return
            
            print(f"💼 Total Positions: {len(all_positions)} (🤖 Bot: {len(bot_positions)}, 👤 Manual: {len(manual_positions)})")
            
            # แสดง Bot positions
            if bot_positions:
                print(f"\n🤖 Bot Positions ({len(bot_positions)}):")
                for i, pos in enumerate(bot_positions, 1):
                    profit = pos.profit
                    profit_pips = profit / (mt5.symbol_info(self.symbol).point * 10)
                    position_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                    
                    print(f"   {i}. {position_type} {pos.volume} lots @ ${pos.price_open:.2f}")
                    print(f"      Profit: ${profit:.2f} ({profit_pips:.1f} pips)")
                    print(f"      SL: ${pos.sl:.2f}, TP: ${pos.tp:.2f}")
                    print(f"      Comment: {pos.comment}")
                    
                    # ตรวจสอบและปรับ TP/SL แบบ dynamic
                    if self.enable_dynamic_tpsl and profit_pips > self.profit_trail_threshold:
                        self.manage_dynamic_tpsl(pos, profit_pips)
            
            # แสดง Manual positions (ถ้ามี)
            if manual_positions:
                print(f"\n👤 Manual Positions ({len(manual_positions)}):")
                for i, pos in enumerate(manual_positions, 1):
                    profit = pos.profit
                    profit_pips = profit / (mt5.symbol_info(self.symbol).point * 10)
                    position_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                    
                    print(f"   {i}. {position_type} {pos.volume} lots @ ${pos.price_open:.2f}")
                    print(f"      Profit: ${profit:.2f} ({profit_pips:.1f} pips)")
                    print(f"      SL: ${pos.sl:.2f}, TP: ${pos.tp:.2f}")
                    print(f"      Magic: {pos.magic}, Comment: {pos.comment}")
                
        except Exception as e:
            print(f"❌ Show positions error: {e}")
    
    def manage_dynamic_tpsl(self, position, profit_pips):
        """จัดการ TP/SL แบบ dynamic เมื่อมีกำไร"""
        try:
            current_price = mt5.symbol_info_tick(self.symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(self.symbol).ask
            
            # ตรวจสอบเทรน
            df = self.get_gold_data(self.main_timeframe, 50)
            if df is None:
                return
            
            df = self.calculate_simple_indicators(df)
            if df is None:
                return
            
            # ตรวจสอบโอกาสเทรดตามเทรน
            is_trend, trend_msg, trend_direction, trend_strength = self.detect_trend_following_opportunity(df)
            
            if is_trend and self.enable_trend_following:
                # เทรดตามเทรน - ขยาย TP และปรับ SL
                print(f"🎯 TREND FOLLOWING DETECTED: {trend_msg}")
                
                # คำนวณ TP และ SL ใหม่
                point = mt5.symbol_info(self.symbol).point
                
                if position.type == mt5.POSITION_TYPE_BUY and trend_direction == "UP":
                    # ขยาย TP สำหรับ uptrend
                    new_tp = position.tp + (self.tp_extension_step * point * 10)
                    # เลื่อน SL ขึ้น
                    new_sl = max(position.sl, current_price - (self.trail_step * point * 10))
                    
                elif position.type == mt5.POSITION_TYPE_SELL and trend_direction == "DOWN":
                    # ขยาย TP สำหรับ downtrend
                    new_tp = position.tp - (self.tp_extension_step * point * 10)
                    # เลื่อน SL ลง
                    new_sl = min(position.sl, current_price + (self.trail_step * point * 10))
                else:
                    return
                
                # ปรับ TP/SL
                self.modify_position(position.ticket, new_sl, new_tp, f"Trend following adjustment")
                
            else:
                # ไม่ใช่เทรน - ใช้ trailing stop ปกติ
                point = mt5.symbol_info(self.symbol).point
                
                if position.type == mt5.POSITION_TYPE_BUY:
                    new_sl = max(position.sl, current_price - (self.trail_step * point * 10))
                    if new_sl > position.sl:
                        self.modify_position(position.ticket, new_sl, position.tp, f"Trailing stop")
                        
                elif position.type == mt5.POSITION_TYPE_SELL:
                    new_sl = min(position.sl, current_price + (self.trail_step * point * 10))
                    if new_sl < position.sl:
                        self.modify_position(position.ticket, new_sl, position.tp, f"Trailing stop")
                        
        except Exception as e:
            print(f"❌ Dynamic TP/SL management error: {e}")
    
    def modify_position(self, ticket, new_sl, new_tp, reason):
        """ปรับแก้ position"""
        try:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": new_sl,
                "tp": new_tp,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Position modified: SL={new_sl:.2f}, TP={new_tp:.2f} - {reason}")
                return True
            else:
                print(f"❌ Failed to modify position: {result.comment}")
                return False
                
        except Exception as e:
            print(f"❌ Position modification error: {e}")
            return False
    
    def close_position(self, ticket, reason="Manual close"):
        """ปิด position"""
        try:
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return False
            
            position = positions[0]
            
            # สร้าง request ปิด position
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
                "deviation": 20,
                "magic": 123456,
                "comment": reason,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            print(f"❌ Close position error: {e}")
            return False
    
    def run_scalping_session(self, duration_minutes=60):
        """รันเซสชัน scalping"""
        print(f"⚡ Starting Working Gold Scalping Session ({duration_minutes} minutes)")
        print("=" * 60)
        
        # เชื่อมต่อ MT5
        if not self.connect_mt5():
            print("❌ Cannot connect to MT5")
            return False
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        print(f"🕐 Session: {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
        print(f"⚙️ Settings: Adaptive SL/TP (ATR+BB Width), SL Range={self.min_sl_points/10:.1f}-{self.max_sl_points/10:.1f}pips, Confidence={self.confidence_threshold:.0%}")
        print(f"💼 Position Limit: 2 positions maximum (จำกัดไม่ให้เข้าเยอะเกินไป)")
        
        # แสดงสถานะ positions ปัจจุบัน
        self.show_positions_status()
        
        # ส่งข้อความเริ่มต้น
        start_message = f"""
⚡ <b>BB + ZIGZAG + AI SCALPING STARTED</b> ⚡

🕐 <b>Duration:</b> {duration_minutes} minutes
⚙️ <b>Settings:</b>
• SL/TP: Adaptive (ATR + BB Width + Volatility)
• ATR Multiplier: {self.atr_sl_multiplier:.1f}x
• BB Width Factor: {self.bb_sl_multiplier:.1f}x
• SL Range: {self.min_sl_points/10:.1f}-{self.max_sl_points/10:.1f} pips
• Max Spread: {self.max_spread} points
• Confidence: {self.confidence_threshold:.0%}

🎯 <b>Strategy:</b>
• Bollinger Bands Touch Detection
• ZigZag Peak/Trough Analysis
• AI ML Confirmation
• Trend Reversal Signals
• Adaptive SL/TP based on Market Volatility

<i>🎯 BB + ZigZag + AI Scalping Trader</i>
        """.strip()
        
        self.send_telegram_message(start_message)
        
        signal_count = 0
        last_signal_time = None
        
        try:
            while datetime.now() < end_time:
                current_time = datetime.now()
                
                # ตรวจสอบสภาพตลาด
                market_ok, market_msg = self.check_simple_market_conditions()
                
                if market_ok:
                    # ตรวจสอบจำนวน bot positions ก่อนสร้าง signal (เฉพาะบอท)
                    bot_positions = self.get_bot_positions_only()
                    if len(bot_positions) >= self.max_positions:  # จำกัดเฉพาะ bot positions
                        print(f"   ⚠️ Max bot positions reached: {len(bot_positions)}/{self.max_positions} - Skipping signal generation")
                        time.sleep(10)  # รอ 10 วินาที
                        continue
                    
                    # ตรวจสอบ daily bot trade limit (เฉพาะบอท)
                    current_bot_trades = self.count_daily_bot_trades()
                    if current_bot_trades >= self.max_daily_trades:
                        print(f"   ⚠️ Daily bot trade limit reached: {current_bot_trades}/{self.max_daily_trades} - Monitoring only")
                        time.sleep(30)  # รอ 30 วินาที
                        continue
                    
                    # อัพเดท daily trades counter
                    self.daily_trades = current_bot_trades
                    
                    # สร้างสัญญาณ
                    signal_data = self.generate_simple_signal()
                    
                    if signal_data:
                        signal_count += 1
                        
                        # แสดงข้อมูลสัญญาณ
                        print(f"\n🎯 Signal #{signal_count} - {current_time.strftime('%H:%M:%S')}")
                        print(f"   📊 {signal_data['signal']} - Confidence: {signal_data['confidence']:.1%}")
                        print(f"   💰 Price: ${signal_data['price']:.2f}")
                        print(f"   📈 RSI: {signal_data['rsi']:.1f}")
                        print(f"   📋 Reasons: {', '.join(signal_data['entry_reasons'])}")
                        
                        # วางออเดอร์ทันที (ไม่ต้องตรวจสอบ signal conditions ซ้ำ)
                        success, order_msg = self.place_scalping_order(signal_data)
                        
                        if success:
                            print(f"   ✅ {order_msg}")
                            
                            # ส่งข้อความ Telegram
                            zigzag_info = ""
                            if 'zigzag_data' in signal_data:
                                if signal_data['zigzag_data']['peak'] == 1:
                                    zigzag_info = "📈 ZigZag Peak"
                                elif signal_data['zigzag_data']['trough'] == 1:
                                    zigzag_info = "📉 ZigZag Trough"
                            
                            telegram_message = f"""
🎯 <b>BB + ZIGZAG + AI SIGNAL #{signal_count}</b>

📊 <b>Signal:</b> {signal_data['signal']}
🎯 <b>Confidence:</b> {signal_data['confidence']:.1%}
💰 <b>Entry Price:</b> ${signal_data['price']:.2f}
📈 <b>RSI:</b> {signal_data['rsi']:.1f}

📊 <b>Bollinger Bands:</b>
🔴 Upper Band: ${signal_data.get('bb_upper', 0):.2f}
🟢 Lower Band: ${signal_data.get('bb_lower', 0):.2f}
📏 BB Width: ${(signal_data.get('bb_upper', 0) - signal_data.get('bb_lower', 0)):.2f}

🎯 <b>Adaptive SL/TP:</b>
🛡️ Stop Loss: ATR + BB Width + Volatility
🎯 Take Profit: {self.tp_risk_reward_ratio:.1f}x Risk/Reward
📊 Range: {self.min_sl_points/10:.1f}-{self.max_sl_points/10:.1f} pips

{zigzag_info}

📋 <b>Entry Reasons:</b>
{chr(10).join([f"• {reason}" for reason in signal_data['entry_reasons']])}

✅ <b>Order Status:</b> {order_msg}

<i>🎯 BB + ZigZag + AI Scalping</i>
                            """.strip()
                            
                            self.send_telegram_message(telegram_message)
                            last_signal_time = current_time
                            
                            # รอหลังจากวาง order สำเร็จ
                            time.sleep(60)
                        else:
                            print(f"   ❌ {order_msg}")
                            # รอน้อยกว่าถ้า order ไม่สำเร็จ
                            time.sleep(30)
                        
                        # รอก่อนตรวจสอบสัญญาณใหม่
                        last_signal_time = current_time
                    
                    else:
                        # ไม่มีสัญญาณ - รอสักครู่
                        time.sleep(self.signal_interval_seconds)
                
                else:
                    # ตลาดไม่เหมาะสม
                    print(f"   ⚠️ Market not suitable: {market_msg}")
                    time.sleep(15)
            
            # ตรวจสอบและจัดการ Recovery System
            if self.enable_martingale_recovery:
                self.check_and_execute_recovery()
            
            # สิ้นสุดเซสชัน
            print(f"\n🏁 Scalping session completed!")
            print(f"📊 Total signals generated: {signal_count}")
            print(f"📈 Total orders placed: {len(self.orders_placed)}")
            
            # ส่งสรุปผล
            positions = self.get_active_positions()
            
            summary_message = f"""
🏁 <b>BB + ZIGZAG + AI SESSION COMPLETED</b>

📊 <b>Session Results:</b>
• Duration: {duration_minutes} minutes
• Signals Generated: {signal_count}
• Orders Placed: {len(self.orders_placed)}
• Active Positions: {len(positions)}

🎯 <b>Strategy Performance:</b>
• BB + ZigZag Signals Used
• AI ML Confirmations Applied
• Peak/Trough Analysis Completed

<i>🎯 BB + ZigZag + AI Scalping Trader</i>
            """.strip()
            
            self.send_telegram_message(summary_message)
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n⏹️ Session stopped by user")
            return False
        except Exception as e:
            print(f"\n❌ Session error: {e}")
            return False
        finally:
            mt5.shutdown()

    def check_and_execute_recovery(self):
        """ตรวจสอบและดำเนินการ Martingale Recovery เมื่อมี position ขาดทุน"""
        try:
            positions = self.get_active_positions()
            if not positions:
                return
            
            for position in positions:
                # ตรวจสอบ position ที่ขาดทุน
                profit_pips = self.calculate_position_profit_pips(position)
                
                if profit_pips < -20:  # ขาดทุนเกิน 20 pips
                    print(f"🔄 Checking recovery for position {position.ticket} (Loss: {profit_pips:.1f} pips)")
                    
                    # ตรวจสอบว่าต้องการ recovery หรือไม่
                    if self.should_execute_recovery(position):
                        self.execute_martingale_recovery(position)
                        
        except Exception as e:
            print(f"❌ Recovery check error: {e}")
    
    def should_execute_recovery(self, position):
        """ตรวจสอบว่าควร execute recovery หรือไม่"""
        try:
            # ตรวจสอบ trend ปัจจุบัน
            trend_direction, trend_strength, trend_msg = self.get_higher_timeframe_trend()
            
            # ตรวจสอบว่า position ขัดกับ trend หรือไม่
            position_type = "BUY" if position.type == mt5.POSITION_TYPE_BUY else "SELL"
            
            counter_trend = False
            if position_type == "SELL" and trend_direction in ["UP", "STRONG_UP"]:
                counter_trend = True
            elif position_type == "BUY" and trend_direction in ["DOWN", "STRONG_DOWN"]:
                counter_trend = True
            
            # ตรวจสอบจำนวน recovery positions ที่มีอยู่แล้ว
            symbol_key = f"{self.symbol}_{position_type}"
            current_recovery_level = self.recovery_positions.get(symbol_key, 0)
            
            # เงื่อนไขสำหรับ recovery
            should_recover = (
                counter_trend and  # Position ขัดกับ trend
                current_recovery_level < self.max_recovery_levels and  # ยังไม่ถึง max level
                trend_strength > 0.0005  # Trend มีความแรงพอ
            )
            
            if should_recover:
                print(f"✅ Recovery conditions met: Counter-trend {position_type} vs {trend_direction}")
                return True
            else:
                print(f"❌ Recovery not needed: {position_type} vs {trend_direction}, Level: {current_recovery_level}")
                return False
                
        except Exception as e:
            print(f"❌ Recovery check error: {e}")
            return False
    
    def execute_martingale_recovery(self, losing_position):
        """ดำเนินการ Martingale Recovery"""
        try:
            # ตรวจสอบ trend เพื่อกำหนดทิศทางการ recovery
            trend_direction, trend_strength, trend_msg = self.get_higher_timeframe_trend()
            
            # กำหนดทิศทาง recovery ตาม trend
            if trend_direction in ["UP", "STRONG_UP"]:
                recovery_signal = "BUY"
            elif trend_direction in ["DOWN", "STRONG_DOWN"]:
                recovery_signal = "SELL"
            else:
                print("❌ No clear trend for recovery")
                return False
            
            # คำนวณ recovery level
            position_type = "BUY" if losing_position.type == mt5.POSITION_TYPE_BUY else "SELL"
            symbol_key = f"{self.symbol}_{position_type}"
            current_level = self.recovery_positions.get(symbol_key, 0)
            
            if current_level >= len(self.martingale_lot_sequence):
                print(f"❌ Max recovery level reached for {symbol_key}")
                return False
            
            # คำนวณ lot size สำหรับ recovery
            recovery_lot = self.martingale_lot_sequence[current_level]
            
            # ดึงราคาปัจจุบัน
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return False
            
            current_price = tick.ask if recovery_signal == "BUY" else tick.bid
            
            # คำนวณ SL ใหม่ตามจุดล่าสุด + 3x buffer
            sl_buffer_points = int(300 * self.martingale_sl_multiplier)  # 30 pips * 3 = 90 pips buffer
            
            if recovery_signal == "BUY":
                sl_price = current_price - (sl_buffer_points * 0.01)
                tp_price = current_price + (sl_buffer_points * 0.01 * self.tp_risk_reward_ratio)
            else:
                sl_price = current_price + (sl_buffer_points * 0.01)
                tp_price = current_price - (sl_buffer_points * 0.01 * self.tp_risk_reward_ratio)
            
            # วาง recovery order
            success, msg = self.place_recovery_order(recovery_signal, recovery_lot, current_price, sl_price, tp_price)
            
            if success:
                # อัพเดท recovery tracking
                self.recovery_positions[symbol_key] = current_level + 1
                
                # อัพเดท SL ของ positions ทั้งหมดในกลุ่มเดียวกัน
                self.update_all_positions_sl(sl_price, recovery_signal)
                
                # ส่งแจ้งเตือน
                recovery_message = f"""
🔄 <b>MARTINGALE RECOVERY EXECUTED</b>

📊 <b>Recovery Level:</b> {current_level + 1}/{self.max_recovery_levels}
🎯 <b>Signal:</b> {recovery_signal} (Following {trend_direction} trend)
💰 <b>Lot Size:</b> {recovery_lot}
📈 <b>Entry Price:</b> ${current_price:.2f}
🛡️ <b>Stop Loss:</b> ${sl_price:.2f}
🎯 <b>Take Profit:</b> ${tp_price:.2f}

📋 <b>Reason:</b> Counter-trend position recovery
🔄 <b>Strategy:</b> Progressive lot sizing + Dynamic SL

<i>🎯 Martingale Recovery System</i>
                """.strip()
                
                self.send_telegram_message(recovery_message)
                print(f"✅ Recovery order placed: {recovery_signal} {recovery_lot} lots")
                return True
            else:
                print(f"❌ Recovery order failed: {msg}")
                return False
                
        except Exception as e:
            print(f"❌ Recovery execution error: {e}")
            return False
    
    def place_recovery_order(self, signal, lot_size, price, sl_price, tp_price):
        """วาง recovery order"""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                return False, "Symbol info not available"
            
            # กำหนด order type
            if signal == "BUY":
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(self.symbol).ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(self.symbol).bid
            
            # สร้าง request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Recovery_{signal}_{lot_size}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # ส่ง order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return False, f"Order failed: {result.retcode}"
            
            return True, f"Recovery order placed: {result.order}"
            
        except Exception as e:
            return False, str(e)
    
    def update_all_positions_sl(self, new_sl, signal_type):
        """อัพเดท SL ของ positions ทั้งหมดในทิศทางเดียวกัน"""
        try:
            positions = self.get_active_positions()
            
            for position in positions:
                position_type = "BUY" if position.type == mt5.POSITION_TYPE_BUY else "SELL"
                
                # อัพเดทเฉพาะ positions ที่เป็นทิศทางเดียวกับ recovery
                if position_type == signal_type:
                    # ตรวจสอบว่า SL ใหม่ดีกว่าเดิมหรือไม่
                    should_update = False
                    
                    if signal_type == "BUY" and (position.sl == 0 or new_sl > position.sl):
                        should_update = True
                    elif signal_type == "SELL" and (position.sl == 0 or new_sl < position.sl):
                        should_update = True
                    
                    if should_update:
                        success = self.modify_position(position.ticket, new_sl, position.tp, "Recovery SL Update")
                        if success:
                            print(f"✅ Updated SL for position {position.ticket}: ${new_sl:.2f}")
                        else:
                            print(f"❌ Failed to update SL for position {position.ticket}")
                            
        except Exception as e:
            print(f"❌ SL update error: {e}")
    
    def calculate_position_profit_pips(self, position):
        """คำนวณกำไร/ขาดทุนเป็น pips"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return 0
            
            if position.type == mt5.POSITION_TYPE_BUY:
                current_price = tick.bid
                profit_points = (current_price - position.price_open) * 100
            else:
                current_price = tick.ask
                profit_points = (position.price_open - current_price) * 100
            
            return profit_points
            
        except Exception as e:
            print(f"❌ Profit calculation error: {e}")
            return 0
        finally:
            mt5.shutdown()

def main():
    """ฟังก์ชันหลัก"""
    print("⚡ Working Gold Scalping Trader")
    print("=" * 50)
    
    # สร้าง trader
    trader = WorkingGoldScalpingTrader()
    
    # รันเซสชัน - ใช้ default 5 นาทีสำหรับทดสอบ
    try:
        duration_input = input("Enter session duration (minutes, default 5): ").strip()
        duration = int(duration_input) if duration_input else 5
    except (EOFError, KeyboardInterrupt):
        # ถ้าไม่สามารถรับ input ได้ (เช่น รันผ่าน script) ใช้ default
        duration = 5
        print("Using default duration: 5 minutes")
    
    success = trader.run_scalping_session(duration)
    
    if success:
        print("✅ Session completed successfully!")
    else:
        print("❌ Session failed!")

if __name__ == "__main__":
    main()