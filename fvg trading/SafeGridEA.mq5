//+------------------------------------------------------------------+
//|                                          GridTradingEA_v2.mq5   |
//|                           Grid Trading with Trend Management     |
//|                                    Enhanced Recovery System      |
//+------------------------------------------------------------------+
#property copyright "Grid Trading EA v2"
#property link      ""
#property version   "2.00"
#property description "Grid Trading with Trend Reversal Management"

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
input double InpBaseLotSize = 0.1;                   // Base Lot Size
input double InpLotMultiplier = 1.3;                 // Lot Multiplier
input int InpGridStep = 100;                         // Grid Step (points)
input int InpMaxLevels = 5;                          // Maximum Grid Levels
input double InpProfitTarget = 20.0;                 // Profit Target ($)

input group "=== Recovery Settings ==="
input bool InpUseRecovery = true;                    // Use Recovery System
input int InpRecoveryTriggerLevel = 3;               // Recovery Trigger (Grid Level)
input double InpRecoveryMultiplier = 2.0;            // Recovery Lot Multiplier
input int InpMaxDrawdownPips = 500;                  // Max Drawdown (pips) before reset

input group "=== Trend Management ==="
input bool InpUseTrendFilter = true;                 // Use Trend Filter
input int InpMAPeriod = 50;                          // MA Period for Trend
input int InpRSIPeriod = 14;                         // RSI Period
input double InpRSIOverbought = 70.0;                // RSI Overbought Level
input double InpRSIOversold = 30.0;                  // RSI Oversold Level

input group "=== Risk Management ==="
input double InpMaxDrawdown = 500.0;                 // Maximum Drawdown ($)
input double InpDailyProfitTarget = 100.0;           // Daily Profit Target ($)
input double InpDailyLossLimit = 200.0;              // Daily Loss Limit ($)
input bool InpCloseOnOpposite = true;                // Close on Opposite Signal

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
struct GridLevel {
    double price;
    double lot;
    ulong ticket;
    datetime time;
    bool active;
};

GridLevel buyGrid[];
GridLevel sellGrid[];

int buy_count = 0;
int sell_count = 0;

double initial_balance = 0.0;
double daily_starting_balance = 0.0;
double grid_start_price = 0.0;
datetime last_order_time = 0;
datetime current_day_start = 0;

bool grid_active = false;
string grid_direction = "NONE";
bool in_recovery_mode = false;

// Indicator handles
int ma_handle = INVALID_HANDLE;
int rsi_handle = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== Grid Trading EA v2 Started ===");
    
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
        Print("ERROR: Failed to select symbol");
        return INIT_FAILED;
    }
    
    // Initialize indicators
    if(InpUseTrendFilter)
    {
        ma_handle = iMA(_Symbol, PERIOD_CURRENT, InpMAPeriod, 0, MODE_EMA, PRICE_CLOSE);
        rsi_handle = iRSI(_Symbol, PERIOD_CURRENT, InpRSIPeriod, PRICE_CLOSE);
        
        if(ma_handle == INVALID_HANDLE || rsi_handle == INVALID_HANDLE)
        {
            Print("ERROR: Failed to create indicators");
            return INIT_FAILED;
        }
    }
    
    // Wait for symbol data
    int attempts = 0;
    while(!symbolInfo.RefreshRates() && attempts < 10)
    {
        Sleep(1000);
        attempts++;
    }
    
    if(attempts >= 10)
    {
        Print("ERROR: Symbol data not available");
        return INIT_FAILED;
    }
    
    initial_balance = account.Balance();
    daily_starting_balance = initial_balance;
    current_day_start = TimeCurrent();
    
    // Initialize grid arrays
    ArrayResize(buyGrid, InpMaxLevels);
    ArrayResize(sellGrid, InpMaxLevels);
    
    // Validate lot size
    if(InpBaseLotSize < symbolInfo.LotsMin())
    {
        Print("ERROR: Base lot size too small");
        return INIT_PARAMETERS_INCORRECT;
    }
    
    CloseAllPositions();
    ResetGrid();
    
    Print("Initialization successful");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    if(ma_handle != INVALID_HANDLE) IndicatorRelease(ma_handle);
    if(rsi_handle != INVALID_HANDLE) IndicatorRelease(rsi_handle);
    
    Print("=== Grid Trading EA Stopped ===");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    symbolInfo.RefreshRates();
    
    if(!IsValidMarketCondition()) return;
    
    CheckDailyReset();
    UpdatePositions();
    
    // Check for trend reversal
    if(grid_active && InpCloseOnOpposite)
    {
        if(CheckTrendReversal())
        {
            HandleTrendReversal();
            return;
        }
    }
    
    // Check profit/loss targets
    if(CheckTargets())
    {
        CloseAllPositions();
        ResetGrid();
        return;
    }
    
    // Start new grid if needed
    if(!grid_active && TimeCurrent() - last_order_time > 30)
    {
        StartNewGrid();
        return;
    }
    
    // Manage existing grid
    if(grid_active)
    {
        if(in_recovery_mode)
        {
            ManageRecoveryMode();
        }
        else
        {
            ManageNormalGrid();
        }
    }
}

//+------------------------------------------------------------------+
//| Check for trend reversal                                         |
//+------------------------------------------------------------------+
bool CheckTrendReversal()
{
    if(!InpUseTrendFilter) return false;
    
    string current_trend = GetCurrentTrend();
    
    // Check if trend has reversed against our position
    if(grid_direction == "BUY" && current_trend == "SELL")
    {
        double current_loss = GetTotalProfit();
        if(current_loss < -InpMaxDrawdownPips * symbolInfo.Point() * 10) // Convert pips to money
        {
            Print("Trend reversal detected - BUY grid in SELL trend");
            return true;
        }
    }
    else if(grid_direction == "SELL" && current_trend == "BUY")
    {
        double current_loss = GetTotalProfit();
        if(current_loss < -InpMaxDrawdownPips * symbolInfo.Point() * 10)
        {
            Print("Trend reversal detected - SELL grid in BUY trend");
            return true;
        }
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Handle trend reversal                                            |
//+------------------------------------------------------------------+
void HandleTrendReversal()
{
    Print("=== HANDLING TREND REVERSAL ===");
    
    double current_profit = GetTotalProfit();
    
    if(InpUseRecovery && current_profit < 0)
    {
        // Enter recovery mode
        in_recovery_mode = true;
        Print("Entering RECOVERY MODE - Loss: $", MathAbs(current_profit));
        
        // Close losing positions gradually
        CloseWorstPosition();
        
        // Open counter-trend recovery position
        if(grid_direction == "BUY")
        {
            double recovery_lot = CalculateRecoveryLot();
            OpenSellOrder(symbolInfo.Bid(), recovery_lot, 99); // Level 99 = recovery
            Print("Opened recovery SELL: ", recovery_lot, " lots");
        }
        else if(grid_direction == "SELL")
        {
            double recovery_lot = CalculateRecoveryLot();
            OpenBuyOrder(symbolInfo.Ask(), recovery_lot, 99);
            Print("Opened recovery BUY: ", recovery_lot, " lots");
        }
    }
    else
    {
        // Close all and restart
        Print("Closing all positions due to trend reversal");
        CloseAllPositions();
        ResetGrid();
        
        // Wait before starting new grid
        last_order_time = TimeCurrent() + 60; // Wait 60 seconds
    }
}

//+------------------------------------------------------------------+
//| Calculate recovery lot size                                      |
//+------------------------------------------------------------------+
double CalculateRecoveryLot()
{
    double total_loss = MathAbs(GetTotalProfit());
    double point_value = symbolInfo.Point() * 10; // pip value
    double required_pips = total_loss / point_value;
    
    // Calculate lot size needed to recover loss in next movement
    double recovery_lot = (total_loss / (InpGridStep * point_value)) * InpRecoveryMultiplier;
    
    // Apply safety limits
    recovery_lot = MathMin(recovery_lot, symbolInfo.LotsMax());
    recovery_lot = MathMax(recovery_lot, InpBaseLotSize * InpRecoveryMultiplier);
    
    return NormalizeLotSize(recovery_lot);
}

//+------------------------------------------------------------------+
//| Close worst performing position                                  |
//+------------------------------------------------------------------+
void CloseWorstPosition()
{
    double worst_profit = 0;
    ulong worst_ticket = 0;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                double profit = position.Profit();
                if(profit < worst_profit)
                {
                    worst_profit = profit;
                    worst_ticket = position.Ticket();
                }
            }
        }
    }
    
    if(worst_ticket > 0)
    {
        trade.PositionClose(worst_ticket);
        Print("Closed worst position: Ticket ", worst_ticket, " Loss: $", MathAbs(worst_profit));
    }
}

//+------------------------------------------------------------------+
//| Manage recovery mode                                             |
//+------------------------------------------------------------------+
void ManageRecoveryMode()
{
    double total_profit = GetTotalProfit();
    
    // Exit recovery if back to breakeven or profit
    if(total_profit >= 0)
    {
        Print("Recovery successful! Profit: $", total_profit);
        CloseAllPositions();
        ResetGrid();
        in_recovery_mode = false;
        return;
    }
    
    // Continue recovery strategy
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();
    double step_size = InpGridStep * symbolInfo.Point() * 0.5; // Smaller steps in recovery
    
    // Add recovery positions based on current trend
    string trend = GetCurrentTrend();
    
    if(trend == "BUY" && buy_count < InpMaxLevels)
    {
        if(current_ask <= grid_start_price - (buy_count * step_size))
        {
            double lot = InpBaseLotSize * InpRecoveryMultiplier;
            OpenBuyOrder(current_ask, lot, buy_count);
        }
    }
    else if(trend == "SELL" && sell_count < InpMaxLevels)
    {
        if(current_bid >= grid_start_price + (sell_count * step_size))
        {
            double lot = InpBaseLotSize * InpRecoveryMultiplier;
            OpenSellOrder(current_bid, lot, sell_count);
        }
    }
}

//+------------------------------------------------------------------+
//| Get current trend                                                |
//+------------------------------------------------------------------+
string GetCurrentTrend()
{
    if(!InpUseTrendFilter) return "NEUTRAL";
    
    double ma_value = GetIndicatorValue(ma_handle, 0);
    double rsi_value = GetIndicatorValue(rsi_handle, 0);
    double current_price = symbolInfo.Bid();
    
    // Strong BUY signal
    if(current_price > ma_value && rsi_value < InpRSIOverbought && rsi_value > 50)
    {
        return "BUY";
    }
    // Strong SELL signal
    else if(current_price < ma_value && rsi_value > InpRSIOversold && rsi_value < 50)
    {
        return "SELL";
    }
    
    return "NEUTRAL";
}

//+------------------------------------------------------------------+
//| Get indicator value                                              |
//+------------------------------------------------------------------+
double GetIndicatorValue(int handle, int index)
{
    double buffer[];
    if(handle != INVALID_HANDLE && CopyBuffer(handle, 0, index, 1, buffer) > 0)
    {
        return buffer[0];
    }
    return 0;
}

//+------------------------------------------------------------------+
//| Manage normal grid                                               |
//+------------------------------------------------------------------+
void ManageNormalGrid()
{
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();
    double step_size = InpGridStep * symbolInfo.Point();
    
    if(grid_direction == "BUY")
    {
        // Add more BUY orders when price drops
        if(buy_count < InpMaxLevels)
        {
            double next_level = grid_start_price - (buy_count * step_size);
            if(current_ask <= next_level && TimeCurrent() - last_order_time > 5)
            {
                double lot_size = InpBaseLotSize * MathPow(InpLotMultiplier, buy_count);
                
                // Check if we should enter recovery mode
                if(buy_count >= InpRecoveryTriggerLevel && InpUseRecovery)
                {
                    lot_size *= InpRecoveryMultiplier;
                    in_recovery_mode = true;
                    Print("Entering recovery mode at level ", buy_count);
                }
                
                OpenBuyOrder(current_ask, lot_size, buy_count);
            }
        }
    }
    else if(grid_direction == "SELL")
    {
        // Add more SELL orders when price rises
        if(sell_count < InpMaxLevels)
        {
            double next_level = grid_start_price + (sell_count * step_size);
            if(current_bid >= next_level && TimeCurrent() - last_order_time > 5)
            {
                double lot_size = InpBaseLotSize * MathPow(InpLotMultiplier, sell_count);
                
                // Check if we should enter recovery mode
                if(sell_count >= InpRecoveryTriggerLevel && InpUseRecovery)
                {
                    lot_size *= InpRecoveryMultiplier;
                    in_recovery_mode = true;
                    Print("Entering recovery mode at level ", sell_count);
                }
                
                OpenSellOrder(current_bid, lot_size, sell_count);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check profit/loss targets                                        |
//+------------------------------------------------------------------+
bool CheckTargets()
{
    double total_profit = GetTotalProfit();
    double daily_profit = account.Balance() - daily_starting_balance;
    
    // Check profit target
    if(total_profit >= InpProfitTarget)
    {
        Print("Profit target reached: $", total_profit);
        return true;
    }
    
    // Check daily profit target
    if(daily_profit >= InpDailyProfitTarget)
    {
        Print("Daily profit target reached: $", daily_profit);
        return true;
    }
    
    // Check max drawdown
    if(total_profit <= -InpMaxDrawdown)
    {
        Print("Max drawdown reached: $", MathAbs(total_profit));
        return true;
    }
    
    // Check daily loss limit
    if(daily_profit <= -InpDailyLossLimit)
    {
        Print("Daily loss limit reached: $", MathAbs(daily_profit));
        return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Start new grid                                                   |
//+------------------------------------------------------------------+
void StartNewGrid()
{
    string trend = GetCurrentTrend();
    
    if(trend == "BUY")
    {
        grid_direction = "BUY";
        grid_start_price = symbolInfo.Ask();
        OpenBuyOrder(symbolInfo.Ask(), InpBaseLotSize, 0);
        Print("Started BUY grid with trend");
    }
    else if(trend == "SELL")
    {
        grid_direction = "SELL";
        grid_start_price = symbolInfo.Bid();
        OpenSellOrder(symbolInfo.Bid(), InpBaseLotSize, 0);
        Print("Started SELL grid with trend");
    }
    else
    {
        // No clear trend, wait
        Print("No clear trend, waiting...");
        return;
    }
    
    grid_active = true;
    in_recovery_mode = false;
}

//+------------------------------------------------------------------+
//| Check daily reset                                                |
//+------------------------------------------------------------------+
void CheckDailyReset()
{
    MqlDateTime current_time, start_time;
    TimeToStruct(TimeCurrent(), current_time);
    TimeToStruct(current_day_start, start_time);
    
    if(current_time.day != start_time.day)
    {
        daily_starting_balance = account.Balance();
        current_day_start = TimeCurrent();
        Print("New day - Balance: $", daily_starting_balance);
    }
}

//+------------------------------------------------------------------+
//| Check valid market condition                                     |
//+------------------------------------------------------------------+
bool IsValidMarketCondition()
{
    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();
    double spread = current_ask - current_bid;
    double max_spread = InpGridStep * symbolInfo.Point() * 0.3; // Max 30% of grid step
    
    if(spread > max_spread)
    {
        return false; // Spread too high
    }
    
    return (current_ask > 0 && current_bid > 0);
}

//+------------------------------------------------------------------+
//| Open BUY order                                                   |
//+------------------------------------------------------------------+
void OpenBuyOrder(double price, double lot_size, int level)
{
    lot_size = NormalizeLotSize(lot_size);
    if(lot_size <= 0) return;
    
    string comment = StringFormat("Grid BUY L%d%s", level, in_recovery_mode ? " [R]" : "");
    
    if(trade.Buy(lot_size, _Symbol, 0, 0, 0, comment))
    {
        ulong ticket = trade.ResultOrder();
        
        if(level < ArraySize(buyGrid))
        {
            buyGrid[buy_count].price = symbolInfo.Ask();
            buyGrid[buy_count].lot = lot_size;
            buyGrid[buy_count].ticket = ticket;
            buyGrid[buy_count].time = TimeCurrent();
            buyGrid[buy_count].active = true;
        }
        
        buy_count++;
        last_order_time = TimeCurrent();
        Print("BUY opened: ", ticket, " Price: ", symbolInfo.Ask(), " Lot: ", lot_size);
    }
}

//+------------------------------------------------------------------+
//| Open SELL order                                                  |
//+------------------------------------------------------------------+
void OpenSellOrder(double price, double lot_size, int level)
{
    lot_size = NormalizeLotSize(lot_size);
    if(lot_size <= 0) return;
    
    string comment = StringFormat("Grid SELL L%d%s", level, in_recovery_mode ? " [R]" : "");
    
    if(trade.Sell(lot_size, _Symbol, 0, 0, 0, comment))
    {
        ulong ticket = trade.ResultOrder();
        
        if(level < ArraySize(sellGrid))
        {
            sellGrid[sell_count].price = symbolInfo.Bid();
            sellGrid[sell_count].lot = lot_size;
            sellGrid[sell_count].ticket = ticket;
            sellGrid[sell_count].time = TimeCurrent();
            sellGrid[sell_count].active = true;
        }
        
        sell_count++;
        last_order_time = TimeCurrent();
        Print("SELL opened: ", ticket, " Price: ", symbolInfo.Bid(), " Lot: ", lot_size);
    }
}

//+------------------------------------------------------------------+
//| Update positions                                                  |
//+------------------------------------------------------------------+
void UpdatePositions()
{
    // Update buy positions
    for(int i = 0; i < buy_count; i++)
    {
        if(buyGrid[i].ticket > 0 && buyGrid[i].active)
        {
            if(!position.SelectByTicket(buyGrid[i].ticket))
            {
                buyGrid[i].active = false;
            }
        }
    }
    
    // Update sell positions
    for(int i = 0; i < sell_count; i++)
    {
        if(sellGrid[i].ticket > 0 && sellGrid[i].active)
        {
            if(!position.SelectByTicket(sellGrid[i].ticket))
            {
                sellGrid[i].active = false;
            }
        }
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
    
    Print("All positions closed");
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
    in_recovery_mode = false;
    
    // Clear arrays
    for(int i = 0; i < ArraySize(buyGrid); i++)
    {
        buyGrid[i].price = 0;
        buyGrid[i].lot = 0;
        buyGrid[i].ticket = 0;
        buyGrid[i].time = 0;
        buyGrid[i].active = false;
    }
    
    for(int i = 0; i < ArraySize(sellGrid); i++)
    {
        sellGrid[i].price = 0;
        sellGrid[i].lot = 0;
        sellGrid[i].ticket = 0;
        sellGrid[i].time = 0;
        sellGrid[i].active = false;
    }
    
    last_order_time = 0;
    Print("Grid reset completed");
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
    
    return NormalizeDouble(lot_size, 2);
}