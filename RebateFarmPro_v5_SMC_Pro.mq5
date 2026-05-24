//+------------------------------------------------------------------+
//|                                      RebateFarmPro_v5_SMC_Pro.mq5 |
//|                                        Copyright 2025, RebateFarm |
//|        Professional SMC: FVG, OB, Liquidity, Structure (HH/LL)   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, RebateFarm"
#property link      "https://www.mql5.com"
#property version   "5.00"
#property description "SMC Pro: FVG + Order Block + Liquidity Sweep + Structure"
#property description "Entry: Wait for liquidity grab then enter at OB/FVG"

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

enum ENUM_SMC_ENTRY
{
    ENTRY_OB_ONLY = 0,       // Order Block Only
    ENTRY_FVG_ONLY = 1,      // FVG Only
    ENTRY_OB_FVG = 2,        // OB + FVG (แนะนำ)
    ENTRY_LQ_SWEEP = 3       // Liquidity Sweep + OB
};

enum ENUM_MARKET_STRUCTURE
{
    STRUCTURE_BULLISH = 1,   // HH + HL
    STRUCTURE_BEARISH = -1,  // LH + LL
    STRUCTURE_RANGING = 0    // No clear structure
};

//--- Input Parameters
input group "=== SMC STRUCTURE SETTINGS ==="
input ENUM_TIMEFRAMES InpHTF = PERIOD_H1;               // Higher TF (Structure)
input ENUM_TIMEFRAMES InpLTF = PERIOD_M5;               // Lower TF (Entry)
input int InpSwingLookback = 20;                        // Swing Point Lookback
input int InpSwingStrength = 3;                         // Swing Strength (bars each side)
input int InpStructureShift = 2;                        // Min bars for structure confirm

input group "=== SMC ENTRY SETTINGS ==="
input ENUM_SMC_ENTRY InpEntryType = ENTRY_OB_FVG;       // Entry Type
input int InpOBLookback = 15;                           // Order Block Lookback
input int InpFVGLookback = 10;                          // FVG Lookback
input double InpOBMinSize = 5.0;                        // Min OB Size (points)
input double InpFVGMinSize = 5.0;                       // Min FVG Size (points)
input bool InpRequireLiqSweep = true;                   // Require Liquidity Sweep
input int InpLiqSweepPoints = 20;                       // Liquidity Sweep Min (points)

input group "=== RISK MANAGEMENT ==="
input double InpLotSize = 0.01;                         // Lot Size
input int InpStopLoss = 100;                            // Stop Loss (points)
input int InpTakeProfit = 150;                          // Take Profit (points)
input int InpBreakevenTrigger = 50;                     // Move to BE after (points)
input int InpBreakevenPlus = 5;                         // BE + buffer (points)
input bool InpUseTrailing = true;                       // Use Trailing
input int InpTrailingStep = 40;                         // Trailing Step (points)
input int InpMaxPositions = 3;                          // Max Positions

input group "=== FILTERS ==="
input int InpMaxSpread = 30;                            // Max Spread (points)
input int InpStartHour = 3;                             // Start Hour
input int InpEndHour = 21;                              // End Hour
input int InpMinBarsBetweenTrades = 5;                  // Min bars between trades

input group "=== REBATE ==="
input bool InpEnableRebate = true;                      // Enable Rebate
input ENUM_ACCOUNT_TYPE InpAccountType = ACCOUNT_ULTRA; // Account Type
input double InpRebateRate = 6.0;                       // Rebate ($/lot)

input group "=== SYSTEM ==="
input int InpMagicNumber = 202505;                      // Magic Number
input string InpComment = "SMC_Pro";                    // Comment
input bool InpShowVisuals = true;                       // Show Chart Objects

//--- Global Objects
CTrade         m_trade;
CPositionInfo  m_position;
CAccountInfo   m_account;
CSymbolInfo    m_symbol;

//--- Swing Point Structure
struct SwingPoint
{
    double price;
    datetime time;
    int bar_index;
    bool is_high;      // true = swing high, false = swing low
    bool is_broken;    // ถูก break แล้วหรือยัง
};

//--- Order Block Structure
struct OrderBlock
{
    double top;
    double bottom;
    datetime time;
    int bar_index;
    bool is_bullish;   // true = bullish OB (demand), false = bearish OB (supply)
    bool is_valid;
    bool is_tested;    // ราคากลับมา test แล้วหรือยัง
};

//--- FVG Structure
struct FairValueGap
{
    double top;
    double bottom;
    datetime time;
    int bar_index;
    bool is_bullish;   // true = bullish FVG, false = bearish FVG
    bool is_valid;
    bool is_filled;    // ถูก fill แล้วหรือยัง
};

//--- Liquidity Structure
struct LiquidityLevel
{
    double price;
    datetime time;
    int touches;       // จำนวนครั้งที่ราคาแตะ
    bool is_swept;     // ถูก sweep แล้วหรือยัง
    bool is_high;      // true = liquidity above (buy stops), false = below (sell stops)
};

//--- Market Structure
struct MarketStructure
{
    SwingPoint swing_highs[10];
    SwingPoint swing_lows[10];
    int high_count;
    int low_count;
    ENUM_MARKET_STRUCTURE trend;
    double last_hh;    // Last Higher High
    double last_hl;    // Last Higher Low
    double last_lh;    // Last Lower High
    double last_ll;    // Last Lower Low
    bool bos_bullish;  // Break of Structure bullish
    bool bos_bearish;  // Break of Structure bearish
    bool choch;        // Change of Character
};

//--- SMC Analysis
struct SMCAnalysis
{
    MarketStructure htf_structure;
    MarketStructure ltf_structure;
    OrderBlock bull_ob;
    OrderBlock bear_ob;
    FairValueGap bull_fvg;
    FairValueGap bear_fvg;
    LiquidityLevel liq_high;
    LiquidityLevel liq_low;
    bool liq_swept_high;
    bool liq_swept_low;
};

SMCAnalysis m_smc;

//--- State
int m_positions_count;
double m_total_profit;
datetime m_last_trade_bar;
double m_initial_balance;

//--- Rebate
double m_daily_lots;
double m_daily_rebate;
double m_total_rebate;
int m_daily_trades;
datetime m_day_start;

//--- Stats
int m_win_count;
int m_loss_count;
int m_be_count;

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

    // Initialize
    ZeroMemory(m_smc);
    m_initial_balance = m_account.Balance();
    m_day_start = GetDayStart(TimeCurrent());
    m_last_trade_bar = 0;
    m_win_count = 0;
    m_loss_count = 0;
    m_be_count = 0;

    Print("=== RebateFarmPro v5.0 - SMC Pro Edition ===");
    Print("Entry: ", EnumToString(InpEntryType));
    Print("HTF: ", EnumToString(InpHTF), " | LTF: ", EnumToString(InpLTF));
    Print("Require Liquidity Sweep: ", InpRequireLiqSweep ? "Yes" : "No");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    ObjectsDeleteAll(0, "SMC_");
    Comment("");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    m_symbol.RefreshRates();

    // Update SMC Analysis
    AnalyzeMarketStructure(InpHTF, m_smc.htf_structure);
    AnalyzeMarketStructure(InpLTF, m_smc.ltf_structure);
    FindOrderBlocks();
    FindFVGs();
    FindLiquidityLevels();
    CheckLiquiditySweep();

    // Update state
    UpdateState();

    // Manage positions
    ManagePositions();

    // Check for new trades
    if(CanTrade())
        CheckForEntry();

    // Update rebate
    UpdateRebateTracking();

    // Display
    UpdateDisplay();

    // Draw visuals
    if(InpShowVisuals)
        DrawSMCObjects();
}

//+------------------------------------------------------------------+
//| Analyze Market Structure - Find HH, HL, LH, LL                  |
//+------------------------------------------------------------------+
void AnalyzeMarketStructure(ENUM_TIMEFRAMES tf, MarketStructure &structure)
{
    double high[], low[], close[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);

    int bars = InpSwingLookback + 20;
    if(CopyHigh(_Symbol, tf, 0, bars, high) <= 0) return;
    if(CopyLow(_Symbol, tf, 0, bars, low) <= 0) return;
    if(CopyClose(_Symbol, tf, 0, bars, close) <= 0) return;

    // Reset
    structure.high_count = 0;
    structure.low_count = 0;
    structure.bos_bullish = false;
    structure.bos_bearish = false;
    structure.choch = false;

    // Find Swing Points
    for(int i = InpSwingStrength; i < InpSwingLookback - InpSwingStrength; i++)
    {
        // Check Swing High
        bool is_swing_high = true;
        for(int j = 1; j <= InpSwingStrength; j++)
        {
            if(high[i] <= high[i-j] || high[i] <= high[i+j])
            {
                is_swing_high = false;
                break;
            }
        }

        if(is_swing_high && structure.high_count < 10)
        {
            structure.swing_highs[structure.high_count].price = high[i];
            structure.swing_highs[structure.high_count].time = iTime(_Symbol, tf, i);
            structure.swing_highs[structure.high_count].bar_index = i;
            structure.swing_highs[structure.high_count].is_high = true;
            structure.swing_highs[structure.high_count].is_broken = (close[0] > high[i]);
            structure.high_count++;
        }

        // Check Swing Low
        bool is_swing_low = true;
        for(int j = 1; j <= InpSwingStrength; j++)
        {
            if(low[i] >= low[i-j] || low[i] >= low[i+j])
            {
                is_swing_low = false;
                break;
            }
        }

        if(is_swing_low && structure.low_count < 10)
        {
            structure.swing_lows[structure.low_count].price = low[i];
            structure.swing_lows[structure.low_count].time = iTime(_Symbol, tf, i);
            structure.swing_lows[structure.low_count].bar_index = i;
            structure.swing_lows[structure.low_count].is_high = false;
            structure.swing_lows[structure.low_count].is_broken = (close[0] < low[i]);
            structure.low_count++;
        }
    }

    // Determine Market Structure (HH/HL or LH/LL)
    DetermineStructure(structure, close[0]);
}

//+------------------------------------------------------------------+
//| Determine if HH/HL (bullish) or LH/LL (bearish)                 |
//+------------------------------------------------------------------+
void DetermineStructure(MarketStructure &structure, double current_price)
{
    if(structure.high_count < 2 || structure.low_count < 2)
    {
        structure.trend = STRUCTURE_RANGING;
        return;
    }

    // Get recent swing points
    double sh1 = structure.swing_highs[0].price;  // Most recent swing high
    double sh2 = structure.swing_highs[1].price;  // Previous swing high
    double sl1 = structure.swing_lows[0].price;   // Most recent swing low
    double sl2 = structure.swing_lows[1].price;   // Previous swing low

    // Check for Higher Highs & Higher Lows (Bullish)
    bool hh = (sh1 > sh2);
    bool hl = (sl1 > sl2);

    // Check for Lower Highs & Lower Lows (Bearish)
    bool lh = (sh1 < sh2);
    bool ll = (sl1 < sl2);

    // Store values
    if(hh) structure.last_hh = sh1;
    if(hl) structure.last_hl = sl1;
    if(lh) structure.last_lh = sh1;
    if(ll) structure.last_ll = sl1;

    // Determine trend
    if(hh && hl)
    {
        structure.trend = STRUCTURE_BULLISH;
        // Check for BOS (Break of Structure) - price breaks above recent high
        if(current_price > sh1)
            structure.bos_bullish = true;
    }
    else if(lh && ll)
    {
        structure.trend = STRUCTURE_BEARISH;
        // Check for BOS - price breaks below recent low
        if(current_price < sl1)
            structure.bos_bearish = true;
    }
    else
    {
        structure.trend = STRUCTURE_RANGING;

        // Check for CHoCH (Change of Character)
        // Bullish CHoCH: Was making LL, now breaks above LH
        if(ll && current_price > sh1)
        {
            structure.choch = true;
            structure.trend = STRUCTURE_BULLISH;
        }
        // Bearish CHoCH: Was making HH, now breaks below HL
        if(hh && current_price < sl1)
        {
            structure.choch = true;
            structure.trend = STRUCTURE_BEARISH;
        }
    }
}

//+------------------------------------------------------------------+
//| Find Order Blocks                                                |
//+------------------------------------------------------------------+
void FindOrderBlocks()
{
    double high[], low[], close[], open[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);
    ArraySetAsSeries(open, true);

    if(CopyHigh(_Symbol, InpLTF, 0, InpOBLookback + 5, high) <= 0) return;
    if(CopyLow(_Symbol, InpLTF, 0, InpOBLookback + 5, low) <= 0) return;
    if(CopyClose(_Symbol, InpLTF, 0, InpOBLookback + 5, close) <= 0) return;
    if(CopyOpen(_Symbol, InpLTF, 0, InpOBLookback + 5, open) <= 0) return;

    double point = m_symbol.Point();
    double min_size = InpOBMinSize * point;
    double bid = m_symbol.Bid();

    // Reset OBs
    m_smc.bull_ob.is_valid = false;
    m_smc.bear_ob.is_valid = false;

    for(int i = 2; i < InpOBLookback; i++)
    {
        // BULLISH OB: Last bearish candle before strong bullish move
        // The candle that "created" the demand zone
        if(!m_smc.bull_ob.is_valid)
        {
            bool is_bearish_candle = (close[i] < open[i]);
            bool followed_by_bullish = (close[i-1] > open[i-1]);
            bool strong_move = (close[i-1] > high[i]); // Breaks above the OB

            if(is_bearish_candle && followed_by_bullish && strong_move)
            {
                double ob_size = high[i] - low[i];
                if(ob_size >= min_size)
                {
                    m_smc.bull_ob.top = high[i];
                    m_smc.bull_ob.bottom = low[i];
                    m_smc.bull_ob.time = iTime(_Symbol, InpLTF, i);
                    m_smc.bull_ob.bar_index = i;
                    m_smc.bull_ob.is_bullish = true;
                    m_smc.bull_ob.is_valid = true;
                    m_smc.bull_ob.is_tested = (bid <= m_smc.bull_ob.top && bid >= m_smc.bull_ob.bottom);
                }
            }
        }

        // BEARISH OB: Last bullish candle before strong bearish move
        if(!m_smc.bear_ob.is_valid)
        {
            bool is_bullish_candle = (close[i] > open[i]);
            bool followed_by_bearish = (close[i-1] < open[i-1]);
            bool strong_move = (close[i-1] < low[i]); // Breaks below the OB

            if(is_bullish_candle && followed_by_bearish && strong_move)
            {
                double ob_size = high[i] - low[i];
                if(ob_size >= min_size)
                {
                    m_smc.bear_ob.top = high[i];
                    m_smc.bear_ob.bottom = low[i];
                    m_smc.bear_ob.time = iTime(_Symbol, InpLTF, i);
                    m_smc.bear_ob.bar_index = i;
                    m_smc.bear_ob.is_bullish = false;
                    m_smc.bear_ob.is_valid = true;
                    m_smc.bear_ob.is_tested = (bid <= m_smc.bear_ob.top && bid >= m_smc.bear_ob.bottom);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Find Fair Value Gaps (FVG / Imbalance)                          |
//+------------------------------------------------------------------+
void FindFVGs()
{
    double high[], low[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);

    if(CopyHigh(_Symbol, InpLTF, 0, InpFVGLookback + 3, high) <= 0) return;
    if(CopyLow(_Symbol, InpLTF, 0, InpFVGLookback + 3, low) <= 0) return;

    double point = m_symbol.Point();
    double min_size = InpFVGMinSize * point;
    double bid = m_symbol.Bid();

    // Reset FVGs
    m_smc.bull_fvg.is_valid = false;
    m_smc.bear_fvg.is_valid = false;

    for(int i = 1; i < InpFVGLookback; i++)
    {
        // BULLISH FVG: Gap between candle[i+1] high and candle[i-1] low
        // (Price moved up so fast it left a gap)
        if(!m_smc.bull_fvg.is_valid)
        {
            double fvg_bottom = high[i+1];  // High of 2 bars ago
            double fvg_top = low[i-1];       // Low of current bar

            if(fvg_top > fvg_bottom) // There's a gap
            {
                double gap_size = fvg_top - fvg_bottom;
                if(gap_size >= min_size)
                {
                    m_smc.bull_fvg.top = fvg_top;
                    m_smc.bull_fvg.bottom = fvg_bottom;
                    m_smc.bull_fvg.time = iTime(_Symbol, InpLTF, i);
                    m_smc.bull_fvg.bar_index = i;
                    m_smc.bull_fvg.is_bullish = true;
                    m_smc.bull_fvg.is_valid = true;
                    m_smc.bull_fvg.is_filled = (bid < fvg_top && bid > fvg_bottom);
                }
            }
        }

        // BEARISH FVG: Gap between candle[i-1] high and candle[i+1] low
        if(!m_smc.bear_fvg.is_valid)
        {
            double fvg_top = low[i+1];      // Low of 2 bars ago
            double fvg_bottom = high[i-1];   // High of current bar

            if(fvg_top > fvg_bottom) // There's a gap
            {
                double gap_size = fvg_top - fvg_bottom;
                if(gap_size >= min_size)
                {
                    m_smc.bear_fvg.top = fvg_top;
                    m_smc.bear_fvg.bottom = fvg_bottom;
                    m_smc.bear_fvg.time = iTime(_Symbol, InpLTF, i);
                    m_smc.bear_fvg.bar_index = i;
                    m_smc.bear_fvg.is_bullish = false;
                    m_smc.bear_fvg.is_valid = true;
                    m_smc.bear_fvg.is_filled = (bid > fvg_bottom && bid < fvg_top);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Find Liquidity Levels (Equal Highs/Lows, Swing Points)          |
//+------------------------------------------------------------------+
void FindLiquidityLevels()
{
    // Liquidity = areas where stop losses are likely to be
    // Above recent highs = buy stop liquidity
    // Below recent lows = sell stop liquidity

    // Use HTF swing points as liquidity levels
    if(m_smc.htf_structure.high_count > 0)
    {
        m_smc.liq_high.price = m_smc.htf_structure.swing_highs[0].price;
        m_smc.liq_high.time = m_smc.htf_structure.swing_highs[0].time;
        m_smc.liq_high.is_high = true;
        m_smc.liq_high.is_swept = false;
    }

    if(m_smc.htf_structure.low_count > 0)
    {
        m_smc.liq_low.price = m_smc.htf_structure.swing_lows[0].price;
        m_smc.liq_low.time = m_smc.htf_structure.swing_lows[0].time;
        m_smc.liq_low.is_high = false;
        m_smc.liq_low.is_swept = false;
    }
}

//+------------------------------------------------------------------+
//| Check for Liquidity Sweep                                       |
//+------------------------------------------------------------------+
void CheckLiquiditySweep()
{
    double high[], low[], close[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);

    if(CopyHigh(_Symbol, InpLTF, 0, 10, high) <= 0) return;
    if(CopyLow(_Symbol, InpLTF, 0, 10, low) <= 0) return;
    if(CopyClose(_Symbol, InpLTF, 0, 10, close) <= 0) return;

    double point = m_symbol.Point();
    double sweep_dist = InpLiqSweepPoints * point;

    m_smc.liq_swept_high = false;
    m_smc.liq_swept_low = false;

    // Check if price swept above liquidity high then closed below
    // (Grabbed buy stops then reversed)
    if(m_smc.liq_high.price > 0)
    {
        for(int i = 1; i < 5; i++)
        {
            // Price wicked above liquidity level
            if(high[i] > m_smc.liq_high.price + sweep_dist)
            {
                // But closed below it (rejection)
                if(close[i] < m_smc.liq_high.price)
                {
                    m_smc.liq_swept_high = true;
                    m_smc.liq_high.is_swept = true;
                    break;
                }
            }
        }
    }

    // Check if price swept below liquidity low then closed above
    if(m_smc.liq_low.price > 0)
    {
        for(int i = 1; i < 5; i++)
        {
            // Price wicked below liquidity level
            if(low[i] < m_smc.liq_low.price - sweep_dist)
            {
                // But closed above it (rejection)
                if(close[i] > m_smc.liq_low.price)
                {
                    m_smc.liq_swept_low = true;
                    m_smc.liq_low.is_swept = true;
                    break;
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Update state                                                     |
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
//| Can trade check                                                  |
//+------------------------------------------------------------------+
bool CanTrade()
{
    if(m_positions_count >= InpMaxPositions) return false;

    int spread = (int)m_symbol.Spread();
    if(spread > InpMaxSpread) return false;

    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);
    if(dt.hour < InpStartHour || dt.hour >= InpEndHour) return false;
    if(dt.day_of_week == 5 && dt.hour >= 20) return false;
    if(dt.day_of_week == 0 || dt.day_of_week == 6) return false;

    datetime current_bar = iTime(_Symbol, InpLTF, 0);
    if(m_last_trade_bar == current_bar) return false;

    int bars_since = iBarShift(_Symbol, InpLTF, m_last_trade_bar);
    if(bars_since < InpMinBarsBetweenTrades && m_last_trade_bar > 0) return false;

    return true;
}

//+------------------------------------------------------------------+
//| Check for entry                                                  |
//+------------------------------------------------------------------+
void CheckForEntry()
{
    int signal = GetSMCSignal();

    if(signal == 1)
        OpenBuy();
    else if(signal == -1)
        OpenSell();
}

//+------------------------------------------------------------------+
//| Get SMC Signal                                                   |
//+------------------------------------------------------------------+
int GetSMCSignal()
{
    double bid = m_symbol.Bid();
    double ask = m_symbol.Ask();

    // ===== BUY CONDITIONS =====
    // 1. HTF structure must be bullish (HH + HL)
    // 2. LTF confirms with BOS or CHoCH
    // 3. Price at OB or FVG
    // 4. (Optional) Liquidity swept below

    bool htf_bullish = (m_smc.htf_structure.trend == STRUCTURE_BULLISH);
    bool ltf_bullish = (m_smc.ltf_structure.trend == STRUCTURE_BULLISH ||
                        m_smc.ltf_structure.bos_bullish ||
                        m_smc.ltf_structure.choch);

    // Check if price is at entry zone
    bool at_bull_ob = m_smc.bull_ob.is_valid &&
                      bid >= m_smc.bull_ob.bottom &&
                      bid <= m_smc.bull_ob.top;

    bool at_bull_fvg = m_smc.bull_fvg.is_valid &&
                       bid >= m_smc.bull_fvg.bottom &&
                       bid <= m_smc.bull_fvg.top;

    bool liq_swept = !InpRequireLiqSweep || m_smc.liq_swept_low;

    // Generate BUY signal based on entry type
    bool buy_signal = false;

    if(htf_bullish && ltf_bullish && liq_swept)
    {
        switch(InpEntryType)
        {
            case ENTRY_OB_ONLY:
                buy_signal = at_bull_ob;
                break;
            case ENTRY_FVG_ONLY:
                buy_signal = at_bull_fvg;
                break;
            case ENTRY_OB_FVG:
                buy_signal = at_bull_ob || at_bull_fvg;
                break;
            case ENTRY_LQ_SWEEP:
                buy_signal = m_smc.liq_swept_low && (at_bull_ob || at_bull_fvg);
                break;
        }
    }

    if(buy_signal)
    {
        Print("BUY Signal: HTF=", EnumToString(m_smc.htf_structure.trend),
              " LTF=", EnumToString(m_smc.ltf_structure.trend),
              " OB=", at_bull_ob, " FVG=", at_bull_fvg,
              " LiqSwept=", m_smc.liq_swept_low);
        return 1;
    }

    // ===== SELL CONDITIONS =====
    bool htf_bearish = (m_smc.htf_structure.trend == STRUCTURE_BEARISH);
    bool ltf_bearish = (m_smc.ltf_structure.trend == STRUCTURE_BEARISH ||
                        m_smc.ltf_structure.bos_bearish ||
                        m_smc.ltf_structure.choch);

    bool at_bear_ob = m_smc.bear_ob.is_valid &&
                      ask >= m_smc.bear_ob.bottom &&
                      ask <= m_smc.bear_ob.top;

    bool at_bear_fvg = m_smc.bear_fvg.is_valid &&
                       ask >= m_smc.bear_fvg.bottom &&
                       ask <= m_smc.bear_fvg.top;

    bool liq_swept_high = !InpRequireLiqSweep || m_smc.liq_swept_high;

    bool sell_signal = false;

    if(htf_bearish && ltf_bearish && liq_swept_high)
    {
        switch(InpEntryType)
        {
            case ENTRY_OB_ONLY:
                sell_signal = at_bear_ob;
                break;
            case ENTRY_FVG_ONLY:
                sell_signal = at_bear_fvg;
                break;
            case ENTRY_OB_FVG:
                sell_signal = at_bear_ob || at_bear_fvg;
                break;
            case ENTRY_LQ_SWEEP:
                sell_signal = m_smc.liq_swept_high && (at_bear_ob || at_bear_fvg);
                break;
        }
    }

    if(sell_signal)
    {
        Print("SELL Signal: HTF=", EnumToString(m_smc.htf_structure.trend),
              " LTF=", EnumToString(m_smc.ltf_structure.trend),
              " OB=", at_bear_ob, " FVG=", at_bear_fvg,
              " LiqSwept=", m_smc.liq_swept_high);
        return -1;
    }

    return 0;
}

//+------------------------------------------------------------------+
//| Open Buy                                                         |
//+------------------------------------------------------------------+
void OpenBuy()
{
    double price = m_symbol.Ask();
    double point = m_symbol.Point();

    // SL below OB or recent swing low
    double sl_price = price - InpStopLoss * point;
    if(m_smc.bull_ob.is_valid)
        sl_price = MathMin(sl_price, m_smc.bull_ob.bottom - 10 * point);

    double tp_price = price + InpTakeProfit * point;

    sl_price = NormalizeDouble(sl_price, m_symbol.Digits());
    tp_price = NormalizeDouble(tp_price, m_symbol.Digits());

    if(m_trade.Buy(InpLotSize, _Symbol, price, sl_price, tp_price, InpComment))
    {
        m_last_trade_bar = iTime(_Symbol, InpLTF, 0);
        m_daily_trades++;
        Print("BUY @ ", price, " SL: ", sl_price, " TP: ", tp_price);
    }
}

//+------------------------------------------------------------------+
//| Open Sell                                                        |
//+------------------------------------------------------------------+
void OpenSell()
{
    double price = m_symbol.Bid();
    double point = m_symbol.Point();

    // SL above OB or recent swing high
    double sl_price = price + InpStopLoss * point;
    if(m_smc.bear_ob.is_valid)
        sl_price = MathMax(sl_price, m_smc.bear_ob.top + 10 * point);

    double tp_price = price - InpTakeProfit * point;

    sl_price = NormalizeDouble(sl_price, m_symbol.Digits());
    tp_price = NormalizeDouble(tp_price, m_symbol.Digits());

    if(m_trade.Sell(InpLotSize, _Symbol, price, sl_price, tp_price, InpComment))
    {
        m_last_trade_bar = iTime(_Symbol, InpLTF, 0);
        m_daily_trades++;
        Print("SELL @ ", price, " SL: ", sl_price, " TP: ", tp_price);
    }
}

//+------------------------------------------------------------------+
//| Manage positions                                                 |
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

            if(profit_pts >= InpBreakevenTrigger)
            {
                double be_price = open_price + InpBreakevenPlus * point;
                be_price = NormalizeDouble(be_price, m_symbol.Digits());

                if(current_sl < be_price)
                {
                    m_trade.PositionModify(m_position.Ticket(), be_price, tp);
                }
                else if(InpUseTrailing)
                {
                    double trail_sl = bid - InpTrailingStep * point;
                    trail_sl = NormalizeDouble(trail_sl, m_symbol.Digits());
                    if(trail_sl > current_sl + point)
                        m_trade.PositionModify(m_position.Ticket(), trail_sl, tp);
                }
            }
        }
        else
        {
            double ask = m_symbol.Ask();
            double profit_pts = (open_price - ask) / point;

            if(profit_pts >= InpBreakevenTrigger)
            {
                double be_price = open_price - InpBreakevenPlus * point;
                be_price = NormalizeDouble(be_price, m_symbol.Digits());

                if(current_sl > be_price || current_sl == 0)
                {
                    m_trade.PositionModify(m_position.Ticket(), be_price, tp);
                }
                else if(InpUseTrailing)
                {
                    double trail_sl = ask + InpTrailingStep * point;
                    trail_sl = NormalizeDouble(trail_sl, m_symbol.Digits());
                    if(trail_sl < current_sl - point)
                        m_trade.PositionModify(m_position.Ticket(), trail_sl, tp);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Draw SMC objects on chart                                       |
//+------------------------------------------------------------------+
void DrawSMCObjects()
{
    // Draw Bullish OB
    if(m_smc.bull_ob.is_valid)
    {
        string name = "SMC_BullOB";
        ObjectDelete(0, name);
        ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                    m_smc.bull_ob.time, m_smc.bull_ob.bottom,
                    TimeCurrent() + PeriodSeconds(InpLTF) * 20, m_smc.bull_ob.top);
        ObjectSetInteger(0, name, OBJPROP_COLOR, clrGreen);
        ObjectSetInteger(0, name, OBJPROP_FILL, true);
        ObjectSetInteger(0, name, OBJPROP_BACK, true);
        ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
    }

    // Draw Bearish OB
    if(m_smc.bear_ob.is_valid)
    {
        string name = "SMC_BearOB";
        ObjectDelete(0, name);
        ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                    m_smc.bear_ob.time, m_smc.bear_ob.bottom,
                    TimeCurrent() + PeriodSeconds(InpLTF) * 20, m_smc.bear_ob.top);
        ObjectSetInteger(0, name, OBJPROP_COLOR, clrRed);
        ObjectSetInteger(0, name, OBJPROP_FILL, true);
        ObjectSetInteger(0, name, OBJPROP_BACK, true);
    }

    // Draw Bullish FVG
    if(m_smc.bull_fvg.is_valid)
    {
        string name = "SMC_BullFVG";
        ObjectDelete(0, name);
        ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                    m_smc.bull_fvg.time, m_smc.bull_fvg.bottom,
                    TimeCurrent() + PeriodSeconds(InpLTF) * 20, m_smc.bull_fvg.top);
        ObjectSetInteger(0, name, OBJPROP_COLOR, clrLime);
        ObjectSetInteger(0, name, OBJPROP_FILL, true);
        ObjectSetInteger(0, name, OBJPROP_BACK, true);
        ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DOT);
    }

    // Draw Bearish FVG
    if(m_smc.bear_fvg.is_valid)
    {
        string name = "SMC_BearFVG";
        ObjectDelete(0, name);
        ObjectCreate(0, name, OBJ_RECTANGLE, 0,
                    m_smc.bear_fvg.time, m_smc.bear_fvg.bottom,
                    TimeCurrent() + PeriodSeconds(InpLTF) * 20, m_smc.bear_fvg.top);
        ObjectSetInteger(0, name, OBJPROP_COLOR, clrOrangeRed);
        ObjectSetInteger(0, name, OBJPROP_FILL, true);
        ObjectSetInteger(0, name, OBJPROP_BACK, true);
    }

    // Draw Liquidity Levels
    if(m_smc.liq_high.price > 0)
    {
        string name = "SMC_LiqHigh";
        ObjectDelete(0, name);
        ObjectCreate(0, name, OBJ_HLINE, 0, 0, m_smc.liq_high.price);
        ObjectSetInteger(0, name, OBJPROP_COLOR, m_smc.liq_swept_high ? clrGray : clrMagenta);
        ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DASHDOT);
        ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
    }

    if(m_smc.liq_low.price > 0)
    {
        string name = "SMC_LiqLow";
        ObjectDelete(0, name);
        ObjectCreate(0, name, OBJ_HLINE, 0, 0, m_smc.liq_low.price);
        ObjectSetInteger(0, name, OBJPROP_COLOR, m_smc.liq_swept_low ? clrGray : clrCyan);
        ObjectSetInteger(0, name, OBJPROP_STYLE, STYLE_DASHDOT);
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

    static int last_deals = 0;
    if(HistorySelect(m_day_start, TimeCurrent()))
    {
        int deals = HistoryDealsTotal();
        if(deals > last_deals)
        {
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
    info += "║        💎 REBATE FARM PRO v5.0 - SMC PRO EDITION 💎          ║\n";
    info += "║         FVG + Order Block + Liquidity + Structure            ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    // Market Structure
    info += "║ 📊 MARKET STRUCTURE                                           ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    string htf_str = m_smc.htf_structure.trend == STRUCTURE_BULLISH ? "🟢 BULLISH (HH+HL)" :
                     m_smc.htf_structure.trend == STRUCTURE_BEARISH ? "🔴 BEARISH (LH+LL)" : "🟡 RANGING";
    info += "║ HTF (" + EnumToString(InpHTF) + "): " + htf_str +
            StringFormat("%*s", 27-StringLen(htf_str), "") + "║\n";

    string ltf_str = m_smc.ltf_structure.trend == STRUCTURE_BULLISH ? "🟢 BULLISH" :
                     m_smc.ltf_structure.trend == STRUCTURE_BEARISH ? "🔴 BEARISH" : "🟡 RANGING";
    info += "║ LTF (" + EnumToString(InpLTF) + "): " + ltf_str +
            StringFormat("%*s", 32-StringLen(ltf_str), "") + "║\n";

    // BOS / CHoCH
    string bos = "";
    if(m_smc.ltf_structure.bos_bullish) bos = "🟢 BOS Bullish";
    else if(m_smc.ltf_structure.bos_bearish) bos = "🔴 BOS Bearish";
    else if(m_smc.ltf_structure.choch) bos = "⚡ CHoCH";
    else bos = "⏳ No BOS";
    info += "║ Break of Structure: " + bos + StringFormat("%*s", 42-StringLen(bos), "") + "║\n";

    // SMC Zones
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 🎯 SMC ZONES                                                  ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    string bull_ob = m_smc.bull_ob.is_valid ?
        "🟢 " + DoubleToString(m_smc.bull_ob.bottom, (int)m_symbol.Digits()) + "-" +
        DoubleToString(m_smc.bull_ob.top, (int)m_symbol.Digits()) : "❌ None";
    info += "║ Bull OB: " + bull_ob + StringFormat("%*s", 52-StringLen(bull_ob), "") + "║\n";

    string bear_ob = m_smc.bear_ob.is_valid ?
        "🔴 " + DoubleToString(m_smc.bear_ob.bottom, (int)m_symbol.Digits()) + "-" +
        DoubleToString(m_smc.bear_ob.top, (int)m_symbol.Digits()) : "❌ None";
    info += "║ Bear OB: " + bear_ob + StringFormat("%*s", 52-StringLen(bear_ob), "") + "║\n";

    string bull_fvg = m_smc.bull_fvg.is_valid ?
        "🟢 " + DoubleToString(m_smc.bull_fvg.bottom, (int)m_symbol.Digits()) + "-" +
        DoubleToString(m_smc.bull_fvg.top, (int)m_symbol.Digits()) : "❌ None";
    info += "║ Bull FVG: " + bull_fvg + StringFormat("%*s", 51-StringLen(bull_fvg), "") + "║\n";

    string bear_fvg = m_smc.bear_fvg.is_valid ?
        "🔴 " + DoubleToString(m_smc.bear_fvg.bottom, (int)m_symbol.Digits()) + "-" +
        DoubleToString(m_smc.bear_fvg.top, (int)m_symbol.Digits()) : "❌ None";
    info += "║ Bear FVG: " + bear_fvg + StringFormat("%*s", 51-StringLen(bear_fvg), "") + "║\n";

    // Liquidity
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 💧 LIQUIDITY                                                   ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    string liq_h = m_smc.liq_high.price > 0 ?
        DoubleToString(m_smc.liq_high.price, (int)m_symbol.Digits()) +
        (m_smc.liq_swept_high ? " ✅ SWEPT" : " ⏳") : "N/A";
    info += "║ Liq High (Buy Stops): " + liq_h + StringFormat("%*s", 39-StringLen(liq_h), "") + "║\n";

    string liq_l = m_smc.liq_low.price > 0 ?
        DoubleToString(m_smc.liq_low.price, (int)m_symbol.Digits()) +
        (m_smc.liq_swept_low ? " ✅ SWEPT" : " ⏳") : "N/A";
    info += "║ Liq Low (Sell Stops): " + liq_l + StringFormat("%*s", 39-StringLen(liq_l), "") + "║\n";

    // Trading Status
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 📈 TRADING                                                     ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    string spread_icon = spread < 2.0 ? "🟢" : spread < 3.5 ? "🟡" : "🔴";
    info += "║ " + spread_icon + " Spread: " + DoubleToString(spread, 1) + " pips" +
            StringFormat("%*s", 47, "") + "║\n";

    info += "║ Positions: " + IntegerToString(m_positions_count) + "/" + IntegerToString(InpMaxPositions) +
            StringFormat("%*s", 50, "") + "║\n";

    string float_icon = m_total_profit >= 0 ? "📈" : "📉";
    info += "║ " + float_icon + " Float P/L: $" + DoubleToString(m_total_profit, 2) +
            StringFormat("%*s", 47-StringLen(DoubleToString(m_total_profit, 2)), "") + "║\n";

    int total_trades = m_win_count + m_loss_count + m_be_count;
    if(total_trades > 0)
    {
        double win_rate = (double)(m_win_count + m_be_count) / total_trades * 100;
        info += "║ Stats: W:" + IntegerToString(m_win_count) + " L:" + IntegerToString(m_loss_count) +
                " BE:" + IntegerToString(m_be_count) + " | WR: " + DoubleToString(win_rate, 1) + "%" +
                StringFormat("%*s", 22, "") + "║\n";
    }

    // Account
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 💰 ACCOUNT                                                     ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    info += "║ Balance: $" + DoubleToString(balance, 2) +
            StringFormat("%*s", 51-StringLen(DoubleToString(balance, 2)), "") + "║\n";

    string pnl = (profit >= 0 ? "+" : "") + DoubleToString(profit, 2);
    info += "║ Trading P/L: $" + pnl + StringFormat("%*s", 47-StringLen(pnl), "") + "║\n";

    // Rebate
    if(InpEnableRebate)
    {
        info += "╠═══════════════════════════════════════════════════════════════╣\n";
        info += "║ 💎 REBATE                                                      ║\n";
        info += "╠═══════════════════════════════════════════════════════════════╣\n";

        info += "║ Today: " + IntegerToString(m_daily_trades) + " trades | " +
                DoubleToString(m_daily_lots, 2) + " lots | $" + DoubleToString(m_daily_rebate, 2) +
                StringFormat("%*s", 25, "") + "║\n";

        double net = profit + m_daily_rebate + m_total_rebate;
        string net_icon = net >= 0 ? "✅" : "⚠️";
        info += "║ " + net_icon + " NET: $" + DoubleToString(net, 2) + " (P/L + Rebate)" +
                StringFormat("%*s", 35-StringLen(DoubleToString(net, 2)), "") + "║\n";
    }

    info += "╚═══════════════════════════════════════════════════════════════╝\n";
    info += "   📘 SMC: HTF Structure → LTF Confirmation → OB/FVG Entry\n";
    info += "   💡 Wait for Liquidity Sweep before entering!";

    Comment(info);
}
//+------------------------------------------------------------------+
