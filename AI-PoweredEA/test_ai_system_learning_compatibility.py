"""
Test suite for AI System Learning Compatibility
Tests updates to AI system for learning integration
"""

import unittest
import tempfile
import os
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from Python.ai_system_learning_compatibility import (
    AISystemLearningCompatibility, LearningCompatibilityConfig,
    LearningMode, ModelSwitchStrategy
)


class TestAISystemLearningCompatibility(unittest.TestCase):
    """Test AI System Learning Compatibility functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test configuration
        self.config = LearningCompatibilityConfig(
            learning_mode=LearningMode.ACTIVE,
            model_switch_strategy=ModelSwitchStrategy.PERFORMANCE_BASED,
            enable_data_collection=True,
            enable_model_switching=True,
            performance_threshold=0.05,
            min_signals_for_switch=10  # Lower for testing
        )
        
        # Mock AI system
        self.mock_ai_system = Mock()
        self.mock_ai_system.current_config = {}
        
        self.compatibility = AISystemLearningCompatibility(
            self.config, 
            self.mock_ai_system
        )
    
    def test_initialization(self):
        """Test learning compatibility initialization"""
        print("\n--- Testing Learning Compatibility Initialization ---")
        
        self.assertIsNotNone(self.compatibility)
        self.assertEqual(self.compatibility.config.learning_mode, LearningMode.ACTIVE)
        self.assertEqual(self.compatibility.config.model_switch_strategy, ModelSwitchStrategy.PERFORMANCE_BASED)
        self.assertFalse(self.compatibility.learning_enabled)
        
        print("✓ Learning compatibility initialized successfully")
    
    def test_learning_compatibility_config(self):
        """Test learning compatibility configuration"""
        print("\n--- Testing Learning Compatibility Configuration ---")
        
        # Test default configuration
        default_config = LearningCompatibilityConfig()
        self.assertEqual(default_config.learning_mode, LearningMode.ACTIVE)
        self.assertEqual(default_config.model_switch_strategy, ModelSwitchStrategy.PERFORMANCE_BASED)
        self.assertTrue(default_config.enable_data_collection)
        self.assertTrue(default_config.enable_model_switching)
        
        # Test custom configuration
        custom_config = LearningCompatibilityConfig(
            learning_mode=LearningMode.PASSIVE,
            model_switch_strategy=ModelSwitchStrategy.TIME_BASED,
            performance_threshold=0.1,
            min_signals_for_switch=100
        )
        
        self.assertEqual(custom_config.learning_mode, LearningMode.PASSIVE)
        self.assertEqual(custom_config.model_switch_strategy, ModelSwitchStrategy.TIME_BASED)
        self.assertEqual(custom_config.performance_threshold, 0.1)
        self.assertEqual(custom_config.min_signals_for_switch, 100)
        
        print("✓ Learning compatibility configuration validation passed")
    
    def test_learning_mode_update(self):
        """Test learning mode updates"""
        print("\n--- Testing Learning Mode Updates ---")
        
        # Test mode update
        success = self.compatibility.update_learning_mode(LearningMode.PASSIVE)
        self.assertTrue(success)
        self.assertEqual(self.compatibility.config.learning_mode, LearningMode.PASSIVE)
        
        # Test disabled mode
        success = self.compatibility.update_learning_mode(LearningMode.DISABLED)
        self.assertTrue(success)
        self.assertEqual(self.compatibility.config.learning_mode, LearningMode.DISABLED)
        
        # Test aggressive mode
        success = self.compatibility.update_learning_mode(LearningMode.AGGRESSIVE)
        self.assertTrue(success)
        self.assertEqual(self.compatibility.config.learning_mode, LearningMode.AGGRESSIVE)
        
        print("✓ Learning mode updates successful")
    
    def test_hook_installation(self):
        """Test hook installation"""
        print("\n--- Testing Hook Installation ---")
        
        # Test signal hook installation
        signal_hook = Mock()
        success = self.compatibility.install_signal_generation_hook(signal_hook)
        self.assertTrue(success)
        self.assertIn(signal_hook, self.compatibility.signal_hooks)
        
        # Test outcome hook installation
        outcome_hook = Mock()
        success = self.compatibility.install_outcome_tracking_hook(outcome_hook)
        self.assertTrue(success)
        self.assertIn(outcome_hook, self.compatibility.outcome_hooks)
        
        print("✓ Hook installation successful")
    
    def test_signal_processing_with_learning(self):
        """Test signal processing with learning"""
        print("\n--- Testing Signal Processing with Learning ---")
        
        # Mock pipeline integration
        mock_pipeline = Mock()
        self.compatibility.pipeline_integration = mock_pipeline
        self.compatibility.current_model_id = "test_model"
        
        # Test signal data
        signal_data = {
            'signal_id': 'test_signal_001',
            'symbol': 'EURUSD',
            'signal_type': 'BUY',
            'confidence': 0.75,
            'features': {'rsi': 30, 'macd': 0.5}
        }
        
        # Process signal
        result = self.compatibility.process_signal_with_learning(signal_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn('learning_metadata', result)
        self.assertEqual(result['learning_metadata']['model_id'], 'test_model')
        self.assertEqual(self.compatibility.signal_count, 1)
        
        # Verify pipeline integration was called
        mock_pipeline.process_new_signal.assert_called_once()
        
        print(f"✓ Signal processed with learning metadata: {result['learning_metadata']}")
    
    def test_outcome_processing_with_learning(self):
        """Test outcome processing with learning"""
        print("\n--- Testing Outcome Processing with Learning ---")
        
        # Mock pipeline integration
        mock_pipeline = Mock()
        self.compatibility.pipeline_integration = mock_pipeline
        self.compatibility.current_model_id = "test_model"
        
        # Test outcome data
        outcome_data = {
            'signal_id': 'test_signal_001',
            'outcome': 'WIN',
            'profit_loss': 100.0,
            'duration_minutes': 30
        }
        
        # Process outcome
        success = self.compatibility.process_outcome_with_learning(outcome_data)
        
        self.assertTrue(success)
        
        # Verify pipeline integration was called
        mock_pipeline.process_signal_outcome.assert_called_once()
        
        # Check performance history was updated
        self.assertIn('test_model', self.compatibility.model_performance_history)
        self.assertEqual(len(self.compatibility.model_performance_history['test_model']), 1)
        
        print("✓ Outcome processed with learning tracking")
    
    def test_model_switching_with_learning(self):
        """Test model switching with learning"""
        print("\n--- Testing Model Switching with Learning ---")
        
        # Mock pipeline integration
        mock_pipeline = Mock()
        self.compatibility.pipeline_integration = mock_pipeline
        
        # Mock AI system model switching
        self.mock_ai_system.switch_to_model = Mock(return_value=True)
        
        old_model = "old_model"
        new_model = "new_model"
        self.compatibility.current_model_id = old_model
        
        # Switch model
        success = self.compatibility.switch_model_with_learning(new_model, "performance_improvement")
        
        self.assertTrue(success)
        self.assertEqual(self.compatibility.current_model_id, new_model)
        self.assertEqual(self.compatibility.signal_count, 0)  # Should reset
        
        # Verify pipeline integration was notified
        mock_pipeline.switch_model.assert_called_once_with(new_model, "performance_improvement")
        
        print(f"✓ Model switched with learning: {old_model} → {new_model}")
    
    def test_learning_status(self):
        """Test learning status retrieval"""
        print("\n--- Testing Learning Status Retrieval ---")
        
        # Set up test state
        self.compatibility.learning_enabled = True
        self.compatibility.current_model_id = "status_test_model"
        self.compatibility.signal_count = 42
        
        # Mock pipeline integration
        mock_pipeline = Mock()
        mock_pipeline.get_performance_summary.return_value = {
            'accuracy': 0.85,
            'signal_count': 42
        }
        self.compatibility.pipeline_integration = mock_pipeline
        
        # Get status
        status = self.compatibility.get_learning_status()
        
        self.assertIsInstance(status, dict)
        self.assertTrue(status['learning_enabled'])
        self.assertEqual(status['learning_mode'], LearningMode.ACTIVE.value)
        self.assertEqual(status['current_model_id'], 'status_test_model')
        self.assertEqual(status['signal_count'], 42)
        self.assertIn('performance_summary', status)
        
        print(f"✓ Learning status retrieved: {status['learning_mode']}, signals: {status['signal_count']}")
    
    def test_configuration_updates(self):
        """Test learning configuration updates"""
        print("\n--- Testing Configuration Updates ---")
        
        # Mock learning configuration
        mock_learning_config = Mock()
        self.compatibility.learning_config = mock_learning_config
        
        # Test configuration updates
        config_updates = {
            'learning_mode': 'passive',
            'performance_threshold': 0.1,
            'enable_data_collection': False,
            'min_signals_for_switch': 200
        }
        
        success = self.compatibility.update_learning_configuration(config_updates)
        
        self.assertTrue(success)
        self.assertEqual(self.compatibility.config.learning_mode, LearningMode.PASSIVE)
        self.assertEqual(self.compatibility.config.performance_threshold, 0.1)
        self.assertFalse(self.compatibility.config.enable_data_collection)
        self.assertEqual(self.compatibility.config.min_signals_for_switch, 200)
        
        # Verify learning config was updated
        mock_learning_config.update_configuration.assert_called_once()
        
        print("✓ Configuration updates successful")
    
    def test_performance_history_tracking(self):
        """Test performance history tracking"""
        print("\n--- Testing Performance History Tracking ---")
        
        self.compatibility.current_model_id = "history_test_model"
        
        # Create mock outcome
        from Python.ai_learning_pipeline_integration import SignalOutcome
        
        outcome1 = SignalOutcome(
            signal_id="test_001",
            timestamp=datetime.now(),
            outcome="WIN",
            profit_loss=100.0,
            duration_minutes=30
        )
        
        outcome2 = SignalOutcome(
            signal_id="test_002",
            timestamp=datetime.now(),
            outcome="LOSS",
            profit_loss=-50.0,
            duration_minutes=15
        )
        
        # Update performance history
        self.compatibility._update_performance_history(outcome1)
        self.compatibility._update_performance_history(outcome2)
        
        # Check history was recorded
        self.assertIn("history_test_model", self.compatibility.model_performance_history)
        history = self.compatibility.model_performance_history["history_test_model"]
        self.assertEqual(len(history), 2)
        
        # Get current performance
        performance = self.compatibility._get_current_model_performance()
        self.assertIsNotNone(performance)
        self.assertEqual(performance['accuracy'], 0.5)  # 1 win out of 2
        self.assertEqual(performance['total_profit'], 50.0)  # 100 - 50
        
        print(f"✓ Performance history tracked: accuracy={performance['accuracy']}, profit={performance['total_profit']}")
    
    def test_model_switching_evaluation(self):
        """Test model switching evaluation"""
        print("\n--- Testing Model Switching Evaluation ---")
        
        # Set up for evaluation
        self.compatibility.current_model_id = "eval_test_model"
        self.compatibility.signal_count = 50  # Above minimum threshold
        
        # Mock current performance (poor performance)
        self.compatibility._get_current_model_performance = Mock(return_value={
            'accuracy': 0.6,
            'total_profit': -100.0
        })
        
        # Mock available models (with better performance)
        self.compatibility._get_available_models = Mock(return_value=[
            {
                'model_id': 'better_model',
                'performance_metrics': {'accuracy': 0.8}
            }
        ])
        
        # Mock model switching
        self.compatibility.switch_model_with_learning = Mock(return_value=True)
        
        # Evaluate switching
        self.compatibility._evaluate_performance_based_switching({'accuracy': 0.6})
        
        # Verify switching was attempted
        self.compatibility.switch_model_with_learning.assert_called_once_with(
            'better_model', 'performance_improvement'
        )
        
        print("✓ Model switching evaluation successful")
    
    def test_monitoring_lifecycle(self):
        """Test monitoring thread lifecycle"""
        print("\n--- Testing Monitoring Lifecycle ---")
        
        # Start monitoring
        self.compatibility._start_learning_monitoring()
        
        self.assertTrue(self.compatibility.is_monitoring)
        self.assertIsNotNone(self.compatibility.monitoring_thread)
        self.assertTrue(self.compatibility.monitoring_thread.is_alive())
        
        # Wait briefly for monitoring to run
        time.sleep(0.1)
        
        # Stop monitoring
        self.compatibility._stop_learning_monitoring()
        
        self.assertFalse(self.compatibility.is_monitoring)
        
        print("✓ Monitoring lifecycle test completed")
    
    def test_ai_system_config_updates(self):
        """Test AI system configuration updates"""
        print("\n--- Testing AI System Config Updates ---")
        
        # Mock AI system update method
        self.mock_ai_system.update_config = Mock()
        
        # Update AI system config
        self.compatibility._update_ai_system_config()
        
        # Verify update was called
        self.mock_ai_system.update_config.assert_called_once()
        
        # Check the configuration passed
        call_args = self.mock_ai_system.update_config.call_args[0][0]
        self.assertTrue(call_args['learning_enabled'])
        self.assertEqual(call_args['learning_mode'], LearningMode.ACTIVE.value)
        self.assertTrue(call_args['model_switching_enabled'])
        
        print("✓ AI system configuration updates successful")
    
    def test_hook_callbacks(self):
        """Test hook callback execution"""
        print("\n--- Testing Hook Callbacks ---")
        
        # Install test hooks
        signal_hook = Mock()
        outcome_hook = Mock()
        model_switch_hook = Mock()
        
        self.compatibility.install_signal_generation_hook(signal_hook)
        self.compatibility.install_outcome_tracking_hook(outcome_hook)
        self.compatibility.model_switch_hooks.append(model_switch_hook)
        
        # Mock pipeline integration
        self.compatibility.pipeline_integration = Mock()
        self.compatibility.current_model_id = "hook_test_model"
        
        # Test signal processing with hooks
        signal_data = {
            'signal_id': 'hook_test_001',
            'symbol': 'GBPUSD',
            'signal_type': 'SELL',
            'confidence': 0.8,
            'features': {'rsi': 70}
        }
        
        self.compatibility.process_signal_with_learning(signal_data)
        
        # Verify signal hook was called
        signal_hook.assert_called_once()
        
        # Test outcome processing with hooks
        outcome_data = {
            'signal_id': 'hook_test_001',
            'outcome': 'WIN',
            'profit_loss': 150.0,
            'duration_minutes': 25
        }
        
        self.compatibility.process_outcome_with_learning(outcome_data)
        
        # Verify outcome hook was called
        outcome_hook.assert_called_once()
        
        print("✓ Hook callbacks executed successfully")
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        print("\n--- Testing Error Handling ---")
        
        # Test with None pipeline integration
        self.compatibility.pipeline_integration = None
        
        # Should handle gracefully
        result = self.compatibility.process_signal_with_learning({
            'signal_id': 'error_test',
            'symbol': 'INVALID'
        })
        
        self.assertIsInstance(result, dict)
        
        # Test with invalid configuration updates
        success = self.compatibility.update_learning_configuration({
            'invalid_key': 'invalid_value'
        })
        
        # Should still succeed (ignores invalid keys)
        self.assertTrue(success)
        
        print("✓ Error handling validation passed")
    
    def tearDown(self):
        """Clean up test environment"""
        # Stop monitoring if running
        if self.compatibility.is_monitoring:
            self.compatibility._stop_learning_monitoring()
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestLearningCompatibilityEnums(unittest.TestCase):
    """Test learning compatibility enums"""
    
    def test_learning_mode_enum(self):
        """Test LearningMode enum"""
        print("\n--- Testing LearningMode Enum ---")
        
        self.assertEqual(LearningMode.DISABLED.value, "disabled")
        self.assertEqual(LearningMode.PASSIVE.value, "passive")
        self.assertEqual(LearningMode.ACTIVE.value, "active")
        self.assertEqual(LearningMode.AGGRESSIVE.value, "aggressive")
        
        # Test enum creation from string
        mode = LearningMode("active")
        self.assertEqual(mode, LearningMode.ACTIVE)
        
        print("✓ LearningMode enum validation passed")
    
    def test_model_switch_strategy_enum(self):
        """Test ModelSwitchStrategy enum"""
        print("\n--- Testing ModelSwitchStrategy Enum ---")
        
        self.assertEqual(ModelSwitchStrategy.PERFORMANCE_BASED.value, "performance_based")
        self.assertEqual(ModelSwitchStrategy.TIME_BASED.value, "time_based")
        self.assertEqual(ModelSwitchStrategy.HYBRID.value, "hybrid")
        self.assertEqual(ModelSwitchStrategy.MANUAL.value, "manual")
        
        # Test enum creation from string
        strategy = ModelSwitchStrategy("hybrid")
        self.assertEqual(strategy, ModelSwitchStrategy.HYBRID)
        
        print("✓ ModelSwitchStrategy enum validation passed")


if __name__ == '__main__':
    print("="*60)
    print("AI SYSTEM LEARNING COMPATIBILITY TESTS")
    print("="*60)
    
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*60)
    print("LEARNING COMPATIBILITY TEST SUMMARY")
    print("="*60)
    print("Tests validate AI system updates for learning integration")
    print("including model switching, data collection hooks,")
    print("and configuration management.")
    print("="*60)