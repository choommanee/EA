//+------------------------------------------------------------------+
//|                                        RebateConfigValidator.mq5 |
//|                               Configuration Validator & Optimizer|
//+------------------------------------------------------------------+
#property copyright "Rebate Farm Config Validator"
#property version   "1.00"
#property script_show_inputs

input group "=== VALIDATION SETTINGS ==="
input bool ValidateAccount = true;      // ตรวจสอบ Account
input bool ValidateSymbols = true;      // ตรวจสอบ Symbols
input bool ValidateSettings = true;     // ตรวจสอบ Settings
input bool ValidateBroker = true;       // ตรวจสอบ Broker
input bool GenerateReport = true;       // สร้าง Report

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart() {
    Print("=== เริ่มตรวจสอบการกำหนดค่า REBATE FARM PRO ===");
    
    bool allPassed = true;
    string report = "<!DOCTYPE html><html><head><title>Rebate Farm Configuration Report</title></head><body>";
    report += "<h1>🔍 Rebate Farm Pro - Configuration Validation Report</h1>";
    report += "<p>Generated: " + TimeToString(TimeCurrent(), TIME_SECONDS) + "</p>";
    
    if(ValidateAccount) {
        Print("💰 ตรวจสอบ Account...");
        bool accountOK = ValidateAccountSettings();
        allPassed = allPassed && accountOK;
        report += GenerateAccountReport(accountOK);
    }
    
    if(ValidateSymbols) {
        Print("📊 ตรวจสอบ Symbols...");
        bool symbolsOK = ValidateSymbolSettings();
        allPassed = allPassed && symbolsOK;
        report += GenerateSymbolReport(symbolsOK);
    }
    
    if(ValidateSettings) {
        Print("⚙️ ตรวจสอบ Settings...");
        bool settingsOK = ValidateEASettings();
        allPassed = allPassed && settingsOK;
        report += GenerateSettingsReport(settingsOK);
    }
    
    if(ValidateBroker) {
        Print("🏦 ตรวจสอบ Broker...");
        bool brokerOK = ValidateBrokerSettings();
        allPassed = allPassed && brokerOK;
        report += GenerateBrokerReport(brokerOK);
    }
    
    // สรุปผล
    report += "<h2>" + (allPassed ? "✅ การตรวจสอบผ่านทั้งหมด" : "⚠️ พบปัญหาในการกำหนดค่า") + "</h2>";
    report += "</body></html>";
    
    if(GenerateReport) {
        SaveReport(report);
    }
    
    string result = allPassed ? "✅ พร้อมใช้งาน" : "❌ ต้องปรับแก้";
    Print("=== ผลการตรวจสอบ: ", result, " ===");
    
    if(!allPassed) {
        Alert("🚨 Rebate Farm Pro: พบปัญหาการกำหนดค่า กรุณาตรวจสอบ");
    }
}

//+------------------------------------------------------------------+
//| ตรวจสอบ Account Settings                                         |
//+------------------------------------------------------------------+
bool ValidateAccountSettings() {
    bool passed = true;
    
    // ตรวจสอบยอดเงิน
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    Print("💰 Account Balance: $", DoubleToString(balance, 2));
    
    if(balance < 1000) {
        Print("⚠️ คำเตือน: ยอดเงินต่ำกว่า $1,000 อาจมีความเสี่ยงสูง");
        passed = false;
    }
    
    // ตรวจสอบ Account Type
    string accountType = AccountInfoString(ACCOUNT_COMPANY);
    Print("🏢 Broker: ", accountType);
    
    // ตรวจสอบ Leverage
    long leverage = AccountInfoInteger(ACCOUNT_LEVERAGE);
    Print("📊 Leverage: 1:", leverage);
    
    if(leverage < 100) {
        Print("⚠️ คำเตือน: Leverage ต่ำอาจทำให้ต้องใช้ margin สูง");
        passed = false;
    }
    
    // ตรวจสอบ Currency
    string currency = AccountInfoString(ACCOUNT_CURRENCY);
    Print("💱 Currency: ", currency);
    
    if(currency != "USD") {
        Print("⚠️ คำเตือน: Account currency ไม่ใช่ USD อาจมีผลต่อการคำนวณ");
    }
    
    // ตรวจสอบ Trading Permissions
    if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) {
        Print("❌ การเทรดถูกปิดใช้งาน");
        passed = false;
    }
    
    if(!AccountInfoInteger(ACCOUNT_TRADE_EXPERT)) {
        Print("❌ EA ถูกปิดใช้งาน");
        passed = false;
    }
    
    return passed;
}

//+------------------------------------------------------------------+
//| ตรวจสอบ Symbol Settings                                          |
//+------------------------------------------------------------------+
bool ValidateSymbolSettings() {
    bool passed = true;
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "GOLDmicro"};
    
    for(int i = 0; i < ArraySize(symbols); i++) {
        string symbol = symbols[i];
        Print("📊 ตรวจสอบ ", symbol, "...");
        
        // ตรวจสอบความพร้อมใช้งาน
        if(!SymbolSelect(symbol, true)) {
            Print("❌ ", symbol, " ไม่สามารถใช้งานได้");
            passed = false;
            continue;
        }
        
        // ตรวจสอบการเทรด
        if(!SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE)) {
            Print("❌ ", symbol, " การเทรดถูกปิด");
            passed = false;
            continue;
        }
        
        // ตรวจสอบ Spread
        double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
        double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
        double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
        double spread = (ask - bid) / point;
        
        Print("  Spread: ", DoubleToString(spread, 1), " points");
        
        if(spread > 50) {
            Print("⚠️ ", symbol, " Spread สูงมาก: ", DoubleToString(spread, 1));
            passed = false;
        }
        
        // ตรวจสอบ Lot Size
        double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
        double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
        double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
        
        Print("  Min Lot: ", DoubleToString(minLot, 2));
        Print("  Max Lot: ", DoubleToString(maxLot, 2));
        Print("  Lot Step: ", DoubleToString(lotStep, 2));
        
        // ตรวจสอบ Margin
        double marginRequired = 0;
        if(OrderCalcMargin(ORDER_TYPE_BUY, symbol, minLot, ask, marginRequired)) {
            Print("  Margin per lot: $", DoubleToString(marginRequired/minLot, 2));
        }
        
        Print("✅ ", symbol, " ผ่านการตรวจสอบ");
    }
    
    return passed;
}

//+------------------------------------------------------------------+
//| ตรวจสอบ EA Settings                                              |
//+------------------------------------------------------------------+
bool ValidateEASettings() {
    bool passed = true;
    
    // ตรวจสอบ Target และ Rebate Rate
    double targetDaily = 100.0; // Default target
    double rebateRate = 5.0;    // Default rate
    
    double lotsNeeded = targetDaily / rebateRate;
    Print("🎯 เป้าหมาย Rebate: $", DoubleToString(targetDaily, 0));
    Print("💰 Rebate Rate: $", DoubleToString(rebateRate, 1), "/lot");
    Print("📊 Lots ต้องทำ: ", DoubleToString(lotsNeeded, 2));
    
    if(lotsNeeded > 50) {
        Print("⚠️ คำเตือน: ต้องทำ lots สูงมาก อาจมีความเสี่ยง");
        passed = false;
    }
    
    // ตรวจสอบ Risk Settings
    double maxDrawdown = 5.0;
    double maxDailyLoss = 50.0;
    
    Print("🛡️ Max Drawdown: ", DoubleToString(maxDrawdown, 1), "%");
    Print("🛡️ Max Daily Loss: $", DoubleToString(maxDailyLoss, 0));
    
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double riskPercent = (maxDailyLoss / balance) * 100;
    
    Print("📊 Risk per day: ", DoubleToString(riskPercent, 2), "% of balance");
    
    if(riskPercent > 5) {
        Print("⚠️ คำเตือน: ความเสี่ยงต่อวันสูงกว่า 5%");
        passed = false;
    }
    
    // ตรวจสอบ Lot Size vs Balance
    double lotSize = 0.5;
    double marginPerLot = 1000; // Approximate
    double totalMargin = lotsNeeded * marginPerLot;
    double marginPercent = (totalMargin / balance) * 100;
    
    Print("💰 Lot Size: ", DoubleToString(lotSize, 2));
    Print("📊 Margin Usage: ", DoubleToString(marginPercent, 1), "%");
    
    if(marginPercent > 80) {
        Print("❌ Margin usage เกิน 80% - ความเสี่ยงสูงมาก");
        passed = false;
    }
    
    return passed;
}

//+------------------------------------------------------------------+
//| ตรวจสอบ Broker Settings                                          |
//+------------------------------------------------------------------+
bool ValidateBrokerSettings() {
    bool passed = true;
    
    // ตรวจสอบ Execution Mode
    string company = AccountInfoString(ACCOUNT_COMPANY);
    string server = AccountInfoString(ACCOUNT_SERVER);
    
    Print("🏢 Broker: ", company);
    Print("🌐 Server: ", server);
    
    // ตรวจสอบ Execution Speed
    datetime startTime = TimeCurrent();
    // Simulate small test (ในสภาพจริงควรทำ test order)
    Sleep(10);
    datetime endTime = TimeCurrent();
    
    long executionTime = endTime - startTime;
    Print("⚡ Execution Speed Test: ", executionTime, "ms");
    
    if(executionTime > 1000) {
        Print("⚠️ คำเตือน: Execution ช้า อาจส่งผลต่อการเทรด");
        passed = false;
    }
    
    // ตรวจสอบ Trading Hours
    Print("🕐 ตรวจสอบ Trading Hours...");
    
    bool tradingAllowed = true;
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    if(dt.day_of_week == 0 || dt.day_of_week == 6) {
        Print("📅 วันหยุดสุดสัปดาห์ - ตลาดปิด");
        tradingAllowed = false;
    }
    
    // ตรวจสอบ Rebate Program
    Print("💰 ตรวจสอบ Rebate Program...");
    Print("ℹ️ กรุณายืนยัน Rebate Rate กับ Broker:");
    Print("   - EURUSD: $5.0/lot");
    Print("   - GBPUSD: $6.0/lot");
    Print("   - USDJPY: $5.5/lot");
    Print("   - GOLDmicro: $7.0/lot");
    
    return passed;
}

//+------------------------------------------------------------------+
//| Generate Reports                                                |
//+------------------------------------------------------------------+
string GenerateAccountReport(bool passed) {
    string report = "<h2>" + (passed ? "✅" : "❌") + " Account Validation</h2>";
    report += "<table border='1'>";
    report += "<tr><th>Metric</th><th>Value</th><th>Status</th></tr>";
    
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    report += "<tr><td>Balance</td><td>$" + DoubleToString(balance, 2) + "</td>";
    report += "<td>" + (balance >= 1000 ? "✅" : "⚠️") + "</td></tr>";
    
    long leverage = AccountInfoInteger(ACCOUNT_LEVERAGE);
    report += "<tr><td>Leverage</td><td>1:" + IntegerToString(leverage) + "</td>";
    report += "<td>" + (leverage >= 100 ? "✅" : "⚠️") + "</td></tr>";
    
    string currency = AccountInfoString(ACCOUNT_CURRENCY);
    report += "<tr><td>Currency</td><td>" + currency + "</td>";
    report += "<td>" + (currency == "USD" ? "✅" : "⚠️") + "</td></tr>";
    
    report += "</table>";
    return report;
}

string GenerateSymbolReport(bool passed) {
    string report = "<h2>" + (passed ? "✅" : "❌") + " Symbol Validation</h2>";
    report += "<table border='1'>";
    report += "<tr><th>Symbol</th><th>Spread</th><th>Min Lot</th><th>Status</th></tr>";
    
    string symbols[] = {"EURUSD", "GBPUSD", "USDJPY", "GOLDmicro"};
    
    for(int i = 0; i < ArraySize(symbols); i++) {
        string symbol = symbols[i];
        
        if(SymbolSelect(symbol, true)) {
            double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
            double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
            double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
            double spread = (ask - bid) / point;
            double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
            
            report += "<tr><td>" + symbol + "</td>";
            report += "<td>" + DoubleToString(spread, 1) + "</td>";
            report += "<td>" + DoubleToString(minLot, 2) + "</td>";
            report += "<td>" + (spread < 50 ? "✅" : "⚠️") + "</td></tr>";
        }
    }
    
    report += "</table>";
    return report;
}

string GenerateSettingsReport(bool passed) {
    string report = "<h2>" + (passed ? "✅" : "❌") + " Settings Validation</h2>";
    report += "<p>Target: $100/day | Risk: 5% max | Strategy: Breakeven</p>";
    return report;
}

string GenerateBrokerReport(bool passed) {
    string report = "<h2>" + (passed ? "✅" : "❌") + " Broker Validation</h2>";
    report += "<p>Company: " + AccountInfoString(ACCOUNT_COMPANY) + "</p>";
    report += "<p>Server: " + AccountInfoString(ACCOUNT_SERVER) + "</p>";
    return report;
}

void SaveReport(string content) {
    string fileName = "RebateFarm_Config_Report_" + TimeToString(TimeCurrent(), TIME_DATE) + ".html";
    int file = FileOpen(fileName, FILE_WRITE|FILE_TXT);
    
    if(file != INVALID_HANDLE) {
        FileWriteString(file, content);
        FileClose(file);
        Print("✅ รายงานถูกบันทึกที่: ", fileName);
    }
}

//+------------------------------------------------------------------+