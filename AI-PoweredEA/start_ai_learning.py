"""
AI Continuous Learning System - Quick Start Script
สคริปต์เริ่มต้นใช้งานระบบ AI Learning แบบง่ายๆ
"""

import os
import sys
import time
import json
from datetime import datetime

# Add Python directory to path
sys.path.append('Python')

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}")

def print_section(title):
    """Print formatted section"""
    print(f"\n{'-'*40}")
    print(f"🔧 {title}")
    print(f"{'-'*40}")

def check_system_status():
    """ตรวจสอบสถานะระบบ"""
    print_section("ตรวจสอบสถานะระบบ")
    
    try:
        # Test imports
        from performance_monitor import PerformanceMonitor
        from model_manager import ModelManager
        from learning_metrics_collector import LearningMetricsCollector
        
        print("✅ ระบบพร้อมใช้งาน")
        print("✅ ทุกโมดูลโหลดสำเร็จ")
        return True
        
    except ImportError as e:
        print(f"❌ ข้อผิดพลาด: {e}")
        print("❌ ระบบยังไม่พร้อมใช้งาน")
        return False

def create_default_config():
    """สร้างไฟล์ configuration เริ่มต้น"""
    print_section("สร้างการตั้งค่าเริ่มต้น")
    
    config = {
        "learning": {
            "enabled": True,
            "update_frequency": "daily",
            "performance_threshold": 0.75,
            "max_models": 10
        },
        "performance": {
            "monitoring_enabled": True,
            "alert_threshold": 0.6,
            "reporting_frequency": "hourly"
        },
        "security": {
            "encryption_enabled": True,
            "session_timeout": 3600,
            "audit_logging": True
        },
        "trading": {
            "pairs": ["EURUSD", "GBPUSD", "USDJPY"],
            "timeframes": ["H1", "H4"],
            "risk_management": {
                "max_risk_per_trade": 0.02,
                "max_daily_loss": 0.05
            }
        }
    }
    
    config_file = "ai_learning_config.json"
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ สร้างไฟล์การตั้งค่า: {config_file}")
        print("✅ ใช้การตั้งค่าเริ่มต้นที่แนะนำ")
        return config_file
        
    except Exception as e:
        print(f"❌ ไม่สามารถสร้างไฟล์การตั้งค่า: {e}")
        return None

def initialize_performance_monitor():
    """เริ่มต้น Performance Monitor"""
    print_section("เริ่มต้น Performance Monitor")
    
    try:
        from performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Test with sample data
        sample_signal = {
            'signal_id': 'EURUSD_TEST_001',
            'prediction': 'BUY',
            'confidence': 0.85,
            'actual_outcome': 'WIN',
            'profit_loss': 25.0,
            'timestamp': datetime.now().isoformat()
        }
        
        # แก้ไข API call ให้ถูกต้อง
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
        
        if success:
            metrics = monitor.get_current_performance()
            print("✅ Performance Monitor เริ่มทำงานแล้ว")
            print(f"📊 Accuracy: {metrics.get('accuracy', 0):.2%}")
            print(f"💰 Total P&L: {metrics.get('total_profit_loss', 0)}")
            return monitor
        else:
            print("⚠️ Performance Monitor เริ่มทำงานแต่มีปัญหา")
            return None
            
    except Exception as e:
        print(f"❌ ไม่สามารถเริ่ม Performance Monitor: {e}")
        return None

def initialize_model_manager():
    """เริ่มต้น Model Manager"""
    print_section("เริ่มต้น Model Manager")
    
    try:
        from model_manager import ModelManager
        from sklearn.ensemble import RandomForestClassifier
        
        manager = ModelManager()
        
        # Create sample model
        sample_model = RandomForestClassifier(n_estimators=10, random_state=42)
        
        # Create dummy training data
        import numpy as np
        X_sample = np.random.rand(100, 5)
        y_sample = np.random.randint(0, 2, 100)
        sample_model.fit(X_sample, y_sample)
        
        # Save model - แก้ไข API call
        from model_manager import ModelType
        
        performance_metrics = {
            'accuracy': 0.85,
            'precision': 0.82,
            'recall': 0.88
        }
        
        model_version = manager.save_model(
            model=sample_model,
            model_name="EURUSD_Starter_Model",
            model_type=ModelType.CLASSIFICATION,
            performance_metrics=performance_metrics,
            metadata={
                'pair': 'EURUSD',
                'timeframe': 'H1',
                'features': ['RSI', 'MACD', 'BB', 'EMA', 'Volume'],
                'created_by': 'AI_Learning_System'
            }
        )
        
        if model_version:
            print("✅ Model Manager เริ่มทำงานแล้ว")
            print(f"🤖 สร้างโมเดลตัวอย่าง: {model_version.model_id}")
            
            # Get model info
            models = manager.list_models()
            print(f"📋 จำนวนโมเดลในระบบ: {len(models)}")
            return manager
        else:
            print("⚠️ Model Manager เริ่มทำงานแต่ไม่สามารถสร้างโมเดล")
            return None
            
    except Exception as e:
        print(f"❌ ไม่สามารถเริ่ม Model Manager: {e}")
        return None

def initialize_metrics_collector():
    """เริ่มต้น Metrics Collector"""
    print_section("เริ่มต้น Metrics Collector")
    
    try:
        from learning_metrics_collector import LearningMetricsCollector
        
        collector = LearningMetricsCollector()
        
        # Start collection
        collector.start_collection()
        
        # Wait a moment for metrics to be collected
        time.sleep(1)
        
        # Get initial metrics
        metrics = collector.get_real_time_metrics()
        
        print("✅ Metrics Collector เริ่มทำงานแล้ว")
        print(f"📊 เก็บเมตริกได้: {len(metrics)} รายการ")
        
        # Show some metrics
        for key, value in list(metrics.items())[:3]:
            print(f"   📈 {key}: {value}")
        
        return collector
        
    except Exception as e:
        print(f"❌ ไม่สามารถเริ่ม Metrics Collector: {e}")
        return None

def show_usage_examples():
    """แสดงตัวอย่างการใช้งาน"""
    print_section("ตัวอย่างการใช้งาน")
    
    print("🎯 การใช้งานพื้นฐาน:")
    print("""
# 1. ติดตามสัญญาณใหม่
from Python.performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()

signal = {
    'signal_id': 'EURUSD_BUY_001',
    'prediction': 'BUY',
    'confidence': 0.85,
    'actual_outcome': 'WIN',  # หรือ 'LOSS'
    'profit_loss': 50.0
}
monitor.track_signal_outcome(signal)

# 2. ดูประสิทธิภาพปัจจุบัน
metrics = monitor.get_current_performance()
print(f"Accuracy: {metrics['accuracy']:.2%}")
""")
    
    print("\n🤖 การจัดการโมเดล:")
    print("""
# โหลดโมเดลที่มีอยู่
from Python.model_manager import ModelManager
manager = ModelManager()

models = manager.list_models()
if models:
    model = manager.load_model(models[0]['model_id'])
    # ใช้โมเดลทำนาย
    prediction = model.predict([[0.5, 0.3, 0.8, 0.2, 0.6]])
""")
    
    print("\n📊 การดูเมตริก:")
    print("""
# ดูเมตริกแบบ real-time
from Python.learning_metrics_collector import LearningMetricsCollector
collector = LearningMetricsCollector()

metrics = collector.get_real_time_metrics()
trends = collector.get_performance_trends(days=7)
""")

def main():
    """ฟังก์ชันหลัก"""
    print_header("🧠 AI Continuous Learning System - Quick Start")
    print(f"⏰ เริ่มต้น: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Check system status
    if not check_system_status():
        print("\n❌ ระบบไม่พร้อม กรุณาตรวจสอบการติดตั้ง")
        return False
    
    # 2. Create default configuration
    config_file = create_default_config()
    if not config_file:
        print("\n⚠️ ไม่สามารถสร้างการตั้งค่า แต่ยังสามารถใช้งานได้")
    
    # 3. Initialize components
    print_section("เริ่มต้นระบบหลัก")
    
    monitor = initialize_performance_monitor()
    manager = initialize_model_manager()
    collector = initialize_metrics_collector()
    
    # 4. Summary
    print_section("สรุปการเริ่มต้น")
    
    components_status = {
        "Performance Monitor": "✅" if monitor else "❌",
        "Model Manager": "✅" if manager else "❌",
        "Metrics Collector": "✅" if collector else "❌"
    }
    
    print("📋 สถานะคอมโพเนนต์:")
    for component, status in components_status.items():
        print(f"   {status} {component}")
    
    success_count = sum(1 for status in components_status.values() if status == "✅")
    total_count = len(components_status)
    
    print(f"\n🎯 ระบบพร้อมใช้งาน: {success_count}/{total_count} คอมโพเนนต์")
    
    if success_count >= 2:
        print("\n🎉 ระบบพร้อมใช้งานแล้ว!")
        print("📖 อ่านคู่มือการใช้งานใน: AI_LEARNING_USER_GUIDE.md")
        
        # Show usage examples
        show_usage_examples()
        
        print("\n🚀 เริ่มใช้งานได้เลย!")
        return True
    else:
        print("\n⚠️ ระบบยังไม่พร้อมสมบูรณ์")
        print("🔧 กรุณาตรวจสอบและแก้ไขปัญหาก่อนใช้งาน")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ หยุดการทำงานโดยผู้ใช้")
        exit(1)
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        exit(1)