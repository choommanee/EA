#!/usr/bin/env python3
"""
Quick MT5 Check - ตรวจสอบ MT5 อย่างรวดเร็ว
"""

import subprocess
import os

def quick_mt5_check():
    """ตรวจสอบ MT5 อย่างรวดเร็ว"""
    
    print("🔍 Quick MT5 Status Check")
    print("=" * 30)
    
    # ตรวจสอบ process
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq terminal64.exe'], 
                              capture_output=True, text=True, shell=True)
        
        if 'terminal64.exe' in result.stdout:
            print("✅ MT5 Terminal is RUNNING")
            
            # แสดงรายละเอียด process
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'terminal64.exe' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        print(f"   PID: {parts[1]}")
                        print(f"   Memory: {parts[4]}")
            return True
        else:
            print("❌ MT5 Terminal is NOT RUNNING")
            return False
            
    except Exception as e:
        print(f"❌ Error checking MT5: {e}")
        return False

def find_mt5_executable():
    """หา MT5 executable"""
    
    print("\n🔍 Looking for MT5 installation...")
    
    paths = [
        "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe"
    ]
    
    for path in paths:
        if os.path.exists(path):
            print(f"✅ Found MT5 at: {path}")
            return path
    
    print("❌ MT5 executable not found in common locations")
    return None

def start_mt5():
    """เริ่ม MT5"""
    
    mt5_path = find_mt5_executable()
    if not mt5_path:
        return False
    
    try:
        print(f"\n🚀 Starting MT5...")
        subprocess.Popen([mt5_path])
        print("✅ MT5 start command sent")
        print("⏳ Please wait for MT5 to fully load and login to your account")
        return True
    except Exception as e:
        print(f"❌ Failed to start MT5: {e}")
        return False

if __name__ == "__main__":
    is_running = quick_mt5_check()
    
    if not is_running:
        print("\n💡 MT5 is not running")
        choice = input("Do you want to start MT5? (y/n): ").lower().strip()
        
        if choice == 'y':
            if start_mt5():
                print("\n📋 Next steps:")
                print("1. Wait for MT5 to fully load")
                print("2. Login to your trading account")
                print("3. Enable automated trading (Tools → Options → Expert Advisors)")
                print("4. Run the bot again")
            else:
                print("\n💡 Please start MT5 manually:")
                print("- Go to Start Menu")
                print("- Search 'MetaTrader 5'")
                print("- Click to open")
        else:
            print("\n💡 Please start MT5 manually before running the bot")
    else:
        print("\n✅ MT5 is running!")
        print("💡 Make sure you're logged in and automated trading is enabled")
    
    input("\nPress Enter to exit...")
