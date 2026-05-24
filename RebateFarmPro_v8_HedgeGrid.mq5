//+------------------------------------------------------------------+
//|                                    RebateFarmPro_v8_HedgeGrid.mq5 |
//|                                        Copyright 2025, RebateFarm |
//|     HEDGE + GRID Strategy - Based on Proven Rebate EA Methods    |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, RebateFarm"
#property link      "https://www.mql5.com"
#property version   "8.00"
#property description "Hedge-Grid Rebate Farming EA"
#property description "Strategy: Open Buy+Sell simultaneously, Grid on pullback"
#property description "Goal: High volume + Minimal loss + Maximum rebate"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>

//--- Dashboard Prefix
#define PANEL_PREFIX    "HGPanel_"

//--- Enumerations
enum ENUM_STRATEGY_MODE
{
    MODE_HEDGE_ONLY = 0,      // Hedge Only (Buy+Sell พร้อมกัน)
    MODE_GRID_TREND = 1,      // Grid + Trend Following
    MODE_HEDGE_GRID = 2       // Hedge + Grid Combined (Recommended)
};

//--- Input Parameters
input group "=== STRATEGY ==="
input ENUM_STRATEGY_MODE InpMode = MODE_HEDGE_GRID;  // Strategy Mode
input bool InpAllowHedge = true;                      // Allow Hedge (ต้องเป็น Hedge Account)

input group "=== LOT SIZE ==="
input double InpBaseLot = 0.01;                       // Base Lot Size
input double InpLotMultiplier = 1.5;                  // Lot Multiplier สำหรับ Grid
input double InpMaxLot = 0.5;                         // Max Total Lot Size
input int InpMaxOrders = 10;                          // Max Orders รวม

input group "=== GRID SETTINGS ==="
input int InpGridDistance = 150;                      // Grid Distance (points)
input int InpGridLevels = 5;                          // Max Grid Levels
input int InpMinGridInterval = 60;                    // Min seconds between grid orders

input group "=== TAKE PROFIT ==="
input int InpTPPoints = 100;                          // TP per order (points) - สำหรับ Hedge
input double InpBasketTP = 5.0;                       // Basket TP ($) - ปิดทั้งหมดเมื่อกำไรถึง
input double InpBasketSL = -100.0;                    // Basket SL ($) - ปิดทั้งหมดเมื่อขาดทุนถึง

input group "=== HEDGE SETTINGS ==="
input int InpHedgeSL = 500;                           // Hedge SL (points) - แต่ละ order
input int InpHedgeTP = 300;                           // Hedge TP (points) - แต่ละ order
input int InpReopenDelay = 5;                         // Reopen Delay (seconds) หลังปิด

input group "=== FILTERS ==="
input int InpMaxSpread = 50;                          // Max Spread (points)
input int InpStartHour = 1;                           // Start Hour
input int InpEndHour = 23;                            // End Hour
input bool InpAvoidFriday = true;                     // หลีกเลี่ยงวันศุกร์ตอนเย็น

input group "=== REBATE ==="
input double InpRebateRate = 6.0;                     // Rebate Rate ($/lot)

input group "=== SYSTEM ==="
input int InpMagicNumber = 202508;                    // Magic Number
input string InpComment = "HedgeGrid";                // Order Comment

//--- Global Objects
CTrade         m_trade;
CPositionInfo  m_position;
CAccountInfo   m_account;
CSymbolInfo    m_symbol;

//--- State Variables
struct GridState
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
    double lowest_buy_price;
    double highest_sell_price;
    int buy_grid_level;
    int sell_grid_level;
};
GridState m_state;

//--- Timing
datetime m_last_buy_grid_time;
datetime m_last_sell_grid_time;
datetime m_last_hedge_time;
datetime m_last_order_close_time;

//--- Stats
double m_initial_balance;
double m_daily_lots;
double m_daily_rebate;
double m_total_rebate;
int m_daily_trades;
int m_total_orders;
int m_cycles_completed;
datetime m_day_start;

//--- Hedge State
bool m_hedge_cycle_active;
double m_cycle_start_equity;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Check hedging account
    if(InpAllowHedge && m_account.MarginMode() != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
    {
        Print("WARNING: Hedge mode requires Hedging account type!");
        Print("Current account type: ", EnumToString(m_account.MarginMode()));
        // ไม่ return fail เพราะอาจใช้ Grid only mode
    }

    if(!m_symbol.Name(_Symbol))
    {
        Print("Error initializing symbol");
        return INIT_FAILED;
    }

    m_trade.SetExpertMagicNumber(InpMagicNumber);
    m_trade.SetDeviationInPoints(30);
    m_trade.SetTypeFilling(ORDER_FILLING_IOC);

    // Initialize state
    ZeroMemory(m_state);
    m_initial_balance = m_account.Balance();
    m_day_start = GetDayStart(TimeCurrent());
    m_daily_lots = 0;
    m_daily_rebate = 0;
    m_total_rebate = 0;
    m_daily_trades = 0;
    m_total_orders = 0;
    m_cycles_completed = 0;
    m_hedge_cycle_active = false;
    m_cycle_start_equity = m_account.Equity();

    m_last_buy_grid_time = 0;
    m_last_sell_grid_time = 0;
    m_last_hedge_time = 0;
    m_last_order_close_time = 0;

    Print("=== RebateFarmPro v8.0 - HEDGE GRID ===");
    Print("Mode: ", EnumToString(InpMode));
    Print("Base Lot: ", InpBaseLot, " | Max Lot: ", InpMaxLot);
    Print("Grid Distance: ", InpGridDistance, " pts | Levels: ", InpGridLevels);
    Print("Basket TP: $", InpBasketTP, " | Basket SL: $", InpBasketSL);

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    ObjectsDeleteAll(0, PANEL_PREFIX);
    Comment("");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    m_symbol.RefreshRates();

    // Update state
    UpdateState();

    // Check basket profit/loss - MOST IMPORTANT
    CheckBasketClose();

    // Run strategy
    switch(InpMode)
    {
        case MODE_HEDGE_ONLY:
            RunHedgeStrategy();
            break;
        case MODE_GRID_TREND:
            RunGridStrategy();
            break;
        case MODE_HEDGE_GRID:
            RunHedgeGridStrategy();
            break;
    }

    // Update tracking
    UpdateRebateTracking();

    // Display
    UpdateDisplay();
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
    m_state.lowest_buy_price = DBL_MAX;
    m_state.highest_sell_price = 0;

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
                    if(m_position.PriceOpen() < m_state.lowest_buy_price)
                        m_state.lowest_buy_price = m_position.PriceOpen();
                }
                else
                {
                    m_state.sell_count++;
                    m_state.sell_volume += m_position.Volume();
                    m_state.sell_profit += profit;
                    sell_cost += m_position.PriceOpen() * m_position.Volume();
                    if(m_position.PriceOpen() > m_state.highest_sell_price)
                        m_state.highest_sell_price = m_position.PriceOpen();
                }
            }
        }
    }

    if(m_state.buy_volume > 0)
        m_state.avg_buy_price = buy_cost / m_state.buy_volume;
    if(m_state.sell_volume > 0)
        m_state.avg_sell_price = sell_cost / m_state.sell_volume;

    // Count grid levels
    m_state.buy_grid_level = m_state.buy_count;
    m_state.sell_grid_level = m_state.sell_count;
}

//+------------------------------------------------------------------+
//| Check if can trade                                               |
//+------------------------------------------------------------------+
bool CanTrade()
{
    // Spread check
    int spread = (int)m_symbol.Spread();
    if(spread > InpMaxSpread) return false;

    // Time check
    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    if(dt.hour < InpStartHour || dt.hour >= InpEndHour) return false;

    // Friday evening check
    if(InpAvoidFriday && dt.day_of_week == 5 && dt.hour >= 18) return false;

    // Weekend check
    if(dt.day_of_week == 0 || dt.day_of_week == 6) return false;

    // Max orders check
    int total_orders = m_state.buy_count + m_state.sell_count;
    if(total_orders >= InpMaxOrders) return false;

    // Max lot check
    double total_lots = m_state.buy_volume + m_state.sell_volume;
    if(total_lots >= InpMaxLot) return false;

    return true;
}

//+------------------------------------------------------------------+
//| STRATEGY 1: Hedge Only - Open Buy+Sell simultaneously            |
//+------------------------------------------------------------------+
void RunHedgeStrategy()
{
    if(!CanTrade()) return;

    // Check if we need to open new hedge pair
    bool need_hedge = (m_state.buy_count == 0 && m_state.sell_count == 0);

    // Also reopen if one side closed with profit
    if(m_state.buy_count == 0 && m_state.sell_count > 0)
        need_hedge = true;
    if(m_state.sell_count == 0 && m_state.buy_count > 0)
        need_hedge = true;

    // Delay after order close
    if(TimeCurrent() - m_last_order_close_time < InpReopenDelay)
        return;

    if(need_hedge)
    {
        OpenHedgePair();
    }
}

//+------------------------------------------------------------------+
//| STRATEGY 2: Grid + Trend                                         |
//+------------------------------------------------------------------+
void RunGridStrategy()
{
    if(!CanTrade()) return;

    double point = m_symbol.Point();
    double bid = m_symbol.Bid();
    double ask = m_symbol.Ask();

    // No positions - determine trend and open first order
    if(m_state.buy_count == 0 && m_state.sell_count == 0)
    {
        // Simple trend detection using price vs MA
        double ma[];
        ArraySetAsSeries(ma, true);
        int ma_handle = iMA(_Symbol, PERIOD_CURRENT, 20, 0, MODE_EMA, PRICE_CLOSE);
        if(CopyBuffer(ma_handle, 0, 0, 2, ma) > 0)
        {
            if(bid > ma[0])
                OpenBuy(InpBaseLot, "Grid_Entry");
            else
                OpenSell(InpBaseLot, "Grid_Entry");
        }
        IndicatorRelease(ma_handle);
        return;
    }

    // Grid: Add buy when price drops
    if(m_state.buy_count > 0 && m_state.buy_grid_level < InpGridLevels)
    {
        if(TimeCurrent() - m_last_buy_grid_time >= InpMinGridInterval)
        {
            double dist = (m_state.lowest_buy_price - ask) / point;
            if(dist >= InpGridDistance)
            {
                double lot = CalculateGridLot(m_state.buy_grid_level);
                OpenBuy(lot, "Grid_" + IntegerToString(m_state.buy_grid_level + 1));
                m_last_buy_grid_time = TimeCurrent();
            }
        }
    }

    // Grid: Add sell when price rises
    if(m_state.sell_count > 0 && m_state.sell_grid_level < InpGridLevels)
    {
        if(TimeCurrent() - m_last_sell_grid_time >= InpMinGridInterval)
        {
            double dist = (bid - m_state.highest_sell_price) / point;
            if(dist >= InpGridDistance)
            {
                double lot = CalculateGridLot(m_state.sell_grid_level);
                OpenSell(lot, "Grid_" + IntegerToString(m_state.sell_grid_level + 1));
                m_last_sell_grid_time = TimeCurrent();
            }
        }
    }
}

//+------------------------------------------------------------------+
//| STRATEGY 3: Hedge + Grid Combined (RECOMMENDED)                  |
//+------------------------------------------------------------------+
void RunHedgeGridStrategy()
{
    if(!CanTrade()) return;

    double point = m_symbol.Point();
    double bid = m_symbol.Bid();
    double ask = m_symbol.Ask();

    // STEP 1: Open initial hedge pair if no positions
    if(m_state.buy_count == 0 && m_state.sell_count == 0)
    {
        if(TimeCurrent() - m_last_order_close_time >= InpReopenDelay)
        {
            OpenHedgePair();
            m_hedge_cycle_active = true;
            m_cycle_start_equity = m_account.Equity();
        }
        return;
    }

    // STEP 2: Grid BUY - Add when price drops significantly
    if(m_state.buy_count > 0 && m_state.buy_grid_level < InpGridLevels)
    {
        if(TimeCurrent() - m_last_buy_grid_time >= InpMinGridInterval)
        {
            // Add buy when price drops from lowest buy
            double dist = (m_state.lowest_buy_price - ask) / point;
            if(dist >= InpGridDistance)
            {
                double lot = CalculateGridLot(m_state.buy_grid_level);
                if(OpenBuy(lot, "Grid_B" + IntegerToString(m_state.buy_grid_level + 1)))
                    m_last_buy_grid_time = TimeCurrent();
            }
        }
    }

    // STEP 3: Grid SELL - Add when price rises significantly
    if(m_state.sell_count > 0 && m_state.sell_grid_level < InpGridLevels)
    {
        if(TimeCurrent() - m_last_sell_grid_time >= InpMinGridInterval)
        {
            // Add sell when price rises from highest sell
            double dist = (bid - m_state.highest_sell_price) / point;
            if(dist >= InpGridDistance)
            {
                double lot = CalculateGridLot(m_state.sell_grid_level);
                if(OpenSell(lot, "Grid_S" + IntegerToString(m_state.sell_grid_level + 1)))
                    m_last_sell_grid_time = TimeCurrent();
            }
        }
    }

    // STEP 4: Reopen hedge if one side closed but other remains
    // This maintains volume generation
    if(m_hedge_cycle_active)
    {
        // If buy side cleared but sells remain, add buy
        if(m_state.buy_count == 0 && m_state.sell_count > 0)
        {
            if(TimeCurrent() - m_last_order_close_time >= InpReopenDelay)
            {
                OpenBuy(InpBaseLot, "Rehedge_B");
            }
        }
        // If sell side cleared but buys remain, add sell
        else if(m_state.sell_count == 0 && m_state.buy_count > 0)
        {
            if(TimeCurrent() - m_last_order_close_time >= InpReopenDelay)
            {
                OpenSell(InpBaseLot, "Rehedge_S");
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Open Hedge Pair (Buy + Sell simultaneously)                      |
//+------------------------------------------------------------------+
void OpenHedgePair()
{
    double ask = m_symbol.Ask();
    double bid = m_symbol.Bid();
    double point = m_symbol.Point();

    double lot = NormalizeLot(InpBaseLot);

    // Calculate SL/TP for hedge
    double buy_sl = NormalizeDouble(ask - InpHedgeSL * point, m_symbol.Digits());
    double buy_tp = NormalizeDouble(ask + InpHedgeTP * point, m_symbol.Digits());
    double sell_sl = NormalizeDouble(bid + InpHedgeSL * point, m_symbol.Digits());
    double sell_tp = NormalizeDouble(bid - InpHedgeTP * point, m_symbol.Digits());

    // Open BUY
    if(m_trade.Buy(lot, _Symbol, ask, buy_sl, buy_tp, InpComment + "_HedgeB"))
    {
        m_daily_trades++;
        m_total_orders++;
        Print("HEDGE BUY: ", lot, " @ ", ask, " SL=", buy_sl, " TP=", buy_tp);
    }

    // Open SELL
    if(m_trade.Sell(lot, _Symbol, bid, sell_sl, sell_tp, InpComment + "_HedgeS"))
    {
        m_daily_trades++;
        m_total_orders++;
        Print("HEDGE SELL: ", lot, " @ ", bid, " SL=", sell_sl, " TP=", sell_tp);
    }

    m_last_hedge_time = TimeCurrent();
}

//+------------------------------------------------------------------+
//| Open Buy Order                                                   |
//+------------------------------------------------------------------+
bool OpenBuy(double lot, string comment)
{
    double ask = m_symbol.Ask();
    double point = m_symbol.Point();

    lot = NormalizeLot(lot);

    // Check max lot
    if(m_state.buy_volume + lot > InpMaxLot)
        lot = NormalizeLot(InpMaxLot - m_state.buy_volume);
    if(lot < m_symbol.LotsMin()) return false;

    double sl = NormalizeDouble(ask - InpHedgeSL * point, m_symbol.Digits());
    double tp = NormalizeDouble(ask + InpHedgeTP * point, m_symbol.Digits());

    if(m_trade.Buy(lot, _Symbol, ask, sl, tp, InpComment + "_" + comment))
    {
        m_daily_trades++;
        m_total_orders++;
        Print("BUY: ", lot, " @ ", ask, " [", comment, "]");
        return true;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Open Sell Order                                                  |
//+------------------------------------------------------------------+
bool OpenSell(double lot, string comment)
{
    double bid = m_symbol.Bid();
    double point = m_symbol.Point();

    lot = NormalizeLot(lot);

    // Check max lot
    if(m_state.sell_volume + lot > InpMaxLot)
        lot = NormalizeLot(InpMaxLot - m_state.sell_volume);
    if(lot < m_symbol.LotsMin()) return false;

    double sl = NormalizeDouble(bid + InpHedgeSL * point, m_symbol.Digits());
    double tp = NormalizeDouble(bid - InpHedgeTP * point, m_symbol.Digits());

    if(m_trade.Sell(lot, _Symbol, bid, sl, tp, InpComment + "_" + comment))
    {
        m_daily_trades++;
        m_total_orders++;
        Print("SELL: ", lot, " @ ", bid, " [", comment, "]");
        return true;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Calculate Grid Lot Size                                          |
//+------------------------------------------------------------------+
double CalculateGridLot(int level)
{
    double lot = InpBaseLot;

    // Apply multiplier for each level
    for(int i = 0; i < level; i++)
    {
        lot *= InpLotMultiplier;
    }

    // Cap at max lot
    lot = MathMin(lot, InpMaxLot - m_state.buy_volume - m_state.sell_volume);

    return NormalizeLot(lot);
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
//| Check basket profit/loss for closing                             |
//+------------------------------------------------------------------+
void CheckBasketClose()
{
    // Basket Take Profit - ปิดทั้งหมดเมื่อกำไรถึงเป้า
    if(m_state.total_profit >= InpBasketTP && (m_state.buy_count + m_state.sell_count) > 0)
    {
        Print("=== BASKET TP HIT: $", DoubleToString(m_state.total_profit, 2), " ===");
        CloseAll();
        m_cycles_completed++;
        m_hedge_cycle_active = false;
        m_last_order_close_time = TimeCurrent();
        return;
    }

    // Basket Stop Loss - ปิดทั้งหมดเมื่อขาดทุนถึงเป้า
    if(m_state.total_profit <= InpBasketSL && (m_state.buy_count + m_state.sell_count) > 0)
    {
        Print("=== BASKET SL HIT: $", DoubleToString(m_state.total_profit, 2), " ===");
        CloseAll();
        m_cycles_completed++;
        m_hedge_cycle_active = false;
        m_last_order_close_time = TimeCurrent();
        return;
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
//| OnTrade - Track when orders close                                |
//+------------------------------------------------------------------+
void OnTrade()
{
    static int prev_positions = 0;
    int curr_positions = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
                curr_positions++;
        }
    }

    // If position count decreased, record close time
    if(curr_positions < prev_positions)
    {
        m_last_order_close_time = TimeCurrent();
    }

    prev_positions = curr_positions;
    UpdateState();
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
//| Dashboard                                                        |
//+------------------------------------------------------------------+
#define PANEL_X         20
#define PANEL_Y         30
#define PANEL_WIDTH     320
#define ROW_HEIGHT      18
#define MARGIN          10
#define COL2            170

#define CLR_BG_MAIN     C'25,25,28'
#define CLR_BG_HEADER   C'156,39,176'
#define CLR_BG_SECTION  C'38,38,42'
#define CLR_TEXT_WHITE  C'255,255,255'
#define CLR_TEXT_GRAY   C'155,155,160'
#define CLR_PROFIT      C'50,205,50'
#define CLR_LOSS        C'255,82,82'
#define CLR_WARNING     C'255,193,7'

bool g_panel_created = false;

void CreateRect(string name, int x, int y, int w, int h, color bg, color border = C'55,55,60')
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
}

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

void UpdateText(string name, string text, color clr = CLR_TEXT_WHITE)
{
    string obj_name = PANEL_PREFIX + name;
    ObjectSetString(0, obj_name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clr);
}

int CreateSection(string name, string title, int y)
{
    CreateRect(name + "_bg", PANEL_X + 4, y, PANEL_WIDTH - 8, 22, CLR_BG_SECTION, CLR_BG_SECTION);
    CreateText(name + "_title", title, PANEL_X + MARGIN, y + 4, CLR_TEXT_GRAY, 9, "Segoe UI Semibold");
    return y + 24;
}

int CreateRow(string name, string label, int y)
{
    CreateText(name + "_lbl", label, PANEL_X + MARGIN, y, C'120,120,125', 9);
    CreateText(name + "_val", "-", PANEL_X + COL2, y, CLR_TEXT_WHITE, 9, "Consolas");
    return y + ROW_HEIGHT;
}

void CreateDashboard()
{
    if(g_panel_created) return;

    int y = PANEL_Y;
    int panel_height = 360;

    CreateRect("main", PANEL_X, y, PANEL_WIDTH, panel_height, CLR_BG_MAIN);
    CreateRect("header", PANEL_X, y, PANEL_WIDTH, 32, CLR_BG_HEADER, CLR_BG_HEADER);
    CreateText("title", "HEDGE-GRID v8.0", PANEL_X + MARGIN, y + 4, CLR_TEXT_WHITE, 11, "Segoe UI Bold");
    CreateText("mode", EnumToString(InpMode), PANEL_X + MARGIN, y + 18, C'220,180,255', 8);
    CreateText("status", "●", PANEL_X + PANEL_WIDTH - 24, y + 8, CLR_PROFIT, 12);
    y += 36;

    y = CreateSection("sec_pos", "POSITIONS", y);
    y = CreateRow("buy", "Buy Orders", y);
    y = CreateRow("sell", "Sell Orders", y);
    y = CreateRow("floating", "Floating P/L", y);
    y = CreateRow("spread", "Spread", y);
    y += 6;

    y = CreateSection("sec_grid", "GRID STATUS", y);
    y = CreateRow("buy_grid", "Buy Grid Level", y);
    y = CreateRow("sell_grid", "Sell Grid Level", y);
    y = CreateRow("cycles", "Cycles Completed", y);
    y += 6;

    y = CreateSection("sec_acc", "ACCOUNT", y);
    y = CreateRow("balance", "Balance", y);
    y = CreateRow("equity", "Equity", y);
    y = CreateRow("pnl", "Trading P/L", y);
    y += 6;

    y = CreateSection("sec_rebate", "REBATE", y);
    y = CreateRow("today", "Today Volume", y);
    y = CreateRow("rebate", "Est. Rebate", y);
    y = CreateRow("net", "Net Result", y);

    g_panel_created = true;
    ChartRedraw(0);
}

void UpdateDisplay()
{
    if(!g_panel_created) CreateDashboard();

    double balance = m_account.Balance();
    double equity = m_account.Equity();
    double profit = balance - m_initial_balance;
    double spread = m_symbol.Spread() / 10.0;
    double net = profit + m_daily_rebate + m_total_rebate;

    // Status
    int total_pos = m_state.buy_count + m_state.sell_count;
    color status_clr = total_pos > 0 ? CLR_PROFIT : CLR_TEXT_GRAY;
    UpdateText("status", "●", status_clr);

    // Positions
    string buy_info = IntegerToString(m_state.buy_count) + " | " + DoubleToString(m_state.buy_volume, 2) + " lots";
    UpdateText("buy_val", buy_info, m_state.buy_profit >= 0 ? CLR_PROFIT : CLR_LOSS);

    string sell_info = IntegerToString(m_state.sell_count) + " | " + DoubleToString(m_state.sell_volume, 2) + " lots";
    UpdateText("sell_val", sell_info, m_state.sell_profit >= 0 ? CLR_PROFIT : CLR_LOSS);

    UpdateText("floating_val", "$" + DoubleToString(m_state.total_profit, 2),
               m_state.total_profit >= 0 ? CLR_PROFIT : CLR_LOSS);

    color spread_clr = spread < 3 ? CLR_PROFIT : spread < 5 ? CLR_WARNING : CLR_LOSS;
    UpdateText("spread_val", DoubleToString(spread, 1) + " pips", spread_clr);

    // Grid
    UpdateText("buy_grid_val", IntegerToString(m_state.buy_grid_level) + "/" + IntegerToString(InpGridLevels), CLR_TEXT_WHITE);
    UpdateText("sell_grid_val", IntegerToString(m_state.sell_grid_level) + "/" + IntegerToString(InpGridLevels), CLR_TEXT_WHITE);
    UpdateText("cycles_val", IntegerToString(m_cycles_completed), CLR_PROFIT);

    // Account
    UpdateText("balance_val", "$" + DoubleToString(balance, 2), CLR_TEXT_WHITE);
    UpdateText("equity_val", "$" + DoubleToString(equity, 2), equity >= balance ? CLR_PROFIT : CLR_LOSS);

    string pnl_str = (profit >= 0 ? "+" : "") + "$" + DoubleToString(profit, 2);
    UpdateText("pnl_val", pnl_str, profit >= 0 ? CLR_PROFIT : CLR_LOSS);

    // Rebate
    UpdateText("today_val", DoubleToString(m_daily_lots, 2) + " lots (" + IntegerToString(m_daily_trades) + " trades)", CLR_TEXT_WHITE);
    UpdateText("rebate_val", "$" + DoubleToString(m_daily_rebate + m_total_rebate, 2), CLR_PROFIT);

    string net_str = (net >= 0 ? "+" : "") + "$" + DoubleToString(net, 2);
    UpdateText("net_val", net_str, net >= 0 ? CLR_PROFIT : CLR_LOSS);

    ChartRedraw(0);
}
//+------------------------------------------------------------------+
