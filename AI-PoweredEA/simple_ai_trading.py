"""
Simple AI Trading Script
สคริปต์การเทรดด้วย AI แบบง่ายๆ ที่ใช้งานได้จริง
"""

import os
import sys
import time
import json
from datetime import datetime
import numpy as np

# Add Python directory to path
sys.path.append('Python')

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*50}")
    print(f"{title:^50}")
    print(f"{'='*50}")

def print_section(title):
    """Print formatted section"""
    print(f"\n{'-'*30}")
    print(f"🎯 {title}")
    print(f"{'-'*30}")

def create_simple_model():
    """สร้างโมเดล AI แบบง่ายๆ"""
    print_section("สร้างโมเดล AI")
    
    try:
        from sklearn.ensemble import RandomForestClassifier
        
        # สร้างโมเดล
        model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42
        )
        
        # สร้างข้อมูลตัวอย่างสำหรับเทรน
        # Features: [RSI, MACD, Bollinger_Band, EMA_Signal, Volume]
        np.random.seed(42)
        X_train = np.random.rand(1000, 5)
        
        # สร้าง labels (0=SELL, 1=BUY) โดยใช้กฎง่ายๆ
        y_train = []
        for features in X_train:
            rsi, macd, bb, ema, volume = features
            # กฎง่ายๆ: BUY ถ้า RSI < 0.3 และ MACD > 0.5
            if rsi < 0.3 and macd > 0.5:
                y_train.append(1)  # BUY
            elif rsi > 0.7 and macd < 0.5:
                y_train.append(0)  # SELL
            else:
                y_train.append(np.random.randint(0, 2))  # Random
        
        # เทรนโมเดล
        model.fit(X_train, y_train)
        
        # ทดสอบโมเดล
        accuracy = model.score(X_train, y_train)
        
        print(f"✅ สร้างโมเดลสำเร็จ")
        print(f"📊 Accuracy: {accuracy:.2%}")
        print(f"🎯 Features: RSI, MACD, BB, EMA, Volume")
        
        return model
        
    except Exception as e:
        print(f"❌ ไม่สามารถสร้างโมเดล: {e}")
        return None

def get_market_features(pair="EURUSD"):
    """จำลองการดึงข้อมูลตลาด (ในการใช้งานจริงจะดึงจาก MT5)"""
    print_section(f"ข้อมูลตลาด {pair}")
    
    # จำลองข้อมูลตลาดปัจจุบัน
    np.random.seed(int(time.time()) % 1000)
    
    features = {
        'RSI': np.random.uniform(20, 80),
        'MACD': np.random.uniform(-0.5, 0.5),
        'Bollinger_Band': np.random.uniform(0, 1),
        'EMA_Signal': np.random.uniform(0, 1),
        'Volume': np.random.uniform(0.3, 1.0)
    }
    
    print(f"📊 {pair} Market Data:")
    for indicator, value in features.items():
        if indicator == 'RSI':
            status = "Oversold" if value < 30 else "Overbought" if value > 70 else "Normal"
            print(f"   📈 {indicator}: {value:.1f} ({status})")
        elif indicator == 'MACD':
            status = "Bullish" if value > 0 else "Bearish"
            print(f"   📊 {indicator}: {value:.3f} ({status})")
        else:
            print(f"   📉 {indicator}: {value:.3f}")
    
    # Return as array for model prediction
    return np.array([list(features.values())])

def make_trading_decision(model, features, pair="EURUSD"):
    """ตัดสินใจการเทรดด้วย AI"""
    print_section(f"การตัดสินใจ {pair}")
    
    try:
        # ทำนายด้วยโมเดล
        prediction = model.predict(features)[0]
        prediction_proba = model.predict_proba(features)[0]
        
        # แปลงผลลัพธ์
        signal = "BUY" if prediction == 1 else "SELL"
        confidence = max(prediction_proba)
        
        print(f"🤖 AI Prediction:")
        print(f"   🎯 Signal: {signal}")
        print(f"   💪 Confidence: {confidence:.1%}")
        
        # ประเมินความเสี่ยง
        if confidence > 0.8:
            risk = "ต่ำ"
            recommendation = "แนะนำให้เทรด"
            emoji = "✅"
        elif confidence > 0.6:
            risk = "ปานกลาง"
            recommendation = "ระมัดระวัง"
            emoji = "⚠️"
        else:
            risk = "สูง"
            recommendation = "ไม่แนะนำ"
            emoji = "❌"
        
        print(f"   🛡️ Risk Level: {risk}")
        print(f"   {emoji} Recommendation: {recommendation}")
        
        return {
            'pair': pair,
            'signal': signal,
            'confidence': confidence,
            'risk': risk,
            'recommendation': recommendation,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        
    except Exception as e:
        print(f"❌ ไม่สามารถตัดสินใจ: {e}")
        return None

def simulate_trade_result(decision):
    """จำลองผลการเทรด"""
    print_section("ผลการเทรด (จำลอง)")
    
    if not decision:
        return None
    
    # จำลองผลการเทรดตาม confidence
    confidence = decision['confidence']
    
    # โอกาสชนะขึ้นอยู่กับ confidence
    win_probability = confidence * 0.8 + 0.1  # 10-90% based on confidence
    
    # สุ่มผลลัพธ์
    is_win = np.random.random() < win_probability
    
    # คำนวณกำไร/ขาดทุน
    if is_win:
        profit_loss = np.random.uniform(20, 100)  # กำไร 20-100
        outcome = "WIN"
        emoji = "🎉"
    else:
        profit_loss = -np.random.uniform(15, 80)  # ขาดทุน 15-80
        outcome = "LOSS"
        emoji = "😞"
    
    print(f"{emoji} Trade Result:")
    print(f"   📊 Pair: {decision['pair']}")
    print(f"   🎯 Signal: {decision['signal']}")
    print(f"   📈 Outcome: {outcome}")
    print(f"   💰 P&L: {profit_loss:+.2f}")
    print(f"   ⏰ Time: {decision['timestamp']}")
    
    return {
        'pair': decision['pair'],
        'signal': decision['signal'],
        'outcome': outcome,
        'profit_loss': profit_loss,
        'confidence': decision['confidence'],
        'timestamp': decision['timestamp']
    }

def track_performance(results):
    """ติดตามประสิทธิภาพ"""
    print_section("สรุปประสิทธิภาพ")
    
    if not results:
        print("❌ ไม่มีข้อมูลการเทรด")
        return
    
    total_trades = len(results)
    wins = sum(1 for r in results if r['outcome'] == 'WIN')
    losses = total_trades - wins
    
    win_rate = wins / total_trades if total_trades > 0 else 0
    total_pnl = sum(r['profit_loss'] for r in results)
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
    
    print(f"📊 Trading Summary:")
    print(f"   🎯 Total Trades: {total_trades}")
    print(f"   ✅ Wins: {wins}")
    print(f"   ❌ Losses: {losses}")
    print(f"   📈 Win Rate: {win_rate:.1%}")
    print(f"   💰 Total P&L: {total_pnl:+.2f}")
    print(f"   📊 Avg P&L per Trade: {avg_pnl:+.2f}")
    
    # Performance rating
    if win_rate >= 0.7 and total_pnl > 0:
        rating = "🏆 Excellent"
    elif win_rate >= 0.6 and total_pnl > 0:
        rating = "🥈 Good"
    elif win_rate >= 0.5:
        rating = "🥉 Average"
    else:
        rating = "📉 Needs Improvement"
    
    print(f"   🎖️ Performance: {rating}")

def main():
    """ฟังก์ชันหลัก"""
    print_header("🤖 Simple AI Trading System")
    print(f"⏰ เวลา: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. สร้างโมเดล AI
    model = create_simple_model()
    if not model:
        print("\n❌ ไม่สามารถสร้างโมเดลได้")
        return False
    
    # 2. เทรดหลายคู่เงิน
    currency_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    trade_results = []
    
    for pair in currency_pairs:
        print(f"\n{'='*50}")
        print(f"💱 Trading {pair}")
        print(f"{'='*50}")
        
        # ดึงข้อมูลตลาด
        features = get_market_features(pair)
        
        # ตัดสินใจการเทรด
        decision = make_trading_decision(model, features, pair)
        
        # จำลองการเทรด (ถ้า confidence สูงพอ)
        if decision and decision['confidence'] > 0.5:
            result = simulate_trade_result(decision)
            if result:
                trade_results.append(result)
        else:
            print("⏭️ ข้ามการเทรดเนื่องจาก confidence ต่ำ")
        
        time.sleep(1)  # หน่วงเวลาเล็กน้อย
    
    # 3. สรุปประสิทธิภาพ
    print(f"\n{'='*50}")
    track_performance(trade_results)
    
    # 4. แสดงคำแนะนำ
    print_section("คำแนะนำ")
    
    if trade_results:
        avg_confidence = np.mean([r['confidence'] for r in trade_results])
        win_rate = sum(1 for r in trade_results if r['outcome'] == 'WIN') / len(trade_results)
        
        print("💡 Tips for Better Trading:")
        
        if avg_confidence < 0.7:
            print("   📈 ปรับปรุงโมเดลเพื่อเพิ่ม confidence")
        
        if win_rate < 0.6:
            print("   🎯 ปรับ strategy หรือ risk management")
        
        print("   📊 ติดตามผลการเทรดอย่างสม่ำเสมอ")
        print("   🔄 อัพเดทโมเดลด้วยข้อมูลใหม่")
        print("   ⚠️ ใช้ stop loss และ take profit")
        
    else:
        print("   ⚠️ ไม่มีการเทรดเนื่องจาก confidence ต่ำ")
        print("   🔧 ควรปรับปรุงโมเดลหรือลดเกณฑ์ confidence")
    
    print(f"\n{'='*50}")
    print("🎉 การเทรดด้วย AI เสร็จสิ้น!")
    print("📖 ศึกษาเพิ่มเติมใน: AI_LEARNING_USER_GUIDE.md")
    print(f"{'='*50}")
    
    return len(trade_results) > 0

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ หยุดการทำงานโดยผู้ใช้")
        exit(1)
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        exit(1)