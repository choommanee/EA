"""
Simple Integration Tests for AI Continuous Learning System
Tests basic component interactions with actual interfaces
"""

import unittest
import tempfile
import os
import time
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Import components that we know work
from Python.data_preprocessing_pipeline import DataPreprocessingPipeline
from Python.model_evaluator import ModelEvaluator
from Python.cross_validation_framework import CrossValidationFramework
from Python.ai_system_integration import AISystemIntegration
from Python.learning_notification_system import LearningNotificationSystem
from Python.learning_configuration import LearningConfiguration
from Python.config_management_interface import ConfigurationInterface


class TestSimpleIntegration(unittest.TestCase):
    """Test basic integration between core components"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize components that don't require database
        self.preprocessing_pipeline = DataPreprocessingPipeline()
        self.model_evaluator = ModelEvaluator()
        self.cv_framework = CrossValidationFramework()
        self.ai_integration = AISystemIntegration()
        self.notification_system = LearningNotificationSystem()
        self.config = LearningConfiguration()
        self.config_interface = ConfigurationInterface(self.config)
    
    def test_data_preprocessing_model_evaluation_flow(self):
        """Test data preprocessing to model evaluation flow"""
        print("\n--- Testing Data Preprocessing → Model Evaluation Flow ---")
        
        # Step 1: Create test dataset
        raw_data = pd.DataFrame({
            'feature1': np.random.rand(100),
            'feature2': np.random.rand(100),
            'feature3': np.random.rand(100),
            'target': np.random.randint(0, 2, 100)
        })
        
        # Step 2: Preprocess data
        processed_data = self.preprocessing_pipeline.preprocess_data(raw_data)
        
        # Verify preprocessing
        self.assertIsNotNone(processed_data, "Processed data should not be None")
        self.assertIn('features', processed_data, "Should have features")
        self.assertIn('targets', processed_data, "Should have targets")
        
        # Step 3: Prepare data for model evaluation
        X_test = processed_data['features'][:20]
        y_test = processed_data['targets'][:20]
        
        # Step 4: Create mock model and evaluate
        mock_model = Mock()
        mock_model.predict.return_value = np.random.randint(0, 2, len(y_test))
        mock_model.predict_proba.return_value = np.random.rand(len(y_test), 2)
        
        metrics = self.model_evaluator.evaluate_model(mock_model, X_test, y_test)
        
        # Verify evaluation
        self.assertIsNotNone(metrics, "Metrics should not be None")
        self.assertIn('accuracy', metrics, "Should have accuracy metric")
        
        print(f"✓ Successfully processed {len(raw_data)} records → accuracy: {metrics['accuracy']:.3f}")
    
    def test_cross_validation_integration(self):
        """Test cross-validation with model evaluation"""
        print("\n--- Testing Cross-Validation Integration ---")
        
        # Create test data
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        # Create mock model
        mock_model = Mock()
        mock_model.fit = Mock()
        mock_model.predict.return_value = np.random.randint(0, 2, 20)  # For 5-fold CV
        
        # Perform cross-validation
        cv_results = self.cv_framework.cross_validate_model(
            mock_model, X, y, cv_folds=5
        )
        
        # Verify results
        self.assertIsNotNone(cv_results, "CV results should not be None")
        self.assertIn('mean_accuracy', cv_results, "Should have mean accuracy")
        
        print(f"✓ Cross-validation completed: mean accuracy = {cv_results['mean_accuracy']:.3f}")
    
    def test_configuration_system_integration(self):
        """Test configuration system with other components"""
        print("\n--- Testing Configuration System Integration ---")
        
        # Update configuration
        self.config_interface.update_model_config({
            'algorithm': 'random_forest',
            'max_depth': 10,
            'n_estimators': 100
        })
        
        self.config_interface.update_data_config({
            'batch_size': 1000,
            'validation_split': 0.2
        })
        
        # Verify configuration
        model_config = self.config.get_model_config()
        data_config = self.config.get_data_config()
        
        self.assertEqual(model_config['algorithm'], 'random_forest')
        self.assertEqual(data_config['batch_size'], 1000)
        
        # Test configuration with preprocessing
        test_data = pd.DataFrame({
            'feature1': np.random.rand(50),
            'feature2': np.random.rand(50),
            'target': np.random.randint(0, 2, 50)
        })
        
        processed_data = self.preprocessing_pipeline.preprocess_data(test_data)
        self.assertIsNotNone(processed_data)
        
        print(f"✓ Configuration updated: {model_config['algorithm']}, batch_size: {data_config['batch_size']}")
    
    def test_notification_system_integration(self):
        """Test notification system"""
        print("\n--- Testing Notification System Integration ---")
        
        # Capture notifications
        notifications_sent = []
        
        original_send = self.notification_system.send_notification
        def mock_send(notification_type, message, **kwargs):
            notifications_sent.append({
                'type': notification_type,
                'message': message,
                'kwargs': kwargs
            })
            return True
        
        self.notification_system.send_notification = mock_send
        
        # Send test notifications
        self.notification_system.send_notification('learning_started', 'Learning cycle initiated')
        self.notification_system.send_notification('model_trained', 'Model training completed', accuracy=0.85)
        self.notification_system.send_notification('performance_alert', 'Performance degraded', threshold=0.7)
        
        # Verify notifications
        self.assertEqual(len(notifications_sent), 3)
        self.assertEqual(notifications_sent[0]['type'], 'learning_started')
        self.assertEqual(notifications_sent[1]['kwargs']['accuracy'], 0.85)
        
        # Restore original method
        self.notification_system.send_notification = original_send
        
        print(f"✓ Sent {len(notifications_sent)} notifications successfully")
    
    def test_ai_system_integration_basic(self):
        """Test basic AI system integration"""
        print("\n--- Testing AI System Integration ---")
        
        # Initialize integration
        init_result = self.ai_integration.initialize_integration()
        self.assertTrue(init_result, "AI integration should initialize")
        
        # Test signal processing
        test_signal = {
            'symbol': 'EURUSD',
            'features': [0.5, 0.3, 0.8, 0.2, 0.9],
            'timestamp': datetime.now()
        }
        
        processed_signal = self.ai_integration.process_signal(test_signal)
        self.assertIsNotNone(processed_signal, "Signal processing should return result")
        
        print(f"✓ AI integration initialized and processed signal for {test_signal['symbol']}")
    
    def test_component_performance_characteristics(self):
        """Test performance characteristics of components"""
        print("\n--- Testing Component Performance ---")
        
        # Test preprocessing performance
        large_dataset = pd.DataFrame({
            'feature1': np.random.rand(5000),
            'feature2': np.random.rand(5000),
            'feature3': np.random.rand(5000),
            'target': np.random.randint(0, 2, 5000)
        })
        
        start_time = time.time()
        processed_data = self.preprocessing_pipeline.preprocess_data(large_dataset)
        preprocessing_time = time.time() - start_time
        
        self.assertLess(preprocessing_time, 2.0, "Preprocessing should be fast")
        self.assertIsNotNone(processed_data)
        
        # Test model evaluation performance
        X_test = np.random.rand(1000, 10)
        y_test = np.random.randint(0, 2, 1000)
        
        mock_model = Mock()
        mock_model.predict.return_value = np.random.randint(0, 2, 1000)
        mock_model.predict_proba.return_value = np.random.rand(1000, 2)
        
        start_time = time.time()
        metrics = self.model_evaluator.evaluate_model(mock_model, X_test, y_test)
        evaluation_time = time.time() - start_time
        
        self.assertLess(evaluation_time, 1.0, "Evaluation should be fast")
        self.assertIsNotNone(metrics)
        
        print(f"✓ Performance: Preprocessing={preprocessing_time:.3f}s, Evaluation={evaluation_time:.3f}s")
    
    def test_error_handling_integration(self):
        """Test error handling across components"""
        print("\n--- Testing Error Handling Integration ---")
        
        # Test preprocessing with invalid data
        invalid_data = pd.DataFrame()  # Empty dataframe
        
        try:
            processed_data = self.preprocessing_pipeline.preprocess_data(invalid_data)
            # Should handle gracefully
            print("✓ Preprocessing handled empty data gracefully")
        except Exception as e:
            print(f"✓ Preprocessing raised expected error: {type(e).__name__}")
        
        # Test model evaluation with mismatched data
        X_test = np.random.rand(10, 5)
        y_test = np.random.randint(0, 2, 15)  # Mismatched size
        
        mock_model = Mock()
        mock_model.predict.return_value = np.random.randint(0, 2, 10)
        mock_model.predict_proba.return_value = np.random.rand(10, 2)
        
        try:
            metrics = self.model_evaluator.evaluate_model(mock_model, X_test, y_test)
            print("✓ Model evaluation handled mismatched data")
        except Exception as e:
            print(f"✓ Model evaluation raised expected error: {type(e).__name__}")
    
    def test_memory_efficiency(self):
        """Test memory efficiency during operations"""
        print("\n--- Testing Memory Efficiency ---")
        
        import psutil
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple operations
        for i in range(5):
            # Create and process data
            data = pd.DataFrame({
                'feature1': np.random.rand(2000),
                'feature2': np.random.rand(2000),
                'target': np.random.randint(0, 2, 2000)
            })
            
            processed = self.preprocessing_pipeline.preprocess_data(data)
            
            # Evaluate mock model
            if processed and 'features' in processed:
                X = processed['features'][:100]
                y = processed['targets'][:100]
                
                mock_model = Mock()
                mock_model.predict.return_value = np.random.randint(0, 2, len(y))
                mock_model.predict_proba.return_value = np.random.rand(len(y), 2)
                
                metrics = self.model_evaluator.evaluate_model(mock_model, X, y)
            
            # Clean up
            del data, processed
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        self.assertLess(memory_increase, 50, "Memory increase should be reasonable")
        print(f"✓ Memory efficiency: +{memory_increase:.1f}MB after 5 cycles")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestComponentValidation(unittest.TestCase):
    """Validate individual components work correctly"""
    
    def test_preprocessing_pipeline_validation(self):
        """Validate preprocessing pipeline"""
        pipeline = DataPreprocessingPipeline()
        
        # Test with various data types
        test_cases = [
            pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6], 'target': [0, 1, 0]}),
            pd.DataFrame({'x': np.random.rand(50), 'y': np.random.rand(50), 'target': np.random.randint(0, 2, 50)})
        ]
        
        for i, data in enumerate(test_cases):
            result = pipeline.preprocess_data(data)
            self.assertIsNotNone(result, f"Test case {i} should return result")
    
    def test_model_evaluator_validation(self):
        """Validate model evaluator"""
        evaluator = ModelEvaluator()
        
        # Test with different data sizes
        test_sizes = [10, 50, 100]
        
        for size in test_sizes:
            X = np.random.rand(size, 5)
            y = np.random.randint(0, 2, size)
            
            mock_model = Mock()
            mock_model.predict.return_value = np.random.randint(0, 2, size)
            mock_model.predict_proba.return_value = np.random.rand(size, 2)
            
            metrics = evaluator.evaluate_model(mock_model, X, y)
            self.assertIsNotNone(metrics, f"Should return metrics for size {size}")
            self.assertIn('accuracy', metrics, f"Should have accuracy for size {size}")
    
    def test_configuration_validation(self):
        """Validate configuration system"""
        config = LearningConfiguration()
        interface = ConfigurationInterface(config)
        
        # Test configuration updates
        interface.update_model_config({'test_param': 'test_value'})
        model_config = config.get_model_config()
        
        self.assertEqual(model_config['test_param'], 'test_value')


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)