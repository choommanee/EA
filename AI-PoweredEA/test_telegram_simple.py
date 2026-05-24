"""
Simple Telegram Test - ทดสอบ Telegram แบบง่ายๆ
"""

import requests
from datetime import datetime

def send_simple_message():
    """ส่งข้อความง่ายๆ"""
    
    # ข้อมูล Telegram
    token = "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
    chat_id = "-1002852894581"
    
    # ข้อความง่ายๆ
    message = f"🧪 Test message from Python at {datetime.now().strftime('%H:%M:%S')}"
    
    print(f"📱 Sending: {message}")
    print(f"📊 To chat: {chat_id}")
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        
        print(f"🔗 URL: {url}")
        print(f"📦 Payload: {payload}")
        
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Message sent successfully!")
                print(f"📊 Message ID: {result['result']['message_id']}")
                return True
            else:
                print("❌ Telegram API returned error")
                return False
        else:
            print("❌ HTTP error")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def get_chat_info():
    """ดูข้อมูล chat"""
    token = "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
    chat_id = "-1002852894581"
    
    try:
        url = f"https://api.telegram.org/bot{token}/getChat"
        payload = {'chat_id': chat_id}
        
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"📊 Chat Info Response: {response.status_code}")
        print(f"📄 Chat Data: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                chat_data = result['result']
                print(f"✅ Chat Title: {chat_data.get('title', 'Unknown')}")
                print(f"📊 Chat Type: {chat_data.get('type', 'Unknown')}")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Chat info error: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("📱 Simple Telegram Test")
    print("=" * 30)
    
    # ดูข้อมูล chat
    print("1. 📊 Getting chat info...")
    get_chat_info()
    
    print("\n2. 📱 Sending test message...")
    success = send_simple_message()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("💡 Check your Telegram group for the message")
    else:
        print("\n❌ Test failed")
        print("💡 Please check:")
        print("   - Bot token is correct")
        print("   - Chat ID is correct") 
        print("   - Bot is added to the group")
        print("   - Bot has permission to send messages")

if __name__ == "__main__":
    main()