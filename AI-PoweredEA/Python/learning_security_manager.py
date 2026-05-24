"""
Learning Security Manager

This module provides comprehensive security measures for the AI continuous learning system,
including model protection, access control, and audit logging.
"""

import os
import json
import hashlib
import hmac
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import sqlite3
import pickle


class LearningSecurityManager:
    """
    Manages security for the AI continuous learning system including:
    - Model file encryption and integrity checks
    - Access control for learning operations
    - Audit logging for all learning activities
    """
    
    def __init__(self, config_path: str = "learning_security_config.json"):
        """
        Initialize the security manager.
        
        Args:
            config_path: Path to security configuration file
        """
        self.config_path = config_path
        self.config = self._load_security_config()
        self.logger = self._setup_security_logger()
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.audit_db_path = self.config.get('audit_db_path', 'learning_audit.db')
        self._initialize_audit_database()
        
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration from file."""
        default_config = {
            'encryption_enabled': True,
            'access_control_enabled': True,
            'audit_logging_enabled': True,
            'key_rotation_days': 90,
            'max_failed_attempts': 3,
            'session_timeout_minutes': 30,
            'allowed_operations': [
                'model_load', 'model_save', 'model_delete',
                'config_read', 'config_write', 'metrics_read'
            ],
            'admin_users': ['system', 'admin'],
            'audit_retention_days': 365
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                default_config.update(config)
            else:
                # Create default config file
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to load security config: {e}, using defaults")
            
        return default_config
    
    def _setup_security_logger(self) -> logging.Logger:
        """Set up security-specific logger."""
        logger = logging.getLogger('learning_security')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('learning_security.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for model protection."""
        key_file = 'learning_encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Restrict permissions
            
        return key
    
    def _initialize_audit_database(self):
        """Initialize audit logging database."""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    resource TEXT,
                    success BOOLEAN NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    session_id TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS access_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    ip_address TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failed_attempts (
                    user_id TEXT,
                    timestamp TEXT,
                    ip_address TEXT,
                    operation TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audit database: {e}")
    
    def encrypt_model_file(self, model_data: bytes, model_id: str) -> Tuple[bytes, str]:
        """
        Encrypt model file data.
        
        Args:
            model_data: Raw model data to encrypt
            model_id: Unique identifier for the model
            
        Returns:
            Tuple of (encrypted_data, integrity_hash)
        """
        if not self.config.get('encryption_enabled', True):
            return model_data, self._calculate_integrity_hash(model_data)
        
        try:
            # Encrypt the data
            encrypted_data = self.cipher_suite.encrypt(model_data)
            
            # Calculate integrity hash
            integrity_hash = self._calculate_integrity_hash(encrypted_data)
            
            # Log the operation
            self._log_audit_event(
                user_id='system',
                operation='model_encrypt',
                resource=model_id,
                success=True,
                details=f"Model encrypted, size: {len(encrypted_data)} bytes"
            )
            
            return encrypted_data, integrity_hash
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt model {model_id}: {e}")
            self._log_audit_event(
                user_id='system',
                operation='model_encrypt',
                resource=model_id,
                success=False,
                details=str(e)
            )
            raise
    
    def decrypt_model_file(self, encrypted_data: bytes, model_id: str, 
                          expected_hash: str) -> bytes:
        """
        Decrypt model file data with integrity verification.
        
        Args:
            encrypted_data: Encrypted model data
            model_id: Unique identifier for the model
            expected_hash: Expected integrity hash
            
        Returns:
            Decrypted model data
        """
        if not self.config.get('encryption_enabled', True):
            # Verify integrity even if encryption is disabled
            actual_hash = self._calculate_integrity_hash(encrypted_data)
            if actual_hash != expected_hash:
                raise ValueError(f"Integrity check failed for model {model_id}")
            return encrypted_data
        
        try:
            # Verify integrity first
            actual_hash = self._calculate_integrity_hash(encrypted_data)
            if actual_hash != expected_hash:
                raise ValueError(f"Integrity check failed for model {model_id}")
            
            # Decrypt the data
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # Log the operation
            self._log_audit_event(
                user_id='system',
                operation='model_decrypt',
                resource=model_id,
                success=True,
                details=f"Model decrypted, size: {len(decrypted_data)} bytes"
            )
            
            return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt model {model_id}: {e}")
            self._log_audit_event(
                user_id='system',
                operation='model_decrypt',
                resource=model_id,
                success=False,
                details=str(e)
            )
            raise
    
    def _calculate_integrity_hash(self, data: bytes) -> str:
        """Calculate SHA-256 hash for integrity verification."""
        return hashlib.sha256(data).hexdigest()
    
    def create_access_session(self, user_id: str, ip_address: str = None) -> str:
        """
        Create a new access session for a user.
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            
        Returns:
            Session ID
        """
        session_id = self._generate_session_id()
        timestamp = datetime.now().isoformat()
        
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_sessions 
                (session_id, user_id, created_at, last_activity, ip_address)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_id, timestamp, timestamp, ip_address))
            
            conn.commit()
            conn.close()
            
            self._log_audit_event(
                user_id=user_id,
                operation='session_create',
                success=True,
                details=f"Session created: {session_id}",
                ip_address=ip_address,
                session_id=session_id
            )
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session for user {user_id}: {e}")
            raise
    
    def validate_access_session(self, session_id: str, user_id: str) -> bool:
        """
        Validate an access session.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            True if session is valid, False otherwise
        """
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT created_at, last_activity, is_active 
                FROM access_sessions 
                WHERE session_id = ? AND user_id = ?
            ''', (session_id, user_id))
            
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False
            
            created_at, last_activity, is_active = result
            
            if not is_active:
                conn.close()
                return False
            
            # Check session timeout
            last_activity_time = datetime.fromisoformat(last_activity)
            timeout_minutes = self.config.get('session_timeout_minutes', 30)
            
            if datetime.now() - last_activity_time > timedelta(minutes=timeout_minutes):
                # Expire the session
                cursor.execute('''
                    UPDATE access_sessions 
                    SET is_active = 0 
                    WHERE session_id = ?
                ''', (session_id,))
                conn.commit()
                conn.close()
                return False
            
            # Update last activity
            cursor.execute('''
                UPDATE access_sessions 
                SET last_activity = ? 
                WHERE session_id = ?
            ''', (datetime.now().isoformat(), session_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate session {session_id}: {e}")
            return False
    
    def check_operation_permission(self, user_id: str, operation: str, 
                                 session_id: str = None) -> bool:
        """
        Check if user has permission for specific operation.
        
        Args:
            user_id: User identifier
            operation: Operation to check
            session_id: Optional session ID
            
        Returns:
            True if operation is allowed, False otherwise
        """
        if not self.config.get('access_control_enabled', True):
            return True
        
        try:
            # Check if user is admin
            if user_id in self.config.get('admin_users', []):
                return True
            
            # Check if operation is allowed
            allowed_operations = self.config.get('allowed_operations', [])
            if operation not in allowed_operations:
                self._log_audit_event(
                    user_id=user_id,
                    operation=operation,
                    success=False,
                    details="Operation not allowed",
                    session_id=session_id
                )
                return False
            
            # Check session if provided
            if session_id and not self.validate_access_session(session_id, user_id):
                self._log_audit_event(
                    user_id=user_id,
                    operation=operation,
                    success=False,
                    details="Invalid session",
                    session_id=session_id
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check permission for {user_id}: {e}")
            return False
    
    def _generate_session_id(self) -> str:
        """Generate a secure session ID."""
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
    
    def _log_audit_event(self, user_id: str, operation: str, success: bool,
                        resource: str = None, details: str = None,
                        ip_address: str = None, session_id: str = None):
        """Log an audit event."""
        if not self.config.get('audit_logging_enabled', True):
            return
        
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_log 
                (timestamp, user_id, operation, resource, success, details, ip_address, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                user_id,
                operation,
                resource,
                success,
                details,
                ip_address,
                session_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
    
    def get_audit_log(self, user_id: str = None, operation: str = None,
                     start_date: str = None, end_date: str = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit log entries.
        
        Args:
            user_id: Filter by user ID
            operation: Filter by operation
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if operation:
                query += " AND operation = ?"
                params.append(operation)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            conn.close()
            
            # Convert to list of dictionaries
            columns = ['id', 'timestamp', 'user_id', 'operation', 'resource',
                      'success', 'details', 'ip_address', 'session_id']
            
            return [dict(zip(columns, row)) for row in results]
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve audit log: {e}")
            return []
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            timeout_minutes = self.config.get('session_timeout_minutes', 30)
            cutoff_time = (datetime.now() - timedelta(minutes=timeout_minutes)).isoformat()
            
            cursor.execute('''
                UPDATE access_sessions 
                SET is_active = 0 
                WHERE last_activity < ? AND is_active = 1
            ''', (cutoff_time,))
            
            expired_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if expired_count > 0:
                self.logger.info(f"Cleaned up {expired_count} expired sessions")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
    
    def cleanup_old_audit_logs(self):
        """Clean up old audit log entries."""
        try:
            retention_days = self.config.get('audit_retention_days', 365)
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
            
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM audit_log 
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old audit log entries")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old audit logs: {e}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status and statistics."""
        try:
            conn = sqlite3.connect(self.audit_db_path)
            cursor = conn.cursor()
            
            # Get active sessions count
            cursor.execute('SELECT COUNT(*) FROM access_sessions WHERE is_active = 1')
            active_sessions = cursor.fetchone()[0]
            
            # Get recent failed attempts
            cursor.execute('''
                SELECT COUNT(*) FROM audit_log 
                WHERE success = 0 AND timestamp > ?
            ''', ((datetime.now() - timedelta(hours=24)).isoformat(),))
            recent_failures = cursor.fetchone()[0]
            
            # Get total audit entries
            cursor.execute('SELECT COUNT(*) FROM audit_log')
            total_audit_entries = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'encryption_enabled': self.config.get('encryption_enabled', True),
                'access_control_enabled': self.config.get('access_control_enabled', True),
                'audit_logging_enabled': self.config.get('audit_logging_enabled', True),
                'active_sessions': active_sessions,
                'recent_failures_24h': recent_failures,
                'total_audit_entries': total_audit_entries,
                'key_rotation_due': self._is_key_rotation_due(),
                'last_cleanup': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get security status: {e}")
            return {'error': str(e)}
    
    def _is_key_rotation_due(self) -> bool:
        """Check if encryption key rotation is due."""
        try:
            key_file = 'learning_encryption.key'
            if not os.path.exists(key_file):
                return True
            
            key_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(key_file))
            rotation_days = self.config.get('key_rotation_days', 90)
            
            return key_age.days >= rotation_days
            
        except Exception:
            return True