"""
Test Error Handling Integration
Comprehensive tests for error handling integration across learning system components
"""

import sys
import os
sys.path.append('Python')

import unittest
import logging
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import warnings
warnings.filterwarnings('ignore')

from Python.error_handling_integration import ErrorHandlingIntegration, error_handler_decorator
from Python.learning_error_handler import LearningErrorHandler, ErrorSeverity, ErrorCategory
from Python.learning_coordinator import LearningCoordinator
from Python.learning_config_manager import LearningConfigManager
from Python.learning_notification_system import LearningNotificationSystem


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test cases for Error Handling Integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_integration.db")
        self.test_log_dir = os.path.join(self.test_dir, "logs")
        self.test_config_dir = os.path.join(self.test_dir, "config")
        
        # Create directories
        os.makedirs(self.test_log_dir, exist_ok=True)
        os.makedirs(self.test_config_dir, exist_ok=True)
        
        # Initialize integration
        self.integration = ErrorHandlingIntegration(self.test_db, self.test_log_dir)
        
        # Create mock components
        self.mock_coordinator = Mock(spec=LearningCoordinator)
        self.mock_config_manager = Mock(spec=LearningConfigManager)
        self.mock_notification_system = Mock(spec=LearningNotificationSystem)
        
        # Setup mock attributes
        self.mock_coordinator.learning_cycle_active = False
        self.mock_coordinator.db_manager = Mock()
        self.mock_coordinator.db_manager.db_path = self.test_db
        
        self.mock_config_manager.config_cache = {}
        self.mock_config_manager.cache_timestamps = {}
        
        self.mock_notification_system.config = {
            'channels': {
                'email': {'enabled': True},
                'webhook': {'enabled': True},
                'log': {'enabled': True}
            }
        }
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            self.integration.shutdown()
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except:
            pass
    
    def test_initialization(self):
        """Test integration initialization"""
        self.assertIsNotNone(self.integration.error_handler)
        self.assertIsInstance(self.integration.error_handler, LearningErrorHandler)
        self.assertEqual(self.integration.integration_status, {})
        self.assertFalse(self.integration.recovery_strategies_registered)
    
    def test_coordinator_integration(self):
        """Test integration with learning coordinator"""
        # Test successful integration
        result = self.integration.integrate_with_coordinator(self.mock_coordinator)
        
        self.assertTrue(result)
        self.assertEqual(self.integration.integration_status['coordinator'], 'integrated')
        self.assertIsNotNone(self.integration.coordinator)
    
    def test_config_manager_integration(self):
        """Test integration with configuration manager"""
        # Test successful integration
        result = self.integration.integrate_with_config_manager(self.mock_config_manager)
        
        self.assertTrue(result)
        self.assertEqual(self.integration.integration_status['config_manager'], 'integrated')
        self.assertIsNotNone(self.integration.config_manager)
    
    def test_notification_system_integration(self):
        """Test integration with notification system"""
        # Test successful integration
        result = self.integration.integrate_with_notification_system(self.mock_notification_system)
        
        self.assertTrue(result)
        self.assertEqual(self.integration.integration_status['notification_system'], 'integrated')
        self.assertIsNotNone(self.integration.notification_system)
    
    def test_complete_integration(self):
        """Test complete integration with all components"""
        results = self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        self.assertTrue(results['coordinator'])
        self.assertTrue(results['config_manager'])
        self.assertTrue(results['notification_system'])
        
        # Check all components are integrated
        self.assertEqual(len(self.integration.integration_status), 3)
    
    def test_integration_status(self):
        """Test getting integration status"""
        # Integrate components first
        self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        status = self.integration.get_integration_status()
        
        self.assertIn('integration_status', status)
        self.assertIn('error_handler_status', status)
        self.assertIn('recovery_strategies_count', status)
        self.assertIn('fallback_handlers_count', status)
        
        # Check that recovery strategies were registered
        self.assertGreater(status['recovery_strategies_count'], 0)
        self.assertGreater(status['fallback_handlers_count'], 0)
    
    def test_error_handler_decorator(self):
        """Test error handler decorator functionality"""
        # Create a test function that raises an error
        @error_handler_decorator("test_component", self.integration.error_handler, 
                               ErrorSeverity.LOW, "fallback_value")
        def test_function():
            raise ValueError("Test error")
        
        # Test that decorator catches error and returns fallback
        result = test_function()
        self.assertEqual(result, "fallback_value")
        
        # Check that error was recorded
        self.assertGreater(len(self.integration.error_handler.error_records), 0)
    
    def test_coordinator_recovery_strategies(self):
        """Test coordinator-specific recovery strategies"""
        # Integrate coordinator
        self.integration.integrate_with_coordinator(self.mock_coordinator)
        
        # Check that recovery strategies were registered
        strategies = self.integration.error_handler.recovery_strategies
        
        # Should have strategies for coordinator
        coordinator_strategies = [key for key in strategies.keys() if 'learning_coordinator' in key]
        self.assertGreater(len(coordinator_strategies), 0)
    
    def test_config_manager_recovery_strategies(self):
        """Test config manager-specific recovery strategies"""
        # Integrate config manager
        self.integration.integrate_with_config_manager(self.mock_config_manager)
        
        # Check that recovery strategies were registered
        strategies = self.integration.error_handler.recovery_strategies
        
        # Should have strategies for config manager
        config_strategies = [key for key in strategies.keys() if 'config_manager' in key]
        self.assertGreater(len(config_strategies), 0)
    
    def test_notification_recovery_strategies(self):
        """Test notification system-specific recovery strategies"""
        # Integrate notification system
        self.integration.integrate_with_notification_system(self.mock_notification_system)
        
        # Check that recovery strategies were registered
        strategies = self.integration.error_handler.recovery_strategies
        
        # Should have strategies for notification system
        notification_strategies = [key for key in strategies.keys() if 'notification_system' in key]
        self.assertGreater(len(notification_strategies), 0)
    
    def test_fallback_handlers(self):
        """Test fallback handler registration"""
        # Integrate all components
        self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        # Check that fallback handlers were registered
        fallbacks = self.integration.error_handler.fallback_handlers
        
        self.assertIn('learning_coordinator', fallbacks)
        self.assertIn('config_manager', fallbacks)
        self.assertIn('notification_system', fallbacks)
    
    def test_graceful_degradation_coordinator(self):
        """Test graceful degradation for coordinator"""
        # Setup coordinator with learning cycle active
        self.mock_coordinator.learning_cycle_active = True
        self.integration.integrate_with_coordinator(self.mock_coordinator)
        
        # Trigger degradation
        result = self.integration.trigger_graceful_degradation('coordinator', 'test reason')
        
        self.assertTrue(result)
        self.assertFalse(self.mock_coordinator.learning_cycle_active)
    
    def test_graceful_degradation_config_manager(self):
        """Test graceful degradation for config manager"""
        self.integration.integrate_with_config_manager(self.mock_config_manager)
        
        # Trigger degradation
        result = self.integration.trigger_graceful_degradation('config_manager', 'test reason')
        
        self.assertTrue(result)
        # Should have called clear_cache
        self.mock_config_manager.clear_cache.assert_called_once()
    
    def test_graceful_degradation_notification_system(self):
        """Test graceful degradation for notification system"""
        self.integration.integrate_with_notification_system(self.mock_notification_system)
        
        # Trigger degradation
        result = self.integration.trigger_graceful_degradation('notification_system', 'test reason')
        
        self.assertTrue(result)
        # Should have disabled non-log channels
        self.assertFalse(self.mock_notification_system.config['channels']['email']['enabled'])
        self.assertFalse(self.mock_notification_system.config['channels']['webhook']['enabled'])
        self.assertTrue(self.mock_notification_system.config['channels']['log']['enabled'])
    
    def test_method_wrapping(self):
        """Test that component methods are properly wrapped with error handling"""
        # Create real coordinator for method wrapping test
        with patch('Python.learning_coordinator.LearningDatabaseManager'):
            with patch('Python.learning_coordinator.PerformanceMonitor'):
                with patch('Python.learning_coordinator.LearningDataCollector'):
                    with patch('Python.learning_coordinator.DataPreprocessingPipeline'):
                        with patch('Python.learning_coordinator.ModelEvaluator'):
                            with patch('Python.learning_coordinator.AdaptiveTrainer'):
                                with patch('Python.learning_coordinator.CrossValidationFramework'):
                                    with patch('Python.learning_coordinator.AIModelIntegration'):
                                        coordinator = LearningCoordinator(self.test_db)
                                        
                                        # Store original method
                                        original_method = coordinator.execute_learning_cycle
                                        
                                        # Integrate
                                        self.integration.integrate_with_coordinator(coordinator)
                                        
                                        # Check that method was wrapped
                                        self.assertNotEqual(coordinator.execute_learning_cycle, original_method)
    
    def test_cross_component_error_handling(self):
        """Test cross-component error handling setup"""
        # Integrate all components
        self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        # Test that cross-component setup was called
        # This is verified by checking that the integration completed successfully
        status = self.integration.get_integration_status()
        self.assertEqual(len(status['integration_status']), 3)
    
    def test_global_recovery_strategies(self):
        """Test global recovery strategies registration"""
        # Integrate all components to trigger global strategy registration
        self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        # Check for global strategies
        strategies = self.integration.error_handler.recovery_strategies
        global_strategies = [key for key in strategies.keys() if 'global' in key]
        
        self.assertGreater(len(global_strategies), 0)
    
    def test_error_propagation(self):
        """Test error propagation through integrated components"""
        # Integrate components
        self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        # Simulate an error in coordinator
        test_error = ValueError("Test propagation error")
        error_id = self.integration.error_handler.handle_error(
            test_error, 
            "learning_coordinator",
            {"test": "context"}
        )
        
        self.assertIsNotNone(error_id)
        self.assertGreater(len(self.integration.error_handler.error_records), 0)
    
    def test_circuit_breaker_integration(self):
        """Test circuit breaker integration"""
        # Integrate components
        self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        # Get circuit breaker status
        status = self.integration.get_integration_status()
        circuit_breakers = status['error_handler_status']['circuit_breakers']
        
        self.assertIsInstance(circuit_breakers, dict)
    
    def test_error_statistics_integration(self):
        """Test error statistics integration"""
        # Integrate components
        self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        # Generate some errors
        for i in range(3):
            self.integration.error_handler.handle_error(
                ValueError(f"Test error {i}"),
                "test_component"
            )
        
        # Get statistics
        status = self.integration.get_integration_status()
        error_stats = status['error_handler_status']['error_statistics']
        
        self.assertIn('total_errors', error_stats)
        self.assertGreater(error_stats['total_errors'], 0)
    
    def test_shutdown(self):
        """Test integration shutdown"""
        # Integrate components
        self.integration.integrate_all_components(
            self.mock_coordinator,
            self.mock_config_manager,
            self.mock_notification_system
        )
        
        # Test shutdown
        self.integration.shutdown()
        
        # Should complete without errors
        self.assertTrue(True)  # If we get here, shutdown worked
    
    def test_integration_failure_handling(self):
        """Test handling of integration failures"""
        # Create a mock that raises an exception
        failing_coordinator = Mock()
        failing_coordinator.side_effect = Exception("Integration failure")
        
        # Test that integration handles failures gracefully
        result = self.integration.integrate_with_coordinator(failing_coordinator)
        
        # Should return False and mark as failed
        self.assertFalse(result)
        self.assertEqual(self.integration.integration_status.get('coordinator'), 'failed')
    
    def test_recovery_strategy_execution(self):
        """Test execution of recovery strategies"""
        # Integrate coordinator
        self.integration.integrate_with_coordinator(self.mock_coordinator)
        
        # Create an error record
        from Python.learning_error_handler import ErrorRecord
        error_record = ErrorRecord(
            error_id="test_error",
            timestamp=datetime.now(),
            component="learning_coordinator",
            error_type="Exception",
            error_message="Test error",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.SYSTEM_ERROR,
            stack_trace="test stack trace"
        )
        
        # Test recovery attempt
        recovery_success = self.integration.error_handler._attempt_recovery(error_record)
        
        # Should attempt recovery (may or may not succeed depending on strategy)
        self.assertIsInstance(recovery_success, bool)


class TestErrorHandlerDecorator(unittest.TestCase):
    """Test cases for error handler decorator"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_decorator.db")
        self.error_handler = LearningErrorHandler(self.test_db)
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            self.error_handler.shutdown()
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except:
            pass
    
    def test_decorator_success(self):
        """Test decorator with successful function execution"""
        @error_handler_decorator("test_component", self.error_handler)
        def successful_function():
            return "success"
        
        result = successful_function()
        self.assertEqual(result, "success")
    
    def test_decorator_error_handling(self):
        """Test decorator error handling"""
        @error_handler_decorator("test_component", self.error_handler, 
                               ErrorSeverity.LOW, "fallback")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        self.assertEqual(result, "fallback")
        
        # Check error was recorded
        self.assertGreater(len(self.error_handler.error_records), 0)
    
    def test_decorator_critical_error(self):
        """Test decorator with critical error (should re-raise)"""
        @error_handler_decorator("test_component", self.error_handler, 
                               ErrorSeverity.CRITICAL, "fallback")
        def critical_failing_function():
            raise ValueError("Critical error")
        
        with self.assertRaises(ValueError):
            critical_failing_function()
    
    def test_decorator_with_context(self):
        """Test decorator captures function context"""
        @error_handler_decorator("test_component", self.error_handler, 
                               ErrorSeverity.LOW, None)
        def function_with_args(arg1, arg2, kwarg1=None):
            raise ValueError("Test error")
        
        function_with_args("test1", "test2", kwarg1="test3")
        
        # Check that context was captured
        error_records = list(self.error_handler.error_records.values())
        self.assertGreater(len(error_records), 0)
        
        error_record = error_records[0]
        self.assertIn('function', error_record.context)
        self.assertEqual(error_record.context['function'], 'function_with_args')


if __name__ == '__main__':
    # Setup logging for tests
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)