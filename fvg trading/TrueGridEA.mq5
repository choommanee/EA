//+------------------------------------------------------------------+
//|                                                TrueGridEA.mq5   |
//|                                Real Grid Trading Strategy       |
//|                          Based on Axiory Grid Trading Principles|
//+------------------------------------------------------------------+
#property copyright "True Grid EA"
#property link      ""
#property version   "1.00"
#property description "True Grid Trading - Buy Low, Sell High Strategy"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>

CTrade trade;
CPositionInfo position;
COrderInfo order;

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input group "=== Grid Settings ==="
input int InpMagicNumber = 12345;        // Magic Number
input double InpLotSize = 0.01;          // Lot Size (fixed, no martingale)
input int InpGridStep = 100;             // Grid Step (points)
input int InpGridLevels = 5;             // Grid Levels (each side)
input double InpTakeProfit = 50;         // Take Profit (points)

input group "=== Range Settings ==="
input double InpCenterPrice = 0;         // Center Price (0 = auto-detect)
input double InpRangeSize = 500;         // Total Range Size (points)
input bool InpAutoRange = true;          // Auto-detect Range

input group "=== Risk Management ==="
input double InpMaxSpread = 3.0;         // Max Spread (points)
input bool InpAvoidNews = true;          // Avoid News Hours
input double InpMaxDailyLoss = 100.0;    // Max Daily Loss ($)
input double InpMaxGridLoss = 50.0;      // Max Loss per Grid ($)

input group "=== Trend Protection ==="
input bool InpUseTrendFilter = true;     // Use Trend Filter
input int InpTrendPeriod = 50;           // Trend MA Period
input double InpMaxTrendStrength = 200;  // Max Trend Strength (points)
input int InpMaxLevelsInTrend = 3;       // Max Levels against strong trend

input group "=== Hedge Settings ==="
input bool InpEnableHedge = true;        // Enable Hedge Trading
input double InpHedgePercent = 50.0;     // Hedge Size (% of grid position)
input int InpHedgeTrendPeriod = 20;      // Hedge Trend Period
input double InpHedgeExitThreshold = 30; // Hedge Exit Threshold (points)

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
double grid_center_price = 0;
double grid_upper_bound = 0;
double grid_lower_bound = 0;
bool grid_initialized = false;
datetime last_order_time = 0;
datetime today_start = 0;
double daily_start_balance = 0;

struct GridOrder
{
    double price;
    bool is_buy;
    bool is_filled;
    ulong ticket;
    datetime time;
};

GridOrder buy_grid[20];
GridOrder sell_grid[20];
int buy_count = 0;
int sell_count = 0;

// Hedge variables
struct HedgePosition
{
    ulong ticket;
    bool is_buy;
    double lot_size;
    double entry_price;
    datetime entry_time;
    bool is_active;
};

HedgePosition hedge_positions[50];
int hedge_count = 0;
double total_grid_volume_buy = 0;
double total_grid_volume_sell = 0;
double actual_lot_size = 0; // Adjusted lot size for symbol

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== TRUE GRID TRADING EA STARTED ===");

    trade.SetExpertMagicNumber(InpMagicNumber);
    today_start = TimeCurrent();
    daily_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);

    // Validate and adjust lot size
    if(!ValidateLotSize())
    {
        Print("ERROR: Cannot adjust lot size to symbol requirements");
        return INIT_PARAMETERS_INCORRECT;
    }

    Print("Grid Strategy: Buy Low, Sell High");
    Print("Grid Step: ", InpGridStep, " points");
    Print("Grid Levels: ", InpGridLevels, " each side");
    Print("Input Lot Size: ", InpLotSize);
    Print("Actual Lot Size: ", actual_lot_size, " (adjusted for symbol)");
    Print("Take Profit: ", InpTakeProfit, " points");

    // Initialize grid
    if(InpAutoRange)
    {
        DetectTradingRange();
    }
    else
    {
        if(InpCenterPrice > 0)
        {
            grid_center_price = InpCenterPrice;
        }
        else
        {
            grid_center_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
        }
    }

    SetupGrid();

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Validate and adjust lot size                                     |
//+------------------------------------------------------------------+
bool ValidateLotSize()
{
    double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

    Print("Symbol: ", _Symbol);
    Print("Min Lot: ", min_lot, " Max Lot: ", max_lot, " Lot Step: ", lot_step);

    // Force use input lot size regardless of symbol requirements
    actual_lot_size = InpLotSize;

    Print("Using FORCED lot size: ", actual_lot_size, " (ignoring symbol minimum)");
    Print("WARNING: This may cause trading errors if broker rejects the lot size");

    return true;
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_log = 0;

    // Daily reset
    CheckDailyReset();

    // Safety checks
    if(!PassSafetyChecks()) return;

    // No need for UpdateGridOrders() - CheckProfitTaking() handles this

    // Debug logging
    if(TimeCurrent() - last_log > 30)
    {
        double current_profit = GetTotalProfit();
        Print("Grid Status: Center=", grid_center_price,
              " Current=", SymbolInfoDouble(_Symbol, SYMBOL_BID),
              " Profit=$", current_profit,
              " ActiveOrders=", CountActiveOrders());
        last_log = TimeCurrent();
    }

    // Check grid loss limit
    if(CheckGridLossLimit())
    {
        Print("Grid loss limit exceeded - closing all positions");
        CloseAllPositions();
        ResetAllGrids();
        last_order_time = TimeCurrent() + 300; // Wait 5 minutes
        return;
    }

    // Main grid management
    ManageGrid();

    // Hedge management
    if(InpEnableHedge)
    {
        ManageHedge();
        CheckHedgeExit();
    }

    // Check for profit taking (manual TP)
    CheckProfitTaking();
}

//+------------------------------------------------------------------+
//| Detect trading range automatically                               |
//+------------------------------------------------------------------+
void DetectTradingRange()
{
    // Use recent high/low to determine range
    double high = 0, low = 999999;

    for(int i = 1; i <= 100; i++) // Look at last 100 bars
    {
        double bar_high = iHigh(_Symbol, PERIOD_H1, i);
        double bar_low = iLow(_Symbol, PERIOD_H1, i);

        if(bar_high > high) high = bar_high;
        if(bar_low < low) low = bar_low;
    }

    grid_center_price = (high + low) / 2;
    double range = high - low;

    grid_upper_bound = grid_center_price + (range * 0.4);
    grid_lower_bound = grid_center_price - (range * 0.4);

    Print("Auto-detected Range: Center=", grid_center_price,
          " Upper=", grid_upper_bound,
          " Lower=", grid_lower_bound);
}

//+------------------------------------------------------------------+
//| Setup grid orders                                                |
//+------------------------------------------------------------------+
void SetupGrid()
{
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double grid_step = InpGridStep * point;

    buy_count = 0;
    sell_count = 0;

    // Setup BUY grid (below center price)
    for(int i = 1; i <= InpGridLevels; i++)
    {
        buy_grid[buy_count].price = grid_center_price - (i * grid_step);
        buy_grid[buy_count].is_buy = true;
        buy_grid[buy_count].is_filled = false;
        buy_grid[buy_count].ticket = 0;
        buy_count++;
    }

    // Setup SELL grid (above center price)
    for(int i = 1; i <= InpGridLevels; i++)
    {
        sell_grid[sell_count].price = grid_center_price + (i * grid_step);
        sell_grid[sell_count].is_buy = false;
        sell_grid[sell_count].is_filled = false;
        sell_grid[sell_count].ticket = 0;
        sell_count++;
    }

    grid_initialized = true;
    Print("Grid initialized with ", buy_count, " BUY levels and ", sell_count, " SELL levels");
}

//+------------------------------------------------------------------+
//| Manage grid trading                                               |
//+------------------------------------------------------------------+
void ManageGrid()
{
    if(!grid_initialized) return;

    double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double current_ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

    // Analyze trend before placing orders
    string trend_direction = "SIDEWAYS";
    double trend_strength = 0;

    if(InpUseTrendFilter)
    {
        AnalyzeTrend(trend_direction, trend_strength);
    }

    // Check BUY opportunities (when price is LOW)
    for(int i = 0; i < buy_count; i++)
    {
        if(!buy_grid[i].is_filled && current_ask <= buy_grid[i].price)
        {
            if(TimeCurrent() - last_order_time > 5) // Prevent rapid orders
            {
                // Check trend protection
                if(ShouldPlaceBuyOrder(trend_direction, trend_strength, i))
                {
                    PlaceBuyOrder(i);
                }
                else
                {
                    Print("BUY order blocked by trend filter: Direction=", trend_direction, " Strength=", trend_strength);
                }
            }
        }
    }

    // Check SELL opportunities (when price is HIGH)
    for(int i = 0; i < sell_count; i++)
    {
        if(!sell_grid[i].is_filled && current_price >= sell_grid[i].price)
        {
            if(TimeCurrent() - last_order_time > 5) // Prevent rapid orders
            {
                // Check trend protection
                if(ShouldPlaceSellOrder(trend_direction, trend_strength, i))
                {
                    PlaceSellOrder(i);
                }
                else
                {
                    Print("SELL order blocked by trend filter: Direction=", trend_direction, " Strength=", trend_strength);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Place BUY order                                                   |
//+------------------------------------------------------------------+
void PlaceBuyOrder(int index)
{
    string comment = "Grid-Buy-" + IntegerToString(index);

    // Place BUY order without TP (manual monitoring)
    if(trade.Buy(actual_lot_size, _Symbol, 0, 0, 0, comment))
    {
        buy_grid[index].is_filled = true;
        buy_grid[index].ticket = trade.ResultOrder();
        buy_grid[index].time = TimeCurrent();
        last_order_time = TimeCurrent();

        // Update grid volume for hedge calculation
        total_grid_volume_buy += actual_lot_size;

        Print("BUY order placed at level ", index,
              " Entry=", buy_grid[index].price,
              " Ticket=", buy_grid[index].ticket,
              " (Manual TP monitoring)");

        // Check if hedge is needed
        if(InpEnableHedge)
        {
            CheckHedgeOpportunity();
        }
    }
    else
    {
        Print("Failed to place BUY order: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Place SELL order                                                  |
//+------------------------------------------------------------------+
void PlaceSellOrder(int index)
{
    string comment = "Grid-Sell-" + IntegerToString(index);

    // Place SELL order without TP (manual monitoring)
    if(trade.Sell(actual_lot_size, _Symbol, 0, 0, 0, comment))
    {
        sell_grid[index].is_filled = true;
        sell_grid[index].ticket = trade.ResultOrder();
        sell_grid[index].time = TimeCurrent();
        last_order_time = TimeCurrent();

        // Update grid volume for hedge calculation
        total_grid_volume_sell += actual_lot_size;

        Print("SELL order placed at level ", index,
              " Entry=", sell_grid[index].price,
              " Ticket=", sell_grid[index].ticket,
              " (Manual TP monitoring)");

        // Check if hedge is needed
        if(InpEnableHedge)
        {
            CheckHedgeOpportunity();
        }
    }
    else
    {
        Print("Failed to place SELL order: ", trade.ResultRetcodeDescription());
    }
}

// UpdateGridOrders() function removed - replaced by CheckProfitTaking()

//+------------------------------------------------------------------+
//| Safety checks                                                     |
//+------------------------------------------------------------------+
bool PassSafetyChecks()
{
    // Spread check
    double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    if(spread > InpMaxSpread * SymbolInfoDouble(_Symbol, SYMBOL_POINT))
    {
        return false;
    }

    // Daily loss check
    double daily_pnl = AccountInfoDouble(ACCOUNT_BALANCE) - daily_start_balance;
    if(daily_pnl <= -InpMaxDailyLoss)
    {
        Print("Daily loss limit reached: $", daily_pnl);
        CloseAllPositions();
        return false;
    }

    // News hours check (simplified)
    if(InpAvoidNews)
    {
        MqlDateTime time_struct;
        TimeToStruct(TimeCurrent(), time_struct);

        // Avoid trading during major news hours (8:30, 10:00, 14:00 GMT)
        if((time_struct.hour == 8 && time_struct.min >= 25 && time_struct.min <= 35) ||
           (time_struct.hour == 10 && time_struct.min <= 10) ||
           (time_struct.hour == 14 && time_struct.min <= 10))
        {
            return false;
        }
    }

    return true;
}

//+------------------------------------------------------------------+
//| Utility functions                                                 |
//+------------------------------------------------------------------+
int CountActiveOrders()
{
    int count = 0;

    for(int i = 0; i < buy_count; i++)
    {
        if(buy_grid[i].is_filled) count++;
    }

    for(int i = 0; i < sell_count; i++)
    {
        if(sell_grid[i].is_filled) count++;
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
    // Close all hedges first
    if(InpEnableHedge)
    {
        CloseAllHedges();
    }

    // Close all grid positions
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

void CheckDailyReset()
{
    MqlDateTime current_time, start_time;
    TimeToStruct(TimeCurrent(), current_time);
    TimeToStruct(today_start, start_time);

    if(current_time.day != start_time.day)
    {
        daily_start_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        today_start = TimeCurrent();
        Print("New trading day started");
    }
}

//+------------------------------------------------------------------+
//| Check profit taking manually                                     |
//+------------------------------------------------------------------+
void CheckProfitTaking()
{
    double tp_points = InpTakeProfit * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double current_ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double current_bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    // Check BUY positions for profit taking
    for(int i = 0; i < buy_count; i++)
    {
        if(buy_grid[i].is_filled && buy_grid[i].ticket > 0)
        {
            if(position.SelectByTicket(buy_grid[i].ticket))
            {
                // Check if BUY position reached profit target
                double entry_price = position.PriceOpen();
                double target_price = entry_price + tp_points;

                if(current_bid >= target_price) // Can close at bid price
                {
                    if(trade.PositionClose(buy_grid[i].ticket))
                    {
                        double profit = position.Profit() + position.Swap() + position.Commission();
                        Print("BUY position closed with profit: Ticket=", buy_grid[i].ticket,
                              " Entry=", entry_price,
                              " Exit=", current_bid,
                              " Profit=$", profit);

                        // Reset grid level for new order
                        buy_grid[i].is_filled = false;
                        buy_grid[i].ticket = 0;

                        // Update grid volumes
                        total_grid_volume_buy -= actual_lot_size;
                    }
                }
            }
            else
            {
                // Position not found (already closed)
                buy_grid[i].is_filled = false;
                buy_grid[i].ticket = 0;
                total_grid_volume_buy -= actual_lot_size;
            }
        }
    }

    // Check SELL positions for profit taking
    for(int i = 0; i < sell_count; i++)
    {
        if(sell_grid[i].is_filled && sell_grid[i].ticket > 0)
        {
            if(position.SelectByTicket(sell_grid[i].ticket))
            {
                // Check if SELL position reached profit target
                double entry_price = position.PriceOpen();
                double target_price = entry_price - tp_points;

                if(current_ask <= target_price) // Can close at ask price
                {
                    if(trade.PositionClose(sell_grid[i].ticket))
                    {
                        double profit = position.Profit() + position.Swap() + position.Commission();
                        Print("SELL position closed with profit: Ticket=", sell_grid[i].ticket,
                              " Entry=", entry_price,
                              " Exit=", current_ask,
                              " Profit=$", profit);

                        // Reset grid level for new order
                        sell_grid[i].is_filled = false;
                        sell_grid[i].ticket = 0;

                        // Update grid volumes
                        total_grid_volume_sell -= actual_lot_size;
                    }
                }
            }
            else
            {
                // Position not found (already closed)
                sell_grid[i].is_filled = false;
                sell_grid[i].ticket = 0;
                total_grid_volume_sell -= actual_lot_size;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Analyze market trend                                              |
//+------------------------------------------------------------------+
void AnalyzeTrend(string &direction, double &strength)
{
    double ma_values[];
    int ma_handle = iMA(_Symbol, PERIOD_CURRENT, InpTrendPeriod, 0, MODE_EMA, PRICE_CLOSE);

    if(ma_handle != INVALID_HANDLE && CopyBuffer(ma_handle, 0, 0, 2, ma_values) >= 2)
    {
        double ma_current = ma_values[0];
        double ma_previous = ma_values[1];
        double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);

        // Calculate trend strength
        strength = MathAbs(current_price - ma_current) / SymbolInfoDouble(_Symbol, SYMBOL_POINT);

        // Determine trend direction
        if(current_price > ma_current && ma_current > ma_previous)
        {
            direction = "UP";
        }
        else if(current_price < ma_current && ma_current < ma_previous)
        {
            direction = "DOWN";
        }
        else
        {
            direction = "SIDEWAYS";
        }
    }
    else
    {
        direction = "SIDEWAYS";
        strength = 0;
    }
}

//+------------------------------------------------------------------+
//| Check if should place BUY order                                  |
//+------------------------------------------------------------------+
bool ShouldPlaceBuyOrder(string trend_direction, double trend_strength, int level)
{
    // Always allow first level
    if(level == 0) return true;

    // In strong downtrend, be very careful with BUY orders
    if(trend_direction == "DOWN" && trend_strength > InpMaxTrendStrength)
    {
        if(level >= InpMaxLevelsInTrend)
        {
            Print("BUY blocked: Strong downtrend (", trend_strength, " points), level ", level);
            return false;
        }
    }

    // In strong uptrend, BUY orders are safer
    if(trend_direction == "UP") return true;

    // In sideways market, allow all orders
    if(trend_direction == "SIDEWAYS") return true;

    return true;
}

//+------------------------------------------------------------------+
//| Check if should place SELL order                                 |
//+------------------------------------------------------------------+
bool ShouldPlaceSellOrder(string trend_direction, double trend_strength, int level)
{
    // Always allow first level
    if(level == 0) return true;

    // In strong uptrend, be very careful with SELL orders
    if(trend_direction == "UP" && trend_strength > InpMaxTrendStrength)
    {
        if(level >= InpMaxLevelsInTrend)
        {
            Print("SELL blocked: Strong uptrend (", trend_strength, " points), level ", level);
            return false;
        }
    }

    // In strong downtrend, SELL orders are safer
    if(trend_direction == "DOWN") return true;

    // In sideways market, allow all orders
    if(trend_direction == "SIDEWAYS") return true;

    return true;
}

//+------------------------------------------------------------------+
//| Check grid loss limit                                             |
//+------------------------------------------------------------------+
bool CheckGridLossLimit()
{
    double total_loss = GetTotalProfit();

    if(total_loss <= -InpMaxGridLoss)
    {
        Print("Grid loss limit exceeded: $", total_loss, " (Limit: $", -InpMaxGridLoss, ")");
        return true;
    }

    return false;
}

//+------------------------------------------------------------------+
//| Reset all grids                                                   |
//+------------------------------------------------------------------+
void ResetAllGrids()
{
    // Reset BUY grid
    for(int i = 0; i < buy_count; i++)
    {
        buy_grid[i].is_filled = false;
        buy_grid[i].ticket = 0;
    }

    // Reset SELL grid
    for(int i = 0; i < sell_count; i++)
    {
        sell_grid[i].is_filled = false;
        sell_grid[i].ticket = 0;
    }

    // Reset hedge positions
    for(int i = 0; i < hedge_count; i++)
    {
        hedge_positions[i].is_active = false;
        hedge_positions[i].ticket = 0;
    }
    hedge_count = 0;

    // Reset volumes
    total_grid_volume_buy = 0;
    total_grid_volume_sell = 0;

    Print("All grids and hedges reset");
}

//+------------------------------------------------------------------+
//| Hedge Management Functions                                        |
//+------------------------------------------------------------------+
void CheckHedgeOpportunity()
{
    double net_volume = total_grid_volume_buy - total_grid_volume_sell;
    double abs_net_volume = MathAbs(net_volume);

    // Only hedge if net exposure is significant
    if(abs_net_volume >= actual_lot_size * 2) // At least 2 lots net exposure
    {
        double hedge_volume = abs_net_volume * (InpHedgePercent / 100.0);

        // Round to proper lot size
        double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
        double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
        hedge_volume = MathMax(hedge_volume, min_lot);
        hedge_volume = NormalizeDouble(hedge_volume / lot_step, 0) * lot_step;

        // Place hedge in opposite direction
        if(net_volume > 0) // Net BUY exposure, hedge with SELL
        {
            PlaceHedge(false, hedge_volume);
        }
        else // Net SELL exposure, hedge with BUY
        {
            PlaceHedge(true, hedge_volume);
        }
    }
}

void PlaceHedge(bool is_buy, double volume)
{
    string comment = "Hedge-" + (is_buy ? "Buy" : "Sell");
    double current_price = is_buy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);

    bool success = false;

    if(is_buy)
    {
        success = trade.Buy(volume, _Symbol, 0, 0, 0, comment);
    }
    else
    {
        success = trade.Sell(volume, _Symbol, 0, 0, 0, comment);
    }

    if(success)
    {
        // Add to hedge array
        hedge_positions[hedge_count].ticket = trade.ResultOrder();
        hedge_positions[hedge_count].is_buy = is_buy;
        hedge_positions[hedge_count].lot_size = volume;
        hedge_positions[hedge_count].entry_price = current_price;
        hedge_positions[hedge_count].entry_time = TimeCurrent();
        hedge_positions[hedge_count].is_active = true;
        hedge_count++;

        Print("Hedge placed: ", (is_buy ? "BUY" : "SELL"), " ", volume, " lots at ", current_price);
    }
    else
    {
        Print("Failed to place hedge: ", trade.ResultRetcodeDescription());
    }
}

void ManageHedge()
{
    // Update grid volume totals
    UpdateGridVolumes();
}

void UpdateGridVolumes()
{
    total_grid_volume_buy = 0;
    total_grid_volume_sell = 0;

    // Count active grid positions
    for(int i = 0; i < buy_count; i++)
    {
        if(buy_grid[i].is_filled && buy_grid[i].ticket > 0)
        {
            if(position.SelectByTicket(buy_grid[i].ticket))
            {
                total_grid_volume_buy += position.Volume();
            }
        }
    }

    for(int i = 0; i < sell_count; i++)
    {
        if(sell_grid[i].is_filled && sell_grid[i].ticket > 0)
        {
            if(position.SelectByTicket(sell_grid[i].ticket))
            {
                total_grid_volume_sell += position.Volume();
            }
        }
    }
}

void CheckHedgeExit()
{
    double ma_values[];
    int ma_handle = iMA(_Symbol, PERIOD_CURRENT, InpHedgeTrendPeriod, 0, MODE_EMA, PRICE_CLOSE);

    if(ma_handle == INVALID_HANDLE || CopyBuffer(ma_handle, 0, 0, 3, ma_values) < 3)
    {
        return; // Cannot analyze trend
    }

    double ma_current = ma_values[0];
    double ma_previous = ma_values[1];
    double ma_older = ma_values[2];
    double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    // Determine trend direction
    bool trend_up = (ma_current > ma_previous) && (ma_previous > ma_older) && (current_price > ma_current);
    bool trend_down = (ma_current < ma_previous) && (ma_previous < ma_older) && (current_price < ma_current);

    // Check each hedge position for exit
    for(int i = 0; i < hedge_count; i++)
    {
        if(hedge_positions[i].is_active && hedge_positions[i].ticket > 0)
        {
            if(position.SelectByTicket(hedge_positions[i].ticket))
            {
                double profit_points = 0;

                if(hedge_positions[i].is_buy)
                {
                    profit_points = (current_price - hedge_positions[i].entry_price) / point;

                    // Exit BUY hedge on downtrend or profit target
                    if(trend_down || profit_points >= InpHedgeExitThreshold)
                    {
                        CloseHedgePosition(i, "Trend Exit");
                    }
                }
                else // SELL hedge
                {
                    profit_points = (hedge_positions[i].entry_price - current_price) / point;

                    // Exit SELL hedge on uptrend or profit target
                    if(trend_up || profit_points >= InpHedgeExitThreshold)
                    {
                        CloseHedgePosition(i, "Trend Exit");
                    }
                }
            }
            else
            {
                // Position not found, mark as inactive
                hedge_positions[i].is_active = false;
            }
        }
    }
}

void CloseHedgePosition(int index, string reason)
{
    if(trade.PositionClose(hedge_positions[index].ticket))
    {
        Print("Hedge closed: ", (hedge_positions[index].is_buy ? "BUY" : "SELL"),
              " Ticket=", hedge_positions[index].ticket,
              " Reason=", reason);

        hedge_positions[index].is_active = false;
    }
    else
    {
        Print("Failed to close hedge: ", trade.ResultRetcodeDescription());
    }
}

void CloseAllHedges()
{
    for(int i = 0; i < hedge_count; i++)
    {
        if(hedge_positions[i].is_active)
        {
            CloseHedgePosition(i, "Force Close");
        }
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== TRUE GRID TRADING EA STOPPED ===");
    double final_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double total_pnl = final_balance - daily_start_balance;
    Print("Session P&L: $", total_pnl);
}