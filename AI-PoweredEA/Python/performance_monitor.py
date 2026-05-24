"""
Performance Monitor for AI Continuous Learning System
Monitors model performance and detects degradation in real-time
"""

import sys
import os
sys.path.append('Python')

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import sqlite3
import json
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')


class PerformanceMetric(Enum):
    """Performance metrics for monitoring"""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ROC_AUC = "roc_auc"
    PROFIT_LOSS = "profit_loss"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNKNOWN = "unknown"


@dataclass
class PerformanceRecord:
    """Performance record for tracking"""
    timestamp: datetime
    model_id: str
    model_version: str
    metric_type: PerformanceMetric
    metric_value: float
    signal_count: int
    correct_signals: int
    market_regime: MarketRegime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DegradationAlert:
    """Performance degradation alert"""
    timestamp: datetime
    model_id: str
    metric_type: PerformanceMetric
    current_value: float
    baseline_value: float
    degradation_percent: float
    severity: str
    message: str


class PerformanceMonitor:
    """Monitors model performance and detects degradation"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # Performance tracking
        self.performance_records = []
        self.baseline_performance = {}
        self.current_performance = {}
        
        # Degradation detection settings
        self.degradation_threshold = 0.1  # 10% degradation threshold
        self.min_samples_for_baseline = 100
        self.performance_window_hours = 24
        
        # Market regime detection
        self.regime_detection_window = 50
        self.volatility_threshold = 0.02
        
        # Initialize database tables
        self._init_performance_tables()
        
        self.logger.info("Performance Monitor initialized")
    
    def track_signal_outcome(self, model_id: str, model_version: str,
                           signal_data: Dict[str, Any], outcome: Dict[str, Any]) -> bool:
        """Track the outcome of a trading signal"""
        try:
            # Extract signal information
            signal_type = signal_data.get('signal_type', 'unknown')
            confidence = signal_data.get('confidence', 0.0)
            timestamp = datetime.fromisoformat(signal_data.get('timestamp', datetime.now().isoformat()))
            
            # Extract outcome information
            actual_result = outcome.get('actual_result', 0.0)
            predicted_result = outcome.get('predicted_result', 0.0)
            is_correct = outcome.get('is_correct', False)
            profit_loss = outcome.get('profit_loss', 0.0)
            
            # Calculate performance metrics
            accuracy = 1.0 if is_correct else 0.0
            
            # Detect current market regime
            market_regime = self._detect_market_regime(timestamp)
            
            # Create performance record
            performance_record = PerformanceRecord(
                timestamp=timestamp,
                model_id=model_id,
                model_version=model_version,
                metric_type=PerformanceMetric.ACCURACY,
                metric_value=accuracy,
                signal_count=1,
                correct_signals=1 if is_correct else 0,
                market_regime=market_regime,
                metadata={
                    'signal_type': signal_type,
                    'confidence': confidence,
                    'actual_result': actual_result,
                    'predicted_result': predicted_result,
                    'profit_loss': profit_loss
                }
            )
            
            # Store performance record
            self.performance_records.append(performance_record)
            self._store_performance_record(performance_record)
            
            # Update current performance
            self._update_current_performance(model_id, performance_record)
            
            # Check for performance degradation
            self._check_performance_degradation(model_id, model_version)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error tracking signal outcome: {e}")
            return False
    
    def calculate_model_performance(self, model_id: str, 
                                  start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Calculate comprehensive performance metrics for a model"""
        try:
            # Get performance records for the time period
            records = self._get_performance_records(model_id, start_time, end_time)
            
            if not records:
                return {'accuracy': 0.0, 'signal_count': 0}
            
            # Calculate basic metrics
            total_signals = len(records)
            correct_signals = sum(1 for r in records if r.metric_value > 0.5)
            accuracy = correct_signals / total_signals if total_signals > 0 else 0.0
            
            # Calculate profit/loss metrics
            total_profit_loss = sum(r.metadata.get('profit_loss', 0.0) for r in records)
            avg_profit_per_signal = total_profit_loss / total_signals if total_signals > 0 else 0.0
            
            # Calculate confidence-weighted accuracy
            confidence_weighted_accuracy = 0.0
            total_confidence = 0.0
            
            for record in records:
                confidence = record.metadata.get('confidence', 1.0)
                accuracy_score = record.metric_value
                confidence_weighted_accuracy += confidence * accuracy_score
                total_confidence += confidence
            
            if total_confidence > 0:
                confidence_weighted_accuracy /= total_confidence
            
            # Calculate regime-specific performance
            regime_performance = {}
            for regime in MarketRegime:
                regime_records = [r for r in records if r.market_regime == regime]
                if regime_records:
                    regime_accuracy = sum(r.metric_value for r in regime_records) / len(regime_records)
                    regime_performance[regime.value] = regime_accuracy
            
            # Calculate Sharpe ratio (simplified)
            if len(records) > 1:
                profit_losses = [r.metadata.get('profit_loss', 0.0) for r in records]
                returns = np.array(profit_losses)
                sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0.0
            else:
                sharpe_ratio = 0.0
            
            performance_metrics = {
                'accuracy': accuracy,
                'confidence_weighted_accuracy': confidence_weighted_accuracy,
                'signal_count': total_signals,
                'correct_signals': correct_signals,
                'total_profit_loss': total_profit_loss,
                'avg_profit_per_signal': avg_profit_per_signal,
                'sharpe_ratio': sharpe_ratio,
                'regime_performance': regime_performance
            }
            
            return performance_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating model performance: {e}")
            return {'accuracy': 0.0, 'signal_count': 0}
    
    def detect_performance_degradation(self, model_id: str, 
                                     threshold: float = None) -> Optional[DegradationAlert]:
        """Detect if model performance has degraded"""
        try:
            if threshold is None:
                threshold = self.degradation_threshold
            
            # Get baseline performance
            baseline = self._get_baseline_performance(model_id)
            if not baseline:
                return None
            
            # Get current performance
            current = self._get_current_performance(model_id)
            if not current:
                return None
            
            # Check for degradation
            baseline_accuracy = baseline.get('accuracy', 0.0)
            current_accuracy = current.get('accuracy', 0.0)
            
            if baseline_accuracy > 0:
                degradation_percent = (baseline_accuracy - current_accuracy) / baseline_accuracy
                
                if degradation_percent > threshold:
                    # Determine severity
                    if degradation_percent > 0.3:
                        severity = "CRITICAL"
                    elif degradation_percent > 0.2:
                        severity = "HIGH"
                    elif degradation_percent > 0.1:
                        severity = "MEDIUM"
                    else:
                        severity = "LOW"
                    
                    alert = DegradationAlert(
                        timestamp=datetime.now(),
                        model_id=model_id,
                        metric_type=PerformanceMetric.ACCURACY,
                        current_value=current_accuracy,
                        baseline_value=baseline_accuracy,
                        degradation_percent=degradation_percent,
                        severity=severity,
                        message=f"Model {model_id} performance degraded by {degradation_percent:.1%}"
                    )
                    
                    return alert
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting performance degradation: {e}")
            return None
    
    def get_performance_trends(self, model_id: str, 
                             days: int = 7) -> Dict[str, List[float]]:
        """Get performance trends over time"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # Get performance records
            records = self._get_performance_records(model_id, start_time, end_time)
            
            if not records:
                return {}
            
            # Group by day
            daily_performance = {}
            for record in records:
                day_key = record.timestamp.strftime('%Y-%m-%d')
                if day_key not in daily_performance:
                    daily_performance[day_key] = []
                daily_performance[day_key].append(record.metric_value)
            
            # Calculate daily averages
            trends = {
                'dates': [],
                'accuracy': [],
                'signal_count': []
            }
            
            for day in sorted(daily_performance.keys()):
                day_records = daily_performance[day]
                avg_accuracy = sum(day_records) / len(day_records)
                
                trends['dates'].append(day)
                trends['accuracy'].append(avg_accuracy)
                trends['signal_count'].append(len(day_records))
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error getting performance trends: {e}")
            return {}
    
    def get_regime_performance_analysis(self, model_id: str, 
                                      days: int = 30) -> Dict[str, Dict[str, float]]:
        """Analyze performance across different market regimes"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            records = self._get_performance_records(model_id, start_time, end_time)
            
            if not records:
                return {}
            
            # Group by market regime
            regime_analysis = {}
            
            for regime in MarketRegime:
                regime_records = [r for r in records if r.market_regime == regime]
                
                if regime_records:
                    total_signals = len(regime_records)
                    correct_signals = sum(1 for r in regime_records if r.metric_value > 0.5)
                    accuracy = correct_signals / total_signals
                    
                    total_profit = sum(r.metadata.get('profit_loss', 0.0) for r in regime_records)
                    avg_profit = total_profit / total_signals
                    
                    regime_analysis[regime.value] = {
                        'accuracy': accuracy,
                        'signal_count': total_signals,
                        'total_profit_loss': total_profit,
                        'avg_profit_per_signal': avg_profit
                    }
            
            return regime_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing regime performance: {e}")
            return {}
    
    def _detect_market_regime(self, timestamp: datetime) -> MarketRegime:
        """Detect current market regime based on recent price data"""
        try:
            # This is a simplified regime detection
            # In a real implementation, this would analyze price data, volatility, etc.
            
            # For now, return a default regime
            # This should be enhanced with actual market data analysis
            return MarketRegime.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return MarketRegime.UNKNOWN
    
    def _get_performance_records(self, model_id: str, 
                               start_time: datetime, end_time: datetime) -> List[PerformanceRecord]:
        """Get performance records from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT timestamp, model_id, model_version, metric_type, metric_value,
                       signal_count, correct_signals, market_regime, metadata
                FROM performance_records 
                WHERE model_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """
            
            cursor.execute(query, (model_id, start_time.isoformat(), end_time.isoformat()))
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                try:
                    metadata = json.loads(row[8]) if row[8] else {}
                    
                    record = PerformanceRecord(
                        timestamp=datetime.fromisoformat(row[0]),
                        model_id=row[1],
                        model_version=row[2],
                        metric_type=PerformanceMetric(row[3]),
                        metric_value=row[4],
                        signal_count=row[5],
                        correct_signals=row[6],
                        market_regime=MarketRegime(row[7]),
                        metadata=metadata
                    )
                    records.append(record)
                    
                except Exception as record_error:
                    self.logger.warning(f"Error parsing performance record: {record_error}")
                    continue
            
            conn.close()
            return records
            
        except Exception as e:
            self.logger.error(f"Error getting performance records: {e}")
            return []
    
    def _store_performance_record(self, record: PerformanceRecord):
        """Store performance record in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                INSERT INTO performance_records 
                (timestamp, model_id, model_version, metric_type, metric_value,
                 signal_count, correct_signals, market_regime, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                record.timestamp.isoformat(),
                record.model_id,
                record.model_version,
                record.metric_type.value,
                record.metric_value,
                record.signal_count,
                record.correct_signals,
                record.market_regime.value,
                json.dumps(record.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing performance record: {e}")
    
    def _update_current_performance(self, model_id: str, record: PerformanceRecord):
        """Update current performance metrics"""
        try:
            if model_id not in self.current_performance:
                self.current_performance[model_id] = {
                    'accuracy': 0.0,
                    'signal_count': 0,
                    'correct_signals': 0,
                    'last_updated': datetime.now()
                }
            
            current = self.current_performance[model_id]
            
            # Update running averages
            total_signals = current['signal_count'] + record.signal_count
            total_correct = current['correct_signals'] + record.correct_signals
            
            current['accuracy'] = total_correct / total_signals if total_signals > 0 else 0.0
            current['signal_count'] = total_signals
            current['correct_signals'] = total_correct
            current['last_updated'] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error updating current performance: {e}")
    
    def _get_baseline_performance(self, model_id: str) -> Optional[Dict[str, float]]:
        """Get baseline performance for a model"""
        try:
            if model_id in self.baseline_performance:
                return self.baseline_performance[model_id]
            
            # Calculate baseline from historical data
            end_time = datetime.now() - timedelta(days=7)  # Use data from a week ago
            start_time = end_time - timedelta(days=30)     # 30-day baseline period
            
            baseline_metrics = self.calculate_model_performance(model_id, start_time, end_time)
            
            if baseline_metrics.get('signal_count', 0) >= self.min_samples_for_baseline:
                self.baseline_performance[model_id] = baseline_metrics
                return baseline_metrics
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting baseline performance: {e}")
            return None
    
    def _get_current_performance(self, model_id: str) -> Optional[Dict[str, float]]:
        """Get current performance for a model"""
        try:
            if model_id in self.current_performance:
                return self.current_performance[model_id]
            
            # Calculate current performance from recent data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=self.performance_window_hours)
            
            current_metrics = self.calculate_model_performance(model_id, start_time, end_time)
            
            if current_metrics.get('signal_count', 0) > 0:
                return current_metrics
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting current performance: {e}")
            return None
    
    def _check_performance_degradation(self, model_id: str, model_version: str):
        """Check for performance degradation and alert if necessary"""
        try:
            alert = self.detect_performance_degradation(model_id)
            
            if alert:
                self.logger.warning(f"Performance degradation detected: {alert.message}")
                
                # Store degradation alert
                self._store_degradation_alert(alert)
                
                # Here you could trigger notifications or other actions
                
        except Exception as e:
            self.logger.error(f"Error checking performance degradation: {e}")
    
    def _store_degradation_alert(self, alert: DegradationAlert):
        """Store degradation alert in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                INSERT INTO degradation_alerts 
                (timestamp, model_id, metric_type, current_value, baseline_value,
                 degradation_percent, severity, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                alert.timestamp.isoformat(),
                alert.model_id,
                alert.metric_type.value,
                alert.current_value,
                alert.baseline_value,
                alert.degradation_percent,
                alert.severity,
                alert.message
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing degradation alert: {e}")
    
    def _init_performance_tables(self):
        """Initialize database tables for performance monitoring"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Performance records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    signal_count INTEGER NOT NULL,
                    correct_signals INTEGER NOT NULL,
                    market_regime TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Degradation alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS degradation_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    baseline_value REAL NOT NULL,
                    degradation_percent REAL NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_performance_model_time 
                ON performance_records(model_id, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_model_time 
                ON degradation_alerts(model_id, timestamp)
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing performance tables: {e}")
    
    def get_current_performance(self):
        """ดูประสิทธิภาพปัจจุบัน"""
        try:
            # Return basic performance metrics
            if self.current_performance:
                # Get the first model's performance
                first_model = list(self.current_performance.keys())[0]
                return self.current_performance[first_model]
            
            # Return default values if no data
            return {
                'accuracy': 0.0,
                'signal_count': 0,
                'correct_signals': 0,
                'total_profit_loss': 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting current performance: {e}")
            return {
                'accuracy': 0.0,
                'signal_count': 0,
                'correct_signals': 0,
                'total_profit_loss': 0.0
            }
    
    def get_performance_summary(self, days=1):
        """ดูสรุปประสิทธิภาพ"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # Get all models performance
            all_performance = {}
            for model_id in self.current_performance.keys():
                performance = self.calculate_model_performance(model_id, start_time, end_time)
                all_performance[model_id] = performance
            
            # Return combined performance or default
            if all_performance:
                first_model = list(all_performance.keys())[0]
                return all_performance[first_model]
            
            return {
                'accuracy': 0.0,
                'signal_count': 0,
                'total_profit_loss': 0.0,
                'win_rate': 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {
                'accuracy': 0.0,
                'signal_count': 0,
                'total_profit_loss': 0.0,
                'win_rate': 0.0
            }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize performance monitor
    monitor = PerformanceMonitor("Data/test_performance.db")
    
    print("Performance Monitor initialized successfully!")
    
    # Test signal tracking
    signal_data = {
        'signal_type': 'BUY',
        'confidence': 0.85,
        'timestamp': datetime.now().isoformat()
    }
    
    outcome = {
        'actual_result': 1.0,
        'predicted_result': 1.0,
        'is_correct': True,
        'profit_loss': 50.0
    }
    
    success = monitor.track_signal_outcome("test_model", "v1.0", signal_data, outcome)
    print(f"Signal tracking test: {success}")
    
    # Test performance calculation
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=1)
    
    performance = monitor.calculate_model_performance("test_model", start_time, end_time)
    print(f"Performance metrics: {performance}")
    
    print("Performance Monitor test completed!")