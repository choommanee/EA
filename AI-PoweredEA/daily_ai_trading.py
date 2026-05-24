"""
Daily AI Trading Script
สคริปต์สำหรับการเทรดประจำวันด้วย AI Learning System
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta

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
    print(f"📊 {title}")
    print(f"{'-'*40}")

def check_daily_performance():
    """ตรวจสอบประสิทธิภาพรายวัน"""
    print_section("ประสิทธิภาพเมื่อวาน")
    
    try:
        from performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Get yesterday's performance
        yesterday = datetime.now() - timedelta(days=1)
        performance = monitor.get_performance_summary(days=1)
        
        print(f"📅 วันที่: {yesterday.strftime('%Y-%m-%d')}")
        print(f"🎯 Accuracy: {performance.get('accuracy', 0):.2%}")
        print(f"💰 Total P&L: {performance.get('total_profit_loss', 0):.2f}")
        print(f"📊 Signal Count: {performance.get('signal_count', 0)}")
        print(f"✅ Win Rate: {performance.get('win_rate', 0):.2%}")
        
        # Performance alert
        if performance.get('accuracy', 0) < 0.6:
            print("⚠️ แจ้งเตือน: ประสิทธิภาพต่ำกว่า 60%")
            return False
        elif performance.get('accuracy', 0) > 0.8:
            print("🎉 ยอดเยี่ยม: ประสิทธิภาพสูงกว่า 80%")
            return True
        else:
            print("✅ ประสิทธิภาพอยู่ในเกณฑ์ปกติ")
            return True
            
    except Exception as e:
        print(f"❌ ไม่สามารถตรวจสอบประสิทธิภาพ: {e}")
        return False

def get_active_models():
    """ดูโมเดลที่ใช้งานอยู่"""
    print_section("โมเดลที่ใช้งานอยู่")
    
    try:
        from model_manager import ModelManager
        
        manager = ModelManager()
        models = manager.list_models()
        
        if not models:
            print("❌ ไม่มีโมเดลในระบบ")
            return []
        
        active_models = []
        for model in models:
            if model.status in ['production', 'staging']:
                active_models.append(model)
                print(f"🤖 {model.model_name} (v{model.version})")
                print(f"   📊 Type: {model.model_type.value}")
                print(f"   🎯 Status: {model.status.value}")
                print(f"   📅 Created: {model.training_timestamp}")
        
        print(f"\n📋 รวม: {len(active_models)} โมเดลที่ใช้งานอยู่")
        return active_models
        
    except Exception as e:
        print(f"❌ ไม่สามารถดูโมเดล: {e}")
        return []

def get_current_metrics():
    """ดูเมตริกปัจจุบัน"""
    print_section("เมตริกปัจจุบัน")
    
    try:
        from learning_metrics_collector import LearningMetricsCollector
        
        collector = LearningMetricsCollector()
        
        # Start collection if not running
        collector.start_collection()
        time.sleep(1)  # Wait for metrics
        
        metrics = collector.get_real_time_metrics()
        
        if not metrics:
            print("⚠️ ไม่มีเมตริกในขณะนี้")
            return {}
        
        # Show key metrics
        key_metrics = [
            'system_accuracy',
            'total_signals',
            'active_models',
            'avg_prediction_time',
            'memory_usage',
            'cpu_usage'
        ]
        
        print("📊 เมตริกสำคัญ:")
        for key in key_metrics:
            if key in metrics:
                value = metrics[key]
                if isinstance(value, float):
                    if key.endswith('_time'):
                        print(f"   ⏱️ {key}: {value:.2f}ms")
                    elif key.endswith('_usage'):
                        print(f"   💻 {key}: {value:.1f}%")
                    else:
                        print(f"   📈 {key}: {value:.3f}")
                else:
                    print(f"   📊 {key}: {value}")
        
        return metrics
        
    except Exception as e:
        print(f"❌ ไม่สามารถดูเมตริก: {e}")
        return {}

def make_trading_prediction(pair="EURUSD"):
    """ทำการทำนายสำหรับการเทรด"""
    print_section(f"การทำนายสำหรับ {pair}")
    
    try:
        from model_manager import ModelManager
        import numpy as np
        
        manager = ModelManager()
        models = manager.list_models()
        
        # Find active model
        active_model = None
        model_info = None
        for model in models:
            if model.status.value == 'production':
                loaded_model, model_version = manager.load_model(model.model_id)
                active_model = loaded_model
                model_info = model_version
                break
        
        if not active_model:
            print("❌ ไม่มีโมเดลที่ใช้งานได้")
            return None
        
        # Simulate current market data (ในการใช้งานจริงจะดึงจาก MT5)
        current_features = np.random.rand(1, 5)  # 5 features
        
        # Make prediction
        prediction = active_model.predict(current_features)[0]
        prediction_proba = active_model.predict_proba(current_features)[0]
        
        confidence = max(prediction_proba)
        signal = "BUY" if prediction == 1 else "SELL"
        
        print(f"🎯 คู่เงิน: {pair}")
        print(f"📊 โมเดล: {model_info['name']} v{model_info['version']}")
        print(f"🔮 สัญญาณ: {signal}")
        print(f"💪 ความมั่นใจ: {confidence:.2%}")
        
        # Risk assessment
        if confidence > 0.8:
            risk_level = "ต่ำ"
            print("✅ แนะนำ: เทรดได้")
        elif confidence > 0.6:
            risk_level = "ปานกลาง"
            print("⚠️ แนะนำ: ระวังความเสี่ยง")
        else:
            risk_level = "สูง"
            print("❌ แนะนำ: ไม่ควรเทรด")
        
        prediction_result = {
            'pair': pair,
            'signal': signal,
            'confidence': confidence,
            'risk_level': risk_level,
            'model': model_info['name'],
            'timestamp': datetime.now().isoformat()
        }
        
        return prediction_result
        
    except Exception as e:
        print(f"❌ ไม่สามารถทำนาย: {e}")
        return None

def track_signal_result(signal_id, actual_outcome, profit_loss):
    """บันทึกผลการเทรด"""
    print_section("บันทึกผลการเทรด")
    
    try:
        from performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        signal_result = {
            'signal_id': signal_id,
            'actual_outcome': actual_outcome,  # 'WIN' or 'LOSS'
            'profit_loss': profit_loss,
            'timestamp': datetime.now().isoformat()
        }
        
        success = monitor.track_signal_outcome(signal_result)
        
        if success:
            print(f"✅ บันทึกผลสำเร็จ: {signal_id}")
            print(f"📊 ผลลัพธ์: {actual_outcome}")
            print(f"💰 กำไร/ขาดทุน: {profit_loss:.2f}")
            
            # Update performance
            current_perf = monitor.get_current_performance()
            print(f"🎯 Accuracy ปัจจุบัน: {current_perf.get('accuracy', 0):.2%}")
            
            return True
        else:
            print(f"❌ ไม่สามารถบันทึกผล: {signal_id}")
            return False
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def show_trading_summary():
    """แสดงสรุปการเทรดวันนี้"""
    print_section("สรุปการเทรดวันนี้")
    
    try:
        from performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        today_performance = monitor.get_performance_summary(days=0)  # Today only
        
        print(f"📅 วันที่: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"📊 จำนวนสัญญาณ: {today_performance.get('signal_count', 0)}")
        print(f"🎯 Accuracy: {today_performance.get('accuracy', 0):.2%}")
        print(f"💰 กำไร/ขาดทุนรวม: {today_performance.get('total_profit_loss', 0):.2f}")
        print(f"📈 กำไรเฉลี่ยต่อสัญญาณ: {today_performance.get('avg_profit_per_signal', 0):.2f}")
        
        # Performance rating
        accuracy = today_performance.get('accuracy', 0)
        if accuracy >= 0.8:
            print("🏆 เกรด: A (ยอดเยี่ยม)")
        elif accuracy >= 0.7:
            print("🥈 เกรด: B (ดี)")
        elif accuracy >= 0.6:
            print("🥉 เกรด: C (พอใช้)")
        else:
            print("📉 เกรด: D (ต้องปรับปรุง)")
        
        return today_performance
        
    except Exception as e:
        print(f"❌ ไม่สามารถแสดงสรุป: {e}")
        return {}

def main():
    """ฟังก์ชันหลัก"""
    print_header("🤖 Daily AI Trading Dashboard")
    print(f"📅 วันที่: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Check yesterday's performance
    yesterday_ok = check_daily_performance()
    
    # 2. Check active models
    active_models = get_active_models()
    
    # 3. Get current metrics
    current_metrics = get_current_metrics()
    
    # 4. Make trading predictions for major pairs
    major_pairs = ["EURUSD", "GBPUSD", "USDJPY"]
    predictions = []
    
    for pair in major_pairs:
        prediction = make_trading_prediction(pair)
        if prediction:
            predictions.append(prediction)
    
    # 5. Show trading summary
    today_summary = show_trading_summary()
    
    # 6. Overall status
    print_section("สถานะรวม")
    
    system_health = {
        "Yesterday Performance": "✅" if yesterday_ok else "⚠️",
        "Active Models": "✅" if active_models else "❌",
        "Current Metrics": "✅" if current_metrics else "⚠️",
        "Predictions": "✅" if predictions else "❌"
    }
    
    print("🏥 สุขภาพระบบ:")
    for component, status in system_health.items():
        print(f"   {status} {component}")
    
    healthy_count = sum(1 for status in system_health.values() if status == "✅")
    total_count = len(system_health)
    
    print(f"\n🎯 สถานะรวม: {healthy_count}/{total_count} ปกติ")
    
    if healthy_count >= 3:
        print("\n🎉 ระบบพร้อมสำหรับการเทรด!")
        
        # Show recommended actions
        print("\n📋 การดำเนินการที่แนะนำ:")
        
        high_confidence_signals = [p for p in predictions if p['confidence'] > 0.7]
        if high_confidence_signals:
            print(f"   🎯 มีสัญญาณความมั่นใจสูง: {len(high_confidence_signals)} สัญญาณ")
            for signal in high_confidence_signals:
                print(f"      • {signal['pair']}: {signal['signal']} ({signal['confidence']:.1%})")
        
        if not yesterday_ok:
            print("   ⚠️ ควรตรวจสอบและปรับปรุงโมเดล")
        
        print("\n🚀 เริ่มเทรดได้!")
        
    else:
        print("\n⚠️ ระบบมีปัญหา ควรตรวจสอบก่อนเทรด")
    
    return healthy_count >= 3

if __name__ == "__main__":
    try:
        success = main()
        
        print(f"\n{'='*60}")
        print("💡 วิธีใช้งาน:")
        print("   1. ดูสัญญาณที่แนะนำ")
        print("   2. ตรวจสอบความมั่นใจก่อนเทรด")
        print("   3. บันทึกผลหลังเทรดด้วย track_signal_result()")
        print("   4. รันสคริปต์นี้ทุกเช้าก่อนเทรด")
        print(f"{'='*60}")
        
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ หยุดการทำงานโดยผู้ใช้")
        exit(1)
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        exit(1)