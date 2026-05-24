"""
Test suite for Learning Maintenance Manager

Tests maintenance and cleanup utilities including data cleanup, model optimization,
database maintenance, and system monitoring.
"""

import unittest
import tempfile
import os
import json
import sqlite3
import shutil
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the maintenance manager
from Python.learning_maintenance_manager import LearningMaintenanceManager


class TestLearningMaintenanceManager(unittest.TestCase):
    """Test cases for LearningMaintenanceManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_maintenance_config.json')
        self.archive_dir = os.path.join(self.temp_dir, 'archives')
        self.temp_files_dir = os.path.join(self.temp_dir, 'temp')
        self.logs_dir = os.path.join(self.temp_dir, 'logs')
        self.models_dir = os.path.join(self.temp_dir, 'models')
        
        # Create test configuration
        test_config = {
            'maintenance_root': self.temp_dir,
            'archive_dir': self.archive_dir,
            'temp_dir': self.temp_files_dir,
            'logs_dir': self.logs_dir,
            'database_files': ['test_performance.db', 'test_audit.db'],
            'model_directories': ['models'],
            'log_files': ['test.log'],
            'cleanup_policies': {
                'old_data_days': 7,  # Short for testing
                'old_logs_days': 3,
                'old_models_days': 5,
                'temp_files_hours': 1,
                'archive_retention_days': 30
            },
            'optimization_settings': {
                'database_vacuum_enabled': True,
                'model_compression_enabled': True,
                'memory_cleanup_enabled': True,
                'disk_cleanup_enabled': True
            },
            'performance_thresholds': {
                'max_cpu_percent': 80,
                'max_memory_percent': 85,
                'max_disk_percent': 90,
                'min_free_space_gb': 1  # Low for testing
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Create test directories
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Create test database files
        self._create_test_databases()
        
        # Create test log files
        self._create_test_log_files()
        
        # Create test model files
        self._create_test_model_files()
        
        # Create test temp files
        self._create_test_temp_files()
        
        # Change to temp directory
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.maintenance_manager = LearningMaintenanceManager(self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        # Stop any running scheduler
        if hasattr(self.maintenance_manager, 'scheduler_running'):
            self.maintenance_manager.stop_scheduled_maintenance()
        
        os.chdir(self.original_cwd)
        
        # Clean up temp files
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_databases(self):
        """Create test database files with sample data."""
        # Create performance database
        perf_db = os.path.join(self.temp_dir, 'test_performance.db')
        conn = sqlite3.connect(perf_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE performance_records (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                accuracy REAL,
                created_at TEXT
            )
        ''')
        
        # Insert old and new records
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        new_date = datetime.now().isoformat()
        
        cursor.execute('INSERT INTO performance_records VALUES (1, ?, 0.85, ?)', (old_date, old_date))
        cursor.execute('INSERT INTO performance_records VALUES (2, ?, 0.90, ?)', (new_date, new_date))
        
        conn.commit()
        conn.close()
        
        # Create audit database
        audit_db = os.path.join(self.temp_dir, 'test_audit.db')
        conn = sqlite3.connect(audit_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                user_id TEXT,
                operation TEXT
            )
        ''')
        
        cursor.execute('INSERT INTO audit_log VALUES (1, ?, "user1", "test")', (old_date,))
        cursor.execute('INSERT INTO audit_log VALUES (2, ?, "user2", "test")', (new_date,))
        
        conn.commit()
        conn.close()
    
    def _create_test_log_files(self):
        """Create test log files with sample entries."""
        log_file = os.path.join(self.logs_dir, 'test.log')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        old_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
        new_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'w') as f:
            f.write(f"{old_date} - INFO - Old log entry\n")
            f.write(f"{new_date} - INFO - New log entry\n")
            f.write("Invalid timestamp line\n")
    
    def _create_test_model_files(self):
        """Create test model files."""
        # Create old model file
        old_model = os.path.join(self.models_dir, 'old_model.pkl')
        with open(old_model, 'w') as f:
            f.write('old model data')
        
        # Set old timestamp
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_model, (old_time, old_time))
        
        # Create new model file
        new_model = os.path.join(self.models_dir, 'new_model.pkl')
        with open(new_model, 'w') as f:
            f.write('new model data that should be compressed')
    
    def _create_test_temp_files(self):
        """Create test temporary files."""
        os.makedirs(self.temp_files_dir, exist_ok=True)
        
        # Create old temp file
        old_temp = os.path.join(self.temp_files_dir, 'old_temp.tmp')
        with open(old_temp, 'w') as f:
            f.write('old temp data')
        
        # Set old timestamp
        old_time = (datetime.now() - timedelta(hours=2)).timestamp()
        os.utime(old_temp, (old_time, old_time))
        
        # Create new temp file
        new_temp = os.path.join(self.temp_files_dir, 'new_temp.tmp')
        with open(new_temp, 'w') as f:
            f.write('new temp data')
    
    def test_initialization(self):
        """Test maintenance manager initialization."""
        self.assertIsNotNone(self.maintenance_manager.config)
        self.assertEqual(self.maintenance_manager.maintenance_root, self.temp_dir)
        self.assertTrue(os.path.exists(self.archive_dir))
        self.assertTrue(os.path.exists(self.temp_files_dir))
        self.assertTrue(os.path.exists(self.logs_dir))
    
    def test_cleanup_old_data(self):
        """Test old data cleanup functionality."""
        cleanup_results = self.maintenance_manager.cleanup_old_data()
        
        self.assertIn('databases_cleaned', cleanup_results)
        self.assertIn('logs_cleaned', cleanup_results)
        self.assertIn('temp_files_cleaned', cleanup_results)
        self.assertIn('total_space_freed_mb', cleanup_results)
        
        # Should have cleaned some databases
        self.assertGreater(len(cleanup_results['databases_cleaned']), 0)
        
        # Should have cleaned temp files
        self.assertGreater(cleanup_results['temp_files_cleaned'], 0)
        
        # Verify old temp file was removed
        old_temp = os.path.join(self.temp_files_dir, 'old_temp.tmp')
        self.assertFalse(os.path.exists(old_temp))
        
        # Verify new temp file still exists
        new_temp = os.path.join(self.temp_files_dir, 'new_temp.tmp')
        self.assertTrue(os.path.exists(new_temp))
    
    def test_database_cleanup(self):
        """Test database record cleanup."""
        db_path = os.path.join(self.temp_dir, 'test_performance.db')
        cutoff_date = datetime.now() - timedelta(days=5)
        
        # Count records before cleanup
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM performance_records')
        count_before = cursor.fetchone()[0]
        conn.close()
        
        # Run cleanup
        cleaned_count = self.maintenance_manager._cleanup_database_records(db_path, cutoff_date)
        
        # Count records after cleanup
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM performance_records')
        count_after = cursor.fetchone()[0]
        conn.close()
        
        # Should have removed old records
        self.assertGreater(cleaned_count, 0)
        self.assertLess(count_after, count_before)
    
    def test_log_file_cleanup(self):
        """Test log file cleanup."""
        log_file = os.path.join(self.logs_dir, 'test.log')
        cutoff_date = datetime.now() - timedelta(days=2)
        
        # Count lines before cleanup
        with open(log_file, 'r') as f:
            lines_before = len(f.readlines())
        
        # Run cleanup
        lines_removed = self.maintenance_manager._cleanup_log_file(log_file, cutoff_date)
        
        # Count lines after cleanup
        with open(log_file, 'r') as f:
            lines_after = len(f.readlines())
        
        # Should have removed some lines
        self.assertGreater(lines_removed, 0)
        self.assertLess(lines_after, lines_before)
    
    def test_model_optimization(self):
        """Test model optimization functionality."""
        optimization_results = self.maintenance_manager.optimize_models()
        
        self.assertIn('models_optimized', optimization_results)
        self.assertIn('models_compressed', optimization_results)
        self.assertIn('old_models_removed', optimization_results)
        self.assertIn('space_saved_mb', optimization_results)
        
        # Should have processed models
        self.assertGreater(optimization_results['models_optimized'], 0)
        
        # Should have removed old model
        self.assertGreater(optimization_results['old_models_removed'], 0)
        
        # Verify old model was removed
        old_model = os.path.join(self.models_dir, 'old_model.pkl')
        self.assertFalse(os.path.exists(old_model))
    
    def test_database_optimization(self):
        """Test database optimization."""
        optimization_results = self.maintenance_manager.optimize_databases()
        
        self.assertIn('databases_vacuumed', optimization_results)
        self.assertIn('indexes_rebuilt', optimization_results)
        self.assertIn('space_reclaimed_mb', optimization_results)
        
        # Should have vacuumed databases
        self.assertGreater(optimization_results['databases_vacuumed'], 0)
    
    @patch('gc.collect')
    def test_memory_cleanup(self, mock_gc_collect):
        """Test memory cleanup functionality."""
        # Mock garbage collection
        mock_gc_collect.return_value = 42
        
        cleanup_results = self.maintenance_manager.cleanup_memory()
        
        self.assertIn('memory_before_mb', cleanup_results)
        self.assertIn('memory_after_mb', cleanup_results)
        self.assertIn('garbage_collected', cleanup_results)
        
        # Should have called garbage collection
        mock_gc_collect.assert_called_once()
        self.assertEqual(cleanup_results['garbage_collected'], 42)
    
    def test_system_status(self):
        """Test system status reporting."""
        status = self.maintenance_manager.get_system_status()
        
        self.assertIn('timestamp', status)
        self.assertIn('database_sizes_mb', status)
        self.assertIn('log_sizes_mb', status)
        self.assertIn('model_count', status)
        self.assertIn('temp_files_count', status)
        self.assertIn('maintenance_needed', status)
        self.assertIn('recommendations', status)
        
        # Should have found our test files
        self.assertGreater(len(status['database_sizes_mb']), 0)
        self.assertGreater(status['model_count'], 0)
        self.assertGreater(status['temp_files_count'], 0)
    
    def test_full_maintenance_cycle(self):
        """Test complete maintenance cycle."""
        maintenance_results = self.maintenance_manager.run_full_maintenance()
        
        self.assertIn('start_time', maintenance_results)
        self.assertIn('data_cleanup', maintenance_results)
        self.assertIn('model_optimization', maintenance_results)
        self.assertIn('database_optimization', maintenance_results)
        self.assertIn('memory_cleanup', maintenance_results)
        self.assertIn('archival', maintenance_results)
        self.assertIn('overall_success', maintenance_results)
        self.assertIn('total_space_saved_mb', maintenance_results)
        
        # Should have completed all steps
        self.assertIsInstance(maintenance_results['data_cleanup'], dict)
        self.assertIsInstance(maintenance_results['model_optimization'], dict)
        self.assertIsInstance(maintenance_results['database_optimization'], dict)
    
    def test_file_compression(self):
        """Test file compression functionality."""
        # Create test file
        test_file = os.path.join(self.temp_files_dir, 'test_compress.txt')
        test_content = 'This is test content for compression' * 100
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        compressed_file = test_file + '.gz'
        
        # Compress file
        self.maintenance_manager._compress_file(test_file, compressed_file)
        
        # Verify compressed file exists and is smaller
        self.assertTrue(os.path.exists(compressed_file))
        
        original_size = os.path.getsize(test_file)
        compressed_size = os.path.getsize(compressed_file)
        
        # Compressed file should be smaller (for repetitive content)
        self.assertLess(compressed_size, original_size)
    
    def test_archive_creation(self):
        """Test data archival functionality."""
        archival_results = self.maintenance_manager.archive_old_data()
        
        self.assertIn('archives_created', archival_results)
        self.assertIn('files_archived', archival_results)
        
        # Check if archive was created (might be 0 if no old data to archive)
        self.assertIsInstance(archival_results['archives_created'], int)
    
    def test_scheduled_maintenance(self):
        """Test scheduled maintenance functionality."""
        # Start scheduler (may not work if schedule module not available)
        self.maintenance_manager.start_scheduled_maintenance()
        
        # If schedule module is available, should start
        try:
            import schedule
            self.assertTrue(self.maintenance_manager.scheduler_running)
            self.assertIsNotNone(self.maintenance_manager.scheduler_thread)
        except ImportError:
            # Schedule module not available, should not start
            self.assertFalse(self.maintenance_manager.scheduler_running)
        
        # Stop scheduler
        self.maintenance_manager.stop_scheduled_maintenance()
        
        self.assertFalse(self.maintenance_manager.scheduler_running)
    
    def test_configuration_loading(self):
        """Test configuration loading and defaults."""
        # Test with non-existent config file
        nonexistent_config = os.path.join(self.temp_dir, 'nonexistent_config.json')
        manager = LearningMaintenanceManager(nonexistent_config)
        
        # Should create default config
        self.assertIsNotNone(manager.config)
        self.assertTrue(os.path.exists(nonexistent_config))
        
        # Test with corrupted config file
        corrupted_config = os.path.join(self.temp_dir, 'corrupted_config.json')
        with open(corrupted_config, 'w') as f:
            f.write('invalid json content')
        
        manager = LearningMaintenanceManager(corrupted_config)
        self.assertIsNotNone(manager.config)  # Should fall back to defaults
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test cleanup with non-existent database
        fake_config = self.maintenance_manager.config.copy()
        fake_config['database_files'] = ['nonexistent.db']
        self.maintenance_manager.config = fake_config
        
        cleanup_results = self.maintenance_manager.cleanup_old_data()
        
        # Should handle missing files gracefully
        self.assertIn('databases_cleaned', cleanup_results)
        
        # Test with permission errors (mock)
        with patch('os.remove', side_effect=PermissionError("Permission denied")):
            cleanup_results = self.maintenance_manager.cleanup_old_data()
            # Should continue despite errors
            self.assertIn('temp_files_cleaned', cleanup_results)


class TestMaintenanceIntegration(unittest.TestCase):
    """Integration tests for maintenance manager."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'integration_config.json')
        
        # Create minimal integration config
        config = {
            'maintenance_root': self.temp_dir,
            'archive_dir': os.path.join(self.temp_dir, 'archives'),
            'temp_dir': os.path.join(self.temp_dir, 'temp'),
            'logs_dir': os.path.join(self.temp_dir, 'logs'),
            'database_files': ['integration_test.db'],
            'model_directories': ['models'],
            'cleanup_policies': {
                'old_data_days': 1,  # Very short for testing
                'temp_files_hours': 1
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        # Create test database
        test_db = os.path.join(self.temp_dir, 'integration_test.db')
        conn = sqlite3.connect(test_db)
        conn.execute('CREATE TABLE test_data (id INTEGER, timestamp TEXT)')
        
        old_date = (datetime.now() - timedelta(days=2)).isoformat()
        conn.execute('INSERT INTO test_data VALUES (1, ?)', (old_date,))
        conn.commit()
        conn.close()
        
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.maintenance_manager = LearningMaintenanceManager(self.config_path)
    
    def tearDown(self):
        """Clean up integration test environment."""
        if hasattr(self.maintenance_manager, 'scheduler_running'):
            self.maintenance_manager.stop_scheduled_maintenance()
        
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_maintenance_workflow(self):
        """Test complete maintenance workflow."""
        # Get initial system status
        initial_status = self.maintenance_manager.get_system_status()
        
        # Run full maintenance
        maintenance_results = self.maintenance_manager.run_full_maintenance()
        
        # Get final system status
        final_status = self.maintenance_manager.get_system_status()
        
        # Verify maintenance was performed
        self.assertIn('overall_success', maintenance_results)
        self.assertIsInstance(initial_status, dict)
        self.assertIsInstance(final_status, dict)
        
        # Should have processed the database
        self.assertIn('databases_cleaned', maintenance_results['data_cleanup'])


if __name__ == '__main__':
    unittest.main()