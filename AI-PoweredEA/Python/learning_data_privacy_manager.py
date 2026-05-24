"""
Learning Data Privacy Manager

This module provides comprehensive data privacy and protection for the AI continuous learning system,
including data encryption, secure transmission, retention policies, and GDPR compliance features.
"""

import os
import json
import hashlib
import hmac
import time
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64
import uuid
import pickle
import gzip


class LearningDataPrivacyManager:
    """
    Manages data privacy and protection for the AI continuous learning system including:
    - Data encryption for sensitive learning data
    - Secure data transmission between components
    - Data retention and cleanup policies
    - GDPR compliance features
    - Data anonymization and pseudonymization
    """
    
    def __init__(self, config_path: str = "learning_privacy_config.json"):
        """
        Initialize the data privacy manager.
        
        Args:
            config_path: Path to privacy configuration file
        """
        self.config_path = config_path
        self.config = self._load_privacy_config()
        self.logger = self._setup_privacy_logger()
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.privacy_db_path = self.config.get('privacy_db_path', 'learning_privacy.db')
        self._initialize_privacy_database()
        self._lock = threading.Lock()
        
        # Initialize RSA keys for secure transmission
        self.rsa_private_key, self.rsa_public_key = self._get_or_create_rsa_keys()
        
    def _load_privacy_config(self) -> Dict[str, Any]:
        """Load privacy configuration from file."""
        default_config = {
            'data_encryption_enabled': True,
            'secure_transmission_enabled': True,
            'data_retention_enabled': True,
            'anonymization_enabled': True,
            'gdpr_compliance_enabled': True,
            'default_retention_days': 730,  # 2 years
            'sensitive_data_retention_days': 365,  # 1 year
            'anonymization_threshold_days': 90,
            'compression_enabled': True,
            'backup_encryption_enabled': True,
            'data_categories': {
                'trading_signals': {'retention_days': 365, 'sensitive': True},
                'model_performance': {'retention_days': 730, 'sensitive': False},
                'user_interactions': {'retention_days': 90, 'sensitive': True},
                'system_metrics': {'retention_days': 180, 'sensitive': False}
            },
            'anonymization_fields': [
                'user_id', 'ip_address', 'session_id', 'device_id'
            ],
            'encryption_algorithm': 'AES-256-GCM',
            'key_rotation_days': 90
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
            self.logger.warning(f"Failed to load privacy config: {e}, using defaults")
            
        return default_config
    
    def _setup_privacy_logger(self) -> logging.Logger:
        """Set up privacy-specific logger."""
        logger = logging.getLogger('learning_privacy')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('learning_privacy.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for data protection."""
        key_file = 'learning_privacy_encryption.key'
        
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
    
    def _get_or_create_rsa_keys(self) -> Tuple[Any, Any]:
        """Get or create RSA key pair for secure transmission."""
        private_key_file = 'learning_privacy_rsa_private.pem'
        public_key_file = 'learning_privacy_rsa_public.pem'
        
        if os.path.exists(private_key_file) and os.path.exists(public_key_file):
            # Load existing keys
            with open(private_key_file, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(), password=None
                )
            with open(public_key_file, 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read())
        else:
            # Generate new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Save keys
            with open(private_key_file, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            with open(public_key_file, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            # Restrict permissions
            os.chmod(private_key_file, 0o600)
            os.chmod(public_key_file, 0o644)
            
        return private_key, public_key
    
    def _initialize_privacy_database(self):
        """Initialize privacy management database."""
        try:
            conn = sqlite3.connect(self.privacy_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_records (
                    id TEXT PRIMARY KEY,
                    data_category TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    is_sensitive BOOLEAN DEFAULT 0,
                    is_anonymized BOOLEAN DEFAULT 0,
                    encryption_method TEXT,
                    data_hash TEXT,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retention_policies (
                    data_category TEXT PRIMARY KEY,
                    retention_days INTEGER NOT NULL,
                    is_sensitive BOOLEAN DEFAULT 0,
                    anonymization_days INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anonymization_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_record_id TEXT NOT NULL,
                    anonymization_method TEXT NOT NULL,
                    anonymized_at TEXT NOT NULL,
                    original_fields TEXT,
                    anonymized_fields TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_record_id TEXT NOT NULL,
                    accessed_by TEXT NOT NULL,
                    access_type TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    purpose TEXT,
                    ip_address TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize privacy database: {e}")
    
    def encrypt_sensitive_data(self, data: Union[str, bytes, Dict], 
                             data_category: str, 
                             metadata: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        Encrypt sensitive data with privacy protection.
        
        Args:
            data: Data to encrypt (string, bytes, or dictionary)
            data_category: Category of data for retention policy
            metadata: Additional metadata about the data
            
        Returns:
            Tuple of (data_record_id, encrypted_data_base64)
        """
        if not self.config.get('data_encryption_enabled', True):
            # Return unencrypted data with record ID and type markers
            data_record_id = str(uuid.uuid4())
            if isinstance(data, dict):
                data_str = 'JSON:' + json.dumps(data)
            elif isinstance(data, bytes):
                data_str = 'BYTES:' + base64.b64encode(data).decode('utf-8')
            else:
                data_str = 'STR:' + str(data)
            
            self._record_data_creation(data_record_id, data_category, False, metadata)
            return data_record_id, data_str
        
        try:
            # Prepare data for encryption with type marker
            if isinstance(data, dict):
                data_bytes = b'JSON:' + json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = b'STR:' + data.encode('utf-8')
            else:
                data_bytes = b'BYTES:' + data
            
            # Compress if enabled
            if self.config.get('compression_enabled', True):
                data_bytes = gzip.compress(data_bytes)
            
            # Encrypt the data
            encrypted_data = self.cipher_suite.encrypt(data_bytes)
            encrypted_data_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            # Generate record ID and hash
            data_record_id = str(uuid.uuid4())
            data_hash = hashlib.sha256(data_bytes).hexdigest()
            
            # Record the data creation
            self._record_data_creation(
                data_record_id, data_category, True, metadata, data_hash
            )
            
            self.logger.info(f"Encrypted sensitive data: {data_record_id}")
            return data_record_id, encrypted_data_b64
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt sensitive data: {e}")
            raise
    
    def decrypt_sensitive_data(self, data_record_id: str, 
                             encrypted_data_b64: str,
                             access_purpose: str = None,
                             accessed_by: str = "system") -> Union[str, bytes, Dict]:
        """
        Decrypt sensitive data with access logging.
        
        Args:
            data_record_id: Record ID of the data
            encrypted_data_b64: Base64 encoded encrypted data
            access_purpose: Purpose of accessing the data
            accessed_by: Who is accessing the data
            
        Returns:
            Decrypted data in original format
        """
        if not self.config.get('data_encryption_enabled', True):
            # Return unencrypted data with type marker handling
            self._log_data_access(data_record_id, accessed_by, "read", access_purpose)
            if encrypted_data_b64.startswith('JSON:'):
                return json.loads(encrypted_data_b64[5:])
            elif encrypted_data_b64.startswith('STR:'):
                return encrypted_data_b64[4:]
            elif encrypted_data_b64.startswith('BYTES:'):
                return base64.b64decode(encrypted_data_b64[6:])
            else:
                # Legacy data without markers
                try:
                    return json.loads(encrypted_data_b64)
                except:
                    try:
                        return base64.b64decode(encrypted_data_b64)
                    except:
                        return encrypted_data_b64
        
        try:
            # Check if data record exists and is not expired
            if not self._is_data_record_valid(data_record_id):
                raise ValueError(f"Data record {data_record_id} is invalid or expired")
            
            # Decrypt the data
            encrypted_data = base64.b64decode(encrypted_data_b64)
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # Decompress if needed
            if self.config.get('compression_enabled', True):
                try:
                    decrypted_data = gzip.decompress(decrypted_data)
                except:
                    pass  # Data might not be compressed
            
            # Log the access
            self._log_data_access(data_record_id, accessed_by, "read", access_purpose)
            
            # Check for type markers and decode accordingly
            try:
                decoded_str = decrypted_data.decode('utf-8')
                if decoded_str.startswith('JSON:'):
                    return json.loads(decoded_str[5:])
                elif decoded_str.startswith('STR:'):
                    return decoded_str[4:]
                elif decoded_str.startswith('BYTES:'):
                    return decrypted_data[6:]  # Return bytes without marker
                else:
                    # Legacy data without markers - try JSON first
                    try:
                        return json.loads(decoded_str)
                    except json.JSONDecodeError:
                        return decoded_str
            except UnicodeDecodeError:
                # Handle case where BYTES: marker exists but data is binary
                if decrypted_data.startswith(b'BYTES:'):
                    return decrypted_data[6:]
                return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt data {data_record_id}: {e}")
            raise
    
    def anonymize_data(self, data: Dict[str, Any], 
                      data_record_id: str = None) -> Dict[str, Any]:
        """
        Anonymize sensitive data by removing or hashing identifiable information.
        
        Args:
            data: Data dictionary to anonymize
            data_record_id: Optional record ID for logging
            
        Returns:
            Anonymized data dictionary
        """
        if not self.config.get('anonymization_enabled', True):
            return data
        
        try:
            anonymized_data = data.copy()
            anonymization_fields = self.config.get('anonymization_fields', [])
            original_fields = {}
            anonymized_fields = {}
            
            for field in anonymization_fields:
                if field in anonymized_data:
                    original_value = anonymized_data[field]
                    original_fields[field] = str(original_value)
                    
                    # Create anonymized version
                    if field in ['user_id', 'session_id', 'device_id']:
                        # Hash-based anonymization
                        anonymized_value = self._hash_anonymize(str(original_value))
                    elif field == 'ip_address':
                        # IP address anonymization (keep first 3 octets)
                        anonymized_value = self._anonymize_ip_address(str(original_value))
                    else:
                        # Generic anonymization
                        anonymized_value = self._generic_anonymize(str(original_value))
                    
                    anonymized_data[field] = anonymized_value
                    anonymized_fields[field] = anonymized_value
            
            # Log anonymization if record ID provided
            if data_record_id:
                self._log_anonymization(
                    data_record_id, "field_anonymization", 
                    original_fields, anonymized_fields
                )
            
            return anonymized_data
            
        except Exception as e:
            self.logger.error(f"Failed to anonymize data: {e}")
            return data
    
    def _hash_anonymize(self, value: str) -> str:
        """Create hash-based anonymized value."""
        # Use HMAC with a secret key for consistent anonymization
        secret_key = self.encryption_key[:32]  # Use first 32 bytes as HMAC key
        return hmac.new(secret_key, value.encode('utf-8'), hashlib.sha256).hexdigest()[:16]
    
    def _anonymize_ip_address(self, ip_address: str) -> str:
        """Anonymize IP address by masking last octet."""
        try:
            parts = ip_address.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
            else:
                return "xxx.xxx.xxx.xxx"
        except:
            return "xxx.xxx.xxx.xxx"
    
    def _generic_anonymize(self, value: str) -> str:
        """Generic anonymization by replacing with asterisks."""
        if len(value) <= 2:
            return "*" * len(value)
        else:
            return value[0] + "*" * (len(value) - 2) + value[-1]
    
    def secure_data_transmission(self, data: bytes, recipient_public_key: bytes = None) -> bytes:
        """
        Encrypt data for secure transmission between components.
        
        Args:
            data: Data to encrypt for transmission
            recipient_public_key: Optional recipient's public key
            
        Returns:
            Encrypted data for secure transmission
        """
        if not self.config.get('secure_transmission_enabled', True):
            return data
        
        try:
            # Use recipient's public key if provided, otherwise use our own
            if recipient_public_key:
                public_key = serialization.load_pem_public_key(recipient_public_key)
            else:
                public_key = self.rsa_public_key
            
            # For large data, use hybrid encryption (RSA + AES)
            if len(data) > 190:  # RSA 2048 can encrypt max ~245 bytes
                # Generate random AES key
                aes_key = os.urandom(32)
                iv = os.urandom(16)
                
                # Encrypt data with AES
                cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
                encryptor = cipher.encryptor()
                
                # Pad data to AES block size
                padding_length = 16 - (len(data) % 16)
                padded_data = data + bytes([padding_length]) * padding_length
                
                encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
                
                # Encrypt AES key with RSA
                encrypted_aes_key = public_key.encrypt(
                    aes_key + iv,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                # Combine encrypted key and data
                return encrypted_aes_key + encrypted_data
            else:
                # Direct RSA encryption for small data
                return public_key.encrypt(
                    data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
        except Exception as e:
            self.logger.error(f"Failed to encrypt data for transmission: {e}")
            raise
    
    def decrypt_transmitted_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data received from secure transmission.
        
        Args:
            encrypted_data: Encrypted data from transmission
            
        Returns:
            Decrypted original data
        """
        if not self.config.get('secure_transmission_enabled', True):
            return encrypted_data
        
        try:
            # Check if this is hybrid encryption (large data)
            if len(encrypted_data) > 256:  # RSA 2048 produces 256 byte ciphertext
                # Extract encrypted AES key (first 256 bytes)
                encrypted_aes_key = encrypted_data[:256]
                encrypted_data_part = encrypted_data[256:]
                
                # Decrypt AES key with RSA
                aes_key_and_iv = self.rsa_private_key.decrypt(
                    encrypted_aes_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                aes_key = aes_key_and_iv[:32]
                iv = aes_key_and_iv[32:]
                
                # Decrypt data with AES
                cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
                decryptor = cipher.decryptor()
                
                padded_data = decryptor.update(encrypted_data_part) + decryptor.finalize()
                
                # Remove padding
                padding_length = padded_data[-1]
                return padded_data[:-padding_length]
            else:
                # Direct RSA decryption
                return self.rsa_private_key.decrypt(
                    encrypted_data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
        except Exception as e:
            self.logger.error(f"Failed to decrypt transmitted data: {e}")
            raise
    
    def _record_data_creation(self, data_record_id: str, data_category: str,
                            is_encrypted: bool, metadata: Dict[str, Any] = None,
                            data_hash: str = None):
        """Record data creation in privacy database."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.privacy_db_path)
                cursor = conn.cursor()
                
                # Get retention policy for category
                retention_days = self._get_retention_days(data_category)
                is_sensitive = self._is_sensitive_category(data_category)
                
                created_at = datetime.now().isoformat()
                expires_at = (datetime.now() + timedelta(days=retention_days)).isoformat()
                
                cursor.execute('''
                    INSERT INTO data_records 
                    (id, data_category, created_at, expires_at, is_sensitive, 
                     encryption_method, data_hash, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_record_id, data_category, created_at, expires_at,
                    is_sensitive, 'AES-256' if is_encrypted else None,
                    data_hash, json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Failed to record data creation: {e}")
    
    def _is_data_record_valid(self, data_record_id: str) -> bool:
        """Check if data record is valid and not expired."""
        try:
            conn = sqlite3.connect(self.privacy_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT expires_at FROM data_records 
                WHERE id = ?
            ''', (data_record_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False
            
            expires_at = datetime.fromisoformat(result[0])
            return datetime.now() < expires_at
            
        except Exception as e:
            self.logger.error(f"Failed to check data record validity: {e}")
            return False
    
    def _log_data_access(self, data_record_id: str, accessed_by: str,
                        access_type: str, purpose: str = None):
        """Log data access for audit purposes."""
        try:
            conn = sqlite3.connect(self.privacy_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_access_log 
                (data_record_id, accessed_by, access_type, accessed_at, purpose)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data_record_id, accessed_by, access_type,
                datetime.now().isoformat(), purpose
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to log data access: {e}")
    
    def _log_anonymization(self, data_record_id: str, method: str,
                          original_fields: Dict, anonymized_fields: Dict):
        """Log anonymization operation."""
        try:
            conn = sqlite3.connect(self.privacy_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO anonymization_log 
                (data_record_id, anonymization_method, anonymized_at, 
                 original_fields, anonymized_fields)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data_record_id, method, datetime.now().isoformat(),
                json.dumps(original_fields), json.dumps(anonymized_fields)
            ))
            
            # Update data record as anonymized
            cursor.execute('''
                UPDATE data_records 
                SET is_anonymized = 1 
                WHERE id = ?
            ''', (data_record_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to log anonymization: {e}")
    
    def _get_retention_days(self, data_category: str) -> int:
        """Get retention days for data category."""
        categories = self.config.get('data_categories', {})
        if data_category in categories:
            return categories[data_category].get('retention_days', 
                                               self.config.get('default_retention_days', 730))
        return self.config.get('default_retention_days', 730)
    
    def _is_sensitive_category(self, data_category: str) -> bool:
        """Check if data category is sensitive."""
        categories = self.config.get('data_categories', {})
        if data_category in categories:
            return categories[data_category].get('sensitive', False)
        return False
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data according to retention policies."""
        try:
            with self._lock:
                conn = sqlite3.connect(self.privacy_db_path)
                cursor = conn.cursor()
                
                current_time = datetime.now().isoformat()
                
                # Get expired records
                cursor.execute('''
                    SELECT id, data_category FROM data_records 
                    WHERE expires_at < ?
                ''', (current_time,))
                
                expired_records = cursor.fetchall()
                
                # Delete expired records
                cursor.execute('''
                    DELETE FROM data_records 
                    WHERE expires_at < ?
                ''', (current_time,))
                
                deleted_records = cursor.rowcount
                
                # Clean up related logs
                for record_id, _ in expired_records:
                    cursor.execute('''
                        DELETE FROM data_access_log 
                        WHERE data_record_id = ?
                    ''', (record_id,))
                    
                    cursor.execute('''
                        DELETE FROM anonymization_log 
                        WHERE data_record_id = ?
                    ''', (record_id,))
                
                conn.commit()
                conn.close()
                
                result = {
                    'deleted_records': deleted_records,
                    'cleaned_access_logs': len(expired_records),
                    'cleaned_anonymization_logs': len(expired_records)
                }
                
                if deleted_records > 0:
                    self.logger.info(f"Cleaned up {deleted_records} expired data records")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired data: {e}")
            return {'error': str(e)}
    
    def get_privacy_status(self) -> Dict[str, Any]:
        """Get current privacy status and statistics."""
        try:
            conn = sqlite3.connect(self.privacy_db_path)
            cursor = conn.cursor()
            
            # Get total records
            cursor.execute('SELECT COUNT(*) FROM data_records')
            total_records = cursor.fetchone()[0]
            
            # Get sensitive records
            cursor.execute('SELECT COUNT(*) FROM data_records WHERE is_sensitive = 1')
            sensitive_records = cursor.fetchone()[0]
            
            # Get anonymized records
            cursor.execute('SELECT COUNT(*) FROM data_records WHERE is_anonymized = 1')
            anonymized_records = cursor.fetchone()[0]
            
            # Get records by category
            cursor.execute('''
                SELECT data_category, COUNT(*) 
                FROM data_records 
                GROUP BY data_category
            ''')
            records_by_category = dict(cursor.fetchall())
            
            # Get recent access count
            cursor.execute('''
                SELECT COUNT(*) FROM data_access_log 
                WHERE accessed_at > ?
            ''', ((datetime.now() - timedelta(hours=24)).isoformat(),))
            recent_access_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'data_encryption_enabled': self.config.get('data_encryption_enabled', True),
                'secure_transmission_enabled': self.config.get('secure_transmission_enabled', True),
                'anonymization_enabled': self.config.get('anonymization_enabled', True),
                'gdpr_compliance_enabled': self.config.get('gdpr_compliance_enabled', True),
                'total_data_records': total_records,
                'sensitive_records': sensitive_records,
                'anonymized_records': anonymized_records,
                'records_by_category': records_by_category,
                'recent_access_24h': recent_access_count,
                'retention_policies_count': len(self.config.get('data_categories', {})),
                'last_cleanup': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get privacy status: {e}")
            return {'error': str(e)}
    
    def export_user_data(self, user_identifier: str) -> Dict[str, Any]:
        """
        Export all data related to a specific user (GDPR compliance).
        
        Args:
            user_identifier: User identifier to export data for
            
        Returns:
            Dictionary containing all user data
        """
        try:
            conn = sqlite3.connect(self.privacy_db_path)
            cursor = conn.cursor()
            
            # Find records that might contain user data
            cursor.execute('''
                SELECT id, data_category, created_at, is_sensitive, 
                       is_anonymized, metadata
                FROM data_records 
                WHERE metadata LIKE ?
            ''', (f'%{user_identifier}%',))
            
            user_records = cursor.fetchall()
            
            # Get access logs for user
            cursor.execute('''
                SELECT data_record_id, access_type, accessed_at, purpose
                FROM data_access_log 
                WHERE accessed_by = ?
            ''', (user_identifier,))
            
            access_logs = cursor.fetchall()
            
            conn.close()
            
            return {
                'user_identifier': user_identifier,
                'export_timestamp': datetime.now().isoformat(),
                'data_records': [
                    {
                        'record_id': record[0],
                        'category': record[1],
                        'created_at': record[2],
                        'is_sensitive': bool(record[3]),
                        'is_anonymized': bool(record[4]),
                        'metadata': json.loads(record[5]) if record[5] else None
                    }
                    for record in user_records
                ],
                'access_history': [
                    {
                        'record_id': log[0],
                        'access_type': log[1],
                        'accessed_at': log[2],
                        'purpose': log[3]
                    }
                    for log in access_logs
                ],
                'total_records': len(user_records),
                'total_access_events': len(access_logs)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export user data: {e}")
            return {'error': str(e)}
    
    def delete_user_data(self, user_identifier: str) -> Dict[str, int]:
        """
        Delete all data related to a specific user (GDPR right to be forgotten).
        
        Args:
            user_identifier: User identifier to delete data for
            
        Returns:
            Dictionary with deletion statistics
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.privacy_db_path)
                cursor = conn.cursor()
                
                # Find user records
                cursor.execute('''
                    SELECT id FROM data_records 
                    WHERE metadata LIKE ?
                ''', (f'%{user_identifier}%',))
                
                user_record_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete user records
                cursor.execute('''
                    DELETE FROM data_records 
                    WHERE metadata LIKE ?
                ''', (f'%{user_identifier}%',))
                
                deleted_records = cursor.rowcount
                
                # Delete related access logs
                deleted_access_logs = 0
                deleted_anonymization_logs = 0
                
                for record_id in user_record_ids:
                    cursor.execute('''
                        DELETE FROM data_access_log 
                        WHERE data_record_id = ?
                    ''', (record_id,))
                    deleted_access_logs += cursor.rowcount
                    
                    cursor.execute('''
                        DELETE FROM anonymization_log 
                        WHERE data_record_id = ?
                    ''', (record_id,))
                    deleted_anonymization_logs += cursor.rowcount
                
                # Also delete access logs by user
                cursor.execute('''
                    DELETE FROM data_access_log 
                    WHERE accessed_by = ?
                ''', (user_identifier,))
                deleted_access_logs += cursor.rowcount
                
                conn.commit()
                conn.close()
                
                result = {
                    'deleted_records': deleted_records,
                    'deleted_access_logs': deleted_access_logs,
                    'deleted_anonymization_logs': deleted_anonymization_logs
                }
                
                self.logger.info(f"Deleted user data for {user_identifier}: {result}")
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to delete user data: {e}")
            return {'error': str(e)}