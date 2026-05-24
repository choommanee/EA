//+------------------------------------------------------------------+
//|                                                 TestCompile.mq5 |
//|                                             Test Compilation     |
//+------------------------------------------------------------------+
#property copyright "Test"
#property version   "1.00"

#include <Trade\Trade.mqh>

CTrade trade;

int OnInit()
{
    // Test TimeToStruct function
    MqlDateTime time_struct;
    TimeToStruct(TimeCurrent(), time_struct);
    int hour = time_struct.hour;

    Print("Current hour: ", hour);
    return INIT_SUCCEEDED;
}

void OnTick()
{
    // Test basic functionality
}

void OnDeinit(const int reason)
{
    Print("Test EA stopped");
}