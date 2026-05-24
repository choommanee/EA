"""
Test suite for Learning Deployment Manager

Tests deployment automation including environment validation, backup/restore,
database migration, and system health checks.
"""

import unittest
import tempfile
import os
import json
import sqlite3
import shutil
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the deployment manager
from Python.learning_deployment_manager import LearningDeploymentManager


class TestLearningDeploymentManager(unittest.TestCase):
    """Test cases for LearningDeploymentManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_deployment_config.json')
        self.backup_dir = os.path.join(self.temp_dir, 'backups')
        self.logs_dir = os.path.join(self.temp_dir, 'logs')
        
        # Create test configuration
        test_config = {
            'deployment_root': self.temp_dir,
            'backup_dir': self.backup_dir,
            'logs_dir': self.logs_dir,
            'python_executable': sys.executable,
            'required_python_version': '3.7',  # Lower for compatibility
            'required_packages': ['json'],  # Built-in package for testing
            'database_files': ['test_db.db'],
            'config_files': ['test_config.json'],
            'python_modules': ['test_module.py'],
            'health_check_endpoints': ['test_component'],
            'backup_retention_days': 7
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Create test files
        self.test_db_path = os.path.join(self.temp_dir, 'test_db.db')
        self.test_config_file = os.path.join(self.temp_dir, 'test_config.json')
        self.test_module_file = os.path.join(self.temp_dir, 'test_module.py')
        
        # Create test database
        conn = sqlite3.connect(self.test_db_path)
        conn.execute('CREATE TABLE test (id INTEGER, name TEXT)')
        conn.execute('INSERT INTO test VALUES (1, "test")')
        conn.commit()
        conn.close()
        
        # Create test config file
        with open(self.test_config_file, 'w') as f:
            json.dump({'test': 'config'}, f)
        
        # Create test module file
        with open(self.test_module_file, 'w') as f:
            f.write('# Test module\nprint("Hello, World!")\n')
        
        # Change to temp directory
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.deployment_manager = LearningDeploymentManager(self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        
        # Clean up temp files
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test deployment manager initialization."""
        self.assertIsNotNone(self.deployment_manager.config)
        self.assertEqual(self.deployment_manager.deployment_root, self.temp_dir)
        self.assertTrue(os.path.exists(self.backup_dir))
        self.assertTrue(os.path.exists(self.logs_dir))
    
    def test_environment_validation(self):
        """Test environment validation."""
        validation_result = self.deployment_manager.validate_environment()
        
        self.assertIn('python_version', validation_result)
        self.assertIn('required_packages', validation_result)
        self.assertIn('file_permissions', validation_result)
        self.assertIn('disk_space', validation_result)
        self.assertIn('database_access', validation_result)
        self.assertIn('overall_status', validation_result)
        
        # Should pass with our test configuration
        self.assertTrue(validation_result['python_version'])
        self.assertTrue(validation_result['required_packages'])
        self.assertTrue(validation_result['file_permissions'])
        self.assertTrue(validation_result['database_access'])
    
    def test_backup_creation(self):
        """Test backup creation."""
        backup_path = self.deployment_manager.create_backup('test_backup')
        
        self.assertTrue(os.path.exists(backup_path))
        self.assertTrue(backup_path.endswith('.zip'))
        
        # Verify backup contents
        import zipfile
        with zipfile.ZipFile(backup_path, 'r') as backup_zip:
            file_list = backup_zip.namelist()
            self.assertIn('backup_metadata.json', file_list)
            
            # Check if our test files are in the backup
            if os.path.exists('test_db.db'):
                self.assertIn('test_db.db', file_list)
    
    def test_backup_restore(self):
        """Test backup restoration."""
        # Create a backup first
        backup_path = self.deployment_manager.create_backup('restore_test')
        
        # Modify a file
        with open(self.test_config_file, 'w') as f:
            json.dump({'modified': 'config'}, f)
        
        # Restore backup
        restore_result = self.deployment_manager.restore_backup(backup_path)
        
        self.assertTrue(restore_result)
        
        # Verify restoration (original content should be back)
        with open(self.test_config_file, 'r') as f:
            restored_config = json.load(f)
            self.assertEqual(restored_config, {'test': 'config'})
    
    def test_database_migration(self):
        """Test database migration."""
        migration_results = self.deployment_manager.migrate_databases()
        
        self.assertIsInstance(migration_results, dict)
        
        # Check if our test database was processed
        # (It might not be in the standard migration list, so we check the structure)
        for db_name, result in migration_results.items():
            self.assertIsInstance(result, bool)
    
    def test_health_check_database(self):
        """Test database health check."""
        # Test existing database
        health_result = self.deployment_manager._check_database_health('test_db.db')
        self.assertTrue(health_result)
        
        # Test non-existent database
        health_result = self.deployment_manager._check_database_health('nonexistent.db')
        self.assertFalse(health_result)
    
    def test_health_check_file_integrity(self):
        """Test file integrity check."""
        # Test existing file
        integrity_result = self.deployment_manager._check_file_integrity('test_module.py')
        self.assertTrue(integrity_result)
        
        # Test non-existent file
        integrity_result = self.deployment_manager._check_file_integrity('nonexistent.py')
        self.assertFalse(integrity_result)
        
        # Test empty file
        empty_file = os.path.join(self.temp_dir, 'empty.py')
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        integrity_result = self.deployment_manager._check_file_integrity('empty.py')
        self.assertFalse(integrity_result)
    
    @patch('subprocess.run')
    def test_install_dependencies(self, mock_subprocess):
        """Test dependency installation."""
        # Mock successful installation
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        install_result = self.deployment_manager.install_dependencies()
        self.assertTrue(install_result)
        
        # Mock failed installation
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Installation failed"
        
        install_result = self.deployment_manager.install_dependencies()
        self.assertFalse(install_result)
    
    def test_performance_metrics_collection(self):
        """Test performance metrics collection."""
        metrics = self.deployment_manager._collect_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        # Should have at least some metrics or a note about availability
        self.assertTrue(len(metrics) > 0)
    
    def test_deployment_status(self):
        """Test deployment status reporting."""
        status = self.deployment_manager.get_deployment_status()
        
        self.assertIn('deployment_root', status)
        self.assertIn('python_version', status)
        self.assertIn('timestamp', status)
        self.assertIn('backup_count', status)
        self.assertIn('database_files', status)
        self.assertIn('module_files', status)
        
        self.assertEqual(status['deployment_root'], self.temp_dir)
    
    def test_backup_cleanup(self):
        """Test old backup cleanup."""
        # Create some test backup files with different ages
        old_backup = os.path.join(self.backup_dir, 'old_backup.zip')
        recent_backup = os.path.join(self.backup_dir, 'recent_backup.zip')
        
        # Create old backup (simulate old timestamp)
        with open(old_backup, 'w') as f:
            f.write('old backup')
        
        # Set old timestamp (more than retention period)
        old_time = datetime.now() - timedelta(days=10)
        os.utime(old_backup, (old_time.timestamp(), old_time.timestamp()))
        
        # Create recent backup
        with open(recent_backup, 'w') as f:
            f.write('recent backup')
        
        # Run cleanup
        cleaned_count = self.deployment_manager.cleanup_old_backups()
        
        # Old backup should be removed, recent should remain
        self.assertFalse(os.path.exists(old_backup))
        self.assertTrue(os.path.exists(recent_backup))
        self.assertEqual(cleaned_count, 1)
    
    @patch('subprocess.run')
    def test_full_deployment(self, mock_subprocess):
        """Test full deployment process."""
        # Mock successful dependency installation
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        deployment_result = self.deployment_manager.deploy_system(
            environment='development',
            skip_backup=True  # Skip backup for faster testing
        )
        
        self.assertIn('environment', deployment_result)
        self.assertIn('steps', deployment_result)
        self.assertIn('overall_success', deployment_result)
        
        self.assertEqual(deployment_result['environment'], 'development')
        
        # Check that all steps were attempted
        steps = deployment_result['steps']
        self.assertIn('environment_validation', steps)
        self.assertIn('backup_creation', steps)
        self.assertIn('dependency_installation', steps)
        self.assertIn('database_migration', steps)
        self.assertIn('health_check', steps)
    
    def test_component_health_check_mock(self):
        """Test component health check with mocked components."""
        # Test unknown component
        health_result = self.deployment_manager._check_component_health('unknown_component')
        self.assertFalse(health_result)
        
        # Test component health check error handling
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            health_result = self.deployment_manager._check_component_health('performance_monitor')
            self.assertFalse(health_result)
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test backup with invalid path
        with patch('zipfile.ZipFile', side_effect=Exception("Backup failed")):
            with self.assertRaises(Exception):
                self.deployment_manager.create_backup('error_test')
        
        # Test restore with non-existent backup
        restore_result = self.deployment_manager.restore_backup('nonexistent_backup.zip')
        self.assertFalse(restore_result)
    
    def test_configuration_loading(self):
        """Test configuration loading and defaults."""
        # Test with non-existent config file
        nonexistent_config = os.path.join(self.temp_dir, 'nonexistent_config.json')
        manager = LearningDeploymentManager(nonexistent_config)
        
        # Should create default config
        self.assertIsNotNone(manager.config)
        self.assertTrue(os.path.exists(nonexistent_config))
        
        # Test with corrupted config file
        corrupted_config = os.path.join(self.temp_dir, 'corrupted_config.json')
        with open(corrupted_config, 'w') as f:
            f.write('invalid json content')
        
        manager = LearningDeploymentManager(corrupted_config)
        self.assertIsNotNone(manager.config)  # Should fall back to defaults


class TestDeploymentIntegration(unittest.TestCase):
    """Integration tests for deployment manager."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'integration_config.json')
        
        # Create minimal integration config
        config = {
            'deployment_root': self.temp_dir,
            'backup_dir': os.path.join(self.temp_dir, 'backups'),
            'logs_dir': os.path.join(self.temp_dir, 'logs'),
            'required_python_version': '3.7',
            'required_packages': [],  # Empty for faster testing
            'database_files': ['integration_test.db'],
            'python_modules': ['integration_module.py']
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        # Create test files
        test_db = os.path.join(self.temp_dir, 'integration_test.db')
        conn = sqlite3.connect(test_db)
        conn.execute('CREATE TABLE integration_test (id INTEGER)')
        conn.close()
        
        test_module = os.path.join(self.temp_dir, 'integration_module.py')
        with open(test_module, 'w') as f:
            f.write('# Integration test module\n')
        
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.deployment_manager = LearningDeploymentManager(self.config_path)
    
    def tearDown(self):
        """Clean up integration test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_complete_deployment_workflow(self, mock_subprocess):
        """Test complete deployment workflow."""
        # Mock successful subprocess calls
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        # Step 1: Environment validation
        validation_result = self.deployment_manager.validate_environment()
        self.assertTrue(validation_result['overall_status'])
        
        # Step 2: Create backup
        backup_path = self.deployment_manager.create_backup('workflow_test')
        self.assertTrue(os.path.exists(backup_path))
        
        # Step 3: Database migration
        migration_results = self.deployment_manager.migrate_databases()
        self.assertIsInstance(migration_results, dict)
        
        # Step 4: Health check
        health_results = self.deployment_manager.perform_health_check()
        self.assertIn('overall_status', health_results)
        
        # Step 5: Full deployment
        deployment_result = self.deployment_manager.deploy_system('development')
        self.assertIn('overall_success', deployment_result)
        
        # Step 6: Status check
        status = self.deployment_manager.get_deployment_status()
        self.assertIn('deployment_root', status)


if __name__ == '__main__':
    unittest.main()