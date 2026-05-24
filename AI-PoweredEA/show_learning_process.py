"""
Show Learning Process - แสดงกระบวนการเรียนรู้ของระบบ AI
"""

import os
import sys
import time
import json
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# Add Python directory to path
sys.path.append('Python')

class LearningProcessDemo:
    """แสดงกระบวนการเรียนรู้ของระบบ"""
    
    def __init__(self):
        self.db_path = "Data/learning_demo.db"
        self.models = {}
        self.performance_history = []
        self.learning_cycles = 0
        
        # สร้างฐานข้อมูล
        self._init_database()
        
        print("🧠 Learning Process Demo initialized")
    
    def _init_database(self):
        """สร้างฐานข้อมูล"""
        try:
            os.makedirs("Data", exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ตารางข้อมูลการเทรด
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    actual_result TEXT,
                    profit_loss REAL,
                    rsi REAL,
                    macd REAL,
                    bb_position REAL,
                    ema_signal REAL,
                    volume_ratio REAL
                )
            """)
            
            # ตารางประสิทธิภาพโมเดล
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_version TEXT NOT NULL,
                    accuracy REAL NOT NULL,
                    precision_score REAL,
                    recall_score REAL,
                    f1_score REAL,
                    training_samples INTEGER,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # ตารางการเรียนรู้
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_number INTEGER NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    old_accuracy REAL,
                    new_accuracy REAL,
                    improvement REAL,
                    training_time_seconds REAL,
                    timestamp TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            
            print("✅ Learning database initialized")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    def generate_initial_data(self, n_samples=200):
        """สร้างข้อมูลเริ่มต้น"""
        print(f"📊 Generating {n_samples} initial trading samples...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # สร้างข้อมูลจำลอง
            np.random.seed(42)
            
            for i in range(n_samples):
                # สร้าง features
                rsi = np.random.uniform(20, 80)
                macd = np.random.uniform(-0.5, 0.5)
                bb_position = np.random.uniform(0, 1)
                ema_signal = np.random.randint(0, 2)
                volume_ratio = np.random.uniform(0.5, 2.0)
                
                # สร้าง signal ตามกฎ
                if rsi < 30 and macd > 0:
                    signal = "BUY"
                    confidence = np.random.uniform(0.7, 0.9)
                elif rsi > 70 and macd < 0:
                    signal = "SELL"
                    confidence = np.random.uniform(0.7, 0.9)
                else:
                    signal = np.random.choice(["BUY", "SELL"])
                    confidence = np.random.uniform(0.5, 0.8)
                
                # สร้างผลลัพธ์ (ยิ่ง confidence สูง ยิ่งมีโอกาสถูก)
                win_probability = confidence * 0.8 + 0.1
                actual_result = "WIN" if np.random.random() < win_probability else "LOSS"
                profit_loss = np.random.uniform(10, 50) if actual_result == "WIN" else -np.random.uniform(5, 30)
                
                # บันทึกข้อมูล
                timestamp = (datetime.now() - timedelta(days=n_samples-i)).isoformat()
                
                cursor.execute("""
                    INSERT INTO trading_data 
                    (timestamp, signal, confidence, actual_result, profit_loss, 
                     rsi, macd, bb_position, ema_signal, volume_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, signal, confidence, actual_result, profit_loss,
                      rsi, macd, bb_position, ema_signal, volume_ratio))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Generated {n_samples} trading samples")
            return True
            
        except Exception as e:
            print(f"❌ Data generation error: {e}")
            return False
    
    def train_initial_model(self):
        """เทรนโมเดลเริ่มต้น"""
        print("🧠 Training initial model...")
        
        try:
            # ดึงข้อมูลจากฐานข้อมูล
            conn = sqlite3.connect(self.db_path)
            
            query = """
                SELECT rsi, macd, bb_position, ema_signal, volume_ratio, actual_result
                FROM trading_data 
                WHERE actual_result IS NOT NULL
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) < 50:
                print("❌ Not enough data for training")
                return False
            
            # เตรียมข้อมูล
            features = ['rsi', 'macd', 'bb_position', 'ema_signal', 'volume_ratio']
            X = df[features].values
            y = (df['actual_result'] == 'WIN').astype(int).values
            
            # เทรนโมเดล
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            model.fit(X, y)
            
            # ประเมินโมเดล
            y_pred = model.predict(X)
            accuracy = accuracy_score(y, y_pred)
            
            # บันทึกโมเดล
            self.models['v1.0'] = {
                'model': model,
                'accuracy': accuracy,
                'training_samples': len(X),
                'version': 'v1.0',
                'timestamp': datetime.now()
            }
            
            # บันทึกประสิทธิภาพ
            self._save_model_performance('v1.0', accuracy, len(X))
            
            print(f"✅ Initial model trained!")
            print(f"📊 Accuracy: {accuracy:.2%}")
            print(f"📈 Training samples: {len(X)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Initial training error: {e}")
            return False
    
    def simulate_new_trading_data(self, n_new_samples=50):
        """จำลองข้อมูลการเทรดใหม่"""
        print(f"📈 Simulating {n_new_samples} new trading results...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # สร้างข้อมูลใหม่ที่มีแนวโน้มเปลี่ยนแปลง
            np.random.seed(int(time.time()) % 1000)
            
            for i in range(n_new_samples):
                # สร้าง features ที่เปลี่ยนแปลงไปตามเวลา
                rsi = np.random.uniform(25, 75)  # RSI เปลี่ยนแปลง
                macd = np.random.uniform(-0.3, 0.3)  # MACD เปลี่ยนแปลง
                bb_position = np.random.uniform(0.2, 0.8)
                ema_signal = np.random.randint(0, 2)
                volume_ratio = np.random.uniform(0.8, 1.5)
                
                # กฎการสร้าง signal เปลี่ยนไป (market regime change)
                if rsi < 35 and macd > 0.1:  # เงื่อนไขเปลี่ยน
                    signal = "BUY"
                    confidence = np.random.uniform(0.6, 0.85)
                elif rsi > 65 and macd < -0.1:  # เงื่อนไขเปลี่ยน
                    signal = "SELL"
                    confidence = np.random.uniform(0.6, 0.85)
                else:
                    signal = np.random.choice(["BUY", "SELL"])
                    confidence = np.random.uniform(0.5, 0.7)
                
                # ผลลัพธ์ (ตลาดเปลี่ยนแปลง - โมเดลเก่าอาจไม่แม่นยำ)
                win_probability = confidence * 0.6 + 0.2  # ลดลงจากเดิม
                actual_result = "WIN" if np.random.random() < win_probability else "LOSS"
                profit_loss = np.random.uniform(8, 40) if actual_result == "WIN" else -np.random.uniform(8, 35)
                
                # บันทึกข้อมูล
                timestamp = (datetime.now() - timedelta(hours=n_new_samples-i)).isoformat()
                
                cursor.execute("""
                    INSERT INTO trading_data 
                    (timestamp, signal, confidence, actual_result, profit_loss, 
                     rsi, macd, bb_position, ema_signal, volume_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, signal, confidence, actual_result, profit_loss,
                      rsi, macd, bb_position, ema_signal, volume_ratio))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Added {n_new_samples} new trading samples")
            return True
            
        except Exception as e:
            print(f"❌ New data simulation error: {e}")
            return False
    
    def detect_performance_degradation(self):
        """ตรวจสอบการลดลงของประสิทธิภาพ"""
        print("🔍 Checking for performance degradation...")
        
        try:
            if 'v1.0' not in self.models:
                return False
            
            # ดึงข้อมูลล่าสุด
            conn = sqlite3.connect(self.db_path)
            
            # ประสิทธิภาพ 7 วันล่าสุด
            query = """
                SELECT actual_result
                FROM trading_data 
                WHERE actual_result IS NOT NULL 
                AND datetime(timestamp) >= datetime('now', '-7 days')
                ORDER BY timestamp DESC
            """
            
            df_recent = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df_recent) < 10:
                print("⚠️ Not enough recent data")
                return False
            
            # คำนวณประสิทธิภาพปัจจุบัน
            recent_accuracy = (df_recent['actual_result'] == 'WIN').mean()
            baseline_accuracy = self.models['v1.0']['accuracy']
            
            print(f"📊 Baseline accuracy: {baseline_accuracy:.2%}")
            print(f"📊 Recent accuracy: {recent_accuracy:.2%}")
            
            # ตรวจสอบการลดลง
            degradation = baseline_accuracy - recent_accuracy
            degradation_percent = degradation / baseline_accuracy if baseline_accuracy > 0 else 0
            
            print(f"📉 Performance degradation: {degradation_percent:.1%}")
            
            if degradation_percent > 0.15:  # ลดลงมากกว่า 15%
                print("🚨 Performance degradation detected!")
                return True
            else:
                print("✅ Performance is stable")
                return False
                
        except Exception as e:
            print(f"❌ Degradation check error: {e}")
            return False
    
    def retrain_model(self):
        """เทรนโมเดลใหม่ด้วยข้อมูลล่าสุด"""
        print("🔄 Retraining model with new data...")
        
        try:
            # ดึงข้อมูลทั้งหมด
            conn = sqlite3.connect(self.db_path)
            
            query = """
                SELECT rsi, macd, bb_position, ema_signal, volume_ratio, actual_result
                FROM trading_data 
                WHERE actual_result IS NOT NULL
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) < 100:
                print("❌ Not enough data for retraining")
                return False
            
            # เตรียมข้อมูล
            features = ['rsi', 'macd', 'bb_position', 'ema_signal', 'volume_ratio']
            X = df[features].values
            y = (df['actual_result'] == 'WIN').astype(int).values
            
            # ให้น้ำหนักมากกับข้อมูลล่าสุด (recent data weighting)
            sample_weights = np.linspace(0.5, 1.0, len(X))  # ข้อมูลใหม่มีน้ำหนักมากกว่า
            
            # เทรนโมเดลใหม่
            new_model = RandomForestClassifier(
                n_estimators=150,  # เพิ่มจำนวน trees
                max_depth=12,      # เพิ่ม depth
                min_samples_split=3,
                random_state=42
            )
            
            new_model.fit(X, y, sample_weight=sample_weights)
            
            # ประเมินโมเดลใหม่
            y_pred = new_model.predict(X)
            new_accuracy = accuracy_score(y, y_pred)
            
            # เปรียบเทียบกับโมเดลเก่า
            old_accuracy = self.models['v1.0']['accuracy']
            improvement = new_accuracy - old_accuracy
            
            print(f"📊 Old model accuracy: {old_accuracy:.2%}")
            print(f"📊 New model accuracy: {new_accuracy:.2%}")
            print(f"📈 Improvement: {improvement:+.2%}")
            
            # ตัดสินใจว่าจะใช้โมเดลใหม่หรือไม่
            if new_accuracy > old_accuracy or new_accuracy > 0.6:
                # ใช้โมเดลใหม่
                version = f"v{len(self.models) + 1}.0"
                self.models[version] = {
                    'model': new_model,
                    'accuracy': new_accuracy,
                    'training_samples': len(X),
                    'version': version,
                    'timestamp': datetime.now()
                }
                
                # บันทึกการเรียนรู้
                self._save_learning_cycle(old_accuracy, new_accuracy, improvement)
                self._save_model_performance(version, new_accuracy, len(X))
                
                print(f"✅ New model deployed: {version}")
                print(f"🎯 Performance improved by {improvement:+.2%}")
                
                return True
            else:
                print("⚠️ New model not better - keeping old model")
                return False
                
        except Exception as e:
            print(f"❌ Retraining error: {e}")
            return False
    
    def _save_learning_cycle(self, old_accuracy, new_accuracy, improvement):
        """บันทึกรอบการเรียนรู้"""
        try:
            self.learning_cycles += 1
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO learning_cycles 
                (cycle_number, trigger_reason, old_accuracy, new_accuracy, improvement, training_time_seconds, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.learning_cycles,
                "performance_degradation",
                old_accuracy,
                new_accuracy,
                improvement,
                60.0,  # จำลองเวลาเทรน
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Save learning cycle error: {e}")
    
    def _save_model_performance(self, version, accuracy, training_samples):
        """บันทึกประสิทธิภาพโมเดล"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO model_performance 
                (model_version, accuracy, training_samples, timestamp)
                VALUES (?, ?, ?, ?)
            """, (version, accuracy, training_samples, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Save performance error: {e}")
    
    def show_learning_history(self):
        """แสดงประวัติการเรียนรู้"""
        print("\n📚 Learning History:")
        print("=" * 50)
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # ดูรอบการเรียนรู้
            query = """
                SELECT cycle_number, old_accuracy, new_accuracy, improvement, timestamp
                FROM learning_cycles
                ORDER BY cycle_number
            """
            
            df_cycles = pd.read_sql_query(query, conn)
            
            if not df_cycles.empty:
                print("🔄 Learning Cycles:")
                for _, cycle in df_cycles.iterrows():
                    improvement_str = f"{cycle['improvement']:+.2%}"
                    emoji = "📈" if cycle['improvement'] > 0 else "📉"
                    
                    print(f"   Cycle {cycle['cycle_number']}: {cycle['old_accuracy']:.2%} → {cycle['new_accuracy']:.2%} ({emoji} {improvement_str})")
            
            # ดูประสิทธิภาพโมเดล
            query = """
                SELECT model_version, accuracy, training_samples, timestamp
                FROM model_performance
                ORDER BY timestamp
            """
            
            df_performance = pd.read_sql_query(query, conn)
            
            if not df_performance.empty:
                print(f"\n🤖 Model Versions:")
                for _, perf in df_performance.iterrows():
                    timestamp = datetime.fromisoformat(perf['timestamp']).strftime('%m/%d %H:%M')
                    print(f"   {perf['model_version']}: {perf['accuracy']:.2%} accuracy ({perf['training_samples']} samples) - {timestamp}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ History display error: {e}")
    
    def run_learning_simulation(self, cycles=3):
        """รันการจำลองกระบวนการเรียนรู้"""
        print(f"🧠 Running Learning Simulation ({cycles} cycles)")
        print("=" * 60)
        
        # 1. สร้างข้อมูลเริ่มต้น
        if not self.generate_initial_data(200):
            return False
        
        # 2. เทรนโมเดลเริ่มต้น
        if not self.train_initial_model():
            return False
        
        # 3. รันรอบการเรียนรู้
        for cycle in range(cycles):
            print(f"\n🔄 Learning Cycle {cycle + 1}/{cycles}")
            print("-" * 40)
            
            # เพิ่มข้อมูลใหม่
            self.simulate_new_trading_data(30)
            
            # ตรวจสอบประสิทธิภาพ
            needs_retraining = self.detect_performance_degradation()
            
            if needs_retraining:
                print("🚨 Retraining triggered!")
                self.retrain_model()
            else:
                print("✅ Model performance is good")
            
            # รอสักครู่
            time.sleep(2)
        
        # 4. แสดงผลสรุป
        self.show_learning_history()
        
        print(f"\n🎉 Learning simulation completed!")
        print(f"📊 Total learning cycles: {self.learning_cycles}")
        print(f"🤖 Total model versions: {len(self.models)}")
        
        # แสดงการปรับปรุง
        if len(self.models) > 1:
            first_accuracy = self.models['v1.0']['accuracy']
            latest_version = max(self.models.keys())
            latest_accuracy = self.models[latest_version]['accuracy']
            
            total_improvement = latest_accuracy - first_accuracy
            print(f"📈 Total improvement: {total_improvement:+.2%}")
            
            if total_improvement > 0:
                print("🎯 System learned and improved!")
            else:
                print("⚖️ System maintained performance")
        
        return True


def main():
    """ฟังก์ชันหลัก"""
    print("🧠 AI Learning Process Demonstration")
    print("=" * 50)
    
    # สร้าง demo
    demo = LearningProcessDemo()
    
    # เลือกโหมด
    print("\nSelect demonstration:")
    print("1. Full Learning Simulation (3 cycles)")
    print("2. Quick Learning Demo (1 cycle)")
    print("3. Show Learning History Only")
    
    choice = input("Enter choice (1-3): ").strip()
    
    try:
        if choice == "1":
            demo.run_learning_simulation(3)
        elif choice == "2":
            demo.run_learning_simulation(1)
        elif choice == "3":
            demo.show_learning_history()
        else:
            print("Running full simulation...")
            demo.run_learning_simulation(3)
        
        print("\n🎉 Learning demonstration completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")


if __name__ == "__main__":
    main()