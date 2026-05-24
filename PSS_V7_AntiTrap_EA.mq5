//+------------------------------------------------------------------+
//|                                           PSS_V7_AntiTrap_EA.mq5 |
//|                        Professional Scalping System V7 Anti-Trap |
//|         Enhanced with Trap Detection & Whipsaw Protection        |
//+------------------------------------------------------------------+
#property copyright "PSS V7 Anti-Trap"
#property link      ""
#property version   "7.0"
#property description "Professional Scalping System with Anti-Trap Technology"
#property description "Features: Liquidity Sweep Detection, ATR Volatility Filter"
#property description "Entry Delay Confirmation, Multi-Timeframe Validation"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>

//+------------------------------------------------------------------+
//| ENUMS                                                             |
//+------------------------------------------------------------------+
enum ENUM_BOT_MODE
{
   BOT_SMART_MART = 1,    // Smart Martingale (Anti-Trap)
   BOT_CONSERVATIVE = 2,   // Conservative Mode (Low Risk)
   BOT_AGGRESSIVE = 3      // Aggressive Mode (High Risk)
};

enum ENUM_DIRECTION
{
   DIR_NONE = 0,
   DIR_BUY = 1,
   DIR_SELL = 2
};

enum ENUM_TRAP_STATUS
{
   TRAP_NONE = 0,         // No Trap Detected
   TRAP_POSSIBLE = 1,     // Possible Trap (Warning)
   TRAP_CONFIRMED = 2     // Confirmed Trap (Block Entry)
};

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - GENERAL                                        |
//+------------------------------------------------------------------+
input group "=== GENERAL SETTINGS ==="
input ENUM_BOT_MODE   InpBotMode = BOT_SMART_MART;    // Bot Mode
input double          InpBaseLot = 0.01;              // Base Lot Size
input int             InpSlippage = 30;               // Max Slippage (points)
input bool            InpShowPanel = true;            // Show Info Panel
input int             InpMagicNumber = 888888;        // Magic Number

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - ANTI-TRAP SYSTEM (NEW!)                        |
//+------------------------------------------------------------------+
input group "=== ANTI-TRAP SYSTEM (Core Protection) ==="
input bool            InpAntiTrapEnabled = true;      // Enable Anti-Trap System
input int             InpEntryDelayBars = 2;          // Entry Delay (bars after signal)
input int             InpConfirmationCandles = 3;     // Confirmation Candles Required
input double          InpMinBodyRatio = 0.4;          // Min Candle Body Ratio (0.3-0.6)
input bool            InpWaitForRetest = true;        // Wait for Level Retest
input int             InpRetestTolerance = 5;         // Retest Tolerance (pips)

input group "=== ATR VOLATILITY FILTER ==="
input bool            InpAtrFilterEnabled = true;     // Enable ATR Filter
input int             InpAtrPeriod = 14;              // ATR Period
input double          InpAtrMinMultiplier = 0.5;      // Min ATR Multiplier (avoid low vol)
input double          InpAtrMaxMultiplier = 3.0;      // Max ATR Multiplier (avoid high vol)
input int             InpAtrPercentile = 80;          // ATR Percentile Filter (0-100, 0=off)

input group "=== LIQUIDITY SWEEP DETECTION ==="
input bool            InpLiquiditySweepEnabled = true; // Enable Liquidity Sweep Detection
input int             InpSweepLookback = 20;           // Sweep Lookback (bars)
input double          InpSweepMinPips = 5.0;           // Min Sweep Size (pips)
input int             InpPostSweepDelay = 3;           // Delay After Sweep (bars)

input group "=== MULTI-TIMEFRAME CONFIRMATION ==="
input bool            InpMtfEnabled = true;           // Enable MTF Confirmation
input ENUM_TIMEFRAMES InpMtfHigher = PERIOD_H1;       // Higher Timeframe
input int             InpMtfAgreementScore = 2;       // Min MTF Agreement Score (1-3)

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - SMART MARTINGALE                               |
//+------------------------------------------------------------------+
input group "=== SMART MARTINGALE SETTINGS ==="
input double          InpMartMultiplier = 1.3;        // Lot Multiplier (reduced from 1.5)
input int             InpMartMaxLevel = 4;            // Max Levels (reduced from 5+)
input int             InpMartMinDistance = 50;        // Min Distance (pips) - INCREASED
input int             InpMartFallbackDist = 80;       // Fallback Distance (pips) - INCREASED
input double          InpMartTakeProfitUSD = 3.0;     // Take Profit ($ per 0.01 lot)
input double          InpMaxTotalLot = 0.3;           // Max Total Lot - REDUCED
input bool            InpAdaptiveDistance = true;     // Use ATR-Based Adaptive Distance

//+------------------------------------------------------------------+
//| INPUT PARAMETERS - RISK MANAGEMENT                                |
//+------------------------------------------------------------------+
input group "=== RISK MANAGEMENT ==="
input double          InpDailyProfitTarget = 50.0;    // Daily Profit Target ($)
input double          InpDailyLossLimit = 30.0;       // Daily Loss Limit ($)
input double          InpMaxDrawdownPct = 15.0;       // Max Drawdown % (reduced)
input double          InpEmergencyMarginPct = 50.0;   // Emergency Exit Margin % (higher safety)
input int             InpMaxConsecutiveLoss = 3;      // Max Consecutive Losses (stricter)
input bool            InpHardStopLoss = true;         // Use Hard Stop Loss
input int             InpHardStopPips = 100;          // Hard Stop Loss (pips)

input group "=== WHIPSAW PROTECTION ==="
input bool            InpWhipsawProtection = true;    // Enable Whipsaw Protection
input int             InpWhipsawCooldown = 5;         // Cooldown After Loss (minutes)
input int             InpMaxTradesPerHour = 4;        // Max Trades Per Hour
input double          InpMinProfitToAdd = 0.0;        // Min Profit Before Adding ($ or 0=allow loss)

input group "=== SESSION FILTER ==="
input bool            InpSessionFilter = true;        // Use Session Filter
input bool            InpAvoidAsian = true;           // Avoid Asian Session (low vol)
input bool            InpAvoidNewsHours = true;       // Avoid News Hours
input int             InpNewsAvoidBefore = 30;        // Avoid X mins Before News
input int             InpNewsAvoidAfter = 15;         // Avoid X mins After News

//+------------------------------------------------------------------+
//| STRUCTURES                                                        |
//+------------------------------------------------------------------+
struct TrapAnalysis
{
   ENUM_TRAP_STATUS status;
   string           reason;
   int              score;
   bool             liquiditySweep;
   bool             fakeBreakout;
   bool             volumeAnomaly;
   datetime         lastTrapTime;
};

struct MarketContext
{
   double           atr;
   double           atrPercentile;
   bool             isHighVolatility;
   bool             isLowVolatility;
   ENUM_DIRECTION   htfTrend;
   ENUM_DIRECTION   mtfTrend;
   ENUM_DIRECTION   ltfTrend;
   int              trendAlignment;
   double           spreadPips;
   bool             isTradingSession;
};

struct EntrySignal
{
   bool             valid;
   ENUM_DIRECTION   direction;
   int              score;
   string           reason;
   double           entryPrice;
   double           stopLoss;
   double           takeProfit;
   int              confirmationBars;
   datetime         signalTime;
};

struct BotStats
{
   int              totalPositions;
   double           totalLot;
   double           totalProfit;
   double           avgPrice;
   ENUM_DIRECTION   direction;
   int              currentLevel;
};

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
CTrade trade;
CPositionInfo posInfo;

// Daily tracking
double g_dailyProfit = 0;
double g_dailyStartBalance = 0;
double g_peakBalance = 0;
datetime g_lastResetDate = 0;

// Anti-Trap State
TrapAnalysis g_trapAnalysis;
MarketContext g_marketContext;
EntrySignal g_pendingSignal;
datetime g_lastTrapDetected = 0;
datetime g_lastLiquiditySweep = 0;
int g_sweepDirection = 0;  // 1=swept highs, -1=swept lows

// Whipsaw Protection
datetime g_lastLossTime = 0;
int g_tradesThisHour = 0;
datetime g_hourStart = 0;
int g_consecutiveLosses = 0;

// Direction tracking
ENUM_DIRECTION g_currentDirection = DIR_NONE;

// Indicator handles
int g_handleAtr = INVALID_HANDLE;
int g_handleAtrHTF = INVALID_HANDLE;
int g_handleEmaFast = INVALID_HANDLE;
int g_handleEmaSlow = INVALID_HANDLE;
int g_handleEmaHTF = INVALID_HANDLE;
int g_handleRsi = INVALID_HANDLE;
int g_handleAdx = INVALID_HANDLE;
int g_handleVolume = INVALID_HANDLE;

// ATR History for percentile
double g_atrHistory[];
int g_atrHistorySize = 100;

// Panel
string g_panelName = "PSS_V7_Panel";

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Validate symbol
   if(!SymbolSelect(_Symbol, true))
   {
      Print("ERROR: Failed to select symbol ", _Symbol);
      return INIT_FAILED;
   }

   // Setup trade
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   trade.SetTypeFilling(ORDER_FILLING_IOC);

   // Initialize indicators
   g_handleAtr = iATR(_Symbol, PERIOD_CURRENT, InpAtrPeriod);
   g_handleAtrHTF = iATR(_Symbol, InpMtfHigher, InpAtrPeriod);
   g_handleEmaFast = iMA(_Symbol, PERIOD_CURRENT, 8, 0, MODE_EMA, PRICE_CLOSE);
   g_handleEmaSlow = iMA(_Symbol, PERIOD_CURRENT, 21, 0, MODE_EMA, PRICE_CLOSE);
   g_handleEmaHTF = iMA(_Symbol, InpMtfHigher, 21, 0, MODE_EMA, PRICE_CLOSE);
   g_handleRsi = iRSI(_Symbol, PERIOD_CURRENT, 14, PRICE_CLOSE);
   g_handleAdx = iADX(_Symbol, PERIOD_CURRENT, 14);

   if(g_handleAtr == INVALID_HANDLE || g_handleEmaFast == INVALID_HANDLE)
   {
      Print("ERROR: Failed to create indicators");
      return INIT_FAILED;
   }

   // Initialize ATR history
   ArrayResize(g_atrHistory, g_atrHistorySize);
   ArrayInitialize(g_atrHistory, 0);

   // Initialize balances
   g_dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   g_peakBalance = g_dailyStartBalance;
   g_lastResetDate = TimeCurrent();

   // Initialize trap analysis
   g_trapAnalysis.status = TRAP_NONE;
   g_trapAnalysis.score = 0;

   // Create panel
   if(InpShowPanel)
      CreatePanel();

   Print("========================================");
   Print("PSS V7 Anti-Trap EA Initialized");
   Print("Mode: ", EnumToString(InpBotMode));
   Print("Anti-Trap: ", InpAntiTrapEnabled ? "ENABLED" : "DISABLED");
   Print("ATR Filter: ", InpAtrFilterEnabled ? "ENABLED" : "DISABLED");
   Print("Liquidity Sweep: ", InpLiquiditySweepEnabled ? "ENABLED" : "DISABLED");
   Print("MTF Confirm: ", InpMtfEnabled ? "ENABLED" : "DISABLED");
   Print("========================================");

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Release indicators
   if(g_handleAtr != INVALID_HANDLE) IndicatorRelease(g_handleAtr);
   if(g_handleAtrHTF != INVALID_HANDLE) IndicatorRelease(g_handleAtrHTF);
   if(g_handleEmaFast != INVALID_HANDLE) IndicatorRelease(g_handleEmaFast);
   if(g_handleEmaSlow != INVALID_HANDLE) IndicatorRelease(g_handleEmaSlow);
   if(g_handleEmaHTF != INVALID_HANDLE) IndicatorRelease(g_handleEmaHTF);
   if(g_handleRsi != INVALID_HANDLE) IndicatorRelease(g_handleRsi);
   if(g_handleAdx != INVALID_HANDLE) IndicatorRelease(g_handleAdx);

   // Delete panel
   ObjectsDeleteAll(0, g_panelName);

   Print("PSS V7 Anti-Trap EA Deinitialized");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check daily reset
   CheckDailyReset();

   // Update market context
   UpdateMarketContext();

   // Check daily limits
   UpdateDailyProfit();
   if(CheckDailyLimits())
      return;

   // Check whipsaw cooldown
   if(!CheckWhipsawCooldown())
      return;

   // Check hourly trade limit
   if(!CheckHourlyLimit())
      return;

   // Update on new bar
   static datetime lastBar = 0;
   datetime currentBar = iTime(_Symbol, PERIOD_CURRENT, 0);

   if(currentBar != lastBar)
   {
      lastBar = currentBar;

      // Update ATR history for percentile
      UpdateAtrHistory();

      // Detect traps
      if(InpAntiTrapEnabled)
         DetectTraps();

      // Detect liquidity sweeps
      if(InpLiquiditySweepEnabled)
         DetectLiquiditySweep();
   }

   // Run main bot logic
   switch(InpBotMode)
   {
      case BOT_SMART_MART:
         RunSmartMartingale();
         break;
      case BOT_CONSERVATIVE:
         RunConservativeMode();
         break;
      case BOT_AGGRESSIVE:
         RunAggressiveMode();
         break;
   }

   // Update panel
   if(InpShowPanel)
      UpdatePanel();
}

//+------------------------------------------------------------------+
//| Update Market Context                                             |
//+------------------------------------------------------------------+
void UpdateMarketContext()
{
   // Get ATR
   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(g_handleAtr, 0, 0, 5, atr) > 0)
      g_marketContext.atr = atr[0];

   // Calculate ATR percentile
   g_marketContext.atrPercentile = CalculateAtrPercentile(g_marketContext.atr);

   // Determine volatility state
   double avgAtr = CalculateAverageAtr();
   g_marketContext.isHighVolatility = (g_marketContext.atr > avgAtr * InpAtrMaxMultiplier);
   g_marketContext.isLowVolatility = (g_marketContext.atr < avgAtr * InpAtrMinMultiplier);

   // Get trends from multiple timeframes
   g_marketContext.ltfTrend = GetTrendDirection(PERIOD_CURRENT);
   g_marketContext.mtfTrend = GetTrendDirection(PERIOD_M15);
   g_marketContext.htfTrend = GetTrendDirection(InpMtfHigher);

   // Calculate trend alignment
   g_marketContext.trendAlignment = 0;
   if(g_marketContext.ltfTrend == g_marketContext.mtfTrend)
      g_marketContext.trendAlignment++;
   if(g_marketContext.mtfTrend == g_marketContext.htfTrend)
      g_marketContext.trendAlignment++;
   if(g_marketContext.ltfTrend == g_marketContext.htfTrend)
      g_marketContext.trendAlignment++;

   // Get spread
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   g_marketContext.spreadPips = (ask - bid) / PipsToPrice(1);

   // Check trading session
   g_marketContext.isTradingSession = IsTradingSession();
}

//+------------------------------------------------------------------+
//| Get Trend Direction                                               |
//+------------------------------------------------------------------+
ENUM_DIRECTION GetTrendDirection(ENUM_TIMEFRAMES tf)
{
   int emaFast = iMA(_Symbol, tf, 8, 0, MODE_EMA, PRICE_CLOSE);
   int emaSlow = iMA(_Symbol, tf, 21, 0, MODE_EMA, PRICE_CLOSE);

   if(emaFast == INVALID_HANDLE || emaSlow == INVALID_HANDLE)
      return DIR_NONE;

   double fast[], slow[];
   ArraySetAsSeries(fast, true);
   ArraySetAsSeries(slow, true);

   if(CopyBuffer(emaFast, 0, 0, 3, fast) <= 0) { IndicatorRelease(emaFast); IndicatorRelease(emaSlow); return DIR_NONE; }
   if(CopyBuffer(emaSlow, 0, 0, 3, slow) <= 0) { IndicatorRelease(emaFast); IndicatorRelease(emaSlow); return DIR_NONE; }

   IndicatorRelease(emaFast);
   IndicatorRelease(emaSlow);

   // Check consecutive alignment
   int bullCount = 0, bearCount = 0;
   for(int i = 0; i < 3; i++)
   {
      if(fast[i] > slow[i]) bullCount++;
      else bearCount++;
   }

   if(bullCount >= 2) return DIR_BUY;
   if(bearCount >= 2) return DIR_SELL;

   return DIR_NONE;
}

//+------------------------------------------------------------------+
//| TRAP DETECTION SYSTEM                                             |
//+------------------------------------------------------------------+
void DetectTraps()
{
   g_trapAnalysis.status = TRAP_NONE;
   g_trapAnalysis.score = 0;
   g_trapAnalysis.reason = "";
   g_trapAnalysis.fakeBreakout = false;
   g_trapAnalysis.volumeAnomaly = false;

   double high[], low[], close[], open[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(open, true);

   int bars = 30;
   if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high) <= 0) return;
   if(CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low) <= 0) return;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, bars, close) <= 0) return;
   if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, bars, open) <= 0) return;

   // === CHECK 1: Fake Breakout Pattern ===
   // Price breaks level but closes back inside
   double recentHigh = high[ArrayMaximum(high, 2, 20)];
   double recentLow = low[ArrayMinimum(low, 2, 20)];

   // Bullish fake breakout (bear trap)
   if(low[1] < recentLow && close[1] > recentLow && close[0] > close[1])
   {
      g_trapAnalysis.score += 2;
      g_trapAnalysis.reason += "BearTrap+";
      g_trapAnalysis.fakeBreakout = true;
   }

   // Bearish fake breakout (bull trap)
   if(high[1] > recentHigh && close[1] < recentHigh && close[0] < close[1])
   {
      g_trapAnalysis.score += 2;
      g_trapAnalysis.reason += "BullTrap+";
      g_trapAnalysis.fakeBreakout = true;
   }

   // === CHECK 2: Wick Rejection ===
   double body1 = MathAbs(close[1] - open[1]);
   double range1 = high[1] - low[1];
   double upperWick = high[1] - MathMax(close[1], open[1]);
   double lowerWick = MathMin(close[1], open[1]) - low[1];

   // Long upper wick after uptrend = potential trap
   if(upperWick > body1 * 2 && close[2] > close[3] && close[3] > close[4])
   {
      g_trapAnalysis.score += 2;
      g_trapAnalysis.reason += "WickRejHigh+";
   }

   // Long lower wick after downtrend = potential trap
   if(lowerWick > body1 * 2 && close[2] < close[3] && close[3] < close[4])
   {
      g_trapAnalysis.score += 2;
      g_trapAnalysis.reason += "WickRejLow+";
   }

   // === CHECK 3: Sudden Reversal ===
   double move1 = close[1] - close[2];
   double move2 = close[0] - close[1];

   if(MathAbs(move2) > MathAbs(move1) * 1.5 && move1 * move2 < 0)  // Opposite direction
   {
      g_trapAnalysis.score += 1;
      g_trapAnalysis.reason += "SuddenRev+";
   }

   // === CHECK 4: Candle Body Ratio (weak candles) ===
   if(range1 > 0 && body1 / range1 < InpMinBodyRatio)
   {
      g_trapAnalysis.score += 1;
      g_trapAnalysis.reason += "WeakBody+";
   }

   // === CHECK 5: Divergence with HTF ===
   ENUM_DIRECTION ltf = GetTrendDirection(PERIOD_CURRENT);
   ENUM_DIRECTION htf = GetTrendDirection(InpMtfHigher);

   if(ltf != DIR_NONE && htf != DIR_NONE && ltf != htf)
   {
      g_trapAnalysis.score += 2;
      g_trapAnalysis.reason += "TFDiverge+";
   }

   // === Determine Trap Status ===
   if(g_trapAnalysis.score >= 4)
   {
      g_trapAnalysis.status = TRAP_CONFIRMED;
      g_trapAnalysis.lastTrapTime = TimeCurrent();
      g_lastTrapDetected = TimeCurrent();
      Print("[TRAP DETECTED] Score: ", g_trapAnalysis.score, " Reason: ", g_trapAnalysis.reason);
   }
   else if(g_trapAnalysis.score >= 2)
   {
      g_trapAnalysis.status = TRAP_POSSIBLE;
   }
}

//+------------------------------------------------------------------+
//| LIQUIDITY SWEEP DETECTION                                         |
//+------------------------------------------------------------------+
void DetectLiquiditySweep()
{
   double high[], low[], close[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);

   int bars = InpSweepLookback + 5;
   if(CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high) <= 0) return;
   if(CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low) <= 0) return;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, bars, close) <= 0) return;

   // Find previous swing high/low
   double swingHigh = high[ArrayMaximum(high, 2, InpSweepLookback)];
   double swingLow = low[ArrayMinimum(low, 2, InpSweepLookback)];

   double sweepPips = InpSweepMinPips * PipsToPrice(1);

   // Check for liquidity sweep of highs (stop hunt)
   if(high[1] > swingHigh && close[1] < swingHigh - sweepPips)
   {
      g_lastLiquiditySweep = TimeCurrent();
      g_sweepDirection = 1;  // Swept highs = likely to go down
      g_trapAnalysis.liquiditySweep = true;
      Print("[LIQUIDITY SWEEP] Highs swept! Expecting reversal DOWN");
   }

   // Check for liquidity sweep of lows (stop hunt)
   if(low[1] < swingLow && close[1] > swingLow + sweepPips)
   {
      g_lastLiquiditySweep = TimeCurrent();
      g_sweepDirection = -1;  // Swept lows = likely to go up
      g_trapAnalysis.liquiditySweep = true;
      Print("[LIQUIDITY SWEEP] Lows swept! Expecting reversal UP");
   }
}

//+------------------------------------------------------------------+
//| Check if Entry is Safe (Anti-Trap Validation)                     |
//+------------------------------------------------------------------+
bool IsEntrySafe(ENUM_DIRECTION direction)
{
   // 1. Check trap status
   if(g_trapAnalysis.status == TRAP_CONFIRMED)
   {
      Print("[ANTI-TRAP] Entry BLOCKED - Trap confirmed (score: ", g_trapAnalysis.score, ")");
      return false;
   }

   // 2. Check post-trap cooldown
   if(g_lastTrapDetected > 0)
   {
      int barsSinceTrap = Bars(_Symbol, PERIOD_CURRENT, g_lastTrapDetected, TimeCurrent());
      if(barsSinceTrap < InpEntryDelayBars)
      {
         Print("[ANTI-TRAP] Entry DELAYED - ", InpEntryDelayBars - barsSinceTrap, " bars remaining after trap");
         return false;
      }
   }

   // 3. Check post-sweep delay
   if(g_lastLiquiditySweep > 0)
   {
      int barsSinceSweep = Bars(_Symbol, PERIOD_CURRENT, g_lastLiquiditySweep, TimeCurrent());
      if(barsSinceSweep < InpPostSweepDelay)
      {
         // Only allow entry in sweep direction
         if((direction == DIR_BUY && g_sweepDirection != -1) ||
            (direction == DIR_SELL && g_sweepDirection != 1))
         {
            Print("[ANTI-TRAP] Entry BLOCKED - Wrong direction after sweep");
            return false;
         }
      }
   }

   // 4. ATR Volatility Filter
   if(InpAtrFilterEnabled)
   {
      if(g_marketContext.isHighVolatility)
      {
         Print("[ATR FILTER] Entry BLOCKED - Volatility too high (ATR percentile: ",
               DoubleToString(g_marketContext.atrPercentile, 1), "%)");
         return false;
      }

      if(g_marketContext.isLowVolatility)
      {
         Print("[ATR FILTER] Entry BLOCKED - Volatility too low");
         return false;
      }

      // Check percentile filter
      if(InpAtrPercentile > 0 && g_marketContext.atrPercentile > InpAtrPercentile)
      {
         Print("[ATR FILTER] Entry BLOCKED - ATR in top ", 100 - InpAtrPercentile, "% (extreme)");
         return false;
      }
   }

   // 5. MTF Confirmation
   if(InpMtfEnabled)
   {
      if(g_marketContext.trendAlignment < InpMtfAgreementScore)
      {
         Print("[MTF FILTER] Entry BLOCKED - Trend alignment: ", g_marketContext.trendAlignment,
               "/", InpMtfAgreementScore, " required");
         return false;
      }

      // Direction must match HTF
      if(direction != g_marketContext.htfTrend && g_marketContext.htfTrend != DIR_NONE)
      {
         Print("[MTF FILTER] Entry BLOCKED - Against HTF trend");
         return false;
      }
   }

   // 6. Session Filter
   if(InpSessionFilter && !g_marketContext.isTradingSession)
   {
      Print("[SESSION FILTER] Entry BLOCKED - Outside trading session");
      return false;
   }

   // 7. Check Confirmation Candles
   if(!CheckConfirmationCandles(direction))
   {
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Check Confirmation Candles                                        |
//+------------------------------------------------------------------+
bool CheckConfirmationCandles(ENUM_DIRECTION direction)
{
   double close[], open[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(open, true);

   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, InpConfirmationCandles + 1, close) <= 0) return false;
   if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, InpConfirmationCandles + 1, open) <= 0) return false;

   int confirmCount = 0;

   for(int i = 1; i <= InpConfirmationCandles; i++)
   {
      bool bullish = close[i] > open[i];
      bool bearish = close[i] < open[i];

      if(direction == DIR_BUY && bullish) confirmCount++;
      if(direction == DIR_SELL && bearish) confirmCount++;
   }

   // Need majority confirmation
   if(confirmCount < (InpConfirmationCandles / 2) + 1)
   {
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| SMART MARTINGALE BOT                                              |
//+------------------------------------------------------------------+
void RunSmartMartingale()
{
   // Emergency checks
   if(!CheckEmergencyConditions())
      return;

   BotStats stats = GetBotStats();

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double price = (bid + ask) / 2;

   // === NO POSITIONS - LOOK FOR ENTRY ===
   if(stats.totalPositions == 0)
   {
      // Determine direction from HTF
      ENUM_DIRECTION direction = g_marketContext.htfTrend;

      if(direction == DIR_NONE)
      {
         // Fallback to LTF
         direction = g_marketContext.ltfTrend;
      }

      if(direction == DIR_NONE)
         return;

      // Anti-Trap Validation
      if(InpAntiTrapEnabled && !IsEntrySafe(direction))
         return;

      // Calculate entry with confirmation
      EntrySignal signal = CalculateEntrySignal(direction);

      if(signal.valid)
      {
         double lot = NormalizeLot(InpBaseLot);

         // Check lot limit
         if(GetTotalLot() + lot > InpMaxTotalLot)
            return;

         double sl = InpHardStopLoss ? signal.stopLoss : 0;

         string comment = "PSS7 L1 " + signal.reason;

         if(OpenOrderWithRetry(direction, lot, sl, 0, comment))
         {
            g_currentDirection = direction;
            Print("[SMART MART] L1 Opened: ", EnumToString(direction), " | ", signal.reason);
         }
      }
      return;
   }

   // === HAS POSITIONS ===
   ENUM_DIRECTION direction = stats.direction;

   // Calculate profit in pips
   double profitPips = 0;
   if(direction == DIR_BUY)
      profitPips = PriceToPips(price - stats.avgPrice);
   else
      profitPips = PriceToPips(stats.avgPrice - price);

   // Dynamic TP
   double targetProfit = InpMartTakeProfitUSD * (stats.totalLot / 0.01);
   targetProfit = MathMax(targetProfit, 1.0);

   // Check TP
   if(stats.totalProfit >= targetProfit)
   {
      if(CloseAllPositions())
      {
         UpdateTradeStats(stats.totalProfit);
         g_currentDirection = DIR_NONE;
         Print("[SMART MART] TP Hit! Profit: $", DoubleToString(stats.totalProfit, 2));
      }
      return;
   }

   // Check for adding positions
   if(stats.totalPositions < InpMartMaxLevel)
   {
      double lastPrice = GetLastEntryPrice();

      // Calculate distance - ADAPTIVE based on ATR
      double minDistance = InpMartMinDistance;
      if(InpAdaptiveDistance && g_marketContext.atr > 0)
      {
         double atrPips = g_marketContext.atr / PipsToPrice(1);
         minDistance = MathMax(minDistance, atrPips * 1.5);  // At least 1.5x ATR
      }

      double distancePips = MathAbs(PriceToPips(lastPrice - price));

      // Must be far enough
      if(distancePips < minDistance)
         return;

      // Must be in loss
      bool priceMovedAgainst = false;
      if(direction == DIR_BUY && price < lastPrice)
         priceMovedAgainst = true;
      else if(direction == DIR_SELL && price > lastPrice)
         priceMovedAgainst = true;

      if(!priceMovedAgainst)
         return;

      // Check minimum profit before adding (whipsaw protection)
      if(InpMinProfitToAdd > 0 && stats.totalProfit < -InpMinProfitToAdd)
      {
         // If too deep in loss, don't add blindly
         // Require extra confirmation
         if(g_trapAnalysis.status != TRAP_NONE)
         {
            Print("[WHIPSAW] Add BLOCKED - In loss and trap possible");
            return;
         }
      }

      // Anti-Trap check for adding
      if(InpAntiTrapEnabled)
      {
         // Stricter check for adding - require no trap signals at all
         if(g_trapAnalysis.status != TRAP_NONE)
         {
            Print("[ANTI-TRAP] Add BLOCKED - Trap status: ", EnumToString(g_trapAnalysis.status));
            return;
         }

         // Must have trend alignment
         if(g_marketContext.trendAlignment < 1)
         {
            Print("[ANTI-TRAP] Add BLOCKED - No trend alignment");
            return;
         }
      }

      // Calculate next lot
      int nextLevel = stats.totalPositions + 1;
      double nextLot = NormalizeLot(InpBaseLot * MathPow(InpMartMultiplier, nextLevel - 1));

      // Check lot limit
      if(GetTotalLot() + nextLot > InpMaxTotalLot)
      {
         Print("[SMART MART] Max lot limit reached");
         return;
      }

      // Calculate SL
      double sl = 0;
      if(InpHardStopLoss)
      {
         if(direction == DIR_BUY)
            sl = ask - PipsToPrice(InpHardStopPips);
         else
            sl = bid + PipsToPrice(InpHardStopPips);
      }

      string comment = "PSS7 L" + IntegerToString(nextLevel) + " " + IntegerToString((int)distancePips) + "p";

      if(OpenOrderWithRetry(direction, nextLot, sl, 0, comment))
      {
         Print("[SMART MART] L", nextLevel, " Added: ", DoubleToString(nextLot, 2), " lot @ ",
               DoubleToString(distancePips, 0), " pips");
      }
   }
}

//+------------------------------------------------------------------+
//| Calculate Entry Signal                                            |
//+------------------------------------------------------------------+
EntrySignal CalculateEntrySignal(ENUM_DIRECTION direction)
{
   EntrySignal signal;
   signal.valid = false;
   signal.direction = direction;
   signal.score = 0;
   signal.reason = "";

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   // Get indicator values
   double emaFast[], emaSlow[], rsi[], adx[];
   ArraySetAsSeries(emaFast, true);
   ArraySetAsSeries(emaSlow, true);
   ArraySetAsSeries(rsi, true);
   ArraySetAsSeries(adx, true);

   if(CopyBuffer(g_handleEmaFast, 0, 0, 5, emaFast) <= 0) return signal;
   if(CopyBuffer(g_handleEmaSlow, 0, 0, 5, emaSlow) <= 0) return signal;
   if(CopyBuffer(g_handleRsi, 0, 0, 5, rsi) <= 0) return signal;
   if(CopyBuffer(g_handleAdx, 0, 0, 5, adx) <= 0) return signal;

   double close[];
   ArraySetAsSeries(close, true);
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 5, close) <= 0) return signal;

   // === SCORING SYSTEM ===

   // 1. EMA Alignment
   if(direction == DIR_BUY && emaFast[0] > emaSlow[0] && close[0] > emaFast[0])
   {
      signal.score += 2;
      signal.reason += "EMA+";
   }
   else if(direction == DIR_SELL && emaFast[0] < emaSlow[0] && close[0] < emaFast[0])
   {
      signal.score += 2;
      signal.reason += "EMA+";
   }

   // 2. RSI Confirmation
   if(direction == DIR_BUY && rsi[0] > 50 && rsi[0] < 70)
   {
      signal.score += 1;
      signal.reason += "RSI+";
   }
   else if(direction == DIR_SELL && rsi[0] < 50 && rsi[0] > 30)
   {
      signal.score += 1;
      signal.reason += "RSI+";
   }

   // 3. ADX Strength
   if(adx[0] > 20)
   {
      signal.score += 1;
      signal.reason += "ADX+";
   }

   // 4. Post-Sweep Entry (premium)
   if(g_lastLiquiditySweep > 0)
   {
      int barsSinceSweep = Bars(_Symbol, PERIOD_CURRENT, g_lastLiquiditySweep, TimeCurrent());
      if(barsSinceSweep >= InpPostSweepDelay && barsSinceSweep <= InpPostSweepDelay + 3)
      {
         if((direction == DIR_BUY && g_sweepDirection == -1) ||
            (direction == DIR_SELL && g_sweepDirection == 1))
         {
            signal.score += 3;
            signal.reason += "SWEEP+";
         }
      }
   }

   // 5. MTF Alignment Bonus
   if(g_marketContext.trendAlignment >= 2)
   {
      signal.score += 1;
      signal.reason += "MTF+";
   }

   // === VALIDATE ===
   int minScore = (InpBotMode == BOT_CONSERVATIVE) ? 4 : 3;

   if(signal.score >= minScore)
   {
      signal.valid = true;
      signal.signalTime = TimeCurrent();

      // Calculate SL/TP
      double atrSL = g_marketContext.atr * 2;
      if(atrSL == 0) atrSL = PipsToPrice(InpHardStopPips);

      if(direction == DIR_BUY)
      {
         signal.entryPrice = ask;
         signal.stopLoss = ask - atrSL;
         signal.takeProfit = ask + atrSL * 1.5;
      }
      else
      {
         signal.entryPrice = bid;
         signal.stopLoss = bid + atrSL;
         signal.takeProfit = bid - atrSL * 1.5;
      }
   }

   return signal;
}

//+------------------------------------------------------------------+
//| Conservative Mode                                                 |
//+------------------------------------------------------------------+
void RunConservativeMode()
{
   // Similar to Smart Mart but with:
   // - Max 2 levels
   // - Larger distances
   // - Stricter filters

   BotStats stats = GetBotStats();

   if(stats.totalPositions >= 2)
   {
      // In conservative mode, just manage existing positions
      CheckTakeProfitConservative(stats);
      return;
   }

   // Very strict entry requirements
   if(g_trapAnalysis.status != TRAP_NONE)
      return;

   if(g_marketContext.trendAlignment < 3)  // All timeframes must agree
      return;

   if(g_marketContext.isHighVolatility || g_marketContext.isLowVolatility)
      return;

   ENUM_DIRECTION direction = g_marketContext.htfTrend;
   if(direction == DIR_NONE)
      return;

   EntrySignal signal = CalculateEntrySignal(direction);

   if(signal.valid && signal.score >= 5)  // Higher score required
   {
      double lot = NormalizeLot(InpBaseLot);

      if(OpenOrderWithRetry(direction, lot, signal.stopLoss, signal.takeProfit, "PSS7-CON"))
      {
         g_currentDirection = direction;
      }
   }
}

//+------------------------------------------------------------------+
//| Check TP for Conservative Mode                                    |
//+------------------------------------------------------------------+
void CheckTakeProfitConservative(BotStats &stats)
{
   double targetProfit = 2.0 * (stats.totalLot / 0.01);  // $2 per 0.01 lot

   if(stats.totalProfit >= targetProfit)
   {
      if(CloseAllPositions())
      {
         UpdateTradeStats(stats.totalProfit);
         g_currentDirection = DIR_NONE;
      }
   }
}

//+------------------------------------------------------------------+
//| Aggressive Mode                                                   |
//+------------------------------------------------------------------+
void RunAggressiveMode()
{
   // Higher risk, faster entries
   // But still respects anti-trap

   BotStats stats = GetBotStats();

   if(stats.totalPositions == 0)
   {
      ENUM_DIRECTION direction = g_marketContext.ltfTrend;

      if(direction == DIR_NONE)
         direction = g_marketContext.mtfTrend;

      if(direction == DIR_NONE)
         return;

      // Still check for confirmed traps
      if(g_trapAnalysis.status == TRAP_CONFIRMED)
         return;

      EntrySignal signal = CalculateEntrySignal(direction);

      if(signal.valid && signal.score >= 2)  // Lower score OK
      {
         double lot = NormalizeLot(InpBaseLot * 1.5);  // Larger lot

         if(GetTotalLot() + lot <= InpMaxTotalLot)
         {
            if(OpenOrderWithRetry(direction, lot, signal.stopLoss, 0, "PSS7-AGG"))
            {
               g_currentDirection = direction;
            }
         }
      }
   }
   else
   {
      // Aggressive TP
      double targetProfit = InpMartTakeProfitUSD * 0.5 * (stats.totalLot / 0.01);  // 50% TP

      if(stats.totalProfit >= targetProfit)
      {
         if(CloseAllPositions())
         {
            UpdateTradeStats(stats.totalProfit);
            g_currentDirection = DIR_NONE;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| EMERGENCY CONDITION CHECKS                                        |
//+------------------------------------------------------------------+
bool CheckEmergencyConditions()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double margin = AccountInfoDouble(ACCOUNT_MARGIN);

   // 1. Margin Level Check
   if(margin > 0)
   {
      double marginLevel = (equity / margin) * 100.0;

      if(marginLevel < InpEmergencyMarginPct)
      {
         Print("[EMERGENCY] Margin level ", DoubleToString(marginLevel, 1), "% < ",
               DoubleToString(InpEmergencyMarginPct, 0), "% - Closing all!");
         CloseAllPositions();
         return false;
      }
   }

   // 2. Drawdown Check
   double drawdown = 0;
   if(g_peakBalance > 0)
      drawdown = ((g_peakBalance - equity) / g_peakBalance) * 100.0;

   if(drawdown >= InpMaxDrawdownPct)
   {
      Print("[EMERGENCY] Drawdown ", DoubleToString(drawdown, 1), "% >= ",
            DoubleToString(InpMaxDrawdownPct, 0), "% - Closing all!");
      CloseAllPositions();
      return false;
   }

   // 3. Consecutive Loss Check
   if(g_consecutiveLosses >= InpMaxConsecutiveLoss)
   {
      Print("[EMERGENCY] ", g_consecutiveLosses, " consecutive losses - Pausing");
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| WHIPSAW PROTECTION                                                |
//+------------------------------------------------------------------+
bool CheckWhipsawCooldown()
{
   if(!InpWhipsawProtection)
      return true;

   if(g_lastLossTime > 0)
   {
      int minutesSinceLoss = (int)((TimeCurrent() - g_lastLossTime) / 60);

      if(minutesSinceLoss < InpWhipsawCooldown)
      {
         return false;  // Still in cooldown
      }
   }

   return true;
}

bool CheckHourlyLimit()
{
   if(InpMaxTradesPerHour <= 0)
      return true;

   MqlDateTime now;
   TimeToStruct(TimeCurrent(), now);

   MqlDateTime hourStartTime;
   TimeToStruct(g_hourStart, hourStartTime);

   // Reset if new hour
   if(now.hour != hourStartTime.hour || now.day != hourStartTime.day)
   {
      g_hourStart = TimeCurrent();
      g_tradesThisHour = 0;
   }

   return (g_tradesThisHour < InpMaxTradesPerHour);
}

//+------------------------------------------------------------------+
//| UTILITY FUNCTIONS                                                 |
//+------------------------------------------------------------------+
double PipsToPrice(int pips)
{
   return pips * _Point * 10;
}

double PipsToPrice(double pips)
{
   return pips * _Point * 10;
}

double PriceToPips(double priceDistance)
{
   return priceDistance / (_Point * 10);
}

double NormalizeLot(double lot)
{
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lot = MathFloor(lot / lotStep) * lotStep;
   lot = MathMax(minLot, MathMin(maxLot, lot));

   return NormalizeDouble(lot, 2);
}

double GetTotalLot()
{
   double totalLot = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
            totalLot += posInfo.Volume();
      }
   }

   return totalLot;
}

BotStats GetBotStats()
{
   BotStats stats;
   stats.totalPositions = 0;
   stats.totalLot = 0;
   stats.totalProfit = 0;
   stats.avgPrice = 0;
   stats.direction = DIR_NONE;
   stats.currentLevel = 0;

   double totalValue = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            stats.totalPositions++;
            stats.totalLot += posInfo.Volume();
            stats.totalProfit += posInfo.Profit();
            totalValue += posInfo.PriceOpen() * posInfo.Volume();

            if(posInfo.PositionType() == POSITION_TYPE_BUY)
               stats.direction = DIR_BUY;
            else
               stats.direction = DIR_SELL;
         }
      }
   }

   if(stats.totalLot > 0)
      stats.avgPrice = totalValue / stats.totalLot;

   stats.currentLevel = stats.totalPositions;

   return stats;
}

double GetLastEntryPrice()
{
   double lastPrice = 0;
   datetime lastTime = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            if(posInfo.Time() > lastTime)
            {
               lastTime = posInfo.Time();
               lastPrice = posInfo.PriceOpen();
            }
         }
      }
   }

   return lastPrice;
}

//+------------------------------------------------------------------+
//| Open Order With Retry                                             |
//+------------------------------------------------------------------+
bool OpenOrderWithRetry(ENUM_DIRECTION direction, double lot, double sl, double tp, string comment)
{
   // Increment trade counter
   g_tradesThisHour++;

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   for(int attempt = 1; attempt <= 3; attempt++)
   {
      bool success = false;

      if(direction == DIR_BUY)
         success = trade.Buy(lot, _Symbol, ask, sl, tp, comment);
      else
         success = trade.Sell(lot, _Symbol, bid, sl, tp, comment);

      if(success)
      {
         Print("Order opened: ", comment, " Lot: ", DoubleToString(lot, 2));
         return true;
      }

      Print("Order attempt ", attempt, " failed: ", trade.ResultRetcode());
      Sleep(500);
   }

   return false;
}

//+------------------------------------------------------------------+
//| Close All Positions                                               |
//+------------------------------------------------------------------+
bool CloseAllPositions()
{
   int closed = 0;
   int failed = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
         {
            if(trade.PositionClose(posInfo.Ticket()))
               closed++;
            else
               failed++;
         }
      }
   }

   Print("Closed ", closed, " positions, Failed: ", failed);
   return (failed == 0);
}

//+------------------------------------------------------------------+
//| ATR Functions                                                     |
//+------------------------------------------------------------------+
void UpdateAtrHistory()
{
   double atr[];
   ArraySetAsSeries(atr, true);

   if(CopyBuffer(g_handleAtr, 0, 0, 1, atr) <= 0)
      return;

   // Shift array
   for(int i = g_atrHistorySize - 1; i > 0; i--)
      g_atrHistory[i] = g_atrHistory[i-1];

   g_atrHistory[0] = atr[0];
}

double CalculateAtrPercentile(double currentAtr)
{
   int countBelow = 0;
   int total = 0;

   for(int i = 0; i < g_atrHistorySize; i++)
   {
      if(g_atrHistory[i] > 0)
      {
         total++;
         if(g_atrHistory[i] < currentAtr)
            countBelow++;
      }
   }

   if(total == 0) return 50.0;

   return (double)countBelow / (double)total * 100.0;
}

double CalculateAverageAtr()
{
   double sum = 0;
   int count = 0;

   for(int i = 0; i < g_atrHistorySize; i++)
   {
      if(g_atrHistory[i] > 0)
      {
         sum += g_atrHistory[i];
         count++;
      }
   }

   if(count == 0) return g_marketContext.atr;

   return sum / count;
}

//+------------------------------------------------------------------+
//| Session Check                                                     |
//+------------------------------------------------------------------+
bool IsTradingSession()
{
   MqlDateTime now;
   TimeToStruct(TimeCurrent(), now);
   int hour = now.hour;

   // Avoid Asian session if enabled
   if(InpAvoidAsian && hour >= 0 && hour < 7)
      return false;

   // London & NY session (best for XAU)
   if(hour >= 7 && hour < 20)
      return true;

   return false;
}

//+------------------------------------------------------------------+
//| Daily Management                                                  |
//+------------------------------------------------------------------+
void CheckDailyReset()
{
   MqlDateTime now, lastReset;
   TimeToStruct(TimeCurrent(), now);
   TimeToStruct(g_lastResetDate, lastReset);

   if(now.day != lastReset.day)
   {
      g_dailyProfit = 0;
      g_dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      g_peakBalance = g_dailyStartBalance;
      g_lastResetDate = TimeCurrent();
      g_consecutiveLosses = 0;
      g_tradesThisHour = 0;
      g_currentDirection = DIR_NONE;

      // Reset trap detection
      g_lastTrapDetected = 0;
      g_lastLiquiditySweep = 0;

      Print("[NEW DAY] Reset complete");
   }
}

void UpdateDailyProfit()
{
   g_dailyProfit = AccountInfoDouble(ACCOUNT_BALANCE) - g_dailyStartBalance;

   // Add floating P&L
   double floating = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == InpMagicNumber)
            floating += posInfo.Profit();
      }
   }
   g_dailyProfit += floating;

   // Update peak balance
   double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(currentBalance > g_peakBalance)
      g_peakBalance = currentBalance;
}

bool CheckDailyLimits()
{
   if(g_dailyProfit >= InpDailyProfitTarget)
   {
      Comment("Daily profit target reached: $", DoubleToString(g_dailyProfit, 2));
      return true;
   }

   if(g_dailyProfit <= -InpDailyLossLimit)
   {
      Comment("Daily loss limit reached: $", DoubleToString(g_dailyProfit, 2));
      return true;
   }

   return false;
}

void UpdateTradeStats(double profit)
{
   if(profit > 0)
   {
      g_consecutiveLosses = 0;
   }
   else if(profit < 0)
   {
      g_consecutiveLosses++;
      g_lastLossTime = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| Panel Functions                                                   |
//+------------------------------------------------------------------+
void CreatePanel()
{
   int x = 10, y = 30;
   int width = 280, height = 350;

   ObjectCreate(0, g_panelName + "_BG", OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, g_panelName + "_BG", OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, g_panelName + "_BG", OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, g_panelName + "_BG", OBJPROP_XSIZE, width);
   ObjectSetInteger(0, g_panelName + "_BG", OBJPROP_YSIZE, height);
   ObjectSetInteger(0, g_panelName + "_BG", OBJPROP_BGCOLOR, clrBlack);
   ObjectSetInteger(0, g_panelName + "_BG", OBJPROP_BORDER_COLOR, clrGold);
   ObjectSetInteger(0, g_panelName + "_BG", OBJPROP_CORNER, CORNER_LEFT_UPPER);
}

void UpdatePanel()
{
   BotStats stats = GetBotStats();

   string info = "";
   info += "=== PSS V7 ANTI-TRAP ===\n";
   info += "Mode: " + EnumToString(InpBotMode) + "\n";
   info += "------------------------\n";

   // Trap Status
   string trapStatus = "NONE";
   color trapColor = clrGreen;
   if(g_trapAnalysis.status == TRAP_POSSIBLE) { trapStatus = "POSSIBLE"; trapColor = clrYellow; }
   if(g_trapAnalysis.status == TRAP_CONFIRMED) { trapStatus = "BLOCKED"; trapColor = clrRed; }
   info += "Trap: " + trapStatus + "\n";

   // Market Context
   info += "ATR: " + DoubleToString(g_marketContext.atr / _Point, 0) + " pts (" +
           DoubleToString(g_marketContext.atrPercentile, 0) + "%)\n";
   info += "Trend Align: " + IntegerToString(g_marketContext.trendAlignment) + "/3\n";
   info += "------------------------\n";

   // Positions
   info += "Positions: " + IntegerToString(stats.totalPositions) + "/" + IntegerToString(InpMartMaxLevel) + "\n";
   info += "Total Lot: " + DoubleToString(stats.totalLot, 2) + "/" + DoubleToString(InpMaxTotalLot, 2) + "\n";
   info += "Profit: $" + DoubleToString(stats.totalProfit, 2) + "\n";
   info += "Direction: " + EnumToString(stats.direction) + "\n";
   info += "------------------------\n";

   // Daily
   info += "Daily P/L: $" + DoubleToString(g_dailyProfit, 2) + "\n";
   info += "Consec Loss: " + IntegerToString(g_consecutiveLosses) + "/" + IntegerToString(InpMaxConsecutiveLoss) + "\n";
   info += "Trades/Hour: " + IntegerToString(g_tradesThisHour) + "/" + IntegerToString(InpMaxTradesPerHour) + "\n";

   Comment(info);
}
//+------------------------------------------------------------------+
