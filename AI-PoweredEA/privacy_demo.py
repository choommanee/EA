"""
Data Privacy Manager Demonstration

This script demonstrates the comprehensive data privacy and protection features
of the Learning Data Privacy Manager.
"""

import os
import json
import tempfile
from datetime import datetime
from Python.learning_data_privacy_manager import LearningDataPrivacyManager


def demonstrate_privacy_features():
    """Demonstrate key data privacy features."""
    print("🔐 AI Continuous Learning System - Data Privacy Manager Demo")
    print("=" * 70)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'demo_privacy_config.json')
    privacy_db_path = os.path.join(temp_dir, 'demo_privacy.db')
    
    # Create demo configuration
    demo_config = {
        'data_encryption_enabled': True,
        'secure_transmission_enabled': True,
        'data_retention_enabled': True,
        'anonymization_enabled': True,
        'gdpr_compliance_enabled': True,
        'privacy_db_path': privacy_db_path,
        'default_retention_days': 730,
        'sensitive_data_retention_days': 365,
        'anonymization_threshold_days': 90,
        'compression_enabled': True,
        'data_categories': {
            'trading_signals': {'retention_days': 365, 'sensitive': True},
            'model_performance': {'retention_days': 730, 'sensitive': False},
            'user_interactions': {'retention_days': 90, 'sensitive': True},
            'system_metrics': {'retention_days': 180, 'sensitive': False}
        },
        'anonymization_fields': [
            'user_id', 'ip_address', 'session_id', 'device_id', 'email'
        ]
    }
    
    with open(config_path, 'w') as f:
        json.dump(demo_config, f, indent=2)
    
    # Change to temp directory for key file creation
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Initialize privacy manager
        print("\n1. 🚀 Initializing Data Privacy Manager...")
        privacy_manager = LearningDataPrivacyManager(config_path)
        print("   ✅ Privacy manager initialized successfully")
        print(f"   📁 Privacy database: {privacy_db_path}")
        print(f"   🔑 Encryption keys generated and secured")
        print(f"   🛡️ RSA key pair created for secure transmission")
        
        # Demonstrate sensitive data encryption
        print("\n2. 🔐 Sensitive Data Encryption...")
        
        # Trading signal data
        trading_signal = {
            'user_id': 'trader_john_doe',
            'signal_type': 'BUY',
            'symbol': 'EURUSD',
            'confidence': 0.87,
            'timestamp': datetime.now().isoformat(),
            'ip_address': '192.168.1.100',
            'session_id': 'sess_abc123def456',
            'account_balance': 50000.00
        }
        
        print(f"   📊 Original data size: {len(str(trading_signal))} characters")
        
        # Encrypt trading signal
        record_id, encrypted_data = privacy_manager.encrypt_sensitive_data(
            trading_signal, 'trading_signals', 
            {'user_identifier': 'trader_john_doe', 'source': 'demo'}
        )
        
        print(f"   🔒 Encrypted data size: {len(encrypted_data)} characters")
        print(f"   🆔 Record ID: {record_id[:16]}...")
        print(f"   📈 Compression ratio: {len(str(trading_signal))/len(encrypted_data)*100:.1f}%")
        
        # Decrypt trading signal
        decrypted_signal = privacy_manager.decrypt_sensitive_data(
            record_id, encrypted_data, 'analysis', 'system'
        )
        
        print(f"   🔓 Decryption successful: {decrypted_signal == trading_signal}")
        
        # Demonstrate data anonymization
        print("\n3. 🎭 Data Anonymization...")
        
        user_data = {
            'user_id': 'trader_john_doe',
            'email': 'john.doe@example.com',
            'ip_address': '192.168.1.100',
            'session_id': 'sess_abc123def456',
            'device_id': 'device_xyz789',
            'trading_volume': 1000000,
            'profit_loss': 15000.50
        }
        
        print("   📋 Original sensitive data:")
        for key, value in user_data.items():
            if key in demo_config['anonymization_fields']:
                print(f"      🔍 {key}: {value}")
            else:
                print(f"      📊 {key}: {value}")
        
        anonymized_data = privacy_manager.anonymize_data(user_data, record_id)
        
        print("\n   🎭 Anonymized data:")
        for key, value in anonymized_data.items():
            if key in demo_config['anonymization_fields']:
                print(f"      🔒 {key}: {value}")
            else:
                print(f"      📊 {key}: {value}")
        
        # Demonstrate secure transmission
        print("\n4. 🚀 Secure Data Transmission...")
        
        # Small data transmission
        small_message = b"Small trading alert: EURUSD signal triggered"
        print(f"   📤 Small message: {len(small_message)} bytes")
        
        encrypted_small = privacy_manager.secure_data_transmission(small_message)
        decrypted_small = privacy_manager.decrypt_transmitted_data(encrypted_small)
        
        print(f"   🔒 Encrypted size: {len(encrypted_small)} bytes")
        print(f"   ✅ Small transmission successful: {decrypted_small == small_message}")
        
        # Large data transmission (hybrid encryption)
        large_data = json.dumps({
            'model_weights': [0.1] * 1000,  # Simulate large model data
            'training_history': ['epoch_' + str(i) for i in range(100)],
            'metadata': {'version': '1.0', 'timestamp': datetime.now().isoformat()}
        }).encode('utf-8')
        
        print(f"   📤 Large data: {len(large_data)} bytes")
        
        encrypted_large = privacy_manager.secure_data_transmission(large_data)
        decrypted_large = privacy_manager.decrypt_transmitted_data(encrypted_large)
        
        print(f"   🔒 Encrypted size: {len(encrypted_large)} bytes")
        print(f"   ✅ Large transmission successful: {decrypted_large == large_data}")
        print(f"   ⚡ Hybrid encryption used for large data")
        
        # Demonstrate different data types
        print("\n5. 📊 Multi-Type Data Handling...")
        
        # String data
        string_data = "Confidential trading strategy notes"
        str_record_id, str_encrypted = privacy_manager.encrypt_sensitive_data(
            string_data, 'user_interactions'
        )
        str_decrypted = privacy_manager.decrypt_sensitive_data(str_record_id, str_encrypted)
        print(f"   📝 String data: {str_decrypted == string_data}")
        
        # Binary data
        binary_data = b"Binary model file content with special characters: \x00\x01\x02"
        bin_record_id, bin_encrypted = privacy_manager.encrypt_sensitive_data(
            binary_data, 'model_performance'
        )
        bin_decrypted = privacy_manager.decrypt_sensitive_data(bin_record_id, bin_encrypted)
        print(f"   🔢 Binary data: {bin_decrypted == binary_data}")
        
        # Dictionary data
        dict_data = {'nested': {'data': {'structure': 'preserved'}}}
        dict_record_id, dict_encrypted = privacy_manager.encrypt_sensitive_data(
            dict_data, 'system_metrics'
        )
        dict_decrypted = privacy_manager.decrypt_sensitive_data(dict_record_id, dict_encrypted)
        print(f"   📋 Dictionary data: {dict_decrypted == dict_data}")
        
        # Demonstrate GDPR compliance
        print("\n6. ⚖️ GDPR Compliance Features...")
        
        user_identifier = 'trader_john_doe'
        
        # Export user data
        export_result = privacy_manager.export_user_data(user_identifier)
        print(f"   📤 Data export for {user_identifier}:")
        print(f"      📊 Total records: {export_result['total_records']}")
        print(f"      👁️ Access events: {export_result['total_access_events']}")
        print(f"      📅 Export timestamp: {export_result['export_timestamp'][:19]}")
        
        if export_result['data_records']:
            print("      📋 Data categories found:")
            categories = set(record['category'] for record in export_result['data_records'])
            for category in categories:
                count = sum(1 for r in export_result['data_records'] if r['category'] == category)
                print(f"         • {category}: {count} records")
        
        # Demonstrate privacy status
        print("\n7. 📊 Privacy Status & Statistics...")
        status = privacy_manager.get_privacy_status()
        
        print(f"   🔐 Data Encryption: {'Enabled' if status['data_encryption_enabled'] else 'Disabled'}")
        print(f"   🚀 Secure Transmission: {'Enabled' if status['secure_transmission_enabled'] else 'Disabled'}")
        print(f"   🎭 Anonymization: {'Enabled' if status['anonymization_enabled'] else 'Disabled'}")
        print(f"   ⚖️ GDPR Compliance: {'Enabled' if status['gdpr_compliance_enabled'] else 'Disabled'}")
        print(f"   📊 Total Data Records: {status['total_data_records']}")
        print(f"   🔒 Sensitive Records: {status['sensitive_records']}")
        print(f"   🎭 Anonymized Records: {status['anonymized_records']}")
        print(f"   👁️ Recent Access (24h): {status['recent_access_24h']}")
        
        print("\n   📋 Records by Category:")
        for category, count in status['records_by_category'].items():
            sensitive_marker = "🔒" if demo_config['data_categories'].get(category, {}).get('sensitive', False) else "📊"
            retention_days = demo_config['data_categories'].get(category, {}).get('retention_days', 730)
            print(f"      {sensitive_marker} {category}: {count} records ({retention_days} days retention)")
        
        # Demonstrate data cleanup
        print("\n8. 🧹 Data Retention & Cleanup...")
        
        cleanup_result = privacy_manager.cleanup_expired_data()
        print(f"   🗑️ Expired records cleaned: {cleanup_result.get('deleted_records', 0)}")
        print(f"   📋 Access logs cleaned: {cleanup_result.get('cleaned_access_logs', 0)}")
        print(f"   🎭 Anonymization logs cleaned: {cleanup_result.get('cleaned_anonymization_logs', 0)}")
        
        # Show final status
        final_status = privacy_manager.get_privacy_status()
        print(f"   📊 Active records after cleanup: {final_status['total_data_records']}")
        
        # Demonstrate right to be forgotten
        print("\n9. 🗑️ Right to be Forgotten (GDPR)...")
        
        print(f"   ⚠️ Simulating data deletion for user: {user_identifier}")
        deletion_result = privacy_manager.delete_user_data(user_identifier)
        
        print(f"   🗑️ Deleted records: {deletion_result.get('deleted_records', 0)}")
        print(f"   📋 Deleted access logs: {deletion_result.get('deleted_access_logs', 0)}")
        print(f"   🎭 Deleted anonymization logs: {deletion_result.get('deleted_anonymization_logs', 0)}")
        
        # Verify deletion
        post_deletion_export = privacy_manager.export_user_data(user_identifier)
        print(f"   ✅ User data after deletion: {post_deletion_export['total_records']} records")
        
        print("\n🎉 Data Privacy Manager Demo Completed Successfully!")
        print("=" * 70)
        print("\n📋 Key Privacy Features Demonstrated:")
        print("   • 🔐 AES-256 encryption for sensitive data with compression")
        print("   • 🚀 RSA + AES hybrid encryption for secure transmission")
        print("   • 🎭 Intelligent data anonymization with field-specific methods")
        print("   • 📊 Multi-type data handling (strings, bytes, dictionaries)")
        print("   • ⚖️ GDPR compliance with data export and deletion")
        print("   • 🗂️ Automated data retention and cleanup policies")
        print("   • 👁️ Comprehensive access logging and audit trails")
        print("   • 📈 Real-time privacy status monitoring")
        print("\n🛡️ Your sensitive learning data is now fully protected!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        os.chdir(original_cwd)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    demonstrate_privacy_features()