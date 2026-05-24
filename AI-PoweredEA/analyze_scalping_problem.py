#!/usr/bin/env python3
"""
วิเคราะห์ปัญหา Gold Scalping Trader ที่ขาดทุนแม้กันหน้าทุน
"""

def analyze_scalping_settings():
    """วิเคราะห์การตั้งค่า Scalping"""
    print("🔍 SCALPING PROBLEM ANALYSIS")
    print("=" * 60)
    
    # การตั้งค่าปัจจุบัน
    current_tp = 120  # points
    current_sl = 150  # points
    
    print(f"📊 Current Settings:")
    print(f"   🎯 Take Profit: {current_tp} points ({current_tp/10} pips)")
    print(f"   🛡️ Stop Loss: {current_sl} points ({current_sl/10} pips)")
    print(f"   📈 Risk/Reward Ratio: 1:{current_tp/current_sl:.2f}")
    
    print(f"\n❌ PROBLEM IDENTIFIED:")
    print(f"   Stop Loss ({current_sl} points) > Take Profit ({current_tp} points)")
    print(f"   Risk: {current_sl/10} pips vs Reward: {current_tp/10} pips")
    print(f"   This means you lose MORE when wrong than you gain when right!")
    
    # คำนวณ breakeven win rate
    breakeven_rate = current_sl / (current_tp + current_sl)
    print(f"\n📊 Required Win Rate for Breakeven: {breakeven_rate:.1%}")
    print(f"   You need to be right {breakeven_rate:.1%} of the time just to break even!")
    
    # แสดงตัวอย่างผลลัพธ์
    print(f"\n💰 Example Results (10 trades):")
    
    scenarios = [
        {"wins": 5, "losses": 5, "name": "50% Win Rate"},
        {"wins": 6, "losses": 4, "name": "60% Win Rate"},
        {"wins": 7, "losses": 3, "name": "70% Win Rate"},
        {"wins": 8, "losses": 2, "name": "80% Win Rate"},
    ]
    
    for scenario in scenarios:
        wins = scenario["wins"]
        losses = scenario["losses"]
        profit = (wins * current_tp) - (losses * current_sl)
        print(f"   {scenario['name']}: {wins}W/{losses}L = {profit:+d} points ({profit/10:+.1f} pips)")
    
    print(f"\n🔧 RECOMMENDED FIXES:")
    
    # แนะนำการตั้งค่าใหม่
    recommended_configs = [
        {"tp": 150, "sl": 100, "name": "Conservative Scalping"},
        {"tp": 200, "sl": 100, "name": "Aggressive Scalping"},
        {"tp": 120, "sl": 80, "name": "Balanced Scalping"},
        {"tp": 100, "sl": 50, "name": "Quick Scalping"},
    ]
    
    for config in recommended_configs:
        tp = config["tp"]
        sl = config["sl"]
        ratio = tp / sl
        breakeven = sl / (tp + sl)
        
        print(f"\n   📋 {config['name']}:")
        print(f"      🎯 TP: {tp} points ({tp/10} pips)")
        print(f"      🛡️ SL: {sl} points ({sl/10} pips)")
        print(f"      📈 Risk/Reward: 1:{ratio:.2f}")
        print(f"      📊 Breakeven Rate: {breakeven:.1%}")
        
        # ตัวอย่างผลลัพธ์
        profit_60 = (6 * tp) - (4 * sl)
        print(f"      💰 60% Win Rate Result: {profit_60:+d} points ({profit_60/10:+.1f} pips)")

def analyze_other_issues():
    """วิเคราะห์ปัญหาอื่นๆ"""
    print(f"\n🔍 OTHER POTENTIAL ISSUES:")
    
    issues = [
        {
            "issue": "Spread Impact",
            "description": "Max spread 30 points (3 pips) eats into small scalping profits",
            "solution": "Reduce max spread to 15-20 points for scalping"
        },
        {
            "issue": "Overtrading",
            "description": "Max 100 trades/day with 30-second intervals",
            "solution": "Reduce frequency, increase signal quality threshold"
        },
        {
            "issue": "Market Conditions",
            "description": "Scalping in wrong market conditions",
            "solution": "Stricter volatility and trend filters"
        },
        {
            "issue": "Position Management",
            "description": "Breakeven at 100 points but TP only 120 points",
            "solution": "Adjust breakeven trigger or increase TP"
        },
        {
            "issue": "Adaptive Settings",
            "description": "Settings change during trading, inconsistent results",
            "solution": "Fix settings or improve adaptation logic"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"\n   {i}. {issue['issue']}:")
        print(f"      ❌ Problem: {issue['description']}")
        print(f"      ✅ Solution: {issue['solution']}")

def generate_fixed_settings():
    """สร้างการตั้งค่าที่แก้ไขแล้ว"""
    print(f"\n🛠️ RECOMMENDED FIXED SETTINGS:")
    
    settings = {
        # Risk Management - แก้ไขปัญหาหลัก
        "tp_points": 150,           # เพิ่ม TP
        "sl_points": 100,           # ลด SL
        "max_spread": 20,           # ลด spread tolerance
        
        # Position Management
        "breakeven_points": 80,     # เลื่อน breakeven เร็วขึ้น
        "partial_close_points": 100, # partial close ที่ 10 pips
        
        # Trading Frequency
        "signal_interval_seconds": 60,  # ลดความถี่
        "max_daily_trades": 50,     # ลดจำนวนเทรด
        "max_positions": 3,         # ลดจำนวน positions
        
        # Market Conditions
        "min_volatility": 0.2,      # เพิ่ม min volatility
        "max_volatility": 1.5,      # ลด max volatility
        "confidence_threshold": 0.75, # เพิ่ม confidence threshold
        
        # Time Management
        "max_hold_minutes": 15,     # เพิ่มเวลาถือ
        "cooldown_seconds": 120,    # เพิ่ม cooldown
    }
    
    for key, value in settings.items():
        print(f"   {key}: {value}")
    
    # คำนวณ Risk/Reward ใหม่
    new_ratio = settings["tp_points"] / settings["sl_points"]
    new_breakeven = settings["sl_points"] / (settings["tp_points"] + settings["sl_points"])
    
    print(f"\n📊 New Risk/Reward Analysis:")
    print(f"   📈 Risk/Reward Ratio: 1:{new_ratio:.2f}")
    print(f"   📊 Breakeven Win Rate: {new_breakeven:.1%}")
    
    # ตัวอย่างผลลัพธ์ใหม่
    print(f"\n💰 Expected Results (10 trades):")
    for win_rate in [0.5, 0.6, 0.7]:
        wins = int(10 * win_rate)
        losses = 10 - wins
        profit = (wins * settings["tp_points"]) - (losses * settings["sl_points"])
        print(f"   {win_rate:.0%} Win Rate: {wins}W/{losses}L = {profit:+d} points ({profit/10:+.1f} pips)")

if __name__ == "__main__":
    analyze_scalping_settings()
    analyze_other_issues()
    generate_fixed_settings()