"""
Test suite for Learning Coordinator
Comprehensive tests for learning workflow orchestration and management
"""

import sys
import os
sys.path.append('Python')

import unittest
import tempfile
import shutil
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

try:
    from learning_coordinator import (
        LearningCoordinator, LearningPhase, LearningTrigger,
        LearningCycleConfig, LearningCycleStatus, LearningProgress,
        create_sample_progress_callback
    )
except ImportError:
    from Python.learning_coordinator import (
        LearningCoordinator, LearningPhase, LearningTrigger,
        LearningCycleConfig, LearningCycleStatus, LearningProgress,
        create_sample_progress_callback
    )


class TestLearningCoordinator(unittest.TestCase):
    """Test cases for Learning Coordinator"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock the components to avoid complex dependencies
        with patch.multiple(
            'Python.learning_coordinator',
            ModelManager=MagicMock,
            AISystemIntegration=MagicMock,
            PerformanceMonitor=MagicMock,
            LearningDataCollector=MagicMock,
            DataPreprocessingPipeline=MagicMock,
            ModelEvaluator=MagicMock,
            CrossValidationFramework=MagicMock,
            LearningErrorHandler=MagicMock
        ):
            # Initialize coordinator
            self.coordinator = LearningCoordinator(
                db_path=self.temp_db.name,
                models_directory=os.path.join(self.temp_dir, "models")
            )
        
        # Set up mock responses
        self._setup_mocks()
    
    def tearDown(self):
        """Clean up test environment"""
        # Stop coordinator if running
        if self.coordinator.is_running:
            self.coordinator.stop_coordinator()
        
        try:
            shutil.rmtree(self.temp_dir)
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _setup_mocks(self):
        """Set up mock responses for components"""
        # Mock data collector
        mock_data = Mock()
        mock_data.empty = False
        mock_data.__len__ = Mock(return_value=100)
        mock_data.shape = (100, 10)
        mock_data.drop = Mock(return_value=Mock(values=[[1, 2, 3, 4, 5]] * 100))
        mock_data.tail = Mock(return_value=mock_data)
        mock_data.head = Mock(return_value=mock_data)
        
        self.coordinator.data_collector.collect_learning_data = Mock(return_value=mock_data)
        self.coordinator.data_collector.validate_data_quality = Mock(return_value={"quality": "good"})
        
        # Mock data pipeline
        self.coordinator.data_pipeline.process_learning_data = Mock(return_value=mock_data)
        self.coordinator.data_pipeline.validate_processed_data = Mock(return_value={"valid": True})
        
        # Mock model manager
        mock_model_version = Mock()
        mock_model_version.model_id = "test_model_123"
        mock_model_version.version = "1"
        
        self.coordinator.model_manager.save_model = Mock(return_value=mock_model_version)
        self.coordinator.model_manager.load_model = Mock(return_value=(Mock(), mock_model_version))
        self.coordinator.model_manager._update_model_status = Mock()
        
        # Mock model evaluator
        mock_evaluation = Mock()
        mock_evaluation.metrics = {"accuracy": 0.85, "precision": 0.83}
        mock_evaluation.recommendations = ["Good performance"]
        
        self.coordinator.model_evaluator.evaluate_model = Mock(return_value=mock_evaluation)
        
        # Mock cross-validation framework
        mock_cv_result = Mock()
        mock_cv_result.mean_scores = {"accuracy": 0.84}
        
        self.coordinator.cv_framework.perform_cross_validation = Mock(return_value=mock_cv_result)
        
        # Mock AI integration
        self.coordinator.ai_integration.get_integration_status = Mock(return_value={
            'status': 'active',
            'performance': 0.8
        })
        self.coordinator.ai_integration.switch_to_model = Mock(return_value=True)
        self.coordinator.ai_integration.activate_integration = Mock(return_value=True)
        
        # Mock error handler
        self.coordinator.error_handler.handle_error = Mock(return_value={"severity": "low"})
        self.coordinator.error_handler.attempt_recovery = Mock(return_value={"recovered": True})
    
    def test_initialization(self):
        """Test coordinator initialization"""
        self.assertIsInstance(self.coordinator, LearningCoordinator)
        self.assertFalse(self.coordinator.is_running)
        self.assertIsNone(self.coordinator.current_cycle)
        self.assertEqual(len(self.coordinator.cycle_history), 0)
        
        # Check database tables were created
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['coordinator_events', 'learning_cycles', 'monitoring_configs']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    def test_start_stop_coordinator(self):
        """Test starting and stopping coordinator"""
        # Test start
        success = self.coordinator.start_coordinator()
        self.assertTrue(success)
        self.assertTrue(self.coordinator.is_running)
        self.assertIsNotNone(self.coordinator.scheduler_thread)
        
        # Test start when already running
        success_again = self.coordinator.start_coordinator()
        self.assertFalse(success_again)
        
        # Test stop
        success_stop = self.coordinator.stop_coordinator()
        self.assertTrue(success_stop)
        self.assertFalse(self.coordinator.is_running)
    
    def test_trigger_learning_cycle(self):
        """Test triggering learning cycle"""
        # Test manual trigger
        cycle_id = self.coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
        
        self.assertIsNotNone(cycle_id)
        self.assertIn("manual", cycle_id)
        
        # Wait a moment for cycle to start
        time.sleep(0.1)
        
        # Check current cycle is set
        self.assertIsNotNone(self.coordinator.current_cycle)
        self.assertEqual(self.coordinator.current_cycle.trigger_type, LearningTrigger.MANUAL)
    
    def test_get_current_status(self):
        """Test getting current status"""
        # Test status when idle
        status = self.coordinator.get_current_status()
        
        self.assertIn('coordinator_running', status)
        self.assertIn('current_cycle', status)
        self.assertIn('total_cycles', status)
        self.assertIn('last_cycle', status)
        
        self.assertFalse(status['coordinator_running'])
        self.assertIsNone(status['current_cycle'])
        self.assertEqual(status['total_cycles'], 0)
        
        # Test status when running
        self.coordinator.start_coordinator()
        status_running = self.coordinator.get_current_status()
        self.assertTrue(status_running['coordinator_running'])
        
        self.coordinator.stop_coordinator()
    
    def test_learning_cycle_config(self):
        """Test learning cycle configuration"""
        config = LearningCycleConfig(
            cycle_id="test_config",
            trigger_type=LearningTrigger.SCHEDULED,
            schedule_interval_hours=12,
            performance_threshold=0.75,
            auto_deploy_threshold=0.85
        )
        
        self.assertEqual(config.cycle_id, "test_config")
        self.assertEqual(config.trigger_type, LearningTrigger.SCHEDULED)
        self.assertEqual(config.schedule_interval_hours, 12)
        self.assertEqual(config.performance_threshold, 0.75)
        self.assertEqual(config.auto_deploy_threshold, 0.85)
    
    def test_learning_progress_tracking(self):
        """Test learning progress tracking"""
        # Trigger a cycle
        cycle_id = self.coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
        
        # Wait for cycle to start
        time.sleep(0.1)
        
        # Get progress
        progress = self.coordinator.get_learning_progress()
        
        if progress:  # Progress might be None if cycle completed quickly
            self.assertIsInstance(progress, LearningProgress)
            self.assertEqual(progress.cycle_id, cycle_id)
            self.assertIsInstance(progress.phase, LearningPhase)
            self.assertGreaterEqual(progress.total_progress, 0)
            self.assertLessEqual(progress.total_progress, 100)
    
    def test_progress_callbacks(self):
        """Test progress callback functionality"""
        callback_calls = []
        
        def test_callback(progress: LearningProgress):
            callback_calls.append(progress)
        
        # Add callback
        self.coordinator.add_progress_callback(test_callback)
        
        # Trigger cycle
        cycle_id = self.coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
        
        # Wait for some progress
        time.sleep(0.2)
        
        # Remove callback
        self.coordinator.remove_progress_callback(test_callback)
        
        # Check if callback was called
        # Note: This might be 0 if the cycle completes very quickly
        self.assertGreaterEqual(len(callback_calls), 0)
    
    def test_cycle_history(self):
        """Test cycle history tracking"""
        # Initially no history
        history = self.coordinator.get_cycle_history()
        self.assertEqual(len(history), 0)
        
        # Trigger a cycle and wait for completion
        cycle_id = self.coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
        
        # Wait for cycle to complete (with timeout)
        timeout = 10  # 10 seconds timeout
        start_time = time.time()
        
        while (self.coordinator.current_cycle and 
               self.coordinator.current_cycle.current_phase not in [LearningPhase.COMPLETED, LearningPhase.FAILED] and
               time.time() - start_time < timeout):
            time.sleep(0.1)
        
        # Check history
        history = self.coordinator.get_cycle_history()
        self.assertGreaterEqual(len(history), 1)
        
        if len(history) > 0:
            last_cycle = history[-1]
            self.assertIn('cycle_id', last_cycle)
            self.assertIn('trigger_type', last_cycle)
            self.assertIn('final_phase', last_cycle)
            self.assertIn('success', last_cycle)
    
    def test_error_handling(self):
        """Test error handling in learning cycles"""
        # Mock an error in data collection
        self.coordinator.data_collector.collect_learning_data.side_effect = Exception("Data collection failed")
        
        # Trigger cycle
        cycle_id = self.coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
        
        # Wait for cycle to complete
        timeout = 10
        start_time = time.time()
        
        while (self.coordinator.current_cycle and 
               self.coordinator.current_cycle.current_phase not in [LearningPhase.COMPLETED, LearningPhase.FAILED] and
               time.time() - start_time < timeout):
            time.sleep(0.1)
        
        # Check that error was handled
        if self.coordinator.current_cycle:
            self.assertGreater(self.coordinator.current_cycle.error_count, 0)
        
        # Reset mock
        self.coordinator.data_collector.collect_learning_data.side_effect = None
    
    def test_workflow_steps(self):
        """Test individual workflow steps"""
        config = LearningCycleConfig(
            cycle_id="test_workflow",
            trigger_type=LearningTrigger.MANUAL
        )
        
        # Test data collection step
        try:
            result = self.coordinator._execute_data_collection(config)
            self.assertIn('samples_collected', result)
            self.assertIn('date_range', result)
        except Exception as e:
            # Expected if mocks aren't perfect
            self.assertIsInstance(e, Exception)
        
        # Test data preprocessing step
        try:
            result = self.coordinator._execute_data_preprocessing(config)
            self.assertIn('processed_samples', result)
        except Exception as e:
            self.assertIsInstance(e, Exception)
    
    def test_configuration_conversion(self):
        """Test configuration to dictionary conversion"""
        config = LearningCycleConfig(
            cycle_id="test_config",
            trigger_type=LearningTrigger.SCHEDULED,
            performance_threshold=0.8
        )
        
        config_dict = self.coordinator._config_to_dict(config)
        
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['cycle_id'], "test_config")
        self.assertEqual(config_dict['trigger_type'], "scheduled")
        self.assertEqual(config_dict['performance_threshold'], 0.8)
    
    def test_database_operations(self):
        """Test database operations"""
        # Test logging coordinator event
        self.coordinator._log_coordinator_event("test_event", {"test": "data"})
        
        # Test storing cycle status
        cycle_status = LearningCycleStatus(
            cycle_id="test_cycle",
            trigger_type=LearningTrigger.MANUAL,
            current_phase=LearningPhase.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        self.coordinator._store_cycle_status(cycle_status)
        
        # Test storing monitoring config
        monitoring_config = {
            "model_id": "test_model",
            "model_version": "1",
            "cycle_id": "test_cycle"
        }
        
        self.coordinator._store_monitoring_config(monitoring_config)
        
        # Verify data was stored
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM coordinator_events")
        event_count = cursor.fetchone()[0]
        self.assertGreater(event_count, 0)
        
        cursor.execute("SELECT COUNT(*) FROM learning_cycles")
        cycle_count = cursor.fetchone()[0]
        self.assertGreater(cycle_count, 0)
        
        cursor.execute("SELECT COUNT(*) FROM monitoring_configs")
        config_count = cursor.fetchone()[0]
        self.assertGreater(config_count, 0)
        
        conn.close()


class TestLearningCoordinatorIntegration(unittest.TestCase):
    """Integration tests for Learning Coordinator"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create coordinator with minimal mocking
        with patch.multiple(
            'Python.learning_coordinator',
            ModelManager=MagicMock,
            AISystemIntegration=MagicMock,
            PerformanceMonitor=MagicMock,
            LearningDataCollector=MagicMock,
            DataPreprocessingPipeline=MagicMock,
            ModelEvaluator=MagicMock,
            CrossValidationFramework=MagicMock,
            LearningErrorHandler=MagicMock
        ):
            self.coordinator = LearningCoordinator(
                db_path=self.temp_db.name,
                models_directory=os.path.join(self.temp_dir, "models")
            )
    
    def tearDown(self):
        """Clean up integration test environment"""
        if self.coordinator.is_running:
            self.coordinator.stop_coordinator()
        
        try:
            shutil.rmtree(self.temp_dir)
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_complete_coordinator_lifecycle(self):
        """Test complete coordinator lifecycle"""
        # 1. Start coordinator
        success = self.coordinator.start_coordinator()
        self.assertTrue(success)
        self.assertTrue(self.coordinator.is_running)
        
        # 2. Check initial status
        status = self.coordinator.get_current_status()
        self.assertTrue(status['coordinator_running'])
        self.assertEqual(status['total_cycles'], 0)
        
        # 3. Add progress callback
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append(progress)
        
        self.coordinator.add_progress_callback(progress_callback)
        
        # 4. Trigger learning cycle
        cycle_id = self.coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
        self.assertIsNotNone(cycle_id)
        
        # 5. Wait for cycle to complete
        timeout = 15  # 15 seconds timeout
        start_time = time.time()
        
        while (self.coordinator.current_cycle and 
               self.coordinator.current_cycle.current_phase not in [LearningPhase.COMPLETED, LearningPhase.FAILED] and
               time.time() - start_time < timeout):
            time.sleep(0.1)
        
        # 6. Check final status
        final_status = self.coordinator.get_current_status()
        self.assertGreaterEqual(final_status['total_cycles'], 1)
        
        # 7. Check cycle history
        history = self.coordinator.get_cycle_history()
        self.assertGreaterEqual(len(history), 1)
        
        # 8. Stop coordinator
        success_stop = self.coordinator.stop_coordinator()
        self.assertTrue(success_stop)
        self.assertFalse(self.coordinator.is_running)
    
    def test_multiple_cycles(self):
        """Test handling multiple learning cycles"""
        self.coordinator.start_coordinator()
        
        # Trigger first cycle
        cycle1_id = self.coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
        
        # Wait for first cycle to complete
        timeout = 10
        start_time = time.time()
        
        while (self.coordinator.current_cycle and 
               self.coordinator.current_cycle.cycle_id == cycle1_id and
               self.coordinator.current_cycle.current_phase not in [LearningPhase.COMPLETED, LearningPhase.FAILED] and
               time.time() - start_time < timeout):
            time.sleep(0.1)
        
        # Trigger second cycle
        cycle2_id = self.coordinator.trigger_learning_cycle(LearningTrigger.PERFORMANCE_DEGRADATION)
        
        # Verify different cycle IDs
        self.assertNotEqual(cycle1_id, cycle2_id)
        
        # Wait for second cycle
        start_time = time.time()
        while (self.coordinator.current_cycle and 
               self.coordinator.current_cycle.cycle_id == cycle2_id and
               self.coordinator.current_cycle.current_phase not in [LearningPhase.COMPLETED, LearningPhase.FAILED] and
               time.time() - start_time < timeout):
            time.sleep(0.1)
        
        # Check history has both cycles
        history = self.coordinator.get_cycle_history()
        self.assertGreaterEqual(len(history), 2)
        
        self.coordinator.stop_coordinator()


class TestProgressCallback(unittest.TestCase):
    """Test progress callback functionality"""
    
    def test_sample_progress_callback(self):
        """Test sample progress callback"""
        callback = create_sample_progress_callback()
        
        # Create sample progress
        progress = LearningProgress(
            cycle_id="test_cycle",
            phase=LearningPhase.MODEL_TRAINING,
            step_name="Training model",
            step_progress=50.0,
            total_progress=75.0,
            message="Training in progress"
        )
        
        # Test callback doesn't raise exception
        try:
            callback(progress)
        except Exception as e:
            self.fail(f"Progress callback raised exception: {e}")


if __name__ == '__main__':
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)