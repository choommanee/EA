
//+------------------------------------------------------------------+
//|                                               GridTradingEA.mq5 |
//|                                    Pure Grid Trading System     |
//|                                             Clean & Simple      |
//+------------------------------------------------------------------+
#property copyright "Grid Trading EA"
#property link      ""
#property version   "1.00"
#property description "Pure Grid Trading System - Buy Low, Sell High"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

CTrade trade;
CPositionInfo position;
CSymbolInfo symbolInfo;
CAccountInfo account;

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input group "=== Grid Settings ==="
input int InpMagicNumber = 54321;                    // Magic Number
input double InpBaseLotSize = 0.03;                  // Base Lot Size - ลดลงเพื่อลดความเสี่ยง
input double InpLotMultiplier = 1.5;                 // Lot Multiplier - ลดลงเพื่อควบคุมความเสี่ยง
input int InpGridStep = 30;                          // Grid Step (points) - ลดลงเพื่อเข้า position บ่อยขึ้น
input int InpMaxLevels = 5;                          // Maximum Grid Levels - ลดลงเพื่อควบคุมความเสี่ยง
input double InpProfitTargetPercent = 0.2;           // Profit Target (% of total lot volume) - ลดลงเพื่อปิดเร็วขึ้น
input bool InpForceProfitClose = true;               // Force Close at Target - บังคับปิดเมื่อถึงเป้า
input int InpMaxHoldingMinutes = 10;                 // Max Holding Time (minutes) - ลดเวลาถือครอง
input bool InpUseHedging = true;                     // Use Hedging Strategy - เปิดใช้งาน

input group "=== Trend & Hedge Settings ==="
input int InpTrendPeriod = 20;                       // Trend Detection Period
input int InpFastMA = 5;                             // Fast MA Period
input int InpSlowMA = 20;                            // Slow MA Period
input double InpTrendThreshold = 50.0;               // Trend Strength Threshold (points)
input double InpReverseMultiplier = 1.0;             // Reverse Position Multiplier - ลดลง
input bool InpAutoReverse = true;                    // Auto Reverse - เปิดใหม่แต่ปรับปรุง
input int InpReverseTrigger = 200;                   // Reverse Trigger - เพิ่มขึ้น
input double InpHedgeStepSize = 0.3;                 // Hedge Step Size (fraction of grid lot)
input int InpMaxHedgeLevels = 3;                     // Maximum Hedge Levels
input int InpHedgeGridStep = 150;                    // Hedge Grid Step (points) - ระยะห่างระหว่าง hedge levels

input group "=== FVG Dynamic Grid Settings ==="
input bool InpUseFVGGrid = true;                     // Use FVG for Dynamic Grid Step
input int InpFVGLookback = 20;                       // FVG Detection Lookback Bars
input double InpFVGMultiplier = 1.0;                 // FVG Size Multiplier for Grid Step
input double InpMinGridStep = 30.0;                  // Minimum Grid Step (points)
input double InpMaxGridStep = 300.0;                 // Maximum Grid Step (points)
input double InpFVGSensitivity = 0.5;                // FVG Sensitivity (0.1-2.0)

input group "=== Risk Management ==="
input double InpMaxDrawdown = 500.0;                 // Maximum Drawdown ($) - เพิ่มขึ้นเพื่อรองรับการปั่น lot มากขึ้น
input double InpMaxDailyLoss = 250.0;               // Maximum Daily Loss ($) - เพิ่มขึ้นเพื่อให้มีพื้นที่ทำกำไรมากขึ้น
input double InpQuickProfitPercent = 0.05;           // Quick Profit % - ลดลงเพื่อปิดเร็วขึ้น
input int InpMaxTradesPerDay = 1000;                // Maximum Trades Per Day - เพิ่มขึ้นเป็น 1000 เพื่อปั่น lot เยอะๆ
input double InpMinLotProfit = 0.02;                // Minimum Profit Per Lot - ลดขั้นต่ำ
input bool InpUseTimeFilter = false;                // Use Time Filter
input int InpStartHour = 0;                         // Start Trading Hour
input int InpEndHour = 23;                          // End Trading Hour

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
// Indicator handles
int ma_fast_handle = INVALID_HANDLE;
int ma_slow_handle = INVALID_HANDLE;
int atr_handle = INVALID_HANDLE;

double buy_prices[100];
double buy_lots[100];
ulong buy_tickets[100];
datetime buy_times[100];

double sell_prices[100];
double sell_lots[100];
ulong sell_tickets[100];
datetime sell_times[100];

int buy_count = 0;
int sell_count = 0;

double initial_balance = 0.0;
double grid_start_price = 0.0;
datetime last_order_time = 0;
bool grid_active = false;
string grid_direction = "NONE"; // "BUY", "SELL", "NONE"

// Trend and Hedge Variables
string current_trend = "NONE";    // "BULLISH", "BEARISH", "SIDEWAYS", "NONE"
bool trend_reversed = false;
double last_trend_price = 0.0;
datetime last_trend_check = 0;
int hedge_count = 0;
double hedge_prices[50];
double hedge_lots[50];
ulong hedge_tickets[50];
string hedge_directions[50]; // "BUY" or "SELL"
bool is_reversing = false;   // Flag to track if we're in reverse mode
bool is_following = false;   // Flag to track if we're following trend
datetime last_hedge_time = 0; // Last hedge order time
double hedge_start_price = 0.0;  // Starting price for hedge grid
double next_hedge_level_price = 0.0; // Next hedge level price

// FVG Dynamic Grid Variables
double current_grid_step = 100.0;     // Current dynamic grid step in points
double last_fvg_size = 0.0;           // Last detected FVG size
datetime last_fvg_check = 0;          // Last FVG calculation time
bool fvg_detected = false;            // FVG detection flag
double fvg_bull_gaps[10];             // Bullish FVG levels
double fvg_bear_gaps[10];             // Bearish FVG levels
int fvg_bull_count = 0;               // Count of bullish FVGs
int fvg_bear_count = 0;               // Count of bearish FVGs

// Risk Management Variables
double daily_start_balance = 0.0;    // Daily starting balance
datetime last_daily_reset = 0;       // Last daily reset time
bool daily_limit_reached = false;    // Daily loss limit flag
int daily_trade_count = 0;           // Count of trades today
double daily_profit = 0.0;           // Today's profit/loss
double max_daily_profit = 0.0;       // Maximum profit reached today
bool emergency_stop = false;         // Emergency stop flag
double volatility_multiplier = 1.0;  // Dynamic multiplier based on market volatility
double last_atr_value = 0.0;         // Last ATR value for volatility measurement
double total_lot_volume = 0.0;       // Total lot volume for profit calculation
datetime last_force_close = 0;       // Last forced close time
datetime grid_start_time = 0;        // Grid start time for timeout

// 📊 NEW: Performance Tracking Variables
double daily_total_lots = 0.0;       // Total lots traded today
double daily_volume_target = 400.0;  // Daily volume target (lots)
double session_lots = 0.0;           // Current session lots
double profit_per_lot = 0.0;         // Average profit per lot
int winning_trades = 0;               // Count of profitable trades
int losing_trades = 0;                // Count of losing trades
double largest_profit = 0.0;          // Largest single trade profit
double largest_loss = 0.0;            // Largest single trade loss
string performance_display = "";       // Performance display string
datetime last_display_update = 0;     // Last display update time

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== Grid Trading EA Started ===");

    trade.SetExpertMagicNumber(InpMagicNumber);
    trade.SetMarginMode();
    trade.SetTypeFillingBySymbol(_Symbol);

    // Proper symbol initialization
    if(!symbolInfo.Name(_Symbol))
    {
        Print("ERROR: Failed to set symbol name");
        return INIT_FAILED;
    }

    // Add symbol to Market Watch if needed
    if(!SymbolSelect(_Symbol, true))
    {
        Print("ERROR: Failed to select symbol in Market Watch");
        return INIT_FAILED;
    }

    // Wait for symbol to be available
    int attempts = 0;
    while(!symbolInfo.RefreshRates() && attempts < 10)
    {
        Sleep(1000);
        attempts++;
        Print("Waiting for symbol data... attempt ", attempts);
    }

    if(attempts >= 10)
    {
        Print("ERROR: Symbol data not available after 10 attempts");
        return INIT_FAILED;
    }

    initial_balance = account.Balance();

    // Check symbol specifications
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    double lot_step = symbolInfo.LotsStep();
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    Print("Symbol: ", _Symbol);
    Print("Current Ask: ", current_ask, " Bid: ", current_bid);
    Print("Min Lot: ", min_lot, " Max Lot: ", max_lot, " Lot Step: ", lot_step);
    Print("Initial Balance: $", initial_balance);
    Print("Grid Step: ", InpGridStep, " points");
    Print("Max Levels: ", InpMaxLevels);

    // Validate prices
    if(current_ask <= 0 || current_bid <= 0)
    {
        Print("ERROR: Invalid prices - Ask: ", current_ask, " Bid: ", current_bid);
        return INIT_FAILED;
    }

    // Validate lot size
    if(InpBaseLotSize < min_lot)
    {
        Print("ERROR: Base lot size ", InpBaseLotSize, " is less than minimum ", min_lot);
        return INIT_PARAMETERS_INCORRECT;
    }

    // Clear existing positions with our magic number
    CloseAllPositions();
    ResetGrid();

    // Initialize hedge arrays
    ArrayInitialize(hedge_prices, 0.0);
    ArrayInitialize(hedge_lots, 0.0);
    ArrayInitialize(hedge_tickets, 0);
    // Initialize string array manually
    for(int i = 0; i < 50; i++)
    {
        hedge_directions[i] = "";
    }
    hedge_count = 0;

    // Initialize FVG arrays
    ArrayInitialize(fvg_bull_gaps, 0.0);
    ArrayInitialize(fvg_bear_gaps, 0.0);
    fvg_bull_count = 0;
    fvg_bear_count = 0;
    current_grid_step = InpGridStep;
    last_fvg_check = 0;
    fvg_detected = false;

    // Initialize indicators
    ma_fast_handle = iMA(_Symbol, PERIOD_CURRENT, InpFastMA, 0, MODE_EMA, PRICE_CLOSE);
    ma_slow_handle = iMA(_Symbol, PERIOD_CURRENT, InpSlowMA, 0, MODE_EMA, PRICE_CLOSE);
    atr_handle = iATR(_Symbol, PERIOD_CURRENT, 14);

    if(ma_fast_handle == INVALID_HANDLE || ma_slow_handle == INVALID_HANDLE || atr_handle == INVALID_HANDLE)
    {
        Print("ERROR: Failed to create indicators");
        return INIT_FAILED;
    }

    // Initialize risk management
    daily_start_balance = account.Balance();
    last_daily_reset = TimeCurrent();
    daily_limit_reached = false;
    daily_trade_count = 0;        // 🔄 Start fresh
    daily_profit = 0.0;
    max_daily_profit = 0.0;
    emergency_stop = false;
    volatility_multiplier = 1.0;
    last_atr_value = 0.0;
    last_force_close = 0;         // 🔄 Reset force close time
    grid_start_time = 0;          // 🔄 Reset grid time
    total_lot_volume = 0.0;       // 🔄 Reset lot volume

    // 📊 Initialize performance tracking
    daily_total_lots = 0.0;
    session_lots = 0.0;
    profit_per_lot = 0.0;
    winning_trades = 0;
    losing_trades = 0;
    largest_profit = 0.0;
    largest_loss = 0.0;
    last_display_update = 0;

    Print("🚀 FRESH START - All counters reset for aggressive lot spinning!");

    // Initialize hedge variables
    hedge_start_price = 0.0;
    next_hedge_level_price = 0.0;

    // Force reset everything to ensure clean start
    ForceResetCounters();

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== Grid Trading EA Stopped ===");
    Print("Reason: ", reason);

    // Release indicator handles
    if(ma_fast_handle != INVALID_HANDLE)
        IndicatorRelease(ma_fast_handle);
    if(ma_slow_handle != INVALID_HANDLE)
        IndicatorRelease(ma_slow_handle);
    if(atr_handle != INVALID_HANDLE)
        IndicatorRelease(atr_handle);

    CloseAllPositions();
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_log_time = 0;

    // Refresh symbol info
    symbolInfo.RefreshRates();

    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    // 📊 ENHANCED Performance Display every 10 seconds
    if(TimeCurrent() - last_log_time > 10)
    {
        UpdatePerformanceDisplay();
        Print("📊 PERFORMANCE: ", performance_display);
        Print("🎯 LOTS: Daily=", daily_total_lots, "/", daily_volume_target, " | Session=", session_lots, " | Profit/Lot=$", DoubleToString(profit_per_lot, 2));
        Print("💹 TRADES: W/L=", winning_trades, "/", losing_trades, " | Win%=", DoubleToString(GetWinRate(), 1), "% | P&L=$", daily_profit);
        last_log_time = TimeCurrent();
    }

    // Check if we have valid prices
    if(current_ask <= 0 || current_bid <= 0)
    {
        Print("ERROR: Invalid prices - Ask: ", current_ask, " Bid: ", current_bid);
        return;
    }

    if(!IsTimeToTrade())
    {
        Print("Outside trading hours");
        return;
    }

    UpdatePositions();
    CheckProfitTarget();

    // Check daily risk limits and market conditions
    if(!CheckDailyRiskLimits() || emergency_stop)
    {
        Print("Daily risk limit or emergency stop - stopping trading");
        return;
    }

    // Update market volatility
    UpdateMarketVolatility();

    // Check trend and manage hedging
    CheckTrend();
    ManageHedging();

    // Update FVG-based grid step
    if(InpUseFVGGrid)
    {
        UpdateFVGGridStep();
    }

    // Grid trading ไม่ใช้ Stop Loss เพราะต้องรอให้ราคากลับมา

    // 🚀 HYPER AGGRESSIVE GRID RESTART for maximum lot spinning
    if(!grid_active)
    {
        bool can_trade = (daily_trade_count < InpMaxTradesPerDay);
        int cooldown_period = GetDynamicCooldown();
        bool cooldown_ok = (TimeCurrent() - last_order_time >= cooldown_period);
        bool market_ok = IsMarketConditionGood();

        // 📊 Simplified debug - less spam for high frequency
        static datetime last_debug = 0;
        if(TimeCurrent() - last_debug > 30) // Debug every 30 seconds
        {
            if(!can_trade) Print("🚫 Trade limit: ", daily_trade_count, "/", InpMaxTradesPerDay);
            if(!cooldown_ok) Print("⏳ Cooldown: ", TimeCurrent() - last_order_time, "s/", cooldown_period, "s");
            if(!market_ok) Print("🌪️ Market wait");
            last_debug = TimeCurrent();
        }

        if(can_trade && cooldown_ok && market_ok)
        {
            // 🔥 INSTANT restart conditions
            bool instant_restart = false;

            // Instant restart after profit
            if(TimeCurrent() - last_force_close < 30) instant_restart = true;

            // Instant restart if very profitable today
            if(daily_profit > 100.0 && daily_trade_count < 200) instant_restart = true;

            // Instant restart during peak hours with low count
            MqlDateTime time_struct;
            TimeToStruct(TimeCurrent(), time_struct);
            int hour = time_struct.hour;
            if((hour >= 8 && hour <= 16) && daily_trade_count < 50) instant_restart = true;

            if(instant_restart || (TimeCurrent() - last_order_time >= cooldown_period))
            {
                Print("🚀 GRID #", daily_trade_count + 1, " | P&L: $", daily_profit, " | Volume: ", daily_total_lots, "/", daily_volume_target, " lots");
                UpdatePerformanceDisplay(); // Update display when starting new grid
                StartNewGrid();
                return;
            }
        }
    }

    // Manage existing grid
    if(grid_direction == "BUY")
    {
        ManageBuyGrid();
    }
    else if(grid_direction == "SELL")
    {
        ManageSellGrid();
    }
}

//+------------------------------------------------------------------+
//| Check if it's time to trade                                      |
//+------------------------------------------------------------------+
bool IsTimeToTrade()
{
    if(!InpUseTimeFilter) return true;

    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);

    return (time_struct.hour >= InpStartHour && time_struct.hour < InpEndHour);
}

//+------------------------------------------------------------------+
//| Start new grid                                                   |
//+------------------------------------------------------------------+
void StartNewGrid()
{
    // Use direct price calls as backup
    double current_ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double current_bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    // If direct calls also fail, use last known price
    if(current_ask <= 0) current_ask = symbolInfo.Ask();
    if(current_bid <= 0) current_bid = symbolInfo.Bid();

    Print("StartNewGrid called - Ask: ", current_ask, " Bid: ", current_bid);

    if(current_ask <= 0 || current_bid <= 0)
    {
        Print("ERROR: Still invalid prices in StartNewGrid");
        return;
    }

    // Simple alternating strategy - no MA dependency
    static bool last_was_buy = false;

    if(!last_was_buy)
    {
        // Start BUY grid
        grid_direction = "BUY";
        grid_start_price = current_ask;
        grid_start_time = TimeCurrent();
        total_lot_volume = InpBaseLotSize;
        OpenBuyOrder(current_ask, InpBaseLotSize, 0);
        Print("Started BUY Grid at ", current_ask, " with lot: ", InpBaseLotSize);
        last_was_buy = true;
    }
    else
    {
        // Start SELL grid
        grid_direction = "SELL";
        grid_start_price = current_bid;
        grid_start_time = TimeCurrent();
        total_lot_volume = InpBaseLotSize;
        OpenSellOrder(current_bid, InpBaseLotSize, 0);
        Print("Started SELL Grid at ", current_bid, " with lot: ", InpBaseLotSize);
        last_was_buy = false;
    }

    grid_active = true;
}

//+------------------------------------------------------------------+
//| Manage BUY grid                                                  |
//+------------------------------------------------------------------+
void ManageBuyGrid()
{
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();
    double step_size = GetDynamicGridStep() * symbolInfo.Point(); // Use dynamic step

    // Add more BUY orders when price goes down (averaging down)
    if(buy_count < InpMaxLevels)
    {
        double next_buy_level = grid_start_price - (buy_count * step_size);

        if(current_ask <= next_buy_level &&
           TimeCurrent() - last_order_time > GetDynamicCooldown() &&
           current_ask > 0 && CanOpenNewPosition())
        {
            double lot_size = CalculateDynamicLotSize(InpBaseLotSize * MathPow(InpLotMultiplier, buy_count), buy_count);
            Print("BUY Grid Trigger (FVG Step: ", GetDynamicGridStep(), "): Current=", current_ask, " Target=", next_buy_level, " Level=", buy_count, " Lot=", lot_size);
            OpenBuyOrder(current_ask, lot_size, buy_count);
        }
        else
        {
            Print("BUY Grid Wait (FVG Step: ", GetDynamicGridStep(), "): Current=", current_ask, " Target=", next_buy_level, " TimeDiff=", TimeCurrent() - last_order_time);
        }
    }

    // Enhanced hedging - managed by ManageHedging() function
    // Old basic hedging code removed in favor of advanced trend-based hedging
}

//+------------------------------------------------------------------+
//| Manage SELL grid                                                 |
//+------------------------------------------------------------------+
void ManageSellGrid()
{
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();
    double step_size = GetDynamicGridStep() * symbolInfo.Point(); // Use dynamic step

    // Add more SELL orders when price goes up (averaging up)
    if(sell_count < InpMaxLevels)
    {
        double next_sell_level = grid_start_price + (sell_count * step_size);

        if(current_bid >= next_sell_level &&
           TimeCurrent() - last_order_time > GetDynamicCooldown() &&
           current_bid > 0 && CanOpenNewPosition())
        {
            double lot_size = CalculateDynamicLotSize(InpBaseLotSize * MathPow(InpLotMultiplier, sell_count), sell_count);
            Print("SELL Grid Trigger (FVG Step: ", GetDynamicGridStep(), "): Current=", current_bid, " Target=", next_sell_level, " Level=", sell_count, " Lot=", lot_size);
            OpenSellOrder(current_bid, lot_size, sell_count);
        }
        else
        {
            Print("SELL Grid Wait (FVG Step: ", GetDynamicGridStep(), "): Current=", current_bid, " Target=", next_sell_level, " TimeDiff=", TimeCurrent() - last_order_time);
        }
    }

    // Enhanced hedging - managed by ManageHedging() function
    // Old basic hedging code removed in favor of advanced trend-based hedging
}

//+------------------------------------------------------------------+
//| Open BUY order                                                   |
//+------------------------------------------------------------------+
void OpenBuyOrder(double price, double lot_size, int level)
{
    // Validate lot size
    lot_size = NormalizeLotSize(lot_size);
    if(lot_size <= 0)
    {
        Print("ERROR: Invalid lot size after normalization: ", lot_size);
        return;
    }

    // Use current market price for market orders
    double current_ask = symbolInfo.Ask();
    string comment = "Grid BUY L" + IntegerToString(level);

    if(trade.Buy(lot_size, _Symbol, 0, 0, 0, comment)) // ใช้ 0 สำหรับ market order
    {
        ulong ticket = trade.ResultOrder();

        buy_prices[buy_count] = current_ask; // บันทึกราคาปัจจุบัน
        buy_lots[buy_count] = lot_size;
        buy_tickets[buy_count] = ticket;
        buy_times[buy_count] = TimeCurrent();

        buy_count++;
        last_order_time = TimeCurrent();
        total_lot_volume += lot_size;

        // 📊 Update volume tracking
        daily_total_lots += lot_size;
        session_lots += lot_size;

        Print("🟢 BUY: Ticket=", ticket, " Lot=", lot_size, " Price=", current_ask, " | Daily Lots: ", daily_total_lots, "/", daily_volume_target);
    }
    else
    {
        Print("ERROR: Failed to open BUY order - ", trade.ResultRetcodeDescription());
        Print("Ask Price: ", current_ask, " Lot: ", lot_size, " Comment: ", comment);
    }
}

//+------------------------------------------------------------------+
//| Open SELL order                                                  |
//+------------------------------------------------------------------+
void OpenSellOrder(double price, double lot_size, int level)
{
    // Validate lot size
    lot_size = NormalizeLotSize(lot_size);
    if(lot_size <= 0)
    {
        Print("ERROR: Invalid lot size after normalization: ", lot_size);
        return;
    }

    // Use current market price for market orders
    double current_bid = symbolInfo.Bid();
    string comment = "Grid SELL L" + IntegerToString(level);

    if(trade.Sell(lot_size, _Symbol, 0, 0, 0, comment)) // ใช้ 0 สำหรับ market order
    {
        ulong ticket = trade.ResultOrder();

        sell_prices[sell_count] = current_bid; // บันทึกราคาปัจจุบัน
        sell_lots[sell_count] = lot_size;
        sell_tickets[sell_count] = ticket;
        sell_times[sell_count] = TimeCurrent();

        sell_count++;
        last_order_time = TimeCurrent();
        total_lot_volume += lot_size;

        // 📊 Update volume tracking
        daily_total_lots += lot_size;
        session_lots += lot_size;

        Print("🔴 SELL: Ticket=", ticket, " Lot=", lot_size, " Price=", current_bid, " | Daily Lots: ", daily_total_lots, "/", daily_volume_target);
    }
    else
    {
        Print("ERROR: Failed to open SELL order - ", trade.ResultRetcodeDescription());
        Print("Bid Price: ", current_bid, " Lot: ", lot_size, " Comment: ", comment);
    }
}

//+------------------------------------------------------------------+
//| Update positions                                                  |
//+------------------------------------------------------------------+
void UpdatePositions()
{
    // Check if grid positions are still open
    for(int i = 0; i < buy_count; i++)
    {
        if(buy_tickets[i] > 0)
        {
            if(!position.SelectByTicket(buy_tickets[i]))
            {
                buy_tickets[i] = 0; // Position closed
            }
        }
    }

    for(int i = 0; i < sell_count; i++)
    {
        if(sell_tickets[i] > 0)
        {
            if(!position.SelectByTicket(sell_tickets[i]))
            {
                sell_tickets[i] = 0; // Position closed
            }
        }
    }

    // Update hedge positions
    UpdateHedgePositions();
}

//+------------------------------------------------------------------+
//| Check profit target                                               |
//+------------------------------------------------------------------+
void CheckProfitTarget()
{
    double total_profit = GetTotalProfit();
    double current_balance = account.Balance();
    double current_drawdown = initial_balance - current_balance;
    double grid_profit = GetGridProfit();
    double hedge_profit = GetHedgeProfit();
    double daily_pnl = current_balance - daily_start_balance;

    // Calculate target profits based on lot volume - OPTIMIZED for high volume
    double target_profit = CalculateTargetProfit(total_lot_volume, InpProfitTargetPercent);
    double quick_profit = CalculateTargetProfit(total_lot_volume, InpQuickProfitPercent);

    // 🚀 OPTIMIZED profit taking for better profitability
    double micro_profit = total_lot_volume * 1.0; // $1.0 per lot (increased from $0.5)
    int holding_minutes = (grid_start_time > 0) ? (int)((TimeCurrent() - grid_start_time) / 60) : 0;

    // Log every 10 seconds for better monitoring
    static datetime last_log = 0;
    if(TimeCurrent() - last_log > 10)
    {
        Print("📊 P&L: $", total_profit, " | Lots: ", total_lot_volume, " | Target: $", target_profit,
              " | Quick: $", quick_profit, " | Hold: ", holding_minutes, "m | Daily: ", daily_trade_count, " trades");
        last_log = TimeCurrent();
    }

    // AGGRESSIVE LOT SPINNING STRATEGY
    // 0. 💨 MICRO PROFIT scalping - ปรับเพิ่มกำไร
    if(total_profit >= micro_profit && (buy_count + sell_count) == 1)
    {
        Print("💨 MICRO SCALP: $", total_profit, " (", DoubleToString(total_profit/total_lot_volume*100, 2), "% | ", total_lot_volume, " lots)");
        RecordTradeResult(total_profit);
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 1;
        return;
    }

    // 1. 🚀 ULTRA QUICK scalping - ปรับเพิ่มกำไร
    if(total_profit >= quick_profit && (buy_count + sell_count) <= 2)
    {
        Print("⚡ ULTRA QUICK: $", total_profit, " (", DoubleToString(total_profit/total_lot_volume*100, 2), "% | ", total_lot_volume, " lots)");
        RecordTradeResult(total_profit);
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 2;
        return;
    }

    // 2. 🎯 MAIN TARGET reached
    if(total_profit >= target_profit || (InpForceProfitClose && total_profit >= target_profit * 0.7))
    {
        Print("🎯 TARGET HIT: $", total_profit, " (", DoubleToString(total_profit/total_lot_volume*100, 2), "% | ", total_lot_volume, " lots)");
        RecordTradeResult(total_profit);
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 2;
        return;
    }

    // 3. ⏰ TIME-BASED forced close - STRICTER profit requirement
    if(holding_minutes >= InpMaxHoldingMinutes && total_profit > total_lot_volume * InpMinLotProfit)
    {
        Print("⏰ TIME FORCE: ", holding_minutes, "m | $", total_profit, " | Lot spinning");
        RecordTradeResult(total_profit);
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 3;
        return;
    }

    // 3.1 🚫 LOSS PREVENTION - Close losing trades early
    if(holding_minutes >= 5 && total_profit < -total_lot_volume * 2.0 && (buy_count + sell_count) <= 3)
    {
        Print("🚫 LOSS CUT: ", holding_minutes, "m | Loss: $", total_profit, " | Prevent big loss");
        RecordTradeResult(total_profit);
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 10; // Longer cooldown after loss
        return;
    }

    // 3.5. 🏃 AGGRESSIVE time force - ANY profit after 5 minutes
    if(holding_minutes >= 5 && total_profit > 0.1)
    {
        Print("🏃 FAST FORCE: ", holding_minutes, "m | Any profit: $", total_profit, " | Spinning lots faster");
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 2;
        return;
    }

    // 4. Close profitable hedge positions first
    if(hedge_profit > 15.0 && hedge_count > 0)
    {
        CloseHedgePositions();
        Print("🛡️ Hedge profit taken: $", hedge_profit);
    }

    // 5. Emergency stop if max drawdown exceeded
    if(current_drawdown >= InpMaxDrawdown)
    {
        Print("🚨 EMERGENCY STOP - Drawdown: $", current_drawdown, " >= $", InpMaxDrawdown);
        CloseAllPositions();
        ResetGrid();
        emergency_stop = true;
        last_order_time = TimeCurrent() + 60; // รอแค่ 1 นาที
        return;
    }

    // 6. Force close any position after timeout (fix timeout calculation)
    if(grid_start_time > 0 && holding_minutes >= InpMaxHoldingMinutes * 2 && holding_minutes < 1440) // Max 24 hours
    {
        // 🚑 Force close to prevent holding forever
        Print("⏱️ TIMEOUT FORCE: ", holding_minutes, "m | P&L: $", total_profit, " | Must close for lot spinning");
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++; // 🚫 Prevent overflow
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 15;
        return;
    }

    // 6.5. Earlier force close if small profit available
    if(holding_minutes >= InpMaxHoldingMinutes && total_profit > total_lot_volume * 0.05)
    {
        Print("⏰ EARLY FORCE: ", holding_minutes, "m | Small profit: $", total_profit);
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++; // 🚫 Prevent overflow
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 5;
        return;
    }

    // 7. Close losing hedge positions if they're making things worse
    if(hedge_profit < -30.0 && current_drawdown > InpMaxDrawdown * 0.3)
    {
        CloseHedgePositions();
        Print("🛡️ Emergency hedge close: $", hedge_profit);
    }

    // 8. 💎 SMART PARTIAL profit taking for sustained volume
    if(total_profit > target_profit * 0.4 && (buy_count + sell_count) >= 2 && total_lot_volume >= 0.2)
    {
        double partial_profit = GetTotalProfit() * 0.6; // Take 60% of profit
        CloseHalfPositions();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++;
        daily_profit += partial_profit;
        Print("💎 SMART PARTIAL: $", partial_profit, " (", DoubleToString(partial_profit/total_lot_volume*100, 1), "%) | Keep spinning");
        last_force_close = TimeCurrent();
        return;
    }

    // 9. Aggressive trailing stop for lot spinning
    if(total_profit > max_daily_profit)
    {
        max_daily_profit = total_profit;
    }

    // Close if profit drops from peak (protect gains aggressively)
    if(max_daily_profit > target_profit * 0.5 && total_profit < max_daily_profit * 0.8)
    {
        Print("📉 TRAILING: Peak=$", max_daily_profit, " Now=$", total_profit, " | Protecting profits");
        CloseAllPositions();
        ResetGrid();
        if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++; // 🚫 Prevent overflow
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 3; // รอแค่ 3 วินาที
        return;
    }

    // 10. Grid depth protection
    if((buy_count + sell_count) >= InpMaxLevels && total_profit < -target_profit)
    {
        Print("🚫 MAX GRID DEPTH - Force close to prevent further loss");
        CloseAllPositions();
        ResetGrid();
        last_order_time = TimeCurrent() + 30; // รอแค่ 30 วินาที
    }
}

//+------------------------------------------------------------------+
//| Get total profit                                                  |
//+------------------------------------------------------------------+
double GetTotalProfit()
{
    double total_profit = 0.0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                total_profit += position.Profit() + position.Swap() + position.Commission();
            }
        }
    }

    return total_profit;
}

//+------------------------------------------------------------------+
//| Close half of positions for partial profit taking               |
//+------------------------------------------------------------------+
void CloseHalfPositions()
{
    int positions_closed = 0;
    int total_positions = GetPositionCount();
    int positions_to_close = total_positions / 2;

    for(int i = PositionsTotal() - 1; i >= 0 && positions_closed < positions_to_close; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                string comment = position.Comment();
                // Close grid positions first (not hedge)
                if(StringFind(comment, "Grid ") >= 0)
                {
                    if(trade.PositionClose(position.Ticket()))
                    {
                        positions_closed++;
                        Print("Partial close - Ticket: ", position.Ticket());
                    }
                }
            }
        }
    }

    Print("Closed ", positions_closed, " of ", total_positions, " positions for partial profit taking");
}

//+------------------------------------------------------------------+
//| Close all positions                                               |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                trade.PositionClose(position.Ticket());
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Reset grid                                                        |
//+------------------------------------------------------------------+
void ResetGrid()
{
    buy_count = 0;
    sell_count = 0;
    grid_active = false;
    grid_direction = "NONE";
    grid_start_price = 0.0;
    grid_start_time = 0; // 🔄 Reset to 0, will be set when new grid starts
    total_lot_volume = 0.0;
    max_daily_profit = 0.0; // Reset peak profit tracking

    // Clear arrays
    ArrayInitialize(buy_prices, 0.0);
    ArrayInitialize(buy_lots, 0.0);
    ArrayInitialize(buy_tickets, 0);
    ArrayInitialize(buy_times, 0);

    ArrayInitialize(sell_prices, 0.0);
    ArrayInitialize(sell_lots, 0.0);
    ArrayInitialize(sell_tickets, 0);
    ArrayInitialize(sell_times, 0);

    // Reset hedge arrays
    ArrayInitialize(hedge_prices, 0.0);
    ArrayInitialize(hedge_lots, 0.0);
    ArrayInitialize(hedge_tickets, 0);
    // Reset string array manually
    for(int i = 0; i < 50; i++)
    {
        hedge_directions[i] = "";
    }
    hedge_count = 0;

    // Reset trend variables
    current_trend = "NONE";
    trend_reversed = false;
    last_trend_price = 0.0;
    last_trend_check = 0;

    // Reset FVG variables
    ArrayInitialize(fvg_bull_gaps, 0.0);
    ArrayInitialize(fvg_bear_gaps, 0.0);
    fvg_bull_count = 0;
    fvg_bear_count = 0;
    current_grid_step = InpGridStep;
    last_fvg_check = 0;
    fvg_detected = false;

    // Reset hedge strategy flags
    is_reversing = false;
    is_following = false;
    last_hedge_time = 0;
    hedge_start_price = 0.0;
    next_hedge_level_price = 0.0;

    // Reset daily counters if new day (improved logic)
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    MqlDateTime last_reset_struct;
    TimeToStruct(last_daily_reset, last_reset_struct);

    if(time_struct.day != last_reset_struct.day || daily_trade_count > InpMaxTradesPerDay)
    {
        daily_trade_count = 0;
        daily_profit = 0.0;
        max_daily_profit = 0.0;
        emergency_stop = false;
        last_daily_reset = TimeCurrent();
        Print("🔄 DAILY COUNTERS RESET in ResetGrid()");
    }

    // Reset daily tracking if needed
    if(daily_limit_reached)
    {
        daily_limit_reached = false;
    }

    // Reset last order time to allow immediate new grid
    last_order_time = 0;

    // 🧠 Debug reset confirmation
    Print("🔄 GRID RESET COMPLETE - Ready for lot spinning");
}

//+------------------------------------------------------------------+
//| Update Performance Display                                      |
//+------------------------------------------------------------------+
void UpdatePerformanceDisplay()
{
    // Calculate performance metrics
    double completion_percent = (daily_total_lots / daily_volume_target) * 100.0;
    double win_rate = GetWinRate();

    if(daily_total_lots > 0)
        profit_per_lot = daily_profit / daily_total_lots;
    else
        profit_per_lot = 0.0;

    // Create performance display string
    performance_display = StringFormat(
        "Vol: %.2f/%.0f (%.1f%%) | P&L: $%.2f (%.2f/lot) | W/L: %d/%d (%.1f%%) | Max: +$%.2f/-$%.2f",
        daily_total_lots, daily_volume_target, completion_percent,
        daily_profit, profit_per_lot,
        winning_trades, losing_trades, win_rate,
        largest_profit, MathAbs(largest_loss)
    );

    // Update comment on chart
    string chart_comment = StringFormat(
        "📊 GRID TRADING PERFORMANCE 📊\n" +
        "🎯 Volume: %.2f / %.0f lots (%.1f%% complete)\n" +
        "💰 Daily P&L: $%.2f (Average: $%.2f per lot)\n" +
        "🏆 Trades: %d Wins / %d Losses (%.1f%% win rate)\n" +
        "📈 Best: +$%.2f | Worst: -$%.2f\n" +
        "🔄 Session: %d trades | %.2f lots\n" +
        "🕑 Status: %s | %s",
        daily_total_lots, daily_volume_target, completion_percent,
        daily_profit, profit_per_lot,
        winning_trades, losing_trades, win_rate,
        largest_profit, MathAbs(largest_loss),
        daily_trade_count, session_lots,
        (grid_active ? "ACTIVE" : "WAITING"), grid_direction
    );

    Comment(chart_comment);
}

//+------------------------------------------------------------------+
//| Record Trade Result for Performance Tracking                   |
//+------------------------------------------------------------------+
void RecordTradeResult(double profit)
{
    if(profit > 0)
    {
        winning_trades++;
        if(profit > largest_profit)
            largest_profit = profit;
    }
    else
    {
        losing_trades++;
        if(profit < largest_loss)
            largest_loss = profit;
    }

    // Reset session lots after each trade
    session_lots = 0.0;
}

//+------------------------------------------------------------------+
//| Get Win Rate Percentage                                         |
//+------------------------------------------------------------------+
double GetWinRate()
{
    int total_trades = winning_trades + losing_trades;
    if(total_trades == 0) return 0.0;
    return (double)winning_trades / total_trades * 100.0;
}

//+------------------------------------------------------------------+
//| Detect Fair Value Gaps (FVG)                                    |
//+------------------------------------------------------------------+
bool DetectFVG()
{
    if(TimeCurrent() - last_fvg_check < 30) return fvg_detected; // Check every 30 seconds

    fvg_detected = false;
    fvg_bull_count = 0;
    fvg_bear_count = 0;
    ArrayInitialize(fvg_bull_gaps, 0.0);
    ArrayInitialize(fvg_bear_gaps, 0.0);

    double high[], low[], close[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);

    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, InpFVGLookback + 3, high) <= 0 ||
       CopyLow(_Symbol, PERIOD_CURRENT, 0, InpFVGLookback + 3, low) <= 0 ||
       CopyClose(_Symbol, PERIOD_CURRENT, 0, InpFVGLookback + 3, close) <= 0)
    {
        Print("Error: Failed to copy price data for FVG detection");
        return false;
    }

    // Scan for FVG patterns
    for(int i = 2; i < InpFVGLookback; i++)
    {
        // Bullish FVG: low[i-1] > high[i+1]
        if(low[i-1] > high[i+1])
        {
            double gap_size = (low[i-1] - high[i+1]) / symbolInfo.Point();
            if(gap_size >= InpMinGridStep * InpFVGSensitivity && fvg_bull_count < 10)
            {
                fvg_bull_gaps[fvg_bull_count] = gap_size;
                fvg_bull_count++;
                fvg_detected = true;
                Print("Bullish FVG detected: ", gap_size, " points at bar ", i);
            }
        }

        // Bearish FVG: high[i-1] < low[i+1]
        if(high[i-1] < low[i+1])
        {
            double gap_size = (low[i+1] - high[i-1]) / symbolInfo.Point();
            if(gap_size >= InpMinGridStep * InpFVGSensitivity && fvg_bear_count < 10)
            {
                fvg_bear_gaps[fvg_bear_count] = gap_size;
                fvg_bear_count++;
                fvg_detected = true;
                Print("Bearish FVG detected: ", gap_size, " points at bar ", i);
            }
        }
    }

    last_fvg_check = TimeCurrent();
    return fvg_detected;
}

//+------------------------------------------------------------------+
//| Update Grid Step Based on FVG Analysis                          |
//+------------------------------------------------------------------+
void UpdateFVGGridStep()
{
    if(!DetectFVG())
    {
        // No FVG detected, use default or ATR-based step
        current_grid_step = InpGridStep;
        return;
    }

    double total_gap_size = 0.0;
    int total_gaps = fvg_bull_count + fvg_bear_count;

    if(total_gaps == 0)
    {
        current_grid_step = InpGridStep;
        return;
    }

    // Calculate average FVG size
    for(int i = 0; i < fvg_bull_count; i++)
    {
        total_gap_size += fvg_bull_gaps[i];
    }
    for(int i = 0; i < fvg_bear_count; i++)
    {
        total_gap_size += fvg_bear_gaps[i];
    }

    double average_fvg_size = total_gap_size / total_gaps;

    // Apply FVG multiplier and constraints
    double new_grid_step = average_fvg_size * InpFVGMultiplier;

    // Apply min/max constraints
    if(new_grid_step < InpMinGridStep)
        new_grid_step = InpMinGridStep;
    if(new_grid_step > InpMaxGridStep)
        new_grid_step = InpMaxGridStep;

    // Smooth the transition to avoid sudden changes
    if(current_grid_step > 0)
    {
        current_grid_step = (current_grid_step * 0.7) + (new_grid_step * 0.3);
    }
    else
    {
        current_grid_step = new_grid_step;
    }

    last_fvg_size = average_fvg_size;

    Print("FVG Grid Update - Avg FVG: ", average_fvg_size, " New Step: ", current_grid_step,
          " Bull FVGs: ", fvg_bull_count, " Bear FVGs: ", fvg_bear_count);
}

//+------------------------------------------------------------------+
//| Get Current Dynamic Grid Step                                   |
//+------------------------------------------------------------------+
double GetDynamicGridStep()
{
    if(InpUseFVGGrid && current_grid_step > 0)
    {
        return current_grid_step;
    }
    return InpGridStep; // Fallback to static step
}

//+------------------------------------------------------------------+
//| Check Daily Risk Limits                                         |
//+------------------------------------------------------------------+
bool CheckDailyRiskLimits()
{
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);

    // Reset daily limits at midnight
    MqlDateTime last_reset_struct;
    TimeToStruct(last_daily_reset, last_reset_struct);

    if(time_struct.day != last_reset_struct.day)
    {
        daily_start_balance = account.Balance();
        last_daily_reset = TimeCurrent();
        daily_limit_reached = false;
        daily_trade_count = 0; // 🔄 RESET TRADE COUNT
        daily_profit = 0.0;    // 🔄 RESET DAILY PROFIT
        max_daily_profit = 0.0;
        emergency_stop = false;
        Print("📅 DAILY RESET - New day started! Balance: $", daily_start_balance, " | Trade count reset to 0");
    }

    // Check daily loss limit
    double daily_loss = daily_start_balance - account.Balance();
    if(daily_loss >= InpMaxDailyLoss)
    {
        if(!daily_limit_reached)
        {
            Print("Daily loss limit reached: $", daily_loss, " >= $", InpMaxDailyLoss);
            CloseAllPositions();
            ResetGrid();
            daily_limit_reached = true;
            emergency_stop = true;
        }
        return false;
    }

    // Check trade count limit
    if(daily_trade_count >= InpMaxTradesPerDay)
    {
        Print("Daily trade limit reached: ", daily_trade_count, " >= ", InpMaxTradesPerDay);
        return false;
    }

    // Reset emergency stop if profit is positive
    if(emergency_stop && daily_profit > 0)
    {
        emergency_stop = false;
        Print("Emergency stop reset - daily profit positive: $", daily_profit);
    }

    return true;
}

// CheckGridStopLoss ฟังก์ชันถูกเอาออกแล้ว เพราะ Grid Trading ไม่ควรมี Stop Loss

//+------------------------------------------------------------------+
//| Check Trend Direction and Strength                              |
//+------------------------------------------------------------------+
void CheckTrend()
{
    if(TimeCurrent() - last_trend_check < 10) return; // Check every 10 seconds

    double fast_ma = GetMovingAverage(InpFastMA);
    double slow_ma = GetMovingAverage(InpSlowMA);
    double current_price = (symbolInfo.Ask() + symbolInfo.Bid()) / 2;
    double price_diff = MathAbs(current_price - slow_ma);
    double threshold = InpTrendThreshold * symbolInfo.Point();

    string previous_trend = current_trend;

    // Determine trend direction
    if(fast_ma > slow_ma && price_diff > threshold)
    {
        current_trend = "BULLISH";
    }
    else if(fast_ma < slow_ma && price_diff > threshold)
    {
        current_trend = "BEARISH";
    }
    else
    {
        current_trend = "SIDEWAYS";
    }

    // Check for trend reversal
    if(previous_trend != "NONE" && previous_trend != current_trend && current_trend != "SIDEWAYS")
    {
        trend_reversed = true;
        last_trend_price = current_price;
        Print("Trend Reversal Detected: ", previous_trend, " -> ", current_trend, " at ", current_price);
    }

    last_trend_check = TimeCurrent();
    Print("Current Trend: ", current_trend, " Fast MA: ", fast_ma, " Slow MA: ", slow_ma);
}

//+------------------------------------------------------------------+
//| Simplified Smart Hedging Strategy                               |
//+------------------------------------------------------------------+
void ManageHedging()
{
    // ⚡ Simplified for lot spinning - reduced hedging complexity
    if(!InpUseHedging || !grid_active || daily_trade_count > 200) return; // Reduced hedging for lot spinning

    // 🚑 Skip hedging if holding too long (focus on forced closing)
    int holding_minutes = (int)((TimeCurrent() - grid_start_time) / 60);
    if(holding_minutes > InpMaxHoldingMinutes * 0.5) return;

    double current_price = (symbolInfo.Ask() + symbolInfo.Bid()) / 2;
    double average_grid_price = 0.0;
    double total_grid_lots = 0.0;
    double grid_profit = GetGridProfit();

    // Calculate average grid price and total lots
    if(grid_direction == "BUY")
    {
        average_grid_price = GetAverageBuyPrice();
        total_grid_lots = GetTotalBuyLots();
    }
    else if(grid_direction == "SELL")
    {
        average_grid_price = GetAverageSellPrice();
        total_grid_lots = GetTotalSellLots();
    }

    if(average_grid_price <= 0 || total_grid_lots <= 0) return;

    double price_diff = MathAbs(current_price - average_grid_price);
    double trigger_distance = InpReverseTrigger * symbolInfo.Point();

    // Smart hedging logic - only hedge when grid is significantly underwater
    bool should_hedge = false;
    string hedge_type = "";

    // 1. Hedge when grid is losing significantly and trend is opposite
    if(grid_profit < -20.0 && price_diff > trigger_distance && hedge_count < InpMaxHedgeLevels)
    {
        if(grid_direction == "BUY" && current_trend == "BEARISH")
        {
            should_hedge = true;
            hedge_type = "SELL"; // Hedge with SELL positions
        }
        else if(grid_direction == "SELL" && current_trend == "BULLISH")
        {
            should_hedge = true;
            hedge_type = "BUY"; // Hedge with BUY positions
        }
    }

    // 2. Follow strong trends for additional profit
    if(hedge_count > 0 && hedge_count < InpMaxHedgeLevels)
    {
        double hedge_profit = GetHedgeProfit();
        if(hedge_profit > 10.0) // Hedges are profitable, continue trend following
        {
            if(current_trend == "BULLISH" && TimeCurrent() - last_hedge_time > 30)
            {
                should_hedge = true;
                hedge_type = "BUY";
            }
            else if(current_trend == "BEARISH" && TimeCurrent() - last_hedge_time > 30)
            {
                should_hedge = true;
                hedge_type = "SELL";
            }
        }
    }

    // Execute hedge if conditions are met
    if(should_hedge && CanOpenNewPosition())
    {
        double hedge_lot = total_grid_lots * InpHedgeStepSize * volatility_multiplier;
        hedge_lot = CalculateDynamicLotSize(hedge_lot, hedge_count);

        if(hedge_type == "BUY")
        {
            string comment = "Hedge BUY " + IntegerToString(hedge_count);
            if(trade.Buy(hedge_lot, _Symbol, 0, 0, 0, comment))
            {
                RecordHedgePosition(current_price, hedge_lot, trade.ResultOrder(), "BUY");
                Print("🛡️ Smart Hedge BUY opened: Lot=", hedge_lot, " Price=", current_price);
            }
        }
        else if(hedge_type == "SELL")
        {
            string comment = "Hedge SELL " + IntegerToString(hedge_count);
            if(trade.Sell(hedge_lot, _Symbol, 0, 0, 0, comment))
            {
                RecordHedgePosition(current_price, hedge_lot, trade.ResultOrder(), "SELL");
                Print("🛡️ Smart Hedge SELL opened: Lot=", hedge_lot, " Price=", current_price);
            }
        }
    }

    // Close hedges if grid becomes profitable
    if(grid_profit > 5.0 && hedge_count > 0)
    {
        double hedge_profit = GetHedgeProfit();
        if(hedge_profit > -10.0) // Don't close if hedges are losing significantly
        {
            CloseHedgePositions();
            Print("🎯 Closed hedge positions - grid profitable: $", grid_profit);
        }
    }
}

//+------------------------------------------------------------------+
//| Record Hedge Position                                            |
//+------------------------------------------------------------------+
void RecordHedgePosition(double price, double lot_size, ulong ticket, string direction)
{
    if(hedge_count >= 50) return; // Array size limit

    hedge_prices[hedge_count] = price;
    hedge_lots[hedge_count] = lot_size;
    hedge_tickets[hedge_count] = ticket;
    hedge_directions[hedge_count] = direction;
    hedge_count++;
    last_hedge_time = TimeCurrent();
    if(daily_trade_count < InpMaxTradesPerDay) daily_trade_count++; // 🚫 Prevent overflow
}


//+------------------------------------------------------------------+
//| Get Moving Average                                                |
//+------------------------------------------------------------------+
double GetMovingAverage(int period)
{
    double ma_values[];
    int handle = (period == InpFastMA) ? ma_fast_handle : ma_slow_handle;

    if(handle != INVALID_HANDLE && CopyBuffer(handle, 0, 0, 1, ma_values) > 0)
    {
        return ma_values[0];
    }

    return symbolInfo.Bid(); // Fallback
}

//+------------------------------------------------------------------+
//| Get position count                                                |
//+------------------------------------------------------------------+
int GetPositionCount()
{
    int count = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                count++;
            }
        }
    }

    return count;
}

//+------------------------------------------------------------------+
//| Get average BUY price                                             |
//+------------------------------------------------------------------+
double GetAverageBuyPrice()
{
    double total_price = 0.0;
    double total_lots = 0.0;

    for(int i = 0; i < buy_count; i++)
    {
        if(buy_tickets[i] > 0)
        {
            total_price += buy_prices[i] * buy_lots[i];
            total_lots += buy_lots[i];
        }
    }

    return (total_lots > 0) ? total_price / total_lots : 0.0;
}

//+------------------------------------------------------------------+
//| Get average SELL price                                            |
//+------------------------------------------------------------------+
double GetAverageSellPrice()
{
    double total_price = 0.0;
    double total_lots = 0.0;

    for(int i = 0; i < sell_count; i++)
    {
        if(sell_tickets[i] > 0)
        {
            total_price += sell_prices[i] * sell_lots[i];
            total_lots += sell_lots[i];
        }
    }

    return (total_lots > 0) ? total_price / total_lots : 0.0;
}

//+------------------------------------------------------------------+
//| Get total BUY lots                                                |
//+------------------------------------------------------------------+
double GetTotalBuyLots()
{
    double total_lots = 0.0;

    for(int i = 0; i < buy_count; i++)
    {
        if(buy_tickets[i] > 0)
        {
            total_lots += buy_lots[i];
        }
    }

    return total_lots;
}

//+------------------------------------------------------------------+
//| Get total SELL lots                                               |
//+------------------------------------------------------------------+
double GetTotalSellLots()
{
    double total_lots = 0.0;

    for(int i = 0; i < sell_count; i++)
    {
        if(sell_tickets[i] > 0)
        {
            total_lots += sell_lots[i];
        }
    }

    return total_lots;
}

//+------------------------------------------------------------------+
//| Get Grid Profit Only                                            |
//+------------------------------------------------------------------+
double GetGridProfit()
{
    double grid_profit = 0.0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                string comment = position.Comment();
                if(StringFind(comment, "Grid ") >= 0)
                {
                    grid_profit += position.Profit() + position.Swap() + position.Commission();
                }
            }
        }
    }

    return grid_profit;
}

//+------------------------------------------------------------------+
//| Get Hedge Profit Only                                           |
//+------------------------------------------------------------------+
double GetHedgeProfit()
{
    double hedge_profit = 0.0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                string comment = position.Comment();
                if(StringFind(comment, "Hedge ") >= 0)
                {
                    hedge_profit += position.Profit() + position.Swap() + position.Commission();
                }
            }
        }
    }

    return hedge_profit;
}

//+------------------------------------------------------------------+
//| Close Hedge Positions Only                                      |
//+------------------------------------------------------------------+
void CloseHedgePositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                string comment = position.Comment();
                if(StringFind(comment, "Hedge ") >= 0)
                {
                    trade.PositionClose(position.Ticket());
                    Print("Closed hedge position: ", position.Ticket());
                }
            }
        }
    }

    // Reset hedge arrays after closing
    ArrayInitialize(hedge_prices, 0.0);
    ArrayInitialize(hedge_lots, 0.0);
    ArrayInitialize(hedge_tickets, 0);
    // Reset string array manually
    for(int i = 0; i < 50; i++)
    {
        hedge_directions[i] = "";
    }
    hedge_count = 0;
}

//+------------------------------------------------------------------+
//| Update Hedge Positions Status                                   |
//+------------------------------------------------------------------+
void UpdateHedgePositions()
{
    for(int i = 0; i < hedge_count; i++)
    {
        if(hedge_tickets[i] > 0)
        {
            if(!position.SelectByTicket(hedge_tickets[i]))
            {
                hedge_tickets[i] = 0; // Position closed
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Normalize lot size according to symbol specifications            |
//+------------------------------------------------------------------+
double NormalizeLotSize(double lot_size)
{
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    double lot_step = symbolInfo.LotsStep();

    // Ensure lot size is not below minimum
    if(lot_size < min_lot)
        lot_size = min_lot;

    // Ensure lot size is not above maximum
    if(lot_size > max_lot)
        lot_size = max_lot;

    // Round to nearest lot step
    lot_size = MathRound(lot_size / lot_step) * lot_step;

    return lot_size;
}

//+------------------------------------------------------------------+
//| Calculate Dynamic Lot Size Based on Market Conditions          |
//+------------------------------------------------------------------+
double CalculateDynamicLotSize(double base_lot, int level)
{
    double dynamic_lot = base_lot;

    // AGGRESSIVE LOT SIZING for volume spinning
    double balance = account.Balance();
    double equity_ratio = account.Equity() / balance;

    // Base multiplier based on account health
    double health_multiplier = 1.0;
    if(equity_ratio > 0.95) health_multiplier = 2.0;      // Account healthy - double lots
    else if(equity_ratio > 0.90) health_multiplier = 1.5; // Good condition - 50% more
    else if(equity_ratio > 0.85) health_multiplier = 1.2; // Normal
    else health_multiplier = 0.8;                         // Conservative

    dynamic_lot *= health_multiplier;

    // Volume boost based on daily performance
    if(daily_profit > 0 && daily_trade_count < 100)
        dynamic_lot *= 1.3; // 30% boost when profitable and low count

    // Time-based lot increase for fast spinning
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    int hour = time_struct.hour;
    if(hour >= 8 && hour <= 16) // Active trading hours
        dynamic_lot *= 1.2;

    // Progressive scaling - MORE AGGRESSIVE
    if(level == 0)
        dynamic_lot *= 1.5; // First position gets 50% boost
    else if(level <= 2)
        dynamic_lot *= (1.0 + level * 0.3); // 30% per level
    else
        dynamic_lot *= (1.0 + level * 0.4); // 40% per deep level

    // Apply volatility multiplier
    dynamic_lot *= volatility_multiplier;

    // Maximum lot based on balance - MORE AGGRESSIVE
    double max_allowed_lot = balance * 0.002; // 0.2% of balance per trade (doubled)
    if(dynamic_lot > max_allowed_lot)
        dynamic_lot = max_allowed_lot;

    // Minimum lot for volume spinning
    double min_spinning_lot = symbolInfo.LotsMin() * 2;
    if(dynamic_lot < min_spinning_lot)
        dynamic_lot = min_spinning_lot;

    return NormalizeLotSize(dynamic_lot);
}

//+------------------------------------------------------------------+
//| Check if Can Open New Position                                  |
//+------------------------------------------------------------------+
bool CanOpenNewPosition()
{
    // Check daily trade limit
    if(daily_trade_count >= InpMaxTradesPerDay)
        return false;

    // Check if emergency stop is active
    if(emergency_stop)
        return false;

    // Check account equity vs balance ratio
    double equity_ratio = account.Equity() / account.Balance();
    if(equity_ratio < 0.8) // Stop if equity is less than 80% of balance
    {
        Print("Equity ratio too low: ", equity_ratio);
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Get Dynamic Cooldown Period                                     |
//+------------------------------------------------------------------+
int GetDynamicCooldown()
{
    // 🚀 HYPER FAST cooldown for maximum lot spinning
    int base_cooldown = 1; // ULTRA FAST - 1 second default

    // Dynamic scaling based on trade count for sustained volume
    if(daily_trade_count > 200)
        base_cooldown = 5;      // High volume protection
    else if(daily_trade_count > 150)
        base_cooldown = 4;
    else if(daily_trade_count > 100)
        base_cooldown = 3;
    else if(daily_trade_count > 50)
        base_cooldown = 2;
    else
        base_cooldown = 1;      // Maximum speed for early trades

    // 🔥 INSTANT restart after profit
    if(TimeCurrent() - last_force_close < 60) // Within 1 minute of profit
        base_cooldown = 0; // INSTANT restart

    // Time-based speed boost
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    int hour = time_struct.hour;
    if(hour >= 8 && hour <= 16) // Peak trading hours
        base_cooldown = MathMax(base_cooldown - 1, 0); // At least 1 second faster

    // Profit-based acceleration
    if(daily_profit > 50.0) // If profitable today
        base_cooldown = MathMax(base_cooldown - 1, 0);

    // Volatility adjustment - minimal impact
    if(volatility_multiplier > 2.0) // Only extreme volatility
        base_cooldown += 1;

    return MathMax(base_cooldown, 0); // Never below 0
}

//+------------------------------------------------------------------+
//| Update Market Volatility                                        |
//+------------------------------------------------------------------+
void UpdateMarketVolatility()
{
    static datetime last_volatility_check = 0;

    // Update every 30 seconds
    if(TimeCurrent() - last_volatility_check < 30)
        return;

    // Get ATR for volatility measurement
    double atr_values[];

    if(atr_handle != INVALID_HANDLE && CopyBuffer(atr_handle, 0, 0, 1, atr_values) > 0)
    {
        double current_atr = atr_values[0];

        if(last_atr_value > 0)
        {
            // Calculate volatility multiplier
            double atr_ratio = current_atr / last_atr_value;

            if(atr_ratio > 1.3)
                volatility_multiplier = 0.7; // Reduce lot size in high volatility
            else if(atr_ratio < 0.7)
                volatility_multiplier = 1.3; // Increase lot size in low volatility
            else
                volatility_multiplier = 1.0; // Normal volatility
        }

        last_atr_value = current_atr;
    }

    last_volatility_check = TimeCurrent();
}

//+------------------------------------------------------------------+
//| Check Market Condition for New Grid                             |
//+------------------------------------------------------------------+
bool IsMarketConditionGood()
{
    // Don't trade during high volatility periods
    if(volatility_multiplier < 0.8)
    {
        Print("Market too volatile - waiting for stability");
        return false;
    }

    // Check spread condition
    double spread = symbolInfo.Spread() * symbolInfo.Point();
    double max_allowed_spread = GetDynamicGridStep() * symbolInfo.Point() * 0.3;

    if(spread > max_allowed_spread)
    {
        Print("Spread too high: ", spread, " vs max: ", max_allowed_spread);
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Calculate Target Profit Based on Lot Volume (% method)          |
//+------------------------------------------------------------------+
double CalculateTargetProfit(double lot_volume, double profit_percent)
{
    if(lot_volume <= 0) return 0.5; // Minimum $0.5 profit for micro trades

    // 🚀 OPTIMIZED for high-volume lot spinning
    double base_profit_per_lot = 50.0; // Reduced from 100 for faster trades
    double target = lot_volume * profit_percent * base_profit_per_lot;

    // 📈 Volume-based scaling - MORE PROFIT for higher volumes
    if(lot_volume >= 1.0) target *= 1.5;      // 50% bonus for 1+ lots
    if(lot_volume >= 2.0) target *= 1.3;      // Additional 30% for 2+ lots
    if(lot_volume >= 5.0) target *= 1.2;      // Additional 20% for 5+ lots

    // 🎯 Market-specific optimizations for lot spinning
    string symbol = _Symbol;
    if(StringFind(symbol, "EUR") >= 0 || StringFind(symbol, "USD") >= 0)
        target *= 1.0;  // Major pairs - standard
    else if(StringFind(symbol, "JPY") >= 0)
        target *= 0.3;  // JPY pairs - higher volume, lower per-pip
    else if(StringFind(symbol, "XAU") >= 0 || StringFind(symbol, "GOLD") >= 0)
        target *= 2.0;  // Gold - higher volatility, higher profit
    else if(StringFind(symbol, "GBP") >= 0)
        target *= 1.4;  // GBP - volatile, good for spinning
    else if(StringFind(symbol, "AUD") >= 0 || StringFind(symbol, "NZD") >= 0)
        target *= 1.1;  // Commodity pairs

    // ⚡ Daily progress bonus
    if(daily_trade_count < 50)
        target *= 0.8;  // Smaller targets early in day for faster spinning
    else if(daily_trade_count < 100)
        target *= 0.9;  // Slightly higher as day progresses

    // 🎰 Time-based adjustments
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    int hour = time_struct.hour;
    if(hour >= 8 && hour <= 10) target *= 0.7;  // Morning rush - quick profits
    if(hour >= 14 && hour <= 16) target *= 0.8; // Afternoon session

    // ⚙️ Optimized thresholds for volume spinning
    if(target < 0.3) target = 0.3;         // Minimum $0.3 for micro scalping
    if(target > 500.0) target = 500.0;     // Reduced max for faster cycling

    return target;
}

//+------------------------------------------------------------------+
//| Force Reset All Counters (Emergency function)                  |
//+------------------------------------------------------------------+
void ForceResetCounters()
{
    daily_trade_count = 0;
    daily_profit = 0.0;
    max_daily_profit = 0.0;
    emergency_stop = false;
    grid_start_time = 0;
    total_lot_volume = 0.0;
    last_force_close = 0;
    last_order_time = 0;
    grid_active = false;
    grid_direction = "NONE";

    Print("🚑 EMERGENCY RESET - All counters forced to zero for lot spinning!");
}