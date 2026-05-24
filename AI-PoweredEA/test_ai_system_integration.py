"""
Test suite for AI System Integration
Comprehensive tests for model management integration with AI analysis system
"""

import sys
import os
sys.path.append('Python')

import unittest
import tempfile
import shutil
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

try:
    from ai_system_integration import (
        AISystemIntegration, IntegrationStatus, AISystemConfig,
        ModelSwitchEvent, create_sample_ai_system
    )
    from model_manager import ModelManager, ModelType, ModelStatus
except ImportError:
    from Python.ai_system_integration import (
        AISystemIntegration, IntegrationStatus, AISystemConfig,
        ModelSwitchEvent, create_sample_ai_system
    )
    from Python.model_manager import ModelManager, ModelType, ModelStatus

from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification


class TestAISystemIntegration(unittest.TestCase):
    """Test cases for AI System Integration"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize integration
        self.integration = AISystemIntegration(
            db_path=self.temp_db.name,
            models_directory=os.path.join(self.temp_dir, "models")
        )
        
        # Create sample models
        self.sample_models = self._create_sample_models()
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.temp_dir)
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_sample_models(self):
        """Create sample models for testing"""
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        
        models = {}
        
        # Model 1 - Good performance
        model1 = RandomForestClassifier(n_estimators=10, random_state=42)
        model1.fit(X, y)
        models['model1'] = {
            'model': model1,
            'metrics': {'accuracy': 0.95, 'precision': 0.94, 'recall': 0.96}
        }
        
        # Model 2 - Better performance
        model2 = RandomForestClassifier(n_estimators=15, random_state=43)
        model2.fit(X, y)
        models['model2'] = {
            'model': model2,
            'metrics': {'accuracy': 0.97, 'precision': 0.96, 'recall': 0.98}
        }
        
        return models
    
    def test_initialization(self):
        """Test integration initialization"""
        self.assertIsInstance(self.integration, AISystemIntegration)
        self.assertEqual(self.integration.status, IntegrationStatus.INACTIVE)
        self.assertIsNone(self.integration.current_config)
        
        # Check database tables were created
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'integration_config', 'integration_events', 
            'model_switch_events', 'prediction_logs'
        ]
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    def test_activate_integration(self):
        """Test activating integration with a model"""
        # Save a model first
        model_data = self.sample_models['model1']
        model_version = self.integration.model_manager.save_model(
            model_data['model'], "test_model", ModelType.CLASSIFICATION,
            model_data['metrics'], {"test": True}, "Test model"
        )
        
        # Update status to allow deployment
        self.integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        # Activate integration
        success = self.integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        # Verify activation
        self.assertTrue(success)
        self.assertEqual(self.integration.status, IntegrationStatus.ACTIVE)
        self.assertIsNotNone(self.integration.current_config)
        self.assertEqual(self.integration.current_config.active_model_id, model_version.model_id)
        self.assertEqual(self.integration.current_config.active_version, model_version.version)
    
    def test_get_active_model(self):
        """Test getting the active model"""
        # First activate integration
        model_data = self.sample_models['model1']
        model_version = self.integration.model_manager.save_model(
            model_data['model'], "active_test", ModelType.CLASSIFICATION,
            model_data['metrics']
        )
        
        self.integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        self.integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        # Get active model
        model, version = self.integration.get_active_model()
        
        # Verify model
        self.assertIsNotNone(model)
        self.assertIsNotNone(version)
        self.assertTrue(hasattr(model, 'predict'))
        self.assertIn(model_version.model_id, version)
    
    def test_make_prediction(self):
        """Test making predictions with active model"""
        # Activate integration
        model_data = self.sample_models['model1']
        model_version = self.integration.model_manager.save_model(
            model_data['model'], "prediction_test", ModelType.CLASSIFICATION,
            model_data['metrics']
        )
        
        self.integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        self.integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        # Make prediction
        features = np.random.rand(10)
        result = self.integration.make_prediction(features, "EURUSD")
        
        # Verify prediction result
        self.assertIsNotNone(result)
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('model_version', result)
        self.assertIn('symbol', result)
        self.assertIn('timestamp', result)
        
        self.assertEqual(result['symbol'], "EURUSD")
        self.assertIsInstance(result['prediction'], int)
        self.assertIsInstance(result['confidence'], float)
        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)
    
    def test_model_switching(self):
        """Test model switching functionality"""
        # Save two models
        model1_data = self.sample_models['model1']
        model1_version = self.integration.model_manager.save_model(
            model1_data['model'], "switch_test_1", ModelType.CLASSIFICATION,
            model1_data['metrics']
        )
        
        model2_data = self.sample_models['model2']
        model2_version = self.integration.model_manager.save_model(
            model2_data['model'], "switch_test_2", ModelType.CLASSIFICATION,
            model2_data['metrics']
        )
        
        # Update statuses
        for version in [model1_version, model2_version]:
            self.integration.model_manager._update_model_status(
                version.model_id, version.version, ModelStatus.TESTING
            )
        
        # Activate with first model
        self.integration.activate_integration(
            model1_version.model_id, model1_version.version
        )
        
        # Switch to second model
        success = self.integration.switch_to_model(
            model2_version.model_id, model2_version.version, "Manual test switch"
        )
        
        # Verify switch
        self.assertTrue(success)
        self.assertEqual(self.integration.current_config.active_model_id, model2_version.model_id)
        self.assertEqual(self.integration.current_config.active_version, model2_version.version)
        
        # Verify switch history
        self.assertGreater(len(self.integration.switch_history), 0)
        last_switch = self.integration.switch_history[-1]
        self.assertTrue(last_switch.success)
        self.assertEqual(last_switch.to_model_id, model2_version.model_id)
    
    def test_integration_status(self):
        """Test getting integration status"""
        # Test inactive status
        status = self.integration.get_integration_status()
        self.assertEqual(status['status'], 'inactive')
        self.assertIsNone(status['active_model'])
        
        # Activate integration
        model_data = self.sample_models['model1']
        model_version = self.integration.model_manager.save_model(
            model_data['model'], "status_test", ModelType.CLASSIFICATION,
            model_data['metrics']
        )
        
        self.integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        self.integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        # Test active status
        status = self.integration.get_integration_status()
        self.assertEqual(status['status'], 'active')
        self.assertIsNotNone(status['active_model'])
        self.assertIsNotNone(status['config'])
        self.assertIn('active_model_id', status['config'])
    
    def test_config_update(self):
        """Test updating integration configuration"""
        # Activate integration first
        model_data = self.sample_models['model1']
        model_version = self.integration.model_manager.save_model(
            model_data['model'], "config_test", ModelType.CLASSIFICATION,
            model_data['metrics']
        )
        
        self.integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        self.integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        # Update configuration
        success = self.integration.update_config(
            performance_threshold=0.8,
            auto_switching_enabled=False,
            max_daily_switches=3
        )
        
        # Verify update
        self.assertTrue(success)
        self.assertEqual(self.integration.current_config.performance_threshold, 0.8)
        self.assertFalse(self.integration.current_config.auto_switching_enabled)
        self.assertEqual(self.integration.current_config.max_daily_switches, 3)
    
    def test_deactivate_integration(self):
        """Test deactivating integration"""
        # Activate first
        model_data = self.sample_models['model1']
        model_version = self.integration.model_manager.save_model(
            model_data['model'], "deactivate_test", ModelType.CLASSIFICATION,
            model_data['metrics']
        )
        
        self.integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        self.integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        # Verify active
        self.assertEqual(self.integration.status, IntegrationStatus.ACTIVE)
        
        # Deactivate
        success = self.integration.deactivate_integration()
        
        # Verify deactivation
        self.assertTrue(success)
        self.assertEqual(self.integration.status, IntegrationStatus.INACTIVE)
        self.assertIsNone(self.integration.current_config)
    
    def test_model_validation(self):
        """Test model validation for AI system"""
        # Test valid model
        valid_model = self.sample_models['model1']['model']
        is_valid = self.integration._validate_model_for_ai_system(valid_model)
        self.assertTrue(is_valid)
        
        # Test invalid model (missing predict method)
        invalid_model = Mock()
        del invalid_model.predict  # Remove predict method
        is_valid = self.integration._validate_model_for_ai_system(invalid_model)
        self.assertFalse(is_valid)
    
    def test_cache_functionality(self):
        """Test model caching functionality"""
        # Activate integration
        model_data = self.sample_models['model1']
        model_version = self.integration.model_manager.save_model(
            model_data['model'], "cache_test", ModelType.CLASSIFICATION,
            model_data['metrics']
        )
        
        self.integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        self.integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        # First call should load model
        model1, version1 = self.integration.get_active_model()
        self.assertIsNotNone(model1)
        
        # Second call should use cache
        model2, version2 = self.integration.get_active_model()
        self.assertIs(model1, model2)  # Should be same object from cache
        self.assertEqual(version1, version2)
        
        # Clear cache and verify
        self.integration._clear_model_cache()
        self.assertFalse(self.integration._is_cache_valid())
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test activation with non-existent model
        success = self.integration.activate_integration("non_existent", "1")
        self.assertFalse(success)
        
        # Test prediction without active model
        features = np.random.rand(10)
        result = self.integration.make_prediction(features)
        self.assertIsNone(result)
        
        # Test switching to non-existent model
        success = self.integration.switch_to_model("non_existent", "1", "test")
        self.assertFalse(success)


class TestSampleAISystem(unittest.TestCase):
    """Test the sample AI system implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.integration = AISystemIntegration(
            db_path=self.temp_db.name,
            models_directory=os.path.join(self.temp_dir, "models")
        )
        
        # Create and activate a model
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        model_version = self.integration.model_manager.save_model(
            model, "ai_system_test", ModelType.CLASSIFICATION,
            {'accuracy': 0.95}
        )
        
        self.integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        self.integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        # Create sample AI system
        SampleAISystem = create_sample_ai_system()
        self.ai_system = SampleAISystem(self.integration)
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.temp_dir)
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_market_analysis(self):
        """Test market analysis functionality"""
        # Sample market data
        market_data = {
            'open': 1.1234,
            'high': 1.1250,
            'low': 1.1220,
            'close': 1.1245,
            'volume': 1000000,
            'rsi': 65.5,
            'macd': 0.0012,
            'bb_upper': 1.1260,
            'bb_lower': 1.1210,
            'sma_20': 1.1235
        }
        
        # Analyze market
        result = self.ai_system.analyze_market("EURUSD", market_data)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertIn('symbol', result)
        self.assertIn('signal', result)
        self.assertIn('confidence', result)
        self.assertIn('model_version', result)
        self.assertIn('timestamp', result)
        
        self.assertEqual(result['symbol'], "EURUSD")
        self.assertIn(result['signal'], ['BUY', 'SELL', 'HOLD'])
        self.assertIsInstance(result['confidence'], float)
    
    def test_model_update_check(self):
        """Test model update checking"""
        # This should return False since we don't have performance degradation
        result = self.ai_system.check_and_update_models()
        
        # The result depends on the current model performance
        # It should be a boolean
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)