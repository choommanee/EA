//+------------------------------------------------------------------+
//|                                   RebateFarmPro_v7_Improved.mq5  |
//|                                        Copyright 2025, RebateFarm |
//|     IMPROVED VERSION - Wider TP/SL + ATR + Session Filter        |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, RebateFarm"
#property link      "https://www.mql5.com"
#property version   "7.00"
#property description "v7 Improved: ATR-based stops, Wider TP/SL, Session Filter"
#property description "เป้าหมาย: ลดการขาดทุน + Order เยอะ + เก็บ Rebate"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>

//--- Dashboard Panel Prefix
#define PANEL_PREFIX    "TRPanel_"

//--- Enumerations
enum ENUM_TREND_MODE
{
    TREND_FOLLOW_AGGRESSIVE = 0,  // Aggressive - เข้าเยอะตาม trend
    TREND_FOLLOW_NORMAL = 1,      // Normal - balanced
    TREND_FOLLOW_SAFE = 2         // Safe - เข้าน้อยแต่แม่น
};

enum ENUM_SL_MODE
{
    SL_MODE_FIXED = 0,            // Fixed Points
    SL_MODE_ATR = 1               // ATR-based (Recommended)
};

//--- Input Parameters
input group "=== TREND DETECTION ==="
input int InpEMA_Fast = 8;                    // EMA Fast
input int InpEMA_Slow = 21;                   // EMA Slow
input int InpEMA_Trend = 50;                  // EMA Trend Filter
input int InpADX_Period = 14;                 // ADX Period
input int InpADX_Min = 20;                    // ADX Min for Trend (เพิ่มเป็น 20)
input ENUM_TREND_MODE InpMode = TREND_FOLLOW_NORMAL; // Mode (เปลี่ยนเป็น Normal)

input group "=== SCALING IN (เข้าหลาย Order ตาม Trend) ==="
input int InpScaleDistance = 100;             // Distance ระหว่าง Orders (points) - เพิ่มเป็น 100
input int InpMaxScaleOrders = 8;              // Max Orders ต่อทิศทาง - ลดเป็น 8
input double InpBaseLot = 0.01;               // Base Lot
input bool InpUsePyramid = true;              // Pyramid (เพิ่ม lot เมื่อ trend แรง)
input double InpPyramidMultiplier = 1.0;      // Pyramid Multiplier (1.0 = เท่าเดิม)
input int InpMinOrderInterval = 30;           // Min seconds between orders - เพิ่มเป็น 30

input group "=== TAKE PROFIT & STOP LOSS ==="
input ENUM_SL_MODE InpSLMode = SL_MODE_ATR;   // SL/TP Mode (ATR recommended)
input int InpMainTP = 500;                    // Main TP (points) - เพิ่มมากขึ้น
input int InpInitialSL = 1500;                // Initial SL (points) - กว้างขึ้นมาก
input double InpATR_TP_Mult = 3.0;            // ATR TP Multiplier (ถ้าใช้ ATR)
input double InpATR_SL_Mult = 8.0;            // ATR SL Multiplier (ถ้าใช้ ATR)
input int InpATR_Period = 14;                 // ATR Period

input group "=== TRAILING STOP (ควรปิด) ==="
input bool InpUseTrailing = false;            // Use Trailing - ปิด
input int InpTrailingTrigger = 400;           // Trailing เริ่มหลังกำไร (points) - เพิ่มมาก
input int InpTrailingStep = 100;              // Trailing Step (points) - เพิ่ม

input group "=== BREAKEVEN (ควรปิด) ==="
input bool InpUseBreakeven = false;           // Use Breakeven - ปิด
input int InpBreakevenAt = 300;               // Move to BE at (points) - เพิ่มมาก
input int InpBreakevenBuffer = 50;            // BE Buffer (points) - เพิ่ม
input int InpMinModifyInterval = 120;         // Min seconds between SL modifications

input group "=== RECOVERY SYSTEM ==="
input bool InpUseRecovery = false;            // Enable Recovery - ปิด (อันตราย)
input double InpRecoveryTrigger = -50.0;      // Recovery Trigger ($)
input double InpRecoveryMultiplier = 1.5;     // Recovery Lot Multiplier
input int InpMaxRecoveryLevels = 2;           // Max Recovery Levels
input int InpRecoveryDistance = 300;          // Recovery Distance (points)

input group "=== BASKET MANAGEMENT ==="
input bool InpUseBasketTP = true;             // Close All at Basket Profit
input double InpBasketTP = 10.0;              // Basket Take Profit ($) - เพิ่ม
input double InpBasketSL = -80.0;             // Basket Stop Loss ($) - กว้างขึ้น
input bool InpCloseOpposite = false;          // Close Opposite on Strong Signal - ปิด

input group "=== SESSION FILTER (สำคัญมาก) ==="
input bool InpUseSessionFilter = true;        // Use Session Filter
input int InpLondonStart = 8;                 // London Start Hour (GMT+0)
input int InpLondonEnd = 16;                  // London End Hour
input int InpNYStart = 13;                    // NY Start Hour (GMT+0)
input int InpNYEnd = 21;                      // NY End Hour
input int InpGMTOffset = 0;                   // GMT Offset (Server Time)

input group "=== SPREAD FILTER ==="
input int InpMaxSpread = 50;                  // Max Spread (points) - ลดลง
input int InpIdealSpread = 30;                // Ideal Spread (points)

input group "=== OTHER FILTERS ==="
input int InpStartHour = 2;                   // Start Hour (Server Time)
input int InpEndHour = 22;                    // End Hour (Server Time)
input int InpMinCandleSize = 10;              // Min Candle Size (points)
input bool InpAvoidNews = false;              // Avoid High Impact News (manual)

input group "=== REBATE ==="
input double InpRebateRate = 6.0;             // Rebate Rate ($/lot)

input group "=== SYSTEM ==="
input int InpMagicNumber = 202507;            // Magic Number
input string InpComment = "TrendRiderV7";     // Comment

//--- Global Objects
CTrade         m_trade;
CPositionInfo  m_position;
CAccountInfo   m_account;
CSymbolInfo    m_symbol;

//--- Indicator Handles
int m_ema_fast_handle;
int m_ema_slow_handle;
int m_ema_trend_handle;
int m_adx_handle;
int m_atr_handle;

//--- Buffers
double m_ema_fast[];
double m_ema_slow[];
double m_ema_trend[];
double m_adx_main[];
double m_adx_plus[];
double m_adx_minus[];
double m_atr[];

//--- State
struct PositionState
{
    int buy_count;
    int sell_count;
    double buy_volume;
    double sell_volume;
    double buy_profit;
    double sell_profit;
    double total_profit;
    double avg_buy_price;
    double avg_sell_price;
    double lowest_buy;
    double highest_sell;
    int recovery_level;
};
PositionState m_state;

//--- Trend
int m_current_trend;      // 1=bullish, -1=bearish, 0=no trend
int m_trend_strength;     // 1=weak, 2=normal, 3=strong
datetime m_last_bar;
datetime m_last_scale_bar;
datetime m_last_order_time;

//--- Stats & Rebate
double m_initial_balance;
double m_daily_lots;
double m_daily_rebate;
double m_total_rebate;
int m_daily_trades;
int m_total_orders;
datetime m_day_start;

//--- ATR Values
double m_current_atr;
double m_dynamic_tp;
double m_dynamic_sl;

//--- SL Modification Tracking
#define MAX_TRACKED_POSITIONS 100
ulong m_tracked_tickets[MAX_TRACKED_POSITIONS];
datetime m_last_modify_time[MAX_TRACKED_POSITIONS];
int m_tracked_count = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    if(!m_symbol.Name(_Symbol))
    {
        Print("Error initializing symbol");
        return INIT_FAILED;
    }

    m_trade.SetExpertMagicNumber(InpMagicNumber);
    m_trade.SetDeviationInPoints(30);  // เพิ่ม slippage tolerance
    m_trade.SetTypeFilling(ORDER_FILLING_IOC);

    // Create indicators
    m_ema_fast_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
    m_ema_slow_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
    m_ema_trend_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Trend, 0, MODE_EMA, PRICE_CLOSE);
    m_adx_handle = iADX(_Symbol, PERIOD_CURRENT, InpADX_Period);
    m_atr_handle = iATR(_Symbol, PERIOD_CURRENT, InpATR_Period);

    if(m_ema_fast_handle == INVALID_HANDLE || m_ema_slow_handle == INVALID_HANDLE ||
       m_ema_trend_handle == INVALID_HANDLE || m_adx_handle == INVALID_HANDLE ||
       m_atr_handle == INVALID_HANDLE)
    {
        Print("Error creating indicators");
        return INIT_FAILED;
    }

    ArraySetAsSeries(m_ema_fast, true);
    ArraySetAsSeries(m_ema_slow, true);
    ArraySetAsSeries(m_ema_trend, true);
    ArraySetAsSeries(m_adx_main, true);
    ArraySetAsSeries(m_adx_plus, true);
    ArraySetAsSeries(m_adx_minus, true);
    ArraySetAsSeries(m_atr, true);

    // Initialize
    ZeroMemory(m_state);
    m_initial_balance = m_account.Balance();
    m_day_start = GetDayStart(TimeCurrent());
    m_last_bar = 0;
    m_last_scale_bar = 0;
    m_last_order_time = 0;
    m_current_trend = 0;
    m_trend_strength = 0;
    m_daily_lots = 0;
    m_daily_rebate = 0;
    m_total_rebate = 0;
    m_daily_trades = 0;
    m_total_orders = 0;
    m_current_atr = 0;
    m_dynamic_tp = InpMainTP;
    m_dynamic_sl = InpInitialSL;

    Print("=== RebateFarmPro v7.0 - IMPROVED ===");
    Print("Mode: ", EnumToString(InpMode));
    Print("SL/TP Mode: ", EnumToString(InpSLMode));
    Print("Main TP: ", InpMainTP, " pts | Initial SL: ", InpInitialSL, " pts");
    Print("Session Filter: ", InpUseSessionFilter ? "ON" : "OFF");
    Print("Trailing: ", InpUseTrailing ? "ON" : "OFF");
    Print("Breakeven: ", InpUseBreakeven ? "ON" : "OFF");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    IndicatorRelease(m_ema_fast_handle);
    IndicatorRelease(m_ema_slow_handle);
    IndicatorRelease(m_ema_trend_handle);
    IndicatorRelease(m_adx_handle);
    IndicatorRelease(m_atr_handle);

    ObjectsDeleteAll(0, PANEL_PREFIX);
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

    // Update ATR-based values
    UpdateATRValues();

    // Update state
    UpdateState();

    // Analyze trend
    AnalyzeTrend();

    // Check basket profit/loss
    if(InpUseBasketTP)
        CheckBasketClose();

    // Recovery check
    if(InpUseRecovery)
        CheckRecovery();

    // Manage existing positions
    ManagePositions();

    // Check for new orders
    if(CanTrade())
    {
        if(InpMode == TREND_FOLLOW_AGGRESSIVE || IsNewBar())
            CheckForEntry();
    }

    // Scaling
    if(InpUsePyramid && CanTrade())
        CheckForScale();

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
    if(CopyBuffer(m_ema_trend_handle, 0, 0, 5, m_ema_trend) <= 0) return false;
    if(CopyBuffer(m_adx_handle, 0, 0, 5, m_adx_main) <= 0) return false;
    if(CopyBuffer(m_adx_handle, 1, 0, 5, m_adx_plus) <= 0) return false;
    if(CopyBuffer(m_adx_handle, 2, 0, 5, m_adx_minus) <= 0) return false;
    if(CopyBuffer(m_atr_handle, 0, 0, 5, m_atr) <= 0) return false;
    return true;
}

//+------------------------------------------------------------------+
//| Update ATR-based TP/SL values                                    |
//+------------------------------------------------------------------+
void UpdateATRValues()
{
    m_current_atr = m_atr[0];
    double point = m_symbol.Point();

    if(InpSLMode == SL_MODE_ATR && m_current_atr > 0)
    {
        // คำนวณ TP/SL จาก ATR
        m_dynamic_tp = MathMax(InpMainTP, (int)(m_current_atr * InpATR_TP_Mult / point));
        m_dynamic_sl = MathMax(InpInitialSL, (int)(m_current_atr * InpATR_SL_Mult / point));

        // Cap maximum values
        m_dynamic_tp = MathMin(m_dynamic_tp, 1500);  // Max 1500 pts
        m_dynamic_sl = MathMin(m_dynamic_sl, 3000);  // Max 3000 pts
    }
    else
    {
        m_dynamic_tp = InpMainTP;
        m_dynamic_sl = InpInitialSL;
    }
}

//+------------------------------------------------------------------+
//| Update position state                                            |
//+------------------------------------------------------------------+
void UpdateState()
{
    m_state.buy_count = 0;
    m_state.sell_count = 0;
    m_state.buy_volume = 0;
    m_state.sell_volume = 0;
    m_state.buy_profit = 0;
    m_state.sell_profit = 0;
    m_state.total_profit = 0;
    m_state.lowest_buy = DBL_MAX;
    m_state.highest_sell = 0;

    double buy_cost = 0, sell_cost = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                double profit = m_position.Profit() + m_position.Swap() + m_position.Commission();
                m_state.total_profit += profit;

                if(m_position.PositionType() == POSITION_TYPE_BUY)
                {
                    m_state.buy_count++;
                    m_state.buy_volume += m_position.Volume();
                    m_state.buy_profit += profit;
                    buy_cost += m_position.PriceOpen() * m_position.Volume();
                    if(m_position.PriceOpen() < m_state.lowest_buy)
                        m_state.lowest_buy = m_position.PriceOpen();
                }
                else
                {
                    m_state.sell_count++;
                    m_state.sell_volume += m_position.Volume();
                    m_state.sell_profit += profit;
                    sell_cost += m_position.PriceOpen() * m_position.Volume();
                    if(m_position.PriceOpen() > m_state.highest_sell)
                        m_state.highest_sell = m_position.PriceOpen();
                }
            }
        }
    }

    if(m_state.buy_volume > 0)
        m_state.avg_buy_price = buy_cost / m_state.buy_volume;
    if(m_state.sell_volume > 0)
        m_state.avg_sell_price = sell_cost / m_state.sell_volume;
}

//+------------------------------------------------------------------+
//| Analyze trend                                                    |
//+------------------------------------------------------------------+
void AnalyzeTrend()
{
    double price = m_symbol.Bid();
    double ema_fast = m_ema_fast[0];
    double ema_slow = m_ema_slow[0];
    double ema_trend = m_ema_trend[0];
    double adx = m_adx_main[0];
    double di_plus = m_adx_plus[0];
    double di_minus = m_adx_minus[0];

    m_current_trend = 0;
    m_trend_strength = 0;

    if(adx < InpADX_Min)
    {
        m_current_trend = 0;
        return;
    }

    bool ema_bullish = (ema_fast > ema_slow) && (price > ema_trend);
    bool ema_bearish = (ema_fast < ema_slow) && (price < ema_trend);
    bool di_bullish = di_plus > di_minus;
    bool di_bearish = di_minus > di_plus;

    if(ema_bullish && di_bullish)
    {
        m_current_trend = 1;
        if(adx > 40) m_trend_strength = 3;
        else if(adx > 30) m_trend_strength = 2;
        else m_trend_strength = 1;
    }
    else if(ema_bearish && di_bearish)
    {
        m_current_trend = -1;
        if(adx > 40) m_trend_strength = 3;
        else if(adx > 30) m_trend_strength = 2;
        else m_trend_strength = 1;
    }
}

//+------------------------------------------------------------------+
//| Check if new bar                                                 |
//+------------------------------------------------------------------+
bool IsNewBar()
{
    datetime current_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(current_bar != m_last_bar)
    {
        m_last_bar = current_bar;
        return true;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Check session filter                                             |
//+------------------------------------------------------------------+
bool IsGoodSession()
{
    if(!InpUseSessionFilter) return true;

    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    int hour = dt.hour - InpGMTOffset;  // Convert to GMT
    if(hour < 0) hour += 24;
    if(hour >= 24) hour -= 24;

    // London Session
    bool london = (hour >= InpLondonStart && hour < InpLondonEnd);

    // NY Session
    bool ny = (hour >= InpNYStart && hour < InpNYEnd);

    return (london || ny);
}

//+------------------------------------------------------------------+
//| Check spread filter                                              |
//+------------------------------------------------------------------+
bool IsGoodSpread()
{
    int spread = (int)m_symbol.Spread();
    return (spread <= InpMaxSpread);
}

//+------------------------------------------------------------------+
//| Check if ideal spread                                            |
//+------------------------------------------------------------------+
bool IsIdealSpread()
{
    int spread = (int)m_symbol.Spread();
    return (spread <= InpIdealSpread);
}

//+------------------------------------------------------------------+
//| Can trade check                                                  |
//+------------------------------------------------------------------+
bool CanTrade()
{
    // Spread filter
    if(!IsGoodSpread()) return false;

    // Session filter
    if(!IsGoodSession()) return false;

    // Time filter
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    if(dt.hour < InpStartHour || dt.hour >= InpEndHour) return false;
    if(dt.day_of_week == 5 && dt.hour >= 20) return false;
    if(dt.day_of_week == 0 || dt.day_of_week == 6) return false;

    // Candle size check
    double high = iHigh(_Symbol, PERIOD_CURRENT, 1);
    double low = iLow(_Symbol, PERIOD_CURRENT, 1);
    double candle_size = (high - low) / m_symbol.Point();
    if(candle_size < InpMinCandleSize) return false;

    return true;
}

//+------------------------------------------------------------------+
//| Can open new order (time throttle)                               |
//+------------------------------------------------------------------+
bool CanOpenNewOrder()
{
    if(TimeCurrent() - m_last_order_time < InpMinOrderInterval)
        return false;
    return true;
}

//+------------------------------------------------------------------+
//| Check for entry                                                  |
//+------------------------------------------------------------------+
void CheckForEntry()
{
    if(!CanOpenNewOrder()) return;

    // AGGRESSIVE MODE
    if(InpMode == TREND_FOLLOW_AGGRESSIVE)
    {
        if(m_ema_fast[0] > m_ema_slow[0])
        {
            if(InpCloseOpposite && m_state.sell_count > 0)
                CloseAllSells();

            if(m_state.buy_count == 0)
            {
                OpenBuy(InpBaseLot, "Entry");
                m_last_order_time = TimeCurrent();
            }
        }
        else if(m_ema_fast[0] < m_ema_slow[0])
        {
            if(InpCloseOpposite && m_state.buy_count > 0)
                CloseAllBuys();

            if(m_state.sell_count == 0)
            {
                OpenSell(InpBaseLot, "Entry");
                m_last_order_time = TimeCurrent();
            }
        }
        return;
    }

    // NORMAL/SAFE MODE
    if(m_current_trend == 0) return;

    int min_strength = (InpMode == TREND_FOLLOW_NORMAL) ? 1 : 2;
    if(m_trend_strength < min_strength) return;

    // ต้อง spread ดีสำหรับ Normal/Safe mode
    if(InpMode == TREND_FOLLOW_SAFE && !IsIdealSpread()) return;

    if(m_current_trend == 1 && m_state.buy_count == 0)
    {
        if(InpCloseOpposite && m_state.sell_count > 0)
            CloseAllSells();
        OpenBuy(InpBaseLot, "Entry");
        m_last_order_time = TimeCurrent();
    }

    if(m_current_trend == -1 && m_state.sell_count == 0)
    {
        if(InpCloseOpposite && m_state.buy_count > 0)
            CloseAllBuys();
        OpenSell(InpBaseLot, "Entry");
        m_last_order_time = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Check for scaling                                                |
//+------------------------------------------------------------------+
void CheckForScale()
{
    if(!CanOpenNewOrder()) return;

    double point = m_symbol.Point();
    double bid = m_symbol.Bid();
    double ask = m_symbol.Ask();

    // Use dynamic scale distance based on ATR
    int scale_dist = InpScaleDistance;
    if(InpSLMode == SL_MODE_ATR && m_current_atr > 0)
    {
        scale_dist = MathMax(InpScaleDistance, (int)(m_current_atr * 1.5 / point));
        scale_dist = MathMin(scale_dist, 300);  // Cap at 300 pts
    }

    // SCALE BUY
    bool is_buy_trend = (m_ema_fast[0] > m_ema_slow[0]);

    if(is_buy_trend && m_state.buy_count > 0 && m_state.buy_count < InpMaxScaleOrders)
    {
        double dist_from_lowest = (bid - m_state.lowest_buy) / point;
        double dist_from_avg = (m_state.avg_buy_price - ask) / point;

        if(dist_from_lowest >= scale_dist || dist_from_avg >= scale_dist)
        {
            OpenBuy(InpBaseLot, "Scale" + IntegerToString(m_state.buy_count + 1));
            m_last_order_time = TimeCurrent();
        }
    }

    // SCALE SELL
    bool is_sell_trend = (m_ema_fast[0] < m_ema_slow[0]);

    if(is_sell_trend && m_state.sell_count > 0 && m_state.sell_count < InpMaxScaleOrders)
    {
        double dist_from_highest = (m_state.highest_sell - bid) / point;
        double dist_from_avg = (ask - m_state.avg_sell_price) / point;

        if(dist_from_highest >= scale_dist || dist_from_avg >= scale_dist)
        {
            OpenSell(InpBaseLot, "Scale" + IntegerToString(m_state.sell_count + 1));
            m_last_order_time = TimeCurrent();
        }
    }
}

//+------------------------------------------------------------------+
//| Open Buy                                                         |
//+------------------------------------------------------------------+
void OpenBuy(double lot, string comment)
{
    double price = m_symbol.Ask();
    double point = m_symbol.Point();
    double sl = price - m_dynamic_sl * point;
    double tp = price + m_dynamic_tp * point;

    lot = NormalizeLot(lot);
    sl = NormalizeDouble(sl, m_symbol.Digits());
    tp = NormalizeDouble(tp, m_symbol.Digits());

    if(m_trade.Buy(lot, _Symbol, price, sl, tp, InpComment + "_" + comment))
    {
        m_daily_trades++;
        m_total_orders++;
        Print("BUY ", lot, " @ ", price, " SL=", sl, " (", (int)m_dynamic_sl, "pts) TP=", tp, " (", (int)m_dynamic_tp, "pts) [", comment, "]");
    }
}

//+------------------------------------------------------------------+
//| Open Sell                                                        |
//+------------------------------------------------------------------+
void OpenSell(double lot, string comment)
{
    double price = m_symbol.Bid();
    double point = m_symbol.Point();
    double sl = price + m_dynamic_sl * point;
    double tp = price - m_dynamic_tp * point;

    lot = NormalizeLot(lot);
    sl = NormalizeDouble(sl, m_symbol.Digits());
    tp = NormalizeDouble(tp, m_symbol.Digits());

    if(m_trade.Sell(lot, _Symbol, price, sl, tp, InpComment + "_" + comment))
    {
        m_daily_trades++;
        m_total_orders++;
        Print("SELL ", lot, " @ ", price, " SL=", sl, " (", (int)m_dynamic_sl, "pts) TP=", tp, " (", (int)m_dynamic_tp, "pts) [", comment, "]");
    }
}

//+------------------------------------------------------------------+
//| Normalize lot                                                    |
//+------------------------------------------------------------------+
double NormalizeLot(double lot)
{
    double min_lot = m_symbol.LotsMin();
    double max_lot = m_symbol.LotsMax();
    double step = m_symbol.LotsStep();

    lot = MathMax(min_lot, MathMin(max_lot, lot));
    lot = MathRound(lot / step) * step;
    return lot;
}

//+------------------------------------------------------------------+
//| Check basket close                                               |
//+------------------------------------------------------------------+
void CheckBasketClose()
{
    if(m_state.total_profit >= InpBasketTP)
    {
        Print("BASKET TP: $", m_state.total_profit);
        CloseAll();
        m_state.recovery_level = 0;
    }

    if(m_state.total_profit <= InpBasketSL)
    {
        Print("BASKET SL: $", m_state.total_profit);
        CloseAll();
        m_state.recovery_level = 0;
    }
}

//+------------------------------------------------------------------+
//| Check recovery                                                   |
//+------------------------------------------------------------------+
void CheckRecovery()
{
    if(m_state.recovery_level >= InpMaxRecoveryLevels) return;

    double point = m_symbol.Point();

    if(m_state.buy_count > 0 && m_state.buy_profit < InpRecoveryTrigger)
    {
        double price = m_symbol.Ask();
        double dist = (m_state.avg_buy_price - price) / point;

        if(dist >= InpRecoveryDistance)
        {
            double lot = m_state.buy_volume * InpRecoveryMultiplier;
            lot = NormalizeLot(lot);

            if(m_trade.Buy(lot, _Symbol, price, 0, 0, InpComment + "_Recovery"))
            {
                m_state.recovery_level++;
                m_daily_trades++;
                m_total_orders++;
                Print("RECOVERY BUY: ", lot, " lots at level ", m_state.recovery_level);
            }
        }
    }

    if(m_state.sell_count > 0 && m_state.sell_profit < InpRecoveryTrigger)
    {
        double price = m_symbol.Bid();
        double dist = (price - m_state.avg_sell_price) / point;

        if(dist >= InpRecoveryDistance)
        {
            double lot = m_state.sell_volume * InpRecoveryMultiplier;
            lot = NormalizeLot(lot);

            if(m_trade.Sell(lot, _Symbol, price, 0, 0, InpComment + "_Recovery"))
            {
                m_state.recovery_level++;
                m_daily_trades++;
                m_total_orders++;
                Print("RECOVERY SELL: ", lot, " lots at level ", m_state.recovery_level);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check if can modify SL (time-based throttle)                     |
//+------------------------------------------------------------------+
bool CanModifySL(ulong ticket)
{
    datetime now = TimeCurrent();

    for(int i = 0; i < m_tracked_count; i++)
    {
        if(m_tracked_tickets[i] == ticket)
        {
            if((now - m_last_modify_time[i]) >= InpMinModifyInterval)
                return true;
            else
                return false;
        }
    }

    return true;
}

//+------------------------------------------------------------------+
//| Record SL modification time                                       |
//+------------------------------------------------------------------+
void RecordModifyTime(ulong ticket)
{
    datetime now = TimeCurrent();

    for(int i = 0; i < m_tracked_count; i++)
    {
        if(m_tracked_tickets[i] == ticket)
        {
            m_last_modify_time[i] = now;
            return;
        }
    }

    if(m_tracked_count < MAX_TRACKED_POSITIONS)
    {
        m_tracked_tickets[m_tracked_count] = ticket;
        m_last_modify_time[m_tracked_count] = now;
        m_tracked_count++;
    }
}

//+------------------------------------------------------------------+
//| Clean up closed position tickets                                  |
//+------------------------------------------------------------------+
void CleanupTracking()
{
    for(int i = m_tracked_count - 1; i >= 0; i--)
    {
        bool found = false;
        for(int j = PositionsTotal() - 1; j >= 0; j--)
        {
            if(m_position.SelectByIndex(j))
            {
                if(m_position.Ticket() == m_tracked_tickets[i])
                {
                    found = true;
                    break;
                }
            }
        }

        if(!found)
        {
            for(int k = i; k < m_tracked_count - 1; k++)
            {
                m_tracked_tickets[k] = m_tracked_tickets[k + 1];
                m_last_modify_time[k] = m_last_modify_time[k + 1];
            }
            m_tracked_count--;
        }
    }
}

//+------------------------------------------------------------------+
//| Manage positions                                                 |
//+------------------------------------------------------------------+
void ManagePositions()
{
    double point = m_symbol.Point();

    // Cleanup periodically
    static datetime last_cleanup = 0;
    if(TimeCurrent() - last_cleanup > 60)
    {
        CleanupTracking();
        last_cleanup = TimeCurrent();
    }

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(!m_position.SelectByIndex(i)) continue;
        if(m_position.Symbol() != _Symbol || m_position.Magic() != InpMagicNumber) continue;

        ulong ticket = m_position.Ticket();
        double open_price = m_position.PriceOpen();
        double current_sl = m_position.StopLoss();
        double current_tp = m_position.TakeProfit();

        if(m_position.PositionType() == POSITION_TYPE_BUY)
        {
            double bid = m_symbol.Bid();
            double profit_pts = (bid - open_price) / point;

            if(!CanModifySL(ticket)) continue;

            double stop_level = m_symbol.StopsLevel() * point;
            if(stop_level < 50 * point) stop_level = 50 * point;

            // Breakeven - เฉพาะเมื่อเปิดและกำไรพอ
            if(InpUseBreakeven && profit_pts >= InpBreakevenAt && current_sl < open_price)
            {
                double be_sl = open_price + InpBreakevenBuffer * point;
                be_sl = NormalizeDouble(be_sl, m_symbol.Digits());

                double max_valid_sl = bid - stop_level;
                if(be_sl > max_valid_sl) continue;

                if(current_tp > 0 && (current_tp - be_sl) < stop_level) continue;

                if(m_trade.PositionModify(ticket, be_sl, current_tp))
                {
                    RecordModifyTime(ticket);
                    Print("BE Set: Ticket #", ticket, " SL=", be_sl);
                }
            }
            // Trailing - เฉพาะเมื่อกำไรมากพอ (400+ pts)
            else if(InpUseTrailing && profit_pts >= InpTrailingTrigger)
            {
                double new_sl = bid - InpTrailingStep * point;
                new_sl = NormalizeDouble(new_sl, m_symbol.Digits());

                double min_sl = open_price + InpBreakevenBuffer * point;
                if(new_sl < min_sl) new_sl = min_sl;

                double max_valid_sl = bid - stop_level;
                if(new_sl > max_valid_sl) new_sl = max_valid_sl;

                double min_diff = (InpTrailingStep / 2) * point;
                if(new_sl > current_sl + min_diff)
                {
                    if(m_trade.PositionModify(ticket, new_sl, current_tp))
                    {
                        RecordModifyTime(ticket);
                        Print("Trailing: Ticket #", ticket, " SL=", new_sl);
                    }
                }
            }
        }
        else // SELL
        {
            double ask = m_symbol.Ask();
            double profit_pts = (open_price - ask) / point;

            if(!CanModifySL(ticket)) continue;

            double stop_level = m_symbol.StopsLevel() * point;
            if(stop_level < 50 * point) stop_level = 50 * point;

            // Breakeven
            if(InpUseBreakeven && profit_pts >= InpBreakevenAt && (current_sl > open_price || current_sl == 0))
            {
                double be_sl = open_price - InpBreakevenBuffer * point;
                be_sl = NormalizeDouble(be_sl, m_symbol.Digits());

                double min_valid_sl = ask + stop_level;
                if(be_sl < min_valid_sl) continue;

                if(current_tp > 0 && (be_sl - current_tp) < stop_level) continue;

                if(m_trade.PositionModify(ticket, be_sl, current_tp))
                {
                    RecordModifyTime(ticket);
                    Print("BE Set: Ticket #", ticket, " SL=", be_sl);
                }
            }
            // Trailing
            else if(InpUseTrailing && profit_pts >= InpTrailingTrigger)
            {
                double new_sl = ask + InpTrailingStep * point;
                new_sl = NormalizeDouble(new_sl, m_symbol.Digits());

                double max_sl = open_price - InpBreakevenBuffer * point;
                if(new_sl > max_sl) new_sl = max_sl;

                double min_valid_sl = ask + stop_level;
                if(new_sl < min_valid_sl) new_sl = min_valid_sl;

                double min_diff = (InpTrailingStep / 2) * point;
                if(new_sl < current_sl - min_diff || current_sl == 0)
                {
                    if(m_trade.PositionModify(ticket, new_sl, current_tp))
                    {
                        RecordModifyTime(ticket);
                        Print("Trailing: Ticket #", ticket, " SL=", new_sl);
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Close all positions                                              |
//+------------------------------------------------------------------+
void CloseAll()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                m_trade.PositionClose(m_position.Ticket());
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Close all buys                                                   |
//+------------------------------------------------------------------+
void CloseAllBuys()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                if(m_position.PositionType() == POSITION_TYPE_BUY)
                    m_trade.PositionClose(m_position.Ticket());
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Close all sells                                                  |
//+------------------------------------------------------------------+
void CloseAllSells()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                if(m_position.PositionType() == POSITION_TYPE_SELL)
                    m_trade.PositionClose(m_position.Ticket());
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
            if(ticket > 0 && HistoryDealGetInteger(ticket, DEAL_MAGIC) == InpMagicNumber)
            {
                if(HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_IN)
                    volume += HistoryDealGetDouble(ticket, DEAL_VOLUME);
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
//| OnTrade                                                          |
//+------------------------------------------------------------------+
void OnTrade()
{
    UpdateState();
}

//+------------------------------------------------------------------+
//| Dashboard Configuration                                          |
//+------------------------------------------------------------------+
#define PANEL_X         20
#define PANEL_Y         30
#define PANEL_WIDTH     300
#define ROW_HEIGHT      18
#define SECTION_GAP     6
#define MARGIN          10
#define COL2            160

// Professional Dark Theme Colors
#define CLR_BG_MAIN     C'25,25,28'
#define CLR_BG_HEADER   C'0,150,136'
#define CLR_BG_SECTION  C'38,38,42'
#define CLR_BORDER      C'55,55,60'
#define CLR_TEXT_WHITE  C'255,255,255'
#define CLR_TEXT_GRAY   C'155,155,160'
#define CLR_TEXT_LABEL  C'120,120,125'
#define CLR_PROFIT      C'50,205,50'
#define CLR_LOSS        C'255,82,82'
#define CLR_WARNING     C'255,193,7'
#define CLR_BULLISH     C'0,200,83'
#define CLR_BEARISH     C'255,82,82'
#define CLR_NEUTRAL     C'255,193,7'

bool g_panel_created = false;

//+------------------------------------------------------------------+
//| Create Rectangle Label                                           |
//+------------------------------------------------------------------+
void CreateRect(string name, int x, int y, int w, int h, color bg, color border = CLR_BORDER)
{
   string obj_name = PANEL_PREFIX + name;
   ObjectCreate(0, obj_name, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, obj_name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, obj_name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, obj_name, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, obj_name, OBJPROP_YSIZE, h);
   ObjectSetInteger(0, obj_name, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, obj_name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, obj_name, OBJPROP_COLOR, border);
   ObjectSetInteger(0, obj_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, obj_name, OBJPROP_BACK, false);
}

//+------------------------------------------------------------------+
//| Create Text Label                                                |
//+------------------------------------------------------------------+
void CreateText(string name, string text, int x, int y, color clr, int size = 9, string font = "Segoe UI")
{
   string obj_name = PANEL_PREFIX + name;
   ObjectCreate(0, obj_name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, obj_name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, obj_name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, obj_name, OBJPROP_TEXT, text);
   ObjectSetString(0, obj_name, OBJPROP_FONT, font);
   ObjectSetInteger(0, obj_name, OBJPROP_FONTSIZE, size);
   ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, obj_name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
}

//+------------------------------------------------------------------+
//| Update Text Label                                                |
//+------------------------------------------------------------------+
void UpdateText(string name, string text, color clr = CLR_TEXT_WHITE)
{
   string obj_name = PANEL_PREFIX + name;
   ObjectSetString(0, obj_name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| Create Section Header                                            |
//+------------------------------------------------------------------+
int CreateSection(string name, string title, int y)
{
   CreateRect(name + "_bg", PANEL_X + 4, y, PANEL_WIDTH - 8, 22, CLR_BG_SECTION, CLR_BG_SECTION);
   CreateText(name + "_title", title, PANEL_X + MARGIN, y + 4, CLR_TEXT_GRAY, 9, "Segoe UI Semibold");
   return y + 24;
}

//+------------------------------------------------------------------+
//| Create Data Row                                                  |
//+------------------------------------------------------------------+
int CreateRow(string name, string label, int y)
{
   CreateText(name + "_lbl", label, PANEL_X + MARGIN, y, CLR_TEXT_LABEL, 9);
   CreateText(name + "_val", "-", PANEL_X + COL2, y, CLR_TEXT_WHITE, 9, "Consolas");
   return y + ROW_HEIGHT;
}

//+------------------------------------------------------------------+
//| Create Dashboard Panel                                           |
//+------------------------------------------------------------------+
void CreateDashboard()
{
   if(g_panel_created) return;

   int y = PANEL_Y;
   int panel_height = 400;

   // Main Background
   CreateRect("main", PANEL_X, y, PANEL_WIDTH, panel_height, CLR_BG_MAIN);

   // Header
   CreateRect("header", PANEL_X, y, PANEL_WIDTH, 32, CLR_BG_HEADER, CLR_BG_HEADER);
   CreateText("title", "TREND RIDER v7.0 IMPROVED", PANEL_X + MARGIN, y + 4, CLR_TEXT_WHITE, 11, "Segoe UI Bold");
   CreateText("symbol", _Symbol, PANEL_X + MARGIN, y + 18, C'200,220,255', 8);
   CreateText("status", "●", PANEL_X + PANEL_WIDTH - 24, y + 8, CLR_PROFIT, 12);
   y += 36;

   // TREND Section
   y = CreateSection("sec_trend", "TREND", y);
   y = CreateRow("trend", "Direction", y);
   y = CreateRow("strength", "Strength", y);
   y = CreateRow("adx", "ADX", y);
   y = CreateRow("atr", "ATR", y);
   y = CreateRow("spread", "Spread", y);
   y = CreateRow("session", "Session", y);
   y += SECTION_GAP;

   // POSITIONS Section
   y = CreateSection("sec_pos", "POSITIONS", y);
   y = CreateRow("buy", "Buy", y);
   y = CreateRow("sell", "Sell", y);
   y = CreateRow("floating", "Floating P/L", y);
   y += SECTION_GAP;

   // ACCOUNT Section
   y = CreateSection("sec_acc", "ACCOUNT", y);
   y = CreateRow("balance", "Balance", y);
   y = CreateRow("equity", "Equity", y);
   y = CreateRow("pnl", "Trading P/L", y);
   y += SECTION_GAP;

   // REBATE Section
   y = CreateSection("sec_rebate", "REBATE", y);
   y = CreateRow("today", "Today", y);
   y = CreateRow("total", "Total", y);
   y = CreateRow("net", "Net Result", y);

   g_panel_created = true;
   ChartRedraw(0);
}

//+------------------------------------------------------------------+
//| Update Dashboard Display                                         |
//+------------------------------------------------------------------+
void UpdateDisplay()
{
   if(!g_panel_created) CreateDashboard();

   double balance = m_account.Balance();
   double equity = m_account.Equity();
   double profit = balance - m_initial_balance;
   double spread = m_symbol.Spread() / 10.0;
   double net = profit + m_daily_rebate + m_total_rebate;

   // Status indicator
   color status_clr = (m_state.buy_count + m_state.sell_count > 0) ? CLR_PROFIT : CLR_TEXT_GRAY;
   UpdateText("status", "●", status_clr);

   // TREND
   string trend_str = (m_current_trend == 1) ? "BULLISH" : (m_current_trend == -1) ? "BEARISH" : "NEUTRAL";
   color trend_clr = (m_current_trend == 1) ? CLR_BULLISH : (m_current_trend == -1) ? CLR_BEARISH : CLR_NEUTRAL;
   UpdateText("trend_val", trend_str, trend_clr);

   string str_str = (m_trend_strength == 3) ? "STRONG" : (m_trend_strength == 2) ? "NORMAL" : (m_trend_strength == 1) ? "WEAK" : "NONE";
   color str_clr = (m_trend_strength >= 2) ? CLR_PROFIT : (m_trend_strength == 1) ? CLR_WARNING : CLR_TEXT_GRAY;
   UpdateText("strength_val", str_str, str_clr);

   UpdateText("adx_val", DoubleToString(m_adx_main[0], 1) + " | +" + DoubleToString(m_adx_plus[0], 1) + " -" + DoubleToString(m_adx_minus[0], 1), CLR_TEXT_WHITE);

   // ATR Info
   string atr_info = DoubleToString(m_current_atr, 2) + " | TP:" + IntegerToString((int)m_dynamic_tp) + " SL:" + IntegerToString((int)m_dynamic_sl);
   UpdateText("atr_val", atr_info, CLR_TEXT_WHITE);

   color spread_clr = (spread < 3.0) ? CLR_PROFIT : (spread < 5.0) ? CLR_WARNING : CLR_LOSS;
   UpdateText("spread_val", DoubleToString(spread, 1) + " pips", spread_clr);

   // Session
   string sess_str = IsGoodSession() ? "ACTIVE" : "OFF";
   color sess_clr = IsGoodSession() ? CLR_PROFIT : CLR_TEXT_GRAY;
   UpdateText("session_val", sess_str, sess_clr);

   // POSITIONS
   string buy_info = IntegerToString(m_state.buy_count) + " | " + DoubleToString(m_state.buy_volume, 2) + " lots";
   color buy_clr = (m_state.buy_profit >= 0) ? CLR_PROFIT : CLR_LOSS;
   UpdateText("buy_val", buy_info, buy_clr);

   string sell_info = IntegerToString(m_state.sell_count) + " | " + DoubleToString(m_state.sell_volume, 2) + " lots";
   color sell_clr = (m_state.sell_profit >= 0) ? CLR_PROFIT : CLR_LOSS;
   UpdateText("sell_val", sell_info, sell_clr);

   color float_clr = (m_state.total_profit >= 0) ? CLR_PROFIT : CLR_LOSS;
   UpdateText("floating_val", "$" + DoubleToString(m_state.total_profit, 2), float_clr);

   // ACCOUNT
   UpdateText("balance_val", "$" + DoubleToString(balance, 2), CLR_TEXT_WHITE);

   color eq_clr = (equity >= balance) ? CLR_PROFIT : CLR_LOSS;
   UpdateText("equity_val", "$" + DoubleToString(equity, 2), eq_clr);

   color pnl_clr = (profit >= 0) ? CLR_PROFIT : CLR_LOSS;
   string pnl_str = (profit >= 0 ? "+" : "") + "$" + DoubleToString(profit, 2);
   UpdateText("pnl_val", pnl_str, pnl_clr);

   // REBATE
   string today_info = IntegerToString(m_daily_trades) + " trades | " + DoubleToString(m_daily_lots, 2) + " lots";
   UpdateText("today_val", today_info, CLR_TEXT_WHITE);

   UpdateText("total_val", "$" + DoubleToString(m_total_rebate + m_daily_rebate, 2), CLR_PROFIT);

   color net_clr = (net >= 0) ? CLR_PROFIT : CLR_LOSS;
   string net_str = (net >= 0 ? "+" : "") + "$" + DoubleToString(net, 2);
   UpdateText("net_val", net_str, net_clr);

   ChartRedraw(0);
}
//+------------------------------------------------------------------+
