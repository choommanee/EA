"""
Check Market Conditions - ตรวจสอบสภาพตลาดสำหรับ Scalping
"""

import sys
sys.path.append('.')

from gold_scalping_trader import GoldScalpingTrader
import MetaTrader5 as mt5
from datetime import datetime

def check_current_market():
    """ตรวจสอบสภาพตลาดปัจจุบัน"""
    print("🔍 Gold Market Conditions Check")
    print("=" * 40)
    
    trader = GoldScalpingTrader()
    
    try:
        # เชื่อมต่อ MT5
        if not trader.connect_mt5():
            print("❌ Cannot connect to MT5")
            return
        
        print(f"\n📊 Current Market Analysis:")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ดูข้อมูลพื้นฐาน
        tick = mt5.symbol_info_tick(trader.symbol)
        symbol_info = mt5.symbol_info(trader.symbol)
        
        if tick and symbol_info:
            spread_points = (tick.ask - tick.bid) / symbol_info.point
            spread_pips = spread_points / 10
            
            print(f"💰 Current Price: ${tick.bid:.2f}")
            print(f"📊 Spread: {spread_points:.1f} points ({spread_pips:.1f} pips)")
            print(f"📈 Ask: ${tick.ask:.2f}")
            print(f"📉 Bid: ${tick.bid:.2f}")
        
        # วิเคราะห์สภาพตลาดแบบละเอียด
        analysis = trader.get_market_analysis()
        
        if analysis:
            print(f"\n📊 Technical Analysis:")
            print(f"   ⚡ ATR (Volatility): {analysis['atr']:.3f} - {analysis['atr_status']}")
            print(f"      • Min allowed: {trader.min_volatility}")
            print(f"      • Max allowed: {trader.max_volatility}")
            print(f"      • Current status: {'✅' if analysis['atr_status'] == 'Normal' else '❌'}")
            
            print(f"\n   📊 Spread Analysis:")
            print(f"      • Current: {analysis['spread_points']:.1f} points")
            print(f"      • Max allowed: {trader.max_spread} points")
            print(f"      • Status: {'✅' if analysis['spread_status'] == 'OK' else '❌'} {analysis['spread_status']}")
            
            print(f"\n   📈 Technical Indicators:")
            print(f"      • RSI Fast: {analysis['rsi_fast']:.1f} - {analysis['rsi_status']}")
            print(f"      • MACD Fast: {analysis['macd_fast']:.6f} - {analysis['macd_status']}")
            print(f"      • BB Position: {analysis['bb_position']:.3f} - {analysis['bb_status']}")
            print(f"      • Volume Ratio: {analysis['volume_ratio']:.2f} - {analysis['volume_status']}")
            
            print(f"\n   📊 Trading Status:")
            print(f"      • Daily Trades: {analysis['daily_trades']}/{trader.max_daily_trades}")
            print(f"      • Daily P&L: ${analysis['daily_profit']:.2f}")
        
        # ตรวจสอบเงื่อนไขการเทรด
        print(f"\n🔍 Scalping Conditions Check:")
        market_ok, market_msg = trader.check_market_conditions()
        
        print(f"   Status: {'✅ READY' if market_ok else '❌ NOT READY'}")
        print(f"   Message: {market_msg}")
        
        # แนะนำการปรับแต่ง
        if not market_ok and analysis:
            print(f"\n💡 Recommendations:")
            
            if analysis['atr'] > trader.max_volatility:
                print(f"   📈 Market too volatile (ATR: {analysis['atr']:.3f})")
                print(f"      • Consider increasing max_volatility to {analysis['atr']*1.2:.1f}")
                print(f"      • Or wait for volatility to decrease")
                print(f"      • Current volatility is {analysis['atr']/trader.max_volatility:.1f}x higher than limit")
            
            elif analysis['atr'] < trader.min_volatility:
                print(f"   📉 Market too quiet (ATR: {analysis['atr']:.3f})")
                print(f"      • Consider decreasing min_volatility to {analysis['atr']*0.8:.3f}")
                print(f"      • Or wait for more market movement")
            
            if analysis['spread_points'] > trader.max_spread:
                print(f"   📊 Spread too high ({analysis['spread_points']:.1f} points)")
                print(f"      • Wait for spread to tighten")
                print(f"      • Or increase max_spread to {analysis['spread_points']*1.1:.0f}")
        
        # แสดงการตั้งค่าปัจจุบัน
        print(f"\n⚙️ Current Scalping Settings:")
        print(f"   🎯 Take Profit: {trader.tp_points} points ({trader.tp_points/10} pips)")
        print(f"   🛡️ Stop Loss: {trader.sl_points} points ({trader.sl_points/10} pips)")
        print(f"   📊 Max Spread: {trader.max_spread} points ({trader.max_spread/10} pips)")
        print(f"   ⚡ Min Volatility: {trader.min_volatility}")
        print(f"   📈 Max Volatility: {trader.max_volatility}")
        print(f"   💼 Max Positions: {trader.max_positions}")
        print(f"   📅 Max Daily Trades: {trader.max_daily_trades}")
        
        # ดู positions ปัจจุบัน
        positions = trader.get_active_positions()
        if positions:
            print(f"\n📋 Active Positions ({len(positions)}):")
            for pos in positions:
                pos_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                hold_time = datetime.now() - datetime.fromtimestamp(pos.time)
                print(f"   🎫 {pos.ticket}: {pos_type} {pos.volume} lots @ ${pos.price_open:.2f}")
                print(f"      P&L: ${pos.profit:.2f}, Hold: {str(hold_time).split('.')[0]}")
        else:
            print(f"\n📋 No active positions")
        
        # สรุปและคำแนะนำ
        print(f"\n📋 Summary:")
        if market_ok:
            print(f"   ✅ Market is ready for scalping")
            print(f"   🚀 You can start trading now")
        else:
            print(f"   ❌ Market conditions not suitable")
            print(f"   ⏳ Wait for better conditions or adjust settings")
        
    except Exception as e:
        print(f"❌ Error checking market: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mt5.shutdown()
        print("🔌 MT5 connection closed")

def suggest_optimal_settings():
    """แนะนำการตั้งค่าที่เหมาะสม"""
    print("\n💡 Optimal Scalping Settings Suggestions:")
    print("=" * 50)
    
    trader = GoldScalpingTrader()
    
    try:
        if not trader.connect_mt5():
            return
        
        analysis = trader.get_market_analysis()
        if not analysis:
            return
        
        current_atr = analysis['atr']
        current_spread = analysis['spread_points']
        
        print(f"📊 Based on current market conditions:")
        print(f"   Current ATR: {current_atr:.3f}")
        print(f"   Current Spread: {current_spread:.1f} points")
        
        # แนะนำ volatility range
        suggested_min_vol = max(0.1, current_atr * 0.5)
        suggested_max_vol = current_atr * 2.0
        
        print(f"\n⚡ Suggested Volatility Range:")
        print(f"   Min Volatility: {suggested_min_vol:.1f}")
        print(f"   Max Volatility: {suggested_max_vol:.1f}")
        
        # แนะนำ TP/SL ตาม volatility
        if current_atr > 1.0:  # High volatility
            suggested_tp = 80
            suggested_sl = 50
            print(f"\n🎯 High Volatility Settings:")
        elif current_atr > 0.5:  # Medium volatility
            suggested_tp = 60
            suggested_sl = 40
            print(f"\n🎯 Medium Volatility Settings:")
        else:  # Low volatility
            suggested_tp = 40
            suggested_sl = 25
            print(f"\n🎯 Low Volatility Settings:")
        
        print(f"   Take Profit: {suggested_tp} points ({suggested_tp/10} pips)")
        print(f"   Stop Loss: {suggested_sl} points ({suggested_sl/10} pips)")
        print(f"   Risk/Reward: 1:{suggested_tp/suggested_sl:.1f}")
        
        # แนะนำ spread limit
        suggested_max_spread = max(30, current_spread * 1.5)
        print(f"\n📊 Suggested Max Spread: {suggested_max_spread:.0f} points")
        
        print(f"\n📝 Copy these settings:")
        print(f"trader.min_volatility = {suggested_min_vol:.1f}")
        print(f"trader.max_volatility = {suggested_max_vol:.1f}")
        print(f"trader.tp_points = {suggested_tp}")
        print(f"trader.sl_points = {suggested_sl}")
        print(f"trader.max_spread = {suggested_max_spread:.0f}")
        
    except Exception as e:
        print(f"❌ Error suggesting settings: {e}")
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    print("🔍 Market Conditions Checker")
    print("1. Check Current Market")
    print("2. Suggest Optimal Settings")
    
    choice = input("Enter choice (1-2, default 1): ").strip() or "1"
    
    if choice == "1":
        check_current_market()
    elif choice == "2":
        suggest_optimal_settings()
    else:
        print("❌ Invalid choice")