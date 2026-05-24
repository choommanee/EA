#!/usr/bin/env python3
"""
Scalping Analysis & Fix - วิเคราะห์และแก้ไขปัญหา Scalping ที่โดน SL เกือบหมด
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

class ScalpingAnalysisFix:
    """วิเคราะห์และแก้ไขปัญหา Scalping"""
    
    def __init__(self):
        self.symbol = "GOLDm#"
        self.telegram_token = "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
        self.chat_id = "-1002852894581"
        
        print("🔍 Scalping Analysis & Fix System initialized")
    
    def analyze_problems(self):
        """วิเคราะห์ปัญหาจากข้อมูลที่เห็น"""
        print("🔍 SCALPING PROBLEM ANALYSIS")
        print("=" * 60)
        
        problems = {
            "entry_timing": {
                "issue": "เข้า order ผิดจังหวะ - ไม่มี confirmation",
                "evidence": "โดน SL เกือบทุกเทรด",
                "impact": "Win rate ต่ำมาก"
            },
            "tp_sl_ratio": {
                "issue": "TP/SL ไม่เหมาะสมกับ market volatility",
                "evidence": "SL 12 pips อาจน้อยเกินไปสำหรับทอง",
                "impact": "โดน noise ของตลาด"
            },
            "ai_model": {
                "issue": "AI Model อาจไม่ได้เรียนรู้ pattern ที่ถูกต้อง",
                "evidence": "สัญญาณไม่แม่นยำ",
                "impact": "Prediction ผิดบ่อย"
            },
            "market_conditions": {
                "issue": "ไม่ได้กรองสภาพตลาดที่เหมาะสำหรับ scalping",
                "evidence": "เทรดในช่วงที่ตลาดไม่เหมาะ",
                "impact": "เข้าตลาดที่มี noise สูง"
            }
        }
        
        for problem, details in problems.items():
            print(f"\n❌ {problem.upper()}:")
            print(f"   Issue: {details['issue']}")
            print(f"   Evidence: {details['evidence']}")
            print(f"   Impact: {details['impact']}")
        
        return problems