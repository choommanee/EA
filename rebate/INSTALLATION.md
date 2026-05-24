# 🚀 INSTALLATION GUIDE - REBATE FARM PRO EA

## 📋 ข้อกำหนดระบบ

### Software Requirements
- ✅ MetaTrader 5 (Build 3390+)
- ✅ Windows 10/11 หรือ Windows Server
- ✅ .NET Framework 4.7.2+
- ✅ Internet Connection (สำหรับ Real-time Data)

### Hardware Requirements  
- 💾 RAM: 4GB ขั้นต่ำ (8GB แนะนำ)
- 💽 Storage: 1GB ว่าง
- 🖥️ Resolution: 1280x720 ขั้นต่ำ (1920x1080 แนะนำ)
- 🌐 Internet: Stable connection

### Broker Requirements
- 🏦 Broker ที่รองรับ Rebate Program
- 📊 ECN/STP Account Type (แนะนำ)
- 💰 Minimum Balance: $1,000
- 🔄 Leverage: 1:100 ขึ้นไป

## 🔧 การติดตั้ง Step-by-Step

### Step 1: เตรียม MT5
1. เปิด MetaTrader 5
2. กด `Ctrl + Shift + D` เพื่อเปิด Data Folder
3. หรือไป Tools → Options → Common → Data Folder

### Step 2: Copy Files
```
Copy ไฟล์ดังนี้:
📁 [Data Folder]\MQL5\Experts\
   └── 📄 RebateFarmPro.mq5

📁 [Data Folder]\MQL5\Include\  
   ├── 📄 Dashboard.mqh
   ├── 📄 RiskManager.mqh
   └── 📄 RebateLibrary.mqh
```

### Step 3: Compile EA
1. เปิด MetaEditor (กด F4 ใน MT5)
2. เปิดไฟล์ `RebateFarmPro.mq5`
3. กด F7 หรือ Compile
4. ตรวจสอบว่าไม่มี Error

### Step 4: Setup EA
1. ใน MT5 ไป Navigator → Expert Advisors
2. หา "RebateFarmPro"
3. Drag & Drop ลงบน Chart
4. กำหนด Parameters

## ⚙️ การกำหนดค่าครั้งแรก

### Basic Settings
```
=== REBATE SETTINGS ===
TargetRebateDaily: 100.0
RebatePerLot: 5.0 (ตรวจสอบจาก Broker)
LotSize: 0.5
MaxDailyTrades: 40

=== RISK MANAGEMENT ===  
MaxDrawdownPercent: 5.0
MaxDailyLoss: 50.0
ProfitPips: 2
StopLossPips: 2
UseBreakevenStrategy: true

=== TRADING SETTINGS ===
TradeEURUSD: true
TradeGBPUSD: true  
TradeUSDJPY: true
TradeGold: true
MaxSpread: 3.0
MagicNumber: 789456

=== TIME FILTER ===
UseTimeFilter: true
StartHour: 8
EndHour: 22
AvoidNews: true

=== DASHBOARD ===
ShowDashboard: true
DashboardX: 20
DashboardY: 50
DashboardColor: clrDarkBlue
```

### Account-Specific Settings

#### $1,000 Account
- LotSize: 0.01-0.1
- MaxDailyLoss: 10-20
- TargetRebateDaily: 10-20

#### $5,000 Account  
- LotSize: 0.1-0.3
- MaxDailyLoss: 25-50
- TargetRebateDaily: 50-75

#### $10,000+ Account
- LotSize: 0.5-1.0
- MaxDailyLoss: 50-100
- TargetRebateDaily: 100-150

## 🔍 การทดสอบ

### Demo Testing
1. ใช้ Demo Account ทดสอบ 1 สัปดาห์
2. ติดตาม Dashboard ทุกวัน
3. บันทึกผลลัพธ์
4. ปรับ Parameters ตามความเหมาะสม

### Live Testing  
1. เริ่มด้วย Lot Size เล็ก
2. ใช้ Conservative Settings
3. ติดตามผล 1 สัปดาห์
4. เพิ่มความเสี่ยงทีละน้อย

## 🚨 Common Issues & Solutions

### Issue 1: EA ไม่ทำงาน
**Symptoms**: ไม่มี Trade, Dashboard ไม่แสดง
**Solutions**:
- ✅ ตรวจสอบ AutoTrading เปิดอยู่
- ✅ ตรวจสอบ EA Enabled  
- ✅ ดู Journal/Expert Tab หา Error
- ✅ Compile EA ใหม่

### Issue 2: ไม่มีสัญญาณเทรด
**Symptoms**: EA ทำงานแต่ไม่เทรด  
**Solutions**:
- ✅ เพิ่ม MaxSpread เป็น 5.0
- ✅ ปิด UseTimeFilter ชั่วคราว
- ✅ ตรวจสอบ Symbol ว่า Market เปิดอยู่
- ✅ ลด ProfitPips และ StopLossPips

### Issue 3: Dashboard ไม่แสดง
**Symptoms**: EA ทำงานแต่ไม่เห็น Dashboard
**Solutions**:  
- ✅ ตั้ง ShowDashboard = true
- ✅ ปรับ DashboardX, DashboardY
- ✅ Restart EA
- ✅ ตรวจสอบ Chart Size

### Issue 4: ขาดทุนเกินขีดจำกัด
**Symptoms**: Daily Loss เกิน MaxDailyLoss
**Solutions**:
- ✅ ลด LotSize
- ✅ เพิ่ม StopLossPips  
- ✅ ลด MaxDailyTrades
- ✅ ใช้ Conservative Settings

### Issue 5: Rebate ไม่ถึงเป้าหมาย
**Symptoms**: Rebate น้อยกว่า Target
**Solutions**:
- ✅ เพิ่ม MaxDailyTrades
- ✅ เปิด Symbol เพิ่มเติม
- ✅ ตรวจสอบ RebatePerLot จริง
- ✅ ลด TargetRebateDaily

## 📊 การติดตาม Performance

### Daily Checklist
- [ ] ตรวจสอบ Dashboard เช้า/เย็น
- [ ] บันทึก Daily Rebate  
- [ ] ดู Win Rate และ Drawdown
- [ ] อ่าน Daily Summary ใน Journal

### Weekly Review
- [ ] คำนวณ Average Daily Rebate
- [ ] วิเคราะห์ Best/Worst Trading Days
- [ ] ปรับ Parameters ถ้าจำเป็น
- [ ] Backup Settings

### Monthly Analysis  
- [ ] สร้าง Performance Report
- [ ] เปรียบเทียบกับเป้าหมาย
- [ ] ปรับ Strategy ถ้าจำเป็น
- [ ] อัพเดท Rebate Rates

## 🔐 Security & Backup

### Settings Backup
สำรองข้อมูลที่สำคัญ:
```
📁 Backup Folder
├── 📄 EA_Settings_[Date].set
├── 📄 Performance_Log_[Month].xlsx  
├── 📁 EA_Files_Backup/
└── 📄 Broker_Rebate_Rates.txt
```

### VPS Setup (แนะนำ)
- 🌐 Windows VPS with MT5
- 🔄 24/7 Internet Connection
- 💾 Auto Backup Schedule
- 📱 Remote Access Setup

## 📞 Support & Updates

### Getting Help
- 📖 อ่าน README.md ก่อน
- 🔍 ตรวจสอบ Common Issues
- 📝 บันทึก Error Messages
- 📧 ติดต่อ Support พร้อม Log Files

### Update Process
1. Download เวอร์ชันใหม่
2. Backup Settings ปัจจุบัน  
3. Replace ไฟล์เก่า
4. Compile ใหม่
5. Load Settings เดิม

---

## ✅ Pre-Launch Checklist

ก่อนเริ่มใช้ Live Account:

- [ ] ทดสอบ Demo สำเร็จ 1 สัปดาห์
- [ ] เข้าใจ Parameters ทั้งหมด
- [ ] ตั้งค่า Risk Management ถูกต้อง
- [ ] ยืนยัน Rebate Rate กับ Broker
- [ ] Backup Settings และ EA Files
- [ ] เตรียม Plan B หาก EA มีปัญหา
- [ ] เข้าใจความเสี่ยงและยอมรับได้

🎯 **Ready to Start Earning Rebate!**

*"การเตรียมการที่ดีคือกุญแจสู่ความสำเร็จ"*