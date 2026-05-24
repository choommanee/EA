//+------------------------------------------------------------------+
//|                                            SimpleDayTradeEA.mq5 |
//|                                    Simple Day Trading System    |
//|                                        Easy Entry & Quick Exit  |
//+------------------------------------------------------------------+
#property copyright "Simple Day Trade EA"
#property link      ""
#property version   "1.00"
#property description "Simple Day Trading - Easy Entry, Quick Exit"

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
input group "=== Day Trade Settings ==="
input int InpMagicNumber = 12345;                    // Magic Number
input double InpLotSize = 0.1;                       // Fixed Lot Size
input double InpTakeProfit = 20.0;                   // Take Profit (points) - ลดลงให้ออกง่าย
input double InpStopLoss = 40.0;                     // Stop Loss (points) - เพิ่มขึ้นเล็ก
input int InpMaxTrades = 10;                         // Max Trades Per Day - เพิ่มโอกาส

input group "=== Entry Signals ==="
input int InpFastMA = 5;                             // Fast MA Period
input int InpSlowMA = 20;                            // Slow MA Period
input int InpRSIPeriod = 14;                         // RSI Period
input double InpRSIBuy = 40.0;                       // RSI Buy Level - ง่ายขึ้น
input double InpRSISell = 60.0;                      // RSI Sell Level - ง่ายขึ้น
input bool InpUseSimpleEntry = true;                 // Use Simple Entry (MA only)

input group "=== Risk Management ==="
input double InpMaxDailyLoss = 50.0;                 // Max Daily Loss ($) - ลดลง
input double InpMaxDailyProfit = 100.0;              // Max Daily Profit ($) - ลดลง
input bool InpCloseAtEndOfDay = true;                // Close All at End of Day
input int InpEndHour = 23;                           // End Trading Hour

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
int daily_trades = 0;
double daily_start_balance = 0.0;
datetime last_trade_time = 0;
datetime last_daily_reset = 0;
bool daily_limit_reached = false;

int fast_ma_handle = INVALID_HANDLE;
int slow_ma_handle = INVALID_HANDLE;
int rsi_handle = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("=== Simple Day Trade EA Started ===");

    trade.SetExpertMagicNumber(InpMagicNumber);
    trade.SetMarginMode();
    trade.SetTypeFillingBySymbol(_Symbol);

    // Initialize symbol
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

    // Initialize indicators
    fast_ma_handle = iMA(_Symbol, PERIOD_CURRENT, InpFastMA, 0, MODE_EMA, PRICE_CLOSE);
    slow_ma_handle = iMA(_Symbol, PERIOD_CURRENT, InpSlowMA, 0, MODE_EMA, PRICE_CLOSE);
    rsi_handle = iRSI(_Symbol, PERIOD_CURRENT, InpRSIPeriod, PRICE_CLOSE);

    if(fast_ma_handle == INVALID_HANDLE || slow_ma_handle == INVALID_HANDLE || rsi_handle == INVALID_HANDLE)
    {
        Print("ERROR: Failed to create indicators");
        return INIT_FAILED;
    }

    // Initialize daily tracking
    daily_start_balance = account.Balance();
    last_daily_reset = TimeCurrent();
    daily_trades = 0;
    daily_limit_reached = false;

    Print("✅ Setup Complete - Balance: $", daily_start_balance);
    Print("🚀 Ready to trade! Waiting for signals...");
    Print("🎯 TP: ", InpTakeProfit, " points, SL: ", InpStopLoss, " points");
    Print("📋 Max Trades: ", InpMaxTrades, "/day, Max Loss: $", InpMaxDailyLoss);
    Print("⚙️ Simple Entry: ", InpUseSimpleEntry ? "ON (MA only)" : "OFF (MA+RSI)");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("=== Simple Day Trade EA Stopped ===");
    Print("Daily Trades: ", daily_trades);
    Print("P&L: $", account.Balance() - daily_start_balance);
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
    static datetime last_status = 0;

    // Check daily reset
    if(!CheckDailyReset()) return;

    // Check daily limits
    if(!CheckDailyLimits())
    {
        if(TimeCurrent() - last_status > 300) // Every 5 minutes
        {
            Print("⚠️ Daily limits reached - not trading");
            last_status = TimeCurrent();
        }
        return;
    }

    // Check if we can trade
    if(!CanTrade())
    {
        if(TimeCurrent() - last_status > 300) // Every 5 minutes
        {
            Print("⏰ Cannot trade now - waiting...");
            last_status = TimeCurrent();
        }
        return;
    }

    // Check for exit signals first
    CheckExitSignals();

    // Check for entry signals if no open positions
    int positions = GetOpenPositions();
    if(positions == 0)
    {
        CheckEntrySignals();
    }
    else if(TimeCurrent() - last_status > 60) // Every minute when positions open
    {
        Print("📊 Current positions: ", positions, " | P&L: $", account.Balance() - daily_start_balance);
        last_status = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Check daily reset                                               |
//+------------------------------------------------------------------+
bool CheckDailyReset()
{
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);

    MqlDateTime last_reset_struct;
    TimeToStruct(last_daily_reset, last_reset_struct);

    if(time_struct.day != last_reset_struct.day)
    {
        daily_start_balance = account.Balance();
        last_daily_reset = TimeCurrent();
        daily_trades = 0;
        daily_limit_reached = false;
        Print("📅 Daily Reset - New Balance: $", daily_start_balance);
        return true;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Check daily limits                                              |
//+------------------------------------------------------------------+
bool CheckDailyLimits()
{
    if(daily_limit_reached) return false;

    double daily_pnl = account.Balance() - daily_start_balance;

    // Check max daily loss
    if(daily_pnl <= -InpMaxDailyLoss)
    {
        Print("⛔ Daily loss limit reached: $", daily_pnl);
        CloseAllPositions();
        daily_limit_reached = true;
        return false;
    }

    // Check max daily profit
    if(daily_pnl >= InpMaxDailyProfit)
    {
        Print("🎯 Daily profit target reached: $", daily_pnl);
        CloseAllPositions();
        daily_limit_reached = true;
        return false;
    }

    // Check max trades
    if(daily_trades >= InpMaxTrades)
    {
        Print("📊 Max daily trades reached: ", daily_trades);
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Check if we can trade                                           |
//+------------------------------------------------------------------+
bool CanTrade()
{
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);

    // Don't trade near end of day
    if(time_struct.hour >= InpEndHour)
    {
        if(InpCloseAtEndOfDay && GetOpenPositions() > 0)
        {
            Print("🕐 End of day - closing all positions");
            CloseAllPositions();
        }
        return false;
    }

    // Don't trade too frequently
    if(TimeCurrent() - last_trade_time < 30) // Wait 30 seconds only
    {
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Check entry signals                                             |
//+------------------------------------------------------------------+
void CheckEntrySignals()
{
    double fast_ma[], slow_ma[], rsi[];
    ArraySetAsSeries(fast_ma, true);
    ArraySetAsSeries(slow_ma, true);
    ArraySetAsSeries(rsi, true);

    if(CopyBuffer(fast_ma_handle, 0, 0, 3, fast_ma) <= 0 ||
       CopyBuffer(slow_ma_handle, 0, 0, 3, slow_ma) <= 0 ||
       CopyBuffer(rsi_handle, 0, 0, 3, rsi) <= 0)
    {
        static datetime last_error = 0;
        if(TimeCurrent() - last_error > 60)
        {
            Print("⚠️ Failed to get indicator data - waiting...");
            last_error = TimeCurrent();
        }
        return;
    }

    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();

    if(InpUseSimpleEntry)
    {
        // Simple Entry - เฉพาะ MA crossover
        if(fast_ma[0] > slow_ma[0] && fast_ma[1] <= slow_ma[1]) // BUY on MA cross up
        {
            Print("📈 Simple BUY signal: Fast MA crossed above Slow MA");
            OpenBuyTrade(current_ask);
        }
        else if(fast_ma[0] < slow_ma[0] && fast_ma[1] >= slow_ma[1]) // SELL on MA cross down
        {
            Print("📉 Simple SELL signal: Fast MA crossed below Slow MA");
            OpenSellTrade(current_bid);
        }
    }
    else
    {
        // Advanced Entry - MA + RSI
        if(fast_ma[0] > slow_ma[0] && fast_ma[1] <= slow_ma[1] && rsi[0] < InpRSIBuy)
        {
            Print("📈 Advanced BUY signal: MA cross + RSI ", rsi[0]);
            OpenBuyTrade(current_ask);
        }
        else if(fast_ma[0] < slow_ma[0] && fast_ma[1] >= slow_ma[1] && rsi[0] > InpRSISell)
        {
            Print("📉 Advanced SELL signal: MA cross + RSI ", rsi[0]);
            OpenSellTrade(current_bid);
        }
    }

    // Debug info
    static datetime last_debug = 0;
    if(TimeCurrent() - last_debug > 60) // Every minute
    {
        Print("💡 Debug: Fast MA=", fast_ma[0], " Slow MA=", slow_ma[0], " RSI=", rsi[0], " Positions=", GetOpenPositions());
        last_debug = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Open BUY trade                                                  |
//+------------------------------------------------------------------+
void OpenBuyTrade(double price)
{
    double sl = price - (InpStopLoss * symbolInfo.Point());
    double tp = price + (InpTakeProfit * symbolInfo.Point());

    if(trade.Buy(InpLotSize, _Symbol, 0, sl, tp, "Day BUY"))
    {
        ulong ticket = trade.ResultOrder();
        daily_trades++;
        last_trade_time = TimeCurrent();
        Print("✅ BUY opened: #", ticket, " Price:", price, " SL:", sl, " TP:", tp, " (Trade ", daily_trades, "/", InpMaxTrades, ")");
    }
    else
    {
        Print("❌ BUY failed: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Open SELL trade                                                 |
//+------------------------------------------------------------------+
void OpenSellTrade(double price)
{
    double sl = price + (InpStopLoss * symbolInfo.Point());
    double tp = price - (InpTakeProfit * symbolInfo.Point());

    if(trade.Sell(InpLotSize, _Symbol, 0, sl, tp, "Day SELL"))
    {
        ulong ticket = trade.ResultOrder();
        daily_trades++;
        last_trade_time = TimeCurrent();
        Print("✅ SELL opened: #", ticket, " Price:", price, " SL:", sl, " TP:", tp, " (Trade ", daily_trades, "/", InpMaxTrades, ")");
    }
    else
    {
        Print("❌ SELL failed: ", trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Check exit signals                                              |
//+------------------------------------------------------------------+
void CheckExitSignals()
{
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                // Quick exit on opposite signal
                double fast_ma[], slow_ma[];
                ArraySetAsSeries(fast_ma, true);
                ArraySetAsSeries(slow_ma, true);

                if(CopyBuffer(fast_ma_handle, 0, 0, 2, fast_ma) > 0 &&
                   CopyBuffer(slow_ma_handle, 0, 0, 2, slow_ma) > 0)
                {
                    bool should_close = false;

                    if(position.PositionType() == POSITION_TYPE_BUY)
                    {
                        // Close BUY if MA turns bearish
                        if(fast_ma[0] < slow_ma[0] && fast_ma[1] >= slow_ma[1])
                        {
                            should_close = true;
                        }
                    }
                    else if(position.PositionType() == POSITION_TYPE_SELL)
                    {
                        // Close SELL if MA turns bullish
                        if(fast_ma[0] > slow_ma[0] && fast_ma[1] <= slow_ma[1])
                        {
                            should_close = true;
                        }
                    }

                    if(should_close)
                    {
                        trade.PositionClose(position.Ticket());
                        Print("🔄 Quick exit: #", position.Ticket(), " on signal reversal");
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Get number of open positions                                    |
//+------------------------------------------------------------------+
int GetOpenPositions()
{
    int count = 0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                count++;
            }
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| Close all positions                                             |
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
                Print("🛑 Closed position: #", position.Ticket());
            }
        }
    }
}