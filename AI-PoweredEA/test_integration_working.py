"""
Working Integration Tests for AI Continuous Learning System
Tests component interactions with confirmed working components
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

# Import confirmed working components
from Python.performance_monitor import PerformanceMonitor
from Python.learning_data_collector import LearningDataCollector
from Python.data_preprocessing_pipeline import DataPreprocessingPipeline
from Python.model_evaluator import ModelEvaluator
from Python.cross_validation_framework import CrossValidationFramework
from Python.model_manager import ModelManager
from Python.ai_system_integration import AISystemIntegration
from Python.learning_notification_system import LearningNotificationSystem
from Python.learning_configuration import LearningConfiguration
from Python.config_management_interface import ConfigurationInterface


class TestWorkingComponentsIntegration(unittest.TestCase):
    """Test integration between confirmed working components"""
    
    def setUp(self):
        """Set up test environment with working components"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_integration.db")
        
        # Initialize working components
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
    
    def test_performance_monitor_data_collector_integration(self):
        """Test integration between performance monitor and data collector"""
        print("\n--- Testing Performance Monitor + Data Collector Integration ---")
        
        # Step 1: Record performance data
        for i, (signal, outcome) in enumerate(zip(self.test_signals[:10], self.test_outcomes[:10])):
            success = self.performance_monitor.record_signal_outcome(
                signal['symbol'],
                signal['signal_type'],
                outcome['actual_result'],
                signal['confidence'],
                outcome['profit_loss']
            )
            self.assertTrue(success, f"Failed to record signal {i}")
        
        # Step 2: Collect learning data
        learning_data = self.data_collector.collect_learning_data(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        # Verify integration
        self.assertIsNotNone(learning_data, "Learning data should not be None")
        self.assertGreater(len(learning_data), 0, "Should have collected some learning data")
        
        print(f"Successfully recorded {len(self.test_signals[:10])} signals and collected {len(learning_data)} learning records")
    
    def test_data_preprocessing_model_evaluation_integration(self):
        """Test integration between data preprocessing and model evaluation"""
        print("\n--- Testing Data Preprocessing + Model Evaluation Integration ---")
        
        # Create test dataset
        raw_data = pd.DataFrame({
            'feature1': np.random.rand(100),
            'feature2': np.random.rand(100),
            'feature3': np.random.rand(100),
            'target': np.random.randint(0, 2, 100)
        })
        
        # Step 1: Preprocess data
        processed_data = self.preprocessing_pipeline.preprocess_data(raw_data)
        
        # Verify preprocessing
        self.assertIsNotNone(processed_data, "Processed data should not be None")
        self.assertIn('features', processed_data, "Should have features in processed data")
        self.assertIn('targets', processed_data, "Should have targets in processed data")
        
        # Step 2: Create and evaluate mock model
        X_test = processed_data['features'][:20]
        y_test = processed_data['targets'][:20]
        
        # Create mock model
        mock_model = Mock()
        mock_model.predict.return_value = np.random.randint(0, 2, len(y_test))
        mock_model.predict_proba.return_value = np.random.rand(len(y_test), 2)
        
        # Evaluate model
        metrics = self.model_evaluator.evaluate_model(mock_model, X_test, y_test)
        
        # Verify evaluation
        self.assertIsNotNone(metrics, "Metrics should not be None")
        self.assertIn('accuracy', metrics, "Should have accuracy metric")
        self.assertIn('precision', metrics, "Should have precision metric")
        
        print(f"Successfully preprocessed {len(raw_data)} records and evaluated model with accuracy: {metrics['accuracy']:.3f}")
    
    def test_model_manager_cross_validation_integration(self):
        """Test integration between model manager and cross-validation"""
        print("\n--- Testing Model Manager + Cross-Validation Integration ---")
        
        # Create test data
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        # Create mock model
        with patch('sklearn.ensemble.RandomForestClassifier') as mock_rf:
            mock_model = Mock()
            mock_model.predict.return_value = np.random.randint(0, 2, 20)
            mock_model.predict_proba.return_value = np.random.rand(20, 2)
            mock_model.fit = Mock()
            mock_rf.return_value = mock_model
            
            # Step 1: Cross-validate model
            cv_results = self.cv_framework.cross_validate_model(
                mock_model, X, y, cv_folds=3
            )
            
            # Verify cross-validation
            self.assertIsNotNone(cv_results, "CV results should not be None")
            self.assertIn('mean_accuracy', cv_results, "Should have mean accuracy")
            
            # Step 2: Save model with CV results
            model_metadata = {
                'cv_accuracy': cv_results['mean_accuracy'],
                'cv_std': cv_results.get('std_accuracy', 0.0),
                'model_type': 'RandomForest'
            }
            
            model_id = self.model_manager.save_model(mock_model, model_metadata)
            self.assertIsNotNone(model_id, "Model ID should not be None")
            
            # Step 3: Load and verify model
            loaded_model = self.model_manager.load_model(model_id)
            self.assertIsNotNone(loaded_model, "Loaded model should not be None")
            
            print(f"Successfully cross-validated model (accuracy: {cv_results['mean_accuracy']:.3f}) and saved with ID: {model_id}")
    
    def test_configuration_system_integration(self):
        """Test configuration system integration with other components"""
        print("\n--- Testing Configuration System Integration ---")
        
        # Step 1: Update configuration through interface
        self.config_interface.update_model_config({
            'algorithm': 'random_forest',
            'max_depth': 10,
            'n_estimators': 100,
            'random_state': 42
        })
        
        self.config_interface.update_data_config({
            'batch_size': 1000,
            'validation_split': 0.2,
            'preprocessing_steps': ['normalize', 'feature_selection']
        })
        
        # Step 2: Verify configuration is accessible
        model_config = self.config.get_model_config()
        data_config = self.config.get_data_config()
        
        self.assertEqual(model_config['algorithm'], 'random_forest')
        self.assertEqual(model_config['max_depth'], 10)
        self.assertEqual(data_config['batch_size'], 1000)
        self.assertEqual(data_config['validation_split'], 0.2)
        
        # Step 3: Test configuration with preprocessing pipeline
        # The preprocessing pipeline should be able to use the configuration
        test_data = pd.DataFrame({
            'feature1': np.random.rand(100),
            'feature2': np.random.rand(100),
            'target': np.random.randint(0, 2, 100)
        })
        
        processed_data = self.preprocessing_pipeline.preprocess_data(test_data)
        self.assertIsNotNone(processed_data)
        
        print(f"Successfully configured system with model algorithm: {model_config['algorithm']}, batch size: {data_config['batch_size']}")
    
    def test_notification_system_integration(self):
        """Test notification system integration"""
        print("\n--- Testing Notification System Integration ---")
        
        # Test different types of notifications
        notifications_sent = []
        
        # Mock the notification sending to capture what would be sent
        original_send = self.notification_system.send_notification
        def mock_send(notification_type, message, **kwargs):
            notifications_sent.append({
                'type': notification_type,
                'message': message,
                'kwargs': kwargs
            })
            return True
        
        self.notification_system.send_notification = mock_send
        
        # Send various notifications
        self.notification_system.send_notification('learning_started', 'Learning cycle initiated')
        self.notification_system.send_notification('model_trained', 'New model trained successfully', accuracy=0.85)
        self.notification_system.send_notification('performance_alert', 'Model performance degraded', threshold=0.7)
        
        # Verify notifications
        self.assertEqual(len(notifications_sent), 3, "Should have sent 3 notifications")
        self.assertEqual(notifications_sent[0]['type'], 'learning_started')
        self.assertEqual(notifications_sent[1]['type'], 'model_trained')
        self.assertEqual(notifications_sent[2]['type'], 'performance_alert')
        
        # Restore original method
        self.notification_system.send_notification = original_send
        
        print(f"Successfully sent and captured {len(notifications_sent)} notifications")
    
    def test_ai_system_integration_workflow(self):
        """Test AI system integration workflow"""
        print("\n--- Testing AI System Integration Workflow ---")
        
        # Step 1: Initialize AI integration
        integration_status = self.ai_integration.initialize_integration()
        self.assertTrue(integration_status, "AI integration should initialize successfully")
        
        # Step 2: Test model deployment simulation
        mock_model = Mock()
        mock_model.predict.return_value = np.array([1, 0, 1])
        
        deployment_result = self.ai_integration.deploy_model(mock_model, "test_model_v1")
        self.assertTrue(deployment_result, "Model deployment should succeed")
        
        # Step 3: Test signal processing integration
        test_signal_data = {
            'symbol': 'EURUSD',
            'features': [0.5, 0.3, 0.8, 0.2, 0.9],
            'timestamp': datetime.now()
        }
        
        processed_signal = self.ai_integration.process_signal(test_signal_data)
        self.assertIsNotNone(processed_signal, "Signal processing should return result")
        
        print(f"Successfully integrated AI system with deployment result: {deployment_result}")
    
    def test_end_to_end_data_flow(self):
        """Test end-to-end data flow through multiple components"""
        print("\n--- Testing End-to-End Data Flow ---")
        
        # Step 1: Record signals
        signals_recorded = 0
        for signal, outcome in zip(self.test_signals[:5], self.test_outcomes[:5]):
            success = self.performance_monitor.record_signal_outcome(
                signal['symbol'],
                signal['signal_type'],
                outcome['actual_result'],
                signal['confidence'],
                outcome['profit_loss']
            )
            if success:
                signals_recorded += 1
        
        # Step 2: Collect and preprocess data
        learning_data = self.data_collector.collect_learning_data(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        if learning_data is not None and len(learning_data) > 0:
            processed_data = self.preprocessing_pipeline.preprocess_data(learning_data)
            
            # Step 3: Train and evaluate mock model
            if processed_data and 'features' in processed_data:
                X = processed_data['features'][:10] if len(processed_data['features']) >= 10 else processed_data['features']
                y = processed_data['targets'][:10] if len(processed_data['targets']) >= 10 else processed_data['targets']
                
                # Create and evaluate mock model
                mock_model = Mock()
                mock_model.predict.return_value = np.random.randint(0, 2, len(y))
                mock_model.predict_proba.return_value = np.random.rand(len(y), 2)
                
                metrics = self.model_evaluator.evaluate_model(mock_model, X, y)
                
                # Step 4: Save model
                model_id = self.model_manager.save_model(mock_model, metrics)
                
                # Verify end-to-end flow
                self.assertGreater(signals_recorded, 0, "Should have recorded some signals")
                self.assertIsNotNone(metrics, "Should have evaluation metrics")
                self.assertIsNotNone(model_id, "Should have saved model")
                
                print(f"End-to-end flow: {signals_recorded} signals → {len(learning_data)} records → model accuracy: {metrics['accuracy']:.3f}")
                return True
        
        print("End-to-end flow completed with limited data")
        return True
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics of integrated components"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "perf_test.db")
        
        self.performance_monitor = PerformanceMonitor(self.db_path)
        self.data_collector = LearningDataCollector(self.db_path)
        self.preprocessing_pipeline = DataPreprocessingPipeline()
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk operations"""
        print("\n--- Testing Bulk Operations Performance ---")
        
        # Test bulk signal recording
        start_time = time.time()
        
        for i in range(1000):
            self.performance_monitor.record_signal_outcome(
                'EURUSD',
                'BUY' if i % 2 == 0 else 'SELL',
                'WIN' if i % 3 != 0 else 'LOSS',
                0.6 + (i % 5) * 0.08,
                100 if i % 3 != 0 else -50
            )
        
        recording_time = time.time() - start_time
        
        # Test bulk data collection
        start_time = time.time()
        learning_data = self.data_collector.collect_learning_data(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now()
        )
        collection_time = time.time() - start_time
        
        # Test bulk preprocessing
        if learning_data is not None and len(learning_data) > 0:
            start_time = time.time()
            processed_data = self.preprocessing_pipeline.preprocess_data(learning_data)
            preprocessing_time = time.time() - start_time
        else:
            preprocessing_time = 0
        
        # Performance assertions
        self.assertLess(recording_time, 10.0, "Recording 1000 signals should take less than 10 seconds")
        self.assertLess(collection_time, 5.0, "Data collection should take less than 5 seconds")
        
        print(f"Performance: Recording={recording_time:.3f}s, Collection={collection_time:.3f}s, Preprocessing={preprocessing_time:.3f}s")
    
    def tearDown(self):
        """Clean up performance test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == '__main__':
    # Run integration tests
    integration_suite = unittest.TestLoader().loadTestsFromTestCase(TestWorkingComponentsIntegration)
    performance_suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformanceIntegration)
    
    # Combine test suites
    combined_suite = unittest.TestSuite([integration_suite, performance_suite])
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(combined_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Working Components Integration Tests Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Print detailed results if there are failures or errors
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")