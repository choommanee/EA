//+------------------------------------------------------------------+
//|                                         RebateFarmPro_v3_SMC.mq5 |
//|                                        Copyright 2025, RebateFarm |
//|     SMC Trend Following + High Volume Trading for Maximum Rebate |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, RebateFarm"
#property link      "https://www.mql5.com"
#property version   "3.00"
#property description "SMC-Based Rebate Farming EA - High Volume Trend Following"
#property description "Features: Order Blocks, BOS, Multi-TF Trend, Grid Scaling"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>

//--- Enumerations
enum ENUM_ACCOUNT_TYPE
{
    ACCOUNT_STANDARD = 0,    // Standard Account ($10/lot)
    ACCOUNT_ULTRA = 1,       // Ultra Low Spread ($6/lot)
    ACCOUNT_MICRO = 2        // Micro Account ($10/lot)
};

enum ENUM_SMC_MODE
{
    SMC_CONSERVATIVE = 0,    // Conservative - Fewer trades, higher accuracy
    SMC_BALANCED = 1,        // Balanced - Medium frequency
    SMC_AGGRESSIVE = 2       // Aggressive - Maximum volume for rebate
};

enum ENUM_TREND_STATE
{
    TREND_BULLISH = 1,
    TREND_BEARISH = -1,
    TREND_RANGING = 0
};

//--- Input Parameters
input group "=== SMC STRATEGY SETTINGS ==="
input ENUM_SMC_MODE InpSMCMode = SMC_AGGRESSIVE;        // SMC Trading Mode
input ENUM_TIMEFRAMES InpHTF = PERIOD_H1;               // Higher Timeframe (Trend)
input ENUM_TIMEFRAMES InpLTF = PERIOD_M5;               // Lower Timeframe (Entry)
input int InpStructureLookback = 50;                    // Structure Lookback Bars
input int InpOBLookback = 20;                           // Order Block Lookback
input double InpOBMinSize = 10;                         // Min Order Block Size (points)

input group "=== VOLUME FARMING SETTINGS (LOW CAPITAL) ==="
input double InpBaseLot = 0.01;                         // Base Lot Size (minimum)
input bool InpUseAutoLot = true;                        // Auto Lot Sizing
input double InpRiskPercent = 0.3;                      // Risk % per Position (low for safety)
input int InpMaxPositions = 5;                          // Max Positions (same direction)
input int InpMaxTotalPositions = 8;                     // Max Total Positions
input int InpGridSpacing = 150;                         // Grid Spacing (points) - wider for safety
input double InpLotMultiplier = 1.0;                    // Lot Multiplier for Grid
input double InpMinBalance = 50.0;                      // Minimum Balance to Trade ($)
input double InpMaxDrawdownPercent = 15.0;              // Max Drawdown % (stop trading)

input group "=== QUICK PROFIT SETTINGS ==="
input int InpQuickTP = 50;                              // Quick TP (points) - for rebate
input int InpNormalTP = 150;                            // Normal TP (points)
input int InpMaxTP = 300;                               // Max TP (points)
input int InpStopLoss = 500;                            // Stop Loss (points)
input bool InpUseTrailing = true;                       // Use Trailing Stop
input int InpTrailingStart = 30;                        // Trailing Start (points)
input int InpTrailingStep = 20;                         // Trailing Step (points)

input group "=== HEDGE PROTECTION (LOW CAPITAL) ==="
input bool InpUseHedge = true;                          // Enable Hedge Protection
input double InpHedgeTriggerPercent = 5.0;              // Hedge Trigger (% of balance)
input double InpHedgeRatio = 0.3;                       // Hedge Ratio (0.3 = 30% - safer)
input int InpHedgeTP = 80;                              // Hedge TP (points)

input group "=== SPREAD & TIME FILTER ==="
input int InpMaxSpread = 40;                            // Maximum Spread (points)
input bool InpUseTimeFilter = true;                     // Use Time Filter
input int InpStartHour = 2;                             // Start Hour (Server)
input int InpEndHour = 22;                              // End Hour (Server)
input bool InpTradeNews = false;                        // Trade During News

input group "=== XM REBATE SYSTEM ==="
input bool InpEnableRebate = true;                      // Enable Rebate Tracking
input ENUM_ACCOUNT_TYPE InpAccountType = ACCOUNT_ULTRA; // Account Type
input double InpRebateStandard = 10.0;                  // Standard Rebate ($/lot)
input double InpRebateUltra = 6.0;                      // Ultra Rebate ($/lot)

input group "=== SYSTEM ==="
input int InpMagicNumber = 202503;                      // Magic Number
input string InpComment = "SMC_Rebate";                 // Order Comment
input bool InpShowPanel = true;                         // Show Info Panel

//--- Global Objects
CTrade         m_trade;
CPositionInfo  m_position;
CAccountInfo   m_account;
CSymbolInfo    m_symbol;

//--- SMC Structure Variables
struct SMC_Structure
{
    double swing_high;
    double swing_low;
    double last_high;
    double last_low;
    datetime swing_high_time;
    datetime swing_low_time;
    ENUM_TREND_STATE trend;
    bool bos_bullish;
    bool bos_bearish;
    double ob_bull_top;
    double ob_bull_bottom;
    double ob_bear_top;
    double ob_bear_bottom;
    bool ob_bull_valid;
    bool ob_bear_valid;
};

SMC_Structure m_htf_structure;
SMC_Structure m_ltf_structure;

//--- Trading State
struct TradingState
{
    int buy_count;
    int sell_count;
    double buy_volume;
    double sell_volume;
    double total_profit;
    double last_entry_price;
    datetime last_trade_time;
    bool hedge_active;
    int hedge_ticket;
};

TradingState m_state;

//--- Rebate Tracking
double m_daily_lots;
double m_daily_rebate;
double m_total_rebate;
double m_rebate_rate;
int m_daily_trades;
datetime m_day_start;
double m_initial_balance;
double m_max_balance;
bool m_drawdown_pause;

//--- Indicator Handles
int m_atr_handle;
double m_atr_buffer[];

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

    // Setup trade object
    m_trade.SetExpertMagicNumber(InpMagicNumber);
    m_trade.SetDeviationInPoints(30);
    m_trade.SetTypeFilling(ORDER_FILLING_IOC);

    // Initialize ATR
    m_atr_handle = iATR(_Symbol, InpLTF, 14);
    if(m_atr_handle == INVALID_HANDLE)
    {
        Print("Error creating ATR indicator");
        return INIT_FAILED;
    }
    ArraySetAsSeries(m_atr_buffer, true);

    // Initialize structures
    ZeroMemory(m_htf_structure);
    ZeroMemory(m_ltf_structure);
    ZeroMemory(m_state);

    // Initialize rebate system
    InitializeRebateSystem();

    // Store initial balance
    m_initial_balance = m_account.Balance();
    m_max_balance = m_initial_balance;
    m_drawdown_pause = false;

    Print("=== RebateFarmPro v3.0 SMC Edition (Low Capital) ===");
    Print("Mode: ", EnumToString(InpSMCMode));
    Print("HTF: ", EnumToString(InpHTF), " | LTF: ", EnumToString(InpLTF));
    Print("Max Positions: ", InpMaxPositions, " | Grid: ", InpGridSpacing, " pts");
    Print("Rebate Rate: $", DoubleToString(m_rebate_rate, 2), "/lot");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    if(m_atr_handle != INVALID_HANDLE)
        IndicatorRelease(m_atr_handle);

    Comment("");
    ObjectsDeleteAll(0, "SMC_");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Update symbol info
    m_symbol.RefreshRates();

    // Check basic conditions
    if(!CheckBasicConditions()) return;

    // Update ATR
    if(CopyBuffer(m_atr_handle, 0, 0, 3, m_atr_buffer) <= 0) return;

    // Update SMC structures
    UpdateSMCStructure(InpHTF, m_htf_structure);
    UpdateSMCStructure(InpLTF, m_ltf_structure);

    // Update trading state
    UpdateTradingState();

    // Check for hedge
    if(InpUseHedge)
        ManageHedge();

    // Main trading logic
    if(IsTimeToTrade())
        ExecuteTradingLogic();

    // Manage positions
    ManageOpenPositions();

    // Update rebate tracking
    UpdateRebateTracking();

    // Update display
    if(InpShowPanel)
        UpdateDisplay();
}

//+------------------------------------------------------------------+
//| Check basic trading conditions                                   |
//+------------------------------------------------------------------+
bool CheckBasicConditions()
{
    // Check spread
    int spread = (int)m_symbol.Spread();
    if(spread > InpMaxSpread)
        return false;

    // Check if market is open
    if(!SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE))
        return false;

    // Check minimum balance (LOW CAPITAL PROTECTION)
    double balance = m_account.Balance();
    if(balance < InpMinBalance)
    {
        static datetime last_warn = 0;
        if(TimeCurrent() - last_warn > 3600) // Warn hourly
        {
            Print("⚠️ Balance ($", balance, ") below minimum ($", InpMinBalance, ") - Trading paused");
            last_warn = TimeCurrent();
        }
        return false;
    }

    // Check drawdown protection
    if(!CheckDrawdownLimit())
        return false;

    return true;
}

//+------------------------------------------------------------------+
//| Check drawdown limit - LOW CAPITAL PROTECTION                   |
//+------------------------------------------------------------------+
bool CheckDrawdownLimit()
{
    double balance = m_account.Balance();
    double equity = m_account.Equity();

    // Update max balance
    if(balance > m_max_balance)
        m_max_balance = balance;

    // Calculate drawdown from peak
    double drawdown_percent = 0;
    if(m_max_balance > 0)
        drawdown_percent = ((m_max_balance - equity) / m_max_balance) * 100;

    // Check if drawdown exceeded
    if(drawdown_percent >= InpMaxDrawdownPercent)
    {
        if(!m_drawdown_pause)
        {
            m_drawdown_pause = true;
            Print("🛑 DRAWDOWN LIMIT REACHED: ", DoubleToString(drawdown_percent, 1), "% - New trades paused");
        }
        return false;
    }

    // Resume if equity recovers to 50% of drawdown
    if(m_drawdown_pause && drawdown_percent < InpMaxDrawdownPercent * 0.5)
    {
        m_drawdown_pause = false;
        Print("✅ Drawdown recovered - Trading resumed");
    }

    return !m_drawdown_pause;
}

//+------------------------------------------------------------------+
//| Check if time to trade                                          |
//+------------------------------------------------------------------+
bool IsTimeToTrade()
{
    if(!InpUseTimeFilter) return true;

    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);

    // Check trading hours
    if(dt.hour < InpStartHour || dt.hour >= InpEndHour)
        return false;

    // Avoid Friday close
    if(dt.day_of_week == 5 && dt.hour >= 20)
        return false;

    return true;
}

//+------------------------------------------------------------------+
//| Update SMC Structure for given timeframe                        |
//+------------------------------------------------------------------+
void UpdateSMCStructure(ENUM_TIMEFRAMES tf, SMC_Structure &structure)
{
    double high[], low[], close[], open[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);
    ArraySetAsSeries(open, true);

    int bars = InpStructureLookback + 10;
    if(CopyHigh(_Symbol, tf, 0, bars, high) <= 0) return;
    if(CopyLow(_Symbol, tf, 0, bars, low) <= 0) return;
    if(CopyClose(_Symbol, tf, 0, bars, close) <= 0) return;
    if(CopyOpen(_Symbol, tf, 0, bars, open) <= 0) return;

    // Find swing points
    FindSwingPoints(high, low, structure);

    // Detect Break of Structure
    DetectBOS(high, low, close, structure);

    // Find Order Blocks
    FindOrderBlocks(high, low, close, open, structure);

    // Determine trend
    DetermineTrend(structure);
}

//+------------------------------------------------------------------+
//| Find Swing High and Low points                                  |
//+------------------------------------------------------------------+
void FindSwingPoints(const double &high[], const double &low[], SMC_Structure &structure)
{
    double highest = 0, lowest = DBL_MAX;
    int highest_idx = 0, lowest_idx = 0;

    for(int i = 1; i < InpStructureLookback; i++)
    {
        // Swing High: Higher than 2 bars on each side
        if(i >= 2 && i < InpStructureLookback - 2)
        {
            if(high[i] > high[i-1] && high[i] > high[i-2] &&
               high[i] > high[i+1] && high[i] > high[i+2])
            {
                if(high[i] > highest)
                {
                    highest = high[i];
                    highest_idx = i;
                }
            }

            // Swing Low
            if(low[i] < low[i-1] && low[i] < low[i-2] &&
               low[i] < low[i+1] && low[i] < low[i+2])
            {
                if(low[i] < lowest)
                {
                    lowest = low[i];
                    lowest_idx = i;
                }
            }
        }
    }

    if(highest > 0)
    {
        structure.swing_high = highest;
        structure.swing_high_time = iTime(_Symbol, InpHTF, highest_idx);
    }

    if(lowest < DBL_MAX)
    {
        structure.swing_low = lowest;
        structure.swing_low_time = iTime(_Symbol, InpHTF, lowest_idx);
    }

    // Recent highs and lows
    structure.last_high = high[ArrayMaximum(high, 0, 10)];
    structure.last_low = low[ArrayMinimum(low, 0, 10)];
}

//+------------------------------------------------------------------+
//| Detect Break of Structure                                       |
//+------------------------------------------------------------------+
void DetectBOS(const double &high[], const double &low[], const double &close[], SMC_Structure &structure)
{
    structure.bos_bullish = false;
    structure.bos_bearish = false;

    double prev_high = high[ArrayMaximum(high, 3, 15)];
    double prev_low = low[ArrayMinimum(low, 3, 15)];

    // Bullish BOS: Price breaks above previous high
    if(close[0] > prev_high && close[1] <= prev_high)
    {
        structure.bos_bullish = true;
    }

    // Bearish BOS: Price breaks below previous low
    if(close[0] < prev_low && close[1] >= prev_low)
    {
        structure.bos_bearish = true;
    }
}

//+------------------------------------------------------------------+
//| Find Order Blocks                                               |
//+------------------------------------------------------------------+
void FindOrderBlocks(const double &high[], const double &low[],
                     const double &close[], const double &open[], SMC_Structure &structure)
{
    structure.ob_bull_valid = false;
    structure.ob_bear_valid = false;

    double point = m_symbol.Point();
    double min_size = InpOBMinSize * point;

    for(int i = 2; i < InpOBLookback; i++)
    {
        // Bullish Order Block: Last down candle before up move
        if(!structure.ob_bull_valid)
        {
            if(close[i] < open[i]) // Down candle
            {
                // Check if followed by strong up move
                if(close[i-1] > open[i-1] && close[i-1] > high[i])
                {
                    double ob_size = high[i] - low[i];
                    if(ob_size >= min_size)
                    {
                        structure.ob_bull_top = high[i];
                        structure.ob_bull_bottom = low[i];
                        structure.ob_bull_valid = true;
                    }
                }
            }
        }

        // Bearish Order Block: Last up candle before down move
        if(!structure.ob_bear_valid)
        {
            if(close[i] > open[i]) // Up candle
            {
                // Check if followed by strong down move
                if(close[i-1] < open[i-1] && close[i-1] < low[i])
                {
                    double ob_size = high[i] - low[i];
                    if(ob_size >= min_size)
                    {
                        structure.ob_bear_top = high[i];
                        structure.ob_bear_bottom = low[i];
                        structure.ob_bear_valid = true;
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Determine overall trend                                         |
//+------------------------------------------------------------------+
void DetermineTrend(SMC_Structure &structure)
{
    double bid = m_symbol.Bid();

    // Higher highs and higher lows = Bullish
    if(structure.swing_high > 0 && structure.swing_low > 0)
    {
        if(bid > structure.swing_low && structure.bos_bullish)
        {
            structure.trend = TREND_BULLISH;
        }
        else if(bid < structure.swing_high && structure.bos_bearish)
        {
            structure.trend = TREND_BEARISH;
        }
        else
        {
            // Use price position relative to swings
            double mid = (structure.swing_high + structure.swing_low) / 2;
            if(bid > mid)
                structure.trend = TREND_BULLISH;
            else if(bid < mid)
                structure.trend = TREND_BEARISH;
            else
                structure.trend = TREND_RANGING;
        }
    }
}

//+------------------------------------------------------------------+
//| Update trading state                                            |
//+------------------------------------------------------------------+
void UpdateTradingState()
{
    m_state.buy_count = 0;
    m_state.sell_count = 0;
    m_state.buy_volume = 0;
    m_state.sell_volume = 0;
    m_state.total_profit = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                m_state.total_profit += m_position.Profit() + m_position.Swap();

                if(m_position.PositionType() == POSITION_TYPE_BUY)
                {
                    m_state.buy_count++;
                    m_state.buy_volume += m_position.Volume();
                }
                else
                {
                    m_state.sell_count++;
                    m_state.sell_volume += m_position.Volume();
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Execute main trading logic                                      |
//+------------------------------------------------------------------+
void ExecuteTradingLogic()
{
    int total_positions = m_state.buy_count + m_state.sell_count;
    if(total_positions >= InpMaxTotalPositions) return;

    double bid = m_symbol.Bid();
    double ask = m_symbol.Ask();
    double point = m_symbol.Point();

    // Get combined trend signal
    ENUM_TREND_STATE combined_trend = GetCombinedTrend();

    // Check entry conditions based on mode
    bool can_buy = false, can_sell = false;
    double entry_score = 0;

    switch(InpSMCMode)
    {
        case SMC_CONSERVATIVE:
            // Need strong confluence
            can_buy = (combined_trend == TREND_BULLISH &&
                      m_ltf_structure.ob_bull_valid &&
                      bid >= m_ltf_structure.ob_bull_bottom &&
                      bid <= m_ltf_structure.ob_bull_top);

            can_sell = (combined_trend == TREND_BEARISH &&
                       m_ltf_structure.ob_bear_valid &&
                       ask >= m_ltf_structure.ob_bear_bottom &&
                       ask <= m_ltf_structure.ob_bear_top);
            break;

        case SMC_BALANCED:
            // Need trend alignment + OB or BOS
            can_buy = (combined_trend == TREND_BULLISH &&
                      (m_ltf_structure.ob_bull_valid || m_ltf_structure.bos_bullish));

            can_sell = (combined_trend == TREND_BEARISH &&
                       (m_ltf_structure.ob_bear_valid || m_ltf_structure.bos_bearish));
            break;

        case SMC_AGGRESSIVE:
            // Follow trend, enter on any pullback or continuation
            can_buy = (combined_trend == TREND_BULLISH || m_htf_structure.trend == TREND_BULLISH);
            can_sell = (combined_trend == TREND_BEARISH || m_htf_structure.trend == TREND_BEARISH);

            // Add extra entries on structure signals
            if(m_ltf_structure.bos_bullish) can_buy = true;
            if(m_ltf_structure.bos_bearish) can_sell = true;
            break;
    }

    // Check grid spacing for additional entries
    bool spacing_ok = true;
    if(total_positions > 0)
    {
        spacing_ok = CheckGridSpacing(bid);
    }

    // Execute trades
    if(can_buy && m_state.buy_count < InpMaxPositions && spacing_ok)
    {
        if(!m_state.hedge_active || m_state.sell_count == 0)
            OpenPosition(ORDER_TYPE_BUY);
    }

    if(can_sell && m_state.sell_count < InpMaxPositions && spacing_ok)
    {
        if(!m_state.hedge_active || m_state.buy_count == 0)
            OpenPosition(ORDER_TYPE_SELL);
    }
}

//+------------------------------------------------------------------+
//| Get combined trend from HTF and LTF                             |
//+------------------------------------------------------------------+
ENUM_TREND_STATE GetCombinedTrend()
{
    // HTF trend has priority
    if(m_htf_structure.trend == TREND_BULLISH && m_ltf_structure.trend != TREND_BEARISH)
        return TREND_BULLISH;

    if(m_htf_structure.trend == TREND_BEARISH && m_ltf_structure.trend != TREND_BULLISH)
        return TREND_BEARISH;

    // If HTF is ranging, use LTF
    return m_ltf_structure.trend;
}

//+------------------------------------------------------------------+
//| Check grid spacing for new entries                              |
//+------------------------------------------------------------------+
bool CheckGridSpacing(double current_price)
{
    double min_distance = InpGridSpacing * m_symbol.Point();

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() == _Symbol && m_position.Magic() == InpMagicNumber)
            {
                double distance = MathAbs(current_price - m_position.PriceOpen());
                if(distance < min_distance)
                    return false;
            }
        }
    }
    return true;
}

//+------------------------------------------------------------------+
//| Open position                                                    |
//+------------------------------------------------------------------+
void OpenPosition(ENUM_ORDER_TYPE type)
{
    double lot = CalculateLotSize();
    double point = m_symbol.Point();
    double price, sl, tp;

    // Select TP based on mode
    int tp_points = InpQuickTP;
    switch(InpSMCMode)
    {
        case SMC_CONSERVATIVE: tp_points = InpMaxTP; break;
        case SMC_BALANCED: tp_points = InpNormalTP; break;
        case SMC_AGGRESSIVE: tp_points = InpQuickTP; break;
    }

    if(type == ORDER_TYPE_BUY)
    {
        price = m_symbol.Ask();
        sl = InpStopLoss > 0 ? price - InpStopLoss * point : 0;
        tp = tp_points > 0 ? price + tp_points * point : 0;

        if(m_trade.Buy(lot, _Symbol, price, sl, tp, InpComment))
        {
            m_state.last_entry_price = price;
            m_state.last_trade_time = TimeCurrent();
            m_daily_trades++;
            Print("BUY opened: ", lot, " lots @ ", price, " TP: ", tp_points, " pts");
        }
    }
    else
    {
        price = m_symbol.Bid();
        sl = InpStopLoss > 0 ? price + InpStopLoss * point : 0;
        tp = tp_points > 0 ? price - tp_points * point : 0;

        if(m_trade.Sell(lot, _Symbol, price, sl, tp, InpComment))
        {
            m_state.last_entry_price = price;
            m_state.last_trade_time = TimeCurrent();
            m_daily_trades++;
            Print("SELL opened: ", lot, " lots @ ", price, " TP: ", tp_points, " pts");
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate lot size - OPTIMIZED FOR LOW CAPITAL                  |
//+------------------------------------------------------------------+
double CalculateLotSize()
{
    double lot = InpBaseLot;
    double balance = m_account.Balance();
    double equity = m_account.Equity();

    if(InpUseAutoLot)
    {
        double risk_money = balance * InpRiskPercent / 100.0;
        double tick_value = m_symbol.TickValue();

        if(tick_value > 0 && InpStopLoss > 0)
        {
            lot = risk_money / (InpStopLoss * tick_value);
        }

        // LOW CAPITAL: Scale down if equity is dropping
        double equity_ratio = equity / balance;
        if(equity_ratio < 0.95) // If equity < 95% of balance
        {
            lot = lot * equity_ratio; // Reduce lot size proportionally
        }

        // LOW CAPITAL: Scale down based on open positions
        int total_pos = m_state.buy_count + m_state.sell_count;
        if(total_pos > 0)
        {
            // Reduce lot size for each open position
            lot = lot * MathPow(0.9, total_pos); // 10% reduction per position
        }
    }

    // Normalize
    double min_lot = m_symbol.LotsMin();
    double max_lot = m_symbol.LotsMax();
    double lot_step = m_symbol.LotsStep();

    // LOW CAPITAL: Cap at base lot if balance is low
    if(balance < 200)
        max_lot = MathMin(max_lot, InpBaseLot * 2);
    else if(balance < 500)
        max_lot = MathMin(max_lot, InpBaseLot * 5);

    lot = MathMax(min_lot, MathMin(max_lot, lot));
    lot = MathRound(lot / lot_step) * lot_step;

    return lot;
}

//+------------------------------------------------------------------+
//| Manage hedge positions - LOW CAPITAL OPTIMIZED                  |
//+------------------------------------------------------------------+
void ManageHedge()
{
    double balance = m_account.Balance();
    double hedge_trigger = -(balance * InpHedgeTriggerPercent / 100.0);

    // Check if we need to hedge (based on % of balance, not fixed $)
    if(!m_state.hedge_active && m_state.total_profit < hedge_trigger)
    {
        double hedge_volume = 0;
        ENUM_ORDER_TYPE hedge_type = ORDER_TYPE_BUY;

        // Hedge against the larger exposure
        if(m_state.buy_volume > m_state.sell_volume)
        {
            hedge_volume = m_state.buy_volume * InpHedgeRatio;
            hedge_type = ORDER_TYPE_SELL;
        }
        else if(m_state.sell_volume > m_state.buy_volume)
        {
            hedge_volume = m_state.sell_volume * InpHedgeRatio;
            hedge_type = ORDER_TYPE_BUY;
        }
        else
        {
            return; // No net exposure to hedge
        }

        // LOW CAPITAL: Ensure minimum lot
        double min_lot = m_symbol.LotsMin();
        if(hedge_volume < min_lot)
            hedge_volume = min_lot;

        // Normalize hedge volume
        double lot_step = m_symbol.LotsStep();
        hedge_volume = MathRound(hedge_volume / lot_step) * lot_step;
        hedge_volume = MathMin(hedge_volume, m_symbol.LotsMax());

        double price, tp;
        double point = m_symbol.Point();

        if(hedge_type == ORDER_TYPE_BUY)
        {
            price = m_symbol.Ask();
            tp = price + InpHedgeTP * point;
            if(m_trade.Buy(hedge_volume, _Symbol, price, 0, tp, "HEDGE"))
            {
                m_state.hedge_active = true;
                Print("🛡️ HEDGE BUY opened: ", hedge_volume, " lots (Trigger: ",
                      DoubleToString(InpHedgeTriggerPercent, 1), "% = $", DoubleToString(-hedge_trigger, 2), ")");
            }
        }
        else
        {
            price = m_symbol.Bid();
            tp = price - InpHedgeTP * point;
            if(m_trade.Sell(hedge_volume, _Symbol, price, 0, tp, "HEDGE"))
            {
                m_state.hedge_active = true;
                Print("🛡️ HEDGE SELL opened: ", hedge_volume, " lots (Trigger: ",
                      DoubleToString(InpHedgeTriggerPercent, 1), "% = $", DoubleToString(-hedge_trigger, 2), ")");
            }
        }
    }

    // Check if hedge can be removed (profit recovered)
    if(m_state.hedge_active && m_state.total_profit > 0)
    {
        m_state.hedge_active = false;
        Print("✅ Hedge condition cleared - profit recovered");
    }
}

//+------------------------------------------------------------------+
//| Manage open positions - trailing stop                           |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
    if(!InpUseTrailing) return;

    double point = m_symbol.Point();

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(m_position.SelectByIndex(i))
        {
            if(m_position.Symbol() != _Symbol || m_position.Magic() != InpMagicNumber)
                continue;

            double new_sl = 0;

            if(m_position.PositionType() == POSITION_TYPE_BUY)
            {
                double bid = m_symbol.Bid();
                double profit_pts = (bid - m_position.PriceOpen()) / point;

                if(profit_pts >= InpTrailingStart)
                {
                    new_sl = bid - InpTrailingStep * point;

                    if(new_sl > m_position.StopLoss() + point || m_position.StopLoss() == 0)
                    {
                        m_trade.PositionModify(m_position.Ticket(), new_sl, m_position.TakeProfit());
                    }
                }
            }
            else // SELL
            {
                double ask = m_symbol.Ask();
                double profit_pts = (m_position.PriceOpen() - ask) / point;

                if(profit_pts >= InpTrailingStart)
                {
                    new_sl = ask + InpTrailingStep * point;

                    if(new_sl < m_position.StopLoss() - point || m_position.StopLoss() == 0)
                    {
                        m_trade.PositionModify(m_position.Ticket(), new_sl, m_position.TakeProfit());
                    }
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Initialize rebate system                                        |
//+------------------------------------------------------------------+
void InitializeRebateSystem()
{
    switch(InpAccountType)
    {
        case ACCOUNT_STANDARD:
        case ACCOUNT_MICRO:
            m_rebate_rate = InpRebateStandard;
            break;
        case ACCOUNT_ULTRA:
            m_rebate_rate = InpRebateUltra;
            break;
    }

    m_daily_lots = 0;
    m_daily_rebate = 0;
    m_total_rebate = 0;
    m_daily_trades = 0;
    m_day_start = GetDayStart(TimeCurrent());
}

//+------------------------------------------------------------------+
//| Update rebate tracking                                          |
//+------------------------------------------------------------------+
void UpdateRebateTracking()
{
    // Check for new day
    datetime today = GetDayStart(TimeCurrent());
    if(today > m_day_start)
    {
        m_total_rebate += m_daily_rebate;
        m_daily_lots = 0;
        m_daily_rebate = 0;
        m_daily_trades = 0;
        m_day_start = today;
    }

    // Calculate today's volume
    m_daily_lots = CalculateDailyVolume();
    m_daily_rebate = m_daily_lots * m_rebate_rate;
}

//+------------------------------------------------------------------+
//| Calculate daily trading volume                                  |
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
//| Get day start time                                              |
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
//| Update display panel                                            |
//+------------------------------------------------------------------+
void UpdateDisplay()
{
    double balance = m_account.Balance();
    double equity = m_account.Equity();
    double profit = balance - m_initial_balance;
    double spread_pts = m_symbol.Spread() / 10.0;

    // Calculate drawdown
    double drawdown_amount = m_max_balance - equity;
    double drawdown_percent = m_max_balance > 0 ? (drawdown_amount / m_max_balance) * 100 : 0;

    string info = "\n";
    info += "╔═══════════════════════════════════════════════════════════════╗\n";
    info += "║      🚀 REBATE FARM PRO v3.0 - SMC LOW CAPITAL EDITION 🚀    ║\n";
    info += "║         Smart Money Concepts + Safe High Volume Trading       ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    // SMC Status
    info += "║ 📊 SMC ANALYSIS                                               ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    string htf_trend = m_htf_structure.trend == TREND_BULLISH ? "🟢 BULLISH" :
                       m_htf_structure.trend == TREND_BEARISH ? "🔴 BEARISH" : "🟡 RANGING";
    info += "║ HTF Trend (" + EnumToString(InpHTF) + "): " + htf_trend +
            StringFormat("%*s", 30-StringLen(htf_trend)-StringLen(EnumToString(InpHTF)), "") + "║\n";

    string ltf_trend = m_ltf_structure.trend == TREND_BULLISH ? "🟢 BULLISH" :
                       m_ltf_structure.trend == TREND_BEARISH ? "🔴 BEARISH" : "🟡 RANGING";
    info += "║ LTF Trend (" + EnumToString(InpLTF) + "): " + ltf_trend +
            StringFormat("%*s", 30-StringLen(ltf_trend)-StringLen(EnumToString(InpLTF)), "") + "║\n";

    string bos_status = "";
    if(m_ltf_structure.bos_bullish) bos_status = "🟢 BULLISH BOS";
    else if(m_ltf_structure.bos_bearish) bos_status = "🔴 BEARISH BOS";
    else bos_status = "⏳ Waiting...";
    info += "║ Break of Structure: " + bos_status +
            StringFormat("%*s", 42-StringLen(bos_status), "") + "║\n";

    string ob_status = "";
    if(m_ltf_structure.ob_bull_valid) ob_status += "🟢 Bull OB ";
    if(m_ltf_structure.ob_bear_valid) ob_status += "🔴 Bear OB";
    if(ob_status == "") ob_status = "No active OB";
    info += "║ Order Blocks: " + ob_status +
            StringFormat("%*s", 48-StringLen(ob_status), "") + "║\n";

    // Trading Status
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 📈 TRADING STATUS                                             ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    string mode_str = EnumToString(InpSMCMode);
    info += "║ Mode: " + mode_str + StringFormat("%*s", 56-StringLen(mode_str), "") + "║\n";

    string spread_icon = spread_pts < 2.0 ? "🟢" : spread_pts < 4.0 ? "🟡" : "🔴";
    info += "║ " + spread_icon + " Spread: " + DoubleToString(spread_pts, 1) + " pips" +
            StringFormat("%*s", 48-StringLen(DoubleToString(spread_pts, 1)), "") + "║\n";

    info += "║ 📊 Positions: BUY " + IntegerToString(m_state.buy_count) +
            " | SELL " + IntegerToString(m_state.sell_count) +
            " | Total " + IntegerToString(m_state.buy_count + m_state.sell_count) + "/" + IntegerToString(InpMaxTotalPositions) +
            StringFormat("%*s", 20, "") + "║\n";

    string profit_icon = m_state.total_profit >= 0 ? "📈" : "📉";
    info += "║ " + profit_icon + " Float P/L: $" + DoubleToString(m_state.total_profit, 2) +
            StringFormat("%*s", 46-StringLen(DoubleToString(m_state.total_profit, 2)), "") + "║\n";

    if(m_state.hedge_active)
        info += "║ ⚠️  HEDGE ACTIVE                                              ║\n";

    // Account Info
    info += "╠═══════════════════════════════════════════════════════════════╣\n";
    info += "║ 💰 ACCOUNT (LOW CAPITAL MODE)                                  ║\n";
    info += "╠═══════════════════════════════════════════════════════════════╣\n";

    info += "║ Balance: $" + DoubleToString(balance, 2) +
            StringFormat("%*s", 51-StringLen(DoubleToString(balance, 2)), "") + "║\n";
    info += "║ Equity: $" + DoubleToString(equity, 2) +
            StringFormat("%*s", 52-StringLen(DoubleToString(equity, 2)), "") + "║\n";

    string pnl_str = (profit >= 0 ? "+" : "") + DoubleToString(profit, 2);
    info += "║ Session P/L: $" + pnl_str +
            StringFormat("%*s", 47-StringLen(pnl_str), "") + "║\n";

    // Drawdown display
    string dd_icon = drawdown_percent < 5 ? "🟢" : drawdown_percent < 10 ? "🟡" : "🔴";
    string dd_str = DoubleToString(drawdown_percent, 1) + "% ($" + DoubleToString(drawdown_amount, 2) + ")";
    info += "║ " + dd_icon + " Drawdown: " + dd_str +
            StringFormat("%*s", 49-StringLen(dd_str), "") + "║\n";

    // Risk status
    string risk_status;
    if(m_drawdown_pause)
        risk_status = "🛑 PAUSED (DD Limit)";
    else if(balance < InpMinBalance * 1.5)
        risk_status = "⚠️  LOW BALANCE";
    else if(drawdown_percent > InpMaxDrawdownPercent * 0.7)
        risk_status = "⚠️  HIGH RISK";
    else
        risk_status = "✅ SAFE";
    info += "║ Risk Status: " + risk_status +
            StringFormat("%*s", 49-StringLen(risk_status), "") + "║\n";

    // Rebate Section
    if(InpEnableRebate)
    {
        info += "╠═══════════════════════════════════════════════════════════════╣\n";
        info += "║ 💎 REBATE FARMING                                              ║\n";
        info += "╠═══════════════════════════════════════════════════════════════╣\n";

        info += "║ Rate: $" + DoubleToString(m_rebate_rate, 2) + "/lot (" + GetAccountTypeName() + ")" +
                StringFormat("%*s", 38-StringLen(DoubleToString(m_rebate_rate, 2) + GetAccountTypeName()), "") + "║\n";

        info += "║ Today's Trades: " + IntegerToString(m_daily_trades) +
                StringFormat("%*s", 46-StringLen(IntegerToString(m_daily_trades)), "") + "║\n";

        info += "║ Today's Volume: " + DoubleToString(m_daily_lots, 2) + " lots" +
                StringFormat("%*s", 40-StringLen(DoubleToString(m_daily_lots, 2)), "") + "║\n";

        info += "║ 💵 Today's Rebate: $" + DoubleToString(m_daily_rebate, 2) +
                StringFormat("%*s", 42-StringLen(DoubleToString(m_daily_rebate, 2)), "") + "║\n";

        info += "║ 🏆 Total Rebate: $" + DoubleToString(m_total_rebate + m_daily_rebate, 2) +
                StringFormat("%*s", 44-StringLen(DoubleToString(m_total_rebate + m_daily_rebate, 2)), "") + "║\n";

        // Projections
        if(m_daily_rebate > 0)
        {
            double monthly = m_daily_rebate * 22;
            info += "║ 📅 Monthly Est: $" + DoubleToString(monthly, 2) +
                    StringFormat("%*s", 44-StringLen(DoubleToString(monthly, 2)), "") + "║\n";
        }

        // Net result
        double net = profit + m_daily_rebate + m_total_rebate;
        string net_icon = net >= 0 ? "✅" : "⚠️";
        info += "║ " + net_icon + " NET RESULT: $" + DoubleToString(net, 2) +
                StringFormat("%*s", 46-StringLen(DoubleToString(net, 2)), "") + "║\n";
    }

    info += "╚═══════════════════════════════════════════════════════════════╝\n";
    info += "   💡 SMC Mode: Follow Smart Money + Farm Rebates\n";

    Comment(info);
}

//+------------------------------------------------------------------+
//| Get account type name                                           |
//+------------------------------------------------------------------+
string GetAccountTypeName()
{
    switch(InpAccountType)
    {
        case ACCOUNT_STANDARD: return "Standard";
        case ACCOUNT_ULTRA: return "Ultra";
        case ACCOUNT_MICRO: return "Micro";
    }
    return "Unknown";
}

//+------------------------------------------------------------------+
//| OnTrade event handler                                           |
//+------------------------------------------------------------------+
void OnTrade()
{
    UpdateTradingState();
    UpdateRebateTracking();
}
//+------------------------------------------------------------------+
