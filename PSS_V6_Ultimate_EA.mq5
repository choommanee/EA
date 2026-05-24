//+------------------------------------------------------------------+
//|                                          PSS_V6_Ultimate_EA.mq5   |
//|                        Professional Scalping System V6 Ultimate   |
//|                           4-in-1 Trading Bot (SMC + Multi-Strategy)|
//+------------------------------------------------------------------+
#property copyright "PSS V6 Ultimate"
#property link      ""
#property version   "6.0"
#property description "Professional Scalping System with SMC Analysis"
#property description "Includes: Martingale, SMC Trend, Grid, Momentum Bots"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>

//+------------------------------------------------------------------+
//| ENUMS                                                             |
//+------------------------------------------------------------------+
enum ENUM_BOT_MODE
{
   BOT_MANUAL = 0,        // Manual (No Bot)
   BOT_MARTINGALE = 1     // Martingale (SMC Entry)
};

enum ENUM_DIRECTION
{
   DIR_NONE = 0,
   DIR_BUY = 1,
   DIR_SELL = 2
};

enum ENUM_FILLING_CHECK
{
   FILLING_AUTO = 0,      // Auto Detect
   FILLING_FOK = 1,       // Fill or Kill
   FILLING_IOC = 2,       // Immediate or Cancel
   FILLING_RETURN = 3     // Return (Partial Fill OK)
};

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                  |
//+------------------------------------------------------------------+
input group "=== GENERAL SETTINGS ==="
input ENUM_BOT_MODE   InpBotMode = BOT_MARTINGALE;  // Bot Mode
input double          InpBaseLot = 0.01;            // Base Lot Size
input int             InpSlippage = 50;             // Max Slippage (points)
input bool            InpShowPanel = true;          // Show Info Panel
input ENUM_FILLING_CHECK InpFillingMode = FILLING_AUTO; // Order Filling Mode
input int             InpMaxRetries = 3;            // Max Order Retries
input int             InpRetryDelayMs = 500;        // Retry Delay (ms)

input group "=== RISK MANAGEMENT ==="
input double          InpDailyProfitTarget = 100.0; // Daily Profit Target ($)
input double          InpDailyLossLimit = 50.0;     // Daily Loss Limit ($)
input double          InpMaxTotalLot = 0.5;         // Max Total Lot (All Positions)
input bool            InpUseRiskPercent = false;    // Use Risk % Instead of Fixed Lot
input double          InpRiskPercent = 1.0;         // Risk Per Trade (%)
input int             InpMaxConsecutiveLoss = 5;    // Max Consecutive Losses (0=off)
input double          InpMaxDrawdownPercent = 20.0; // Max Drawdown % (0=off)

input group "=== MARTINGALE BOT (Magic: 777777) ==="
input double          InpMartMultiplier = 1.5;      // Lot Multiplier
input int             InpMartMaxLevel = 5;          // Max Levels
input int             InpMartMinDistance = 20;      // Min Distance Before Add (pips)
input int             InpMartFallbackDist = 40;     // Fallback Distance (pips)
input double          InpMartTakeProfitUSD = 5.0;   // Take Profit ($)
input bool            InpMartTPScaling = false;     // Scale TP with Lot Size (true = $ per 0.01 lot)
input double          InpMartMinProfitUSD = 1.0;    // Min Profit to Close ($)
input bool            InpMartUseAdaptiveBasketTP = true; // Use AvgPrice + ATR/Pip Basket TP
input double          InpMartTPBasePips = 30.0;     // Base Basket TP from AvgPrice (pips)
input double          InpMartTPAtrMultiplier = 0.35; // ATR part for Basket TP
input double          InpMartTPMinPips = 8.0;       // Minimum Basket TP from AvgPrice (pips)
input double          InpMartTPMaxPips = 80.0;      // Maximum Basket TP from AvgPrice (pips)
input double          InpMartProfitPer001Lot = 1.0; // Minimum $ profit per 0.01 total lot
input bool            InpMartUseRecoveryProfitTP = true; // Scale TP by basket max floating DD
input int             InpMartRecoveryTPMinLevel = 4; // Start DD-scaled TP from level
input double          InpMartRecoveryTPPercent = 15.0; // Target % of basket max floating DD
input double          InpMartRecoveryTPMaxUSD = 0.0; // Max DD-scaled TP (0=off)
input bool            InpMartAutoDirection = true;  // Auto Direction (AI)
input bool            InpMartUseATR = true;         // Use ATR Dynamic Grid
input double          InpMartAtrMultiplier = 1.5;   // ATR Multiplier for Grid Spacing

input group "=== MARTINGALE SMC/SMS PRECISION ==="
input bool            InpMartStrictSmcEntry = false; // Require CHoCH+BOS+LQ+OB for L1/Add
input bool            InpMartAllowFallbackAdd = false; // Allow distance-only fallback add
input bool            InpMartStopAddOnOppositeBos = false; // Stop add on opposite BOS/CHoCH
input int             InpMartStructureLookback = 40; // Structure Lookback (bars)
input int             InpMartLqSweepLookback = 3;   // LQ Sweep Lookback (closed bars)
input int             InpMartObBufferPips = 10;     // OB Entry Buffer (pips)
input bool            InpMartUseDailyHLGuard = false; // Block BUY near daily high / SELL near daily low
input int             InpMartDailyHLBufferPips = 20; // Daily H/L Guard Buffer (pips)
input int             InpMartCooldownMinutes = 5;    // Cooldown between adds (minutes)

input group "=== SOLUTION 1: SAFETY FEATURES (Web Research) ==="
input bool            InpBreakevenEnabled = false;  // Enable Breakeven SL
input int             InpBreakevenTrigger = 17;     // Breakeven Trigger (pips, 50% of TP)
input int             InpBreakevenOffset = 2;       // Breakeven Offset (pips)
input bool            InpPartialCloseEnabled = false; // Enable Partial Close
input int             InpPartialClosePips = 15;     // Partial Close Trigger (pips)
input int             InpPartialClosePct = 50;      // Partial Close % (of positions)
input bool            InpTrendFilterEnabled = false; // Enable Trend Filter (Anti-Trend Trading)
input bool            InpTrendRevExitEnabled = false; // Enable Trend Reversal Exit
input int             InpTrendRevCandles = 5;       // Trend Reversal Candles (consecutive)
input double          InpTrendRevLossPct = 20.0;    // Trend Reversal Loss % (of balance)
input bool            InpEmergencyExitEnabled = false; // Enable Emergency Exit
input double          InpEmergencyMarginPct = 30.0; // Emergency Margin Level % (exit before stop out)

input group "=== DIRECTION FILTER (EMA & RSI) ==="
input ENUM_TIMEFRAMES InpHtfPeriod = PERIOD_H1;     // HTF Period for Trend Filter
input bool            InpUseHtfFilter = true;        // Use Strict HTF Trend Filter
input bool            InpUseMajorTrendGuard = true;  // Use major trend as L1 direction bias
input ENUM_TIMEFRAMES InpMajorTrendPeriod = PERIOD_H4; // Major Trend Period
input int             InpMajorTrendFastEma = 50;     // Major Trend Fast EMA
input int             InpMajorTrendSlowEma = 200;    // Major Trend Slow EMA
input int             InpMajorTrendSlopeBars = 12;   // Major Trend Slope Bars
input int             InpMomEmaFast = 8;            // EMA Fast Period
input int             InpMomEmaSlow = 21;           // EMA Slow Period
input int             InpMomRsiPeriod = 14;         // RSI Period

input group "=== SMC ANALYSIS SETTINGS ==="
input int             InpSwingLookback = 10;        // Swing Point Lookback
input int             InpObLookback = 20;           // Order Block Lookback
input int             InpLqLookback = 15;           // Liquidity Zone Lookback
input int             InpBosLookback = 50;          // BOS/CHoCH Lookback
input int             InpMinSmcScore = 3;           // Min SMC Score for Entry

input group "=== SESSION FILTER ==="
input bool            InpUseSessionFilter = true;   // Use Session Filter
input int             InpAsianStart = 0;            // Asian Session Start (Hour)
input int             InpAsianEnd = 8;              // Asian Session End (Hour)
input int             InpLondonStart = 8;           // London Session Start (Hour)
input int             InpLondonEnd = 16;            // London Session End (Hour)
input int             InpNYStart = 13;              // NY Session Start (Hour)
input int             InpNYEnd = 21;                // NY Session End (Hour)

input group "=== NEWS FILTER ==="
input bool            InpUseNewsFilter = false;     // Use Manual News Filter
input string          InpNewsTimes = "";            // Server times: 2026.04.30 12:30;2026.05.01 12:30
input int             InpNewsBlockBeforeMin = 120;  // Block before news (minutes)
input int             InpNewsBlockAfterMin = 240;   // Block after news (minutes)
input bool            InpNewsBlockNewEntry = true;  // Block new baskets during news
input bool            InpNewsBlockAddOrders = true; // Block martingale adds during news

//+------------------------------------------------------------------+
//| MAGIC NUMBERS                                                     |
//+------------------------------------------------------------------+
#define MAGIC_MARTINGALE  777777

//+------------------------------------------------------------------+
//| STRUCTURES                                                        |
//+------------------------------------------------------------------+
struct SwingPoint
{
   int      index;
   double   price;
   bool     isHigh;
   string   label;  // HH, HL, LH, LL
};

struct StructureBreak
{
   int      index;
   double   price;
   bool     isBullish;
   string   label;  // BOS or CHoCH
   datetime time;
};

struct OrderBlock
{
   double   high;
   double   low;
   int      startIndex;
   bool     isBullish;
   bool     mitigated;
   datetime time;
};

struct LiquidityZone
{
   double   price;
   int      index;
   bool     isHigh;
   bool     swept;
   datetime time;
};

struct FairValueGap
{
   double   high;
   double   low;
   int      index;
   bool     isBullish;
   datetime time;
};

struct SmcSignal
{
   bool     valid;
   int      score;
   string   reason;
   string   waiting;
};

struct BotStats
{
   int      totalPositions;
   double   totalLot;
   double   totalProfit;
   double   avgPrice;
   ENUM_DIRECTION direction;
   int      maxLevelReached;
};

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+
CTrade trade;
CPositionInfo posInfo;

// Daily tracking
double g_dailyProfit = 0;
double g_dailyStartBalance = 0;
double g_monthlyProfit = 0;
double g_monthlyClosedProfit = 0;
double g_monthlyStartBalance = 0;
double g_peakBalance = 0;
double g_maxCurrentDrawdown = 0;
datetime g_lastResetDate = 0;
datetime g_lastMonthResetDate = 0;

// Bot state
ENUM_DIRECTION g_martDirection = DIR_NONE;

// Solution 1: Safety Features State
bool g_breakevenMoved = false;
bool g_partialClosed = false;
double g_highestProfitPips = 0;

// Filling mode
ENUM_ORDER_TYPE_FILLING g_fillingMode = ORDER_FILLING_IOC;

// Loss tracking
int g_consecutiveLosses = 0;
int g_totalTrades = 0;
int g_winTrades = 0;
int g_lossTrades = 0;

// Last error tracking
string g_lastError = "";
datetime g_lastErrorTime = 0;
datetime g_lastTPDebugTime = 0;
double g_calcTPPrice = 0;
double g_calcTargetProfit = 0;
double g_basketMaxFloatingLoss = 0;
bool g_tpPending = false;
string g_tradeStatus = "INIT";

// SMC Data
SwingPoint g_swings[];
StructureBreak g_breaks[];
OrderBlock g_orderBlocks[];
LiquidityZone g_liquidityZones[];
FairValueGap g_fvgs[];

// Indicator handles
int g_handleEmaFast = INVALID_HANDLE;
int g_handleEmaSlow = INVALID_HANDLE;
int g_handleRsi = INVALID_HANDLE;
int g_handleAtr = INVALID_HANDLE;
datetime g_lastMartAddTime = 0;

// Panel
string g_panelName = "PSS_Panel";

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   // Ensure symbol is selected and visible
   if(!SymbolSelect(_Symbol, true))
   {
      Print("ERROR: Failed to select symbol ", _Symbol);
      return INIT_FAILED;
   }

   // Verify trading is allowed
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
   {
      Print("WARNING: Trading is not allowed in terminal");
   }

   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
   {
      Print("WARNING: Trading is not allowed for this EA");
   }

   // Set trade parameters
   trade.SetExpertMagicNumber(GetMagicNumber());
   trade.SetDeviationInPoints(InpSlippage);

   // Auto detect filling mode
   if(!SetupFillingMode())
   {
      Print("ERROR: Could not setup filling mode");
      return INIT_FAILED;
   }

   // Verify minimum requirements
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   if(InpBaseLot < minLot)
   {
      Print("WARNING: Base lot ", InpBaseLot, " is below minimum ", minLot);
   }

    // Initialize indicators
    g_handleEmaFast = iMA(_Symbol, InpHtfPeriod, InpMomEmaFast, 0, MODE_EMA, PRICE_CLOSE);
    g_handleEmaSlow = iMA(_Symbol, InpHtfPeriod, InpMomEmaSlow, 0, MODE_EMA, PRICE_CLOSE);
    g_handleRsi = iRSI(_Symbol, InpHtfPeriod, InpMomRsiPeriod, PRICE_CLOSE);
    g_handleAtr = iATR(_Symbol, PERIOD_CURRENT, 14);

   if(g_handleEmaFast == INVALID_HANDLE || g_handleEmaSlow == INVALID_HANDLE ||
      g_handleRsi == INVALID_HANDLE || g_handleAtr == INVALID_HANDLE)
   {
      Print("ERROR: Failed to create indicators");
      return INIT_FAILED;
   }

   // Initialize daily tracking
   g_dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   g_monthlyStartBalance = g_dailyStartBalance;
   g_peakBalance = g_dailyStartBalance;
   g_lastResetDate = TimeCurrent();
   g_lastMonthResetDate = TimeCurrent();
   g_consecutiveLosses = 0;

   // Create panel (don't update yet - no data)
   if(InpShowPanel)
   {
      CreatePanel();
      ChartRedraw();  // Force chart redraw to show panel
   }

   Print("========================================");
   Print("PSS V6 Ultimate EA initialized");
   Print("Mode: ", EnumToString(InpBotMode));
   Print("Symbol: ", _Symbol);
   Print("Account: ", AccountInfoInteger(ACCOUNT_LOGIN));
   Print("Balance: $", DoubleToString(g_dailyStartBalance, 2));
   Print("Filling Mode: ", GetFillingModeString());
   Print("========================================");

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Setup Filling Mode                                                |
//+------------------------------------------------------------------+
bool SetupFillingMode()
{
   ENUM_ORDER_TYPE_FILLING filling = ORDER_FILLING_IOC;

   if(InpFillingMode == FILLING_AUTO)
   {
      // Auto detect from symbol
      int symbolFilling = (int)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);

      if((symbolFilling & ORDER_FILLING_FOK) != 0)
         filling = ORDER_FILLING_FOK;
      else if((symbolFilling & ORDER_FILLING_IOC) != 0)
         filling = ORDER_FILLING_IOC;
      else if((symbolFilling & ORDER_FILLING_RETURN) != 0)
         filling = ORDER_FILLING_RETURN;
      else
      {
         // Try each mode with order check
         filling = TestFillingMode();
      }
   }
   else
   {
      switch(InpFillingMode)
      {
         case FILLING_FOK:    filling = ORDER_FILLING_FOK; break;
         case FILLING_IOC:    filling = ORDER_FILLING_IOC; break;
         case FILLING_RETURN: filling = ORDER_FILLING_RETURN; break;
      }
   }

   g_fillingMode = filling;
   trade.SetTypeFilling(filling);
   Print("Filling mode set to: ", EnumToString(filling));
   return true;
}

//+------------------------------------------------------------------+
//| Test Filling Mode with Order Check                                |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING TestFillingMode()
{
   ENUM_ORDER_TYPE_FILLING modes[] = {ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN};

   for(int i = 0; i < 3; i++)
   {
      MqlTradeRequest request = {};
      MqlTradeCheckResult checkResult = {};

      request.action = TRADE_ACTION_DEAL;
      request.symbol = _Symbol;
      request.volume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      request.type = ORDER_TYPE_BUY;
      request.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      request.type_filling = modes[i];
      request.type_time = ORDER_TIME_GTC;

      if(OrderCheck(request, checkResult))
      {
         if(checkResult.retcode == 0 || checkResult.retcode == TRADE_RETCODE_DONE)
         {
            Print("Filling mode ", EnumToString(modes[i]), " supported");
            return modes[i];
         }
      }
   }

   Print("WARNING: Could not detect filling mode, using IOC");
   return ORDER_FILLING_IOC;
}

//+------------------------------------------------------------------+
//| Get Filling Mode String                                           |
//+------------------------------------------------------------------+
string GetFillingModeString()
{
   return EnumToString(g_fillingMode);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Release indicators
   if(g_handleEmaFast != INVALID_HANDLE) IndicatorRelease(g_handleEmaFast);
   if(g_handleEmaSlow != INVALID_HANDLE) IndicatorRelease(g_handleEmaSlow);
   if(g_handleRsi != INVALID_HANDLE) IndicatorRelease(g_handleRsi);
   if(g_handleAtr != INVALID_HANDLE) IndicatorRelease(g_handleAtr);

   // Delete panel
   ObjectsDeleteAll(0, g_panelName);
   ObjectDelete(0, "PSS_TP_Line");
   ObjectDelete(0, "PSS_TP_Label");
   ObjectDelete(0, "PSS_Avg_Line");
   ObjectDelete(0, "PSS_Avg_Label");
   ObjectDelete(0, "PSS_BE_Line");
   ObjectDelete(0, "PSS_BE_Label");

   Print("PSS V6 Ultimate EA deinitialized");
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check daily reset
   CheckDailyReset();
   CheckMonthlyReset();

   // Check daily limits ONLY when we have no active positions (to prevent freezing active baskets)
   UpdateDailyProfit();
   UpdateMonthlyProfit();
   UpdateDrawdownTracking();
   if(PositionsTotal() == 0)
   {
      if(CheckDailyLimits())
         return;
   }

   // Update SMC analysis on new bar
   static datetime lastBar = 0;

   // Check if we have at least 1 bar before calling iTime()
   if(Bars(_Symbol, PERIOD_CURRENT) < 1)
      return;

   datetime currentBar = iTime(_Symbol, PERIOD_CURRENT, 0);

   if(currentBar != lastBar)
   {
      lastBar = currentBar;
      UpdateSmcAnalysis();
   }

   // Run selected bot
   switch(InpBotMode)
   {
      case BOT_MARTINGALE:
         RunMartingaleBot();
         break;
      default:
         break;
   }

   // Update panel
   if(InpShowPanel)
      UpdatePanel();

   // Draw TP/AvgPrice/BE lines on chart
   DrawTPLines();
}

//+------------------------------------------------------------------+
//| Get magic number based on bot mode                                |
//+------------------------------------------------------------------+
int GetMagicNumber()
{
   return MAGIC_MARTINGALE;
}

//+------------------------------------------------------------------+
//| DAILY MANAGEMENT                                                  |
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
      g_lastResetDate = TimeCurrent();
      g_martDirection = DIR_NONE;
      Print("Daily reset - New trading day");
   }
}

void CheckMonthlyReset()
{
   MqlDateTime now, lastReset;
   TimeToStruct(TimeCurrent(), now);
   TimeToStruct(g_lastMonthResetDate, lastReset);

   if(now.mon != lastReset.mon || now.year != lastReset.year)
   {
      g_monthlyProfit = 0;
      g_monthlyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      g_lastMonthResetDate = TimeCurrent();
      Print("Monthly reset - New trading month");
   }
}

double GetOpenFloatingPL()
{
   double floatingPL = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == GetMagicNumber())
            floatingPL += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
      }
   }

   return floatingPL;
}

void UpdateDailyProfit()
{
   g_dailyProfit = AccountInfoDouble(ACCOUNT_BALANCE) - g_dailyStartBalance;
   g_dailyProfit += GetOpenFloatingPL();
}

void UpdateMonthlyProfit()
{
   MqlDateTime now;
   TimeToStruct(TimeCurrent(), now);
   now.day = 1;
   now.hour = 0;
   now.min = 0;
   now.sec = 0;
   datetime monthStart = StructToTime(now);

   g_monthlyClosedProfit = 0;
   if(HistorySelect(monthStart, TimeCurrent()))
   {
      int deals = HistoryDealsTotal();
      for(int i = 0; i < deals; i++)
      {
         ulong ticket = HistoryDealGetTicket(i);
         if(ticket == 0)
            continue;

         string dealSymbol = HistoryDealGetString(ticket, DEAL_SYMBOL);
         long dealMagic = HistoryDealGetInteger(ticket, DEAL_MAGIC);
         long dealType = HistoryDealGetInteger(ticket, DEAL_TYPE);

         if(dealSymbol != _Symbol || dealMagic != GetMagicNumber())
            continue;
         if(dealType != DEAL_TYPE_BUY && dealType != DEAL_TYPE_SELL)
            continue;

         g_monthlyClosedProfit += HistoryDealGetDouble(ticket, DEAL_PROFIT);
         g_monthlyClosedProfit += HistoryDealGetDouble(ticket, DEAL_SWAP);
         g_monthlyClosedProfit += HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      }
   }

   g_monthlyProfit = g_monthlyClosedProfit + GetOpenFloatingPL();
}

double GetCurrentDrawdownPercent()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(balance <= 0 || equity >= balance)
      return 0;

   return ((balance - equity) / balance) * 100.0;
}

void UpdateDrawdownTracking()
{
   double currentDD = GetCurrentDrawdownPercent();
   if(currentDD > g_maxCurrentDrawdown)
      g_maxCurrentDrawdown = currentDD;
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

//+------------------------------------------------------------------+
//| SESSION FUNCTIONS                                                 |
//+------------------------------------------------------------------+
string GetCurrentSession()
{
   MqlDateTime now;
   TimeToStruct(TimeCurrent(), now);
   int hour = now.hour;

   if(hour >= InpLondonStart && hour < InpLondonEnd)
      return "london";
   else if(hour >= InpNYStart && hour < InpNYEnd)
      return "newyork";
   else if(hour >= InpAsianStart && hour < InpAsianEnd)
      return "asian";

   return "off";
}

double GetSessionMultiplier()
{
   string session = GetCurrentSession();

   if(session == "london" || session == "newyork")
      return 0.9;  // Easier entry
   else if(session == "asian")
      return 1.3;  // Harder entry

   return 1.0;
}

bool IsInManualNewsWindow(string &reason)
{
   reason = "";
   if(!InpUseNewsFilter || InpNewsTimes == "")
      return false;

   string items[];
   int count = StringSplit(InpNewsTimes, ';', items);
   datetime now = TimeCurrent();

   for(int i = 0; i < count; i++)
   {
      string item = items[i];
      StringTrimLeft(item);
      StringTrimRight(item);
      if(item == "")
         continue;

      datetime newsTime = StringToTime(item);
      if(newsTime <= 0)
         continue;

      datetime blockFrom = newsTime - InpNewsBlockBeforeMin * 60;
      datetime blockTo = newsTime + InpNewsBlockAfterMin * 60;
      if(now >= blockFrom && now <= blockTo)
      {
         int minutesToNews = (int)MathRound((newsTime - now) / 60.0);
         if(minutesToNews >= 0)
            reason = "NEWS in " + IntegerToString(minutesToNews) + "m @ " + item;
         else
            reason = "NEWS +" + IntegerToString(MathAbs(minutesToNews)) + "m @ " + item;
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| POSITION MANAGEMENT                                               |
//+------------------------------------------------------------------+
BotStats GetBotStats(int magic)
{
   BotStats stats;
   stats.totalPositions = 0;
   stats.totalLot = 0;
   stats.totalProfit = 0;
   stats.avgPrice = 0;
   stats.direction = DIR_NONE;
   stats.maxLevelReached = 0;

   double totalValue = 0;
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   bool doLog = (TimeCurrent() - g_lastTPDebugTime >= 25); // Log near debug time

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;

      string posSymbol = PositionGetString(POSITION_SYMBOL);
      long posMagic = PositionGetInteger(POSITION_MAGIC);

      if(posSymbol == _Symbol && posMagic == magic)
      {
         double volume = PositionGetDouble(POSITION_VOLUME);
         double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
         long posType = PositionGetInteger(POSITION_TYPE);
         double posInfoProfit = PositionGetDouble(POSITION_PROFIT);

         double profit = posInfoProfit;

         // Debug: log each position's profit
         if(doLog && stats.totalPositions < 6)
         {
            Print("[STATS-DBG] #", ticket,
                  " ", (posType == POSITION_TYPE_BUY ? "BUY" : "SELL"),
                  " vol=", DoubleToString(volume, 2),
                  " open=", DoubleToString(openPrice, _Digits),
                  " profit=$", DoubleToString(profit, 2));
         }

         // Parse level from comment e.g. "Mart L1 ..."
         string posComment = PositionGetString(POSITION_COMMENT);
         int posLevel = 0;
         int posIdx = StringFind(posComment, "Mart L");
         if(posIdx >= 0)
         {
            string levelStr = StringSubstr(posComment, posIdx + 6, 2);
            posLevel = (int)StringToInteger(levelStr);
         }
         if(posLevel > stats.maxLevelReached)
         {
            stats.maxLevelReached = posLevel;
         }

         stats.totalPositions++;
         stats.totalLot += volume;
         stats.totalProfit += profit;
         totalValue += openPrice * volume;

         if(posType == POSITION_TYPE_BUY)
            stats.direction = DIR_BUY;
         else
            stats.direction = DIR_SELL;
      }
   }

   if(stats.totalLot > 0)
      stats.avgPrice = totalValue / stats.totalLot;

   if(doLog && stats.totalPositions > 0)
   {
      Print("[STATS-DBG] TOTAL: pos=", stats.totalPositions,
            " lot=", DoubleToString(stats.totalLot, 2),
            " profit=$", DoubleToString(stats.totalProfit, 2),
            " avg=", DoubleToString(stats.avgPrice, _Digits),
            " bid=", DoubleToString(bid, _Digits),
            " ask=", DoubleToString(ask, _Digits));
   }

   return stats;
}

double GetLastEntryPrice(int magic)
{
   double lastPrice = 0;
   datetime lastTime = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol && posInfo.Magic() == magic)
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

// CloseAllPositions replaced by CloseAllPositionsWithRetry for better error handling

double GetTotalLot()
{
   double totalLot = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
      {
         if(posInfo.Symbol() == _Symbol)
            totalLot += posInfo.Volume();
      }
   }

   return totalLot;
}

//+------------------------------------------------------------------+
//| UTILITY FUNCTIONS                                                 |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| Open Order With Retry                                             |
//+------------------------------------------------------------------+
bool OpenOrderWithRetry(ENUM_DIRECTION direction, double lot, double sl, double tp, string comment)
{
   if(lot <= 0)
   {
      LogError("Invalid lot size: " + DoubleToString(lot, 2));
      return false;
   }

   // Check margin before opening
   double margin = 0;
   double price = (direction == DIR_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);

   if(!OrderCalcMargin(direction == DIR_BUY ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, _Symbol, lot, price, margin))
   {
      LogError("Cannot calculate margin");
      return false;
   }

   if(margin > AccountInfoDouble(ACCOUNT_MARGIN_FREE))
   {
      LogError("Insufficient margin. Required: " + DoubleToString(margin, 2) + " Free: " + DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2));
      return false;
   }

   // Retry loop
   for(int attempt = 1; attempt <= InpMaxRetries; attempt++)
   {
      // Refresh rates
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

      bool success = false;

      if(direction == DIR_BUY)
         success = trade.Buy(lot, _Symbol, ask, sl, tp, comment);
      else
         success = trade.Sell(lot, _Symbol, bid, sl, tp, comment);

      if(success)
      {
         g_totalTrades++;
         Print("Order opened successfully: ", comment, " Lot: ", DoubleToString(lot, 2));
         return true;
      }

      // Get error info
      uint errorCode = trade.ResultRetcode();
      string errorMsg = trade.ResultRetcodeDescription();

      LogError("Order attempt " + IntegerToString(attempt) + " failed: " + IntegerToString(errorCode) + " - " + errorMsg);

      // Check if should retry
      if(!IsRetryableError(errorCode))
      {
         Print("Non-retryable error, aborting");
         return false;
      }

      // Wait before retry
      if(attempt < InpMaxRetries)
      {
         Print("Waiting ", InpRetryDelayMs, "ms before retry...");
         Sleep(InpRetryDelayMs);
      }
   }

   LogError("All " + IntegerToString(InpMaxRetries) + " attempts failed");
   return false;
}

//+------------------------------------------------------------------+
//| Check if Error is Retryable                                       |
//+------------------------------------------------------------------+
bool IsRetryableError(uint errorCode)
{
   switch(errorCode)
   {
      case TRADE_RETCODE_REQUOTE:        // Requote
      case TRADE_RETCODE_PRICE_OFF:      // Price off
      case TRADE_RETCODE_PRICE_CHANGED:  // Price changed
      case TRADE_RETCODE_CONNECTION:     // Connection error
      case TRADE_RETCODE_TIMEOUT:        // Timeout
      case TRADE_RETCODE_SERVER_DISABLES_AT: // Auto trading disabled by server
         return true;

      case TRADE_RETCODE_NO_MONEY:       // No money
      case TRADE_RETCODE_INVALID_VOLUME: // Invalid volume
      case TRADE_RETCODE_INVALID_PRICE:  // Invalid price
      case TRADE_RETCODE_INVALID_STOPS:  // Invalid stops
      case TRADE_RETCODE_TRADE_DISABLED: // Trade disabled
      case TRADE_RETCODE_MARKET_CLOSED:  // Market closed
         return false;

      default:
         return false;
   }
}

//+------------------------------------------------------------------+
//| Close Position With Retry                                         |
//+------------------------------------------------------------------+
bool ClosePositionWithRetry(ulong ticket)
{
   // First verify the position still exists
   if(!PositionSelectByTicket(ticket))
   {
      Print("Position ", ticket, " no longer exists (already closed)");
      return true; // Consider it closed
   }

   for(int attempt = 1; attempt <= InpMaxRetries; attempt++)
   {
      // Re-verify position still exists before each attempt
      if(!PositionSelectByTicket(ticket))
      {
         Print("Position ", ticket, " closed between attempts");
         return true;
      }

      if(trade.PositionClose(ticket))
      {
         // Verify close actually happened
         if(!PositionSelectByTicket(ticket))
         {
            Print("Position ", ticket, " closed successfully");
            return true;
         }
         // trade returned true but position still there - check retcode
         if(trade.ResultRetcode() == TRADE_RETCODE_DONE)
         {
            Print("Position ", ticket, " close confirmed by retcode");
            return true;
         }
      }

      uint errorCode = trade.ResultRetcode();
      LogError("Close attempt " + IntegerToString(attempt) + " failed: " + IntegerToString(errorCode) + " - " + trade.ResultRetcodeDescription());

      if(!IsRetryableError(errorCode) && errorCode != 0)
         break; // Non-retryable, try alternative

      if(attempt < InpMaxRetries)
         Sleep(InpRetryDelayMs);
   }

   // FALLBACK: Try alternative close method (direct OrderSend)
   Print("[ALT-CLOSE] Trying direct OrderSend for ticket ", ticket);
   return TryAlternativeClose(ticket);
}

//+------------------------------------------------------------------+
//| Alternative Close: Direct OrderSend in opposite direction          |
//+------------------------------------------------------------------+
bool TryAlternativeClose(ulong ticket)
{
   if(!PositionSelectByTicket(ticket))
      return true; // Already closed

   double volume = PositionGetDouble(POSITION_VOLUME);
   ENUM_POSITION_TYPE posType = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

   MqlTradeRequest request = {};
   MqlTradeResult result = {};

   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.volume = volume;
   request.type = (posType == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price = (posType == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   request.deviation = InpSlippage;
   request.type_filling = g_fillingMode;
   request.position = ticket;
   request.comment = "Close #" + IntegerToString((int)ticket);

   if(OrderSend(request, result))
   {
      if(result.retcode == TRADE_RETCODE_DONE)
      {
         Print("[ALT-CLOSE] Position ", ticket, " closed via OrderSend! Profit will be realized.");
         return true;
      }
   }

   // Last resort: try with different filling modes
   ENUM_ORDER_TYPE_FILLING modes[] = {ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN};
   for(int m = 0; m < 3; m++)
   {
      if(modes[m] == g_fillingMode) continue; // Already tried

      request.type_filling = modes[m];
      request.price = (posType == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      if(OrderSend(request, result))
      {
         if(result.retcode == TRADE_RETCODE_DONE)
         {
            Print("[ALT-CLOSE] Position ", ticket, " closed with filling mode ", EnumToString(modes[m]));
            return true;
         }
      }
   }

   LogError("[ALT-CLOSE] ALL methods failed for ticket " + IntegerToString((int)ticket) + " retcode: " + IntegerToString(result.retcode));
   return false;
}

//+------------------------------------------------------------------+
//| Log Error                                                         |
//+------------------------------------------------------------------+
void LogError(string message)
{
   g_lastError = message;
   g_lastErrorTime = TimeCurrent();
   Print("ERROR: ", message);
}

void SetTradeStatus(string status)
{
   g_tradeStatus = status;
}

//+------------------------------------------------------------------+
//| Check Drawdown Protection                                         |
//+------------------------------------------------------------------+
bool CheckDrawdownProtection()
{
   if(InpMaxDrawdownPercent <= 0)
      return true;

   double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);

   // Update peak balance
   if(currentBalance > g_peakBalance)
      g_peakBalance = currentBalance;

   // Calculate drawdown
   double drawdown = 0;
   if(g_peakBalance > 0)
      drawdown = ((g_peakBalance - equity) / g_peakBalance) * 100.0;

   if(drawdown >= InpMaxDrawdownPercent)
   {
      Comment("DRAWDOWN LIMIT REACHED: ", DoubleToString(drawdown, 2), "%");
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Check Consecutive Losses                                          |
//+------------------------------------------------------------------+
bool CheckConsecutiveLosses()
{
   if(InpMaxConsecutiveLoss <= 0)
      return true;

   if(g_consecutiveLosses >= InpMaxConsecutiveLoss)
   {
      Comment("MAX CONSECUTIVE LOSSES REACHED: ", g_consecutiveLosses);
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Update Trade Statistics                                           |
//+------------------------------------------------------------------+
void UpdateTradeStats(double profit)
{
   if(profit > 0)
   {
      g_winTrades++;
      g_consecutiveLosses = 0;
   }
   else if(profit < 0)
   {
      g_lossTrades++;
      g_consecutiveLosses++;
   }
}

double CalculateLotSize(double slPips)
{
   if(!InpUseRiskPercent)
      return InpBaseLot;

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskAmount = equity * InpRiskPercent / 100.0;
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

   double pipValue = tickValue * (PipsToPrice(1) / tickSize);
   double lot = riskAmount / (slPips * pipValue);

   return NormalizeLot(lot);
}

//+------------------------------------------------------------------+
//| SMC ANALYSIS FUNCTIONS                                            |
//+------------------------------------------------------------------+
void UpdateSmcAnalysis()
{
   // Check if we have enough bars
   int bars = Bars(_Symbol, PERIOD_CURRENT);
   if(bars < 100)
   {
      Print("[SMC] Not enough bars (", bars, "/100) - skipping analysis");
      return;
   }

   // Find swing points
   FindSwingPoints();

   // Find structure breaks (BOS/CHoCH)
   FindStructureBreaks();

   // Find order blocks
   FindOrderBlocks();

   // Find liquidity zones
   FindLiquidityZones();

   // Find fair value gaps
   FindFairValueGaps();
}

//+------------------------------------------------------------------+
//| Find Swing Points                                                 |
//+------------------------------------------------------------------+
void FindSwingPoints()
{
   ArrayResize(g_swings, 0);

   int bars = Bars(_Symbol, PERIOD_CURRENT);
   if(bars < 50)
   {
      Print("[SMC] FindSwingPoints: Not enough bars (", bars, ")");
      return;
   }

   int lookback = InpSwingLookback;

   double high[], low[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);

   int copied_high = CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   int copied_low = CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);

   if(copied_high <= 0 || copied_low <= 0)
   {
      Print("[SMC] FindSwingPoints: Failed to copy price data");
      return;
   }

   // Use actual copied size
   bars = MathMin(copied_high, copied_low);

   for(int i = lookback; i < bars - lookback && i < 200; i++)
   {
      // Check for swing high
      bool isSwingHigh = true;
      for(int j = 1; j <= lookback; j++)
      {
         if(high[i] <= high[i-j] || high[i] <= high[i+j])
         {
            isSwingHigh = false;
            break;
         }
      }

      if(isSwingHigh)
      {
         SwingPoint sp;
         sp.index = i;
         sp.price = high[i];
         sp.isHigh = true;
         sp.label = "";

         int size = ArraySize(g_swings);
         ArrayResize(g_swings, size + 1);
         g_swings[size] = sp;
      }

      // Check for swing low
      bool isSwingLow = true;
      for(int j = 1; j <= lookback; j++)
      {
         if(low[i] >= low[i-j] || low[i] >= low[i+j])
         {
            isSwingLow = false;
            break;
         }
      }

      if(isSwingLow)
      {
         SwingPoint sp;
         sp.index = i;
         sp.price = low[i];
         sp.isHigh = false;
         sp.label = "";

         int size = ArraySize(g_swings);
         ArrayResize(g_swings, size + 1);
         g_swings[size] = sp;
      }
   }
}

//+------------------------------------------------------------------+
//| Find Structure Breaks (BOS/CHoCH)                                 |
//+------------------------------------------------------------------+
void FindStructureBreaks()
{
   ArrayResize(g_breaks, 0);

   int bars_needed = InpBosLookback + 50;
   int bars_available = Bars(_Symbol, PERIOD_CURRENT);

   if(bars_available < bars_needed)
   {
      Print("[SMC] FindStructureBreaks: Not enough bars (", bars_available, "/", bars_needed, ")");
      return;
   }

   double close[];
   datetime time[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(time, true);

   int copied = CopyClose(_Symbol, PERIOD_CURRENT, 0, bars_needed, close);
   int copied_time = CopyTime(_Symbol, PERIOD_CURRENT, 0, bars_needed, time);

   if(copied <= 0 || copied_time <= 0)
   {
      Print("[SMC] FindStructureBreaks: Failed to copy price/time data");
      return;
   }

   // Use actual copied size
   bars_needed = MathMin(copied, copied_time);

   int currentBias = 0;  // 0=neutral, 1=bullish, -1=bearish

   // Check bullish breaks (price breaks above swing high)
   for(int s = 0; s < ArraySize(g_swings); s++)
   {
      if(!g_swings[s].isHigh) continue;

      // CRITICAL: Skip swing if index exceeds available bars
      if(g_swings[s].index >= bars_needed) continue;

      for(int i = g_swings[s].index - 1; i >= 0 && i > g_swings[s].index - InpBosLookback; i--)
      {
         // Safety check: ensure index is within bounds
         if(i >= bars_needed) continue;

         if(close[i] > g_swings[s].price)
         {
            StructureBreak sb;
            sb.index = i;
            sb.price = g_swings[s].price;
            sb.isBullish = true;
            sb.label = (currentBias == -1) ? "CHoCH" : "BOS";
            sb.time = time[i];  // Use time array instead of iTime()

            int size = ArraySize(g_breaks);
            ArrayResize(g_breaks, size + 1);
            g_breaks[size] = sb;

            currentBias = 1;
            break;
         }
      }
   }

   // Check bearish breaks (price breaks below swing low)
   for(int s = 0; s < ArraySize(g_swings); s++)
   {
      if(g_swings[s].isHigh) continue;

      // CRITICAL: Skip swing if index exceeds available bars
      if(g_swings[s].index >= bars_needed) continue;

      for(int i = g_swings[s].index - 1; i >= 0 && i > g_swings[s].index - InpBosLookback; i--)
      {
         // Safety check: ensure index is within bounds
         if(i >= bars_needed) continue;

         if(close[i] < g_swings[s].price)
         {
            StructureBreak sb;
            sb.index = i;
            sb.price = g_swings[s].price;
            sb.isBullish = false;
            sb.label = (currentBias == 1) ? "CHoCH" : "BOS";
            sb.time = time[i];  // Use time array instead of iTime()

            int size = ArraySize(g_breaks);
            ArrayResize(g_breaks, size + 1);
            g_breaks[size] = sb;

            currentBias = -1;
            break;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Find Order Blocks                                                 |
//+------------------------------------------------------------------+
void FindOrderBlocks()
{
   ArrayResize(g_orderBlocks, 0);

   int bars_available = Bars(_Symbol, PERIOD_CURRENT);
   if(bars_available < 50)
   {
      Print("[SMC] FindOrderBlocks: Not enough bars (", bars_available, ")");
      return;
   }

   double high[], low[], open[], close[];
   datetime time[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(time, true);

   int bars = MathMin(200, bars_available);
   int copied_h = CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   int copied_l = CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   int copied_o = CopyOpen(_Symbol, PERIOD_CURRENT, 0, bars, open);
   int copied_c = CopyClose(_Symbol, PERIOD_CURRENT, 0, bars, close);
   int copied_t = CopyTime(_Symbol, PERIOD_CURRENT, 0, bars, time);

   if(copied_h <= 0 || copied_l <= 0 || copied_o <= 0 || copied_c <= 0 || copied_t <= 0)
   {
      Print("[SMC] FindOrderBlocks: Failed to copy price/time data");
      return;
   }

   // Use actual copied size
   bars = MathMin(MathMin(MathMin(copied_h, copied_l), MathMin(copied_o, copied_c)), copied_t);

   for(int s = 0; s < ArraySize(g_swings); s++)
   {
      int swingIdx = g_swings[s].index;
      if(swingIdx < 1 || swingIdx >= bars - 1) continue;

      // Bullish OB: at swing low, find bearish candle before
      if(!g_swings[s].isHigh)
      {
         for(int j = swingIdx; j < swingIdx + InpObLookback && j < bars; j++)
         {
            if(close[j] < open[j])  // Bearish candle
            {
               OrderBlock ob;
               ob.high = high[j];
               ob.low = low[j];
               ob.startIndex = j;
               ob.isBullish = true;
               ob.mitigated = false;
               ob.time = time[j];  // Use time array instead of iTime()

               int size = ArraySize(g_orderBlocks);
               ArrayResize(g_orderBlocks, size + 1);
               g_orderBlocks[size] = ob;
               break;
            }
         }
      }
      // Bearish OB: at swing high, find bullish candle before
      else
      {
         for(int j = swingIdx; j < swingIdx + InpObLookback && j < bars; j++)
         {
            if(close[j] > open[j])  // Bullish candle
            {
               OrderBlock ob;
               ob.high = high[j];
               ob.low = low[j];
               ob.startIndex = j;
               ob.isBullish = false;
               ob.mitigated = false;
               ob.time = time[j];  // Use time array instead of iTime()

               int size = ArraySize(g_orderBlocks);
               ArrayResize(g_orderBlocks, size + 1);
               g_orderBlocks[size] = ob;
               break;
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Find Liquidity Zones                                              |
//+------------------------------------------------------------------+
void FindLiquidityZones()
{
   ArrayResize(g_liquidityZones, 0);

   int bars_available = Bars(_Symbol, PERIOD_CURRENT);
   if(bars_available < 50)
   {
      Print("[SMC] FindLiquidityZones: Not enough bars (", bars_available, ")");
      return;
   }

   double high[], low[];
   datetime time[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(time, true);

   int bars = MathMin(200, bars_available);
   int copied_h = CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   int copied_l = CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   int copied_t = CopyTime(_Symbol, PERIOD_CURRENT, 0, bars, time);

   if(copied_h <= 0 || copied_l <= 0 || copied_t <= 0)
   {
      Print("[SMC] FindLiquidityZones: Failed to copy price/time data");
      return;
   }

   // Use actual copied size
   bars = MathMin(MathMin(copied_h, copied_l), copied_t);

   int lookback = InpLqLookback;

   for(int i = lookback; i < bars - lookback && i < 150; i++)
   {
      // Check for liquidity high
      bool isLqHigh = true;
      for(int j = 1; j <= lookback; j++)
      {
         if(high[i] <= high[i-j] || high[i] <= high[i+j])
         {
            isLqHigh = false;
            break;
         }
      }

      if(isLqHigh)
      {
         LiquidityZone lz;
         lz.price = high[i];
         lz.index = i;
         lz.isHigh = true;
         lz.swept = false;
         lz.time = time[i];  // Use time array instead of iTime()

         // Check if swept
         for(int k = i - 1; k >= 0; k--)
         {
            if(high[k] > lz.price)
            {
               lz.swept = true;
               break;
            }
         }

         if(!lz.swept)
         {
            int size = ArraySize(g_liquidityZones);
            ArrayResize(g_liquidityZones, size + 1);
            g_liquidityZones[size] = lz;
         }
      }

      // Check for liquidity low
      bool isLqLow = true;
      for(int j = 1; j <= lookback; j++)
      {
         if(low[i] >= low[i-j] || low[i] >= low[i+j])
         {
            isLqLow = false;
            break;
         }
      }

      if(isLqLow)
      {
         LiquidityZone lz;
         lz.price = low[i];
         lz.index = i;
         lz.isHigh = false;
         lz.swept = false;
         lz.time = time[i];  // Use time array instead of iTime()

         // Check if swept
         for(int k = i - 1; k >= 0; k--)
         {
            if(low[k] < lz.price)
            {
               lz.swept = true;
               break;
            }
         }

         if(!lz.swept)
         {
            int size = ArraySize(g_liquidityZones);
            ArrayResize(g_liquidityZones, size + 1);
            g_liquidityZones[size] = lz;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Find Fair Value Gaps                                              |
//+------------------------------------------------------------------+
void FindFairValueGaps()
{
   ArrayResize(g_fvgs, 0);

   int bars_available = Bars(_Symbol, PERIOD_CURRENT);
   if(bars_available < 10)
   {
      Print("[SMC] FindFairValueGaps: Not enough bars (", bars_available, ")");
      return;
   }

   double high[], low[];
   datetime time[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(time, true);

   int bars = MathMin(100, bars_available);
   int copied_h = CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   int copied_l = CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   int copied_t = CopyTime(_Symbol, PERIOD_CURRENT, 0, bars, time);

   if(copied_h <= 0 || copied_l <= 0 || copied_t <= 0)
   {
      Print("[SMC] FindFairValueGaps: Failed to copy price/time data");
      return;
   }

   // Use actual copied size
   bars = MathMin(MathMin(copied_h, copied_l), copied_t);

   for(int i = 2; i < bars - 2; i++)
   {
      // Bullish FVG: low[i] > high[i+2]
      if(low[i] > high[i+2])
      {
         FairValueGap fvg;
         fvg.high = low[i];
         fvg.low = high[i+2];
         fvg.index = i;
         fvg.isBullish = true;
         fvg.time = time[i];  // Use time array instead of iTime()

         // Check if mitigated (price went below fvg.low)
         bool mitigated = false;
         for(int k = i - 1; k >= 1; k--)
         {
            if(low[k] <= fvg.low)
            {
               mitigated = true;
               break;
            }
         }

         if(!mitigated)
         {
            int size = ArraySize(g_fvgs);
            ArrayResize(g_fvgs, size + 1);
            g_fvgs[size] = fvg;
         }
      }

      // Bearish FVG: high[i] < low[i+2]
      if(high[i] < low[i+2])
      {
         FairValueGap fvg;
         fvg.high = low[i+2];
         fvg.low = high[i];
         fvg.index = i;
         fvg.isBullish = false;
         fvg.time = time[i];  // Use time array instead of iTime()

         // Check if mitigated (price went above fvg.high)
         bool mitigated = false;
         for(int k = i - 1; k >= 1; k--)
         {
            if(high[k] >= fvg.high)
            {
               mitigated = true;
               break;
            }
         }

         if(!mitigated)
         {
            int size = ArraySize(g_fvgs);
            ArrayResize(g_fvgs, size + 1);
            g_fvgs[size] = fvg;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check SMC Entry Conditions                                        |
//+------------------------------------------------------------------+
SmcSignal CheckSmcEntry(ENUM_DIRECTION direction)
{
   SmcSignal signal;
   signal.valid = false;
   signal.score = 0;
   signal.reason = "";
   signal.waiting = "";

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double price = (bid + ask) / 2;
   double pipDistance = PipsToPrice(10);

   // 1. Check Order Block
   for(int i = 0; i < ArraySize(g_orderBlocks); i++)
   {
      OrderBlock ob = g_orderBlocks[i];

      if(direction == DIR_BUY && ob.isBullish)
      {
         if(price >= ob.low - pipDistance && price <= ob.high + pipDistance)
         {
            signal.score += 2;
            signal.reason += "OB+";
            break;
         }
      }
      else if(direction == DIR_SELL && !ob.isBullish)
      {
         if(price >= ob.low - pipDistance && price <= ob.high + pipDistance)
         {
            signal.score += 2;
            signal.reason += "OB+";
            break;
         }
      }
   }

   // 2. Check Liquidity Sweep
   for(int i = 0; i < ArraySize(g_liquidityZones); i++)
   {
      LiquidityZone lz = g_liquidityZones[i];
      double lqDistance = MathAbs(price - lz.price);

      if(direction == DIR_BUY && !lz.isHigh)
      {
         if(lqDistance <= PipsToPrice(20))
         {
            signal.score += 2;
            signal.reason += "LQ+";
            break;
         }
      }
      else if(direction == DIR_SELL && lz.isHigh)
      {
         if(lqDistance <= PipsToPrice(20))
         {
            signal.score += 2;
            signal.reason += "LQ+";
            break;
         }
      }
   }

   // 3. Check FVG
   for(int i = 0; i < ArraySize(g_fvgs); i++)
   {
      FairValueGap fvg = g_fvgs[i];

      if(direction == DIR_BUY && fvg.isBullish)
      {
         if(price >= fvg.low && price <= fvg.high)
         {
            signal.score += 1;
            signal.reason += "FVG+";
            break;
         }
      }
      else if(direction == DIR_SELL && !fvg.isBullish)
      {
         if(price >= fvg.low && price <= fvg.high)
         {
            signal.score += 1;
            signal.reason += "FVG+";
            break;
         }
      }
   }

   // 4. Check Price Action
   double open[], close[], high[], low[];
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);

   if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, 5, open) > 0 &&
      CopyClose(_Symbol, PERIOD_CURRENT, 0, 5, close) > 0 &&
      CopyHigh(_Symbol, PERIOD_CURRENT, 0, 5, high) > 0 &&
      CopyLow(_Symbol, PERIOD_CURRENT, 0, 5, low) > 0)
   {
      // Engulfing pattern
      double prevBody = MathAbs(close[2] - open[2]);
      double currBody = MathAbs(close[1] - open[1]);

      bool bullishEngulf = close[2] < open[2] && close[1] > open[1] && currBody > prevBody * 1.2;
      bool bearishEngulf = close[2] > open[2] && close[1] < open[1] && currBody > prevBody * 1.2;

      if(direction == DIR_BUY && bullishEngulf)
      {
         signal.score += 2;
         signal.reason += "ENG+";
      }
      else if(direction == DIR_SELL && bearishEngulf)
      {
         signal.score += 2;
         signal.reason += "ENG+";
      }

      // Pin Bar
      double body = MathAbs(close[1] - open[1]);
      double upperWick = high[1] - MathMax(close[1], open[1]);
      double lowerWick = MathMin(close[1], open[1]) - low[1];

      bool bullishPin = lowerWick > body * 2 && upperWick < body;
      bool bearishPin = upperWick > body * 2 && lowerWick < body;

      if(direction == DIR_BUY && bullishPin)
      {
         signal.score += 2;
         signal.reason += "PIN+";
      }
      else if(direction == DIR_SELL && bearishPin)
      {
         signal.score += 2;
         signal.reason += "PIN+";
      }
   }

   // Check minimum score
   if(signal.score >= InpMinSmcScore)
   {
      signal.valid = true;
      if(StringLen(signal.reason) > 0)
         signal.reason = StringSubstr(signal.reason, 0, StringLen(signal.reason) - 1);
   }
   else
   {
      signal.waiting = "Score " + IntegerToString(signal.score) + "/" + IntegerToString(InpMinSmcScore);
   }

   return signal;
}

bool DirectionMatchesBreak(ENUM_DIRECTION direction, StructureBreak &brk)
{
   if(direction == DIR_BUY)
      return brk.isBullish;
   if(direction == DIR_SELL)
      return !brk.isBullish;
   return false;
}

//+------------------------------------------------------------------+
//| Get latest structure break by time                                |
//+------------------------------------------------------------------+
bool GetLatestStructureBreak(StructureBreak &latest, int maxBars, ENUM_DIRECTION direction = DIR_NONE)
{
   bool found = false;
   datetime latestTime = 0;

   for(int i = 0; i < ArraySize(g_breaks); i++)
   {
      if(maxBars > 0 && g_breaks[i].index > maxBars)
         continue;

      if(direction != DIR_NONE && !DirectionMatchesBreak(direction, g_breaks[i]))
         continue;

      if(!found || g_breaks[i].time > latestTime)
      {
         latest = g_breaks[i];
         latestTime = g_breaks[i].time;
         found = true;
      }
   }

   return found;
}

//+------------------------------------------------------------------+
//| CHoCH -> BOS confirmation for SMC/SMS martingale entries          |
//+------------------------------------------------------------------+
bool HasSmcStructureSequence(ENUM_DIRECTION direction, string &reason)
{
   datetime latestChoch = 0;
   datetime latestBos = 0;
   bool hasChoch = false;
   bool hasBos = false;

   for(int i = 0; i < ArraySize(g_breaks); i++)
   {
      StructureBreak brk = g_breaks[i];
      if(brk.index > InpMartStructureLookback)
         continue;
      if(!DirectionMatchesBreak(direction, brk))
         continue;

      if(brk.label == "CHoCH")
      {
         if(!hasChoch || brk.time > latestChoch)
            latestChoch = brk.time;
         hasChoch = true;
      }
      else if(brk.label == "BOS")
      {
         if(!hasBos || brk.time > latestBos)
            latestBos = brk.time;
         hasBos = true;
      }
   }

   if(hasChoch && hasBos && latestBos >= latestChoch)
   {
      reason = (direction == DIR_BUY) ? "CHoCH+BOS Bull" : "CHoCH+BOS Bear";
      return true;
   }

   if(!hasChoch && !hasBos)
      reason = "Need CHoCH+BOS";
   else if(!hasChoch)
      reason = "Need CHoCH";
   else if(!hasBos)
      reason = "Need BOS";
   else
      reason = "Need BOS after CHoCH";

   return false;
}

//+------------------------------------------------------------------+
//| Opposite BOS/CHoCH guard                                          |
//+------------------------------------------------------------------+
bool HasOppositeRecentStructure(ENUM_DIRECTION direction, string &reason)
{
   StructureBreak latest;
   if(!GetLatestStructureBreak(latest, InpMartStructureLookback, DIR_NONE))
      return false;

   if(!DirectionMatchesBreak(direction, latest))
   {
      reason = (latest.isBullish ? "Opposite Bull " : "Opposite Bear ") + latest.label;
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Directional order block entry zone                                |
//+------------------------------------------------------------------+
bool IsPriceInDirectionalOrderBlock(ENUM_DIRECTION direction, int bufferPips, string &reason)
{
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double price = (bid + ask) / 2;
   double buffer = PipsToPrice(bufferPips);

   for(int i = 0; i < ArraySize(g_orderBlocks); i++)
   {
      OrderBlock ob = g_orderBlocks[i];
      bool obMatches = (direction == DIR_BUY && ob.isBullish) || (direction == DIR_SELL && !ob.isBullish);
      if(!obMatches)
         continue;

      if(price >= ob.low - buffer && price <= ob.high + buffer)
      {
         reason = (direction == DIR_BUY ? "Bull OB" : "Bear OB") + " " +
                  DoubleToString(ob.low, _Digits) + "-" + DoubleToString(ob.high, _Digits);
         return true;
      }
   }

   reason = "Need OB zone";
   return false;
}

//+------------------------------------------------------------------+
//| Recent liquidity sweep and reclaim/rejection                      |
//+------------------------------------------------------------------+
bool HasRecentLiquiditySweep(ENUM_DIRECTION direction, int lookbackBars, string &reason)
{
   int barsNeeded = InpLqLookback + lookbackBars + 10;
   if(barsNeeded < 30)
      barsNeeded = 30;

   double high[], low[], close[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);

   int copiedHigh = CopyHigh(_Symbol, PERIOD_CURRENT, 0, barsNeeded, high);
   int copiedLow = CopyLow(_Symbol, PERIOD_CURRENT, 0, barsNeeded, low);
   int copiedClose = CopyClose(_Symbol, PERIOD_CURRENT, 0, barsNeeded, close);
   int copied = MathMin(MathMin(copiedHigh, copiedLow), copiedClose);

   if(copied <= InpLqLookback + lookbackBars + 1)
   {
      reason = "Need more bars for LQ";
      return false;
   }

   for(int shift = 1; shift <= lookbackBars; shift++)
   {
      int maxRef = MathMin(copied - 1, shift + InpLqLookback);
      if(shift + 1 > maxRef)
         continue;

      double refHigh = high[shift + 1];
      double refLow = low[shift + 1];

      for(int j = shift + 2; j <= maxRef; j++)
      {
         if(high[j] > refHigh)
            refHigh = high[j];
         if(low[j] < refLow)
            refLow = low[j];
      }

      if(direction == DIR_BUY)
      {
         if(low[shift] < refLow && close[shift] > refLow)
         {
            reason = "LQ low sweep " + DoubleToString(refLow, _Digits);
            return true;
         }
      }
      else if(direction == DIR_SELL)
      {
         if(high[shift] > refHigh && close[shift] < refHigh)
         {
            reason = "LQ high sweep " + DoubleToString(refHigh, _Digits);
            return true;
         }
      }
   }

   reason = "Need LQ sweep";
   return false;
}

//+------------------------------------------------------------------+
//| Daily high/low guard                                              |
//+------------------------------------------------------------------+
bool PassDailyHighLowGuard(ENUM_DIRECTION direction, string &reason)
{
   if(!InpMartUseDailyHLGuard)
      return true;

   double high[], low[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);

   if(CopyHigh(_Symbol, PERIOD_D1, 0, 1, high) <= 0 || CopyLow(_Symbol, PERIOD_D1, 0, 1, low) <= 0)
      return true;

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double price = (bid + ask) / 2;
   double buffer = PipsToPrice(InpMartDailyHLBufferPips);

   if(direction == DIR_BUY && (high[0] - price) <= buffer)
   {
      reason = "BUY blocked near daily high";
      return false;
   }

   if(direction == DIR_SELL && (price - low[0]) <= buffer)
   {
      reason = "SELL blocked near daily low";
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Directional FVG entry zone                                        |
//+------------------------------------------------------------------+
bool IsPriceInRecentDirectionalFvg(ENUM_DIRECTION direction, int bufferPips, string &reason)
{
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double price = (bid + ask) / 2;
   double buffer = PipsToPrice(bufferPips);

   for(int f = 0; f < ArraySize(g_fvgs); f++)
   {
      FairValueGap fvg = g_fvgs[f];
      if(fvg.index > 20)
         continue;

      bool matchDir = (direction == DIR_BUY && fvg.isBullish) ||
                      (direction == DIR_SELL && !fvg.isBullish);
      if(!matchDir)
         continue;

      if(price >= (fvg.low - buffer) && price <= (fvg.high + buffer))
      {
         reason = (direction == DIR_BUY ? "Bull FVG" : "Bear FVG") + " " +
                  DoubleToString(fvg.low, _Digits) + "-" + DoubleToString(fvg.high, _Digits);
         return true;
      }
   }

   reason = "Need recent FVG";
   return false;
}

//+------------------------------------------------------------------+
//| Smart recovery add gate for deeper Martingale levels              |
//+------------------------------------------------------------------+
bool CheckMartingaleSmartAddEntry(ENUM_DIRECTION direction, int nextLevel, string &reason, string &waiting)
{
   reason = "";
   waiting = "";

   string guardReason = "";
   if(!PassDailyHighLowGuard(direction, guardReason))
   {
      waiting = guardReason;
      return false;
   }

   string oppositeReason = "";
   if(InpMartStopAddOnOppositeBos && HasOppositeRecentStructure(direction, oppositeReason))
   {
      waiting = oppositeReason;
      return false;
   }

   string fvgReason = "";
   string obReason = "";
   string lqReason = "";
   string structureReason = "";

   bool inFvg = IsPriceInRecentDirectionalFvg(direction, InpMartObBufferPips, fvgReason);
   bool inOb = IsPriceInDirectionalOrderBlock(direction, InpMartObBufferPips, obReason);
   bool hasLq = HasRecentLiquiditySweep(direction, InpMartLqSweepLookback, lqReason);
   bool hasStructure = HasSmcStructureSequence(direction, structureReason);

   if(nextLevel <= 6)
   {
      if(inOb || inFvg || hasLq)
      {
         reason = "SmartL" + IntegerToString(nextLevel) + ":";
         if(inOb) reason += obReason;
         else if(inFvg) reason += fvgReason;
         else reason += lqReason;
         return true;
      }

      waiting = "L" + IntegerToString(nextLevel) + " needs OB/FVG/LQ, not distance only";
      return false;
   }

   if(!hasStructure)
   {
      waiting = "L" + IntegerToString(nextLevel) + " needs " + structureReason;
      return false;
   }

   if(!hasLq)
   {
      waiting = "L" + IntegerToString(nextLevel) + " needs " + lqReason;
      return false;
   }

   if(!(inOb || inFvg))
   {
      waiting = "L" + IntegerToString(nextLevel) + " needs OB/FVG zone";
      return false;
   }

   reason = "SmartL" + IntegerToString(nextLevel) + ":" + structureReason + "+" + lqReason + "+";
   reason += inOb ? obReason : fvgReason;
   return true;
}

//+------------------------------------------------------------------+
//| Strict Martingale SMC/SMS gate                                    |
//+------------------------------------------------------------------+
SmcSignal CheckMartingaleSmcPrecisionEntry(ENUM_DIRECTION direction, bool isAdd)
{
   if(!InpMartStrictSmcEntry)
      return CheckSmcEntry(direction);

   SmcSignal signal;
   signal.valid = false;
   signal.score = 0;
   signal.reason = "";
   signal.waiting = "";

   if(direction == DIR_NONE)
   {
      signal.waiting = "No direction";
      return signal;
   }

   string guardReason = "";
   if(!PassDailyHighLowGuard(direction, guardReason))
   {
      signal.waiting = guardReason;
      return signal;
   }

   string oppositeReason = "";
   if(InpMartStopAddOnOppositeBos && HasOppositeRecentStructure(direction, oppositeReason))
   {
      signal.waiting = oppositeReason;
      return signal;
   }

   string structureReason = "";
   if(!HasSmcStructureSequence(direction, structureReason))
   {
      signal.waiting = structureReason;
      return signal;
   }
   signal.score += 3;

   string lqReason = "";
   if(!HasRecentLiquiditySweep(direction, InpMartLqSweepLookback, lqReason))
   {
      signal.waiting = lqReason;
      return signal;
   }
   signal.score += 2;

   string obReason = "";
   if(!IsPriceInDirectionalOrderBlock(direction, InpMartObBufferPips, obReason))
   {
      signal.waiting = obReason;
      return signal;
   }
   signal.score += 2;

   SmcSignal base = CheckSmcEntry(direction);
   if(base.score > 0)
      signal.score += MathMin(base.score, 2);

   signal.valid = true;
   signal.reason = structureReason + "+" + lqReason + "+" + obReason;
   if(base.score > 0 && base.reason != "")
      signal.reason += "+" + base.reason;

   return signal;
}

//+------------------------------------------------------------------+
//| Get Trend Direction from BOS/CHoCH                                |
//+------------------------------------------------------------------+
ENUM_DIRECTION GetSmcTrendDirection()
{
   if(ArraySize(g_breaks) == 0)
      return DIR_NONE;

   // Get most recent break within last 20 bars
   for(int i = ArraySize(g_breaks) - 1; i >= 0; i--)
   {
      if(g_breaks[i].index <= 20)
      {
         return g_breaks[i].isBullish ? DIR_BUY : DIR_SELL;
      }
   }

   // Use the most recent break if none within 20 bars
   if(ArraySize(g_breaks) > 0)
   {
      StructureBreak lastBreak = g_breaks[ArraySize(g_breaks) - 1];
      return lastBreak.isBullish ? DIR_BUY : DIR_SELL;
   }

   return DIR_NONE;
}

//+------------------------------------------------------------------+
//| Get Higher Timeframe (HTF) Trend Direction                       |
//+------------------------------------------------------------------+
ENUM_DIRECTION GetHTFTrendDirection()
{
   double emaFast[], emaSlow[];
   ArraySetAsSeries(emaFast, true);
   ArraySetAsSeries(emaSlow, true);

   if(CopyBuffer(g_handleEmaFast, 0, 0, 2, emaFast) <= 0) return DIR_NONE;
   if(CopyBuffer(g_handleEmaSlow, 0, 0, 2, emaSlow) <= 0) return DIR_NONE;

   if(emaFast[0] > emaSlow[0])
      return DIR_BUY;
   else if(emaFast[0] < emaSlow[0])
      return DIR_SELL;

   return DIR_NONE;
}

//+------------------------------------------------------------------+
//| Get major trend direction for L1 anti-trap guard                  |
//+------------------------------------------------------------------+
ENUM_DIRECTION GetMajorTrendDirection(string &reason)
{
   reason = "";

   int fastPeriod = MathMax(2, InpMajorTrendFastEma);
   int slowPeriod = MathMax(fastPeriod + 1, InpMajorTrendSlowEma);
   int slopeBars = MathMax(3, InpMajorTrendSlopeBars);

   double emaFast[], emaSlow[], close[];
   ArraySetAsSeries(emaFast, true);
   ArraySetAsSeries(emaSlow, true);
   ArraySetAsSeries(close, true);

   int fastHandle = iMA(_Symbol, InpMajorTrendPeriod, fastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   int slowHandle = iMA(_Symbol, InpMajorTrendPeriod, slowPeriod, 0, MODE_EMA, PRICE_CLOSE);

   if(fastHandle == INVALID_HANDLE || slowHandle == INVALID_HANDLE)
   {
      if(fastHandle != INVALID_HANDLE) IndicatorRelease(fastHandle);
      if(slowHandle != INVALID_HANDLE) IndicatorRelease(slowHandle);
      reason = "major trend handles unavailable";
      return DIR_NONE;
   }

   int barsNeeded = slopeBars + 2;
   int copiedFast = CopyBuffer(fastHandle, 0, 0, barsNeeded, emaFast);
   int copiedSlow = CopyBuffer(slowHandle, 0, 0, barsNeeded, emaSlow);
   int copiedClose = CopyClose(_Symbol, InpMajorTrendPeriod, 0, barsNeeded, close);

   IndicatorRelease(fastHandle);
   IndicatorRelease(slowHandle);

   int copied = MathMin(MathMin(copiedFast, copiedSlow), copiedClose);
   if(copied <= slopeBars)
   {
      reason = "major trend needs more bars";
      return DIR_NONE;
   }

   bool bullish = emaFast[1] > emaSlow[1] &&
                  close[1] > emaFast[1] &&
                  emaFast[1] > emaFast[slopeBars] &&
                  close[1] > close[slopeBars];

   bool bearish = emaFast[1] < emaSlow[1] &&
                  close[1] < emaFast[1] &&
                  emaFast[1] < emaFast[slopeBars] &&
                  close[1] < close[slopeBars];

   if(bullish)
   {
      reason = "major BUY " + EnumToString(InpMajorTrendPeriod) +
               " EMA" + IntegerToString(fastPeriod) + ">EMA" + IntegerToString(slowPeriod);
      return DIR_BUY;
   }

   if(bearish)
   {
      reason = "major SELL " + EnumToString(InpMajorTrendPeriod) +
               " EMA" + IntegerToString(fastPeriod) + "<EMA" + IntegerToString(slowPeriod);
      return DIR_SELL;
   }

   reason = "major trend mixed";
   return DIR_NONE;
}

//+------------------------------------------------------------------+
//| Analyze Daily Direction (for Martingale)                          |
//+------------------------------------------------------------------+
ENUM_DIRECTION AnalyzeDailyDirection()
{
   double emaFast[], emaSlow[], rsi[];
   ArraySetAsSeries(emaFast, true);
   ArraySetAsSeries(emaSlow, true);
   ArraySetAsSeries(rsi, true);

   if(CopyBuffer(g_handleEmaFast, 0, 0, 10, emaFast) <= 0) return DIR_BUY;
   if(CopyBuffer(g_handleEmaSlow, 0, 0, 10, emaSlow) <= 0) return DIR_BUY;
   if(CopyBuffer(g_handleRsi, 0, 0, 10, rsi) <= 0) return DIR_BUY;

   string majorReason = "";
   ENUM_DIRECTION majorDir = GetMajorTrendDirection(majorReason);
   if(InpUseMajorTrendGuard && majorDir != DIR_NONE)
   {
      Print("[DIR-BIAS] Major trend selected ", EnumToString(majorDir), ": ", majorReason);
      return majorDir;
   }

   int buyScore = 0;
   int sellScore = 0;

   // EMA alignment
   if(emaFast[0] > emaSlow[0])
      buyScore += 2;
   else
      sellScore += 2;

   // RSI
   if(rsi[0] > 50)
      buyScore += 1;
   else
      sellScore += 1;

   // Recent price movement on HTF
   double close[];
   ArraySetAsSeries(close, true);
   int copied = CopyClose(_Symbol, InpHtfPeriod, 0, 50, close);
   if(copied >= 50)  // Make sure we have at least 50 bars
   {
      if(close[0] > close[49])
         buyScore += 1;
      else
         sellScore += 1;
   }

   // SMC Trend (local chart)
   ENUM_DIRECTION smcDir = GetSmcTrendDirection();
   if(smcDir == DIR_BUY)
      buyScore += 2;
   else if(smcDir == DIR_SELL)
      sellScore += 2;

   Print("[DIR-SCORE] BUY=", buyScore, " SELL=", sellScore,
         " HTF_EMA=", (emaFast[0] > emaSlow[0] ? "BUY" : "SELL"),
         " RSI=", DoubleToString(rsi[0], 1),
         " SMC=", EnumToString(smcDir));

   return (buyScore > sellScore) ? DIR_BUY : DIR_SELL;
}

//+------------------------------------------------------------------+
//| SOLUTION 1: Check Trend Filter (Anti-Trend Trading)              |
//| จาก Web Research: Grid Bot Best Practices, Blueberry Markets     |
//+------------------------------------------------------------------+
bool CheckTrendFilter(ENUM_DIRECTION direction)
{
   if(!InpTrendFilterEnabled)
      return true;  // Filter disabled, allow entry

   double emaFast[], emaSlow[], close[];
   ArraySetAsSeries(emaFast, true);
   ArraySetAsSeries(emaSlow, true);
   ArraySetAsSeries(close, true);

   // Need EMA 21 and EMA 50
   int ema21 = iMA(_Symbol, PERIOD_CURRENT, 21, 0, MODE_EMA, PRICE_CLOSE);
   int ema50 = iMA(_Symbol, PERIOD_CURRENT, 50, 0, MODE_EMA, PRICE_CLOSE);

   if(ema21 == INVALID_HANDLE || ema50 == INVALID_HANDLE)
      return true;  // Cannot check, allow entry

   if(CopyBuffer(ema21, 0, 0, 5, emaFast) <= 0) return true;
   if(CopyBuffer(ema50, 0, 0, 5, emaSlow) <= 0) return true;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 0, 5, close) <= 0) return true;

   IndicatorRelease(ema21);
   IndicatorRelease(ema50);

   // Check strong trend (3 candles consecutive)
   int consecutiveBullish = 0;
   int consecutiveBearish = 0;

   for(int i = 0; i < 3; i++)
   {
      if(emaFast[i] > emaSlow[i])
         consecutiveBullish++;
      else
         consecutiveBearish++;

      if(i < 2 && close[i] > close[i+1])
         consecutiveBullish++;
      else if(i < 2)
         consecutiveBearish++;
   }

   // Block SELL when strong uptrend
   if(direction == DIR_SELL && consecutiveBullish >= 5)
   {
      Print("[TREND-FILTER] SELL BLOCKED: Strong uptrend detected (EMA21 > EMA50 x3)");
      return false;
   }

   // Block BUY when strong downtrend
   if(direction == DIR_BUY && consecutiveBearish >= 5)
   {
      Print("[TREND-FILTER] BUY BLOCKED: Strong downtrend detected (EMA21 < EMA50 x3)");
      return false;
   }

   return true;  // Allow entry
}

//+------------------------------------------------------------------+
//| SOLUTION 1: Check Trend Reversal Exit                            |
//| จาก Statement Analysis 2026-01-02: Stop Out Prevention           |
//+------------------------------------------------------------------+
bool CheckTrendReversalExit(ENUM_DIRECTION direction, double totalProfit)
{
   if(!InpTrendRevExitEnabled)
      return false;  // Feature disabled

   if(totalProfit >= 0)
      return false;  // Only check when losing

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double lossPct = (MathAbs(totalProfit) / balance) * 100.0;

   if(lossPct < InpTrendRevLossPct)
      return false;  // Loss not big enough yet

   // Check if price moving wrong direction for 5 consecutive candles
   double emaFast[], emaSlow[];
   ArraySetAsSeries(emaFast, true);
   ArraySetAsSeries(emaSlow, true);

   int ema21 = iMA(_Symbol, PERIOD_CURRENT, 21, 0, MODE_EMA, PRICE_CLOSE);
   int ema50 = iMA(_Symbol, PERIOD_CURRENT, 50, 0, MODE_EMA, PRICE_CLOSE);

   if(ema21 == INVALID_HANDLE || ema50 == INVALID_HANDLE)
      return false;

   if(CopyBuffer(ema21, 0, 0, InpTrendRevCandles + 1, emaFast) <= 0)
   {
      IndicatorRelease(ema21);
      IndicatorRelease(ema50);
      return false;
   }
   if(CopyBuffer(ema50, 0, 0, InpTrendRevCandles + 1, emaSlow) <= 0)
   {
      IndicatorRelease(ema21);
      IndicatorRelease(ema50);
      return false;
   }

   IndicatorRelease(ema21);
   IndicatorRelease(ema50);

   int consecutiveWrong = 0;

   for(int i = 0; i < InpTrendRevCandles; i++)
   {
      // SELL but price going up (EMA21 > EMA50) = wrong direction
      if(direction == DIR_SELL && emaFast[i] > emaSlow[i])
         consecutiveWrong++;
      // BUY but price going down (EMA21 < EMA50) = wrong direction
      else if(direction == DIR_BUY && emaFast[i] < emaSlow[i])
         consecutiveWrong++;
   }

   if(consecutiveWrong >= InpTrendRevCandles)
   {
      Print("[MARTINGALE] TREND REVERSAL EXIT TRIGGERED!");
      Print("[MARTINGALE]    Direction: ", EnumToString(direction));
      Print("[MARTINGALE]    Consecutive wrong: ", consecutiveWrong, "/", InpTrendRevCandles);
      Print("[MARTINGALE]    Loss: $", DoubleToString(totalProfit, 2), " (", DoubleToString(lossPct, 1), "% of balance)");
      Print("[MARTINGALE]    Cutting loss to prevent Stop Out");
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| SOLUTION 1: Check Emergency Exit (Margin/Drawdown Protection)    |
//| จาก Statement Analysis: Stop Out at Margin Level 17-20%          |
//+------------------------------------------------------------------+
bool CheckEmergencyExit(double totalProfit)
{
   if(!InpEmergencyExitEnabled)
      return false;

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double margin = AccountInfoDouble(ACCOUNT_MARGIN);

   // Calculate margin level %
   double marginLevelPct = 999;
   if(margin > 0)
      marginLevelPct = (equity / margin) * 100.0;

   // Calculate drawdown %
   double drawdownPct = 0;
   if(balance > 0)
      drawdownPct = ((balance - equity) / balance) * 100.0;

   // Check 1: Margin Level < 30% (before stop out at 20%)
   if(margin > 0 && marginLevelPct < InpEmergencyMarginPct)
   {
      Print("[MARTINGALE] EMERGENCY EXIT: Margin Level ", DoubleToString(marginLevelPct, 1), "% < ", DoubleToString(InpEmergencyMarginPct, 0), "%");
      Print("[MARTINGALE]    Equity: $", DoubleToString(equity, 2));
      Print("[MARTINGALE]    Margin: $", DoubleToString(margin, 2));
      Print("[MARTINGALE]    Cutting loss at $", DoubleToString(totalProfit, 2), " to protect capital");
      return true;
   }

   // Check 2: Drawdown > 30%
   if(drawdownPct > 30.0)
   {
      Print("[MARTINGALE] EMERGENCY EXIT: Drawdown ", DoubleToString(drawdownPct, 1), "% > 30%");
      return true;
   }

   // Check 3: Floating Loss > 50% of balance
   if(totalProfit < 0 && MathAbs(totalProfit) > (balance * 0.5))
   {
      Print("[MARTINGALE] EMERGENCY EXIT: Loss $", DoubleToString(MathAbs(totalProfit), 2), " > 50% of balance");
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| MARTINGALE BOT                                                    |
//+------------------------------------------------------------------+
void RunMartingaleBot()
{
   SetTradeStatus("ACTIVE");
   BotStats stats = GetBotStats(MAGIC_MARTINGALE);

   // Check additional protections ONLY when we have no positions (to prevent opening new baskets)
   if(stats.totalPositions == 0)
   {
      if(!CheckDrawdownProtection() || !CheckConsecutiveLosses())
      {
         SetTradeStatus("WAIT RISK LIMIT");
         return;
      }
   }

   // TP RETRY: If TP was triggered but close failed, keep retrying
   if(g_tpPending && stats.totalPositions > 0)
   {
      SetTradeStatus("TP RETRY");
      Print("[TP-RETRY] Re-attempting to close all positions... Profit: $", DoubleToString(stats.totalProfit, 2));
      if(CloseAllPositionsWithRetry(MAGIC_MARTINGALE))
      {
         g_tpPending = false;
         g_martDirection = DIR_NONE;
         g_breakevenMoved = false;
         g_partialClosed = false;
         g_highestProfitPips = 0;
         g_basketMaxFloatingLoss = 0;
         Print("[TP-RETRY] SUCCESS! All positions closed!");
      }
      else
      {
         Print("[TP-RETRY] FAILED again, will retry next tick");
      }
      return; // Don't do anything else while TP close is pending
   }
   else if(g_tpPending && stats.totalPositions == 0)
   {
      g_tpPending = false; // Positions were closed externally
      g_martDirection = DIR_NONE;
      g_breakevenMoved = false;
      g_partialClosed = false;
      g_highestProfitPips = 0;
      g_basketMaxFloatingLoss = 0;
      Print("[TP-RETRY] Positions closed (externally). Reset.");
      return;
   }

   // === SOLUTION 1: SAFETY CHECKS (Web Research) ===

   // 1. Emergency Exit - Check FIRST before everything
   if(stats.totalPositions > 0 && CheckEmergencyExit(stats.totalProfit))
   {
      SetTradeStatus("EMERGENCY EXIT");
      Print("[EMERGENCY EXIT] Closing all positions!");
      if(CloseAllPositionsWithRetry(MAGIC_MARTINGALE))
      {
         UpdateTradeStats(stats.totalProfit);
         g_martDirection = DIR_NONE;
         g_breakevenMoved = false;
         g_partialClosed = false;
         g_highestProfitPips = 0;
         g_basketMaxFloatingLoss = 0;
      }
      return;
   }

   // 2. Trend Reversal Exit - Check when in loss
   if(stats.totalPositions >= 2 && stats.totalProfit < 0)
   {
      if(CheckTrendReversalExit(stats.direction, stats.totalProfit))
      {
         SetTradeStatus("TREND REV EXIT");
         Print("[TREND REVERSAL EXIT] Chart moved wrong direction! Closing all!");
         if(CloseAllPositionsWithRetry(MAGIC_MARTINGALE))
         {
            UpdateTradeStats(stats.totalProfit);
            g_martDirection = DIR_NONE;
            g_breakevenMoved = false;
            g_partialClosed = false;
            g_highestProfitPips = 0;
            g_basketMaxFloatingLoss = 0;
         }
         return;
      }
   }

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double price = (bid + ask) / 2;

   // No positions - Open first order
   if(stats.totalPositions == 0)
   {
      string newsReason = "";
      if(InpNewsBlockNewEntry && IsInManualNewsWindow(newsReason))
      {
         SetTradeStatus("WAIT NEWS - no new order");
         static datetime lastNewsEntryLog = 0;
         if(TimeCurrent() - lastNewsEntryLog >= 60)
         {
            lastNewsEntryLog = TimeCurrent();
            Print("[NEWS-FILTER] New basket blocked: ", newsReason);
         }
         return;
      }

      // Determine direction
      if(InpMartAutoDirection || g_martDirection == DIR_NONE)
      {
         g_martDirection = AnalyzeDailyDirection();

         // Apply strict HTF trend filter
         if(InpUseHtfFilter)
         {
            ENUM_DIRECTION htfDir = GetHTFTrendDirection();
            if(htfDir != DIR_NONE && g_martDirection != htfDir)
            {
               Print("[HTF-FILTER] Blocked L1 entry in ", EnumToString(g_martDirection), " direction because HTF trend is ", EnumToString(htfDir));
               SetTradeStatus("WAIT HTF TREND");
               g_martDirection = DIR_NONE;
               return;
            }
         }

      }

      Print("[MARTINGALE] No positions. Direction: ", EnumToString(g_martDirection));

      // 3. Trend Filter - Block new entries against strong trend
      if(!CheckTrendFilter(g_martDirection))
         {
            Print("[TREND FILTER] ", EnumToString(g_martDirection), " blocked by trend filter");
            SetTradeStatus("WAIT TREND FILTER");
            return;
         }

      // Check strict SMC/SMS entry: CHoCH+BOS, liquidity sweep and OB zone.
      SmcSignal signal = CheckMartingaleSmcPrecisionEntry(g_martDirection, false);

      Print("[MARTINGALE] SMC Signal - Valid: ", signal.valid, " Score: ", signal.score,
            " Reason: ", signal.reason, " Waiting: ", signal.waiting);

      if(signal.valid)
      {
         double lot = NormalizeLot(InpBaseLot);

         // Check max lot
         if(GetTotalLot() + lot > InpMaxTotalLot)
         {
            Print("Max lot limit reached");
            SetTradeStatus("WAIT MAX LOT");
            return;
         }

         string comment = "Mart L1 " + signal.reason;

         Print("[MARTINGALE] Opening L1: ", EnumToString(g_martDirection), " Lot: ", lot, " Reason: ", signal.reason);
         if(OpenOrderWithRetry(g_martDirection, lot, 0, 0, comment))
         {
            Print("[MARTINGALE] L1 opened successfully!");
         }
         else
         {
            Print("[MARTINGALE] L1 failed to open!");
         }
      }
      else
      {
         Print("[MARTINGALE] Waiting for SMC signal (score ", signal.score, "/", InpMinSmcScore, ")");
         SetTradeStatus("WAIT SMC L1");
      }
      return;
   }

   // Has positions
   ENUM_DIRECTION direction = stats.direction;

   // Calculate profit in pips
   double avgPrice = stats.avgPrice;
   double profitPips = 0;
   if(direction == DIR_BUY)
      profitPips = PriceToPips(price - avgPrice);
   else
      profitPips = PriceToPips(avgPrice - price);

   // Track highest profit
   if(profitPips > g_highestProfitPips)
      g_highestProfitPips = profitPips;

   if(stats.totalProfit < 0)
      g_basketMaxFloatingLoss = MathMax(g_basketMaxFloatingLoss, MathAbs(stats.totalProfit));

   // ================================================================
   // TP CHECK FIRST! (Before Breakeven / Partial Close)
   // ================================================================

   // Calculate basket TP. Adaptive mode uses AvgPrice + pips/ATR so bigger baskets
   // do not close for the same fixed $ target as a single small entry.
   double targetProfit = InpMartTakeProfitUSD;
   double tpDist = 0;

   if(InpMartUseAdaptiveBasketTP)
   {
      double targetPips = InpMartTPBasePips;

      if(g_handleAtr != INVALID_HANDLE)
      {
         double atrValues[];
         ArraySetAsSeries(atrValues, true);
         if(CopyBuffer(g_handleAtr, 0, 0, 1, atrValues) > 0)
         {
            double atrPips = PriceToPips(atrValues[0]);
            if(atrPips > 0)
               targetPips = MathMax(targetPips, atrPips * InpMartTPAtrMultiplier);
         }
      }

      if(stats.maxLevelReached >= 10)
         targetPips *= 0.45;
      else if(stats.maxLevelReached >= 7)
         targetPips *= 0.60;
      else if(stats.maxLevelReached >= 4)
         targetPips *= 0.80;

      targetPips = MathMax(InpMartTPMinPips, MathMin(InpMartTPMaxPips, targetPips));
      tpDist = PipsToPrice(targetPips);

      double tickVal = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tickSz = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      double priceBasedProfit = 0;
      if(stats.totalLot > 0 && tickVal > 0 && tickSz > 0)
         priceBasedProfit = (tpDist / tickSz) * tickVal * stats.totalLot;

      double lotBasedProfit = InpMartProfitPer001Lot * (stats.totalLot / 0.01);
      targetProfit = MathMax(MathMax(priceBasedProfit, lotBasedProfit), InpMartMinProfitUSD);
   }
   else
   {
      if(InpMartTPScaling)
         targetProfit = InpMartTakeProfitUSD * (stats.totalLot / 0.01);
      targetProfit = MathMax(targetProfit, InpMartMinProfitUSD);

      double tickVal = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tickSz = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      if(stats.totalLot > 0 && tickVal > 0)
         tpDist = (targetProfit / stats.totalLot) * (tickSz / tickVal);
   }

   if(InpMartUseRecoveryProfitTP && stats.totalPositions >= InpMartRecoveryTPMinLevel && g_basketMaxFloatingLoss > 0)
   {
      double recoveryTarget = g_basketMaxFloatingLoss * (InpMartRecoveryTPPercent / 100.0);
      if(InpMartRecoveryTPMaxUSD > 0)
         recoveryTarget = MathMin(recoveryTarget, InpMartRecoveryTPMaxUSD);
      targetProfit = MathMax(targetProfit, recoveryTarget);

      double tickVal = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double tickSz = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
      if(stats.totalLot > 0 && tickVal > 0)
         tpDist = (targetProfit / stats.totalLot) * (tickSz / tickVal);
   }

   g_calcTargetProfit = targetProfit;

   // Calculate TP price level for visual display and price-based backup close
   {
      if(direction == DIR_BUY)
         g_calcTPPrice = avgPrice + tpDist;
      else
         g_calcTPPrice = avgPrice - tpDist;
   }

   // TP Debug logging every 30 seconds
   if(TimeCurrent() - g_lastTPDebugTime >= 30)
   {
      g_lastTPDebugTime = TimeCurrent();
      Print("[TP-DEBUG] Profit: $", DoubleToString(stats.totalProfit, 2),
            " / Target: $", DoubleToString(targetProfit, 2),
            " | AvgPrice: ", DoubleToString(avgPrice, _Digits),
            " | TP Price: ", DoubleToString(g_calcTPPrice, _Digits),
            " | Lots: ", DoubleToString(stats.totalLot, 2),
            " | Pos: ", stats.totalPositions,
            " | ProfitPips: ", DoubleToString(profitPips, 1),
            " | BasketMaxDD: $", DoubleToString(g_basketMaxFloatingLoss, 2));
   }

   // Check take profit
   bool tpTriggered = false;

   // 1. Dollar-based TP check
   if(stats.totalProfit >= targetProfit)
   {
      tpTriggered = true;
      Print("[TP-$] Dollar TP triggered! Profit: $", DoubleToString(stats.totalProfit, 2),
            " >= Target: $", DoubleToString(targetProfit, 2));
   }
   // 2. BACKUP: Price-based TP check
   else if(g_calcTPPrice > 0 && stats.totalProfit > InpMartMinProfitUSD)
   {
      bool pricePastTP = false;
      if(direction == DIR_BUY && bid >= g_calcTPPrice)
         pricePastTP = true;
      else if(direction == DIR_SELL && ask <= g_calcTPPrice)
         pricePastTP = true;

      if(pricePastTP)
      {
         tpTriggered = true;
         Print("[TP-PRICE] Price passed TP level! bid=", DoubleToString(bid, _Digits),
               " ask=", DoubleToString(ask, _Digits),
               " tpPrice=", DoubleToString(g_calcTPPrice, _Digits),
               " profit=$", DoubleToString(stats.totalProfit, 2));
      }
   }

   // TP TRIGGERED - proceed to close
   if(tpTriggered)
   {
      // Hedge Protection
      bool hasHedge = false;
      int buyCount = 0, sellCount = 0;

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(posInfo.SelectByIndex(i) && posInfo.Magic() == MAGIC_MARTINGALE)
         {
            if(posInfo.PositionType() == POSITION_TYPE_BUY)
               buyCount++;
            else
               sellCount++;
         }
      }

      if(buyCount > 0 && sellCount > 0)
         hasHedge = true;

      if(hasHedge)
      {
         double minHedgeProfit = targetProfit * 0.3;
         minHedgeProfit = MathMax(minHedgeProfit, InpMartMinProfitUSD);

         if(stats.totalProfit < minHedgeProfit)
         {
            Print("[HEDGE PROTECTION] Hedge active - profit $", DoubleToString(stats.totalProfit, 2),
                  " < minimum $", DoubleToString(minHedgeProfit, 2), " - waiting");
            return;
         }
      }

      Print("Martingale TP triggered! Target: $", DoubleToString(targetProfit, 2),
            " Actual: $", DoubleToString(stats.totalProfit, 2));

      if(CloseAllPositionsWithRetry(MAGIC_MARTINGALE))
      {
         Print("Martingale closed with profit: $", DoubleToString(stats.totalProfit, 2));
         g_martDirection = DIR_NONE;
         g_tpPending = false;
         g_breakevenMoved = false;
         g_partialClosed = false;
         g_highestProfitPips = 0;
         g_basketMaxFloatingLoss = 0;
      }
      else
      {
         g_tpPending = true;
         Print("[TP-CLOSE FAILED] Will retry on next tick! Profit: $", DoubleToString(stats.totalProfit, 2));
      }
      return;
   }

   // ================================================================
   // SAFETY FEATURES (only when TP NOT triggered)
   // ================================================================

   // 4. Breakeven SL - Move SL to breakeven when in profit
   if(InpBreakevenEnabled && !g_breakevenMoved && stats.totalPositions >= 1)
   {
      if(profitPips >= InpBreakevenTrigger)
      {
         Print("[BREAKEVEN] Profit ", DoubleToString(profitPips, 1), " pips >= ", InpBreakevenTrigger, " pips trigger");

         double pipValue = (_Symbol == "XAUUSD" || StringFind(_Symbol, "XAU") >= 0) ? 0.1 : 0.0001;
         double breakevenPrice = 0;

         if(direction == DIR_BUY)
            breakevenPrice = avgPrice + (InpBreakevenOffset * pipValue);
         else
            breakevenPrice = avgPrice - (InpBreakevenOffset * pipValue);

         int movedCount = 0;
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            if(posInfo.SelectByIndex(i))
            {
               if(posInfo.Magic() == MAGIC_MARTINGALE)
               {
                  MqlTradeRequest request = {};
                  MqlTradeResult result = {};

                  request.action = TRADE_ACTION_SLTP;
                  request.position = posInfo.Ticket();
                  request.sl = NormalizeDouble(breakevenPrice, _Digits);
                  request.tp = posInfo.TakeProfit();
                  request.symbol = _Symbol;

                  if(OrderSend(request, result))
                  {
                     if(result.retcode == TRADE_RETCODE_DONE)
                        movedCount++;
                  }
               }
            }
         }

         if(movedCount > 0)
         {
            g_breakevenMoved = true;
            Print("[BREAKEVEN] Moved ", movedCount, " positions to breakeven @ ", DoubleToString(breakevenPrice, _Digits));
         }
      }
   }

   // 5. Partial Close - Close 50% when in profit (AFTER TP check)
   if(InpPartialCloseEnabled && !g_partialClosed && stats.totalPositions >= 2)
   {
      if(profitPips >= InpPartialClosePips)
      {
         Print("[PARTIAL CLOSE] Profit ", DoubleToString(profitPips, 1), " pips >= ", InpPartialClosePips, " pips trigger");

         int totalPositions = 0;
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            if(posInfo.SelectByIndex(i) && posInfo.Magic() == MAGIC_MARTINGALE)
               totalPositions++;
         }

         int positionsToClose = (int)MathFloor(totalPositions * InpPartialClosePct / 100.0);
         positionsToClose = MathMax(positionsToClose, 1);

         // FIX: Close SMALLEST positions first (L1, L2) instead of largest!
         int closedCount = 0;
         for(int i = 0; i < PositionsTotal() && closedCount < positionsToClose; i++)
         {
            if(posInfo.SelectByIndex(i))
            {
               if(posInfo.Magic() == MAGIC_MARTINGALE)
               {
                  if(trade.PositionClose(posInfo.Ticket()))
                  {
                     closedCount++;
                     i--; // Index shifts after close
                  }
               }
            }
         }

         if(closedCount > 0)
         {
            g_partialClosed = true;
            Print("[PARTIAL CLOSE] Closed ", closedCount, "/", totalPositions, " positions (", InpPartialClosePct, "%)");
         }
      }
   }

   // Check for adding positions
   int currentLevel = (stats.totalPositions > stats.maxLevelReached) ? stats.totalPositions : stats.maxLevelReached;

   // Debug log when maximum level limit reached
   if(currentLevel >= InpMartMaxLevel)
   {
      SetTradeStatus("MAX LEVEL - wait TP");
      static datetime lastMaxLevelLog = 0;
      if(TimeCurrent() - lastMaxLevelLog >= 60)
      {
         lastMaxLevelLog = TimeCurrent();
         Print("[MART-DEBUG] Cannot add more positions: reached max level ", InpMartMaxLevel, " (current positions: ", stats.totalPositions, ")");
      }
      return;
   }

   if(currentLevel < InpMartMaxLevel)
   {
      // Cooldown: prevent rapid-fire add (L7->L8->L9 in same minute/seconds)
      if(g_lastMartAddTime > 0 && (TimeCurrent() - g_lastMartAddTime) < InpMartCooldownMinutes * 60)
      {
         SetTradeStatus("WAIT COOLDOWN");
         return;
      }

      double lastPrice = GetLastEntryPrice(MAGIC_MARTINGALE);

      // Use absolute value for distance (FIX: distance can be negative bug)
      double distancePips = MathAbs(PriceToPips(lastPrice - price));

      // Smart Dynamic Grid: reads chart volatility + scales with level
      double activeMinDistance = InpMartMinDistance;
      double activeFallbackDistance = InpMartFallbackDist;

      // 1) ATR-based: when market moves fast, grid widens automatically
      if(g_handleAtr != INVALID_HANDLE)
      {
         double atrValues[];
         ArraySetAsSeries(atrValues, true);
         if(CopyBuffer(g_handleAtr, 0, 0, 1, atrValues) > 0)
         {
            double atrPips = PriceToPips(atrValues[0]);
            double atrMultiplier = InpMartUseATR ? InpMartAtrMultiplier : 1.0;
            double dynamicAtrDist = atrPips * atrMultiplier;
            activeMinDistance = MathMax(InpMartMinDistance, dynamicAtrDist);
            activeFallbackDistance = MathMax(InpMartFallbackDist, dynamicAtrDist * 1.5);
         }
      }

      // 2) Level scaling: deeper levels = wider spacing (bigger lots = need more room)
      //    L1-L3: x1.0 (normal), L4-L6: x1.3, L7-L9: x1.6, L10+: x2.0
      double levelMultiplier = 1.0;
      if(currentLevel >= 10)
         levelMultiplier = 2.0;
      else if(currentLevel >= 7)
         levelMultiplier = 1.6;
      else if(currentLevel >= 4)
         levelMultiplier = 1.3;

      activeMinDistance *= levelMultiplier;
      activeFallbackDistance *= levelMultiplier;

      // Minimum distance check
      if(distancePips < activeMinDistance)
      {
         SetTradeStatus("WAIT DISTANCE L" + IntegerToString(currentLevel + 1));
         static datetime lastDistLog = 0;
         if(TimeCurrent() - lastDistLog >= 60)
         {
            lastDistLog = TimeCurrent();
            Print("[MART-DEBUG] Can't add L", currentLevel + 1, ": price distance ", DoubleToString(distancePips, 1), " pips < minimum required ", DoubleToString(activeMinDistance, 1), " pips");
         }
         return;
      }

      // Additional check: price must move against position (loss condition)
      bool priceMovedAgainst = false;
      if(direction == DIR_BUY && price < lastPrice)
         priceMovedAgainst = true;
      else if(direction == DIR_SELL && price > lastPrice)
         priceMovedAgainst = true;

      if(!priceMovedAgainst)
      {
         SetTradeStatus("WAIT PROFIT/AGAINST");
         static datetime lastAgainstLog = 0;
         if(TimeCurrent() - lastAgainstLog >= 60)
         {
            lastAgainstLog = TimeCurrent();
            Print("[MART-DEBUG] Can't add L", currentLevel + 1, ": price did not move against current direction (profit condition - wait)");
         }
         return;
      }

      // Session multiplier
      double sessionMult = GetSessionMultiplier();

      string newsReason = "";
      if(InpNewsBlockAddOrders && IsInManualNewsWindow(newsReason))
      {
         SetTradeStatus("WAIT NEWS - no add order");
         static datetime lastNewsAddLog = 0;
         if(TimeCurrent() - lastNewsAddLog >= 60)
         {
            lastNewsAddLog = TimeCurrent();
            Print("[NEWS-FILTER] Martingale add L", currentLevel + 1, " blocked: ", newsReason);
         }
         return;
      }

      // Check SMC/SMS signal. Distance is only a safety throttle; it is not the entry trigger.
      SmcSignal signal;
      signal.valid = false;
      signal.score = 0;
      signal.reason = "";
      signal.waiting = "";
      bool shouldEnter = false;
      string reason = "";
      int nextLevel = currentLevel + 1;

      if(!InpMartStrictSmcEntry)
      {
         // L2-L3: distance is enough. L4+ must wait for a real recovery setup.
         if(nextLevel <= 3)
         {
            shouldEnter = true;
            reason = IntegerToString((int)distancePips) + "p distance";
         }
         else
         {
            string smartReason = "";
            string smartWaiting = "";
            if(CheckMartingaleSmartAddEntry(direction, nextLevel, smartReason, smartWaiting))
            {
               shouldEnter = true;
               reason = IntegerToString((int)distancePips) + "p+" + smartReason;
            }
            else
               signal.waiting = smartWaiting;
         }
      }
      else
      {
         signal = CheckMartingaleSmcPrecisionEntry(direction, true);
      }

      if(!shouldEnter && signal.valid)
      {
         shouldEnter = true;
         reason = IntegerToString((int)distancePips) + "p+" + signal.reason;
      }
      else if(!shouldEnter && InpMartAllowFallbackAdd && distancePips >= activeFallbackDistance * sessionMult)
      {
         // Fallback: allow add even without FVG if distance is very far
         shouldEnter = true;
         reason = "Fallback " + IntegerToString((int)distancePips) + "p";
      }

      if(!shouldEnter)
      {
         string waitText = signal.waiting == "" ? "WAIT SMART ENTRY" : "WAIT " + signal.waiting;
         SetTradeStatus(StringSubstr(waitText, 0, 32));
         static datetime lastNoEnterLog = 0;
         if(TimeCurrent() - lastNoEnterLog >= 60)
         {
            lastNoEnterLog = TimeCurrent();
            Print("[MART-DEBUG] Can't add L", currentLevel + 1, ": strict SMC/SMS gate not ready (", signal.waiting,
                  "). Distance=", DoubleToString(distancePips, 1),
                  "p Fallback=", (InpMartAllowFallbackAdd ? "ON" : "OFF"));
         }
      }

      if(shouldEnter)
      {
         double nextLot = NormalizeLot(InpBaseLot * MathPow(InpMartMultiplier, nextLevel - 1));

         // Check max lot
         if(GetTotalLot() + nextLot > InpMaxTotalLot)
         {
            Print("Max lot reached at level ", nextLevel, ", lot needed: ", DoubleToString(nextLot, 2));
            SetTradeStatus("WAIT MAX LOT");
            return;
         }

         // Calculate potential risk
         double totalLotAfterAdd = stats.totalLot + nextLot;
         Print("Adding Martingale L", nextLevel, " - Lot: ", DoubleToString(nextLot, 2),
               " Total: ", DoubleToString(totalLotAfterAdd, 2));

         string comment = "Mart L" + IntegerToString(nextLevel) + " " + reason;

         if(OpenOrderWithRetry(direction, nextLot, 0, 0, comment))
         {
            g_lastMartAddTime = TimeCurrent();
            SetTradeStatus("OPENED L" + IntegerToString(nextLevel));
            Print("Martingale L", nextLevel, " added: ", reason);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Close All Positions With Retry                                    |
//+------------------------------------------------------------------+
bool CloseAllPositionsWithRetry(int magic)
{
   int closeCount = 0;
   int failCount = 0;
   double totalProfit = 0;
   int maxRounds = 3; // Try up to 3 complete rounds

   for(int round = 1; round <= maxRounds; round++)
   {
      bool anyFound = false;
      failCount = 0;

      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(posInfo.SelectByIndex(i))
         {
            if(posInfo.Symbol() == _Symbol && posInfo.Magic() == magic)
            {
               anyFound = true;
               totalProfit += posInfo.Profit();
               ulong ticket = posInfo.Ticket();

               if(ClosePositionWithRetry(ticket))
               {
                  closeCount++;
                  Print("[CLOSE-ALL] Round ", round, " - Ticket ", ticket, " closed OK");
               }
               else
               {
                  failCount++;
                  LogError("[CLOSE-ALL] Round " + IntegerToString(round) + " - Failed ticket: " + IntegerToString((int)ticket));
               }
            }
         }
      }

      // Re-check: are there any positions left?
      BotStats checkStats = GetBotStats(magic);
      if(checkStats.totalPositions == 0)
      {
         Print("[CLOSE-ALL] All positions closed after round ", round, "!");
         UpdateTradeStats(totalProfit);
         return true;
      }

      if(!anyFound)
         break;

      if(round < maxRounds)
      {
         Print("[CLOSE-ALL] Round ", round, " done. Remaining: ", checkStats.totalPositions, ". Retrying...");
         Sleep(200);
      }
   }

   // Final check
   BotStats finalStats = GetBotStats(magic);
   Print("Close result: Closed=", closeCount, " Remaining=", finalStats.totalPositions, " Profit=$", DoubleToString(totalProfit, 2));

   if(finalStats.totalPositions == 0)
   {
      UpdateTradeStats(totalProfit);
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Draw Horizontal Line With Label                                   |
//+------------------------------------------------------------------+
void DrawHLineWithLabel(string lineName, string labelName, double priceLevel,
                        color clr, ENUM_LINE_STYLE style, int lineWidth, string text)
{
   // Horizontal line
   if(ObjectFind(0, lineName) < 0)
      ObjectCreate(0, lineName, OBJ_HLINE, 0, 0, priceLevel);
   ObjectSetDouble(0, lineName, OBJPROP_PRICE, priceLevel);
   ObjectSetInteger(0, lineName, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, lineName, OBJPROP_STYLE, style);
   ObjectSetInteger(0, lineName, OBJPROP_WIDTH, lineWidth);
   ObjectSetInteger(0, lineName, OBJPROP_BACK, false);
   ObjectSetInteger(0, lineName, OBJPROP_SELECTABLE, false);
   ObjectSetString(0, lineName, OBJPROP_TEXT, text);

   // Text label on chart (right side)
   int periodSec = PeriodSeconds();
   if(periodSec <= 0) periodSec = 60;
   datetime lblTime = TimeCurrent() + periodSec * 3;
   if(ObjectFind(0, labelName) < 0)
      ObjectCreate(0, labelName, OBJ_TEXT, 0, lblTime, priceLevel);
   ObjectMove(0, labelName, 0, lblTime, priceLevel);
   ObjectSetString(0, labelName, OBJPROP_TEXT, text);
   ObjectSetInteger(0, labelName, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, labelName, OBJPROP_FONTSIZE, 8);
   ObjectSetString(0, labelName, OBJPROP_FONT, "Arial Bold");
   ObjectSetInteger(0, labelName, OBJPROP_ANCHOR, ANCHOR_LEFT);
   ObjectSetInteger(0, labelName, OBJPROP_SELECTABLE, false);
}

//+------------------------------------------------------------------+
//| Delete TP/Avg/BE Lines                                            |
//+------------------------------------------------------------------+
void DeleteTPLines()
{
   ObjectDelete(0, "PSS_TP_Line");
   ObjectDelete(0, "PSS_TP_Label");
   ObjectDelete(0, "PSS_Avg_Line");
   ObjectDelete(0, "PSS_Avg_Label");
   ObjectDelete(0, "PSS_BE_Line");
   ObjectDelete(0, "PSS_BE_Label");
}

//+------------------------------------------------------------------+
//| Draw TP / Avg Price / BE Lines on Chart                           |
//+------------------------------------------------------------------+
void DrawTPLines()
{
   int magic = GetMagicNumber();
   BotStats stats = GetBotStats(magic);

   // No positions - clean up all lines
   if(stats.totalPositions == 0)
   {
      g_calcTPPrice = 0;
      g_calcTargetProfit = 0;
      DeleteTPLines();
      return;
   }

   // ===== AVG PRICE LINE (Gold/Yellow dashed) =====
   DrawHLineWithLabel("PSS_Avg_Line", "PSS_Avg_Label", stats.avgPrice,
                      clrGold, STYLE_DASH, 1,
                      "Avg: " + DoubleToString(stats.avgPrice, _Digits));

   // ===== TP LINE (Lime/Green solid) =====
   if(InpBotMode == BOT_MARTINGALE && g_calcTPPrice > 0)
   {
      // Martingale: TP from $ target calculation
      DrawHLineWithLabel("PSS_TP_Line", "PSS_TP_Label", g_calcTPPrice,
                         clrLime, STYLE_SOLID, 2,
                         "TP: " + DoubleToString(g_calcTPPrice, _Digits) +
                         " ($" + DoubleToString(g_calcTargetProfit, 2) + ")");
   }
   else
   {
      // Other modes (manual): get TP from position
      double posTP = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(posInfo.SelectByIndex(i) && posInfo.Magic() == magic && posInfo.Symbol() == _Symbol)
         {
            posTP = posInfo.TakeProfit();
            if(posTP > 0) break;
         }
      }
      if(posTP > 0)
      {
         DrawHLineWithLabel("PSS_TP_Line", "PSS_TP_Label", posTP,
                            clrLime, STYLE_SOLID, 2,
                            "TP: " + DoubleToString(posTP, _Digits));
      }
      else
      {
         ObjectDelete(0, "PSS_TP_Line");
         ObjectDelete(0, "PSS_TP_Label");
      }
   }

   // ===== BREAKEVEN / SL LINE (Red dotted) =====
   double slPrice = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Magic() == magic && posInfo.Symbol() == _Symbol)
      {
         slPrice = posInfo.StopLoss();
         if(slPrice > 0) break;
      }
   }

   if(slPrice > 0)
   {
      string slText = (g_breakevenMoved && InpBotMode == BOT_MARTINGALE) ?
                      "BE SL: " : "SL: ";
      DrawHLineWithLabel("PSS_BE_Line", "PSS_BE_Label", slPrice,
                         clrRed, STYLE_DOT, 1,
                         slText + DoubleToString(slPrice, _Digits));
   }
   else
   {
      ObjectDelete(0, "PSS_BE_Line");
      ObjectDelete(0, "PSS_BE_Label");
   }
}

//+------------------------------------------------------------------+
//| Create Info Panel                                                 |
//+------------------------------------------------------------------+
void DeletePanel()
{
   ObjectDelete(0, g_panelName + "_bg");
   ObjectDelete(0, g_panelName + "_header");
   ObjectDelete(0, g_panelName + "_title");
   ObjectDelete(0, g_panelName + "_subtitle");

   for(int i = 0; i < 25; i++)
   {
      ObjectDelete(0, g_panelName + "_lbl" + IntegerToString(i));
      ObjectDelete(0, g_panelName + "_val" + IntegerToString(i));
   }
}

void CreatePanel()
{
   DeletePanel();

   int x = 15, y = 20;
   int width = 320;
   int height = 470;
   color bgColor = C'25,25,40';        // Dark blue-gray
   color borderColor = C'255,215,0';   // Gold
   color textColor = clrWhiteSmoke;

   // Background with gradient effect (main panel)
   ObjectCreate(0, g_panelName + "_bg", OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_XSIZE, width);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_YSIZE, height);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_BGCOLOR, bgColor);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_COLOR, borderColor);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_WIDTH, 2);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, g_panelName + "_bg", OBJPROP_BACK, false);

   // Header background
   ObjectCreate(0, g_panelName + "_header", OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, g_panelName + "_header", OBJPROP_XDISTANCE, x + 2);
   ObjectSetInteger(0, g_panelName + "_header", OBJPROP_YDISTANCE, y + 2);
   ObjectSetInteger(0, g_panelName + "_header", OBJPROP_XSIZE, width - 4);
   ObjectSetInteger(0, g_panelName + "_header", OBJPROP_YSIZE, 45);
   ObjectSetInteger(0, g_panelName + "_header", OBJPROP_BGCOLOR, C'40,40,60');
   ObjectSetInteger(0, g_panelName + "_header", OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, g_panelName + "_header", OBJPROP_CORNER, CORNER_LEFT_UPPER);

   // Title
   ObjectCreate(0, g_panelName + "_title", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, g_panelName + "_title", OBJPROP_XDISTANCE, x + 10);
   ObjectSetInteger(0, g_panelName + "_title", OBJPROP_YDISTANCE, y + 8);
   ObjectSetString(0, g_panelName + "_title", OBJPROP_TEXT, "PSS V6 ULTIMATE EA");
   ObjectSetInteger(0, g_panelName + "_title", OBJPROP_COLOR, borderColor);
   ObjectSetInteger(0, g_panelName + "_title", OBJPROP_FONTSIZE, 11);
   ObjectSetString(0, g_panelName + "_title", OBJPROP_FONT, "Arial Black");
   ObjectSetInteger(0, g_panelName + "_title", OBJPROP_CORNER, CORNER_LEFT_UPPER);

   // Subtitle
   ObjectCreate(0, g_panelName + "_subtitle", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, g_panelName + "_subtitle", OBJPROP_XDISTANCE, x + 10);
   ObjectSetInteger(0, g_panelName + "_subtitle", OBJPROP_YDISTANCE, y + 28);
   ObjectSetString(0, g_panelName + "_subtitle", OBJPROP_TEXT, "Pro Trading System + Solution 1");
   ObjectSetInteger(0, g_panelName + "_subtitle", OBJPROP_COLOR, C'150,150,150');
   ObjectSetInteger(0, g_panelName + "_subtitle", OBJPROP_FONTSIZE, 8);
   ObjectSetString(0, g_panelName + "_subtitle", OBJPROP_FONT, "Arial");
   ObjectSetInteger(0, g_panelName + "_subtitle", OBJPROP_CORNER, CORNER_LEFT_UPPER);

   // Labels
   string labels[] = {"Mode:", "Status:", "Positions:", "Total Lot:", "Daily P&L:", "Month Closed:", "Month Total:", "Direction:", "SMC Signal:", "Session:", "News:", "Win Rate:", "DD Cur/Max:", "Last Error:", "TP Target:", "TP Price:"};
   int startY = y + 55;  // After header

   for(int i = 0; i < ArraySize(labels); i++)
   {
      string name = g_panelName + "_lbl" + IntegerToString(i);
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x + 12);
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, startY + i * 25);
      ObjectSetString(0, name, OBJPROP_TEXT, labels[i]);
      ObjectSetInteger(0, name, OBJPROP_COLOR, C'180,180,200');
      ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 9);
      ObjectSetString(0, name, OBJPROP_FONT, "Arial");
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);

      // Value label
      string valueName = g_panelName + "_val" + IntegerToString(i);
      ObjectCreate(0, valueName, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, valueName, OBJPROP_XDISTANCE, x + 110);
      ObjectSetInteger(0, valueName, OBJPROP_YDISTANCE, startY + i * 25);
      ObjectSetString(0, valueName, OBJPROP_TEXT, "-");
      ObjectSetInteger(0, valueName, OBJPROP_COLOR, clrLime);
      ObjectSetInteger(0, valueName, OBJPROP_FONTSIZE, 9);
      ObjectSetString(0, valueName, OBJPROP_FONT, "Arial Bold");
      ObjectSetInteger(0, valueName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   }
}

//+------------------------------------------------------------------+
//| Update Info Panel                                                 |
//+------------------------------------------------------------------+
void UpdatePanel()
{
   // Check if panel exists
   if(ObjectFind(0, g_panelName + "_bg") < 0) return;
   BotStats stats = GetBotStats(GetMagicNumber());
   string modeText = "";
   switch(InpBotMode)
   {
      case BOT_MANUAL:     modeText = "Manual"; break;
      case BOT_MARTINGALE: modeText = "Martingale"; break;
   }
   ObjectSetString(0, g_panelName + "_val0", OBJPROP_TEXT, modeText);
   color statusColor = clrLime;
   if(StringFind(g_tradeStatus, "WAIT") >= 0)
      statusColor = clrOrange;
   else if(StringFind(g_tradeStatus, "EXIT") >= 0 || StringFind(g_tradeStatus, "RETRY") >= 0)
      statusColor = clrYellow;
   ObjectSetString(0, g_panelName + "_val1", OBJPROP_TEXT, StringSubstr(g_tradeStatus, 0, 30));
   ObjectSetInteger(0, g_panelName + "_val1", OBJPROP_COLOR, statusColor);

    // Positions
    string posText = IntegerToString(stats.totalPositions);
    if(InpBotMode == BOT_MARTINGALE && stats.totalPositions > 0)
    {
       posText += " (L" + IntegerToString(stats.maxLevelReached) + ")";
    }
    posText += " / ";
    if(InpBotMode == BOT_MARTINGALE)
       posText += IntegerToString(InpMartMaxLevel);
    else
       posText += "-";

     ObjectSetString(0, g_panelName + "_val2", OBJPROP_TEXT, posText);

   // Total Lot
   ObjectSetString(0, g_panelName + "_val3", OBJPROP_TEXT, DoubleToString(stats.totalLot, 2) + " / " + DoubleToString(InpMaxTotalLot, 2));

   // Daily P&L
   string plText = "$" + DoubleToString(g_dailyProfit, 2);
   color plColor = g_dailyProfit >= 0 ? clrLime : clrRed;
   ObjectSetString(0, g_panelName + "_val4", OBJPROP_TEXT, plText);
   ObjectSetInteger(0, g_panelName + "_val4", OBJPROP_COLOR, plColor);

   // Monthly closed P&L from trade history
   string monthClosedText = "$" + DoubleToString(g_monthlyClosedProfit, 2);
   color monthClosedColor = g_monthlyClosedProfit >= 0 ? clrLime : clrRed;
   ObjectSetString(0, g_panelName + "_val5", OBJPROP_TEXT, monthClosedText);
   ObjectSetInteger(0, g_panelName + "_val5", OBJPROP_COLOR, monthClosedColor);

   // Monthly total P&L = closed trades this month + current floating P&L
   string monthText = "$" + DoubleToString(g_monthlyProfit, 2);
   color monthColor = g_monthlyProfit >= 0 ? clrLime : clrRed;
   ObjectSetString(0, g_panelName + "_val6", OBJPROP_TEXT, monthText);
   ObjectSetInteger(0, g_panelName + "_val6", OBJPROP_COLOR, monthColor);

   // Direction
   string dirText = "-";
   color dirColor = clrWhite;
   if(InpBotMode == BOT_MARTINGALE)
   {
      if(g_martDirection == DIR_BUY) { dirText = "BUY"; dirColor = clrLime; }
      else if(g_martDirection == DIR_SELL) { dirText = "SELL"; dirColor = clrRed; }
   }
   ObjectSetString(0, g_panelName + "_val7", OBJPROP_TEXT, dirText);
   ObjectSetInteger(0, g_panelName + "_val7", OBJPROP_COLOR, dirColor);

   // SMC Signal
   string smcText = "OB:" + IntegerToString(ArraySize(g_orderBlocks)) +
                    " LQ:" + IntegerToString(ArraySize(g_liquidityZones)) +
                    " BOS:" + IntegerToString(ArraySize(g_breaks));
   ObjectSetString(0, g_panelName + "_val8", OBJPROP_TEXT, smcText);

   // Session
   string sessionText = GetCurrentSession();
   color sessionColor = clrWhite;
   if(sessionText == "london" || sessionText == "newyork") sessionColor = clrLime;
   else if(sessionText == "asian") sessionColor = clrYellow;
   else sessionColor = clrGray;

   // Convert to uppercase manually
   string sessionUpper = sessionText;
   StringToUpper(sessionUpper);

   ObjectSetString(0, g_panelName + "_val9", OBJPROP_TEXT, sessionUpper);
   ObjectSetInteger(0, g_panelName + "_val9", OBJPROP_COLOR, sessionColor);

   // News filter state
   string newsReason = "";
   bool newsBlocked = IsInManualNewsWindow(newsReason);
   string newsText = !InpUseNewsFilter ? "OFF" : (newsBlocked ? newsReason : "CLEAR");
   ObjectSetString(0, g_panelName + "_val10", OBJPROP_TEXT, StringSubstr(newsText, 0, 28));
   ObjectSetInteger(0, g_panelName + "_val10", OBJPROP_COLOR, !InpUseNewsFilter ? clrGray : (newsBlocked ? clrOrange : clrLime));

   // Win Rate
   double winRate = 0;
   if(g_totalTrades > 0)
      winRate = (double)g_winTrades / g_totalTrades * 100.0;
   string winText = DoubleToString(winRate, 1) + "% (" + IntegerToString(g_winTrades) + "/" + IntegerToString(g_totalTrades) + ")";
   ObjectSetString(0, g_panelName + "_val11", OBJPROP_TEXT, winText);
   ObjectSetInteger(0, g_panelName + "_val11", OBJPROP_COLOR, winRate >= 50 ? clrLime : clrOrange);

   // Current floating drawdown from Balance to Equity. This is not cumulative peak DD.
   double drawdown = GetCurrentDrawdownPercent();
   string ddText = DoubleToString(drawdown, 2) + "% / " + DoubleToString(g_maxCurrentDrawdown, 2) + "%";
   color ddColor = clrLime;
   if(InpMaxDrawdownPercent > 0 && drawdown > InpMaxDrawdownPercent * 0.5) ddColor = clrOrange;
   if(InpMaxDrawdownPercent > 0 && drawdown > InpMaxDrawdownPercent * 0.8) ddColor = clrRed;
   ObjectSetString(0, g_panelName + "_val12", OBJPROP_TEXT, ddText);
   ObjectSetInteger(0, g_panelName + "_val12", OBJPROP_COLOR, ddColor);

   // Last Error
   string errText = (g_lastError == "") ? "None" : StringSubstr(g_lastError, 0, 25);
   ObjectSetString(0, g_panelName + "_val13", OBJPROP_TEXT, errText);
   ObjectSetInteger(0, g_panelName + "_val13", OBJPROP_COLOR, (g_lastError == "") ? clrLime : clrRed);

   // TP Target (Profit / Target)
   string tpTargetText = "-";
   color tpTargetColor = clrWhite;
   if(stats.totalPositions > 0)
   {
      if(InpBotMode == BOT_MARTINGALE && g_calcTargetProfit > 0)
      {
         tpTargetText = "$" + DoubleToString(stats.totalProfit, 2) + " / $" + DoubleToString(g_calcTargetProfit, 2);
         if(stats.totalProfit >= g_calcTargetProfit * 0.8)
            tpTargetColor = clrLime;
         else if(stats.totalProfit >= 0)
            tpTargetColor = clrYellow;
         else
            tpTargetColor = clrOrange;
      }
      else
      {
         tpTargetText = "$" + DoubleToString(stats.totalProfit, 2);
         tpTargetColor = stats.totalProfit >= 0 ? clrLime : clrRed;
      }
   }
   ObjectSetString(0, g_panelName + "_val14", OBJPROP_TEXT, tpTargetText);
   ObjectSetInteger(0, g_panelName + "_val14", OBJPROP_COLOR, tpTargetColor);

   // TP Price Level + Distance
   string tpPriceText = "-";
   if(stats.totalPositions > 0)
   {
      if(InpBotMode == BOT_MARTINGALE && g_calcTPPrice > 0)
      {
         double bidNow = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         double distPips = 0;
         if(stats.direction == DIR_BUY)
            distPips = PriceToPips(g_calcTPPrice - bidNow);
         else
            distPips = PriceToPips(bidNow - g_calcTPPrice);
         tpPriceText = DoubleToString(g_calcTPPrice, _Digits) + " (" + DoubleToString(distPips, 1) + "p)";
      }
      else
      {
         double posTP = 0;
         for(int i = PositionsTotal() - 1; i >= 0; i--)
         {
            if(posInfo.SelectByIndex(i) && posInfo.Magic() == GetMagicNumber())
            {
               posTP = posInfo.TakeProfit();
               if(posTP > 0) break;
            }
         }
         if(posTP > 0)
            tpPriceText = DoubleToString(posTP, _Digits);
      }
   }
   ObjectSetString(0, g_panelName + "_val15", OBJPROP_TEXT, tpPriceText);
   ObjectSetInteger(0, g_panelName + "_val15", OBJPROP_COLOR, clrCyan);
}

//+------------------------------------------------------------------+
