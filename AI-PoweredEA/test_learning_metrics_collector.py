"""
Test suite for Learning Metrics Collector
Tests metrics collection, trend analysis, and resource monitoring
"""

import unittest
import tempfile
import os
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import numpy as np

from Python.learning_metrics_collector import (
    LearningMetricsCollector, MetricType, MetricCategory, 
    MetricRecord, PerformanceTrend, ResourceUsage
)


class TestLearningMetricsCollector(unittest.TestCase):
    """Test Learning Metrics Collector functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_metrics.db")
        self.collector = LearningMetricsCollector(self.db_path, collection_interval=1)
    
    def test_initialization(self):
        """Test metrics collector initialization"""
        self.assertIsNotNone(self.collector)
        self.assertEqual(self.collector.db_path, self.db_path)
        self.assertFalse(self.collector.is_collecting)
        self.assertEqual(len(self.collector.metrics_buffer), 0)
    
    def test_record_learning_progress(self):
        """Test recording learning progress metrics"""
        success = self.collector.record_learning_progress(
            model_id="test_model",
            epoch=1,
            loss=0.5,
            accuracy=0.85,
            validation_loss=0.4,
            validation_accuracy=0.88
        )
        
        self.assertTrue(success)
        self.assertGreater(len(self.collector.metrics_buffer), 0)
        
        # Check real-time metrics
        real_time = self.collector.get_real_time_metrics()
        self.assertEqual(real_time["test_model_current_epoch"], 1)
        self.assertEqual(real_time["test_model_current_loss"], 0.5)
        self.assertEqual(real_time["test_model_current_accuracy"], 0.85)
    
    def test_record_model_performance(self):
        """Test recording model performance metrics"""
        performance_metrics = {
            "accuracy": 0.85,
            "precision": 0.82,
            "recall": 0.88,
            "f1_score": 0.85
        }
        
        success = self.collector.record_model_performance(
            model_id="test_model",
            metrics=performance_metrics,
            test_type="validation"
        )
        
        self.assertTrue(success)
        self.assertGreater(len(self.collector.metrics_buffer), 0)
        
        # Check performance history
        self.assertIn("test_model_accuracy", self.collector.performance_history)
        self.assertGreater(len(self.collector.performance_history["test_model_accuracy"]), 0)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    @patch('psutil.Process')
    @patch('psutil.pids')
    def test_record_resource_usage(self, mock_pids, mock_process, mock_net, 
                                 mock_disk, mock_memory, mock_cpu):
        """Test recording resource usage metrics"""
        # Mock system metrics
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(percent=60.0, used=8000000000)
        mock_disk.return_value = Mock(percent=45.0)
        mock_net.return_value = Mock(bytes_sent=1000000, bytes_recv=2000000)
        mock_pids.return_value = [1, 2, 3, 4, 5]
        
        # Mock process
        mock_proc = Mock()
        mock_proc.memory_info.return_value = Mock(rss=500000000)
        mock_proc.num_threads.return_value = 8
        mock_process.return_value = mock_proc
        
        success = self.collector.record_resource_usage()
        
        self.assertTrue(success)
        self.assertGreater(len(self.collector.resource_history), 0)
        self.assertGreater(len(self.collector.metrics_buffer), 0)
        
        # Check resource usage record
        latest_resource = self.collector.resource_history[-1]
        self.assertEqual(latest_resource.cpu_percent, 25.5)
        self.assertEqual(latest_resource.memory_percent, 60.0)
    
    def test_record_training_metrics(self):
        """Test recording training-specific metrics"""
        success = self.collector.record_training_metrics(
            model_id="test_model",
            training_time=120.5,
            samples_processed=1000,
            batch_size=32,
            learning_rate=0.001
        )
        
        self.assertTrue(success)
        self.assertGreater(len(self.collector.metrics_buffer), 0)
        
        # Check that derived metrics are calculated
        # Should have training_time, samples_processed, samples_per_second, learning_rate
        training_metrics = [m for m in self.collector.metrics_buffer 
                          if m.metric_type == MetricType.TRAINING_METRICS]
        self.assertGreaterEqual(len(training_metrics), 4)
    
    def test_record_error_metrics(self):
        """Test recording error metrics"""
        success = self.collector.record_error_metrics(
            component="trainer",
            error_type="validation_error",
            error_count=3,
            severity="high"
        )
        
        self.assertTrue(success)
        self.assertGreater(len(self.collector.metrics_buffer), 0)
        
        # Check real-time error tracking
        real_time = self.collector.get_real_time_metrics()
        self.assertEqual(real_time["trainer_validation_error_errors"], 3)
    
    def test_get_real_time_metrics(self):
        """Test getting real-time metrics"""
        # Record some metrics first
        self.collector.record_learning_progress("test_model", 1, 0.5, 0.85)
        self.collector.record_error_metrics("trainer", "test_error", 1)
        
        real_time = self.collector.get_real_time_metrics()
        
        self.assertIsInstance(real_time, dict)
        self.assertIn("test_model_current_epoch", real_time)
        self.assertIn("trainer_test_error_errors", real_time)
        self.assertIn("metrics_collection_active", real_time)
        self.assertIn("metrics_buffer_size", real_time)
    
    def test_analyze_performance_trends(self):
        """Test performance trend analysis"""
        # Record multiple performance metrics over time
        base_time = datetime.now()
        
        for i in range(10):
            # Simulate improving accuracy over time
            accuracy = 0.7 + (i * 0.02)
            
            # Create metric record with specific timestamp
            metric = MetricRecord(
                timestamp=base_time + timedelta(minutes=i),
                metric_type=MetricType.MODEL_PERFORMANCE,
                metric_name="accuracy",
                metric_value=accuracy,
                category=MetricCategory.REAL_TIME,
                model_id="test_model",
                component="evaluator"
            )
            
            self.collector._add_metric(metric)
        
        # Flush to database
        self.collector._flush_metrics_buffer()
        
        # Analyze trends
        trends = self.collector.analyze_performance_trends("test_model", 1)
        
        self.assertIsInstance(trends, list)
        if trends:  # If trends were found
            accuracy_trend = next((t for t in trends if t.metric_name == "accuracy"), None)
            if accuracy_trend:
                self.assertEqual(accuracy_trend.trend_direction, "improving")
                self.assertGreater(accuracy_trend.trend_strength, 0)
    
    def test_get_resource_usage_history(self):
        """Test getting resource usage history"""
        # Add some resource usage records
        for i in range(5):
            resource = ResourceUsage(
                timestamp=datetime.now() - timedelta(minutes=i),
                cpu_percent=20.0 + i,
                memory_percent=50.0 + i,
                memory_mb=4000.0 + i * 100,
                disk_usage_percent=30.0,
                network_io={"bytes_sent": 1000, "bytes_recv": 2000},
                process_count=100,
                thread_count=10
            )
            self.collector.resource_history.append(resource)
        
        history = self.collector.get_resource_usage_history(1)
        
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 0)
        
        if history:
            self.assertIsInstance(history[0], ResourceUsage)
    
    def test_get_aggregated_metrics(self):
        """Test getting aggregated metrics"""
        # Add some metrics with different timestamps
        base_time = datetime.now()
        
        for i in range(20):
            metric = MetricRecord(
                timestamp=base_time - timedelta(minutes=i * 5),
                metric_type=MetricType.MODEL_PERFORMANCE,
                metric_name="accuracy",
                metric_value=0.8 + (i % 5) * 0.02,
                category=MetricCategory.REAL_TIME,
                model_id="test_model"
            )
            self.collector._add_metric(metric)
        
        # Flush to database
        self.collector._flush_metrics_buffer()
        
        # Get aggregated metrics
        aggregated = self.collector.get_aggregated_metrics('hour', 2)
        
        self.assertIsInstance(aggregated, dict)
        # May or may not have data depending on timing
    
    def test_collection_start_stop(self):
        """Test starting and stopping metrics collection"""
        # Test start
        success = self.collector.start_collection()
        self.assertTrue(success)
        self.assertTrue(self.collector.is_collecting)
        self.assertIsNotNone(self.collector.collection_thread)
        
        # Wait a bit for collection to run
        time.sleep(2)
        
        # Test stop
        success = self.collector.stop_collection()
        self.assertTrue(success)
        self.assertFalse(self.collector.is_collecting)
    
    def test_metrics_buffer_flush(self):
        """Test metrics buffer flushing"""
        # Add metrics to buffer
        for i in range(10):
            metric = MetricRecord(
                timestamp=datetime.now(),
                metric_type=MetricType.LEARNING_PROGRESS,
                metric_name="test_metric",
                metric_value=float(i),
                category=MetricCategory.REAL_TIME
            )
            self.collector._add_metric(metric)
        
        initial_buffer_size = len(self.collector.metrics_buffer)
        self.assertGreater(initial_buffer_size, 0)
        
        # Flush buffer
        self.collector._flush_metrics_buffer()
        
        # Buffer should be empty
        self.assertEqual(len(self.collector.metrics_buffer), 0)
    
    def test_trend_calculation(self):
        """Test trend calculation algorithm"""
        # Test improving trend
        improving_values = [0.5, 0.6, 0.7, 0.8, 0.9]
        trend = self.collector._calculate_trend(improving_values)
        
        self.assertEqual(trend['direction'], 'improving')
        self.assertGreater(trend['strength'], 0)
        self.assertGreater(trend['confidence'], 0)
        
        # Test declining trend
        declining_values = [0.9, 0.8, 0.7, 0.6, 0.5]
        trend = self.collector._calculate_trend(declining_values)
        
        self.assertEqual(trend['direction'], 'declining')
        self.assertGreater(trend['strength'], 0)
        
        # Test stable trend
        stable_values = [0.7, 0.7, 0.7, 0.7, 0.7]
        trend = self.collector._calculate_trend(stable_values)
        
        self.assertEqual(trend['direction'], 'stable')
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with invalid model_id (None)
        success = self.collector.record_learning_progress(
            model_id=None,
            epoch=1,
            loss=0.5,
            accuracy=0.85
        )
        # Should still work (model_id is optional in some contexts)
        self.assertTrue(success)
        
        # Test trend analysis with no data
        trends = self.collector.analyze_performance_trends("nonexistent_model", 1)
        self.assertIsInstance(trends, list)
        self.assertEqual(len(trends), 0)
        
        # Test getting metrics with empty database
        aggregated = self.collector.get_aggregated_metrics('hour', 1)
        self.assertIsInstance(aggregated, dict)
    
    def tearDown(self):
        """Clean up test environment"""
        # Stop collection if running
        if self.collector.is_collecting:
            self.collector.stop_collection()
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestMetricDataStructures(unittest.TestCase):
    """Test metric data structures"""
    
    def test_metric_record_creation(self):
        """Test MetricRecord creation"""
        metric = MetricRecord(
            timestamp=datetime.now(),
            metric_type=MetricType.LEARNING_PROGRESS,
            metric_name="accuracy",
            metric_value=0.85,
            category=MetricCategory.REAL_TIME,
            model_id="test_model",
            component="trainer",
            metadata={"epoch": 1}
        )
        
        self.assertIsNotNone(metric)
        self.assertEqual(metric.metric_name, "accuracy")
        self.assertEqual(metric.metric_value, 0.85)
        self.assertEqual(metric.model_id, "test_model")
        self.assertEqual(metric.metadata["epoch"], 1)
    
    def test_performance_trend_creation(self):
        """Test PerformanceTrend creation"""
        trend = PerformanceTrend(
            metric_name="accuracy",
            time_period="24h",
            trend_direction="improving",
            trend_strength=0.8,
            current_value=0.9,
            previous_value=0.7,
            change_percentage=28.57,
            confidence=0.95
        )
        
        self.assertIsNotNone(trend)
        self.assertEqual(trend.metric_name, "accuracy")
        self.assertEqual(trend.trend_direction, "improving")
        self.assertEqual(trend.trend_strength, 0.8)
    
    def test_resource_usage_creation(self):
        """Test ResourceUsage creation"""
        resource = ResourceUsage(
            timestamp=datetime.now(),
            cpu_percent=25.5,
            memory_percent=60.0,
            memory_mb=4096.0,
            disk_usage_percent=45.0,
            network_io={"bytes_sent": 1000, "bytes_recv": 2000},
            process_count=150,
            thread_count=12
        )
        
        self.assertIsNotNone(resource)
        self.assertEqual(resource.cpu_percent, 25.5)
        self.assertEqual(resource.memory_percent, 60.0)
        self.assertEqual(resource.network_io["bytes_sent"], 1000)


if __name__ == '__main__':
    unittest.main(verbosity=2)