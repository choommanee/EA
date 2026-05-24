#!/usr/bin/env python3
"""
Run BTC Analysis - รันการวิเคราะห์ BTC แบบง่าย
"""

from btc_analysis_bot import BTCAnalysisBot
import sys

def main():
    """รันการวิเคราะห์ BTC"""
    print("₿ Running BTC Analysis...")
    print("=" * 40)
    
    try:
        # สร้างและรัน bot
        bot = BTCAnalysisBot()
        success = bot.run_btc_analysis()
        
        if success:
            print("\n✅ BTC analysis completed and sent to Telegram!")
        else:
            print("\n❌ BTC analysis failed!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()