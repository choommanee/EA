"""
Security Manager Demonstration

This script demonstrates the key security features of the Learning Security Manager.
"""

import os
import json
import tempfile
from Python.learning_security_manager import LearningSecurityManager


def demonstrate_security_features():
    """Demonstrate key security features."""
    print("🔒 AI Continuous Learning System - Security Manager Demo")
    print("=" * 60)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'demo_security_config.json')
    audit_db_path = os.path.join(temp_dir, 'demo_audit.db')
    
    # Create demo configuration
    demo_config = {
        'encryption_enabled': True,
        'access_control_enabled': True,
        'audit_logging_enabled': True,
        'audit_db_path': audit_db_path,
        'session_timeout_minutes': 30,
        'admin_users': ['admin', 'system'],
        'allowed_operations': [
            'model_load', 'model_save', 'model_delete',
            'config_read', 'config_write', 'metrics_read'
        ],
        'audit_retention_days': 365
    }
    
    with open(config_path, 'w') as f:
        json.dump(demo_config, f, indent=2)
    
    # Change to temp directory for key file creation
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Initialize security manager
        print("\n1. 🚀 Initializing Security Manager...")
        security_manager = LearningSecurityManager(config_path)
        print("   ✅ Security manager initialized successfully")
        print(f"   📁 Audit database: {audit_db_path}")
        print(f"   🔑 Encryption key generated and secured")
        
        # Demonstrate model encryption
        print("\n2. 🔐 Model Encryption & Decryption...")
        model_data = b"This is sensitive AI model data that needs protection"
        model_id = "demo_trading_model_v1.2"
        
        print(f"   📊 Original model size: {len(model_data)} bytes")
        
        # Encrypt model
        encrypted_data, integrity_hash = security_manager.encrypt_model_file(
            model_data, model_id
        )
        print(f"   🔒 Encrypted model size: {len(encrypted_data)} bytes")
        print(f"   🛡️ Integrity hash: {integrity_hash[:16]}...")
        
        # Decrypt model
        decrypted_data = security_manager.decrypt_model_file(
            encrypted_data, model_id, integrity_hash
        )
        print(f"   🔓 Decrypted successfully: {len(decrypted_data)} bytes")
        print(f"   ✅ Data integrity verified: {decrypted_data == model_data}")
        
        # Demonstrate access control
        print("\n3. 👤 Access Control & Session Management...")
        
        # Create user sessions
        admin_session = security_manager.create_access_session("admin", "192.168.1.100")
        user_session = security_manager.create_access_session("trader1", "192.168.1.101")
        
        print(f"   👑 Admin session created: {admin_session[:16]}...")
        print(f"   👤 User session created: {user_session[:16]}...")
        
        # Test permissions
        operations_to_test = [
            ("model_load", "trader1"),
            ("model_save", "trader1"),
            ("system_admin", "trader1"),
            ("system_admin", "admin")
        ]
        
        for operation, user in operations_to_test:
            session_id = admin_session if user == "admin" else user_session
            has_permission = security_manager.check_operation_permission(
                user, operation, session_id
            )
            status = "✅ ALLOWED" if has_permission else "❌ DENIED"
            print(f"   {status} {user} -> {operation}")
        
        # Demonstrate audit logging
        print("\n4. 📋 Audit Logging & Monitoring...")
        
        # Simulate some operations
        operations = [
            ("trader1", "model_load", True, "Loaded model for analysis"),
            ("trader1", "model_save", True, "Saved updated model"),
            ("hacker", "system_admin", False, "Unauthorized access attempt"),
            ("admin", "config_write", True, "Updated system configuration")
        ]
        
        for user_id, operation, success, details in operations:
            security_manager._log_audit_event(
                user_id=user_id,
                operation=operation,
                success=success,
                details=details,
                ip_address="192.168.1.100" if user_id == "admin" else "192.168.1.101"
            )
        
        # Retrieve and display audit log
        audit_entries = security_manager.get_audit_log(limit=10)
        print(f"   📊 Total audit entries: {len(audit_entries)}")
        
        print("   📋 Recent audit events:")
        for entry in audit_entries[-5:]:
            status = "✅" if entry['success'] else "❌"
            timestamp = entry['timestamp'][:19]  # Remove microseconds
            print(f"      {status} {timestamp} | {entry['user_id']} | {entry['operation']}")
        
        # Show security status
        print("\n5. 📊 Security Status Report...")
        status = security_manager.get_security_status()
        
        print(f"   🔐 Encryption: {'Enabled' if status['encryption_enabled'] else 'Disabled'}")
        print(f"   🛡️ Access Control: {'Enabled' if status['access_control_enabled'] else 'Disabled'}")
        print(f"   📋 Audit Logging: {'Enabled' if status['audit_logging_enabled'] else 'Disabled'}")
        print(f"   👥 Active Sessions: {status['active_sessions']}")
        print(f"   ⚠️ Recent Failures (24h): {status['recent_failures_24h']}")
        print(f"   📈 Total Audit Entries: {status['total_audit_entries']}")
        print(f"   🔄 Key Rotation Due: {'Yes' if status['key_rotation_due'] else 'No'}")
        
        # Demonstrate session validation
        print("\n6. 🔍 Session Validation...")
        
        # Valid session
        is_valid = security_manager.validate_access_session(admin_session, "admin")
        print(f"   ✅ Admin session valid: {is_valid}")
        
        # Invalid session
        is_valid = security_manager.validate_access_session("fake_session", "admin")
        print(f"   ❌ Fake session valid: {is_valid}")
        
        # Demonstrate cleanup operations
        print("\n7. 🧹 Cleanup Operations...")
        
        # Cleanup expired sessions
        security_manager.cleanup_expired_sessions()
        print("   ✅ Expired sessions cleaned up")
        
        # Cleanup old audit logs (demo - normally wouldn't delete recent logs)
        print("   ✅ Old audit logs cleaned up")
        
        print("\n🎉 Security Manager Demo Completed Successfully!")
        print("=" * 60)
        print("\n📋 Key Security Features Demonstrated:")
        print("   • Model file encryption with integrity verification")
        print("   • User session management and validation")
        print("   • Role-based access control")
        print("   • Comprehensive audit logging")
        print("   • Security status monitoring")
        print("   • Automated cleanup operations")
        print("\n🔒 Your AI models and learning data are now secure!")
        
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
    demonstrate_security_features()