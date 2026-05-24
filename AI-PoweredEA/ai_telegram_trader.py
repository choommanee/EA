"""
AI Telegram Trader - ระบบเทรด AI ส่งสัญญาณไป Telegram
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

# Import ระบบที่พัฒนาไว้
try:
    from performance_monitor import PerformanceMonitor
    from model_manager import ModelManager, ModelType
    from learning_metrics_collector import LearningMetricsCollector
    from learning_notification_system import LearningNotificationSystem
    print("✅ Imported AI Learning System components")
except ImportError as e:
    print(f"⚠️ Some AI components not available: {e}")

class AITelegramTrader:
    """AI Trader ที่ส่งสัญญาณไป Telegram"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        # Telegram settings
        self.telegram_