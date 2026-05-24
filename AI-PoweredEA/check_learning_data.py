"""
Check Learning Data - ตรวจสอบข้อมูล Learning ที่เก็บไว้
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def check_database(db_file):
    """ตรวจสอบฐานข้อมูล"""
    if not os.path.exists(db_file):
        print(f"❌ Database not found: {db_file}")
        return
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # ดูตารางที่มี
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Database: {db_file}")
        print(f"📋 Tables: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   📄 {table_name}: {count} records")
                
                # แสดงข้อมูลตัวอย่าง
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    
                    # ดู column names
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    print(f"      Columns: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                    
                    if sample_data:
                        print(f"      Sample: {sample_data[0][:3] if len(sample_data[0]) > 3 else sample_data[0]}")
            
            except Exception as e:
                print(f"   ❌ Error reading {table_name}: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error with {db_file}: {e}")

def check_models_directory():
    """ตรวจสอบโฟลเดอร์ Models"""
    models_dir = "Models"
    
    if not os.path.exists(models_dir):
        print(f"❌ Models directory not found")
        return
    
    print(f"\n🤖 Models Directory:")
    
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    print(f"📋 Model files: {len(model_files)}")
    
    for model_file in model_files:
        file_path = os.path.join(models_dir, model_file)
        file_size = os.path.getsize(file_path) / 1024  # KB
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        print(f"   🤖 {model_file}")
        print(f"      Size: {file_size:.1f} KB")
        print(f"      Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

def check_learning_system_status():
    """ตรวจสอบสถานะระบบ Learning"""
    print("🧠 Learning System Status Check")
    print("=" * 50)
    
    # ตรวจสอบฐานข้อมูล
    db_files = [
        'Data/forex_trading.db',
        'Data/learning_demo.db', 
        'Data/learning_metrics.db',
        'Data/performance.db',
        'Data/models.db'
    ]
    
    for db_file in db_files:
        check_database(db_file)
    
    # ตรวจสอบโมเดล
    check_models_directory()
    
    # ตรวจสอบ config
    config_file = "ai_learning_config.json"
    if os.path.exists(config_file):
        print(f"\n⚙️ Configuration:")
        print(f"   📄 {config_file}: ✅ Found")
        
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"   🧠 Learning enabled: {config.get('learning', {}).get('enabled', False)}")
            print(f"   📊 Performance monitoring: {config.get('performance', {}).get('monitoring_enabled', False)}")
            print(f"   🔒 Security enabled: {config.get('security', {}).get('encryption_enabled', False)}")
            
        except Exception as e:
            print(f"   ❌ Error reading config: {e}")
    else:
        print(f"\n⚙️ Configuration: ❌ {config_file} not found")

def test_learning_components():
    """ทดสอบคอมโพเนนต์ Learning"""
    print(f"\n🧪 Testing Learning Components:")
    
    try:
        # Test Performance Monitor
        print("   📊 Testing Performance Monitor...")
        import sys
        sys.path.append('Python')
        
        from performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        
        # Test tracking
        signal_data = {
            'signal_type': 'BUY',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat()
        }
        
        outcome = {
            'actual_result': 1.0,
            'predicted_result': 1.0,
            'is_correct': True,
            'profit_loss': 25.0
        }
        
        success = monitor.track_signal_outcome("test_model", "v1.0", signal_data, outcome)
        print(f"      ✅ Signal tracking: {'Success' if success else 'Failed'}")
        
        # Get performance
        metrics = monitor.get_current_performance()
        print(f"      📈 Current accuracy: {metrics.get('accuracy', 0):.2%}")
        
    except Exception as e:
        print(f"   ❌ Performance Monitor error: {e}")
    
    try:
        # Test Model Manager
        print("   🤖 Testing Model Manager...")
        from model_manager import ModelManager
        
        manager = ModelManager()
        models = manager.list_models()
        print(f"      📋 Available models: {len(models)}")
        
        if models:
            latest_model = models[0]
            print(f"      🤖 Latest model: {latest_model.get('model_name', 'Unknown')}")
            print(f"      📊 Accuracy: {latest_model.get('accuracy', 0):.2%}")
        
    except Exception as e:
        print(f"   ❌ Model Manager error: {e}")
    
    try:
        # Test Metrics Collector
        print("   📊 Testing Metrics Collector...")
        from learning_metrics_collector import LearningMetricsCollector
        
        collector = LearningMetricsCollector()
        collector.start_collection()
        
        import time
        time.sleep(1)  # รอให้เก็บเมตริก
        
        metrics = collector.get_real_time_metrics()
        print(f"      📈 Real-time metrics: {len(metrics)} items")
        
        # แสดงเมตริกบางส่วน
        for key, value in list(metrics.items())[:3]:
            print(f"         {key}: {value}")
        
    except Exception as e:
        print(f"   ❌ Metrics Collector error: {e}")

if __name__ == "__main__":
    check_learning_system_status()
    test_learning_components()