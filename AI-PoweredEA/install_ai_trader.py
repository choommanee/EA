"""
AI Trader Installation Script
สคริปต์ติดตั้งระบบเทรด AI แบบง่ายๆ
"""

import subprocess
import sys
import os

def install_package(package):
    """ติดตั้ง package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_mt5_installation():
    """ตรวจสอบการติดตั้ง MT5"""
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 ติดตั้งแล้ว")
        return True
    except ImportError:
        print("❌ MetaTrader5 ยังไม่ได้ติดตั้ง")
        return False

def main():
    print("🚀 AI Trader Installation")
    print("=" * 40)
    
    # รายการ packages ที่จำเป็น
    required_packages = [
        "MetaTrader5",
        "pandas", 
        "numpy",
        "scikit-learn",
        "matplotlib"
    ]
    
    print("📦 กำลังติดตั้ง packages...")
    
    failed_packages = []
    
    for package in required_packages:
        print(f"   กำลังติดตั้ง {package}...")
        if install_package(package):
            print(f"   ✅ {package} ติดตั้งสำเร็จ")
        else:
            print(f"   ❌ {package} ติดตั้งไม่สำเร็จ")
            failed_packages.append(package)
    
    print("\n" + "=" * 40)
    
    if failed_packages:
        print("❌ การติดตั้งไม่สมบูรณ์")
        print("Packages ที่ติดตั้งไม่สำเร็จ:")
        for pkg in failed_packages:
            print(f"   - {pkg}")
        print("\n💡 ลองติดตั้งด้วยตนเอง:")
        print("pip install " + " ".join(failed_packages))
    else:
        print("✅ ติดตั้งสำเร็จทั้งหมด!")
        
        # ตรวจสอบ MT5
        if check_mt5_installation():
            print("\n🎉 ระบบพร้อมใช้งาน!")
            print("🚀 รันด้วยคำสั่ง: python real_ai_trader.py")
        else:
            print("\n⚠️ กรุณาติดตั้ง MetaTrader5 ก่อน")
    
    print("\n📋 ขั้นตอนต่อไป:")
    print("1. เปิด MetaTrader5")
    print("2. เปิด Tools > Options > Expert Advisors")
    print("3. เปิด 'Allow automated trading'")
    print("4. รัน: python real_ai_trader.py")

if __name__ == "__main__":
    main()