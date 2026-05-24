//+------------------------------------------------------------------+
//|                                       HighPerformanceGridEA.mq5 |
//|                          High Performance Grid Trading System   |
//|                                  Optimized for Maximum Returns  |
//+------------------------------------------------------------------+
#property copyright "High Performance Grid EA"
#property link      ""
#property version   "1.00"
#property description "High Performance Grid Trading - Maximum Annual Returns"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade trade;
CPositionInfo position;

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input group "=== Performance Settings ==="
input int InpMagicNumber = 77777;        // Magic Number
input double InpStartLot = 0.01;         // Starting Lot Size
input double InpAccountGrowthRate = 2.0; // Account Growth Multiplier (% per month)
input double InpProfitAccelerator = 1.5; // Profit Acceleration Factor

input group "=== Grid Settings ==="
input int InpGridStep = 50;              // Grid Step (points) - Tighter for more trades
input int InpMaxLevels = 8;              // Max Grid Levels (controlled risk)
input double InpQuickProfitTarget = 15.0; // Quick Profit Target ($)
input double InpGridProfitTarget = 50.0; // Grid Cycle Profit Target ($)

input group "=== Dynamic Risk Management ==="
input double InpMaxRiskPercent = 5.0;    // Max Risk per Grid Cycle (%)
input double InpDailyProfitTarget = 200.0; // Daily Profit Target ($)
input double InpMaxDailyDrawdown = 500.0; // Max Daily Drawdown ($)
input bool InpCompoundGrowth = true;      // Enable Compound Growth

input group "=== Trend Optimization ==="
input bool InpUseTrendBoost = true;      // Use Trend Boost for faster profits
input int InpTrendPeriod = 21;           // Trend Period for boost
input double InpTrendBoostMultiplier = 2.0; // Trend Boost Multiplier

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
double initial_balance = 0;
double daily_start_balance = 0;
double current_lot_size = 0;
datetime last_order_time = 0;
datetime today_start = 0;
double daily_profit = 0;
int trades_today = 0;

// Performance tracking
double monthly_start_balance = 0;
datetime month_start = 0;
double total_profit_this_month = 0;

// Grid management
struct GridPosition
{
    double price;
    bool is_buy;
    bool is_filled;
    ulong ticket;
    double lot_size;
    datetime time;
};

GridPosition grid_positions[50];
int grid_count = 0;
double grid_start_price = 0;
string grid_direction = "NONE";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== HIGH PERFORMANCE GRID EA STARTED ===");

    trade.SetExpertMagicNumber(InpMagicNumber);
    initial_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    daily_start_balance = initial_balance;
    monthly_start_balance = initial_balance;
    today_start = TimeCurrent();
    month_start = TimeCurrent();

    current_lot_size = InpStartLot;

    Print("Starting Balance: $", initial_balance);
    Print("Target Annual Return: 200%+");
    Print("Daily Profit Target: $", InpDailyProfitTarget);
    Print("Starting Lot Size: ", current_lot_size);
    Print("Compound Growth: ", (InpCompoundGrowth ? "ENABLED" : "DISABLED"));

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_log = 0;

    // Daily and monthly reset
    CheckDailyReset();
    CheckMonthlyReset();

    // Dynamic lot sizing based on account growth
    UpdateLotSize();

    // Safety checks
    if(!PassSafetyChecks()) return;

    // Debug logging
    if(TimeCurrent() - last_log > 30)
    {
        double current_profit = GetTotalProfit();
        double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        double daily_pnl = account_balance - daily_start_balance;
        double monthly_pnl = account_balance - monthly_start_balance;

        Print("Performance: Balance=$", account_balance,
              " Daily=$", daily_pnl,
              " Monthly=$", monthly_pnl,
              " CurrentLot=", current_lot_size,
              " GridProfit=$", current_profit);
        last_log = TimeCurrent();
    }

    // Check for quick profits
    if(CheckQuickProfit()) return;

    // Check for grid cycle completion
    if(CheckGridCycleProfit()) return;

    // Main grid trading logic
    ManageHighPerformanceGrid();
}

//+------------------------------------------------------------------+
//| High Performance Grid Management                                 |
//+------------------------------------------------------------------+
void ManageHighPerformanceGrid()
{
    int active_positions = CountActivePositions();

    // Start new grid if none exists
    if(active_positions == 0 && TimeCurrent() - last_order_time > 5)
    {
        StartNewGrid();
        return;
    }

    // Add to existing grid with trend boost
    if(active_positions > 0 && active_positions < InpMaxLevels)
    {
        AddToGridWithBoost();
    }
}

//+------------------------------------------------------------------+
//| Start new high-performance grid                                  |
//+------------------------------------------------------------------+
void StartNewGrid()
{
    double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

    if(ask <= 0 || current_price <= 0) return;

    // Analyze trend for direction
    string trend = AnalyzeTrend();
    bool use_buy = (trend == "UP" || trend == "SIDEWAYS");

    grid_direction = use_buy ? "BUY" : "SELL";
    grid_start_price = use_buy ? ask : current_price;
    grid_count = 0;

    // Calculate dynamic lot size
    double lot_size = CalculateOptimalLotSize();

    if(use_buy)
    {
        if(trade.Buy(lot_size, _Symbol, 0, 0, 0, "HPGrid-B0"))
        {
            AddToGridArray(ask, true, lot_size, trade.ResultOrder());
            Print("Started HIGH PERFORMANCE BUY Grid: Entry=", ask, " Lot=", lot_size);
        }
    }
    else
    {
        if(trade.Sell(lot_size, _Symbol, 0, 0, 0, "HPGrid-S0"))
        {
            AddToGridArray(current_price, false, lot_size, trade.ResultOrder());
            Print("Started HIGH PERFORMANCE SELL Grid: Entry=", current_price, " Lot=", lot_size);
        }
    }

    last_order_time = TimeCurrent();
    trades_today++;
}

//+------------------------------------------------------------------+
//| Add to grid with trend boost                                     |
//+------------------------------------------------------------------+
void AddToGridWithBoost()
{
    if(TimeCurrent() - last_order_time < 3) return; // Prevent rapid orders

    double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double grid_distance = InpGridStep * SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    // Dynamic grid distance based on trend
    if(InpUseTrendBoost)
    {
        string trend = AnalyzeTrend();
        if(trend == "STRONG_UP" || trend == "STRONG_DOWN")
        {
            grid_distance *= 0.7; // Tighter grid in strong trends
        }
    }

    if(grid_direction == "BUY")
    {
        // Add BUY when price goes down
        double last_buy_price = GetLastGridPrice(true);
        if(last_buy_price > 0 && ask <= (last_buy_price - grid_distance))
        {
            double lot_size = CalculateOptimalLotSize();

            if(trade.Buy(lot_size, _Symbol, 0, 0, 0, "HPGrid-B" + IntegerToString(grid_count)))
            {
                AddToGridArray(ask, true, lot_size, trade.ResultOrder());
                Print("Added BUY Level ", grid_count, ": Entry=", ask, " Lot=", lot_size);
                last_order_time = TimeCurrent();
                trades_today++;
            }
        }
    }
    else if(grid_direction == "SELL")
    {
        // Add SELL when price goes up
        double last_sell_price = GetLastGridPrice(false);
        if(last_sell_price > 0 && current_price >= (last_sell_price + grid_distance))
        {
            double lot_size = CalculateOptimalLotSize();

            if(trade.Sell(lot_size, _Symbol, 0, 0, 0, "HPGrid-S" + IntegerToString(grid_count)))
            {
                AddToGridArray(current_price, false, lot_size, trade.ResultOrder());
                Print("Added SELL Level ", grid_count, ": Entry=", current_price, " Lot=", lot_size);
                last_order_time = TimeCurrent();
                trades_today++;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate optimal lot size for maximum performance              |
//+------------------------------------------------------------------+
double CalculateOptimalLotSize()
{
    double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);

    if(InpCompoundGrowth)
    {
        // Compound growth: increase lot size with account growth
        double growth_factor = account_balance / initial_balance;
        current_lot_size = InpStartLot * growth_factor;
    }
    else
    {
        current_lot_size = InpStartLot;
    }

    // Apply trend boost multiplier
    if(InpUseTrendBoost)
    {
        string trend = AnalyzeTrend();
        if(trend == "STRONG_UP" || trend == "STRONG_DOWN")
        {
            current_lot_size *= InpTrendBoostMultiplier;
        }
    }

    // Ensure minimum lot size
    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    if(min_lot > 0)
    {
        current_lot_size = MathMax(current_lot_size, min_lot);
    }
    else
    {
        current_lot_size = MathMax(current_lot_size, 0.01);
    }

    // Apply risk management
    double max_lot = (account_balance * InpMaxRiskPercent / 100.0) / (InpGridStep * 10); // Simplified risk calc
    current_lot_size = MathMin(current_lot_size, max_lot);

    return NormalizeDouble(current_lot_size, 2);
}

//+------------------------------------------------------------------+
//| Analyze trend for optimal entry                                  |
//+------------------------------------------------------------------+
string AnalyzeTrend()
{
    double ma_values[];
    int ma_handle = iMA(_Symbol, PERIOD_CURRENT, InpTrendPeriod, 0, MODE_EMA, PRICE_CLOSE);

    if(ma_handle == INVALID_HANDLE || CopyBuffer(ma_handle, 0, 0, 3, ma_values) < 3)
    {
        return "SIDEWAYS";
    }

    double ma_current = ma_values[0];
    double ma_previous = ma_values[1];
    double ma_older = ma_values[2];
    double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    double trend_strength = MathAbs(current_price - ma_current) / SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    if(current_price > ma_current && ma_current > ma_previous && ma_previous > ma_older)
    {
        return (trend_strength > 100) ? "STRONG_UP" : "UP";
    }
    else if(current_price < ma_current && ma_current < ma_previous && ma_previous < ma_older)
    {
        return (trend_strength > 100) ? "STRONG_DOWN" : "DOWN";
    }

    return "SIDEWAYS";
}

//+------------------------------------------------------------------+
//| Check for quick profits                                          |
//+------------------------------------------------------------------+
bool CheckQuickProfit()
{
    double total_profit = GetTotalProfit();

    if(total_profit >= InpQuickProfitTarget)
    {
        Print("QUICK PROFIT TARGET HIT: $", total_profit);
        CloseAllPositions();
        ResetGrid();
        last_order_time = TimeCurrent() + 2; // Quick restart for more profits
        daily_profit += total_profit;
        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| Check for grid cycle completion                                  |
//+------------------------------------------------------------------+
bool CheckGridCycleProfit()
{
    double total_profit = GetTotalProfit();

    if(total_profit >= InpGridProfitTarget)
    {
        Print("GRID CYCLE COMPLETE: $", total_profit);
        CloseAllPositions();
        ResetGrid();
        last_order_time = TimeCurrent() + 10; // Brief pause before next cycle
        daily_profit += total_profit;
        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| Safety checks for high performance                               |
//+------------------------------------------------------------------+
bool PassSafetyChecks()
{
    // Daily profit target reached - pause to secure profits
    double daily_pnl = AccountInfoDouble(ACCOUNT_BALANCE) - daily_start_balance;
    if(daily_pnl >= InpDailyProfitTarget)
    {
        Print("DAILY PROFIT TARGET ACHIEVED: $", daily_pnl, " - Securing profits");
        return false;
    }

    // Daily drawdown limit
    if(daily_pnl <= -InpMaxDailyDrawdown)
    {
        Print("DAILY DRAWDOWN LIMIT: $", daily_pnl);
        CloseAllPositions();
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Update lot size for compound growth                              |
//+------------------------------------------------------------------+
void UpdateLotSize()
{
    if(InpCompoundGrowth)
    {
        double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        double monthly_growth = (account_balance - monthly_start_balance) / monthly_start_balance * 100;

        if(monthly_growth >= InpAccountGrowthRate)
        {
            current_lot_size = InpStartLot * (account_balance / initial_balance);
            Print("LOT SIZE INCREASED: New lot=", current_lot_size, " Monthly growth=", monthly_growth, "%");
        }
    }
}

//+------------------------------------------------------------------+
//| Utility Functions                                                |
//+------------------------------------------------------------------+
void AddToGridArray(double price, bool is_buy, double lot_size, ulong ticket)
{
    grid_positions[grid_count].price = price;
    grid_positions[grid_count].is_buy = is_buy;
    grid_positions[grid_count].is_filled = true;
    grid_positions[grid_count].ticket = ticket;
    grid_positions[grid_count].lot_size = lot_size;
    grid_positions[grid_count].time = TimeCurrent();
    grid_count++;
}

double GetLastGridPrice(bool is_buy)
{
    double last_price = 0;
    for(int i = grid_count - 1; i >= 0; i--)
    {
        if(grid_positions[i].is_buy == is_buy && grid_positions[i].is_filled)
        {
            last_price = grid_positions[i].price;
            break;
        }
    }
    return last_price;
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

void ResetGrid()
{
    grid_direction = "NONE";
    grid_start_price = 0;
    grid_count = 0;

    for(int i = 0; i < 50; i++)
    {
        grid_positions[i].is_filled = false;
        grid_positions[i].ticket = 0;
    }
}

void CheckDailyReset()
{
    MqlDateTime current_time, start_time;
    TimeToStruct(TimeCurrent(), current_time);
    TimeToStruct(today_start, start_time);

    if(current_time.day != start_time.day)
    {
        double daily_pnl = AccountInfoDouble(ACCOUNT_BALANCE) - daily_start_balance;
        Print("DAILY PERFORMANCE: $", daily_pnl, " (",
              NormalizeDouble(daily_pnl/daily_start_balance*100, 2), "%)");

        daily_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        today_start = TimeCurrent();
        trades_today = 0;
        daily_profit = 0;
    }
}

void CheckMonthlyReset()
{
    MqlDateTime current_time, start_time;
    TimeToStruct(TimeCurrent(), current_time);
    TimeToStruct(month_start, start_time);

    if(current_time.mon != start_time.mon)
    {
        double monthly_pnl = AccountInfoDouble(ACCOUNT_BALANCE) - monthly_start_balance;
        Print("MONTHLY PERFORMANCE: $", monthly_pnl, " (",
              NormalizeDouble(monthly_pnl/monthly_start_balance*100, 2), "%)");

        monthly_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        month_start = TimeCurrent();
        total_profit_this_month = 0;
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== HIGH PERFORMANCE GRID EA STOPPED ===");
    double final_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double total_pnl = final_balance - initial_balance;
    double annual_return = (total_pnl / initial_balance) * 100;

    Print("Final Balance: $", final_balance);
    Print("Total P&L: $", total_pnl);
    Print("Return: ", annual_return, "%");
    Print("Target: 200%+ Annual Return");
}