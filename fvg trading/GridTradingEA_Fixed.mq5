//+------------------------------------------------------------------+
//|                                         GridTradingEA_Fixed.mq5 |
//|                                    Pure Grid Trading System     |
//|                              Optimized for High Volume Trading  |
//+------------------------------------------------------------------+
#property copyright "Grid Trading EA - Fixed"
#property link      ""
#property version   "1.01"
#property description "High Volume Grid Trading System - 400-1000 lots/day"

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
input double InpBaseLotSize = 0.05;                  // Base Lot Size
input double InpLotMultiplier = 2.0;                 // Lot Multiplier
input int InpGridStep = 50;                          // Grid Step (points)
input int InpMaxLevels = 8;                          // Maximum Grid Levels
input double InpProfitTargetPercent = 0.3;           // Profit Target (%)
input bool InpForceProfitClose = true;               // Force Close at Target
input int InpMaxHoldingMinutes = 15;                 // Max Holding Time (minutes)

input group "=== Risk Management ==="
input double InpMaxDrawdown = 500.0;                 // Maximum Drawdown ($)
input double InpMaxDailyLoss = 250.0;               // Maximum Daily Loss ($)
input double InpQuickProfitPercent = 0.1;            // Quick Profit %
input int InpMaxTradesPerDay = 1000;                // Maximum Trades Per Day
input double InpMinLotProfit = 0.05;                // Minimum Profit Per Lot

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
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
string grid_direction = "NONE";

// Risk Management Variables
double daily_start_balance = 0.0;
datetime last_daily_reset = 0;
bool daily_limit_reached = false;
int daily_trade_count = 0;
double daily_profit = 0.0;
double max_daily_profit = 0.0;
bool emergency_stop = false;
double total_lot_volume = 0.0;
datetime last_force_close = 0;
datetime grid_start_time = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== Grid Trading EA Fixed Started ===");

    trade.SetExpertMagicNumber(InpMagicNumber);
    trade.SetMarginMode();
    trade.SetTypeFillingBySymbol(_Symbol);

    if(!symbolInfo.Name(_Symbol))
    {
        Print("ERROR: Failed to set symbol name");
        return INIT_FAILED;
    }

    if(!SymbolSelect(_Symbol, true))
    {
        Print("ERROR: Failed to select symbol in Market Watch");
        return INIT_FAILED;
    }

    int attempts = 0;
    while(!symbolInfo.RefreshRates() && attempts < 10)
    {
        Sleep(1000);
        attempts++;
        Print("Waiting for symbol data... attempt ", attempts);
    }

    if(attempts >= 10)
    {
        Print("ERROR: Symbol data not available");
        return INIT_FAILED;
    }

    initial_balance = account.Balance();
    daily_start_balance = account.Balance();
    last_daily_reset = TimeCurrent();

    // Validate lot size
    double min_lot = symbolInfo.LotsMin();
    if(InpBaseLotSize < min_lot)
    {
        Print("ERROR: Base lot size too small");
        return INIT_PARAMETERS_INCORRECT;
    }

    CloseAllPositions();
    ResetGrid();

    Print("✅ EA Initialized Successfully");
    Print("Symbol: ", _Symbol);
    Print("Balance: $", initial_balance);
    Print("Max Trades: ", InpMaxTradesPerDay);

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== Grid Trading EA Stopped ===");
    Print("Final Stats - Trades: ", daily_trade_count, " | P&L: $", daily_profit);
    CloseAllPositions();
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_log_time = 0;

    symbolInfo.RefreshRates();
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    // Debug logging every 10 seconds
    if(TimeCurrent() - last_log_time > 10)
    {
        Print("📊 Ask=", current_ask, " | Trades: ", daily_trade_count, "/", InpMaxTradesPerDay, " | P&L: $", daily_profit);
        last_log_time = TimeCurrent();
    }

    if(current_ask <= 0 || current_bid <= 0)
    {
        Print("ERROR: Invalid prices");
        return;
    }

    UpdatePositions();
    CheckProfitTarget();

    if(!CheckDailyRiskLimits() || emergency_stop)
    {
        return;
    }

    // Start new grid
    if(!grid_active)
    {
        bool can_trade = (daily_trade_count < InpMaxTradesPerDay);
        int cooldown_period = GetDynamicCooldown();
        bool cooldown_ok = (TimeCurrent() - last_order_time >= cooldown_period);

        if(can_trade && cooldown_ok)
        {
            bool instant_restart = false;

            // Instant restart conditions
            if(TimeCurrent() - last_force_close < 30) instant_restart = true;
            if(daily_profit > 100.0 && daily_trade_count < 200) instant_restart = true;

            // Peak hours check
            MqlDateTime time_struct;
            TimeToStruct(TimeCurrent(), time_struct);
            int hour = time_struct.hour;
            if((hour >= 8 && hour <= 16) && daily_trade_count < 50) instant_restart = true;

            if(instant_restart || (TimeCurrent() - last_order_time >= cooldown_period))
            {
                Print("🚀 STARTING GRID #", daily_trade_count + 1, " | P&L: $", daily_profit);
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
//| Start new grid                                                   |
//+------------------------------------------------------------------+
void StartNewGrid()
{
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    if(current_ask <= 0 || current_bid <= 0)
    {
        Print("ERROR: Invalid prices in StartNewGrid");
        return;
    }

    // Simple alternating strategy
    static bool last_was_buy = false;
    double initial_lot = CalculateDynamicLotSize(InpBaseLotSize, 0);

    if(!last_was_buy)
    {
        grid_direction = "BUY";
        grid_start_price = current_ask;
        grid_start_time = TimeCurrent();
        total_lot_volume = initial_lot;
        OpenBuyOrder(current_ask, initial_lot, 0);
        Print("🟢 BUY Grid at ", current_ask, " | Lot: ", initial_lot);
        last_was_buy = true;
    }
    else
    {
        grid_direction = "SELL";
        grid_start_price = current_bid;
        grid_start_time = TimeCurrent();
        total_lot_volume = initial_lot;
        OpenSellOrder(current_bid, initial_lot, 0);
        Print("🔴 SELL Grid at ", current_bid, " | Lot: ", initial_lot);
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
    double step_size = InpGridStep * symbolInfo.Point();

    if(buy_count < InpMaxLevels)
    {
        double next_buy_level = grid_start_price - (buy_count * step_size);

        if(current_ask <= next_buy_level &&
           TimeCurrent() - last_order_time > GetDynamicCooldown() &&
           current_ask > 0 && CanOpenNewPosition())
        {
            double lot_size = CalculateDynamicLotSize(InpBaseLotSize * MathPow(InpLotMultiplier, buy_count), buy_count);
            OpenBuyOrder(current_ask, lot_size, buy_count);
        }
    }
}

//+------------------------------------------------------------------+
//| Manage SELL grid                                                 |
//+------------------------------------------------------------------+
void ManageSellGrid()
{
    double current_bid = symbolInfo.Bid();
    double step_size = InpGridStep * symbolInfo.Point();

    if(sell_count < InpMaxLevels)
    {
        double next_sell_level = grid_start_price + (sell_count * step_size);

        if(current_bid >= next_sell_level &&
           TimeCurrent() - last_order_time > GetDynamicCooldown() &&
           current_bid > 0 && CanOpenNewPosition())
        {
            double lot_size = CalculateDynamicLotSize(InpBaseLotSize * MathPow(InpLotMultiplier, sell_count), sell_count);
            OpenSellOrder(current_bid, lot_size, sell_count);
        }
    }
}

//+------------------------------------------------------------------+
//| Open BUY order                                                   |
//+------------------------------------------------------------------+
void OpenBuyOrder(double price, double lot_size, int level)
{
    lot_size = NormalizeLotSize(lot_size);
    if(lot_size <= 0) return;

    double current_ask = symbolInfo.Ask();
    string comment = "Grid BUY L" + IntegerToString(level);

    if(trade.Buy(lot_size, _Symbol, 0, 0, 0, comment))
    {
        ulong ticket = trade.ResultOrder();
        buy_prices[buy_count] = current_ask;
        buy_lots[buy_count] = lot_size;
        buy_tickets[buy_count] = ticket;
        buy_times[buy_count] = TimeCurrent();

        buy_count++;
        last_order_time = TimeCurrent();
        total_lot_volume += lot_size;

        Print("✅ BUY order: Ticket=", ticket, " Lot=", lot_size, " Price=", current_ask);
    }
    else
    {
        Print("❌ BUY order failed: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Open SELL order                                                  |
//+------------------------------------------------------------------+
void OpenSellOrder(double price, double lot_size, int level)
{
    lot_size = NormalizeLotSize(lot_size);
    if(lot_size <= 0) return;

    double current_bid = symbolInfo.Bid();
    string comment = "Grid SELL L" + IntegerToString(level);

    if(trade.Sell(lot_size, _Symbol, 0, 0, 0, comment))
    {
        ulong ticket = trade.ResultOrder();
        sell_prices[sell_count] = current_bid;
        sell_lots[sell_count] = lot_size;
        sell_tickets[sell_count] = ticket;
        sell_times[sell_count] = TimeCurrent();

        sell_count++;
        last_order_time = TimeCurrent();
        total_lot_volume += lot_size;

        Print("✅ SELL order: Ticket=", ticket, " Lot=", lot_size, " Price=", current_bid);
    }
    else
    {
        Print("❌ SELL order failed: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Update positions                                                  |
//+------------------------------------------------------------------+
void UpdatePositions()
{
    for(int i = 0; i < buy_count; i++)
    {
        if(buy_tickets[i] > 0)
        {
            if(!position.SelectByTicket(buy_tickets[i]))
            {
                buy_tickets[i] = 0;
            }
        }
    }

    for(int i = 0; i < sell_count; i++)
    {
        if(sell_tickets[i] > 0)
        {
            if(!position.SelectByTicket(sell_tickets[i]))
            {
                sell_tickets[i] = 0;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check profit target                                               |
//+------------------------------------------------------------------+
void CheckProfitTarget()
{
    double total_profit = GetTotalProfit();
    double target_profit = CalculateTargetProfit(total_lot_volume, InpProfitTargetPercent);
    double quick_profit = CalculateTargetProfit(total_lot_volume, InpQuickProfitPercent);
    double micro_profit = total_lot_volume * 0.5;

    int holding_minutes = (grid_start_time > 0) ? (int)((TimeCurrent() - grid_start_time) / 60) : 0;

    // 💨 MICRO SCALP: Close immediately with tiny profit
    if(total_profit >= micro_profit && (buy_count + sell_count) == 1)
    {
        Print("💨 MICRO SCALP: $", total_profit);
        CloseAllPositions();
        ResetGrid();
        daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 1;
        return;
    }

    // ⚡ ULTRA QUICK: Fast scalping
    if(total_profit >= quick_profit && (buy_count + sell_count) <= 2)
    {
        Print("⚡ ULTRA QUICK: $", total_profit);
        CloseAllPositions();
        ResetGrid();
        daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 2;
        return;
    }

    // 🎯 TARGET HIT
    if(total_profit >= target_profit)
    {
        Print("🎯 TARGET HIT: $", total_profit);
        CloseAllPositions();
        ResetGrid();
        daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 2;
        return;
    }

    // ⏰ TIME FORCE: Close after holding time
    if(holding_minutes >= InpMaxHoldingMinutes && total_profit > total_lot_volume * InpMinLotProfit)
    {
        Print("⏰ TIME FORCE: ", holding_minutes, "m | $", total_profit);
        CloseAllPositions();
        ResetGrid();
        daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 3;
        return;
    }

    // 🏃 FAST FORCE: Any profit after 5 minutes
    if(holding_minutes >= 5 && total_profit > 0.1 && daily_trade_count < 500)
    {
        Print("🏃 FAST FORCE: ", holding_minutes, "m | $", total_profit);
        CloseAllPositions();
        ResetGrid();
        daily_trade_count++;
        daily_profit += total_profit;
        last_force_close = TimeCurrent();
        last_order_time = TimeCurrent() + 2;
        return;
    }

    // 🚨 EMERGENCY STOP
    double current_drawdown = initial_balance - account.Balance();
    if(current_drawdown >= InpMaxDrawdown)
    {
        Print("🚨 EMERGENCY STOP - Drawdown: $", current_drawdown);
        CloseAllPositions();
        ResetGrid();
        emergency_stop = true;
        last_order_time = TimeCurrent() + 60;
        return;
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
    grid_start_time = 0;
    total_lot_volume = 0.0;
    max_daily_profit = 0.0;

    ArrayInitialize(buy_prices, 0.0);
    ArrayInitialize(buy_lots, 0.0);
    ArrayInitialize(buy_tickets, 0);
    ArrayInitialize(buy_times, 0);

    ArrayInitialize(sell_prices, 0.0);
    ArrayInitialize(sell_lots, 0.0);
    ArrayInitialize(sell_tickets, 0);
    ArrayInitialize(sell_times, 0);

    // Reset daily counters if new day
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    MqlDateTime last_reset_struct;
    TimeToStruct(last_daily_reset, last_reset_struct);

    if(time_struct.day != last_reset_struct.day)
    {
        daily_trade_count = 0;
        daily_profit = 0.0;
        max_daily_profit = 0.0;
        emergency_stop = false;
        last_daily_reset = TimeCurrent();
        Print("🔄 NEW DAY - Counters reset");
    }

    last_order_time = 0;
}

//+------------------------------------------------------------------+
//| Calculate Dynamic Lot Size                                      |
//+------------------------------------------------------------------+
double CalculateDynamicLotSize(double base_lot, int level)
{
    double dynamic_lot = base_lot;
    double balance = account.Balance();
    double equity_ratio = account.Equity() / balance;

    // Health-based multiplier
    double health_multiplier = 1.0;
    if(equity_ratio > 0.95) health_multiplier = 2.0;
    else if(equity_ratio > 0.90) health_multiplier = 1.5;
    else if(equity_ratio > 0.85) health_multiplier = 1.2;
    else health_multiplier = 0.8;

    dynamic_lot *= health_multiplier;

    // Daily performance boost
    if(daily_profit > 0 && daily_trade_count < 100)
        dynamic_lot *= 1.3;

    // Time-based boost
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    int hour = time_struct.hour;
    if(hour >= 8 && hour <= 16)
        dynamic_lot *= 1.2;

    // Level-based scaling
    if(level == 0)
        dynamic_lot *= 1.5;
    else if(level <= 2)
        dynamic_lot *= (1.0 + level * 0.3);
    else
        dynamic_lot *= (1.0 + level * 0.4);

    // Maximum lot constraint
    double max_allowed_lot = balance * 0.002;
    if(dynamic_lot > max_allowed_lot)
        dynamic_lot = max_allowed_lot;

    // Minimum lot for volume spinning
    double min_spinning_lot = symbolInfo.LotsMin() * 2;
    if(dynamic_lot < min_spinning_lot)
        dynamic_lot = min_spinning_lot;

    return NormalizeLotSize(dynamic_lot);
}

//+------------------------------------------------------------------+
//| Check Daily Risk Limits                                         |
//+------------------------------------------------------------------+
bool CheckDailyRiskLimits()
{
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    MqlDateTime last_reset_struct;
    TimeToStruct(last_daily_reset, last_reset_struct);

    // Reset at midnight
    if(time_struct.day != last_reset_struct.day)
    {
        daily_start_balance = account.Balance();
        last_daily_reset = TimeCurrent();
        daily_limit_reached = false;
        daily_trade_count = 0;
        daily_profit = 0.0;
        max_daily_profit = 0.0;
        emergency_stop = false;
        Print("📅 NEW DAY - Limits reset");
    }

    // Check daily loss
    double daily_loss = daily_start_balance - account.Balance();
    if(daily_loss >= InpMaxDailyLoss)
    {
        if(!daily_limit_reached)
        {
            Print("🚨 Daily loss limit: $", daily_loss);
            CloseAllPositions();
            ResetGrid();
            daily_limit_reached = true;
            emergency_stop = true;
        }
        return false;
    }

    // Check trade count
    if(daily_trade_count >= InpMaxTradesPerDay)
    {
        Print("🎯 Daily target reached: ", daily_trade_count, " trades | Profit: $", daily_profit);
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Can Open New Position                                          |
//+------------------------------------------------------------------+
bool CanOpenNewPosition()
{
    if(daily_trade_count >= InpMaxTradesPerDay) return false;
    if(emergency_stop) return false;

    double equity_ratio = account.Equity() / account.Balance();
    if(equity_ratio < 0.8) return false;

    return true;
}

//+------------------------------------------------------------------+
//| Get Dynamic Cooldown                                           |
//+------------------------------------------------------------------+
int GetDynamicCooldown()
{
    int base_cooldown = 1; // Ultra fast

    // Scale based on trade count
    if(daily_trade_count > 200) base_cooldown = 5;
    else if(daily_trade_count > 150) base_cooldown = 4;
    else if(daily_trade_count > 100) base_cooldown = 3;
    else if(daily_trade_count > 50) base_cooldown = 2;

    // Instant restart after profit
    if(TimeCurrent() - last_force_close < 60) base_cooldown = 0;

    // Time boost
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    int hour = time_struct.hour;
    if(hour >= 8 && hour <= 16)
        base_cooldown = MathMax(base_cooldown - 1, 0);

    // Profit boost
    if(daily_profit > 50.0)
        base_cooldown = MathMax(base_cooldown - 1, 0);

    return MathMax(base_cooldown, 0);
}

//+------------------------------------------------------------------+
//| Calculate Target Profit                                        |
//+------------------------------------------------------------------+
double CalculateTargetProfit(double lot_volume, double profit_percent)
{
    if(lot_volume <= 0) return 0.5;

    double base_profit_per_lot = 50.0; // Reduced for faster trades
    double target = lot_volume * profit_percent * base_profit_per_lot;

    // Volume bonuses
    if(lot_volume >= 1.0) target *= 1.5;
    if(lot_volume >= 2.0) target *= 1.3;
    if(lot_volume >= 5.0) target *= 1.2;

    // Market adjustments
    string symbol = _Symbol;
    if(StringFind(symbol, "JPY") >= 0) target *= 0.3;
    else if(StringFind(symbol, "XAU") >= 0) target *= 2.0;
    else if(StringFind(symbol, "GBP") >= 0) target *= 1.4;

    // Daily progress adjustment
    if(daily_trade_count < 50) target *= 0.8;
    else if(daily_trade_count < 100) target *= 0.9;

    // Time adjustments
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    int hour = time_struct.hour;
    if(hour >= 8 && hour <= 10) target *= 0.7;
    if(hour >= 14 && hour <= 16) target *= 0.8;

    // Constraints
    if(target < 0.3) target = 0.3;
    if(target > 500.0) target = 500.0;

    return target;
}

//+------------------------------------------------------------------+
//| Normalize lot size                                               |
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