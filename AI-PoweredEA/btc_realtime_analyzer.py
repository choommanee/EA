#!/usr/bin/env python3
"""
BTC Real-time Analyzer - วิเคราะห์ BTC แบบ real-time และส่งอัพเดท
"""

import time
import schedule
from btc_analysis_bot import BTCAnalysisBot

class BTCRealtimeAnalyzer:
    """วิเคราะห์ BTC แบบ real-time"""
    
    def __init__(self):
        self.bot = BTCAnalysisBot()
        self.last_analysis_time = None
        self.last_signal = None
        self.analysis_count = 0
        
        print("₿ BTC Real-time Analyzer initialized")
    
    def quick_analysis(self):
        """วิเคราะห์แบบเร็ว"""
        try:
            print(f"\n⏰ Quick Analysis #{self.analysis_count + 1} - {time.strftime('%H:%M:%S')}")
            
            success = self.bot.run_btc_analysis()
            
            if success:
                self.analysis_count += 1
                self.last_analysis_time = time.time()
                print(f"✅ Quick analysis completed")
            else:
                print(f"❌ Quick analysis failed")
                
        except Exception as e:
            print(f"❌ Quick analysis error: {e}")
    
    def detailed_analysis(self):
        """วิเคราะห์แบบละเอียด"""
        try:
            print(f"\n📊 Detailed Analysis - {time.strftime('%H:%M:%S')}")
            
            # ส่งข้อความแจ้งเตือน
            notification = f"""
₿ <b>BTC DETAILED ANALYSIS STARTING</b> ₿

⏰ <b>Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}
📊 <b>Analysis Type:</b> Comprehensive Technical Analysis
🤖 <b>AI Model:</b> Active

<i>กำลังวิเคราะห์ข้อมูลจากหลาย timeframes...</i>
            """.strip()
            
            self.bot.send_telegram_message(notification)
            
            success = self.bot.run_btc_analysis()
            
            if success:
                self.analysis_count += 1
                self.last_analysis_time = time.time()
                print(f"✅ Detailed analysis completed")
            else:
                print(f"❌ Detailed analysis failed")
                
        except Exception as e:
            print(f"❌ Detailed analysis error: {e}")
    
    def start_realtime_monitoring(self):
        """เริ่มการติดตามแบบ real-time"""
        print("₿ Starting BTC Real-time Monitoring...")
        
        # กำหนดตารางเวลา
        schedule.every(15).minutes.do(self.quick_analysis)  # วิเคราะห์เร็วทุก 15 นาที
        schedule.every(1).hours.do(self.detailed_analysis)  # วิเคราะห์ละเอียดทุก 1 ชั่วโมง
        
        # ส่งข้อความเริ่มต้น
        start_message = f"""
₿ <b>BTC REAL-TIME ANALYZER STARTED</b> ₿

⏰ <b>Started:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}
📊 <b>Quick Analysis:</b> Every 15 minutes
🔍 <b>Detailed Analysis:</b> Every 1 hour
🤖 <b>AI Model:</b> Active

<i>🚀 Ready for real-time BTC monitoring!</i>
        """.strip()
        
        self.bot.send_telegram_message(start_message)
        
        # รันการวิเคราะห์ครั้งแรก
        self.detailed_analysis()
        
        print("✅ Real-time monitoring started")
        print("📊 Quick analysis: Every 15 minutes")
        print("🔍 Detailed analysis: Every 1 hour")
        print("⏹️ Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # ตรวจสอบทุกนาที
                
        except KeyboardInterrupt:
            print("\n⏹️ Real-time monitoring stopped by user")
            
            # ส่งข้อความปิด
            stop_message = f"""
₿ <b>BTC REAL-TIME ANALYZER STOPPED</b> ₿

⏰ <b>Stopped:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}
📊 <b>Total Analyses:</b> {self.analysis_count}

<i>📴 Real-time monitoring has been stopped</i>
            """.strip()
            
            self.bot.send_telegram_message(stop_message)

def main():
    """ฟังก์ชันหลัก"""
    print("₿ BTC Real-time Analyzer")
    print("=" * 60)
    
    try:
        analyzer = BTCRealtimeAnalyzer()
        
        print("\nSelect mode:")
        print("1. Single Analysis (วิเคราะห์ครั้งเดียว)")
        print("2. Real-time Monitoring (ติดตามแบบ real-time)")
        
        choice = input("\nEnter choice (1 or 2, default 1): ").strip() or "1"
        
        if choice == "2":
            analyzer.start_realtime_monitoring()
        else:
            analyzer.detailed_analysis()
            print("\n🎉 Single analysis completed!")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()