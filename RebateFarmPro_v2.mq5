//+------------------------------------------------------------------+
//|                                            RebateFarmPro_v2.mq5 |
//|                                        Copyright 2025, Your Name |
//|                                   Optimized for Gold Trading Bot |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Your Name"
#property link      "https://www.mql5.com"
#property version   "2.00"
#property description "Advanced Gold Trading EA with Multi-Strategy Approach"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>

// Account type enumeration for XM rebate system
enum ENUM_ACCOUNT_TYPE
{
    ACCOUNT_STANDARD = 0,    // Standard Account ($10/lot)
    ACCOUNT_ULTRA = 1,       // Ultra Low Spread Account ($6/lot)
    ACCOUNT_MICRO = 2        // Micro Account ($10/lot)
};

//--- Input parameters
input group "=== TRADING SETTINGS ==="
input double InpLotSize = 0.01;                // Fixed lot size
input bool InpUseAutoLot = true;               // Use automatic lot sizing
input double InpRiskPercent = 1.0;             // Risk per trade (%)
input int InpStopLoss = 500;                   // Stop Loss (points)
input int InpTakeProfit = 800;                 // Take Profit (points)
input int InpMaxSpread = 50;                   // Maximum spread (points)

input group "=== STRATEGY SETTINGS ==="
input int InpRSIPeriod = 14;                   // RSI Period
input int InpMAFast = 21;                      // Fast MA Period
input int InpMASlow = 50;                      // Slow MA Period
input ENUM_MA_METHOD InpMAMethod = MODE_EMA;   // MA Method
input double InpRSIBuy = 30.0;                // RSI Buy Level
input double InpRSISell = 70.0;               // RSI Sell Level

input group "=== RISK MANAGEMENT ==="
input int InpMaxPositions = 1;                // Maximum positions
input bool InpUseTrailing = true;             // Use trailing stop
input int InpTrailingStart = 300;             // Trailing start (points)
input int InpTrailingStop = 200;              // Trailing stop (points)
input int InpTrailingStep = 50;               // Trailing step (points)

input group "=== TIME FILTER ==="
input bool InpUseTimeFilter = true;           // Use time filter
input int InpStartHour = 1;                   // Start hour (server time)
input int InpEndHour = 23;                    // End hour (server time)
input bool InpTradeFriday = false;            // Trade on Friday

input group "=== XM REBATE SYSTEM ==="
input bool InpEnableRebate = true;            // Enable rebate tracking
input ENUM_ACCOUNT_TYPE InpAccountType = 1; // XM Account type
input double InpRebateStandard = 10.0;        // Standard rebate rate ($/lot)
input double InpRebateUltra = 6.0;            // Ultra rebate rate ($/lot)
input bool InpShowRebateInfo = true;          // Show rebate info on chart
input bool InpSaveRebateData = true;          // Save rebate data to file

input group "=== ADVANCED ==="
input int InpMagicNumber = 202507;            // Magic Number
input string InpComment = "RebateFarmPro";    // Order comment
input bool InpShowInfo = true;                // Show info on chart

//--- Global variables
CTrade         m_trade;
CPositionInfo  m_position;
CAccountInfo   m_account;
CSymbolInfo    m_symbol;

int m_rsi_handle;
int m_ma_fast_handle;
int m_ma_slow_handle;

double m_rsi_buffer[];
double m_ma_fast_buffer[];
double m_ma_slow_buffer[];

datetime m_last_deal_time;
double m_initial_balance;
int m_total_deals;
double m_total_profit;

// Rebate system variables
double m_daily_lots_traded;
double m_daily_rebate_earned;
double m_total_rebate_earned;
datetime m_last_rebate_reset;
string m_rebate_file_name;
double m_current_rebate_rate;
int m_daily_trades_count;
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Initialize symbol
    if(!m_symbol.Name(_Symbol))
    {
        Print("Error initializing symbol: ", _Symbol);
        return INIT_FAILED;
    }
    
    // Set magic number
    m_trade.SetExpertMagicNumber(InpMagicNumber);
    
    // Initialize indicators
    m_rsi_handle = iRSI(_Symbol, PERIOD_CURRENT, InpRSIPeriod, PRICE_CLOSE);
    m_ma_fast_handle = iMA(_Symbol, PERIOD_CURRENT, InpMAFast, 0, InpMAMethod, PRICE_CLOSE);
    m_ma_slow_handle = iMA(_Symbol, PERIOD_CURRENT, InpMASlow, 0, InpMAMethod, PRICE_CLOSE);
    
    if(m_rsi_handle == INVALID_HANDLE || m_ma_fast_handle == INVALID_HANDLE || 
       m_ma_slow_handle == INVALID_HANDLE)
    {
        Print("Error creating indicators!");
        return INIT_FAILED;
    }
    
    // Set arrays as series
    ArraySetAsSeries(m_rsi_buffer, true);
    ArraySetAsSeries(m_ma_fast_buffer, true);
    ArraySetAsSeries(m_ma_slow_buffer, true);
    
    // Initialize variables
    m_last_deal_time = 0;
    m_initial_balance = m_account.Balance();
    m_total_deals = 0;
    m_total_profit = 0.0;
    
    // Initialize rebate system
    if(InpEnableRebate)
    {
        InitializeRebateSystem();
        LoadRebateData();
        Print("XM Rebate System initialized - Rate: $", DoubleToString(m_current_rebate_rate, 2), "/lot");
    }
    
    // Validate parameters
    if(!ValidateParameters())
    {
        Print("Invalid input parameters!");
        return INIT_PARAMETERS_INCORRECT;
    }
    
    Print("RebateFarmPro v2.0 initialized successfully on ", _Symbol);
    Print("Initial Balance: $", DoubleToString(m_initial_balance, 2));
    
    // Show initial dashboard
    UpdateDisplay();
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Release indicator handles
    if(m_rsi_handle != INVALID_HANDLE) IndicatorRelease(m_rsi_handle);
    if(m_ma_fast_handle != INVALID_HANDLE) IndicatorRelease(m_ma_fast_handle);
    if(m_ma_slow_handle != INVALID_HANDLE) IndicatorRelease(m_ma_slow_handle);
    
    // Clear comment
    Comment("");
    
    string reason_text;
    switch(reason)
    {
        case REASON_PROGRAM:     reason_text = "Expert removed"; break;
        case REASON_REMOVE:      reason_text = "Expert removed from chart"; break;
        case REASON_RECOMPILE:   reason_text = "Expert recompiled"; break;
        case REASON_CHARTCHANGE: reason_text = "Symbol or timeframe changed"; break;
        case REASON_CHARTCLOSE:  reason_text = "Chart closed"; break;
        case REASON_PARAMETERS:  reason_text = "Input parameters changed"; break;
        case REASON_ACCOUNT:     reason_text = "Account changed"; break;
        default:                 reason_text = "Unknown reason"; break;
    }
    
    Print("RebateFarmPro v2.0 deinitialized: ", reason_text);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check if we have enough bars
    if(Bars(_Symbol, PERIOD_CURRENT) < InpMASlow + 10) return;
    
    // Update indicators
    if(!UpdateIndicators()) return;
    
    // Wait for indicators to have data
    if(ArraySize(m_rsi_buffer) == 0 || ArraySize(m_ma_fast_buffer) == 0 || ArraySize(m_ma_slow_buffer) == 0)
    {
        // Show loading message and return
        if(InpEnableRebate)
        {
            UpdateRebateTracking();
        }
        UpdateDisplay();
        return;
    }
    
    // Check market conditions
    if(!CheckMarketConditions()) return;
    
    // Check time filter
    if(InpUseTimeFilter && !IsTimeToTrade()) return;
    
    // Main trading logic
    CheckForSignals();
    
    // Manage open positions
    ManagePositions();
    
    // Update rebate tracking (real-time)
    if(InpEnableRebate)
    {
        UpdateRebateTracking();
    }
    
    // Update display (always show)
    UpdateDisplay();
}

//+------------------------------------------------------------------+
//| Update indicators                                                |
//+------------------------------------------------------------------+
bool UpdateIndicators()
{
    // Copy RSI values
    if(CopyBuffer(m_rsi_handle, 0, 0, 3, m_rsi_buffer) <= 0)
    {
        Print("Error copying RSI data: ", GetLastError());
        return false;
    }
    
    // Copy MA Fast values
    if(CopyBuffer(m_ma_fast_handle, 0, 0, 3, m_ma_fast_buffer) <= 0)
    {
        Print("Error copying MA Fast data: ", GetLastError());
        return false;
    }
    
    // Copy MA Slow values
    if(CopyBuffer(m_ma_slow_handle, 0, 0, 3, m_ma_slow_buffer) <= 0)
    {
        Print("Error copying MA Slow data: ", GetLastError());
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Check market conditions                                          |
//+------------------------------------------------------------------+
bool CheckMarketConditions()
{
    // Check spread
    int spread = (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
    if(spread > InpMaxSpread)
    {
        return false;
    }
    
    // Check if market is open
    if(!SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE))
    {
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Check if it's time to trade                                     |
//+------------------------------------------------------------------+
bool IsTimeToTrade()
{
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    
    // Check Friday trading
    if(!InpTradeFriday && dt.day_of_week == 5 && dt.hour >= 20)
        return false;
    
    // Check trading hours
    if(dt.hour < InpStartHour || dt.hour >= InpEndHour)
        return false;
    
    return true;
}

//+------------------------------------------------------------------+
//| Check for trading signals                                        |
//+------------------------------------------------------------------+
void CheckForSignals()
{
    // Check if we can open new positions
    if(CountOpenPositions() >= InpMaxPositions) return;
    
    // Prevent multiple trades in same bar
    if(m_last_deal_time == iTime(_Symbol, PERIOD_CURRENT, 0)) return;
    
    // Get current signal
    ENUM_SIGNAL signal = GetSignal();
    
    if(signal == SIGNAL_BUY)
    {
        OpenBuyPosition();
    }
    else if(signal == SIGNAL_SELL)
    {
        OpenSellPosition();
    }
}

//+------------------------------------------------------------------+
//| Signal enumeration                                               |
//+------------------------------------------------------------------+
enum ENUM_SIGNAL
{
    SIGNAL_NONE,
    SIGNAL_BUY,
    SIGNAL_SELL
};

//+------------------------------------------------------------------+
//| Get trading signal                                               |
//+------------------------------------------------------------------+
ENUM_SIGNAL GetSignal()
{
    // RSI signals
    bool rsi_oversold = m_rsi_buffer[0] <= InpRSIBuy && m_rsi_buffer[1] > InpRSIBuy;
    bool rsi_overbought = m_rsi_buffer[0] >= InpRSISell && m_rsi_buffer[1] < InpRSISell;
    
    // MA signals
    bool ma_bullish = m_ma_fast_buffer[0] > m_ma_slow_buffer[0];
    bool ma_bearish = m_ma_fast_buffer[0] < m_ma_slow_buffer[0];
    bool ma_cross_up = m_ma_fast_buffer[0] > m_ma_slow_buffer[0] && 
                       m_ma_fast_buffer[1] <= m_ma_slow_buffer[1];
    bool ma_cross_down = m_ma_fast_buffer[0] < m_ma_slow_buffer[0] && 
                         m_ma_fast_buffer[1] >= m_ma_slow_buffer[1];
    
    // Buy conditions
    if((rsi_oversold && ma_bullish) || (ma_cross_up && m_rsi_buffer[0] < 50))
    {
        return SIGNAL_BUY;
    }
    
    // Sell conditions
    if((rsi_overbought && ma_bearish) || (ma_cross_down && m_rsi_buffer[0] > 50))
    {
        return SIGNAL_SELL;
    }
    
    return SIGNAL_NONE;
}

//+------------------------------------------------------------------+
//| Open buy position                                                |
//+------------------------------------------------------------------+
void OpenBuyPosition()
{
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double sl = InpStopLoss > 0 ? ask - InpStopLoss * SymbolInfoDouble(_Symbol, SYMBOL_POINT) : 0;
    double tp = InpTakeProfit > 0 ? ask + InpTakeProfit * SymbolInfoDouble(_Symbol, SYMBOL_POINT) : 0;
    double lot = CalculateLotSize();
    
    if(m_trade.Buy(lot, _Symbol, ask, sl, tp, InpComment))
    {
        m_last_deal_time = iTime(_Symbol, PERIOD_CURRENT, 0);
        m_total_deals++;
        Print("BUY order opened: Price=", ask, " SL=", sl, " TP=", tp, " Lot=", lot);
    }
    else
    {
        Print("Error opening BUY position: ", m_trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Open sell position                                               |
//+------------------------------------------------------------------+
void OpenSellPosition()
{
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double sl = InpStopLoss > 0 ? bid + InpStopLoss * SymbolInfoDouble(_Symbol, SYMBOL_POINT) : 0;
    double tp = InpTakeProfit > 0 ? bid - InpTakeProfit * SymbolInfoDouble(_Symbol, SYMBOL_POINT) : 0;
    double lot = CalculateLotSize();
    
    if(m_trade.Sell(lot, _Symbol, bid, sl, tp, InpComment))
    {
        m_last_deal_time = iTime(_Symbol, PERIOD_CURRENT, 0);
        m_total_deals++;
        Print("SELL order opened: Price=", bid, " SL=", sl, " TP=", tp, " Lot=", lot);
    }
    else
    {
        Print("Error opening SELL position: ", m_trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Calculate lot size                                               |
//+------------------------------------------------------------------+
double CalculateLotSize()
{
    if(!InpUseAutoLot) return InpLotSize;
    
    double balance = m_account.Balance();
    double risk_money = balance * InpRiskPercent / 100;
    double point_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double lot_size = risk_money / (InpStopLoss * point_value);
    
    // Normalize lot size
    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    
    lot_size = MathMax(min_lot, MathMin(max_lot, lot_size));
    lot_size = MathRound(lot_size / lot_step) * lot_step;
    
    return lot_size;
}

//+------------------------------------------------------------------+
//| Count open positions                                             |
//+------------------------------------------------------------------+
int CountOpenPositions()
{
    int count = 0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
                count++;
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| Manage open positions                                            |
//+------------------------------------------------------------------+
void ManagePositions()
{
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                if(InpUseTrailing)
                {
                    TrailingStop(m_position.Ticket());
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Trailing stop function                                           |
//+------------------------------------------------------------------+
void TrailingStop(ulong ticket)
{
    if(!m_position.SelectByTicket(ticket)) return;
    
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double new_sl = 0;
    
    if(m_position.PositionType() == POSITION_TYPE_BUY)
    {
        double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        double profit_points = (bid - m_position.PriceOpen()) / point;
        
        if(profit_points >= InpTrailingStart)
        {
            new_sl = bid - InpTrailingStop * point;
            
            if(new_sl > m_position.StopLoss() + InpTrailingStep * point || 
               m_position.StopLoss() == 0)
            {
                m_trade.PositionModify(ticket, new_sl, m_position.TakeProfit());
            }
        }
    }
    else if(m_position.PositionType() == POSITION_TYPE_SELL)
    {
        double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        double profit_points = (m_position.PriceOpen() - ask) / point;
        
        if(profit_points >= InpTrailingStart)
        {
            new_sl = ask + InpTrailingStop * point;
            
            if(new_sl < m_position.StopLoss() - InpTrailingStep * point || 
               m_position.StopLoss() == 0)
            {
                m_trade.PositionModify(ticket, new_sl, m_position.TakeProfit());
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Validate input parameters                                        |
//+------------------------------------------------------------------+
bool ValidateParameters()
{
    if(InpLotSize <= 0)
    {
        Print("Invalid lot size: ", InpLotSize);
        return false;
    }
    
    if(InpRiskPercent <= 0 || InpRiskPercent > 10)
    {
        Print("Invalid risk percent: ", InpRiskPercent);
        return false;
    }
    
    if(InpMaxPositions <= 0 || InpMaxPositions > 10)
    {
        Print("Invalid max positions: ", InpMaxPositions);
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Update display information                                       |
//+------------------------------------------------------------------+
void UpdateDisplay()
{
    double current_balance = m_account.Balance();
    double current_equity = m_account.Equity();
    double profit = current_balance - m_initial_balance;
    double profit_percent = m_initial_balance > 0 ? (profit / m_initial_balance) * 100 : 0;
    
    // Get current time
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    string current_time = StringFormat("%02d:%02d:%02d", dt.hour, dt.min, dt.sec);
    
    // Create beautiful header
    string info = "\n";
    info += "╔══════════════════════════════════════════════════════════╗\n";
    info += "║                🚀 REBATE FARM PRO v2.0 🚀                ║\n";
    info += "║                  XM Rebate Trading System                ║\n";
    info += "╠══════════════════════════════════════════════════════════╣\n";
    info += "║ 📊 TRADING STATUS                                        ║\n";
    info += "╠══════════════════════════════════════════════════════════╣\n";
    
    // Trading information with icons
    info += "║ 📈 Symbol: " + _Symbol + StringFormat("%*s", 45-StringLen(_Symbol), "") + "║\n";
    info += "║ ⏰ Time: " + current_time + StringFormat("%*s", 47-StringLen(current_time), "") + "║\n";
    
    // Spread analysis with color coding
    int current_spread = (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
    double spread_pips = current_spread / 10.0;
    string spread_status = spread_pips < 3.0 ? "🟢 GOOD" : spread_pips < 5.0 ? "🟡 OK" : "🔴 HIGH";
    info += "║ 📏 Spread: " + DoubleToString(spread_pips, 1) + " pips (" + spread_status + ")" + 
            StringFormat("%*s", 35-StringLen(DoubleToString(spread_pips, 1) + " pips (" + spread_status + ")"), "") + "║\n";
    
    // Account information
    string balance_str = "$" + DoubleToString(current_balance, 2);
    string equity_str = "$" + DoubleToString(current_equity, 2);
    info += "║ 💰 Balance: " + balance_str + StringFormat("%*s", 43-StringLen(balance_str), "") + "║\n";
    info += "║ 💎 Equity: " + equity_str + StringFormat("%*s", 44-StringLen(equity_str), "") + "║\n";
    
    // Profit with color coding
    string profit_icon = profit >= 0 ? "📈" : "📉";
    string profit_str = (profit >= 0 ? "+" : "") + DoubleToString(profit, 2) + " (" + 
                       (profit_percent >= 0 ? "+" : "") + DoubleToString(profit_percent, 2) + "%)";
    info += "║ " + profit_icon + " P&L: $" + profit_str + StringFormat("%*s", 42-StringLen(profit_str), "") + "║\n";
    
    // Position information
    string pos_str = IntegerToString(CountOpenPositions()) + "/" + IntegerToString(InpMaxPositions);
    info += "║ 📋 Positions: " + pos_str + StringFormat("%*s", 41-StringLen(pos_str), "") + "║\n";
    info += "║ 🔄 Total Deals: " + IntegerToString(m_total_deals) + StringFormat("%*s", 39-StringLen(IntegerToString(m_total_deals)), "") + "║\n";
    
    // XM Rebate System Section
    if(InpEnableRebate)
    {
        info += "╠══════════════════════════════════════════════════════════╣\n";
        info += "║ 💎 XM REBATE SYSTEM                                      ║\n";
        info += "╠══════════════════════════════════════════════════════════╣\n";
        
        // Status with icon
        string status_icon = InpEnableRebate ? "🟢" : "🔴";
        string status_text = InpEnableRebate ? "ACTIVE" : "DISABLED";
        info += "║ " + status_icon + " Status: " + status_text + StringFormat("%*s", 46-StringLen(status_text), "") + "║\n";
        
        // Account type with icon
        string account_icon = "🏦";
        string account_type = GetAccountTypeName();
        info += "║ " + account_icon + " Account: " + account_type + StringFormat("%*s", 45-StringLen(account_type), "") + "║\n";
        
        // Rebate rate
        string rate_str = "$" + DoubleToString(m_current_rebate_rate, 2) + "/lot";
        info += "║ 💵 Rate: " + rate_str + StringFormat("%*s", 46-StringLen(rate_str), "") + "║\n";
        
        // Daily statistics
        info += "║ 📊 Today's Stats:                                        ║\n";
        string trades_str = IntegerToString(m_daily_trades_count) + " trades";
        info += "║   🔄 Trades: " + trades_str + StringFormat("%*s", 42-StringLen(trades_str), "") + "║\n";
        
        string volume_str = DoubleToString(m_daily_lots_traded, 2) + " lots";
        info += "║   📦 Volume: " + volume_str + StringFormat("%*s", 42-StringLen(volume_str), "") + "║\n";
        
        string daily_rebate_str = "$" + DoubleToString(m_daily_rebate_earned, 2);
        info += "║   💰 Daily Rebate: " + daily_rebate_str + StringFormat("%*s", 36-StringLen(daily_rebate_str), "") + "║\n";
        
        string total_rebate_str = "$" + DoubleToString(m_total_rebate_earned, 2);
        info += "║   🏆 Total Rebate: " + total_rebate_str + StringFormat("%*s", 36-StringLen(total_rebate_str), "") + "║\n";
        
        // Projections
        if(m_daily_rebate_earned > 0)
        {
            info += "║ 📈 Projections:                                          ║\n";
            double monthly_projection = m_daily_rebate_earned * 22;
            double yearly_projection = m_daily_rebate_earned * 250;
            
            string monthly_str = "$" + DoubleToString(monthly_projection, 2);
            info += "║   📅 Monthly: " + monthly_str + StringFormat("%*s", 41-StringLen(monthly_str), "") + "║\n";
            
            string yearly_str = "$" + DoubleToString(yearly_projection, 2);
            info += "║   🎯 Yearly: " + yearly_str + StringFormat("%*s", 42-StringLen(yearly_str), "") + "║\n";
        }
        else
        {
            info += "║ ⏳ Status: Waiting for trades...                        ║\n";
            string potential_str = "$" + DoubleToString(m_current_rebate_rate, 2) + "/lot";
            info += "║ 🎯 Potential: " + potential_str + StringFormat("%*s", 41-StringLen(potential_str), "") + "║\n";
        }
        
        // Break-even analysis
        info += "║ ⚖️  Break-even Analysis:                                 ║\n";
        double breakeven_spread = m_current_rebate_rate / 10.0;
        string breakeven_str = DoubleToString(breakeven_spread, 1) + " pips";
        info += "║   📏 Break-even: " + breakeven_str + StringFormat("%*s", 38-StringLen(breakeven_str), "") + "║\n";
        
        string current_str = DoubleToString(spread_pips, 1) + " pips";
        info += "║   📊 Current: " + current_str + StringFormat("%*s", 41-StringLen(current_str), "") + "║\n";
        
        // Profitability status
        string profit_status, profit_icon_status;
        if(spread_pips < breakeven_spread)
        {
            profit_status = "PROFITABLE";
            profit_icon_status = "✅";
        }
        else
        {
            profit_status = "CHECK SPREAD";
            profit_icon_status = "⚠️";
        }
        info += "║   " + profit_icon_status + " Status: " + profit_status + StringFormat("%*s", 44-StringLen(profit_status), "") + "║\n";
    }
    
    // Technical Indicators Section
    info += "╠══════════════════════════════════════════════════════════╣\n";
    info += "║ 📊 TECHNICAL INDICATORS                                  ║\n";
    info += "╠══════════════════════════════════════════════════════════╣\n";
    
    // RSI with signal indication (with array bounds checking)
    double rsi_value = 0.0;
    string rsi_signal = "LOADING";
    string rsi_icon = "⏳";
    
    if(ArraySize(m_rsi_buffer) > 0)
    {
        rsi_value = m_rsi_buffer[0];
        if(rsi_value <= 30) { rsi_signal = "OVERSOLD"; rsi_icon = "🔴"; }
        else if(rsi_value >= 70) { rsi_signal = "OVERBOUGHT"; rsi_icon = "🔴"; }
        else { rsi_signal = "NEUTRAL"; rsi_icon = "🟡"; }
    }
    
    string rsi_str = DoubleToString(rsi_value, 2) + " (" + rsi_signal + ")";
    info += "║ " + rsi_icon + " RSI: " + rsi_str + StringFormat("%*s", 49-StringLen(rsi_str), "") + "║\n";
    
    // Moving Averages (with array bounds checking)
    string ma_fast_str = "Loading...";
    string ma_slow_str = "Loading...";
    
    if(ArraySize(m_ma_fast_buffer) > 0)
    {
        ma_fast_str = DoubleToString(m_ma_fast_buffer[0], (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS));
    }
    info += "║ 📈 MA Fast: " + ma_fast_str + StringFormat("%*s", 43-StringLen(ma_fast_str), "") + "║\n";
    
    if(ArraySize(m_ma_slow_buffer) > 0)
    {
        ma_slow_str = DoubleToString(m_ma_slow_buffer[0], (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS));
    }
    info += "║ 📉 MA Slow: " + ma_slow_str + StringFormat("%*s", 43-StringLen(ma_slow_str), "") + "║\n";
    
    // MA Signal (with array bounds checking)
    string ma_signal = "LOADING";
    string ma_icon = "⏳";
    
    if(ArraySize(m_ma_fast_buffer) > 0 && ArraySize(m_ma_slow_buffer) > 0)
    {
        if(m_ma_fast_buffer[0] > m_ma_slow_buffer[0]) { ma_signal = "BULLISH"; ma_icon = "🟢"; }
        else { ma_signal = "BEARISH"; ma_icon = "🔴"; }
    }
    
    info += "║ " + ma_icon + " MA Signal: " + ma_signal + StringFormat("%*s", 44-StringLen(ma_signal), "") + "║\n";
    
    // Footer
    info += "╚══════════════════════════════════════════════════════════╝\n";
    info += "   💡 Tip: Monitor spread vs break-even for optimal profits\n";
    info += "   🔗 XM Rebate System - Earn on every trade!";
    
    Comment(info);
}

//+------------------------------------------------------------------+
//| OnTrade function                                                 |
//+------------------------------------------------------------------+
void OnTrade()
{
    // Update profit statistics
    m_total_profit = m_account.Balance() - m_initial_balance;
    
    // Update rebate tracking
    if(InpEnableRebate)
    {
        UpdateRebateTracking();
    }
}

//+------------------------------------------------------------------+
//| Initialize Rebate System                                        |
//+------------------------------------------------------------------+
void InitializeRebateSystem()
{
    // Set rebate rate based on account type
    switch(InpAccountType)
    {
        case ACCOUNT_STANDARD:
        case ACCOUNT_MICRO:
            m_current_rebate_rate = InpRebateStandard;
            break;
        case ACCOUNT_ULTRA:
            m_current_rebate_rate = InpRebateUltra;
            break;
        default:
            m_current_rebate_rate = InpRebateStandard;
            break;
    }
    
    // Initialize variables
    m_daily_lots_traded = 0.0;
    m_daily_rebate_earned = 0.0;
    m_total_rebate_earned = 0.0;
    m_daily_trades_count = 0;
    m_last_rebate_reset = GetDayStartTime(TimeCurrent());
    m_rebate_file_name = "RebateData_v2.csv";
    
    Print("XM Rebate System initialized with rate: $", m_current_rebate_rate, "/lot");
}

//+------------------------------------------------------------------+
//| Update Rebate Tracking                                          |
//+------------------------------------------------------------------+
void UpdateRebateTracking()
{
    // Check if we need to reset daily counters
    datetime current_day_start = GetDayStartTime(TimeCurrent());
    if(current_day_start > m_last_rebate_reset)
    {
        // Save yesterday's data before reset
        if(InpSaveRebateData)
            SaveDailyRebateData();
        
        // Reset daily counters
        m_daily_lots_traded = 0.0;
        m_daily_rebate_earned = 0.0;
        m_daily_trades_count = 0;
        m_last_rebate_reset = current_day_start;
        
        Print("Daily rebate counters reset for new trading day");
    }
    
    // Calculate today's trading volume
    double today_volume = CalculateDailyTradingVolume();
    int today_trades = CountDailyTrades();
    double today_rebate = today_volume * m_current_rebate_rate;
    
    // Update counters
    m_daily_lots_traded = today_volume;
    m_daily_trades_count = today_trades;
    m_daily_rebate_earned = today_rebate;
    
    // Update total rebate (simulation)
    static double last_calculated_total = 0.0;
    if(m_daily_rebate_earned > last_calculated_total)
    {
        m_total_rebate_earned += (m_daily_rebate_earned - last_calculated_total);
        last_calculated_total = m_daily_rebate_earned;
    }
}

//+------------------------------------------------------------------+
//| Calculate Daily Trading Volume                                  |
//+------------------------------------------------------------------+
double CalculateDailyTradingVolume()
{
    double total_volume = 0.0;
    datetime day_start = GetDayStartTime(TimeCurrent());
    
    if(HistorySelect(day_start, TimeCurrent()))
    {
        int total_deals = HistoryDealsTotal();
        
        for(int i = 0; i < total_deals; i++)
        {
            ulong deal_ticket = HistoryDealGetTicket(i);
            if(deal_ticket > 0)
            {
                if(HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) == InpMagicNumber)
                {
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
//| Count Daily Trades                                              |
//+------------------------------------------------------------------+
int CountDailyTrades()
{
    int trade_count = 0;
    datetime day_start = GetDayStartTime(TimeCurrent());
    
    if(HistorySelect(day_start, TimeCurrent()))
    {
        int total_deals = HistoryDealsTotal();
        
        for(int i = 0; i < total_deals; i++)
        {
            ulong deal_ticket = HistoryDealGetTicket(i);
            if(deal_ticket > 0)
            {
                if(HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) == InpMagicNumber)
                {
                    ENUM_DEAL_ENTRY deal_entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
                    if(deal_entry == DEAL_ENTRY_IN)
                    {
                        trade_count++;
                    }
                }
            }
        }
    }
    
    return trade_count;
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
    if(m_daily_lots_traded > 0)
    {
        int file_handle = FileOpen(m_rebate_file_name, FILE_WRITE|FILE_CSV|FILE_COMMON);
        if(file_handle != INVALID_HANDLE)
        {
            if(FileSize(file_handle) == 0)
            {
                FileWrite(file_handle, "Date", "Symbol", "Trades", "Volume", "Rate", "Daily Rebate", "Total Rebate");
            }
            
            FileWrite(file_handle, 
                     TimeToString(m_last_rebate_reset, TIME_DATE),
                     _Symbol,
                     IntegerToString(m_daily_trades_count),
                     DoubleToString(m_daily_lots_traded, 2),
                     DoubleToString(m_current_rebate_rate, 2),
                     DoubleToString(m_daily_rebate_earned, 2),
                     DoubleToString(m_total_rebate_earned, 2));
            
            FileClose(file_handle);
            Print("Daily rebate saved: $", m_daily_rebate_earned, " from ", m_daily_lots_traded, " lots (", m_daily_trades_count, " trades)");
        }
    }
}

//+------------------------------------------------------------------+
//| Load Rebate Data                                                |
//+------------------------------------------------------------------+
void LoadRebateData()
{
    int file_handle = FileOpen(m_rebate_file_name, FILE_READ|FILE_CSV|FILE_COMMON);
    if(file_handle != INVALID_HANDLE)
    {
        if(!FileIsEnding(file_handle))
        {
            string header = FileReadString(file_handle);
        }
        
        string last_line = "";
        while(!FileIsEnding(file_handle))
        {
            last_line = FileReadString(file_handle);
        }
        
        if(last_line != "")
        {
            string parts[];
            int count = StringSplit(last_line, ',', parts);
            if(count >= 7)
            {
                m_total_rebate_earned = StringToDouble(parts[6]);
                Print("Loaded total rebate: $", m_total_rebate_earned);
            }
        }
        
        FileClose(file_handle);
    }
    else
    {
        Print("Rebate data file not found - starting fresh");
        m_total_rebate_earned = 0.0;
    }
}

//+------------------------------------------------------------------+
//| Get Account Type Name                                           |
//+------------------------------------------------------------------+
string GetAccountTypeName()
{
    switch(InpAccountType)
    {
        case ACCOUNT_STANDARD: return "Standard";
        case ACCOUNT_ULTRA: return "Ultra Low Spread";
        case ACCOUNT_MICRO: return "Micro";
        default: return "Unknown";
    }
}

//+------------------------------------------------------------------+
//| Get Rebate Statistics                                           |
//+------------------------------------------------------------------+
string GetRebateStatistics()
{
    string stats = "\n=== XM REBATE SYSTEM STATISTICS ===";
    stats += "\nAccount Type: " + GetAccountTypeName();
    stats += "\nRebate Rate: $" + DoubleToString(m_current_rebate_rate, 2) + "/lot";
    stats += "\nToday's Trades: " + IntegerToString(m_daily_trades_count);
    stats += "\nToday's Volume: " + DoubleToString(m_daily_lots_traded, 2) + " lots";
    stats += "\nToday's Rebate: $" + DoubleToString(m_daily_rebate_earned, 2);
    stats += "\nTotal Rebate: $" + DoubleToString(m_total_rebate_earned, 2);
    
    if(m_daily_rebate_earned > 0)
    {
        double monthly_projection = m_daily_rebate_earned * 22;
        double yearly_projection = m_daily_rebate_earned * 250;
        stats += "\nMonthly Projection: $" + DoubleToString(monthly_projection, 2);
        stats += "\nYearly Projection: $" + DoubleToString(yearly_projection, 2);
    }
    
    return stats;
}
