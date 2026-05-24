"""
Test Telegram Bot - ทดสอบการส่งข้อความไป Telegram
"""

import requests
import json
from datetime import datetime

def test_telegram_bot():
    """ทดสอบการส่งข้อความไป Telegram"""
    
    # Telegram settings
    telegram_token = "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
    chat_id = "-1002852894581"  # New supergroup chat ID
    
    print("🤖 Testing Telegram Bot...")
    print(f"📊 Chat ID: {chat_id}")
    
    # ข้อความทดสอบ
    test_message = f"""
🧪 <b>Telegram Bot Test</b> 🧪

✅ <b>Status:</b> Testing connection
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
📅 <b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}

🤖 <b>Bot:</b> Gold AI Trader
🔗 <b>Connection:</b> Active

<i>This is a test message from Gold AI Trader Bot</i>
    """.strip()
    
    try:
        # ส่งข้อความ
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'HTML'
        }
        
        print(f"🔗 Sending to: {url}")
        
        response = requests.post(url, data=data, timeout=10)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Message sent successfully!")
            print(f"📊 Message ID: {result['result']['message_id']}")
            return True
        else:
            print("❌ Failed to send message")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_gold_signal():
    """ทดสอบส่งสัญญาณทอง"""
    
    telegram_token = "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
    chat_id = "-1002852894581"  # New supergroup chat ID
    
    print("\n🥇 Testing Gold Signal...")
    
    # สัญญาณทองจำลอง
    gold_signal = f"""
🥇 <b>GOLD AI SIGNAL</b> 🥇

🟢📈 <b>สัญญาณ: ซื้อ (BUY)</b>
💰 <b>ราคา:</b> $2,045.50
🎯 <b>ความมั่นใจ:</b> 85.2%
💪 <b>ความแข็งแกร่ง:</b> แข็งแกร่งมาก 💪
📊 <b>Timeframe Votes:</b> 3 BUY, 1 SELL

⏰ <b>เวลา:</b> {datetime.now().strftime('%H:%M:%S')}
📅 <b>วันที่:</b> {datetime.now().strftime('%d/%m/%Y')}

<i>🤖 สร้างโดย Gold AI Trader</i>
    """.strip()
    
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': gold_signal,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ Gold signal sent successfully!")
            return True
        else:
            print("❌ Failed to send gold signal")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("📱 Telegram Bot Testing")
    print("=" * 40)
    
    # ทดสอบการเชื่อมต่อ
    test1 = test_telegram_bot()
    
    # ทดสอบสัญญาณทอง
    test2 = test_gold_signal()
    
    # สรุปผล
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"   Basic Message: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"   Gold Signal: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n🎉 All tests passed! Telegram bot is working!")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    main()