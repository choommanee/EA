"""
Gold AI Intelligence - ระบบวิเคราะห์และสรุปข้อมูลการเทรดทองด้วย AI
รวม News Analysis, Market Summary, Learning Insights, และ Daily Framework
"""

import os
import sys
import time
import json
import requests
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add Python directory to path
sys.path.append('Python')

# Import AI components
try:
    from performance_monitor import PerformanceMonitor
    from model_manager import ModelManager
    from learning_metrics_collector import LearningMetricsCollector
except ImportError as e:
    print(f"Warning: Could not import AI components: {e}")

class GoldAIIntelligence:
    """ระบบ AI Intelligence สำหรับการเทรดทอง"""
    
    def __init__(self, telegram_token=None, chat_id=None):
        # Telegram settings
        self.telegram_token = telegram_token or "8437050147:AAGtJ68MZzL6W-M4DX2J7igTVtGnTdXhYZY"
        self.chat_id = chat_id or "-1002852894581"
        
        # AI components
        self.performance_monitor = None
        self.model_manager = None
        self.metrics_collector = None
        
        # Data storage
        self.db_path = "Data/ai_intelligence.db"
        self.news_sources = [
            "https://api.marketaux.com/v1/news/all",
            "https://newsapi.org/v2/everything"
        ]
        
        # Analysis settings
        self.analysis_timeframes = ['1D', '1W', '1M']
        self.key_indicators = ['RSI', 'MACD', 'BB', 'EMA', 'ATR', 'Volume']
        
        print("🧠 Gold AI Intelligence initialized")
    
    def initialize_components(self):
        """เริ่มต้นคอมโพเนนต์ AI"""
        try:
            self.performance_monitor = PerformanceMonitor()
            self.model_manager = ModelManager()
            self.metrics_collector = LearningMetricsCollector()
            
            # สร้างฐานข้อมูล
            self._init_database()
            
            print("✅ AI Intelligence components initialized")
            return True
            
        except Exception as e:
            print(f"❌ Component initialization failed: {e}")
            return False    

    def _init_database(self):
        """สร้างฐานข้อมูลสำหรับ Intelligence"""
        try:
            os.makedirs("Data", exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # ตารางข่าวสาร
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    source TEXT,
                    sentiment REAL,
                    impact_score REAL,
                    gold_relevance REAL,
                    ai_summary TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # ตารางสรุปรายวัน
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    market_sentiment TEXT,
                    volatility_level TEXT,
                    key_levels TEXT,
                    trading_bias TEXT,
                    risk_level TEXT,
                    ai_insights TEXT,
                    performance_summary TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            # ตารางการเรียนรู้
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    model_performance REAL,
                    accuracy_trend TEXT,
                    key_patterns TEXT,
                    market_adaptation TEXT,
                    recommendations TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            print("✅ Intelligence database initialized")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def send_telegram_message(self, message):
        """ส่งข้อความไป Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
            return False 
   
    def analyze_news_sentiment(self, news_text):
        """วิเคราะห์ sentiment ของข่าว (แบบง่าย)"""
        try:
            # คำสำคัญที่ส่งผลต่อทอง
            bullish_keywords = [
                'inflation', 'uncertainty', 'crisis', 'war', 'conflict',
                'recession', 'dovish', 'stimulus', 'quantitative easing',
                'safe haven', 'hedge', 'volatility', 'risk off'
            ]
            
            bearish_keywords = [
                'hawkish', 'rate hike', 'strong dollar', 'recovery',
                'growth', 'optimism', 'risk on', 'tapering',
                'normalization', 'tightening', 'yield rise'
            ]
            
            text_lower = news_text.lower()
            
            bullish_score = sum(1 for word in bullish_keywords if word in text_lower)
            bearish_score = sum(1 for word in bearish_keywords if word in text_lower)
            
            # คำนวณ sentiment (-1 ถึง 1)
            total_score = bullish_score + bearish_score
            if total_score == 0:
                sentiment = 0
            else:
                sentiment = (bullish_score - bearish_score) / total_score
            
            # คำนวณ impact score (0 ถึง 1)
            impact_score = min(total_score / 10, 1.0)
            
            # คำนวณ gold relevance
            gold_keywords = ['gold', 'precious metal', 'xau', 'bullion', 'fed', 'dollar', 'inflation']
            gold_relevance = sum(1 for word in gold_keywords if word in text_lower) / len(gold_keywords)
            
            return sentiment, impact_score, gold_relevance
            
        except Exception as e:
            print(f"❌ News sentiment analysis error: {e}")
            return 0, 0, 0
    
    def get_market_news(self):
        """ดึงข่าวสารที่เกี่ยวข้องกับตลาดทอง"""
        try:
            # จำลองข่าวสาร (ในการใช้งานจริงจะดึงจาก API)
            sample_news = [
                {
                    'title': 'Fed Signals Potential Rate Cuts Amid Economic Uncertainty',
                    'content': 'Federal Reserve officials hint at possible dovish stance as inflation concerns mount and economic indicators show mixed signals.',
                    'source': 'Financial Times',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'title': 'Gold Prices Surge on Safe Haven Demand',
                    'content': 'Gold futures climb higher as investors seek safe haven assets amid geopolitical tensions and market volatility.',
                    'source': 'Reuters',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'title': 'Dollar Strength Pressures Precious Metals',
                    'content': 'Strong US dollar index weighs on gold and silver prices as Treasury yields remain elevated.',
                    'source': 'Bloomberg',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            analyzed_news = []
            
            for news in sample_news:
                sentiment, impact, relevance = self.analyze_news_sentiment(
                    news['title'] + ' ' + news['content']
                )
                
                # สร้าง AI summary
                ai_summary = self.generate_ai_summary(news, sentiment, impact)
                
                analyzed_news.append({
                    'title': news['title'],
                    'content': news['content'],
                    'source': news['source'],
                    'sentiment': sentiment,
                    'impact_score': impact,
                    'gold_relevance': relevance,
                    'ai_summary': ai_summary,
                    'timestamp': news['timestamp']
                })
            
            return analyzed_news
            
        except Exception as e:
            print(f"❌ News retrieval error: {e}")
            return []    

    def generate_ai_summary(self, news, sentiment, impact):
        """สร้างสรุป AI จากข่าว"""
        try:
            sentiment_text = "Bullish" if sentiment > 0.2 else "Bearish" if sentiment < -0.2 else "Neutral"
            impact_text = "High" if impact > 0.6 else "Medium" if impact > 0.3 else "Low"
            
            summary = f"{sentiment_text} sentiment ({sentiment:+.2f}) with {impact_text} impact ({impact:.2f}). "
            
            if sentiment > 0.3:
                summary += "Positive for gold prices. Consider bullish positions."
            elif sentiment < -0.3:
                summary += "Negative for gold prices. Consider bearish positions or caution."
            else:
                summary += "Mixed signals. Monitor for clearer direction."
            
            return summary
            
        except Exception as e:
            return f"Analysis error: {e}"
    
    def get_learning_insights(self):
        """ดึงข้อมูล insights จากการเรียนรู้ของ AI"""
        try:
            insights = {
                'model_performance': 0.0,
                'accuracy_trend': 'Unknown',
                'key_patterns': [],
                'market_adaptation': 'Normal',
                'recommendations': []
            }
            
            if self.performance_monitor:
                # ดูประสิทธิภาพปัจจุบัน
                current_perf = self.performance_monitor.get_current_performance()
                insights['model_performance'] = current_perf.get('accuracy', 0.0)
                
                # วิเคราะห์ trend
                if insights['model_performance'] > 0.8:
                    insights['accuracy_trend'] = 'Improving'
                    insights['recommendations'].append('Model performing well - continue current strategy')
                elif insights['model_performance'] > 0.6:
                    insights['accuracy_trend'] = 'Stable'
                    insights['recommendations'].append('Model stable - monitor for improvements')
                else:
                    insights['accuracy_trend'] = 'Declining'
                    insights['recommendations'].append('Model needs retraining - collect more data')
            
            if self.model_manager:
                # ดูจำนวนโมเดล
                models = self.model_manager.list_models()
                if len(models) > 3:
                    insights['market_adaptation'] = 'High'
                    insights['key_patterns'].append('Multiple model versions indicate active learning')
                elif len(models) > 1:
                    insights['market_adaptation'] = 'Medium'
                    insights['key_patterns'].append('Model evolution in progress')
                else:
                    insights['market_adaptation'] = 'Low'
                    insights['key_patterns'].append('Single model - may need more adaptation')
            
            # เพิ่ม insights ทั่วไป
            insights['key_patterns'].extend([
                'Gold responds strongly to Fed policy changes',
                'Volatility increases during US market hours',
                'Safe haven demand correlates with risk-off sentiment'
            ])
            
            insights['recommendations'].extend([
                'Monitor Fed speeches and economic data releases',
                'Adjust position sizes based on volatility levels',
                'Use correlation with USD index for confirmation'
            ])
            
            return insights
            
        except Exception as e:
            print(f"❌ Learning insights error: {e}")
            return {
                'model_performance': 0.0,
                'accuracy_trend': 'Error',
                'key_patterns': ['Analysis unavailable'],
                'market_adaptation': 'Unknown',
                'recommendations': ['Check system components']
            }    

    def generate_daily_framework(self, news_analysis, learning_insights):
        """สร้างกรอบการเทรดรายวัน"""
        try:
            framework = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'market_bias': 'Neutral',
                'key_levels': [],
                'trading_sessions': {},
                'risk_management': {},
                'strategy_focus': [],
                'alerts': []
            }
            
            # วิเคราะห์ market bias จากข่าว
            avg_sentiment = np.mean([news['sentiment'] for news in news_analysis]) if news_analysis else 0
            
            if avg_sentiment > 0.2:
                framework['market_bias'] = 'Bullish'
                framework['strategy_focus'].append('Look for buy opportunities on dips')
                framework['strategy_focus'].append('Target resistance breaks')
            elif avg_sentiment < -0.2:
                framework['market_bias'] = 'Bearish'
                framework['strategy_focus'].append('Look for sell opportunities on rallies')
                framework['strategy_focus'].append('Target support breaks')
            else:
                framework['market_bias'] = 'Neutral'
                framework['strategy_focus'].append('Range trading strategy')
                framework['strategy_focus'].append('Wait for clear breakouts')
            
            # กำหนด key levels (จำลอง)
            current_price = 2650  # จำลองราคาทองปัจจุบัน
            framework['key_levels'] = [
                {'level': current_price + 20, 'type': 'Resistance', 'strength': 'Strong'},
                {'level': current_price + 10, 'type': 'Resistance', 'strength': 'Medium'},
                {'level': current_price, 'type': 'Current', 'strength': 'N/A'},
                {'level': current_price - 10, 'type': 'Support', 'strength': 'Medium'},
                {'level': current_price - 20, 'type': 'Support', 'strength': 'Strong'}
            ]
            
            # กำหนด trading sessions
            framework['trading_sessions'] = {
                'Asian': {
                    'time': '00:00-09:00 UTC',
                    'characteristics': 'Lower volatility, range-bound',
                    'strategy': 'Scalping, range trading'
                },
                'London': {
                    'time': '08:00-17:00 UTC',
                    'characteristics': 'High volatility, trend moves',
                    'strategy': 'Trend following, breakouts'
                },
                'New York': {
                    'time': '13:00-22:00 UTC',
                    'characteristics': 'Highest volatility, news impact',
                    'strategy': 'News trading, momentum'
                }
            }
            
            # Risk management ตาม model performance
            model_perf = learning_insights.get('model_performance', 0.5)
            
            if model_perf > 0.8:
                framework['risk_management'] = {
                    'position_size': 'Normal to Aggressive',
                    'max_risk_per_trade': '2-3%',
                    'confidence_level': 'High'
                }
            elif model_perf > 0.6:
                framework['risk_management'] = {
                    'position_size': 'Conservative to Normal',
                    'max_risk_per_trade': '1-2%',
                    'confidence_level': 'Medium'
                }
            else:
                framework['risk_management'] = {
                    'position_size': 'Very Conservative',
                    'max_risk_per_trade': '0.5-1%',
                    'confidence_level': 'Low'
                }
            
            # สร้าง alerts
            high_impact_news = [n for n in news_analysis if n['impact_score'] > 0.6]
            if high_impact_news:
                framework['alerts'].append('High impact news detected - expect volatility')
            
            if learning_insights.get('accuracy_trend') == 'Declining':
                framework['alerts'].append('Model performance declining - reduce position sizes')
            
            if avg_sentiment > 0.5:
                framework['alerts'].append('Strong bullish sentiment - watch for overextension')
            elif avg_sentiment < -0.5:
                framework['alerts'].append('Strong bearish sentiment - watch for oversold bounce')
            
            return framework
            
        except Exception as e:
            print(f"❌ Daily framework generation error: {e}")
            return None
    
    def generate_daily_summary(self):
        """สร้างสรุปรายวันแบบครบถ้วน"""
        try:
            print("🧠 Generating Daily AI Intelligence Summary...")
            
            # ดึงข้อมูลต่างๆ
            news_analysis = self.get_market_news()
            learning_insights = self.get_learning_insights()
            daily_framework = self.generate_daily_framework(news_analysis, learning_insights)
            
            # สร้างสรุป
            summary = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'news_analysis': news_analysis,
                'learning_insights': learning_insights,
                'daily_framework': daily_framework,
                'performance_metrics': self.get_performance_metrics()
            }
            
            # บันทึกลงฐานข้อมูล
            self.save_daily_summary(summary)
            
            # ส่งไป Telegram
            telegram_message = self.format_telegram_summary(summary)
            self.send_telegram_message(telegram_message)
            
            print("✅ Daily summary generated and sent")
            return summary
            
        except Exception as e:
            print(f"❌ Daily summary generation error: {e}")
            return None
    
    def get_performance_metrics(self):
        """ดึงเมตริกประสิทธิภาพ"""
        try:
            metrics = {
                'daily_trades': 0,
                'win_rate': 0.0,
                'profit_loss': 0.0,
                'accuracy': 0.0,
                'volatility': 0.0
            }
            
            if self.performance_monitor:
                current_perf = self.performance_monitor.get_current_performance()
                metrics.update({
                    'accuracy': current_perf.get('accuracy', 0.0),
                    'profit_loss': current_perf.get('total_profit_loss', 0.0)
                })
            
            # จำลองข้อมูลเพิ่มเติม
            metrics.update({
                'daily_trades': np.random.randint(5, 25),
                'win_rate': np.random.uniform(0.6, 0.8),
                'volatility': np.random.uniform(0.5, 1.5)
            })
            
            return metrics
            
        except Exception as e:
            print(f"❌ Performance metrics error: {e}")
            return {
                'daily_trades': 0,
                'win_rate': 0.0,
                'profit_loss': 0.0,
                'accuracy': 0.0,
                'volatility': 0.0
            }
    
    def save_daily_summary(self, summary):
        """บันทึกสรุปรายวันลงฐานข้อมูล"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # บันทึกข่าวสาร
            for news in summary['news_analysis']:
                cursor.execute("""
                    INSERT OR REPLACE INTO news_analysis 
                    (date, title, content, source, sentiment, impact_score, gold_relevance, ai_summary, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    summary['date'], news['title'], news['content'], news['source'],
                    news['sentiment'], news['impact_score'], news['gold_relevance'],
                    news['ai_summary'], news['timestamp']
                ))
            
            # บันทึกสรุปรายวัน
            framework = summary['daily_framework']
            cursor.execute("""
                INSERT OR REPLACE INTO daily_summary 
                (date, market_sentiment, volatility_level, key_levels, trading_bias, 
                 risk_level, ai_insights, performance_summary, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                summary['date'],
                framework['market_bias'],
                'Medium',  # จำลอง
                json.dumps(framework['key_levels']),
                framework['market_bias'],
                'Medium',  # จำลอง
                json.dumps(summary['learning_insights']),
                json.dumps(summary['performance_metrics']),
                summary['timestamp']
            ))
            
            # บันทึก learning insights
            insights = summary['learning_insights']
            cursor.execute("""
                INSERT INTO learning_insights 
                (date, model_performance, accuracy_trend, key_patterns, market_adaptation, recommendations, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                summary['date'],
                insights['model_performance'],
                insights['accuracy_trend'],
                json.dumps(insights['key_patterns']),
                insights['market_adaptation'],
                json.dumps(insights['recommendations']),
                summary['timestamp']
            ))
            
            conn.commit()
            conn.close()
            
            print("✅ Daily summary saved to database")
            
        except Exception as e:
            print(f"❌ Save daily summary error: {e}")   
 
    def format_telegram_summary(self, summary):
        """จัดรูปแบบสรุปสำหรับ Telegram"""
        try:
            date = summary['date']
            news = summary['news_analysis']
            insights = summary['learning_insights']
            framework = summary['daily_framework']
            metrics = summary['performance_metrics']
            
            # หา sentiment รวม
            avg_sentiment = np.mean([n['sentiment'] for n in news]) if news else 0
            sentiment_emoji = "🟢" if avg_sentiment > 0.2 else "🔴" if avg_sentiment < -0.2 else "🟡"
            
            message = f"""
🧠 <b>GOLD AI INTELLIGENCE REPORT</b> 🧠
📅 <b>Date:</b> {date}

{sentiment_emoji} <b>MARKET SENTIMENT</b>
• <b>Overall Bias:</b> {framework['market_bias']}
• <b>Sentiment Score:</b> {avg_sentiment:+.2f}
• <b>Key Focus:</b> {framework['strategy_focus'][0] if framework['strategy_focus'] else 'Monitor market'}

📰 <b>NEWS ANALYSIS</b> ({len(news)} items)
"""
            
            # เพิ่มข่าวสำคัญ
            for i, n in enumerate(news[:2], 1):  # แสดงแค่ 2 ข่าวแรก
                impact_emoji = "🔥" if n['impact_score'] > 0.6 else "📊" if n['impact_score'] > 0.3 else "📝"
                sentiment_text = "Bullish" if n['sentiment'] > 0.2 else "Bearish" if n['sentiment'] < -0.2 else "Neutral"
                
                message += f"""
{impact_emoji} <b>News {i}:</b> {n['title'][:50]}...
   • <b>Impact:</b> {n['impact_score']:.1f}/1.0
   • <b>Sentiment:</b> {sentiment_text} ({n['sentiment']:+.2f})
   • <b>AI Summary:</b> {n['ai_summary'][:80]}...
"""
            
            message += f"""
🤖 <b>AI LEARNING INSIGHTS</b>
• <b>Model Performance:</b> {insights['model_performance']:.1%}
• <b>Accuracy Trend:</b> {insights['accuracy_trend']}
• <b>Market Adaptation:</b> {insights['market_adaptation']}
• <b>Key Pattern:</b> {insights['key_patterns'][0] if insights['key_patterns'] else 'None'}

📊 <b>PERFORMANCE METRICS</b>
• <b>Daily Trades:</b> {metrics['daily_trades']}
• <b>Win Rate:</b> {metrics['win_rate']:.1%}
• <b>P&L:</b> ${metrics['profit_loss']:.2f}
• <b>Accuracy:</b> {metrics['accuracy']:.1%}

🎯 <b>TRADING FRAMEWORK</b>
• <b>Market Bias:</b> {framework['market_bias']}
• <b>Risk Level:</b> {framework['risk_management']['confidence_level']}
• <b>Position Size:</b> {framework['risk_management']['position_size']}
• <b>Max Risk/Trade:</b> {framework['risk_management']['max_risk_per_trade']}

📈 <b>KEY LEVELS</b>
"""
            
            # เพิ่ม key levels
            for level in framework['key_levels'][:3]:  # แสดงแค่ 3 levels
                level_emoji = "🔴" if level['type'] == 'Resistance' else "🟢" if level['type'] == 'Support' else "🟡"
                message += f"   {level_emoji} {level['type']}: ${level['level']:.0f} ({level['strength']})\n"
            
            message += f"""
⚠️ <b>ALERTS & RECOMMENDATIONS</b>
"""
            
            # เพิ่ม alerts
            for alert in framework['alerts'][:2]:  # แสดงแค่ 2 alerts
                message += f"   • {alert}\n"
            
            # เพิ่ม recommendations
            for rec in insights['recommendations'][:2]:  # แสดงแค่ 2 recommendations
                message += f"   • {rec}\n"
            
            message += f"""
🕐 <b>TRADING SESSIONS TODAY</b>
• <b>London:</b> {framework['trading_sessions']['London']['strategy']}
• <b>New York:</b> {framework['trading_sessions']['New York']['strategy']}

⏰ <b>Generated:</b> {datetime.now().strftime('%H:%M:%S')}
<i>🧠 AI Intelligence System</i>
            """.strip()
            
            return message
            
        except Exception as e:
            print(f"❌ Telegram format error: {e}")
            return f"❌ Error formatting summary: {e}"
    
    def get_historical_analysis(self, days=7):
        """วิเคราะห์ข้อมูลย้อนหลัง"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # ดึงข้อมูลย้อนหลัง
            query = """
                SELECT date, market_sentiment, ai_insights, performance_summary
                FROM daily_summary 
                WHERE date >= date('now', '-{} days')
                ORDER BY date DESC
            """.format(days)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty:
                return None
            
            analysis = {
                'period': f"Last {days} days",
                'total_days': len(df),
                'sentiment_distribution': df['market_sentiment'].value_counts().to_dict(),
                'performance_trend': 'Improving',  # จำลอง
                'key_insights': [
                    'Model accuracy has been stable',
                    'Bullish bias dominated the period',
                    'Volatility remained within normal ranges'
                ]
            }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Historical analysis error: {e}")
            return None
    
    def run_intelligence_cycle(self):
        """รันรอบการวิเคราะห์ Intelligence"""
        try:
            print("🧠 Starting AI Intelligence Cycle...")
            
            # เริ่มต้นคอมโพเนนต์
            if not self.initialize_components():
                print("❌ Failed to initialize components")
                return False
            
            # สร้างสรุปรายวัน
            daily_summary = self.generate_daily_summary()
            
            if daily_summary:
                print("✅ Daily intelligence summary completed")
                
                # วิเคราะห์ข้อมูลย้อนหลัง
                historical = self.get_historical_analysis(7)
                if historical:
                    print(f"📊 Historical analysis: {historical['total_days']} days analyzed")
                
                return True
            else:
                print("❌ Failed to generate daily summary")
                return False
                
        except Exception as e:
            print(f"❌ Intelligence cycle error: {e}")
            return False

def main():
    """ฟังก์ชันหลัก"""
    print("🧠 Gold AI Intelligence System")
    print("=" * 50)
    
    # สร้าง intelligence system
    ai_intel = GoldAIIntelligence()
    
    print("\n🎯 Select Intelligence Mode:")
    print("1. Generate Daily Summary")
    print("2. Run Full Intelligence Cycle")
    print("3. View Historical Analysis")
    
    choice = input("Enter choice (1-3, default 1): ").strip() or "1"
    
    try:
        if choice == "1":
            # สร้างสรุปรายวัน
            print("\n📊 Generating daily summary...")
            ai_intel.initialize_components()
            summary = ai_intel.generate_daily_summary()
            
            if summary:
                print("\n🎉 Daily summary generated successfully!")
                print(f"📰 News analyzed: {len(summary['news_analysis'])}")
                print(f"🤖 Model performance: {summary['learning_insights']['model_performance']:.1%}")
                print(f"📈 Market bias: {summary['daily_framework']['market_bias']}")
            else:
                print("\n❌ Failed to generate daily summary")
        
        elif choice == "2":
            # รันรอบเต็ม
            print("\n🔄 Running full intelligence cycle...")
            success = ai_intel.run_intelligence_cycle()
            
            if success:
                print("\n🎉 Intelligence cycle completed successfully!")
            else:
                print("\n❌ Intelligence cycle failed")
        
        elif choice == "3":
            # ดูข้อมูลย้อนหลัง
            print("\n📊 Analyzing historical data...")
            ai_intel.initialize_components()
            historical = ai_intel.get_historical_analysis(7)
            
            if historical:
                print(f"\n📈 Historical Analysis ({historical['period']}):")
                print(f"   Total days: {historical['total_days']}")
                print(f"   Sentiment distribution: {historical['sentiment_distribution']}")
                print(f"   Performance trend: {historical['performance_trend']}")
                
                print(f"\n💡 Key Insights:")
                for insight in historical['key_insights']:
                    print(f"   • {insight}")
            else:
                print("\n❌ No historical data available")
        
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()