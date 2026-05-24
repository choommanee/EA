"""
Learning Configuration Manager
Manages configuration settings for the AI Continuous Learning System
"""

import sys
import os
sys.path.append('Python')

import logging
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import warnings
warnings.filterwarnings('ignore')


class ConfigFormat(Enum):
    """Configuration file formats"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


@dataclass
class ModelTrainingConfig:
    """Model training configuration"""
    retraining_frequency_hours: int = 24
    min_samples_for_retraining: int = 100
    max_training_time_minutes: int = 60
    cross_validation_folds: int = 5
    test_size_ratio: float = 0.2
    random_state: int = 42
    enable_hyperparameter_optimization: bool = True
    enable_ensemble_learning: bool = True
    ensemble_size: int = 3
    auto_model_selection: bool = True


@dataclass
class PerformanceMonitoringConfig:
    """Performance monitoring configuration"""
    performance_threshold: float = 0.7
    performance_window_hours: int = 24
    degradation_threshold: float = 0.1
    monitoring_frequency_minutes: int = 30
    alert_on_degradation: bool = True
    track_prediction_accuracy: bool = True
    track_model_drift: bool = True
    drift_detection_window: int = 1000


@dataclass
class DataCollectionConfig:
    """Data collection configuration"""
    data_collection_window_hours: int = 48
    max_data_age_days: int = 90
    min_data_quality_score: float = 0.8
    enable_data_validation: bool = True
    enable_outlier_detection: bool = True
    outlier_threshold: float = 3.0
    feature_selection_enabled: bool = True
    max_features: int = 50


@dataclass
class SystemConfig:
    """System-level configuration"""
    max_concurrent_jobs: int = 4
    job_timeout_minutes: int = 120
    max_memory_usage_gb: float = 8.0
    enable_gpu: bool = False
    log_level: str = "INFO"
    enable_profiling: bool = False
    backup_frequency_hours: int = 24
    cleanup_old_data: bool = True


@dataclass
class NotificationConfig:
    """Notification configuration"""
    enabled: bool = True
    email_enabled: bool = False
    webhook_enabled: bool = False
    telegram_enabled: bool = False
    slack_enabled: bool = False
    rate_limit_minutes: int = 5
    alert_levels: List[str] = field(default_factory=lambda: ["WARNING", "ERROR", "CRITICAL"])
    email_recipients: List[str] = field(default_factory=list)
    webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_encryption: bool = True
    encryption_key_path: str = "Config/encryption.key"
    enable_access_control: bool = False
    allowed_ips: List[str] = field(default_factory=list)
    session_timeout_minutes: int = 60
    max_login_attempts: int = 3
    enable_audit_logging: bool = True
    audit_log_path: str = "Logs/audit.log"


@dataclass
class LearningConfiguration:
    """Complete learning system configuration"""
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Component configurations
    model_training: ModelTrainingConfig = field(default_factory=ModelTrainingConfig)
    performance_monitoring: PerformanceMonitoringConfig = field(default_factory=PerformanceMonitoringConfig)
    data_collection: DataCollectionConfig = field(default_factory=DataCollectionConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningConfiguration':
        """Create configuration from dictionary"""
        # Handle datetime fields
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Create component configurations
        config = cls()
        
        if 'model_training' in data:
            config.model_training = ModelTrainingConfig(**data['model_training'])
        if 'performance_monitoring' in data:
            config.performance_monitoring = PerformanceMonitoringConfig(**data['performance_monitoring'])
        if 'data_collection' in data:
            config.data_collection = DataCollectionConfig(**data['data_collection'])
        if 'system' in data:
            config.system = SystemConfig(**data['system'])
        if 'notifications' in data:
            config.notifications = NotificationConfig(**data['notifications'])
        if 'security' in data:
            config.security = SecurityConfig(**data['security'])
        
        # Set other fields
        for key, value in data.items():
            if hasattr(config, key) and key not in ['model_training', 'performance_monitoring', 
                                                   'data_collection', 'system', 'notifications', 'security']:
                setattr(config, key, value)
        
        return config


class LearningConfigManager:
    """Configuration manager for the learning system"""
    
    def __init__(self, config_dir: str = "Config"):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration cache
        self.config_cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = timedelta(minutes=5)
        
        # Configuration history
        self.config_history = []
        self.max_history = 50
        
        # Validation rules
        self.validation_rules = self._setup_validation_rules()
        
        self.logger.info("Learning Configuration Manager initialized")
    
    def load_config(self, config_name: str = "default", 
                   config_format: ConfigFormat = ConfigFormat.JSON) -> Optional[LearningConfiguration]:
        """Load configuration from file"""
        try:
            # Check cache first
            cache_key = f"{config_name}_{config_format.value}"
            if self._is_cache_valid(cache_key):
                return self.config_cache[cache_key]
            
            # Determine file path
            file_extension = config_format.value
            config_file = self.config_dir / f"{config_name}.{file_extension}"
            
            if not config_file.exists():
                self.logger.warning(f"Configuration file not found: {config_file}")
                # Create default configuration
                default_config = LearningConfiguration()
                self.save_config(default_config, config_name, config_format)
                return default_config
            
            # Load configuration
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_format == ConfigFormat.JSON:
                    data = json.load(f)
                elif config_format == ConfigFormat.YAML:
                    data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_format}")
            
            # Create configuration object
            config = LearningConfiguration.from_dict(data)
            
            # Validate configuration
            if self.validate_config(config):
                # Cache configuration
                self.config_cache[cache_key] = config
                self.cache_timestamps[cache_key] = datetime.now()
                
                self.logger.info(f"Configuration loaded: {config_name}")
                return config
            else:
                self.logger.error(f"Configuration validation failed: {config_name}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return None
    
    def save_config(self, config: LearningConfiguration, config_name: str = "default",
                   config_format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Save configuration to file"""
        try:
            # Update timestamp
            config.updated_at = datetime.now()
            
            # Validate configuration
            if not self.validate_config(config):
                self.logger.error("Configuration validation failed, not saving")
                return False
            
            # Determine file path
            file_extension = config_format.value
            config_file = self.config_dir / f"{config_name}.{file_extension}"
            
            # Create backup if file exists
            if config_file.exists():
                backup_file = self.config_dir / f"{config_name}.{file_extension}.backup"
                config_file.rename(backup_file)
            
            # Convert to dictionary
            config_dict = config.to_dict()
            
            # Handle datetime serialization
            config_dict['created_at'] = config.created_at.isoformat()
            config_dict['updated_at'] = config.updated_at.isoformat()
            
            # Save configuration
            with open(config_file, 'w', encoding='utf-8') as f:
                if config_format == ConfigFormat.JSON:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                elif config_format == ConfigFormat.YAML:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise ValueError(f"Unsupported config format: {config_format}")
            
            # Update cache
            cache_key = f"{config_name}_{config_format.value}"
            self.config_cache[cache_key] = config
            self.cache_timestamps[cache_key] = datetime.now()
            
            # Add to history
            self._add_to_history(config_name, config_format, "saved")
            
            self.logger.info(f"Configuration saved: {config_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def validate_config(self, config: LearningConfiguration) -> bool:
        """Validate configuration against rules"""
        try:
            validation_errors = []
            
            # Validate model training config
            mt_config = config.model_training
            if mt_config.retraining_frequency_hours < 1:
                validation_errors.append("Retraining frequency must be at least 1 hour")
            if mt_config.min_samples_for_retraining < 10:
                validation_errors.append("Minimum samples for retraining must be at least 10")
            if not 0.1 <= mt_config.test_size_ratio <= 0.5:
                validation_errors.append("Test size ratio must be between 0.1 and 0.5")
            
            # Validate performance monitoring config
            pm_config = config.performance_monitoring
            if not 0.0 <= pm_config.performance_threshold <= 1.0:
                validation_errors.append("Performance threshold must be between 0.0 and 1.0")
            if pm_config.performance_window_hours < 1:
                validation_errors.append("Performance window must be at least 1 hour")
            
            # Validate data collection config
            dc_config = config.data_collection
            if dc_config.data_collection_window_hours < 1:
                validation_errors.append("Data collection window must be at least 1 hour")
            if dc_config.max_data_age_days < 1:
                validation_errors.append("Max data age must be at least 1 day")
            
            # Validate system config
            sys_config = config.system
            if sys_config.max_concurrent_jobs < 1:
                validation_errors.append("Max concurrent jobs must be at least 1")
            if sys_config.job_timeout_minutes < 1:
                validation_errors.append("Job timeout must be at least 1 minute")
            
            # Log validation errors
            if validation_errors:
                for error in validation_errors:
                    self.logger.error(f"Configuration validation error: {error}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
            return False
    
    def update_config(self, config_name: str, updates: Dict[str, Any],
                     config_format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Update specific configuration values"""
        try:
            # Load current configuration
            config = self.load_config(config_name, config_format)
            if not config:
                self.logger.error(f"Failed to load configuration: {config_name}")
                return False
            
            # Apply updates
            config_dict = config.to_dict()
            self._deep_update(config_dict, updates)
            
            # Create updated configuration
            updated_config = LearningConfiguration.from_dict(config_dict)
            
            # Save updated configuration
            success = self.save_config(updated_config, config_name, config_format)
            
            if success:
                # Add to history
                self._add_to_history(config_name, config_format, "updated", updates)
                self.logger.info(f"Configuration updated: {config_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """List all available configurations"""
        try:
            configs = []
            
            for config_file in self.config_dir.glob("*.json"):
                if config_file.stem.endswith('.backup'):
                    continue
                
                try:
                    stat = config_file.stat()
                    configs.append({
                        'name': config_file.stem,
                        'format': 'json',
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'path': str(config_file)
                    })
                except Exception as file_error:
                    self.logger.warning(f"Error reading config file {config_file}: {file_error}")
            
            for config_file in self.config_dir.glob("*.yaml"):
                if config_file.stem.endswith('.backup'):
                    continue
                
                try:
                    stat = config_file.stat()
                    configs.append({
                        'name': config_file.stem,
                        'format': 'yaml',
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'path': str(config_file)
                    })
                except Exception as file_error:
                    self.logger.warning(f"Error reading config file {config_file}: {file_error}")
            
            return sorted(configs, key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing configurations: {e}")
            return []
    
    def backup_config(self, config_name: str, 
                     config_format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Create backup of configuration"""
        try:
            file_extension = config_format.value
            config_file = self.config_dir / f"{config_name}.{file_extension}"
            
            if not config_file.exists():
                self.logger.error(f"Configuration file not found: {config_file}")
                return False
            
            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.config_dir / f"{config_name}_{timestamp}.{file_extension}.backup"
            
            # Copy file
            import shutil
            shutil.copy2(config_file, backup_file)
            
            self.logger.info(f"Configuration backup created: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating configuration backup: {e}")
            return False
    
    def restore_config(self, config_name: str, backup_timestamp: str,
                      config_format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Restore configuration from backup"""
        try:
            file_extension = config_format.value
            backup_file = self.config_dir / f"{config_name}_{backup_timestamp}.{file_extension}.backup"
            
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            config_file = self.config_dir / f"{config_name}.{file_extension}"
            
            # Create current backup before restore
            if config_file.exists():
                current_backup = self.config_dir / f"{config_name}_pre_restore.{file_extension}.backup"
                import shutil
                shutil.copy2(config_file, current_backup)
            
            # Restore from backup
            import shutil
            shutil.copy2(backup_file, config_file)
            
            # Clear cache
            cache_key = f"{config_name}_{config_format.value}"
            if cache_key in self.config_cache:
                del self.config_cache[cache_key]
                del self.cache_timestamps[cache_key]
            
            # Add to history
            self._add_to_history(config_name, config_format, "restored", {"backup_timestamp": backup_timestamp})
            
            self.logger.info(f"Configuration restored from backup: {config_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring configuration: {e}")
            return False
    
    def get_config_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        try:
            return sorted(self.config_history, key=lambda x: x['timestamp'], reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting configuration history: {e}")
            return []
    
    def clear_cache(self):
        """Clear configuration cache"""
        self.config_cache.clear()
        self.cache_timestamps.clear()
        self.logger.info("Configuration cache cleared")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid"""
        if cache_key not in self.config_cache:
            return False
        
        if cache_key not in self.cache_timestamps:
            return False
        
        return datetime.now() - self.cache_timestamps[cache_key] < self.cache_ttl
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _add_to_history(self, config_name: str, config_format: ConfigFormat, 
                       action: str, details: Optional[Dict[str, Any]] = None):
        """Add entry to configuration history"""
        try:
            history_entry = {
                'timestamp': datetime.now(),
                'config_name': config_name,
                'config_format': config_format.value,
                'action': action,
                'details': details or {}
            }
            
            self.config_history.append(history_entry)
            
            # Trim history if too long
            if len(self.config_history) > self.max_history:
                self.config_history = self.config_history[-self.max_history:]
            
        except Exception as e:
            self.logger.error(f"Error adding to configuration history: {e}")
    
    def _setup_validation_rules(self) -> Dict[str, Any]:
        """Setup configuration validation rules"""
        return {
            'model_training': {
                'retraining_frequency_hours': {'min': 1, 'max': 168},  # 1 hour to 1 week
                'min_samples_for_retraining': {'min': 10, 'max': 100000},
                'test_size_ratio': {'min': 0.1, 'max': 0.5}
            },
            'performance_monitoring': {
                'performance_threshold': {'min': 0.0, 'max': 1.0},
                'performance_window_hours': {'min': 1, 'max': 720}  # 1 hour to 30 days
            },
            'system': {
                'max_concurrent_jobs': {'min': 1, 'max': 16},
                'job_timeout_minutes': {'min': 1, 'max': 1440}  # 1 minute to 24 hours
            }
        }


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize configuration manager
    config_manager = LearningConfigManager("Config")
    
    print("Learning Configuration Manager initialized successfully!")
    
    # Test creating and saving default configuration
    default_config = LearningConfiguration()
    success = config_manager.save_config(default_config, "test_config")
    print(f"Default configuration saved: {success}")
    
    # Test loading configuration
    loaded_config = config_manager.load_config("test_config")
    print(f"Configuration loaded: {loaded_config is not None}")
    
    # Test listing configurations
    configs = config_manager.list_configs()
    print(f"Available configurations: {len(configs)}")
    
    print("Learning Configuration Manager test completed!")