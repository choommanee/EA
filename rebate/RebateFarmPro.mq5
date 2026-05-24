//+------------------------------------------------------------------+
//|                                                RebateFarmPro.mq5 |
//|                    Professional Rebate Farming EA with Dashboard |
//|                        Target: $100 Rebate Daily with Zero Loss |
//+------------------------------------------------------------------+
#property copyright "RebateFarm Pro v2.1"
#property version   "2.10"
#property strict

// === INPUT PARAMETERS ===
input group "=== REBATE SETTINGS ==="
input double   TargetRebateDaily = 20.0;       // เป้าหมาย Rebate ต่อวัน ($) - เหมาะกับทุน $100
input double   RebatePerLot = 6.0;             // Rebate ต่อ Lot ($) - XM Ultra Low = $6/lot
input double   LotSize = 0.01;                 // ขนาด Lot เริ่มต้น - Micro lot สำหรับทุน $100
input int      MaxDailyTrades = 100;           // จำนวนเทรดสูงสุดต่อวัน - เพิ่มเพื่อให้ทำงานต่อเนื่อง

input group "=== RISK MANAGEMENT ==="
input double   MaxDrawdownPercent = 10.0;      // Drawdown สูงสุด (%) - เพิ่มเพื่อให้ทำงานต่อเนื่อง
input double   MaxDailyLoss = 10.0;            // ขาดทุนสูงสุดต่อวัน ($) - เหมาะกับทุน $100
input int      ProfitPips = 12;                // เป้าหมายกำไร (pips) - เพิ่มเพื่อปรับ R:R
input int      StopLossPips = 6;               // Stop Loss (pips) - ลดเพื่อควบคุมความเสี่ยง
input bool     UseBreakevenStrategy = true;    // ใช้กลยุทธ์ Breakeven
input bool     UseTrailingStop = true;         // ใช้ Trailing Stop
input int      TrailingStopPips = 8;           // Trailing Stop Distance (pips)
input int      MinProfitForTrailing = 10;      // กำไรขั้นต่ำก่อนเริ่ม Trailing (pips)
input bool     UseProfitLock = true;           // ล็อคกำไรเมื่อถึงเป้าหมาย
input double   ProfitLockPercent = 70.0;       // ล็อคกำไร % ของ TP

input group "=== TRADING SETTINGS ==="
input bool     TradeEURUSD = true;             // เทรด EURUSD
input bool     TradeGBPUSD = true;             // เทรด GBPUSD
input bool     TradeUSDJPY = true;             // เทรด USDJPY
input bool     TradeGold = true;               // เปิด Gold สำหรับ scalping
input double   MaxSpread = 2.0;                // Spread สูงสุด Forex (pips) - เข้มงวดขึ้น
input double   MaxSpreadGold = 30.0;           // Spread สูงสุด Gold (pips) - ลดเพื่อคุณภาพ
input int      MagicNumber = 789456;           // Magic Number

input group "=== TIME FILTER ==="
input bool     UseTimeFilter = false;          // ปิด Filter เวลา - ให้ทำงาน 24 ชั่วโมง
input int      StartHour = 0;                  // เวลาเริ่มเทรด - 24 ชั่วโมง
input int      EndHour = 23;                   // เวลาสิ้นสุดเทรด - 24 ชั่วโมง
input bool     AvoidNews = false;              // ไม่หลีกเลี่ยงข่าว - เทรดต่อเนื่อง

input group "=== DASHBOARD ==="
input bool     ShowDashboard = true;           // แสดง Dashboard
input bool     DebugMode = true;               // โหมด Debug (แสดงข้อมูลเพิ่มเติม)
input int      DashboardX = 20;                // ตำแหน่ง X
input int      DashboardY = 50;                // ตำแหน่ง Y
input color    DashboardColor = clrDarkBlue;   // สี Dashboard

// === GLOBAL VARIABLES ===
string symbols[] = {"EURUSDm#", "GBPUSDm#", "USDJPYm#", "GOLDm#"};
bool symbolEnabled[] = {true, true, true, true};

// Backup symbols (without suffix) in case m# versions don't exist
string backupSymbols[] = {"EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "GOLD"};

datetime lastTradeTime = 0;
int dailyTradeCount = 0;
double dailyProfit = 0;
double dailyRebate = 0;
double accountBalance = 0;
double accountEquity = 0;
bool tradingEnabled = true;

// === MONTHLY REBATE TRACKING ===
double monthlyRebate = 0;           // ยอดรวม rebate เดือนนี้
int currentMonth = 0;               // เดือนปัจจุบัน
int currentYear = 0;                // ปีปัจจุบัน
string monthlyRebateFile = "RebateFarm_Monthly.csv";  // ไฟล์เก็บข้อมูล rebate รายเดือน

struct TradeStats {
    int totalTrades;
    int winTrades;
    int lossTrades;
    double winRate;
    double totalProfit;
    double maxDrawdown;
    double currentDrawdown;
};

TradeStats stats;

// Indicator handles
int ma_fast_handles[4];
int ma_slow_handles[4];
int rsi_handles[4];

// Dashboard variables
string dashboard_prefix = "RebateDash_";
bool dashboard_created = false;

//+------------------------------------------------------------------+
//| Get Valid Symbol (with backup options)                          |
//+------------------------------------------------------------------+
string GetValidSymbol(string originalSymbol, int index)
{
    // ลองใช้ symbol เดิมก่อน
    if(SymbolSelect(originalSymbol, true))
    {
        return originalSymbol;
    }
    
    // ถ้าไม่ได้ ลอง backup symbols
    if(index < ArraySize(backupSymbols))
    {
        string backupSymbol = backupSymbols[index];
        if(SymbolSelect(backupSymbol, true))
        {
            Print("📋 ใช้ backup symbol: ", backupSymbol, " แทน ", originalSymbol);
            return backupSymbol;
        }
    }
    
    // ลองหา Gold symbols อื่นๆ สำหรับ Gold
    if(StringFind(originalSymbol, "GOLD") >= 0 || StringFind(originalSymbol, "XAU") >= 0)
    {
        string goldSymbols[] = {"XAUUSD", "GOLD", "GOLDmicro", "XAUUSD.", "GOLD."};
        for(int i = 0; i < ArraySize(goldSymbols); i++)
        {
            if(SymbolSelect(goldSymbols[i], true))
            {
                Print("🥇 ใช้ Gold symbol: ", goldSymbols[i], " แทน ", originalSymbol);
                return goldSymbols[i];
            }
        }
    }
    
    return ""; // ไม่พบ symbol ที่ใช้ได้
}

//+------------------------------------------------------------------+
//| Get Supported Filling Mode for Symbol                           |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetSupportedFillingMode(string symbol)
{
    // ตรวจสอบ filling modes ที่ symbol รองรับ
    long filling_modes = SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE);
    
    // ลองตามลำดับความนิยม
    if((filling_modes & 1) != 0)  // FOK mode
    {
        return ORDER_FILLING_FOK;  // Fill or Kill
    }
    else if((filling_modes & 2) != 0)  // IOC mode
    {
        return ORDER_FILLING_IOC;  // Immediate or Cancel
    }
    else
    {
        return ORDER_FILLING_RETURN;  // Return (default)
    }
}
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
    Print("=== REBATE FARM PRO EA v2.1 เริ่มทำงาน ===");
    
    // กำหนดค่าเริ่มต้น
    accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    accountEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    
    // ตั้งค่า symbols
    symbolEnabled[0] = TradeEURUSD;
    symbolEnabled[1] = TradeGBPUSD;
    symbolEnabled[2] = TradeUSDJPY;
    symbolEnabled[3] = TradeGold;
    
    // สร้าง indicator handles (ใช้ symbol ปัจจุบันแทน)
    string currentSymbol = Symbol();
    
    // Initialize handles for all symbols
    for(int i = 0; i < ArraySize(symbols); i++) {
        ma_fast_handles[i] = INVALID_HANDLE;
        ma_slow_handles[i] = INVALID_HANDLE;
        rsi_handles[i] = INVALID_HANDLE;
    }
    
    Print("✅ Indicator handles initialized - จะสร้างเมื่อใช้งานจริง");
    
    // สร้าง dashboard
    if(ShowDashboard) {
        CreateDashboard();
    }
    
    // Reset daily counters
    dailyTradeCount = 0;
    dailyProfit = 0;
    dailyRebate = 0;
    tradingEnabled = true;
    
    // เริ่มต้นระบบติดตาม Monthly Rebate
    InitializeMonthlyRebate();
    
    Print("✅ เป้าหมาย Rebate: $", TargetRebateDaily, " ต่อวัน");
    Print("✅ จำนวน Lot ต้องทำ: ", DoubleToString(TargetRebateDaily / RebatePerLot, 2), " lots");
    Print("✅ Magic Number: ", MagicNumber);
    
    return INIT_SUCCEEDED;
}
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() {
    // อัพเดท account info
    accountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
    accountEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    
    // ตรวจสอบวันใหม่
    static int lastDay = -1;
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    
    if(lastDay != time_struct.day) {
        dailyTradeCount = 0;
        dailyProfit = 0;
        dailyRebate = 0;
        tradingEnabled = true;
        lastDay = time_struct.day;
        Print("🌅 วันใหม่ - Reset ข้อมูลรายวัน");
    }
    
    // ตรวจสอบความเสี่ยง
    double currentDrawdown = 0;
    if(accountBalance > 0) {
        currentDrawdown = ((accountBalance - accountEquity) / accountBalance) * 100;
    }
    
    if(currentDrawdown > MaxDrawdownPercent) {
        tradingEnabled = false;
        Comment("⚠️ การเทรดหยุดชั่วคราว - Drawdown เกินขีดจำกัด: " + DoubleToString(currentDrawdown, 2) + "%");
        return;
    }
    
    if(dailyProfit <= -MaxDailyLoss) {
        tradingEnabled = false;
        Comment("⚠️ การเทรดหยุดชั่วคราว - ขาดทุนเกินขีดจำกัด: $" + DoubleToString(dailyProfit, 2));
        return;
    }
    
    // ตรวจสอบเป้าหมาย rebate - แต่ยังคงเทรดต่อไปเพื่อเพิ่ม rebate
    if(dailyRebate >= TargetRebateDaily) {
        Comment("🎯 เป้าหมาย Rebate วันนี้สำเร็จแล้ว: $" + DoubleToString(dailyRebate, 2) + " - ยังคงเทรดต่อไปเพื่อเพิ่ม Rebate");
        // ไม่ return - ให้เทรดต่อไปเพื่อเพิ่ม rebate
    }
    
    // จัดการ open positions
    ManageOpenPositions();
    
    // หาโอกาสเทรดใหม่
    if(tradingEnabled && ShouldTrade()) {
        ScanForTradingOpportunities();
    }
    
    // อัพเดท dashboard
    if(ShowDashboard && dashboard_created) {
        UpdateDashboard();
    }
}

//+------------------------------------------------------------------+
//| ตรวจสอบเงื่อนไขการเทรด                                            |
//+------------------------------------------------------------------+
bool ShouldTrade() {
    // ตรวจสอบจำนวนเทรดสูงสุด
    if(dailyTradeCount >= MaxDailyTrades) {
        return false;
    }
    
    // ตรวจสอบขาดทุนสูงสุด
    if(dailyProfit <= -MaxDailyLoss) {
        tradingEnabled = false;
        Comment("⚠️ การเทรดหยุดชั่วคราว - ขาดทุนเกินขีดจำกัด: $" + DoubleToString(dailyProfit, 2));
        return false;
    }
    
    // ตรวจสอบเวลาทำการ
    if(UseTimeFilter) {
        MqlDateTime dt;
        TimeToStruct(TimeCurrent(), dt);
        if(dt.hour < StartHour || dt.hour > EndHour) {
            return false;
        }
    }
    
    // ตรวจสอบ news
    if(AvoidNews) {
        MqlDateTime dt;
        TimeToStruct(TimeCurrent(), dt);
        // หลีกเลี่ยงช่วง 15:30-16:30 GMT (US news)
        if(dt.hour == 15 && dt.min >= 30) return false;
        if(dt.hour == 16 && dt.min <= 30) return false;
    }
    
    // ตรวจสอบว่ามี position เปิดอยู่แล้วหรือไม่
    if(PositionsTotal() >= 3) { // จำกัดไม่เกิน 3 positions
        return false;
    }
    
    // Cooldown period ระหว่างการเทรด - ลดเวลาให้เทรดบ่อยขึ้น
    if(TimeCurrent() - lastTradeTime < 5) { // 5 วินาที
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| หาโอกาสเทรดในทุก symbols                                          |
//+------------------------------------------------------------------+
void ScanForTradingOpportunities() {
    if(DebugMode) Print("🔍 กำลังสแกนหาโอกาสเทรด...");
    
    for(int i = 0; i < ArraySize(symbols); i++) {
        if(!symbolEnabled[i]) {
            if(DebugMode) Print("⏭️ ", symbols[i], " ถูกปิดใช้งาน");
            continue;
        }
        
        string symbol = symbols[i];
        
        if(DebugMode) Print("🔍 ตรวจสอบ ", symbol, "...");
        
        // ตรวจสอบ symbol พร้อมใช้งาน (พร้อม backup)
        string validSymbol = GetValidSymbol(symbol, i);
        if(validSymbol == "") {
            Print("❌ No valid symbol found for index: ", i);
            continue;
        }
        
        // ใช้ valid symbol
        symbol = validSymbol;
        if(DebugMode) Print("✅ ใช้ symbol: ", symbol);
        
        // รอให้ symbol sync ข้อมูล
        Sleep(50);
        
        // ตรวจสอบ spread
        double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
        double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
        
        if(ask == 0 || bid == 0) {
            Print("❌ No quotes for ", symbol, " - พยายามรีเฟรช...");
            // พยายาม refresh symbol
            SymbolSelect(symbol, false);
            Sleep(100);
            SymbolSelect(symbol, true);
            Sleep(100);
            
            // ลองอีกครั้ง
            ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
            bid = SymbolInfoDouble(symbol, SYMBOL_BID);
            
            if(ask == 0 || bid == 0) {
                Print("❌ ยังไม่มี quotes สำหรับ ", symbol, " - ข้าม");
                continue;
            }
        }
        
        double spread = SymbolInfoInteger(symbol, SYMBOL_SPREAD) * SymbolInfoDouble(symbol, SYMBOL_POINT);
        double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
        double pip_size = (digits == 5 || digits == 3) ? point * 10 : point;
        double spreadPips = spread / pip_size;
        
        double maxAllowedSpread = (symbol == "GOLDm#" || symbol == "XAUUSD" || symbol == "GOLD") ? MaxSpreadGold : MaxSpread;
        
        // เพิ่ม tolerance 50% สำหรับ spread
        if(spreadPips > maxAllowedSpread * 1.5) {
            if(DebugMode) Print("❌ ", symbol, " Spread สูงเกินไป: ", DoubleToString(spreadPips, 1), " pips (max: ", DoubleToString(maxAllowedSpread * 1.5, 1), ")");
            continue;
        }
        
        // ตรวจสอบว่ามี position ของ symbol นี้อยู่แล้วหรือไม่
        bool hasPosition = false;
        for(int j = 0; j < PositionsTotal(); j++) {
            if(PositionGetTicket(j)) {
                if(PositionGetInteger(POSITION_MAGIC) == MagicNumber && 
                   PositionGetString(POSITION_SYMBOL) == symbol) {
                    hasPosition = true;
                    break;
                }
            }
        }
        if(hasPosition) continue;
        
        // หาสัญญาณเทรด
        int signal = GetTradingSignal(symbol);
        
        if(DebugMode) Print("🎯 Signal สำหรับ ", symbol, ": ", signal);
        
        if(signal != 0) {
            if(DebugMode) Print("✅ พบสัญญาณ! กำลังเปิด order...");
            ExecuteTrade(symbol, signal);
            break; // ทำทีละ trade
        } else {
            if(DebugMode) Print(" ไม่มีสัญญาณสำหรับ ", symbol);
        }
    }
}

//+------------------------------------------------------------------+
//| Execute Trade                                                    |
//+------------------------------------------------------------------+
void ExecuteTrade(string symbol, int signal) {
    // คำนวณขนาด lot ที่เหมาะสม (ใช้ fixed lot size)
    double lots = LotSize;
    
    // ตรวจสอบขนาด lot
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    
    if(lots < minLot || lots > maxLot) {
        Print("❌ ขนาด lot ไม่ถูกต้อง: ", lots);
        return;
    }
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
    double digits = (double)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    
    // ปรับ point สำหรับ 5-digit brokers และ Gold
    double multiplier = 1.0;
    if(symbol == "GOLDmicro") {
        multiplier = 0.1; // Gold ใช้ 0.1 point เป็น 1 pip
    } else {
        multiplier = (digits == 5 || digits == 3) ? 10.0 : 1.0;
    }
    
    // คำนวณ SL/TP ที่ถูกต้อง
    double slDistance = StopLossPips * point * multiplier;
    double tpDistance = ProfitPips * point * multiplier;
    
    // ตรวจสอบและตั้งค่า filling mode ที่ถูกต้อง
    ENUM_ORDER_TYPE_FILLING filling_mode = GetSupportedFillingMode(symbol);
    
    if(signal == 1) { // Buy
        request.action = TRADE_ACTION_DEAL;
        request.symbol = symbol;
        request.volume = lots;
        request.type = ORDER_TYPE_BUY;
        request.price = ask;
        request.magic = MagicNumber;
        request.comment = "RebateFarm_Buy";
        request.deviation = 10;
        request.type_filling = filling_mode;  // เพิ่ม filling mode
        
        // ไม่ตั้ง SL/TP ตอนเปิด Order (เพื่อหลีกเลี่ยง filling mode error)
        request.sl = 0;
        request.tp = 0;
    }
    else if(signal == -1) { // Sell
        request.action = TRADE_ACTION_DEAL;
        request.symbol = symbol;
        request.volume = lots;
        request.type = ORDER_TYPE_SELL;
        request.price = bid;
        request.magic = MagicNumber;
        request.comment = "RebateFarm_Sell";
        request.deviation = 10;
        request.type_filling = filling_mode;  // เพิ่ม filling mode
        
        // ไม่ตั้ง SL/TP ตอนเปิด Order
        request.sl = 0;
        request.tp = 0;
    }
    
    if(OrderSend(request, result)) {
        if(result.retcode == TRADE_RETCODE_DONE) {
            Print("✅ Order เปิดสำเร็จ - ", symbol, " Ticket: ", result.order, 
                  " Lots: ", DoubleToString(lots, 2), " Type: ", (signal == 1 ? "BUY" : "SELL"));
            
            // ตั้ง SL/TP หลังจากเปิด Order สำเร็จ
            SetStopLossAndTakeProfit(result.order, signal, ask, bid, slDistance, tpDistance);
            
            // อัพเดทสถิติ
            dailyTradeCount++;
            lastTradeTime = TimeCurrent();
            
            // คำนวณ rebate
            double rebateRate = GetRebateRate(symbol);
            double rebate = lots * rebateRate;
            dailyRebate += rebate;
            
            // อัพเดท Monthly Rebate
            UpdateMonthlyRebate(rebate);
            
            Print("💰 Rebate เพิ่ม: $", DoubleToString(rebate, 2), 
                  " (", symbol, " ", DoubleToString(lots, 2), " lots)");
            Print("💰 Rebate รวมวันนี้: $", DoubleToString(dailyRebate, 2));
            Print("📅 Rebate รวมเดือนนี้: $", DoubleToString(monthlyRebate, 2));
            
            // เพิ่มในสถิติ
            stats.totalTrades++;
        }
    }
    else {
        Print("❌ Error เปิด order: ", result.retcode, " - ", symbol);
    }
}

//+------------------------------------------------------------------+
//| WH Fair Value Gap (FVG) Detection                               |
//+------------------------------------------------------------------+
struct FVGInfo {
    double high;
    double low;
    int direction;  // 1 = bullish FVG, -1 = bearish FVG
    int bar_index;
    bool is_valid;
    
    // Constructor
    FVGInfo() {
        high = 0;
        low = 0;
        direction = 0;
        bar_index = 0;
        is_valid = false;
    }
    
    // Copy constructor
    FVGInfo(const FVGInfo& other) {
        high = other.high;
        low = other.low;
        direction = other.direction;
        bar_index = other.bar_index;
        is_valid = other.is_valid;
    }
};

// ตรวจหา FVG ใน 3 แท่งเทียน
FVGInfo DetectFVG(string symbol, ENUM_TIMEFRAMES timeframe = PERIOD_M5) {
    FVGInfo fvg;
    fvg.high = 0;
    fvg.low = 0;
    fvg.direction = 0;
    fvg.bar_index = 0;
    fvg.is_valid = false;
    
    double high[], low[], close[], open[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);
    ArraySetAsSeries(open, true);
    
    if(CopyHigh(symbol, timeframe, 0, 10, high) < 10 ||
       CopyLow(symbol, timeframe, 0, 10, low) < 10 ||
       CopyClose(symbol, timeframe, 0, 10, close) < 10 ||
       CopyOpen(symbol, timeframe, 0, 10, open) < 10) {
        return fvg;
    }
    
    // ตรวจหา Bullish FVG (3 แท่ง: Down, Strong Up, Any)
    // เงื่อนไข: low[1] > high[3] (มี gap ระหว่างแท่งที่ 1 และ 3)
    if(low[1] > high[3] && close[2] > open[2]) { // แท่งกลางเป็น bullish
        fvg.high = low[1];
        fvg.low = high[3];
        fvg.direction = 1;
        fvg.bar_index = 2;
        fvg.is_valid = true;
    }
    // ตรวจหา Bearish FVG (3 แท่ง: Up, Strong Down, Any)
    // เงื่อนไข: high[1] < low[3] (มี gap ระหว่างแท่งที่ 1 และ 3)
    else if(high[1] < low[3] && close[2] < open[2]) { // แท่งกลางเป็น bearish
        fvg.high = low[3];
        fvg.low = high[1];
        fvg.direction = -1;
        fvg.bar_index = 2;
        fvg.is_valid = true;
    }
    
    return fvg;
}

//+------------------------------------------------------------------+
//| Basic Candlestick Pattern Detection                             |
//+------------------------------------------------------------------+

// ตรวจหา Hammer/Doji patterns
int DetectCandlestickPattern(string symbol, ENUM_TIMEFRAMES timeframe = PERIOD_M5) {
    double high[], low[], close[], open[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);
    ArraySetAsSeries(open, true);
    
    if(CopyHigh(symbol, timeframe, 0, 5, high) < 5 ||
       CopyLow(symbol, timeframe, 0, 5, low) < 5 ||
       CopyClose(symbol, timeframe, 0, 5, close) < 5 ||
       CopyOpen(symbol, timeframe, 0, 5, open) < 5) {
        return 0;
    }
    
    // ข้อมูลแท่งปัจจุบัน (index 1 = แท่งที่แล้ว)
    double o1 = open[1], h1 = high[1], l1 = low[1], c1 = close[1];
    double body = MathAbs(c1 - o1);
    double upperShadow = h1 - MathMax(o1, c1);
    double lowerShadow = MathMin(o1, c1) - l1;
    double totalRange = h1 - l1;
    
    if(totalRange == 0) return 0;
    
    // Hammer Pattern (Bullish)
    if(lowerShadow > body * 2 && upperShadow < body * 0.5 && body > 0) {
        return 1; // Bullish signal
    }
    
    // Inverted Hammer Pattern (Bearish)
    if(upperShadow > body * 2 && lowerShadow < body * 0.5 && body > 0) {
        return -1; // Bearish signal
    }
    
    // Doji Pattern (Neutral/Reversal)
    if(body < totalRange * 0.1) {
        // ดู trend ก่อนหน้า
        if(close[2] > close[3] && close[3] > close[4]) {
            return -1; // Bearish reversal
        } else if(close[2] < close[3] && close[3] < close[4]) {
            return 1; // Bullish reversal
        }
    }
    
    // Engulfing Pattern
    double o2 = open[2], c2 = close[2];
    
    // Bullish Engulfing
    if(c2 < o2 && c1 > o1 && c1 > o2 && o1 < c2) {
        return 1;
    }
    
    // Bearish Engulfing
    if(c2 > o2 && c1 < o1 && c1 < o2 && o1 > c2) {
        return -1;
    }
    
    return 0; // No pattern
}

//+------------------------------------------------------------------+
//| Support and Resistance Detection                                |
//+------------------------------------------------------------------+
double FindNearestSupport(string symbol, ENUM_TIMEFRAMES timeframe = PERIOD_M15) {
    double low[];
    ArraySetAsSeries(low, true);
    
    if(CopyLow(symbol, timeframe, 0, 50, low) < 50) return 0;
    
    double currentPrice = SymbolInfoDouble(symbol, SYMBOL_BID);
    double support = 0;
    
    // หา swing lows ที่อยู่ใต้ราคาปัจจุบัน
    for(int i = 2; i < 48; i++) {
        if(low[i] < low[i-1] && low[i] < low[i+1] && low[i] < low[i-2] && low[i] < low[i+2]) {
            if(low[i] < currentPrice && (support == 0 || low[i] > support)) {
                support = low[i];
            }
        }
    }
    
    return support;
}

double FindNearestResistance(string symbol, ENUM_TIMEFRAMES timeframe = PERIOD_M15) {
    double high[];
    ArraySetAsSeries(high, true);
    
    if(CopyHigh(symbol, timeframe, 0, 50, high) < 50) return 0;
    
    double currentPrice = SymbolInfoDouble(symbol, SYMBOL_ASK);
    double resistance = 0;
    
    // หา swing highs ที่อยู่เหนือราคาปัจจุบัน
    for(int i = 2; i < 48; i++) {
        if(high[i] > high[i-1] && high[i] > high[i+1] && high[i] > high[i-2] && high[i] > high[i+2]) {
            if(high[i] > currentPrice && (resistance == 0 || high[i] < resistance)) {
                resistance = high[i];
            }
        }
    }
    
    return resistance;
}

//+------------------------------------------------------------------+
//| Enhanced Trading Signal with FVG and Candlestick Patterns       |
//+------------------------------------------------------------------+
int GetTradingSignal(string symbol) {
    if(DebugMode) Print("🔍 Analyzing ", symbol, " for trading signals...");
    
    // Get current price for reference
    double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
    double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
    double currentPrice = (bid + ask) / 2;
    
    // === TREND FILTER: Check overall trend direction ===
    double close[];
    ArraySetAsSeries(close, true);
    if(CopyClose(symbol, PERIOD_M15, 0, 50, close) < 50) {
        if(DebugMode) Print("❌ Cannot get price data for trend analysis");
        return 0;
    }
    
    // Calculate trend using EMA 20 and EMA 50 on M15
    double ema20_sum = 0, ema50_sum = 0;
    for(int i = 0; i < 20; i++) ema20_sum += close[i];
    for(int i = 0; i < 50; i++) ema50_sum += close[i];
    
    double ema20 = ema20_sum / 20;
    double ema50 = ema50_sum / 50;
    
    bool upTrend = (ema20 > ema50 && currentPrice > ema20);
    bool downTrend = (ema20 < ema50 && currentPrice < ema20);
    
    if(DebugMode) Print("📈 Trend Analysis: EMA20=", DoubleToString(ema20, 5), " EMA50=", DoubleToString(ema50, 5), " UpTrend=", upTrend, " DownTrend=", downTrend);
    
    // === PRIORITY 1: FVG + Trend + Pattern Combination (More Selective) ===
    FVGInfo fvg = DetectFVG(symbol, PERIOD_M5);
    int pattern = DetectCandlestickPattern(symbol, PERIOD_M5);
    
    if(fvg.is_valid && pattern != 0) {
        // Check if price is within FVG zone
        bool priceInFVG = (currentPrice >= fvg.low && currentPrice <= fvg.high);
        
        // More selective: FVG + Pattern + Trend alignment
        if(fvg.direction == 1 && pattern == 1 && priceInFVG && upTrend) {
            if(DebugMode) Print("✅ STRONG BUY: Bullish FVG + Pattern + UpTrend at ", DoubleToString(currentPrice, 5));
            return 1;
        }
        
        if(fvg.direction == -1 && pattern == -1 && priceInFVG && downTrend) {
            if(DebugMode) Print("✅ STRONG SELL: Bearish FVG + Pattern + DownTrend at ", DoubleToString(currentPrice, 5));
            return -1;
        }
    }
    
    // === PRIORITY 2: Support/Resistance Bounce + Pattern ===
    double support = FindNearestSupport(symbol, PERIOD_M15);
    double resistance = FindNearestResistance(symbol, PERIOD_M15);
    
    if(pattern != 0) {
        // Support bounce with bullish pattern
        if(support > 0 && pattern == 1) {
            double distanceToSupport = MathAbs(currentPrice - support) / SymbolInfoDouble(symbol, SYMBOL_POINT);
            if(distanceToSupport <= 20) { // Within 20 pips of support
                if(DebugMode) Print("✅ BUY: Support bounce + Bullish pattern. Support: ", DoubleToString(support, 5));
                return 1;
            }
        }
        
        // Resistance bounce with bearish pattern
        if(resistance > 0 && pattern == -1) {
            double distanceToResistance = MathAbs(currentPrice - resistance) / SymbolInfoDouble(symbol, SYMBOL_POINT);
            if(distanceToResistance <= 20) { // Within 20 pips of resistance
                if(DebugMode) Print("✅ SELL: Resistance bounce + Bearish pattern. Resistance: ", DoubleToString(resistance, 5));
                return -1;
            }
        }
    }
    
    // === PRIORITY 3: MA Cross (Fallback for Rebate Generation) ===
    // Simple MA crossover for consistent rebate generation
    double ma_fast[], ma_slow[];
    ArraySetAsSeries(ma_fast, true);
    ArraySetAsSeries(ma_slow, true);
    
    // Reuse existing close array for MA calculation
    
    if(CopyClose(symbol, PERIOD_M5, 0, 20, close) >= 20) {
        // Calculate simple moving averages
        double sum_fast = 0, sum_slow = 0;
        
        for(int i = 0; i < 5; i++) sum_fast += close[i];
        for(int i = 0; i < 10; i++) sum_slow += close[i];
        
        double ma5_current = sum_fast / 5;
        double ma10_current = sum_slow / 10;
        
        // Previous MA values
        sum_fast = 0; sum_slow = 0;
        for(int i = 1; i < 6; i++) sum_fast += close[i];
        for(int i = 1; i < 11; i++) sum_slow += close[i];
        
        double ma5_prev = sum_fast / 5;
        double ma10_prev = sum_slow / 10;
        
        // MA crossover signals
        if(ma5_prev <= ma10_prev && ma5_current > ma10_current) {
            if(DebugMode) Print("📈 BUY: MA5 crosses above MA10 (Rebate signal)");
            return 1;
        }
        if(ma5_prev >= ma10_prev && ma5_current < ma10_current) {
            if(DebugMode) Print("📉 SELL: MA5 crosses below MA10 (Rebate signal)");
            return -1;
        }
    }
    
    // === PRIORITY 4: RSI Oversold/Overbought (Additional Rebate Signal) ===
    double rsi[];
    ArraySetAsSeries(rsi, true);
    
    // Simple RSI calculation for fallback
    if(CopyClose(symbol, PERIOD_M5, 0, 15, close) >= 15) {
        double gain = 0, loss = 0;
        for(int i = 1; i < 15; i++) {
            double change = close[i-1] - close[i];
            if(change > 0) gain += change;
            else loss += MathAbs(change);
        }
        
        if(loss > 0) {
            double rs = gain / loss;
            double rsi_value = 100 - (100 / (1 + rs));
            
            if(rsi_value < 30) {
                if(DebugMode) Print("📈 BUY: RSI Oversold (", DoubleToString(rsi_value, 2), ")");
                return 1;
            }
            if(rsi_value > 70) {
                if(DebugMode) Print("📉 SELL: RSI Overbought (", DoubleToString(rsi_value, 2), ")");
                return -1;
            }
        }
    }
    
    if(DebugMode) Print("⚪ No clear signal for ", symbol);
    return 0; // No signal
}





//+------------------------------------------------------------------+
//| Calculate Lot Size based on Risk Management                     |
//+------------------------------------------------------------------+
double CalculateLotSize(string symbol) {
    // Use fixed lot size for micro account
    double lotSize = LotSize;
    
    // Get symbol info
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
    
    // Ensure lot size is within limits
    if(lotSize < minLot) lotSize = minLot;
    if(lotSize > maxLot) lotSize = maxLot;
    
    // Round to lot step
    lotSize = MathRound(lotSize / lotStep) * lotStep;
    
    // Additional risk check - don't risk more than 2% of balance per trade
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double riskAmount = balance * 0.02; // 2% risk
    
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double digits = (double)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    double multiplier = (digits == 5 || digits == 3) ? 10.0 : 1.0;
    double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
    
    if(tickValue > 0) {
        double stopLossDistance = StopLossPips * point * multiplier;
        double maxLotByRisk = riskAmount / (stopLossDistance * tickValue / point);
        
        if(maxLotByRisk > 0 && maxLotByRisk < lotSize) {
            lotSize = maxLotByRisk;
            lotSize = MathRound(lotSize / lotStep) * lotStep;
        }
    }
    
    if(DebugMode) Print("💰 Calculated lot size for ", symbol, ": ", DoubleToString(lotSize, 2));
    return lotSize;
}

//+------------------------------------------------------------------+
//| Execute Trade                                                    |
//+------------------------------------------------------------------+
void ExecuteTrade(string symbol, int signal, double lots) {
    if(DebugMode) Print("🚀 Executing trade: ", symbol, " Signal: ", signal, " Lots: ", DoubleToString(lots, 2));
    
    // Get current prices
    double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
    
    if(ask == 0 || bid == 0) {
        Print("❌ Invalid prices for ", symbol, " - Ask: ", ask, " Bid: ", bid);
        return;
    }
    
    // Calculate pip size for SL/TP
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double digits = (double)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    double pip_size = (digits == 5 || digits == 3) ? point * 10 : point;
    
    // Prepare trade request
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = lots;
    request.magic = MagicNumber;
    request.comment = "RebateFarm_v2.1";
    request.type_filling = GetSupportedFillingMode(symbol);
    
    if(signal == 1) { // BUY
        request.type = ORDER_TYPE_BUY;
        request.price = ask;
        request.sl = ask - (StopLossPips * pip_size);
        request.tp = ask + (ProfitPips * pip_size);
    } else { // SELL
        request.type = ORDER_TYPE_SELL;
        request.price = bid;
        request.sl = bid + (StopLossPips * pip_size);
        request.tp = bid - (ProfitPips * pip_size);
    }
    
    // Send order
    if(OrderSend(request, result)) {
        if(result.retcode == TRADE_RETCODE_DONE) {
            Print("✅ Trade opened successfully!");
            Print("📊 Symbol: ", symbol);
            Print("📊 Type: ", (signal == 1) ? "BUY" : "SELL");
            Print("📊 Volume: ", DoubleToString(lots, 2));
            Print("📊 Price: ", DoubleToString(request.price, 5));
            Print("📊 SL: ", DoubleToString(request.sl, 5));
            Print("📊 TP: ", DoubleToString(request.tp, 5));
            Print("📊 Ticket: ", result.order);
            
            // Update statistics
            dailyTradeCount++;
            lastTradeTime = TimeCurrent();
            
            // Calculate rebate
            double rebateRate = GetRebateRate(symbol);
            double rebate = lots * rebateRate;
            dailyRebate += rebate;
            
            // Update Monthly Rebate
            UpdateMonthlyRebate(rebate);
            
            Print("💰 Rebate earned: $", DoubleToString(rebate, 2), 
                  " (Rate: $", DoubleToString(rebateRate, 2), "/lot)");
            Print("💰 Daily rebate total: $", DoubleToString(dailyRebate, 2));
            Print("📅 Monthly rebate total: $", DoubleToString(monthlyRebate, 2));
            
            // Update statistics
            stats.totalTrades++;
        }
        else {
            Print("❌ Trade failed - Error: ", result.retcode, " (", GetTradeErrorDescription(result.retcode), ")");
            Print("📊 Symbol: ", symbol, " Signal: ", signal, " Lots: ", lots);
        }
    }
    else {
        Print("❌ OrderSend failed for ", symbol);
    }
}

//+------------------------------------------------------------------+
//| Get Trade Error Description                                      |
//+------------------------------------------------------------------+
string GetTradeErrorDescription(uint retcode) {
    switch(retcode) {
        case TRADE_RETCODE_REQUOTE: return "Requote";
        case TRADE_RETCODE_REJECT: return "Request rejected";
        case TRADE_RETCODE_CANCEL: return "Request canceled";
        case TRADE_RETCODE_PLACED: return "Order placed";
        case TRADE_RETCODE_DONE: return "Done";
        case TRADE_RETCODE_DONE_PARTIAL: return "Done partially";
        case TRADE_RETCODE_ERROR: return "Common error";
        case TRADE_RETCODE_TIMEOUT: return "Timeout";
        case TRADE_RETCODE_INVALID: return "Invalid request";
        case TRADE_RETCODE_INVALID_VOLUME: return "Invalid volume";
        case TRADE_RETCODE_INVALID_PRICE: return "Invalid price";
        case TRADE_RETCODE_INVALID_STOPS: return "Invalid stops";
        case TRADE_RETCODE_TRADE_DISABLED: return "Trade disabled";
        case TRADE_RETCODE_MARKET_CLOSED: return "Market closed";
        case TRADE_RETCODE_NO_MONEY: return "No money";
        case TRADE_RETCODE_PRICE_CHANGED: return "Price changed";
        case TRADE_RETCODE_PRICE_OFF: return "Off quotes";
        case TRADE_RETCODE_INVALID_EXPIRATION: return "Invalid expiration";
        case TRADE_RETCODE_ORDER_CHANGED: return "Order changed";
        case TRADE_RETCODE_TOO_MANY_REQUESTS: return "Too many requests";
        case TRADE_RETCODE_NO_CHANGES: return "No changes";
        case TRADE_RETCODE_SERVER_DISABLES_AT: return "Auto trading disabled by server";
        case TRADE_RETCODE_CLIENT_DISABLES_AT: return "Auto trading disabled by client";
        case TRADE_RETCODE_LOCKED: return "Request locked";
        case TRADE_RETCODE_FROZEN: return "Order or position frozen";
        case TRADE_RETCODE_INVALID_FILL: return "Invalid fill";
        case TRADE_RETCODE_CONNECTION: return "Connection problem";
        case TRADE_RETCODE_ONLY_REAL: return "Only real accounts";
        case TRADE_RETCODE_LIMIT_ORDERS: return "Limit orders limit reached";
        case TRADE_RETCODE_LIMIT_VOLUME: return "Volume limit reached";
        default: return "Unknown error (" + IntegerToString(retcode) + ")";
    }
}

//+------------------------------------------------------------------+
//| Get Rebate Rate                                                  |
//+------------------------------------------------------------------+
double GetRebateRate(string symbol) {
    if(symbol == "EURUSD") return 5.0;
    if(symbol == "GBPUSD") return 6.0;
    if(symbol == "USDJPY") return 5.5;
    if(symbol == "GOLDmicro") return 7.0;
    return 5.0; // default rate
}

//+------------------------------------------------------------------+
//| Set SL and TP after opening position                            |
//+------------------------------------------------------------------+
void SetStopLossAndTakeProfit(ulong ticket, int signal, double ask, double bid, double slDistance, double tpDistance) {
    Sleep(100); // รอให้ position เสถียร
    
    if(!PositionSelectByTicket(ticket)) {
        Print("❌ ไม่พบ position ticket: ", ticket);
        return;
    }
    
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double sl = 0, tp = 0;
    
    if(signal == 1) { // BUY
        sl = openPrice - slDistance;
        tp = openPrice + tpDistance;
    } else { // SELL
        sl = openPrice + slDistance;
        tp = openPrice - tpDistance;
    }
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_SLTP;
    request.position = ticket;
    request.sl = sl;
    request.tp = tp;
    
    if(OrderSend(request, result)) {
        if(result.retcode == TRADE_RETCODE_DONE) {
            Print("✅ ตั้ง SL/TP สำเร็จ - Ticket: ", ticket, 
                  " SL: ", DoubleToString(sl, 5), " TP: ", DoubleToString(tp, 5));
        } else {
            Print("❌ ไม่สามารถตั้ง SL/TP - Error: ", result.retcode, " Ticket: ", ticket);
        }
    }
}
//+------------------------------------------------------------------+
//| Position Management Functions                                   |
//+------------------------------------------------------------------+
void ManageOpenPositions() {
    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        ulong ticket = PositionGetTicket(i);
        if(PositionSelectByTicket(ticket)) {
            if(PositionGetInteger(POSITION_MAGIC) == MagicNumber) {
                
                string symbol = PositionGetString(POSITION_SYMBOL);
                double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
                double currentPrice = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                                    SymbolInfoDouble(symbol, SYMBOL_BID) : 
                                    SymbolInfoDouble(symbol, SYMBOL_ASK);
                
                double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
                double digits = (double)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
                double multiplier = (digits == 5 || digits == 3) ? 10.0 : 1.0;
                
                bool isBuy = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
                double pips = 0;
                
                if(isBuy) {
                    pips = (currentPrice - openPrice) / (point * multiplier);
                } else {
                    pips = (openPrice - currentPrice) / (point * multiplier);
                }
                
                // 💰 PROFIT MANAGEMENT - ปรับปรุงเพื่อกำไรมากขึ้น
                
                // 1. Profit Lock - ล็อคกำไรเมื่อถึง 70% ของ TP
                if(UseProfitLock && pips >= (ProfitPips * ProfitLockPercent / 100.0)) {
                    double lockLevel = ProfitPips * (ProfitLockPercent / 100.0);
                    ApplyProfitLock(ticket, lockLevel);
                }
                
                // 2. Trailing Stop - เริ่มเมื่อกำไรถึง MinProfitForTrailing
                else if(UseTrailingStop && pips >= MinProfitForTrailing) {
                    ApplyTrailingStop(ticket, pips);
                }
                
                // 3. Breakeven - เลื่อน SL ไป Breakeven เมื่อกำไรพอ
                else if(UseBreakevenStrategy && pips >= 5.0) {
                    ModifyToBreakeven(ticket);
                }
                
                // 4. Early Close สำหรับกำไรเล็กน้อย (2-4 pips)
                else if(pips >= 2.0 && pips <= 4.0) {
                    // ปิดกำไรเล็กน้อยเพื่อรับ rebate
                    ClosePosition(ticket, "Small Profit Lock");
                }
                
                // 5. Loss Management - จัดการขาดทุน
                else if(pips <= -StopLossPips) {
                    ClosePosition(ticket, "Stop Loss Hit");
                }
                
                // 6. Emergency Close - ขาดทุนมากเกินไป
                else if(pips <= -(StopLossPips + 5)) {
                    ClosePosition(ticket, "Emergency Stop");
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Apply Profit Lock - ล็อคกำไรเมื่อถึงเป้าหมาย                      |
//+------------------------------------------------------------------+
void ApplyProfitLock(ulong ticket, double lockLevel) {
    if(!PositionSelectByTicket(ticket)) return;
    
    string symbol = PositionGetString(POSITION_SYMBOL);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentSL = PositionGetDouble(POSITION_SL);
    bool isBuy = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
    
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double digits = (double)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    double multiplier = (digits == 5 || digits == 3) ? 10.0 : 1.0;
    
    double newSL = 0;
    
    if(isBuy) {
        newSL = openPrice + (lockLevel * point * multiplier);
        // ตรวจสอบว่า SL ใหม่ดีกว่า SL เดิม
        if(currentSL == 0 || newSL > currentSL) {
            ModifyStopLoss(ticket, newSL, "Profit Lock");
        }
    } else {
        newSL = openPrice - (lockLevel * point * multiplier);
        // ตรวจสอบว่า SL ใหม่ดีกว่า SL เดิม
        if(currentSL == 0 || newSL < currentSL) {
            ModifyStopLoss(ticket, newSL, "Profit Lock");
        }
    }
}

//+------------------------------------------------------------------+
//| Apply Trailing Stop - ติดตามกำไรด้วย Trailing Stop               |
//+------------------------------------------------------------------+
void ApplyTrailingStop(ulong ticket, double currentPips) {
    if(!PositionSelectByTicket(ticket)) return;
    
    string symbol = PositionGetString(POSITION_SYMBOL);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentSL = PositionGetDouble(POSITION_SL);
    double currentPrice = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                         SymbolInfoDouble(symbol, SYMBOL_BID) : 
                         SymbolInfoDouble(symbol, SYMBOL_ASK);
    
    bool isBuy = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
    
    double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
    double digits = (double)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
    double multiplier = (digits == 5 || digits == 3) ? 10.0 : 1.0;
    
    double trailingDistance = TrailingStopPips * point * multiplier;
    double newSL = 0;
    
    if(isBuy) {
        newSL = currentPrice - trailingDistance;
        // อัพเดท SL เฉพาะเมื่อ SL ใหม่ดีกว่า SL เดิม
        if(currentSL == 0 || newSL > currentSL) {
            ModifyStopLoss(ticket, newSL, "Trailing Stop");
        }
    } else {
        newSL = currentPrice + trailingDistance;
        // อัพเดท SL เฉพาะเมื่อ SL ใหม่ดีกว่า SL เดิม
        if(currentSL == 0 || newSL < currentSL) {
            ModifyStopLoss(ticket, newSL, "Trailing Stop");
        }
    }
}

//+------------------------------------------------------------------+
//| Modify Stop Loss - ปรับปรุง SL ด้วยการตรวจสอบที่ดีขึ้น            |
//+------------------------------------------------------------------+
void ModifyStopLoss(ulong ticket, double newSL, string reason) {
    if(!PositionSelectByTicket(ticket)) return;
    
    string symbol = PositionGetString(POSITION_SYMBOL);
    double currentTP = PositionGetDouble(POSITION_TP);
    
    // ตรวจสอบ minimum stop level
    double minStopLevel = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL) * SymbolInfoDouble(symbol, SYMBOL_POINT);
    double currentPrice = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                         SymbolInfoDouble(symbol, SYMBOL_BID) : 
                         SymbolInfoDouble(symbol, SYMBOL_ASK);
    
    // ตรวจสอบระยะห่างขั้นต่ำ
    if(MathAbs(currentPrice - newSL) < minStopLevel) {
        if(DebugMode) Print("⚠️ SL ใกล้ราคาปัจจุบันเกินไป - Ticket: ", ticket);
        return;
    }
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_SLTP;
    request.position = ticket;
    request.sl = NormalizeDouble(newSL, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
    request.tp = currentTP;
    
    if(OrderSend(request, result)) {
        if(result.retcode == TRADE_RETCODE_DONE) {
            Print("✅ ", reason, " - Ticket: ", ticket, " SL: ", DoubleToString(newSL, 5));
        } else {
            Print("❌ Error ", reason, " - ", result.retcode, " Ticket: ", ticket);
        }
    }
}

void ClosePosition(ulong ticket, string reason) {
    if(!PositionSelectByTicket(ticket)) return;
    
    // ป้องกันการเรียกซ้ำ - ตรวจสอบว่า position ยังมีอยู่จริงหรือไม่
    static ulong lastClosedTicket = 0;
    static datetime lastCloseTime = 0;
    datetime currentTime = TimeCurrent();
    
    if(ticket == lastClosedTicket && (currentTime - lastCloseTime) < 5) {
        if(DebugMode) Print("⚠️ ป้องกันการปิด position ซ้ำ - Ticket: ", ticket);
        return;
    }
    
    string symbol = PositionGetString(POSITION_SYMBOL);
    double profit = PositionGetDouble(POSITION_PROFIT);
    
    // ตรวจสอบว่า symbol ยังใช้งานได้หรือไม่
    if(!SymbolSelect(symbol, true)) {
        Print("❌ ไม่สามารถเลือก symbol: ", symbol);
        return;
    }
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = symbol;
    request.volume = PositionGetDouble(POSITION_VOLUME);
    request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                  ORDER_TYPE_SELL : ORDER_TYPE_BUY;
    request.price = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                   SymbolInfoDouble(symbol, SYMBOL_BID) : 
                   SymbolInfoDouble(symbol, SYMBOL_ASK);
    request.position = ticket;
    request.magic = MagicNumber;
    request.comment = "RebateFarm_Close_" + reason;
    request.deviation = 10;
    
    // ใช้ GetSupportedFillingMode เพื่อป้องกัน "Unsupported filling mode"
    request.type_filling = GetSupportedFillingMode(symbol);
    
    // ลองปิด position สูงสุด 3 ครั้ง
    int maxRetries = 3;
    bool success = false;
    
    for(int retry = 0; retry < maxRetries && !success; retry++) {
        if(OrderSend(request, result)) {
            if(result.retcode == TRADE_RETCODE_DONE) {
                Print("✅ Position ปิดสำเร็จ - Ticket: ", ticket, " เหตุผล: ", reason, 
                      " P&L: $", DoubleToString(profit, 2));
                
                // อัพเดทสถิติ
                dailyProfit += profit;
                
                if(profit > 0) {
                    stats.winTrades++;
                } else {
                    stats.lossTrades++;
                }
                
                // บันทึกการปิด position เพื่อป้องกันการเรียกซ้ำ
                lastClosedTicket = ticket;
                lastCloseTime = currentTime;
                success = true;
            }
            else {
                Print("❌ Error ปิด position (ครั้งที่ ", retry + 1, "): ", result.retcode, " - ", result.comment);
                
                // หากเป็น filling mode error ให้ลองใช้ filling mode อื่น
                if(result.retcode == TRADE_RETCODE_INVALID_FILL) {
                    if(request.type_filling == ORDER_FILLING_FOK) {
                        request.type_filling = ORDER_FILLING_IOC;
                    } else if(request.type_filling == ORDER_FILLING_IOC) {
                        request.type_filling = ORDER_FILLING_RETURN;
                    } else {
                        request.type_filling = ORDER_FILLING_FOK;
                    }
                    Print("🔄 เปลี่ยน filling mode เป็น: ", EnumToString(request.type_filling));
                }
                
                // รอสักครู่ก่อนลองใหม่
                Sleep(100);
            }
        }
        else {
            Print("❌ ไม่สามารถส่ง order ปิด position - Ticket: ", ticket);
            break;
        }
    }
    
    if(!success) {
        Print("💥 ไม่สามารถปิด position ได้หลังจากพยายาม ", maxRetries, " ครั้ง - Ticket: ", ticket);
        // บันทึกเพื่อป้องกันการพยายามปิดซ้ำ
        lastClosedTicket = ticket;
        lastCloseTime = currentTime;
    }
}

void ModifyToBreakeven(ulong ticket) {
    if(!PositionSelectByTicket(ticket)) return;
    
    // ป้องกันการแก้ไข SL ซ้ำ
    static ulong lastModifiedTicket = 0;
    static datetime lastModifyTime = 0;
    datetime currentTime = TimeCurrent();
    
    if(ticket == lastModifiedTicket && (currentTime - lastModifyTime) < 10) {
        if(DebugMode) Print("⚠️ ป้องกันการแก้ไข SL ซ้ำ - Ticket: ", ticket);
        return;
    }
    
    string symbol = PositionGetString(POSITION_SYMBOL);
    double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
    double currentSL = PositionGetDouble(POSITION_SL);
    double currentTP = PositionGetDouble(POSITION_TP);
    
    // ตรวจสอบว่าต้องแก้ไข SL หรือไม่
    bool needModify = false;
    double newSL = openPrice;
    
    // ตรวจสอบ minimum stop level
    double minStopLevel = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL) * SymbolInfoDouble(symbol, SYMBOL_POINT);
    double currentPrice = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 
                         SymbolInfoDouble(symbol, SYMBOL_BID) : 
                         SymbolInfoDouble(symbol, SYMBOL_ASK);
    
    if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) {
        // BUY position: SL ต้องต่ำกว่า open price และห่างจาก current price มากพอ
        if(currentSL < openPrice && (currentPrice - newSL) > minStopLevel) {
            needModify = true;
        }
    } else {
        // SELL position: SL ต้องสูงกว่า open price และห่างจาก current price มากพอ
        if(currentSL > openPrice && (newSL - currentPrice) > minStopLevel) {
            needModify = true;
        }
    }
    
    // ตรวจสอบว่า SL ใหม่ไม่ใกล้กับ SL ปัจจุบันมากเกินไป
    if(MathAbs(newSL - currentSL) < SymbolInfoDouble(symbol, SYMBOL_POINT) * 2) {
        needModify = false;
    }
    
    if(needModify) {
        MqlTradeRequest request = {};
        MqlTradeResult result = {};
        
        request.action = TRADE_ACTION_SLTP;
        request.position = ticket;
        request.sl = NormalizeDouble(newSL, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS));
        request.tp = currentTP; // รักษา TP เดิม
        
        // ลองแก้ไขสูงสุด 2 ครั้ง
        int maxRetries = 2;
        bool success = false;
        
        for(int retry = 0; retry < maxRetries && !success; retry++) {
            if(OrderSend(request, result)) {
                if(result.retcode == TRADE_RETCODE_DONE) {
                    Print("✅ แก้ไข SL เป็น Breakeven - Ticket: ", ticket, 
                          " SL: ", DoubleToString(request.sl, 5));
                    
                    // บันทึกการแก้ไข
                    lastModifiedTicket = ticket;
                    lastModifyTime = currentTime;
                    success = true;
                }
                else {
                    Print("❌ Error แก้ไข SL (ครั้งที่ ", retry + 1, "): ", result.retcode, " - ", result.comment);
                    
                    // หากเป็น invalid stops ให้หยุดการพยายาม
                    if(result.retcode == TRADE_RETCODE_INVALID_STOPS) {
                        Print("⚠️ Invalid stops - หยุดการแก้ไข SL สำหรับ Ticket: ", ticket);
                        break;
                    }
                    
                    Sleep(100);
                }
            }
            else {
                Print("❌ ไม่สามารถส่ง order แก้ไข SL - Ticket: ", ticket);
                break;
            }
        }
        
        if(!success) {
            // บันทึกเพื่อป้องกันการพยายามแก้ไขซ้ำ
            lastModifiedTicket = ticket;
            lastModifyTime = currentTime;
        }
    }
}

//+------------------------------------------------------------------+
//| Monthly Rebate Tracking Functions                               |
//+------------------------------------------------------------------+
void InitializeMonthlyRebate() {
    MqlDateTime dt;
    TimeCurrent(dt);
    
    currentMonth = dt.mon;
    currentYear = dt.year;
    
    // โหลดข้อมูล rebate รายเดือนจากไฟล์
    LoadMonthlyRebateData();
    
    Print("📅 เริ่มต้นระบบติดตาม Rebate รายเดือน - ", dt.mon, "/", dt.year);
    Print("💰 Rebate เดือนนี้: $", DoubleToString(monthlyRebate, 2));
}

void CheckMonthChange() {
    MqlDateTime dt;
    TimeCurrent(dt);
    
    // ตรวจสอบว่าเปลี่ยนเดือนหรือไม่
    if(dt.mon != currentMonth || dt.year != currentYear) {
        // บันทึกข้อมูลเดือนเก่า
        SaveMonthlyRebateData();
        
        Print("🗓️ เปลี่ยนเดือนใหม่! เดือนเก่า: ", currentMonth, "/", currentYear, 
              " Rebate รวม: $", DoubleToString(monthlyRebate, 2));
        
        // รีเซ็ตข้อมูลสำหรับเดือนใหม่
        currentMonth = dt.mon;
        currentYear = dt.year;
        monthlyRebate = 0;
        
        Print("🆕 เริ่มเดือนใหม่: ", currentMonth, "/", currentYear);
    }
}

void UpdateMonthlyRebate(double dailyRebateAmount) {
    CheckMonthChange();
    monthlyRebate += dailyRebateAmount;
    
    if(DebugMode) {
        Print("📈 อัพเดท Monthly Rebate: +$", DoubleToString(dailyRebateAmount, 2), 
              " รวมเดือนนี้: $", DoubleToString(monthlyRebate, 2));
    }
}

void LoadMonthlyRebateData() {
    int fileHandle = FileOpen(monthlyRebateFile, FILE_READ | FILE_CSV);
    
    if(fileHandle != INVALID_HANDLE) {
        string line = "";
        
        // อ่านหาข้อมูลเดือนปัจจุบัน
        while(!FileIsEnding(fileHandle)) {
            line = FileReadString(fileHandle);
            string data[];
            
            if(StringSplit(line, ',', data) >= 3) {
                int fileYear = (int)StringToInteger(data[0]);
                int fileMonth = (int)StringToInteger(data[1]);
                double fileRebate = StringToDouble(data[2]);
                
                if(fileYear == currentYear && fileMonth == currentMonth) {
                    monthlyRebate = fileRebate;
                    Print("📂 โหลดข้อมูล Monthly Rebate: ", fileMonth, "/", fileYear, 
                          " = $", DoubleToString(monthlyRebate, 2));
                    break;
                }
            }
        }
        
        FileClose(fileHandle);
    } else {
        Print("📝 สร้างไฟล์ Monthly Rebate ใหม่: ", monthlyRebateFile);
        monthlyRebate = 0;
    }
}

void SaveMonthlyRebateData() {
    // อ่านข้อมูลเก่าทั้งหมด
    string allData = "";
    bool foundCurrentMonth = false;
    
    int readHandle = FileOpen(monthlyRebateFile, FILE_READ | FILE_TXT);
    if(readHandle != INVALID_HANDLE) {
        while(!FileIsEnding(readHandle)) {
            string line = FileReadString(readHandle);
            string data[];
            
            if(StringSplit(line, ',', data) >= 3) {
                int fileYear = (int)StringToInteger(data[0]);
                int fileMonth = (int)StringToInteger(data[1]);
                
                if(fileYear == currentYear && fileMonth == currentMonth) {
                    // อัพเดทข้อมูลเดือนปัจจุบัน
                    allData += IntegerToString(currentYear) + "," + 
                              IntegerToString(currentMonth) + "," + 
                              DoubleToString(monthlyRebate, 2) + "\n";
                    foundCurrentMonth = true;
                } else {
                    // เก็บข้อมูลเดือนอื่นๆ
                    allData += line + "\n";
                }
            }
        }
        FileClose(readHandle);
    }
    
    // ถ้าไม่พบข้อมูลเดือนปัจจุบัน ให้เพิ่มใหม่
    if(!foundCurrentMonth) {
        allData += IntegerToString(currentYear) + "," + 
                  IntegerToString(currentMonth) + "," + 
                  DoubleToString(monthlyRebate, 2) + "\n";
    }
    
    // เขียนข้อมูลทั้งหมดกลับไปในไฟล์
    int writeHandle = FileOpen(monthlyRebateFile, FILE_WRITE | FILE_TXT);
    if(writeHandle != INVALID_HANDLE) {
        FileWriteString(writeHandle, allData);
        FileClose(writeHandle);
        
        Print("💾 บันทึก Monthly Rebate: ", currentMonth, "/", currentYear, 
              " = $", DoubleToString(monthlyRebate, 2));
    } else {
        Print("❌ ไม่สามารถบันทึกไฟล์ Monthly Rebate ได้");
    }
}

string GetMonthlyRebateHistory() {
    string history = "";
    double totalAllMonths = 0;
    int monthCount = 0;
    
    int fileHandle = FileOpen(monthlyRebateFile, FILE_READ | FILE_TXT);
    if(fileHandle != INVALID_HANDLE) {
        while(!FileIsEnding(fileHandle)) {
            string line = FileReadString(fileHandle);
            string data[];
            
            if(StringSplit(line, ',', data) >= 3) {
                int fileYear = (int)StringToInteger(data[0]);
                int fileMonth = (int)StringToInteger(data[1]);
                double fileRebate = StringToDouble(data[2]);
                
                string monthName = GetMonthName(fileMonth);
                history += "║ • " + monthName + " " + IntegerToString(fileYear) + ": $" + DoubleToString(fileRebate, 2);
                
                // เพิ่มไอคอนสำหรับเดือนปัจจุบัน
                if(fileYear == currentYear && fileMonth == currentMonth) {
                    history += " 📍";
                }
                
                // เพิ่มช่องว่างให้พอดี
                int spaces = 35 - StringLen(monthName + " " + IntegerToString(fileYear) + ": $" + DoubleToString(fileRebate, 2));
                for(int i = 0; i < spaces; i++) history += " ";
                history += "║\n";
                
                totalAllMonths += fileRebate;
                monthCount++;
            }
        }
        FileClose(fileHandle);
    }
    
    // เพิ่มสถิติรวม
    if(monthCount > 0) {
        double avgPerMonth = totalAllMonths / monthCount;
        history += "╠══════════════════════════════════════════════════════════╣\n";
        history += "║ 📊 สถิติรวม: " + IntegerToString(monthCount) + " เดือน";
        int spaces = 42 - StringLen("สถิติรวม: " + IntegerToString(monthCount) + " เดือน");
        for(int i = 0; i < spaces; i++) history += " ";
        history += "║\n";
        history += "║ 💰 รวมทั้งหมด: $" + DoubleToString(totalAllMonths, 2);
        spaces = 38 - StringLen("รวมทั้งหมด: $" + DoubleToString(totalAllMonths, 2));
        for(int i = 0; i < spaces; i++) history += " ";
        history += "║\n";
        history += "║ 📈 เฉลี่ยต่อเดือน: $" + DoubleToString(avgPerMonth, 2);
        spaces = 35 - StringLen("เฉลี่ยต่อเดือน: $" + DoubleToString(avgPerMonth, 2));
        for(int i = 0; i < spaces; i++) history += " ";
        history += "║\n";
    }
    
    return history;
}

string GetMonthName(int month) {
    switch(month) {
        case 1: return "ม.ค.";
        case 2: return "ก.พ.";
        case 3: return "มี.ค.";
        case 4: return "เม.ย.";
        case 5: return "พ.ค.";
        case 6: return "มิ.ย.";
        case 7: return "ก.ค.";
        case 8: return "ส.ค.";
        case 9: return "ก.ย.";
        case 10: return "ต.ค.";
        case 11: return "พ.ย.";
        case 12: return "ธ.ค.";
        default: return "N/A";
    }
}

string GetMonthlyRebateReport() {
    string report = "\n";
    report += "╔══════════════════════════════════════════════════════════╗\n";
    report += "║                📅 MONTHLY REBATE REPORT                 ║\n";
    report += "╠══════════════════════════════════════════════════════════╣\n";
    
    // แสดงข้อมูลเดือนปัจจุบัน
    MqlDateTime dt;
    TimeCurrent(dt);
    double avgPerDay = (dt.day > 0) ? monthlyRebate / dt.day : 0;
    double projectedMonthly = avgPerDay * 30;
    
    report += "║ 🎯 เดือนปัจจุบัน: " + GetMonthName(currentMonth) + " " + IntegerToString(currentYear);
    int spaces = 32 - StringLen("เดือนปัจจุบัน: " + GetMonthName(currentMonth) + " " + IntegerToString(currentYear));
    for(int i = 0; i < spaces; i++) report += " ";
    report += "║\n";
    
    report += "║ 💰 Rebate เดือนนี้: $" + DoubleToString(monthlyRebate, 2);
    spaces = 35 - StringLen("Rebate เดือนนี้: $" + DoubleToString(monthlyRebate, 2));
    for(int i = 0; i < spaces; i++) report += " ";
    report += "║\n";
    
    report += "║ 📈 เฉลี่ยต่อวัน: $" + DoubleToString(avgPerDay, 2);
    spaces = 37 - StringLen("เฉลี่ยต่อวัน: $" + DoubleToString(avgPerDay, 2));
    for(int i = 0; i < spaces; i++) report += " ";
    report += "║\n";
    
    report += "║ 🎯 ประมาณการสิ้นเดือน: $" + DoubleToString(projectedMonthly, 2);
    spaces = 28 - StringLen("ประมาณการสิ้นเดือน: $" + DoubleToString(projectedMonthly, 2));
    for(int i = 0; i < spaces; i++) report += " ";
    report += "║\n";
    
    report += "╠══════════════════════════════════════════════════════════╣\n";
    report += "║ 📋 ประวัติ Rebate รายเดือน:                              ║\n";
    report += "╠══════════════════════════════════════════════════════════╣\n";
    
    // เพิ่มประวัติทุกเดือน
    report += GetMonthlyRebateHistory();
    
    report += "╚══════════════════════════════════════════════════════════╝\n";
    
    return report;
}

//+------------------------------------------------------------------+
//| Dashboard Functions                                             |
//+------------------------------------------------------------------+
void CreateDashboard() {
    int x = DashboardX;
    int y = DashboardY;
    
    // สร้าง background
    CreateRectangle("bg_main", x, y, 300, 400, DashboardColor);
    CreateRectangle("bg_header", x, y, 300, 40, clrNavy);
    
    // สร้าง labels
    CreateLabel("title", "🏆 REBATE FARM PRO v2.1", x + 10, y + 15, clrGold, 12);
    
    // Rebate Section
    CreateLabel("rebate_title", "💰 REBATE STATUS", x + 10, y + 55, clrYellow, 10);
    CreateLabel("daily_rebate", "วันนี้: $0.00", x + 15, y + 75, clrWhite, 9);
    CreateLabel("target_rebate", "เป้าหมาย: $" + DoubleToString(TargetRebateDaily, 0), x + 15, y + 90, clrWhite, 9);
    CreateLabel("progress_rebate", "ความคืบหน้า: 0%", x + 15, y + 105, clrWhite, 9);
    CreateLabel("monthly_rebate", "📅 เดือนนี้: $0.00", x + 15, y + 120, clrGold, 9);
    
    // Trading Section
    CreateLabel("trading_title", "📊 TRADING STATUS", x + 10, y + 160, clrAqua, 10);
    CreateLabel("trades_today", "เทรดวันนี้: 0", x + 15, y + 180, clrWhite, 9);
    CreateLabel("lots_today", "Lots วันนี้: 0.00", x + 15, y + 195, clrWhite, 9);
    CreateLabel("profit_today", "กำไรวันนี้: $0.00", x + 15, y + 210, clrWhite, 9);
    CreateLabel("win_rate", "Win Rate: 0%", x + 15, y + 225, clrWhite, 9);
    CreateLabel("status", "สถานะ: รอสัญญาณ", x + 15, y + 240, clrOrange, 9);
    
    // Risk Section
    CreateLabel("risk_title", "⚠️ RISK MANAGEMENT", x + 10, y + 270, clrOrangeRed, 10);
    CreateLabel("drawdown", "Drawdown: 0%", x + 15, y + 290, clrWhite, 9);
    CreateLabel("risk_level", "ระดับเสี่ยง: ต่ำ", x + 15, y + 305, clrLime, 9);
    CreateLabel("positions", "Positions: 0", x + 15, y + 320, clrWhite, 9);
    
    // Stats Section
    CreateLabel("stats_title", "📈 STATISTICS", x + 10, y + 360, clrLightBlue, 10);
    CreateLabel("account_balance", "ยอดเงิน: $" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2), x + 15, y + 380, clrWhite, 8);
    CreateLabel("equity", "Equity: $" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2), x + 15, y + 395, clrWhite, 8);
    
    dashboard_created = true;
}

void UpdateDashboard() {
    if(!dashboard_created) return;
    
    // คำนวณค่าต่างๆ
    double rebateProgress = (dailyRebate / TargetRebateDaily) * 100;
    double currentDrawdown = 0;
    if(accountBalance > 0) {
        currentDrawdown = ((accountBalance - accountEquity) / accountBalance) * 100;
    }
    double totalLots = dailyTradeCount * LotSize;
    double winRate = (stats.totalTrades > 0) ? ((double)stats.winTrades / stats.totalTrades) * 100 : 0;
    
    // อัพเดท Rebate Section
    UpdateLabel("daily_rebate", "วันนี้: $" + DoubleToString(dailyRebate, 2));
    UpdateLabel("progress_rebate", "ความคืบหน้า: " + DoubleToString(rebateProgress, 1) + "%");
    
    // อัพเดท Monthly Rebate
    MqlDateTime dt;
    TimeCurrent(dt);
    string monthText = IntegerToString(dt.mon) + "/" + IntegerToString(dt.year);
    color monthlyColor = (monthlyRebate >= 1000) ? clrGold : (monthlyRebate >= 500) ? clrYellow : clrWhite;
    UpdateLabel("monthly_rebate", "📅 " + monthText + ": $" + DoubleToString(monthlyRebate, 2), monthlyColor);
    
    // อัพเดท Trading Section
    UpdateLabel("trades_today", "เทรดวันนี้: " + IntegerToString(dailyTradeCount));
    UpdateLabel("lots_today", "Lots วันนี้: " + DoubleToString(totalLots, 2));
    
    color profitColor = (dailyProfit >= 0) ? clrLime : clrRed;
    UpdateLabel("profit_today", "กำไรวันนี้: $" + DoubleToString(dailyProfit, 2), profitColor);
    UpdateLabel("win_rate", "Win Rate: " + DoubleToString(winRate, 1) + "%");
    UpdateLabel("status", "สถานะ: " + GetTradingStatus());
    
    // อัพเดท Risk Section
    color drawdownColor = (currentDrawdown < 2) ? clrLime : (currentDrawdown < 5) ? clrOrange : clrRed;
    UpdateLabel("drawdown", "Drawdown: " + DoubleToString(currentDrawdown, 2) + "%", drawdownColor);
    
    string riskLevel = (currentDrawdown < 2) ? "ต่ำ" : (currentDrawdown < 5) ? "ปานกลาง" : "สูง";
    color riskColor = (currentDrawdown < 2) ? clrLime : (currentDrawdown < 5) ? clrOrange : clrRed;
    UpdateLabel("risk_level", "ระดับเสี่ยง: " + riskLevel, riskColor);
    UpdateLabel("positions", "Positions: " + IntegerToString(PositionsTotal()));
    
    // อัพเดท Stats
    UpdateLabel("account_balance", "ยอดเงิน: $" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
    UpdateLabel("equity", "Equity: $" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2));
    
    // Progress Bar
    CreateProgressBar(rebateProgress);
}

void CreateProgressBar(double progress) {
    int x = DashboardX;
    int y = DashboardY;
    int barWidth = (int)(280 * progress / 100);
    color barColor = (progress >= 100) ? clrLime : clrOrange;
    
    // ลบ progress bar เก่า
    ObjectDelete(0, dashboard_prefix + "progress_bar");
    ObjectDelete(0, dashboard_prefix + "progress_bg");
    
    // สร้าง background bar
    CreateRectangle("progress_bg", x + 10, y + 120, 280, 8, clrDarkGray);
    
    // สร้าง progress bar
    if(barWidth > 0) {
        CreateRectangle("progress_bar", x + 10, y + 120, barWidth, 8, barColor);
    }
}
//+------------------------------------------------------------------+
//| Helper Functions                                                 |
//+------------------------------------------------------------------+
void CreateRectangle(string name, int x, int y, int width, int height, color clr) {
    string obj_name = dashboard_prefix + name;
    ObjectCreate(0, obj_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, obj_name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, obj_name, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, obj_name, OBJPROP_XSIZE, width);
    ObjectSetInteger(0, obj_name, OBJPROP_YSIZE, height);
    ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clr);
    ObjectSetInteger(0, obj_name, OBJPROP_BGCOLOR, clr);
    ObjectSetInteger(0, obj_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, obj_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
    ObjectSetInteger(0, obj_name, OBJPROP_BACK, true);
    ObjectSetInteger(0, obj_name, OBJPROP_SELECTABLE, false);
    ObjectSetInteger(0, obj_name, OBJPROP_HIDDEN, true);
}

void CreateLabel(string name, string text, int x, int y, color clr, int font_size) {
    string obj_name = dashboard_prefix + name;
    ObjectCreate(0, obj_name, OBJ_LABEL, 0, 0, 0);
    ObjectSetString(0, obj_name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, obj_name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, obj_name, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clr);
    ObjectSetInteger(0, obj_name, OBJPROP_FONTSIZE, font_size);
    ObjectSetString(0, obj_name, OBJPROP_FONT, "Arial");
    ObjectSetInteger(0, obj_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
    ObjectSetInteger(0, obj_name, OBJPROP_SELECTABLE, false);
    ObjectSetInteger(0, obj_name, OBJPROP_HIDDEN, true);
}

void UpdateLabel(string name, string text, color clr = clrNONE) {
    string obj_name = dashboard_prefix + name;
    ObjectSetString(0, obj_name, OBJPROP_TEXT, text);
    if(clr != clrNONE) {
        ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clr);
    }
}

string GetTradingStatus() {
    if(!tradingEnabled) return "หยุดเทรด";
    if(dailyRebate >= TargetRebateDaily) return "บรรลุเป้าหมาย";
    if(PositionsTotal() > 0) return "กำลังเทรด";
    if(dailyTradeCount >= MaxDailyTrades) return "ครบจำนวนเทรด";
    if(dailyProfit <= -MaxDailyLoss) return "เกินขาดทุน";
    return "รอสัญญาณ";
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
    Print("=== REBATE FARM PRO EA v2.1 หยุดทำงาน ===");
    
    // บันทึกข้อมูล Monthly Rebate ก่อนหยุด
    SaveMonthlyRebateData();
    
    // คำนวณสถิติรวม
    double totalLots = dailyTradeCount * LotSize;
    double avgRebatePerLot = (totalLots > 0) ? dailyRebate / totalLots : 0;
    double netResult = dailyRebate + dailyProfit;
    double successRate = (TargetRebateDaily > 0) ? (dailyRebate / TargetRebateDaily) * 100 : 0;
    
    Print("╔══════════════════════════════════════════════════════════╗");
    Print("║                🏆 REBATE FARM PRO v2.1                  ║");
    Print("║                   สรุปผลการทำงานวันนี้                   ║");
    Print("╠══════════════════════════════════════════════════════════╣");
    Print("║ 📊 TRADING STATISTICS                                    ║");
    Print("║ • จำนวนเทรด: ", dailyTradeCount, " trades");
    Print("║ • ปริมาณรวม: ", DoubleToString(totalLots, 2), " lots");
    Print("║ • Win Rate: ", DoubleToString(((double)stats.winTrades/MathMax(stats.totalTrades,1))*100, 1), "%");
    Print("╠══════════════════════════════════════════════════════════╣");
    Print("║ 💰 REBATE PERFORMANCE                                    ║");
    Print("║ • Rebate ได้รับ: $", DoubleToString(dailyRebate, 2));
    Print("║ • เป้าหมายรายวัน: $", DoubleToString(TargetRebateDaily, 2));
    Print("║ • ความสำเร็จ: ", DoubleToString(successRate, 1), "%");
    Print("║ • Rebate/Lot: $", DoubleToString(avgRebatePerLot, 2));
    Print("╠══════════════════════════════════════════════════════════╣");
    Print("║ 📈 FINANCIAL SUMMARY                                     ║");
    Print("║ • กำไร/ขาดทุน: $", DoubleToString(dailyProfit, 2));
    Print("║ • Rebate รวม: $", DoubleToString(dailyRebate, 2));
    Print("║ • ผลรวมสุทธิ: $", DoubleToString(netResult, 2));
    
    // แสดงสถานะความสำเร็จ
    if(successRate >= 100) {
        Print("║ 🎯 สถานะ: บรรลุเป้าหมาย! ✅                            ║");
    } else if(successRate >= 50) {
        Print("║ 📊 สถานะ: ใกล้เป้าหมาย (", DoubleToString(successRate, 1), "%) 🟡                ║");
    } else {
        Print("║ ⚠️ สถานะ: ต้องปรับปรุง (", DoubleToString(successRate, 1), "%) 🔴                ║");
    }
    
    // แสดงประวัติ Rebate รายเดือนแบบครบถ้วน
    string monthlyReport = GetMonthlyRebateReport();
    Print(monthlyReport);
    Print("╠══════════════════════════════════════════════════════════╣");
    Print("║ 📋 XM REBATE INFO (ตามข้อมูลจริง)                        ║");
    Print("║ • XM Rebate: สูงสุด $25/lot (ขึ้นกับประเภทบัญชี)          ║");
    Print("║ • จ่ายสัปดาห์ละ 2 ครั้ง (อัตโนมัติ)                      ║");
    Print("║ • เฉพาะเงินจริง (ไม่รวม bonus/credit)                    ║");
    Print("║ • จ่ายไม่ว่าจะกำไรหรือขาดทุน                            ║");
    Print("╚══════════════════════════════════════════════════════════╝");
    
    // ลบ dashboard objects
    for(int i = ObjectsTotal(0) - 1; i >= 0; i--) {
        string obj_name = ObjectName(0, i);
        if(StringFind(obj_name, dashboard_prefix) == 0) {
            ObjectDelete(0, obj_name);
        }
    }
    
    // Release indicator handles
    for(int i = 0; i < ArraySize(symbols); i++) {
        if(ma_fast_handles[i] != INVALID_HANDLE) {
            IndicatorRelease(ma_fast_handles[i]);
        }
        if(ma_slow_handles[i] != INVALID_HANDLE) {
            IndicatorRelease(ma_slow_handles[i]);
        }
        if(rsi_handles[i] != INVALID_HANDLE) {
            IndicatorRelease(rsi_handles[i]);
        }
    }
    
    Comment("");
}

//+------------------------------------------------------------------+
//| OnTrade function - เรียกเมื่อมี trade events                     |
//+------------------------------------------------------------------+
void OnTrade() {
    // อัพเดทสถิติเมื่อมีการปิด trade
    Print("📊 Trade Event - อัพเดทสถิติ");
    
    // Force update dashboard
    if(ShowDashboard && dashboard_created) {
        UpdateDashboard();
    }
}

//+------------------------------------------------------------------+
//| OnChartEvent function - จัดการ event บน chart                   |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long& lparam, const double& dparam, const string& sparam) {
    if(id == CHARTEVENT_OBJECT_CLICK) {
        // จัดการคลิกที่ dashboard (สำหรับอนาคต)
        if(StringFind(sparam, dashboard_prefix) >= 0) {
            Print("Dashboard clicked: ", sparam);
        }
    }
}

//+------------------------------------------------------------------+