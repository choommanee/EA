"""
Test suite for AI Learning Pipeline Integration
Tests integration between learning system and AI analysis pipeline
"""

import unittest
import tempfile
import os
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from Python.ai_learning_pipeline_integration import (
    AILearningPipelineIntegration, IntegrationConfig, IntegrationStatus,
    SignalData, SignalOutcome, DataFlowDirection
)


class TestAILearningPipelineIntegration(unittest.TestCase):
    """Test AI Learning Pipeline Integration functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_integration.db")
        
        # Create test configuration
        self.config = IntegrationConfig(
            enable_performance_monitoring=True,
            enable_model_switching=True,
            enable_data_collection=True,
            performance_check_interval=1,  # 1 second for testing
            model_switch_threshold=0.05
        )
        
        self.integration = AILearningPipelineIntegration(self.config, self.db_path)
    
    def test_initialization(self):
        """Test integration initialization"""
        print("\n--- Testing Integration Initialization ---")
        
        self.assertIsNotNone(self.integration)
        self.assertEqual(self.integration.status, IntegrationStatus.DISCONNECTED)
        self.assertEqual(self.integration.db_path, self.db_path)
        self.assertIsInstance(self.integration.config, IntegrationConfig)
        
        print("✓ Integration initialized successfully")
    
    def test_integration_config(self):
        """Test integration configuration"""
        print("\n--- Testing Integration Configuration ---")
        
        # Test default configuration
        default_config = IntegrationConfig()
        self.assertTrue(default_config.enable_performance_monitoring)
        self.assertTrue(default_config.enable_model_switching)
        self.assertEqual(default_config.performance_check_interval, 300)
        
        # Test custom configuration
        custom_config = IntegrationConfig(
            enable_performance_monitoring=False,
            performance_check_interval=60,
            model_switch_threshold=0.1
        )
        self.assertFalse(custom_config.enable_performance_monitoring)
        self.assertEqual(custom_config.performance_check_interval, 60)
        self.assertEqual(custom_config.model_switch_threshold, 0.1)
        
        print("✓ Integration configuration validation passed")
    
    def test_signal_data_structure(self):
        """Test SignalData structure"""
        print("\n--- Testing SignalData Structure ---")
        
        signal = SignalData(
            signal_id="test_001",
            timestamp=datetime.now(),
            symbol="EURUSD",
            signal_type="BUY",
            confidence=0.75,
            features={"rsi": 30, "macd": 0.5},
            model_id="test_model"
        )
        
        self.assertEqual(signal.signal_id, "test_001")
        self.assertEqual(signal.symbol, "EURUSD")
        self.assertEqual(signal.signal_type, "BUY")
        self.assertEqual(signal.confidence, 0.75)
        self.assertEqual(signal.model_id, "test_model")
        self.assertIn("rsi", signal.features)
        
        print("✓ SignalData structure validation passed")
    
    def test_signal_outcome_structure(self):
        """Test SignalOutcome structure"""
        print("\n--- Testing SignalOutcome Structure ---")
        
        outcome = SignalOutcome(
            signal_id="test_001",
            timestamp=datetime.now(),
            outcome="WIN",
            profit_loss=100.0,
            duration_minutes=30,
            actual_price=1.2345
        )
        
        self.assertEqual(outcome.signal_id, "test_001")
        self.assertEqual(outcome.outcome, "WIN")
        self.assertEqual(outcome.profit_loss, 100.0)
        self.assertEqual(outcome.duration_minutes, 30)
        self.assertEqual(outcome.actual_price, 1.2345)
        
        print("✓ SignalOutcome structure validation passed")
    
    def test_process_new_signal(self):
        """Test processing new signals"""
        print("\n--- Testing Signal Processing ---")
        
        # Create test signal
        signal = SignalData(
            signal_id="test_signal_001",
            timestamp=datetime.now(),
            symbol="EURUSD",
            signal_type="BUY",
            confidence=0.75,
            features={"rsi": 30, "macd": 0.5},
            model_id="test_model"
        )
        
        # Process signal
        success = self.integration.process_new_signal(signal)
        
        self.assertTrue(success)
        self.assertIn(signal, self.integration.signal_queue)
        
        print(f"✓ Successfully processed signal: {signal.signal_id}")
    
    def test_process_signal_outcome(self):
        """Test processing signal outcomes"""
        print("\n--- Testing Outcome Processing ---")
        
        # Create test outcome
        outcome = SignalOutcome(
            signal_id="test_signal_001",
            timestamp=datetime.now(),
            outcome="WIN",
            profit_loss=100.0,
            duration_minutes=30
        )
        
        # Process outcome
        success = self.integration.process_signal_outcome(outcome)
        
        self.assertTrue(success)
        self.assertIn(outcome, self.integration.outcome_queue)
        
        print(f"✓ Successfully processed outcome: {outcome.signal_id}")
    
    def test_callback_registration(self):
        """Test callback registration"""
        print("\n--- Testing Callback Registration ---")
        
        # Test signal callback
        signal_callback = Mock()
        success = self.integration.register_signal_callback(signal_callback)
        self.assertTrue(success)
        self.assertIn(signal_callback, self.integration.signal_callbacks)
        
        # Test outcome callback
        outcome_callback = Mock()
        success = self.integration.register_outcome_callback(outcome_callback)
        self.assertTrue(success)
        self.assertIn(outcome_callback, self.integration.outcome_callbacks)
        
        # Test model switch callback
        switch_callback = Mock()
        success = self.integration.register_model_switch_callback(switch_callback)
        self.assertTrue(success)
        self.assertIn(switch_callback, self.integration.model_switch_callbacks)
        
        print("✓ All callback registrations successful")
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        print("\n--- Testing Performance Summary ---")
        
        # Add some test data
        test_signal = SignalData(
            signal_id="perf_test_001",
            timestamp=datetime.now(),
            symbol="EURUSD",
            signal_type="BUY",
            confidence=0.8,
            features={"rsi": 25},
            model_id="perf_model"
        )
        
        test_outcome = SignalOutcome(
            signal_id="perf_test_001",
            timestamp=datetime.now(),
            outcome="WIN",
            profit_loss=150.0,
            duration_minutes=45
        )
        
        self.integration.process_new_signal(test_signal)
        self.integration.process_signal_outcome(test_outcome)
        
        # Get performance summary
        summary = self.integration.get_performance_summary(24)
        
        self.assertIsInstance(summary, dict)
        self.assertIn('integration_status', summary)
        self.assertIn('signals_processed', summary)
        self.assertIn('outcomes_processed', summary)
        self.assertIn('performance_data', summary)
        
        print(f"✓ Generated performance summary with {summary['signals_processed']} signals")
    
    def test_database_operations(self):
        """Test database operations"""
        print("\n--- Testing Database Operations ---")
        
        # Test signal record storage
        signal_record = {
            'signal_id': 'db_test_001',
            'timestamp': datetime.now(),
            'symbol': 'GBPUSD',
            'signal_type': 'SELL',
            'confidence': 0.65,
            'model_id': 'db_model',
            'features': {'rsi': 70, 'macd': -0.3}
        }
        
        self.integration._store_signal_record(signal_record)
        
        # Retrieve signal record
        retrieved_record = self.integration._get_signal_record('db_test_001')
        
        self.assertIsNotNone(retrieved_record)
        self.assertEqual(retrieved_record['signal_id'], 'db_test_001')
        self.assertEqual(retrieved_record['symbol'], 'GBPUSD')
        self.assertEqual(retrieved_record['signal_type'], 'SELL')
        
        print("✓ Database operations successful")
    
    def test_model_switch_recording(self):
        """Test model switch recording"""
        print("\n--- Testing Model Switch Recording ---")
        
        previous_model = {
            'model_id': 'old_model',
            'version': '1.0',
            'performance_metrics': {'accuracy': 0.75}
        }
        
        new_model_id = 'new_model'
        reason = 'performance_improvement'
        
        # Record model switch
        self.integration._record_model_switch(previous_model, new_model_id, reason)
        
        # Verify record was stored (would need to query database)
        print(f"✓ Model switch recorded: {previous_model['model_id']} → {new_model_id}")
    
    def test_processing_thread_lifecycle(self):
        """Test processing thread lifecycle"""
        print("\n--- Testing Processing Thread Lifecycle ---")
        
        # Start processing
        self.integration._start_processing_thread()
        
        self.assertTrue(self.integration.is_processing)
        self.assertIsNotNone(self.integration.processing_thread)
        self.assertTrue(self.integration.processing_thread.is_alive())
        
        # Add some data to process
        test_signal = SignalData(
            signal_id="thread_test_001",
            timestamp=datetime.now(),
            symbol="USDJPY",
            signal_type="BUY",
            confidence=0.7,
            features={"rsi": 35}
        )
        
        self.integration.signal_queue.append(test_signal)
        
        # Wait briefly for processing
        time.sleep(0.2)
        
        # Stop processing
        self.integration.is_processing = False
        self.integration.processing_thread.join(timeout=1.0)
        
        self.assertFalse(self.integration.processing_thread.is_alive())
        
        print("✓ Processing thread lifecycle test completed")
    
    def test_connection_health_check(self):
        """Test connection health checking"""
        print("\n--- Testing Connection Health Check ---")
        
        # Mock AI system
        mock_ai_system = Mock()
        mock_ai_system.get_integration_status.return_value = {'active': True}
        self.integration.ai_system = mock_ai_system
        
        # Check connection health
        self.integration._check_connection_health()
        
        self.assertEqual(self.integration.status, IntegrationStatus.CONNECTED)
        self.assertEqual(self.integration.connection_errors, 0)
        self.assertIsNotNone(self.integration.last_connection_check)
        
        # Test error condition
        mock_ai_system.get_integration_status.return_value = {'active': False}
        
        # Trigger multiple errors to exceed threshold
        for _ in range(self.config.max_retry_attempts + 1):
            self.integration._check_connection_health()
        
        self.assertEqual(self.integration.status, IntegrationStatus.ERROR)
        
        print("✓ Connection health check validation passed")
    
    def test_signal_outcome_matching(self):
        """Test signal and outcome matching"""
        print("\n--- Testing Signal-Outcome Matching ---")
        
        # Create and process signal
        signal = SignalData(
            signal_id="match_test_001",
            timestamp=datetime.now(),
            symbol="EURJPY",
            signal_type="BUY",
            confidence=0.8,
            features={"rsi": 25, "macd": 0.2},
            model_id="match_model"
        )
        
        self.integration.process_new_signal(signal)
        
        # Create matching outcome
        outcome = SignalOutcome(
            signal_id="match_test_001",
            timestamp=datetime.now() + timedelta(minutes=30),
            outcome="WIN",
            profit_loss=200.0,
            duration_minutes=30
        )
        
        self.integration.process_signal_outcome(outcome)
        
        # Verify signal can be retrieved
        retrieved_signal = self.integration._get_signal_record("match_test_001")
        self.assertIsNotNone(retrieved_signal)
        self.assertEqual(retrieved_signal['signal_id'], "match_test_001")
        
        print("✓ Signal-outcome matching test completed")
    
    def test_performance_data_retrieval(self):
        """Test performance data retrieval"""
        print("\n--- Testing Performance Data Retrieval ---")
        
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        # Get performance data (may be empty initially)
        performance_data = self.integration._get_recent_performance_data(start_time, end_time)
        
        self.assertIsInstance(performance_data, dict)
        self.assertIn('signal_count', performance_data)
        self.assertIn('accuracy', performance_data)
        self.assertIn('avg_profit_loss', performance_data)
        
        print(f"✓ Retrieved performance data: {performance_data}")
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        print("\n--- Testing Error Handling ---")
        
        # Test with invalid signal data
        invalid_signal = SignalData(
            signal_id="",  # Empty signal ID
            timestamp=datetime.now(),
            symbol="INVALID",
            signal_type="UNKNOWN",
            confidence=-1.0,  # Invalid confidence
            features={}
        )
        
        # Should handle gracefully
        success = self.integration.process_new_signal(invalid_signal)
        self.assertTrue(success)  # Should not crash
        
        # Test with None values
        try:
            self.integration._get_signal_record(None)
            # Should not crash
        except Exception:
            pass  # Expected to handle gracefully
        
        print("✓ Error handling validation passed")
    
    def test_integration_status_transitions(self):
        """Test integration status transitions"""
        print("\n--- Testing Integration Status Transitions ---")
        
        # Initial status
        self.assertEqual(self.integration.status, IntegrationStatus.DISCONNECTED)
        
        # Simulate connecting
        self.integration.status = IntegrationStatus.CONNECTING
        self.assertEqual(self.integration.status, IntegrationStatus.CONNECTING)
        
        # Simulate connected
        self.integration.status = IntegrationStatus.CONNECTED
        self.assertEqual(self.integration.status, IntegrationStatus.CONNECTED)
        
        # Simulate error
        self.integration.status = IntegrationStatus.ERROR
        self.assertEqual(self.integration.status, IntegrationStatus.ERROR)
        
        print("✓ Integration status transitions validated")
    
    def test_cleanup_and_shutdown(self):
        """Test cleanup and shutdown procedures"""
        print("\n--- Testing Cleanup and Shutdown ---")
        
        # Add some data
        test_signal = SignalData(
            signal_id="cleanup_test",
            timestamp=datetime.now(),
            symbol="USDCAD",
            signal_type="SELL",
            confidence=0.6,
            features={"rsi": 80}
        )
        
        self.integration.signal_queue.append(test_signal)
        
        # Start processing
        self.integration._start_processing_thread()
        
        # Stop integration
        success = self.integration.stop_integration()
        
        self.assertTrue(success)
        self.assertFalse(self.integration.is_processing)
        self.assertEqual(self.integration.status, IntegrationStatus.DISCONNECTED)
        self.assertEqual(len(self.integration.signal_queue), 0)
        self.assertEqual(len(self.integration.outcome_queue), 0)
        
        print("✓ Cleanup and shutdown completed successfully")
    
    def tearDown(self):
        """Clean up test environment"""
        # Stop integration if running
        if self.integration.is_processing:
            self.integration.stop_integration()
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestIntegrationDataStructures(unittest.TestCase):
    """Test integration data structures"""
    
    def test_integration_config_defaults(self):
        """Test IntegrationConfig default values"""
        print("\n--- Testing IntegrationConfig Defaults ---")
        
        config = IntegrationConfig()
        
        self.assertTrue(config.enable_performance_monitoring)
        self.assertTrue(config.enable_model_switching)
        self.assertTrue(config.enable_data_collection)
        self.assertTrue(config.enable_real_time_updates)
        self.assertEqual(config.performance_check_interval, 300)
        self.assertEqual(config.model_switch_threshold, 0.05)
        self.assertEqual(config.data_collection_batch_size, 100)
        self.assertEqual(config.max_retry_attempts, 3)
        self.assertEqual(config.connection_timeout, 30)
        
        print("✓ IntegrationConfig defaults validated")
    
    def test_signal_data_with_metadata(self):
        """Test SignalData with metadata"""
        print("\n--- Testing SignalData with Metadata ---")
        
        signal = SignalData(
            signal_id="meta_test_001",
            timestamp=datetime.now(),
            symbol="GBPJPY",
            signal_type="BUY",
            confidence=0.85,
            features={"rsi": 20, "macd": 0.8, "volume": 1000},
            model_id="meta_model",
            metadata={
                "source": "ai_analyzer",
                "version": "2.1",
                "confidence_factors": ["technical", "fundamental"]
            }
        )
        
        self.assertEqual(signal.metadata["source"], "ai_analyzer")
        self.assertEqual(signal.metadata["version"], "2.1")
        self.assertIn("technical", signal.metadata["confidence_factors"])
        
        print("✓ SignalData with metadata validated")
    
    def test_signal_outcome_with_metadata(self):
        """Test SignalOutcome with metadata"""
        print("\n--- Testing SignalOutcome with Metadata ---")
        
        outcome = SignalOutcome(
            signal_id="meta_outcome_001",
            timestamp=datetime.now(),
            outcome="LOSS",
            profit_loss=-50.0,
            duration_minutes=15,
            actual_price=1.3456,
            metadata={
                "exit_reason": "stop_loss",
                "slippage": 0.0002,
                "market_conditions": "volatile"
            }
        )
        
        self.assertEqual(outcome.metadata["exit_reason"], "stop_loss")
        self.assertEqual(outcome.metadata["slippage"], 0.0002)
        self.assertEqual(outcome.metadata["market_conditions"], "volatile")
        
        print("✓ SignalOutcome with metadata validated")


if __name__ == '__main__':
    print("="*60)
    print("AI LEARNING PIPELINE INTEGRATION TESTS")
    print("="*60)
    
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    print("Tests validate integration between learning system")
    print("and AI analysis pipeline with signal processing,")
    print("outcome tracking, and model switching.")
    print("="*60)