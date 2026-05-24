"""
Learning Metrics Collector for AI Continuous Learning System
Collects and tracks real-time learning progress, performance trends, and resource usage
"""

import sys
import os
sys.path.append('Python')

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
import json
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')


class MetricType(Enum):
    """Types of metrics collected"""
    LEARNING_PROGRESS = "learning_progress"
    MODEL_PERFORMANCE = "model_performance"
    RESOURCE_USAGE = "resource_usage"
    TRAINING_METRICS = "training_metrics"
    SYSTEM_HEALTH = "system_health"
    ERROR_METRICS = "error_metrics"


class MetricCategory(Enum):
    """Categories for metric organization"""
    REAL_TIME = "real_time"
    HISTORICAL = "historical"
    AGGREGATED = "aggregated"
    TREND = "trend"


@dataclass
class MetricRecord:
    """Individual metric record"""
    timestamp: datetime
    metric_type: MetricType
    metric_name: str
    metric_value: float
    category: MetricCategory
    model_id: Optional[str] = None
    component: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTrend:
    """Performance trend analysis"""
    metric_name: str
    time_period: str
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0.0 to 1.0
    current_value: float
    previous_value: float
    change_percentage: float
    confidence: float


@dataclass
class ResourceUsage:
    """System resource usage metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    thread_count: int


class LearningMetricsCollector:
    """Collects and manages learning system metrics"""
    
    def __init__(self, db_path: str = "Data/learning_metrics.db", 
                 collection_interval: int = 30):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.collection_interval = collection_interval
        
        # Metric storage
        self.metrics_buffer = deque(maxlen=1000)
        self.real_time_metrics = {}
        self.trend_cache = {}
        
        # Collection control
        self.is_collecting = False
        self.collection_thread = None
        self.last_collection_time = None
        
        # Performance tracking
        self.performance_history = defaultdict(list)
        self.resource_history = deque(maxlen=100)
        
        # Aggregation settings
        self.aggregation_intervals = {
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        # Initialize database
        self._init_metrics_database()
        
        self.logger.info("Learning Metrics Collector initialized")
    
    def start_collection(self) -> bool:
        """Start automatic metrics collection"""
        try:
            if self.is_collecting:
                self.logger.warning("Metrics collection already running")
                return True
            
            self.is_collecting = True
            self.collection_thread = threading.Thread(
                target=self._collection_loop,
                daemon=True
            )
            self.collection_thread.start()
            
            self.logger.info("Started metrics collection")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting metrics collection: {e}")
            return False
    
    def stop_collection(self) -> bool:
        """Stop automatic metrics collection"""
        try:
            self.is_collecting = False
            
            if self.collection_thread and self.collection_thread.is_alive():
                self.collection_thread.join(timeout=5.0)
            
            # Flush remaining metrics
            self._flush_metrics_buffer()
            
            self.logger.info("Stopped metrics collection")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping metrics collection: {e}")
            return False
    
    def record_learning_progress(self, model_id: str, epoch: int, 
                               loss: float, accuracy: float, 
                               validation_loss: Optional[float] = None,
                               validation_accuracy: Optional[float] = None) -> bool:
        """Record learning progress metrics"""
        try:
            timestamp = datetime.now()
            
            # Record training metrics
            metrics = [
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.LEARNING_PROGRESS,
                    metric_name="training_loss",
                    metric_value=loss,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="trainer",
                    metadata={"epoch": epoch}
                ),
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.LEARNING_PROGRESS,
                    metric_name="training_accuracy",
                    metric_value=accuracy,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="trainer",
                    metadata={"epoch": epoch}
                )
            ]
            
            # Add validation metrics if provided
            if validation_loss is not None:
                metrics.append(MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.LEARNING_PROGRESS,
                    metric_name="validation_loss",
                    metric_value=validation_loss,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="trainer",
                    metadata={"epoch": epoch}
                ))
            
            if validation_accuracy is not None:
                metrics.append(MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.LEARNING_PROGRESS,
                    metric_name="validation_accuracy",
                    metric_value=validation_accuracy,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="trainer",
                    metadata={"epoch": epoch}
                ))
            
            # Store metrics
            for metric in metrics:
                self._add_metric(metric)
            
            # Update real-time tracking
            self.real_time_metrics[f"{model_id}_current_epoch"] = epoch
            self.real_time_metrics[f"{model_id}_current_loss"] = loss
            self.real_time_metrics[f"{model_id}_current_accuracy"] = accuracy
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording learning progress: {e}")
            return False
    
    def record_model_performance(self, model_id: str, metrics: Dict[str, float],
                               test_type: str = "evaluation") -> bool:
        """Record model performance metrics"""
        try:
            timestamp = datetime.now()
            
            for metric_name, metric_value in metrics.items():
                metric_record = MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.MODEL_PERFORMANCE,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="evaluator",
                    metadata={"test_type": test_type}
                )
                
                self._add_metric(metric_record)
                
                # Update performance history
                self.performance_history[f"{model_id}_{metric_name}"].append({
                    'timestamp': timestamp,
                    'value': metric_value
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording model performance: {e}")
            return False
    
    def record_resource_usage(self) -> bool:
        """Record current system resource usage"""
        try:
            timestamp = datetime.now()
            
            if not PSUTIL_AVAILABLE:
                # Create dummy resource usage when psutil is not available
                resource_usage = ResourceUsage(
                    timestamp=timestamp,
                    cpu_percent=0.0,
                    memory_percent=0.0,
                    memory_mb=0.0,
                    disk_usage_percent=0.0,
                    network_io={'bytes_sent': 0, 'bytes_recv': 0},
                    process_count=0,
                    thread_count=0
                )
                
                # Store in history
                self.resource_history.append(resource_usage)
                
                # Create minimal metric records
                resource_metrics = [
                    MetricRecord(
                        timestamp=timestamp,
                        metric_type=MetricType.RESOURCE_USAGE,
                        metric_name="cpu_percent",
                        metric_value=0.0,
                        category=MetricCategory.REAL_TIME,
                        component="system",
                        metadata={"psutil_available": False}
                    )
                ]
                
                # Store metrics
                for metric in resource_metrics:
                    self._add_metric(metric)
                
                return True
            
            # Get system metrics using psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)  # Shorter interval for testing
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Get process information
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # Create resource usage record
            resource_usage = ResourceUsage(
                timestamp=timestamp,
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_mb=memory.used / 1024 / 1024,
                disk_usage_percent=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                process_count=len(psutil.pids()),
                thread_count=process.num_threads()
            )
            
            # Store in history
            self.resource_history.append(resource_usage)
            
            # Create metric records
            resource_metrics = [
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.RESOURCE_USAGE,
                    metric_name="cpu_percent",
                    metric_value=cpu_percent,
                    category=MetricCategory.REAL_TIME,
                    component="system"
                ),
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.RESOURCE_USAGE,
                    metric_name="memory_percent",
                    metric_value=memory.percent,
                    category=MetricCategory.REAL_TIME,
                    component="system"
                ),
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.RESOURCE_USAGE,
                    metric_name="memory_mb",
                    metric_value=memory.used / 1024 / 1024,
                    category=MetricCategory.REAL_TIME,
                    component="system"
                ),
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.RESOURCE_USAGE,
                    metric_name="process_memory_mb",
                    metric_value=process_memory.rss / 1024 / 1024,
                    category=MetricCategory.REAL_TIME,
                    component="process"
                )
            ]
            
            # Store metrics
            for metric in resource_metrics:
                self._add_metric(metric)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording resource usage: {e}")
            return False
    
    def record_training_metrics(self, model_id: str, training_time: float,
                              samples_processed: int, batch_size: int,
                              learning_rate: float) -> bool:
        """Record training-specific metrics"""
        try:
            timestamp = datetime.now()
            
            # Calculate derived metrics
            samples_per_second = samples_processed / training_time if training_time > 0 else 0
            batches_processed = samples_processed // batch_size if batch_size > 0 else 0
            
            training_metrics = [
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.TRAINING_METRICS,
                    metric_name="training_time_seconds",
                    metric_value=training_time,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="trainer"
                ),
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.TRAINING_METRICS,
                    metric_name="samples_processed",
                    metric_value=samples_processed,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="trainer"
                ),
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.TRAINING_METRICS,
                    metric_name="samples_per_second",
                    metric_value=samples_per_second,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="trainer"
                ),
                MetricRecord(
                    timestamp=timestamp,
                    metric_type=MetricType.TRAINING_METRICS,
                    metric_name="learning_rate",
                    metric_value=learning_rate,
                    category=MetricCategory.REAL_TIME,
                    model_id=model_id,
                    component="trainer"
                )
            ]
            
            # Store metrics
            for metric in training_metrics:
                self._add_metric(metric)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording training metrics: {e}")
            return False
    
    def record_error_metrics(self, component: str, error_type: str,
                           error_count: int = 1, severity: str = "medium") -> bool:
        """Record error and system health metrics"""
        try:
            timestamp = datetime.now()
            
            error_metric = MetricRecord(
                timestamp=timestamp,
                metric_type=MetricType.ERROR_METRICS,
                metric_name=f"{error_type}_count",
                metric_value=error_count,
                category=MetricCategory.REAL_TIME,
                component=component,
                metadata={
                    "error_type": error_type,
                    "severity": severity
                }
            )
            
            self._add_metric(error_metric)
            
            # Update real-time error tracking
            error_key = f"{component}_{error_type}_errors"
            current_count = self.real_time_metrics.get(error_key, 0)
            self.real_time_metrics[error_key] = current_count + error_count
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording error metrics: {e}")
            return False
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        try:
            # Add current resource usage
            if self.resource_history:
                latest_resource = self.resource_history[-1]
                self.real_time_metrics.update({
                    'current_cpu_percent': latest_resource.cpu_percent,
                    'current_memory_percent': latest_resource.memory_percent,
                    'current_memory_mb': latest_resource.memory_mb
                })
            
            # Add collection status
            self.real_time_metrics.update({
                'metrics_collection_active': self.is_collecting,
                'last_collection_time': self.last_collection_time.isoformat() if self.last_collection_time else None,
                'metrics_buffer_size': len(self.metrics_buffer)
            })
            
            return dict(self.real_time_metrics)
            
        except Exception as e:
            self.logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    def analyze_performance_trends(self, model_id: str, 
                                 time_window_hours: int = 24) -> List[PerformanceTrend]:
        """Analyze performance trends for a model"""
        try:
            trends = []
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            # Get performance metrics for the time window
            metrics = self._get_metrics_by_time_range(
                start_time, end_time, 
                metric_type=MetricType.MODEL_PERFORMANCE,
                model_id=model_id
            )
            
            # Group metrics by name
            metric_groups = defaultdict(list)
            for metric in metrics:
                metric_groups[metric.metric_name].append(metric)
            
            # Analyze trends for each metric
            for metric_name, metric_list in metric_groups.items():
                if len(metric_list) < 2:
                    continue
                
                # Sort by timestamp
                metric_list.sort(key=lambda x: x.timestamp)
                
                # Calculate trend
                values = [m.metric_value for m in metric_list]
                trend = self._calculate_trend(values)
                
                current_value = values[-1]
                previous_value = values[0]
                change_percentage = ((current_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
                
                performance_trend = PerformanceTrend(
                    metric_name=metric_name,
                    time_period=f"{time_window_hours}h",
                    trend_direction=trend['direction'],
                    trend_strength=trend['strength'],
                    current_value=current_value,
                    previous_value=previous_value,
                    change_percentage=change_percentage,
                    confidence=trend['confidence']
                )
                
                trends.append(performance_trend)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance trends: {e}")
            return []
    
    def get_resource_usage_history(self, hours: int = 24) -> List[ResourceUsage]:
        """Get resource usage history"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter resource history by time
            filtered_history = [
                resource for resource in self.resource_history
                if resource.timestamp >= cutoff_time
            ]
            
            return filtered_history
            
        except Exception as e:
            self.logger.error(f"Error getting resource usage history: {e}")
            return []
    
    def get_aggregated_metrics(self, interval: str = 'hour', 
                             hours_back: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """Get aggregated metrics for specified interval"""
        try:
            if interval not in self.aggregation_intervals:
                raise ValueError(f"Invalid interval: {interval}")
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Get all metrics in time range
            metrics = self._get_metrics_by_time_range(start_time, end_time)
            
            # Group by interval and metric name
            interval_seconds = self.aggregation_intervals[interval]
            aggregated = defaultdict(lambda: defaultdict(list))
            
            for metric in metrics:
                # Calculate interval bucket
                timestamp_seconds = metric.timestamp.timestamp()
                interval_bucket = int(timestamp_seconds // interval_seconds) * interval_seconds
                bucket_time = datetime.fromtimestamp(interval_bucket)
                
                aggregated[metric.metric_name][bucket_time].append(metric.metric_value)
            
            # Calculate aggregations
            result = {}
            for metric_name, time_buckets in aggregated.items():
                metric_data = []
                for bucket_time, values in sorted(time_buckets.items()):
                    metric_data.append({
                        'timestamp': bucket_time.isoformat(),
                        'count': len(values),
                        'mean': np.mean(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'std': np.std(values)
                    })
                result[metric_name] = metric_data
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting aggregated metrics: {e}")
            return {}
    
    def _collection_loop(self):
        """Main collection loop running in background thread"""
        while self.is_collecting:
            try:
                # Record resource usage
                self.record_resource_usage()
                
                # Flush metrics buffer periodically
                if len(self.metrics_buffer) > 100:
                    self._flush_metrics_buffer()
                
                self.last_collection_time = datetime.now()
                
                # Sleep for collection interval
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                time.sleep(self.collection_interval)
    
    def _add_metric(self, metric: MetricRecord):
        """Add metric to buffer"""
        self.metrics_buffer.append(metric)
        
        # Auto-flush if buffer is getting full
        if len(self.metrics_buffer) >= 500:
            self._flush_metrics_buffer()
    
    def _flush_metrics_buffer(self):
        """Flush metrics buffer to database"""
        try:
            if not self.metrics_buffer:
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare batch insert
            metrics_to_insert = []
            while self.metrics_buffer:
                metric = self.metrics_buffer.popleft()
                metrics_to_insert.append((
                    metric.timestamp.isoformat(),
                    metric.metric_type.value,
                    metric.metric_name,
                    metric.metric_value,
                    metric.category.value,
                    metric.model_id,
                    metric.component,
                    json.dumps(metric.metadata)
                ))
            
            # Batch insert
            cursor.executemany("""
                INSERT INTO learning_metrics 
                (timestamp, metric_type, metric_name, metric_value, category, 
                 model_id, component, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, metrics_to_insert)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error flushing metrics buffer: {e}")
    
    def _get_metrics_by_time_range(self, start_time: datetime, end_time: datetime,
                                 metric_type: Optional[MetricType] = None,
                                 model_id: Optional[str] = None) -> List[MetricRecord]:
        """Get metrics from database by time range"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT timestamp, metric_type, metric_name, metric_value, 
                       category, model_id, component, metadata
                FROM learning_metrics 
                WHERE timestamp BETWEEN ? AND ?
            """
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type.value)
            
            if model_id:
                query += " AND model_id = ?"
                params.append(model_id)
            
            query += " ORDER BY timestamp"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            metrics = []
            for row in rows:
                try:
                    metric = MetricRecord(
                        timestamp=datetime.fromisoformat(row[0]),
                        metric_type=MetricType(row[1]),
                        metric_name=row[2],
                        metric_value=row[3],
                        category=MetricCategory(row[4]),
                        model_id=row[5],
                        component=row[6],
                        metadata=json.loads(row[7]) if row[7] else {}
                    )
                    metrics.append(metric)
                except Exception as parse_error:
                    self.logger.warning(f"Error parsing metric record: {parse_error}")
                    continue
            
            conn.close()
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting metrics by time range: {e}")
            return []
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend direction and strength"""
        try:
            if len(values) < 2:
                return {'direction': 'stable', 'strength': 0.0, 'confidence': 0.0}
            
            # Simple linear regression for trend
            x = np.arange(len(values))
            y = np.array(values)
            
            # Calculate slope
            slope = np.polyfit(x, y, 1)[0]
            
            # Determine direction
            if abs(slope) < 0.001:
                direction = 'stable'
            elif slope > 0:
                direction = 'improving'
            else:
                direction = 'declining'
            
            # Calculate strength (normalized slope)
            value_range = max(values) - min(values)
            strength = min(abs(slope) / (value_range / len(values)), 1.0) if value_range > 0 else 0.0
            
            # Calculate confidence based on consistency
            differences = np.diff(values)
            sign_changes = sum(1 for i in range(len(differences)-1) 
                             if differences[i] * differences[i+1] < 0)
            confidence = max(0.0, 1.0 - (sign_changes / len(differences)))
            
            return {
                'direction': direction,
                'strength': strength,
                'confidence': confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trend: {e}")
            return {'direction': 'stable', 'strength': 0.0, 'confidence': 0.0}
    
    def _init_metrics_database(self):
        """Initialize metrics database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Learning metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    category TEXT NOT NULL,
                    model_id TEXT,
                    component TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON learning_metrics(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_type_model 
                ON learning_metrics(metric_type, model_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_name_time 
                ON learning_metrics(metric_name, timestamp)
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing metrics database: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize metrics collector
    collector = LearningMetricsCollector("Data/test_metrics.db")
    
    print("Learning Metrics Collector initialized successfully!")
    
    # Start collection
    collector.start_collection()
    
    # Test metric recording
    collector.record_learning_progress("test_model", 1, 0.5, 0.85, 0.4, 0.88)
    collector.record_model_performance("test_model", {"accuracy": 0.85, "precision": 0.82})
    collector.record_training_metrics("test_model", 120.5, 1000, 32, 0.001)
    
    # Wait a bit for collection
    time.sleep(2)
    
    # Get real-time metrics
    real_time = collector.get_real_time_metrics()
    print(f"Real-time metrics: {len(real_time)} items")
    
    # Analyze trends
    trends = collector.analyze_performance_trends("test_model", 1)
    print(f"Performance trends: {len(trends)} trends found")
    
    # Stop collection
    collector.stop_collection()
    
    print("Learning Metrics Collector test completed!")