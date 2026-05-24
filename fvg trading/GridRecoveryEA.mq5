//+------------------------------------------------------------------+
//|                                               GridRecoveryEA.mq5 |
//|                        Grid + Recovery System for High Profits  |
//|                    Advanced Reverse & Follow Strategy           |
//+------------------------------------------------------------------+
#property copyright "Grid Recovery EA"
#property version   "2.00"
#property description "Grid Recovery System - Never Give Up Until Profit!"

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
input group "=== Grid Recovery Settings ==="
input int InpMagicNumber = 99999;                    // Magic Number
input double InpBaseLotSize = 0.05;                  // Base Lot Size
input double InpRecoveryMultiplier = 1.8;            // Recovery Multiplier (เพิ่มขนาด lot เมื่อ recovery)
input int InpGridStep = 25;                          // Grid Step (points)
input int InpMaxGridLevels = 7;                      // Max Grid Levels ก่อน Recovery
input double InpRecoveryTrigger = -50.0;             // Recovery Trigger Loss ($)

input group "=== Profit & Recovery ==="
input double InpTargetProfit = 100.0;               // Target Profit ($) - เป้าหมายกำไรสูงขึ้น
input double InpMinRecoveryProfit = 20.0;            // Min Recovery Profit ($)
input int InpMaxRecoveryLevels = 5;                  // Max Recovery Attempts
input bool InpAggressiveRecovery = true;             // Aggressive Recovery Mode
input double InpPartialClosePercent = 60.0;          // Partial Close % when reversing

input group "=== Risk Management ==="
input double InpMaxTotalLoss = 500.0;               // Max Total Loss ($) - สูงขึ้นเพื่อให้ recovery ได้
input double InpDailyVolumeTarget = 500.0;           // Daily Volume Target (lots)
input int InpMaxDailyTrades = 2000;                 // Max Daily Trades
input bool InpForceRecovery = true;                  // Force Recovery Until Profit

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
// Grid Arrays
double grid_prices[50];
double grid_lots[50];
ulong grid_tickets[50];
string grid_directions[50]; // "BUY" or "SELL"
int grid_count = 0;

// Recovery System
string current_direction = "NONE";                   // Current grid direction
string recovery_direction = "NONE";                  // Recovery direction
bool recovery_mode = false;                          // Recovery mode active
int recovery_level = 0;                             // Current recovery level
double recovery_start_balance = 0.0;                // Balance when recovery started
double total_loss_to_recover = 0.0;                // Total loss that needs recovery
double break_even_target = 0.0;                     // Target to break even + profit

// Performance Tracking
double daily_volume = 0.0;                          // Daily lot volume
double daily_profit = 0.0;                          // Daily profit/loss
double session_high_profit = 0.0;                   // Session highest profit
double session_low_loss = 0.0;                      // Session lowest loss
int successful_recoveries = 0;                      // Count of successful recoveries
int failed_recoveries = 0;                          // Count of failed attempts
int daily_trade_count = 0;                          // Daily trade count

// Control Variables
bool system_active = true;                           // System active flag
datetime last_action_time = 0;                      // Last action timestamp
datetime last_display_update = 0;                   // Last display update
datetime daily_reset_time = 0;                      // Daily reset timestamp
double initial_balance = 0.0;                       // Starting balance

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== 🚀 GRID RECOVERY SYSTEM STARTED 🚀 ===");

    // Initialize trade settings
    trade.SetExpertMagicNumber(InpMagicNumber);
    trade.SetMarginMode();
    trade.SetTypeFillingBySymbol(_Symbol);

    // Symbol validation
    if(!symbolInfo.Name(_Symbol) || !SymbolSelect(_Symbol, true))
    {
        Print("❌ ERROR: Symbol initialization failed");
        return INIT_FAILED;
    }

    // Wait for price data
    int attempts = 0;
    while(!symbolInfo.RefreshRates() && attempts < 10)
    {
        Sleep(1000);
        attempts++;
    }

    if(attempts >= 10)
    {
        Print("❌ ERROR: Price data unavailable");
        return INIT_FAILED;
    }

    // Initialize system
    initial_balance = account.Balance();
    recovery_start_balance = initial_balance;
    daily_reset_time = TimeCurrent();

    // Clear existing positions
    CloseAllPositions();
    ResetSystem();

    Print("✅ SYSTEM INITIALIZED");
    Print("💰 Starting Balance: $", initial_balance);
    Print("🎯 Target Profit: $", InpTargetProfit);
    Print("🔄 Recovery Trigger: $", InpRecoveryTrigger);
    Print("📊 Daily Volume Target: ", InpDailyVolumeTarget, " lots");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    UpdateDisplay();
    Print("=== 🏁 GRID RECOVERY SYSTEM STOPPED 🏁 ===");
    Print("📊 Final Stats:");
    Print("💰 Total P&L: $", daily_profit);
    Print("📈 Daily Volume: ", daily_volume, " lots");
    Print("🏆 Successful Recoveries: ", successful_recoveries);
    Print("❌ Failed Attempts: ", failed_recoveries);
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    if(!system_active) return;

    // Update display every 10 seconds
    if(TimeCurrent() - last_display_update >= 10)
    {
        UpdateDisplay();
        last_display_update = TimeCurrent();
    }

    // Check daily reset
    CheckDailyReset();

    // Refresh price data
    symbolInfo.RefreshRates();
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    if(current_ask <= 0 || current_bid <= 0) return;

    // Get current total profit/loss
    double total_pnl = GetTotalPnL();
    UpdateSessionStats(total_pnl);

    // 🎯 CHECK FOR PROFIT TARGET REACHED
    if(total_pnl >= InpTargetProfit)
    {
        Print("🎉 TARGET PROFIT REACHED: $", total_pnl);
        CloseAllPositions();
        RecordSuccessfulRecovery(total_pnl);
        ResetSystem();
        return;
    }

    // 🔄 RECOVERY SYSTEM LOGIC
    if(!recovery_mode)
    {
        // Normal grid trading
        if(grid_count == 0)
        {
            StartNewGrid();
        }
        else
        {
            ManageGrid();

            // Check if need to trigger recovery
            if(total_pnl <= InpRecoveryTrigger && grid_count >= 3)
            {
                TriggerRecovery(total_pnl);
            }
        }
    }
    else
    {
        // Recovery mode active
        ManageRecovery();

        // Check recovery success
        if(total_pnl >= break_even_target)
        {
            Print("✅ RECOVERY SUCCESSFUL: $", total_pnl, " (Target: $", break_even_target, ")");
            CloseAllPositions();
            RecordSuccessfulRecovery(total_pnl);
            ResetSystem();
            return;
        }

        // Check if need another recovery level
        if(ShouldAddRecoveryLevel())
        {
            AddRecoveryLevel();
        }
    }

    // 🚨 EMERGENCY STOP
    if(total_pnl <= -InpMaxTotalLoss)
    {
        Print("🚨 EMERGENCY STOP: Loss $", total_pnl, " exceeds limit $", InpMaxTotalLoss);
        CloseAllPositions();
        failed_recoveries++;
        system_active = false;
        return;
    }
}

//+------------------------------------------------------------------+
//| Start New Grid                                                   |
//+------------------------------------------------------------------+
void StartNewGrid()
{
    if(TimeCurrent() - last_action_time < 5) return; // Cooldown

    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    // Determine direction (simple alternating for now)
    static bool last_was_buy = false;

    if(!last_was_buy)
    {
        current_direction = "BUY";
        OpenGridPosition("BUY", current_ask, InpBaseLotSize);
        last_was_buy = true;
    }
    else
    {
        current_direction = "SELL";
        OpenGridPosition("SELL", current_bid, InpBaseLotSize);
        last_was_buy = false;
    }

    Print("🔄 NEW GRID STARTED: ", current_direction, " at ", (current_direction == "BUY" ? current_ask : current_bid));
    last_action_time = TimeCurrent();
}

//+------------------------------------------------------------------+
//| Manage Grid Positions                                            |
//+------------------------------------------------------------------+
void ManageGrid()
{
    if(grid_count >= InpMaxGridLevels) return;
    if(TimeCurrent() - last_action_time < 3) return; // Cooldown

    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();
    double step_size = InpGridStep * symbolInfo.Point();

    // Get last grid price
    double last_price = grid_prices[grid_count - 1];

    if(current_direction == "BUY")
    {
        // Add BUY position when price goes down
        double next_level = last_price - step_size;
        if(current_ask <= next_level)
        {
            double lot_size = InpBaseLotSize * MathPow(1.3, grid_count);
            OpenGridPosition("BUY", current_ask, lot_size);
        }
    }
    else if(current_direction == "SELL")
    {
        // Add SELL position when price goes up
        double next_level = last_price + step_size;
        if(current_bid >= next_level)
        {
            double lot_size = InpBaseLotSize * MathPow(1.3, grid_count);
            OpenGridPosition("SELL", current_bid, lot_size);
        }
    }
}

//+------------------------------------------------------------------+
//| Trigger Recovery System                                          |
//+------------------------------------------------------------------+
void TriggerRecovery(double current_loss)
{
    Print("🔄 TRIGGERING RECOVERY SYSTEM");
    Print("💸 Current Loss: $", current_loss);

    // Partial close current positions
    double close_percent = InpPartialClosePercent / 100.0;
    PartialClosePositions(close_percent);

    // Calculate recovery requirements
    total_loss_to_recover = MathAbs(current_loss);
    break_even_target = InpMinRecoveryProfit; // Minimum profit target

    // Set recovery direction (opposite to current)
    if(current_direction == "BUY")
        recovery_direction = "SELL";
    else
        recovery_direction = "BUY";

    recovery_mode = true;
    recovery_level = 1;
    recovery_start_balance = account.Balance();

    Print("✅ RECOVERY MODE ACTIVATED");
    Print("🎯 Recovery Direction: ", recovery_direction);
    Print("💰 Target: $", break_even_target);

    // Start first recovery position
    AddRecoveryLevel();
}

//+------------------------------------------------------------------+
//| Add Recovery Level                                               |
//+------------------------------------------------------------------+
void AddRecoveryLevel()
{
    if(recovery_level > InpMaxRecoveryLevels)
    {
        Print("❌ MAX RECOVERY LEVELS REACHED");
        return;
    }

    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    // Calculate recovery lot size (progressive increase)
    double base_recovery_lot = InpBaseLotSize * 2.0; // Start with 2x base
    double recovery_lot = base_recovery_lot * MathPow(InpRecoveryMultiplier, recovery_level - 1);

    // Normalize lot size
    recovery_lot = NormalizeLotSize(recovery_lot);

    if(recovery_direction == "BUY")
    {
        OpenGridPosition("BUY", current_ask, recovery_lot);
        Print("🚀 RECOVERY BUY Level ", recovery_level, ": ", recovery_lot, " lots at ", current_ask);
    }
    else
    {
        OpenGridPosition("SELL", current_bid, recovery_lot);
        Print("🚀 RECOVERY SELL Level ", recovery_level, ": ", recovery_lot, " lots at ", current_bid);
    }

    recovery_level++;
    last_action_time = TimeCurrent();
}

//+------------------------------------------------------------------+
//| Manage Recovery Positions                                        |
//+------------------------------------------------------------------+
void ManageRecovery()
{
    // Check if market reversed again (need to switch recovery direction)
    double total_pnl = GetTotalPnL();

    // If recovery is failing badly, consider switching direction again
    if(total_pnl < (total_loss_to_recover * -1.5) && recovery_level >= 3)
    {
        Print("🔄 MARKET REVERSED AGAIN - SWITCHING RECOVERY DIRECTION");

        // Partial close current recovery positions
        PartialClosePositions(0.7); // Close 70%

        // Switch direction
        if(recovery_direction == "BUY")
            recovery_direction = "SELL";
        else
            recovery_direction = "BUY";

        // Reset recovery level but keep recovery mode
        recovery_level = 1;

        Print("🔄 NEW RECOVERY DIRECTION: ", recovery_direction);
        AddRecoveryLevel();
    }
}

//+------------------------------------------------------------------+
//| Check if should add recovery level                               |
//+------------------------------------------------------------------+
bool ShouldAddRecoveryLevel()
{
    if(recovery_level > InpMaxRecoveryLevels) return false;
    if(TimeCurrent() - last_action_time < 10) return false; // Cooldown

    double total_pnl = GetTotalPnL();

    // Add recovery level if still losing and conditions met
    if(total_pnl < break_even_target * -0.5) // If losing more than half target
    {
        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| Open Grid Position                                               |
//+------------------------------------------------------------------+
void OpenGridPosition(string direction, double price, double lot_size)
{
    if(grid_count >= 50) return; // Array limit

    lot_size = NormalizeLotSize(lot_size);
    if(lot_size <= 0) return;

    string comment = StringFormat("%s_%s_L%d",
                                  (recovery_mode ? "REC" : "GRID"),
                                  direction,
                                  (recovery_mode ? recovery_level : grid_count));

    bool success = false;
    ulong ticket = 0;

    if(direction == "BUY")
    {
        success = trade.Buy(lot_size, _Symbol, 0, 0, 0, comment);
    }
    else
    {
        success = trade.Sell(lot_size, _Symbol, 0, 0, 0, comment);
    }

    if(success)
    {
        ticket = trade.ResultOrder();

        // Record position
        grid_prices[grid_count] = price;
        grid_lots[grid_count] = lot_size;
        grid_tickets[grid_count] = ticket;
        grid_directions[grid_count] = direction;
        grid_count++;

        // Update statistics
        daily_volume += lot_size;
        daily_trade_count++;

        Print("✅ ", comment, " opened: ", lot_size, " lots at ", price, " (Ticket: ", ticket, ")");
    }
    else
    {
        Print("❌ Failed to open ", direction, " position: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Partial Close Positions                                          |
//+------------------------------------------------------------------+
void PartialClosePositions(double close_percent)
{
    int positions_to_close = (int)(grid_count * close_percent);
    int closed_count = 0;

    Print("🔄 PARTIAL CLOSE: Closing ", close_percent * 100, "% of positions (", positions_to_close, " positions)");

    for(int i = grid_count - 1; i >= 0 && closed_count < positions_to_close; i--)
    {
        if(grid_tickets[i] > 0)
        {
            if(trade.PositionClose(grid_tickets[i]))
            {
                Print("📤 Closed position: Ticket ", grid_tickets[i]);
                grid_tickets[i] = 0; // Mark as closed
                closed_count++;
            }
        }
    }

    // Clean up closed positions from array
    CompactGridArray();
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
//| Reset System                                                      |
//+------------------------------------------------------------------+
void ResetSystem()
{
    // Reset grid
    ArrayInitialize(grid_prices, 0.0);
    ArrayInitialize(grid_lots, 0.0);
    ArrayInitialize(grid_tickets, 0);
    for(int i = 0; i < 50; i++)
        grid_directions[i] = "";
    grid_count = 0;

    // Reset recovery
    current_direction = "NONE";
    recovery_direction = "NONE";
    recovery_mode = false;
    recovery_level = 0;
    total_loss_to_recover = 0.0;
    break_even_target = 0.0;

    Print("🔄 SYSTEM RESET - Ready for new cycle");
}

//+------------------------------------------------------------------+
//| Record Successful Recovery                                        |
//+------------------------------------------------------------------+
void RecordSuccessfulRecovery(double profit)
{
    successful_recoveries++;
    daily_profit += profit;

    Print("🎉 RECOVERY SUCCESS #", successful_recoveries);
    Print("💰 Profit: $", profit);
    Print("📊 Daily Total: $", daily_profit);
}

//+------------------------------------------------------------------+
//| Update Display                                                    |
//+------------------------------------------------------------------+
void UpdateDisplay()
{
    double current_pnl = GetTotalPnL();
    double balance = account.Balance();
    double equity = account.Equity();

    string status = "NORMAL";
    if(recovery_mode) status = StringFormat("RECOVERY L%d", recovery_level);

    string chart_comment = StringFormat(
        "🚀 GRID RECOVERY SYSTEM 🚀\n" +
        "💰 Balance: $%.2f | Equity: $%.2f\n" +
        "📈 Current P&L: $%.2f\n" +
        "🎯 Target Profit: $%.2f\n" +
        "📊 Daily Volume: %.2f / %.0f lots\n" +
        "🏆 Successful Recoveries: %d\n" +
        "❌ Failed Attempts: %d\n" +
        "🔄 Status: %s | Direction: %s\n" +
        "📍 Grid Levels: %d | Daily Trades: %d\n" +
        "📈 Session High: $%.2f | Low: $%.2f",
        balance, equity, current_pnl, InpTargetProfit,
        daily_volume, InpDailyVolumeTarget,
        successful_recoveries, failed_recoveries,
        status, (recovery_mode ? recovery_direction : current_direction),
        grid_count, daily_trade_count,
        session_high_profit, session_low_loss
    );

    Comment(chart_comment);
}

//+------------------------------------------------------------------+
//| Update Session Statistics                                         |
//+------------------------------------------------------------------+
void UpdateSessionStats(double current_pnl)
{
    if(current_pnl > session_high_profit)
        session_high_profit = current_pnl;

    if(current_pnl < session_low_loss)
        session_low_loss = current_pnl;
}

//+------------------------------------------------------------------+
//| Check Daily Reset                                                 |
//+------------------------------------------------------------------+
void CheckDailyReset()
{
    MqlDateTime current_time, reset_time;
    TimeToStruct(TimeCurrent(), current_time);
    TimeToStruct(daily_reset_time, reset_time);

    if(current_time.day != reset_time.day)
    {
        // New day - reset daily statistics
        daily_volume = 0.0;
        daily_profit = 0.0;
        daily_trade_count = 0;
        session_high_profit = 0.0;
        session_low_loss = 0.0;
        daily_reset_time = TimeCurrent();

        Print("📅 NEW DAY - Statistics reset");
    }
}

//+------------------------------------------------------------------+
//| Compact Grid Array                                               |
//+------------------------------------------------------------------+
void CompactGridArray()
{
    int write_index = 0;

    for(int read_index = 0; read_index < grid_count; read_index++)
    {
        if(grid_tickets[read_index] > 0) // Position still open
        {
            if(write_index != read_index)
            {
                grid_prices[write_index] = grid_prices[read_index];
                grid_lots[write_index] = grid_lots[read_index];
                grid_tickets[write_index] = grid_tickets[read_index];
                grid_directions[write_index] = grid_directions[read_index];
            }
            write_index++;
        }
    }

    grid_count = write_index;
}

//+------------------------------------------------------------------+
//| Normalize Lot Size                                               |
//+------------------------------------------------------------------+
double NormalizeLotSize(double lot_size)
{
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    double lot_step = symbolInfo.LotsStep();

    if(lot_size < min_lot) lot_size = min_lot;
    if(lot_size > max_lot) lot_size = max_lot;

    lot_size = MathRound(lot_size / lot_step) * lot_step;
    return lot_size;
}