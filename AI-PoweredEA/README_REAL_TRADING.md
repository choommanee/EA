# 🤖 Real AI Trader - ระบบเทรด AI ที่ใช้งานได้จริง

## 🚀 การติดตั้งและใช้งาน (5 นาที)

### ขั้นตอนที่ 1: ติดตั้ง Dependencies
```bash
python install_ai_trader.py
```

### ขั้นตอนที่ 2: ตั้งค่า MetaTrader5
1. เปิด MetaTrader5
2. ไป **Tools > Options > Expert Advisors**
3. เปิด ✅ **Allow automated trading**
4. เปิด ✅ **Allow DLL imports**

### ขั้นตอนที่ 3: รันระบบ
```bash
python real_ai_trader.py
```

## 🎯 ความสามารถ

### ✅ ที่ทำได้จริง:
- **เชื่อมต่อ MT5** - เชื่อมต่อกับ MetaTrader5 ได้จริง
- **ดึงข้อมูลตลาด** - ดึงข้อมูลราคาแบบ real-time
- **วิเคราะห์ Technical** - คำนวณ RSI, MACD, Bollinger Bands
- **AI Prediction** - ใช้ Random Forest ทำนายทิศทางราคา
- **ส่งคำสั่งเทรด** - ส่งคำสั่ง BUY/SELL ได้จริง
- **จัดการ Risk** - ตรวจสอบ spread และ lot size
- **ติดตาม Position** - ดูและปิด positions

### 🎛️ การตั้งค่า:
```python
# ในไฟล์ real_ai_trader.py
self.trading_pairs = ["EURUSD", "GBPUSD", "USDJPY"]  # คู่เงินที่เทรด
self.lot_size = 0.01  # ขนาดการเทรด (0.01 = 1,000 units)
self.max_spread = 20  # spread สูงสุด (points)
```

## 📊 วิธีการทำงาน

### 1. การเทรนโมเดล AI
- ดึงข้อมูลย้อนหลัง 1,000 bars
- คำนวณ Technical Indicators
- สร้าง labels จากการเปลี่ยนแปลงราคาในอนาคต
- เทรน Random Forest Model

### 2. การทำนาย
- วิเคราะห์ข้อมูลปัจจุบัน
- คำนวณ indicators
- ทำนายด้วย AI Model
- ให้ confidence score

### 3. การเทรด
- ตรวจสอบ confidence > 70%
- ตรวจสอบ spread ไม่เกิน 20 points
- ส่งคำสั่งเทรดไป MT5
- ติดตาม positions

## 🛡️ ความปลอดภัย

### การป้องกันความเสี่ยง:
- **Lot Size เล็ก**: เริ่มต้นด้วย 0.01 lot
- **Spread Check**: ไม่เทรดถ้า spread สูงเกินไป
- **Confidence Filter**: เทรดเฉพาะสัญญาณที่มั่นใจ > 70%
- **Manual Confirmation**: ถามก่อนเทรดจริง

### การทดสอบ:
```python
# ทดสอบการเชื่อมต่อ
trader = RealAITrader()
trader.connect_mt5()

# ทดสอบการทำนาย (ไม่เทรดจริง)
prediction = trader.get_prediction("EURUSD")
print(prediction)
```

## 📈 ตัวอย่างการใช้งาน

### การรันแบบทดสอบ:
```bash
python real_ai_trader.py
# เลือก 'N' เมื่อถามว่าจะเทรดจริงไหม
```

### การรันแบบเทรดจริง:
```bash
python real_ai_trader.py
# เลือก 'y' เมื่อถามว่าจะเทรดจริงไหม
# ระบุเวลาที่ต้องการเทรด (นาที)
```

## 🔧 การปรับแต่ง

### เปลี่ยนคู่เงิน:
```python
self.trading_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
```

### เปลี่ยนขนาดการเทรด:
```python
self.lot_size = 0.1  # เพิ่มเป็น 0.1 lot
```

### เปลี่ยนเกณฑ์ confidence:
```python
if prediction['confidence'] > 0.8:  # เพิ่มเป็น 80%
```

## ⚠️ ข้อควรระวัง

### ก่อนเทรดจริง:
1. **ทดสอบใน Demo Account ก่อน**
2. **เริ่มด้วย lot size เล็ก**
3. **ติดตามผลอย่างใกล้ชิด**
4. **ตั้ง Stop Loss เสมอ**

### ข้อจำกัด:
- ต้องมี MetaTrader5 ที่เชื่อมต่อกับโบรกเกอร์
- ต้องมีอินเทอร์เน็ตเสถียร
- ผลการเทรดขึ้นอยู่กับสภาวะตลาด

## 🆘 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย:

**1. เชื่อมต่อ MT5 ไม่ได้:**
```
❌ ไม่สามารถเชื่อมต่อ MT5 ได้
```
**วิธีแก้:**
- ตรวจสอบว่าเปิด MT5 แล้ว
- เปิด Allow automated trading
- Login เข้าบัญชีใน MT5

**2. ไม่สามารถส่งคำสั่งเทรด:**
```
❌ ส่งคำสั่งไม่สำเร็จ
```
**วิธีแก้:**
- ตรวจสอบยอดเงินในบัญชี
- ตรวจสอบว่าตลาดเปิดอยู่
- ลดขนาด lot size

**3. Spread สูงเกินไป:**
```
⚠️ Spread ของ EURUSD สูงเกินไป
```
**วิธีแก้:**
- รอให้ spread ลดลง
- เพิ่มค่า max_spread
- เปลี่ยนโบรกเกอร์

## 📞 การขอความช่วยเหลือ

หากมีปัญหา:
1. ตรวจสอบ error messages
2. ดูว่า MT5 เชื่อมต่อปกติไหม
3. ทดสอบด้วย Demo Account ก่อน

## 🎉 เริ่มใช้งาน

```bash
# 1. ติดตั้ง
python install_ai_trader.py

# 2. ตั้งค่า MT5
# เปิด Allow automated trading

# 3. รันระบบ
python real_ai_trader.py

# 4. เลือก 'N' สำหรับทดสอบ
# หรือ 'y' สำหรับเทรดจริง
```

**🚀 ระบบพร้อมใช้งานจริงแล้ว!**