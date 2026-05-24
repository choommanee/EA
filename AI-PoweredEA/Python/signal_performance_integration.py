"""
Signal Performance Integration
Integrates performance monitoring with the existing signal system
"""

import sys
import os
sys.path.append('Python')

import logging
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import json
import threading
import time
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from performance_monitor import PerformanceMonitor, PerformanceRecord, MarketRegime


@dataclass
class SignalRecord:
    """Signal record from existing system"""
    id: int
    timestamp: datetime
    symbol: str
    signal_type: str
    confidence: float
    entry_price: float
    exit_price: Optional[float]
    profit_loss: Optional[float]
    is_closed: bool
    model_version: str
    metadata: Dict[str, Any]


class SignalPerformanceIntegration:
    """Integrates performance monitoring with existing signal system"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # Initialize performance monitor
        self.performance_monitor = PerformanceMonitor(db_path)
        
        # Integration settings
        self.sync_interval_minutes = 5
        self.batch_size = 100
        self.last_sync_time = None
        
        # Threading for real-time monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Performance cache
        self.performance_cache = {}
        self.cache_ttl_minutes = 10
        
        self.logger.info("Signal Performance Integration initialized")
    
    def start_real_time_monitoring(self) -> bool:
        """Start real-time performance monitoring"""
        try:
            if self.monitoring_active:
                self.logger.warning("Real-time monitoring already active")
                return True
            
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            self.logger.info("Real-time performance monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting real-time monitoring: {e}")
            return False
    
    def stop_real_time_monitoring(self) -> bool:
        """Stop real-time performance monitoring"""
        try:
            if not self.monitoring_active:
                return True
            
            self.monitoring_active = False
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=10)
            
            self.logger.info("Real-time performance monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping real-time monitoring: {e}")
            return False
    
    def sync_historical_signals(self, days_back: int = 30) -> Dict[str, Any]:
        """Sync historical signals with performance monitoring"""
        try:
            self.logger.info(f"Syncing historical signals for {days_back} days...")
            
            # Get historical signals
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            
            signals = self._get_historical_signals(start_time, end_time)
            
            if not signals:
                return {'synced_signals': 0, 'errors': 0}
            
            synced_count = 0
            error_count = 0
            
            # Process signals in batches
            for i in range(0, len(signals), self.batch_size):
                batch = signals[i:i + self.batch_size]
                
                for signal in batch:
                    try:
                        if signal.is_closed and signal.exit_price is not None:
                            # Convert signal to performance tracking format
                            signal_data = {
                                'signal_type': signal.signal_type,
                                'confidence': signal.confidence,
                                'timestamp': signal.timestamp.isoformat(),
                                'symbol': signal.symbol,
                                'entry_price': signal.entry_price
                            }
                            
                            # Determine if signal was correct
                            is_correct = self._determine_signal_correctness(signal)
                            
                            outcome = {
                                'actual_result': 1.0 if is_correct else 0.0,
                                'predicted_result': signal.confidence,
                                'is_correct': is_correct,
                                'profit_loss': signal.profit_loss or 0.0
                            }
                            
                            # Track with performance monitor
                            success = self.performance_monitor.track_signal_outcome(
                                model_id=f"signal_model_{signal.symbol}",
                                model_version=signal.model_version,
                                signal_data=signal_data,
                                outcome=outcome
                            )
                            
                            if success:
                                synced_count += 1
                            else:
                                error_count += 1
                                
                    except Exception as signal_error:
                        self.logger.warning(f"Error processing signal {signal.id}: {signal_error}")
                        error_count += 1
                
                # Small delay between batches
                time.sleep(0.1)
            
            self.last_sync_time = datetime.now()
            
            result = {
                'synced_signals': synced_count,
                'errors': error_count,
                'total_signals': len(signals),
                'sync_time': self.last_sync_time
            }
            
            self.logger.info(f"Historical sync completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error syncing historical signals: {e}")
            return {'synced_signals': 0, 'errors': 1, 'error': str(e)}
    
    def get_real_time_performance_metrics(self, model_id: str = None) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        try:
            # Check cache first
            cache_key = f"performance_{model_id or 'all'}"
            if cache_key in self.performance_cache:
                cached_data, cache_time = self.performance_cache[cache_key]
                if (datetime.now() - cache_time).total_seconds() < self.cache_ttl_minutes * 60:
                    return cached_data
            
            metrics = {}
            
            if model_id:
                # Get metrics for specific model
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=24)
                
                model_metrics = self.performance_monitor.calculate_model_performance(
                    model_id, start_time, end_time
                )
                metrics[model_id] = model_metrics
                
            else:
                # Get metrics for all active models
                active_models = self._get_active_models()
                
                for model in active_models:
                    end_time = datetime.now()
                    start_time = end_time - timedelta(hours=24)
                    
                    model_metrics = self.performance_monitor.calculate_model_performance(
                        model, start_time, end_time
                    )
                    metrics[model] = model_metrics
            
            # Add system-wide metrics
            metrics['system_summary'] = self._calculate_system_metrics(metrics)
            
            # Cache results
            self.performance_cache[cache_key] = (metrics, datetime.now())
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting real-time performance metrics: {e}")
            return {}
    
    def detect_performance_issues(self) -> List[Dict[str, Any]]:
        """Detect performance issues across all models"""
        try:
            issues = []
            
            # Get all active models
            active_models = self._get_active_models()
            
            for model_id in active_models:
                # Check for performance degradation
                alert = self.performance_monitor.detect_performance_degradation(model_id)
                
                if alert:
                    issues.append({
                        'type': 'performance_degradation',
                        'model_id': model_id,
                        'severity': alert.severity,
                        'message': alert.message,
                        'current_value': alert.current_value,
                        'baseline_value': alert.baseline_value,
                        'degradation_percent': alert.degradation_percent,
                        'timestamp': alert.timestamp
                    })
                
                # Check for low signal volume
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=24)
                
                metrics = self.performance_monitor.calculate_model_performance(
                    model_id, start_time, end_time
                )
                
                signal_count = metrics.get('signal_count', 0)
                if signal_count < 5:  # Less than 5 signals in 24 hours
                    issues.append({
                        'type': 'low_signal_volume',
                        'model_id': model_id,
                        'severity': 'MEDIUM',
                        'message': f"Low signal volume: only {signal_count} signals in 24 hours",
                        'signal_count': signal_count,
                        'timestamp': datetime.now()
                    })
                
                # Check for poor accuracy
                accuracy = metrics.get('accuracy', 0.0)
                if accuracy < 0.5 and signal_count > 10:  # Poor accuracy with sufficient signals
                    issues.append({
                        'type': 'poor_accuracy',
                        'model_id': model_id,
                        'severity': 'HIGH',
                        'message': f"Poor accuracy: {accuracy:.1%} with {signal_count} signals",
                        'accuracy': accuracy,
                        'signal_count': signal_count,
                        'timestamp': datetime.now()
                    })
            
            return issues
            
        except Exception as e:
            self.logger.error(f"Error detecting performance issues: {e}")
            return []
    
    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for performance dashboard"""
        try:
            dashboard_data = {
                'timestamp': datetime.now(),
                'real_time_metrics': self.get_real_time_performance_metrics(),
                'performance_issues': self.detect_performance_issues(),
                'system_health': self._get_system_health(),
                'recent_signals': self._get_recent_signals(limit=50),
                'performance_trends': self._get_performance_trends()
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return {'error': str(e)}
    
    def _monitoring_loop(self):
        """Main monitoring loop for real-time performance tracking"""
        try:
            while self.monitoring_active:
                try:
                    # Sync new signals
                    self._sync_new_signals()
                    
                    # Check for performance issues
                    issues = self.detect_performance_issues()
                    
                    if issues:
                        for issue in issues:
                            self.logger.warning(f"Performance issue detected: {issue['message']}")
                    
                    # Clear old cache entries
                    self._cleanup_cache()
                    
                    # Wait for next sync interval
                    time.sleep(self.sync_interval_minutes * 60)
                    
                except Exception as loop_error:
                    self.logger.error(f"Error in monitoring loop: {loop_error}")
                    time.sleep(60)  # Wait 1 minute before retrying
                    
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}")
    
    def _sync_new_signals(self):
        """Sync new signals since last sync"""
        try:
            if self.last_sync_time is None:
                # First sync - get signals from last hour
                start_time = datetime.now() - timedelta(hours=1)
            else:
                start_time = self.last_sync_time
            
            end_time = datetime.now()
            
            # Get new signals
            new_signals = self._get_historical_signals(start_time, end_time)
            
            if new_signals:
                synced_count = 0
                
                for signal in new_signals:
                    if signal.is_closed and signal.exit_price is not None:
                        try:
                            signal_data = {
                                'signal_type': signal.signal_type,
                                'confidence': signal.confidence,
                                'timestamp': signal.timestamp.isoformat(),
                                'symbol': signal.symbol,
                                'entry_price': signal.entry_price
                            }
                            
                            is_correct = self._determine_signal_correctness(signal)
                            
                            outcome = {
                                'actual_result': 1.0 if is_correct else 0.0,
                                'predicted_result': signal.confidence,
                                'is_correct': is_correct,
                                'profit_loss': signal.profit_loss or 0.0
                            }
                            
                            success = self.performance_monitor.track_signal_outcome(
                                model_id=f"signal_model_{signal.symbol}",
                                model_version=signal.model_version,
                                signal_data=signal_data,
                                outcome=outcome
                            )
                            
                            if success:
                                synced_count += 1
                                
                        except Exception as signal_error:
                            self.logger.warning(f"Error syncing signal {signal.id}: {signal_error}")
                
                if synced_count > 0:
                    self.logger.info(f"Synced {synced_count} new signals")
            
            self.last_sync_time = end_time
            
        except Exception as e:
            self.logger.error(f"Error syncing new signals: {e}")
    
    def _get_historical_signals(self, start_time: datetime, end_time: datetime) -> List[SignalRecord]:
        """Get historical signals from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # This query assumes a signals table exists in the existing system
            # Adjust table name and columns as needed for your specific database schema
            query = """
                SELECT id, timestamp, symbol, signal_type, confidence, 
                       entry_price, exit_price, profit_loss, is_closed, 
                       model_version, metadata
                FROM signals 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """
            
            try:
                cursor.execute(query, (start_time.isoformat(), end_time.isoformat()))
                rows = cursor.fetchall()
                
                signals = []
                for row in rows:
                    try:
                        metadata = json.loads(row[10]) if row[10] else {}
                        
                        signal = SignalRecord(
                            id=row[0],
                            timestamp=datetime.fromisoformat(row[1]),
                            symbol=row[2],
                            signal_type=row[3],
                            confidence=row[4],
                            entry_price=row[5],
                            exit_price=row[6],
                            profit_loss=row[7],
                            is_closed=bool(row[8]),
                            model_version=row[9] or "v1.0",
                            metadata=metadata
                        )
                        signals.append(signal)
                        
                    except Exception as row_error:
                        self.logger.warning(f"Error parsing signal row: {row_error}")
                        continue
                
                conn.close()
                return signals
                
            except sqlite3.OperationalError:
                # Table doesn't exist yet - return empty list
                conn.close()
                return []
            
        except Exception as e:
            self.logger.error(f"Error getting historical signals: {e}")
            return []
    
    def _determine_signal_correctness(self, signal: SignalRecord) -> bool:
        """Determine if a signal was correct based on profit/loss"""
        try:
            if signal.profit_loss is None:
                return False
            
            # Simple correctness: positive profit = correct signal
            return signal.profit_loss > 0
            
        except Exception as e:
            self.logger.error(f"Error determining signal correctness: {e}")
            return False
    
    def _get_active_models(self) -> List[str]:
        """Get list of active model IDs"""
        try:
            # Get unique model IDs from recent performance records
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get models that have been active in the last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            query = """
                SELECT DISTINCT model_id 
                FROM performance_records 
                WHERE timestamp > ?
            """
            
            cursor.execute(query, (cutoff_time.isoformat(),))
            rows = cursor.fetchall()
            
            models = [row[0] for row in rows]
            conn.close()
            
            return models
            
        except Exception as e:
            self.logger.error(f"Error getting active models: {e}")
            return []
    
    def _calculate_system_metrics(self, model_metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Calculate system-wide performance metrics"""
        try:
            if not model_metrics:
                return {}
            
            total_signals = 0
            total_correct = 0
            total_profit = 0.0
            model_count = 0
            
            for model_id, metrics in model_metrics.items():
                if model_id == 'system_summary':
                    continue
                
                signal_count = metrics.get('signal_count', 0)
                accuracy = metrics.get('accuracy', 0.0)
                profit_loss = metrics.get('total_profit_loss', 0.0)
                
                total_signals += signal_count
                total_correct += int(signal_count * accuracy)
                total_profit += profit_loss
                model_count += 1
            
            system_metrics = {
                'total_models': model_count,
                'total_signals': total_signals,
                'system_accuracy': total_correct / total_signals if total_signals > 0 else 0.0,
                'total_profit_loss': total_profit,
                'avg_signals_per_model': total_signals / model_count if model_count > 0 else 0.0
            }
            
            return system_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating system metrics: {e}")
            return {}
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            health = {
                'status': 'healthy',
                'issues': [],
                'last_sync': self.last_sync_time,
                'monitoring_active': self.monitoring_active
            }
            
            # Check for recent activity
            if self.last_sync_time:
                time_since_sync = (datetime.now() - self.last_sync_time).total_seconds() / 60
                if time_since_sync > self.sync_interval_minutes * 2:
                    health['status'] = 'degraded'
                    health['issues'].append('Sync delay detected')
            
            # Check performance issues
            issues = self.detect_performance_issues()
            critical_issues = [i for i in issues if i['severity'] == 'CRITICAL']
            high_issues = [i for i in issues if i['severity'] == 'HIGH']
            
            if critical_issues:
                health['status'] = 'critical'
                health['issues'].extend([i['message'] for i in critical_issues])
            elif high_issues:
                health['status'] = 'degraded'
                health['issues'].extend([i['message'] for i in high_issues])
            
            return health
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_recent_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent signals for dashboard"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            signals = self._get_historical_signals(start_time, end_time)
            
            # Sort by timestamp (most recent first) and limit
            signals.sort(key=lambda x: x.timestamp, reverse=True)
            recent_signals = signals[:limit]
            
            # Convert to dict format
            signal_dicts = []
            for signal in recent_signals:
                signal_dict = {
                    'id': signal.id,
                    'timestamp': signal.timestamp.isoformat(),
                    'symbol': signal.symbol,
                    'signal_type': signal.signal_type,
                    'confidence': signal.confidence,
                    'profit_loss': signal.profit_loss,
                    'is_closed': signal.is_closed,
                    'is_correct': self._determine_signal_correctness(signal) if signal.is_closed else None
                }
                signal_dicts.append(signal_dict)
            
            return signal_dicts
            
        except Exception as e:
            self.logger.error(f"Error getting recent signals: {e}")
            return []
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trends for dashboard"""
        try:
            trends = {}
            
            active_models = self._get_active_models()
            
            for model_id in active_models[:5]:  # Limit to top 5 models
                model_trends = self.performance_monitor.get_performance_trends(model_id, days=7)
                if model_trends:
                    trends[model_id] = model_trends
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error getting performance trends: {e}")
            return {}
    
    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, (data, cache_time) in self.performance_cache.items():
                if (current_time - cache_time).total_seconds() > self.cache_ttl_minutes * 60:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.performance_cache[key]
                
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize integration
    integration = SignalPerformanceIntegration("Data/test_integration.db")
    
    print("Signal Performance Integration initialized successfully!")
    
    # Test historical sync
    sync_result = integration.sync_historical_signals(days_back=1)
    print(f"Historical sync result: {sync_result}")
    
    # Test real-time metrics
    metrics = integration.get_real_time_performance_metrics()
    print(f"Real-time metrics: {len(metrics)} models")
    
    # Test performance issues detection
    issues = integration.detect_performance_issues()
    print(f"Performance issues detected: {len(issues)}")
    
    print("Signal Performance Integration test completed!")