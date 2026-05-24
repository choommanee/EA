"""
Test suite for Learning Data Privacy Manager

Tests data privacy and protection features including encryption, secure transmission,
retention policies, and GDPR compliance.
"""

import unittest
import tempfile
import os
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Import the privacy manager
from Python.learning_data_privacy_manager import LearningDataPrivacyManager


class TestLearningDataPrivacyManager(unittest.TestCase):
    """Test cases for LearningDataPrivacyManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_privacy_config.json')
        self.privacy_db_path = os.path.join(self.temp_dir, 'test_privacy.db')
        
        # Create test configuration
        test_config = {
            'data_encryption_enabled': True,
            'secure_transmission_enabled': True,
            'data_retention_enabled': True,
            'anonymization_enabled': True,
            'gdpr_compliance_enabled': True,
            'privacy_db_path': self.privacy_db_path,
            'default_retention_days': 30,  # Short for testing
            'data_categories': {
                'test_signals': {'retention_days': 10, 'sensitive': True},
                'test_metrics': {'retention_days': 20, 'sensitive': False}
            },
            'anonymization_fields': ['user_id', 'ip_address', 'session_id']
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Change to temp directory for key file creation
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.privacy_manager = LearningDataPrivacyManager(self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test privacy manager initialization."""
        self.assertIsNotNone(self.privacy_manager.config)
        self.assertIsNotNone(self.privacy_manager.encryption_key)
        self.assertIsNotNone(self.privacy_manager.cipher_suite)
        self.assertIsNotNone(self.privacy_manager.rsa_private_key)
        self.assertIsNotNone(self.privacy_manager.rsa_public_key)
        self.assertTrue(os.path.exists(self.privacy_db_path))
    
    def test_sensitive_data_encryption_decryption(self):
        """Test sensitive data encryption and decryption."""
        # Test with dictionary data
        test_data = {
            'user_id': 'user123',
            'signal_value': 0.85,
            'timestamp': '2024-01-01T10:00:00'
        }
        
        # Encrypt data
        record_id, encrypted_data = self.privacy_manager.encrypt_sensitive_data(
            test_data, 'test_signals', {'source': 'unit_test'}
        )
        
        self.assertIsInstance(record_id, str)
        self.assertIsInstance(encrypted_data, str)
        self.assertNotEqual(encrypted_data, json.dumps(test_data))
        
        # Decrypt data
        decrypted_data = self.privacy_manager.decrypt_sensitive_data(
            record_id, encrypted_data, 'testing', 'test_user'
        )
        
        self.assertEqual(decrypted_data, test_data)
    
    def test_string_data_encryption(self):
        """Test string data encryption and decryption."""
        test_string = "This is sensitive trading data"
        
        record_id, encrypted_data = self.privacy_manager.encrypt_sensitive_data(
            test_string, 'test_signals'
        )
        
        decrypted_data = self.privacy_manager.decrypt_sensitive_data(
            record_id, encrypted_data
        )
        
        self.assertEqual(decrypted_data, test_string)
    
    def test_bytes_data_encryption(self):
        """Test bytes data encryption and decryption."""
        test_bytes = b"Binary trading model data"
        
        record_id, encrypted_data = self.privacy_manager.encrypt_sensitive_data(
            test_bytes, 'test_signals'
        )
        
        decrypted_data = self.privacy_manager.decrypt_sensitive_data(
            record_id, encrypted_data
        )
        
        self.assertEqual(decrypted_data, test_bytes)
    
    def test_data_anonymization(self):
        """Test data anonymization functionality."""
        test_data = {
            'user_id': 'user123',
            'ip_address': '192.168.1.100',
            'session_id': 'session_abc123',
            'signal_value': 0.75,
            'timestamp': '2024-01-01T10:00:00'
        }
        
        anonymized_data = self.privacy_manager.anonymize_data(test_data)
        
        # Check that sensitive fields are anonymized
        self.assertNotEqual(anonymized_data['user_id'], test_data['user_id'])
        self.assertNotEqual(anonymized_data['ip_address'], test_data['ip_address'])
        self.assertNotEqual(anonymized_data['session_id'], test_data['session_id'])
        
        # Check that non-sensitive fields remain unchanged
        self.assertEqual(anonymized_data['signal_value'], test_data['signal_value'])
        self.assertEqual(anonymized_data['timestamp'], test_data['timestamp'])
        
        # Check IP address anonymization format
        self.assertTrue(anonymized_data['ip_address'].endswith('.xxx'))
    
    def test_secure_data_transmission(self):
        """Test secure data transmission encryption and decryption."""
        # Test small data (direct RSA)
        small_data = b"Small test data"
        
        encrypted_data = self.privacy_manager.secure_data_transmission(small_data)
        decrypted_data = self.privacy_manager.decrypt_transmitted_data(encrypted_data)
        
        self.assertEqual(decrypted_data, small_data)
        
        # Test large data (hybrid encryption)
        large_data = b"Large test data " * 50  # > 190 bytes
        
        encrypted_data = self.privacy_manager.secure_data_transmission(large_data)
        decrypted_data = self.privacy_manager.decrypt_transmitted_data(encrypted_data)
        
        self.assertEqual(decrypted_data, large_data)
    
    def test_data_record_management(self):
        """Test data record creation and validation."""
        test_data = {'test': 'data'}
        
        record_id, _ = self.privacy_manager.encrypt_sensitive_data(
            test_data, 'test_signals'
        )
        
        # Check that record is valid
        is_valid = self.privacy_manager._is_data_record_valid(record_id)
        self.assertTrue(is_valid)
        
        # Check invalid record
        is_valid = self.privacy_manager._is_data_record_valid('invalid_id')
        self.assertFalse(is_valid)
    
    def test_data_access_logging(self):
        """Test data access logging."""
        test_data = {'test': 'data'}
        
        record_id, encrypted_data = self.privacy_manager.encrypt_sensitive_data(
            test_data, 'test_signals'
        )
        
        # Access the data (should be logged)
        self.privacy_manager.decrypt_sensitive_data(
            record_id, encrypted_data, 'testing', 'test_user'
        )
        
        # Check access log
        conn = sqlite3.connect(self.privacy_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT accessed_by, access_type, purpose 
            FROM data_access_log 
            WHERE data_record_id = ?
        ''', (record_id,))
        
        access_log = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(access_log)
        self.assertEqual(access_log[0], 'test_user')
        self.assertEqual(access_log[1], 'read')
        self.assertEqual(access_log[2], 'testing')
    
    def test_retention_policies(self):
        """Test data retention policy enforcement."""
        # Test category-specific retention
        retention_days = self.privacy_manager._get_retention_days('test_signals')
        self.assertEqual(retention_days, 10)
        
        retention_days = self.privacy_manager._get_retention_days('test_metrics')
        self.assertEqual(retention_days, 20)
        
        # Test default retention
        retention_days = self.privacy_manager._get_retention_days('unknown_category')
        self.assertEqual(retention_days, 30)
        
        # Test sensitive category detection
        is_sensitive = self.privacy_manager._is_sensitive_category('test_signals')
        self.assertTrue(is_sensitive)
        
        is_sensitive = self.privacy_manager._is_sensitive_category('test_metrics')
        self.assertFalse(is_sensitive)
    
    def test_expired_data_cleanup(self):
        """Test cleanup of expired data."""
        # Create test data
        test_data = {'test': 'data'}
        record_id, _ = self.privacy_manager.encrypt_sensitive_data(
            test_data, 'test_signals'
        )
        
        # Manually expire the data
        conn = sqlite3.connect(self.privacy_db_path)
        cursor = conn.cursor()
        
        expired_time = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute('''
            UPDATE data_records 
            SET expires_at = ? 
            WHERE id = ?
        ''', (expired_time, record_id))
        
        conn.commit()
        conn.close()
        
        # Run cleanup
        cleanup_result = self.privacy_manager.cleanup_expired_data()
        
        self.assertGreater(cleanup_result['deleted_records'], 0)
        
        # Verify data is deleted
        is_valid = self.privacy_manager._is_data_record_valid(record_id)
        self.assertFalse(is_valid)
    
    def test_privacy_status(self):
        """Test privacy status reporting."""
        # Create some test data
        test_data = {'test': 'data'}
        self.privacy_manager.encrypt_sensitive_data(test_data, 'test_signals')
        self.privacy_manager.encrypt_sensitive_data(test_data, 'test_metrics')
        
        status = self.privacy_manager.get_privacy_status()
        
        self.assertIn('data_encryption_enabled', status)
        self.assertIn('secure_transmission_enabled', status)
        self.assertIn('anonymization_enabled', status)
        self.assertIn('gdpr_compliance_enabled', status)
        self.assertIn('total_data_records', status)
        self.assertIn('sensitive_records', status)
        self.assertIn('records_by_category', status)
        
        self.assertTrue(status['data_encryption_enabled'])
        self.assertGreaterEqual(status['total_data_records'], 2)
        self.assertGreaterEqual(status['sensitive_records'], 1)
    
    def test_user_data_export(self):
        """Test GDPR user data export."""
        user_id = 'test_user_123'
        
        # Create test data with user identifier
        test_data = {'user_id': user_id, 'data': 'sensitive'}
        metadata = {'user_identifier': user_id}
        
        record_id, encrypted_data = self.privacy_manager.encrypt_sensitive_data(
            test_data, 'test_signals', metadata
        )
        
        # Access the data to create access log
        self.privacy_manager.decrypt_sensitive_data(
            record_id, encrypted_data, 'testing', user_id
        )
        
        # Export user data
        export_result = self.privacy_manager.export_user_data(user_id)
        
        self.assertIn('user_identifier', export_result)
        self.assertIn('data_records', export_result)
        self.assertIn('access_history', export_result)
        self.assertEqual(export_result['user_identifier'], user_id)
        self.assertGreater(len(export_result['data_records']), 0)
        self.assertGreater(len(export_result['access_history']), 0)
    
    def test_user_data_deletion(self):
        """Test GDPR right to be forgotten."""
        user_id = 'test_user_delete'
        
        # Create test data with user identifier
        test_data = {'user_id': user_id, 'data': 'to_be_deleted'}
        metadata = {'user_identifier': user_id}
        
        record_id, encrypted_data = self.privacy_manager.encrypt_sensitive_data(
            test_data, 'test_signals', metadata
        )
        
        # Access the data to create access log
        self.privacy_manager.decrypt_sensitive_data(
            record_id, encrypted_data, 'testing', user_id
        )
        
        # Delete user data
        deletion_result = self.privacy_manager.delete_user_data(user_id)
        
        self.assertIn('deleted_records', deletion_result)
        self.assertIn('deleted_access_logs', deletion_result)
        self.assertGreater(deletion_result['deleted_records'], 0)
        self.assertGreater(deletion_result['deleted_access_logs'], 0)
        
        # Verify data is deleted
        export_result = self.privacy_manager.export_user_data(user_id)
        self.assertEqual(len(export_result['data_records']), 0)
    
    def test_disabled_encryption(self):
        """Test behavior when encryption is disabled."""
        # Create config with encryption disabled
        disabled_config = {
            'data_encryption_enabled': False,
            'secure_transmission_enabled': False,
            'anonymization_enabled': True,
            'privacy_db_path': self.privacy_db_path
        }
        
        disabled_config_path = os.path.join(self.temp_dir, 'disabled_config.json')
        with open(disabled_config_path, 'w') as f:
            json.dump(disabled_config, f)
        
        disabled_manager = LearningDataPrivacyManager(disabled_config_path)
        
        # Test encryption/decryption with disabled encryption
        test_data = {'test': 'data'}
        
        record_id, encrypted_data = disabled_manager.encrypt_sensitive_data(
            test_data, 'test_signals'
        )
        
        # Data should not be encrypted
        decrypted_data = disabled_manager.decrypt_sensitive_data(
            record_id, encrypted_data
        )
        
        self.assertEqual(decrypted_data, test_data)
        
        # Test secure transmission with disabled encryption
        test_bytes = b"test data"
        transmitted_data = disabled_manager.secure_data_transmission(test_bytes)
        received_data = disabled_manager.decrypt_transmitted_data(transmitted_data)
        
        self.assertEqual(received_data, test_bytes)
    
    def test_disabled_anonymization(self):
        """Test behavior when anonymization is disabled."""
        # Create config with anonymization disabled
        disabled_config = {
            'data_encryption_enabled': True,
            'anonymization_enabled': False,
            'privacy_db_path': self.privacy_db_path
        }
        
        disabled_config_path = os.path.join(self.temp_dir, 'disabled_anon_config.json')
        with open(disabled_config_path, 'w') as f:
            json.dump(disabled_config, f)
        
        disabled_manager = LearningDataPrivacyManager(disabled_config_path)
        
        # Test anonymization with disabled anonymization
        test_data = {
            'user_id': 'user123',
            'ip_address': '192.168.1.100',
            'data': 'test'
        }
        
        anonymized_data = disabled_manager.anonymize_data(test_data)
        
        # Data should remain unchanged
        self.assertEqual(anonymized_data, test_data)
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test decryption with invalid record ID
        with self.assertRaises(ValueError):
            self.privacy_manager.decrypt_sensitive_data(
                'invalid_id', 'fake_data'
            )
        
        # Test transmission with corrupted data
        with self.assertRaises(Exception):
            self.privacy_manager.decrypt_transmitted_data(b'corrupted_data')
    
    def test_anonymization_methods(self):
        """Test different anonymization methods."""
        # Test hash anonymization
        value = "user123"
        anonymized = self.privacy_manager._hash_anonymize(value)
        
        self.assertNotEqual(anonymized, value)
        self.assertEqual(len(anonymized), 16)  # Hash is truncated to 16 chars
        
        # Test IP address anonymization
        ip = "192.168.1.100"
        anonymized_ip = self.privacy_manager._anonymize_ip_address(ip)
        
        self.assertEqual(anonymized_ip, "192.168.1.xxx")
        
        # Test generic anonymization
        generic_value = "sensitive_data"
        anonymized_generic = self.privacy_manager._generic_anonymize(generic_value)
        
        self.assertTrue(anonymized_generic.startswith('s'))
        self.assertTrue(anonymized_generic.endswith('a'))
        self.assertIn('*', anonymized_generic)


class TestDataPrivacyIntegration(unittest.TestCase):
    """Integration tests for data privacy manager."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'integration_config.json')
        self.privacy_db_path = os.path.join(self.temp_dir, 'integration_privacy.db')
        
        config = {
            'data_encryption_enabled': True,
            'secure_transmission_enabled': True,
            'anonymization_enabled': True,
            'gdpr_compliance_enabled': True,
            'privacy_db_path': self.privacy_db_path,
            'data_categories': {
                'trading_signals': {'retention_days': 365, 'sensitive': True},
                'model_metrics': {'retention_days': 180, 'sensitive': False}
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
        
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        self.privacy_manager = LearningDataPrivacyManager(self.config_path)
    
    def tearDown(self):
        """Clean up integration test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_data_lifecycle(self):
        """Test complete data lifecycle with privacy protection."""
        user_id = "integration_user"
        
        # 1. Create sensitive trading data
        trading_data = {
            'user_id': user_id,
            'signal_type': 'buy',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'ip_address': '192.168.1.100'
        }
        
        # 2. Encrypt and store data
        record_id, encrypted_data = self.privacy_manager.encrypt_sensitive_data(
            trading_data, 'trading_signals', {'user': user_id}
        )
        
        # 3. Anonymize data for analytics
        anonymized_data = self.privacy_manager.anonymize_data(trading_data, record_id)
        
        # 4. Secure transmission simulation
        transmitted_data = self.privacy_manager.secure_data_transmission(
            json.dumps(anonymized_data).encode('utf-8')
        )
        received_data = self.privacy_manager.decrypt_transmitted_data(transmitted_data)
        received_dict = json.loads(received_data.decode('utf-8'))
        
        # 5. Access original data
        original_data = self.privacy_manager.decrypt_sensitive_data(
            record_id, encrypted_data, 'analysis', user_id
        )
        
        # 6. Export user data (GDPR)
        export_result = self.privacy_manager.export_user_data(user_id)
        
        # 7. Get privacy status
        status = self.privacy_manager.get_privacy_status()
        
        # Verify complete lifecycle
        self.assertEqual(original_data, trading_data)
        self.assertNotEqual(received_dict['user_id'], trading_data['user_id'])
        self.assertEqual(received_dict['signal_type'], trading_data['signal_type'])
        self.assertGreater(len(export_result['data_records']), 0)
        self.assertGreater(status['total_data_records'], 0)
        self.assertGreater(status['sensitive_records'], 0)


if __name__ == '__main__':
    unittest.main()