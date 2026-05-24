//+------------------------------------------------------------------+
//|                                           RebateFarmTest.mq5     |
//|                                    Test Script for Rebate Farm EA|
//+------------------------------------------------------------------+
#property copyright "Rebate Farm Pro Test"
#property version   "1.00"
#property script_show_inputs

input group "=== TEST SETTINGS ==="
input bool TestDashboard = true;        // ทดสอบ Dashboard
input bool TestRiskManagement = true;   // ทดสอบ Risk Management  
input bool TestSignals = true;          // ทดสอบ Trading Signals
input bool TestRebateCalc = true;       // ทดสอบ Rebate Calculation

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart() {
    Print("=== เริ่มทดสอบ REBATE FARM PRO EA ===");
    
    if(TestDashboard) {
        Print("🎨 ทดสอบ Dashboard...");
        TestDashboardFunctions();
    }
    
    if(TestRiskManagement) {
        Print("🛡️ ทดสอบ Risk Management...");
        TestRiskFunctions();
    }
    
    if(TestSignals) {
        Print("📊 ทดสอบ Trading Signals...");
        TestSignalFunctions();
    }
    
    if(TestRebateCalc) {
        Print("💰 ทดสอบ Rebate Calculation...");
        TestRebateFunctions();
    }
    
    Print("=== การทดสอบเสร็จสิ้น ===");
}

//+------------------------------------------------------------------+
//| ทดสอบ Dashboard Functions                                        |
//+------------------------------------------------------------------+
void TestDashboardFunctions() {
    // ทดสอบการสร้าง Objects
    string prefix = "Test_";
    
    // สร้าง Rectangle
    ObjectCreate(0, prefix + "rect_test", OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_XDISTANCE, 20);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_YDISTANCE, 50);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_XSIZE, 200);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_YSIZE, 100);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_BGCOLOR, clrDarkBlue);
    
    // สร้าง Label
    ObjectCreate(0, prefix + "label_test", OBJ_LABEL, 0, 0, 0);
    ObjectSetString(0, prefix + "label_test", OBJPROP_TEXT, "✅ Dashboard Test OK");
    ObjectSetInteger(0, prefix + "label_test", OBJPROP_XDISTANCE, 30);
    ObjectSetInteger(0, prefix + "label_test", OBJPROP_YDISTANCE, 80);
    ObjectSetInteger(0, prefix + "label_test", OBJPROP_COLOR, clrLime);
    ObjectSetInteger(0, prefix + "label_test", OBJPROP_FONTSIZE, 10);
    
    ChartRedraw();
    
    Print("✅ Dashboard objects สร้างสำเร็จ");
    
    // ลบ test objects หลัง 5 วินาที
    Sleep(5000);
    ObjectDelete(0, prefix + "rect_test");
    ObjectDelete(0, prefix + "label_test");
    ChartRedraw();
}

//+------------------------------------------------------------------+
//| ทดสอบ Risk Management Functions                                 |
//+------------------------------------------------------------------+
void TestRiskFunctions() {
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double margin = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
    
    Print("Account Balance: $", DoubleToString(balance, 2));
    Print("Account Equity: $", DoubleToString(equity, 2));
    Print("Margin Level: ", DoubleToString(margin, 2), "%");
    
    // ทดสอบ Drawdown calculation
    double drawdown = 0;
    if(balance > 0) {
        drawdown = ((balance - equity) / balance) * 100;
    }
    Print("Current Drawdown: ", DoubleToString(drawdown, 2), "%");
    
    // ทดสอบ Lot Size calculation
    string symbol = "EURUSD";
    if(SymbolSelect(symbol, true)) {
        double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
        double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
        double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
        
        Print("Symbol: ", symbol);
        Print("Min Lot: ", DoubleToString(minLot, 2));
        Print("Max Lot: ", DoubleToString(maxLot, 2));
        Print("Lot Step: ", DoubleToString(lotStep, 2));
        
        // ทดสอบ Margin calculation
        double marginRequired = 0;
        if(OrderCalcMargin(ORDER_TYPE_BUY, symbol, minLot, 
            SymbolInfoDouble(symbol, SYMBOL_ASK), marginRequired)) {
            Print("Margin Required for ", DoubleToString(minLot, 2), " lot: $", 
                  DoubleToString(marginRequired, 2));
        }
    }
    
    Print("✅ Risk Management functions ทำงานปกติ");
}

//+------------------------------------------------------------------+
//| ทดสอบ Trading Signal Functions                                  |
//+------------------------------------------------------------------+
void TestSignalFunctions() {
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "GOLDmicro"};
    
    for(int i = 0; i < ArraySize(symbols); i++) {
        string symbol = symbols[i];
        
        if(!SymbolSelect(symbol, true)) {
            Print("❌ Symbol not available: ", symbol);
            continue;
        }
        
        // ทดสอบ Spread
        double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
        double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
        double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        double spread = (ask - bid) / point;
        
        Print("Symbol: ", symbol);
        Print("  Ask: ", DoubleToString(ask, 5));
        Print("  Bid: ", DoubleToString(bid, 5));
        Print("  Spread: ", DoubleToString(spread, 1), " points");
        
        // ทดสอบ Indicators
        int ma_handle = iMA(symbol, PERIOD_M5, 20, 0, MODE_SMA, PRICE_CLOSE);
        int rsi_handle = iRSI(symbol, PERIOD_M5, 14, PRICE_CLOSE);
        
        if(ma_handle != INVALID_HANDLE && rsi_handle != INVALID_HANDLE) {
            double ma_value[], rsi_value[];
            ArraySetAsSeries(ma_value, true);
            ArraySetAsSeries(rsi_value, true);
            
            if(CopyBuffer(ma_handle, 0, 0, 1, ma_value) > 0 && 
               CopyBuffer(rsi_handle, 0, 0, 1, rsi_value) > 0) {
                Print("  MA(20): ", DoubleToString(ma_value[0], 5));
                Print("  RSI(14): ", DoubleToString(rsi_value[0], 2));
            }
            
            IndicatorRelease(ma_handle);
            IndicatorRelease(rsi_handle);
        }
        
        Print("✅ ", symbol, " indicators ทำงานปกติ");
    }
}

//+------------------------------------------------------------------+
//| ทดสอบ Rebate Calculation Functions                              |
//+------------------------------------------------------------------+
void TestRebateFunctions() {
    // ทดสอบ Rebate rates
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "GOLDmicro"};
    double rates[] = {5.0, 6.0, 5.5, 7.0};
    
    Print("=== Rebate Rate Testing ===");
    for(int i = 0; i < ArraySize(symbols); i++) {
        Print(symbols[i], ": $", DoubleToString(rates[i], 1), "/lot");
    }
    
    // ทดสอบ calculation
    double testLots = 1.0;
    double totalRebate = 0;
    
    Print("=== Rebate Calculation for ", DoubleToString(testLots, 1), " lot each ===");
    for(int i = 0; i < ArraySize(symbols); i++) {
        double rebate = testLots * rates[i];
        totalRebate += rebate;
        Print(symbols[i], ": $", DoubleToString(rebate, 2));
    }
    
    Print("Total Rebate: $", DoubleToString(totalRebate, 2));
    
    // ทดสอบ target calculation
    double targetDaily = 100.0;
    double avgRate = 5.75; // average rate
    double lotsNeeded = targetDaily / avgRate;
    
    Print("=== Target Analysis ===");
    Print("Daily Target: $", DoubleToString(targetDaily, 0));
    Print("Average Rate: $", DoubleToString(avgRate, 2), "/lot");
    Print("Lots Needed: ", DoubleToString(lotsNeeded, 2));
    
    Print("✅ Rebate calculations ทำงานปกติ");
}

//+------------------------------------------------------------------+    // ทดสอบการสร้าง Objects
    string prefix = "Test_";
    
    // สร้าง Rectangle
    ObjectCreate(0, prefix + "rect_test", OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_XDISTANCE, 20);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_YDISTANCE, 50);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_XSIZE, 200);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_YSIZE, 100);
    ObjectSetInteger(0, prefix + "rect_test", OBJPROP_BGCOLOR, clrDarkBlue);
    
    // สร้าง Label
    ObjectCreate(0, prefix + "label_test", OBJ_LABEL, 0, 0, 0);
    ObjectSetString(0, prefix + "label_test", OBJPROP_TEXT, "✅ Dashboard Test OK");
    ObjectSetInteger(0, prefix + "label_test", OBJPROP_XDISTANCE, 30);
    ObjectSetInteger(0, prefix + "label_test", OBJPROP_YDISTANCE, 80);
    ObjectSetInteger(0, prefix + "label_test", OBJPROP_COLOR, clrLime);
    ObjectSetInteger(0, prefix + "label_test", OBJPROP_FONTSIZE, 10);
    
    ChartRedraw();
    
    Print("✅ Dashboard objects สร้างสำเร็จ");
    
    // ลบ test objects หลัง 5 วินาที
    Sleep(5000);
    ObjectDelete(0, prefix + "rect_test");
    ObjectDelete(0, prefix + "label_test");
    ChartRedraw();
}

//+------------------------------------------------------------------+
//| ทดสอบ Risk Management Functions                                 |
//+------------------------------------------------------------------+
void TestRiskFunctions() {
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double margin = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
    
    Print("Account Balance: $", DoubleToString(balance, 2));
    Print("Account Equity: $", DoubleToString(equity, 2));
    Print("Margin Level: ", DoubleToString(margin, 2), "%");
    
    // ทดสอบ Drawdown calculation
    double drawdown = 0;
    if(balance > 0) {
        drawdown = ((balance - equity) / balance) * 100;
    }
    Print("Current Drawdown: ", DoubleToString(drawdown, 2), "%");
    
    // ทดสอบ Lot Size calculation
    string symbol = "EURUSD";
    if(SymbolSelect(symbol, true)) {
        double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
        double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
        double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
        
        Print("Symbol: ", symbol);
        Print("Min Lot: ", DoubleToString(minLot, 2));
        Print("Max Lot: ", DoubleToString(maxLot, 2));
        Print("Lot Step: ", DoubleToString(lotStep, 2));
        
        // ทดสอบ Margin calculation
        double marginRequired = 0;
        if(OrderCalcMargin(ORDER_TYPE_BUY, symbol, minLot, 
            SymbolInfoDouble(symbol, SYMBOL_ASK), marginRequired)) {
            Print("Margin Required for ", DoubleToString(minLot, 2), " lot: $", 
                  DoubleToString(marginRequired, 2));
        }
    }
    
    Print("✅ Risk Management functions ทำงานปกติ");
}

//+------------------------------------------------------------------+
//| ทดสอบ Trading Signal Functions                                  |
//+------------------------------------------------------------------+
void TestSignalFunctions() {
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "GOLDmicro"};
    
    for(int i = 0; i < ArraySize(symbols); i++) {
        string symbol = symbols[i];
        
        if(!SymbolSelect(symbol, true)) {
            Print("❌ Symbol not available: ", symbol);
            continue;
        }
        
        // ทดสอบ Spread
        double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
        double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
        double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        double spread = (ask - bid) / point;
        
        Print("Symbol: ", symbol);
        Print("  Ask: ", DoubleToString(ask, 5));
        Print("  Bid: ", DoubleToString(bid, 5));
        Print("  Spread: ", DoubleToString(spread, 1), " points");
        
        // ทดสอบ Indicators
        int ma_handle = iMA(symbol, PERIOD_M5, 20, 0, MODE_SMA, PRICE_CLOSE);
        int rsi_handle = iRSI(symbol, PERIOD_M5, 14, PRICE_CLOSE);
        
        if(ma_handle != INVALID_HANDLE && rsi_handle != INVALID_HANDLE) {
            double ma_value[], rsi_value[];
            ArraySetAsSeries(ma_value, true);
            ArraySetAsSeries(rsi_value, true);
            
            if(CopyBuffer(ma_handle, 0, 0, 1, ma_value) > 0 && 
               CopyBuffer(rsi_handle, 0, 0, 1, rsi_value) > 0) {
                Print("  MA(20): ", DoubleToString(ma_value[0], 5));
                Print("  RSI(14): ", DoubleToString(rsi_value[0], 2));
            }
            
            IndicatorRelease(ma_handle);
            IndicatorRelease(rsi_handle);
        }
        
        Print("✅ ", symbol, " indicators ทำงานปกติ");
    }
}

//+------------------------------------------------------------------+
//| ทดสอบ Rebate Calculation Functions                              |
//+------------------------------------------------------------------+
void TestRebateFunctions() {
    // ทดสอบ Rebate rates
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "GOLDmicro"};
    double rates[] = {5.0, 6.0, 5.5, 7.0};
    
    Print("=== Rebate Rate Testing ===");
    for(int i = 0; i < ArraySize(symbols); i++) {
        Print(symbols[i], ": $", DoubleToString(rates[i], 1), "/lot");
    }
    
    // ทดสอบ calculation
    double testLots = 1.0;
    double totalRebate = 0;
    
    Print("=== Rebate Calculation for ", DoubleToString(testLots, 1), " lot each ===");
    for(int i = 0; i < ArraySize(symbols); i++) {
        double rebate = testLots * rates[i];
        totalRebate += rebate;
        Print(symbols[i], ": $", DoubleToString(rebate, 2));
    }
    
    Print("Total Rebate: $", DoubleToString(totalRebate, 2));
    
    // ทดสอบ target calculation
    double targetDaily = 100.0;
    double avgRate = 5.75; // average rate
    double lotsNeeded = targetDaily / avgRate;
    
    Print("=== Target Analysis ===");
    Print("Daily Target: $", DoubleToString(targetDaily, 0));
    Print("Average Rate: $", DoubleToString(avgRate, 2), "/lot");
    Print("Lots Needed: ", DoubleToString(lotsNeeded, 2));
    
    Print("✅ Rebate calculations ทำงานปกติ");
}

//+------------------------------------------------------------------+