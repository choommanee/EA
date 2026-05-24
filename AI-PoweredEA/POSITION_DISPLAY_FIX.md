# การแก้ไข Error: 'TradePosition' object has no attribute 'type_str'

## ปัญหา
```
❌ Show positions error: 'TradePosition' object has no attribute 'type_str'
```

## สาเหตุ
- ใช้ `pos.type_str` ซึ่งไม่มีใน MT5 TradePosition object
- MT5 TradePosition มีแค่ `pos.type` ที่เป็นตัวเลข (0=BUY, 1=SELL)

## การแก้ไข

### เดิม (ผิด):
```python
print(f"   {i}. {pos.type_str} {pos.volume} lots @ ${pos.price_open:.2f}")
```

### ใหม่ (ถูก):
```python
# แปลง position type เป็น string
position_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"

print(f"   {i}. {position_type} {pos.volume} lots @ ${pos.price_open:.2f}")
print(f"      Profit: ${profit:.2f} ({profit_pips:.1f} pips)")
print(f"      SL: ${pos.sl:.2f}, TP: ${pos.tp:.2f}")
print(f"      Ticket: {pos.ticket}")
```

## ผลลัพธ์หลังแก้ไข

### ✅ การแสดงผลที่ถูกต้อง:
```
💼 Active Positions: 1/2
   1. BUY 0.2 lots @ $3319.45
      Profit: $-2.40 (-2.4 pips)
      SL: $3317.80, TP: $3325.00
      Ticket: 123456789
```

### 📊 ข้อมูลที่แสดง:
- **Position Type**: BUY/SELL (แปลงจาก type number)
- **Volume**: จำนวน lots
- **Entry Price**: ราคาเปิด position
- **Profit**: กำไร/ขาดทุนใน USD และ pips
- **SL/TP**: ระดับ Stop Loss และ Take Profit
- **Ticket**: หมายเลข position

## MT5 TradePosition Attributes ที่ใช้ได้:
- `pos.ticket` - หมายเลข position
- `pos.type` - ประเภท (0=BUY, 1=SELL)
- `pos.volume` - จำนวน lots
- `pos.price_open` - ราคาเปิด
- `pos.price_current` - ราคาปัจจุบัน
- `pos.sl` - Stop Loss
- `pos.tp` - Take Profit
- `pos.profit` - กำไร/ขาดทุน
- `pos.swap` - ค่า swap
- `pos.comment` - หมายเหตุ

## การทดสอบ
รันไฟล์ `test_positions_display.py` เพื่อทดสอบ:
```bash
python test_positions_display.py
```

## สรุป
✅ แก้ไข error `type_str` แล้ว
✅ แสดงข้อมูล positions ได้ถูกต้อง
✅ เพิ่มข้อมูล ticket number
✅ ระบบทำงานได้ปกติ