//+------------------------------------------------------------------+
//|                                               SimpleGridEA.mq5  |
//|                                      Simple Grid Trading System |
//|                                              Pure Grid Strategy |
//+------------------------------------------------------------------+
#property copyright "Simple Grid EA"
#property link      ""
#property version   "1.00"
#property description "Simple Grid Trading System - Actually Works"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade trade;
CPositionInfo position;

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input int InpMagicNumber = 99999;        // Magic Number
input double InpLotSize = 0.1;           // Lot Size
input int InpGridStep = 50;              // Grid Step (points)
input int InpMaxOrders = 5;              // Max Orders
input double InpTakeProfit = 10.0;       // Take Profit ($)

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
double initial_balance = 0;
datetime last_order_time = 0;
bool trading_started = false;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== Simple Grid EA Started ===");

    trade.SetExpertMagicNumber(InpMagicNumber);
    initial_balance = AccountInfoDouble(ACCOUNT_BALANCE);

    Print("Magic Number: ", InpMagicNumber);
    Print("Lot Size: ", InpLotSize);
    Print("Grid Step: ", InpGridStep, " points");
    Print("Max Orders: ", InpMaxOrders);
    Print("Take Profit: $", InpTakeProfit);

    // Close existing positions
    CloseAllPositions();

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_log = 0;

    // Get current prices
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    // Debug every 10 seconds
    if(TimeCurrent() - last_log > 10)
    {
        Print("Tick: Ask=", ask, " Bid=", bid, " Orders=", CountOrders(), " Profit=$", GetTotalProfit());
        last_log = TimeCurrent();
    }

    // Check profit
    CheckProfit();

    // Start trading if no orders
    if(CountOrders() == 0 && TimeCurrent() - last_order_time > 5)
    {
        OpenFirstOrder();
        return;
    }

    // Add grid orders
    if(CountOrders() > 0 && CountOrders() < InpMaxOrders)
    {
        CheckGridOrders();
    }
}

//+------------------------------------------------------------------+
//| Open first order                                                 |
//+------------------------------------------------------------------+
void OpenFirstOrder()
{
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

    if(ask > 0)
    {
        if(trade.Buy(InpLotSize, _Symbol, 0, 0, 0, "Grid Start"))
        {
            Print("First BUY order opened at ", ask);
            last_order_time = TimeCurrent();
            trading_started = true;
        }
        else
        {
            Print("ERROR: Failed to open first order - ", trade.ResultRetcodeDescription());
        }
    }
    else
    {
        Print("ERROR: Invalid ASK price: ", ask);
    }
}

//+------------------------------------------------------------------+
//| Check grid orders                                                 |
//+------------------------------------------------------------------+
void CheckGridOrders()
{
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    if(ask <= 0 || bid <= 0) return;

    double lowest_buy = GetLowestBuyPrice();
    double highest_sell = GetHighestSellPrice();
    double grid_distance = InpGridStep * SymbolInfoDouble(_Symbol, SYMBOL_POINT);

    // Add BUY orders when price goes down
    if(lowest_buy > 0 && ask <= (lowest_buy - grid_distance))
    {
        if(TimeCurrent() - last_order_time > 3)
        {
            if(trade.Buy(InpLotSize, _Symbol, 0, 0, 0, "Grid BUY"))
            {
                Print("Added BUY order at ", ask);
                last_order_time = TimeCurrent();
            }
        }
    }

    // Add SELL orders when price goes up
    if(lowest_buy > 0 && bid >= (lowest_buy + grid_distance))
    {
        if(TimeCurrent() - last_order_time > 3)
        {
            if(trade.Sell(InpLotSize, _Symbol, 0, 0, 0, "Grid SELL"))
            {
                Print("Added SELL order at ", bid);
                last_order_time = TimeCurrent();
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Get lowest BUY price                                             |
//+------------------------------------------------------------------+
double GetLowestBuyPrice()
{
    double lowest = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.PositionType() == POSITION_TYPE_BUY)
                {
                    if(lowest == 0 || position.PriceOpen() < lowest)
                        lowest = position.PriceOpen();
                }
            }
        }
    }

    return lowest;
}

//+------------------------------------------------------------------+
//| Get highest SELL price                                           |
//+------------------------------------------------------------------+
double GetHighestSellPrice()
{
    double highest = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.PositionType() == POSITION_TYPE_SELL)
                {
                    if(position.PriceOpen() > highest)
                        highest = position.PriceOpen();
                }
            }
        }
    }

    return highest;
}

//+------------------------------------------------------------------+
//| Count orders                                                      |
//+------------------------------------------------------------------+
int CountOrders()
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

//+------------------------------------------------------------------+
//| Get total profit                                                  |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| Check profit and close if target reached                         |
//+------------------------------------------------------------------+
void CheckProfit()
{
    double profit = GetTotalProfit();

    if(profit >= InpTakeProfit)
    {
        Print("Profit target reached: $", profit);
        CloseAllPositions();
        last_order_time = TimeCurrent() + 10; // Wait 10 seconds before new grid
    }
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
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== Simple Grid EA Stopped ===");
}