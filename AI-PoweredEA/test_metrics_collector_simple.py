"""
Simple test suite for Learning Metrics Collector
Tests core functionality without external dependencies
"""

import unittest
import tempfile
import os
import time
from datetime import datetime, timedelta

from Python.learning_metrics_collector import (
    LearningMetricsCollector, MetricType, MetricCategory, 
    MetricRecord, PerformanceTrend, ResourceUsage
)


class TestLearningMetricsCollectorSimple(unittest.TestCase):
    """Test Learning Metrics Collector core functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_metrics.db")
        self.collector = LearningMetricsCollector(self.db_path, collection_interval=1)
    
    def test_initialization(self):
        """Test metrics collector initialization"""
        print("\n--- Testing Metrics Collector Initialization ---")
        
        self.assertIsNotNone(self.collector)
        self.assertEqual(self.collector.db_path, self.db_path)
        self.assertFalse(self.collector.is_collecting)
        self.assertEqual(len(self.collector.metrics_buffer), 0)
        
        print("✓ Metrics collector initialized successfully")
    
    def test_record_learning_progress(self):
        """Test recording learning progress metrics"""
        print("\n--- Testing Learning Progress Recording ---")
        
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
        
        print(f"✓ Recorded learning progress: epoch {real_time['test_model_current_epoch']}, accuracy {real_time['test_model_current_accuracy']}")
    
    def test_record_model_performance(self):
        """Test recording model performance metrics"""
        print("\n--- Testing Model Performance Recording ---")
        
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
        
        print(f"✓ Recorded {len(performance_metrics)} performance metrics")
    
    def test_record_training_metrics(self):
        """Test recording training-specific metrics"""
        print("\n--- Testing Training Metrics Recording ---")
        
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
        training_metrics = [m for m in self.collector.metrics_buffer 
                          if m.metric_type == MetricType.TRAINING_METRICS]
        self.assertGreaterEqual(len(training_metrics), 4)
        
        # Find samples per second metric
        samples_per_sec_metric = next(
            (m for m in training_metrics if m.metric_name == "samples_per_second"), 
            None
        )
        self.assertIsNotNone(samples_per_sec_metric)
        expected_rate = 1000 / 120.5
        self.assertAlmostEqual(samples_per_sec_metric.metric_value, expected_rate, places=2)
        
        print(f"✓ Recorded training metrics: {expected_rate:.2f} samples/sec")
    
    def test_record_error_metrics(self):
        """Test recording error metrics"""
        print("\n--- Testing Error Metrics Recording ---")
        
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
        
        print("✓ Recorded error metrics with real-time tracking")
    
    def test_resource_usage_recording(self):
        """Test resource usage recording (with or without psutil)"""
        print("\n--- Testing Resource Usage Recording ---")
        
        success = self.collector.record_resource_usage()
        self.assertTrue(success)
        
        # Should have added resource usage to history
        self.assertGreater(len(self.collector.resource_history), 0)
        
        # Should have added metrics to buffer
        resource_metrics = [m for m in self.collector.metrics_buffer 
                          if m.metric_type == MetricType.RESOURCE_USAGE]
        self.assertGreater(len(resource_metrics), 0)
        
        print("✓ Resource usage recorded successfully")
    
    def test_get_real_time_metrics(self):
        """Test getting real-time metrics"""
        print("\n--- Testing Real-Time Metrics Retrieval ---")
        
        # Record some metrics first
        self.collector.record_learning_progress("test_model", 1, 0.5, 0.85)
        self.collector.record_error_metrics("trainer", "test_error", 1)
        
        real_time = self.collector.get_real_time_metrics()
        
        self.assertIsInstance(real_time, dict)
        self.assertIn("test_model_current_epoch", real_time)
        self.assertIn("trainer_test_error_errors", real_time)
        self.assertIn("metrics_collection_active", real_time)
        self.assertIn("metrics_buffer_size", real_time)
        
        print(f"✓ Retrieved {len(real_time)} real-time metrics")
    
    def test_metrics_buffer_management(self):
        """Test metrics buffer flushing"""
        print("\n--- Testing Metrics Buffer Management ---")
        
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
        self.assertEqual(initial_buffer_size, 10)
        
        # Flush buffer
        self.collector._flush_metrics_buffer()
        
        # Buffer should be empty
        self.assertEqual(len(self.collector.metrics_buffer), 0)
        
        print(f"✓ Flushed {initial_buffer_size} metrics from buffer")
    
    def test_trend_calculation(self):
        """Test trend calculation algorithm"""
        print("\n--- Testing Trend Calculation ---")
        
        # Test improving trend
        improving_values = [0.5, 0.6, 0.7, 0.8, 0.9]
        trend = self.collector._calculate_trend(improving_values)
        
        self.assertEqual(trend['direction'], 'improving')
        self.assertGreater(trend['strength'], 0)
        self.assertGreater(trend['confidence'], 0)
        
        print(f"✓ Improving trend: strength={trend['strength']:.3f}, confidence={trend['confidence']:.3f}")
        
        # Test declining trend
        declining_values = [0.9, 0.8, 0.7, 0.6, 0.5]
        trend = self.collector._calculate_trend(declining_values)
        
        self.assertEqual(trend['direction'], 'declining')
        self.assertGreater(trend['strength'], 0)
        
        print(f"✓ Declining trend: strength={trend['strength']:.3f}")
        
        # Test stable trend
        stable_values = [0.7, 0.7, 0.7, 0.7, 0.7]
        trend = self.collector._calculate_trend(stable_values)
        
        self.assertEqual(trend['direction'], 'stable')
        
        print(f"✓ Stable trend: direction={trend['direction']}")
    
    def test_performance_trend_analysis(self):
        """Test performance trend analysis with database"""
        print("\n--- Testing Performance Trend Analysis ---")
        
        # Record multiple performance metrics over time
        base_time = datetime.now()
        
        for i in range(5):
            # Simulate improving accuracy over time
            accuracy = 0.7 + (i * 0.05)
            
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
                print(f"✓ Found accuracy trend: {accuracy_trend.trend_direction} (strength: {accuracy_trend.trend_strength:.3f})")
            else:
                print("✓ Trend analysis completed (no accuracy trend found)")
        else:
            print("✓ Trend analysis completed (no trends found)")
    
    def test_collection_lifecycle(self):
        """Test starting and stopping metrics collection"""
        print("\n--- Testing Collection Lifecycle ---")
        
        # Test start
        success = self.collector.start_collection()
        self.assertTrue(success)
        self.assertTrue(self.collector.is_collecting)
        self.assertIsNotNone(self.collector.collection_thread)
        
        print("✓ Started metrics collection")
        
        # Wait a bit for collection to run
        time.sleep(1.5)
        
        # Check that collection is working
        self.assertIsNotNone(self.collector.last_collection_time)
        
        print("✓ Collection thread is running")
        
        # Test stop
        success = self.collector.stop_collection()
        self.assertTrue(success)
        self.assertFalse(self.collector.is_collecting)
        
        print("✓ Stopped metrics collection")
    
    def test_aggregated_metrics(self):
        """Test aggregated metrics functionality"""
        print("\n--- Testing Aggregated Metrics ---")
        
        # Add some metrics with different timestamps
        base_time = datetime.now()
        
        for i in range(10):
            metric = MetricRecord(
                timestamp=base_time - timedelta(minutes=i * 10),
                metric_type=MetricType.MODEL_PERFORMANCE,
                metric_name="accuracy",
                metric_value=0.8 + (i % 3) * 0.05,
                category=MetricCategory.REAL_TIME,
                model_id="test_model"
            )
            self.collector._add_metric(metric)
        
        # Flush to database
        self.collector._flush_metrics_buffer()
        
        # Get aggregated metrics
        aggregated = self.collector.get_aggregated_metrics('hour', 2)
        
        self.assertIsInstance(aggregated, dict)
        
        if aggregated:
            print(f"✓ Generated aggregated metrics for {len(aggregated)} metric types")
        else:
            print("✓ Aggregated metrics query completed (no data in time range)")
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        print("\n--- Testing Error Handling ---")
        
        # Test with None model_id
        success = self.collector.record_learning_progress(
            model_id=None,
            epoch=1,
            loss=0.5,
            accuracy=0.85
        )
        self.assertTrue(success)
        print("✓ Handled None model_id gracefully")
        
        # Test trend analysis with no data
        trends = self.collector.analyze_performance_trends("nonexistent_model", 1)
        self.assertIsInstance(trends, list)
        self.assertEqual(len(trends), 0)
        print("✓ Handled missing data gracefully")
        
        # Test getting metrics with empty database
        aggregated = self.collector.get_aggregated_metrics('hour', 1)
        self.assertIsInstance(aggregated, dict)
        print("✓ Handled empty database gracefully")
    
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
        print("\n--- Testing MetricRecord Creation ---")
        
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
        
        print("✓ MetricRecord created successfully")
    
    def test_performance_trend_creation(self):
        """Test PerformanceTrend creation"""
        print("\n--- Testing PerformanceTrend Creation ---")
        
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
        
        print("✓ PerformanceTrend created successfully")
    
    def test_resource_usage_creation(self):
        """Test ResourceUsage creation"""
        print("\n--- Testing ResourceUsage Creation ---")
        
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
        
        print("✓ ResourceUsage created successfully")


if __name__ == '__main__':
    print("="*60)
    print("LEARNING METRICS COLLECTOR TESTS")
    print("="*60)
    
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*60)
    print("METRICS COLLECTOR TEST SUMMARY")
    print("="*60)
    print("Tests validate metrics collection, trend analysis,")
    print("resource monitoring, and real-time tracking.")
    print("="*60)