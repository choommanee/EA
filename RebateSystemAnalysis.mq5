//+------------------------------------------------------------------+
//|                                          RebateSystemAnalysis.mq5 |
//|                                        Copyright 2025, Your Name |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Your Name"
#property link      "https://www.mql5.com"
#property version   "1.00"
#property script_show_inputs

// Input parameters for analysis
input group "=== Analysis Settings ==="
input double TestLotSize = 0.01;               // Test lot size
input int TestDays = 30;                       // Number of days to analyze
input double RebateRate = 10.0;                // Rebate rate per lot ($)
input int TradesPerDay = 10;                   // Average trades per day
input double AverageSpread = 2.0;              // Average spread in pips
input double Commission = 0.0;                 // Commission per lot (if any)

input group "=== Cost Analysis ==="
input double SwapLong = -2.0;                  // Swap cost for long positions (per lot/day)
input double SwapShort = -1.5;                 // Swap cost for short positions (per lot/day)
input double SlippageCost = 0.5;               // Average slippage cost per trade (pips)

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== XM REBATE SYSTEM PROFIT ANALYSIS ===");
    Print("Analysis Period: ", TestDays, " days");
    Print("Test Parameters:");
    Print("- Lot Size: ", TestLotSize);
    Print("- Trades/Day: ", TradesPerDay);
    Print("- Rebate Rate: $", RebateRate, "/lot");
    Print("- Average Spread: ", AverageSpread, " pips");
    Print("");
    
    // Calculate daily metrics
    CalculateDailyProfitability();
    
    // Calculate monthly and yearly projections
    CalculateProjections();
    
    // Analyze break-even scenarios
    AnalyzeBreakEvenScenarios();
    
    // Risk analysis
    PerformRiskAnalysis();
    
    // Real-world scenarios
    AnalyzeRealWorldScenarios();
    
    Print("=== ANALYSIS COMPLETE ===");
}

//+------------------------------------------------------------------+
//| Calculate Daily Profitability                                   |
//+------------------------------------------------------------------+
void CalculateDailyProfitability()
{
    Print("--- DAILY PROFITABILITY ANALYSIS ---");
    
    // Daily rebate income
    double daily_volume = TestLotSize * TradesPerDay;
    double daily_rebate = daily_volume * RebateRate;
    
    // Daily costs
    double spread_cost = TestLotSize * TradesPerDay * AverageSpread * 10; // $10 per pip for standard lot
    double commission_cost = TestLotSize * TradesPerDay * Commission;
    double slippage_cost = TestLotSize * TradesPerDay * SlippageCost * 10;
    double swap_cost = TestLotSize * (SwapLong + SwapShort) / 2; // Average swap cost
    
    double total_daily_costs = spread_cost + commission_cost + slippage_cost + swap_cost;
    double net_daily_profit = daily_rebate - total_daily_costs;
    
    Print("Daily Volume: ", DoubleToString(daily_volume, 2), " lots");
    Print("Daily Rebate Income: $", DoubleToString(daily_rebate, 2));
    Print("");
    Print("Daily Costs Breakdown:");
    Print("- Spread Cost: $", DoubleToString(spread_cost, 2));
    Print("- Commission: $", DoubleToString(commission_cost, 2));
    Print("- Slippage: $", DoubleToString(slippage_cost, 2));
    Print("- Swap Cost: $", DoubleToString(swap_cost, 2));
    Print("- Total Costs: $", DoubleToString(total_daily_costs, 2));
    Print("");
    Print("NET DAILY PROFIT: $", DoubleToString(net_daily_profit, 2));
    
    if(net_daily_profit > 0)
        Print("✅ PROFITABLE - System generates positive daily income");
    else
        Print("❌ NOT PROFITABLE - Daily costs exceed rebate income");
    
    Print("");
}

//+------------------------------------------------------------------+
//| Calculate Monthly and Yearly Projections                        |
//+------------------------------------------------------------------+
void CalculateProjections()
{
    Print("--- PROFIT PROJECTIONS ---");
    
    double daily_volume = TestLotSize * TradesPerDay;
    double daily_rebate = daily_volume * RebateRate;
    double daily_costs = TestLotSize * TradesPerDay * AverageSpread * 10;
    double net_daily_profit = daily_rebate - daily_costs;
    
    double monthly_profit = net_daily_profit * 22; // 22 trading days
    double yearly_profit = net_daily_profit * 250; // 250 trading days
    
    Print("Monthly Projection (22 trading days): $", DoubleToString(monthly_profit, 2));
    Print("Yearly Projection (250 trading days): $", DoubleToString(yearly_profit, 2));
    Print("");
    
    // ROI Analysis (assuming $1000 account)
    double account_size = 1000.0;
    double monthly_roi = (monthly_profit / account_size) * 100;
    double yearly_roi = (yearly_profit / account_size) * 100;
    
    Print("ROI Analysis (based on $1000 account):");
    Print("- Monthly ROI: ", DoubleToString(monthly_roi, 2), "%");
    Print("- Yearly ROI: ", DoubleToString(yearly_roi, 2), "%");
    Print("");
}

//+------------------------------------------------------------------+
//| Analyze Break-Even Scenarios                                    |
//+------------------------------------------------------------------+
void AnalyzeBreakEvenScenarios()
{
    Print("--- BREAK-EVEN ANALYSIS ---");
    
    double cost_per_trade = TestLotSize * AverageSpread * 10;
    double rebate_per_trade = TestLotSize * RebateRate;
    double profit_per_trade = rebate_per_trade - cost_per_trade;
    
    Print("Per Trade Analysis:");
    Print("- Rebate per trade: $", DoubleToString(rebate_per_trade, 2));
    Print("- Cost per trade: $", DoubleToString(cost_per_trade, 2));
    Print("- Profit per trade: $", DoubleToString(profit_per_trade, 2));
    Print("");
    
    // Break-even spread calculation
    double breakeven_spread = RebateRate / 10; // Convert to pips
    Print("Break-even spread: ", DoubleToString(breakeven_spread, 1), " pips");
    Print("Current spread: ", DoubleToString(AverageSpread, 1), " pips");
    
    if(AverageSpread < breakeven_spread)
        Print("✅ Current spread is below break-even - System is profitable");
    else
        Print("❌ Current spread exceeds break-even - System is not profitable");
    
    Print("");
}

//+------------------------------------------------------------------+
//| Perform Risk Analysis                                           |
//+------------------------------------------------------------------+
void PerformRiskAnalysis()
{
    Print("--- RISK ANALYSIS ---");
    
    Print("Key Risks:");
    Print("1. Spread Widening Risk:");
    Print("   - If spreads increase above ", DoubleToString(RebateRate/10, 1), " pips, system becomes unprofitable");
    Print("   - Market volatility can cause temporary spread increases");
    Print("");
    
    Print("2. Rebate Rate Changes:");
    Print("   - Brokers may reduce rebate rates without notice");
    Print("   - Competition between rebate providers may affect rates");
    Print("");
    
    Print("3. Execution Risks:");
    Print("   - Slippage can reduce profitability");
    Print("   - Connection issues may cause missed opportunities");
    Print("");
    
    Print("4. Regulatory Risks:");
    Print("   - Changes in broker regulations");
    Print("   - Rebate program discontinuation");
    Print("");
    
    // Calculate maximum acceptable spread
    double max_spread = (RebateRate * 0.8) / 10; // 80% safety margin
    Print("Recommended maximum spread: ", DoubleToString(max_spread, 1), " pips (80% safety margin)");
    Print("");
}

//+------------------------------------------------------------------+
//| Analyze Real-World Scenarios                                   |
//+------------------------------------------------------------------+
void AnalyzeRealWorldScenarios()
{
    Print("--- REAL-WORLD SCENARIOS ---");
    
    // Scenario 1: Conservative Trading
    Print("Scenario 1 - Conservative Trading:");
    Print("- 5 trades/day, 0.01 lots, 1.5 pip spread");
    double scenario1_daily = (0.01 * 5 * 10.0) - (0.01 * 5 * 1.5 * 10);
    Print("- Daily profit: $", DoubleToString(scenario1_daily, 2));
    Print("- Monthly profit: $", DoubleToString(scenario1_daily * 22, 2));
    Print("");
    
    // Scenario 2: Moderate Trading
    Print("Scenario 2 - Moderate Trading:");
    Print("- 15 trades/day, 0.02 lots, 2.0 pip spread");
    double scenario2_daily = (0.02 * 15 * 10.0) - (0.02 * 15 * 2.0 * 10);
    Print("- Daily profit: $", DoubleToString(scenario2_daily, 2));
    Print("- Monthly profit: $", DoubleToString(scenario2_daily * 22, 2));
    Print("");
    
    // Scenario 3: Aggressive Trading
    Print("Scenario 3 - Aggressive Trading:");
    Print("- 30 trades/day, 0.05 lots, 2.5 pip spread");
    double scenario3_daily = (0.05 * 30 * 10.0) - (0.05 * 30 * 2.5 * 10);
    Print("- Daily profit: $", DoubleToString(scenario3_daily, 2));
    Print("- Monthly profit: $", DoubleToString(scenario3_daily * 22, 2));
    Print("");
    
    // Best case scenario
    Print("Best Case Scenario (XM Ultra account, tight spreads):");
    Print("- 20 trades/day, 0.1 lots, 0.8 pip spread, $6/lot rebate");
    double best_case_daily = (0.1 * 20 * 6.0) - (0.1 * 20 * 0.8 * 10);
    Print("- Daily profit: $", DoubleToString(best_case_daily, 2));
    Print("- Monthly profit: $", DoubleToString(best_case_daily * 22, 2));
    Print("- Yearly profit: $", DoubleToString(best_case_daily * 250, 2));
    Print("");
}
