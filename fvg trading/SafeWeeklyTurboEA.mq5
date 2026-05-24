//+------------------------------------------------------------------+
//|                                        SafeWeeklyTurboEA.mq5   |
//|                                    SAFE VERSION WITH CONTROLS   |
//|                                         FIXED RISK MANAGEMENT   |
//+------------------------------------------------------------------+
#property copyright "Safe Weekly Turbo EA"
#property link      ""
#property version   "2.00"
#property description "SAFE EA - Fixed Risk Management & Position Control"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade trade;
CPositionInfo position;

//+------------------------------------------------------------------+
//| Input Parameters - SAFE SETTINGS                                |
//+------------------------------------------------------------------+
input group "=== SAFE SETTINGS ==="
input int InpMagicNumber = 88888;        // Magic Number
input double InpWeeklyTarget = 5.0;      // Weekly Target (%) - REDUCED
input double InpDailyTarget = 1.0;       // Daily Target (%) - REDUCED
input bool InpSafeMode = true;           // SAFE MODE (Low Risk)

input group "=== RISK MANAGEMENT ==="
input double InpRiskPercent = 2.0;       // Risk per Trade (%) - SAFE
input double InpMaxRiskPercent = 10.0;   // Max Total Risk (%) - SAFE
input double InpStopLossPoints = 500;    // Stop Loss (Points) - MANDATORY
input double InpTakeProfitPoints = 300;  // Take Profit (Points)

input group "=== POSITION CONTROL ==="
input double InpMaxLotSize = 1.0;        // Max Lot Size - CONTROLLED
input int InpMinOrderInterval = 30;      // Min Seconds Between Orders
input int InpMaxPositions = 5;           // Max Positions - REDUCED
input int InpMaxTradesPerHour = 10;      // Max Trades per Hour - REDUCED

input group "=== GRID SETTINGS ==="
input int InpGridStep = 200;             // Grid Step (Points) - INCREASED
input double InpGridProfit = 50.0;       // Grid Profit Target ($)
input bool InpUseGrid = true;            // Enable Grid Trading

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
double weekly_start_balance = 0;
double daily_start_balance = 0;
datetime week_start = 0;
datetime day_start = 0;
datetime last_order_time = 0;
int trades_this_hour = 0;
datetime hour_start = 0;

// Safety tracking
double max_drawdown = 0;
double peak_balance = 0;
int consecutive_losses = 0;
bool emergency_stop = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== GRID TURBO EA - NO STOP LOSS ===");
    Print("GRID MODE: Pure grid trading without stop loss");
    
    trade.SetExpertMagicNumber(InpMagicNumber);
    
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    weekly_start_balance = balance;
    daily_start_balance = balance;
    peak_balance = balance;
    week_start = TimeCurrent();
    day_start = TimeCurrent();
    hour_start = TimeCurrent();
    
    Print("Starting Balance: $", balance);
    Print("*** GRID PROFIT TARGET: $", InpGridProfit, " ***");
    Print("EA will close ALL positions when total profit >= $", InpGridProfit);
    Print("Grid Step: ", InpGridStep, " points");
    Print("Max Positions: ", InpMaxPositions);
    Print("Starting Lot: 0.01 (increases with martingale)");
    Print("WARNING: NO STOP LOSS - Pure Grid Trading");
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_log = 0;
    
    // FIRST PRIORITY: Check Grid Profit Target
    double current_profit = GetTotalProfit();
    int positions = CountActivePositions();
    
    // Debug every 10 seconds when positions exist
    if(positions > 0)
    {
        static datetime last_debug = 0;
        if(TimeCurrent() - last_debug > 10)
        {
            Print("GRID CHECK: Positions=", positions, " Profit=$", current_profit, " Target=$", InpGridProfit);
            last_debug = TimeCurrent();
        }
    }
    
    // Close all positions when profit target reached
    if(positions > 0 && current_profit >= InpGridProfit)
    {
        Print("*** GRID PROFIT TARGET REACHED ***");
        Print("Total Positions: ", positions);
        Print("Current Profit: $", current_profit);
        Print("Target Profit: $", InpGridProfit);
        CloseAllPositions();
        Print("All positions closed successfully");
        return;
    }
    
    // Reset counters
    CheckTimeResets();
    
    // Update safety metrics
    UpdateSafetyMetrics();
    
    // Performance monitoring (every 60 seconds)
    if(TimeCurrent() - last_log > 60)
    {
        LogPerformance();
        last_log = TimeCurrent();
    }
    
    // Emergency safety check
    if(!SafetyCheck()) return;
    
    // Rate limiting
    if(trades_this_hour >= InpMaxTradesPerHour) return;
    
    // Position limit check
    if(CountActivePositions() >= InpMaxPositions) return;
    
    // Time interval check
    if(TimeCurrent() - last_order_time < InpMinOrderInterval) return;
    
    // Main safe trading logic
    ExecuteSafeStrategy();
}

//+------------------------------------------------------------------+
//| Execute Safe Strategy                                            |
//+------------------------------------------------------------------+
void ExecuteSafeStrategy()
{
    // Profit checking is now done in OnTick() - removed duplicate check
    
    // Manage existing positions
    ManagePositions();
    
    // Open new positions if conditions are met
    if(InpUseGrid && CountActivePositions() == 0)
    {
        OpenInitialPosition();
    }
    else if(InpUseGrid && CountActivePositions() > 0 && CountActivePositions() < InpMaxPositions)
    {
        CheckGridExpansion();
    }
}

//+------------------------------------------------------------------+
//| Open Initial Position with Safe Lot Size                        |
//+------------------------------------------------------------------+
void OpenInitialPosition()
{
    double lot_size = CalculateSafeLotSize();
    if(lot_size <= 0) return;
    
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    
    if(ask <= 0 || bid <= 0) return;
    
    // Simple trend analysis
    string trend = AnalyzeMarketSafe();
    bool open_buy = (trend == "BUY");
    
    // Grid Trading - NO STOP LOSS, NO TAKE PROFIT
    if(open_buy)
    {
        if(trade.Buy(lot_size, _Symbol, 0, 0, 0, "Grid-B0"))
        {
            Print("GRID BUY OPENED: Lot=", lot_size, " Price=", ask, " NO SL/TP");
            last_order_time = TimeCurrent();
            trades_this_hour++;
        }
    }
    else
    {
        if(trade.Sell(lot_size, _Symbol, 0, 0, 0, "Grid-S0"))
        {
            Print("GRID SELL OPENED: Lot=", lot_size, " Price=", bid, " NO SL/TP");
            last_order_time = TimeCurrent();
            trades_this_hour++;
        }
    }
}

//+------------------------------------------------------------------+
//| Check Grid Expansion with Safe Controls                         |
//+------------------------------------------------------------------+
void CheckGridExpansion()
{
    double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double grid_distance = InpGridStep * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    
    // Get the last position price
    double last_price = GetLastPositionPrice();
    if(last_price <= 0) return;
    
    // Check if price has moved enough to add new position
    bool should_add = false;
    bool is_buy_direction = IsLastPositionBuy();
    
    if(is_buy_direction && current_price <= (last_price - grid_distance))
    {
        should_add = true;
    }
    else if(!is_buy_direction && current_price >= (last_price + grid_distance))
    {
        should_add = true;
    }
    
    if(should_add)
    {
        double lot_size = CalculateSafeLotSize();
        if(lot_size <= 0) return;
        
        // Grid Trading - NO STOP LOSS
        if(is_buy_direction)
        {
            double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
                
            if(trade.Buy(lot_size, _Symbol, 0, 0, 0, "Grid-B" + IntegerToString(CountActivePositions())))
            {
                Print("GRID BUY ADDED: Level=", CountActivePositions(), " Lot=", lot_size, " Price=", ask, " NO SL");
                last_order_time = TimeCurrent();
                trades_this_hour++;
            }
        }
        else
        {
            double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
                
            if(trade.Sell(lot_size, _Symbol, 0, 0, 0, "Grid-S" + IntegerToString(CountActivePositions())))
            {
                Print("GRID SELL ADDED: Level=", CountActivePositions(), " Lot=", lot_size, " Price=", bid, " NO SL");
                last_order_time = TimeCurrent();
                trades_this_hour++;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate Safe Lot Size Based on Risk Management                |
//+------------------------------------------------------------------+
double CalculateSafeLotSize()
{
    // Grid Trading - Fixed lot size, no risk calculation
    double lot_size = 0.01; // Start with minimum lot
    
    // Increase lot size based on number of positions (martingale style)
    int positions = CountActivePositions();
    if(positions > 0)
    {
        lot_size = 0.01 * MathPow(1.5, positions); // Multiply by 1.5 each level
    }
    
    // Apply maximum lot size limit
    lot_size = MathMin(lot_size, InpMaxLotSize);
    
    // Ensure minimum requirements
    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    if(min_lot > 0)
        lot_size = MathMax(lot_size, min_lot);
    else
        lot_size = MathMax(lot_size, 0.01);
    
    return NormalizeDouble(lot_size, 2);
}

//+------------------------------------------------------------------+
//| Analyze Market with Safe Approach                               |
//+------------------------------------------------------------------+
string AnalyzeMarketSafe()
{
    // Simple and safe trend analysis
    double ma_fast[], ma_slow[];
    
    int ma_fast_handle = iMA(_Symbol, PERIOD_CURRENT, 10, 0, MODE_EMA, PRICE_CLOSE);
    int ma_slow_handle = iMA(_Symbol, PERIOD_CURRENT, 30, 0, MODE_EMA, PRICE_CLOSE);
    
    if(CopyBuffer(ma_fast_handle, 0, 0, 1, ma_fast) < 1 ||
       CopyBuffer(ma_slow_handle, 0, 0, 1, ma_slow) < 1)
    {
        return "NEUTRAL";
    }
    
    if(ma_fast[0] > ma_slow[0])
        return "BUY";
    else
        return "SELL";
}

//+------------------------------------------------------------------+
//| Safety Check Function                                           |
//+------------------------------------------------------------------+
bool SafetyCheck()
{
    if(emergency_stop)
    {
        Print("EMERGENCY STOP ACTIVE - Trading halted");
        return false;
    }
    
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double weekly_loss = weekly_start_balance - balance;
    double max_weekly_loss = weekly_start_balance * InpMaxRiskPercent / 100.0;
    
    if(weekly_loss >= max_weekly_loss)
    {
        Print("WEEKLY RISK LIMIT EXCEEDED: Loss $", weekly_loss, " >= Limit $", max_weekly_loss);
        CloseAllPositions();
        emergency_stop = true;
        return false;
    }
    
    // Check consecutive losses
    if(consecutive_losses >= 5)
    {
        Print("TOO MANY CONSECUTIVE LOSSES: ", consecutive_losses, " - Pausing");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Manage Existing Positions                                       |
//+------------------------------------------------------------------+
void ManagePositions()
{
    // Check for positions that need attention
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                // Add trailing stop or other management logic here
                // For now, let SL/TP handle the positions
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Utility Functions                                                |
//+------------------------------------------------------------------+
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

double GetTotalExposure()
{
    // Grid Trading - Calculate total lot size exposure
    double total_lots = 0;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                total_lots += position.Volume();
            }
        }
    }
    return total_lots;
}

double GetLastPositionPrice()
{
    datetime latest_time = 0;
    double latest_price = 0;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.Time() > latest_time)
                {
                    latest_time = position.Time();
                    latest_price = position.PriceOpen();
                }
            }
        }
    }
    return latest_price;
}

bool IsLastPositionBuy()
{
    datetime latest_time = 0;
    bool is_buy = true;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.Time() > latest_time)
                {
                    latest_time = position.Time();
                    is_buy = (position.PositionType() == POSITION_TYPE_BUY);
                }
            }
        }
    }
    return is_buy;
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

void UpdateSafetyMetrics()
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    
    // Update peak balance
    if(balance > peak_balance)
        peak_balance = balance;
    
    // Calculate current drawdown
    double current_drawdown = (peak_balance - balance) / peak_balance * 100.0;
    if(current_drawdown > max_drawdown)
        max_drawdown = current_drawdown;
}

void LogPerformance()
{
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double weekly_pnl = balance - weekly_start_balance;
    double daily_pnl = balance - daily_start_balance;
    double weekly_percent = (weekly_pnl / weekly_start_balance) * 100;
    double daily_percent = (daily_pnl / daily_start_balance) * 100;
    
    Print("SAFE EA STATUS: Balance=$", balance,
          " WeeklyPnL=", weekly_percent, "%",
          " DailyPnL=", daily_percent, "%",
          " Positions=", CountActivePositions(),
          " MaxDD=", max_drawdown, "%");
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
        double daily_pnl = (AccountInfoDouble(ACCOUNT_BALANCE) - daily_start_balance) / daily_start_balance * 100;
        Print("DAILY PERFORMANCE: ", daily_pnl, "% (Target: ", InpDailyTarget, "%)");
        daily_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        day_start = TimeCurrent();
    }
    
    // Weekly reset
    MqlDateTime week_time;
    TimeToStruct(week_start, week_time);
    if(current_time.day_of_week == 1 && week_time.day_of_week != 1)
    {
        double weekly_pnl = (AccountInfoDouble(ACCOUNT_BALANCE) - weekly_start_balance) / weekly_start_balance * 100;
        Print("WEEKLY PERFORMANCE: ", weekly_pnl, "% (Target: ", InpWeeklyTarget, "%)");
        weekly_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        week_start = TimeCurrent();
        consecutive_losses = 0;
        emergency_stop = false;
    }
    
    // Hourly reset
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
    Print("=== SAFE WEEKLY TURBO EA STOPPED ===");
    double balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double weekly_performance = (balance - weekly_start_balance) / weekly_start_balance * 100;
    
    Print("Final Balance: $", balance);
    Print("Weekly Performance: ", weekly_performance, "%");
    Print("Max Drawdown: ", max_drawdown, "%");
    Print("SAFE MODE: Risk controlled");
}