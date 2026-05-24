//+------------------------------------------------------------------+
//|                                    RebateFarmPro_v4_Breakeven.mq5 |
//|                                        Copyright 2025, RebateFarm |
//|          BREAKEVEN REBATE FARMING - Target: No Loss + Rebate     |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, RebateFarm"
#property link      "https://www.mql5.com"
#property version   "4.00"
#property description "Breakeven Rebate Farming - เป้าหมาย: ไม่ขาดทุน + เก็บ Rebate"
#property description "Strategy: Quick scalp with tight BE protection"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>

//--- Enumerations
enum ENUM_ACCOUNT_TYPE
{
    ACCOUNT_STANDARD = 0,    // Standard ($10/lot)
    ACCOUNT_ULTRA = 1,       // Ultra Low ($6/lot)
    ACCOUNT_MICRO = 2        // Micro ($10/lot)
};

enum ENUM_STRATEGY_MODE
{
    MODE_SCALP_BE = 0,       // Scalp + Breakeven (แนะนำ)
    MODE_TREND_BE = 1,       // Trend + Breakeven
    MODE_RANGE_BE = 2        // Range + Breakeven
};

//--- Input Parameters
input group "=== BREAKEVEN STRATEGY ==="
input ENUM_STRATEGY_MODE InpMode = MODE_SCALP_BE;       // Strategy Mode
input int InpTakeProfit = 80;                           // Take Profit (points)
input int InpStopLoss = 80;                             // Stop Loss (points) - เท่ากับ TP!
input int InpBreakevenTrigger = 40;                     // Move to BE after (points profit)
input int InpBreakevenPlus = 5;                         // BE + extra (points) - ค่า spread
input bool InpUseTrailing = true;                       // Use Trailing after BE
input int InpTrailingStep = 30;                         // Trailing Step (points)

input group "=== ENTRY FILTERS (เข้มงวด) ==="
input int InpEMA_Fast = 8;                              // EMA Fast
input int InpEMA_Slow = 21;                             // EMA Slow
input int InpEMA_Filter = 50;                           // EMA Filter (trend)
input int InpRSI_Period = 7;                            // RSI Period
input int InpRSI_OB = 75;                               // RSI Overbought
input int InpRSI_OS = 25;                               // RSI Oversold
input int InpATR_Period = 14;                           // ATR Period
input double InpATR_MinMultiplier = 0.5;                // Min ATR for entry
input double InpATR_MaxMultiplier = 2.0;                // Max ATR for entry

input group "=== VOLUME & RISK ==="
input double InpLotSize = 0.01;                         // Lot Size
input bool InpAutoLot = false;                          // Auto Lot (disable for safety)
input double InpRiskPercent = 0.5;                      // Risk % (if auto lot)
input int InpMaxPositions = 3;                          // Max Positions
input int InpMinBarsBetweenTrades = 3;                  // Min bars between trades
input int InpGridPoints = 300;                          // Min distance between positions

input group "=== TIME & SPREAD ==="
input int InpMaxSpread = 25;                            // Max Spread (points)
input int InpStartHour = 3;                             // Start Hour
input int InpEndHour = 21;                              // End Hour
input bool InpAvoidHighVolatility = true;               // Avoid high volatility times

input group "=== REBATE TRACKING ==="
input bool InpEnableRebate = true;                      // Enable Rebate Tracking
input ENUM_ACCOUNT_TYPE InpAccountType = ACCOUNT_ULTRA; // Account Type
input double InpRebateRate = 6.0;                       // Rebate Rate ($/lot)

input group "=== SYSTEM ==="
input int InpMagicNumber = 202504;                      // Magic Number
input string InpComment = "BE_Rebate";                  // Order Comment

//--- Global Objects
CTrade         m_trade;
CPositionInfo  m_position;
CAccountInfo   m_account;
CSymbolInfo    m_symbol;

//--- Indicator Handles
int m_ema_fast_handle;
int m_ema_slow_handle;
int m_ema_filter_handle;
int m_rsi_handle;
int m_atr_handle;

//--- Buffers
double m_ema_fast[];
double m_ema_slow[];
double m_ema_filter[];
double m_rsi[];
double m_atr[];

//--- State
int m_positions_count;
double m_total_profit;
datetime m_last_trade_bar;
int m_win_count;
int m_loss_count;
int m_be_count;

//--- Rebate
double m_daily_lots;
double m_daily_rebate;
double m_total_rebate;
int m_daily_trades;
datetime m_day_start;
double m_initial_balance;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Initialize symbol
    if(!m_symbol.Name(_Symbol))
    {
        Print("Error initializing symbol");
        return INIT_FAILED;
    }

    // Trade settings
    m_trade.SetExpertMagicNumber(InpMagicNumber);
    m_trade.SetDeviationInPoints(10);
    m_trade.SetTypeFilling(ORDER_FILLING_IOC);

    // Create indicators
    m_ema_fast_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
    m_ema_slow_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
    m_ema_filter_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Filter, 0, MODE_EMA, PRICE_CLOSE);
    m_rsi_handle = iRSI(_Symbol, PERIOD_CURRENT, InpRSI_Period, PRICE_CLOSE);
    m_atr_handle = iATR(_Symbol, PERIOD_CURRENT, InpATR_Period);

    if(m_ema_fast_handle == INVALID_HANDLE || m_ema_slow_handle == INVALID_HANDLE ||
       m_ema_filter_handle == INVALID_HANDLE || m_rsi_handle == INVALID_HANDLE ||
       m_atr_handle == INVALID_HANDLE)
    {
        Print("Error creating indicators");
        return INIT_FAILED;
    }

    // Set arrays as series
    ArraySetAsSeries(m_ema_fast, true);
    ArraySetAsSeries(m_ema_slow, true);
    ArraySetAsSeries(m_ema_filter, true);
    ArraySetAsSeries(m_rsi, true);
    ArraySetAsSeries(m_atr, true);

    // Initialize
    m_initial_balance = m_account.Balance();
    m_day_start = GetDayStart(TimeCurrent());
    m_last_trade_bar = 0;
    m_win_count = 0;
    m_loss_count = 0;
    m_be_count = 0;
    m_daily_lots = 0;
    m_daily_rebate = 0;
    m_total_rebate = 0;
    m_daily_trades = 0;

    Print("=== RebateFarmPro v4.0 - BREAKEVEN EDITION ===");
    Print("Strategy: ", EnumToString(InpMode));
    Print("TP: ", InpTakeProfit, " | SL: ", InpStopLoss, " | BE Trigger: ", InpBreakevenTrigger);
    Print("Risk:Reward = 1:1 with BE protection");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    IndicatorRelease(m_ema_fast_handle);
    IndicatorRelease(m_ema_slow_handle);
    IndicatorRelease(m_ema_filter_handle);
    IndicatorRelease(m_rsi_handle);
    IndicatorRelease(m_atr_handle);
    Comment("");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    m_symbol.RefreshRates();

    // Update indicators
    if(!UpdateIndicators()) return;

    // Update state
    UpdateState();

    // Manage positions (BE + Trailing)
    ManagePositions();

    // Check for new trades
    if(CanTrade())
        CheckForEntry();

    // Update rebate
    UpdateRebateTracking();

    // Display
    UpdateDisplay();
}

//+------------------------------------------------------------------+
//| Update indicators                                                |
//+------------------------------------------------------------------+
bool UpdateIndicators()
{
    if(CopyBuffer(m_ema_fast_handle, 0, 0, 5, m_ema_fast) <= 0) return false;
    if(CopyBuffer(m_ema_slow_handle, 0, 0, 5, m_ema_slow) <= 0) return false;
    if(CopyBuffer(m_ema_filter_handle, 0, 0, 5, m_ema_filter) <= 0) return false;
    if(CopyBuffer(m_rsi_handle, 0, 0, 5, m_rsi) <= 0) return false;
    if(CopyBuffer(m_atr_handle, 0, 0, 5, m_atr) <= 0) return false;
    return true;
}

//+------------------------------------------------------------------+
//| Update trading state                                             |
//+------------------------------------------------------------------+
void UpdateState()
{
    m_positions_count = 0;
    m_total_profit = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                m_positions_count++;
                m_total_profit += m_position.Profit() + m_position.Swap() + m_position.Commission();
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check if can trade                                               |
//+------------------------------------------------------------------+
bool CanTrade()
{
    // Max positions
    if(m_positions_count >= InpMaxPositions) return false;

    // Spread check
    int spread = (int)m_symbol.Spread();
    if(spread > InpMaxSpread) return false;

    // Time filter
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);

    if(dt.hour < InpStartHour || dt.hour >= InpEndHour) return false;
    if(dt.day_of_week == 5 && dt.hour >= 20) return false; // Friday
    if(dt.day_of_week == 0 || dt.day_of_week == 6) return false; // Weekend

    // Avoid high volatility times (optional)
    if(InpAvoidHighVolatility)
    {
        // Avoid first/last hour of major sessions
        if((dt.hour >= 8 && dt.hour <= 9) || (dt.hour >= 14 && dt.hour <= 15))
        {
            // Check if ATR is too high
            if(m_atr[0] > m_atr[1] * InpATR_MaxMultiplier)
                return false;
        }
    }

    // Bar filter - prevent multiple trades same bar
    datetime current_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(m_last_trade_bar == current_bar) return false;

    // Min bars between trades
    int bars_since = iBarShift(_Symbol, PERIOD_CURRENT, m_last_trade_bar);
    if(bars_since < InpMinBarsBetweenTrades && m_last_trade_bar > 0) return false;

    // ATR filter - avoid too low volatility (no movement)
    double atr_min = m_atr[1] * InpATR_MinMultiplier;
    if(m_atr[0] < atr_min) return false;

    // Grid spacing check
    if(!CheckGridSpacing()) return false;

    return true;
}

//+------------------------------------------------------------------+
//| Check grid spacing                                               |
//+------------------------------------------------------------------+
bool CheckGridSpacing()
{
    double min_dist = InpGridPoints * m_symbol.Point();
    double bid = m_symbol.Bid();

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                if(MathAbs(bid - m_position.PriceOpen()) < min_dist)
                    return false;
            }
        }
    }
    return true;
}

//+------------------------------------------------------------------+
//| Check for entry signals                                          |
//+------------------------------------------------------------------+
void CheckForEntry()
{
    int signal = GetSignal();

    if(signal == 1)
        OpenBuy();
    else if(signal == -1)
        OpenSell();
}

//+------------------------------------------------------------------+
//| Get trading signal                                               |
//+------------------------------------------------------------------+
int GetSignal()
{
    // Current values
    double ema_fast = m_ema_fast[0];
    double ema_slow = m_ema_slow[0];
    double ema_filter = m_ema_filter[0];
    double rsi = m_rsi[0];
    double price = m_symbol.Bid();

    // Previous values (for crossover)
    double ema_fast_prev = m_ema_fast[1];
    double ema_slow_prev = m_ema_slow[1];
    double rsi_prev = m_rsi[1];

    int signal = 0;

    switch(InpMode)
    {
        case MODE_SCALP_BE:
            signal = GetScalpSignal(ema_fast, ema_slow, ema_filter, rsi, rsi_prev, price);
            break;

        case MODE_TREND_BE:
            signal = GetTrendSignal(ema_fast, ema_slow, ema_fast_prev, ema_slow_prev, ema_filter, rsi, price);
            break;

        case MODE_RANGE_BE:
            signal = GetRangeSignal(ema_fast, ema_slow, rsi, rsi_prev, price);
            break;
    }

    return signal;
}

//+------------------------------------------------------------------+
//| Scalp Signal - Quick entries with momentum                       |
//+------------------------------------------------------------------+
int GetScalpSignal(double ema_fast, double ema_slow, double ema_filter,
                   double rsi, double rsi_prev, double price)
{
    // BUY: Price above filter, fast > slow, RSI was oversold and turning up
    if(price > ema_filter && ema_fast > ema_slow)
    {
        // RSI momentum: was below 40, now rising
        if(rsi > rsi_prev && rsi < 60 && rsi_prev < 50)
        {
            // Extra: price near EMA fast (pullback entry)
            double dist = MathAbs(price - ema_fast) / m_symbol.Point();
            if(dist < 50) // Within 50 points of fast EMA
                return 1;
        }
    }

    // SELL: Price below filter, fast < slow, RSI was overbought and turning down
    if(price < ema_filter && ema_fast < ema_slow)
    {
        if(rsi < rsi_prev && rsi > 40 && rsi_prev > 50)
        {
            double dist = MathAbs(price - ema_fast) / m_symbol.Point();
            if(dist < 50)
                return -1;
        }
    }

    return 0;
}

//+------------------------------------------------------------------+
//| Trend Signal - EMA crossover with filter                        |
//+------------------------------------------------------------------+
int GetTrendSignal(double ema_fast, double ema_slow, double ema_fast_prev,
                   double ema_slow_prev, double ema_filter, double rsi, double price)
{
    // BUY: EMA crossover up + price above filter + RSI not overbought
    bool cross_up = ema_fast > ema_slow && ema_fast_prev <= ema_slow_prev;
    if(cross_up && price > ema_filter && rsi < InpRSI_OB)
        return 1;

    // SELL: EMA crossover down + price below filter + RSI not oversold
    bool cross_down = ema_fast < ema_slow && ema_fast_prev >= ema_slow_prev;
    if(cross_down && price < ema_filter && rsi > InpRSI_OS)
        return -1;

    return 0;
}

//+------------------------------------------------------------------+
//| Range Signal - RSI extremes with mean reversion                  |
//+------------------------------------------------------------------+
int GetRangeSignal(double ema_fast, double ema_slow, double rsi, double rsi_prev, double price)
{
    // Check if ranging (EMAs close together)
    double ema_diff = MathAbs(ema_fast - ema_slow) / m_symbol.Point();
    if(ema_diff > 30) return 0; // Not ranging

    // BUY: RSI oversold and turning up
    if(rsi_prev < InpRSI_OS && rsi > rsi_prev && rsi < 50)
        return 1;

    // SELL: RSI overbought and turning down
    if(rsi_prev > InpRSI_OB && rsi < rsi_prev && rsi > 50)
        return -1;

    return 0;
}

//+------------------------------------------------------------------+
//| Open Buy position                                                |
//+------------------------------------------------------------------+
void OpenBuy()
{
    double lot = CalculateLot();
    double price = m_symbol.Ask();
    double point = m_symbol.Point();

    double sl = price - InpStopLoss * point;
    double tp = price + InpTakeProfit * point;

    // Normalize
    sl = NormalizeDouble(sl, m_symbol.Digits());
    tp = NormalizeDouble(tp, m_symbol.Digits());

    if(m_trade.Buy(lot, _Symbol, price, sl, tp, InpComment))
    {
        m_last_trade_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
        m_daily_trades++;
        Print("BUY @ ", price, " SL: ", sl, " TP: ", tp, " Lot: ", lot);
    }
    else
    {
        Print("BUY failed: ", m_trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Open Sell position                                               |
//+------------------------------------------------------------------+
void OpenSell()
{
    double lot = CalculateLot();
    double price = m_symbol.Bid();
    double point = m_symbol.Point();

    double sl = price + InpStopLoss * point;
    double tp = price - InpTakeProfit * point;

    sl = NormalizeDouble(sl, m_symbol.Digits());
    tp = NormalizeDouble(tp, m_symbol.Digits());

    if(m_trade.Sell(lot, _Symbol, price, sl, tp, InpComment))
    {
        m_last_trade_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
        m_daily_trades++;
        Print("SELL @ ", price, " SL: ", sl, " TP: ", tp, " Lot: ", lot);
    }
    else
    {
        Print("SELL failed: ", m_trade.ResultRetcodeDescription());
    }
}

//+------------------------------------------------------------------+
//| Calculate lot size                                               |
//+------------------------------------------------------------------+
double CalculateLot()
{
    double lot = InpLotSize;

    if(InpAutoLot)
    {
        double balance = m_account.Balance();
        double risk_money = balance * InpRiskPercent / 100.0;
        double tick_value = m_symbol.TickValue();

        if(tick_value > 0 && InpStopLoss > 0)
            lot = risk_money / (InpStopLoss * tick_value);
    }

    // Normalize
    double min_lot = m_symbol.LotsMin();
    double max_lot = m_symbol.LotsMax();
    double step = m_symbol.LotsStep();

    lot = MathMax(min_lot, MathMin(max_lot, lot));
    lot = MathRound(lot / step) * step;

    return lot;
}

//+------------------------------------------------------------------+
//| Manage positions - Breakeven + Trailing                         |
//+------------------------------------------------------------------+
void ManagePositions()
{
    double point = m_symbol.Point();

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(!m_position.SelectByIndex(i)) continue;
        if(m_position.Symbol() != _Symbol || m_position.Magic() != InpMagicNumber) continue;

        double open_price = m_position.PriceOpen();
        double current_sl = m_position.StopLoss();
        double tp = m_position.TakeProfit();

        if(m_position.PositionType() == POSITION_TYPE_BUY)
        {
            double bid = m_symbol.Bid();
            double profit_pts = (bid - open_price) / point;

            // Move to breakeven
            if(profit_pts >= InpBreakevenTrigger)
            {
                double be_price = open_price + InpBreakevenPlus * point;
                be_price = NormalizeDouble(be_price, m_symbol.Digits());

                if(current_sl < be_price)
                {
                    if(m_trade.PositionModify(m_position.Ticket(), be_price, tp))
                    {
                        Print("BUY moved to BE+", InpBreakevenPlus, " @ ", be_price);
                    }
                }
                // Trailing after BE
                else if(InpUseTrailing && current_sl >= be_price)
                {
                    double trail_sl = bid - InpTrailingStep * point;
                    trail_sl = NormalizeDouble(trail_sl, m_symbol.Digits());

                    if(trail_sl > current_sl + point)
                    {
                        m_trade.PositionModify(m_position.Ticket(), trail_sl, tp);
                    }
                }
            }
        }
        else // SELL
        {
            double ask = m_symbol.Ask();
            double profit_pts = (open_price - ask) / point;

            // Move to breakeven
            if(profit_pts >= InpBreakevenTrigger)
            {
                double be_price = open_price - InpBreakevenPlus * point;
                be_price = NormalizeDouble(be_price, m_symbol.Digits());

                if(current_sl > be_price || current_sl == 0)
                {
                    if(m_trade.PositionModify(m_position.Ticket(), be_price, tp))
                    {
                        Print("SELL moved to BE+", InpBreakevenPlus, " @ ", be_price);
                    }
                }
                // Trailing after BE
                else if(InpUseTrailing && current_sl <= be_price && current_sl > 0)
                {
                    double trail_sl = ask + InpTrailingStep * point;
                    trail_sl = NormalizeDouble(trail_sl, m_symbol.Digits());

                    if(trail_sl < current_sl - point)
                    {
                        m_trade.PositionModify(m_position.Ticket(), trail_sl, tp);
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Update rebate tracking                                           |
//+------------------------------------------------------------------+
void UpdateRebateTracking()
{
    datetime today = GetDayStart(TimeCurrent());
    if(today > m_day_start)
    {
        m_total_rebate += m_daily_rebate;
        m_daily_lots = 0;
        m_daily_rebate = 0;
        m_daily_trades = 0;
        m_day_start = today;
    }

    m_daily_lots = CalculateDailyVolume();
    m_daily_rebate = m_daily_lots * InpRebateRate;
}

//+------------------------------------------------------------------+
//| Calculate daily volume                                           |
//+------------------------------------------------------------------+
double CalculateDailyVolume()
{
    double volume = 0;

    if(HistorySelect(m_day_start, TimeCurrent()))
    {
        for(int i = 0; i < HistoryDealsTotal(); i++)
        {
            ulong ticket = HistoryDealGetTicket(i);
            if(ticket > 0)
            {
                if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == InpMagicNumber)
                {
                    if(HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_IN)
                    {
                        volume += HistoryDealGetDouble(ticket, DEAL_VOLUME);
                    }
                }
            }
        }
    }

    return volume;
}

//+------------------------------------------------------------------+
//| Get day start                                                    |
//+------------------------------------------------------------------+
datetime GetDayStart(datetime time)
{
    MqlDateTime dt;
    TimeToStruct(time, dt);
    dt.hour = 0;
    dt.min = 0;
    dt.sec = 0;
    return StructToTime(dt);
}

//+------------------------------------------------------------------+
//| Track trade results                                              |
//+------------------------------------------------------------------+
void OnTrade()
{
    UpdateState();

    // Check closed trades for stats
    static int last_deals = 0;

    if(HistorySelect(m_day_start, TimeCurrent()))
    {
        int deals = HistoryDealsTotal();
        if(deals > last_deals)
        {
            // New deal closed
            for(int i = last_deals; i < deals; i++)
            {
                ulong ticket = HistoryDealGetTicket(i);
                if(ticket > 0 && HistoryDealGetInteger(ticket, DEAL_MAGIC) == InpMagicNumber)
                {
                    if(HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_OUT)
                    {
                        double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
                        if(profit > 0.5) m_win_count++;
                        else if(profit < -0.5) m_loss_count++;
                        else m_be_count++;
                    }
                }
            }
            last_deals = deals;
        }
    }
}

//+------------------------------------------------------------------+
//| Update display                                                   |
//+------------------------------------------------------------------+
void UpdateDisplay()
{
    double balance = m_account.Balance();
    double equity = m_account.Equity();
    double profit = balance - m_initial_balance;
    double spread = m_symbol.Spread() / 10.0;

    string info = "\n";
    info += "╔═══════════════════════════════════════════════════════════════╗\n";
    info += "║      💎 REBATE FARM PRO v4.0 - BREAKEVEN EDITION 💎          ║\n";
    info += "║         Target: Zero Loss + Maximum Rebate Income            ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    // Strategy Info
    info += "║ 📊 STRATEGY                                                   ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    string mode = EnumToString(InpMode);
    info += "║ Mode: " + mode + StringFormat("%*s", 56-StringLen(mode), "") + "║\n";

    info += "║ TP: " + IntegerToString(InpTakeProfit) + " | SL: " + IntegerToString(InpStopLoss) +
            " | BE@: " + IntegerToString(InpBreakevenTrigger) + " pts" +
            StringFormat("%*s", 30, "") + "║\n";

    string spread_icon = spread < 1.5 ? "🟢" : spread < 2.5 ? "🟡" : "🔴";
    info += "║ " + spread_icon + " Spread: " + DoubleToString(spread, 1) + " pips" +
            StringFormat("%*s", 47, "") + "║\n";

    // Indicators
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 📈 INDICATORS                                                 ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    string trend = m_ema_fast[0] > m_ema_slow[0] ? "🟢 BULLISH" : "🔴 BEARISH";
    info += "║ EMA Trend: " + trend + StringFormat("%*s", 50-StringLen(trend), "") + "║\n";

    string filter_pos = m_symbol.Bid() > m_ema_filter[0] ? "🟢 Above" : "🔴 Below";
    info += "║ Price vs EMA" + IntegerToString(InpEMA_Filter) + ": " + filter_pos +
            StringFormat("%*s", 43-StringLen(filter_pos), "") + "║\n";

    string rsi_str = DoubleToString(m_rsi[0], 1);
    string rsi_status = m_rsi[0] < 30 ? "🟢 Oversold" : m_rsi[0] > 70 ? "🔴 Overbought" : "🟡 Neutral";
    info += "║ RSI: " + rsi_str + " - " + rsi_status +
            StringFormat("%*s", 45-StringLen(rsi_str)-StringLen(rsi_status), "") + "║\n";

    // Trading Status
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 📊 TRADING STATUS                                             ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    info += "║ Positions: " + IntegerToString(m_positions_count) + "/" + IntegerToString(InpMaxPositions) +
            StringFormat("%*s", 50, "") + "║\n";

    string float_icon = m_total_profit >= 0 ? "📈" : "📉";
    info += "║ " + float_icon + " Float P/L: $" + DoubleToString(m_total_profit, 2) +
            StringFormat("%*s", 47-StringLen(DoubleToString(m_total_profit, 2)), "") + "║\n";

    // Win/Loss/BE Stats
    int total_trades = m_win_count + m_loss_count + m_be_count;
    if(total_trades > 0)
    {
        double win_rate = (double)(m_win_count + m_be_count) / total_trades * 100;
        info += "║ Stats: W:" + IntegerToString(m_win_count) + " L:" + IntegerToString(m_loss_count) +
                " BE:" + IntegerToString(m_be_count) + " | No-Loss: " + DoubleToString(win_rate, 1) + "%" +
                StringFormat("%*s", 18, "") + "║\n";
    }

    // Account
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 💰 ACCOUNT                                                     ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    info += "║ Balance: $" + DoubleToString(balance, 2) +
            StringFormat("%*s", 51-StringLen(DoubleToString(balance, 2)), "") + "║\n";
    info += "║ Equity: $" + DoubleToString(equity, 2) +
            StringFormat("%*s", 52-StringLen(DoubleToString(equity, 2)), "") + "║\n";

    string pnl = (profit >= 0 ? "+" : "") + DoubleToString(profit, 2);
    string pnl_icon = profit >= 0 ? "✅" : "⚠️";
    info += "║ " + pnl_icon + " Trading P/L: $" + pnl +
            StringFormat("%*s", 46-StringLen(pnl), "") + "║\n";

    // Rebate Section
    if(InpEnableRebate)
    {
        info += "╠═══════════════════════════════════════════════════════════════╣\n";
        info += "║ 💎 REBATE INCOME                                               ║\n";
        info += "╠═══════════════════════════════════════════════════════════════╣\n";

        info += "║ Rate: $" + DoubleToString(InpRebateRate, 2) + "/lot" +
                StringFormat("%*s", 51, "") + "║\n";

        info += "║ Today's Trades: " + IntegerToString(m_daily_trades) +
                StringFormat("%*s", 46-StringLen(IntegerToString(m_daily_trades)), "") + "║\n";

        info += "║ Today's Volume: " + DoubleToString(m_daily_lots, 2) + " lots" +
                StringFormat("%*s", 40-StringLen(DoubleToString(m_daily_lots, 2)), "") + "║\n";

        info += "║ 💵 Today's Rebate: $" + DoubleToString(m_daily_rebate, 2) +
                StringFormat("%*s", 42-StringLen(DoubleToString(m_daily_rebate, 2)), "") + "║\n";

        info += "║ 🏆 Total Rebate: $" + DoubleToString(m_total_rebate + m_daily_rebate, 2) +
                StringFormat("%*s", 44-StringLen(DoubleToString(m_total_rebate + m_daily_rebate, 2)), "") + "║\n";

        // NET RESULT
        double net = profit + m_daily_rebate + m_total_rebate;
        string net_icon = net >= 0 ? "✅" : "⚠️";
        info += "║ " + net_icon + " NET RESULT: $" + DoubleToString(net, 2) + " (Trading + Rebate)" +
                StringFormat("%*s", 24-StringLen(DoubleToString(net, 2)), "") + "║\n";
    }

    info += "╚═══════════════════════════════════════════════════════════════╝\n";
    info += "   💡 Strategy: TP=SL (1:1) + Breakeven Protection = Low Risk\n";
    info += "   🎯 Goal: Break-even or small profit + Rebate income";

    Comment(info);
}
//+------------------------------------------------------------------+
