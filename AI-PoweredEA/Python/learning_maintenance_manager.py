"""
Learning Maintenance Manager

This module provides comprehensive maintenance and cleanup utilities for the AI continuous learning system,
including automated data cleanup, model optimization, system maintenance scheduling, and performance optimization.
"""

import os
import json
import sqlite3
import shutil
import logging
import time
import threading
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import hashlib
import zipfile
import tempfile
import gc
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class LearningMaintenanceManager:
    """
    Manages maintenance and cleanup for the AI continuous learning system including:
    - Automated data cleanup and archival tools
    - Model cleanup and optimization utilities
    - System maintenance scheduling and automation
    - Performance monitoring and optimization
    - Resource usage optimization
    """
    
    def __init__(self, config_path: str = "maintenance_config.json"):
        """
        Initialize the maintenance manager.
        
        Args:
            config_path: Path to maintenance configuration file
        """
        self.config_path = config_path
        self.config = self._load_maintenance_config()
        self.logger = self._setup_maintenance_logger()
        self.maintenance_root = self.config.get('maintenance_root', os.getcwd())
        self.archive_dir = self.config.get('archive_dir', 'archives')
        self.temp_dir = self.config.get('temp_dir', 'temp')
        self.logs_dir = self.config.get('logs_dir', 'logs')
        
        # Ensure directories exist
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Maintenance scheduler
        self.scheduler_running = False
        self.scheduler_thread = None
        
    def _load_maintenance_config(self) -> Dict[str, Any]:
        """Load maintenance configuration from file."""
        default_config = {
            'maintenance_root': os.getcwd(),
            'archive_dir': 'archives',
            'temp_dir': 'temp',
            'logs_dir': 'logs',
            'database_files': [
                'learning_performance.db',
                'learning_audit.db',
                'learning_privacy.db'
            ],
            'model_directories': [
                'models',
                'model_cache'
            ],
            'log_files': [
                'learning_performance.log',
                'learning_security.log',
                'learning_privacy.log',
                'deployment.log'
            ],
            'cleanup_policies': {
                'old_data_days': 90,
                'old_logs_days': 30,
                'old_models_days': 60,
                'temp_files_hours': 24,
                'archive_retention_days': 365
            },
            'optimization_settings': {
                'database_vacuum_enabled': True,
                'model_compression_enabled': True,
                'memory_cleanup_enabled': True,
                'disk_cleanup_enabled': True
            },
            'maintenance_schedule': {
                'daily_cleanup_time': '02:00',
                'weekly_optimization_day': 'sunday',
                'weekly_optimization_time': '03:00',
                'monthly_archive_day': 1,
                'monthly_archive_time': '04:00'
            },
            'performance_thresholds': {
                'max_cpu_percent': 80,
                'max_memory_percent': 85,
                'max_disk_percent': 90,
                'min_free_space_gb': 5
            },
            'notification_settings': {
                'enabled': True,
                'email_notifications': False,
                'log_notifications': True
            }
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
            print(f"Warning: Failed to load maintenance config: {e}, using defaults")
            
        return default_config
    
    def _setup_maintenance_logger(self) -> logging.Logger:
        """Set up maintenance-specific logger."""
        logger = logging.getLogger('learning_maintenance')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # File handler
            log_file = os.path.join(self.config.get('logs_dir', 'logs'), 'maintenance.log')
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
    
    def cleanup_old_data(self) -> Dict[str, Any]:
        """
        Clean up old data based on retention policies.
        
        Returns:
            Dictionary with cleanup results
        """
        self.logger.info("Starting old data cleanup...")
        
        cleanup_results = {
            'databases_cleaned': {},
            'logs_cleaned': {},
            'temp_files_cleaned': 0,
            'total_space_freed_mb': 0,
            'errors': []
        }
        
        try:
            old_data_days = self.config['cleanup_policies']['old_data_days']
            old_logs_days = self.config['cleanup_policies']['old_logs_days']
            temp_files_hours = self.config['cleanup_policies']['temp_files_hours']
            
            cutoff_date = datetime.now() - timedelta(days=old_data_days)
            log_cutoff_date = datetime.now() - timedelta(days=old_logs_days)
            temp_cutoff_date = datetime.now() - timedelta(hours=temp_files_hours)
            
            # Clean up database records
            for db_file in self.config['database_files']:
                db_path = os.path.join(self.maintenance_root, db_file)
                if os.path.exists(db_path):
                    try:
                        cleaned_records = self._cleanup_database_records(db_path, cutoff_date)
                        cleanup_results['databases_cleaned'][db_file] = cleaned_records
                        self.logger.info(f"Cleaned {cleaned_records} old records from {db_file}")
                    except Exception as e:
                        error_msg = f"Failed to clean database {db_file}: {e}"
                        cleanup_results['errors'].append(error_msg)
                        self.logger.error(error_msg)
            
            # Clean up log files
            for log_file in self.config['log_files']:
                log_path = os.path.join(self.logs_dir, log_file)
                if os.path.exists(log_path):
                    try:
                        original_size = os.path.getsize(log_path)
                        cleaned_lines = self._cleanup_log_file(log_path, log_cutoff_date)
                        new_size = os.path.getsize(log_path)
                        space_freed = (original_size - new_size) / (1024 * 1024)  # MB
                        
                        cleanup_results['logs_cleaned'][log_file] = {
                            'lines_removed': cleaned_lines,
                            'space_freed_mb': space_freed
                        }
                        cleanup_results['total_space_freed_mb'] += space_freed
                        
                        self.logger.info(f"Cleaned {cleaned_lines} old log entries from {log_file}")
                    except Exception as e:
                        error_msg = f"Failed to clean log file {log_file}: {e}"
                        cleanup_results['errors'].append(error_msg)
                        self.logger.error(error_msg)
            
            # Clean up temporary files
            if os.path.exists(self.temp_dir):
                temp_files_cleaned = 0
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_time < temp_cutoff_date:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                temp_files_cleaned += 1
                                cleanup_results['total_space_freed_mb'] += file_size / (1024 * 1024)
                        except Exception as e:
                            self.logger.warning(f"Failed to remove temp file {file_path}: {e}")
                
                cleanup_results['temp_files_cleaned'] = temp_files_cleaned
                self.logger.info(f"Cleaned {temp_files_cleaned} temporary files")
            
            self.logger.info(f"Data cleanup completed. Total space freed: {cleanup_results['total_space_freed_mb']:.2f} MB")
            
        except Exception as e:
            error_msg = f"Data cleanup failed: {e}"
            cleanup_results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return cleanup_results
    
    def _cleanup_database_records(self, db_path: str, cutoff_date: datetime) -> int:
        """Clean up old records from a database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        total_cleaned = 0
        cutoff_str = cutoff_date.isoformat()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            # Check if table has timestamp columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            timestamp_columns = []
            for column in columns:
                column_name = column[1].lower()
                if any(ts_col in column_name for ts_col in ['timestamp', 'created_at', 'updated_at', 'date']):
                    timestamp_columns.append(column[1])
            
            # Clean old records based on timestamp columns
            for ts_column in timestamp_columns:
                try:
                    cursor.execute(f"DELETE FROM {table_name} WHERE {ts_column} < ?", (cutoff_str,))
                    cleaned_count = cursor.rowcount
                    total_cleaned += cleaned_count
                    if cleaned_count > 0:
                        self.logger.debug(f"Cleaned {cleaned_count} records from {table_name}.{ts_column}")
                    break  # Only clean based on first timestamp column found
                except Exception as e:
                    self.logger.warning(f"Failed to clean {table_name}.{ts_column}: {e}")
        
        conn.commit()
        conn.close()
        
        return total_cleaned
    
    def _cleanup_log_file(self, log_path: str, cutoff_date: datetime) -> int:
        """Clean up old entries from a log file."""
        if not os.path.exists(log_path):
            return 0
        
        temp_file = log_path + '.tmp'
        lines_removed = 0
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as infile:
                with open(temp_file, 'w', encoding='utf-8') as outfile:
                    for line in infile:
                        # Try to extract timestamp from log line
                        try:
                            # Common log format: YYYY-MM-DD HH:MM:SS
                            if len(line) >= 19:
                                timestamp_str = line[:19]
                                log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                
                                if log_time >= cutoff_date:
                                    outfile.write(line)
                                else:
                                    lines_removed += 1
                            else:
                                outfile.write(line)  # Keep lines without timestamps
                        except ValueError:
                            outfile.write(line)  # Keep lines with invalid timestamps
            
            # Replace original file with cleaned version
            shutil.move(temp_file, log_path)
            
        except Exception as e:
            # Clean up temp file if something went wrong
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e
        
        return lines_removed
    
    def optimize_models(self) -> Dict[str, Any]:
        """
        Optimize and clean up model files.
        
        Returns:
            Dictionary with optimization results
        """
        self.logger.info("Starting model optimization...")
        
        optimization_results = {
            'models_optimized': 0,
            'models_compressed': 0,
            'old_models_removed': 0,
            'space_saved_mb': 0,
            'errors': []
        }
        
        try:
            old_models_days = self.config['cleanup_policies']['old_models_days']
            cutoff_date = datetime.now() - timedelta(days=old_models_days)
            
            for model_dir in self.config['model_directories']:
                model_path = os.path.join(self.maintenance_root, model_dir)
                if os.path.exists(model_path):
                    try:
                        dir_results = self._optimize_model_directory(model_path, cutoff_date)
                        
                        optimization_results['models_optimized'] += dir_results['optimized']
                        optimization_results['models_compressed'] += dir_results['compressed']
                        optimization_results['old_models_removed'] += dir_results['removed']
                        optimization_results['space_saved_mb'] += dir_results['space_saved_mb']
                        
                        self.logger.info(f"Optimized {dir_results['optimized']} models in {model_dir}")
                        
                    except Exception as e:
                        error_msg = f"Failed to optimize models in {model_dir}: {e}"
                        optimization_results['errors'].append(error_msg)
                        self.logger.error(error_msg)
            
            self.logger.info(f"Model optimization completed. Space saved: {optimization_results['space_saved_mb']:.2f} MB")
            
        except Exception as e:
            error_msg = f"Model optimization failed: {e}"
            optimization_results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return optimization_results
    
    def _optimize_model_directory(self, model_dir: str, cutoff_date: datetime) -> Dict[str, Any]:
        """Optimize models in a specific directory."""
        results = {
            'optimized': 0,
            'compressed': 0,
            'removed': 0,
            'space_saved_mb': 0
        }
        
        for root, dirs, files in os.walk(model_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    original_size = os.path.getsize(file_path)
                    
                    # Remove old models
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        results['removed'] += 1
                        results['space_saved_mb'] += original_size / (1024 * 1024)
                        self.logger.debug(f"Removed old model: {file}")
                        continue
                    
                    # Compress models if enabled
                    if (self.config['optimization_settings']['model_compression_enabled'] and
                        file.endswith(('.pkl', '.joblib', '.model')) and
                        not file.endswith('.gz')):
                        
                        compressed_path = file_path + '.gz'
                        if not os.path.exists(compressed_path):
                            self._compress_file(file_path, compressed_path)
                            new_size = os.path.getsize(compressed_path)
                            
                            if new_size < original_size:
                                os.remove(file_path)  # Remove original
                                results['compressed'] += 1
                                results['space_saved_mb'] += (original_size - new_size) / (1024 * 1024)
                                self.logger.debug(f"Compressed model: {file}")
                            else:
                                os.remove(compressed_path)  # Remove compressed if not smaller
                    
                    results['optimized'] += 1
                    
                except Exception as e:
                    self.logger.warning(f"Failed to optimize model {file_path}: {e}")
        
        return results
    
    def _compress_file(self, source_path: str, target_path: str):
        """Compress a file using gzip."""
        import gzip
        
        with open(source_path, 'rb') as f_in:
            with gzip.open(target_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def optimize_databases(self) -> Dict[str, Any]:
        """
        Optimize database performance.
        
        Returns:
            Dictionary with optimization results
        """
        self.logger.info("Starting database optimization...")
        
        optimization_results = {
            'databases_vacuumed': 0,
            'indexes_rebuilt': 0,
            'space_reclaimed_mb': 0,
            'errors': []
        }
        
        try:
            if self.config['optimization_settings']['database_vacuum_enabled']:
                for db_file in self.config['database_files']:
                    db_path = os.path.join(self.maintenance_root, db_file)
                    if os.path.exists(db_path):
                        try:
                            original_size = os.path.getsize(db_path)
                            
                            # Vacuum database
                            conn = sqlite3.connect(db_path)
                            cursor = conn.cursor()
                            
                            cursor.execute('VACUUM')
                            cursor.execute('ANALYZE')
                            
                            # Rebuild indexes
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                            indexes = cursor.fetchall()
                            
                            for (index_name,) in indexes:
                                if not index_name.startswith('sqlite_'):
                                    cursor.execute(f'REINDEX {index_name}')
                                    optimization_results['indexes_rebuilt'] += 1
                            
                            conn.close()
                            
                            new_size = os.path.getsize(db_path)
                            space_reclaimed = (original_size - new_size) / (1024 * 1024)
                            
                            optimization_results['databases_vacuumed'] += 1
                            optimization_results['space_reclaimed_mb'] += space_reclaimed
                            
                            self.logger.info(f"Optimized database {db_file}, reclaimed {space_reclaimed:.2f} MB")
                            
                        except Exception as e:
                            error_msg = f"Failed to optimize database {db_file}: {e}"
                            optimization_results['errors'].append(error_msg)
                            self.logger.error(error_msg)
            
            self.logger.info(f"Database optimization completed. Space reclaimed: {optimization_results['space_reclaimed_mb']:.2f} MB")
            
        except Exception as e:
            error_msg = f"Database optimization failed: {e}"
            optimization_results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return optimization_results
    
    def cleanup_memory(self) -> Dict[str, Any]:
        """
        Perform memory cleanup and optimization.
        
        Returns:
            Dictionary with memory cleanup results
        """
        self.logger.info("Starting memory cleanup...")
        
        cleanup_results = {
            'memory_before_mb': 0,
            'memory_after_mb': 0,
            'memory_freed_mb': 0,
            'garbage_collected': 0
        }
        
        try:
            if self.config['optimization_settings']['memory_cleanup_enabled']:
                if PSUTIL_AVAILABLE:
                    # Get memory usage before cleanup
                    process = psutil.Process()
                    memory_before = process.memory_info().rss / (1024 * 1024)  # MB
                    cleanup_results['memory_before_mb'] = memory_before
                    
                    # Force garbage collection
                    collected = gc.collect()
                    cleanup_results['garbage_collected'] = collected
                    
                    # Get memory usage after cleanup
                    memory_after = process.memory_info().rss / (1024 * 1024)  # MB
                    cleanup_results['memory_after_mb'] = memory_after
                    cleanup_results['memory_freed_mb'] = memory_before - memory_after
                    
                    self.logger.info(f"Memory cleanup completed. Freed {cleanup_results['memory_freed_mb']:.2f} MB")
                else:
                    # Basic memory cleanup without detailed metrics
                    collected = gc.collect()
                    cleanup_results['garbage_collected'] = collected
                    cleanup_results['memory_before_mb'] = 0
                    cleanup_results['memory_after_mb'] = 0
                    cleanup_results['memory_freed_mb'] = 0
                    
                    self.logger.info(f"Memory cleanup completed. Collected {collected} objects")
                
        except Exception as e:
            error_msg = f"Memory cleanup failed: {e}"
            self.logger.error(error_msg)
            cleanup_results['error'] = error_msg
        
        return cleanup_results
    
    def archive_old_data(self) -> Dict[str, Any]:
        """
        Archive old data to compressed archives.
        
        Returns:
            Dictionary with archival results
        """
        self.logger.info("Starting data archival...")
        
        archival_results = {
            'archives_created': 0,
            'files_archived': 0,
            'space_saved_mb': 0,
            'errors': []
        }
        
        try:
            archive_retention_days = self.config['cleanup_policies']['archive_retention_days']
            cutoff_date = datetime.now() - timedelta(days=archive_retention_days)
            
            # Create monthly archive
            archive_name = f"learning_data_archive_{datetime.now().strftime('%Y_%m')}.zip"
            archive_path = os.path.join(self.archive_dir, archive_name)
            
            if not os.path.exists(archive_path):
                files_to_archive = []
                total_size_before = 0
                
                # Find files to archive
                for db_file in self.config['database_files']:
                    db_path = os.path.join(self.maintenance_root, db_file)
                    if os.path.exists(db_path):
                        # Create a copy of database with old data only
                        archive_db_path = self._create_archive_database(db_path, cutoff_date)
                        if archive_db_path:
                            files_to_archive.append((archive_db_path, f"archived_{db_file}"))
                            total_size_before += os.path.getsize(archive_db_path)
                
                # Create archive
                if files_to_archive:
                    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive_zip:
                        for file_path, archive_name in files_to_archive:
                            archive_zip.write(file_path, archive_name)
                            archival_results['files_archived'] += 1
                        
                        # Add metadata
                        metadata = {
                            'created_at': datetime.now().isoformat(),
                            'cutoff_date': cutoff_date.isoformat(),
                            'files_count': len(files_to_archive),
                            'original_size_mb': total_size_before / (1024 * 1024)
                        }
                        archive_zip.writestr('archive_metadata.json', json.dumps(metadata, indent=2))
                    
                    # Calculate space saved
                    archive_size = os.path.getsize(archive_path)
                    space_saved = (total_size_before - archive_size) / (1024 * 1024)
                    
                    archival_results['archives_created'] = 1
                    archival_results['space_saved_mb'] = space_saved
                    
                    # Clean up temporary files
                    for file_path, _ in files_to_archive:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    
                    self.logger.info(f"Created archive {archive_name}, saved {space_saved:.2f} MB")
            
        except Exception as e:
            error_msg = f"Data archival failed: {e}"
            archival_results['errors'].append(error_msg)
            self.logger.error(error_msg)
        
        return archival_results
    
    def _create_archive_database(self, db_path: str, cutoff_date: datetime) -> Optional[str]:
        """Create a database containing only old data for archival."""
        try:
            temp_db_path = os.path.join(self.temp_dir, f"archive_{os.path.basename(db_path)}")
            
            # Copy database structure
            shutil.copy2(db_path, temp_db_path)
            
            # Remove recent data, keep only old data
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            cutoff_str = cutoff_date.isoformat()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                # Check if table has timestamp columns
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for column in columns:
                    column_name = column[1].lower()
                    if any(ts_col in column_name for ts_col in ['timestamp', 'created_at', 'updated_at', 'date']):
                        try:
                            # Keep only old data (before cutoff)
                            cursor.execute(f"DELETE FROM {table_name} WHERE {column[1]} >= ?", (cutoff_str,))
                            break
                        except Exception:
                            continue
            
            conn.commit()
            conn.close()
            
            # Check if database has any data
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            has_data = False
            for (table_name,) in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                if count > 0:
                    has_data = True
                    break
            
            conn.close()
            
            if has_data:
                return temp_db_path
            else:
                os.remove(temp_db_path)
                return None
                
        except Exception as e:
            self.logger.warning(f"Failed to create archive database for {db_path}: {e}")
            return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status and resource usage.
        
        Returns:
            Dictionary with system status
        """
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_usage_percent': 0,
                'free_space_gb': 0,
                'database_sizes_mb': {},
                'log_sizes_mb': {},
                'model_count': 0,
                'temp_files_count': 0,
                'archive_count': 0,
                'maintenance_needed': False,
                'recommendations': []
            }
            
            # Get system metrics
            if PSUTIL_AVAILABLE:
                try:
                    status['cpu_percent'] = psutil.cpu_percent(interval=1)
                    status['memory_percent'] = psutil.virtual_memory().percent
                    
                    disk_usage = psutil.disk_usage(self.maintenance_root)
                    status['disk_usage_percent'] = (disk_usage.used / disk_usage.total) * 100
                    status['free_space_gb'] = disk_usage.free / (1024**3)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to get system metrics: {e}")
            else:
                # Fallback metrics without psutil
                try:
                    import shutil
                    total, used, free = shutil.disk_usage(self.maintenance_root)
                    status['disk_usage_percent'] = (used / total) * 100
                    status['free_space_gb'] = free / (1024**3)
                    status['cpu_percent'] = 0  # Not available
                    status['memory_percent'] = 0  # Not available
                except Exception as e:
                    self.logger.warning(f"Failed to get basic system metrics: {e}")
            
            # Get database sizes
            for db_file in self.config['database_files']:
                db_path = os.path.join(self.maintenance_root, db_file)
                if os.path.exists(db_path):
                    size_mb = os.path.getsize(db_path) / (1024 * 1024)
                    status['database_sizes_mb'][db_file] = size_mb
            
            # Get log sizes
            for log_file in self.config['log_files']:
                log_path = os.path.join(self.logs_dir, log_file)
                if os.path.exists(log_path):
                    size_mb = os.path.getsize(log_path) / (1024 * 1024)
                    status['log_sizes_mb'][log_file] = size_mb
            
            # Count models
            for model_dir in self.config['model_directories']:
                model_path = os.path.join(self.maintenance_root, model_dir)
                if os.path.exists(model_path):
                    for root, dirs, files in os.walk(model_path):
                        status['model_count'] += len(files)
            
            # Count temp files
            if os.path.exists(self.temp_dir):
                for root, dirs, files in os.walk(self.temp_dir):
                    status['temp_files_count'] += len(files)
            
            # Count archives
            if os.path.exists(self.archive_dir):
                archives = [f for f in os.listdir(self.archive_dir) if f.endswith('.zip')]
                status['archive_count'] = len(archives)
            
            # Check if maintenance is needed
            thresholds = self.config['performance_thresholds']
            
            if status['cpu_percent'] > thresholds['max_cpu_percent']:
                status['maintenance_needed'] = True
                status['recommendations'].append("High CPU usage detected - consider memory cleanup")
            
            if status['memory_percent'] > thresholds['max_memory_percent']:
                status['maintenance_needed'] = True
                status['recommendations'].append("High memory usage detected - run memory cleanup")
            
            if status['disk_usage_percent'] > thresholds['max_disk_percent']:
                status['maintenance_needed'] = True
                status['recommendations'].append("High disk usage detected - run data cleanup")
            
            if status['free_space_gb'] < thresholds['min_free_space_gb']:
                status['maintenance_needed'] = True
                status['recommendations'].append("Low free space - archive old data")
            
            if status['temp_files_count'] > 100:
                status['maintenance_needed'] = True
                status['recommendations'].append("Many temporary files - run cleanup")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {'error': str(e)}
    
    def run_full_maintenance(self) -> Dict[str, Any]:
        """
        Run complete maintenance cycle.
        
        Returns:
            Dictionary with maintenance results
        """
        self.logger.info("Starting full maintenance cycle...")
        
        maintenance_results = {
            'start_time': datetime.now().isoformat(),
            'data_cleanup': {},
            'model_optimization': {},
            'database_optimization': {},
            'memory_cleanup': {},
            'archival': {},
            'overall_success': False,
            'total_space_saved_mb': 0
        }
        
        try:
            # Step 1: Clean up old data
            self.logger.info("Step 1: Cleaning up old data...")
            maintenance_results['data_cleanup'] = self.cleanup_old_data()
            
            # Step 2: Optimize models
            self.logger.info("Step 2: Optimizing models...")
            maintenance_results['model_optimization'] = self.optimize_models()
            
            # Step 3: Optimize databases
            self.logger.info("Step 3: Optimizing databases...")
            maintenance_results['database_optimization'] = self.optimize_databases()
            
            # Step 4: Clean up memory
            self.logger.info("Step 4: Cleaning up memory...")
            maintenance_results['memory_cleanup'] = self.cleanup_memory()
            
            # Step 5: Archive old data
            self.logger.info("Step 5: Archiving old data...")
            maintenance_results['archival'] = self.archive_old_data()
            
            # Calculate total space saved
            total_space_saved = 0
            total_space_saved += maintenance_results['data_cleanup'].get('total_space_freed_mb', 0)
            total_space_saved += maintenance_results['model_optimization'].get('space_saved_mb', 0)
            total_space_saved += maintenance_results['database_optimization'].get('space_reclaimed_mb', 0)
            total_space_saved += maintenance_results['archival'].get('space_saved_mb', 0)
            
            maintenance_results['total_space_saved_mb'] = total_space_saved
            maintenance_results['end_time'] = datetime.now().isoformat()
            
            # Check overall success
            has_errors = any([
                maintenance_results['data_cleanup'].get('errors', []),
                maintenance_results['model_optimization'].get('errors', []),
                maintenance_results['database_optimization'].get('errors', []),
                maintenance_results['archival'].get('errors', [])
            ])
            
            maintenance_results['overall_success'] = not has_errors
            
            self.logger.info(f"Full maintenance cycle completed. Total space saved: {total_space_saved:.2f} MB")
            
        except Exception as e:
            maintenance_results['error'] = str(e)
            maintenance_results['end_time'] = datetime.now().isoformat()
            self.logger.error(f"Full maintenance cycle failed: {e}")
        
        return maintenance_results
    
    def start_scheduled_maintenance(self):
        """Start scheduled maintenance tasks."""
        if not SCHEDULE_AVAILABLE:
            self.logger.warning("Schedule module not available, cannot start scheduled maintenance")
            return
            
        if self.scheduler_running:
            self.logger.warning("Scheduled maintenance is already running")
            return
        
        self.logger.info("Starting scheduled maintenance...")
        
        # Schedule daily cleanup
        daily_time = self.config['maintenance_schedule'].get('daily_cleanup_time', '02:00')
        schedule.every().day.at(daily_time).do(self.cleanup_old_data)
        
        # Schedule weekly optimization
        weekly_day = self.config['maintenance_schedule'].get('weekly_optimization_day', 'sunday')
        weekly_time = self.config['maintenance_schedule'].get('weekly_optimization_time', '03:00')
        getattr(schedule.every(), weekly_day.lower()).at(weekly_time).do(self._weekly_optimization)
        
        # Schedule weekly archival (simplified from monthly)
        schedule.every().sunday.at("04:00").do(self.archive_old_data)
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduled maintenance started")
    
    def stop_scheduled_maintenance(self):
        """Stop scheduled maintenance tasks."""
        if not self.scheduler_running:
            return
        
        self.scheduler_running = False
        
        if SCHEDULE_AVAILABLE:
            schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Scheduled maintenance stopped")
    
    def _run_scheduler(self):
        """Run the maintenance scheduler."""
        if not SCHEDULE_AVAILABLE:
            return
            
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _weekly_optimization(self):
        """Run weekly optimization tasks."""
        self.logger.info("Running weekly optimization...")
        
        # Optimize models and databases
        self.optimize_models()
        self.optimize_databases()
        self.cleanup_memory()
        
        self.logger.info("Weekly optimization completed")