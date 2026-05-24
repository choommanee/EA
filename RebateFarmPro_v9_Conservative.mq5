//+------------------------------------------------------------------+
//|                                RebateFarmPro_v9_Conservative.mq5 |
//|                                        Copyright 2025, RebateFarm |
//|     CONSERVATIVE - Wide SL, No Grid, Simple Hedge                |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, RebateFarm"
#property link      "https://www.mql5.com"
#property version   "9.00"
#property description "Conservative Rebate Farming - Minimal Loss"
#property description "Strategy: Simple Hedge, Wide SL, NO Grid"
#property description "Goal: Break-even on trades + Earn rebate"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>

#define PANEL_PREFIX    "ConsPanel_"

//--- Input Parameters
input group "=== MAIN SETTINGS ==="
input double InpLotSize = 0.01;                   // Lot Size (fixed)
input int InpMaxPairs = 3;                        // Max Hedge Pairs (Buy+Sell)

input group "=== TP/SL (WIDE!) ==="
input int InpTP = 800;                            // Take Profit (points) - กว้างขึ้น
input int InpSL = 2000;                           // Stop Loss (points) - กว้างมาก
input double InpBasketTP = 3.0;                   // Basket TP ($) - ต่ำลง
input double InpBasketSL = -50.0;                 // Basket SL ($) - กว้างขึ้น

input group "=== TIMING ==="
input int InpReopenDelay = 300;                   // Delay before reopen (seconds) - 5 นาที!
input int InpMinInterval = 120;                   // Min interval new pair (seconds) - 2 นาที

input group "=== FILTERS ==="
input int InpMaxSpread = 40;                      // Max Spread (points)
input int InpStartHour = 8;                       // Start Hour (London open)
input int InpEndHour = 20;                        // End Hour (before Asia)
input bool InpAvoidHighVolatility = true;         // Avoid high volatility periods

input group "=== REBATE ==="
input double InpRebateRate = 6.0;                 // Rebate Rate ($/lot)

input group "=== SYSTEM ==="
input int InpMagicNumber = 202509;                // Magic Number
input string InpComment = "ConsRebate";           // Order Comment

//--- Global Objects
CTrade         m_trade;
CPositionInfo  m_position;
CAccountInfo   m_account;
CSymbolInfo    m_symbol;

//--- State
int m_buy_count;
int m_sell_count;
double m_buy_volume;
double m_sell_volume;
double m_total_profit;

//--- Timing
datetime m_last_open_time;
datetime m_last_close_time;

//--- Stats
double m_initial_balance;
double m_daily_lots;
double m_daily_rebate;
double m_total_rebate;
int m_daily_trades;
int m_cycles_completed;
datetime m_day_start;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    if(m_account.MarginMode() != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
    {
        Print("ERROR: Hedge account required!");
        return INIT_FAILED;
    }

    if(!m_symbol.Name(_Symbol))
    {
        Print("Error initializing symbol");
        return INIT_FAILED;
    }

    m_trade.SetExpertMagicNumber(InpMagicNumber);
    m_trade.SetDeviationInPoints(30);
    m_trade.SetTypeFilling(ORDER_FILLING_IOC);

    m_initial_balance = m_account.Balance();
    m_day_start = GetDayStart(TimeCurrent());
    m_daily_lots = 0;
    m_daily_rebate = 0;
    m_total_rebate = 0;
    m_daily_trades = 0;
    m_cycles_completed = 0;
    m_last_open_time = 0;
    m_last_close_time = 0;

    Print("=== RebateFarmPro v9.0 - CONSERVATIVE ===");
    Print("Lot: ", InpLotSize, " | Max Pairs: ", InpMaxPairs);
    Print("TP: ", InpTP, " pts ($", InpTP * InpLotSize * 0.01, ")");
    Print("SL: ", InpSL, " pts ($", InpSL * InpLotSize * 0.01, ")");
    Print("Reopen Delay: ", InpReopenDelay, " seconds");

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
    UpdateState();

    // Check basket profit/loss
    CheckBasketClose();

    // Main logic - Simple hedge
    if(CanTrade())
    {
        ManageHedgePairs();
    }

    UpdateRebateTracking();
    UpdateDisplay();
}

//+------------------------------------------------------------------+
//| Update position state                                            |
//+------------------------------------------------------------------+
void UpdateState()
{
    m_buy_count = 0;
    m_sell_count = 0;
    m_buy_volume = 0;
    m_sell_volume = 0;
    m_total_profit = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                double profit = m_position.Profit() + m_position.Swap() + m_position.Commission();
                m_total_profit += profit;

                if(m_position.PositionType() == POSITION_TYPE_BUY)
                {
                    m_buy_count++;
                    m_buy_volume += m_position.Volume();
                }
                else
                {
                    m_sell_count++;
                    m_sell_volume += m_position.Volume();
                }
            }
        }
    }
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

    // Weekend check
    if(dt.day_of_week == 0 || dt.day_of_week == 6) return false;

    // Friday evening
    if(dt.day_of_week == 5 && dt.hour >= 18) return false;

    // High volatility periods (optional)
    if(InpAvoidHighVolatility)
    {
        // Avoid first/last hour
        if(dt.hour == InpStartHour || dt.hour == InpEndHour - 1) return false;
        // Avoid 30 min around major hours
        if((dt.hour == 14 || dt.hour == 15) && dt.min < 30) return false; // US open
    }

    return true;
}

//+------------------------------------------------------------------+
//| Manage hedge pairs - SIMPLE LOGIC                                |
//+------------------------------------------------------------------+
void ManageHedgePairs()
{
    int total_pairs = MathMin(m_buy_count, m_sell_count);
    int unpaired_buys = m_buy_count - total_pairs;
    int unpaired_sells = m_sell_count - total_pairs;

    // Case 1: No positions at all - open new pair
    if(m_buy_count == 0 && m_sell_count == 0)
    {
        // Wait after last close
        if(TimeCurrent() - m_last_close_time < InpReopenDelay)
            return;

        // Wait minimum interval
        if(TimeCurrent() - m_last_open_time < InpMinInterval)
            return;

        OpenHedgePair();
        return;
    }

    // Case 2: Have unpaired buy - wait, don't rush to add sell
    // Let it hit TP or SL naturally

    // Case 3: Have unpaired sell - wait, don't rush to add buy
    // Let it hit TP or SL naturally

    // Case 4: All paired and under max - can add more pairs (but with long delay)
    if(total_pairs < InpMaxPairs && unpaired_buys == 0 && unpaired_sells == 0)
    {
        // Long delay between adding pairs
        if(TimeCurrent() - m_last_open_time >= InpMinInterval * 2)
        {
            OpenHedgePair();
        }
    }
}

//+------------------------------------------------------------------+
//| Open Hedge Pair (Buy + Sell)                                     |
//+------------------------------------------------------------------+
void OpenHedgePair()
{
    double ask = m_symbol.Ask();
    double bid = m_symbol.Bid();
    double point = m_symbol.Point();

    double lot = InpLotSize;

    // Calculate SL/TP - WIDE
    double buy_sl = NormalizeDouble(ask - InpSL * point, m_symbol.Digits());
    double buy_tp = NormalizeDouble(ask + InpTP * point, m_symbol.Digits());
    double sell_sl = NormalizeDouble(bid + InpSL * point, m_symbol.Digits());
    double sell_tp = NormalizeDouble(bid - InpTP * point, m_symbol.Digits());

    bool buy_ok = false;
    bool sell_ok = false;

    // Open BUY
    if(m_trade.Buy(lot, _Symbol, ask, buy_sl, buy_tp, InpComment + "_B"))
    {
        buy_ok = true;
        m_daily_trades++;
        Print("HEDGE BUY: ", lot, " @ ", ask, " SL=", buy_sl, " TP=", buy_tp);
    }

    // Open SELL
    if(m_trade.Sell(lot, _Symbol, bid, sell_sl, sell_tp, InpComment + "_S"))
    {
        sell_ok = true;
        m_daily_trades++;
        Print("HEDGE SELL: ", lot, " @ ", bid, " SL=", sell_sl, " TP=", sell_tp);
    }

    if(buy_ok && sell_ok)
    {
        m_last_open_time = TimeCurrent();
        m_cycles_completed++;
    }
}

//+------------------------------------------------------------------+
//| Check basket profit/loss                                         |
//+------------------------------------------------------------------+
void CheckBasketClose()
{
    int total_pos = m_buy_count + m_sell_count;
    if(total_pos == 0) return;

    // Basket Take Profit
    if(m_total_profit >= InpBasketTP)
    {
        Print("=== BASKET TP: $", DoubleToString(m_total_profit, 2), " ===");
        CloseAll();
        m_last_close_time = TimeCurrent();
        return;
    }

    // Basket Stop Loss
    if(m_total_profit <= InpBasketSL)
    {
        Print("=== BASKET SL: $", DoubleToString(m_total_profit, 2), " ===");
        CloseAll();
        m_last_close_time = TimeCurrent();
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
//| OnTrade - Track closes                                           |
//+------------------------------------------------------------------+
void OnTrade()
{
    static int prev_count = 0;
    int curr_count = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
                curr_count++;
        }
    }

    if(curr_count < prev_count)
    {
        m_last_close_time = TimeCurrent();
    }

    prev_count = curr_count;
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
#define PANEL_WIDTH     280
#define ROW_HEIGHT      18
#define MARGIN          10
#define COL2            150

#define CLR_BG_MAIN     C'25,25,28'
#define CLR_BG_HEADER   C'33,150,83'
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
    int panel_height = 300;

    CreateRect("main", PANEL_X, y, PANEL_WIDTH, panel_height, CLR_BG_MAIN);
    CreateRect("header", PANEL_X, y, PANEL_WIDTH, 32, CLR_BG_HEADER, CLR_BG_HEADER);
    CreateText("title", "CONSERVATIVE v9.0", PANEL_X + MARGIN, y + 4, CLR_TEXT_WHITE, 11, "Segoe UI Bold");
    CreateText("subtitle", "Low Risk Rebate Farm", PANEL_X + MARGIN, y + 18, C'180,220,180', 8);
    CreateText("status", "●", PANEL_X + PANEL_WIDTH - 24, y + 8, CLR_PROFIT, 12);
    y += 36;

    y = CreateSection("sec_pos", "POSITIONS", y);
    y = CreateRow("pairs", "Active Pairs", y);
    y = CreateRow("floating", "Floating P/L", y);
    y = CreateRow("spread", "Spread", y);
    y = CreateRow("nextopen", "Next Open In", y);
    y += 6;

    y = CreateSection("sec_acc", "ACCOUNT", y);
    y = CreateRow("balance", "Balance", y);
    y = CreateRow("equity", "Equity", y);
    y = CreateRow("pnl", "Trading P/L", y);
    y += 6;

    y = CreateSection("sec_rebate", "REBATE", y);
    y = CreateRow("volume", "Today Volume", y);
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
    int total_pos = m_buy_count + m_sell_count;
    color status_clr = total_pos > 0 ? CLR_PROFIT : CLR_TEXT_GRAY;
    UpdateText("status", "●", status_clr);

    // Positions
    int pairs = MathMin(m_buy_count, m_sell_count);
    string pairs_info = IntegerToString(pairs) + "/" + IntegerToString(InpMaxPairs) +
                        " (B:" + IntegerToString(m_buy_count) + " S:" + IntegerToString(m_sell_count) + ")";
    UpdateText("pairs_val", pairs_info, CLR_TEXT_WHITE);

    UpdateText("floating_val", "$" + DoubleToString(m_total_profit, 2),
               m_total_profit >= 0 ? CLR_PROFIT : CLR_LOSS);

    color spread_clr = spread < 3 ? CLR_PROFIT : spread < 4 ? CLR_WARNING : CLR_LOSS;
    UpdateText("spread_val", DoubleToString(spread, 1) + " pips", spread_clr);

    // Next open countdown
    int wait_time = 0;
    if(total_pos == 0)
    {
        int since_close = (int)(TimeCurrent() - m_last_close_time);
        wait_time = InpReopenDelay - since_close;
    }
    else
    {
        int since_open = (int)(TimeCurrent() - m_last_open_time);
        wait_time = InpMinInterval - since_open;
    }
    if(wait_time < 0) wait_time = 0;

    string wait_str = wait_time > 0 ? IntegerToString(wait_time) + "s" : "Ready";
    color wait_clr = wait_time > 0 ? CLR_WARNING : CLR_PROFIT;
    UpdateText("nextopen_val", wait_str, wait_clr);

    // Account
    UpdateText("balance_val", "$" + DoubleToString(balance, 2), CLR_TEXT_WHITE);
    UpdateText("equity_val", "$" + DoubleToString(equity, 2), equity >= balance ? CLR_PROFIT : CLR_LOSS);

    string pnl_str = (profit >= 0 ? "+" : "") + "$" + DoubleToString(profit, 2);
    UpdateText("pnl_val", pnl_str, profit >= 0 ? CLR_PROFIT : CLR_LOSS);

    // Rebate
    UpdateText("volume_val", DoubleToString(m_daily_lots, 2) + " lots (" + IntegerToString(m_daily_trades) + ")", CLR_TEXT_WHITE);
    UpdateText("rebate_val", "$" + DoubleToString(m_daily_rebate + m_total_rebate, 2), CLR_PROFIT);

    string net_str = (net >= 0 ? "+" : "") + "$" + DoubleToString(net, 2);
    UpdateText("net_val", net_str, net >= 0 ? CLR_PROFIT : CLR_LOSS);

    ChartRedraw(0);
}
//+------------------------------------------------------------------+
