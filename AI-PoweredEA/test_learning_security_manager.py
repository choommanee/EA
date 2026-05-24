"""
Test suite for Learning Security Manager

Tests security measures including model encryption, access control, and audit logging.
"""

import unittest
import tempfile
import os
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the security manager
from Python.learning_security_manager import LearningSecurityManager


class TestLearningSecurityManager(unittest.TestCase):
    """Test cases for LearningSecurityManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_security_config.json')
        self.audit_db_path = os.path.join(self.temp_dir, 'test_audit.db')
        
        # Create test configuration
        test_config = {
            'encryption_enabled': True,
            'access_control_enabled': True,
            'audit_logging_enabled': True,
            'audit_db_path': self.audit_db_path,
            'session_timeout_minutes': 30,
            'admin_users': ['admin', 'system'],
            'allowed_operations': ['model_load', 'model_save', 'config_read']
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Change to temp directory for key file creation
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.security_manager = LearningSecurityManager(self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test security manager initialization."""
        self.assertIsNotNone(self.security_manager.config)
        self.assertIsNotNone(self.security_manager.encryption_key)
        self.assertIsNotNone(self.security_manager.cipher_suite)
        self.assertTrue(os.path.exists(self.audit_db_path))
    
    def test_model_encryption_decryption(self):
        """Test model file encryption and decryption."""
        # Test data
        model_data = b"test model data for encryption"
        model_id = "test_model_v1"
        
        # Encrypt the model
        encrypted_data, integrity_hash = self.security_manager.encrypt_model_file(
            model_data, model_id
        )
        
        self.assertNotEqual(encrypted_data, model_data)
        self.assertIsInstance(integrity_hash, str)
        self.assertEqual(len(integrity_hash), 64)  # SHA-256 hash length
        
        # Decrypt the model
        decrypted_data = self.security_manager.decrypt_model_file(
            encrypted_data, model_id, integrity_hash
        )
        
        self.assertEqual(decrypted_data, model_data)
    
    def test_integrity_check_failure(self):
        """Test integrity check failure during decryption."""
        model_data = b"test model data"
        model_id = "test_model_v1"
        
        encrypted_data, _ = self.security_manager.encrypt_model_file(
            model_data, model_id
        )
        
        # Use wrong hash
        wrong_hash = "wrong_hash"
        
        with self.assertRaises(ValueError):
            self.security_manager.decrypt_model_file(
                encrypted_data, model_id, wrong_hash
            )
    
    def test_session_management(self):
        """Test access session creation and validation."""
        user_id = "test_user"
        ip_address = "192.168.1.1"
        
        # Create session
        session_id = self.security_manager.create_access_session(user_id, ip_address)
        
        self.assertIsInstance(session_id, str)
        self.assertGreater(len(session_id), 20)
        
        # Validate session
        is_valid = self.security_manager.validate_access_session(session_id, user_id)
        self.assertTrue(is_valid)
        
        # Test invalid session
        is_valid = self.security_manager.validate_access_session("invalid_session", user_id)
        self.assertFalse(is_valid)
    
    def test_session_timeout(self):
        """Test session timeout functionality."""
        user_id = "test_user"
        
        # Create session
        session_id = self.security_manager.create_access_session(user_id)
        
        # Manually update last activity to simulate timeout
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        old_time = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute('''
            UPDATE access_sessions 
            SET last_activity = ? 
            WHERE session_id = ?
        ''', (old_time, session_id))
        
        conn.commit()
        conn.close()
        
        # Session should now be invalid due to timeout
        is_valid = self.security_manager.validate_access_session(session_id, user_id)
        self.assertFalse(is_valid)
    
    def test_operation_permissions(self):
        """Test operation permission checking."""
        user_id = "test_user"
        admin_user = "admin"
        
        # Test allowed operation for regular user
        has_permission = self.security_manager.check_operation_permission(
            user_id, "model_load"
        )
        self.assertTrue(has_permission)
        
        # Test disallowed operation for regular user
        has_permission = self.security_manager.check_operation_permission(
            user_id, "system_admin"
        )
        self.assertFalse(has_permission)
        
        # Test admin user (should have all permissions)
        has_permission = self.security_manager.check_operation_permission(
            admin_user, "system_admin"
        )
        self.assertTrue(has_permission)
    
    def test_audit_logging(self):
        """Test audit logging functionality."""
        user_id = "test_user"
        operation = "model_load"
        resource = "test_model"
        
        # Perform operation that should be logged
        self.security_manager._log_audit_event(
            user_id=user_id,
            operation=operation,
            resource=resource,
            success=True,
            details="Test operation"
        )
        
        # Retrieve audit log
        audit_entries = self.security_manager.get_audit_log(
            user_id=user_id,
            operation=operation
        )
        
        self.assertGreater(len(audit_entries), 0)
        
        entry = audit_entries[0]
        self.assertEqual(entry['user_id'], user_id)
        self.assertEqual(entry['operation'], operation)
        self.assertEqual(entry['resource'], resource)
        self.assertTrue(entry['success'])
    
    def test_audit_log_filtering(self):
        """Test audit log filtering capabilities."""
        # Add multiple test entries
        test_entries = [
            ('user1', 'model_load', True),
            ('user2', 'model_save', True),
            ('user1', 'config_read', False),
        ]
        
        for user_id, operation, success in test_entries:
            self.security_manager._log_audit_event(
                user_id=user_id,
                operation=operation,
                success=success,
                details=f"Test {operation}"
            )
        
        # Test filtering by user
        user1_entries = self.security_manager.get_audit_log(user_id='user1')
        self.assertEqual(len(user1_entries), 2)
        
        # Test filtering by operation
        load_entries = self.security_manager.get_audit_log(operation='model_load')
        self.assertEqual(len(load_entries), 1)
        
        # Test limit
        limited_entries = self.security_manager.get_audit_log(limit=1)
        self.assertEqual(len(limited_entries), 1)
    
    def test_security_status(self):
        """Test security status reporting."""
        # Create some test data
        self.security_manager.create_access_session("user1")
        self.security_manager.create_access_session("user2")
        
        status = self.security_manager.get_security_status()
        
        self.assertIn('encryption_enabled', status)
        self.assertIn('access_control_enabled', status)
        self.assertIn('audit_logging_enabled', status)
        self.assertIn('active_sessions', status)
        self.assertIn('total_audit_entries', status)
        
        self.assertTrue(status['encryption_enabled'])
        self.assertTrue(status['access_control_enabled'])
        self.assertTrue(status['audit_logging_enabled'])
        self.assertGreaterEqual(status['active_sessions'], 2)
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        user_id = "test_user"
        
        # Create session
        session_id = self.security_manager.create_access_session(user_id)
        
        # Manually expire the session
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        cursor.execute('''
            UPDATE access_sessions 
            SET last_activity = ? 
            WHERE session_id = ?
        ''', (old_time, session_id))
        
        conn.commit()
        conn.close()
        
        # Run cleanup
        self.security_manager.cleanup_expired_sessions()
        
        # Session should now be inactive
        is_valid = self.security_manager.validate_access_session(session_id, user_id)
        self.assertFalse(is_valid)
    
    def test_cleanup_old_audit_logs(self):
        """Test cleanup of old audit log entries."""
        # Add old audit entry
        conn = sqlite3.connect(self.audit_db_path)
        cursor = conn.cursor()
        
        old_timestamp = (datetime.now() - timedelta(days=400)).isoformat()
        cursor.execute('''
            INSERT INTO audit_log 
            (timestamp, user_id, operation, success)
            VALUES (?, ?, ?, ?)
        ''', (old_timestamp, 'test_user', 'test_operation', True))
        
        conn.commit()
        conn.close()
        
        # Run cleanup
        self.security_manager.cleanup_old_audit_logs()
        
        # Old entry should be removed
        recent_entries = self.security_manager.get_audit_log()
        old_entries = [e for e in recent_entries if e['timestamp'] == old_timestamp]
        self.assertEqual(len(old_entries), 0)
    
    def test_disabled_encryption(self):
        """Test behavior when encryption is disabled."""
        # Create config with encryption disabled
        disabled_config = {
            'encryption_enabled': False,
            'access_control_enabled': True,
            'audit_logging_enabled': True,
            'audit_db_path': self.audit_db_path
        }
        
        disabled_config_path = os.path.join(self.temp_dir, 'disabled_config.json')
        with open(disabled_config_path, 'w') as f:
            json.dump(disabled_config, f)
        
        disabled_manager = LearningSecurityManager(disabled_config_path)
        
        # Test encryption/decryption with disabled encryption
        model_data = b"test model data"
        model_id = "test_model"
        
        encrypted_data, integrity_hash = disabled_manager.encrypt_model_file(
            model_data, model_id
        )
        
        # Data should not be encrypted
        self.assertEqual(encrypted_data, model_data)
        
        decrypted_data = disabled_manager.decrypt_model_file(
            encrypted_data, model_id, integrity_hash
        )
        
        self.assertEqual(decrypted_data, model_data)
    
    def test_disabled_access_control(self):
        """Test behavior when access control is disabled."""
        # Create config with access control disabled
        disabled_config = {
            'encryption_enabled': True,
            'access_control_enabled': False,
            'audit_logging_enabled': True,
            'audit_db_path': self.audit_db_path
        }
        
        disabled_config_path = os.path.join(self.temp_dir, 'disabled_ac_config.json')
        with open(disabled_config_path, 'w') as f:
            json.dump(disabled_config, f)
        
        disabled_manager = LearningSecurityManager(disabled_config_path)
        
        # All operations should be allowed
        has_permission = disabled_manager.check_operation_permission(
            "any_user", "any_operation"
        )
        self.assertTrue(has_permission)
    
    @patch('os.path.exists')
    def test_missing_config_file(self, mock_exists):
        """Test behavior when config file is missing."""
        mock_exists.return_value = False
        
        # Should create default config
        manager = LearningSecurityManager("nonexistent_config.json")
        
        self.assertIsNotNone(manager.config)
        self.assertTrue(manager.config.get('encryption_enabled', False))
        self.assertTrue(manager.config.get('access_control_enabled', False))
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with corrupted data
        with self.assertRaises(Exception):
            self.security_manager.decrypt_model_file(
                b"corrupted_data", "test_model", "fake_hash"
            )
        
        # Test invalid session validation
        is_valid = self.security_manager.validate_access_session(
            "nonexistent_session", "test_user"
        )
        self.assertFalse(is_valid)


class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for security manager with other components."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'integration_config.json')
        self.audit_db_path = os.path.join(self.temp_dir, 'integration_audit.db')
        
        config = {
            'encryption_enabled': True,
            'access_control_enabled': True,
            'audit_logging_enabled': True,
            'audit_db_path': self.audit_db_path,
            'admin_users': ['system'],
            'allowed_operations': ['model_load', 'model_save', 'model_delete']
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.security_manager = LearningSecurityManager(self.config_path)
    
    def tearDown(self):
        """Clean up integration test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_model_lifecycle_security(self):
        """Test complete model lifecycle with security."""
        model_id = "integration_test_model"
        user_id = "system"
        
        # Create session
        session_id = self.security_manager.create_access_session(user_id)
        
        # Check save permission
        can_save = self.security_manager.check_operation_permission(
            user_id, "model_save", session_id
        )
        self.assertTrue(can_save)
        
        # Encrypt model
        model_data = b"test model data for integration"
        encrypted_data, integrity_hash = self.security_manager.encrypt_model_file(
            model_data, model_id
        )
        
        # Check load permission
        can_load = self.security_manager.check_operation_permission(
            user_id, "model_load", session_id
        )
        self.assertTrue(can_load)
        
        # Decrypt model
        decrypted_data = self.security_manager.decrypt_model_file(
            encrypted_data, model_id, integrity_hash
        )
        
        self.assertEqual(decrypted_data, model_data)
        
        # Check audit trail
        audit_entries = self.security_manager.get_audit_log(user_id=user_id)
        
        # Should have entries for session creation, encryption, and decryption
        self.assertGreaterEqual(len(audit_entries), 3)
        
        operations = [entry['operation'] for entry in audit_entries]
        self.assertIn('session_create', operations)
        self.assertIn('model_encrypt', operations)
        self.assertIn('model_decrypt', operations)


if __name__ == '__main__':
    unittest.main()