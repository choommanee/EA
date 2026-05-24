# 🧠 คู่มือการใช้งาน AI Continuous Learning System

## 🚀 การเริ่มต้นใช้งาน

### 1. การตั้งค่าเบื้องต้น
```bash
# ตรวจสอบว่าระบบพร้อมใช้งาน
python e2e_demo.py
```

### 2. การเริ่มระบบหลัก
```bash
# เริ่มระบบ Performance Monitor
python Python/performance_monitor.py

# เริ่มระบบ Model Manager  
python Python/model_manager.py

# เริ่มระบบ Metrics Collection
python Python/learning_metrics_collector.py
```

## 📊 การใช้งานหลัก

### 🎯 1. การติดตามประสิทธิภาพ (Performance Monitoring)

**วิธีใช้:**
```python
from Python.performance_monitor import PerformanceMonitor

# สร้าง Performance Monitor
monitor = PerformanceMonitor()

# ติดตามสัญญาณ
signal_result = {
    'signal_id': 'EURUSD_BUY_001',
    'prediction': 'BUY',
    'confidence': 0.85,
    'actual_outcome': 'WIN',
    'profit_loss': 50.0
}

# บันทึกผลการทำงาน
monitor.track_signal_outcome(signal_result)

# ดูประสิทธิภาพปัจจุบัน
metrics = monitor.get_current_performance()
print(f"Accuracy: {metrics['accuracy']:.2%}")
print(f"Total P&L: {metrics['total_profit_loss']}")
```

### 🤖 2. การจัดการโมเดล (Model Management)

**วิธีใช้:**
```python
from Python.model_manager import ModelManager
from sklearn.ensemble import RandomForestClassifier

# สร้าง Model Manager
manager = ModelManager()

# สร้างโมเดลใหม่
model = RandomForestClassifier(n_estimators=100)
# ... train your model ...

# บันทึกโมเดล
model_id = manager.save_model(
    model=model,
    name="EURUSD_Predictor",
    model_type="classification",
    metadata={
        'pair': 'EURUSD',
        'timeframe': 'H1',
        'features': ['RSI', 'MACD', 'BB']
    }
)

# Deploy โมเดล
deployment_id = manager.deploy_model(model_id, environment="production")

# โหลดโมเดลที่ deploy แล้ว
active_model = manager.load_model(model_id)
```

### 📈 3. การเก็บและวิเคราะห์เมตริก

**วิธีใช้:**
```python
from Python.learning_metrics_collector import LearningMetricsCollector

# สร้าง Metrics Collector
collector = LearningMetricsCollector()

# เริ่มเก็บเมตริก
collector.start_collection()

# ดูเมตริกแบบ real-time
metrics = collector.get_real_time_metrics()
print("Current Metrics:")
for key, value in metrics.items():
    print(f"  {key}: {value}")

# ดูแนวโน้มประสิทธิภาพ
trends = collector.get_performance_trends(days=7)
print(f"Performance trends over 7 days: {len(trends)} data points")
```

### 🔒 4. การรักษาความปลอดภัย

**วิธีใช้:**
```python
from Python.learning_security_manager import LearningSecurityManager

# สร้าง Security Manager
security = LearningSecurityManager()

# สร้าง user session
session_token = security.create_session("trader1", "trader")

# ตรวจสอบสิทธิ์
can_access = security.check_permission(session_token, "model_load")
if can_access:
    print("✅ อนุญาตให้เข้าถึงโมเดล")
else:
    print("❌ ไม่อนุญาตให้เข้าถึง")

# เข้ารหัสโมเดล
encrypted_data = security.encrypt_model_data(model_data)
```

## 🎛️ การตั้งค่าระบบ

### การสร้างไฟล์ Configuration

สร้างไฟล์ `learning_config.json`:
```json
{
  "learning": {
    "enabled": true,
    "update_frequency": "daily",
    "performance_threshold": 0.75,
    "max_models": 10
  },
  "performance": {
    "monitoring_enabled": true,
    "alert_threshold": 0.6,
    "reporting_frequency": "hourly"
  },
  "security": {
    "encryption_enabled": true,
    "session_timeout": 3600,
    "audit_logging": true
  }
}
```

### การใช้งาน Configuration

```python
from Python.learning_configuration import LearningConfiguration

# โหลด configuration
config = LearningConfiguration("learning_config.json")

# ดูการตั้งค่าปัจจุบัน
print(f"Learning enabled: {config.get('learning.enabled')}")
print(f"Performance threshold: {config.get('learning.performance_threshold')}")

# อัพเดทการตั้งค่า
config.update('learning.performance_threshold', 0.8)
config.save()
```

## 🔄 Workflow การใช้งานจริง

### 1. การเริ่มต้นระบบ
```bash
# 1. ตรวจสอบระบบ
python e2e_demo.py

# 2. เริ่ม Performance Monitor
python Python/performance_monitor.py &

# 3. เริ่ม Metrics Collection  
python Python/learning_metrics_collector.py &
```

### 2. การใช้งานประจำวัน

**เช้า - ตรวจสอบประสิทธิภาพ:**
```python
# ดูประสิทธิภาพเมื่อวาน
monitor = PerformanceMonitor()
yesterday_performance = monitor.get_performance_summary(days=1)
print(f"Yesterday's accuracy: {yesterday_performance['accuracy']:.2%}")
```

**กลางวัน - ติดตามการทำงาน:**
```python
# ดูเมตริกปัจจุบัน
collector = LearningMetricsCollector()
current_metrics = collector.get_real_time_metrics()
```

**เย็น - วิเคราะห์และปรับปรุง:**
```python
# ตรวจสอบว่าต้องอัพเดทโมเดลไหม
if yesterday_performance['accuracy'] < 0.75:
    print("⚠️ ประสิทธิภาพลดลง - ควรอัพเดทโมเดล")
    # ทำการ retrain โมเดล
```

## 📊 การดู Dashboard

### เริ่ม Dashboard
```bash
python Python/learning_dashboard.py
```

Dashboard จะแสดง:
- 📈 กราฟประสิทธิภาพแบบ real-time
- 🤖 สถานะโมเดลปัจจุบัน
- 📊 เมตริกสำคัญ
- ⚠️ การแจ้งเตือน

## 🛠️ การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

**1. โมเดลทำงานช้า:**
```python
# ตรวจสอบประสิทธิภาพ
metrics = collector.get_performance_metrics()
if metrics['avg_prediction_time'] > 100:  # > 100ms
    print("⚠️ โมเดลทำงานช้า - ควรปรับปรุง")
```

**2. ประสิทธิภาพลดลง:**
```python
# ตรวจสอบแนวโน้ม
trends = collector.get_performance_trends(days=7)
if trends[-1]['accuracy'] < trends[0]['accuracy'] - 0.1:
    print("📉 ประสิทธิภาพลดลง 10% ใน 7 วัน")
```

**3. ข้อผิดพลาดระบบ:**
```bash
# ดู log files
tail -f learning_system.log
tail -f learning_errors.log
```

## 🎯 Tips การใช้งานให้มีประสิทธิภาพ

### 1. การตั้งค่าที่แนะนำ
- **Performance Threshold**: 0.75-0.80
- **Update Frequency**: daily สำหรับการเทรดปกติ
- **Max Models**: 5-10 โมเดล

### 2. การติดตาม
- ตรวจสอบประสิทธิภาพทุกวัน
- ดู metrics trends ทุกสัปดาห์
- Review โมเดลทุกเดือน

### 3. การบำรุงรักษา
```bash
# รันทุกสัปดาห์
python maintenance_demo.py

# ทำความสะอาดข้อมูลเก่า
python Python/learning_maintenance_manager.py
```

## 🚨 การแจ้งเตือนสำคัญ

ระบบจะแจ้งเตือนเมื่อ:
- 📉 ประสิทธิภาพลดลงต่ำกว่า threshold
- 🤖 โมเดลต้องการอัพเดท
- ⚠️ เกิดข้อผิดพลาดระบบ
- 🔒 มีการเข้าถึงที่ผิดปกติ

## 📞 การขอความช่วยเหลือ

หากมีปัญหา:
1. ตรวจสอบ log files
2. รัน diagnostic tests
3. ดูเอกสาร troubleshooting
4. ติดต่อทีมสนับสนุน

---

**🎉 ขอให้การเทรดด้วย AI Learning System ประสบความสำเร็จครับ!**