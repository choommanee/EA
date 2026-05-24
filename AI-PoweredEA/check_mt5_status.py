#!/usr/bin/env python3
"""
MT5 Status Checker - ตรวจสอบสถานะ MT5 Terminal
"""

import psutil
import os
import subprocess

def check_mt5_running():
    """ตรวจสอบว่า MT5 กำลังทำงานอยู่หรือไม่"""
    
    print("🔍 Checking MT5 Terminal Status")
    print("=" * 40)
    
    # 1. ตรวจสอบ process ที่กำลังทำงาน
    mt5_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and 'terminal64.exe' in proc.info['name'].lower():
                mt5_processes.append(proc)
            elif proc.info['name'] and 'metatrader' in proc.info['name'].lower():
                mt5_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if mt5_processes:
        print(f"✅ MT5 Terminal is RUNNING ({len(mt5_processes)} process(es))")
        for i, proc in enumerate(mt5_processes, 1):
            try:
                print(f"   {i}. PID: {proc.pid}")
                print(f"      Name: {proc.info['name']}")
                if proc.info['exe']:
                    print(f"      Path: {proc.info['exe']}")
                print(f"      Memory: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
            except Exception as e:
                print(f"      Error getting details: {e}")
        return True
    else:
        print("❌ MT5 Terminal is NOT RUNNING")
        return False

def check_mt5_installation():
    """ตรวจสอบการติดตั้ง MT5"""
    
    print("\n🔍 Checking MT5 Installation")
    print("=" * 40)
    
    common_paths = [
        "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
        "C:\\Users\\User\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\terminal64.exe"
    ]
    
    found_installations = []
    
    for path in common_paths:
        if '*' in path:
            # Handle wildcard paths
            import glob
            matches = glob.glob(path)
            for match in matches:
                if os.path.exists(match):
                    found_installations.append(match)
        else:
            if os.path.exists(path):
                found_installations.append(path)
    
    if found_installations:
        print(f"✅ Found MT5 installations:")
        for i, path in enumerate(found_installations, 1):
            print(f"   {i}. {path}")
        return found_installations
    else:
        print("❌ No MT5 installations found")
        return []

def start_mt5_if_needed():
    """เริ่ม MT5 ถ้ายังไม่ทำงาน"""
    
    if check_mt5_running():
        return True
    
    print("\n🚀 Attempting to start MT5...")
    
    installations = check_mt5_installation()
    if not installations:
        print("❌ Cannot start MT5 - No installations found")
        return False
    
    # ลองเริ่ม MT5 จากการติดตั้งแรกที่เจอ
    mt5_path = installations[0]
    
    try:
        print(f"🔄 Starting MT5 from: {mt5_path}")
        subprocess.Popen([mt5_path], shell=True)
        
        # รอสักครู่แล้วเช็คอีกครั้ง
        import time
        print("⏳ Waiting for MT5 to start...")
        time.sleep(5)
        
        if check_mt5_running():
            print("✅ MT5 started successfully!")
            return True
        else:
            print("❌ MT5 failed to start")
            return False
            
    except Exception as e:
        print(f"❌ Error starting MT5: {e}")
        return False

def main():
    """Main function"""
    
    print("🔧 MT5 Terminal Status Checker")
    print("=" * 50)
    
    # เช็คสถานะปัจจุบัน
    is_running = check_mt5_running()
    
    # เช็คการติดตั้ง
    installations = check_mt5_installation()
    
    if not is_running and installations:
        print("\n💡 MT5 is installed but not running")
        choice = input("\nDo you want to start MT5? (y/n): ").lower().strip()
        
        if choice == 'y':
            start_mt5_if_needed()
        else:
            print("💡 Please start MT5 manually before running the trading bot")
    
    elif not is_running and not installations:
        print("\n❌ MT5 is not installed")
        print("💡 Please install MetaTrader 5 first")
        print("   Download from: https://www.metatrader5.com/en/download")
    
    elif is_running:
        print("\n✅ MT5 is ready!")
        print("💡 You can now run the trading bot")
    
    print("\n" + "=" * 50)
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
