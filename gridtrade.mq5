//+------------------------------------------------------------------+
//|                                             GridTradingEA.mq5   |
//|                                  Grid Trading Expert Advisor    |
//|                                            Version 1.0          |
//+------------------------------------------------------------------+
#property copyright "Grid Trading EA"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\AccountInfo.mqh>

//--- ???????????????????????
CTrade trade;
CAccountInfo accountInfo;

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input group "=== General Settings ==="
input int      MagicNumber        = 123456;        // Magic Number
input double   InitialLotSize     = 0.01;         // Initial Lot Size
input string   TradeComment       = "Grid EA";    // Trade Comment

input group "=== Grid Configuration ==="
input int      GridDistance       = 300;          // Grid Distance (points)
input int      MaxGridLevels      = 10;           // Maximum Grid Levels
input double   LotMultiplier      = 1.5;          // Lot Multiplier
input int      TakeProfitPoints   = 500;          // Take Profit (points)
input int      StopLossPoints     = 1000;         // Stop Loss (points)

input group "=== Risk Management ==="
input double   MaxDrawdownPercent = 30.0;         // Maximum Drawdown (%)
input double   RiskPercentage     = 2.0;          // Risk per Trade (%)
input bool     UseBreakeven       = true;         // Use Breakeven
input int      BreakevenPoints    = 200;          // Breakeven Trigger (points)

input group "=== Trading Time ==="
input bool     UseTradingHours    = false;        // Use Trading Hours
input int      StartHour          = 0;            // Start Hour
input int      EndHour            = 23;           // End Hour

input group "=== Indicator Settings ==="
input int      MA_Period          = 20;           // Moving Average Period
input int      MA_Fast_Period     = 10;           // Fast MA Period
input int      MA_Slow_Period     = 30;           // Slow MA Period
input int      RSI_Period         = 14;           // RSI Period
input bool     ShowIndicatorSignals = true;       // Show Indicator Signals

//--- Global Variables
double currentBuyGridLevel = 0;
double currentSellGridLevel = 0;
int buyPositionCount = 0;
int sellPositionCount = 0;
double lastBuyPrice = 0;
double lastSellPrice = 0;
datetime lastBarTime = 0;
bool isTradeAllowed = true;

//--- Real-time Lot Tracking
double totalBuyLots = 0.0;
double totalSellLots = 0.0;
double buyProfit = 0.0;
double sellProfit = 0.0;

//--- Indicator Handles
int maHandle;
int rsiHandle;
int maFastHandle;
int maSlowHandle;

//--- Indicator Arrays
double maValues[];
double rsiValues[];
double maFastValues[];
double maSlowValues[];

//--- Grid Basket Structure
struct GridBasket
{
    int basketId;
    int direction;           // 1=Buy, -1=Sell
    double initialPrice;
    double currentLotSize;
    double totalVolume;
    double averagePrice;
    double totalProfit;
    int positionCount;
    datetime signalTime;
};

GridBasket buyBasket;
GridBasket sellBasket;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    //--- Set magic number for trade object
    trade.SetExpertMagicNumber(MagicNumber);
    
    //--- Initialize baskets
    ResetBasket(buyBasket, 1);
    ResetBasket(sellBasket, -1);
    
    //--- Display initialization message
    Print("Grid Trading EA initialized successfully");
    Print("Grid Distance: ", GridDistance, " points");
    Print("Max Grid Levels: ", MaxGridLevels);
    Print("Lot Multiplier: ", LotMultiplier);
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Comment("");
    Print("Grid Trading EA stopped. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    //--- Check if trading is allowed
    if(!IsTradeAllowed()) return;
    
    //--- Check trading hours
    if(UseTradingHours && !IsTradingTime()) return;
    
    //--- Check drawdown
    if(!CheckDrawdown()) 
    {
        CloseAllPositions();
        return;
    }
    
    //--- Get current prices
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double spread = ask - bid;
    
    //--- Count current positions
    CountPositions();
    
    //--- Manage existing grid positions
    if(buyPositionCount > 0 || sellPositionCount > 0)
    {
        ManageGridPositions(ask, bid);
        CheckBreakeven(ask, bid);
    }
    else
    {
        //--- Look for new entry signals
        if(CheckEntrySignal())
        {
            OpenInitialPosition(ask, bid);
        }
    }
    
    //--- Update display
    UpdateDisplay();
}

//+------------------------------------------------------------------+
//| Check entry signal                                              |
//+------------------------------------------------------------------+
bool CheckEntrySignal()
{
    //--- Simple RSI-based entry (can be replaced with any signal)
    int rsiHandle = iRSI(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE);
    double rsi[];
    ArraySetAsSeries(rsi, true);
    CopyBuffer(rsiHandle, 0, 0, 3, rsi);
    
    //--- Buy signal: RSI oversold
    if(rsi[0] < 30 && buyPositionCount == 0)
    {
        return true;
    }
    
    //--- Sell signal: RSI overbought
    if(rsi[0] > 70 && sellPositionCount == 0)
    {
        return true;
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Open initial position                                           |
//+------------------------------------------------------------------+
void OpenInitialPosition(double ask, double bid)
{
    double lotSize = CalculateLotSize();
    
    //--- Determine direction based on signal
    int rsiHandle = iRSI(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE);
    double rsi[];
    ArraySetAsSeries(rsi, true);
    CopyBuffer(rsiHandle, 0, 0, 1, rsi);
    
    if(rsi[0] < 30) // Buy
    {
        double sl = StopLossPoints > 0 ? ask - StopLossPoints * _Point : 0;
        double tp = TakeProfitPoints > 0 ? ask + TakeProfitPoints * _Point : 0;
        
        if(trade.Buy(lotSize, _Symbol, ask, sl, tp, TradeComment))
        {
            buyBasket.basketId = MagicNumber;
            buyBasket.initialPrice = ask;
            buyBasket.currentLotSize = lotSize;
            buyBasket.positionCount = 1;
            buyBasket.signalTime = TimeCurrent();
            lastBuyPrice = ask;
            
            Print("Initial BUY position opened at ", ask);
        }
    }
    else if(rsi[0] > 70) // Sell
    {
        double sl = StopLossPoints > 0 ? bid + StopLossPoints * _Point : 0;
        double tp = TakeProfitPoints > 0 ? bid - TakeProfitPoints * _Point : 0;
        
        if(trade.Sell(lotSize, _Symbol, bid, sl, tp, TradeComment))
        {
            sellBasket.basketId = MagicNumber;
            sellBasket.initialPrice = bid;
            sellBasket.currentLotSize = lotSize;
            sellBasket.positionCount = 1;
            sellBasket.signalTime = TimeCurrent();
            lastSellPrice = bid;
            
            Print("Initial SELL position opened at ", bid);
        }
    }
}

//+------------------------------------------------------------------+
//| Manage grid positions                                           |
//+------------------------------------------------------------------+
void ManageGridPositions(double ask, double bid)
{
    double gridStep = GridDistance * _Point;
    
    //--- Check for buy grid
    if(buyPositionCount > 0 && buyPositionCount < MaxGridLevels)
    {
        if(ask <= lastBuyPrice - gridStep)
        {
            double newLotSize = NormalizeDouble(buyBasket.currentLotSize * LotMultiplier, 2);
            
            //--- Check margin before opening
            if(CheckMargin(newLotSize, ORDER_TYPE_BUY))
            {
                double sl = StopLossPoints > 0 ? ask - StopLossPoints * _Point : 0;
                
                if(trade.Buy(newLotSize, _Symbol, ask, sl, 0, TradeComment))
                {
                    buyBasket.currentLotSize = newLotSize;
                    buyBasket.positionCount++;
                    lastBuyPrice = ask;
                    
                    Print("Grid BUY #", buyBasket.positionCount, " opened at ", ask, " Lot: ", newLotSize);
                }
            }
        }
    }
    
    //--- Check for sell grid
    if(sellPositionCount > 0 && sellPositionCount < MaxGridLevels)
    {
        if(bid >= lastSellPrice + gridStep)
        {
            double newLotSize = NormalizeDouble(sellBasket.currentLotSize * LotMultiplier, 2);
            
            //--- Check margin before opening
            if(CheckMargin(newLotSize, ORDER_TYPE_SELL))
            {
                double sl = StopLossPoints > 0 ? bid + StopLossPoints * _Point : 0;
                
                if(trade.Sell(newLotSize, _Symbol, bid, sl, 0, TradeComment))
                {
                    sellBasket.currentLotSize = newLotSize;
                    sellBasket.positionCount++;
                    lastSellPrice = bid;
                    
                    Print("Grid SELL #", sellBasket.positionCount, " opened at ", bid, " Lot: ", newLotSize);
                }
            }
        }
    }
    
    //--- Check for profit target
    CheckProfitTarget();
}

//+------------------------------------------------------------------+
//| Select position by index helper                                  |
//+------------------------------------------------------------------+
bool SelectPositionByIndex(const int index)
{
    if(index < 0 || index >= (int)PositionsTotal())
        return false;
    ulong ticket = PositionGetTicket(index);
    if(ticket == 0)
        return false;
    return PositionSelectByTicket(ticket);
}

//+------------------------------------------------------------------+
//| Check breakeven                                                 |
//+------------------------------------------------------------------+
void CheckBreakeven(double ask, double bid)
{
    if(!UseBreakeven) return;
    
    double breakevenDistance = BreakevenPoints * _Point;
    
    int i = PositionsTotal() - 1;
    for(; i >= 0; i--)
    {
        if(SelectPositionByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
            if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
            
            double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
            double currentSL = PositionGetDouble(POSITION_SL);
            double positionProfit = PositionGetDouble(POSITION_PROFIT);
            ulong ticket = PositionGetInteger(POSITION_TICKET);
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
                if(bid >= openPrice + breakevenDistance && currentSL < openPrice)
                {
                    trade.PositionModify(ticket, openPrice + 10 * _Point, 0);
                    Print("BUY position moved to breakeven");
                }
            }
            else if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
            {
                if(ask <= openPrice - breakevenDistance && (currentSL > openPrice || currentSL == 0))
                {
                    trade.PositionModify(ticket, openPrice - 10 * _Point, 0);
                    Print("SELL position moved to breakeven");
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check profit target                                             |
//+------------------------------------------------------------------+
void CheckProfitTarget()
{
    double totalBuyProfit = 0;
    double totalSellProfit = 0;
    double averageBuyPrice = 0;
    double averageSellPrice = 0;
    double totalBuyVolume = 0;
    double totalSellVolume = 0;
    
    //--- Calculate total profits and average prices
    int i = PositionsTotal() - 1;
    for(; i >= 0; i--)
    {
        if(SelectPositionByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
            if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
            
            double profit = PositionGetDouble(POSITION_PROFIT);
            double volume = PositionGetDouble(POSITION_VOLUME);
            double price = PositionGetDouble(POSITION_PRICE_OPEN);
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
                totalBuyProfit += profit;
                totalBuyVolume += volume;
                averageBuyPrice += price * volume;
            }
            else
            {
                totalSellProfit += profit;
                totalSellVolume += volume;
                averageSellPrice += price * volume;
            }
        }
    }
    
    //--- Calculate average prices
    if(totalBuyVolume > 0) averageBuyPrice /= totalBuyVolume;
    if(totalSellVolume > 0) averageSellPrice /= totalSellVolume;
    
    //--- Check if profit target reached
    double targetProfit = TakeProfitPoints * _Point * InitialLotSize * 100000; // Approximate calculation
    
    if(totalBuyProfit >= targetProfit && buyPositionCount > 0)
    {
        CloseAllBuyPositions();
        ResetBasket(buyBasket, 1);
        Print("Buy basket closed with profit: ", totalBuyProfit);
    }
    
    if(totalSellProfit >= targetProfit && sellPositionCount > 0)
    {
        CloseAllSellPositions();
        ResetBasket(sellBasket, -1);
        Print("Sell basket closed with profit: ", totalSellProfit);
    }
}

//+------------------------------------------------------------------+
//| Count positions                                                 |
//+------------------------------------------------------------------+
void CountPositions()
{
    buyPositionCount = 0;
    sellPositionCount = 0;
    double minBuyPrice = DBL_MAX;
    double maxSellPrice = 0;
    
    int i = PositionsTotal() - 1;
    for(; i >= 0; i--)
    {
        if(SelectPositionByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
            if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
            
            double price = PositionGetDouble(POSITION_PRICE_OPEN);
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
                buyPositionCount++;
                if(price < minBuyPrice) 
                {
                    minBuyPrice = price;
                    lastBuyPrice = price;
                }
            }
            else
            {
                sellPositionCount++;
                if(price > maxSellPrice)
                {
                    maxSellPrice = price;
                    lastSellPrice = price;
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate lot size                                              |
//+------------------------------------------------------------------+
double CalculateLotSize()
{
    if(RiskPercentage <= 0) return InitialLotSize;
    
    double accountBalance = accountInfo.Balance();
    double riskAmount = accountBalance * RiskPercentage / 100;
    double stopLossDistance = StopLossPoints * _Point;
    
    if(stopLossDistance <= 0) return InitialLotSize;
    
    double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    double lotSize = riskAmount / (StopLossPoints * tickValue);
    
    //--- Normalize lot size
    double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
    double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
    
    lotSize = MathMax(minLot, MathMin(maxLot, NormalizeDouble(lotSize / lotStep, 0) * lotStep));
    
    return lotSize;
}

//+------------------------------------------------------------------+
//| Check margin                                                    |
//+------------------------------------------------------------------+
bool CheckMargin(double lotSize, ENUM_ORDER_TYPE orderType)
{
    double price = 0;
    
    if(orderType == ORDER_TYPE_BUY)
        price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    else
        price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    
    double requiredMargin = 0;
    if(!OrderCalcMargin(orderType, _Symbol, lotSize, price, requiredMargin))
        return false;
    
    double freeMargin = accountInfo.FreeMargin();
    
    if(requiredMargin > freeMargin * 0.9) // Use only 90% of free margin
    {
        Print("Not enough margin. Required: ", requiredMargin, " Available: ", freeMargin);
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Check drawdown                                                  |
//+------------------------------------------------------------------+
bool CheckDrawdown()
{
    double balance = accountInfo.Balance();
    double equity = accountInfo.Equity();
    double drawdown = (balance - equity) / balance * 100;
    
    if(drawdown > MaxDrawdownPercent)
    {
        Print("Maximum drawdown reached: ", drawdown, "%");
        isTradeAllowed = false;
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Check trading time                                              |
//+------------------------------------------------------------------+
bool IsTradingTime()
{
    if(!UseTradingHours) return true;
    
    MqlDateTime time;
    TimeToStruct(TimeCurrent(), time);
    
    if(StartHour <= EndHour)
    {
        return (time.hour >= StartHour && time.hour <= EndHour);
    }
    else // Overnight trading
    {
        return (time.hour >= StartHour || time.hour <= EndHour);
    }
}

//+------------------------------------------------------------------+
//| Close all positions                                             |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
    int i = PositionsTotal() - 1;
    for(; i >= 0; i--)
    {
        if(SelectPositionByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
            if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
            
            ulong ticket = PositionGetInteger(POSITION_TICKET);
            trade.PositionClose(ticket);
        }
    }
}

//+------------------------------------------------------------------+
//| Close all buy positions                                         |
//+------------------------------------------------------------------+
void CloseAllBuyPositions()
{
    int i = PositionsTotal() - 1;
    for(; i >= 0; i--)
    {
        if(SelectPositionByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
            if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
                ulong ticket = PositionGetInteger(POSITION_TICKET);
                trade.PositionClose(ticket);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Close all sell positions                                        |
//+------------------------------------------------------------------+
void CloseAllSellPositions()
{
    int i = PositionsTotal() - 1;
    for(; i >= 0; i--)
    {
        if(SelectPositionByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
            if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
            {
                ulong ticket = PositionGetInteger(POSITION_TICKET);
                trade.PositionClose(ticket);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Reset basket                                                    |
//+------------------------------------------------------------------+
void ResetBasket(GridBasket &basket, int direction)
{
    basket.basketId = 0;
    basket.direction = direction;
    basket.initialPrice = 0;
    basket.currentLotSize = InitialLotSize;
    basket.totalVolume = 0;
    basket.averagePrice = 0;
    basket.totalProfit = 0;
    basket.positionCount = 0;
    basket.signalTime = 0;
}

//+------------------------------------------------------------------+
//| Update display                                                  |
//+------------------------------------------------------------------+
void UpdateDisplay()
{
    string info = "";
    info += "=== Grid Trading EA ===\n";
    info += "Account Balance: " + DoubleToString(accountInfo.Balance(), 2) + "\n";
    info += "Account Equity: " + DoubleToString(accountInfo.Equity(), 2) + "\n";
    info += "Free Margin: " + DoubleToString(accountInfo.FreeMargin(), 2) + "\n";
    info += "Current Spread: " + IntegerToString((int)((SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / _Point)) + " points\n";
    info += "\n";
    info += "Buy Positions: " + IntegerToString(buyPositionCount) + "/" + IntegerToString(MaxGridLevels) + "\n";
    info += "Sell Positions: " + IntegerToString(sellPositionCount) + "/" + IntegerToString(MaxGridLevels) + "\n";
    
    //--- Calculate current profit
    double currentProfit = 0;
    int i = PositionsTotal() - 1;
    for(; i >= 0; i--)
    {
        if(SelectPositionByIndex(i))
        {
            if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
            if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
            
            currentProfit += PositionGetDouble(POSITION_PROFIT);
        }
    }
    
    info += "Current Profit: " + DoubleToString(currentProfit, 2) + "\n";
    
    Comment(info);
}

//+------------------------------------------------------------------+
//| Trade Allowed Check                                             |
//+------------------------------------------------------------------+
bool IsTradeAllowed()
{
    return (TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) && 
            MQLInfoInteger(MQL_TRADE_ALLOWED) && 
            AccountInfoInteger(ACCOUNT_TRADE_EXPERT) &&
            AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) &&
            isTradeAllowed);
}
