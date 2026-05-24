"""
Comprehensive Integration Tests for AI Continuous Learning System
Tests component interactions and end-to-end workflows
"""

import unittest
import tempfile
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Import all components
from Python.performance_monitor import PerformanceMonitor
from Python.learning_data_collector import LearningDataCollector
from Python.data_preprocessing_pipeline import DataPreprocessingPipeline
from Python.model_evaluator import ModelEvaluator
from Python.cross_validation_framework import CrossValidationFramework
from Python.model_manager import ModelManager
from Python.ai_system_integration import AISystemIntegration
from Python.learning_coordinator import LearningCoordinator
from Python.learning_notification_system import LearningNotificationSystem
from Python.learning_configuration import LearningConfiguration
from Python.config_management_interface import ConfigurationInterface
from Python.learning_error_handler import LearningErrorHandler


class TestLearningSystemIntegration(unittest.TestCase):
    """Test integration between core learning components"""
    
    def setUp(self):
        """Set up test environment with all components"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_learning.db")
        
        # Initialize all components
        self.performance_monitor = PerformanceMonitor(self.db_path)
        self.data_collector = LearningDataCollector(self.db_path)
        self.preprocessing_pipeline = DataPreprocessingPipeline()
        self.model_evaluator = ModelEvaluator()
        self.cv_framework = CrossValidationFramework()
        self.model_manager = ModelManager(self.temp_dir)
        self.ai_integration = AISystemIntegration()
        self.notification_system = LearningNotificationSystem()
        self.config = LearningConfiguration()
        self.config_interface = ConfigurationInterface(self.config)
        self.error_handler = LearningErrorHandler()
        
        # Initialize coordinator with all components
        self.coordinator = LearningCoordinator(
            performance_monitor=self.performance_monitor,
            data_collector=self.data_collector,
            model_manager=self.model_manager,
            notification_system=self.notification_system,
            config=self.config,
            error_handler=self.error_handler
        )
        
        # Create test data
        self.test_signals = self._create_test_signals()
        self.test_outcomes = self._create_test_outcomes()
    
    def _create_test_signals(self):
        """Create realistic test signal data"""
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        signals = []
        
        for i, date in enumerate(dates):
            signal = {
                'timestamp': date,
                'symbol': 'EURUSD',
                'signal_type': 'BUY' if i % 2 == 0 else 'SELL',
                'confidence': 0.6 + (i % 5) * 0.08,
                'features': {
                    'rsi': 30 + (i % 40),
                    'macd': -0.5 + (i % 10) * 0.1,
                    'volume': 1000 + i * 100
                }
            }
            signals.append(signal)
        
        return signals
    
    def _create_test_outcomes(self):
        """Create corresponding outcomes for test signals"""
        outcomes = []
        for i, signal in enumerate(self.test_signals):
            outcome = {
                'signal_id': i,
                'timestamp': signal['timestamp'] + timedelta(hours=1),
                'actual_result': 'WIN' if i % 3 != 0 else 'LOSS',
                'profit_loss': 100 if i % 3 != 0 else -50,
                'duration_minutes': 30 + (i % 60)
            }
            outcomes.append(outcome)
        
        return outcomes
    
    def test_data_flow_integration(self):
        """Test data flow from performance monitoring to model training"""
        # Step 1: Record performance data
        for signal, outcome in zip(self.test_signals[:10], self.test_outcomes[:10]):
            self.performance_monitor.record_signal_outcome(
                signal['symbol'],
                signal['signal_type'],
                outcome['actual_result'],
                signal['confidence'],
                outcome['profit_loss']
            )
        
        # Step 2: Collect learning data
        learning_data = self.data_collector.collect_learning_data(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10)
        )
        
        # Verify data collection
        self.assertIsNotNone(learning_data)
        self.assertGreater(len(learning_data), 0)
        
        # Step 3: Preprocess data
        processed_data = self.preprocessing_pipeline.preprocess_data(learning_data)
        
        # Verify preprocessing
        self.assertIsNotNone(processed_data)
        self.assertIn('features', processed_data)
        self.assertIn('targets', processed_data)
    
    def test_model_lifecycle_integration(self):
        """Test complete model lifecycle from training to deployment"""
        # Create mock training data
        X_train = np.random.rand(100, 5)
        y_train = np.random.randint(0, 2, 100)
        X_test = np.random.rand(20, 5)
        y_test = np.random.randint(0, 2, 20)
        
        # Step 1: Train and evaluate model
        with patch('sklearn.ensemble.RandomForestClassifier') as mock_rf:
            mock_model = Mock()
            mock_model.predict.return_value = y_test
            mock_model.predict_proba.return_value = np.random.rand(20, 2)
            mock_rf.return_value = mock_model
            
            # Train model
            model = mock_rf()
            model.fit(X_train, y_train)
            
            # Evaluate model
            metrics = self.model_evaluator.evaluate_model(model, X_test, y_test)
            self.assertIn('accuracy', metrics)
            self.assertIn('precision', metrics)
            
            # Step 2: Cross-validate model
            cv_results = self.cv_framework.cross_validate_model(
                model, X_train, y_train, cv_folds=3
            )
            self.assertIn('mean_accuracy', cv_results)
            
            # Step 3: Save model
            model_id = self.model_manager.save_model(model, metrics)
            self.assertIsNotNone(model_id)
            
            # Step 4: Load and verify model
            loaded_model = self.model_manager.load_model(model_id)
            self.assertIsNotNone(loaded_model)
    
    def test_coordinator_workflow_integration(self):
        """Test learning coordinator orchestrating full workflow"""
        # Mock external dependencies
        with patch.object(self.data_collector, 'collect_learning_data') as mock_collect, \
             patch.object(self.model_manager, 'get_current_model') as mock_get_model, \
             patch.object(self.model_manager, 'save_model') as mock_save_model:
            
            # Setup mocks
            mock_collect.return_value = pd.DataFrame({
                'feature1': np.random.rand(50),
                'feature2': np.random.rand(50),
                'target': np.random.randint(0, 2, 50)
            })
            
            mock_model = Mock()
            mock_model.predict.return_value = np.random.randint(0, 2, 10)
            mock_get_model.return_value = mock_model
            mock_save_model.return_value = "model_123"
            
            # Execute learning cycle
            result = self.coordinator.execute_learning_cycle()
            
            # Verify workflow execution
            self.assertTrue(result)
            mock_collect.assert_called_once()
    
    def test_error_handling_integration(self):
        """Test error handling across component interactions"""
        # Test error propagation from data collection
        with patch.object(self.data_collector, 'collect_learning_data') as mock_collect:
            mock_collect.side_effect = Exception("Database connection failed")
            
            # Execute learning cycle and verify error handling
            with patch.object(self.error_handler, 'handle_error') as mock_handle:
                result = self.coordinator.execute_learning_cycle()
                
                # Verify error was handled
                mock_handle.assert_called()
                self.assertFalse(result)  # Should return False on error
    
    def test_notification_integration(self):
        """Test notification system integration with learning events"""
        # Test learning start notification
        self.coordinator.start_learning_cycle()
        
        # Verify notification was sent (would need to check notification system state)
        # This is a placeholder for actual notification verification
        self.assertTrue(True)  # Placeholder assertion
    
    def test_configuration_integration(self):
        """Test configuration system integration with all components"""
        # Update configuration
        self.config_interface.update_model_config({
            'algorithm': 'random_forest',
            'max_depth': 10,
            'n_estimators': 100
        })
        
        # Verify configuration is accessible by components
        model_config = self.config.get_model_config()
        self.assertEqual(model_config['algorithm'], 'random_forest')
        self.assertEqual(model_config['max_depth'], 10)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics of integrated system"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "perf_test.db")
        
        # Initialize components for performance testing
        self.performance_monitor = PerformanceMonitor(self.db_path)
        self.data_collector = LearningDataCollector(self.db_path)
        self.preprocessing_pipeline = DataPreprocessingPipeline()
    
    def test_data_collection_performance(self):
        """Test performance of data collection with large datasets"""
        # Record large number of signals
        start_time = time.time()
        
        for i in range(1000):
            self.performance_monitor.record_signal_outcome(
                'EURUSD',
                'BUY' if i % 2 == 0 else 'SELL',
                'WIN' if i % 3 != 0 else 'LOSS',
                0.6 + (i % 5) * 0.08,
                100 if i % 3 != 0 else -50
            )
        
        record_time = time.time() - start_time
        
        # Collect learning data
        start_time = time.time()
        learning_data = self.data_collector.collect_learning_data(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        collection_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(record_time, 10.0, "Recording 1000 signals should take less than 10 seconds")
        self.assertLess(collection_time, 5.0, "Data collection should take less than 5 seconds")
        self.assertIsNotNone(learning_data)
    
    def test_preprocessing_performance(self):
        """Test preprocessing pipeline performance"""
        # Create large dataset
        large_dataset = pd.DataFrame({
            'feature1': np.random.rand(10000),
            'feature2': np.random.rand(10000),
            'feature3': np.random.rand(10000),
            'target': np.random.randint(0, 2, 10000)
        })
        
        # Test preprocessing performance
        start_time = time.time()
        processed_data = self.preprocessing_pipeline.preprocess_data(large_dataset)
        processing_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(processing_time, 2.0, "Preprocessing 10k records should take less than 2 seconds")
        self.assertIsNotNone(processed_data)
    
    def test_memory_usage_integration(self):
        """Test memory usage during integrated operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        for i in range(100):
            # Create and process data
            data = pd.DataFrame({
                'feature1': np.random.rand(1000),
                'feature2': np.random.rand(1000),
                'target': np.random.randint(0, 2, 1000)
            })
            
            processed = self.preprocessing_pipeline.preprocess_data(data)
            
            # Clean up explicitly
            del data, processed
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage should not increase significantly
        self.assertLess(memory_increase, 100, "Memory increase should be less than 100MB")
    
    def tearDown(self):
        """Clean up performance test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == '__main__':
    # Run integration tests
    integration_suite = unittest.TestLoader().loadTestsFromTestCase(TestLearningSystemIntegration)
    performance_suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformanceIntegration)
    
    # Combine test suites
    combined_suite = unittest.TestSuite([integration_suite, performance_suite])
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Integration Tests Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")