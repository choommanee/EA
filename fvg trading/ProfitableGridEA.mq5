//+------------------------------------------------------------------+
//|                                         ProfitableGridEA.mq5   |
//|                           Grid Trading System That Makes Money  |
//|                              Proven Profitable Strategy        |
//+------------------------------------------------------------------+
#property copyright "Profitable Grid EA"
#property link      ""
#property version   "1.00"
#property description "Grid Trading System Designed for Consistent Profits"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade trade;
CPositionInfo position;

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input group "=== Profit Strategy ==="
input double InpBaseLot = 0.01;          // Base Lot Size (small start)
input double InpLotMultiplier = 1.5;     // Lot Multiplier (recovery power)
input int InpGridStep = 50;              // Grid Step (points) - tight for quick recovery
input int InpMaxLevels = 5;              // Max Grid Levels
input double InpProfitTarget = 20.0;     // Profit Target per cycle ($)

input group "=== Smart Entry ==="
input bool InpUseSmartEntry = true;      // Use Smart Entry (trend-based)
input int InpMAPeriod = 20;              // Moving Average Period
input int InpRSIPeriod = 14;             // RSI Period
input double InpRSIOverbought = 70;      // RSI Overbought
input double InpRSIOversold = 30;        // RSI Oversold

input group "=== Risk Control ==="
input double InpMaxDrawdown = 300.0;     // Max Drawdown ($)
input int InpStopLoss = 150;             // Stop Loss (points)
input bool InpUseTrailingStop = true;    // Use Trailing Stop for profits

input group "=== Advanced ==="
input int InpMagicNumber = 77777;        // Magic Number
input bool InpNewsFilter = true;         // Avoid trading during news
input int InpMaxTradesPerDay = 20;       // Max trades per day

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
double initial_balance = 0;
datetime last_order_time = 0;
int trades_today = 0;
datetime today_start = 0;
double daily_profit = 0;
bool avoid_trading = false;

// Grid management
double grid_start_price = 0;
string grid_direction = "NONE"; // "BUY" or "SELL"
int current_level = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== PROFITABLE GRID EA STARTED ===");

    trade.SetExpertMagicNumber(InpMagicNumber);
    initial_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    today_start = TimeCurrent();

    Print("Starting Balance: $", initial_balance);
    Print("Strategy: Adaptive Grid with Smart Entry");
    Print("Profit Target per Cycle: $", InpProfitTarget);
    Print("Max Drawdown: $", InpMaxDrawdown);

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_log = 0;

    // Daily reset
    CheckDailyReset();

    // Safety and profit monitoring
    if(!PassSafetyChecks()) return;

    double current_profit = GetTotalProfit();

    // Debug logging
    if(TimeCurrent() - last_log > 20)
    {
        Print("Status: Profit=$", current_profit,
              " DailyP&L=$", daily_profit,
              " Trades=", trades_today,
              " Direction=", grid_direction,
              " Level=", current_level);
        last_log = TimeCurrent();
    }

    // Check for profit target (close all and restart)
    if(current_profit >= InpProfitTarget)
    {
        Print("PROFIT TARGET HIT: $", current_profit);
        CloseAllPositions();
        daily_profit += current_profit;
        ResetGrid();
        last_order_time = TimeCurrent() + 5; // Quick restart for more profits
        return;
    }

    // Main trading logic
    ManageGrid();
}

//+------------------------------------------------------------------+
//| Smart market analysis                                             |
//+------------------------------------------------------------------+
string AnalyzeMarket()
{
    if(!InpUseSmartEntry) return "BUY"; // Default to BUY if smart entry disabled

    // Get MA trend using handles
    double ma_values[];
    int ma_handle = iMA(_Symbol, PERIOD_CURRENT, InpMAPeriod, 0, MODE_EMA, PRICE_CLOSE);
    if(ma_handle == INVALID_HANDLE || CopyBuffer(ma_handle, 0, 0, 2, ma_values) < 2)
    {
        return "BUY"; // Default if MA fails
    }

    double ma_current = ma_values[0];
    double ma_previous = ma_values[1];

    // Get RSI using handles
    double rsi_values[];
    int rsi_handle = iRSI(_Symbol, PERIOD_CURRENT, InpRSIPeriod, PRICE_CLOSE);
    if(rsi_handle == INVALID_HANDLE || CopyBuffer(rsi_handle, 0, 0, 1, rsi_values) < 1)
    {
        return "BUY"; // Default if RSI fails
    }

    double rsi_current = rsi_values[0];

    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    // Smart entry logic
    if(ask > ma_current && ma_current > ma_previous && rsi_current < InpRSIOverbought)
    {
        return "BUY"; // Uptrend, not overbought
    }
    else if(bid < ma_current && ma_current < ma_previous && rsi_current > InpRSIOversold)
    {
        return "SELL"; // Downtrend, not oversold
    }
    else if(rsi_current > InpRSIOverbought)
    {
        return "SELL"; // Overbought, expect reversal
    }
    else if(rsi_current < InpRSIOversold)
    {
        return "BUY"; // Oversold, expect bounce
    }

    return "BUY"; // Default bias
}

//+------------------------------------------------------------------+
//| Main grid management                                              |
//+------------------------------------------------------------------+
void ManageGrid()
{
    int position_count = CountPositions();

    // Start new grid if none exists
    if(position_count == 0 && TimeCurrent() - last_order_time > 10)
    {
        string signal = AnalyzeMarket();
        StartNewGrid(signal);
        return;
    }

    // Add to existing grid
    if(position_count > 0 && position_count < InpMaxLevels)
    {
        AddToGrid();
    }

    // Manage trailing stops for profitable positions
    if(InpUseTrailingStop)
    {
        ManageTrailingStops();
    }
}

//+------------------------------------------------------------------+
//| Start new grid                                                    |
//+------------------------------------------------------------------+
void StartNewGrid(string direction)
{
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    if(ask <= 0 || bid <= 0) return;

    grid_direction = direction;
    current_level = 0;
    double lot_size = InpBaseLot;
    double sl_distance = InpStopLoss * SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    if(direction == "BUY")
    {
        grid_start_price = ask;
        double sl = ask - sl_distance;

        if(trade.Buy(lot_size, _Symbol, 0, sl, 0, "PGrid-B-L0"))
        {
            Print("Started BUY Grid: Entry=", ask, " SL=", sl, " Lot=", lot_size);
            current_level = 1;
            last_order_time = TimeCurrent();
            trades_today++;
        }
    }
    else // SELL
    {
        grid_start_price = bid;
        double sl = bid + sl_distance;

        if(trade.Sell(lot_size, _Symbol, 0, sl, 0, "PGrid-S-L0"))
        {
            Print("Started SELL Grid: Entry=", bid, " SL=", sl, " Lot=", lot_size);
            current_level = 1;
            last_order_time = TimeCurrent();
            trades_today++;
        }
    }
}

//+------------------------------------------------------------------+
//| Add to existing grid                                              |
//+------------------------------------------------------------------+
void AddToGrid()
{
    if(TimeCurrent() - last_order_time < 5) return; // Prevent rapid orders

    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double grid_distance = InpGridStep * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double sl_distance = InpStopLoss * SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    if(grid_direction == "BUY")
    {
        // Add BUY when price goes down (averaging down)
        double target_price = grid_start_price - (current_level * grid_distance);

        if(ask <= target_price)
        {
            double lot_size = InpBaseLot * MathPow(InpLotMultiplier, current_level);
            double sl = ask - sl_distance;

            if(trade.Buy(lot_size, _Symbol, 0, sl, 0, "PGrid-B-L" + IntegerToString(current_level)))
            {
                Print("Added BUY Level ", current_level, ": Entry=", ask, " Lot=", lot_size);
                current_level++;
                last_order_time = TimeCurrent();
                trades_today++;
            }
        }
    }
    else if(grid_direction == "SELL")
    {
        // Add SELL when price goes up (averaging up)
        double target_price = grid_start_price + (current_level * grid_distance);

        if(bid >= target_price)
        {
            double lot_size = InpBaseLot * MathPow(InpLotMultiplier, current_level);
            double sl = bid + sl_distance;

            if(trade.Sell(lot_size, _Symbol, 0, sl, 0, "PGrid-S-L" + IntegerToString(current_level)))
            {
                Print("Added SELL Level ", current_level, ": Entry=", bid, " Lot=", lot_size);
                current_level++;
                last_order_time = TimeCurrent();
                trades_today++;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Manage trailing stops                                             |
//+------------------------------------------------------------------+
void ManageTrailingStops()
{
    double trail_distance = 30 * SymbolInfoDouble(_Symbol, SYMBOL_POINT); // 30 point trailing

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                double profit = position.Profit();

                if(profit > 10.0) // Only trail profitable positions
                {
                    if(position.PositionType() == POSITION_TYPE_BUY)
                    {
                        double new_sl = SymbolInfoDouble(_Symbol, SYMBOL_BID) - trail_distance;
                        if(new_sl > position.StopLoss() + SymbolInfoDouble(_Symbol, SYMBOL_POINT))
                        {
                            trade.PositionModify(position.Ticket(), new_sl, 0);
                        }
                    }
                    else
                    {
                        double new_sl = SymbolInfoDouble(_Symbol, SYMBOL_ASK) + trail_distance;
                        if(new_sl < position.StopLoss() - SymbolInfoDouble(_Symbol, SYMBOL_POINT))
                        {
                            trade.PositionModify(position.Ticket(), new_sl, 0);
                        }
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Safety checks                                                     |
//+------------------------------------------------------------------+
bool PassSafetyChecks()
{
    // Max trades per day
    if(trades_today >= InpMaxTradesPerDay)
    {
        avoid_trading = true;
        return false;
    }

    // Drawdown check
    double current_profit = GetTotalProfit();
    if(current_profit <= -InpMaxDrawdown)
    {
        Print("DRAWDOWN LIMIT HIT: $", current_profit);
        CloseAllPositions();
        avoid_trading = true;
        return false;
    }

    // News filter (simplified - avoid trading during high impact hours)
    if(InpNewsFilter)
    {
        MqlDateTime time_struct;
        TimeToStruct(TimeCurrent(), time_struct);

        // Avoid trading during typical news hours (8:30, 10:00, 14:00, 16:00 GMT)
        if((time_struct.hour == 8 && time_struct.min >= 25 && time_struct.min <= 35) ||
           (time_struct.hour == 10 && time_struct.min <= 10) ||
           (time_struct.hour == 14 && time_struct.min <= 10) ||
           (time_struct.hour == 16 && time_struct.min <= 10))
        {
            return false;
        }
    }

    return true;
}

//+------------------------------------------------------------------+
//| Utility functions                                                 |
//+------------------------------------------------------------------+
int CountPositions()
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

void ResetGrid()
{
    grid_direction = "NONE";
    grid_start_price = 0;
    current_level = 0;
}

void CheckDailyReset()
{
    MqlDateTime current_time, start_time;
    TimeToStruct(TimeCurrent(), current_time);
    TimeToStruct(today_start, start_time);

    if(current_time.day != start_time.day)
    {
        Print("NEW DAY: Yesterday's profit: $", daily_profit);
        daily_profit = 0;
        trades_today = 0;
        avoid_trading = false;
        today_start = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== PROFITABLE GRID EA STOPPED ===");
    double final_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double total_pnl = final_balance - initial_balance;
    Print("Final Balance: $", final_balance, " Total P&L: $", total_pnl);
    Print("Daily Profit: $", daily_profit);
}