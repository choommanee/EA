"""
Test suite for Model Manager
Comprehensive tests for model versioning, deployment, and lifecycle management
"""

import sys
import os
sys.path.append('Python')

import unittest
import tempfile
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import pickle
import json

try:
    from model_manager import (
        ModelManager, ModelVersion, ModelDeployment, ModelHistory,
        ModelStatus, ModelType
    )
except ImportError:
    from Python.model_manager import (
        ModelManager, ModelVersion, ModelDeployment, ModelHistory,
        ModelStatus, ModelType
    )

from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification


class TestModelManager(unittest.TestCase):
    """Test cases for ModelManager"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize model manager
        self.model_manager = ModelManager(
            db_path=self.temp_db.name,
            models_directory=os.path.join(self.temp_dir, "models")
        )
        
        # Create sample model and data
        self.sample_model, self.sample_metrics = self._create_sample_model()
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.temp_dir)
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_sample_model(self):
        """Create sample model for testing"""
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        metrics = {
            "accuracy": 0.95,
            "precision": 0.94,
            "recall": 0.96,
            "f1_score": 0.95
        }
        
        return model, metrics
    
    def test_initialization(self):
        """Test model manager initialization"""
        self.assertIsInstance(self.model_manager, ModelManager)
        self.assertTrue(Path(self.model_manager.models_directory).exists())
        
        # Check database tables were created
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['model_versions', 'model_deployments', 'model_history']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    def test_save_model(self):
        """Test saving a model"""
        model_version = self.model_manager.save_model(
            self.sample_model,
            "test_classifier",
            ModelType.CLASSIFICATION,
            self.sample_metrics,
            {"algorithm": "RandomForest"},
            "Test classification model",
            ["test", "classification"]
        )
        
        # Verify model version structure
        self.assertIsInstance(model_version, ModelVersion)
        self.assertEqual(model_version.model_name, "test_classifier")
        self.assertEqual(model_version.model_type, ModelType.CLASSIFICATION)
        self.assertEqual(model_version.status, ModelStatus.DEVELOPMENT)
        self.assertEqual(model_version.performance_metrics, self.sample_metrics)
        self.assertEqual(model_version.description, "Test classification model")
        self.assertEqual(model_version.tags, ["test", "classification"])
        
        # Verify file was created
        self.assertTrue(Path(model_version.file_path).exists())
        
        # Verify file size and hash
        self.assertGreater(model_version.file_size, 0)
        self.assertIsNotNone(model_version.file_hash)
        
        # Verify database entry
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM model_versions WHERE model_id = ?', 
                      (model_version.model_id,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        conn.close()
    
    def test_load_model(self):
        """Test loading a model"""
        # Save model first
        model_version = self.model_manager.save_model(
            self.sample_model, "test_load", ModelType.CLASSIFICATION, self.sample_metrics
        )
        
        # Load model
        loaded_model, loaded_version = self.model_manager.load_model(
            model_version.model_id, model_version.version
        )
        
        # Verify loaded model
        self.assertIsNotNone(loaded_model)
        self.assertTrue(hasattr(loaded_model, 'predict'))
        self.assertEqual(loaded_version.model_id, model_version.model_id)
        self.assertEqual(loaded_version.version, model_version.version)
        
        # Test loading latest version (without specifying version)
        loaded_model_latest, loaded_version_latest = self.model_manager.load_model(
            model_version.model_id
        )
        self.assertEqual(loaded_version_latest.version, model_version.version)
    
    def test_model_versioning(self):
        """Test model versioning functionality"""
        model_name = "versioning_test"
        
        # Save multiple versions
        versions = []
        for i in range(3):
            model_version = self.model_manager.save_model(
                self.sample_model, model_name, ModelType.CLASSIFICATION,
                {**self.sample_metrics, "iteration": i}
            )
            versions.append(model_version)
        
        # Verify versions are incremental
        version_numbers = [int(v.version) for v in versions]
        self.assertEqual(version_numbers, [1, 2, 3])
        
        # Verify all versions have same model_id base but different full IDs
        model_names = [v.model_name for v in versions]
        self.assertTrue(all(name == model_name for name in model_names))
    
    def test_deploy_model(self):
        """Test model deployment"""
        # Save and prepare model for deployment
        model_version = self.model_manager.save_model(
            self.sample_model, "deploy_test", ModelType.CLASSIFICATION, self.sample_metrics
        )
        
        # Update status to testing (required for deployment)
        self.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        # Deploy model
        deployment = self.model_manager.deploy_model(
            model_version.model_id, model_version.version, "staging",
            {"config_param": "test_value"}
        )
        
        # Verify deployment
        self.assertIsInstance(deployment, ModelDeployment)
        self.assertEqual(deployment.model_id, model_version.model_id)
        self.assertEqual(deployment.version, model_version.version)
        self.assertEqual(deployment.environment, "staging")
        self.assertEqual(deployment.status, ModelStatus.STAGING)
        self.assertEqual(deployment.deployment_config["config_param"], "test_value")
        
        # Verify health check was performed
        self.assertIn("healthy", deployment.health_check_results)
        self.assertTrue(deployment.health_check_results["healthy"])
        
        # Verify database entry
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM model_deployments WHERE deployment_id = ?',
                      (deployment.deployment_id,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        conn.close()
    
    def test_rollback_model(self):
        """Test model rollback functionality"""
        model_name = "rollback_test"
        
        # Save two versions
        version1 = self.model_manager.save_model(
            self.sample_model, model_name, ModelType.CLASSIFICATION, self.sample_metrics
        )
        version2 = self.model_manager.save_model(
            self.sample_model, model_name, ModelType.CLASSIFICATION, 
            {**self.sample_metrics, "version": 2}
        )
        
        # Update statuses for deployment
        for version in [version1, version2]:
            self.model_manager._update_model_status(
                version.model_id, version.version, ModelStatus.TESTING
            )
        
        # Deploy version 2
        deployment_v2 = self.model_manager.deploy_model(
            version2.model_id, version2.version, "production"
        )
        
        # Rollback to version 1
        rollback_deployment = self.model_manager.rollback_model(
            version2.model_id, "production", version1.version
        )
        
        # Verify rollback
        self.assertEqual(rollback_deployment.version, version1.version)
        self.assertEqual(rollback_deployment.environment, "production")
        self.assertNotEqual(rollback_deployment.deployment_id, deployment_v2.deployment_id)
    
    def test_list_models(self):
        """Test listing models with filters"""
        # Save models with different types and statuses
        models_data = [
            ("classifier_1", ModelType.CLASSIFICATION, ModelStatus.DEVELOPMENT),
            ("classifier_2", ModelType.CLASSIFICATION, ModelStatus.TESTING),
            ("regressor_1", ModelType.REGRESSION, ModelStatus.PRODUCTION),
        ]
        
        saved_models = []
        for name, model_type, status in models_data:
            model_version = self.model_manager.save_model(
                self.sample_model, name, model_type, self.sample_metrics
            )
            # Update status
            self.model_manager._update_model_status(
                model_version.model_id, model_version.version, status
            )
            saved_models.append(model_version)
        
        # Test listing all models
        all_models = self.model_manager.list_models()
        self.assertEqual(len(all_models), 3)
        
        # Test filtering by status
        dev_models = self.model_manager.list_models(status_filter=ModelStatus.DEVELOPMENT)
        self.assertEqual(len(dev_models), 1)
        self.assertEqual(dev_models[0].status, ModelStatus.DEVELOPMENT)
        
        # Test filtering by type
        classification_models = self.model_manager.list_models(
            model_type_filter=ModelType.CLASSIFICATION
        )
        self.assertEqual(len(classification_models), 2)
        for model in classification_models:
            self.assertEqual(model.model_type, ModelType.CLASSIFICATION)
    
    def test_model_history(self):
        """Test model history tracking"""
        # Save model
        model_version = self.model_manager.save_model(
            self.sample_model, "history_test", ModelType.CLASSIFICATION, self.sample_metrics
        )
        
        # Update status (creates history entry)
        self.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        # Get history
        history = self.model_manager.get_model_history(model_version.model_id)
        
        # Verify history entries
        self.assertGreater(len(history), 0)
        
        # Check for model_saved action
        save_actions = [h for h in history if h.action == "model_saved"]
        self.assertEqual(len(save_actions), 1)
        
        save_action = save_actions[0]
        self.assertEqual(save_action.model_id, model_version.model_id)
        self.assertEqual(save_action.version, model_version.version)
        self.assertIn("model_name", save_action.details)
    
    def test_delete_model_version(self):
        """Test deleting model versions"""
        # Save model
        model_version = self.model_manager.save_model(
            self.sample_model, "delete_test", ModelType.CLASSIFICATION, self.sample_metrics
        )
        
        # Verify file exists
        self.assertTrue(Path(model_version.file_path).exists())
        
        # Delete model version
        success = self.model_manager.delete_model_version(
            model_version.model_id, model_version.version
        )
        
        # Verify deletion
        self.assertTrue(success)
        self.assertFalse(Path(model_version.file_path).exists())
        
        # Verify database entry removed
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM model_versions WHERE model_id = ? AND version = ?',
                      (model_version.model_id, model_version.version))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
        conn.close()
    
    def test_model_metrics(self):
        """Test getting model metrics"""
        # Save and deploy model
        model_version = self.model_manager.save_model(
            self.sample_model, "metrics_test", ModelType.CLASSIFICATION, self.sample_metrics
        )
        
        self.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        deployment = self.model_manager.deploy_model(
            model_version.model_id, model_version.version, "staging"
        )
        
        # Get metrics
        metrics = self.model_manager.get_model_metrics(model_version.model_id)
        
        # Verify metrics structure
        self.assertIn("model_info", metrics)
        self.assertIn("performance_metrics", metrics)
        self.assertIn("deployment_info", metrics)
        self.assertIn("history_summary", metrics)
        
        # Verify model info
        model_info = metrics["model_info"]
        self.assertEqual(model_info["model_id"], model_version.model_id)
        self.assertEqual(model_info["version"], model_version.version)
        self.assertEqual(model_info["name"], model_version.model_name)
        
        # Verify deployment info
        deployment_info = metrics["deployment_info"]
        self.assertEqual(deployment_info["total_deployments"], 1)
        self.assertEqual(deployment_info["active_deployments"], 1)
        self.assertIn("staging", deployment_info["environments"])
    
    def test_cleanup_old_versions(self):
        """Test cleanup of old model versions"""
        model_name = "cleanup_test"
        
        # Save multiple versions (more than max_versions_per_model)
        self.model_manager.max_versions_per_model = 3
        versions = []
        
        for i in range(5):
            model_version = self.model_manager.save_model(
                self.sample_model, model_name, ModelType.CLASSIFICATION,
                {**self.sample_metrics, "iteration": i}
            )
            versions.append(model_version)
        
        # Perform cleanup
        cleanup_stats = self.model_manager.cleanup_old_versions(versions[0].model_id, keep_versions=3)
        
        # Verify cleanup results
        self.assertGreater(cleanup_stats["deleted_versions"], 0)
        self.assertGreater(cleanup_stats["freed_space"], 0)
        
        # Verify remaining versions
        remaining_models = self.model_manager.list_models()
        model_versions = [m for m in remaining_models if m.model_name == model_name]
        self.assertLessEqual(len(model_versions), 3)
    
    def test_health_check(self):
        """Test model health check functionality"""
        # Save model
        model_version = self.model_manager.save_model(
            self.sample_model, "health_test", ModelType.CLASSIFICATION, self.sample_metrics
        )
        
        # Perform health check
        health_result = self.model_manager._perform_health_check(
            model_version.model_id, model_version.version
        )
        
        # Verify health check results
        self.assertIn("healthy", health_result)
        self.assertIn("checks", health_result)
        self.assertIn("timestamp", health_result)
        
        # Verify individual checks
        checks = health_result["checks"]
        self.assertTrue(checks["file_exists"])
        self.assertTrue(checks["file_integrity"])
        self.assertTrue(checks["model_loadable"])
        self.assertTrue(checks["has_predict_method"])
        
        # Overall health should be True
        self.assertTrue(health_result["healthy"])
    
    def test_file_integrity(self):
        """Test file integrity checking"""
        # Save model
        model_version = self.model_manager.save_model(
            self.sample_model, "integrity_test", ModelType.CLASSIFICATION, self.sample_metrics
        )
        
        # Verify original hash
        original_hash = self.model_manager._calculate_file_hash(Path(model_version.file_path))
        self.assertEqual(original_hash, model_version.file_hash)
        
        # Corrupt file
        with open(model_version.file_path, 'ab') as f:
            f.write(b'corrupted_data')
        
        # Verify hash changed
        corrupted_hash = self.model_manager._calculate_file_hash(Path(model_version.file_path))
        self.assertNotEqual(corrupted_hash, model_version.file_hash)
        
        # Loading should fail due to integrity check
        with self.assertRaises(ValueError):
            self.model_manager.load_model(model_version.model_id, model_version.version)
    
    def test_deployment_prevention(self):
        """Test prevention of deploying development models"""
        # Save model (status will be DEVELOPMENT)
        model_version = self.model_manager.save_model(
            self.sample_model, "deploy_prevent_test", ModelType.CLASSIFICATION, self.sample_metrics
        )
        
        # Try to deploy development model (should fail)
        with self.assertRaises(ValueError):
            self.model_manager.deploy_model(
                model_version.model_id, model_version.version, "production"
            )
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test loading non-existent model
        with self.assertRaises(ValueError):
            self.model_manager.load_model("non_existent_model", "1")
        
        # Test deploying non-existent model
        with self.assertRaises(ValueError):
            self.model_manager.deploy_model("non_existent_model", "1", "production")
        
        # Test rollback without deployment
        with self.assertRaises(ValueError):
            self.model_manager.rollback_model("non_existent_model", "production")


class TestModelManagerIntegration(unittest.TestCase):
    """Integration tests for ModelManager"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.model_manager = ModelManager(
            db_path=self.temp_db.name,
            models_directory=os.path.join(self.temp_dir, "models")
        )
    
    def tearDown(self):
        """Clean up integration test environment"""
        try:
            shutil.rmtree(self.temp_dir)
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_complete_model_lifecycle(self):
        """Test complete model lifecycle from creation to retirement"""
        # Create sample model
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        metrics = {"accuracy": 0.95, "precision": 0.94}
        
        # 1. Save model
        model_version = self.model_manager.save_model(
            model, "lifecycle_test", ModelType.CLASSIFICATION, metrics,
            {"algorithm": "RandomForest"}, "Lifecycle test model"
        )
        
        self.assertEqual(model_version.status, ModelStatus.DEVELOPMENT)
        
        # 2. Update to testing
        self.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        # 3. Deploy to staging
        staging_deployment = self.model_manager.deploy_model(
            model_version.model_id, model_version.version, "staging"
        )
        
        self.assertEqual(staging_deployment.environment, "staging")
        self.assertEqual(staging_deployment.status, ModelStatus.STAGING)
        
        # 4. Deploy to production
        prod_deployment = self.model_manager.deploy_model(
            model_version.model_id, model_version.version, "production"
        )
        
        self.assertEqual(prod_deployment.environment, "production")
        self.assertEqual(prod_deployment.status, ModelStatus.PRODUCTION)
        
        # 5. Create new version
        improved_metrics = {"accuracy": 0.97, "precision": 0.96}
        model_v2 = self.model_manager.save_model(
            model, "lifecycle_test", ModelType.CLASSIFICATION, improved_metrics,
            {"algorithm": "RandomForest", "improved": True}, "Improved model"
        )
        
        # 6. Deploy new version
        self.model_manager._update_model_status(
            model_v2.model_id, model_v2.version, ModelStatus.TESTING
        )
        
        prod_deployment_v2 = self.model_manager.deploy_model(
            model_v2.model_id, model_v2.version, "production"
        )
        
        # 7. Rollback if needed
        rollback_deployment = self.model_manager.rollback_model(
            model_v2.model_id, "production", model_version.version
        )
        
        self.assertEqual(rollback_deployment.version, model_version.version)
        
        # 8. Get complete history
        history = self.model_manager.get_model_history(model_version.model_id)
        
        # Verify history contains all major actions
        actions = [h.action for h in history]
        expected_actions = ["model_saved", "model_deployed", "model_rolled_back"]
        
        for expected_action in expected_actions:
            self.assertIn(expected_action, actions)
        
        # 9. Get comprehensive metrics
        metrics_result = self.model_manager.get_model_metrics(model_version.model_id)
        
        self.assertIn("model_info", metrics_result)
        self.assertIn("deployment_info", metrics_result)
        self.assertIn("history_summary", metrics_result)
        
        # Verify deployment info shows multiple environments
        deployment_info = metrics_result["deployment_info"]
        self.assertGreater(deployment_info["total_deployments"], 1)
        self.assertIn("production", deployment_info["environments"])
        self.assertIn("staging", deployment_info["environments"])


if __name__ == '__main__':
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)