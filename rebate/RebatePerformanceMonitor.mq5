    int trades;
    double winRate;
    double netResult;
};

PerformanceData dailyData[];
string logFileName = "RebateFarm_Performance.csv";

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit() {
    Print("=== REBATE FARM PERFORMANCE MONITOR เริ่มทำงาน ===");
    
    // สร้างไฟล์ log ถ้ายังไม่มี
    CreateLogFile();
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &volume[],
                const int &spread[]) {
    
    // Monitor performance every hour
    static datetime lastCheck = 0;
    if(TimeCurrent() - lastCheck >= 3600) { // 1 hour
        MonitorPerformance();
        lastCheck = TimeCurrent();
    }
    
    return rates_total;
}

//+------------------------------------------------------------------+
//| สร้างไฟล์ Log                                                     |
//+------------------------------------------------------------------+
void CreateLogFile() {
    int file = FileOpen(logFileName, FILE_WRITE|FILE_CSV);
    if(file != INVALID_HANDLE) {
        // Write header
        FileWrite(file, "Date", "Time", "Daily_Rebate", "Daily_Profit", 
                 "Net_Result", "Drawdown", "Trades", "Win_Rate", "Status");
        FileClose(file);
        Print("✅ Performance log file created: ", logFileName);
    }
    else {
        Print("❌ Error creating log file");
    }
}

//+------------------------------------------------------------------+
//| ตรวจสอบ Performance                                               |
//+------------------------------------------------------------------+
void MonitorPerformance() {
    // หา EA ที่กำลังทำงาน
    double dailyRebate = GetGlobalVariable("RebateFarm_DailyRebate");
    double dailyProfit = GetGlobalVariable("RebateFarm_DailyProfit");
    int dailyTrades = (int)GetGlobalVariable("RebateFarm_DailyTrades");
    
    // คำนวณ metrics
    double drawdown = CalculateCurrentDrawdown();
    double winRate = CalculateWinRate();
    double netResult = dailyRebate + dailyProfit;
    
    // บันทึกข้อมูล
    LogPerformanceData(dailyRebate, dailyProfit, netResult, drawdown, dailyTrades, winRate);
    
    // แสดงสถานะ
    DisplayPerformanceStatus(dailyRebate, dailyProfit, netResult, drawdown, dailyTrades, winRate);
    
    // ตรวจสอบการเตือน
    CheckAlerts(drawdown, dailyProfit, winRate);
}

//+------------------------------------------------------------------+
//| บันทึกข้อมูล Performance                                          |
//+------------------------------------------------------------------+
void LogPerformanceData(double rebate, double profit, double netResult, 
                       double drawdown, int trades, double winRate) {
    int file = FileOpen(logFileName, FILE_WRITE|FILE_CSV|FILE_READ);
    if(file != INVALID_HANDLE) {
        FileSeek(file, 0, SEEK_END);
        
        MqlDateTime dt;
        TimeToStruct(TimeCurrent(), dt);
        
        string status = GetPerformanceStatus(rebate, profit, drawdown);
        
        FileWrite(file, 
                 TimeToString(TimeCurrent(), TIME_DATE),
                 TimeToString(TimeCurrent(), TIME_MINUTES),
                 DoubleToString(rebate, 2),
                 DoubleToString(profit, 2),
                 DoubleToString(netResult, 2),
                 DoubleToString(drawdown, 2),
                 IntegerToString(trades),
                 DoubleToString(winRate, 1),
                 status);
        
        FileClose(file);
    }
}

//+------------------------------------------------------------------+
//| แสดงสถานะ Performance                                             |
//+------------------------------------------------------------------+
void DisplayPerformanceStatus(double rebate, double profit, double netResult,
                             double drawdown, int trades, double winRate) {
    string status = "\n=== REBATE FARM PERFORMANCE ===\n";
    status += "🕐 เวลา: " + TimeToString(TimeCurrent(), TIME_SECONDS) + "\n";
    status += "💰 Rebate วันนี้: $" + DoubleToString(rebate, 2) + "\n";
    status += "📊 กำไรวันนี้: $" + DoubleToString(profit, 2) + "\n";
    status += "💎 ผลรวม: $" + DoubleToString(netResult, 2) + "\n";
    status += "📉 Drawdown: " + DoubleToString(drawdown, 2) + "%\n";
    status += "🔢 จำนวนเทรด: " + IntegerToString(trades) + "\n";
    status += "🎯 Win Rate: " + DoubleToString(winRate, 1) + "%\n";
    status += "⚡ สถานะ: " + GetPerformanceStatus(rebate, profit, drawdown) + "\n";
    
    Comment(status);
}

//+------------------------------------------------------------------+
//| คำนวณ Current Drawdown                                           |
//+------------------------------------------------------------------+
double CalculateCurrentDrawdown() {
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double equity = AccountInfoDouble(ACCOUNT_EQUITY);
    
    if(balance > 0) {
        return ((balance - equity) / balance) * 100;
    }
    return 0;
}

//+------------------------------------------------------------------+
//| คำนวณ Win Rate                                                    |
//+------------------------------------------------------------------+
double CalculateWinRate() {
    int totalTrades = 0;
    int winTrades = 0;
    
    // นับ position ที่ปิดแล้วในวันนี้
    datetime startOfDay = StructToTime(GetStartOfDay());
    
    for(int i = HistoryDealsTotal() - 1; i >= 0; i--) {
        ulong ticket = HistoryDealGetTicket(i);
        if(ticket > 0) {
            datetime dealTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
            if(dealTime < startOfDay) break;
            
            long dealMagic = HistoryDealGetInteger(ticket, DEAL_MAGIC);
            if(dealMagic == 789456) { // RebateFarm magic number
                long dealEntry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
                if(dealEntry == DEAL_ENTRY_OUT) {
                    totalTrades++;
                    double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
                    if(profit > 0) winTrades++;
                }
            }
        }
    }
    
    return (totalTrades > 0) ? ((double)winTrades / totalTrades) * 100 : 0;
}

//+------------------------------------------------------------------+
//| Get Start of Day                                                 |
//+------------------------------------------------------------------+
MqlDateTime GetStartOfDay() {
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    dt.hour = 0;
    dt.min = 0;
    dt.sec = 0;
    return dt;
}

//+------------------------------------------------------------------+
//| Get Performance Status                                           |
//+------------------------------------------------------------------+
string GetPerformanceStatus(double rebate, double profit, double drawdown) {
    if(drawdown > 8) return "🚨 สูงมาก";
    if(drawdown > 5) return "⚠️ ระวัง";
    if(profit < -40) return "🔴 ขาดทุนสูง";
    if(rebate >= 80) return "🎯 ใกล้เป้าหมาย";
    if(rebate >= 100) return "✅ สำเร็จ";
    return "🟢 ปกติ";
}

//+------------------------------------------------------------------+
//| ตรวจสอบการเตือน                                                   |
//+------------------------------------------------------------------+
void CheckAlerts(double drawdown, double profit, double winRate) {
    // Critical alerts
    if(drawdown > 8) {
        Alert("🚨 REBATE FARM: Drawdown สูงมาก " + DoubleToString(drawdown, 2) + "%");
        SendNotification("RebateFarm: Drawdown เกิน 8%");
    }
    
    if(profit < -45) {
        Alert("🚨 REBATE FARM: ขาดทุนสูง $" + DoubleToString(profit, 2));
        SendNotification("RebateFarm: ขาดทุนเกิน $45");
    }
    
    if(winRate < 25 && GetGlobalVariable("RebateFarm_DailyTrades") > 20) {
        Alert("⚠️ REBATE FARM: Win Rate ต่ำมาก " + DoubleToString(winRate, 1) + "%");
    }
    
    // Success alerts
    double rebate = GetGlobalVariable("RebateFarm_DailyRebate");
    if(rebate >= 100) {
        static bool successAlerted = false;
        if(!successAlerted) {
            Alert("🎉 REBATE FARM: บรรลุเป้าหมาย $" + DoubleToString(rebate, 2));
            SendNotification("RebateFarm: เป้าหมาย $100 สำเร็จ!");
            successAlerted = true;
        }
    }
}

//+------------------------------------------------------------------+
//| Get Global Variable with default                                |
//+------------------------------------------------------------------+
double GetGlobalVariable(string name) {
    if(GlobalVariableCheck(name)) {
        return GlobalVariableGet(name);
    }
    return 0;
}

//+------------------------------------------------------------------+
//| Generate Performance Report                                      |
//+------------------------------------------------------------------+
void GeneratePerformanceReport() {
    string reportName = "RebateFarm_Report_" + TimeToString(TimeCurrent(), TIME_DATE) + ".html";
    int file = FileOpen(reportName, FILE_WRITE|FILE_TXT);
    
    if(file != INVALID_HANDLE) {
        // HTML header
        FileWriteString(file, "<!DOCTYPE html>\n");
        FileWriteString(file, "<html><head><title>Rebate Farm Performance Report</title></head>\n");
        FileWriteString(file, "<body><h1>Rebate Farm Pro - Performance Report</h1>\n");
        
        // Summary section
        FileWriteString(file, "<h2>Daily Summary</h2>\n");
        FileWriteString(file, "<table border='1'>\n");
        FileWriteString(file, "<tr><th>Metric</th><th>Value</th></tr>\n");
        
        double rebate = GetGlobalVariable("RebateFarm_DailyRebate");
        double profit = GetGlobalVariable("RebateFarm_DailyProfit");
        int trades = (int)GetGlobalVariable("RebateFarm_DailyTrades");
        
        FileWriteString(file, "<tr><td>Daily Rebate</td><td>$" + DoubleToString(rebate, 2) + "</td></tr>\n");
        FileWriteString(file, "<tr><td>Daily Profit</td><td>$" + DoubleToString(profit, 2) + "</td></tr>\n");
        FileWriteString(file, "<tr><td>Net Result</td><td>$" + DoubleToString(rebate + profit, 2) + "</td></tr>\n");
        FileWriteString(file, "<tr><td>Total Trades</td><td>" + IntegerToString(trades) + "</td></tr>\n");
        FileWriteString(file, "<tr><td>Win Rate</td><td>" + DoubleToString(CalculateWinRate(), 1) + "%</td></tr>\n");
        FileWriteString(file, "<tr><td>Drawdown</td><td>" + DoubleToString(CalculateCurrentDrawdown(), 2) + "%</td></tr>\n");
        
        FileWriteString(file, "</table>\n");
        FileWriteString(file, "</body></html>");
        
        FileClose(file);
        Print("✅ Performance report generated: ", reportName);
    }
}

//+------------------------------------------------------------------+
//| OnDeinit function                                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason) {
    Comment("");
    Print("=== REBATE FARM PERFORMANCE MONITOR หยุดทำงาน ===");
    
    // Generate final report
    GeneratePerformanceReport();
}

//+------------------------------------------------------------------+