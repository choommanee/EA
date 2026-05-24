#!/usr/bin/env python3
"""
MT5 Connection Test - ทดสอบการเชื่อมต่อ MT5
"""

import MetaTrader5 as mt5
import time

def test_mt5_connection():
    """ทดสอบการเชื่อมต่อ MT5 แบบละเอียด"""
    
    print("🔍 MT5 Connection Diagnostic Test")
    print("=" * 50)
    
    # 1. ตรวจสอบ MT5 library
    try:
        print(f"✅ MetaTrader5 library version: {mt5.__version__}")
    except Exception as e:
        print(f"❌ MT5 library error: {e}")
        return False
    
    # 2. ตรวจสอบการ initialize
    print("\n🔄 Attempting MT5 initialization...")
    
    try:
        # ลอง initialize แบบปกติ
        if not mt5.initialize():
            print("❌ MT5 initialize() failed")
            
            # ลอง initialize with path
            mt5_paths = [
                "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
                "C:\\Users\\User\\AppData\\Roaming\\MetaQuotes\\Terminal\\BB16F565FAAA6B23A20C26C49416FF05\\terminal64.exe"
            ]
            
            for path in mt5_paths:
                print(f"🔄 Trying path: {path}")
                try:
                    if mt5.initialize(path=path):
                        print(f"✅ Connected with path: {path}")
                        break
                except Exception as e:
                    print(f"❌ Path failed: {e}")
            else:
                print("❌ All paths failed")
                return False
        else:
            print("✅ MT5 initialized successfully")
        
        # 3. ตรวจสอบ account info
        print("\n📊 Checking account information...")
        account_info = mt5.account_info()
        
        if account_info is None:
            print("❌ No account information - MT5 not logged in")
            print("💡 Solution: Please login to MT5 terminal first")
            return False
        
        print(f"✅ Account Login: {account_info.login}")
        print(f"✅ Account Server: {account_info.server}")
        print(f"✅ Account Balance: ${account_info.balance:.2f}")
        print(f"✅ Account Equity: ${account_info.equity:.2f}")
        print(f"✅ Account Currency: {account_info.currency}")
        
        # 4. ตรวจสอบ symbols
        print("\n🔍 Checking Gold symbols...")
        gold_symbols = ["XAUUSD", "GOLD", "GOLDm#", "GOLD#", "XAU/USD"]
        
        available_symbol = None
        for symbol in gold_symbols:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is not None:
                print(f"✅ Found Gold symbol: {symbol}")
                print(f"   Spread: {symbol_info.spread} points")
                print(f"   Point: {symbol_info.point}")
                print(f"   Digits: {symbol_info.digits}")
                available_symbol = symbol
                break
            else:
                print(f"❌ Symbol not found: {symbol}")
        
        if available_symbol is None:
            print("❌ No Gold symbols available")
            return False
        
        # 5. ทดสอบดึงข้อมูลราคา
        print(f"\n📈 Testing price data for {available_symbol}...")
        
        tick = mt5.symbol_info_tick(available_symbol)
        if tick is None:
            print("❌ Cannot get tick data")
            return False
        
        print(f"✅ Current Price:")
        print(f"   Bid: ${tick.bid:.2f}")
        print(f"   Ask: ${tick.ask:.2f}")
        print(f"   Spread: {(tick.ask - tick.bid) / mt5.symbol_info(available_symbol).point:.0f} points")
        
        # 6. ทดสอบดึงข้อมูล historical data
        print(f"\n📊 Testing historical data...")
        
        rates = mt5.copy_rates_from_pos(available_symbol, mt5.TIMEFRAME_M5, 0, 10)
        if rates is None or len(rates) == 0:
            print("❌ Cannot get historical data")
            return False
        
        print(f"✅ Historical data available: {len(rates)} bars")
        print(f"   Latest close: ${rates[-1]['close']:.2f}")
        
        # 7. ตรวจสอบ trading permissions
        print(f"\n🔒 Checking trading permissions...")
        
        if account_info.trade_allowed:
            print("✅ Trading allowed on account")
        else:
            print("❌ Trading not allowed on account")
        
        if account_info.trade_expert:
            print("✅ Expert Advisor trading allowed")
        else:
            print("❌ Expert Advisor trading not allowed")
        
        print(f"\n🎉 MT5 Connection Test: SUCCESS!")
        print(f"✅ Ready to trade {available_symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False
    
    finally:
        # ปิดการเชื่อมต่อ
        mt5.shutdown()

def main():
    """Main function"""
    success = test_mt5_connection()
    
    if success:
        print(f"\n✅ MT5 is ready for trading!")
        print(f"💡 You can now run the main trading bot")
    else:
        print(f"\n❌ MT5 connection failed!")
        print(f"💡 Troubleshooting steps:")
        print(f"   1. Make sure MT5 terminal is running")
        print(f"   2. Login to your trading account in MT5")
        print(f"   3. Enable 'Allow automated trading' in MT5")
        print(f"   4. Enable 'Allow DLL imports' in MT5")
        print(f"   5. Add this script to MT5 trusted sources")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
