# คู่มือการตั้งค่า Take Profit - SafeWeeklyTurboEA

## โหมด Take Profit ที่มีให้เลือก

### 1. TP_FIXED (Fixed Points)
```
InpTPMode = TP_FIXED
InpTakeProfitPoints = 300  // TP ที่ 300 points
```
- **ใช้เมื่อ**: ต้องการ TP คงที่ทุก trade
- **ข้อดี**: ง่าย เข้าใจง่าย
- **ข้อเสีย**: ไม่ปรับตามสภาพตลาด

### 2. TP_RISK_REWARD (Risk:Reward Ratio)
```
InpTPMode = TP_RISK_REWARD
InpRiskRewardRatio = 1.5   // Risk 1 : Reward 1.5
InpStopLossPoints = 500    // SL 500 points
// TP จะเป็น 500 × 1.5 = 750 points
```
- **ใช้เมื่อ**: ต้องการ risk:reward ที่สมดุล
- **ข้อดี**: ควบคุม risk:reward ได้แม่นยำ
- **แนะนำ**: อัตราส่วน 1:1.5 ถึง 1:2

### 3. TP_PERCENT (Percentage of Balance)
```
InpTPMode = TP_PERCENT
InpTPPercent = 3.0         // TP เมื่อกำไร 3% ของ balance
```
- **ใช้เมื่อ**: ต้องการกำไรเป็น % ของ account
- **ข้อดี**: ปรับตาม account size
- **ตัวอย่าง**: Account $10,000 → TP เมื่อกำไร $300

### 4. TP_GRID_PROFIT (Grid Total Profit)
```
InpTPMode = TP_GRID_PROFIT
InpGridProfit = 50.0       // ปิดทั้ง grid เมื่อกำไรรวม $50
```
- **ใช้เมื่อ**: ใช้ grid trading
- **ข้อดี**: ปิดทั้ง grid พร้อมกัน
- **เหมาะสำหรับ**: Grid strategy

### 5. TP_DYNAMIC (Dynamic based on ATR)
```
InpTPMode = TP_DYNAMIC
// TP = 2 × ATR (Average True Range)
```
- **ใช้เมื่อ**: ต้องการปรับตาม volatility
- **ข้อดี**: ปรับตามสภาพตลาด
- **เหมาะสำหรับ**: ตลาดที่ volatility เปลี่ยนแปลงบ่อย

## ฟีเจอร์เพิ่มเติม

### Trailing Take Profit
```
InpUseTrailingTP = true    // เปิดใช้ trailing TP
InpTrailingStart = 200     // เริ่ม trail เมื่อกำไร 200 points
InpTrailingStep = 50       // ระยะห่าง trailing 50 points
```

**วิธีการทำงาน:**
1. เมื่อกำไรถึง 200 points → เริ่ม trailing
2. TP จะเลื่อนตามราคา โดยห่างจากราคาปัจจุบัน 50 points
3. ถ้าราคากลับมา TP จะไม่เลื่อนย้อนกลับ

### Break Even Move
```
// อัตโนมัติ - ไม่ต้องตั้งค่า
// เมื่อกำไร 150 points → ย้าย SL ไป break even + 10 points
```

## การตั้งค่าแนะนำสำหรับแต่ละสถานการณ์

### สำหรับ Gold Trading (XAUUSD)
```
// Conservative
InpTPMode = TP_RISK_REWARD
InpRiskRewardRatio = 1.5
InpStopLossPoints = 500
InpUseTrailingTP = true
InpTrailingStart = 300
InpTrailingStep = 100

// Aggressive  
InpTPMode = TP_PERCENT
InpTPPercent = 2.0
InpUseTrailingTP = true
InpTrailingStart = 200
InpTrailingStep = 50
```

### สำหรับ Forex Major Pairs
```
// EUR/USD, GBP/USD
InpTPMode = TP_DYNAMIC
InpUseTrailingTP = true
InpTrailingStart = 150
InpTrailingStep = 30
```

### สำหรับ Grid Trading
```
InpTPMode = TP_GRID_PROFIT
InpGridProfit = 100.0      // ปิด grid เมื่อกำไรรวม $100
InpUseTrailingTP = false   // ปิด trailing เพราะใช้ grid profit
```

## ตัวอย่างการคำนวณ

### Risk:Reward Example
```
Account Balance: $10,000
Risk per Trade: 2% = $200
Stop Loss: 500 points
Risk:Reward: 1:2

Lot Size = $200 ÷ (500 points × point value)
Take Profit = 500 × 2 = 1,000 points
Expected Profit = $400 (2× risk)
```

### Percentage Example
```
Account Balance: $10,000
TP Percent: 3%
Target Profit: $300

TP Points = $300 ÷ (lot size × point value)
```

## การติดตาม Performance

EA จะแสดงข้อมูล:
```
SAFE EA STATUS: Balance=$10,500 WeeklyPnL=5.0% DailyPnL=1.2% Positions=3 MaxDD=2.1%
SAFE BUY OPENED: Lot=0.1 Price=1950.25 SL=1945.25 TP=1955.25
TRAILING TP UPDATED (BUY): 12345 New TP: 1952.50
MOVED TO BREAK EVEN (BUY): 12345 New SL: 1950.35
GRID PROFIT TARGET REACHED: $75.50
```

## Tips การใช้งาน

1. **เริ่มต้นด้วย TP_RISK_REWARD** - เข้าใจง่าย ควบคุมได้
2. **ใช้ Trailing TP** - เพิ่มกำไรในเทรนด์ที่ดี
3. **ทดสอบใน Demo** - ก่อนใช้งานจริง
4. **ปรับค่าตาม Market** - แต่ละตลาดมีลักษณะต่างกัน
5. **ติดตาม Win Rate** - ปรับ TP ให้เหมาะสม

## สรุป

ระบบ TP ใหม่นี้ให้ความยืดหยุ่นสูง สามารถปรับให้เหมาะกับ trading style และสภาพตลาดได้ เริ่มจากโหมดง่ายๆ แล้วค่อยทดลองโหมดที่ซับซ้อนมากขึ้น