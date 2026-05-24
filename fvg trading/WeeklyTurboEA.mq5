//+------------------------------------------------------------------+
//|                                             WeeklyTurboEA.mq5   |
//|                                      EXTREME PERFORMANCE SYSTEM |
//|                                         TARGET: 20% PER WEEK    |
//+------------------------------------------------------------------+
#property copyright "Weekly Turbo EA"
#property link      ""
#property version   "1.00"
#property description "AGGRESSIVE EA - Target 20% Weekly Returns (1040% Annual)"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade trade;
CPositionInfo position;

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input group "=== TURBO SETTINGS ==="
input int InpMagicNumber = 88888;        // Magic Number
input double InpWeeklyTarget = 20.0;     // Weekly Target (%)
input double InpDailyTarget = 4.0;       // Daily Target (%) = 20%/5 days
input bool InpAggressiveMode = true;     // AGGRESSIVE MODE (High Risk)

input group "=== SCALING SYSTEM ==="
input double InpStartLot = 0.01;         // Starting Lot Size
input double InpScalingFactor = 1.2;     // Lot Scaling per Profit Cycle
input double InpMaxLotMultiplier = 50.0; // Max Lot Multiplier
input bool InpTurboCompound = true;      // Turbo Compound Growth

input group "=== RAPID GRID ==="
input int InpGridStep = 25;              // Grid Step (TIGHT for rapid trades)
input int InpMaxLevels = 15;             // Max Levels (HIGH exposure)
input double InpQuickProfit = 5.0;       // Quick Profit Target ($)
input double InpCycleProfit = 25.0;      // Cycle Profit Target ($)

input group "=== EXTREME RISK ==="
input double InpMaxRiskPercent = 25.0;   // Max Risk (EXTREME)
input double InpTurboStopLoss = 1000.0;  // Emergency Stop ($)
input int InpMaxTradesPerHour = 100;     // Max Trades per Hour
input bool InpNewsTrading = true;        // Trade During News (HIGH RISK)

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
double weekly_start_balance = 0;
double daily_start_balance = 0;
double current_lot_multiplier = 1.0;
datetime week_start = 0;
datetime day_start = 0;
datetime last_order_time = 0;
int trades_this_hour = 0;
datetime hour_start = 0;

// Performance tracking
double total_cycles_completed = 0;
double avg_profit_per_cycle = 0;
bool turbo_mode_active = false;

// Rapid grid system
struct TurboPosition
{
    double price;
    bool is_buy;
    ulong ticket;
    double lot_size;
    datetime time;
    bool is_active;
};

TurboPosition turbo_grid[100]; // Large array for aggressive trading
int grid_count = 0;
double grid_center = 0;
string grid_direction = "NONE";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== WEEKLY TURBO EA - EXTREME PERFORMANCE MODE ===");
    Print("WARNING: This EA uses AGGRESSIVE strategies for 20% weekly returns");
    Print("TARGET: 20% per week = 1040% annual return");

    trade.SetExpertMagicNumber(InpMagicNumber);

    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    weekly_start_balance = balance;
    daily_start_balance = balance;
    week_start = TimeCurrent();
    day_start = TimeCurrent();
    hour_start = TimeCurrent();

    Print("Starting Balance: $", balance);
    Print("Weekly Target: $", balance * InpWeeklyTarget / 100.0);
    Print("Daily Target: $", balance * InpDailyTarget / 100.0);
    Print("RISK LEVEL: EXTREME");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_log = 0;

    // Reset counters
    CheckTimeResets();

    // Performance monitoring
    if(TimeCurrent() - last_log > 10) // Log every 10 seconds in turbo mode
    {
        double balance = AccountInfoDouble(ACCOUNT_BALANCE);
        double weekly_pnl = balance - weekly_start_balance;
        double daily_pnl = balance - daily_start_balance;
        double weekly_percent = (weekly_pnl / weekly_start_balance) * 100;
        double daily_percent = (daily_pnl / daily_start_balance) * 100;

        Print("TURBO STATUS: Balance=$", balance,
              " WeeklyPnL=", weekly_percent, "%",
              " DailyPnL=", daily_percent, "%",
              " Cycles=", total_cycles_completed,
              " LotMult=", current_lot_multiplier);
        last_log = TimeCurrent();
    }

    // Check targets and adjust aggression
    CheckTargetsAndAdjust();

    // Safety emergency stop
    if(!EmergencySafetyCheck()) return;

    // Rate limiting
    if(trades_this_hour >= InpMaxTradesPerHour) return;

    // Main turbo trading logic
    ExecuteTurboStrategy();
}

//+------------------------------------------------------------------+
//| Execute Turbo Strategy                                            |
//+------------------------------------------------------------------+
void ExecuteTurboStrategy()
{
    double current_profit = GetTotalProfit();

    // Quick profit taking for rapid cycles
    if(current_profit >= InpQuickProfit)
    {
        CloseAllPositions();
        total_cycles_completed++;
        UpdateLotMultiplier();
        ResetTurboGrid();
        Print("QUICK CYCLE COMPLETE: $", current_profit, " Cycles: ", total_cycles_completed);
        return;
    }

    // Larger cycle completion
    if(current_profit >= InpCycleProfit)
    {
        CloseAllPositions();
        total_cycles_completed += 2; // Worth 2 cycles
        UpdateLotMultiplier();
        ResetTurboGrid();
        Print("MAJOR CYCLE COMPLETE: $", current_profit, " Cycles: ", total_cycles_completed);
        return;
    }

    // Manage turbo grid
    ManageTurboGrid();
}

//+------------------------------------------------------------------+
//| Manage Turbo Grid for Maximum Speed                              |
//+------------------------------------------------------------------+
void ManageTurboGrid()
{
    int active_count = CountActivePositions();

    // Start new turbo grid
    if(active_count == 0 && TimeCurrent() - last_order_time > 1) // Very fast restart
    {
        StartTurboGrid();
        return;
    }

    // Add to grid rapidly
    if(active_count > 0 && active_count < InpMaxLevels && TimeCurrent() - last_order_time > 1)
    {
        AddToTurboGrid();
    }
}

//+------------------------------------------------------------------+
//| Start Turbo Grid                                                 |
//+------------------------------------------------------------------+
void StartTurboGrid()
{
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    if(ask <= 0 || bid <= 0) return;

    // Analyze market for direction
    string trend = AnalyzeMarketTurbo();
    bool start_buy = (trend == "BUY" || trend == "NEUTRAL");

    grid_center = start_buy ? ask : bid;
    grid_direction = start_buy ? "BUY" : "SELL";
    grid_count = 0;

    // Calculate aggressive lot size
    double lot_size = CalculateTurboLotSize();

    bool success = false;
    if(start_buy)
    {
        success = trade.Buy(lot_size, _Symbol, 0, 0, 0, "Turbo-B0");
    }
    else
    {
        success = trade.Sell(lot_size, _Symbol, 0, 0, 0, "Turbo-S0");
    }

    if(success)
    {
        AddToTurboArray(grid_center, start_buy, lot_size, trade.ResultOrder());
        Print("TURBO GRID STARTED: ", grid_direction, " Lot=", lot_size, " Price=", grid_center);
        last_order_time = TimeCurrent();
        trades_this_hour++;
    }
}

//+------------------------------------------------------------------+
//| Add to Turbo Grid                                                |
//+------------------------------------------------------------------+
void AddToTurboGrid()
{
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double grid_distance = InpGridStep * SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    if(grid_direction == "BUY")
    {
        // Add BUY positions when price drops
        double target_price = grid_center - (CountActivePositions() * grid_distance);
        if(ask <= target_price)
        {
            double lot_size = CalculateTurboLotSize();
            if(trade.Buy(lot_size, _Symbol, 0, 0, 0, "Turbo-B" + IntegerToString(grid_count)))
            {
                AddToTurboArray(ask, true, lot_size, trade.ResultOrder());
                Print("TURBO BUY ADDED: Level=", grid_count, " Lot=", lot_size, " Price=", ask);
                last_order_time = TimeCurrent();
                trades_this_hour++;
            }
        }
    }
    else if(grid_direction == "SELL")
    {
        // Add SELL positions when price rises
        double target_price = grid_center + (CountActivePositions() * grid_distance);
        if(bid >= target_price)
        {
            double lot_size = CalculateTurboLotSize();
            if(trade.Sell(lot_size, _Symbol, 0, 0, 0, "Turbo-S" + IntegerToString(grid_count)))
            {
                AddToTurboArray(bid, false, lot_size, trade.ResultOrder());
                Print("TURBO SELL ADDED: Level=", grid_count, " Lot=", lot_size, " Price=", bid);
                last_order_time = TimeCurrent();
                trades_this_hour++;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate Turbo Lot Size for Aggressive Growth                  |
//+------------------------------------------------------------------+
double CalculateTurboLotSize()
{
    double base_lot = InpStartLot * current_lot_multiplier;

    // Apply turbo compounding
    if(InpTurboCompound)
    {
        double balance = AccountInfoDouble(ACCOUNT_BALANCE);
        double growth_factor = balance / weekly_start_balance;
        if(growth_factor > 1.0)
        {
            base_lot *= growth_factor;
        }
    }

    // Aggressive scaling based on performance
    double weekly_performance = GetWeeklyPerformance();
    if(weekly_performance < InpWeeklyTarget / 2) // If behind target
    {
        base_lot *= 2.0; // Double aggression
        turbo_mode_active = true;
    }

    // Limit maximum lot size
    double max_lot = InpStartLot * InpMaxLotMultiplier;
    base_lot = MathMin(base_lot, max_lot);

    // Ensure minimum requirements
    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    if(min_lot > 0)
    {
        base_lot = MathMax(base_lot, min_lot);
    }
    else
    {
        base_lot = MathMax(base_lot, 0.01);
    }

    return NormalizeDouble(base_lot, 2);
}

//+------------------------------------------------------------------+
//| Analyze Market for Turbo Trading                                |
//+------------------------------------------------------------------+
string AnalyzeMarketTurbo()
{
    // Simple but fast trend analysis
    double ma_fast[];
    double ma_slow[];

    int ma_fast_handle = iMA(_Symbol, PERIOD_CURRENT, 5, 0, MODE_EMA, PRICE_CLOSE);
    int ma_slow_handle = iMA(_Symbol, PERIOD_CURRENT, 20, 0, MODE_EMA, PRICE_CLOSE);

    if(CopyBuffer(ma_fast_handle, 0, 0, 1, ma_fast) < 1 ||
       CopyBuffer(ma_slow_handle, 0, 0, 1, ma_slow) < 1)
    {
        return "NEUTRAL";
    }

    double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    if(ma_fast[0] > ma_slow[0] && current_price > ma_fast[0])
    {
        return "BUY";
    }
    else if(ma_fast[0] < ma_slow[0] && current_price < ma_fast[0])
    {
        return "SELL";
    }

    return "NEUTRAL";
}

//+------------------------------------------------------------------+
//| Check Targets and Adjust Aggression                             |
//+------------------------------------------------------------------+
void CheckTargetsAndAdjust()
{
    double weekly_performance = GetWeeklyPerformance();
    double daily_performance = GetDailyPerformance();

    // Check if daily target is reached
    if(daily_performance >= InpDailyTarget)
    {
        Print("DAILY TARGET ACHIEVED: ", daily_performance, "% - EXCELLENT!");
        // Could pause here or continue for over-performance
    }

    // Check if weekly target is reached
    if(weekly_performance >= InpWeeklyTarget)
    {
        Print("WEEKLY TARGET ACHIEVED: ", weekly_performance, "% - OUTSTANDING!");
        // Could reduce aggression or continue for over-performance
    }

    // If behind target, increase aggression
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    int days_into_week = time_struct.day_of_week;

    double expected_progress = (InpWeeklyTarget / 5.0) * days_into_week;
    if(weekly_performance < expected_progress * 0.8) // 20% behind
    {
        turbo_mode_active = true;
        Print("BEHIND TARGET - ACTIVATING TURBO MODE");
    }
}

//+------------------------------------------------------------------+
//| Update Lot Multiplier for Compound Growth                       |
//+------------------------------------------------------------------+
void UpdateLotMultiplier()
{
    if(total_cycles_completed > 0)
    {
        current_lot_multiplier = MathPow(InpScalingFactor, total_cycles_completed / 10.0);
        current_lot_multiplier = MathMin(current_lot_multiplier, InpMaxLotMultiplier);

        Print("LOT MULTIPLIER UPDATED: ", current_lot_multiplier,
              " (Cycles: ", total_cycles_completed, ")");
    }
}

//+------------------------------------------------------------------+
//| Emergency Safety Check                                           |
//+------------------------------------------------------------------+
bool EmergencySafetyCheck()
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double total_loss = weekly_start_balance - balance;

    if(total_loss >= InpTurboStopLoss)
    {
        Print("EMERGENCY STOP: Loss $", total_loss, " exceeds limit $", InpTurboStopLoss);
        CloseAllPositions();
        return false;
    }

    // Check if we're in extreme drawdown
    double weekly_performance = GetWeeklyPerformance();
    if(weekly_performance < -50.0) // 50% weekly loss
    {
        Print("EXTREME DRAWDOWN DETECTED: ", weekly_performance, "%");
        CloseAllPositions();
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Utility Functions                                                |
//+------------------------------------------------------------------+
double GetWeeklyPerformance()
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    return ((balance - weekly_start_balance) / weekly_start_balance) * 100.0;
}

double GetDailyPerformance()
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    return ((balance - daily_start_balance) / daily_start_balance) * 100.0;
}

void AddToTurboArray(double price, bool is_buy, double lot_size, ulong ticket)
{
    turbo_grid[grid_count].price = price;
    turbo_grid[grid_count].is_buy = is_buy;
    turbo_grid[grid_count].ticket = ticket;
    turbo_grid[grid_count].lot_size = lot_size;
    turbo_grid[grid_count].time = TimeCurrent();
    turbo_grid[grid_count].is_active = true;
    grid_count++;
}

int CountActivePositions()
{
    int count = 0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
                count++;
        }
    }
    return count;
}

double GetTotalProfit()
{
    double total = 0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                total += position.Profit() + position.Swap() + position.Commission();
            }
        }
    }
    return total;
}

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

void ResetTurboGrid()
{
    grid_direction = "NONE";
    grid_center = 0;
    grid_count = 0;

    for(int i = 0; i < 100; i++)
    {
        turbo_grid[i].is_active = false;
        turbo_grid[i].ticket = 0;
    }
}

void CheckTimeResets()
{
    MqlDateTime current_time;
    TimeToStruct(TimeCurrent(), current_time);

    // Daily reset
    MqlDateTime day_time;
    TimeToStruct(day_start, day_time);
    if(current_time.day != day_time.day)
    {
        double daily_pnl = GetDailyPerformance();
        Print("DAILY PERFORMANCE: ", daily_pnl, "% (Target: ", InpDailyTarget, "%)");
        daily_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        day_start = TimeCurrent();
    }

    // Weekly reset
    MqlDateTime week_time;
    TimeToStruct(week_start, week_time);
    if(current_time.day_of_week == 1 && week_time.day_of_week != 1) // New week (Monday)
    {
        double weekly_pnl = GetWeeklyPerformance();
        Print("WEEKLY PERFORMANCE: ", weekly_pnl, "% (Target: ", InpWeeklyTarget, "%)");
        weekly_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        week_start = TimeCurrent();
        total_cycles_completed = 0;
        current_lot_multiplier = 1.0;
    }

    // Hourly reset for trade counting
    MqlDateTime hour_time;
    TimeToStruct(hour_start, hour_time);
    if(current_time.hour != hour_time.hour)
    {
        trades_this_hour = 0;
        hour_start = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== WEEKLY TURBO EA STOPPED ===");
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double weekly_performance = GetWeeklyPerformance();

    Print("Final Balance: $", balance);
    Print("Weekly Performance: ", weekly_performance, "%");
    Print("Target: ", InpWeeklyTarget, "% per week");
    Print("Cycles Completed: ", total_cycles_completed);
    Print("WARNING: EXTREME RISK STRATEGY");
}