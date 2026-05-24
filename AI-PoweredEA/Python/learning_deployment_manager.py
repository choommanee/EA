"""
Learning Deployment Manager

This module provides comprehensive deployment automation for the AI continuous learning system,
including automated deployment scripts, database migration, setup automation, and system health checks.
"""

import os
import json
import sqlite3
import subprocess
import shutil
import logging
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import hashlib
import zipfile
import tempfile


class LearningDeploymentManager:
    """
    Manages deployment automation for the AI continuous learning system including:
    - Automated deployment scripts for learning system
    - Database migration and setup automation
    - System health checks and validation scripts
    - Environment configuration and validation
    - Backup and rollback capabilities
    """
    
    def __init__(self, config_path: str = "deployment_config.json"):
        """
        Initialize the deployment manager.
        
        Args:
            config_path: Path to deployment configuration file
        """
        self.config_path = config_path
        self.config = self._load_deployment_config()
        self.logger = self._setup_deployment_logger()
        self.deployment_root = self.config.get('deployment_root', os.getcwd())
        self.backup_dir = self.config.get('backup_dir', 'backups')
        self.logs_dir = self.config.get('logs_dir', 'logs')
        
        # Ensure directories exist
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
    def _load_deployment_config(self) -> Dict[str, Any]:
        """Load deployment configuration from file."""
        default_config = {
            'deployment_root': os.getcwd(),
            'backup_dir': 'backups',
            'logs_dir': 'logs',
            'python_executable': sys.executable,
            'required_python_version': '3.8',
            'required_packages': [
                'numpy>=1.20.0',
                'pandas>=1.3.0',
                'scikit-learn>=1.0.0',
                'cryptography>=3.4.0'
            ],
            'database_files': [
                'learning_performance.db',
                'learning_audit.db',
                'learning_privacy.db'
            ],
            'config_files': [
                'learning_config.json',
                'learning_security_config.json',
                'learning_privacy_config.json'
            ],
            'python_modules': [
                'Python/performance_monitor.py',
                'Python/learning_data_collector.py',
                'Python/data_preprocessing_pipeline.py',
                'Python/model_evaluator.py',
                'Python/cross_validation_framework.py',
                'Python/model_manager.py',
                'Python/ai_system_integration.py',
                'Python/learning_coordinator.py',
                'Python/learning_notification_system.py',
                'Python/learning_configuration.py',
                'Python/learning_metrics_collector.py',
                'Python/learning_dashboard.py',
                'Python/ai_learning_pipeline_integration.py',
                'Python/ai_system_learning_compatibility.py',
                'Python/learning_security_manager.py',
                'Python/learning_data_privacy_manager.py'
            ],
            'health_check_endpoints': [
                'performance_monitor',
                'learning_coordinator',
                'model_manager',
                'security_manager',
                'privacy_manager'
            ],
            'deployment_environments': ['development', 'staging', 'production'],
            'backup_retention_days': 30,
            'health_check_timeout': 30,
            'migration_timeout': 300
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
            print(f"Warning: Failed to load deployment config: {e}, using defaults")
            
        return default_config
    
    def _setup_deployment_logger(self) -> logging.Logger:
        """Set up deployment-specific logger."""
        logger = logging.getLogger('learning_deployment')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # File handler
            log_file = os.path.join(self.config.get('logs_dir', 'logs'), 'deployment.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            console_handler = logging.StreamHandler()
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
        return logger
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate the deployment environment.
        
        Returns:
            Dictionary with validation results
        """
        self.logger.info("Starting environment validation...")
        
        validation_results = {
            'python_version': False,
            'required_packages': False,
            'file_permissions': False,
            'disk_space': False,
            'database_access': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check Python version
            python_version = sys.version_info
            required_version = tuple(map(int, self.config['required_python_version'].split('.')))
            
            if python_version >= required_version:
                validation_results['python_version'] = True
                self.logger.info(f"Python version check passed: {python_version}")
            else:
                error_msg = f"Python version {python_version} < required {required_version}"
                validation_results['errors'].append(error_msg)
                self.logger.error(error_msg)
            
            # Check required packages
            missing_packages = []
            for package in self.config['required_packages']:
                try:
                    package_name = package.split('>=')[0]
                    __import__(package_name)
                except ImportError:
                    missing_packages.append(package)
            
            if not missing_packages:
                validation_results['required_packages'] = True
                self.logger.info("All required packages are available")
            else:
                error_msg = f"Missing packages: {missing_packages}"
                validation_results['errors'].append(error_msg)
                self.logger.error(error_msg)
            
            # Check file permissions
            test_file = os.path.join(self.deployment_root, 'test_permissions.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                validation_results['file_permissions'] = True
                self.logger.info("File permissions check passed")
            except Exception as e:
                error_msg = f"File permissions check failed: {e}"
                validation_results['errors'].append(error_msg)
                self.logger.error(error_msg)
            
            # Check disk space (require at least 1GB free)
            try:
                statvfs = os.statvfs(self.deployment_root)
                free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
                
                if free_space_gb >= 1.0:
                    validation_results['disk_space'] = True
                    self.logger.info(f"Disk space check passed: {free_space_gb:.2f}GB free")
                else:
                    warning_msg = f"Low disk space: {free_space_gb:.2f}GB free"
                    validation_results['warnings'].append(warning_msg)
                    validation_results['disk_space'] = True  # Warning, not error
                    self.logger.warning(warning_msg)
            except Exception as e:
                warning_msg = f"Could not check disk space: {e}"
                validation_results['warnings'].append(warning_msg)
                validation_results['disk_space'] = True  # Assume OK if can't check
            
            # Check database access
            try:
                test_db = os.path.join(self.deployment_root, 'validation_test_db.db')
                conn = sqlite3.connect(test_db)
                conn.execute('CREATE TABLE IF NOT EXISTS validation_test (id INTEGER)')
                conn.execute('INSERT INTO validation_test VALUES (1)')
                conn.execute('SELECT * FROM validation_test')
                conn.close()
                if os.path.exists(test_db):
                    os.remove(test_db)
                
                validation_results['database_access'] = True
                self.logger.info("Database access check passed")
            except Exception as e:
                error_msg = f"Database access check failed: {e}"
                validation_results['errors'].append(error_msg)
                self.logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Environment validation failed: {e}"
            validation_results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        # Overall validation status
        validation_results['overall_status'] = (
            validation_results['python_version'] and
            validation_results['required_packages'] and
            validation_results['file_permissions'] and
            validation_results['disk_space'] and
            validation_results['database_access']
        )
        
        self.logger.info(f"Environment validation completed: {'PASSED' if validation_results['overall_status'] else 'FAILED'}")
        return validation_results
    
    def create_backup(self, backup_name: str = None) -> str:
        """
        Create a backup of the current system.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Path to the created backup
        """
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        self.logger.info(f"Creating backup: {backup_path}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                # Backup Python modules
                for module_path in self.config['python_modules']:
                    if os.path.exists(module_path):
                        backup_zip.write(module_path, module_path)
                        self.logger.debug(f"Backed up module: {module_path}")
                
                # Backup configuration files
                for config_file in self.config['config_files']:
                    if os.path.exists(config_file):
                        backup_zip.write(config_file, config_file)
                        self.logger.debug(f"Backed up config: {config_file}")
                
                # Backup database files
                for db_file in self.config['database_files']:
                    if os.path.exists(db_file):
                        backup_zip.write(db_file, db_file)
                        self.logger.debug(f"Backed up database: {db_file}")
                
                # Backup deployment config
                if os.path.exists(self.config_path):
                    backup_zip.write(self.config_path, self.config_path)
                
                # Add backup metadata
                metadata = {
                    'backup_name': backup_name,
                    'created_at': datetime.now().isoformat(),
                    'python_version': sys.version,
                    'deployment_root': self.deployment_root,
                    'files_backed_up': len(backup_zip.namelist())
                }
                
                backup_zip.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
            
            self.logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore from a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if restore was successful
        """
        self.logger.info(f"Restoring from backup: {backup_path}")
        
        if not os.path.exists(backup_path):
            self.logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Create a temporary restore backup first
            temp_backup = self.create_backup("pre_restore_backup")
            
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                # Read metadata
                try:
                    metadata_content = backup_zip.read('backup_metadata.json')
                    metadata = json.loads(metadata_content.decode('utf-8'))
                    self.logger.info(f"Restoring backup from: {metadata['created_at']}")
                except:
                    self.logger.warning("No metadata found in backup")
                
                # Extract all files
                backup_zip.extractall(self.deployment_root)
                
            self.logger.info("Backup restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
    
    def migrate_databases(self) -> Dict[str, bool]:
        """
        Perform database migrations.
        
        Returns:
            Dictionary with migration results for each database
        """
        self.logger.info("Starting database migrations...")
        
        migration_results = {}
        
        # Define migration scripts for each database
        migrations = {
            'learning_performance.db': [
                '''CREATE TABLE IF NOT EXISTS performance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    accuracy REAL,
                    profit_loss REAL,
                    market_conditions TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''',
                '''CREATE INDEX IF NOT EXISTS idx_performance_timestamp 
                   ON performance_records(timestamp)''',
                '''CREATE INDEX IF NOT EXISTS idx_performance_signal_id 
                   ON performance_records(signal_id)'''
            ],
            'learning_audit.db': [
                '''CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    resource TEXT,
                    success BOOLEAN NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    session_id TEXT
                )''',
                '''CREATE TABLE IF NOT EXISTS access_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    ip_address TEXT,
                    is_active BOOLEAN DEFAULT 1
                )''',
                '''CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                   ON audit_log(timestamp)''',
                '''CREATE INDEX IF NOT EXISTS idx_audit_user_id 
                   ON audit_log(user_id)'''
            ],
            'learning_privacy.db': [
                '''CREATE TABLE IF NOT EXISTS data_records (
                    id TEXT PRIMARY KEY,
                    data_category TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    is_sensitive BOOLEAN DEFAULT 0,
                    is_anonymized BOOLEAN DEFAULT 0,
                    encryption_method TEXT,
                    data_hash TEXT,
                    metadata TEXT
                )''',
                '''CREATE TABLE IF NOT EXISTS retention_policies (
                    data_category TEXT PRIMARY KEY,
                    retention_days INTEGER NOT NULL,
                    is_sensitive BOOLEAN DEFAULT 0,
                    anonymization_days INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )''',
                '''CREATE INDEX IF NOT EXISTS idx_data_records_category 
                   ON data_records(data_category)''',
                '''CREATE INDEX IF NOT EXISTS idx_data_records_expires 
                   ON data_records(expires_at)'''
            ]
        }
        
        for db_name, migration_scripts in migrations.items():
            try:
                db_path = os.path.join(self.deployment_root, db_name)
                self.logger.info(f"Migrating database: {db_name}")
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                for script in migration_scripts:
                    cursor.execute(script)
                    self.logger.debug(f"Executed migration script for {db_name}")
                
                conn.commit()
                conn.close()
                
                migration_results[db_name] = True
                self.logger.info(f"Successfully migrated: {db_name}")
                
            except Exception as e:
                migration_results[db_name] = False
                self.logger.error(f"Failed to migrate {db_name}: {e}")
        
        self.logger.info(f"Database migrations completed: {sum(migration_results.values())}/{len(migration_results)} successful")
        return migration_results
    
    def install_dependencies(self) -> bool:
        """
        Install required Python dependencies.
        
        Returns:
            True if installation was successful
        """
        self.logger.info("Installing dependencies...")
        
        try:
            python_executable = self.config['python_executable']
            
            for package in self.config['required_packages']:
                self.logger.info(f"Installing package: {package}")
                
                result = subprocess.run([
                    python_executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.logger.info(f"Successfully installed: {package}")
                else:
                    self.logger.error(f"Failed to install {package}: {result.stderr}")
                    return False
            
            self.logger.info("All dependencies installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check.
        
        Returns:
            Dictionary with health check results
        """
        self.logger.info("Starting system health check...")
        
        health_results = {
            'overall_status': False,
            'components': {},
            'database_status': {},
            'file_integrity': {},
            'performance_metrics': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check component health
            for component in self.config['health_check_endpoints']:
                health_results['components'][component] = self._check_component_health(component)
            
            # Check database health
            for db_file in self.config['database_files']:
                health_results['database_status'][db_file] = self._check_database_health(db_file)
            
            # Check file integrity
            for module_path in self.config['python_modules']:
                health_results['file_integrity'][module_path] = self._check_file_integrity(module_path)
            
            # Performance metrics
            health_results['performance_metrics'] = self._collect_performance_metrics()
            
            # Overall status
            component_health = all(health_results['components'].values())
            database_health = all(health_results['database_status'].values())
            file_integrity = all(health_results['file_integrity'].values())
            
            health_results['overall_status'] = component_health and database_health and file_integrity
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_results['error'] = str(e)
        
        status = "HEALTHY" if health_results['overall_status'] else "UNHEALTHY"
        self.logger.info(f"System health check completed: {status}")
        
        return health_results
    
    def _check_component_health(self, component: str) -> bool:
        """Check health of a specific component."""
        try:
            # Try to import and instantiate the component
            if component == 'performance_monitor':
                from Python.performance_monitor import PerformanceMonitor
                monitor = PerformanceMonitor()
                return True
            elif component == 'learning_coordinator':
                from Python.learning_coordinator import LearningCoordinator
                coordinator = LearningCoordinator()
                return True
            elif component == 'model_manager':
                from Python.model_manager import ModelManager
                manager = ModelManager()
                return True
            elif component == 'security_manager':
                from Python.learning_security_manager import LearningSecurityManager
                security = LearningSecurityManager()
                return True
            elif component == 'privacy_manager':
                from Python.learning_data_privacy_manager import LearningDataPrivacyManager
                privacy = LearningDataPrivacyManager()
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.warning(f"Component {component} health check failed: {e}")
            return False
    
    def _check_database_health(self, db_file: str) -> bool:
        """Check health of a database file."""
        try:
            db_path = os.path.join(self.deployment_root, db_file)
            
            if not os.path.exists(db_path):
                return False
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Basic connectivity test
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            
            conn.close()
            
            return result is not None
            
        except Exception as e:
            self.logger.warning(f"Database {db_file} health check failed: {e}")
            return False
    
    def _check_file_integrity(self, file_path: str) -> bool:
        """Check integrity of a file."""
        try:
            if not os.path.exists(file_path):
                return False
            
            # Check if file is readable and has content
            with open(file_path, 'r') as f:
                content = f.read()
                return len(content) > 0
                
        except Exception as e:
            self.logger.warning(f"File {file_path} integrity check failed: {e}")
            return False
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect basic performance metrics."""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage(self.deployment_root).percent
            }
        except ImportError:
            # psutil not available, return basic metrics
            try:
                statvfs = os.statvfs(self.deployment_root)
                disk_usage = (1 - (statvfs.f_bavail / statvfs.f_blocks)) * 100
                
                return {
                    'disk_usage_percent': disk_usage,
                    'note': 'Limited metrics (psutil not available)'
                }
            except:
                return {'note': 'Performance metrics not available'}
    
    def deploy_system(self, environment: str = 'development', 
                     skip_backup: bool = False) -> Dict[str, Any]:
        """
        Deploy the complete learning system.
        
        Args:
            environment: Target environment (development, staging, production)
            skip_backup: Skip backup creation
            
        Returns:
            Dictionary with deployment results
        """
        self.logger.info(f"Starting deployment to {environment} environment...")
        
        deployment_results = {
            'environment': environment,
            'start_time': datetime.now().isoformat(),
            'steps': {},
            'overall_success': False
        }
        
        try:
            # Step 1: Environment validation
            self.logger.info("Step 1: Validating environment...")
            validation_result = self.validate_environment()
            deployment_results['steps']['environment_validation'] = validation_result['overall_status']
            
            if not validation_result['overall_status']:
                self.logger.error("Environment validation failed, aborting deployment")
                return deployment_results
            
            # Step 2: Create backup (unless skipped)
            if not skip_backup:
                self.logger.info("Step 2: Creating backup...")
                backup_path = self.create_backup(f"pre_deploy_{environment}")
                deployment_results['steps']['backup_creation'] = True
                deployment_results['backup_path'] = backup_path
            else:
                deployment_results['steps']['backup_creation'] = True  # Skipped
            
            # Step 3: Install dependencies
            self.logger.info("Step 3: Installing dependencies...")
            deps_result = self.install_dependencies()
            deployment_results['steps']['dependency_installation'] = deps_result
            
            if not deps_result:
                self.logger.error("Dependency installation failed")
                return deployment_results
            
            # Step 4: Database migration
            self.logger.info("Step 4: Migrating databases...")
            migration_results = self.migrate_databases()
            deployment_results['steps']['database_migration'] = all(migration_results.values())
            deployment_results['migration_details'] = migration_results
            
            # Step 5: Health check
            self.logger.info("Step 5: Performing health check...")
            health_results = self.perform_health_check()
            deployment_results['steps']['health_check'] = health_results['overall_status']
            deployment_results['health_details'] = health_results
            
            # Overall success
            deployment_results['overall_success'] = all([
                deployment_results['steps']['environment_validation'],
                deployment_results['steps']['backup_creation'],
                deployment_results['steps']['dependency_installation'],
                deployment_results['steps']['database_migration'],
                deployment_results['steps']['health_check']
            ])
            
            deployment_results['end_time'] = datetime.now().isoformat()
            
            if deployment_results['overall_success']:
                self.logger.info(f"Deployment to {environment} completed successfully!")
            else:
                self.logger.error(f"Deployment to {environment} failed!")
            
        except Exception as e:
            self.logger.error(f"Deployment failed with exception: {e}")
            deployment_results['error'] = str(e)
            deployment_results['end_time'] = datetime.now().isoformat()
        
        return deployment_results
    
    def cleanup_old_backups(self) -> int:
        """
        Clean up old backup files based on retention policy.
        
        Returns:
            Number of backups cleaned up
        """
        self.logger.info("Cleaning up old backups...")
        
        try:
            retention_days = self.config.get('backup_retention_days', 30)
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
            
            cleaned_count = 0
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        self.logger.info(f"Removed old backup: {filename}")
            
            self.logger.info(f"Cleaned up {cleaned_count} old backups")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """
        Get current deployment status and information.
        
        Returns:
            Dictionary with deployment status
        """
        try:
            # Get system information
            status = {
                'deployment_root': self.deployment_root,
                'python_version': sys.version,
                'timestamp': datetime.now().isoformat(),
                'backup_count': 0,
                'log_files': [],
                'database_files': {},
                'module_files': {}
            }
            
            # Count backups
            if os.path.exists(self.backup_dir):
                backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.zip')]
                status['backup_count'] = len(backup_files)
            
            # List log files
            if os.path.exists(self.logs_dir):
                status['log_files'] = [f for f in os.listdir(self.logs_dir) if f.endswith('.log')]
            
            # Check database files
            for db_file in self.config['database_files']:
                db_path = os.path.join(self.deployment_root, db_file)
                status['database_files'][db_file] = {
                    'exists': os.path.exists(db_path),
                    'size': os.path.getsize(db_path) if os.path.exists(db_path) else 0
                }
            
            # Check module files
            for module_path in self.config['python_modules']:
                status['module_files'][module_path] = {
                    'exists': os.path.exists(module_path),
                    'size': os.path.getsize(module_path) if os.path.exists(module_path) else 0
                }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get deployment status: {e}")
            return {'error': str(e)}