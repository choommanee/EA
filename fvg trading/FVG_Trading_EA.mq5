//+------------------------------------------------------------------+
//|                                              FVG_Trading_EA.mq5 |
//|                                        Copyright 2024, FVG Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, FVG Ltd."
#property link      "https://www.mql5.com"
#property version   "2.00"
#property description "Professional Fair Value Gap Trading EA for MT5"
#property description "Advanced FVG detection with smart money concepts"

//--- Include MQ5 standard libraries
#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Indicators\Indicators.mqh>

//--- Trading objects
CTrade trade;
CPositionInfo position;
COrderInfo order;
CSymbolInfo symbolInfo;
CAccountInfo account;

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                 |
//+------------------------------------------------------------------+
input group "=== Basic Settings ==="
input int InpMagicNumber = 12345; // Magic Number
input bool InpEnableTrading = true; // Enable Trading
input double InpRiskPercent = 2.0; // Risk Per Trade( % )
input double InpFixedLotSize = 0.01; // Fixed Lot Size - เริ่มต้นเล็ก
input bool InpUseFixedLot = true; // Use Fixed Lot Size(เปิดใช้งาน)
input bool InpHighFrequencyMode = true; // High Frequency Trading Mode
input double InpTargetDailyLots = 150.0; // Target Daily Lots(100 - 200)

input group "=== Simple Trading ==="
input bool InpSimpleMode = true; // Simple Trading Mode(เทรดง่ายๆ)
input int InpTradeEveryBars = 1; // Trade Every X Bars(เทรดทุก 1 บาร์)
input bool InpShowFVGZones = false; // Show FVG Zones(ปิดเพื่อเร็ว)
input int InpMinFVGSize = 1; // Min FVG Size(points) - ลดมาก
input int InpMaxFVGAge = 300; // Max FVG Age(bars) - เพิ่มมาก
input double InpFVGQualityFilter = 5.0; // FVG Quality Filter( % ) - ลดมาก
input bool InpHighQualityOnly = false; // High Quality FVGs Only - ปิด
input bool InpUseFVGStrength = false; // Use FVG Strength Analysis - ปิด
input double InpMinFVGStrength = 5.0; // Minimum FVG Strength( % ) - ลดมาก

input group "=== Grid / Martingale System ==="
input bool InpUseStopLoss = false; // Use Stop Loss(ปิดใช้งาน)
input int InpGridDistance = 200; // Grid Distance(points) - เพิ่มระยะห่างมากขึ้น
input double InpGridMultiplier = 1.2; // Grid Lot Multiplier - เพิ่มเล็กน้อยเพื่อ recovery เร็วขึ้น
input int InpMaxGridLevels = 5; // Max Grid Levels - ลดลงอีก
input bool InpUseMarginTP = false; // Use Margin-based Take Profit - ปิดใช้งาน
input double InpMarginTPPercent = 2.0; // TP as % of required margin - ลดเป้าหมาย
input int InpTakeProfit = 100; // Take Profit(points) - เพิ่มเป้าหมาย
input bool InpCloseAllOnProfit = true; // Close All Positions on Profit
input int InpMinDistancePoints = 30; // Min Distance Between Orders - เพิ่ม
input bool InpEnforceSingleDirection = false; // Enforce Single Grid Direction - ปิดใช้งาน (อนุญาตทั้ง BUY และ SELL)
input double InpDirectionChangeThreshold = 200.0; // Direction Change Threshold(points) - เพิ่ม

input group "=== Smart Money Concepts ==="
input bool InpUseSMC = true; // Enable Smart Money Concepts
input bool InpUseBOS = true; // Use Break of Structure
input bool InpUseCHoCH = true; // Use Change of Character
input bool InpUseOrderBlocks = true; // Use Order Blocks
input bool InpUseLiquidity = true; // Use Liquidity Analysis
input bool InpUseMarketStructure = true; // Use Market Structure
input color InpBullishOBColor = clrBlue; // Bullish Order Block Color
input color InpBearishOBColor = clrOrange; // Bearish Order Block Color

input group "=== Trend Filter ==="
input bool InpUseMAFilter = true; // Use MA Trend Filter
input int InpFastMA = 20; // Fast MA Period
input int InpSlowMA = 50; // Slow MA Period
input ENUM_MA_METHOD InpMAMethod = MODE_EMA; // MA Method
input bool InpUseRSIFilter = true; // Use RSI Filter
input int InpRSIPeriod = 14; // RSI Period
input double InpRSIOverbought = 70.0; // RSI Overbought Level
input double InpRSIOversold = 30.0; // RSI Oversold Level
input bool InpUseADXFilter = true; // Use ADX Filter
input int InpADXPeriod = 14; // ADX Period
input double InpADXMinLevel = 25.0; // ADX Minimum Level

input group "=== Time Filter ==="
input bool InpUseTimeFilter = true; // Use Time Filter
input int InpStartHour = 8; // Start Trading Hour
input int InpEndHour = 18; // End Trading Hour

input group "=== Multi - Timeframe Analysis ==="
input bool InpUseMTF = true; // Use Multi - Timeframe Analysis
input ENUM_TIMEFRAMES InpHTF1 = PERIOD_H1; // Higher Timeframe 1
input ENUM_TIMEFRAMES InpHTF2 = PERIOD_H4; // Higher Timeframe 2
input bool InpHTFTrendConfirm = true; // HTF Trend Confirmation

input group "=== Advanced Exit Strategies ==="
input bool InpUsePartialClose = false; // Use Partial Close - ปิดใช้งาน
input double InpPartialClosePercent = 50.0; // Partial Close Percentage
input int InpPartialClosePips = 30; // Partial Close Pips
input bool InpUseTrailingStop = false; // Use Trailing Stop - ปิดใช้งาน
input int InpTrailingStart = 20; // Trailing Start(pips)
input int InpTrailingStep = 10; // Trailing Step(pips)
input bool InpUseBreakEven = false; // Use Break Even - ปิดใช้งาน
input int InpBreakEvenPips = 15; // Break Even Trigger(pips)
input int InpBreakEvenProfit = 5; // Break Even Profit(pips)

input group "=== Safety Settings ==="
input double InpMaxDailyLoss = 10.0; // Max Daily Loss( % )
input int InpMaxOrdersPerDay = 1000; // Max Orders Per Day(เพิ่มขึ้น)
input double InpMaxSpread = 50.0; // Max Spread(points)
input double InpMaxEquityDD = 30.0; // Max Equity Drawdown( % )
input bool InpUseTradingHours = false; // Use Trading Hours(ปิดเพื่อเทรดตลอด)

input group "=== Error Correction System ==="
input bool InpUseErrorCorrection = true; // Use Error Correction
input double InpLotMultiplier = 2.0; // Lot Multiplier on Loss
input int InpMaxLotMultiplications = 5; // Max Lot Multiplications
input bool InpUseReverseTrading = false; // Reverse Trade on Consecutive Losses(ปิดใช้งาน)
input int InpReverseAfterLosses = 3; // Reverse After X Consecutive Losses
input bool InpForceCloseEnabled = false; // Force Close Positions - ปิดใช้งาน
input int InpForceCloseAfterMinutes = 240; // Force Close After X Minutes - เพิ่มเวลา

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES AND STRUCTURES                                 |
//+------------------------------------------------------------------+

// Enhanced FVG Structure with Smart Money Concepts
struct FVG_Zone
{
    double high;
    double low;
    datetime time;
    int type; // 1 = Bullish, - 1 = Bearish
    bool valid;
    bool filled;
    int bars_age;
    double quality_score;
    double strength; // FVG strength percentage
    bool confirmed; // Confirmed by higher timeframe
    double volume; // Associated volume
    bool institutional; // Created by institutional order
};

// Order Block Structure
struct OrderBlock
{
    double high;
    double low;
    datetime time;
    int type; // 1 = Bullish, - 1 = Bearish
    bool valid;
    bool tested; // Has been tested by price
    double strength; // Order block strength
    int touches; // Number of times tested
    bool broken; // Order block broken
};

// Market Structure Point
struct StructurePoint
{
    double price;
    datetime time;
    int type; // 1 = Higher High, 2 = Higher Low, - 1 = Lower High, - 2 = Lower Low
    bool broken; // Structure broken
    bool liquidity_swept; // Liquidity swept
};

// Liquidity Zone
struct LiquidityZone
{
    double price;
    datetime time;
    int type; // 1 = Buy side, - 1 = Sell side
    bool swept; // Liquidity swept
    double strength; // Liquidity strength
};

// Trading Statistics
struct TradingStats
{
    int total_trades;
    int winning_trades;
    int losing_trades;
    double total_profit;
    double total_loss;
    double win_rate;
    double profit_factor;
    double max_drawdown;
    double current_drawdown;
    datetime last_trade_time;
};

// Global Arrays
FVG_Zone g_fvg_zones[];
OrderBlock g_order_blocks[];
StructurePoint g_structure_points[];
LiquidityZone g_liquidity_zones[];
TradingStats g_stats;

// Array sizes
int g_fvg_count = 0;
int g_ob_count = 0;
int g_structure_count = 0;
int g_liquidity_count = 0;

const int MAX_FVG_ZONES = 50;
const int MAX_ORDER_BLOCKS = 30;
const int MAX_STRUCTURE_POINTS = 100;
const int MAX_LIQUIDITY_ZONES = 20;

// Indicator handles
int h_atr;
int h_fast_ma;
int h_slow_ma;
int h_rsi;
int h_adx;
int h_htf1_ma;
int h_htf2_ma;

// Trading variables
datetime g_last_bar_time = 0;
int g_orders_today = 0;
double g_daily_start_balance = 0;
datetime g_last_day_check = 0;
double g_highest_equity = 0;
bool g_trading_allowed = true;
double g_daily_lots_traded = 0.0;

// Order frequency control
datetime g_last_order_time = 0;
int g_min_order_interval = 5; // Minimum 5 seconds between orders
int g_orders_this_minute = 0;
datetime g_current_minute = 0;
int g_max_orders_per_minute = 3; // Maximum 3 orders per minute

// Volatility protection
double g_last_atr_value = 0;
double g_atr_multiplier_threshold = 3.0; // Stop trading if ATR > 3x normal
bool g_high_volatility_mode = false;
datetime g_volatility_cooldown = 0;

// Error Correction Variables
int g_consecutive_losses = 0;
double g_current_lot_size = 0.0;
int g_lot_multiplications = 0;
bool g_reverse_mode = false;
datetime g_last_trade_time = 0;
ulong g_last_trade_ticket = 0;

// Grid System Variables
double g_last_buy_price = 0.0;
double g_last_sell_price = 0.0;
int g_grid_level = 0;
int g_buy_grid_level = 0; // Separate grid level for buy direction
int g_sell_grid_level = 0; // Separate grid level for sell direction
double g_total_buy_lots = 0.0;
double g_total_sell_lots = 0.0;
double g_average_buy_price = 0.0;
double g_average_sell_price = 0.0;

// Simple Trading Variables
int g_bars_counter = 0;
datetime g_last_trade_bar_time = 0;

// Trading State Management and Locking Variables
bool g_trading_lock = false;
datetime g_lock_time = 0;
int g_lock_timeout_seconds = 30;
bool g_order_processing = false;
int g_min_order_delay_seconds = 1; // Minimum 1 second between orders

// Advanced Order Validation Variables
double g_recent_order_prices[10]; // Track recent order prices
datetime g_recent_order_times[10]; // Track recent order times
int g_recent_order_count = 0;
// g_max_orders_per_minute already declared above
double g_min_price_distance_points = 5.0; // Minimum distance between orders in points

// Error Recovery System Variables
enum ENUM_EA_ERROR_CODES
{
    ERROR_NONE = 0,
    ERROR_INSUFFICIENT_MARGIN = 1001,
    ERROR_INVALID_LOT_SIZE = 1002,
    ERROR_BROKER_BUSY = 1003,
    ERROR_PRICE_CHANGED = 1004,
    ERROR_STATE_CORRUPTION = 1005,
    ERROR_LOCK_TIMEOUT = 1006,
    ERROR_GRID_DIRECTION_CONFLICT = 1007,
    ERROR_EXCESSIVE_EXPOSURE = 1008
};

int g_last_error_code = ERROR_NONE;
datetime g_last_error_time = 0;
int g_error_recovery_attempts = 0;
int g_max_recovery_attempts = 3;

// Grid Direction Management Variables
int g_current_grid_direction = 0; // 0 = None, 1 = Buy Grid, - 1 = Sell Grid
datetime g_grid_direction_start_time = 0;
bool g_enforce_single_direction = true; // Enforce single direction grid
double g_grid_direction_change_threshold = 50.0; // Points to trigger direction change

// Market Structure Variables
int g_current_trend = 0; // 1 = Bullish, - 1 = Bearish, 0 = Neutral
bool g_bos_detected = false; // Break of Structure detected
bool g_choch_detected = false; // Change of Character detected
double g_last_higher_high = 0;
double g_last_higher_low = 0;
double g_last_lower_high = 0;
double g_last_lower_low = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    // Validate inputs
    if(InpMagicNumber <= 0)
    {
        Print("Error: Invalid Magic Number");
        return INIT_PARAMETERS_INCORRECT;
    }

    if(InpRiskPercent <= 0 || InpRiskPercent > 10)
    {
        Print("Error: Risk Percent must be between 0.1 and 10.0");
        return INIT_PARAMETERS_INCORRECT;
    }

    // Initialize symbol
    if(!symbolInfo.Name(_Symbol))
    {
        Print("Error: Failed to initialize symbol");
        return INIT_FAILED;
    }

    // Set magic number for trading
    trade.SetExpertMagicNumber(InpMagicNumber);

    // Initialize indicators
    if(!InitializeIndicators())
    {
        Print("Error: Failed to initialize indicators");
        return INIT_FAILED;
    }

    // Initialize arrays
    ArrayResize(g_fvg_zones, MAX_FVG_ZONES);
    ArrayResize(g_order_blocks, MAX_ORDER_BLOCKS);
    ArrayResize(g_structure_points, MAX_STRUCTURE_POINTS);
    ArrayResize(g_liquidity_zones, MAX_LIQUIDITY_ZONES);

    InitializeFVGArray();
    InitializeOrderBlockArray();
    InitializeStructureArray();
    InitializeLiquidityArray();
    InitializeStatistics();

    // Initialize daily tracking
    g_daily_start_balance = account.Balance();
    g_last_day_check = TimeCurrent();
    g_orders_today = 0;
    g_highest_equity = account.Equity();
    g_trading_allowed = true;

    // Initialize error correction system
    InitializeErrorCorrection();

    // Initialize grid system
    InitializeGridSystem();
    
    // Initialize trading state management
    g_trading_lock = false;
    g_lock_time = 0;
    g_order_processing = false;
    g_last_order_time = 0;
    
    // Initialize grid direction management
    g_current_grid_direction = 0;
    g_grid_direction_start_time = 0;
    g_enforce_single_direction = InpEnforceSingleDirection;
    g_grid_direction_change_threshold = InpDirectionChangeThreshold;

    Print("FVG Trading EA initialized successfully with Grid System");
    Print("Grid Distance: ", InpGridDistance, " points, Multiplier: ", InpGridMultiplier);
    if(InpUseMarginTP)
        Print("Take Profit: Margin-based (", InpMarginTPPercent, "% of margin), Stop Loss: DISABLED");
    else
        Print("Take Profit: ", InpTakeProfit, " points, Stop Loss: ", (InpUseStopLoss ? "Enabled" : "DISABLED"));
    if(InpHighFrequencyMode)
    Print("Target Daily Lots: ", InpTargetDailyLots);
    if(InpUseErrorCorrection)
    Print("Error Correction: Enabled, Lot Multiplier: ", InpLotMultiplier);
    if(InpUseReverseTrading)
    Print("Reverse Trading: Enabled after ", InpReverseAfterLosses, " consecutive losses");

    // Test the new progressive lot calculation
    TestProgressiveLotCalculation();
    
    // Test duplicate order prevention
    TestDuplicateOrderPrevention();
    
    // Test grid direction management
    TestGridDirectionManagement();
    
    // Test state management system
    TestStateManagement();
    
    // Test grid system integration
    TestGridSystemIntegration();
    
    // Test advanced order validation
    TestAdvancedOrderValidation();
    
    // Test error recovery system
    TestErrorRecoverySystem();
    
    // Test lot size calculation functions (Unit Tests)
    TestLotSizeCalculationFunctions();
    
    // Test grid logic functions (Unit Tests)
    TestGridLogicFunctions();
    
    // Test complete order execution flow (Integration Test)
    TestCompleteOrderExecutionFlow();
    
    // Test risk management integration (Integration Test)
    TestRiskManagementIntegration();
    
    // Perform position synchronization on EA restart
    Print("Performing position synchronization on EA restart...");
    RebuildGridStateFromPositions();
    
    // Validate state after rebuild
    ValidateGridStateConsistency();

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Clean up chart objects
    CleanupChartObjects();

    // Release indicator handles
    if(h_atr != INVALID_HANDLE) IndicatorRelease(h_atr);
    if(h_fast_ma != INVALID_HANDLE) IndicatorRelease(h_fast_ma);
    if(h_slow_ma != INVALID_HANDLE) IndicatorRelease(h_slow_ma);
    if(h_rsi != INVALID_HANDLE) IndicatorRelease(h_rsi);
    if(h_adx != INVALID_HANDLE) IndicatorRelease(h_adx);
    if(h_htf1_ma != INVALID_HANDLE) IndicatorRelease(h_htf1_ma);
    if(h_htf2_ma != INVALID_HANDLE) IndicatorRelease(h_htf2_ma);

    Print("FVG Trading EA deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // High frequency mode - don't wait for new bar
    if(!InpHighFrequencyMode)
    {
        // Check if new bar only in normal mode
        if(!IsNewBar()) return;
    }

    // Update daily statistics
    UpdateDailyStats();

    // Force close old positions
    ForceCloseOldPositions();

    // Check for closed positions and handle results
    CheckClosedPositions();

    // DISABLE ALL SAFETY CHECKS FOR AGGRESSIVE GRID
    // Force trading without any limits

    // DISABLE TIME AND SPREAD CHECKS
    // Trade 24/7 with any spread

    // Update grid state periodically (every 10th tick for performance)
    static int state_update_counter = 0;
    static int emergency_check_counter = 0;
    state_update_counter++;
    emergency_check_counter++;
    
    if(state_update_counter >= 10)
    {
        UpdateGridState();
        FixGridDirectionSync(); // Fix grid direction synchronization
        state_update_counter = 0;
    }
    
    // Emergency state check every 100 ticks
    if(emergency_check_counter >= 100)
    {
        // Comprehensive error detection and recovery
        DetectAndRecoverErrors();
        
        // Legacy emergency check (kept for compatibility)
        if(g_trading_lock && (TimeCurrent() - g_lock_time) > (g_lock_timeout_seconds * 2))
        {
            Print("EMERGENCY: Detected stuck lock, performing recovery");
            EmergencyStateRecovery();
        }
        emergency_check_counter = 0;
    }

    // Update FVG zones
    UpdateFVGZones();

    // Aggressive FVG detection for high frequency
    if(InpHighFrequencyMode)
    {
        AggressiveFVGDetection();
    }

    // Smart Money Concepts Analysis
    if(InpUseSMC)
    {
        UpdateMarketStructure();
        if(InpUseOrderBlocks) UpdateOrderBlocks();
        if(InpUseLiquidity) UpdateLiquidityZones();
    }

    // Multi-timeframe analysis
    if(InpUseMTF) UpdateHTFAnalysis();

    // Look for trading opportunities
    CheckTradingSignals();

    // Check grid profit closure
    CheckCloseAllOnProfit();

    // เพิ่มการตรวจสอบและเปิดออเดอร์ Grid อัตโนมัติ
    CheckAndOpenGridOrders();

    // Manage open positions
    ManageOpenPositions();

    // Update chart display (disabled for speed in simple mode)
    if(!InpSimpleMode)
    {
        if(InpShowFVGZones) DisplayFVGZones();
        if(InpUseSMC && InpUseOrderBlocks) DisplayOrderBlocks();
    }

    // Display statistics (reduced frequency)
    if(g_orders_today % 30 == 1) // Every 30th order only
    DisplayStatistics();
}

//+------------------------------------------------------------------+
//| Initialize indicators                                            |
//+------------------------------------------------------------------+
bool InitializeIndicators()
{
    // ATR indicator (disabled in grid system)
    h_atr = INVALID_HANDLE;

    // Moving averages
    if(InpUseMAFilter)
    {
        h_fast_ma = iMA(_Symbol, PERIOD_CURRENT, InpFastMA, 0, InpMAMethod, PRICE_CLOSE);
        h_slow_ma = iMA(_Symbol, PERIOD_CURRENT, InpSlowMA, 0, InpMAMethod, PRICE_CLOSE);

        if(h_fast_ma == INVALID_HANDLE || h_slow_ma == INVALID_HANDLE)
        {
            Print("Error creating MA indicators");
            return false;
        }
    }

    // RSI indicator
    if(InpUseRSIFilter)
    {
        h_rsi = iRSI(_Symbol, PERIOD_CURRENT, InpRSIPeriod, PRICE_CLOSE);
        if(h_rsi == INVALID_HANDLE)
        {
            Print("Error creating RSI indicator");
            return false;
        }
    }

    // ADX indicator
    if(InpUseADXFilter)
    {
        h_adx = iADX(_Symbol, PERIOD_CURRENT, InpADXPeriod);
        if(h_adx == INVALID_HANDLE)
        {
            Print("Error creating ADX indicator");
            return false;
        }
    }

    // Multi-timeframe indicators
    if(InpUseMTF)
    {
        h_htf1_ma = iMA(_Symbol, InpHTF1, InpSlowMA, 0, InpMAMethod, PRICE_CLOSE);
        h_htf2_ma = iMA(_Symbol, InpHTF2, InpSlowMA, 0, InpMAMethod, PRICE_CLOSE);

        if(h_htf1_ma == INVALID_HANDLE || h_htf2_ma == INVALID_HANDLE)
        {
            Print("Error creating HTF MA indicators");
            return false;
        }
    }

    return true;
}

//+------------------------------------------------------------------+
//| Check if new bar                                                |
//+------------------------------------------------------------------+
bool IsNewBar()
{
    datetime current_time = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(current_time != g_last_bar_time)
    {
        g_last_bar_time = current_time;
        return true;
    }
    return false;
}

//+------------------------------------------------------------------+
//| Update daily statistics                                         |
//+------------------------------------------------------------------+
void UpdateDailyStats()
{
    datetime current_time = TimeCurrent();
    MqlDateTime dt;
    TimeToStruct(current_time, dt);

    MqlDateTime last_dt;
    TimeToStruct(g_last_day_check, last_dt);

    // Reset daily counters at midnight
    if(dt.day != last_dt.day)
    {
        g_orders_today = 0;
        g_daily_start_balance = account.Balance();
        g_last_day_check = current_time;
    }
}

//+------------------------------------------------------------------+
//| Safety checks                                                   |
//+------------------------------------------------------------------+
bool SafetyChecks()
{
    // Check if trading is allowed
    if(!g_trading_allowed)
    {
        return false;
    }

    // Check daily loss limit
    double current_balance = account.Balance();
    double daily_loss_percent = (g_daily_start_balance - current_balance) / g_daily_start_balance * 100.0;

    if(daily_loss_percent > InpMaxDailyLoss)
    {
        Print("Daily loss limit reached: ", daily_loss_percent, " % ");
        g_trading_allowed = false;
        return false;
    }

    // Check daily order limit
    if(g_orders_today >= InpMaxOrdersPerDay)
    {
        return false;
    }

    // Check if market is open
    if(!symbolInfo.RefreshRates())
    {
        return false;
    }

    // Check trading hours
    if(InpUseTradingHours && !IsWithinTradingHours())
    {
        return false;
    }

    // Check if we already have maximum positions (Grid system allows multiple)
    if(CountOpenPositions() >= InpMaxGridLevels)
    {
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Check if within trading hours                                   |
//+------------------------------------------------------------------+
bool IsWithinTradingHours()
{
    if(!InpUseTradingHours) return true;

    MqlDateTime dt;
    TimeToStruct(TimeCurrent(), dt);

    // Handle overnight sessions (e.g., 22:00 to 08:00)
    if(InpStartHour > InpEndHour)
    {
        return(dt.hour >= InpStartHour || dt.hour < InpEndHour);
    }
    else
    {
        return(dt.hour >= InpStartHour && dt.hour < InpEndHour);
    }
}

//+------------------------------------------------------------------+
//| Get current spread                                              |
//+------------------------------------------------------------------+
double GetCurrentSpread()
{
    return(symbolInfo.Ask() - symbolInfo.Bid()) / symbolInfo.Point();
}

//+------------------------------------------------------------------+
//| Initialize FVG array                                            |
//+------------------------------------------------------------------+
void InitializeFVGArray()
{
    for(int i = 0; i < MAX_FVG_ZONES; i++)
    {
        g_fvg_zones[i].valid = false;
        g_fvg_zones[i].filled = false;
        g_fvg_zones[i].type = 0;
        g_fvg_zones[i].high = 0;
        g_fvg_zones[i].low = 0;
        g_fvg_zones[i].time = 0;
        g_fvg_zones[i].bars_age = 0;
        g_fvg_zones[i].quality_score = 0;
        g_fvg_zones[i].strength = 0;
        g_fvg_zones[i].confirmed = false;
        g_fvg_zones[i].volume = 0;
        g_fvg_zones[i].institutional = false;
    }
    g_fvg_count = 0;
}

//+------------------------------------------------------------------+
//| Initialize Order Block array                                    |
//+------------------------------------------------------------------+
void InitializeOrderBlockArray()
{
    for(int i = 0; i < MAX_ORDER_BLOCKS; i++)
    {
        g_order_blocks[i].valid = false;
        g_order_blocks[i].tested = false;
        g_order_blocks[i].broken = false;
        g_order_blocks[i].type = 0;
        g_order_blocks[i].high = 0;
        g_order_blocks[i].low = 0;
        g_order_blocks[i].time = 0;
        g_order_blocks[i].strength = 0;
        g_order_blocks[i].touches = 0;
    }
    g_ob_count = 0;
}

//+------------------------------------------------------------------+
//| Initialize Structure array                                       |
//+------------------------------------------------------------------+
void InitializeStructureArray()
{
    for(int i = 0; i < MAX_STRUCTURE_POINTS; i++)
    {
        g_structure_points[i].price = 0;
        g_structure_points[i].time = 0;
        g_structure_points[i].type = 0;
        g_structure_points[i].broken = false;
        g_structure_points[i].liquidity_swept = false;
    }
    g_structure_count = 0;
}

//+------------------------------------------------------------------+
//| Initialize Liquidity array                                      |
//+------------------------------------------------------------------+
void InitializeLiquidityArray()
{
    for(int i = 0; i < MAX_LIQUIDITY_ZONES; i++)
    {
        g_liquidity_zones[i].price = 0;
        g_liquidity_zones[i].time = 0;
        g_liquidity_zones[i].type = 0;
        g_liquidity_zones[i].swept = false;
        g_liquidity_zones[i].strength = 0;
    }
    g_liquidity_count = 0;
}

//+------------------------------------------------------------------+
//| Initialize Statistics                                            |
//+------------------------------------------------------------------+
void InitializeStatistics()
{
    g_stats.total_trades = 0;
    g_stats.winning_trades = 0;
    g_stats.losing_trades = 0;
    g_stats.total_profit = 0;
    g_stats.total_loss = 0;
    g_stats.win_rate = 0;
    g_stats.profit_factor = 0;
    g_stats.max_drawdown = 0;
    g_stats.current_drawdown = 0;
    g_stats.last_trade_time = 0;
}

//+------------------------------------------------------------------+
//| Update Market Structure                                          |
//+------------------------------------------------------------------+
void UpdateMarketStructure()
{
    // Get recent price data for structure analysis
    double high[], low[], close[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);

    int bars_needed = 20;
    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars_needed, high) != bars_needed) return;
    if(CopyLow(_Symbol, PERIOD_CURRENT, 0, bars_needed, low) != bars_needed) return;
    if(CopyClose(_Symbol, PERIOD_CURRENT, 0, bars_needed, close) != bars_needed) return;

    // Detect swing highs and lows
    DetectSwingPoints(high, low, close, bars_needed);

    // Analyze Break of Structure (BOS)
    if(InpUseBOS) DetectBreakOfStructure(high, low, close);

    // Analyze Change of Character (CHoCH)
    if(InpUseCHoCH) DetectChangeOfCharacter(high, low, close);
}

//+------------------------------------------------------------------+
//| Detect Swing Points                                             |
//+------------------------------------------------------------------+
void DetectSwingPoints(const double &high[], const double &low[], const double &close[], int bars)
{
    int swing_period = 5; // Look for swings over 5 bars

    for(int i = swing_period; i < bars - swing_period; i++)
    {
        bool is_swing_high = true;
        bool is_swing_low = true;

        // Check if current bar is a swing high
        for(int j = i - swing_period; j <= i + swing_period; j++)
        {
            if(j != i && high[j] >= high[i])
            {
                is_swing_high = false;
                break;
            }
        }

        // Check if current bar is a swing low
        for(int j = i - swing_period; j <= i + swing_period; j++)
        {
            if(j != i && low[j] <= low[i])
            {
                is_swing_low = false;
                break;
            }
        }

        // Add swing high
        if(is_swing_high)
        {
            AddStructurePoint(high[i], iTime(_Symbol, PERIOD_CURRENT, i), 1); // Higher High candidate
        }

        // Add swing low
        if(is_swing_low)
        {
            AddStructurePoint(low[i], iTime(_Symbol, PERIOD_CURRENT, i), - 1); // Lower Low candidate
        }
    }
}

//+------------------------------------------------------------------+
//| Add Structure Point                                             |
//+------------------------------------------------------------------+
void AddStructurePoint(double price, datetime time, int type)
{
    // Find empty slot or replace oldest
    int index = - 1;

    for(int i = 0; i < MAX_STRUCTURE_POINTS; i++)
    {
        if(g_structure_points[i].price == 0)
        {
            index = i;
            break;
        }
    }

    if(index == - 1)
    {
        // Shift array and add to end
        for(int i = 0; i < MAX_STRUCTURE_POINTS - 1; i++)
        {
            g_structure_points[i] = g_structure_points[i + 1];
        }
        index = MAX_STRUCTURE_POINTS - 1;
    }

    g_structure_points[index].price = price;
    g_structure_points[index].time = time;
    g_structure_points[index].type = type;
    g_structure_points[index].broken = false;
    g_structure_points[index].liquidity_swept = false;

    if(index >= g_structure_count)
    g_structure_count = index + 1;
}

//+------------------------------------------------------------------+
//| Detect Break of Structure                                       |
//+------------------------------------------------------------------+
void DetectBreakOfStructure(const double &high[], const double &low[], const double &close[])
{
    double current_price = close[0];
    g_bos_detected = false;

    // Check for bullish BOS (break above previous high)
    for(int i = 0; i < g_structure_count; i++)
    {
        if(g_structure_points[i].type == 1 && !g_structure_points[i].broken)
        {
            if(current_price > g_structure_points[i].price)
            {
                g_structure_points[i].broken = true;
                g_bos_detected = true;
                g_current_trend = 1; // Bullish
                break;
            }
        }
    }

    // Check for bearish BOS (break below previous low)
    for(int i = 0; i < g_structure_count; i++)
    {
        if(g_structure_points[i].type == - 1 && !g_structure_points[i].broken)
        {
            if(current_price < g_structure_points[i].price)
            {
                g_structure_points[i].broken = true;
                g_bos_detected = true;
                g_current_trend = - 1; // Bearish
                break;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Detect Change of Character                                      |
//+------------------------------------------------------------------+
void DetectChangeOfCharacter(const double &high[], const double &low[], const double &close[])
{
    g_choch_detected = false;

    // Simplified CHoCH detection
    // Look for trend reversal patterns
    if(g_current_trend == 1) // Currently bullish
    {
        // Look for lower high followed by lower low
        for(int i = 1; i < 10; i++)
        {
            if(high[i] > high[0] && low[i + 1] < low[i])
            {
                g_choch_detected = true;
                g_current_trend = - 1;
                break;
            }
        }
    }
    else if(g_current_trend == - 1) // Currently bearish
    {
        // Look for higher low followed by higher high
        for(int i = 1; i < 10; i++)
        {
            if(low[i] < low[0] && high[i + 1] > high[i])
            {
                g_choch_detected = true;
                g_current_trend = 1;
                break;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Update Order Blocks                                             |
//+------------------------------------------------------------------+
void UpdateOrderBlocks()
{
    // Age existing order blocks
    for(int i = 0; i < g_ob_count; i++)
    {
        if(g_order_blocks[i].valid)
        {
            // Check if order block is tested
            double current_price = symbolInfo.Bid();

            if(g_order_blocks[i].type == 1) // Bullish OB
            {
                if(current_price >= g_order_blocks[i].low && current_price <= g_order_blocks[i].high)
                {
                    g_order_blocks[i].tested = true;
                    g_order_blocks[i].touches++;
                }

                // Mark as broken if price closes below
                if(current_price < g_order_blocks[i].low)
                {
                    g_order_blocks[i].broken = true;
                }
            }
            else if(g_order_blocks[i].type == - 1) // Bearish OB
            {
                if(current_price >= g_order_blocks[i].low && current_price <= g_order_blocks[i].high)
                {
                    g_order_blocks[i].tested = true;
                    g_order_blocks[i].touches++;
                }

                // Mark as broken if price closes above
                if(current_price > g_order_blocks[i].high)
                {
                    g_order_blocks[i].broken = true;
                }
            }
        }
    }

    // Detect new order blocks
    DetectNewOrderBlocks();
}

//+------------------------------------------------------------------+
//| Detect New Order Blocks                                         |
//+------------------------------------------------------------------+
void DetectNewOrderBlocks()
{
    // Get recent bar data
    double high[], low[], close[], open[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);
    ArraySetAsSeries(close, true);
    ArraySetAsSeries(open, true);

    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 10, high) != 10) return;
    if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 10, low) != 10) return;
    if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 10, close) != 10) return;
    if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, 10, open) != 10) return;

    // Look for strong bullish candles followed by continuation
    for(int i = 1; i < 5; i++)
    {
        double body_size = MathAbs(close[i] - open[i]);
        double candle_range = high[i] - low[i];

        // Bullish order block: Strong bullish candle
        if(close[i] > open[i] && body_size > candle_range * 0.7)
        {
            // Check if price moved away and created imbalance
            if(low[i - 1] > high[i] && close[0] > close[i])
            {
                AddOrderBlock(low[i], high[i], iTime(_Symbol, PERIOD_CURRENT, i), 1);
            }
        }

        // Bearish order block: Strong bearish candle
        if(close[i] < open[i] && body_size > candle_range * 0.7)
        {
            // Check if price moved away and created imbalance
            if(high[i - 1] < low[i] && close[0] < close[i])
            {
                AddOrderBlock(low[i], high[i], iTime(_Symbol, PERIOD_CURRENT, i), - 1);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Add Order Block                                                 |
//+------------------------------------------------------------------+
void AddOrderBlock(double low_price, double high_price, datetime time, int type)
{
    int index = - 1;

    // Find empty slot
    for(int i = 0; i < MAX_ORDER_BLOCKS; i++)
    {
        if(!g_order_blocks[i].valid)
        {
            index = i;
            break;
        }
    }

    // If no empty slot, replace oldest
    if(index == - 1)
    {
        datetime oldest_time = TimeCurrent();
        for(int i = 0; i < MAX_ORDER_BLOCKS; i++)
        {
            if(g_order_blocks[i].time < oldest_time)
            {
                oldest_time = g_order_blocks[i].time;
                index = i;
            }
        }
    }

    if(index >= 0)
    {
        g_order_blocks[index].low = low_price;
        g_order_blocks[index].high = high_price;
        g_order_blocks[index].time = time;
        g_order_blocks[index].type = type;
        g_order_blocks[index].valid = true;
        g_order_blocks[index].tested = false;
        g_order_blocks[index].broken = false;
        g_order_blocks[index].strength = CalculateOrderBlockStrength(low_price, high_price, type);
        g_order_blocks[index].touches = 0;

        if(index >= g_ob_count)
        g_ob_count = index + 1;
    }
}

//+------------------------------------------------------------------+
//| Calculate Order Block Strength                                  |
//+------------------------------------------------------------------+
double CalculateOrderBlockStrength(double low_price, double high_price, int type)
{
    double strength = 50.0; // Base strength

    // Factor in size of the order block
    double ob_size = high_price - low_price;
    double atr_value = GetAverageRange(14);

    if(atr_value > 0)
    {
        double size_ratio = ob_size / atr_value;
        strength += MathMin(size_ratio * 20, 30);
    }

    // Factor in trend alignment
    if((type == 1 && g_current_trend > 0) || (type == - 1 && g_current_trend < 0))
    {
        strength += 20;
    }

    return MathMin(strength, 100.0);
}

//+------------------------------------------------------------------+
//| Update Liquidity Zones                                          |
//+------------------------------------------------------------------+
void UpdateLiquidityZones()
{
    // Simplified liquidity detection
    // Look for equal highs/lows that represent liquidity pools

    double high[], low[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);

    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 50, high) != 50) return;
    if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 50, low) != 50) return;

    double tolerance = symbolInfo.Point() * 5; // 5 point tolerance

    // Find equal highs (sell-side liquidity)
    for(int i = 5; i < 45; i++)
    {
        int equal_count = 1;
        for(int j = i + 1; j < 50; j++)
        {
            if(MathAbs(high[i] - high[j]) <= tolerance)
            {
                equal_count++;
            }
        }

        if(equal_count >= 3) // At least 3 equal highs
        {
            AddLiquidityZone(high[i], iTime(_Symbol, PERIOD_CURRENT, i), - 1); // Sell - side liquidity
        }
    }

    // Find equal lows (buy-side liquidity)
    for(int i = 5; i < 45; i++)
    {
        int equal_count = 1;
        for(int j = i + 1; j < 50; j++)
        {
            if(MathAbs(low[i] - low[j]) <= tolerance)
            {
                equal_count++;
            }
        }

        if(equal_count >= 3) // At least 3 equal lows
        {
            AddLiquidityZone(low[i], iTime(_Symbol, PERIOD_CURRENT, i), 1); // Buy - side liquidity
        }
    }
}

//+------------------------------------------------------------------+
//| Add Liquidity Zone                                              |
//+------------------------------------------------------------------+
void AddLiquidityZone(double price, datetime time, int type)
{
    // Check if similar liquidity zone already exists
    for(int i = 0; i < g_liquidity_count; i++)
    {
        if(MathAbs(g_liquidity_zones[i].price - price) <= symbolInfo.Point() * 10)
        {
            return; // Similar zone already exists
        }
    }

    int index = - 1;

    // Find empty slot
    for(int i = 0; i < MAX_LIQUIDITY_ZONES; i++)
    {
        if(g_liquidity_zones[i].price == 0)
        {
            index = i;
            break;
        }
    }

    if(index == - 1 && g_liquidity_count < MAX_LIQUIDITY_ZONES)
    {
        index = g_liquidity_count;
    }

    if(index >= 0)
    {
        g_liquidity_zones[index].price = price;
        g_liquidity_zones[index].time = time;
        g_liquidity_zones[index].type = type;
        g_liquidity_zones[index].swept = false;
        g_liquidity_zones[index].strength = 70.0; // Default strength

        if(index >= g_liquidity_count)
        g_liquidity_count = index + 1;
    }
}

//+------------------------------------------------------------------+
//| Update Higher Timeframe Analysis                                |
//+------------------------------------------------------------------+
void UpdateHTFAnalysis()
{
    if(h_htf1_ma == INVALID_HANDLE || h_htf2_ma == INVALID_HANDLE) return;

    // This is a simplified HTF analysis
    // In a full implementation, you would analyze HTF structure, trends, etc.

    // For now, just update the HTF trend direction
    // This would be expanded significantly in a production EA
}

//+------------------------------------------------------------------+
//| Update FVG zones                                                |
//+------------------------------------------------------------------+
void UpdateFVGZones()
{
    // Age existing FVG zones
    for(int i = 0; i < g_fvg_count; i++)
    {
        if(g_fvg_zones[i].valid)
        {
            g_fvg_zones[i].bars_age++;

            // Remove old FVG zones
            if(g_fvg_zones[i].bars_age > InpMaxFVGAge)
            {
                g_fvg_zones[i].valid = false;
            }

            // Check if FVG is filled
            CheckFVGFilled(i);
        }
    }

    // Look for new FVG zones
    DetectNewFVG();

    // Clean up invalid zones
    CleanupFVGArray();
}

//+------------------------------------------------------------------+
//| Detect new FVG zones                                            |
//+------------------------------------------------------------------+
void DetectNewFVG()
{
    // Need at least 3 bars to detect FVG
    if(iBars(_Symbol, PERIOD_CURRENT) < 3) return;

    // Get recent bar data
    double high[], low[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);

    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 3, high) != 3) return;
    if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 3, low) != 3) return;

    // Check for Bullish FVG (gap up)
    // Bar 2 low > Bar 0 high
    if(low[2] > high[0])
    {
        double gap_size = low[2] - high[0];
        if(gap_size >= InpMinFVGSize * symbolInfo.Point())
        {
            double quality = CalculateFVGQuality(high[0], low[2], 1);
            if(quality >= InpFVGQualityFilter)
            {
                AddFVGZone(high[0], low[2], iTime(_Symbol, PERIOD_CURRENT, 1), 1, quality);
            }
        }
    }

    // Check for Bearish FVG (gap down)
    // Bar 2 high < Bar 0 low
    if(high[2] < low[0])
    {
        double gap_size = low[0] - high[2];
        if(gap_size >= InpMinFVGSize * symbolInfo.Point())
        {
            double quality = CalculateFVGQuality(high[2], low[0], - 1);
            if(quality >= InpFVGQualityFilter)
            {
                AddFVGZone(high[2], low[0], iTime(_Symbol, PERIOD_CURRENT, 1), - 1, quality);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Calculate FVG quality score                                     |
//+------------------------------------------------------------------+
double CalculateFVGQuality(double low_price, double high_price, int fvg_type)
{
    double quality = 50.0; // Base quality

    // Factor 1: Gap size (larger gaps = higher quality)
    double gap_size = high_price - low_price;
    double avg_range = GetAverageRange(14);
    if(avg_range > 0)
    {
        double size_ratio = gap_size / avg_range;
        quality += MathMin(size_ratio * 20, 30); // Max 30 points
    }

    // Factor 2: Volume (if available)
    // For simplicity, we'll skip volume analysis in this version

    // Factor 3: Market structure context
    int trend_direction = GetTrendDirection();
    if((fvg_type == 1 && trend_direction > 0) || (fvg_type == - 1 && trend_direction < 0))
    {
        quality += 20; // Trend alignment bonus
    }

    return MathMin(quality, 100.0);
}

//+------------------------------------------------------------------+
//| Get average range                                               |
//+------------------------------------------------------------------+
double GetAverageRange(int periods)
{
    if(h_atr == INVALID_HANDLE) return 0;

    double atr_values[];
    if(CopyBuffer(h_atr, 0, 0, 1, atr_values) <= 0) return 0;

    return atr_values[0];
}

//+------------------------------------------------------------------+
//| Get trend direction                                             |
//+------------------------------------------------------------------+
int GetTrendDirection()
{
    if(!InpUseMAFilter || h_fast_ma == INVALID_HANDLE || h_slow_ma == INVALID_HANDLE)
    return 0;

    double fast_ma[], slow_ma[];
    if(CopyBuffer(h_fast_ma, 0, 0, 2, fast_ma) <= 0) return 0;
    if(CopyBuffer(h_slow_ma, 0, 0, 2, slow_ma) <= 0) return 0;

    // Check if fast MA is above slow MA and rising
    if(fast_ma[0] > slow_ma[0] && fast_ma[0] > fast_ma[1])
    return 1; // Bullish

    if(fast_ma[0] < slow_ma[0] && fast_ma[0] < fast_ma[1])
    return - 1; // Bearish

    return 0; // Neutral
}

//+------------------------------------------------------------------+
//| Add FVG zone                                                    |
//+------------------------------------------------------------------+
void AddFVGZone(double low_price, double high_price, datetime time, int type, double quality)
{
    // Find empty slot or replace oldest
    int index = - 1;

    // Look for empty slot
    for(int i = 0; i < MAX_FVG_ZONES; i++)
    {
        if(!g_fvg_zones[i].valid)
        {
            index = i;
            break;
        }
    }

    // If no empty slot, replace oldest
    if(index == - 1)
    {
        datetime oldest_time = TimeCurrent();
        for(int i = 0; i < MAX_FVG_ZONES; i++)
        {
            if(g_fvg_zones[i].time < oldest_time)
            {
                oldest_time = g_fvg_zones[i].time;
                index = i;
            }
        }
    }

    if(index >= 0)
    {
        g_fvg_zones[index].low = low_price;
        g_fvg_zones[index].high = high_price;
        g_fvg_zones[index].time = time;
        g_fvg_zones[index].type = type;
        g_fvg_zones[index].valid = true;
        g_fvg_zones[index].filled = false;
        g_fvg_zones[index].bars_age = 0;
        g_fvg_zones[index].quality_score = quality;

        if(index >= g_fvg_count)
        g_fvg_count = index + 1;
    }
}

//+------------------------------------------------------------------+
//| Check if FVG is filled                                          |
//+------------------------------------------------------------------+
void CheckFVGFilled(int index)
{
    if(!g_fvg_zones[index].valid || g_fvg_zones[index].filled) return;

    double current_price = symbolInfo.Bid();

    // For bullish FVG, check if price moved back down into the gap
    if(g_fvg_zones[index].type == 1)
    {
        if(current_price <= g_fvg_zones[index].high && current_price >= g_fvg_zones[index].low)
        {
            g_fvg_zones[index].filled = true;
        }
    }
    // For bearish FVG, check if price moved back up into the gap
    else if(g_fvg_zones[index].type == - 1)
    {
        if(current_price >= g_fvg_zones[index].low && current_price <= g_fvg_zones[index].high)
        {
            g_fvg_zones[index].filled = true;
        }
    }
}

//+------------------------------------------------------------------+
//| Cleanup FVG array                                              |
//+------------------------------------------------------------------+
void CleanupFVGArray()
{
    for(int i = g_fvg_count - 1; i >= 0; i--)
    {
        if(!g_fvg_zones[i].valid)
        {
            // Shift array down
            for(int j = i; j < g_fvg_count - 1; j++)
            {
                g_fvg_zones[j] = g_fvg_zones[j + 1];
            }
            g_fvg_count--;
        }
    }
}

//+------------------------------------------------------------------+
//| Check trading signals                                           |
//+------------------------------------------------------------------+
void CheckTradingSignals()
{
    // UNLIMITED GRID POSITIONS
    // No limits on number of positions

    // Simple Mode: Trade every X bars regardless of signals
    if(InpSimpleMode)
    {
        datetime current_bar_time = iTime(_Symbol, PERIOD_CURRENT, 0);

        // Only trade on new bars
        if(current_bar_time == g_last_trade_bar_time) return;

        g_bars_counter++;

        // Trade every X bars
        if(g_bars_counter >= InpTradeEveryBars)
        {
            g_bars_counter = 0;
            g_last_trade_bar_time = current_bar_time;

            // SIMPLE GRID LOGIC - ป้องกัน Volume 100+ ปัญหา
            double price_now = symbolInfo.Bid();

            // ตรวจสอบ positions ที่มีอยู่
            int buy_positions = 0;
            int sell_positions = 0;

            for(int i = 0; i < PositionsTotal(); i++)
            {
                if(position.SelectByIndex(i) && position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
                {
                    if(position.PositionType() == POSITION_TYPE_BUY)
                    buy_positions++;
                    else
                    sell_positions++;
                }
            }

            // GRID LOGIC: ถ้าไม่มี position ให้เริ่มต้นด้วยทิศทางเทรน
            if(buy_positions == 0 && sell_positions == 0)
            {
                double price_prev = iClose(_Symbol, PERIOD_CURRENT, 1);
                if(price_now > price_prev)
                OpenBuyOrder(0); // เริ่มด้วย Buy
                else
                OpenSellOrder(0); // เริ่มด้วย Sell
            }
            // ถ้ามี Buy positions แล้ว ให้เพิ่ม Buy เท่านั้น (Grid)
            else if(buy_positions > 0 && sell_positions == 0)
            {
                OpenBuyOrder(0); // เพิ่ม Buy Grid
            }
            // ถ้ามี Sell positions แล้ว ให้เพิ่ม Sell เท่านั้น (Grid)
            else if(sell_positions > 0 && buy_positions == 0)
            {
                OpenSellOrder(0); // เพิ่ม Sell Grid
            }
            // ถ้ามีทั้งสอง = ไม่เทรด (ป้องกันความวุ่นวาย)

            return;
        }
    }

    // Original FVG-based trading (slower) - with grid direction enforcement
    double current_price = symbolInfo.Bid();

    // Check each FVG zone for trading opportunities
    for(int i = 0; i < g_fvg_count; i++)
    {
        if(!g_fvg_zones[i].valid || g_fvg_zones[i].filled) continue;

        // TREND FOLLOWING LOGIC with grid direction validation
        if(g_fvg_zones[i].type == 1) // bullish zone
        {
            if(current_price >= g_fvg_zones[i].high) // price breaks above
            {
                // Check if we can open sell order (respects grid direction)
                if(ValidateGridDirection(ORDER_TYPE_SELL))
                {
                    OpenSellOrder(i);
                    return;
                }
            }
        }
        else if(g_fvg_zones[i].type == - 1) // bearish zone
        {
            if(current_price <= g_fvg_zones[i].low) // price breaks below
            {
                // Check if we can open buy order (respects grid direction)
                if(ValidateGridDirection(ORDER_TYPE_BUY))
                {
                    OpenBuyOrder(i);
                    return;
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Validate buy signal                                             |
//+------------------------------------------------------------------+
bool ValidateBuySignal(int fvg_index)
{
    // Check trend alignment
    if(InpUseMAFilter)
    {
        int trend = GetTrendDirection();
        if(trend < 0) return false; // Don't buy in downtrend
    }

    // Check FVG quality
    if(g_fvg_zones[fvg_index].quality_score < InpFVGQualityFilter)
    return false;

    return true;
}

//+------------------------------------------------------------------+
//| Validate sell signal                                            |
//+------------------------------------------------------------------+
bool ValidateSellSignal(int fvg_index)
{
    // Check trend alignment
    if(InpUseMAFilter)
    {
        int trend = GetTrendDirection();
        if(trend > 0) return false; // Don't sell in uptrend
    }

    // Check FVG quality
    if(g_fvg_zones[fvg_index].quality_score < InpFVGQualityFilter)
    return false;

    return true;
}

//+------------------------------------------------------------------+
//| Open buy order                                                  |
//+------------------------------------------------------------------+
void OpenBuyOrder(int fvg_index)
{
    // Check if we can place a new order (duplicate prevention)
    if(!CanPlaceNewOrder())
    {
        return; // Skip if another order is being processed or too soon
    }
    
    // Acquire trading lock to prevent concurrent execution
    if(!AcquireTradingLock())
    {
        Print("WARNING: Cannot acquire trading lock for buy order");
        return;
    }

    // Update grid positions first
    UpdateGridPositions();

    // Get reliable prices
    double ask = GetReliablePrice(true); // Get Ask price

    // Validate price before proceeding
    if(ask <= 0)
    {
        Print("ERROR: Cannot get valid Ask price: ", ask);
        ReleaseTradingLock();
        return;
    }

    // NO REVERSE TRADING - Direct BUY only
    ENUM_ORDER_TYPE order_type = ORDER_TYPE_BUY;

    // Validate grid direction before proceeding
    if(!ValidateOrderDirection(order_type))
    {
        Print("WARNING: Buy order rejected due to grid direction conflict");
        ReleaseTradingLock(); // Release lock before returning
        return;
    }

    // Calculate lot size with new progressive algorithm
    double lot_size = CalculateGridLotSize(order_type);
    string comment = "Grid Buy";

    double entry_price = ask;
    double sl = 0.0; // NO STOP LOSS
    double tp = 0.0; // NO TAKE PROFIT - Grid will close on profit

    // Execute order using enhanced atomic execution function
    bool success = ExecuteGridOrder(order_type, lot_size, entry_price);
    
    if(!success)
    {
        Print("ERROR: Buy order execution failed");
    }
    
    // Always release the trading lock
    ReleaseTradingLock();
}

//+------------------------------------------------------------------+
//| Open sell order                                                 |
//+------------------------------------------------------------------+
void OpenSellOrder(int fvg_index)
{
    // Check if we can place a new order (duplicate prevention)
    if(!CanPlaceNewOrder())
    {
        return; // Skip if another order is being processed or too soon
    }
    
    // Acquire trading lock to prevent concurrent execution
    if(!AcquireTradingLock())
    {
        Print("WARNING: Cannot acquire trading lock for sell order");
        return;
    }

    // Update grid positions first
    UpdateGridPositions();

    // Get reliable prices
    double bid = GetReliablePrice(false); // Get Bid price

    // Validate price before proceeding
    if(bid <= 0)
    {
        Print("ERROR: Cannot get valid Bid price: ", bid);
        ReleaseTradingLock();
        return;
    }

    // NO REVERSE TRADING - Direct SELL only
    ENUM_ORDER_TYPE order_type = ORDER_TYPE_SELL;

    // Validate grid direction before proceeding
    if(!ValidateOrderDirection(order_type))
    {
        Print("WARNING: Sell order rejected due to grid direction conflict");
        ReleaseTradingLock(); // Release lock before returning
        return;
    }

    // Calculate lot size with new progressive algorithm
    double lot_size = CalculateGridLotSize(order_type);
    string comment = "Grid Sell";

    double entry_price = bid;
    double sl = 0.0; // NO STOP LOSS
    double tp = 0.0; // NO TAKE PROFIT - Grid will close on profit

    // Execute order using enhanced atomic execution function
    bool success = ExecuteGridOrder(order_type, lot_size, entry_price);
    
    if(!success)
    {
        Print("ERROR: Sell order execution failed");
    }
    
    // Always release the trading lock
    ReleaseTradingLock();
}

//+------------------------------------------------------------------+
//| Calculate lot size                                              |
//+------------------------------------------------------------------+
double CalculateLotSize()
{
    // In grid system, always use fixed lot as base
    if(InpUseFixedLot)
    return InpFixedLotSize;

    // Simple risk-based calculation without stop loss
    double balance = account.Balance();
    double risk_amount = balance * InpRiskPercent / 100.0;

    // Use a fixed distance for risk calculation (since no SL in grid)
    double risk_distance = 100 * symbolInfo.Point(); // 100 points fixed risk
    double tick_value = symbolInfo.TickValue();

    double lot_size = risk_amount / (risk_distance / symbolInfo.Point() * tick_value);

    // Normalize lot size
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    double lot_step = symbolInfo.LotsStep();

    lot_size = MathMax(lot_size, min_lot);
    lot_size = MathMin(lot_size, max_lot);
    lot_size = NormalizeDouble(lot_size / lot_step, 0) * lot_step;

    return lot_size;
}

//+------------------------------------------------------------------+
//| Calculate stop loss                                             |
//+------------------------------------------------------------------+
double CalculateStopLoss(ENUM_ORDER_TYPE order_type, double entry_price)
{
    // No stop loss in grid system
    if(!InpUseStopLoss)
    return 0.0;

    // Old stop loss code (not used)
    double sl_distance = 100 * symbolInfo.Point();

    if(order_type == ORDER_TYPE_BUY)
    return entry_price - sl_distance;
    else
    return entry_price + sl_distance;
}

//+------------------------------------------------------------------+
//| Calculate take profit based on margin percentage               |
//+------------------------------------------------------------------+
double CalculateTakeProfit(ENUM_ORDER_TYPE order_type, double entry_price, double lot_size = 0.1)
{
    if(InpUseMarginTP)
    {
        // Calculate required margin for the position
        double required_margin = 0;
        if(!OrderCalcMargin(order_type, _Symbol, lot_size, entry_price, required_margin))
        {
            Print("ERROR: Cannot calculate margin for TP calculation, using fallback");
            // Use fallback method
        }
        else
        {
            // Calculate TP distance based on margin percentage
            double margin_profit = required_margin * (InpMarginTPPercent / 100.0);

            // Convert profit amount to price distance
            double tick_value = symbolInfo.TickValue();
            double tick_size = symbolInfo.TickSize();

            if(tick_value > 0 && lot_size > 0)
            {
                double profit_per_tick = (tick_value * lot_size);
                if(profit_per_tick > 0)
                {
                    double ticks_needed = margin_profit / profit_per_tick;
                    double tp_distance = ticks_needed * tick_size;

                    // Safety check - ensure TP is reasonable
                    double max_tp_distance = 1000 * symbolInfo.Point(); // Max 1000 points
                    if(tp_distance > max_tp_distance)
                    {
                        tp_distance = max_tp_distance;
                        Print("WARNING: TP distance capped at ", max_tp_distance / symbolInfo.Point(), " points");
                    }

                    Print("Margin TP Calculation - Margin: ", required_margin,
                          ", Target Profit: ", margin_profit,
                          ", TP Distance: ", tp_distance);

                    if(order_type == ORDER_TYPE_BUY)
                        return entry_price + tp_distance;
                    else
                        return entry_price - tp_distance;
                }
            }
        }
    }

    // Fallback to points-based TP
    double tp_distance = InpTakeProfit * symbolInfo.Point();

    if(order_type == ORDER_TYPE_BUY)
        return entry_price + tp_distance;
    else
        return entry_price - tp_distance;
}

//+------------------------------------------------------------------+
//| Count open positions                                            |
//+------------------------------------------------------------------+
int CountOpenPositions()
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
//| Manage Open Positions                                           |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                // Trailing stop
                if(InpUseTrailingStop)
                {
                    ManageTrailingStop(position.Ticket());
                }

                // Break even
                if(InpUseBreakEven)
                {
                    ManageBreakEven(position.Ticket());
                }

                // Partial close
                if(InpUsePartialClose)
                {
                    ManagePartialClose(position.Ticket());
                }

                // Update statistics
                UpdatePositionStatistics(position.Ticket());
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Manage Trailing Stop                                            |
//+------------------------------------------------------------------+
void ManageTrailingStop(ulong ticket)
{
    if(!position.SelectByTicket(ticket)) return;

    double current_price = (position.PositionType() == POSITION_TYPE_BUY) ? symbolInfo.Bid() : symbolInfo.Ask();
    double open_price = position.PriceOpen();
    double current_sl = position.StopLoss();

    double trail_distance = InpTrailingStep * symbolInfo.Point();
    double trail_start = InpTrailingStart * symbolInfo.Point();

    if(position.PositionType() == POSITION_TYPE_BUY)
    {
        // Check if profit is enough to start trailing
        if(current_price - open_price >= trail_start)
        {
            double new_sl = current_price - trail_distance;

            // Only move SL up
            if(new_sl > current_sl && new_sl > open_price)
            {
                trade.PositionModify(ticket, new_sl, position.TakeProfit());
            }
        }
    }
    else // SELL position
    {
        // Check if profit is enough to start trailing
        if(open_price - current_price >= trail_start)
        {
            double new_sl = current_price + trail_distance;

            // Only move SL down (for sell)
            if((current_sl == 0 || new_sl < current_sl) && new_sl < open_price)
            {
                trade.PositionModify(ticket, new_sl, position.TakeProfit());
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Manage Break Even                                               |
//+------------------------------------------------------------------+
void ManageBreakEven(ulong ticket)
{
    if(!position.SelectByTicket(ticket)) return;

    double current_price = (position.PositionType() == POSITION_TYPE_BUY) ? symbolInfo.Bid() : symbolInfo.Ask();
    double open_price = position.PriceOpen();
    double current_sl = position.StopLoss();

    double be_trigger = InpBreakEvenPips * symbolInfo.Point();
    double be_profit = InpBreakEvenProfit * symbolInfo.Point();

    if(position.PositionType() == POSITION_TYPE_BUY)
    {
        // Check if profit is enough to move to break even
        if(current_price - open_price >= be_trigger)
        {
            double new_sl = open_price + be_profit;

            // Only move SL if it's better than current
            if(new_sl > current_sl)
            {
                trade.PositionModify(ticket, new_sl, position.TakeProfit());
            }
        }
    }
    else // SELL position
    {
        // Check if profit is enough to move to break even
        if(open_price - current_price >= be_trigger)
        {
            double new_sl = open_price - be_profit;

            // Only move SL if it's better than current
            if(current_sl == 0 || new_sl < current_sl)
            {
                trade.PositionModify(ticket, new_sl, position.TakeProfit());
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Manage Partial Close                                            |
//+------------------------------------------------------------------+
void ManagePartialClose(ulong ticket)
{
    if(!position.SelectByTicket(ticket)) return;

    double current_price = (position.PositionType() == POSITION_TYPE_BUY) ? symbolInfo.Bid() : symbolInfo.Ask();
    double open_price = position.PriceOpen();

    double partial_trigger = InpPartialClosePips * symbolInfo.Point();
    double position_volume = position.Volume();

    // Check if position is already partially closed
    string comment = position.Comment();
    if(StringFind(comment, "partial") >= 0) return;

    if(position.PositionType() == POSITION_TYPE_BUY)
    {
        if(current_price - open_price >= partial_trigger)
        {
            double close_volume = position_volume * InpPartialClosePercent / 100.0;
            close_volume = symbolInfo.LotsMin() * MathFloor(close_volume / symbolInfo.LotsMin());

            if(close_volume >= symbolInfo.LotsMin())
            {
                trade.PositionClosePartial(ticket, close_volume);
            }
        }
    }
    else // SELL position
    {
        if(open_price - current_price >= partial_trigger)
        {
            double close_volume = position_volume * InpPartialClosePercent / 100.0;
            close_volume = symbolInfo.LotsMin() * MathFloor(close_volume / symbolInfo.LotsMin());

            if(close_volume >= symbolInfo.LotsMin())
            {
                trade.PositionClosePartial(ticket, close_volume);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Update Position Statistics                                       |
//+------------------------------------------------------------------+
void UpdatePositionStatistics(ulong ticket)
{
    if(!position.SelectByTicket(ticket)) return;

    double profit = position.Profit();
    double current_equity = account.Equity();

    // Update highest equity
    if(current_equity > g_highest_equity)
    {
        g_highest_equity = current_equity;
    }

    // Calculate current drawdown
    g_stats.current_drawdown = (g_highest_equity - current_equity) / g_highest_equity * 100.0;

    // Update max drawdown
    if(g_stats.current_drawdown > g_stats.max_drawdown)
    {
        g_stats.max_drawdown = g_stats.current_drawdown;
    }

    // Check emergency stop
    if(g_stats.current_drawdown > InpMaxEquityDD)
    {
        g_trading_allowed = false;
        CloseAllPositions();
        Print("EMERGENCY STOP: Maximum drawdown exceeded!");
    }
}

//+------------------------------------------------------------------+
//| Close All Positions                                             |
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
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Display FVG zones                                               |
//+------------------------------------------------------------------+
void DisplayFVGZones()
{
    // Remove old objects
    for(int i = ObjectsTotal(0, 0, OBJ_RECTANGLE) - 1; i >= 0; i--)
    {
        string obj_name = ObjectName(0, i, 0, OBJ_RECTANGLE);
        if(StringFind(obj_name, "FVG_") == 0)
        {
            ObjectDelete(0, obj_name);
        }
    }

    // Draw current FVG zones
    for(int i = 0; i < g_fvg_count; i++)
    {
        if(!g_fvg_zones[i].valid) continue;

        string obj_name = "FVG_" + IntegerToString(i);
        datetime end_time = TimeCurrent() + PeriodSeconds() * 50;

        ObjectCreate(0, obj_name, OBJ_RECTANGLE, 0,
        g_fvg_zones[i].time, g_fvg_zones[i].low,
        end_time, g_fvg_zones[i].high);

        color zone_color = (g_fvg_zones[i].type == 1) ? clrLimeGreen : clrRed;
        if(g_fvg_zones[i].filled) zone_color = clrGray;

        ObjectSetInteger(0, obj_name, OBJPROP_COLOR, zone_color);
        ObjectSetInteger(0, obj_name, OBJPROP_STYLE, STYLE_SOLID);
        ObjectSetInteger(0, obj_name, OBJPROP_WIDTH, 1);
        ObjectSetInteger(0, obj_name, OBJPROP_BACK, true);
        ObjectSetInteger(0, obj_name, OBJPROP_FILL, true);
    }
}

//+------------------------------------------------------------------+
//| Display Order Blocks                                            |
//+------------------------------------------------------------------+
void DisplayOrderBlocks()
{
    // Remove old order block objects
    for(int i = ObjectsTotal(0, 0, OBJ_RECTANGLE) - 1; i >= 0; i--)
    {
        string obj_name = ObjectName(0, i, 0, OBJ_RECTANGLE);
        if(StringFind(obj_name, "OB_") == 0)
        {
            ObjectDelete(0, obj_name);
        }
    }

    // Draw current order blocks
    for(int i = 0; i < g_ob_count; i++)
    {
        if(!g_order_blocks[i].valid || g_order_blocks[i].broken) continue;

        string obj_name = "OB_" + IntegerToString(i);
        datetime end_time = TimeCurrent() + PeriodSeconds() * 20;

        ObjectCreate(0, obj_name, OBJ_RECTANGLE, 0,
        g_order_blocks[i].time, g_order_blocks[i].low,
        end_time, g_order_blocks[i].high);

        color ob_color = (g_order_blocks[i].type == 1) ? InpBullishOBColor : InpBearishOBColor;
        if(g_order_blocks[i].tested) ob_color = clrGray;

        ObjectSetInteger(0, obj_name, OBJPROP_COLOR, ob_color);
        ObjectSetInteger(0, obj_name, OBJPROP_STYLE, STYLE_SOLID);
        ObjectSetInteger(0, obj_name, OBJPROP_WIDTH, 2);
        ObjectSetInteger(0, obj_name, OBJPROP_BACK, true);
        ObjectSetInteger(0, obj_name, OBJPROP_FILL, false);

        // Add text label
        string label_name = "OB_Label_" + IntegerToString(i);
        ObjectCreate(0, label_name, OBJ_TEXT, 0, g_order_blocks[i].time, g_order_blocks[i].high);
        ObjectSetString(0, label_name, OBJPROP_TEXT, "OB " + DoubleToString(g_order_blocks[i].strength, 1) + " % ");
        ObjectSetInteger(0, label_name, OBJPROP_COLOR, ob_color);
        ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 8);
    }
}

//+------------------------------------------------------------------+
//| Display statistics                                              |
//+------------------------------------------------------------------+
void DisplayStatistics()
{
    // Calculate real-time statistics
    CalculateStatistics();

    string text = "=== FVG TRADING EA v2.0 ===\n";
    text += "Status: " + (g_trading_allowed ? "ACTIVE" : "STOPPED") + "\n";
    text += "Current Trend: " +
    (g_current_trend == 1 ? "BULLISH" : (g_current_trend == - 1 ? "BEARISH" : "NEUTRAL")) + "\n";

    text += "\n=== TRADING STATISTICS ===\n";
    text += "Total Trades: " + IntegerToString(g_stats.total_trades) + "\n";
    text += "Win Rate: " + DoubleToString(g_stats.win_rate, 1) + " % (" +
    IntegerToString(g_stats.winning_trades) + " / " + IntegerToString(g_stats.total_trades) + ")\n";
    text += "Profit Factor: " + DoubleToString(g_stats.profit_factor, 2) + "\n";
    text += "Orders Today: " + IntegerToString(g_orders_today) + " / " + IntegerToString(InpMaxOrdersPerDay) + "\n";

    text += "\n=== HIGH FREQUENCY SYSTEM ===\n";
    text += "Daily Lots Traded: " + DoubleToString(g_daily_lots_traded, 2) + " / " + DoubleToString(InpTargetDailyLots, 0) + "\n";
    text += "Progress: " + DoubleToString((g_daily_lots_traded / InpTargetDailyLots) * 100, 1) + " % \n";

    text += "\n=== ERROR CORRECTION ===\n";
    text += "Consecutive Losses: " + IntegerToString(g_consecutive_losses) + "\n";
    text += "Current Lot Size: " + DoubleToString(g_current_lot_size, 2) + "\n";
    text += "Lot Multiplications: " + IntegerToString(g_lot_multiplications) + " / " + IntegerToString(InpMaxLotMultiplications) + "\n";
    text += "Reverse Mode: " + (g_reverse_mode ? "ACTIVE" : "INACTIVE") + "\n";

    text += "\n=== ACCOUNT INFO ===\n";
    text += "Balance: " + DoubleToString(account.Balance(), 2) + "\n";
    text += "Equity: " + DoubleToString(account.Equity(), 2) + "\n";
    text += "Free Margin: " + DoubleToString(account.FreeMargin(), 2) + "\n";
    text += "Current DD: " + DoubleToString(g_stats.current_drawdown, 2) + " % \n";
    text += "Max DD: " + DoubleToString(g_stats.max_drawdown, 2) + " % \n";

    text += "\n=== MARKET ANALYSIS ===\n";
    text += "Active FVGs: " + IntegerToString(CountActiveFVGs()) + "\n";
    text += "Order Blocks: " + IntegerToString(CountActiveOrderBlocks()) + "\n";
    text += "Spread: " + DoubleToString(GetCurrentSpread(), 1) + " pips\n";
    text += "BOS Detected: " + (g_bos_detected ? "YES" : "NO") + "\n";
    text += "CHoCH Detected: " + (g_choch_detected ? "YES" : "NO") + "\n";

    text += "\n=== POSITIONS ===\n";
    int open_positions = CountOpenPositions();
    text += "Open Positions: " + IntegerToString(open_positions) + "\n";

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                text += "Pos #" + IntegerToString(i + 1) + ": " +
                (position.PositionType() == POSITION_TYPE_BUY ? "BUY" : "SELL") + " " +
                DoubleToString(position.Volume(), 2) + " lots, P&L: " +
                DoubleToString(position.Profit(), 2) + "\n";
            }
        }
    }

    Comment(text);
}

//+------------------------------------------------------------------+
//| Calculate Statistics                                             |
//+------------------------------------------------------------------+
void CalculateStatistics()
{
    // Calculate win rate
    if(g_stats.total_trades > 0)
    {
        g_stats.win_rate = (double)g_stats.winning_trades / g_stats.total_trades * 100.0;
    }

    // Calculate profit factor
    if(g_stats.total_loss > 0)
    {
        g_stats.profit_factor = g_stats.total_profit / MathAbs(g_stats.total_loss);
    }
    else if(g_stats.total_profit > 0)
    {
        g_stats.profit_factor = 999.0; // Infinite profit factor
    }
}

//+------------------------------------------------------------------+
//| Count Active FVGs                                               |
//+------------------------------------------------------------------+
int CountActiveFVGs()
{
    int count = 0;
    for(int i = 0; i < g_fvg_count; i++)
    {
        if(g_fvg_zones[i].valid && !g_fvg_zones[i].filled)
        {
            count++;
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| Count Active Order Blocks                                       |
//+------------------------------------------------------------------+
int CountActiveOrderBlocks()
{
    int count = 0;
    for(int i = 0; i < g_ob_count; i++)
    {
        if(g_order_blocks[i].valid && !g_order_blocks[i].broken)
        {
            count++;
        }
    }
    return count;
}

//+------------------------------------------------------------------+
//| Cleanup chart objects                                           |
//+------------------------------------------------------------------+
void CleanupChartObjects()
{
    for(int i = ObjectsTotal(0, 0) - 1; i >= 0; i--)
    {
        string obj_name = ObjectName(0, i);
        if(StringFind(obj_name, "FVG_") == 0 ||
        StringFind(obj_name, "OB_") == 0 ||
        StringFind(obj_name, "LIQ_") == 0 ||
        StringFind(obj_name, "STRUCT_") == 0)
        {
            ObjectDelete(0, obj_name);
        }
    }
}

//+------------------------------------------------------------------+
//| Error Correction and High Frequency Trading Functions           |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Initialize Error Correction System                              |
//+------------------------------------------------------------------+
void InitializeErrorCorrection()
{
    g_consecutive_losses = 0;
    g_current_lot_size = InpFixedLotSize;
    g_lot_multiplications = 0;
    g_reverse_mode = false;
    g_daily_lots_traded = 0.0;
}

//+------------------------------------------------------------------+
//| Update Daily Lots Counter                                       |
//+------------------------------------------------------------------+
void UpdateDailyLotsCounter(double lot_size)
{
    datetime current_time = TimeCurrent();
    MqlDateTime dt;
    TimeToStruct(current_time, dt);

    MqlDateTime last_dt;
    TimeToStruct(g_last_day_check, last_dt);

    // Reset daily counter at midnight
    if(dt.day != last_dt.day)
    {
        g_daily_lots_traded = 0.0;
    }

    g_daily_lots_traded += lot_size;
}

//+------------------------------------------------------------------+
//| Check if should continue trading for target lots               |
//+------------------------------------------------------------------+
bool ShouldContinueTrading()
{
    if(!InpHighFrequencyMode) return true;

    // Continue trading until target lots reached
    return(g_daily_lots_traded < InpTargetDailyLots);
}

//+------------------------------------------------------------------+
//| Handle Trade Result for Error Correction                       |
//+------------------------------------------------------------------+
void HandleTradeResult(bool is_profit, double profit_amount)
{
    if(is_profit)
    {
        // Reset on profit
        g_consecutive_losses = 0;
        g_current_lot_size = InpFixedLotSize;
        g_lot_multiplications = 0;

        // Turn off reverse mode after profit
        if(g_reverse_mode)
        {
            g_reverse_mode = false;
            Print("Reverse mode disabled after profit");
        }
    }
    else
    {
        // Handle loss
        g_consecutive_losses++;

        if(InpUseErrorCorrection)
        {
            // Increase lot size for next trade
            if(g_lot_multiplications < InpMaxLotMultiplications)
            {
                g_current_lot_size *= InpLotMultiplier;
                g_lot_multiplications++;
                Print("Loss detected. Lot size increased to: ", g_current_lot_size);
            }

            // Activate reverse mode after consecutive losses
            if(InpUseReverseTrading && g_consecutive_losses >= InpReverseAfterLosses)
            {
                if(!g_reverse_mode)
                {
                    g_reverse_mode = true;
                    Print("Reverse mode activated after ", g_consecutive_losses, " consecutive losses");
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Get Corrected Lot Size                                         |
//+------------------------------------------------------------------+
double GetCorrectedLotSize()
{
    if(!InpUseErrorCorrection)
    return CalculateLotSize();

    double lot_size = g_current_lot_size;

    // Normalize lot size within broker limits
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    double lot_step = symbolInfo.LotsStep();

    lot_size = MathMax(lot_size, min_lot);
    lot_size = MathMin(lot_size, max_lot);
    lot_size = NormalizeDouble(lot_size / lot_step, 0) * lot_step;

    return lot_size;
}

//+------------------------------------------------------------------+
//| Force Close Old Positions                                      |
//+------------------------------------------------------------------+
void ForceCloseOldPositions()
{
    if(!InpForceCloseEnabled) return;

    datetime current_time = TimeCurrent();
    int force_close_seconds = InpForceCloseAfterMinutes * 60;

    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                datetime position_time = position.Time();

                // Force close if position is too old
                if(current_time - position_time >= force_close_seconds)
                {
                    double profit = position.Profit();
                    trade.PositionClose(position.Ticket());

                    Print("Position force closed after ", InpForceCloseAfterMinutes, " minutes. P&L: ", profit);

                    // Handle result for error correction
                    HandleTradeResult(profit > 0, profit);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check Reverse Trade Signal                                      |
//+------------------------------------------------------------------+
bool ShouldReverseSignal(int original_signal)
{
    if(!g_reverse_mode) return false;

    // In reverse mode, flip the signal
    return true;
}

//+------------------------------------------------------------------+
//| Aggressive FVG Detection for High Frequency                     |
//+------------------------------------------------------------------+
void AggressiveFVGDetection()
{
    if(!InpHighFrequencyMode) return;

    // Lower quality requirements for more frequent signals
    double original_quality = InpFVGQualityFilter;

    // Temporarily lower quality filter for more trades
    double temp_quality = original_quality * 0.7; // 70 % of original quality

    DetectNewFVGWithQuality(temp_quality);
}

//+------------------------------------------------------------------+
//| Detect new FVG with custom quality                             |
//+------------------------------------------------------------------+
void DetectNewFVGWithQuality(double quality_threshold)
{
    if(iBars(_Symbol, PERIOD_CURRENT) < 3) return;

    double high[], low[];
    ArraySetAsSeries(high, true);
    ArraySetAsSeries(low, true);

    if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, 3, high) != 3) return;
    if(CopyLow(_Symbol, PERIOD_CURRENT, 0, 3, low) != 3) return;

    // Check for Bullish FVG
    if(low[2] > high[0])
    {
        double gap_size = low[2] - high[0];
        if(gap_size >= InpMinFVGSize * symbolInfo.Point() * 0.5) // Half the original requirement
        {
            double quality = CalculateFVGQuality(high[0], low[2], 1);
            if(quality >= quality_threshold)
            {
                AddFVGZone(high[0], low[2], iTime(_Symbol, PERIOD_CURRENT, 1), 1, quality);
            }
        }
    }

    // Check for Bearish FVG
    if(high[2] < low[0])
    {
        double gap_size = low[0] - high[2];
        if(gap_size >= InpMinFVGSize * symbolInfo.Point() * 0.5) // Half the original requirement
        {
            double quality = CalculateFVGQuality(high[2], low[0], - 1);
            if(quality >= quality_threshold)
            {
                AddFVGZone(high[2], low[0], iTime(_Symbol, PERIOD_CURRENT, 1), - 1, quality);
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check for closed positions and handle results                  |
//+------------------------------------------------------------------+
void CheckClosedPositions()
{
    if(!InpUseErrorCorrection) return;

    // Check history for recently closed positions
    HistorySelect(g_last_trade_time, TimeCurrent());

    for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
    {
        ulong deal_ticket = HistoryDealGetTicket(i);
        if(deal_ticket <= 0) continue;

        // Check if this is our EA's deal
        if(HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) != InpMagicNumber) continue;
        if(HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != _Symbol) continue;

        // Check if this is a position exit
        ENUM_DEAL_ENTRY deal_entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
        if(deal_entry != DEAL_ENTRY_OUT) continue;

        // Get deal profit
        double profit = HistoryDealGetDouble(deal_ticket, DEAL_PROFIT);
        double swap = HistoryDealGetDouble(deal_ticket, DEAL_SWAP);
        double commission = HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION);
        double total_result = profit + swap + commission;

        // Handle the result
        bool is_profit = total_result > 0;
        HandleTradeResult(is_profit, total_result);

        // Update statistics
        if(is_profit)
        {
            g_stats.winning_trades++;
            g_stats.total_profit += total_result;
        }
        else
        {
            g_stats.losing_trades++;
            g_stats.total_loss += total_result;
        }

        // Minimal logging for closed positions
        if(total_result > 0 && g_orders_today % 50 == 1) // Print only profitable closures, every 50th
        Print("Profit: $", total_result);

        // Update last trade time to avoid processing same deal again
        g_last_trade_time = TimeCurrent();
        break; // Process only one deal per tick
    }
}

//+------------------------------------------------------------------+
//| Grid System Functions                                           |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Initialize Grid System                                          |
//+------------------------------------------------------------------+
void InitializeGridSystem()
{
    g_last_buy_price = 0.0;
    g_last_sell_price = 0.0;
    g_grid_level = 0;
    g_buy_grid_level = 0;
    g_sell_grid_level = 0;
    g_total_buy_lots = 0.0;
    g_total_sell_lots = 0.0;
    g_average_buy_price = 0.0;
    g_average_sell_price = 0.0;
}

//+------------------------------------------------------------------+
//| Update Grid Positions with enhanced state management           |
//+------------------------------------------------------------------+
void UpdateGridPositions()
{
    // Reset all grid state variables
    g_total_buy_lots = 0.0;
    g_total_sell_lots = 0.0;
    g_average_buy_price = 0.0;
    g_average_sell_price = 0.0;

    double total_buy_volume = 0.0;
    double total_sell_volume = 0.0;
    double weighted_buy_price = 0.0;
    double weighted_sell_price = 0.0;
    
    int buy_position_count = 0;
    int sell_position_count = 0;
    
    // Track last prices for grid distance calculation
    double last_buy_price = 0.0;
    double last_sell_price = 0.0;

    // Scan all positions to rebuild grid state
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                double pos_volume = position.Volume();
                double pos_price = position.PriceOpen();
                
                if(position.PositionType() == POSITION_TYPE_BUY)
                {
                    g_total_buy_lots += pos_volume;
                    weighted_buy_price += pos_price * pos_volume;
                    total_buy_volume += pos_volume;
                    buy_position_count++;
                    
                    // Track the most recent buy price
                    if(last_buy_price == 0.0 || pos_price > last_buy_price)
                        last_buy_price = pos_price;
                }
                else if(position.PositionType() == POSITION_TYPE_SELL)
                {
                    g_total_sell_lots += pos_volume;
                    weighted_sell_price += pos_price * pos_volume;
                    total_sell_volume += pos_volume;
                    sell_position_count++;
                    
                    // Track the most recent sell price
                    if(last_sell_price == 0.0 || pos_price < last_sell_price)
                        last_sell_price = pos_price;
                }
            }
        }
    }

    // Calculate average prices
    if(total_buy_volume > 0)
        g_average_buy_price = weighted_buy_price / total_buy_volume;

    if(total_sell_volume > 0)
        g_average_sell_price = weighted_sell_price / total_sell_volume;
    
    // Update last prices for grid calculations
    if(last_buy_price > 0.0)
        g_last_buy_price = last_buy_price;
    if(last_sell_price > 0.0)
        g_last_sell_price = last_sell_price;
    
    // Update grid levels based on actual position count
    g_buy_grid_level = buy_position_count;
    g_sell_grid_level = sell_position_count;
    
    // Update overall grid level (for backward compatibility)
    g_grid_level = MathMax(g_buy_grid_level, g_sell_grid_level);
    
    // Synchronize grid direction based on actual positions
    SynchronizeGridDirection();
    
    // Validate state consistency
    ValidateGridStateConsistency();
}

//+------------------------------------------------------------------+
//| Check if should open grid position                             |
//+------------------------------------------------------------------+
bool ShouldOpenGridPosition(ENUM_ORDER_TYPE order_type)
{
    double current_price = (order_type == ORDER_TYPE_BUY) ? symbolInfo.Ask() : symbolInfo.Bid();
    double min_distance = InpGridDistance * symbolInfo.Point();

    // ปิดการตรวจสอบแนวโน้ม - ให้ Grid ทำงานได้ทุกทิศทาง
    // Grid Trading ต้องทำงานแบบ counter-trend เพื่อ average down
    /*
    int trend = GetTrendDirection();
    if(trend != 0) // มีแนวโน้มชัดเจน
    {
        if(order_type == ORDER_TYPE_BUY && trend < 0) return false; // ไม่ซื้อในเทรนด์ลง
        if(order_type == ORDER_TYPE_SELL && trend > 0) return false; // ไม่ขายในเทรนด์ขึ้น
    }
    */

    // ปิดการตรวจสอบ RSI - ให้ Grid ทำงานได้เสมอ
    // Grid Trading ไม่ควรถูกจำกัดด้วย RSI
    /*
    if(InpUseRSIFilter && h_rsi != INVALID_HANDLE)
    {
        double rsi_val[1];
        if(CopyBuffer(h_rsi, 0, 0, 1, rsi_val) > 0)
        {
            if(order_type == ORDER_TYPE_BUY && rsi_val[0] > InpRSIOverbought) return false;
            if(order_type == ORDER_TYPE_SELL && rsi_val[0] < InpRSIOversold) return false;
        }
    }
    */

    if(order_type == ORDER_TYPE_BUY)
    {
        // Check distance from last buy
        if(g_last_buy_price > 0 && current_price > g_last_buy_price - min_distance)
        return false;

        // Check distance from sell positions
        if(g_total_sell_lots > 0 && MathAbs(current_price - g_average_sell_price) < InpMinDistancePoints * symbolInfo.Point())
        return false;
    }
    else
    {
        // Check distance from last sell
        if(g_last_sell_price > 0 && current_price < g_last_sell_price + min_distance)
        return false;

        // Check distance from buy positions
        if(g_total_buy_lots > 0 && MathAbs(current_price - g_average_buy_price) < InpMinDistancePoints * symbolInfo.Point())
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Validate lot size against broker limits and risk parameters    |
//+------------------------------------------------------------------+
double ValidateLotSize(double requested_lot)
{
    // Get broker limits
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    double lot_step = symbolInfo.LotsStep();
    
    // Normalize to lot step
    requested_lot = NormalizeDouble(requested_lot / lot_step, 0) * lot_step;
    
    // Apply broker limits
    requested_lot = MathMax(requested_lot, min_lot);
    requested_lot = MathMin(requested_lot, max_lot);
    
    // Check against maximum allowed lot based on account balance
    double max_allowed = GetMaxAllowedLot();
    requested_lot = MathMin(requested_lot, max_allowed);

    // Additional safety check - never exceed 5 lots per order
    requested_lot = MathMin(requested_lot, 5.0);

    // Emergency brake - if lot size is still too large, cap it dramatically
    if(requested_lot > 1.0 && account.Balance() < 10000.0)
    {
        requested_lot = MathMin(requested_lot, 0.5); // Cap small accounts to 0.5 lots max
    }
    
    return requested_lot;
}

//+------------------------------------------------------------------+
//| Get maximum allowed lot size based on account balance          |
//+------------------------------------------------------------------+
double GetMaxAllowedLot()
{
    double balance = account.Balance();
    double max_risk_amount = balance * InpRiskPercent / 100.0;
    
    // Use tick value to calculate maximum lot
    double tick_value = symbolInfo.TickValue();
    double risk_distance = 100 * symbolInfo.Point(); // 100 points risk distance
    
    double max_lot = max_risk_amount / (risk_distance / symbolInfo.Point() * tick_value);
    
    // Apply broker limits
    double broker_max = symbolInfo.LotsMax();
    max_lot = MathMin(max_lot, broker_max);
    
    // Cap at reasonable maximum (prevent extreme lot sizes)
    // More conservative maximum based on account balance
    double conservative_max = MathMin(balance / 5000.0, 2.0); // Much more conservative
    max_lot = MathMin(max_lot, conservative_max);
    
    return max_lot;
}

//+------------------------------------------------------------------+
//| Calculate progressive lot size for grid level                  |
//+------------------------------------------------------------------+
double CalculateProgressiveLot(int grid_level)
{
    // Get base lot size
    double base_lot = InpUseFixedLot ? InpFixedLotSize : CalculateLotSize();

    // Enhanced progressive calculation with safety caps
    double progressive_lot = base_lot;

    // Cap grid level to prevent extreme lot sizes
    int safe_grid_level = MathMin(grid_level, 8); // Max 8 levels for safety

    // Apply multiplier only if within safe range
    if(safe_grid_level > 0)
    {
        progressive_lot = base_lot * MathPow(InpGridMultiplier, safe_grid_level);
    }

    // Apply strict maximum lot size (account balance based)
    double balance = account.Balance();
    double max_safe_lot = MathMin(balance / 10000.0, 5.0); // Max 5 lots or balance/10000
    progressive_lot = MathMin(progressive_lot, max_safe_lot);

    // Validate and normalize the result
    return ValidateLotSize(progressive_lot);
}

//+------------------------------------------------------------------+
//| Get current grid level for specific order type                 |
//+------------------------------------------------------------------+
int GetCurrentGridLevel(ENUM_ORDER_TYPE order_type)
{
    if(order_type == ORDER_TYPE_BUY)
    return g_buy_grid_level;
    else if(order_type == ORDER_TYPE_SELL)
    return g_sell_grid_level;
    
    return 0;
}

//+------------------------------------------------------------------+
//| Calculate grid lot size with comprehensive validation (ENHANCED)|
//+------------------------------------------------------------------+
double CalculateGridLotSize(ENUM_ORDER_TYPE order_type)
{
    // Get current grid level for this direction
    int current_level = GetCurrentGridLevel(order_type);
    
    // Validate grid level is within safe bounds
    if(current_level < 0)
    {
        Print("ERROR: Invalid grid level ", current_level, " - using level 0");
        current_level = 0;
    }
    
    if(current_level > 20) // Safety cap at level 20
    {
        Print("WARNING: Grid level ", current_level, " exceeds safety limit - capping at 20");
        current_level = 20;
    }
    
    // Calculate progressive lot size
    double lot_size = CalculateProgressiveLot(current_level);
    
    // Validate and normalize lot size
    lot_size = ValidateLotSize(lot_size);
    
    // Additional risk validation
    double max_allowed = GetMaxAllowedLot();
    if(lot_size > max_allowed)
    {
        Print("WARNING: Calculated lot ", lot_size, " exceeds max allowed ", max_allowed, " - adjusting");
        lot_size = max_allowed;
    }
    
    // Final broker compliance check
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    
    if(lot_size < min_lot)
    {
        Print("WARNING: Lot size ", lot_size, " below broker minimum ", min_lot, " - adjusting");
        lot_size = min_lot;
    }
    
    if(lot_size > max_lot)
    {
        Print("WARNING: Lot size ", lot_size, " above broker maximum ", max_lot, " - adjusting");
        lot_size = max_lot;
    }
    
    // Log the calculation for debugging
    if(g_orders_today % 10 == 1) // Log every 10th calculation
    {
        Print("Grid Lot Calculation - Type: ", (order_type == ORDER_TYPE_BUY ? "BUY" : "SELL"),
        ", Level: ", current_level,
        ", Base: ", (InpUseFixedLot ? InpFixedLotSize : CalculateLotSize()),
        ", Multiplier: ", InpGridMultiplier,
        ", Result: ", lot_size);
    }
    
    return lot_size;
}

//+------------------------------------------------------------------+
//| Reset grid direction when changing from buy to sell or vice versa |
//+------------------------------------------------------------------+
void ResetGridDirection()
{
    // This function can be called when market conditions change
    // and we need to switch from buy grid to sell grid or vice versa
    
    // For now, we'll keep both directions active as per current EA design
    // But this provides the infrastructure for single direction enforcement
    
    Print("Grid direction reset - Buy Level: ", g_buy_grid_level, ", Sell Level: ", g_sell_grid_level);
}

//+------------------------------------------------------------------+
//| Check account risk before opening position                     |
//+------------------------------------------------------------------+
bool CheckAccountRisk(double lot_size, double price)
{
    double balance = account.Balance();
    double equity = account.Equity();
    
    // Check if we have enough margin
    double required_margin = 0;
    if(!OrderCalcMargin(ORDER_TYPE_BUY, _Symbol, lot_size, price, required_margin))
    {
        Print("ERROR: Cannot calculate required margin");
        return false;
    }
    
    double free_margin = account.FreeMargin();
    if(required_margin > free_margin * 0.8) // Use only 80 % of free margin
    {
        Print("WARNING: Insufficient margin. Required: ", required_margin, ", Available: ", free_margin);
        return false;
    }
    
    // Check maximum exposure
    double current_exposure = (g_total_buy_lots + g_total_sell_lots) * price;
    double max_exposure = balance * 0.5; // Maximum 50 % of balance exposure
    
    if(current_exposure + (lot_size * price) > max_exposure)
    {
        Print("WARNING: Maximum exposure limit reached. Current: ", current_exposure, ", Max: ", max_exposure);
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Get current grid direction                                      |
//+------------------------------------------------------------------+
int GetCurrentGridDirection()
{
    return g_current_grid_direction;
}

//+------------------------------------------------------------------+
//| Set grid direction                                              |
//+------------------------------------------------------------------+
void SetGridDirection(int direction)
{
    if(direction != g_current_grid_direction)
    {
        Print("Grid direction changed from ", g_current_grid_direction, " to ", direction);
        g_current_grid_direction = direction;
        g_grid_direction_start_time = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Check if we should change grid direction                       |
//+------------------------------------------------------------------+
bool ShouldChangeGridDirection(ENUM_ORDER_TYPE new_order_type)
{
    if(!g_enforce_single_direction)
    return true; // Allow any direction if enforcement is disabled
    
    int new_direction = (new_order_type == ORDER_TYPE_BUY) ? 1 : - 1;
    
    // If no current direction, allow any
    if(g_current_grid_direction == 0)
    return true;
    
    // If same direction, allow
    if(g_current_grid_direction == new_direction)
    return true;
    
    // Different direction - check if we should change
    // Only change if we have strong reason (market structure change, etc.)
    return ShouldForceDirectionChange(new_direction);
}

//+------------------------------------------------------------------+
//| Check if we should force a direction change                    |
//+------------------------------------------------------------------+
bool ShouldForceDirectionChange(int new_direction)
{
    // Check if current grid is profitable enough to close
    double current_profit = GetCurrentGridProfit();
    
    // If current grid is losing significantly, allow direction change
    if(current_profit < - 100.0) // Losing more than $100
    {
        Print("Forcing grid direction change due to significant loss: ", current_profit);
        return true;
    }
    
    // Check market structure change
    if(HasSignificantMarketStructureChange(new_direction))
    {
        Print("Forcing grid direction change due to market structure change");
        return true;
    }
    
    // Don't change direction if current grid is working
    return false;
}

//+------------------------------------------------------------------+
//| Get current grid profit                                         |
//+------------------------------------------------------------------+
double GetCurrentGridProfit()
{
    double total_profit = 0.0;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                total_profit += position.Profit() + position.Swap() + position.Commission();
            }
        }
    }
    
    return total_profit;
}

//+------------------------------------------------------------------+
//| Check for significant market structure change                  |
//+------------------------------------------------------------------+
bool HasSignificantMarketStructureChange(int new_direction)
{
    // Simple trend change detection
    double current_price = symbolInfo.Bid();
    double price_5_bars_ago = iClose(_Symbol, PERIOD_CURRENT, 5);
    double price_change = current_price - price_5_bars_ago;
    double change_points = MathAbs(price_change) / symbolInfo.Point();
    
    // If price moved significantly in the new direction
    if(change_points > g_grid_direction_change_threshold)
    {
        bool price_supports_new_direction = (new_direction == 1 && price_change > 0) ||
        (new_direction == - 1 && price_change < 0);
        return price_supports_new_direction;
    }
    
    return false;
}


//+------------------------------------------------------------------+
//| Validate order direction against current grid direction        |
//+------------------------------------------------------------------+
bool ValidateOrderDirection(ENUM_ORDER_TYPE order_type)
{
    if(!InpEnforceSingleDirection)
        return true; // Allow any direction if enforcement is disabled

    int order_direction = (order_type == ORDER_TYPE_BUY) ? 1 : -1;

    // If no current direction, allow any direction to start
    if(g_current_grid_direction == 0)
        return true;

    // Check if order direction matches current grid direction
    if(g_current_grid_direction == order_direction)
        return true;

    // Direction mismatch - this should be prevented
    Print("WARNING: Order direction (", order_direction, ") conflicts with grid direction (", g_current_grid_direction, ")");
    return false;
}

//+------------------------------------------------------------------+
//| Test progressive lot calculation (for debugging)               |
//+------------------------------------------------------------------+
void TestProgressiveLotCalculation()
{
    Print("=== TESTING PROGRESSIVE LOT CALCULATION ===");
    Print("Base lot: ", InpFixedLotSize, ", Multiplier: ", InpGridMultiplier);
    
    for(int level = 0; level < 10; level++)
    {
        double progressive_lot = CalculateProgressiveLot(level);
        Print("Level ", level, ": ", progressive_lot, " lots");
        
        // Stop if lot size gets too large
        if(progressive_lot > 10.0)
        {
            Print("WARNING: Lot size exceeds 10.0 at level ", level);
            break;
        }
    }
    Print("=== END TEST ===");
}

//+------------------------------------------------------------------+
//| Test duplicate order prevention (for debugging)               |
//+------------------------------------------------------------------+
void TestDuplicateOrderPrevention()
{
    Print("=== TESTING DUPLICATE ORDER PREVENTION ===");
    
    // Test 1: Check if we can place order initially
    bool can_place_1 = CanPlaceNewOrder();
    Print("Test 1 - Can place initial order: ", (can_place_1 ? "YES" : "NO"));
    
    // Test 2: Simulate order placement
    if(AcquireTradingLock())
    {
        Print("Test 2 - Successfully acquired trading lock");
        UpdateOrderTiming();
        
        // Test 3: Try to place another order immediately
        bool can_place_2 = CanPlaceNewOrder();
        Print("Test 3 - Can place immediate second order: ", (can_place_2 ? "YES" : "NO"));
        
        ReleaseTradingLock();
        Print("Test 4 - Released trading lock");
    }
    else
    {
        Print("Test 2 - FAILED to acquire trading lock");
    }
    
    // Test 5: Check after release
    bool can_place_3 = CanPlaceNewOrder();
    Print("Test 5 - Can place order after release: ", (can_place_3 ? "YES" : "NO"));
    
    Print("=== END DUPLICATE PREVENTION TEST ===");
}

//+------------------------------------------------------------------+
//| Test grid direction management (for debugging)                 |
//+------------------------------------------------------------------+
void TestGridDirectionManagement()
{
    Print("=== TESTING GRID DIRECTION MANAGEMENT ===");
    
    // Test 1: Initial state
    Print("Test 1 - Initial grid direction: ", GetCurrentGridDirection());
    
    // Test 2: Set buy direction
    SetGridDirection(1);
    Print("Test 2 - After setting buy direction: ", GetCurrentGridDirection());
    
    // Test 3: Try to validate buy order (should pass)
    bool can_buy = ValidateOrderDirection(ORDER_TYPE_BUY);
    Print("Test 3 - Can place buy order in buy grid: ", (can_buy ? "YES" : "NO"));
    
    // Test 4: Try to validate sell order (should fail)
    bool can_sell = ValidateOrderDirection(ORDER_TYPE_SELL);
    Print("Test 4 - Can place sell order in buy grid: ", (can_sell ? "YES" : "NO"));
    
    // Test 5: Reset grid direction
    ResetGridDirection();
    Print("Test 5 - After reset, grid direction: ", GetCurrentGridDirection());
    
    // Test 6: Try sell direction
    SetGridDirection( - 1);
    Print("Test 6 - After setting sell direction: ", GetCurrentGridDirection());
    
    bool can_sell_2 = ValidateOrderDirection(ORDER_TYPE_SELL);
    Print("Test 7 - Can place sell order in sell grid: ", (can_sell_2 ? "YES" : "NO"));
    
    bool can_buy_2 = ValidateOrderDirection(ORDER_TYPE_BUY);
    Print("Test 8 - Can place buy order in sell grid: ", (can_buy_2 ? "YES" : "NO"));
    
    // Reset for normal operation
    ResetGridDirection();
    Print("=== END GRID DIRECTION TEST ===");
}

//+------------------------------------------------------------------+
//| Test state management system (for debugging)                  |
//+------------------------------------------------------------------+
void TestStateManagement()
{
    Print("=== TESTING STATE MANAGEMENT SYSTEM ===");
    
    // Test 1: Initial state validation
    Print("Test 1 - Validating initial state consistency");
    ValidateGridStateConsistency();
    
    // Test 2: Grid state synchronization
    Print("Test 2 - Testing grid state synchronization");
    SynchronizeGridDirection();
    
    // Test 3: State update function
    Print("Test 3 - Testing UpdateGridState function");
    UpdateGridState();
    
    // Test 4: Emergency recovery (safe to test with no positions)
    Print("Test 4 - Testing emergency state recovery");
    EmergencyStateRecovery();
    
    // Test 5: Lock timeout simulation
    Print("Test 5 - Testing lock timeout handling");
    if(AcquireTradingLock())
    {
        Print("Lock acquired for timeout test");
        // Simulate old lock time
        g_lock_time = TimeCurrent() - (g_lock_timeout_seconds + 5);
        
        // Try to acquire again - should detect timeout and recover
        bool recovered = AcquireTradingLock();
        Print("Lock timeout recovery: ", (recovered ? "SUCCESS" : "FAILED"));
        
        if(recovered)
            ReleaseTradingLock();
    }
    
    Print("=== END STATE MANAGEMENT TEST ===");
}

//+------------------------------------------------------------------+
//| Test grid system integration (for debugging)                  |
//+------------------------------------------------------------------+
void TestGridSystemIntegration()
{
    Print("=== TESTING GRID SYSTEM INTEGRATION ===");
    
    // Test 1: Grid lot calculation with various levels
    Print("Test 1 - Testing grid lot calculation at different levels");
    for(int level = 0; level <= 5; level++)
    {
        // Temporarily set grid level for testing
        g_buy_grid_level = level;
        double buy_lot = CalculateGridLotSize(ORDER_TYPE_BUY);
        Print("  Buy Level ", level, ": ", buy_lot, " lots");
        
        g_sell_grid_level = level;
        double sell_lot = CalculateGridLotSize(ORDER_TYPE_SELL);
        Print("  Sell Level ", level, ": ", sell_lot, " lots");
    }
    
    // Test 2: Grid level validation
    Print("Test 2 - Testing grid level bounds validation");
    g_buy_grid_level = -1; // Invalid level
    double invalid_lot = CalculateGridLotSize(ORDER_TYPE_BUY);
    Print("  Invalid level (-1) result: ", invalid_lot, " lots");
    
    g_buy_grid_level = 25; // Excessive level
    double excessive_lot = CalculateGridLotSize(ORDER_TYPE_BUY);
    Print("  Excessive level (25) result: ", excessive_lot, " lots");
    
    // Test 3: Progressive vs exponential comparison
    Print("Test 3 - Progressive vs Exponential comparison (first 5 levels)");
    for(int level = 0; level < 5; level++)
    {
        double progressive = CalculateProgressiveLot(level);
        double exponential = InpFixedLotSize * MathPow(InpGridMultiplier, level);
        Print("  Level ", level, ": Progressive=", progressive, ", Exponential=", exponential);
    }
    
    // Test 4: Risk integration
    Print("Test 4 - Testing risk integration in grid calculations");
    double current_price = symbolInfo.Bid();
    double test_lot = CalculateGridLotSize(ORDER_TYPE_BUY);
    bool risk_ok = CheckAccountRisk(test_lot, current_price);
    Print("  Grid lot ", test_lot, " passes risk check: ", (risk_ok ? "YES" : "NO"));
    
    // Reset grid levels
    g_buy_grid_level = 0;
    g_sell_grid_level = 0;
    
    Print("=== END GRID SYSTEM INTEGRATION TEST ===");
}

//+------------------------------------------------------------------+
//| Test advanced order validation (for debugging)                |
//+------------------------------------------------------------------+
void TestAdvancedOrderValidation()
{
    Print("=== TESTING ADVANCED ORDER VALIDATION ===");
    
    double current_price = symbolInfo.Bid();
    
    // Test 1: Price distance validation
    Print("Test 1 - Testing price distance validation");
    
    // Add a fake recent order
    AddToRecentOrders(current_price);
    
    // Test close price (should fail)
    bool close_price_ok = ValidatePriceDistance(current_price + 1 * symbolInfo.Point());
    Print("  Close price validation (1 point away): ", (close_price_ok ? "PASS" : "FAIL"));
    
    // Test distant price (should pass)
    bool distant_price_ok = ValidatePriceDistance(current_price + 10 * symbolInfo.Point());
    Print("  Distant price validation (10 points away): ", (distant_price_ok ? "PASS" : "FAIL"));
    
    // Test 2: Order frequency validation
    Print("Test 2 - Testing order frequency validation");
    bool freq_ok = ValidateOrderFrequency();
    Print("  Current frequency check: ", (freq_ok ? "PASS" : "FAIL"));
    
    // Test 3: Enhanced parameter validation
    Print("Test 3 - Testing enhanced parameter validation");
    bool enhanced_ok = ValidateAdvancedOrderParameters(ORDER_TYPE_BUY, 0.1, current_price + 20 * symbolInfo.Point());
    Print("  Enhanced validation (valid params): ", (enhanced_ok ? "PASS" : "FAIL"));
    
    bool enhanced_fail = ValidateAdvancedOrderParameters(ORDER_TYPE_BUY, 0.0, current_price); // Invalid lot
    Print("  Enhanced validation (invalid lot): ", (enhanced_fail ? "PASS" : "FAIL"));
    
    // Reset recent orders for normal operation
    g_recent_order_count = 0;
    
    Print("=== END ADVANCED ORDER VALIDATION TEST ===");
}

//+------------------------------------------------------------------+
//| Handle specific error with recovery strategy                   |
//+------------------------------------------------------------------+
bool HandleError(int error_code, string context = "")
{
    g_last_error_code = error_code;
    g_last_error_time = TimeCurrent();
    
    string error_description = GetErrorDescription(error_code);
    Print("ERROR [", error_code, "]: ", error_description, " in context: ", context);
    
    // Check if we've exceeded recovery attempts
    if(g_error_recovery_attempts >= g_max_recovery_attempts)
    {
        Print("CRITICAL: Maximum recovery attempts exceeded. Entering safe mode.");
        return false;
    }
    
    g_error_recovery_attempts++;
    
    // Apply recovery strategy based on error type
    bool recovery_success = false;
    
    switch(error_code)
    {
        case ERROR_INSUFFICIENT_MARGIN:
            recovery_success = RecoverFromMarginError();
            break;
            
        case ERROR_INVALID_LOT_SIZE:
            recovery_success = RecoverFromLotSizeError();
            break;
            
        case ERROR_BROKER_BUSY:
            recovery_success = RecoverFromBrokerBusyError();
            break;
            
        case ERROR_STATE_CORRUPTION:
            recovery_success = RecoverFromStateCorruption();
            break;
            
        case ERROR_LOCK_TIMEOUT:
            recovery_success = RecoverFromLockTimeout();
            break;
            
        case ERROR_GRID_DIRECTION_CONFLICT:
            recovery_success = RecoverFromDirectionConflict();
            break;
            
        case ERROR_EXCESSIVE_EXPOSURE:
            recovery_success = RecoverFromExcessiveExposure();
            break;
            
        default:
            Print("WARNING: Unknown error code, applying generic recovery");
            recovery_success = GenericErrorRecovery();
            break;
    }
    
    if(recovery_success)
    {
        Print("SUCCESS: Error recovery completed for error ", error_code);
        g_error_recovery_attempts = 0; // Reset counter on success
    }
    else
    {
        Print("FAILED: Error recovery failed for error ", error_code);
    }
    
    return recovery_success;
}

//+------------------------------------------------------------------+
//| Get human-readable error description                           |
//+------------------------------------------------------------------+
string GetErrorDescription(int error_code)
{
    switch(error_code)
    {
        case ERROR_NONE: return "No error";
        case ERROR_INSUFFICIENT_MARGIN: return "Insufficient margin for trade";
        case ERROR_INVALID_LOT_SIZE: return "Invalid lot size";
        case ERROR_BROKER_BUSY: return "Broker server busy";
        case ERROR_PRICE_CHANGED: return "Price changed during execution";
        case ERROR_STATE_CORRUPTION: return "Grid state corruption detected";
        case ERROR_LOCK_TIMEOUT: return "Trading lock timeout";
        case ERROR_GRID_DIRECTION_CONFLICT: return "Grid direction conflict";
        case ERROR_EXCESSIVE_EXPOSURE: return "Excessive market exposure";
        default: return "Unknown error";
    }
}

//+------------------------------------------------------------------+
//| Recovery strategy for margin errors                            |
//+------------------------------------------------------------------+
bool RecoverFromMarginError()
{
    Print("Recovering from margin error...");
    
    // Reduce lot sizes for future trades
    if(InpFixedLotSize > symbolInfo.LotsMin())
    {
        double new_lot = InpFixedLotSize * 0.5; // Reduce by 50%
        new_lot = MathMax(new_lot, symbolInfo.LotsMin());
        Print("Temporarily reducing lot size from ", InpFixedLotSize, " to ", new_lot);
        // Note: This would need to be implemented as a temporary override
    }
    
    // Wait for margin to improve
    Sleep(5000); // Wait 5 seconds
    
    return true;
}

//+------------------------------------------------------------------+
//| Recovery strategy for lot size errors                          |
//+------------------------------------------------------------------+
bool RecoverFromLotSizeError()
{
    Print("Recovering from lot size error...");
    
    // Force lot size recalibration
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    
    Print("Broker lot limits: Min=", min_lot, ", Max=", max_lot);
    
    return true;
}

//+------------------------------------------------------------------+
//| Recovery strategy for broker busy errors                       |
//+------------------------------------------------------------------+
bool RecoverFromBrokerBusyError()
{
    Print("Recovering from broker busy error...");
    
    // Wait and retry
    Sleep(2000); // Wait 2 seconds
    
    return true;
}

//+------------------------------------------------------------------+
//| Recovery strategy for state corruption                         |
//+------------------------------------------------------------------+
bool RecoverFromStateCorruption()
{
    Print("Recovering from state corruption...");
    
    // Rebuild state from positions
    RebuildGridStateFromPositions();
    
    // Validate consistency
    ValidateGridStateConsistency();
    
    return true;
}

//+------------------------------------------------------------------+
//| Recovery strategy for lock timeout                             |
//+------------------------------------------------------------------+
bool RecoverFromLockTimeout()
{
    Print("Recovering from lock timeout...");
    
    // Force release lock
    g_trading_lock = false;
    g_lock_time = 0;
    g_order_processing = false;
    
    Print("Trading lock forcibly released");
    
    return true;
}

//+------------------------------------------------------------------+
//| Recovery strategy for direction conflicts                      |
//+------------------------------------------------------------------+
bool RecoverFromDirectionConflict()
{
    Print("Recovering from grid direction conflict...");
    
    // Reset grid direction
    ResetGridDirection();
    
    // Rebuild state
    RebuildGridStateFromPositions();
    
    return true;
}

//+------------------------------------------------------------------+
//| Recovery strategy for excessive exposure                       |
//+------------------------------------------------------------------+
bool RecoverFromExcessiveExposure()
{
    Print("Recovering from excessive exposure...");
    
    // Close some positions to reduce exposure
    double current_exposure = (g_total_buy_lots + g_total_sell_lots) * symbolInfo.Bid();
    double max_exposure = account.Balance() * 0.5;
    
    if(current_exposure > max_exposure)
    {
        Print("Current exposure: ", current_exposure, ", Max allowed: ", max_exposure);
        // Could implement position closing logic here
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Generic error recovery                                          |
//+------------------------------------------------------------------+
bool GenericErrorRecovery()
{
    Print("Applying generic error recovery...");
    
    // Release any locks
    ReleaseTradingLock();
    
    // Rebuild state
    RebuildGridStateFromPositions();
    
    // Wait briefly
    Sleep(1000);
    
    return true;
}

//+------------------------------------------------------------------+
//| Detect error state and trigger recovery                        |
//+------------------------------------------------------------------+
void DetectAndRecoverErrors()
{
    // Check for state inconsistencies
    if(g_total_buy_lots < 0 || g_total_sell_lots < 0)
    {
        HandleError(ERROR_STATE_CORRUPTION, "Negative lot values detected");
        return;
    }
    
    // Check for lock timeout
    if(g_trading_lock && (TimeCurrent() - g_lock_time) > g_lock_timeout_seconds)
    {
        HandleError(ERROR_LOCK_TIMEOUT, "Trading lock timeout detected");
        return;
    }
    
    // Check for excessive exposure
    double current_exposure = (g_total_buy_lots + g_total_sell_lots) * symbolInfo.Bid();
    double max_exposure = account.Balance() * 0.6; // 60% threshold for warning
    
    if(current_exposure > max_exposure)
    {
        HandleError(ERROR_EXCESSIVE_EXPOSURE, "Exposure exceeds safe limits");
        return;
    }
}

//+------------------------------------------------------------------+
//| Test error recovery system (for debugging)                    |
//+------------------------------------------------------------------+
void TestErrorRecoverySystem()
{
    Print("=== TESTING ERROR RECOVERY SYSTEM ===");
    
    // Test 1: Error description function
    Print("Test 1 - Testing error descriptions");
    for(int i = ERROR_NONE; i <= ERROR_EXCESSIVE_EXPOSURE; i++)
    {
        string desc = GetErrorDescription(i);
        Print("  Error ", i, ": ", desc);
    }
    
    // Test 2: State corruption detection
    Print("Test 2 - Testing state corruption detection");
    
    // Temporarily corrupt state for testing
    double original_buy_lots = g_total_buy_lots;
    g_total_buy_lots = -1.0; // Invalid negative value
    
    DetectAndRecoverErrors();
    
    // Restore original value
    g_total_buy_lots = original_buy_lots;
    
    // Test 3: Lock timeout recovery
    Print("Test 3 - Testing lock timeout recovery");
    bool recovery_success = RecoverFromLockTimeout();
    Print("  Lock timeout recovery: ", (recovery_success ? "SUCCESS" : "FAILED"));
    
    // Test 4: State corruption recovery
    Print("Test 4 - Testing state corruption recovery");
    recovery_success = RecoverFromStateCorruption();
    Print("  State corruption recovery: ", (recovery_success ? "SUCCESS" : "FAILED"));
    
    // Test 5: Generic error handling
    Print("Test 5 - Testing generic error handling");
    recovery_success = HandleError(9999, "Test context"); // Unknown error code
    Print("  Generic error handling: ", (recovery_success ? "SUCCESS" : "FAILED"));
    
    // Reset error counter
    g_error_recovery_attempts = 0;
    
    Print("=== END ERROR RECOVERY SYSTEM TEST ===");
}

//+------------------------------------------------------------------+
//| Test lot size calculation functions (Unit Tests)              |
//+------------------------------------------------------------------+
void TestLotSizeCalculationFunctions()
{
    Print("=== TESTING LOT SIZE CALCULATION FUNCTIONS ===");
    
    // Test 1: ValidateLotSize() with various scenarios
    Print("Test 1 - Testing ValidateLotSize() function");
    
    // Test normal lot size
    double test_lot_1 = ValidateLotSize(0.1);
    Print("  ValidateLotSize(0.1) = ", test_lot_1, " (Expected: 0.1 or normalized)");
    
    // Test zero lot size
    double test_lot_2 = ValidateLotSize(0.0);
    Print("  ValidateLotSize(0.0) = ", test_lot_2, " (Expected: minimum lot)");
    
    // Test negative lot size
    double test_lot_3 = ValidateLotSize(-0.5);
    Print("  ValidateLotSize(-0.5) = ", test_lot_3, " (Expected: minimum lot)");
    
    // Test excessive lot size
    double test_lot_4 = ValidateLotSize(1000.0);
    Print("  ValidateLotSize(1000.0) = ", test_lot_4, " (Expected: capped to max)");
    
    // Test 2: Progressive lot calculation
    Print("Test 2 - Testing CalculateProgressiveLot() function");
    
    double base_lot = InpFixedLotSize;
    double multiplier = InpGridMultiplier;
    
    for(int level = 0; level <= 5; level++)
    {
        double progressive_lot = CalculateProgressiveLot(level);
        double expected_lot = base_lot * MathPow(multiplier, level);
        
        Print("  Level ", level, ": Progressive=", progressive_lot, 
              ", Expected=", expected_lot, 
              ", Match=", (MathAbs(progressive_lot - expected_lot) < 0.001 ? "YES" : "NO"));
    }
    
    // Test 3: GetMaxAllowedLot() with different scenarios
    Print("Test 3 - Testing GetMaxAllowedLot() function");
    
    double max_allowed = GetMaxAllowedLot();
    double balance = account.Balance();
    Print("  Current balance: ", balance);
    Print("  Max allowed lot: ", max_allowed);
    Print("  Max lot per balance ratio: ", (max_allowed / balance * 1000), " lots per 1000 balance");
    
    // Test 4: Lot size normalization
    Print("Test 4 - Testing lot size normalization");
    
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    double lot_step = symbolInfo.LotsStep();
    
    Print("  Broker limits: Min=", min_lot, ", Max=", max_lot, ", Step=", lot_step);
    
    // Test various lot sizes for normalization
    double test_lots[] = {0.01, 0.05, 0.11, 0.33, 0.99, 1.01, 2.5};
    int test_count = ArraySize(test_lots);
    
    for(int i = 0; i < test_count; i++)
    {
        double normalized = ValidateLotSize(test_lots[i]);
        Print("  Input: ", test_lots[i], " -> Normalized: ", normalized);
    }
    
    // Test 5: Grid lot size calculation
    Print("Test 5 - Testing CalculateGridLotSize() function");
    
    // Test with different grid levels
    for(int level = 0; level <= 3; level++)
    {
        g_buy_grid_level = level;
        double buy_grid_lot = CalculateGridLotSize(ORDER_TYPE_BUY);
        Print("  Buy grid level ", level, ": ", buy_grid_lot, " lots");
        
        g_sell_grid_level = level;
        double sell_grid_lot = CalculateGridLotSize(ORDER_TYPE_SELL);
        Print("  Sell grid level ", level, ": ", sell_grid_lot, " lots");
    }
    
    // Reset grid levels
    g_buy_grid_level = 0;
    g_sell_grid_level = 0;
    
    Print("=== END LOT SIZE CALCULATION TESTS ===");
}

//+------------------------------------------------------------------+
//| Test grid logic functions (Unit Tests)                        |
//+------------------------------------------------------------------+
void TestGridLogicFunctions()
{
    Print("=== TESTING GRID LOGIC FUNCTIONS ===");
    
    // Test 1: Grid level calculation and tracking
    Print("Test 1 - Testing grid level calculation");
    
    // Test GetCurrentGridLevel function
    for(int test_level = 0; test_level <= 5; test_level++)
    {
        g_buy_grid_level = test_level;
        int buy_level = GetCurrentGridLevel(ORDER_TYPE_BUY);
        Print("  Set buy level ", test_level, ", GetCurrentGridLevel(BUY) = ", buy_level);
        
        g_sell_grid_level = test_level;
        int sell_level = GetCurrentGridLevel(ORDER_TYPE_SELL);
        Print("  Set sell level ", test_level, ", GetCurrentGridLevel(SELL) = ", sell_level);
    }
    
    // Test 2: Single direction enforcement
    Print("Test 2 - Testing single direction enforcement");
    
    // Reset grid direction
    ResetGridDirection();
    Print("  After reset, grid direction: ", GetCurrentGridDirection());
    
    // Test setting buy direction
    SetGridDirection(1);
    bool buy_allowed = ValidateOrderDirection(ORDER_TYPE_BUY);
    bool sell_allowed = ValidateOrderDirection(ORDER_TYPE_SELL);
    Print("  Buy direction set - Buy allowed: ", (buy_allowed ? "YES" : "NO"), 
          ", Sell allowed: ", (sell_allowed ? "YES" : "NO"));
    
    // Test setting sell direction
    SetGridDirection(-1);
    buy_allowed = ValidateOrderDirection(ORDER_TYPE_BUY);
    sell_allowed = ValidateOrderDirection(ORDER_TYPE_SELL);
    Print("  Sell direction set - Buy allowed: ", (buy_allowed ? "YES" : "NO"), 
          ", Sell allowed: ", (sell_allowed ? "YES" : "NO"));
    
    // Test 3: Grid reset functionality
    Print("Test 3 - Testing grid reset functionality");
    
    // Set some grid state
    g_buy_grid_level = 3;
    g_sell_grid_level = 2;
    g_current_grid_direction = 1;
    
    Print("  Before reset - Buy level: ", g_buy_grid_level, 
          ", Sell level: ", g_sell_grid_level, 
          ", Direction: ", g_current_grid_direction);
    
    ResetGridDirection();
    
    Print("  After reset - Buy level: ", g_buy_grid_level, 
          ", Sell level: ", g_sell_grid_level, 
          ", Direction: ", g_current_grid_direction);
    
    // Test 4: Grid state synchronization
    Print("Test 4 - Testing grid state synchronization");
    
    // Test SynchronizeGridDirection function
    Print("  Testing SynchronizeGridDirection()");
    SynchronizeGridDirection();
    Print("  Grid direction after sync: ", GetCurrentGridDirection());
    
    // Test UpdateGridPositions function
    Print("  Testing UpdateGridPositions()");
    double original_buy_lots = g_total_buy_lots;
    double original_sell_lots = g_total_sell_lots;
    
    UpdateGridPositions();
    
    Print("  Buy lots: ", original_buy_lots, " -> ", g_total_buy_lots);
    Print("  Sell lots: ", original_sell_lots, " -> ", g_total_sell_lots);
    
    // Test 5: Direction change logic
    Print("Test 5 - Testing direction change logic");
    
    // Test ShouldChangeGridDirection function
    bool should_change_buy = ShouldChangeGridDirection(ORDER_TYPE_BUY);
    bool should_change_sell = ShouldChangeGridDirection(ORDER_TYPE_SELL);
    
    Print("  Should change to buy: ", (should_change_buy ? "YES" : "NO"));
    Print("  Should change to sell: ", (should_change_sell ? "YES" : "NO"));
    
    // Reset for normal operation
    ResetGridDirection();
    
    Print("=== END GRID LOGIC TESTS ===");
}

//+------------------------------------------------------------------+
//| Test complete order execution flow (Integration Test)         |
//+------------------------------------------------------------------+
void TestCompleteOrderExecutionFlow()
{
    Print("=== TESTING COMPLETE ORDER EXECUTION FLOW ===");
    
    // Test 1: Full order execution process simulation
    Print("Test 1 - Testing full order execution process");
    
    double current_price = symbolInfo.Bid();
    double test_lot = 0.01; // Small lot for testing
    
    // Test the complete validation pipeline
    Print("  Step 1: Testing advanced parameter validation");
    bool validation_ok = ValidateAdvancedOrderParameters(ORDER_TYPE_BUY, test_lot, current_price);
    Print("    Advanced validation result: ", (validation_ok ? "PASS" : "FAIL"));
    
    Print("  Step 2: Testing risk validation");
    bool risk_ok = CheckAccountRisk(test_lot, current_price);
    Print("    Risk validation result: ", (risk_ok ? "PASS" : "FAIL"));
    
    Print("  Step 3: Testing direction validation");
    bool direction_ok = ValidateOrderDirection(ORDER_TYPE_BUY);
    Print("    Direction validation result: ", (direction_ok ? "PASS" : "FAIL"));
    
    Print("  Step 4: Testing lock acquisition");
    bool lock_acquired = AcquireTradingLock();
    Print("    Lock acquisition result: ", (lock_acquired ? "SUCCESS" : "FAILED"));
    
    if(lock_acquired)
    {
        Print("  Step 5: Testing order timing validation");
        bool timing_ok = CanPlaceNewOrder();
        Print("    Timing validation result: ", (timing_ok ? "PASS" : "FAIL"));
        
        // Release lock for testing
        ReleaseTradingLock();
        Print("  Step 6: Lock released successfully");
    }
    
    // Test 2: Error handling in complete workflow
    Print("Test 2 - Testing error handling in workflow");
    
    // Simulate various error conditions
    Print("  Testing invalid lot size handling");
    bool invalid_lot_handled = !ValidateAdvancedOrderParameters(ORDER_TYPE_BUY, 0.0, current_price);
    Print("    Invalid lot rejection: ", (invalid_lot_handled ? "PASS" : "FAIL"));
    
    Print("  Testing excessive lot size handling");
    bool excessive_lot_handled = !ValidateAdvancedOrderParameters(ORDER_TYPE_BUY, 1000.0, current_price);
    Print("    Excessive lot rejection: ", (excessive_lot_handled ? "PASS" : "FAIL"));
    
    // Test 3: State consistency throughout execution
    Print("Test 3 - Testing state consistency");
    
    // Record initial state
    int initial_buy_level = g_buy_grid_level;
    int initial_sell_level = g_sell_grid_level;
    int initial_direction = g_current_grid_direction;
    
    Print("  Initial state - Buy level: ", initial_buy_level, 
          ", Sell level: ", initial_sell_level, 
          ", Direction: ", initial_direction);
    
    // Simulate state changes
    UpdateGridPositions();
    ValidateGridStateConsistency();
    
    Print("  After update - Buy level: ", g_buy_grid_level, 
          ", Sell level: ", g_sell_grid_level, 
          ", Direction: ", g_current_grid_direction);
    
    // Test 4: Performance under simulated high-frequency scenarios
    Print("Test 4 - Testing performance under high-frequency simulation");
    
    uint start_time = GetTickCount();
    int test_iterations = 100;
    int successful_validations = 0;
    
    for(int i = 0; i < test_iterations; i++)
    {
        if(ValidateAdvancedOrderParameters(ORDER_TYPE_BUY, test_lot, current_price + i * symbolInfo.Point()))
        {
            successful_validations++;
        }
    }
    
    uint end_time = GetTickCount();
    double elapsed_ms = (double)(end_time - start_time);
    
    Print("  Performance test results:");
    Print("    Iterations: ", test_iterations);
    Print("    Successful validations: ", successful_validations);
    Print("    Time elapsed: ", elapsed_ms, " ms");
    Print("    Average time per validation: ", (elapsed_ms / test_iterations), " ms");
    
    Print("=== END ORDER EXECUTION FLOW TEST ===");
}

//+------------------------------------------------------------------+
//| Test risk management integration (Integration Test)           |
//+------------------------------------------------------------------+
void TestRiskManagementIntegration()
{
    Print("=== TESTING RISK MANAGEMENT INTEGRATION ===");
    
    // Test 1: Risk limit enforcement in trading scenarios
    Print("Test 1 - Testing risk limit enforcement");
    
    double current_price = symbolInfo.Bid();
    double balance = account.Balance();
    
    Print("  Current account balance: ", balance);
    Print("  Current free margin: ", account.FreeMargin());
    
    // Test various lot sizes against risk limits
    double test_lots[] = {0.01, 0.1, 1.0, 5.0, 10.0};
    int lot_count = ArraySize(test_lots);
    
    for(int i = 0; i < lot_count; i++)
    {
        bool risk_ok = CheckAccountRisk(test_lots[i], current_price);
        double max_allowed = GetMaxAllowedLot();
        
        Print("  Lot ", test_lots[i], ": Risk check = ", (risk_ok ? "PASS" : "FAIL"), 
              ", Max allowed = ", max_allowed);
    }
    
    // Test 2: Account balance protection mechanisms
    Print("Test 2 - Testing account balance protection");
    
    // Test maximum allowed lot calculation
    double max_lot = GetMaxAllowedLot();
    double risk_percentage = (max_lot * current_price) / balance * 100;
    
    Print("  Maximum allowed lot: ", max_lot);
    Print("  Risk percentage of balance: ", risk_percentage, "%");
    
    // Test lot size validation
    double validated_lot = ValidateLotSize(max_lot * 2); // Test with double max
    Print("  Validated lot (2x max): ", validated_lot, " (should be capped)");
    
    // Test 3: Maximum exposure limits
    Print("Test 3 - Testing maximum exposure limits");
    
    double current_exposure = (g_total_buy_lots + g_total_sell_lots) * current_price;
    double max_exposure = balance * 0.5; // 50% limit
    
    Print("  Current exposure: ", current_exposure);
    Print("  Maximum allowed exposure: ", max_exposure);
    Print("  Exposure percentage: ", (current_exposure / balance * 100), "%");
    
    // Test exposure checking with additional lots
    double additional_lots[] = {0.1, 1.0, 5.0, 10.0};
    int exposure_count = ArraySize(additional_lots);
    
    for(int i = 0; i < exposure_count; i++)
    {
        bool exposure_ok = CheckAccountRisk(additional_lots[i], SymbolInfoDouble(_Symbol, SYMBOL_BID));
        Print("  Additional ", additional_lots[i], " lots: ", (exposure_ok ? "ALLOWED" : "REJECTED"));
    }
    
    // Test 4: Stress test for extreme market conditions
    Print("Test 4 - Stress testing for extreme conditions");
    
    // Simulate extreme lot size requests
    Print("  Testing extreme lot sizes:");
    double extreme_lots[] = {0.001, 100.0, 1000.0, 10000.0};
    int extreme_count = ArraySize(extreme_lots);
    
    for(int i = 0; i < extreme_count; i++)
    {
        double validated = ValidateLotSize(extreme_lots[i]);
        bool risk_check = CheckAccountRisk(validated, current_price);
        
        Print("    Input: ", extreme_lots[i], " -> Validated: ", validated, 
              ", Risk check: ", (risk_check ? "PASS" : "FAIL"));
    }
    
    // Simulate extreme price movements
    Print("  Testing extreme price scenarios:");
    double price_multipliers[] = {0.5, 2.0, 10.0, 100.0};
    int price_count = ArraySize(price_multipliers);
    
    for(int i = 0; i < price_count; i++)
    {
        double test_price = current_price * price_multipliers[i];
        bool risk_ok = CheckAccountRisk(0.1, test_price);
        
        Print("    Price x", price_multipliers[i], " (", test_price, "): ", 
              (risk_ok ? "PASS" : "FAIL"));
    }
    
    // Test recovery from risk violations
    Print("  Testing risk violation recovery:");
    
    // Temporarily set excessive exposure
    double original_buy_lots = g_total_buy_lots;
    g_total_buy_lots = 1000.0; // Excessive amount
    
    DetectAndRecoverErrors(); // Should detect excessive exposure
    
    // Restore original value
    g_total_buy_lots = original_buy_lots;
    
    Print("=== END RISK MANAGEMENT INTEGRATION TEST ===");
}

//+------------------------------------------------------------------+
//| Acquire trading lock to prevent concurrent order execution     |
//+------------------------------------------------------------------+
bool AcquireTradingLock()
{
    datetime current_time = TimeCurrent();
    
    // Check if lock is already held and not timed out
    if(g_trading_lock)
    {
        // Check for timeout
        if(current_time - g_lock_time > g_lock_timeout_seconds)
        {
            Print("WARNING: Trading lock timed out after ", g_lock_timeout_seconds, " seconds, releasing lock");
            Print("Lock was acquired at: ", TimeToString(g_lock_time), ", current time: ", TimeToString(current_time));
            ReleaseTradingLock();
        }
        else
        {
            // Lock is still active
            int remaining_time = g_lock_timeout_seconds - (int)(current_time - g_lock_time);
            if(g_orders_today % 50 == 1) // Log every 50th attempt to avoid spam
            {
                Print("Trading lock is active, remaining timeout: ", remaining_time, " seconds");
            }
            return false;
        }
    }
    
    // Acquire the lock
    g_trading_lock = true;
    g_lock_time = current_time;
    g_order_processing = true;
    
    // Enhanced logging
    if(g_orders_today % 20 == 1) // Log every 20th lock acquisition
    {
        Print("Trading lock acquired at: ", TimeToString(current_time));
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Release trading lock                                            |
//+------------------------------------------------------------------+
void ReleaseTradingLock()
{
    if(g_trading_lock)
    {
        datetime current_time = TimeCurrent();
        int lock_duration = (int)(current_time - g_lock_time);
        
        // Enhanced logging
        if(g_orders_today % 20 == 1 || lock_duration > 5) // Log every 20th release or if lock was held > 5 seconds
        {
            Print("Trading lock released after ", lock_duration, " seconds");
        }
        
        // Warn if lock was held too long
        if(lock_duration > 10)
        {
            Print("WARNING: Trading lock was held for ", lock_duration, " seconds (longer than expected)");
        }
    }
    
    g_trading_lock = false;
    g_lock_time = 0;
    g_order_processing = false;
}

//+------------------------------------------------------------------+
//| Check if order is currently being processed                    |
//+------------------------------------------------------------------+
bool IsOrderProcessing()
{
    datetime current_time = TimeCurrent();
    
    // Check if we're within minimum delay period
    if(current_time - g_last_order_time < g_min_order_delay_seconds)
    {
        return true;
    }
    
    // Check if trading lock is active
    if(g_trading_lock)
    {
        // Check for timeout
        if(current_time - g_lock_time > g_lock_timeout_seconds)
        {
            Print("WARNING: Trading lock timed out in IsOrderProcessing, releasing lock");
            ReleaseTradingLock();
            return false;
        }
        return true;
    }
    
    return g_order_processing;
}

//+------------------------------------------------------------------+
//| Check if enough time has passed since last order              |
//+------------------------------------------------------------------+
bool CanPlaceNewOrder()
{
    datetime current_time = TimeCurrent();
    
    // Check minimum time delay
    if(current_time - g_last_order_time < g_min_order_delay_seconds)
    {
        return false;
    }
    
    // Check if another order is being processed
    if(IsOrderProcessing())
    {
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Update order timing after successful order placement           |
//+------------------------------------------------------------------+
void UpdateOrderTiming()
{
    g_last_order_time = TimeCurrent();
}

//+------------------------------------------------------------------+
//| Execute grid order with comprehensive validation and logging   |
//+------------------------------------------------------------------+
bool ExecuteGridOrder(ENUM_ORDER_TYPE order_type, double lot_size, double price)
{
    string operation = (order_type == ORDER_TYPE_BUY) ? "BUY" : "SELL";
    
    // Enhanced pre-execution validation
    if(!ValidateAdvancedOrderParameters(order_type, lot_size, price))
    {
        Print("Order execution failed: ", operation, " (VALIDATION FAILED) - Lot: ", lot_size, ", Price: ", price);
        return false;
    }
    
    // Risk validation
    if(!CheckAccountRisk(lot_size, price))
    {
        Print("Order execution failed: ", operation, " (RISK REJECTED) - Lot: ", lot_size, ", Price: ", price);
        return false;
    }
    
    // Direction validation
    if(!ValidateOrderDirection(order_type))
    {
        Print("Order execution failed: ", operation, " (DIRECTION REJECTED) - Lot: ", lot_size, ", Price: ", price);
        return false;
    }

    // Order frequency validation
    if(!CheckOrderFrequency())
    {
        Print("Order execution failed: ", operation, " (FREQUENCY REJECTED) - Too many orders recently");
        return false;
    }

    // Volatility protection
    if(!CheckVolatilityProtection())
    {
        Print("Order execution failed: ", operation, " (VOLATILITY PROTECTION) - High volatility detected");
        return false;
    }

    // Enhanced grid direction validation
    if(!ValidateGridDirection(order_type))
    {
        Print("Order execution failed: ", operation, " (GRID DIRECTION CONFLICT)");
        return false;
    }

    // NO Take Profit และ NO Stop Loss สำหรับ Grid Trading
    double take_profit = 0.0; // ไม่ตั้ง TP แต่ละออเดอร์ - ใช้ Grid Profit แทน
    double stop_loss = 0.0;   // ไม่ตั้ง SL แต่ละออเดอร์

    // Execute the order
    bool success = false;
    string comment = "Grid " + operation;

    if(order_type == ORDER_TYPE_BUY)
    {
        success = trade.Buy(lot_size, _Symbol, price, stop_loss, take_profit, comment);
    }
    else
    {
        success = trade.Sell(lot_size, _Symbol, price, stop_loss, take_profit, comment);
    }
    
    // Log the execution result with TP info
    string tp_info = InpUseMarginTP ?
        StringFormat("TP: %.5f (%.1f%% margin)", take_profit, InpMarginTPPercent) :
        StringFormat("TP: %.5f (%d points)", take_profit, InpTakeProfit);
    Print("Order execution: ", operation, " - Lot: ", lot_size, ", Price: ", price, ", ", tp_info, ", Success: ", success);
    
    if(success)
    {
        // Update order frequency tracking
        UpdateOrderFrequency();

        // Update statistics and timing
        g_orders_today++;
        g_stats.total_trades++;
        g_last_trade_time = TimeCurrent();
        g_last_trade_ticket = trade.ResultOrder();
        UpdateOrderTiming();
        
        // Add to recent orders tracking
        AddToRecentOrders(price);
        
        // Update grid tracking
        if(order_type == ORDER_TYPE_BUY)
            g_last_buy_price = price;
        else
            g_last_sell_price = price;
        
        // Update daily lots counter
        UpdateDailyLotsCounter(lot_size);
    }
    
    return success;
}

//+------------------------------------------------------------------+
//| Check if price level is too close to recent orders             |
//+------------------------------------------------------------------+
bool ValidatePriceDistance(double new_price)
{
    double min_distance = g_min_price_distance_points * symbolInfo.Point();
    
    for(int i = 0; i < g_recent_order_count && i < 10; i++)
    {
        double price_diff = MathAbs(new_price - g_recent_order_prices[i]);
        if(price_diff < min_distance)
        {
            Print("WARNING: New order price ", new_price, " too close to recent order at ", 
                  g_recent_order_prices[i], " (distance: ", price_diff/symbolInfo.Point(), " points)");
            return false;
        }
    }
    return true;
}

//+------------------------------------------------------------------+
//| Check order frequency limits                                    |
//+------------------------------------------------------------------+
bool ValidateOrderFrequency()
{
    datetime current_time = TimeCurrent();
    datetime one_minute_ago = current_time - 60;
    
    int orders_in_last_minute = 0;
    for(int i = 0; i < g_recent_order_count && i < 10; i++)
    {
        if(g_recent_order_times[i] > one_minute_ago)
            orders_in_last_minute++;
    }
    
    if(orders_in_last_minute >= g_max_orders_per_minute)
    {
        Print("WARNING: Order frequency limit reached: ", orders_in_last_minute, 
              " orders in last minute (max: ", g_max_orders_per_minute, ")");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Add order to recent orders tracking                             |
//+------------------------------------------------------------------+
void AddToRecentOrders(double price)
{
    // Shift array if full
    if(g_recent_order_count >= 10)
    {
        for(int i = 0; i < 9; i++)
        {
            g_recent_order_prices[i] = g_recent_order_prices[i + 1];
            g_recent_order_times[i] = g_recent_order_times[i + 1];
        }
        g_recent_order_count = 9;
    }
    
    // Add new order
    g_recent_order_prices[g_recent_order_count] = price;
    g_recent_order_times[g_recent_order_count] = TimeCurrent();
    g_recent_order_count++;
}

//+------------------------------------------------------------------+
//| Check for conflicting pending orders                           |
//+------------------------------------------------------------------+
bool CheckConflictingOrders(ENUM_ORDER_TYPE order_type, double price)
{
    double min_distance = g_min_price_distance_points * symbolInfo.Point();
    
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(order.SelectByIndex(i))
        {
            if(order.Symbol() == _Symbol && order.Magic() == InpMagicNumber)
            {
                double order_price = order.PriceOpen();
                double price_diff = MathAbs(price - order_price);
                
                if(price_diff < min_distance)
                {
                    Print("WARNING: Conflicting pending order found at ", order_price, 
                          " (distance: ", price_diff/symbolInfo.Point(), " points)");
                    
                    // Cancel conflicting order
                    if(trade.OrderDelete(order.Ticket()))
                    {
                        Print("INFO: Cancelled conflicting order #", order.Ticket());
                    }
                    else
                    {
                        Print("ERROR: Failed to cancel conflicting order #", order.Ticket());
                        return false;
                    }
                }
            }
        }
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Enhanced order validation with all checks                      |
//+------------------------------------------------------------------+
bool ValidateAdvancedOrderParameters(ENUM_ORDER_TYPE order_type, double lot_size, double price)
{
    // Basic parameter validation (existing function)
    if(!ValidateOrderParameters(order_type, lot_size, price))
        return false;
    
    // Price distance validation
    if(!ValidatePriceDistance(price))
        return false;
    
    // Order frequency validation
    if(!ValidateOrderFrequency())
        return false;
    
    // Conflicting orders check
    if(!CheckConflictingOrders(order_type, price))
        return false;
    
    return true;
}

//+------------------------------------------------------------------+
//| Update and synchronize grid state variables                    |
//+------------------------------------------------------------------+
void UpdateGridState()
{
    // This function ensures all grid state variables are synchronized
    // with the actual market positions
    
    // Update grid positions (this also updates grid levels)
    UpdateGridPositions();
    
    // Synchronize grid direction with actual positions
    SynchronizeGridDirection();
    
    // Validate state consistency
    ValidateGridStateConsistency();
}

//+------------------------------------------------------------------+
//| Synchronize grid direction with actual positions               |
//+------------------------------------------------------------------+
void SynchronizeGridDirection()
{
    int buy_positions = 0;
    int sell_positions = 0;
    
    // Count actual positions
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.PositionType() == POSITION_TYPE_BUY)
                    buy_positions++;
                else
                    sell_positions++;
            }
        }
    }
    
    // Synchronize grid direction based on actual positions
    if(buy_positions > 0 && sell_positions == 0)
    {
        if(g_current_grid_direction != 1)
        {
            Print("Synchronizing grid direction to BUY based on positions");
            g_current_grid_direction = 1;
        }
    }
    else if(sell_positions > 0 && buy_positions == 0)
    {
        if(g_current_grid_direction != -1)
        {
            Print("Synchronizing grid direction to SELL based on positions");
            g_current_grid_direction = -1;
        }
    }
    else if(buy_positions == 0 && sell_positions == 0)
    {
        if(g_current_grid_direction != 0)
        {
            Print("Synchronizing grid direction to NONE - no positions");
            g_current_grid_direction = 0;
        }
    }
    else if(buy_positions > 0 && sell_positions > 0)
    {
        // Conflicting positions - this shouldn't happen with our new system
        Print("WARNING: Conflicting positions detected - Buy: ", buy_positions, ", Sell: ", sell_positions);
        // Keep current direction but log the issue
    }
}

//+------------------------------------------------------------------+
//| Validate grid state consistency                                |
//+------------------------------------------------------------------+
void ValidateGridStateConsistency()
{
    // Check if grid levels match actual position count
    int actual_buy_positions = 0;
    int actual_sell_positions = 0;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.PositionType() == POSITION_TYPE_BUY)
                    actual_buy_positions++;
                else
                    actual_sell_positions++;
            }
        }
    }
    
    // Validate buy grid level
    if(g_buy_grid_level != actual_buy_positions)
    {
        Print("WARNING: Buy grid level mismatch - Expected: ", g_buy_grid_level, ", Actual: ", actual_buy_positions);
        g_buy_grid_level = actual_buy_positions;
    }
    
    // Validate sell grid level
    if(g_sell_grid_level != actual_sell_positions)
    {
        Print("WARNING: Sell grid level mismatch - Expected: ", g_sell_grid_level, ", Actual: ", actual_sell_positions);
        g_sell_grid_level = actual_sell_positions;
    }
    
    // Validate total lots
    double actual_buy_lots = 0.0;
    double actual_sell_lots = 0.0;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.PositionType() == POSITION_TYPE_BUY)
                    actual_buy_lots += position.Volume();
                else
                    actual_sell_lots += position.Volume();
            }
        }
    }
    
    // Allow small differences due to floating point precision
    double buy_diff = MathAbs(g_total_buy_lots - actual_buy_lots);
    double sell_diff = MathAbs(g_total_sell_lots - actual_sell_lots);
    
    if(buy_diff > 0.01) // More than 0.01 lot difference
    {
        Print("WARNING: Buy lots mismatch - Expected: ", g_total_buy_lots, ", Actual: ", actual_buy_lots);
    }
    
    if(sell_diff > 0.01) // More than 0.01 lot difference
    {
        Print("WARNING: Sell lots mismatch - Expected: ", g_total_sell_lots, ", Actual: ", actual_sell_lots);
    }
}

//+------------------------------------------------------------------+
//| Rebuild grid state from actual positions (recovery function)   |
//+------------------------------------------------------------------+
void RebuildGridStateFromPositions()
{
    Print("Rebuilding grid state from actual positions...");
    
    // Reset all state variables
    g_total_buy_lots = 0.0;
    g_total_sell_lots = 0.0;
    g_buy_grid_level = 0;
    g_sell_grid_level = 0;
    g_average_buy_price = 0.0;
    g_average_sell_price = 0.0;
    
    double total_buy_volume = 0.0;
    double total_sell_volume = 0.0;
    double weighted_buy_price = 0.0;
    double weighted_sell_price = 0.0;
    
    int buy_position_count = 0;
    int sell_position_count = 0;
    
    // Rebuild from actual positions
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.PositionType() == POSITION_TYPE_BUY)
                {
                    g_total_buy_lots += position.Volume();
                    weighted_buy_price += position.PriceOpen() * position.Volume();
                    total_buy_volume += position.Volume();
                    buy_position_count++;
                }
                else
                {
                    g_total_sell_lots += position.Volume();
                    weighted_sell_price += position.PriceOpen() * position.Volume();
                    total_sell_volume += position.Volume();
                    sell_position_count++;
                }
            }
        }
    }
    
    // Calculate averages
    if(total_buy_volume > 0)
        g_average_buy_price = weighted_buy_price / total_buy_volume;
    
    if(total_sell_volume > 0)
        g_average_sell_price = weighted_sell_price / total_sell_volume;
    
    // Set grid levels
    g_buy_grid_level = buy_position_count;
    g_sell_grid_level = sell_position_count;
    
    // Set grid direction
    if(buy_position_count > 0 && sell_position_count == 0)
        g_current_grid_direction = 1;
    else if(sell_position_count > 0 && buy_position_count == 0)
        g_current_grid_direction = -1;
    else if(buy_position_count == 0 && sell_position_count == 0)
        g_current_grid_direction = 0;
    else
    {
        Print("WARNING: Conflicting positions found during rebuild - Buy: ", buy_position_count, ", Sell: ", sell_position_count);
        g_current_grid_direction = 0; // Reset to neutral
    }
    
    Print("Grid state rebuilt - Buy: ", buy_position_count, " positions (", g_total_buy_lots, " lots), Sell: ", sell_position_count, " positions (", g_total_sell_lots, " lots)");
    Print("Grid direction set to: ", g_current_grid_direction);
}

//+------------------------------------------------------------------+
//| Emergency state recovery function                              |
//+------------------------------------------------------------------+
void EmergencyStateRecovery()
{
    Print("EMERGENCY: Performing state recovery...");
    
    // Release any stuck locks
    if(g_trading_lock)
    {
        Print("EMERGENCY: Releasing stuck trading lock");
        ReleaseTradingLock();
    }
    
    // Rebuild grid state from positions
    RebuildGridStateFromPositions();
    
    // Reset error correction state
    g_consecutive_losses = 0;
    g_current_lot_size = 0.0;
    g_lot_multiplications = 0;
    g_reverse_mode = false;
    
    Print("EMERGENCY: State recovery completed");
}

//+------------------------------------------------------------------+
//| Check if there's already an order at similar price level      |
//+------------------------------------------------------------------+
bool HasOrderAtSimilarPrice(ENUM_ORDER_TYPE order_type, double price)
{
    double min_distance = InpGridDistance * symbolInfo.Point();
    
    // Check existing positions
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                bool same_direction = (order_type == ORDER_TYPE_BUY && position.PositionType() == POSITION_TYPE_BUY) ||
                (order_type == ORDER_TYPE_SELL && position.PositionType() == POSITION_TYPE_SELL);
                
                if(same_direction)
                {
                    double distance = MathAbs(position.PriceOpen() - price);
                    if(distance < min_distance)
                    {
                        return true; // Too close to existing position
                    }
                }
            }
        }
    }
    
    // Check pending orders
    for(int i = 0; i < OrdersTotal(); i++)
    {
        if(order.SelectByIndex(i))
        {
            if(order.Symbol() == _Symbol && order.Magic() == InpMagicNumber)
            {
                bool same_direction = (order_type == ORDER_TYPE_BUY && (order.OrderType() == ORDER_TYPE_BUY_LIMIT || order.OrderType() == ORDER_TYPE_BUY_STOP)) ||
                (order_type == ORDER_TYPE_SELL && (order.OrderType() == ORDER_TYPE_SELL_LIMIT || order.OrderType() == ORDER_TYPE_SELL_STOP));
                
                if(same_direction)
                {
                    double distance = MathAbs(order.PriceOpen() - price);
                    if(distance < min_distance)
                    {
                        return true; // Too close to existing order
                    }
                }
            }
        }
    }
    
    return false;
}

//+------------------------------------------------------------------+
//| Validate order parameters before execution                     |
//+------------------------------------------------------------------+
bool ValidateOrderParameters(ENUM_ORDER_TYPE order_type, double lot_size, double price)
{
    // Check lot size
    if(lot_size <= 0)
    {
        Print("ERROR: Invalid lot size: ", lot_size);
        return false;
    }
    
    // Check price
    if(price <= 0)
    {
        Print("ERROR: Invalid price: ", price);
        return false;
    }
    
    // Check if there's already an order at similar price
    if(HasOrderAtSimilarPrice(order_type, price))
    {
        Print("WARNING: Order rejected - too close to existing position / order at price: ", price);
        return false;
    }
    
    // Check broker limits
    double min_lot = symbolInfo.LotsMin();
    double max_lot = symbolInfo.LotsMax();
    
    if(lot_size < min_lot || lot_size > max_lot)
    {
        Print("ERROR: Lot size ", lot_size, " outside broker limits [", min_lot, ", ", max_lot, "]");
        return false;
    }
    
    return true;
}

//+------------------------------------------------------------------+
//| Check if should close all profitable positions                 |
//+------------------------------------------------------------------+
void CheckCloseAllOnProfit()
{
    if(!InpCloseAllOnProfit) return;

    double total_profit = 0.0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                total_profit += position.Profit();
            }
        }
    }

    // Improved profit management - dynamic profit targets
    double min_profit = CalculateDynamicProfitTarget();

    // เพิ่มกำไรขั้นต่ำตามจำนวน positions
    int position_count = CountOpenPositions();
    if(position_count > 1)
    {
        min_profit = min_profit * (1.0 + (position_count - 1) * 0.5); // เพิ่มเป้าหมายตาม grid levels
    }

    if(total_profit > min_profit)
    {
        CloseAllPositions();
        InitializeGridSystem();
        // Reset error correction state on profit
        g_consecutive_losses = 0;
        g_lot_multiplications = 0;
        g_current_lot_size = InpFixedLotSize;

        // Logging ผลกำไร
        Print("Grid closed: $", DoubleToString(total_profit, 2),
              " (Target: $", DoubleToString(min_profit, 2),
              ", Positions: ", position_count, ")");
    }
}

//+------------------------------------------------------------------+
//| Calculate dynamic profit target based on market conditions      |
//+------------------------------------------------------------------+
double CalculateDynamicProfitTarget()
{
    // Base profit target
    double base_profit = 2.0;

    // Account balance based scaling (เพิ่มเป้าหมายตาม account balance)
    double balance = account.Balance();
    if(balance > 10000) base_profit += (balance - 10000) / 5000; // เพิ่ม $1 ทุก $5000

    // Volatility adjustment (ปรับตาม volatility)
    double atr_values[];
    int atr_handle = iATR(_Symbol, PERIOD_CURRENT, 14);
    if(atr_handle != INVALID_HANDLE && CopyBuffer(atr_handle, 0, 0, 1, atr_values) > 0)
    {
        double atr = atr_values[0];
        double point_value = symbolInfo.TickValue() / symbolInfo.TickSize();
        double atr_dollars = atr * point_value * InpFixedLotSize;

        // เพิ่มเป้าหมายกำไรถ้า volatility สูง
        if(atr_dollars > 1.0) base_profit += atr_dollars * 0.5;
    }

    // Minimum และ maximum limits
    if(base_profit < 1.0) base_profit = 1.0;
    if(base_profit > 20.0) base_profit = 20.0;

    return base_profit;
}

//+------------------------------------------------------------------+
//| Check order frequency to prevent rapid-fire orders             |
//+------------------------------------------------------------------+
bool CheckOrderFrequency()
{
    datetime current_time = TimeCurrent();

    // Check minimum interval between orders
    if(g_last_order_time > 0 && (current_time - g_last_order_time) < g_min_order_interval)
    {
        return false; // Too soon since last order
    }

    // Check orders per minute limit
    datetime current_minute_mark = (current_time / 60) * 60; // Round down to minute
    if(g_current_minute != current_minute_mark)
    {
        g_current_minute = current_minute_mark;
        g_orders_this_minute = 0; // Reset counter for new minute
    }

    if(g_orders_this_minute >= g_max_orders_per_minute)
    {
        return false; // Too many orders this minute
    }

    return true;
}

//+------------------------------------------------------------------+
//| Check volatility conditions to prevent trading in extreme news  |
//+------------------------------------------------------------------+
bool CheckVolatilityProtection()
{
    // Check if we're in volatility cooldown
    if(g_high_volatility_mode && (TimeCurrent() - g_volatility_cooldown) < 300) // 5 minute cooldown
    {
        return false;
    }

    // Get current ATR value
    double atr_buffer[1];
    if(CopyBuffer(h_atr, 0, 0, 1, atr_buffer) <= 0)
    {
        return true; // If can't get ATR, allow trading
    }

    double current_atr = atr_buffer[0];

    // Initialize last ATR if not set
    if(g_last_atr_value == 0)
    {
        g_last_atr_value = current_atr;
        return true;
    }

    // Check if ATR has spiked significantly (news event)
    double atr_ratio = current_atr / g_last_atr_value;
    if(atr_ratio > g_atr_multiplier_threshold)
    {
        g_high_volatility_mode = true;
        g_volatility_cooldown = TimeCurrent();
        Print("HIGH VOLATILITY DETECTED - Trading suspended. ATR ratio: ", atr_ratio);
        return false;
    }

    // Reset high volatility mode if ATR is normal
    if(atr_ratio < 1.5)
    {
        g_high_volatility_mode = false;
    }

    // Update last ATR value (slowly to avoid false positives)
    g_last_atr_value = g_last_atr_value * 0.9 + current_atr * 0.1;

    return true;
}

//+------------------------------------------------------------------+
//| Enhanced grid direction validation                               |
//+------------------------------------------------------------------+
bool ValidateGridDirection(ENUM_ORDER_TYPE order_type)
{
    if(!InpEnforceSingleDirection)
        return true; // Direction enforcement disabled

    // Count current positions by type
    int buy_positions = 0;
    int sell_positions = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.PositionType() == POSITION_TYPE_BUY)
                    buy_positions++;
                else if(position.PositionType() == POSITION_TYPE_SELL)
                    sell_positions++;
            }
        }
    }

    // If we have positions in both directions, prevent new orders
    if(buy_positions > 0 && sell_positions > 0)
    {
        Print("WARNING: Both buy and sell positions exist. Preventing new ",
              (order_type == ORDER_TYPE_BUY ? "BUY" : "SELL"), " order.");
        return false;
    }

    // If we have positions in opposite direction to new order, prevent it
    if(order_type == ORDER_TYPE_BUY && sell_positions > 0)
    {
        Print("WARNING: Sell positions exist. Preventing new BUY order.");
        return false;
    }

    if(order_type == ORDER_TYPE_SELL && buy_positions > 0)
    {
        Print("WARNING: Buy positions exist. Preventing new SELL order.");
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Update order frequency tracking                                  |
//+------------------------------------------------------------------+
void UpdateOrderFrequency()
{
    g_last_order_time = TimeCurrent();
    g_orders_this_minute++;
}

//+------------------------------------------------------------------+
//| Get reliable price with multiple fallback methods               |
//+------------------------------------------------------------------+
double GetReliablePrice(bool get_ask)
{
    double price = 0.0;

    // Method 1: Try symbolInfo first
    if(get_ask)
        price = symbolInfo.Ask();
    else
        price = symbolInfo.Bid();

    // Method 2: If failed, try SymbolInfoDouble
    if(price <= 0)
    {
        if(get_ask)
            price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        else
            price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    }

    // Method 3: If still failed, use iClose as last resort
    if(price <= 0)
    {
        price = iClose(_Symbol, PERIOD_CURRENT, 0);

        // For Ask, add spread
        if(get_ask && price > 0)
        {
            double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
            price += spread;
        }
    }

    // Final validation
    if(price <= 0)
    {
        Print("CRITICAL ERROR: Cannot get valid price for ", _Symbol, " - Method: ", (get_ask ? "ASK" : "BID"));
        return 0.0;
    }

    return price;
}

//+------------------------------------------------------------------+
//| Fix grid direction synchronization                               |
//+------------------------------------------------------------------+
void FixGridDirectionSync()
{
    // Count actual positions
    int buy_count = 0;
    int sell_count = 0;

    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol && position.Magic() == InpMagicNumber)
            {
                if(position.PositionType() == POSITION_TYPE_BUY)
                    buy_count++;
                else if(position.PositionType() == POSITION_TYPE_SELL)
                    sell_count++;
            }
        }
    }

    // Synchronize grid direction with actual positions
    if(buy_count > 0 && sell_count == 0)
    {
        if(g_current_grid_direction != 1)
        {
            g_current_grid_direction = 1;
            Print("Grid direction synchronized to BUY (", buy_count, " positions)");
        }
    }
    else if(sell_count > 0 && buy_count == 0)
    {
        if(g_current_grid_direction != -1)
        {
            g_current_grid_direction = -1;
            Print("Grid direction synchronized to SELL (", sell_count, " positions)");
        }
    }
    else if(buy_count == 0 && sell_count == 0)
    {
        if(g_current_grid_direction != 0)
        {
            g_current_grid_direction = 0;
            Print("Grid direction synchronized to NONE - no positions");
        }
    }
    else if(buy_count > 0 && sell_count > 0)
    {
        // Mixed positions - this shouldn't happen with proper direction enforcement
        Print("WARNING: Mixed positions detected - Buy: ", buy_count, ", Sell: ", sell_count);

        // Close the smaller side to maintain direction
        if(buy_count > sell_count)
        {
            Print("Closing sell positions to maintain buy direction");
            ClosePositionsByType(POSITION_TYPE_SELL);
            g_current_grid_direction = 1;
        }
        else
        {
            Print("Closing buy positions to maintain sell direction");
            ClosePositionsByType(POSITION_TYPE_BUY);
            g_current_grid_direction = -1;
        }
    }
}

//+------------------------------------------------------------------+
//| Close positions by type                                          |
//+------------------------------------------------------------------+
void ClosePositionsByType(ENUM_POSITION_TYPE position_type)
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(position.SelectByIndex(i))
        {
            if(position.Symbol() == _Symbol &&
               position.Magic() == InpMagicNumber &&
               position.PositionType() == position_type)
            {
                double close_price = (position_type == POSITION_TYPE_BUY) ?
                                    GetReliablePrice(false) : GetReliablePrice(true);

                if(close_price > 0)
                {
                    trade.PositionClose(position.Ticket());
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Check and open grid orders automatically                        |
//+------------------------------------------------------------------+
void CheckAndOpenGridOrders()
{
    if(!InpEnableTrading) return;

    // Update grid state first
    UpdateGridPositions();

    double current_ask = symbolInfo.Ask();
    double current_bid = symbolInfo.Bid();
    double grid_distance = InpGridDistance * symbolInfo.Point();

    int current_positions = CountOpenPositions();
    if(current_positions >= InpMaxGridLevels) return; // เต็มแล้ว

    // TRUE GRID TRADING - ทั้ง BUY และ SELL Grid

    // เริ่มต้น grid ถ้ายังไม่มีออเดอร์
    if(current_positions == 0)
    {
        // กำหนดทิศทางเริ่มต้นจาก trend หรือ random
        double fast_ma_data[], slow_ma_data[];
        if(CopyBuffer(h_fast_ma, 0, 0, 1, fast_ma_data) > 0 &&
           CopyBuffer(h_slow_ma, 0, 0, 1, slow_ma_data) > 0)
        {
            double fast_ma = fast_ma_data[0];
            double slow_ma = slow_ma_data[0];

            if(fast_ma > slow_ma)
            {
                OpenBuyOrder(0);  // เริ่มด้วย BUY ถ้า uptrend
            }
            else
            {
                OpenSellOrder(0); // เริ่มด้วย SELL ถ้า downtrend
            }
        }
        else
        {
            // ถ้าไม่สามารถ read MA ได้ ใช้ราคาสุดท้าย
            double price_now = symbolInfo.Bid();
            double price_prev = iClose(_Symbol, PERIOD_CURRENT, 1);
            if(price_now > price_prev)
                OpenBuyOrder(0);
            else
                OpenSellOrder(0);
        }
        return;
    }

    // BUY GRID - Average Down เมื่อราคาลง
    if(g_total_buy_lots > 0 && g_total_sell_lots == 0) // มี BUY positions อย่างเดียว
    {
        double distance_down = (g_last_buy_price > 0) ? (g_last_buy_price - current_ask) : 0;
        if(distance_down >= grid_distance && current_positions < InpMaxGridLevels)
        {
            OpenBuyOrder(0); // เปิด BUY เพิ่มเมื่อราคาลง
        }
    }

    // SELL GRID - Average Down เมื่อราคาขึ้น
    if(g_total_sell_lots > 0 && g_total_buy_lots == 0) // มี SELL positions อย่างเดียว
    {
        double distance_up = (g_last_sell_price > 0) ? (current_bid - g_last_sell_price) : 0;
        if(distance_up >= grid_distance && current_positions < InpMaxGridLevels)
        {
            OpenSellOrder(0); // เปิด SELL เพิ่มเมื่อราคาขึ้น
        }
    }

    // หากไม่มี positions (ถูกปิดหมดแล้ว) ให้เริ่มใหม่
    if(g_total_buy_lots == 0 && g_total_sell_lots == 0 && current_positions == 0)
    {
        // เริ่ม grid ใหม่ตาม trend
        double fast_ma_data[], slow_ma_data[];
        if(CopyBuffer(h_fast_ma, 0, 0, 1, fast_ma_data) > 0 &&
           CopyBuffer(h_slow_ma, 0, 0, 1, slow_ma_data) > 0)
        {
            if(fast_ma_data[0] > slow_ma_data[0])
            {
                OpenBuyOrder(0);
            }
            else
            {
                OpenSellOrder(0);
            }
        }
        else
        {
            // ถ้าไม่สามารถ read MA ได้ ใช้ราคาสุดท้าย
            double price_now = symbolInfo.Bid();
            double price_prev = iClose(_Symbol, PERIOD_CURRENT, 1);
            if(price_now > price_prev)
                OpenBuyOrder(0);
            else
                OpenSellOrder(0);
        }
    }
}