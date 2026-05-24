"""
Gold Trading Dashboard - แดชบอร์ดสำหรับดูสถานะการเทรดทอง
ใช้ระบบ Dashboard ที่พัฒนาไว้แล้ว
"""

import os
import sys
import time
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
import warnings
warnings.filterwarnings('ignore')

# Add Python directory to path
sys.path.append('Python')

# Import dashboard components
try:
    from learning_dashboard import LearningDashboard
    from learning_metrics_collector import LearningMetricsCollector
    from performance_monitor import PerformanceMonitor
except ImportError as e:
    print(f"Warning: Could not import dashboard components: {e}")

class GoldTradingDashboard:
    """แดชบอร์ดสำหรับการเทรดทอง"""
    
    def __init__(self):
        self.db_path = "Data/gold_trading.db"
        self.signals_data = []
        self.performance_data = {
            'total_signals': 0,
            'correct_signals': 0,
            'accuracy': 0.0,
            'total_profit': 0.0,
            'win_rate': 0.0
        }
        
        # สร้างฐานข้อมูล
        self._init_database()
        
        # Dashboard components
        self.dashboard = None
        self.metrics_collector = None
        self.performance_monitor = None
        
        self._init_components()
        
        print("📊 Gold Trading Dashboard initialized")
    
    def _init_database(self):
        """สร้างฐานข้อมูลสำหรับเก็บข้อมูลการเทรด"""
        try:
            os.makedirs("Data", exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ตารางสัญญาณ
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gold_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    price REAL NOT NULL,
                    timeframe_votes TEXT,
                    actual_result TEXT,
                    profit_loss REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ตารางประสิทธิภาพ
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gold_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    total_signals INTEGER NOT NULL,
                    correct_signals INTEGER NOT NULL,
                    accuracy REAL NOT NULL,
                    total_profit REAL NOT NULL,
                    win_rate REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            
            print("✅ Gold trading database initialized")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def _init_components(self):
        """เริ่มต้นคอมโพเนนต์ dashboard"""
        try:
            # Learning Dashboard
            self.dashboard = LearningDashboard()
            print("✅ Learning Dashboard initialized")
            
            # Metrics Collector
            self.metrics_collector = LearningMetricsCollector()
            self.metrics_collector.start_collection()
            print("✅ Metrics Collector initialized")
            
            # Performance Monitor
            self.performance_monitor = PerformanceMonitor()
            print("✅ Performance Monitor initialized")
            
        except Exception as e:
            print(f"⚠️ Dashboard components initialization failed: {e}")
    
    def add_signal(self, signal_data):
        """เพิ่มสัญญาณใหม่"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO gold_signals 
                (timestamp, signal, confidence, price, timeframe_votes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                signal_data['timestamp'].isoformat(),
                signal_data['signal'],
                signal_data['confidence'],
                signal_data['current_price'],
                signal_data['timeframe_votes']
            ))
            
            conn.commit()
            conn.close()
            
            self.signals_data.append(signal_data)
            print(f"✅ Signal added: {signal_data['signal']} @ ${signal_data['current_price']:.2f}")
            
        except Exception as e:
            print(f"❌ Add signal error: {e}")
    
    def update_signal_result(self, signal_id, actual_result, profit_loss):
        """อัพเดทผลการเทรด"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE gold_signals 
                SET actual_result = ?, profit_loss = ?
                WHERE id = ?
            """, (actual_result, profit_loss, signal_id))
            
            conn.commit()
            conn.close()
            
            # อัพเดทประสิทธิภาพ
            self._update_performance()
            
            print(f"✅ Signal result updated: {actual_result} ({profit_loss:+.2f})")
            
        except Exception as e:
            print(f"❌ Update signal result error: {e}")
    
    def _update_performance(self):
        """อัพเดทข้อมูลประสิทธิภาพ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # คำนวณประสิทธิภาพ
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(profit_loss) as total_profit
                FROM gold_signals 
                WHERE actual_result IS NOT NULL
            """)
            
            result = cursor.fetchone()
            total, wins, total_profit = result
            
            if total > 0:
                accuracy = wins / total
                win_rate = wins / total
                
                self.performance_data = {
                    'total_signals': total,
                    'correct_signals': wins,
                    'accuracy': accuracy,
                    'total_profit': total_profit or 0.0,
                    'win_rate': win_rate
                }
                
                # บันทึกประสิทธิภาพรายวัน
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT OR REPLACE INTO gold_performance 
                    (date, total_signals, correct_signals, accuracy, total_profit, win_rate)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (today, total, wins, accuracy, total_profit or 0.0, win_rate))
                
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Performance update error: {e}")
    
    def get_signals_data(self, days=7):
        """ดึงข้อมูลสัญญาณ"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # ดึงข้อมูลสัญญาณ
            query = """
                SELECT timestamp, signal, confidence, price, actual_result, profit_loss
                FROM gold_signals 
                WHERE datetime(timestamp) >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            """.format(days)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            print(f"❌ Get signals data error: {e}")
            return pd.DataFrame()
    
    def get_performance_history(self, days=30):
        """ดึงประวัติประสิทธิภาพ"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
                SELECT date, accuracy, total_profit, win_rate, total_signals
                FROM gold_performance 
                WHERE date >= date('now', '-{} days')
                ORDER BY date
            """.format(days)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except Exception as e:
            print(f"❌ Get performance history error: {e}")
            return pd.DataFrame()
    
    def show_current_status(self):
        """แสดงสถานะปัจจุบัน"""
        print("\n" + "="*60)
        print("📊 GOLD TRADING DASHBOARD")
        print("="*60)
        
        # ข้อมูลประสิทธิภาพ
        perf = self.performance_data
        print(f"🎯 Total Signals: {perf['total_signals']}")
        print(f"✅ Correct Signals: {perf['correct_signals']}")
        print(f"📈 Accuracy: {perf['accuracy']:.1%}")
        print(f"💰 Total Profit: ${perf['total_profit']:.2f}")
        print(f"🏆 Win Rate: {perf['win_rate']:.1%}")
        
        # สัญญาณล่าสุด
        signals_df = self.get_signals_data(1)  # วันนี้
        if not signals_df.empty:
            print(f"\n📊 Today's Signals: {len(signals_df)}")
            
            for _, signal in signals_df.head(5).iterrows():
                time_str = signal['timestamp'].strftime('%H:%M')
                result_str = signal['actual_result'] if pd.notna(signal['actual_result']) else 'Pending'
                profit_str = f"${signal['profit_loss']:+.2f}" if pd.notna(signal['profit_loss']) else 'N/A'
                
                print(f"   {time_str} | {signal['signal']} | {signal['confidence']:.1%} | {result_str} | {profit_str}")
        
        print("="*60)
    
    def plot_performance_chart(self, days=7):
        """สร้างกราฟประสิทธิภาพ"""
        try:
            # ดึงข้อมูล
            signals_df = self.get_signals_data(days)
            perf_df = self.get_performance_history(days)
            
            if signals_df.empty and perf_df.empty:
                print("❌ No data to plot")
                return
            
            # สร้างกราฟ
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('🥇 Gold Trading Performance Dashboard', fontsize=16, fontweight='bold')
            
            # กราฟ 1: Signals Timeline
            if not signals_df.empty:
                buy_signals = signals_df[signals_df['signal'] == 'BUY']
                sell_signals = signals_df[signals_df['signal'] == 'SELL']
                
                ax1.scatter(buy_signals['timestamp'], buy_signals['price'], 
                           c='green', marker='^', s=100, alpha=0.7, label='BUY')
                ax1.scatter(sell_signals['timestamp'], sell_signals['price'], 
                           c='red', marker='v', s=100, alpha=0.7, label='SELL')
                
                ax1.set_title('📊 Trading Signals')
                ax1.set_ylabel('Gold Price ($)')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Format x-axis
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
                ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
                plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            # กราฟ 2: Confidence Distribution
            if not signals_df.empty:
                ax2.hist(signals_df['confidence'], bins=20, alpha=0.7, color='blue', edgecolor='black')
                ax2.set_title('🎯 Confidence Distribution')
                ax2.set_xlabel('Confidence Level')
                ax2.set_ylabel('Frequency')
                ax2.grid(True, alpha=0.3)
            
            # กราฟ 3: Accuracy Trend
            if not perf_df.empty:
                ax3.plot(perf_df['date'], perf_df['accuracy'] * 100, 
                        marker='o', linewidth=2, markersize=6, color='green')
                ax3.set_title('📈 Accuracy Trend')
                ax3.set_ylabel('Accuracy (%)')
                ax3.grid(True, alpha=0.3)
                ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            
            # กราฟ 4: Profit/Loss
            if not signals_df.empty and 'profit_loss' in signals_df.columns:
                profit_data = signals_df.dropna(subset=['profit_loss'])
                if not profit_data.empty:
                    cumulative_profit = profit_data['profit_loss'].cumsum()
                    ax4.plot(profit_data['timestamp'], cumulative_profit, 
                            linewidth=2, color='purple', marker='o', markersize=4)
                    ax4.set_title('💰 Cumulative Profit/Loss')
                    ax4.set_ylabel('Profit/Loss ($)')
                    ax4.grid(True, alpha=0.3)
                    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
                    plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            plt.show()
            
            print("📊 Performance chart displayed")
            
        except Exception as e:
            print(f"❌ Plot error: {e}")
    
    def run_dashboard(self, refresh_interval=30):
        """รันแดชบอร์ดแบบ real-time"""
        print(f"🚀 Starting Gold Trading Dashboard (refresh every {refresh_interval}s)")
        
        try:
            while True:
                # แสดงสถานะปัจจุบัน
                self.show_current_status()
                
                # รอ refresh
                print(f"\n⏳ Next update in {refresh_interval} seconds... (Ctrl+C to stop)")
                time.sleep(refresh_interval)
                
                # Clear screen (Windows)
                os.system('cls' if os.name == 'nt' else 'clear')
                
        except KeyboardInterrupt:
            print("\n⏹️ Dashboard stopped by user")
    
    def export_data(self, filename=None):
        """ส่งออกข้อมูลเป็น CSV"""
        try:
            if filename is None:
                filename = f"gold_trading_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # ดึงข้อมูลทั้งหมด
            signals_df = self.get_signals_data(30)  # 30 วันล่าสุด
            
            if not signals_df.empty:
                signals_df.to_csv(filename, index=False)
                print(f"✅ Data exported to: {filename}")
                return filename
            else:
                print("❌ No data to export")
                return None
                
        except Exception as e:
            print(f"❌ Export error: {e}")
            return None


def main():
    """ฟังก์ชันหลัก"""
    print("📊 Gold Trading Dashboard")
    print("=" * 50)
    
    # สร้าง dashboard
    dashboard = GoldTradingDashboard()
    
    # เมนูตัวเลือก
    while True:
        print("\n📋 Dashboard Options:")
        print("1. Show Current Status")
        print("2. Plot Performance Chart")
        print("3. Run Real-time Dashboard")
        print("4. Export Data")
        print("5. Add Test Signal")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            dashboard.show_current_status()
            
        elif choice == "2":
            days = int(input("Days to show (default 7): ") or "7")
            dashboard.plot_performance_chart(days)
            
        elif choice == "3":
            interval = int(input("Refresh interval (seconds, default 30): ") or "30")
            dashboard.run_dashboard(interval)
            
        elif choice == "4":
            filename = input("Filename (optional): ").strip() or None
            dashboard.export_data(filename)
            
        elif choice == "5":
            # เพิ่มสัญญาณทดสอบ
            test_signal = {
                'timestamp': datetime.now(),
                'signal': 'BUY',
                'confidence': 0.85,
                'current_price': 2000.50,
                'timeframe_votes': '3 BUY, 1 SELL'
            }
            dashboard.add_signal(test_signal)
            
        elif choice == "6":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()