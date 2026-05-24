//+------------------------------------------------------------------+
//|                                                LotCounterEA.mq5  |
//|                                          Lot Counter & Indicator EA |
//|                                                    Version 1.0    |
//+------------------------------------------------------------------+
#property copyright "Lot Counter EA"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input group "=== Display Settings ==="
input int      RefreshRate        = 500;          // Refresh Rate (milliseconds)
input bool     ShowOnChart        = true;         // Show Info on Chart
input int      FontSize           = 12;           // Font Size
input color    BuyColor           = clrLime;      // Buy Color
input color    SellColor          = clrRed;       // Sell Color
input color    NeutralColor       = clrYellow;    // Neutral Color

input group "=== Indicator Settings ==="
input int      MA_Fast_Period     = 10;           // Fast MA Period
input int      MA_Slow_Period     = 21;           // Slow MA Period
input int      RSI_Period         = 14;           // RSI Period
input double   RSI_Oversold       = 30.0;         // RSI Oversold Level
input double   RSI_Overbought     = 70.0;         // RSI Overbought Level

//--- Global Variables
double totalBuyLots = 0.0;
double totalSellLots = 0.0;
double buyProfit = 0.0;
double sellProfit = 0.0;
int buyPositionCount = 0;
int sellPositionCount = 0;

//--- Indicator Handles
int maFastHandle;
int maSlowHandle;
int rsiHandle;

//--- Indicator Arrays
double maFastValues[];
double maSlowValues[];
double rsiValues[];

//--- Display variables
string trendDirection = "NEUTRAL";
color currentTrendColor = clrYellow;
datetime lastUpdate = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    //--- Initialize indicator handles
    maFastHandle = iMA(_Symbol, PERIOD_CURRENT, MA_Fast_Period, 0, MODE_SMA, PRICE_CLOSE);
    maSlowHandle = iMA(_Symbol, PERIOD_CURRENT, MA_Slow_Period, 0, MODE_SMA, PRICE_CLOSE);
    rsiHandle = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE);

    //--- Check if handles are valid
    if(maFastHandle == INVALID_HANDLE || maSlowHandle == INVALID_HANDLE || rsiHandle == INVALID_HANDLE)
    {
        Print("Error creating indicator handles");
        return(INIT_FAILED);
    }

    //--- Set array as series
    ArraySetAsSeries(maFastValues, true);
    ArraySetAsSeries(maSlowValues, true);
    ArraySetAsSeries(rsiValues, true);

    //--- Create timer
    EventSetTimer(1); // Update every second

    Print("Lot Counter EA initialized successfully");
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    //--- Kill timer
    EventKillTimer();

    //--- Clear comment
    Comment("");

    //--- Release indicator handles
    IndicatorRelease(maFastHandle);
    IndicatorRelease(maSlowHandle);
    IndicatorRelease(rsiHandle);

    Print("Lot Counter EA stopped");
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
    //--- Update lot counts
    UpdateLotCounts();

    //--- Update indicators
    UpdateIndicators();

    //--- Update display
    if(ShowOnChart)
        UpdateDisplay();
}

//+------------------------------------------------------------------+
//| Tick function                                                    |
//+------------------------------------------------------------------+
void OnTick()
{
    //--- Update on every tick for real-time display
    static datetime lastTickUpdate = 0;

    if(TimeCurrent() != lastTickUpdate)
    {
        UpdateLotCounts();
        UpdateIndicators();

        if(ShowOnChart)
            UpdateDisplay();

        lastTickUpdate = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Update lot counts                                               |
//+------------------------------------------------------------------+
void UpdateLotCounts()
{
    //--- Reset counters
    totalBuyLots = 0.0;
    totalSellLots = 0.0;
    buyProfit = 0.0;
    sellProfit = 0.0;
    buyPositionCount = 0;
    sellPositionCount = 0;

    //--- Count all positions in the market (all symbols)
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByTicket(PositionGetTicket(i)))
        {
            double volume = PositionGetDouble(POSITION_VOLUME);
            double profit = PositionGetDouble(POSITION_PROFIT);

            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
                totalBuyLots += volume;
                buyProfit += profit;
                buyPositionCount++;
            }
            else if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL)
            {
                totalSellLots += volume;
                sellProfit += profit;
                sellPositionCount++;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Update indicators                                               |
//+------------------------------------------------------------------+
void UpdateIndicators()
{
    //--- Copy indicator values
    if(CopyBuffer(maFastHandle, 0, 0, 3, maFastValues) < 3) return;
    if(CopyBuffer(maSlowHandle, 0, 0, 3, maSlowValues) < 3) return;
    if(CopyBuffer(rsiHandle, 0, 0, 3, rsiValues) < 3) return;

    //--- Determine trend direction
    string prevTrend = trendDirection;

    //--- MA Crossover Analysis
    bool maUptrend = maFastValues[0] > maSlowValues[0];
    bool maCrossUp = (maFastValues[1] <= maSlowValues[1]) && (maFastValues[0] > maSlowValues[0]);
    bool maCrossDown = (maFastValues[1] >= maSlowValues[1]) && (maFastValues[0] < maSlowValues[0]);

    //--- RSI Analysis
    bool rsiOversold = rsiValues[0] < RSI_Oversold;
    bool rsiOverbought = rsiValues[0] > RSI_Overbought;
    bool rsiNeutral = rsiValues[0] >= RSI_Oversold && rsiValues[0] <= RSI_Overbought;

    //--- Combine signals
    if((maUptrend || maCrossUp) && !rsiOverbought)
    {
        trendDirection = "BULLISH";
        currentTrendColor = BuyColor;
    }
    else if((!maUptrend || maCrossDown) && !rsiOversold)
    {
        trendDirection = "BEARISH";
        currentTrendColor = SellColor;
    }
    else if(rsiOversold)
    {
        trendDirection = "OVERSOLD";
        currentTrendColor = BuyColor;
    }
    else if(rsiOverbought)
    {
        trendDirection = "OVERBOUGHT";
        currentTrendColor = SellColor;
    }
    else
    {
        trendDirection = "NEUTRAL";
        currentTrendColor = NeutralColor;
    }

    //--- Alert on trend change
    if(prevTrend != trendDirection && prevTrend != "")
    {
        Print("Trend changed from ", prevTrend, " to ", trendDirection);
    }
}

//+------------------------------------------------------------------+
//| Update display                                                  |
//+------------------------------------------------------------------+
void UpdateDisplay()
{
    string info = "";

    //--- Header
    info += "═══════════════════════════════════════\n";
    info += "         📊 LOT COUNTER & SIGNALS 📊\n";
    info += "═══════════════════════════════════════\n\n";

    //--- Real-time lot information
    info += "💰 POSITION SUMMARY:\n";
    info += "   🟢 BUY Positions: " + IntegerToString(buyPositionCount) + " (" + DoubleToString(totalBuyLots, 2) + " lots)\n";
    info += "   🔴 SELL Positions: " + IntegerToString(sellPositionCount) + " (" + DoubleToString(totalSellLots, 2) + " lots)\n";
    info += "   📈 Total Lots: " + DoubleToString(totalBuyLots + totalSellLots, 2) + "\n\n";

    //--- Profit information
    info += "💵 PROFIT/LOSS:\n";
    info += "   🟢 Buy P&L: " + DoubleToString(buyProfit, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";
    info += "   🔴 Sell P&L: " + DoubleToString(sellProfit, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";
    info += "   💰 Total P&L: " + DoubleToString(buyProfit + sellProfit, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n\n";

    //--- Market trend information
    info += "📊 MARKET ANALYSIS (" + _Symbol + "):\n";

    //--- Add trend indicator with color coding
    string trendEmoji = "";
    if(trendDirection == "BULLISH") trendEmoji = "🟢📈";
    else if(trendDirection == "BEARISH") trendEmoji = "🔴📉";
    else if(trendDirection == "OVERSOLD") trendEmoji = "🟡📈";
    else if(trendDirection == "OVERBOUGHT") trendEmoji = "🟡📉";
    else trendEmoji = "⚪️➡️";

    info += "   " + trendEmoji + " Trend: " + trendDirection + "\n";

    //--- Current indicator values
    if(ArraySize(maFastValues) > 0 && ArraySize(maSlowValues) > 0 && ArraySize(rsiValues) > 0)
    {
        info += "   📐 Fast MA(" + IntegerToString(MA_Fast_Period) + "): " + DoubleToString(maFastValues[0], _Digits) + "\n";
        info += "   📐 Slow MA(" + IntegerToString(MA_Slow_Period) + "): " + DoubleToString(maSlowValues[0], _Digits) + "\n";
        info += "   📊 RSI(" + IntegerToString(RSI_Period) + "): " + DoubleToString(rsiValues[0], 1) + "\n";

        //--- RSI status
        string rsiStatus = "";
        if(rsiValues[0] < RSI_Oversold) rsiStatus = "OVERSOLD 🔥";
        else if(rsiValues[0] > RSI_Overbought) rsiStatus = "OVERBOUGHT ⚠️";
        else rsiStatus = "NORMAL ✅";

        info += "   📈 RSI Status: " + rsiStatus + "\n";
    }

    //--- Current price information
    double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
    double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    double spread = ask - bid;

    info += "\n📈 CURRENT PRICES:\n";
    info += "   🔼 Ask: " + DoubleToString(ask, _Digits) + "\n";
    info += "   🔽 Bid: " + DoubleToString(bid, _Digits) + "\n";
    info += "   📏 Spread: " + DoubleToString(spread/_Point, 1) + " points\n\n";

    //--- Signal recommendations
    info += "🎯 SIGNAL RECOMMENDATIONS:\n";
    if(trendDirection == "BULLISH")
        info += "   ✅ Consider BUY positions\n";
    else if(trendDirection == "BEARISH")
        info += "   ✅ Consider SELL positions\n";
    else if(trendDirection == "OVERSOLD")
        info += "   🔥 Strong BUY signal (Oversold)\n";
    else if(trendDirection == "OVERBOUGHT")
        info += "   ⚠️ Strong SELL signal (Overbought)\n";
    else
        info += "   ⏳ Wait for clear signal\n";

    //--- Footer
    info += "\n═══════════════════════════════════════\n";
    info += "🕒 Last Update: " + TimeToString(TimeCurrent(), TIME_SECONDS) + "\n";
    info += "═══════════════════════════════════════";

    //--- Display on chart
    Comment(info);
}

//+------------------------------------------------------------------+
//| Get trend color for display                                     |
//+------------------------------------------------------------------+
color GetTrendColor()
{
    return currentTrendColor;
}

//+------------------------------------------------------------------+
//| Get detailed market signal                                      |
//+------------------------------------------------------------------+
string GetMarketSignal()
{
    if(ArraySize(rsiValues) == 0) return "Loading...";

    string signal = "";

    //--- Strong signals
    if(rsiValues[0] < 20)
        signal = "VERY STRONG BUY 🚀";
    else if(rsiValues[0] > 80)
        signal = "VERY STRONG SELL 🔻";
    else if(trendDirection == "OVERSOLD")
        signal = "STRONG BUY 📈";
    else if(trendDirection == "OVERBOUGHT")
        signal = "STRONG SELL 📉";
    else if(trendDirection == "BULLISH")
        signal = "BUY 🟢";
    else if(trendDirection == "BEARISH")
        signal = "SELL 🔴";
    else
        signal = "NEUTRAL ⚪️";

    return signal;
}

//+------------------------------------------------------------------+
//| Calculate signal strength (0-100)                              |
//+------------------------------------------------------------------+
int GetSignalStrength()
{
    if(ArraySize(rsiValues) == 0 || ArraySize(maFastValues) == 0) return 0;

    int strength = 50; // Base neutral

    //--- RSI contribution
    if(rsiValues[0] < 30)
        strength += (30 - rsiValues[0]) * 2; // Max +60
    else if(rsiValues[0] > 70)
        strength += (rsiValues[0] - 70) * 2; // Max +60

    //--- MA trend contribution
    double maDiff = MathAbs(maFastValues[0] - maSlowValues[0]) / _Point;
    if(maDiff > 10)
        strength += MathMin(20, (int)(maDiff / 5)); // Max +20

    return MathMin(100, MathMax(0, strength));
}