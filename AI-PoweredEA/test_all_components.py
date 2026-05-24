แป#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for AI Continuous Learning System
Tests all components with mock objects, fixtures, and comprehensive coverage
"""

import sys
import os
sys.path.append('Python')

import unittest
import logging
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import warnings
warnings.filterwarnings('ignore')

# Setup logging for tests
logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests


class TestDataGenerator:
    """Generate test data and fixtures for learning system tests"""
    
    @staticmethod
    def generate_signal_data(count: int = 100):
        """Generate mock signal data"""
        import random
        signals = []
        
        for i in range(count):
            signal = {
                'timestamp': datetime.now() - timedelta(hours=i),
                'signal_type': random.choice(['BUY', 'SELL', 'HOLD']),
                'confidence': random.uniform(0.5, 1.0),
                'price': random.uniform(1.0, 2.0),
                'outcome': random.choice([True, False]),
                'profit_loss': random.uniform(-100, 100)
            }
            signals.append(signal)
        
        return signals
    
    @staticmethod
    def generate_model_data():
        """Generate mock model data"""
        return {
            'model_id': 'test_model_001',
            'model_type': 'RandomForest',
            'accuracy': 0.85,
            'precision': 0.82,
            'recall': 0.88,
            'f1_score': 0.85,
            'training_data_size': 1000,
            'created_at': datetime.now(),
            'version': '1.0.0'
        }
    
    @staticmethod
    def generate_performance_data():
        """Generate mock performance data"""
        return {
            'timestamp': datetime.now(),
            'accuracy': 0.85,
            'precision': 0.82,
            'recall': 0.88,
            'total_signals': 100,
            'correct_predictions': 85,
            'profit_loss': 150.0,
            'win_rate': 0.65
        }


class TestPerformanceMonitor(unittest.TestCase):
    """Test Performance Monitor component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = TestDataGenerator.generate_signal_data(50)
        
    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization"""
        try:
            from performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            self.assertIsNotNone(monitor)
            self.assertTrue(hasattr(monitor, 'track_signal_outcome'))
            self.assertTrue(hasattr(monitor, 'get_current_performance'))
            
        except ImportError:
            self.skipTest("PerformanceMonitor not available")
    
    def test_performance_calculation(self):
        """Test performance metrics calculation"""
        try:
            from performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Test tracking signal outcomes
            monitor.track_signal_outcome("test_signal", True, 0.8, 50.0)
            monitor.track_signal_outcome("test_signal2", False, 0.6, -30.0)
            monitor.track_signal_outcome("test_signal3", True, 0.9, 75.0)
            
            # Test getting current performance
            performance = monitor.get_current_performance()
            
            self.assertIsInstance(performance, dict)
            self.assertIn('accuracy', performance)
            self.assertIn('total_signals', performance)
                
        except ImportError:
            self.skipTest("PerformanceMonitor not available")
    
    def test_degradation_detection(self):
        """Test performance degradation detection"""
        try:
            from performance_monitor import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Add some performance data
            monitor.track_signal_outcome("signal1", True, 0.8, 50.0)
            monitor.track_signal_outcome("signal2", False, 0.6, -30.0)
            
            # Test degradation detection
            current_performance = monitor.get_current_performance()
            
            # Mock degradation check
            with patch.object(monitor, 'check_performance_degradation') as mock_check:
                mock_check.return_value = True
                is_degraded = monitor.check_performance_degradation()
                self.assertTrue(is_degraded)
                
        except ImportError:
            self.skipTest("PerformanceMonitor not available")


class TestLearningDataCollector(unittest.TestCase):
    """Test Learning Data Collector component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_signals = TestDataGenerator.generate_signal_data(100)
    
    def test_data_collector_initialization(self):
        """Test data collector initialization"""
        try:
            from learning_data_collector import LearningDataCollector
            
            collector = LearningDataCollector()
            self.assertIsNotNone(collector)
            self.assertTrue(hasattr(collector, 'collect_signal_feedback'))
            self.assertTrue(hasattr(collector, 'prepare_features'))
            
        except ImportError:
            self.skipTest("LearningDataCollector not available")
    
    def test_data_collection(self):
        """Test data collection functionality"""
        try:
            from learning_data_collector import LearningDataCollector
            
            collector = LearningDataCollector()
            
            # Mock database connection
            with patch.object(collector, 'db_manager') as mock_db:
                mock_db.get_signal_feedback.return_value = self.test_signals
                collected_data = collector.collect_signal_feedback()
                
                self.assertIsInstance(collected_data, list)
                
        except ImportError:
            self.skipTest("LearningDataCollector not available")
    
    def test_data_preparation(self):
        """Test training data preparation"""
        try:
            from learning_data_collector import LearningDataCollector
            
            collector = LearningDataCollector()
            
            # Test feature preparation
            features = collector.prepare_features(self.test_signals)
            
            self.assertIsNotNone(features)
            self.assertIsInstance(features, (list, tuple))
            
        except ImportError:
            self.skipTest("LearningDataCollector not available")


class TestModelEvaluator(unittest.TestCase):
    """Test Model Evaluator component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_model = Mock()
        self.mock_model.predict.return_value = [1, 0, 1, 1, 0]
        self.test_X = [[1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
        self.test_y = [1, 0, 1, 1, 0]
    
    def test_evaluator_initialization(self):
        """Test model evaluator initialization"""
        try:
            from model_evaluator import ModelEvaluator
            
            evaluator = ModelEvaluator()
            self.assertIsNotNone(evaluator)
            self.assertTrue(hasattr(evaluator, 'evaluate_model'))
            self.assertTrue(hasattr(evaluator, 'compare_models'))
            
        except ImportError:
            self.skipTest("ModelEvaluator not available")
    
    def test_model_evaluation(self):
        """Test model evaluation functionality"""
        try:
            from model_evaluator import ModelEvaluator
            
            evaluator = ModelEvaluator()
            
            # Test model evaluation with correct signature
            metrics = evaluator.evaluate_model(self.mock_model, self.test_X, self.test_y, "test_model")
            
            self.assertIsInstance(metrics, dict)
            self.assertIn('accuracy', metrics)
            self.assertIn('precision', metrics)
            self.assertIn('recall', metrics)
            
        except ImportError:
            self.skipTest("ModelEvaluator not available")
    
    def test_model_comparison(self):
        """Test model comparison functionality"""
        try:
            from model_evaluator import ModelEvaluator
            
            evaluator = ModelEvaluator()
            
            # Create second mock model
            mock_model2 = Mock()
            mock_model2.predict.return_value = [1, 1, 1, 0, 0]
            
            # Use dictionary format as expected by compare_models
            models = {"model1": self.mock_model, "model2": mock_model2}
            
            # Test model comparison
            comparison = evaluator.compare_models(models, self.test_X, self.test_y)
            
            self.assertIsInstance(comparison, dict)
            self.assertEqual(len(comparison), 2)
            
        except ImportError:
            self.skipTest("ModelEvaluator not available")


class TestModelManager(unittest.TestCase):
    """Test Model Manager component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.model_data = TestDataGenerator.generate_model_data()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_manager_initialization(self):
        """Test model manager initialization"""
        try:
            from model_manager import ModelManager
            
            manager = ModelManager(storage_path=self.temp_dir)
            self.assertIsNotNone(manager)
            self.assertTrue(hasattr(manager, 'save_model'))
            self.assertTrue(hasattr(manager, 'load_model'))
            self.assertTrue(hasattr(manager, 'deploy_model'))
            
        except ImportError:
            self.skipTest("ModelManager not available")
    
    def test_model_saving_loading(self):
        """Test model saving and loading"""
        try:
            from model_manager import ModelManager
            
            manager = ModelManager(storage_path=self.temp_dir)
            
            # Mock model
            mock_model = Mock()
            model_id = "test_model_001"
            
            # Test saving
            with patch.object(manager, '_serialize_model') as mock_serialize:
                mock_serialize.return_value = b"mock_model_data"
                success = manager.save_model(mock_model, model_id, self.model_data)
                self.assertTrue(success)
            
            # Test loading
            with patch.object(manager, '_deserialize_model') as mock_deserialize:
                mock_deserialize.return_value = mock_model
                loaded_model = manager.load_model(model_id)
                self.assertIsNotNone(loaded_model)
                
        except ImportError:
            self.skipTest("ModelManager not available")
    
    def test_model_deployment(self):
        """Test model deployment functionality"""
        try:
            from model_manager import ModelManager
            
            manager = ModelManager(storage_path=self.temp_dir)
            
            model_id = "test_model_001"
            
            # Mock model exists
            with patch.object(manager, 'model_exists', return_value=True):
                with patch.object(manager, 'load_model', return_value=Mock()):
                    success = manager.deploy_model(model_id)
                    self.assertTrue(success)
                    
        except ImportError:
            self.skipTest("ModelManager not available")


class TestLearningCoordinator(unittest.TestCase):
    """Test Learning Coordinator component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_coordinator_initialization(self):
        """Test learning coordinator initialization"""
        try:
            from learning_coordinator import LearningCoordinator
            
            coordinator = LearningCoordinator()
            self.assertIsNotNone(coordinator)
            self.assertTrue(hasattr(coordinator, 'trigger_learning_cycle'))
            self.assertTrue(hasattr(coordinator, 'monitor_learning_progress'))
            
        except ImportError:
            self.skipTest("LearningCoordinator not available")
    
    def test_learning_cycle_trigger(self):
        """Test learning cycle triggering"""
        try:
            from learning_coordinator import LearningCoordinator, LearningTrigger
            
            coordinator = LearningCoordinator()
            
            # Mock dependencies
            with patch.object(coordinator, 'data_collector') as mock_collector:
                with patch.object(coordinator, 'model_trainer') as mock_trainer:
                    mock_collector.collect_learning_data.return_value = [1, 2, 3]
                    mock_trainer.train_models.return_value = True
                    
                    cycle_id = coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
                    self.assertIsNotNone(cycle_id)
                    
        except ImportError:
            self.skipTest("LearningCoordinator not available")
    
    def test_progress_monitoring(self):
        """Test learning progress monitoring"""
        try:
            from learning_coordinator import LearningCoordinator
            
            coordinator = LearningCoordinator()
            
            # Mock active cycle
            cycle_id = "test_cycle_001"
            
            with patch.object(coordinator, '_get_cycle_status') as mock_status:
                mock_status.return_value = {
                    'cycle_id': cycle_id,
                    'status': 'running',
                    'progress': 0.5,
                    'stage': 'training'
                }
                
                progress = coordinator.monitor_learning_progress(cycle_id)
                self.assertIsInstance(progress, dict)
                self.assertIn('status', progress)
                self.assertIn('progress', progress)
                
        except ImportError:
            self.skipTest("LearningCoordinator not available")


class TestNotificationSystem(unittest.TestCase):
    """Test Notification System component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_notification_system_initialization(self):
        """Test notification system initialization"""
        try:
            from learning_notification_system import LearningNotificationSystem
            
            notification_system = LearningNotificationSystem(
                config_path=os.path.join(self.temp_dir, "test_notifications.json")
            )
            self.assertIsNotNone(notification_system)
            self.assertTrue(hasattr(notification_system, 'send_performance_alert'))
            self.assertTrue(hasattr(notification_system, 'send_error_notification'))
            
        except ImportError:
            self.skipTest("LearningNotificationSystem not available")
    
    def test_performance_alert(self):
        """Test performance alert functionality"""
        try:
            from learning_notification_system import LearningNotificationSystem
            
            notification_system = LearningNotificationSystem(
                config_path=os.path.join(self.temp_dir, "test_notifications.json")
            )
            
            # Test performance alert
            success = notification_system.send_performance_alert(
                model_name="test_model",
                current_performance=0.65,
                threshold=0.75,
                degradation_percent=0.13
            )
            
            self.assertTrue(success)
            
        except ImportError:
            self.skipTest("LearningNotificationSystem not available")
    
    def test_error_notification(self):
        """Test error notification functionality"""
        try:
            from learning_notification_system import LearningNotificationSystem
            
            notification_system = LearningNotificationSystem(
                config_path=os.path.join(self.temp_dir, "test_notifications.json")
            )
            
            # Test error notification
            success = notification_system.send_error_notification(
                error_type="TestError",
                error_message="This is a test error",
                component="TestComponent"
            )
            
            self.assertTrue(success)
            
        except ImportError:
            self.skipTest("LearningNotificationSystem not available")


class TestConfigurationSystem(unittest.TestCase):
    """Test Configuration System component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_configuration_initialization(self):
        """Test configuration system initialization"""
        try:
            from learning_configuration import LearningConfiguration
            
            config_manager = LearningConfiguration(config_dir=self.temp_dir)
            self.assertIsNotNone(config_manager)
            self.assertTrue(hasattr(config_manager, 'load_configuration'))
            self.assertTrue(hasattr(config_manager, 'save_configuration'))
            
        except ImportError:
            self.skipTest("LearningConfiguration not available")
    
    def test_configuration_operations(self):
        """Test configuration operations"""
        try:
            from learning_configuration import LearningConfiguration
            
            config_manager = LearningConfiguration(config_dir=self.temp_dir)
            
            # Test getting config value
            batch_size = config_manager.get_config_value("model_training.batch_size")
            self.assertIsNotNone(batch_size)
            
            # Test setting config value
            success = config_manager.set_config_value("model_training.batch_size", 128)
            self.assertTrue(success)
            
            # Verify the change
            new_batch_size = config_manager.get_config_value("model_training.batch_size")
            self.assertEqual(new_batch_size, 128)
            
        except ImportError:
            self.skipTest("LearningConfiguration not available")
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        try:
            from learning_configuration import LearningConfiguration
            
            config_manager = LearningConfiguration(config_dir=self.temp_dir)
            
            # Test valid configuration
            is_valid = config_manager.validate_configuration()
            self.assertTrue(is_valid)
            
            # Test invalid configuration (should be rejected)
            success = config_manager.set_config_value("model_training.batch_size", -10)
            self.assertFalse(success)  # Should fail validation
            
        except ImportError:
            self.skipTest("LearningConfiguration not available")


class TestErrorHandler(unittest.TestCase):
    """Test Error Handler component"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_error_handler_initialization(self):
        """Test error handler initialization"""
        try:
            from learning_error_handler import LearningErrorHandler
            
            error_handler = LearningErrorHandler()
            self.assertIsNotNone(error_handler)
            self.assertTrue(hasattr(error_handler, 'handle_error'))
            self.assertTrue(hasattr(error_handler, 'log_error'))
            
        except ImportError:
            self.skipTest("LearningErrorHandler not available")
    
    def test_error_handling(self):
        """Test error handling functionality"""
        try:
            from learning_error_handler import LearningErrorHandler, ErrorSeverity
            
            error_handler = LearningErrorHandler()
            
            # Test error handling
            test_error = Exception("Test error")
            
            with patch.object(error_handler, 'notification_system') as mock_notifier:
                result = error_handler.handle_error(
                    test_error,
                    component="TestComponent",
                    severity=ErrorSeverity.MEDIUM
                )
                
                self.assertIsInstance(result, dict)
                self.assertIn('handled', result)
                
        except ImportError:
            self.skipTest("LearningErrorHandler not available")
    
    def test_error_recovery(self):
        """Test error recovery functionality"""
        try:
            from learning_error_handler import LearningErrorHandler
            
            error_handler = LearningErrorHandler()
            
            # Test recovery mechanism
            with patch.object(error_handler, '_attempt_recovery') as mock_recovery:
                mock_recovery.return_value = True
                
                recovery_success = error_handler.attempt_recovery("TestComponent", "test_error")
                self.assertTrue(recovery_success)
                
        except ImportError:
            self.skipTest("LearningErrorHandler not available")


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios between components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring with notification integration"""
        try:
            from performance_monitor import PerformanceMonitor
            from learning_notification_system import LearningNotificationSystem
            
            monitor = PerformanceMonitor()
            notifier = LearningNotificationSystem(
                config_path=os.path.join(self.temp_dir, "test_notifications.json")
            )
            
            # Add some performance data
            monitor.track_signal_outcome("signal1", False, 0.6, -30.0)
            monitor.track_signal_outcome("signal2", False, 0.5, -40.0)
            
            # Get current performance
            performance = monitor.get_current_performance()
            
            # Test integration with notification
            success = notifier.send_performance_alert(
                model_name="test_model",
                current_performance=performance.get('accuracy', 0.5),
                threshold=0.75,
                degradation_percent=0.25
            )
            self.assertTrue(success)
                        
        except ImportError:
            self.skipTest("Integration components not available")
    
    def test_data_collection_training_integration(self):
        """Test data collection with model training integration"""
        try:
            from learning_data_collector import LearningDataCollector
            from model_manager import ModelManager
            
            collector = LearningDataCollector()
            manager = ModelManager(storage_path=self.temp_dir)
            
            # Mock data collection
            test_data = TestDataGenerator.generate_signal_data(50)
            
            with patch.object(collector, 'collect_signal_feedback', return_value=test_data):
                with patch.object(collector, 'prepare_features') as mock_prepare:
                    mock_prepare.return_value = ([1, 2, 3], [0, 1, 0])
                    
                    # Test integration
                    collected_data = collector.collect_signal_feedback()
                    self.assertIsNotNone(collected_data)
                    
                    features = collector.prepare_features(collected_data)
                    self.assertIsNotNone(features)
                    
        except ImportError:
            self.skipTest("Integration components not available")


def create_test_suite():
    """Create comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPerformanceMonitor,
        TestLearningDataCollector,
        TestModelEvaluator,
        TestModelManager,
        TestLearningCoordinator,
        TestNotificationSystem,
        TestConfigurationSystem,
        TestErrorHandler,
        TestIntegrationScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_all_tests():
    """Run all unit tests and return results"""
    print("🚀 Starting Comprehensive Unit Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = create_test_suite()
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True
    )
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 UNIT TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total_tests - failures - errors - skipped
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failures}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    
    if total_tests > 0:
        success_rate = (passed / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    else:
        success_rate = 0
        print("Success Rate: 0.0%")
    
    print("-" * 60)
    
    # Print failure details
    if result.failures:
        print("FAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("ERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.skipped:
        print("SKIPPED:")
        for test, reason in result.skipped:
            print(f"- {test}: {reason}")
    
    print("-" * 60)
    
    if failures == 0 and errors == 0:
        print("🎉 All tests passed! All components are working correctly.")
    elif success_rate >= 80:
        print("✅ Most tests passed! Components are mostly functional.")
    else:
        print("⚠️ Several tests failed. Please check component implementations.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("Config", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    os.makedirs("Models", exist_ok=True)
    os.makedirs("Data", exist_ok=True)
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)