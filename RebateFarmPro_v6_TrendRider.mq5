//+------------------------------------------------------------------+
//|                                   RebateFarmPro_v6_TrendRider.mq5 |
//|                                        Copyright 2025, RebateFarm |
//|     TREND RIDER + HIGH VOLUME - วิ่งตาม Trend ออก Order เยอะๆ    |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, RebateFarm"
#property link      "https://www.mql5.com"
#property version   "6.00"
#property description "Trend Rider: วิ่งตาม Trend + Scaling In + Recovery"
#property description "เป้าหมาย: Order เยอะ + ไม่ติดลบ + เก็บ Rebate"

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

//--- Input Parameters
input group "=== TREND DETECTION ==="
input int InpEMA_Fast = 8;                    // EMA Fast
input int InpEMA_Slow = 21;                   // EMA Slow
input int InpEMA_Trend = 50;                  // EMA Trend Filter
input int InpADX_Period = 14;                 // ADX Period
input int InpADX_Min = 15;                    // ADX Min for Trend (ลดลงเพื่อเข้าง่ายขึ้น)
input ENUM_TREND_MODE InpMode = TREND_FOLLOW_AGGRESSIVE; // Mode

input group "=== SCALING IN (เข้าหลาย Order ตาม Trend) ==="
input int InpScaleDistance = 50;              // Distance ระหว่าง Orders (points) - เพิ่มเป็น 50
input int InpMaxScaleOrders = 10;             // Max Orders ต่อทิศทาง - ลดเป็น 10
input double InpBaseLot = 0.01;               // Base Lot
input bool InpUsePyramid = true;              // Pyramid (เพิ่ม lot เมื่อ trend แรง)
input double InpPyramidMultiplier = 1.0;      // Pyramid Multiplier (1.0 = เท่าเดิม)
input int InpMinOrderInterval = 15;           // Min seconds between orders - เพิ่มเป็น 15

input group "=== TAKE PROFIT & STOP LOSS ==="
input int InpQuickTP = 150;                   // Quick TP (points) - เพิ่มขึ้น
input int InpMainTP = 200;                    // Main TP (points) - เพิ่มขึ้น
input int InpInitialSL = 300;                 // Initial SL (points) - SL กว้างขึ้น
input bool InpUseTrailing = false;            // Use Trailing - ปิด
input int InpTrailingStart = 150;             // Trailing Start (points)
input int InpTrailingStep = 50;               // Trailing Step (points)
input bool InpUseBreakeven = false;           // Use Breakeven - ปิด
input int InpBreakevenAt = 120;               // Move to BE at (points)
input int InpBreakevenBuffer = 20;            // BE Buffer (points)
input int InpMinModifyInterval = 60;          // Min seconds between SL modifications

input group "=== RECOVERY SYSTEM ==="
input bool InpUseRecovery = true;             // Enable Recovery
input double InpRecoveryTrigger = -30.0;      // Recovery Trigger ($)
input double InpRecoveryMultiplier = 1.5;     // Recovery Lot Multiplier
input int InpMaxRecoveryLevels = 3;           // Max Recovery Levels
input int InpRecoveryDistance = 150;          // Recovery Distance (points)

input group "=== BASKET MANAGEMENT ==="
input bool InpUseBasketTP = true;             // Close All at Basket Profit
input double InpBasketTP = 5.0;               // Basket Take Profit ($)
input double InpBasketSL = -50.0;             // Basket Stop Loss ($)
input bool InpCloseOpposite = true;           // Close Opposite on Strong Signal

input group "=== FILTERS ==="
input int InpMaxSpread = 35;                  // Max Spread (points)
input int InpStartHour = 2;                   // Start Hour
input int InpEndHour = 22;                    // End Hour
input int InpMinCandleSize = 5;               // Min Candle Size (points)

input group "=== REBATE ==="
input double InpRebateRate = 6.0;             // Rebate Rate ($/lot)

input group "=== SYSTEM ==="
input int InpMagicNumber = 202506;            // Magic Number
input string InpComment = "TrendRider";       // Comment

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

//--- Buffers
double m_ema_fast[];
double m_ema_slow[];
double m_ema_trend[];
double m_adx_main[];
double m_adx_plus[];
double m_adx_minus[];

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
datetime m_last_order_time;  // เวลาเปิด order ล่าสุด

//--- Stats & Rebate
double m_initial_balance;
double m_daily_lots;
double m_daily_rebate;
double m_total_rebate;
int m_daily_trades;
int m_total_orders;
datetime m_day_start;

//--- SL Modification Tracking (ป้องกันการ modify บ่อยเกินไป)
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
    m_trade.SetDeviationInPoints(20);
    m_trade.SetTypeFilling(ORDER_FILLING_IOC);

    // Create indicators
    m_ema_fast_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
    m_ema_slow_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
    m_ema_trend_handle = iMA(_Symbol, PERIOD_CURRENT, InpEMA_Trend, 0, MODE_EMA, PRICE_CLOSE);
    m_adx_handle = iADX(_Symbol, PERIOD_CURRENT, InpADX_Period);

    if(m_ema_fast_handle == INVALID_HANDLE || m_ema_slow_handle == INVALID_HANDLE ||
       m_ema_trend_handle == INVALID_HANDLE || m_adx_handle == INVALID_HANDLE)
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

    Print("=== RebateFarmPro v6.0 - TREND RIDER ===");
    Print("Mode: ", EnumToString(InpMode));
    Print("Max Scale Orders: ", InpMaxScaleOrders);
    Print("Quick TP: ", InpQuickTP, " | Main TP: ", InpMainTP);

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

    // Cleanup dashboard
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

    // Manage existing positions (trailing, BE)
    ManagePositions();

    // Check for new orders - MAIN LOGIC (ไม่ต้องรอ NewBar ใน Aggressive mode)
    if(CanTrade())
    {
        if(InpMode == TREND_FOLLOW_AGGRESSIVE || IsNewBar())
            CheckForEntry();
    }

    // Scaling - add more orders in trend direction
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
    return true;
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

    // Calculate average prices
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

    // Reset
    m_current_trend = 0;
    m_trend_strength = 0;

    // No trend if ADX too low
    if(adx < InpADX_Min)
    {
        m_current_trend = 0;
        return;
    }

    // Determine trend direction
    bool ema_bullish = (ema_fast > ema_slow) && (price > ema_trend);
    bool ema_bearish = (ema_fast < ema_slow) && (price < ema_trend);
    bool di_bullish = di_plus > di_minus;
    bool di_bearish = di_minus > di_plus;

    // BULLISH
    if(ema_bullish && di_bullish)
    {
        m_current_trend = 1;
        if(adx > 40) m_trend_strength = 3;      // Strong
        else if(adx > 30) m_trend_strength = 2; // Normal
        else m_trend_strength = 1;               // Weak
    }
    // BEARISH
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
//| Can trade check                                                  |
//+------------------------------------------------------------------+
bool CanTrade()
{
    int spread = (int)m_symbol.Spread();
    if(spread > InpMaxSpread) return false;

    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    if(dt.hour < InpStartHour || dt.hour >= InpEndHour) return false;
    if(dt.day_of_week == 5 && dt.hour >= 20) return false;
    if(dt.day_of_week == 0 || dt.day_of_week == 6) return false;

    // Check candle size
    double high = iHigh(_Symbol, PERIOD_CURRENT, 1);
    double low = iLow(_Symbol, PERIOD_CURRENT, 1);
    double candle_size = (high - low) / m_symbol.Point();
    if(candle_size < InpMinCandleSize) return false;

    return true;
}

//+------------------------------------------------------------------+
//| Can scale check                                                  |
//+------------------------------------------------------------------+
bool CanScale()
{
    if(!CanTrade()) return false;

    // Rate limit scaling
    datetime current_bar = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(m_last_scale_bar == current_bar) return false;

    return true;
}

//+------------------------------------------------------------------+
//| Check if can open new order (time throttle)                      |
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

    // AGGRESSIVE MODE: เข้าทันทีและต่อเนื่องเมื่อมี trend
    if(InpMode == TREND_FOLLOW_AGGRESSIVE)
    {
        // BUY TREND: EMA Fast > Slow
        if(m_ema_fast[0] > m_ema_slow[0])
        {
            // ปิด Sell ที่ค้างอยู่ถ้าเปิด Close Opposite
            if(InpCloseOpposite && m_state.sell_count > 0)
            {
                CloseAllSells();
            }

            // เปิด Buy ถ้ายังไม่มี หรือถ้าราคาต่ำกว่า order ล่าสุด (average down)
            if(m_state.buy_count == 0)
            {
                OpenBuy(InpBaseLot, "Entry");
                m_last_order_time = TimeCurrent();
            }
        }
        // SELL TREND: EMA Fast < Slow
        else if(m_ema_fast[0] < m_ema_slow[0])
        {
            if(InpCloseOpposite && m_state.buy_count > 0)
            {
                CloseAllBuys();
            }

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
//| Check for scaling (add more orders) - ต่อเนื่องตาม trend         |
//+------------------------------------------------------------------+
void CheckForScale()
{
    if(!CanOpenNewOrder()) return;

    double point = m_symbol.Point();
    double bid = m_symbol.Bid();
    double ask = m_symbol.Ask();

    // SCALE BUY - เพิ่ม order ต่อเนื่องเมื่อ trend ขึ้น
    bool is_buy_trend = (m_ema_fast[0] > m_ema_slow[0]);

    if(is_buy_trend && m_state.buy_count > 0 && m_state.buy_count < InpMaxScaleOrders)
    {
        // วิธี 1: ราคาขึ้นมาจาก lowest buy (pyramid up)
        double dist_from_lowest = (bid - m_state.lowest_buy) / point;

        // วิธี 2: หรือราคาลงมาจาก avg price (average down เพื่อลด avg)
        double dist_from_avg = (m_state.avg_buy_price - ask) / point;

        // เข้าเมื่อราคาขึ้นพอ (pyramid) หรือ ราคาลงมาพอ (average down)
        if(dist_from_lowest >= InpScaleDistance || dist_from_avg >= InpScaleDistance)
        {
            OpenBuy(InpBaseLot, "Scale" + IntegerToString(m_state.buy_count + 1));
            m_last_order_time = TimeCurrent();
        }
    }

    // SCALE SELL - เพิ่ม order ต่อเนื่องเมื่อ trend ลง
    bool is_sell_trend = (m_ema_fast[0] < m_ema_slow[0]);

    if(is_sell_trend && m_state.sell_count > 0 && m_state.sell_count < InpMaxScaleOrders)
    {
        double dist_from_highest = (m_state.highest_sell - bid) / point;
        double dist_from_avg = (ask - m_state.avg_sell_price) / point;

        if(dist_from_highest >= InpScaleDistance || dist_from_avg >= InpScaleDistance)
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
    double sl = price - InpInitialSL * point;  // Initial SL
    double tp = price + InpMainTP * point;

    // Normalize
    lot = NormalizeLot(lot);
    sl = NormalizeDouble(sl, m_symbol.Digits());
    tp = NormalizeDouble(tp, m_symbol.Digits());

    if(m_trade.Buy(lot, _Symbol, price, sl, tp, InpComment + "_" + comment))
    {
        m_daily_trades++;
        m_total_orders++;
        Print("BUY ", lot, " @ ", price, " SL=", sl, " TP=", tp, " [", comment, "]");
    }
}

//+------------------------------------------------------------------+
//| Open Sell                                                        |
//+------------------------------------------------------------------+
void OpenSell(double lot, string comment)
{
    double price = m_symbol.Bid();
    double point = m_symbol.Point();
    double sl = price + InpInitialSL * point;  // Initial SL
    double tp = price - InpMainTP * point;

    lot = NormalizeLot(lot);
    sl = NormalizeDouble(sl, m_symbol.Digits());
    tp = NormalizeDouble(tp, m_symbol.Digits());

    if(m_trade.Sell(lot, _Symbol, price, sl, tp, InpComment + "_" + comment))
    {
        m_daily_trades++;
        m_total_orders++;
        Print("SELL ", lot, " @ ", price, " SL=", sl, " TP=", tp, " [", comment, "]");
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
    // Take profit
    if(m_state.total_profit >= InpBasketTP)
    {
        Print("BASKET TP: $", m_state.total_profit);
        CloseAll();
        m_state.recovery_level = 0;
    }

    // Stop loss
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

    // Check if need recovery for buys
    if(m_state.buy_count > 0 && m_state.buy_profit < InpRecoveryTrigger)
    {
        double price = m_symbol.Ask();
        double dist = (m_state.avg_buy_price - price) / point;

        if(dist >= InpRecoveryDistance)
        {
            // Add recovery buy (average down)
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

    // Check if need recovery for sells
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

    // Find ticket in tracking array
    for(int i = 0; i < m_tracked_count; i++)
    {
        if(m_tracked_tickets[i] == ticket)
        {
            // Check if enough time passed
            if((now - m_last_modify_time[i]) >= InpMinModifyInterval)
                return true;
            else
                return false;
        }
    }

    // Ticket not found = never modified = can modify
    return true;
}

//+------------------------------------------------------------------+
//| Record SL modification time                                       |
//+------------------------------------------------------------------+
void RecordModifyTime(ulong ticket)
{
    datetime now = TimeCurrent();

    // Find existing ticket
    for(int i = 0; i < m_tracked_count; i++)
    {
        if(m_tracked_tickets[i] == ticket)
        {
            m_last_modify_time[i] = now;
            return;
        }
    }

    // Add new ticket
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
    // Remove tickets that are no longer open positions
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
            // Remove from array by shifting
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

    // Cleanup old tracked tickets periodically
    static datetime last_cleanup = 0;
    if(TimeCurrent() - last_cleanup > 60) // Cleanup every minute
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

            // Quick TP - ปิดเพื่อไม่ให้ปิด order เร็วเกินไป
            // ปิดใช้งาน Quick TP - ให้ใช้ Main TP แทน
            /*
            if(profit_pts >= InpQuickTP && m_state.buy_count > 3)
            {
                // ปิด 1 order เพื่อ lock profit
                m_trade.PositionClose(ticket);
                continue;
            }
            */

            // Check if we can modify (time throttle)
            if(!CanModifySL(ticket)) continue;

            // Get minimum stop level from broker
            double stop_level = m_symbol.StopsLevel() * point;
            if(stop_level < 30 * point) stop_level = 30 * point; // minimum 30 pts for safety

            // Breakeven - เฉพาะเมื่อเปิดใช้งาน
            if(InpUseBreakeven && profit_pts >= InpBreakevenAt && current_sl < open_price)
            {
                // BE SL = open + buffer points
                double be_sl = open_price + InpBreakevenBuffer * point;
                be_sl = NormalizeDouble(be_sl, m_symbol.Digits());

                // Validate: SL must be below current price by at least stop_level
                double max_valid_sl = bid - stop_level;
                if(be_sl > max_valid_sl)
                {
                    // Skip - SL would be too close to current price
                    continue;
                }

                // Validate: SL must be far enough from TP
                if(current_tp > 0 && (current_tp - be_sl) < stop_level)
                {
                    // Skip - SL too close to TP
                    continue;
                }

                if(m_trade.PositionModify(ticket, be_sl, current_tp))
                {
                    RecordModifyTime(ticket);
                    Print("BE Set: Ticket #", ticket, " SL=", be_sl, " (buffer=", InpBreakevenBuffer, "pts)");
                }
            }
            // Trailing - เฉพาะเมื่อเปิดใช้งาน
            else if(InpUseTrailing && profit_pts >= InpTrailingStart)
            {
                double new_sl = bid - InpTrailingStep * point;
                new_sl = NormalizeDouble(new_sl, m_symbol.Digits());

                // ห้าม SL ต่ำกว่า Breakeven (ราคาเปิด + buffer)
                double min_sl = open_price + InpBreakevenBuffer * point;
                if(new_sl < min_sl) new_sl = min_sl;

                // Validate against stop level
                double max_valid_sl = bid - stop_level;
                if(new_sl > max_valid_sl) new_sl = max_valid_sl;

                // ต้องห่างจาก current SL มากกว่า trailing step/2 ถึงจะ modify
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

            // Quick TP - ปิดใช้งาน
            /*
            if(profit_pts >= InpQuickTP && m_state.sell_count > 3)
            {
                m_trade.PositionClose(ticket);
                continue;
            }
            */

            // Check if we can modify (time throttle)
            if(!CanModifySL(ticket)) continue;

            // Get minimum stop level from broker
            double stop_level = m_symbol.StopsLevel() * point;
            if(stop_level < 30 * point) stop_level = 30 * point; // minimum 30 pts for safety

            // Breakeven - เฉพาะเมื่อเปิดใช้งาน
            if(InpUseBreakeven && profit_pts >= InpBreakevenAt && (current_sl > open_price || current_sl == 0))
            {
                // BE SL = open - buffer points
                double be_sl = open_price - InpBreakevenBuffer * point;
                be_sl = NormalizeDouble(be_sl, m_symbol.Digits());

                // Validate: SL must be above current price by at least stop_level
                double min_valid_sl = ask + stop_level;
                if(be_sl < min_valid_sl)
                {
                    // Skip - SL would be too close to current price
                    continue;
                }

                // Validate: SL must be far enough from TP
                if(current_tp > 0 && (be_sl - current_tp) < stop_level)
                {
                    // Skip - SL too close to TP
                    continue;
                }

                if(m_trade.PositionModify(ticket, be_sl, current_tp))
                {
                    RecordModifyTime(ticket);
                    Print("BE Set: Ticket #", ticket, " SL=", be_sl, " (buffer=", InpBreakevenBuffer, "pts)");
                }
            }
            // Trailing - เฉพาะเมื่อเปิดใช้งาน
            else if(InpUseTrailing && profit_pts >= InpTrailingStart)
            {
                double new_sl = ask + InpTrailingStep * point;
                new_sl = NormalizeDouble(new_sl, m_symbol.Digits());

                // ห้าม SL สูงกว่า Breakeven (ราคาเปิด - buffer)
                double max_sl = open_price - InpBreakevenBuffer * point;
                if(new_sl > max_sl) new_sl = max_sl;

                // Validate against stop level
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
#define PANEL_WIDTH     280
#define ROW_HEIGHT      18
#define SECTION_GAP     6
#define MARGIN          10
#define COL2            150

// Professional Dark Theme Colors
#define CLR_BG_MAIN     C'25,25,28'
#define CLR_BG_HEADER   C'0,122,255'
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
   int panel_height = 340;

   // Main Background
   CreateRect("main", PANEL_X, y, PANEL_WIDTH, panel_height, CLR_BG_MAIN);

   // Header
   CreateRect("header", PANEL_X, y, PANEL_WIDTH, 32, CLR_BG_HEADER, CLR_BG_HEADER);
   CreateText("title", "TREND RIDER v6.0", PANEL_X + MARGIN, y + 4, CLR_TEXT_WHITE, 11, "Segoe UI Bold");
   CreateText("symbol", _Symbol, PANEL_X + MARGIN, y + 18, C'200,220,255', 8);
   CreateText("status", "●", PANEL_X + PANEL_WIDTH - 24, y + 8, CLR_PROFIT, 12);
   y += 36;

   // TREND Section
   y = CreateSection("sec_trend", "TREND", y);
   y = CreateRow("trend", "Direction", y);
   y = CreateRow("strength", "Strength", y);
   y = CreateRow("adx", "ADX", y);
   y = CreateRow("spread", "Spread", y);
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
//| Destroy Dashboard                                                |
//+------------------------------------------------------------------+
void DestroyDashboard()
{
   ObjectsDeleteAll(0, PANEL_PREFIX);
   g_panel_created = false;
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

   color spread_clr = (spread < 2.0) ? CLR_PROFIT : (spread < 3.5) ? CLR_WARNING : CLR_LOSS;
   UpdateText("spread_val", DoubleToString(spread, 1) + " pips", spread_clr);

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
