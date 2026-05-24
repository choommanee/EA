#!/usr/bin/env python3
"""
Test Gold Learning Trader - ทดสอบว่าทำไม gold_learning_trader.py ไม่ทำงาน
"""

import sys
import os
import traceback
from datetime import datetime

# Add Python directory to path
sys.path.append('Python')

def test_imports():
    """ทดสอบการ import"""
    print("🔍 Testing imports...")
    
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 imported successfully")
    except ImportError as e:
        print(f"❌ MetaTrader5 import failed: {e}")
        return False
    
    try:
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier
        print("✅ Basic ML libraries imported successfully")
    except ImportError as e:
        print(f"❌ ML libraries import failed: {e}")
        return False
    
    # Test AI Learning components
    try:
        from performance_monitor import PerformanceMonitor
        print("✅ PerformanceMonitor imported successfully")
    except ImportError as e:
        print(f"⚠️ PerformanceMonitor import failed: {e}")
    
    try:
        from model_manager import ModelManager, ModelType
        print("✅ ModelManager imported successfully")
    except ImportError as e:
        print(f"⚠️ ModelManager import failed: {e}")
    
    try:
        from learning_coordinator import LearningCoordinator, LearningTrigger
        print("✅ LearningCoordinator imported successfully")
    except ImportError as e:
        print(f"⚠️ LearningCoordinator import failed: {e}")
    
    return True

def test_gold_learning_trader():
    """ทดสอบ GoldLearningTrader class"""
    print("\n🔍 Testing GoldLearningTrader class...")
    
    try:
        from gold_learning_trader import GoldLearningTrader
        print("✅ GoldLearningTrader imported successfully")
        
        # สร้าง instance
        trader = GoldLearningTrader()
        print("✅ GoldLearningTrader instance created successfully")
        
        # ทดสอบ initialize_learning_system
        print("\n🧠 Testing learning system initialization...")
        result = trader.initialize_learning_system()
        print(f"Learning system initialization result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ GoldLearningTrader test failed: {e}")
        print(f"Error details: {traceback.format_exc()}")
        return False

def test_mt5_connection():
    """ทดสอบการเชื่อมต่อ MT5"""
    print("\n🔍 Testing MT5 connection...")
    
    try:
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            print("❌ MT5 initialization failed")
            return False
        
        account_info = mt5.account_info()
        if account_info is None:
            print("❌ Cannot get account info")
            mt5.shutdown()
            return False
        
        print(f"✅ MT5 connected - Account: {account_info.login}")
        print(f"💰 Balance: ${account_info.balance:.2f}")
        
        # ทดสอบ symbol ทอง
        gold_symbols = ["XAUUSD", "GOLD", "GOLDm#", "GOLD#", "XAU/USD"]
        found_symbol = None
        
        for symbol in gold_symbols:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is not None:
                found_symbol = symbol
                print(f"✅ Gold symbol found: {symbol}")
                break
        
        if not found_symbol:
            print("⚠️ No gold symbol found")
        
        mt5.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ MT5 connection test failed: {e}")
        return False

def test_database_connection():
    """ทดสอบการเชื่อมต่อฐานข้อมูล"""
    print("\n🔍 Testing database connection...")
    
    try:
        import sqlite3
        from pathlib import Path
        
        # สร้างโฟลเดอร์ Data ถ้าไม่มี
        data_dir = Path("Data")
        data_dir.mkdir(exist_ok=True)
        
        db_path = "Data/forex_trading.db"
        
        # ทดสอบการเชื่อมต่อ
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # ทดสอบการสร้างตาราง
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                data TEXT
            )
        """)
        
        # ทดสอบการเขียนข้อมูล
        cursor.execute("""
            INSERT INTO test_table (timestamp, data) 
            VALUES (?, ?)
        """, (datetime.now().isoformat(), "test_data"))
        
        conn.commit()
        
        # ทดสอบการอ่านข้อมูล
        cursor.execute("SELECT COUNT(*) FROM test_table")
        count = cursor.fetchone()[0]
        
        print(f"✅ Database connection successful - Test records: {count}")
        
        # ลบตารางทดสอบ
        cursor.execute("DROP TABLE test_table")
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def test_ai_components():
    """ทดสอบ AI components แยกๆ"""
    print("\n🔍 Testing AI components individually...")
    
    # Test PerformanceMonitor
    try:
        from performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        print("✅ PerformanceMonitor created successfully")
    except Exception as e:
        print(f"❌ PerformanceMonitor test failed: {e}")
    
    # Test ModelManager
    try:
        from model_manager import ModelManager, ModelType
        manager = ModelManager()
        print("✅ ModelManager created successfully")
    except Exception as e:
        print(f"❌ ModelManager test failed: {e}")
    
    # Test LearningCoordinator
    try:
        from learning_coordinator import LearningCoordinator
        coordinator = LearningCoordinator()
        print("✅ LearningCoordinator created successfully")
    except Exception as e:
        print(f"❌ LearningCoordinator test failed: {e}")

def main():
    """ฟังก์ชันหลัก"""
    print("🔍 Gold Learning Trader Diagnostic Test")
    print("=" * 60)
    
    # ทดสอบการ import
    if not test_imports():
        print("\n❌ Import test failed - cannot continue")
        return
    
    # ทดสอบการเชื่อมต่อฐานข้อมูล
    test_database_connection()
    
    # ทดสอบการเชื่อมต่อ MT5
    test_mt5_connection()
    
    # ทดสอบ AI components
    test_ai_components()
    
    # ทดสอบ GoldLearningTrader
    test_gold_learning_trader()
    
    print("\n" + "=" * 60)
    print("🏁 Diagnostic test completed!")
    print("If you see errors above, those are likely the cause of the issue.")

if __name__ == "__main__":
    main()