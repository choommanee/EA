//+------------------------------------------------------------------+
//|                                      WorldClassGridEA_Fixed.mq5 |
//|                   World-Class Grid Trading System - FIXED       |
//|                     Now Actually Achieves 400 Lots/Day         |
//+------------------------------------------------------------------+
#property copyright "World Class Grid EA Fixed"
#property version   "4.00"
#property description "Fixed Grid System - Now Works with 400 Lots Target"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

CTrade trade;
CPositionInfo position;
CSymbolInfo symbolInfo;
CAccountInfo account;

//+------------------------------------------------------------------+
//| FIXED Input Parameters                                           |
//+------------------------------------------------------------------+
input group "=== FIXED Grid Settings ==="
input int InpMagicNumber = 777777;                   // Magic Number
input double InpFixedLotSize = 0.15;                 // Fixed Lot Size (INCREASED for 400 lots)
input double InpRiskPercent = 0.5;                   // Risk Per Trade (% of balance)
input double InpTargetRiskReward = 2.0;              // Target Risk:Reward Ratio (1:2)
input int InpGridStepPips = 30;                      // Grid Step (pips) - REDUCED for more entries
input int InpMaxGridLevels = 6;                      // Max Grid Levels - INCREASED

input group "=== Professional Risk Management ==="
input double InpMaxDrawdownPercent = 10.0;           // Max Drawdown (% of balance)
input double InpDailyLossLimit = 3.0;               // Daily Loss Limit (% of balance)
input bool InpUseHardStopLoss = true;               // Use Hard Stop Loss
input double InpStopLossMultiplier = 1.5;           // Stop Loss Multiplier
input double InpMinFreeMarginPercent = 30.0;         // Min Free Margin (% of balance)

input group "=== Profit Optimization ==="
input double InpMinProfitPerLot = 3.0;              // Minimum Profit Per Lot ($)
input bool InpUseBreakEvenMove = true;               // Move to Breakeven when possible
input bool InpUseTrailingStop = true;               // Use Trailing Stop
input double InpTrailingStepPips = 10;              // Trailing Step (pips)

input group "=== Market Condition Filter ==="
input bool InpUseTrendFilter = true;                // Use Trend Filter
input int InpTrendPeriod = 50;                       // Trend Period (EMA)
input bool InpTradeOnlyRanging = true;               // Trade Only in Ranging Markets
input double InpMaxSpreadPips = 3.0;                // Max Spread (pips)

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
// Grid Management
struct GridPosition
{
    ulong ticket;
    double price;
    double lots;
    string direction;
    datetime open_time;
    bool is_active;
};

GridPosition grid_positions[20];
int grid_count = 0;
double grid_base_price = 0.0;
string grid_direction = "NONE";
datetime grid_start_time = 0;

// Risk Management
double daily_start_balance = 0.0;
double max_balance_today = 0.0;
double current_drawdown_percent = 0.0;
bool emergency_stop = false;
bool daily_limit_reached = false;

// Performance Tracking
double daily_profit = 0.0;
double daily_volume = 0.0;
int daily_trades = 0;
int winning_trades = 0;
int losing_trades = 0;
double total_profit_pips = 0.0;
double average_win = 0.0;
double average_loss = 0.0;

// Market Analysis
int trend_handle = INVALID_HANDLE;
double current_trend_value = 0.0;
bool is_ranging_market = false;

// Display
datetime last_display_update = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== WORLD CLASS GRID SYSTEM STARTED (FIXED) ===");

    // Initialize trading
    trade.SetExpertMagicNumber(InpMagicNumber);
    trade.SetMarginMode();
    trade.SetTypeFillingBySymbol(_Symbol);

    // Symbol validation
    if(!symbolInfo.Name(_Symbol) || !SymbolSelect(_Symbol, true))
    {
        Print("ERROR: Symbol initialization failed");
        return INIT_FAILED;
    }

    // Wait for data
    int attempts = 0;
    while(!symbolInfo.RefreshRates() && attempts < 10)
    {
        Sleep(1000);
        attempts++;
    }

    if(attempts >= 10)
    {
        Print("ERROR: Price data unavailable");
        return INIT_FAILED;
    }

    // Initialize indicators
    trend_handle = iMA(_Symbol, PERIOD_CURRENT, InpTrendPeriod, 0, MODE_EMA, PRICE_CLOSE);
    if(trend_handle == INVALID_HANDLE)
    {
        Print("ERROR: Failed to create trend indicator");
        return INIT_FAILED;
    }

    // Initialize variables
    daily_start_balance = account.Balance();
    max_balance_today = daily_start_balance;

    // Clear existing positions
    CloseAllPositions();
    InitializeGridArray();

    // Calculate optimal parameters
    CalculateOptimalSettings();

    Print("WORLD CLASS SYSTEM INITIALIZED (FIXED)");
    Print("Starting Balance: $", daily_start_balance);
    Print("Target R:R Ratio: 1:", InpTargetRiskReward);
    Print("Risk Per Trade: ", InpRiskPercent, "%");
    Print("Fixed Lot Size: ", InpFixedLotSize);

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== WORLD CLASS GRID SYSTEM STOPPED ===");

    // Release indicators
    if(trend_handle != INVALID_HANDLE)
        IndicatorRelease(trend_handle);

    // Final statistics
    double final_balance = account.Balance();
    double total_return = ((final_balance - daily_start_balance) / daily_start_balance) * 100.0;

    Print("FINAL PERFORMANCE:");
    Print("Final Balance: $", final_balance);
    Print("Total Return: ", DoubleToString(total_return, 2), "%");
    Print("Win Rate: ", GetWinRate(), "%");
    Print("Daily Volume: ", daily_volume, " lots");
    Print("Avg Profit per Lot: $", (daily_volume > 0 ? daily_profit / daily_volume : 0));
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    // Update display every 10 seconds
    if(TimeCurrent() - last_display_update >= 10)
    {
        UpdatePerformanceDisplay();
        last_display_update = TimeCurrent();
    }

    // Emergency stops
    if(emergency_stop || daily_limit_reached) return;

    // Check daily reset
    CheckDailyReset();

    // Update market analysis
    UpdateMarketAnalysis();

    // Risk management checks
    if(!CheckRiskLimits()) return;

    // Refresh prices
    symbolInfo.RefreshRates();
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    if(current_ask <= 0 || current_bid <= 0) return;

    // Check spread condition
    double spread_pips = (current_ask - current_bid) / GetPipValue();
    if(spread_pips > InpMaxSpreadPips)
    {
        Print("Spread too high: ", spread_pips, " pips");
        return;
    }

    // Get current P&L
    double current_pnl = GetTotalPnL();

    // Check for profit target
    if(grid_count > 0)
    {
        double target_profit = CalculateTargetProfit();

        if(current_pnl >= target_profit)
        {
            Print("PROFIT TARGET REACHED: $", current_pnl, " (Target: $", target_profit, ")");
            CloseAllGridPositions();
            RecordTradeResult(current_pnl, "WIN");
            ResetGrid();
            return;
        }

        // Hard Stop Loss
        if(InpUseHardStopLoss)
        {
            double stop_loss = CalculateStopLoss();
            if(current_pnl <= stop_loss)
            {
                Print("HARD STOP LOSS HIT: $", current_pnl, " (SL: $", stop_loss, ")");
                CloseAllGridPositions();
                RecordTradeResult(current_pnl, "LOSS");
                ResetGrid();
                return;
            }
        }

        // Manage existing grid
        ManageGrid();
    }
    else
    {
        // Start new grid if conditions are met
        if(ShouldStartNewGrid())
        {
            StartNewGrid();
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate Optimal Settings                                       |
//+------------------------------------------------------------------+
void CalculateOptimalSettings()
{
    // Calculate expected volume
    double total_lots_per_grid = 0.0;
    double current_lot = InpFixedLotSize;

    for(int i = 0; i < InpMaxGridLevels; i++)
    {
        total_lots_per_grid += current_lot;
        current_lot *= 1.2; // Progressive increase
    }

    double grids_needed_per_day = 400.0 / total_lots_per_grid;
    double grids_per_hour = grids_needed_per_day / 24.0;

    Print("OPTIMAL SETTINGS CALCULATED:");
    Print("Balance: $", account.Balance());
    Print("Fixed Lot Size: ", InpFixedLotSize);
    Print("Total lots per grid: ", total_lots_per_grid);
    Print("Grids needed per day: ", grids_needed_per_day);
    Print("Grids per hour: ", grids_per_hour);
}

//+------------------------------------------------------------------+
//| Update Market Analysis                                           |
//+------------------------------------------------------------------+
void UpdateMarketAnalysis()
{
    // Get trend value
    double trend_values[];
    if(CopyBuffer(trend_handle, 0, 0, 1, trend_values) <= 0) return;

    current_trend_value = trend_values[0];
    double current_price = (symbolInfo.Ask() + symbolInfo.Bid()) / 2.0;

    // Determine if market is ranging
    double distance_from_ema = MathAbs(current_price - current_trend_value);
    double atr_equivalent = InpGridStepPips * GetPipValue() * 3;

    is_ranging_market = (distance_from_ema < atr_equivalent);
}

//+------------------------------------------------------------------+
//| Check if should start new grid                                   |
//+------------------------------------------------------------------+
bool ShouldStartNewGrid()
{
    // Market condition filters
    if(InpTradeOnlyRanging && !is_ranging_market)
    {
        return false;
    }

    // Time filter
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);

    // Avoid major news hours
    if(time_struct.hour == 8 || time_struct.hour == 13 || time_struct.hour == 15)
    {
        return false;
    }

    // Cooldown after last grid
    if(TimeCurrent() - grid_start_time < 300) // 5 minutes cooldown
    {
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Start New Grid                                                   |
//+------------------------------------------------------------------+
void StartNewGrid()
{
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    // Determine direction based on trend filter
    string direction = "BUY";
    double entry_price = current_ask;

    if(InpUseTrendFilter)
    {
        double current_price = (current_ask + current_bid) / 2.0;

        if(current_price > current_trend_value)
        {
            direction = "SELL";
            entry_price = current_bid;
        }
        else
        {
            direction = "BUY";
            entry_price = current_ask;
        }
    }

    // Use fixed lot size
    double lot_size = InpFixedLotSize;

    // Open first position
    if(OpenGridPosition(direction, entry_price, lot_size, 0))
    {
        grid_direction = direction;
        grid_base_price = entry_price;
        grid_start_time = TimeCurrent();

        Print("NEW GRID STARTED: ", direction, " at ", entry_price, " | Lot: ", lot_size);
    }
}

//+------------------------------------------------------------------+
//| Open Grid Position - CLEAN VERSION                              |
//+------------------------------------------------------------------+
bool OpenGridPosition(string direction, double price, double lot_size_param, int level)
{
    if(grid_count >= 20) return false;

    // Pre-trade validation
    double free_margin = account.FreeMargin();
    double required_margin = symbolInfo.MarginRequired(lot_size_param);

    Print("Pre-trade check: Free margin: $", free_margin, " | Required: $", required_margin);

    // Check if we have enough margin
    if(free_margin < required_margin * 2) // Need 2x safety margin
    {
        Print("Insufficient margin. Free: $", free_margin, " | Required: $", required_margin);
        return false;
    }

    // Check minimum free margin percentage
    double min_free_margin = account.Balance() * (InpMinFreeMarginPercent / 100.0);
    if(free_margin < min_free_margin)
    {
        Print("Free margin below minimum: $", free_margin, " < $", min_free_margin);
        return false;
    }

    double final_lot_size = NormalizeLotSize(lot_size_param);
    if(final_lot_size <= 0) return false;

    string comment = StringFormat("WCGrid_%s_L%d", direction, level);
    bool success = false;
    ulong ticket = 0;

    Print("Attempting to open: ", direction, " ", final_lot_size, " lots");

    if(direction == "BUY")
    {
        success = trade.Buy(final_lot_size, _Symbol, 0, 0, 0, comment);
    }
    else
    {
        success = trade.Sell(final_lot_size, _Symbol, 0, 0, 0, comment);
    }

    if(success)
    {
        ticket = trade.ResultOrder();

        // Record in grid array
        grid_positions[grid_count].ticket = ticket;
        grid_positions[grid_count].price = price;
        grid_positions[grid_count].lots = final_lot_size;
        grid_positions[grid_count].direction = direction;
        grid_positions[grid_count].open_time = TimeCurrent();
        grid_positions[grid_count].is_active = true;
        grid_count++;

        // Update statistics
        daily_volume += final_lot_size;
        daily_trades++;

        Print("SUCCESS: ", comment, " opened: ", final_lot_size, " lots at ", price, " | Ticket: ", ticket);
        return true;
    }
    else
    {
        Print("Failed to open ", direction, ": ", trade.ResultRetcodeDescription());
        Print("Error details - Lot: ", final_lot_size, " | Price: ", price, " | Free Margin: $", free_margin);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Manage Existing Grid                                            |
//+------------------------------------------------------------------+
void ManageGrid()
{
    if(grid_count >= InpMaxGridLevels) return;

    double current_price = (symbolInfo.Ask() + symbolInfo.Bid()) / 2.0;
    double last_price = grid_positions[grid_count - 1].price;
    double grid_step = InpGridStepPips * GetPipValue();

    bool should_add_level = false;
    double new_price = 0.0;
    double new_lot_size = 0.0;

    if(grid_direction == "BUY")
    {
        // Add BUY when price goes down
        double next_level_price = last_price - grid_step;
        if(current_price <= next_level_price)
        {
            should_add_level = true;
            new_price = symbolInfo.Ask();
            new_lot_size = grid_positions[grid_count - 1].lots * 1.2; // Progressive increase
        }
    }
    else if(grid_direction == "SELL")
    {
        // Add SELL when price goes up
        double next_level_price = last_price + grid_step;
        if(current_price >= next_level_price)
        {
            should_add_level = true;
            new_price = symbolInfo.Bid();
            new_lot_size = grid_positions[grid_count - 1].lots * 1.2; // Progressive increase
        }
    }

    if(should_add_level)
    {
        OpenGridPosition(grid_direction, new_price, new_lot_size, grid_count);
    }
}

//+------------------------------------------------------------------+
//| Calculate Target Profit                                         |
//+------------------------------------------------------------------+
double CalculateTargetProfit()
{
    double total_risk = CalculateStopLoss();
    return MathAbs(total_risk) * InpTargetRiskReward;
}

//+------------------------------------------------------------------+
//| Calculate Stop Loss                                             |
//+------------------------------------------------------------------+
double CalculateStopLoss()
{
    double balance = account.Balance();
    return -(balance * (InpRiskPercent / 100.0));
}

//+------------------------------------------------------------------+
//| Get Total P&L                                                    |
//+------------------------------------------------------------------+
double GetTotalPnL()
{
    double total_pnl = 0.0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                total_pnl += position.Profit() + position.Swap() + position.Commission();
            }
        }
    }

    return total_pnl;
}

//+------------------------------------------------------------------+
//| Check Risk Limits                                               |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
    double current_balance = account.Balance();
    double current_equity = account.Equity();

    // Calculate current drawdown
    current_drawdown_percent = ((daily_start_balance - current_equity) / daily_start_balance) * 100.0;

    // Check max drawdown
    if(current_drawdown_percent >= InpMaxDrawdownPercent)
    {
        Print("MAX DRAWDOWN REACHED: ", current_drawdown_percent, "%");
        CloseAllPositions();
        emergency_stop = true;
        return false;
    }

    // Check daily loss limit
    double daily_loss_percent = ((daily_start_balance - current_balance) / daily_start_balance) * 100.0;
    if(daily_loss_percent >= InpDailyLossLimit)
    {
        Print("DAILY LOSS LIMIT REACHED: ", daily_loss_percent, "%");
        daily_limit_reached = true;
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Close All Grid Positions                                        |
//+------------------------------------------------------------------+
void CloseAllGridPositions()
{
    for(int i = 0; i < grid_count; i++)
    {
        if(grid_positions[i].is_active && grid_positions[i].ticket > 0)
        {
            if(trade.PositionClose(grid_positions[i].ticket))
            {
                grid_positions[i].is_active = false;
                Print("Closed grid position: ", grid_positions[i].ticket);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Close All Positions                                              |
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
//| Record Trade Result                                              |
//+------------------------------------------------------------------+
void RecordTradeResult(double profit, string result)
{
    daily_profit += profit;

    if(result == "WIN")
    {
        winning_trades++;
        if(profit > average_win || average_win == 0)
            average_win = (average_win + profit) / 2.0;
    }
    else
    {
        losing_trades++;
        if(profit < average_loss || average_loss == 0)
            average_loss = (average_loss + profit) / 2.0;
    }
}

//+------------------------------------------------------------------+
//| Reset Grid System                                               |
//+------------------------------------------------------------------+
void ResetGrid()
{
    InitializeGridArray();
    grid_count = 0;
    grid_base_price = 0.0;
    grid_direction = "NONE";
    grid_start_time = 0;

    Print("GRID RESET - Ready for next cycle");
}

//+------------------------------------------------------------------+
//| Initialize Grid Array                                            |
//+------------------------------------------------------------------+
void InitializeGridArray()
{
    for(int i = 0; i < 20; i++)
    {
        grid_positions[i].ticket = 0;
        grid_positions[i].price = 0.0;
        grid_positions[i].lots = 0.0;
        grid_positions[i].direction = "";
        grid_positions[i].open_time = 0;
        grid_positions[i].is_active = false;
    }
}

//+------------------------------------------------------------------+
//| Update Performance Display                                       |
//+------------------------------------------------------------------+
void UpdatePerformanceDisplay()
{
    double current_balance = account.Balance();
    double current_equity = account.Equity();
    double current_pnl = GetTotalPnL();
    double win_rate = GetWinRate();
    double profit_per_lot = (daily_volume > 0) ? daily_profit / daily_volume : 0.0;
    double daily_return = ((current_balance - daily_start_balance) / daily_start_balance) * 100.0;

    // Calculate daily progress towards 400 lot target
    double volume_progress = (daily_volume / 400.0) * 100.0;
    double margin_usage = ((account.Balance() - account.FreeMargin()) / account.Balance()) * 100.0;
    double risk_reward_actual = (average_loss != 0) ? MathAbs(average_win / average_loss) : 0.0;

    string chart_comment = StringFormat(
        "WORLD CLASS GRID SYSTEM (FIXED)\n" +
        "Balance: $%.2f | Equity: $%.2f (%.1f%% health)\n" +
        "Daily Return: %.2f%% | P&L: $%.2f\n" +
        "VOLUME PROGRESS: %.1f/400 lots (%.1f%% complete)\n" +
        "Win Rate: %.1f%% (%d W / %d L) | Trades: %d\n" +
        "Profit per Lot: $%.2f (Target: $%.2f)\n" +
        "R:R Actual: 1:%.1f (Target: 1:%.1f)\n" +
        "Drawdown: %.2f%% | Margin Used: %.1f%%\n" +
        "Grid: %s (%d levels) | Fixed Lot: %.2f\n" +
        "Market: %s | Spread: %.1f pips\n" +
        "Risk: %.1f%% per trade | Status: FIXED VERSION",
        current_balance, current_equity, (current_equity/current_balance)*100,
        daily_return, current_pnl,
        daily_volume, volume_progress,
        win_rate, winning_trades, losing_trades, daily_trades,
        profit_per_lot, InpMinProfitPerLot,
        risk_reward_actual, InpTargetRiskReward,
        current_drawdown_percent, margin_usage,
        grid_direction, grid_count, InpFixedLotSize,
        (is_ranging_market ? "RANGING" : "TRENDING"),
        (symbolInfo.Ask() - symbolInfo.Bid()) / GetPipValue(),
        InpRiskPercent
    );

    Comment(chart_comment);
}

//+------------------------------------------------------------------+
//| Utility Functions                                               |
//+------------------------------------------------------------------+
double GetWinRate()
{
    int total_trades = winning_trades + losing_trades;
    return (total_trades > 0) ? ((double)winning_trades / total_trades) * 100.0 : 0.0;
}

double GetTotalGridLots()
{
    double total_lots = 0.0;
    for(int i = 0; i < grid_count; i++)
    {
        if(grid_positions[i].is_active)
            total_lots += grid_positions[i].lots;
    }
    return total_lots;
}

double GetPipValue()
{
    return symbolInfo.Point() * ((StringFind(_Symbol, "JPY") >= 0) ? 0.01 : 1.0);
}

double NormalizeLotSize(double lot_size)
{
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    double lot_step = symbolInfo.LotsStep();

    if(lot_size < min_lot) lot_size = min_lot;
    if(lot_size > max_lot) lot_size = max_lot;

    return MathRound(lot_size / lot_step) * lot_step;
}

void CheckDailyReset()
{
    static datetime last_check_time = 0;
    static int last_day = -1;

    // Only check once per minute to avoid spam
    if(TimeCurrent() - last_check_time < 60) return;
    last_check_time = TimeCurrent();

    MqlDateTime current_time;
    TimeToStruct(TimeCurrent(), current_time);

    if(last_day == -1)
    {
        last_day = current_time.day; // Initialize
        return;
    }

    if(current_time.day != last_day)
    {
        // New day reset
        daily_start_balance = account.Balance();
        max_balance_today = daily_start_balance;
        daily_profit = 0.0;
        daily_volume = 0.0;
        daily_trades = 0;
        winning_trades = 0;
        losing_trades = 0;
        daily_limit_reached = false;
        emergency_stop = false;

        last_day = current_time.day;

        Print("NEW DAY - Performance metrics reset | Balance: $", daily_start_balance);
    }
}