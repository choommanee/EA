//+------------------------------------------------------------------+
//|                                                RebateFarmPro.mq5 |
//|                                        Copyright 2025, Your Name |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Your Name"
#property link      "https://www.mql5.com"
#property version   "1.00"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>

// Account type enumeration
enum ENUM_ACCOUNT_TYPE
{
    ACCOUNT_VT_STANDARD = 0, // VTMarket Standard Account
    ACCOUNT_VT_RAW_ECN = 1   // VTMarket Raw ECN Account
};

//--- Input parameters
input group "=== Trading Settings ==="
input double LotSize = 0.01;                    // Base lot size
input int MaxSpread = 30;                       // Maximum spread in points
input int StopLoss = 1000;                      // Hard Stop loss in points (safeguard)
input int TakeProfit = 1500;                    // Hard Take profit in points (safeguard)
input bool UseTrailingStop = false;             // Use trailing stop (not recommended for basket close)
input int TrailingStop = 50;                   // Trailing stop in points
input int TrailingStep = 10;                   // Trailing step in points

input group "=== Strategy Settings ==="
input int RSI_Period = 14;                     // RSI period
input int MA_Fast = 12;                        // Fast MA period
input int MA_Slow = 26;                        // Slow MA period
input int MACD_Fast = 12;                      // MACD fast EMA
input int MACD_Slow = 26;                      // MACD slow EMA
input int MACD_Signal = 9;                     // MACD signal line
input double RSI_Oversold = 30.0;             // RSI oversold level
input double RSI_Overbought = 70.0;           // RSI overbought level

input group "=== Martingale Settings ==="
input double MartMultiplier = 1.5;             // Martingale Lot Multiplier
input int MartMaxLevel = 10;                    // Max Martingale Levels (Averaging)
input int MartMinDistance = 150;                // Min Distance to add Martingale (points)

input group "=== Scale-in Settings ==="
input bool EnableScaleIn = true;                // Enable adding positions on profit
input int ScaleInDistance = 150;                // Distance to add Scale-in (points)
input int MaxScaleInPositions = 5;              // Max Scale-in Positions

input group "=== Basket Close & MTP Settings ==="
input double BasketProfitUSD = 1.0;             // Basket Close Profit Target ($)
input bool EnableMTPCheck = true;               // Block closes before MTP duration
input int MinTradeDurationSeconds = 60;         // Min Trade Duration (MTP) in seconds

input group "=== Risk Management ==="
input double MaxRisk = 2.0;                    // Maximum risk per trade (%)
input int MaxPositions = 15;                   // Maximum open positions total (Martingale + Scale-in)
input bool UseEquityStop = true;               // Use equity stop
input double EquityStopPercent = 20.0;         // Equity stop percentage
input bool UseTimeFilter = true;               // Use time filter
input int StartHour = 8;                       // Start trading hour
input int EndHour = 18;                        // End trading hour

input group "=== News Filter ==="
input bool UseNewsFilter = true;               // Use news filter
input int NewsFilterMinutes = 30;              // Minutes before/after news

input group "=== VTMarket Rebate System ==="
input bool EnableRebateSystem = true;          // Enable rebate tracking
input ENUM_ACCOUNT_TYPE AccountType = ACCOUNT_VT_STANDARD; // VTMarket Account type
input double RebateRateStandard = 8.0;         // Rebate rate Standard ($8/lot)
input double RebateRateECN = 2.0;              // Rebate rate Raw ECN ($2/lot)
input double CommissionRateECN = 6.0;          // ECN Commission per round turn lot ($6/lot)
input bool ShowRebateInfo = true;              // Show rebate info on chart
input string RebateComment = "VT Rebate System"; // Rebate tracking comment

// Basket statistics structure
struct BasketStats
{
    int      totalPositions;
    double   totalLot;
    double   totalProfit;
    double   avgPrice;
    int      direction; // 1 = Buy basket, -1 = Sell basket, 0 = None
    int      maxLevelReached;
    int      totalScaleIn;
    int      totalMartingale;
    datetime oldestOpenTime;
};

//--- Global variables
CTrade trade;
CPositionInfo position;
COrderInfo order;

int rsi_handle;
int ma_fast_handle;
int ma_slow_handle;
int macd_handle;

double rsi_buffer[];
double ma_fast_buffer[];
double ma_slow_buffer[];
double macd_main_buffer[];
double macd_signal_buffer[];

datetime last_trade_time = 0;
double initial_equity = 0;
int magic_number = 123456;

// Rebate system variables
double daily_lots_traded = 0.0;
double daily_rebate_earned = 0.0;
double total_rebate_earned = 0.0;
datetime last_rebate_reset = 0;
string rebate_file_name = "RebateData.csv";
double current_rebate_rate = 8.0;

// Global tracking for visualization
double g_calcAvgPrice = 0;
double g_calcTPPrice = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Initialize indicators
    rsi_handle = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE);
    ma_fast_handle = iMA(_Symbol, PERIOD_CURRENT, MA_Fast, 0, MODE_EMA, PRICE_CLOSE);
    ma_slow_handle = iMA(_Symbol, PERIOD_CURRENT, MA_Slow, 0, MODE_EMA, PRICE_CLOSE);
    macd_handle = iMACD(_Symbol, PERIOD_CURRENT, MACD_Fast, MACD_Slow, MACD_Signal, PRICE_CLOSE);
    
    // Check if indicators are created successfully
    if(rsi_handle == INVALID_HANDLE || ma_fast_handle == INVALID_HANDLE || 
       ma_slow_handle == INVALID_HANDLE || macd_handle == INVALID_HANDLE)
    {
        Print("Error creating indicators!");
        return INIT_FAILED;
    }
    
    // Set magic number for trade identification
    trade.SetExpertMagicNumber(magic_number);
    
    // Initialize equity
    initial_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    
    // Set array as series
    ArraySetAsSeries(rsi_buffer, true);
    ArraySetAsSeries(ma_fast_buffer, true);
    ArraySetAsSeries(ma_slow_buffer, true);
    ArraySetAsSeries(macd_main_buffer, true);
    ArraySetAsSeries(macd_signal_buffer, true);
    
    // Initialize rebate system
    if(EnableRebateSystem)
    {
        InitializeRebateSystem();
        LoadRebateData();
        Print("Rebate system initialized - Rate: $", current_rebate_rate, "/lot");
    }
    
    Print("RebateFarmPro initialized successfully!");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Release indicator handles
    if(rsi_handle != INVALID_HANDLE) IndicatorRelease(rsi_handle);
    if(ma_fast_handle != INVALID_HANDLE) IndicatorRelease(ma_fast_handle);
    if(ma_slow_handle != INVALID_HANDLE) IndicatorRelease(ma_slow_handle);
    if(macd_handle != INVALID_HANDLE) IndicatorRelease(macd_handle);
    
    // Clean up visual elements from chart
    DeleteChartLines();
    Comment("");
    
    Print("RebateFarmPro deinitialized");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check if we have enough bars
    if(Bars(_Symbol, PERIOD_CURRENT) < 100) return;
    
    // Get current market data
    MqlTick tick;
    if(!SymbolInfoTick(_Symbol, tick)) return;
    
    // Update indicators
    if(!UpdateIndicators()) return;
    
    // Check time filter
    if(UseTimeFilter && !IsTimeToTrade()) return;
    
    // Check news filter
    if(UseNewsFilter && IsNewsTime()) return;
    
    // Check equity stop
    if(UseEquityStop && CheckEquityStop()) return;
    
    // Check spread
    if(GetSpread() > MaxSpread) return;
    
    // Main trading logic
    CheckForTrade();
    
    // Handle open positions (adding martingale/scale-in, check basket TP)
    ManagePositions();
    
    // Update dashboard in real-time
    UpdateDashboard();
}

//+------------------------------------------------------------------+
//| Update all indicators                                            |
//+------------------------------------------------------------------+
bool UpdateIndicators()
{
    // Copy indicator values
    if(CopyBuffer(rsi_handle, 0, 0, 3, rsi_buffer) <= 0) return false;
    if(CopyBuffer(ma_fast_handle, 0, 0, 3, ma_fast_buffer) <= 0) return false;
    if(CopyBuffer(ma_slow_handle, 0, 0, 3, ma_slow_buffer) <= 0) return false;
    if(CopyBuffer(macd_handle, 0, 0, 3, macd_main_buffer) <= 0) return false;
    if(CopyBuffer(macd_handle, 1, 0, 3, macd_signal_buffer) <= 0) return false;
    
    return true;
}

//+------------------------------------------------------------------+
//| Check if it's time to trade                                     |
//+------------------------------------------------------------------+
bool IsTimeToTrade()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    return (dt.hour >= StartHour && dt.hour <= EndHour);
}

//+------------------------------------------------------------------+
//| Check if it's news time                                         |
//+------------------------------------------------------------------+
bool IsNewsTime()
{
    // Simple news filter - avoid trading during major news hours
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    // Avoid trading during major news hours (customize as needed)
    if(dt.hour == 8 || dt.hour == 10 || dt.hour == 14 || dt.hour == 16)
        return true;
    
    return false;
}

//+------------------------------------------------------------------+
//| Check equity stop                                               |
//+------------------------------------------------------------------+
bool CheckEquityStop()
{
    double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double drawdown = (initial_equity - current_equity) / initial_equity * 100;
    
    if(drawdown > EquityStopPercent)
    {
        CloseAllPositions();
        Print("Equity stop triggered! Drawdown: ", drawdown, "%");
        return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Get current spread                                              |
//+------------------------------------------------------------------+
int GetSpread()
{
    return (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
}

//+------------------------------------------------------------------+
//| Main trading logic                                              |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| Main trading logic                                              |
//+------------------------------------------------------------------+
void CheckForTrade()
{
    // If we already have positions, ManagePositions handles adding martingale/scale-in
    if(CountOpenPositions() > 0) return;
    
    // Prevent multiple trades in the same bar for the first entry
    if(last_trade_time == iTime(_Symbol, PERIOD_CURRENT, 0)) return;
    
    // Get trend signal
    int signal = GetTradeSignal();
    
    if(signal == 1) // Buy trend detected
    {
        OpenBuyPosition(LotSize, "Rebate L1");
    }
    else if(signal == -1) // Sell trend detected
    {
        OpenSellPosition(LotSize, "Rebate L1");
    }
}

//+------------------------------------------------------------------+
//| Get trade signal (Trend Following)                              |
//+------------------------------------------------------------------+
int GetTradeSignal()
{
    // Trend following based on MA and MACD
    bool ma_bullish = ma_fast_buffer[0] > ma_slow_buffer[0];
    bool macd_bullish = macd_main_buffer[0] > macd_signal_buffer[0];
    
    if(ma_bullish && macd_bullish && rsi_buffer[0] < RSI_Overbought)
        return 1; // BUY trend
        
    if(!ma_bullish && !macd_bullish && rsi_buffer[0] > RSI_Oversold)
        return -1; // SELL trend
        
    return 0;
}

//+------------------------------------------------------------------+
//| Open buy position                                               |
//+------------------------------------------------------------------+
bool OpenBuyPosition(double lot, string comment)
{
    double price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double sl = (StopLoss > 0) ? price - StopLoss * _Point : 0;
    double tp = (TakeProfit > 0) ? price + TakeProfit * _Point : 0;
    
    if(trade.Buy(lot, _Symbol, price, sl, tp, comment))
    {
        last_trade_time = iTime(_Symbol, PERIOD_CURRENT, 0);
        Print("Buy position opened: Lot=", lot, " Comment=", comment, " Price=", price);
        return true;
    }
    else
    {
        Print("Failed to open Buy: Lot=", lot, " Comment=", comment, " Error=", trade.ResultRetcode());
        return false;
    }
}

//+------------------------------------------------------------------+
//| Open sell position                                              |
//+------------------------------------------------------------------+
bool OpenSellPosition(double lot, string comment)
{
    double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double sl = (StopLoss > 0) ? price + StopLoss * _Point : 0;
    double tp = (TakeProfit > 0) ? price - TakeProfit * _Point : 0;
    
    if(trade.Sell(lot, _Symbol, price, sl, tp, comment))
    {
        last_trade_time = iTime(_Symbol, PERIOD_CURRENT, 0);
        Print("Sell position opened: Lot=", lot, " Comment=", comment, " Price=", price);
        return true;
    }
    else
    {
        Print("Failed to open Sell: Lot=", lot, " Comment=", comment, " Error=", trade.ResultRetcode());
        return false;
    }
}

//+------------------------------------------------------------------+
//| Calculate lot size based on risk                                |
//+------------------------------------------------------------------+
double CalculateLotSize(int stop_loss_points)
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double risk_amount = balance * MaxRisk / 100;
    double point_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double lot_size = risk_amount / (stop_loss_points * point_value);
    
    // Normalize lot size
    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    
    lot_size = MathMax(min_lot, MathMin(max_lot, lot_size));
    lot_size = MathRound(lot_size / lot_step) * lot_step;
    
    return lot_size;
}

//+------------------------------------------------------------------+
//| Get Basket Statistics                                            |
//+------------------------------------------------------------------+
BasketStats GetBasketStats()
{
    BasketStats stats;
    stats.totalPositions = 0;
    stats.totalLot = 0.0;
    stats.totalProfit = 0.0;
    stats.avgPrice = 0.0;
    stats.direction = 0;
    stats.maxLevelReached = 0;
    stats.totalScaleIn = 0;
    stats.totalMartingale = 0;
    stats.oldestOpenTime = 0;

    double weightedPriceSum = 0;
    
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == magic_number)
            {
                stats.totalPositions++;
                double volume = position.Volume();
                double openPrice = position.PriceOpen();
                double profit = position.Profit();
                double swap = position.Swap();
                double comm = 0;
                
                if(AccountType == ACCOUNT_VT_RAW_ECN)
                {
                    comm = -volume * CommissionRateECN;
                }
                
                stats.totalLot += volume;
                stats.totalProfit += (profit + swap + comm);
                weightedPriceSum += (openPrice * volume);
                
                if(stats.oldestOpenTime == 0 || position.Time() < stats.oldestOpenTime)
                {
                    stats.oldestOpenTime = position.Time();
                }
                
                if(position.PositionType() == POSITION_TYPE_BUY)
                    stats.direction = 1;
                else if(position.PositionType() == POSITION_TYPE_SELL)
                    stats.direction = -1;
                    
                // Parse level/type from comment e.g. "Rebate L3 Mart", "Rebate L2 Scale"
                string comment = position.Comment();
                int idx = StringFind(comment, "L");
                if(idx >= 0)
                {
                    string numStr = StringSubstr(comment, idx + 1, 2);
                    int lvl = (int)StringToInteger(numStr);
                    if(lvl > stats.maxLevelReached)
                        stats.maxLevelReached = lvl;
                }
                
                if(StringFind(comment, "Mart") >= 0)
                    stats.totalMartingale++;
                else if(StringFind(comment, "Scale") >= 0)
                    stats.totalScaleIn++;
            }
        }
    }
    
    if(stats.totalLot > 0)
    {
        stats.avgPrice = weightedPriceSum / stats.totalLot;
    }
    
    return stats;
}

//+------------------------------------------------------------------+
//| Get last open position details                                  |
//+------------------------------------------------------------------+
double GetLastEntryPrice(int &outType, string &outComment)
{
    double lastPrice = 0;
    datetime newestTime = 0;
    outType = -1;
    outComment = "";
    
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == magic_number)
            {
                if(position.Time() > newestTime)
                {
                    newestTime = position.Time();
                    lastPrice = position.PriceOpen();
                    outType = (int)position.PositionType();
                    outComment = position.Comment();
                }
            }
        }
    }
    return lastPrice;
}

//+------------------------------------------------------------------+
//| Normalize lot size                                              |
//+------------------------------------------------------------------+
double NormalizeLotSize(double lot)
{
    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    
    lot = MathMax(min_lot, MathMin(max_lot, lot));
    lot = MathRound(lot / lot_step) * lot_step;
    
    return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| Count open positions                                            |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
    int count = 0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == magic_number)
                count++;
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| Manage open positions                                           |
//+------------------------------------------------------------------+
void ManagePositions()
{
    BasketStats stats = GetBasketStats();
    if(stats.totalPositions == 0)
    {
        g_calcAvgPrice = 0;
        g_calcTPPrice = 0;
        return;
    }
    
    // Save to globals for drawing
    g_calcAvgPrice = stats.avgPrice;
    
    // Target profit calculation (USD per 0.01 lot)
    double targetProfit = BasketProfitUSD * (stats.totalLot / 0.01);
    
    // Calculate TP Price level for visual display
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double price = (bid + ask) / 2;
    
    double tickVal = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double tickSz = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
    
    if(stats.totalLot > 0 && tickVal > 0)
    {
        double tpDist = (targetProfit / stats.totalLot) * (tickSz / tickVal);
        if(stats.direction == 1) // Buy
            g_calcTPPrice = stats.avgPrice + tpDist;
        else if(stats.direction == -1) // Sell
            g_calcTPPrice = stats.avgPrice - tpDist;
    }
    else
    {
        g_calcTPPrice = 0;
    }
    
    // 1. Check for Basket Take Profit
    bool basketTPTriggered = false;
    
    // Net profit target check
    if(stats.totalProfit >= targetProfit)
    {
        basketTPTriggered = true;
        Print("[BASKET TP-$] Profit target reached: $", DoubleToString(stats.totalProfit, 2), " >= Target: $", DoubleToString(targetProfit, 2));
    }
    // Backup price-based TP check
    else if(g_calcTPPrice > 0 && stats.totalProfit > 0)
    {
        if(stats.direction == 1 && bid >= g_calcTPPrice)
        {
            basketTPTriggered = true;
            Print("[BASKET TP-PRICE] Buy price passed TP level. bid=", bid, " TP=", g_calcTPPrice);
        }
        else if(stats.direction == -1 && ask <= g_calcTPPrice)
        {
            basketTPTriggered = true;
            Print("[BASKET TP-PRICE] Sell price passed TP level. ask=", ask, " TP=", g_calcTPPrice);
        }
    }
    
    // If Basket TP is triggered, check MTP time filter before closing
    if(basketTPTriggered)
    {
        bool mtpMet = true;
        if(EnableMTPCheck && stats.oldestOpenTime > 0)
        {
            if(TimeCurrent() - stats.oldestOpenTime < MinTradeDurationSeconds)
            {
                mtpMet = false;
                // Log once in a while
                static datetime last_mtp_log = 0;
                if(TimeCurrent() - last_mtp_log >= 10)
                {
                    last_mtp_log = TimeCurrent();
                    Print("[MTP HOLD] Basket TP is ready, but holding for VTMarket compliance time: ", 
                          TimeCurrent() - stats.oldestOpenTime, "/", MinTradeDurationSeconds, " seconds");
                }
            }
        }
        
        if(mtpMet)
        {
            CloseAllPositions();
            return;
        }
    }
    
    // 2. Trailing Stop (Only applied to individual positions if enabled, though basket close is preferred)
    if(UseTrailingStop)
    {
        for(int i = 0; i < PositionsTotal(); i++)
        {
            if(position.SelectByIndex(i))
            {
                if(position.Symbol() == _Symbol && position.Magic() == magic_number)
                {
                    ApplyTrailingStop(position.Ticket());
                }
            }
        }
    }
    
    // 3. Grid Adding Logic (Martingale and Scale-in)
    if(stats.totalPositions < MaxPositions)
    {
        int lastType = -1;
        string lastComment = "";
        double lastPrice = GetLastEntryPrice(lastType, lastComment);
        
        if(lastPrice > 0)
        {
            // BUY basket adding logic
            if(stats.direction == 1)
            {
                double distanceLoss = lastPrice - ask; // price going down is loss for BUY
                double distanceProfit = bid - lastPrice; // price going up is profit for BUY
                
                // A. Martingale Adding (Price moved against us)
                if(distanceLoss >= MartMinDistance * _Point && stats.maxLevelReached < MartMaxLevel)
                {
                    int nextLvl = stats.maxLevelReached + 1;
                    double nextLot = NormalizeLotSize(LotSize * MathPow(MartMultiplier, nextLvl - 1));
                    string comment = "Rebate L" + IntegerToString(nextLvl) + " Mart";
                    Print("[MARTINGALE ADD] BUY L", nextLvl, " Distance: ", distanceLoss / _Point, " points. Opening lot: ", nextLot);
                    OpenBuyPosition(nextLot, comment);
                }
                // B. Scale-in Adding (Price moved in our favor)
                else if(EnableScaleIn && distanceProfit >= ScaleInDistance * _Point && stats.totalScaleIn < MaxScaleInPositions)
                {
                    int nextLvl = stats.maxLevelReached + 1;
                    double nextLot = LotSize; // Fixed base lot size for scale-in to keep risk low
                    string comment = "Rebate L" + IntegerToString(nextLvl) + " Scale";
                    Print("[SCALE-IN ADD] BUY L", nextLvl, " Distance: ", distanceProfit / _Point, " points. Opening lot: ", nextLot);
                    OpenBuyPosition(nextLot, comment);
                }
            }
            // SELL basket adding logic
            else if(stats.direction == -1)
            {
                double distanceLoss = ask - lastPrice; // price going up is loss for SELL
                double distanceProfit = lastPrice - bid; // price going down is profit for SELL
                
                // A. Martingale Adding
                if(distanceLoss >= MartMinDistance * _Point && stats.maxLevelReached < MartMaxLevel)
                {
                    int nextLvl = stats.maxLevelReached + 1;
                    double nextLot = NormalizeLotSize(LotSize * MathPow(MartMultiplier, nextLvl - 1));
                    string comment = "Rebate L" + IntegerToString(nextLvl) + " Mart";
                    Print("[MARTINGALE ADD] SELL L", nextLvl, " Distance: ", distanceLoss / _Point, " points. Opening lot: ", nextLot);
                    OpenSellPosition(nextLot, comment);
                }
                // B. Scale-in Adding
                else if(EnableScaleIn && distanceProfit >= ScaleInDistance * _Point && stats.totalScaleIn < MaxScaleInPositions)
                {
                    int nextLvl = stats.maxLevelReached + 1;
                    double nextLot = LotSize;
                    string comment = "Rebate L" + IntegerToString(nextLvl) + " Scale";
                    Print("[SCALE-IN ADD] SELL L", nextLvl, " Distance: ", distanceProfit / _Point, " points. Opening lot: ", nextLot);
                    OpenSellPosition(nextLot, comment);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Trailing stop function                                          |
//+------------------------------------------------------------------+
void ApplyTrailingStop(ulong ticket)
{
    if(!position.SelectByTicket(ticket)) return;
    
    double current_price;
    double new_sl;
    
    if(position.PositionType() == POSITION_TYPE_BUY)
    {
        current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        new_sl = current_price - TrailingStop * _Point;
        
        if(new_sl > position.StopLoss() + TrailingStep * _Point)
        {
            if(trade.PositionModify(ticket, new_sl, position.TakeProfit()))
            {
                Print("Buy trailing stop updated to ", new_sl);
            }
        }
    }
    else if(position.PositionType() == POSITION_TYPE_SELL)
    {
        current_price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        new_sl = current_price + TrailingStop * _Point;
        
        if(new_sl < position.StopLoss() - TrailingStep * _Point)
        {
            if(trade.PositionModify(ticket, new_sl, position.TakeProfit()))
            {
                Print("Sell trailing stop updated to ", new_sl);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Close all positions                                             |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == magic_number)
            {
                ulong ticket = position.Ticket();
                trade.PositionClose(ticket);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Draw visual line on chart                                       |
//+------------------------------------------------------------------+
void DrawChartLine(string name, double price, color col, int style, string label)
{
    if(ObjectFind(0, name) < 0)
    {
        ObjectCreate(0, name, OBJ_HLINE, 0, 0, price);
        ObjectSetInteger(0, name, OBJPROP_COLOR, col);
        ObjectSetInteger(0, name, OBJPROP_STYLE, style);
        ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
        ObjectSetString(0, name, OBJPROP_TOOLTIP, label);
    }
    else
    {
        ObjectMove(0, name, 0, 0, price);
        ObjectSetString(0, name, OBJPROP_TOOLTIP, label);
    }
}

//+------------------------------------------------------------------+
//| Delete all visual lines from chart                               |
//+------------------------------------------------------------------+
void DeleteChartLines()
{
    ObjectDelete(0, "Rebate_AvgPrice");
    ObjectDelete(0, "Rebate_BasketTP");
}

//+------------------------------------------------------------------+
//| Update Info Dashboard                                            |
//+------------------------------------------------------------------+
void UpdateDashboard()
{
    BasketStats stats = GetBasketStats();
    double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    double profit = current_equity - initial_equity;
    
    string comment_text = "=== RebateFarmPro Dashboard (VTMarket) ===\n";
    comment_text += "Mode: Trend-Following Martingale & Scale-in Grid\n";
    comment_text += "Account Type: " + GetAccountTypeName() + " | Rate: $" + DoubleToString(current_rebate_rate, 2) + "/lot\n";
    comment_text += "----------------------------------------------\n";
    
    if(stats.totalPositions > 0)
    {
        string dirStr = (stats.direction == 1) ? "BUY" : "SELL";
        comment_text += "Basket Direction: " + dirStr + "\n";
        comment_text += "Open Positions: " + IntegerToString(stats.totalPositions) + " (Max Level: L" + IntegerToString(stats.maxLevelReached) + ")\n";
        comment_text += "   - Martingale positions: " + IntegerToString(stats.totalMartingale) + "\n";
        comment_text += "   - Scale-in positions: " + IntegerToString(stats.totalScaleIn) + "\n";
        comment_text += "Total Lots: " + DoubleToString(stats.totalLot, 2) + "\n";
        comment_text += "Average Entry Price: " + DoubleToString(stats.avgPrice, _Digits) + "\n";
        comment_text += "Floating Profit/Loss: $" + DoubleToString(stats.totalProfit, 2) + " (Net including Swap/Comm)\n";
        
        double targetProfit = BasketProfitUSD * (stats.totalLot / 0.01);
        comment_text += "Basket Target Profit: $" + DoubleToString(targetProfit, 2) + " (TP Price: " + DoubleToString(g_calcTPPrice, _Digits) + ")\n";
        
        if(EnableMTPCheck)
        {
            int age = (int)(TimeCurrent() - stats.oldestOpenTime);
            if(age < MinTradeDurationSeconds)
                comment_text += "MTP Status: " + IntegerToString(age) + "/" + IntegerToString(MinTradeDurationSeconds) + "s (HOLDING)\n";
            else
                comment_text += "MTP Status: " + IntegerToString(age) + "s (MTP OK - Eligible for Rebate)\n";
        }
        
        // Draw lines on chart
        DrawChartLine("Rebate_AvgPrice", stats.avgPrice, clrYellow, STYLE_DOT, "Avg Price: " + DoubleToString(stats.avgPrice, _Digits));
        if(g_calcTPPrice > 0)
            DrawChartLine("Rebate_BasketTP", g_calcTPPrice, clrLime, STYLE_DOT, "Basket TP: " + DoubleToString(g_calcTPPrice, _Digits) + " ($" + DoubleToString(targetProfit, 2) + ")");
        else
            ObjectDelete(0, "Rebate_BasketTP");
    }
    else
    {
        comment_text += "Basket Status: No active positions. Waiting for trend signal...\n";
        DeleteChartLines();
    }
    
    comment_text += "----------------------------------------------\n";
    comment_text += "Rebate Statistics:\n";
    comment_text += "   - Lots Traded Today: " + DoubleToString(daily_lots_traded, 2) + " lots\n";
    comment_text += "   - Rebate Earned Today: $" + DoubleToString(daily_rebate_earned, 2) + "\n";
    comment_text += "   - Total Rebate Earned: $" + DoubleToString(total_rebate_earned, 2) + "\n";
    if(daily_lots_traded > 0)
    {
        double monthly_proj = daily_rebate_earned * 22; // 22 trading days
        comment_text += "   - Monthly Projected Rebate: $" + DoubleToString(monthly_proj, 2) + "\n";
    }
    comment_text += "Capital P&L: $" + DoubleToString(profit, 2) + " (Closed: $" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE) - initial_equity, 2) + ")\n";
    
    Comment(comment_text);
}

//+------------------------------------------------------------------+
//| OnTrade function                                                |
//+------------------------------------------------------------------+
void OnTrade()
{
    // Handle trade events
    static datetime last_trade_time_check = 0;
    
    if(TimeCurrent() > last_trade_time_check)
    {
        last_trade_time_check = TimeCurrent();
        
        // Update rebate tracking
        if(EnableRebateSystem)
        {
            UpdateRebateTracking();
        }
        
        // Update visual dashboard
        UpdateDashboard();
    }
}

//+------------------------------------------------------------------+
//| OnChartEvent function                                           |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
    // Handle chart events if needed
    if(id == CHARTEVENT_KEYDOWN)
    {
        // Emergency close with ESC key
        if(lparam == 27) // ESC key
        {
            CloseAllPositions();
            Print("Emergency close activated!");
        }
        // Save rebate data with 'S' key
        else if(lparam == 83) // S key
        {
            if(EnableRebateSystem)
            {
                SaveRebateData();
                Print("Rebate data saved manually!");
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Initialize Rebate System                                        |
//+------------------------------------------------------------------+
void InitializeRebateSystem()
{
    // Set rebate rate based on account type
    switch(AccountType)
    {
        case ACCOUNT_VT_STANDARD:
            current_rebate_rate = RebateRateStandard;
            break;
        case ACCOUNT_VT_RAW_ECN:
            current_rebate_rate = RebateRateECN;
            break;
        default:
            current_rebate_rate = RebateRateStandard;
            break;
    }
    
    // Initialize daily reset time
    last_rebate_reset = GetDayStartTime(TimeCurrent());
    
    Print("Rebate system initialized with rate: $", current_rebate_rate, "/lot");
}

//+------------------------------------------------------------------+
//| Update Rebate Tracking                                          |
//+------------------------------------------------------------------+
void UpdateRebateTracking()
{
    // Check if we need to reset daily counters
    datetime current_day_start = GetDayStartTime(TimeCurrent());
    if(current_day_start > last_rebate_reset)
    {
        // Save yesterday's data before reset
        SaveDailyRebateData();
        
        // Reset daily counters
        daily_lots_traded = 0.0;
        daily_rebate_earned = 0.0;
        last_rebate_reset = current_day_start;
        
        Print("Daily rebate counters reset for new trading day");
    }
    
    // Calculate today's trading volume
    double today_volume = CalculateDailyTradingVolume();
    double today_rebate = today_volume * current_rebate_rate;
    
    // Update counters
    daily_lots_traded = today_volume;
    daily_rebate_earned = today_rebate;
    
    // Update total rebate (this would normally come from broker)
    // For simulation, we add daily rebate to total
    static double last_calculated_total = 0.0;
    if(daily_rebate_earned > last_calculated_total)
    {
        total_rebate_earned += (daily_rebate_earned - last_calculated_total);
        last_calculated_total = daily_rebate_earned;
    }
}

//+------------------------------------------------------------------+
//| Calculate Daily Trading Volume                                  |
//+------------------------------------------------------------------+
double CalculateDailyTradingVolume()
{
    double total_volume = 0.0;
    datetime day_start = GetDayStartTime(TimeCurrent());
    
    // Get deals from today
    if(HistorySelect(day_start, TimeCurrent()))
    {
        int total_deals = HistoryDealsTotal();
        
        for(int i = 0; i < total_deals; i++)
        {
            ulong deal_ticket = HistoryDealGetTicket(i);
            if(deal_ticket > 0)
            {
                // Check if deal belongs to our EA
                if(HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) == magic_number)
                {
                    // Only count entry deals (not exit deals to avoid double counting)
                    ENUM_DEAL_ENTRY deal_entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
                    if(deal_entry == DEAL_ENTRY_IN)
                    {
                        double volume = HistoryDealGetDouble(deal_ticket, DEAL_VOLUME);
                        total_volume += volume;
                    }
                }
            }
        }
    }
    
    return total_volume;
}

//+------------------------------------------------------------------+
//| Get Day Start Time                                              |
//+------------------------------------------------------------------+
datetime GetDayStartTime(datetime time)
{
    MqlDateTime dt;
    TimeToStruct(time, dt);
    dt.hour = 0;
    dt.min = 0;
    dt.sec = 0;
    return StructToTime(dt);
}

//+------------------------------------------------------------------+
//| Save Daily Rebate Data                                          |
//+------------------------------------------------------------------+
void SaveDailyRebateData()
{
    if(daily_lots_traded > 0)
    {
        int file_handle = FileOpen(rebate_file_name, FILE_WRITE|FILE_CSV|FILE_COMMON);
        if(file_handle != INVALID_HANDLE)
        {
            // Write header if file is new
            if(FileSize(file_handle) == 0)
            {
                FileWrite(file_handle, "Date", "Symbol", "Lots Traded", "Rebate Rate", "Daily Rebate", "Total Rebate");
            }
            
            // Write daily data
            FileWrite(file_handle, 
                     TimeToString(last_rebate_reset, TIME_DATE),
                     _Symbol,
                     DoubleToString(daily_lots_traded, 2),
                     DoubleToString(current_rebate_rate, 2),
                     DoubleToString(daily_rebate_earned, 2),
                     DoubleToString(total_rebate_earned, 2));
            
            FileClose(file_handle);
            Print("Daily rebate data saved: $", daily_rebate_earned, " from ", daily_lots_traded, " lots");
        }
        else
        {
            Print("Error opening rebate data file!");
        }
    }
}

//+------------------------------------------------------------------+
//| Save Rebate Data                                                |
//+------------------------------------------------------------------+
void SaveRebateData()
{
    SaveDailyRebateData();
}

//+------------------------------------------------------------------+
//| Load Rebate Data                                                |
//+------------------------------------------------------------------+
void LoadRebateData()
{
    int file_handle = FileOpen(rebate_file_name, FILE_READ|FILE_CSV|FILE_COMMON);
    if(file_handle != INVALID_HANDLE)
    {
        // Skip header
        if(!FileIsEnding(file_handle))
        {
            string header = FileReadString(file_handle);
        }
        
        // Read last entry to get total rebate
        string last_line = "";
        while(!FileIsEnding(file_handle))
        {
            last_line = FileReadString(file_handle);
        }
        
        if(last_line != "")
        {
            string parts[];
            int count = StringSplit(last_line, ',', parts);
            if(count >= 6)
            {
                total_rebate_earned = StringToDouble(parts[5]);
                Print("Loaded total rebate: $", total_rebate_earned);
            }
        }
        
        FileClose(file_handle);
    }
    else
    {
        Print("Rebate data file not found - starting fresh");
        total_rebate_earned = 0.0;
    }
}

//+------------------------------------------------------------------+
//| Get Rebate Statistics                                           |
//+------------------------------------------------------------------+
string GetRebateStatistics()
{
    string stats = "\n=== XM REBATE SYSTEM STATISTICS ===";
    stats += "\nAccount Type: " + GetAccountTypeName();
    stats += "\nRebate Rate: $" + DoubleToString(current_rebate_rate, 2) + "/lot";
    stats += "\nToday's Volume: " + DoubleToString(daily_lots_traded, 2) + " lots";
    stats += "\nToday's Rebate: $" + DoubleToString(daily_rebate_earned, 2);
    stats += "\nTotal Rebate: $" + DoubleToString(total_rebate_earned, 2);
    
    if(daily_lots_traded > 0)
    {
        double monthly_projection = daily_rebate_earned * 22; // 22 trading days
        stats += "\nMonthly Projection: $" + DoubleToString(monthly_projection, 2);
    }
    
    return stats;
}

//+------------------------------------------------------------------+
//| Get Account Type Name                                           |
//+------------------------------------------------------------------+
string GetAccountTypeName()
{
    switch(AccountType)
    {
        case ACCOUNT_VT_STANDARD: return "VT Standard";
        case ACCOUNT_VT_RAW_ECN: return "VT Raw ECN";
        default: return "Unknown";
    }
}
