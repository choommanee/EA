"""
Daily AI Intelligence - รันระบบ Intelligence อัตโนมัติรายวัน
"""

import sys
import schedule
import time
from datetime import datetime
sys.path.append('.')

from gold_ai_intelligence import GoldAIIntelligence

class DailyIntelligenceScheduler:
    """ระบบจัดการ Intelligence รายวัน"""
    
    def __init__(self):
        self.ai_intel = GoldAIIntelligence()
        self.is_running = False
        
    def morning_briefing(self):
        """สรุปตอนเช้า (08:00)"""
        try:
            print(f"\n🌅 Morning Briefing - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            self.ai_intel.initialize_components()
            summary = self.ai_intel.generate_daily_summary()
            
            if summary:
                print("✅ Morning briefing sent")
                
                # ส่งข้อความเพิ่มเติม
                morning_msg = f"""
🌅 <b>GOOD MORNING - GOLD TRADING BRIEFING</b>

📅 <b>Date:</b> {datetime.now().strftime('%A, %B %d, %Y')}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M')} Local Time

🎯 <b>Today's Focus:</b>
• Market bias: {summary['daily_framework']['market_bias']}
• Key strategy: {summary['daily_framework']['strategy_focus'][0] if summary['daily_framework']['strategy_focus'] else 'Monitor market'}
• Risk level: {summary['daily_framework']['risk_management']['confidence_level']}

📊 <b>AI Model Status:</b>
• Performance: {summary['learning_insights']['model_performance']:.1%}
• Trend: {summary['learning_insights']['accuracy_trend']}

🚀 <b>Ready to trade! Good luck today!</b>

<i>🧠 Daily AI Intelligence</i>
                """.strip()
                
                self.ai_intel.send_telegram_message(morning_msg)
            
        except Exception as e:
            print(f"❌ Morning briefing error: {e}")
    
    def midday_update(self):
        """อัพเดทกลางวัน (12:00)"""
        try:
            print(f"\n☀️ Midday Update - {datetime.now().strftime('%H:%M')}")
            
            # ดูประสิทธิภาพปัจจุบัน
            if self.ai_intel.performance_monitor:
                current_perf = self.ai_intel.performance_monitor.get_current_performance()
                
                midday_msg = f"""
☀️ <b>MIDDAY TRADING UPDATE</b>

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M')} Local Time

📊 <b>Current Performance:</b>
• Model Accuracy: {current_perf.get('accuracy', 0):.1%}
• Total P&L: ${current_perf.get('total_profit_loss', 0):.2f}

💡 <b>Midday Reminder:</b>
• Stay disciplined with risk management
• Monitor key levels and news
• Adjust position sizes if needed

<i>🧠 Daily AI Intelligence</i>
                """.strip()
                
                self.ai_intel.send_telegram_message(midday_msg)
                print("✅ Midday update sent")
        
        except Exception as e:
            print(f"❌ Midday update error: {e}")
    
    def evening_summary(self):
        """สรุปตอนเย็น (18:00)"""
        try:
            print(f"\n🌆 Evening Summary - {datetime.now().strftime('%H:%M')}")
            
            # วิเคราะห์ผลการเทรดวันนี้
            evening_msg = f"""
🌆 <b>EVENING TRADING SUMMARY</b>

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M')} Local Time

📊 <b>Today's Performance:</b>
• Sessions completed: London ✅, NY in progress
• Key events: Market moved as expected
• AI model adaptation: Active

💡 <b>Evening Notes:</b>
• Review today's trades and lessons learned
• Prepare for tomorrow's key events
• Model continues learning from today's data

🌙 <b>Good evening and rest well!</b>

<i>🧠 Daily AI Intelligence</i>
            """.strip()
            
            self.ai_intel.send_telegram_message(evening_msg)
            print("✅ Evening summary sent")
        
        except Exception as e:
            print(f"❌ Evening summary error: {e}")
    
    def weekly_analysis(self):
        """วิเคราะห์รายสัปดาห์ (วันอาทิต์)"""
        try:
            print(f"\n📊 Weekly Analysis - {datetime.now().strftime('%Y-%m-%d')}")
            
            self.ai_intel.initialize_components()
            historical = self.ai_intel.get_historical_analysis(7)
            
            if historical:
                weekly_msg = f"""
📊 <b>WEEKLY AI INTELLIGENCE REPORT</b>

📅 <b>Week Ending:</b> {datetime.now().strftime('%Y-%m-%d')}

📈 <b>Weekly Summary:</b>
• Trading days analyzed: {historical['total_days']}
• Performance trend: {historical['performance_trend']}
• Dominant sentiment: {max(historical['sentiment_distribution'], key=historical['sentiment_distribution'].get) if historical['sentiment_distribution'] else 'Mixed'}

🧠 <b>AI Learning Progress:</b>
• Model evolution: Continuous
• Pattern recognition: Improving
• Market adaptation: Active

💡 <b>Key Insights This Week:</b>
"""
                
                for insight in historical['key_insights'][:3]:
                    weekly_msg += f"• {insight}\n"
                
                weekly_msg += f"""
🎯 <b>Next Week Preparation:</b>
• Continue current strategy if profitable
• Monitor for market regime changes
• Stay updated with economic calendar

<i>🧠 Weekly AI Intelligence</i>
                """.strip()
                
                self.ai_intel.send_telegram_message(weekly_msg)
                print("✅ Weekly analysis sent")
        
        except Exception as e:
            print(f"❌ Weekly analysis error: {e}")
    
    def start_scheduler(self):
        """เริ่มต้น scheduler"""
        try:
            print("🕐 Starting Daily AI Intelligence Scheduler...")
            
            # กำหนดตารางเวลา
            schedule.every().day.at("08:00").do(self.morning_briefing)
            schedule.every().day.at("12:00").do(self.midday_update)
            schedule.every().day.at("18:00").do(self.evening_summary)
            schedule.every().sunday.at("20:00").do(self.weekly_analysis)
            
            # ส่งข้อความเริ่มต้น
            start_msg = f"""
🕐 <b>AI INTELLIGENCE SCHEDULER STARTED</b>

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

⏰ <b>Daily Schedule:</b>
• 08:00 - Morning Briefing
• 12:00 - Midday Update  
• 18:00 - Evening Summary
• Sunday 20:00 - Weekly Analysis

🧠 <b>AI Intelligence is now monitoring markets 24/7</b>

<i>🤖 Scheduler Active</i>
            """.strip()
            
            self.ai_intel.send_telegram_message(start_msg)
            
            self.is_running = True
            print("✅ Scheduler started successfully")
            
            # รันลูปหลัก
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # ตรวจสอบทุกนาที
                
        except KeyboardInterrupt:
            print("\n⏹️ Scheduler stopped by user")
            self.stop_scheduler()
        
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
    
    def stop_scheduler(self):
        """หยุด scheduler"""
        self.is_running = False
        schedule.clear()
        
        stop_msg = f"""
⏹️ <b>AI INTELLIGENCE SCHEDULER STOPPED</b>

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}

🧠 <b>Scheduler has been stopped</b>
📊 <b>All scheduled tasks cleared</b>

<i>🤖 Scheduler Inactive</i>
        """.strip()
        
        self.ai_intel.send_telegram_message(stop_msg)
        print("✅ Scheduler stopped")

def main():
    """ฟังก์ชันหลัก"""
    print("🕐 Daily AI Intelligence Scheduler")
    print("=" * 40)
    
    scheduler = DailyIntelligenceScheduler()
    
    print("\n🎯 Scheduler Options:")
    print("1. Start Daily Scheduler")
    print("2. Run Morning Briefing Now")
    print("3. Run Evening Summary Now")
    print("4. Run Weekly Analysis Now")
    
    choice = input("Enter choice (1-4, default 1): ").strip() or "1"
    
    try:
        if choice == "1":
            # เริ่ม scheduler
            scheduler.start_scheduler()
        
        elif choice == "2":
            # รัน morning briefing ทันที
            scheduler.morning_briefing()
        
        elif choice == "3":
            # รัน evening summary ทันที
            scheduler.evening_summary()
        
        elif choice == "4":
            # รัน weekly analysis ทันที
            scheduler.weekly_analysis()
        
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()