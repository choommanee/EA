//+------------------------------------------------------------------+
//|                                      PSS_SMC_Martingale_EA.mq5    |
//|                         Standalone SMC/SMS Martingale EA          |
//+------------------------------------------------------------------+
#property copyright "PSS"
#property version   "1.00"
#property strict
#property description "Standalone EA: SMC/SMS direction + strict liquidity/OB martingale basket"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

enum ENUM_DIRECTION
{
   DIR_NONE = 0,
   DIR_BUY  = 1,
   DIR_SELL = -1
};

enum ENUM_LOT_MODE
{
   LOT_MULTIPLIER = 0,
   LOT_LINEAR_INCREMENT = 1
};

enum ENUM_RUNAWAY_ACTION
{
   RUNAWAY_STOP_ADD = 0,
   RUNAWAY_CLOSE_BASKET = 1,
   RUNAWAY_HEDGE_ONCE = 2
};

enum ENUM_SMC_ENTRY_MODE
{
   ENTRY_KILLER_MA_GRID = 0,
   ENTRY_FAST_SMC = 1,
   ENTRY_BALANCED_SMC = 2,
   ENTRY_STRICT_SMC = 3
};

input group "=== GENERAL ==="
input ulong           InpMagic = 777771;             // Magic Number
input double          InpBaseLot = 0.03;             // Base Lot
input int             InpSlippage = 50;              // Slippage (points)
input bool            InpShowStatus = true;          // Show Chart Panel

input group "=== DEBUG LOGGING ==="
input bool            InpDebugLog = true;            // Print Backtest Decision Logs
input bool            InpLogStateEachBar = true;     // Log Basket State Each Bar
input bool            InpLogOnlyChanges = true;      // Skip Repeated Decision Logs

input group "=== MARTINGALE BASKET ==="
input ENUM_LOT_MODE   InpLotMode = LOT_LINEAR_INCREMENT; // Lot Mode
input double          InpMultiplier = 1.5;           // Lot Multiplier
input double          InpLotIncrement = 0.01;        // Linear Lot Increment
input int             InpMaxLevel = 18;              // Max Levels
input int             InpMinAddDistancePips = 20;    // Minimum adverse distance before next setup
input double          InpMaxTotalLot = 2.00;         // Max Total Lot
input double          InpProfitPer001Lot = 5.00;     // Basket Take Profit ($)
input bool            InpScaleTPByLot = false;       // Scale TP by Total Lot
input double          InpMinCloseProfitUSD = 1.00;   // Minimum Profit to Close ($)
input bool            InpUseV6PriceTP = true;        // Use V6 Avg-Price TP Backup
input bool            InpCloseAnyPositiveBasket = false; // Close recovered baskets fast
input int             InpAnyPositiveFromLevel = 1;   // Close any positive from level
input double          InpAnyPositiveProfitUSD = 0.01;// Minimum positive basket close ($)
input bool            InpUseProfitLock = false;      // Close if profit appears then fades
input double          InpProfitLockStartUSD = 0.01;  // Profit Lock Starts ($)
input double          InpProfitLockRetraceUSD = 0.01;// Close after profit retrace ($)
input double          InpProfitLockMinUSD = 0.00;    // Minimum Positive Close ($)

input group "=== SMC/SMS ENTRY ==="
input ENUM_SMC_ENTRY_MODE InpEntryMode = ENTRY_KILLER_MA_GRID; // Entry Mode
input int             InpSwingLookback = 10;         // Swing Lookback
input int             InpAnalysisBars = 220;         // Analysis Bars
input int             InpStructureLookback = 45;     // CHoCH/BOS Lookback (bars)
input int             InpLqSweepLookback = 3;        // LQ Sweep Lookback (closed bars)
input int             InpObLookback = 20;            // OB Search Lookback
input int             InpObBufferPips = 10;          // OB Entry Buffer
input bool            InpAllowFvgZone = false;       // Allow FVG as backup entry zone
input bool            InpRequirePriceAction = false; // Require Pin/Engulf confirmation
input bool            InpStopAddOnOppositeBos = true;// Stop adding after opposite BOS/CHoCH

input group "=== RISK GUARDS ==="
input double          InpDailyProfitTarget = 100.0;  // Daily Profit Target ($)
input double          InpDailyLossLimit = 1000.0;    // Daily Loss Limit ($)
input bool            InpCloseOnDailyLoss = false;   // Close basket when daily loss hit
input double          InpMaxDrawdownPercent = 12.0;  // Max Drawdown % (0=off)
input bool            InpUseDailyHLGuard = false;    // Block BUY near daily high / SELL near daily low
input int             InpDailyHLBufferPips = 20;     // Daily H/L Guard Buffer

input group "=== ANTI-RUNAWAY TREND GUARD ==="
input bool            InpUseRunawayGuard = true;     // Use Anti-Runaway Guard
input int             InpRunawayMaPeriod = 60;       // MA Period
input int             InpRunawayAdxPeriod = 14;      // ADX Period
input double          InpRunawayAdxLevel = 32.0;     // Strong Trend ADX
input int             InpRunawayDistancePips = 120;  // Max Avg Distance Before Guard
input double          InpRunawayLossPct = 2.0;       // Floating Loss % Equity
input int             InpRunawayMinLevel = 5;        // Minimum Level Before Action
input ENUM_RUNAWAY_ACTION InpRunawayAction = RUNAWAY_CLOSE_BASKET; // Runaway Action
input double          InpHedgeLotMultiplier = 1.0;   // Hedge Lot x Current Net Lot

input group "=== MULTI-TIMEFRAME FILTER ==="
input bool            InpUseMTFFilter = true;        // Use Higher TF Direction Filter
input ENUM_TIMEFRAMES InpHTFPeriod = PERIOD_H1;      // Higher TF Period
input int             InpHTFMaPeriod = 60;            // Higher TF MA Period

input group "=== EMERGENCY EXIT ==="
input bool            InpUseEmergencyExit = true;     // Emergency Exit on Pure Loss
input double          InpEmergencyLossPct = 5.0;      // Emergency Loss % Equity
input int             InpEmergencyDistPips = 200;     // Emergency Distance (pips)

input group "=== BASKET AGE GUARD ==="
input bool            InpUseBasketAge = true;         // Use Basket Age Guard
input int             InpMaxBasketAgeHours = 24;      // Max Basket Age (hours)
input int             InpStopAddAfterHours = 12;      // Stop Add After (hours)

input group "=== OPPOSITE MOMENTUM BLOCK ==="
input bool            InpBlockOnStrongOpposite = true; // Block add on strong opposite candle
input double          InpStrongCandlePips = 30;        // Strong opposite candle size (pips)

input group "=== TRADING TIME WINDOW ==="
input bool            InpUseTradingWindow = false;   // Use Time Window
input double          InpTimezoneUTCOffset = 7.0;    // Timezone UTC Offset (Thailand = 7)
input int             InpTradeStartHour = 0;         // Start Hour
input int             InpTradeStartMinute = 0;       // Start Minute
input int             InpTradeEndHour = 23;          // End Hour
input int             InpTradeEndMinute = 59;        // End Minute
input bool            InpTradeMonday = true;         // Trade Monday
input bool            InpTradeTuesday = true;        // Trade Tuesday
input bool            InpTradeWednesday = true;      // Trade Wednesday
input bool            InpTradeThursday = true;       // Trade Thursday
input bool            InpTradeFriday = true;         // Trade Friday
input bool            InpCloseBasketOutsideTime = false; // Close basket outside time

input group "=== PANEL ==="
input int             InpPanelX = 12;                // Panel X
input int             InpPanelY = 24;                // Panel Y

struct SwingPoint
{
   int      index;
   double   price;
   bool     isHigh;
   datetime time;
};

struct StructureBreak
{
   int      index;
   double   price;
   bool     isBullish;
   string   label;
   datetime time;
};

struct OrderBlock
{
   double   high;
   double   low;
   int      index;
   bool     isBullish;
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

struct SmcGate
{
   bool     valid;
   string   reason;
   string   waiting;
};

struct BasketStats
{
   int      count;
   double   lots;
   double   profit;
   double   avgPrice;
   ENUM_DIRECTION direction;
   int      maxLevel;
   double   buyLots;
   double   sellLots;
};

struct RunawayState
{
   bool     active;
   bool     trendAgainst;
   double   adx;
   double   distancePips;
   double   lossPct;
   string   reason;
};

CTrade trade;
CPositionInfo posInfo;

SwingPoint g_swings[];
StructureBreak g_breaks[];
OrderBlock g_orderBlocks[];
FairValueGap g_fvgs[];

datetime g_lastBarTime = 0;
datetime g_lastResetTime = 0;
double g_dayStartBalance = 0;
double g_peakEquity = 0;
string g_lastStatus = "";
string g_timeStatus = "";
string g_panelPrefix = "PSS_SMC_MART_PANEL";
int g_handleRunawayMA = INVALID_HANDLE;
int g_handleRunawayADX = INVALID_HANDLE;
bool g_hedgedThisBasket = false;
bool g_closePending = false;
datetime g_lastCloseAttempt = 0;
datetime g_lastStateLogBar = 0;
datetime g_lastDebugLogBar = 0;
string g_lastDebugKey = "";
double g_basketPeakProfit = 0;
bool g_basketProfitTouched = false;
double g_calcTPPrice = 0;
double g_calcTargetProfit = 0;
int g_handleHTFMA = INVALID_HANDLE;
datetime g_basketOpenTime = 0;
bool g_stopAddByAge = false;

//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpSlippage);

   g_handleRunawayMA = iMA(_Symbol, PERIOD_CURRENT, InpRunawayMaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_handleRunawayADX = iADX(_Symbol, PERIOD_CURRENT, InpRunawayAdxPeriod);
   if(g_handleRunawayMA == INVALID_HANDLE || g_handleRunawayADX == INVALID_HANDLE)
   {
      Print("ERROR: Failed to create runaway guard indicators");
      return INIT_FAILED;
   }

   if(InpUseMTFFilter)
   {
      g_handleHTFMA = iMA(_Symbol, InpHTFPeriod, InpHTFMaPeriod, 0, MODE_EMA, PRICE_CLOSE);
      if(g_handleHTFMA == INVALID_HANDLE)
         Print("WARNING: HTF MA indicator failed, MTF filter disabled");
   }

   g_dayStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   g_peakEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_lastResetTime = TimeCurrent();

   UpdateSmcAnalysis();
   if(InpShowStatus)
      CreatePanel();

   Print("PSS SMC Martingale EA initialized | Symbol=", _Symbol,
         " | Magic=", IntegerToString((int)InpMagic));
   DebugLog("INIT",
            "magic=" + IntegerToString((int)InpMagic) +
            "|baseLot=" + DoubleToString(InpBaseLot, 2) +
            "|lotMode=" + EnumToString(InpLotMode) +
            "|entryMode=" + EntryModeText() +
            "|maxLevel=" + IntegerToString(InpMaxLevel) +
            "|maxTotalLot=" + DoubleToString(InpMaxTotalLot, 2) +
            "|minCloseProfit=" + DoubleToString(InpMinCloseProfitUSD, 2) +
            "|v6PriceTP=" + (InpUseV6PriceTP ? "ON" : "OFF") +
            "|closeAnyPositive=" + (InpCloseAnyPositiveBasket ? "ON" : "OFF") +
            "|profitLock=" + (InpUseProfitLock ? "ON" : "OFF") +
            "|runaway=" + (InpUseRunawayGuard ? "ON" : "OFF") +
            "|timeWindow=" + (InpUseTradingWindow ? "ON" : "OFF") +
            "|mtfFilter=" + (InpUseMTFFilter ? "ON" : "OFF") +
            "|emergencyExit=" + (InpUseEmergencyExit ? "ON" : "OFF") +
            "|basketAge=" + (InpUseBasketAge ? "ON" : "OFF") +
            "|oppMomentum=" + (InpBlockOnStrongOpposite ? "ON" : "OFF"),
            true);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Comment("");
   ObjectsDeleteAll(0, g_panelPrefix);
   if(g_handleRunawayMA != INVALID_HANDLE) IndicatorRelease(g_handleRunawayMA);
   if(g_handleRunawayADX != INVALID_HANDLE) IndicatorRelease(g_handleRunawayADX);
   if(g_handleHTFMA != INVALID_HANDLE) IndicatorRelease(g_handleHTFMA);
   DebugLog("DEINIT", "reason=" + IntegerToString(reason), true);
   Print("PSS SMC Martingale EA deinitialized");
}

//+------------------------------------------------------------------+
void OnTick()
{
   CheckDailyReset();

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime != g_lastBarTime)
   {
      g_lastBarTime = barTime;
      UpdateSmcAnalysis();
   }

   RunSmcMartingale();

   if(InpShowStatus)
      UpdatePanel();
   else
      Comment(g_lastStatus);
}

//+------------------------------------------------------------------+
double PipSize()
{
   return _Point * 10.0;
}

double PipsToPrice(double pips)
{
   return pips * PipSize();
}

double PriceToPips(double priceDistance)
{
   return priceDistance / PipSize();
}

double NormalizeLot(double lot)
{
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   if(step <= 0)
      step = 0.01;

   lot = MathFloor(lot / step) * step;
   lot = MathMax(minLot, MathMin(maxLot, lot));
   return NormalizeDouble(lot, 2);
}

double MidPrice()
{
   return (SymbolInfoDouble(_Symbol, SYMBOL_BID) + SymbolInfoDouble(_Symbol, SYMBOL_ASK)) / 2.0;
}

string DirectionText(ENUM_DIRECTION direction)
{
   if(direction == DIR_BUY)
      return "BUY";
   if(direction == DIR_SELL)
      return "SELL";
   return "WAIT";
}

string EntryModeText()
{
   if(InpEntryMode == ENTRY_KILLER_MA_GRID)
      return "KILLER_MA_GRID";
   if(InpEntryMode == ENTRY_FAST_SMC)
      return "FAST_SMC";
   if(InpEntryMode == ENTRY_BALANCED_SMC)
      return "BALANCED_SMC";
   return "STRICT_SMC";
}

ENUM_DIRECTION GetHTFDirection(string &reason)
{
   reason = "";
   if(!InpUseMTFFilter || g_handleHTFMA == INVALID_HANDLE)
      return DIR_NONE;

   double htfMa[];
   double htfClose[];
   ArraySetAsSeries(htfMa, true);
   ArraySetAsSeries(htfClose, true);

   if(CopyBuffer(g_handleHTFMA, 0, 0, 3, htfMa) <= 0 ||
      CopyClose(_Symbol, InpHTFPeriod, 0, 3, htfClose) <= 0)
   {
      reason = "HTF data not ready";
      return DIR_NONE;
   }

   if(htfClose[1] >= htfMa[1])
   {
      reason = "HTF BUY";
      return DIR_BUY;
   }

   reason = "HTF SELL";
   return DIR_SELL;
}

ENUM_DIRECTION GetKillerMaDirection(string &reason)
{
   reason = "";

   double ma[], close[];
   ArraySetAsSeries(ma, true);
   ArraySetAsSeries(close, true);

   if(CopyBuffer(g_handleRunawayMA, 0, 0, 3, ma) <= 0 ||
      CopyClose(_Symbol, PERIOD_CURRENT, 0, 3, close) <= 0)
   {
      reason = "MA data not ready";
      return DIR_NONE;
   }

   double refClose = close[1];
   double refMa = ma[1];
   ENUM_DIRECTION currentDir = DIR_NONE;
   if(refClose >= refMa)
      currentDir = DIR_BUY;
   else
      currentDir = DIR_SELL;

   // MTF Filter: block if higher TF disagrees
   if(InpUseMTFFilter)
   {
      string htfReason = "";
      ENUM_DIRECTION htfDir = GetHTFDirection(htfReason);
      if(htfDir != DIR_NONE && htfDir != currentDir)
      {
         reason = "MA" + IntegerToString(InpRunawayMaPeriod) + " " + DirectionText(currentDir) +
                  " BLOCKED by " + htfReason;
         DebugLog("MTF", "block|currentDir=" + DirectionText(currentDir) +
                  "|htfDir=" + DirectionText(htfDir) + "|" + htfReason, false);
         return DIR_NONE;
      }
   }

   reason = "MA" + IntegerToString(InpRunawayMaPeriod) + " bias " + DirectionText(currentDir);
   return currentDir;
}

ENUM_DIRECTION GetEntryDirection(string &reason)
{
   if(InpEntryMode == ENTRY_KILLER_MA_GRID)
      return GetKillerMaDirection(reason);

   ENUM_DIRECTION direction = GetLatestSmcDirection();
   reason = "latest SMC " + DirectionText(direction);
   return direction;
}

string TimeframeText()
{
   return EnumToString((ENUM_TIMEFRAMES)_Period);
}

void DebugLog(string tag, string message, bool force = false)
{
   if(!InpDebugLog)
      return;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   string key = tag + "|" + message;
   if(!force && InpLogOnlyChanges && key == g_lastDebugKey && barTime == g_lastDebugLogBar)
      return;

   g_lastDebugKey = key;
   g_lastDebugLogBar = barTime;

   Print("PSSDBG|", tag,
         "|server=", TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
         "|symbol=", _Symbol,
         "|tf=", TimeframeText(),
         "|", message);
}

string BasketSummary(BasketStats &stats)
{
   return "pos=" + IntegerToString(stats.count) +
          "|dir=" + DirectionText(stats.direction) +
          "|level=" + IntegerToString(stats.maxLevel) + "/" + IntegerToString(InpMaxLevel) +
          "|lots=" + DoubleToString(stats.lots, 2) + "/" + DoubleToString(InpMaxTotalLot, 2) +
          "|buyLots=" + DoubleToString(stats.buyLots, 2) +
          "|sellLots=" + DoubleToString(stats.sellLots, 2) +
          "|avg=" + DoubleToString(stats.avgPrice, _Digits) +
          "|pl=" + DoubleToString(stats.profit, 2);
}

void LogBasketState(BasketStats &stats, double targetProfit)
{
   if(!InpDebugLog || !InpLogStateEachBar)
      return;

   datetime barTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(barTime == g_lastStateLogBar)
      return;

   g_lastStateLogBar = barTime;
   DebugLog("STATE",
            BasketSummary(stats) +
            "|target=" + DoubleToString(targetProfit, 2) +
            "|daily=" + DoubleToString(DailyPnL(), 2) +
            "|equity=" + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2) +
            "|balance=" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2) +
            "|breaks=" + IntegerToString(ArraySize(g_breaks)) +
            "|ob=" + IntegerToString(ArraySize(g_orderBlocks)) +
            "|fvg=" + IntegerToString(ArraySize(g_fvgs)),
            true);
}

datetime LocalTradingTime()
{
   return TimeGMT() + (int)MathRound(InpTimezoneUTCOffset * 3600.0);
}

bool IsTradeDayAllowed(int dayOfWeek)
{
   if(dayOfWeek == 1)
      return InpTradeMonday;
   if(dayOfWeek == 2)
      return InpTradeTuesday;
   if(dayOfWeek == 3)
      return InpTradeWednesday;
   if(dayOfWeek == 4)
      return InpTradeThursday;
   if(dayOfWeek == 5)
      return InpTradeFriday;
   return false;
}

bool IsTradingTimeAllowed(string &reason)
{
   if(!InpUseTradingWindow)
   {
      g_timeStatus = "Window OFF";
      return true;
   }

   datetime local = LocalTradingTime();
   MqlDateTime dt;
   TimeToStruct(local, dt);

   if(!IsTradeDayAllowed(dt.day_of_week))
   {
      reason = "outside trading day";
      g_timeStatus = TimeToString(local, TIME_MINUTES) + " blocked day";
      return false;
   }

   int nowMin = dt.hour * 60 + dt.min;
   int startMin = MathMax(0, MathMin(1439, InpTradeStartHour * 60 + InpTradeStartMinute));
   int endMin = MathMax(0, MathMin(1439, InpTradeEndHour * 60 + InpTradeEndMinute));

   bool allowed = false;
   if(startMin <= endMin)
      allowed = (nowMin >= startMin && nowMin <= endMin);
   else
      allowed = (nowMin >= startMin || nowMin <= endMin);

   string window = StringFormat("%02d:%02d-%02d:%02d UTC%+.1f",
                                InpTradeStartHour, InpTradeStartMinute,
                                InpTradeEndHour, InpTradeEndMinute,
                                InpTimezoneUTCOffset);

   if(!allowed)
   {
      reason = "outside time window";
      g_timeStatus = TimeToString(local, TIME_MINUTES) + " outside " + window;
      return false;
   }

   g_timeStatus = TimeToString(local, TIME_MINUTES) + " inside " + window;
   return true;
}

void CreatePanel()
{
   ObjectsDeleteAll(0, g_panelPrefix);

   string bg = g_panelPrefix + "_BG";
   ObjectCreate(0, bg, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, bg, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, bg, OBJPROP_XDISTANCE, InpPanelX);
   ObjectSetInteger(0, bg, OBJPROP_YDISTANCE, InpPanelY);
   ObjectSetInteger(0, bg, OBJPROP_XSIZE, 330);
   ObjectSetInteger(0, bg, OBJPROP_YSIZE, 286);
   ObjectSetInteger(0, bg, OBJPROP_BGCOLOR, C'18,22,28');
   ObjectSetInteger(0, bg, OBJPROP_COLOR, C'70,90,110');
   ObjectSetInteger(0, bg, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, bg, OBJPROP_BACK, false);

   string title = g_panelPrefix + "_TITLE";
   ObjectCreate(0, title, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, title, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, title, OBJPROP_XDISTANCE, InpPanelX + 12);
   ObjectSetInteger(0, title, OBJPROP_YDISTANCE, InpPanelY + 10);
   ObjectSetString(0, title, OBJPROP_TEXT, "PSS SMC MARTINGALE");
   ObjectSetInteger(0, title, OBJPROP_COLOR, C'80,210,180');
   ObjectSetInteger(0, title, OBJPROP_FONTSIZE, 10);
   ObjectSetString(0, title, OBJPROP_FONT, "Arial Bold");

   string rows[] = {"Mode", "Local Time", "Direction", "Gate", "Basket", "Lot", "P/L", "Target", "Daily", "SMC Data", "Next"};
   for(int i = 0; i < ArraySize(rows); i++)
   {
      int y = InpPanelY + 42 + i * 21;

      string label = g_panelPrefix + "_L" + IntegerToString(i);
      ObjectCreate(0, label, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, label, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, label, OBJPROP_XDISTANCE, InpPanelX + 12);
      ObjectSetInteger(0, label, OBJPROP_YDISTANCE, y);
      ObjectSetString(0, label, OBJPROP_TEXT, rows[i] + ":");
      ObjectSetInteger(0, label, OBJPROP_COLOR, C'170,182,195');
      ObjectSetInteger(0, label, OBJPROP_FONTSIZE, 8);
      ObjectSetString(0, label, OBJPROP_FONT, "Arial");

      string value = g_panelPrefix + "_V" + IntegerToString(i);
      ObjectCreate(0, value, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, value, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, value, OBJPROP_XDISTANCE, InpPanelX + 105);
      ObjectSetInteger(0, value, OBJPROP_YDISTANCE, y);
      ObjectSetString(0, value, OBJPROP_TEXT, "-");
      ObjectSetInteger(0, value, OBJPROP_COLOR, clrWhite);
      ObjectSetInteger(0, value, OBJPROP_FONTSIZE, 8);
      ObjectSetString(0, value, OBJPROP_FONT, "Arial Bold");
   }
}

void SetPanelValue(int row, string value, color clr = clrWhite)
{
   string name = g_panelPrefix + "_V" + IntegerToString(row);
   if(ObjectFind(0, name) < 0)
      return;

   if(StringLen(value) > 38)
      value = StringSubstr(value, 0, 35) + "...";

   ObjectSetString(0, name, OBJPROP_TEXT, value);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

void UpdatePanel()
{
   if(ObjectFind(0, g_panelPrefix + "_BG") < 0)
      CreatePanel();

   BasketStats stats = GetBasketStats();
   string entryReason = "";
   ENUM_DIRECTION latestDir = GetEntryDirection(entryReason);
   string timeReason = "";
   bool timeAllowed = IsTradingTimeAllowed(timeReason);

   double targetProfit = CalculateTargetProfit(stats);
   if(stats.count > 0)
   {
      g_calcTargetProfit = targetProfit;
      g_calcTPPrice = CalculateV6TPPrice(stats, targetProfit);
   }
   RunawayState runaway = DetectRunaway(stats);

   string gateText = "-";
   color gateColor = clrWhite;
   if(stats.count == 0)
   {
      SmcGate gate = CheckEntryGate(latestDir, false);
      gateText = gate.valid ? gate.reason : gate.waiting;
      gateColor = gate.valid ? clrLime : clrOrange;
   }
   else
   {
      SmcGate gate = CheckEntryGate(stats.direction, true);
      gateText = gate.valid ? gate.reason : gate.waiting;
      gateColor = gate.valid ? clrLime : clrOrange;
   }

   color pnlColor = stats.profit >= 0 ? clrLime : clrTomato;
   double daily = DailyPnL();
   color dailyColor = daily >= 0 ? clrLime : clrTomato;

   SetPanelValue(0, (timeAllowed ? "ACTIVE " : "TIME BLOCK ") + EntryModeText(), timeAllowed ? clrLime : clrTomato);
   SetPanelValue(1, g_timeStatus, timeAllowed ? clrLime : clrOrange);
   SetPanelValue(2, stats.count > 0 ? DirectionText(stats.direction) : DirectionText(latestDir),
                 (stats.count > 0 || latestDir != DIR_NONE) ? clrDeepSkyBlue : clrSilver);
   SetPanelValue(3, gateText, gateColor);
   SetPanelValue(4, IntegerToString(stats.count) + " pos | L" + IntegerToString(stats.maxLevel) + "/" + IntegerToString(InpMaxLevel) +
                    (HasHedgePosition(stats) ? " | HEDGE" : ""));
   SetPanelValue(5, DoubleToString(stats.lots, 2) + " / " + DoubleToString(InpMaxTotalLot, 2));
   SetPanelValue(6, "$" + DoubleToString(stats.profit, 2), pnlColor);
   if(g_calcTPPrice > 0)
      SetPanelValue(7, "$" + DoubleToString(targetProfit, 2) + " @ " + DoubleToString(g_calcTPPrice, _Digits));
   else
      SetPanelValue(7, "$" + DoubleToString(targetProfit, 2));
   SetPanelValue(8, "$" + DoubleToString(daily, 2), dailyColor);
   SetPanelValue(9, "BOS " + IntegerToString(ArraySize(g_breaks)) +
                    " | OB " + IntegerToString(ArraySize(g_orderBlocks)) +
                    " | FVG " + IntegerToString(ArraySize(g_fvgs)));
   if(runaway.active)
      SetPanelValue(10, runaway.reason, clrTomato);
   else
      SetPanelValue(10, g_lastStatus, clrWhite);
}

//+------------------------------------------------------------------+
void CheckDailyReset()
{
   MqlDateTime now, last;
   TimeToStruct(TimeCurrent(), now);
   TimeToStruct(g_lastResetTime, last);

   if(now.day != last.day || now.mon != last.mon || now.year != last.year)
   {
      g_dayStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      g_peakEquity = AccountInfoDouble(ACCOUNT_EQUITY);
      g_lastResetTime = TimeCurrent();
      Print("[DAILY] Reset daily counters");
   }
}

double DailyPnL()
{
   double pnl = AccountInfoDouble(ACCOUNT_BALANCE) - g_dayStartBalance;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == (long)InpMagic)
         pnl += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
   }
   return pnl;
}

bool RiskAllowsTrading(BasketStats &stats)
{
   double daily = DailyPnL();

   if(stats.count == 0)
   {
      if(daily >= InpDailyProfitTarget)
      {
         g_lastStatus = "Daily profit target reached: $" + DoubleToString(daily, 2);
         DebugLog("RISK", "block new basket|dailyProfitTarget|daily=" + DoubleToString(daily, 2), false);
         return false;
      }

      if(daily <= -InpDailyLossLimit)
      {
         g_lastStatus = "Daily loss limit reached: $" + DoubleToString(daily, 2);
         DebugLog("RISK", "block new basket|dailyLossLimit|daily=" + DoubleToString(daily, 2), false);
         return false;
      }
   }
   else if(InpCloseOnDailyLoss && daily <= -InpDailyLossLimit)
   {
      Print("[RISK] Daily loss hit. Closing basket. Daily=$", DoubleToString(daily, 2));
      DebugLog("RISK", "close basket|dailyLossLimit|daily=" + DoubleToString(daily, 2) + "|" + BasketSummary(stats), true);
      g_closePending = true;
      CloseAllBasket();
      return false;
   }

   if(InpMaxDrawdownPercent > 0)
   {
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      if(equity > g_peakEquity)
         g_peakEquity = equity;

      double dd = 0;
      if(g_peakEquity > 0)
         dd = ((g_peakEquity - equity) / g_peakEquity) * 100.0;

      if(dd >= InpMaxDrawdownPercent)
      {
         Print("[RISK] Max drawdown hit: ", DoubleToString(dd, 1), "%. Closing basket.");
         DebugLog("RISK", "close basket|maxDrawdown|dd=" + DoubleToString(dd, 1) + "%|" + BasketSummary(stats), true);
         g_closePending = true;
         CloseAllBasket();
         return false;
      }
   }

   return true;
}

//+------------------------------------------------------------------+
BasketStats GetBasketStats()
{
   BasketStats stats;
   stats.count = 0;
   stats.lots = 0;
   stats.profit = 0;
   stats.avgPrice = 0;
   stats.direction = DIR_NONE;
   stats.maxLevel = 0;
   stats.buyLots = 0;
   stats.sellLots = 0;

   double weighted = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!posInfo.SelectByIndex(i))
         continue;
      if(posInfo.Symbol() != _Symbol || posInfo.Magic() != (long)InpMagic)
         continue;

      stats.count++;
      stats.lots += posInfo.Volume();
      stats.profit += posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
      weighted += posInfo.PriceOpen() * posInfo.Volume();

      if(posInfo.PositionType() == POSITION_TYPE_BUY)
         stats.buyLots += posInfo.Volume();
      else
         stats.sellLots += posInfo.Volume();

      string comment = posInfo.Comment();
      int idx = StringFind(comment, "L");
      if(idx >= 0)
      {
         int lvl = (int)StringToInteger(StringSubstr(comment, idx + 1, 2));
         if(lvl > stats.maxLevel)
            stats.maxLevel = lvl;
      }
   }

   if(stats.lots > 0)
      stats.avgPrice = weighted / stats.lots;
   if(stats.maxLevel == 0)
      stats.maxLevel = stats.count;

   if(stats.buyLots > stats.sellLots)
      stats.direction = DIR_BUY;
   else if(stats.sellLots > stats.buyLots)
      stats.direction = DIR_SELL;

   return stats;
}

double GetLastEntryPrice()
{
   double price = 0;
   datetime lastTime = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == (long)InpMagic)
      {
         if(posInfo.Time() > lastTime)
         {
            lastTime = posInfo.Time();
            price = posInfo.PriceOpen();
         }
      }
   }

   return price;
}

bool OpenBasketOrder(ENUM_DIRECTION direction, double lot, string comment)
{
   lot = NormalizeLot(lot);
   if(lot <= 0)
   {
      DebugLog("ORDER", "skip open|invalidLot|dir=" + DirectionText(direction) + "|lot=" + DoubleToString(lot, 2), true);
      return false;
   }

   bool result = false;

   if(direction == DIR_BUY)
      result = trade.Buy(lot, _Symbol, 0, 0, 0, comment);
   else if(direction == DIR_SELL)
      result = trade.Sell(lot, _Symbol, 0, 0, 0, comment);
   else
   {
      DebugLog("ORDER", "skip open|invalidDirection|comment=" + comment, true);
      return false;
   }

   DebugLog("ORDER",
            "open " + DirectionText(direction) +
            "|lot=" + DoubleToString(lot, 2) +
            "|bid=" + DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_BID), _Digits) +
            "|ask=" + DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_ASK), _Digits) +
            "|comment=" + comment +
            "|ok=" + (result ? "true" : "false") +
            "|retcode=" + IntegerToString((int)trade.ResultRetcode()) +
            "|desc=" + trade.ResultRetcodeDescription(),
            true);

   return result;
}

bool CloseAllBasket()
{
   bool ok = true;
   int finalRemaining = 0;

   for(int round = 0; round < 3; round++)
   {
      int remaining = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == (long)InpMagic)
         {
            remaining++;
            ulong ticket = posInfo.Ticket();
            double volume = posInfo.Volume();
            double profit = posInfo.Profit() + posInfo.Swap() + posInfo.Commission();
            string type = (posInfo.PositionType() == POSITION_TYPE_BUY) ? "BUY" : "SELL";
            if(!trade.PositionClose(posInfo.Ticket()))
            {
               ok = false;
               DebugLog("CLOSE",
                        "close failed|round=" + IntegerToString(round + 1) +
                        "|ticket=" + IntegerToString((long)ticket) +
                        "|type=" + type +
                        "|lot=" + DoubleToString(volume, 2) +
                        "|pl=" + DoubleToString(profit, 2) +
                        "|retcode=" + IntegerToString((int)trade.ResultRetcode()) +
                        "|desc=" + trade.ResultRetcodeDescription(),
                        true);
            }
            else
            {
               DebugLog("CLOSE",
                        "close sent|round=" + IntegerToString(round + 1) +
                        "|ticket=" + IntegerToString((long)ticket) +
                        "|type=" + type +
                        "|lot=" + DoubleToString(volume, 2) +
                        "|pl=" + DoubleToString(profit, 2) +
                        "|retcode=" + IntegerToString((int)trade.ResultRetcode()) +
                        "|desc=" + trade.ResultRetcodeDescription(),
                        true);
            }
         }
      }
      if(remaining == 0)
      {
         g_closePending = false;
         ResetBasketProfitTracker();
         DebugLog("CLOSE", "basket flat|ok=" + (ok ? "true" : "false"), true);
         return ok;
      }
      Sleep(150);
   }

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == (long)InpMagic)
         finalRemaining++;
   }

   g_closePending = (finalRemaining > 0);
   DebugLog("CLOSE",
            "close loop done|ok=" + (ok ? "true" : "false") +
            "|remaining=" + IntegerToString(finalRemaining) +
            "|closePending=" + (g_closePending ? "true" : "false"),
            true);
   return ok;
}

bool RetryPendingClose(BasketStats &stats)
{
   if(!g_closePending)
      return false;

   if(stats.count == 0)
   {
      g_closePending = false;
      return false;
   }

   if(TimeCurrent() - g_lastCloseAttempt < 3)
   {
      g_lastStatus = "Close pending: waiting retry | pos " + IntegerToString(stats.count);
      return true;
   }

   g_lastCloseAttempt = TimeCurrent();
   Print("[CLOSE-PENDING] Retrying basket close. Positions=", stats.count,
         " Profit=$", DoubleToString(stats.profit, 2));
   CloseAllBasket();
   g_lastStatus = "Close pending retry | pos " + IntegerToString(stats.count);
   return true;
}

double CalculateNextLot(int level)
{
   double lot = InpBaseLot;

   if(InpLotMode == LOT_LINEAR_INCREMENT)
      lot = InpBaseLot + (InpLotIncrement * (level - 1));
   else
      lot = InpBaseLot * MathPow(InpMultiplier, level - 1);

   return NormalizeLot(lot);
}

double CalculateTargetProfit(BasketStats &stats)
{
   double target = InpProfitPer001Lot;
   if(InpScaleTPByLot && stats.lots > 0)
      target = InpProfitPer001Lot * (stats.lots / 0.01);

   return MathMax(target, InpMinCloseProfitUSD);
}

double CalculateV6TPPrice(BasketStats &stats, double targetProfit)
{
   if(stats.count <= 0 || stats.lots <= 0 || stats.direction == DIR_NONE)
      return 0;

   double tickVal = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSz = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickVal <= 0 || tickSz <= 0)
      return 0;

   double tpDist = (targetProfit / stats.lots) * (tickSz / tickVal);
   if(stats.direction == DIR_BUY)
      return NormalizeDouble(stats.avgPrice + tpDist, _Digits);
   if(stats.direction == DIR_SELL)
      return NormalizeDouble(stats.avgPrice - tpDist, _Digits);

   return 0;
}

void ResetBasketProfitTracker()
{
   g_basketPeakProfit = 0;
   g_basketProfitTouched = false;
   g_calcTPPrice = 0;
   g_calcTargetProfit = 0;
}

void UpdateBasketProfitTracker(BasketStats &stats)
{
   if(stats.count <= 0)
   {
      ResetBasketProfitTracker();
      return;
   }

   if(stats.profit > g_basketPeakProfit)
      g_basketPeakProfit = stats.profit;

   if(stats.profit >= InpProfitLockStartUSD)
      g_basketProfitTouched = true;
}

bool ShouldCloseBasketForProfit(BasketStats &stats, double targetProfit, string &reason)
{
   reason = "";
   if(stats.count <= 0)
      return false;

   UpdateBasketProfitTracker(stats);

   if(stats.profit >= targetProfit)
   {
      reason = "V6 dollar TP";
      return true;
   }

   if(InpUseV6PriceTP && g_calcTPPrice > 0 && stats.profit > InpMinCloseProfitUSD)
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      bool pricePastTP = false;

      if(stats.direction == DIR_BUY && bid >= g_calcTPPrice)
         pricePastTP = true;
      else if(stats.direction == DIR_SELL && ask <= g_calcTPPrice)
         pricePastTP = true;

      if(pricePastTP)
      {
         reason = "V6 price TP";
         return true;
      }
   }

   if(InpCloseAnyPositiveBasket &&
      stats.maxLevel >= InpAnyPositiveFromLevel &&
      stats.profit >= InpAnyPositiveProfitUSD)
   {
      reason = "recovered basket profit";
      return true;
   }

   if(InpUseProfitLock && g_basketProfitTouched)
   {
      double retrace = g_basketPeakProfit - stats.profit;
      if(retrace >= InpProfitLockRetraceUSD && stats.profit >= InpProfitLockMinUSD)
      {
         reason = "profit lock peak $" + DoubleToString(g_basketPeakProfit, 2) +
                  " retrace $" + DoubleToString(retrace, 2);
         return true;
      }
   }

   return false;
}

bool HasHedgePosition(BasketStats &stats)
{
   return (stats.buyLots > 0 && stats.sellLots > 0);
}

bool OpenRunawayHedge(BasketStats &stats)
{
   if(g_hedgedThisBasket || HasHedgePosition(stats))
   {
      DebugLog("RUNAWAY", "hedge skipped|alreadyHedged|" + BasketSummary(stats), true);
      return false;
   }

   double netLot = MathAbs(stats.buyLots - stats.sellLots);
   if(netLot <= 0)
   {
      DebugLog("RUNAWAY", "hedge skipped|netLotZero|" + BasketSummary(stats), true);
      return false;
   }

   ENUM_DIRECTION hedgeDir = (stats.buyLots > stats.sellLots) ? DIR_SELL : DIR_BUY;
   double hedgeLot = NormalizeLot(netLot * InpHedgeLotMultiplier);
   if(hedgeLot <= 0)
   {
      DebugLog("RUNAWAY", "hedge skipped|invalidLot|netLot=" + DoubleToString(netLot, 2), true);
      return false;
   }

   string comment = "SMC-MART HEDGE runaway";
   if(OpenBasketOrder(hedgeDir, hedgeLot, comment))
   {
      g_hedgedThisBasket = true;
      Print("[RUNAWAY] Hedge opened ", EnumToString(hedgeDir), " ", DoubleToString(hedgeLot, 2));
      return true;
   }

   return false;
}

RunawayState DetectRunaway(BasketStats &stats)
{
   RunawayState state;
   state.active = false;
   state.trendAgainst = false;
   state.adx = 0;
   state.distancePips = 0;
   state.lossPct = 0;
   state.reason = "";

   if(!InpUseRunawayGuard || stats.count == 0 || stats.direction == DIR_NONE)
      return state;

   double price = MidPrice();
   state.distancePips = (stats.direction == DIR_BUY) ? PriceToPips(stats.avgPrice - price) : PriceToPips(price - stats.avgPrice);
   state.distancePips = MathMax(0, state.distancePips);

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity > 0 && stats.profit < 0)
      state.lossPct = (MathAbs(stats.profit) / equity) * 100.0;

   double ma[], adx[];
   ArraySetAsSeries(ma, true);
   ArraySetAsSeries(adx, true);

   if(CopyBuffer(g_handleRunawayMA, 0, 0, 4, ma) > 0 &&
      CopyBuffer(g_handleRunawayADX, 0, 0, 2, adx) > 0)
   {
      state.adx = adx[0];
      bool maDown = ma[0] < ma[3] && price < ma[0];
      bool maUp = ma[0] > ma[3] && price > ma[0];

      if(stats.direction == DIR_BUY && maDown && state.adx >= InpRunawayAdxLevel)
         state.trendAgainst = true;
      else if(stats.direction == DIR_SELL && maUp && state.adx >= InpRunawayAdxLevel)
         state.trendAgainst = true;
   }

   bool distanceHit = state.distancePips >= InpRunawayDistancePips;
   bool lossHit = state.lossPct >= InpRunawayLossPct;
   bool levelHit = stats.maxLevel >= InpRunawayMinLevel;

   // Scoring system: more flexible than strict AND
   int score = 0;
   if(state.trendAgainst) score += 2;
   if(distanceHit)        score += 1;
   if(lossHit)            score += 1;
   if(levelHit)           score += 1;

   if(score >= 3)
   {
      state.active = true;
      state.reason = "runaway score " + IntegerToString(score) + "/5" +
                     " ADX " + DoubleToString(state.adx, 1) +
                     " dist " + DoubleToString(state.distancePips, 0) + "p" +
                     " loss " + DoubleToString(state.lossPct, 1) + "%";
      DebugLog("RUNAWAY",
               "active|" + state.reason +
               "|trendAgainst=" + (state.trendAgainst ? "true" : "false") +
               "|distanceHit=" + (distanceHit ? "true" : "false") +
               "|lossHit=" + (lossHit ? "true" : "false") +
               "|levelHit=" + (levelHit ? "true" : "false") +
               "|score=" + IntegerToString(score) +
               "|" + BasketSummary(stats),
               true);
   }

   return state;
}

bool HandleRunaway(BasketStats &stats, RunawayState &runaway)
{
   if(!runaway.active)
      return true;

   if(InpRunawayAction == RUNAWAY_CLOSE_BASKET)
   {
      Print("[RUNAWAY] Closing basket: ", runaway.reason);
      DebugLog("RUNAWAY", "action=close|" + runaway.reason + "|" + BasketSummary(stats), true);
      g_closePending = true;
      CloseAllBasket();
      g_lastStatus = "Runaway close: " + runaway.reason;
      return false;
   }

   if(InpRunawayAction == RUNAWAY_HEDGE_ONCE)
   {
      DebugLog("RUNAWAY", "action=hedgeOnce|" + runaway.reason + "|" + BasketSummary(stats), true);
      OpenRunawayHedge(stats);
      g_lastStatus = "Runaway hedge/stop add: " + runaway.reason;
      return false;
   }

   DebugLog("RUNAWAY", "action=stopAdd|" + runaway.reason + "|" + BasketSummary(stats), true);
   g_lastStatus = "Runaway stop add: " + runaway.reason;
   return false;
}

//+------------------------------------------------------------------+
void UpdateSmcAnalysis()
{
   FindSwingPoints();
   FindStructureBreaks();
   FindOrderBlocks();
   FindFairValueGaps();
}

void FindSwingPoints()
{
   ArrayResize(g_swings, 0);

   int bars = MathMin(InpAnalysisBars, Bars(_Symbol, PERIOD_CURRENT));
   if(bars < InpSwingLookback * 2 + 20)
      return;

   double high[], low[];
   datetime time[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(time, true);

   int ch = CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   int cl = CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   int ct = CopyTime(_Symbol, PERIOD_CURRENT, 0, bars, time);
   bars = MathMin(MathMin(ch, cl), ct);

   if(bars <= InpSwingLookback * 2)
      return;

   for(int i = InpSwingLookback; i < bars - InpSwingLookback; i++)
   {
      bool swingHigh = true;
      bool swingLow = true;

      for(int j = 1; j <= InpSwingLookback; j++)
      {
         if(high[i] <= high[i - j] || high[i] <= high[i + j])
            swingHigh = false;
         if(low[i] >= low[i - j] || low[i] >= low[i + j])
            swingLow = false;
      }

      if(swingHigh || swingLow)
      {
         SwingPoint sp;
         sp.index = i;
         sp.price = swingHigh ? high[i] : low[i];
         sp.isHigh = swingHigh;
         sp.time = time[i];

         int size = ArraySize(g_swings);
         ArrayResize(g_swings, size + 1);
         g_swings[size] = sp;
      }
   }
}

void FindStructureBreaks()
{
   ArrayResize(g_breaks, 0);

   int bars = MathMin(InpAnalysisBars, Bars(_Symbol, PERIOD_CURRENT));
   if(bars < 60 || ArraySize(g_swings) == 0)
      return;

   double close[];
   datetime time[];
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(time, true);

   int cc = CopyClose(_Symbol, PERIOD_CURRENT, 0, bars, close);
   int ct = CopyTime(_Symbol, PERIOD_CURRENT, 0, bars, time);
   bars = MathMin(cc, ct);

   for(int s = 0; s < ArraySize(g_swings); s++)
   {
      SwingPoint sp = g_swings[s];
      if(sp.index <= 1 || sp.index >= bars)
         continue;

      int minIndex = MathMax(1, sp.index - InpStructureLookback);
      for(int i = sp.index - 1; i >= minIndex; i--)
      {
         if((sp.isHigh && close[i] > sp.price) || (!sp.isHigh && close[i] < sp.price))
         {
            StructureBreak brk;
            brk.index = i;
            brk.price = sp.price;
            brk.isBullish = sp.isHigh;
            brk.label = "BOS";
            brk.time = time[i];

            int size = ArraySize(g_breaks);
            ArrayResize(g_breaks, size + 1);
            g_breaks[size] = brk;
            break;
         }
      }
   }

   SortBreaksByTime();
   RelabelBreaks();
}

void SortBreaksByTime()
{
   int size = ArraySize(g_breaks);
   for(int i = 0; i < size - 1; i++)
   {
      for(int j = i + 1; j < size; j++)
      {
         if(g_breaks[i].time > g_breaks[j].time)
         {
            StructureBreak tmp = g_breaks[i];
            g_breaks[i] = g_breaks[j];
            g_breaks[j] = tmp;
         }
      }
   }
}

void RelabelBreaks()
{
   ENUM_DIRECTION bias = DIR_NONE;
   for(int i = 0; i < ArraySize(g_breaks); i++)
   {
      ENUM_DIRECTION brkDir = g_breaks[i].isBullish ? DIR_BUY : DIR_SELL;
      g_breaks[i].label = (bias != DIR_NONE && bias != brkDir) ? "CHoCH" : "BOS";
      bias = brkDir;
   }
}

void FindOrderBlocks()
{
   ArrayResize(g_orderBlocks, 0);

   int bars = MathMin(InpAnalysisBars, Bars(_Symbol, PERIOD_CURRENT));
   if(bars < 60 || ArraySize(g_swings) == 0)
      return;

   double high[], low[], open[], close[];
   datetime time[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(time, true);

   int ch = CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   int cl = CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   int co = CopyOpen(_Symbol, PERIOD_CURRENT, 0, bars, open);
   int cc = CopyClose(_Symbol, PERIOD_CURRENT, 0, bars, close);
   int ct = CopyTime(_Symbol, PERIOD_CURRENT, 0, bars, time);
   bars = MathMin(MathMin(MathMin(ch, cl), MathMin(co, cc)), ct);

   for(int s = 0; s < ArraySize(g_swings); s++)
   {
      int idx = g_swings[s].index;
      if(idx < 1 || idx >= bars - 1)
         continue;

      for(int j = idx; j < idx + InpObLookback && j < bars; j++)
      {
         bool bullishOb = !g_swings[s].isHigh && close[j] < open[j];
         bool bearishOb = g_swings[s].isHigh && close[j] > open[j];

         if(bullishOb || bearishOb)
         {
            OrderBlock ob;
            ob.high = high[j];
            ob.low = low[j];
            ob.index = j;
            ob.isBullish = bullishOb;
            ob.time = time[j];

            int size = ArraySize(g_orderBlocks);
            ArrayResize(g_orderBlocks, size + 1);
            g_orderBlocks[size] = ob;
            break;
         }
      }
   }
}

void FindFairValueGaps()
{
   ArrayResize(g_fvgs, 0);

   int bars = MathMin(InpAnalysisBars, Bars(_Symbol, PERIOD_CURRENT));
   if(bars < 10)
      return;

   double high[], low[];
   datetime time[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(time, true);

   int ch = CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   int cl = CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   int ct = CopyTime(_Symbol, PERIOD_CURRENT, 0, bars, time);
   bars = MathMin(MathMin(ch, cl), ct);

   for(int i = 2; i < bars - 2; i++)
   {
      if(low[i] > high[i + 2])
      {
         FairValueGap fvg;
         fvg.high = low[i];
         fvg.low = high[i + 2];
         fvg.index = i;
         fvg.isBullish = true;
         fvg.time = time[i];

         int size = ArraySize(g_fvgs);
         ArrayResize(g_fvgs, size + 1);
         g_fvgs[size] = fvg;
      }
      else if(high[i] < low[i + 2])
      {
         FairValueGap fvg;
         fvg.high = low[i + 2];
         fvg.low = high[i];
         fvg.index = i;
         fvg.isBullish = false;
         fvg.time = time[i];

         int size = ArraySize(g_fvgs);
         ArrayResize(g_fvgs, size + 1);
         g_fvgs[size] = fvg;
      }
   }
}

//+------------------------------------------------------------------+
bool DirectionMatches(ENUM_DIRECTION direction, StructureBreak &brk)
{
   return (direction == DIR_BUY && brk.isBullish) || (direction == DIR_SELL && !brk.isBullish);
}

ENUM_DIRECTION GetLatestSmcDirection()
{
   if(ArraySize(g_breaks) == 0)
      return DIR_NONE;

   StructureBreak latest = g_breaks[ArraySize(g_breaks) - 1];
   return latest.isBullish ? DIR_BUY : DIR_SELL;
}

bool HasStructureSequence(ENUM_DIRECTION direction, string &reason)
{
   bool hasChoch = false;
   bool hasBos = false;
   datetime chochTime = 0;
   datetime bosTime = 0;

   for(int i = 0; i < ArraySize(g_breaks); i++)
   {
      StructureBreak brk = g_breaks[i];
      if(brk.index > InpStructureLookback)
         continue;
      if(!DirectionMatches(direction, brk))
         continue;

      if(brk.label == "CHoCH")
      {
         hasChoch = true;
         chochTime = brk.time;
      }
      else if(brk.label == "BOS")
      {
         hasBos = true;
         bosTime = brk.time;
      }
   }

   if(hasChoch && hasBos && bosTime >= chochTime)
   {
      reason = (direction == DIR_BUY) ? "CHoCH+BOS Bull" : "CHoCH+BOS Bear";
      return true;
   }

   reason = "wait CHoCH+BOS";
   return false;
}

bool HasOppositeRecentStructure(ENUM_DIRECTION direction, string &reason)
{
   if(ArraySize(g_breaks) == 0)
      return false;

   StructureBreak latest = g_breaks[ArraySize(g_breaks) - 1];
   if(latest.index <= InpStructureLookback && !DirectionMatches(direction, latest))
   {
      reason = "opposite " + latest.label;
      return true;
   }
   return false;
}

bool HasRecentLiquiditySweep(ENUM_DIRECTION direction, string &reason)
{
   int bars = MathMax(40, InpSwingLookback + InpLqSweepLookback + 10);
   double high[], low[], close[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);

   int ch = CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   int cl = CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   int cc = CopyClose(_Symbol, PERIOD_CURRENT, 0, bars, close);
   bars = MathMin(MathMin(ch, cl), cc);

   if(bars < InpSwingLookback + InpLqSweepLookback + 5)
   {
      reason = "need LQ bars";
      return false;
   }

   for(int shift = 1; shift <= InpLqSweepLookback; shift++)
   {
      double refHigh = high[shift + 1];
      double refLow = low[shift + 1];
      int maxRef = MathMin(bars - 1, shift + InpSwingLookback);

      for(int j = shift + 2; j <= maxRef; j++)
      {
         if(high[j] > refHigh)
            refHigh = high[j];
         if(low[j] < refLow)
            refLow = low[j];
      }

      if(direction == DIR_BUY && low[shift] < refLow && close[shift] > refLow)
      {
         reason = "LQ low sweep";
         return true;
      }

      if(direction == DIR_SELL && high[shift] > refHigh && close[shift] < refHigh)
      {
         reason = "LQ high sweep";
         return true;
      }
   }

   reason = "wait LQ sweep";
   return false;
}

bool IsInOrderBlock(ENUM_DIRECTION direction, string &reason)
{
   double price = MidPrice();
   double buffer = PipsToPrice(InpObBufferPips);

   for(int i = ArraySize(g_orderBlocks) - 1; i >= 0; i--)
   {
      OrderBlock ob = g_orderBlocks[i];
      bool match = (direction == DIR_BUY && ob.isBullish) || (direction == DIR_SELL && !ob.isBullish);
      if(!match)
         continue;

      if(price >= ob.low - buffer && price <= ob.high + buffer)
      {
         reason = direction == DIR_BUY ? "Bull OB" : "Bear OB";
         return true;
      }
   }

   reason = "wait OB";
   return false;
}

bool IsInFvgZone(ENUM_DIRECTION direction, string &reason)
{
   if(!InpAllowFvgZone)
      return false;

   double price = MidPrice();
   for(int i = ArraySize(g_fvgs) - 1; i >= 0; i--)
   {
      FairValueGap fvg = g_fvgs[i];
      bool match = (direction == DIR_BUY && fvg.isBullish) || (direction == DIR_SELL && !fvg.isBullish);
      if(match && price >= fvg.low && price <= fvg.high)
      {
         reason = direction == DIR_BUY ? "Bull FVG" : "Bear FVG";
         return true;
      }
   }

   return false;
}

bool HasPriceAction(ENUM_DIRECTION direction, string &reason)
{
   if(!InpRequirePriceAction)
   {
      reason = "PA optional";
      return true;
   }

   double open[], close[], high[], low[];
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);

   if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, 4, open) <= 0 ||
      CopyClose(_Symbol, PERIOD_CURRENT, 0, 4, close) <= 0 ||
      CopyHigh(_Symbol, PERIOD_CURRENT, 0, 4, high) <= 0 ||
      CopyLow(_Symbol, PERIOD_CURRENT, 0, 4, low) <= 0)
   {
      reason = "need PA bars";
      return false;
   }

   double prevBody = MathAbs(close[2] - open[2]);
   double currBody = MathAbs(close[1] - open[1]);
   bool bullEngulf = close[2] < open[2] && close[1] > open[1] && currBody > prevBody * 1.2;
   bool bearEngulf = close[2] > open[2] && close[1] < open[1] && currBody > prevBody * 1.2;

   double body = MathAbs(close[1] - open[1]);
   double upperWick = high[1] - MathMax(close[1], open[1]);
   double lowerWick = MathMin(close[1], open[1]) - low[1];
   bool bullPin = lowerWick > body * 2.0 && lowerWick > upperWick * 1.5;
   bool bearPin = upperWick > body * 2.0 && upperWick > lowerWick * 1.5;

   if(direction == DIR_BUY && (bullEngulf || bullPin))
   {
      reason = bullEngulf ? "Bull Engulf" : "Bull Pin";
      return true;
   }

   if(direction == DIR_SELL && (bearEngulf || bearPin))
   {
      reason = bearEngulf ? "Bear Engulf" : "Bear Pin";
      return true;
   }

   reason = "wait PA";
   return false;
}

bool PassDailyHLGuard(ENUM_DIRECTION direction, string &reason)
{
   if(!InpUseDailyHLGuard)
      return true;

   double high[], low[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);

   if(CopyHigh(_Symbol, PERIOD_D1, 0, 1, high) <= 0 || CopyLow(_Symbol, PERIOD_D1, 0, 1, low) <= 0)
      return true;

   double price = MidPrice();
   double buffer = PipsToPrice(InpDailyHLBufferPips);

   if(direction == DIR_BUY && high[0] - price <= buffer)
   {
      reason = "BUY near daily high";
      return false;
   }

   if(direction == DIR_SELL && price - low[0] <= buffer)
   {
      reason = "SELL near daily low";
      return false;
   }

   return true;
}

SmcGate CheckEntryGate(ENUM_DIRECTION direction, bool isAdd)
{
   SmcGate gate;
   gate.valid = false;
   gate.reason = "";
   gate.waiting = "";

   if(direction == DIR_NONE)
   {
      gate.waiting = "no SMC direction";
      return gate;
   }

   string tmp = "";
   if(!PassDailyHLGuard(direction, tmp))
   {
      gate.waiting = tmp;
      return gate;
   }

   if(InpEntryMode == ENTRY_KILLER_MA_GRID)
   {
      gate.valid = true;
      gate.reason = "Killer MA Grid " + DirectionText(direction);
      return gate;
   }

   if(isAdd && InpStopAddOnOppositeBos && HasOppositeRecentStructure(direction, tmp))
   {
      gate.waiting = tmp;
      return gate;
   }

   string pa = "";
   if(!HasPriceAction(direction, pa))
   {
      gate.waiting = pa;
      return gate;
   }

   if(InpEntryMode == ENTRY_FAST_SMC)
   {
      gate.valid = true;
      gate.reason = "Fast SMC " + DirectionText(direction);
      if(InpRequirePriceAction)
         gate.reason += "+" + pa;
      return gate;
   }

   string structure = "";
   bool structureOk = HasStructureSequence(direction, structure);

   string lq = "";
   bool lqOk = HasRecentLiquiditySweep(direction, lq);

   string zone = "";
   bool zoneOk = IsInOrderBlock(direction, zone);
   if(!zoneOk)
   {
      string fvg = "";
      if(IsInFvgZone(direction, fvg))
      {
         zone = fvg;
         zoneOk = true;
      }
   }

   if(InpEntryMode == ENTRY_BALANCED_SMC)
   {
      if(!structureOk && !lqOk && !zoneOk)
      {
         gate.waiting = "wait SMC confirm";
         return gate;
      }

      if(!lqOk && !zoneOk)
      {
         gate.waiting = "wait LQ or OB";
         return gate;
      }

      gate.valid = true;
      gate.reason = "Balanced " + DirectionText(direction);
      if(structureOk)
         gate.reason += "+" + structure;
      if(lqOk)
         gate.reason += "+" + lq;
      if(zoneOk)
         gate.reason += "+" + zone;
      if(InpRequirePriceAction)
         gate.reason += "+" + pa;
      return gate;
   }

   if(!structureOk)
   {
      gate.waiting = structure;
      return gate;
   }

   if(!lqOk)
   {
      gate.waiting = lq;
      return gate;
   }

   if(!zoneOk)
   {
      gate.waiting = "wait OB";
      return gate;
   }

   gate.valid = true;
   gate.reason = structure + "+" + lq + "+" + zone;
   if(InpRequirePriceAction)
      gate.reason += "+" + pa;
   return gate;
}

//+------------------------------------------------------------------+
// Emergency Exit - hard safety net, no ADX/MA required
//+------------------------------------------------------------------+
bool CheckEmergencyExit(BasketStats &stats)
{
   if(!InpUseEmergencyExit || stats.count == 0 || stats.direction == DIR_NONE)
      return false;

   double price = MidPrice();
   double distPips = 0;
   if(stats.direction == DIR_BUY)
      distPips = PriceToPips(stats.avgPrice - price);
   else
      distPips = PriceToPips(price - stats.avgPrice);
   distPips = MathMax(0, distPips);

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double lossPct = 0;
   if(equity > 0 && stats.profit < 0)
      lossPct = (MathAbs(stats.profit) / equity) * 100.0;

   bool emergencyDist = distPips >= InpEmergencyDistPips;
   bool emergencyLoss = lossPct >= InpEmergencyLossPct;

   if(emergencyDist || emergencyLoss)
   {
      string reason = "EMERGENCY EXIT";
      if(emergencyDist) reason += " dist=" + DoubleToString(distPips, 0) + "p>=" + IntegerToString(InpEmergencyDistPips);
      if(emergencyLoss) reason += " loss=" + DoubleToString(lossPct, 1) + "%>=" + DoubleToString(InpEmergencyLossPct, 1);

      Print("[EMERGENCY] ", reason, " | ", BasketSummary(stats));
      DebugLog("EMERGENCY", reason + "|" + BasketSummary(stats), true);
      g_closePending = true;
      CloseAllBasket();
      g_lastStatus = reason;
      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
// Basket Age Guard
//+------------------------------------------------------------------+
datetime GetBasketOpenTime()
{
   datetime earliest = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Symbol() == _Symbol && posInfo.Magic() == (long)InpMagic)
      {
         if(earliest == 0 || posInfo.Time() < earliest)
            earliest = posInfo.Time();
      }
   }
   return earliest;
}

bool CheckBasketAgeGuard(BasketStats &stats, bool &stopAdd)
{
   stopAdd = false;
   if(!InpUseBasketAge || stats.count == 0)
   {
      g_basketOpenTime = 0;
      g_stopAddByAge = false;
      return false;
   }

   g_basketOpenTime = GetBasketOpenTime();
   if(g_basketOpenTime == 0)
      return false;

   double ageHours = (double)(TimeCurrent() - g_basketOpenTime) / 3600.0;

   if(ageHours >= InpMaxBasketAgeHours)
   {
      string reason = "basket age " + DoubleToString(ageHours, 1) + "h >= " +
                      IntegerToString(InpMaxBasketAgeHours) + "h";
      Print("[AGE] Close basket: ", reason);
      DebugLog("AGE", "close|" + reason + "|" + BasketSummary(stats), true);
      g_closePending = true;
      CloseAllBasket();
      g_lastStatus = "Age guard close: " + reason;
      return true;
   }

   if(ageHours >= InpStopAddAfterHours)
   {
      stopAdd = true;
      g_stopAddByAge = true;
      DebugLog("AGE", "stopAdd|age=" + DoubleToString(ageHours, 1) + "h|limit=" +
               IntegerToString(InpStopAddAfterHours) + "h|" + BasketSummary(stats), false);
   }
   else
   {
      g_stopAddByAge = false;
   }

   return false;
}

//+------------------------------------------------------------------+
// Opposite Momentum Block - block add if strong candle against basket
//+------------------------------------------------------------------+
bool CheckOppositeMomentumBlock(ENUM_DIRECTION basketDir)
{
   if(!InpBlockOnStrongOpposite || basketDir == DIR_NONE)
      return false;

   double open[], close[];
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(close, true);

   if(CopyOpen(_Symbol, PERIOD_CURRENT, 0, 2, open) <= 0 ||
      CopyClose(_Symbol, PERIOD_CURRENT, 0, 2, close) <= 0)
      return false;

   // Check last closed bar
   double bodyPips = PriceToPips(MathAbs(close[1] - open[1]));
   bool bullCandle = close[1] > open[1];
   bool bearCandle = close[1] < open[1];

   bool blocked = false;
   if(basketDir == DIR_BUY && bearCandle && bodyPips >= InpStrongCandlePips)
      blocked = true;
   if(basketDir == DIR_SELL && bullCandle && bodyPips >= InpStrongCandlePips)
      blocked = true;

   if(blocked)
   {
      DebugLog("MOMENTUM", "block add|dir=" + DirectionText(basketDir) +
               "|candlePips=" + DoubleToString(bodyPips, 1) +
               "|limit=" + DoubleToString(InpStrongCandlePips, 0), false);
   }

   return blocked;
}

//+------------------------------------------------------------------+
void RunSmcMartingale()
{
   BasketStats stats = GetBasketStats();
   if(RetryPendingClose(stats))
      return;

   double price = MidPrice();
   double targetProfit = CalculateTargetProfit(stats);
   g_calcTargetProfit = targetProfit;
   g_calcTPPrice = CalculateV6TPPrice(stats, targetProfit);
   LogBasketState(stats, targetProfit);

   string profitCloseReason = "";
   if(ShouldCloseBasketForProfit(stats, targetProfit, profitCloseReason))
   {
      Print("[TP] Basket profit $", DoubleToString(stats.profit, 2),
            " close by ", profitCloseReason,
            " | target $", DoubleToString(targetProfit, 2), ".");
      DebugLog("TP",
               "close basket|reason=" + profitCloseReason +
               "|profit=" + DoubleToString(stats.profit, 2) +
               "|peak=" + DoubleToString(g_basketPeakProfit, 2) +
               "|target=" + DoubleToString(targetProfit, 2) +
               "|tpPrice=" + DoubleToString(g_calcTPPrice, _Digits) +
               "|" + BasketSummary(stats),
               true);
      g_closePending = true;
      CloseAllBasket();
      return;
   }

   if(!RiskAllowsTrading(stats))
      return;

   // Emergency Exit - hard safety net
   if(CheckEmergencyExit(stats))
      return;

   // Basket Age Guard
   bool ageStopAdd = false;
   if(CheckBasketAgeGuard(stats, ageStopAdd))
      return;

   string timeReason = "";
   bool timeAllowed = IsTradingTimeAllowed(timeReason);
   if(!timeAllowed)
   {
      if(stats.count > 0 && InpCloseBasketOutsideTime)
      {
         Print("[TIME] Outside trading window. Closing basket.");
         DebugLog("TIME", "close basket|outsideWindow|reason=" + timeReason + "|" + BasketSummary(stats), true);
         g_closePending = true;
         CloseAllBasket();
      }

      g_lastStatus = "Time block: " + timeReason;
      DebugLog("TIME", "block entries|reason=" + timeReason + "|" + BasketSummary(stats), false);
      return;
   }

   if(stats.count == 0)
   {
      g_closePending = false;
      ResetBasketProfitTracker();
      string directionReason = "";
      ENUM_DIRECTION direction = GetEntryDirection(directionReason);
      SmcGate gate = CheckEntryGate(direction, false);

      if(!gate.valid)
      {
         g_lastStatus = "PSS SMC Martingale | Wait L1: " + gate.waiting +
                        " | Breaks=" + IntegerToString(ArraySize(g_breaks)) +
                        " OB=" + IntegerToString(ArraySize(g_orderBlocks));
         DebugLog("GATE",
                  "wait L1|dir=" + DirectionText(direction) +
                  "|dirReason=" + directionReason +
                  "|reason=" + gate.waiting +
                  "|breaks=" + IntegerToString(ArraySize(g_breaks)) +
                  "|ob=" + IntegerToString(ArraySize(g_orderBlocks)) +
                  "|fvg=" + IntegerToString(ArraySize(g_fvgs)) +
                  "|price=" + DoubleToString(price, _Digits),
                  false);
         return;
      }

      g_hedgedThisBasket = false;
      DebugLog("GATE",
               "pass L1|dir=" + DirectionText(direction) +
               "|dirReason=" + directionReason +
               "|reason=" + gate.reason +
               "|price=" + DoubleToString(price, _Digits),
               true);

      double lot = CalculateNextLot(1);
      if(lot > InpMaxTotalLot)
      {
         g_lastStatus = "Base lot exceeds max total lot";
         DebugLog("LOT",
                  "block L1|baseLotExceedsMaxTotal|lot=" + DoubleToString(lot, 2) +
                  "|maxTotal=" + DoubleToString(InpMaxTotalLot, 2),
                  true);
         return;
      }

      string comment = "SMC-MART L1 " + gate.reason;
      if(OpenBasketOrder(direction, lot, comment))
         Print("[L1] ", EnumToString(direction), " ", DoubleToString(lot, 2), " | ", gate.reason);

      return;
   }

   ENUM_DIRECTION direction = stats.direction;
   RunawayState runaway = DetectRunaway(stats);
   if(!HandleRunaway(stats, runaway))
      return;

   // MTF Filter: block add if higher TF disagrees with basket direction
   if(InpUseMTFFilter)
   {
      string htfReason = "";
      ENUM_DIRECTION htfDir = GetHTFDirection(htfReason);
      if(htfDir != DIR_NONE && htfDir != direction)
      {
         g_lastStatus = "Stop add: HTF " + DirectionText(htfDir) + " vs basket " + DirectionText(direction);
         DebugLog("MTF", "block add|basket=" + DirectionText(direction) +
                  "|htf=" + DirectionText(htfDir) + "|" + BasketSummary(stats), false);
         return;
      }
   }

   // Basket age stop-add check
   if(g_stopAddByAge)
   {
      g_lastStatus = "PSS SMC Martingale | Stop add: basket too old" +
                     " | P/L $" + DoubleToString(stats.profit, 2);
      DebugLog("AGE", "block add|" + BasketSummary(stats), false);
      return;
   }

   // Opposite momentum block
   if(CheckOppositeMomentumBlock(direction))
   {
      g_lastStatus = "PSS SMC Martingale | Stop add: strong opposite candle" +
                     " | P/L $" + DoubleToString(stats.profit, 2);
      return;
   }

   double profitPips = (direction == DIR_BUY) ? PriceToPips(price - stats.avgPrice) : PriceToPips(stats.avgPrice - price);

   if(stats.maxLevel >= InpMaxLevel)
   {
      g_lastStatus = "PSS SMC Martingale | Max level " + IntegerToString(stats.maxLevel) +
                     "/" + IntegerToString(InpMaxLevel) +
                     " | P/L $" + DoubleToString(stats.profit, 2);
      DebugLog("MART",
               "hold|maxLevelReached|" + BasketSummary(stats) +
               "|profitPips=" + DoubleToString(profitPips, 1),
               false);
      return;
   }

   double lastEntry = GetLastEntryPrice();
   double adversePips = 0;
   if(direction == DIR_BUY)
      adversePips = PriceToPips(lastEntry - price);
   else
      adversePips = PriceToPips(price - lastEntry);

   if(adversePips < InpMinAddDistancePips)
   {
      g_lastStatus = "PSS SMC Martingale | Hold " + EnumToString(direction) +
                     " L" + IntegerToString(stats.maxLevel) +
                     " | adverse " + DoubleToString(adversePips, 1) + "p" +
                     " | P/L $" + DoubleToString(stats.profit, 2) +
                     " | avg pips " + DoubleToString(profitPips, 1);
      DebugLog("MART",
               "hold|waitDistance|dir=" + DirectionText(direction) +
               "|adverse=" + DoubleToString(adversePips, 1) +
               "|need=" + IntegerToString(InpMinAddDistancePips) +
               "|profitPips=" + DoubleToString(profitPips, 1) +
               "|" + BasketSummary(stats),
               false);
      return;
   }

   SmcGate gate = CheckEntryGate(direction, true);
   if(!gate.valid)
   {
      g_lastStatus = "PSS SMC Martingale | Wait add L" + IntegerToString(stats.maxLevel + 1) +
                     ": " + gate.waiting +
                     " | adverse " + DoubleToString(adversePips, 1) + "p";
      DebugLog("GATE",
               "wait add|nextLevel=" + IntegerToString(stats.maxLevel + 1) +
               "|dir=" + DirectionText(direction) +
               "|reason=" + gate.waiting +
               "|adverse=" + DoubleToString(adversePips, 1) +
               "|" + BasketSummary(stats),
               false);
      return;
   }

   int nextLevel = stats.maxLevel + 1;
   double nextLot = CalculateNextLot(nextLevel);
   if(stats.lots + nextLot > InpMaxTotalLot)
   {
      g_lastStatus = "Max lot reached. Need " + DoubleToString(nextLot, 2) +
                     " | total " + DoubleToString(stats.lots, 2) +
                     "/" + DoubleToString(InpMaxTotalLot, 2);
      DebugLog("LOT",
               "block add|maxTotalLot|nextLevel=" + IntegerToString(nextLevel) +
               "|nextLot=" + DoubleToString(nextLot, 2) +
               "|currentLots=" + DoubleToString(stats.lots, 2) +
               "|maxTotal=" + DoubleToString(InpMaxTotalLot, 2) +
               "|" + BasketSummary(stats),
               true);
      return;
   }

   string comment = "SMC-MART L" + IntegerToString(nextLevel) + " " + gate.reason;
   DebugLog("GATE",
            "pass add|nextLevel=" + IntegerToString(nextLevel) +
            "|dir=" + DirectionText(direction) +
            "|reason=" + gate.reason +
            "|adverse=" + DoubleToString(adversePips, 1) +
            "|" + BasketSummary(stats),
            true);
   if(OpenBasketOrder(direction, nextLot, comment))
      Print("[ADD] L", nextLevel, " ", EnumToString(direction), " ", DoubleToString(nextLot, 2),
            " | adverse ", DoubleToString(adversePips, 1), "p | ", gate.reason);
}

//+------------------------------------------------------------------+
