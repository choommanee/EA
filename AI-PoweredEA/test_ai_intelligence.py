"""
Test AI Intelligence - ทดสอบระบบ AI Intelligence
"""

import sys
sys.path.append('.')

from gold_ai_intelligence import GoldAIIntelligence
import json

def test_intelligence_system():
    """ทดสอบระบบ AI Intelligence"""
    print("🧠 Testing AI Intelligence System")
    print("=" * 40)
    
    # สร้าง intelligence system
    ai_intel = GoldAIIntelligence()
    
    try:
        # ทดสอบการเริ่มต้น
        print("\n1. Testing component initialization...")
        if ai_intel.initialize_components():
            print("✅ Components initialized successfully")
        else:
            print("❌ Component initialization failed")
            return
        
        # ทดสอบการดึงข่าว
        print("\n2. Testing news analysis...")
        news = ai_intel.get_market_news()
        
        if news:
            print(f"✅ Retrieved {len(news)} news items")
            for i, n in enumerate(news, 1):
                print(f"   News {i}: {n['title'][:50]}...")
                print(f"   Sentiment: {n['sentiment']:+.2f}, Impact: {n['impact_score']:.2f}")
        else:
            print("❌ No news retrieved")
        
        # ทดสอบ learning insights
        print("\n3. Testing learning insights...")
        insights = ai_intel.get_learning_insights()
        
        if insights:
            print("✅ Learning insights generated")
            print(f"   Model Performance: {insights['model_performance']:.1%}")
            print(f"   Accuracy Trend: {insights['accuracy_trend']}")
            print(f"   Market Adaptation: {insights['market_adaptation']}")
            print(f"   Key Patterns: {len(insights['key_patterns'])}")
            print(f"   Recommendations: {len(insights['recommendations'])}")
        else:
            print("❌ No learning insights")
        
        # ทดสอบ daily framework
        print("\n4. Testing daily framework generation...")
        framework = ai_intel.generate_daily_framework(news, insights)
        
        if framework:
            print("✅ Daily framework generated")
            print(f"   Market Bias: {framework['market_bias']}")
            print(f"   Key Levels: {len(framework['key_levels'])}")
            print(f"   Strategy Focus: {len(framework['strategy_focus'])}")
            print(f"   Alerts: {len(framework['alerts'])}")
            print(f"   Risk Level: {framework['risk_management']['confidence_level']}")
        else:
            print("❌ Framework generation failed")
        
        # ทดสอบการสร้างสรุปรายวัน
        print("\n5. Testing daily summary generation...")
        summary = ai_intel.generate_daily_summary()
        
        if summary:
            print("✅ Daily summary generated successfully")
            print(f"   Date: {summary['date']}")
            print(f"   News Items: {len(summary['news_analysis'])}")
            print(f"   Framework Generated: {'Yes' if summary['daily_framework'] else 'No'}")
            print(f"   Performance Metrics: {'Yes' if summary['performance_metrics'] else 'No'}")
        else:
            print("❌ Daily summary generation failed")
        
        # ทดสอบ Telegram message formatting
        print("\n6. Testing Telegram message formatting...")
        if summary:
            telegram_msg = ai_intel.format_telegram_summary(summary)
            
            if telegram_msg and len(telegram_msg) > 100:
                print("✅ Telegram message formatted successfully")
                print(f"   Message length: {len(telegram_msg)} characters")
                print(f"   Preview: {telegram_msg[:100]}...")
            else:
                print("❌ Telegram message formatting failed")
        
        # ทดสอบ historical analysis
        print("\n7. Testing historical analysis...")
        historical = ai_intel.get_historical_analysis(7)
        
        if historical:
            print("✅ Historical analysis completed")
            print(f"   Period: {historical['period']}")
            print(f"   Total Days: {historical['total_days']}")
            print(f"   Insights: {len(historical['key_insights'])}")
        else:
            print("⚠️ No historical data available (expected for first run)")
        
        print("\n🎉 AI Intelligence system test completed!")
        
        # แสดงตัวอย่างผลลัพธ์
        if summary:
            print(f"\n📊 Sample Results:")
            print(f"   Market Sentiment: {framework['market_bias'] if framework else 'Unknown'}")
            print(f"   AI Model Performance: {insights['model_performance']:.1%}")
            print(f"   News Sentiment: {np.mean([n['sentiment'] for n in news]):+.2f}" if news else "   News Sentiment: N/A")
            print(f"   Daily Trades: {summary['performance_metrics']['daily_trades']}")
            print(f"   Win Rate: {summary['performance_metrics']['win_rate']:.1%}")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()

def test_telegram_integration():
    """ทดสอบการส่ง Telegram"""
    print("\n📱 Testing Telegram Integration")
    print("-" * 30)
    
    ai_intel = GoldAIIntelligence()
    
    # ทดสอบส่งข้อความ
    test_message = """
🧪 <b>AI INTELLIGENCE TEST MESSAGE</b>

📅 <b>Date:</b> Test Run
⏰ <b>Time:</b> Now

🧠 <b>System Status:</b> Testing
📊 <b>Components:</b> All Active

<i>🤖 This is a test message</i>
    """.strip()
    
    print("Sending test message to Telegram...")
    
    if ai_intel.send_telegram_message(test_message):
        print("✅ Test message sent successfully!")
    else:
        print("❌ Failed to send test message")

def show_sample_output():
    """แสดงตัวอย่างผลลัพธ์"""
    print("\n📋 Sample Intelligence Output")
    print("=" * 40)
    
    sample_output = {
        "date": "2025-08-19",
        "market_bias": "Bullish",
        "news_sentiment": +0.35,
        "model_performance": 0.78,
        "key_levels": [2670, 2650, 2630],
        "strategy_focus": "Look for buy opportunities on dips",
        "risk_level": "Medium",
        "alerts": ["High impact news detected", "Model performing well"]
    }
    
    print(f"📅 Date: {sample_output['date']}")
    print(f"📈 Market Bias: {sample_output['market_bias']}")
    print(f"😊 News Sentiment: {sample_output['news_sentiment']:+.2f}")
    print(f"🤖 Model Performance: {sample_output['model_performance']:.1%}")
    print(f"🎯 Key Levels: {sample_output['key_levels']}")
    print(f"💡 Strategy: {sample_output['strategy_focus']}")
    print(f"⚠️ Risk Level: {sample_output['risk_level']}")
    print(f"🚨 Alerts: {len(sample_output['alerts'])}")

if __name__ == "__main__":
    import numpy as np
    
    print("🧪 AI Intelligence Test Suite")
    print("1. Full System Test")
    print("2. Telegram Integration Test")
    print("3. Show Sample Output")
    
    choice = input("Enter choice (1-3, default 1): ").strip() or "1"
    
    if choice == "1":
        test_intelligence_system()
    elif choice == "2":
        test_telegram_integration()
    elif choice == "3":
        show_sample_output()
    else:
        print("❌ Invalid choice")