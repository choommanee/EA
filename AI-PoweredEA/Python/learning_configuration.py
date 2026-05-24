#!/usr/bin/env python3
"""
Learning Configuration System for AI Continuous Learning
Provides comprehensive configuration management with validation, versioning, and rollback capabilities
"""

import os
import json
import yaml
import logging
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import hashlib
import copy


class ConfigFormat(Enum):
    """Configuration file formats"""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"


class ConfigValidationLevel(Enum):
    """Configuration validation levels"""
    STRICT = "strict"      # All fields must be valid
    LENIENT = "lenient"    # Allow unknown fields
    MINIMAL = "minimal"    # Only check required fields


@dataclass
class ConfigVersion:
    """Configuration version information"""
    version: str
    timestamp: datetime
    description: str
    checksum: str
    file_path: str
    created_by: str = "system"


@dataclass
class ValidationRule:
    """Configuration validation rule"""
    field_path: str
    rule_type: str  # 'required', 'type', 'range', 'enum', 'custom'
    rule_value: Any
    error_message: str
    validator_func: Optional[Callable] = None


@dataclass
class LearningConfig:
    """Main learning system configuration"""
    # Model Training Configuration
    model_training: Dict[str, Any] = field(default_factory=lambda: {
        "batch_size": 32,
        "learning_rate": 0.001,
        "epochs": 100,
        "early_stopping_patience": 10,
        "validation_split": 0.2,
        "random_seed": 42
    })
    
    # Performance Monitoring Configuration
    performance_monitoring: Dict[str, Any] = field(default_factory=lambda: {
        "performance_threshold": 0.75,
        "degradation_threshold": 0.1,
        "monitoring_interval_minutes": 60,
        "alert_on_degradation": True,
        "performance_history_days": 30
    })
    
    # Data Collection Configuration
    data_collection: Dict[str, Any] = field(default_factory=lambda: {
        "collection_interval_hours": 24,
        "max_data_age_days": 365,
        "data_quality_threshold": 0.8,
        "auto_cleanup_enabled": True,
        "backup_before_cleanup": True
    })
    
    # Model Management Configuration
    model_management: Dict[str, Any] = field(default_factory=lambda: {
        "max_model_versions": 10,
        "auto_deployment_enabled": False,
        "rollback_on_failure": True,
        "model_storage_path": "Models/learning",
        "compression_enabled": True
    })
    
    # Notification Configuration
    notifications: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "email_notifications": False,
        "log_level": "INFO",
        "alert_channels": ["log"],
        "rate_limiting_minutes": 5
    })
    
    # System Configuration
    system: Dict[str, Any] = field(default_factory=lambda: {
        "max_concurrent_training": 2,
        "memory_limit_gb": 8,
        "cpu_cores": -1,  # -1 means use all available
        "gpu_enabled": False,
        "debug_mode": False
    })


class LearningConfiguration:
    """
    Comprehensive configuration management system for AI continuous learning
    Provides loading, validation, versioning, and rollback capabilities
    """
    
    def __init__(self, config_dir: str = "Config", 
                 config_file: str = "learning_config.json",
                 enable_versioning: bool = True,
                 validation_level: ConfigValidationLevel = ConfigValidationLevel.STRICT):
        """Initialize the configuration system"""
        self.config_dir = Path(config_dir)
        self.config_file = config_file
        self.config_path = self.config_dir / config_file
        self.versions_dir = self.config_dir / "versions"
        self.backup_dir = self.config_dir / "backups"
        
        self.enable_versioning = enable_versioning
        self.validation_level = validation_level
        
        # Current configuration
        self.config: LearningConfig = LearningConfig()
        self.config_versions: List[ConfigVersion] = []
        self.validation_rules: List[ValidationRule] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize directories and load configuration
        self._initialize_directories()
        self._setup_validation_rules()
        self.load_configuration()
        
        if self.enable_versioning:
            self._load_version_history()
    
    def load_configuration(self, config_path: Optional[str] = None) -> bool:
        """Load configuration from file"""
        try:
            target_path = Path(config_path) if config_path else self.config_path
            
            if not target_path.exists():
                self.logger.info(f"Configuration file not found at {target_path}, creating default configuration")
                self._create_default_configuration()
                return True
            
            # Determine file format
            file_format = self._detect_file_format(target_path)
            
            # Load configuration data
            with open(target_path, 'r', encoding='utf-8') as f:
                if file_format == ConfigFormat.JSON:
                    config_data = json.load(f)
                elif file_format in [ConfigFormat.YAML, ConfigFormat.YML]:
                    config_data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported configuration format: {file_format}")
            
            # Validate configuration
            if not self._validate_configuration(config_data):
                self.logger.error("Configuration validation failed")
                return False
            
            # Update configuration object
            self._update_config_from_dict(config_data)
            
            self.logger.info(f"Configuration loaded successfully from {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False
    
    def save_configuration(self, description: str = "Configuration update") -> bool:
        """Save current configuration to file"""
        try:
            # Create backup if versioning is enabled
            if self.enable_versioning and self.config_path.exists():
                self._create_version_backup(description)
            
            # Convert configuration to dictionary
            config_dict = asdict(self.config)
            
            # Determine file format and save
            file_format = self._detect_file_format(self.config_path)
            
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if file_format == ConfigFormat.JSON:
                    json.dump(config_dict, f, indent=2, default=str)
                elif file_format in [ConfigFormat.YAML, ConfigFormat.YML]:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved successfully to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def update_configuration(self, updates: Dict[str, Any], 
                           description: str = "Configuration update") -> bool:
        """Update configuration with new values"""
        try:
            # Create a copy of current config for rollback
            original_config = copy.deepcopy(self.config)
            
            # Apply updates
            self._apply_updates(updates)
            
            # Validate updated configuration
            config_dict = asdict(self.config)
            if not self._validate_configuration(config_dict):
                # Rollback on validation failure
                self.config = original_config
                self.logger.error("Configuration update failed validation, rolled back")
                return False
            
            # Save updated configuration
            if self.save_configuration(description):
                self.logger.info("Configuration updated successfully")
                return True
            else:
                # Rollback on save failure
                self.config = original_config
                self.logger.error("Configuration save failed, rolled back")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return asdict(self.config)
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path"""
        try:
            keys = key_path.split('.')
            value = asdict(self.config)
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting configuration value for {key_path}: {e}")
            return default
    
    def set_config_value(self, key_path: str, value: Any, 
                        description: str = "Single value update") -> bool:
        """Set configuration value by dot-separated path"""
        try:
            keys = key_path.split('.')
            updates = {}
            
            # Build nested dictionary for update
            current = updates
            for key in keys[:-1]:
                current[key] = {}
                current = current[key]
            current[keys[-1]] = value
            
            return self.update_configuration(updates, description)
            
        except Exception as e:
            self.logger.error(f"Error setting configuration value for {key_path}: {e}")
            return False
    
    def validate_configuration(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """Validate configuration data"""
        if config_data is None:
            config_data = asdict(self.config)
        
        return self._validate_configuration(config_data)
    
    def get_version_history(self) -> List[ConfigVersion]:
        """Get configuration version history"""
        return self.config_versions.copy()
    
    def rollback_to_version(self, version: str) -> bool:
        """Rollback configuration to specific version"""
        try:
            if not self.enable_versioning:
                self.logger.error("Versioning is not enabled")
                return False
            
            # Find version
            target_version = None
            for v in self.config_versions:
                if v.version == version:
                    target_version = v
                    break
            
            if not target_version:
                self.logger.error(f"Version {version} not found")
                return False
            
            # Load version file
            version_path = Path(target_version.file_path)
            if not version_path.exists():
                self.logger.error(f"Version file not found: {version_path}")
                return False
            
            # Create backup of current config before rollback
            self._create_version_backup(f"Pre-rollback to {version}")
            
            # Load version configuration
            if self.load_configuration(str(version_path)):
                # Copy version file to main config
                shutil.copy2(version_path, self.config_path)
                self.logger.info(f"Successfully rolled back to version {version}")
                return True
            else:
                self.logger.error(f"Failed to load version {version}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error rolling back to version {version}: {e}")
            return False
    
    def cleanup_old_versions(self, keep_versions: int = 10) -> bool:
        """Clean up old configuration versions"""
        try:
            if not self.enable_versioning:
                return True
            
            if len(self.config_versions) <= keep_versions:
                return True
            
            # Sort versions by timestamp (newest first)
            sorted_versions = sorted(
                self.config_versions, 
                key=lambda v: v.timestamp, 
                reverse=True
            )
            
            # Keep only the specified number of versions
            versions_to_keep = sorted_versions[:keep_versions]
            versions_to_remove = sorted_versions[keep_versions:]
            
            # Remove old version files
            for version in versions_to_remove:
                version_path = Path(version.file_path)
                if version_path.exists():
                    version_path.unlink()
                    self.logger.info(f"Removed old version: {version.version}")
            
            # Update version history
            self.config_versions = versions_to_keep
            self._save_version_history()
            
            self.logger.info(f"Cleaned up {len(versions_to_remove)} old versions")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old versions: {e}")
            return False
    
    def export_configuration(self, export_path: str, 
                           format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Export configuration to file"""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_dict = asdict(self.config)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                if format == ConfigFormat.JSON:
                    json.dump(config_dict, f, indent=2, default=str)
                elif format in [ConfigFormat.YAML, ConfigFormat.YML]:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_configuration(self, import_path: str, 
                           description: str = "Configuration import") -> bool:
        """Import configuration from file"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                self.logger.error(f"Import file not found: {import_path}")
                return False
            
            # Load and validate imported configuration
            if self.load_configuration(str(import_file)):
                # Save as current configuration
                return self.save_configuration(description)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
    
    def _initialize_directories(self):
        """Initialize configuration directories"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if self.enable_versioning:
            self.versions_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_default_configuration(self):
        """Create default configuration file"""
        self.config = LearningConfig()
        self.save_configuration("Initial default configuration")
    
    def _detect_file_format(self, file_path: Path) -> ConfigFormat:
        """Detect configuration file format from extension"""
        suffix = file_path.suffix.lower()
        
        if suffix == '.json':
            return ConfigFormat.JSON
        elif suffix in ['.yaml', '.yml']:
            return ConfigFormat.YAML
        else:
            # Default to JSON
            return ConfigFormat.JSON
    
    def _validate_configuration(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration data against rules"""
        try:
            validation_errors = []
            
            for rule in self.validation_rules:
                error = self._validate_rule(config_data, rule)
                if error:
                    validation_errors.append(error)
            
            if validation_errors:
                if self.validation_level == ConfigValidationLevel.STRICT:
                    for error in validation_errors:
                        self.logger.error(f"Validation error: {error}")
                    return False
                elif self.validation_level == ConfigValidationLevel.LENIENT:
                    for error in validation_errors:
                        self.logger.warning(f"Validation warning: {error}")
                    return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during configuration validation: {e}")
            return False
    
    def _validate_rule(self, config_data: Dict[str, Any], rule: ValidationRule) -> Optional[str]:
        """Validate a single configuration rule"""
        try:
            # Get value at field path
            keys = rule.field_path.split('.')
            value = config_data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    if rule.rule_type == 'required':
                        return f"Required field missing: {rule.field_path}"
                    else:
                        return None  # Field not present, skip other validations
            
            # Apply validation rule
            if rule.rule_type == 'type':
                expected_type = rule.rule_value
                if not isinstance(value, expected_type):
                    return f"{rule.field_path}: Expected {expected_type.__name__}, got {type(value).__name__}"
            
            elif rule.rule_type == 'range':
                min_val, max_val = rule.rule_value
                if not (min_val <= value <= max_val):
                    return f"{rule.field_path}: Value {value} not in range [{min_val}, {max_val}]"
            
            elif rule.rule_type == 'enum':
                allowed_values = rule.rule_value
                if value not in allowed_values:
                    return f"{rule.field_path}: Value {value} not in allowed values {allowed_values}"
            
            elif rule.rule_type == 'custom' and rule.validator_func:
                if not rule.validator_func(value):
                    return f"{rule.field_path}: {rule.error_message}"
            
            return None
            
        except Exception as e:
            return f"Validation error for {rule.field_path}: {e}"
    
    def _setup_validation_rules(self):
        """Setup default validation rules"""
        self.validation_rules = [
            # Model Training Rules
            ValidationRule("model_training.batch_size", "type", int, "Batch size must be integer"),
            ValidationRule("model_training.batch_size", "range", (1, 1000), "Batch size must be between 1 and 1000"),
            ValidationRule("model_training.learning_rate", "type", float, "Learning rate must be float"),
            ValidationRule("model_training.learning_rate", "range", (0.0001, 1.0), "Learning rate must be between 0.0001 and 1.0"),
            ValidationRule("model_training.epochs", "type", int, "Epochs must be integer"),
            ValidationRule("model_training.epochs", "range", (1, 10000), "Epochs must be between 1 and 10000"),
            
            # Performance Monitoring Rules
            ValidationRule("performance_monitoring.performance_threshold", "type", float, "Performance threshold must be float"),
            ValidationRule("performance_monitoring.performance_threshold", "range", (0.0, 1.0), "Performance threshold must be between 0.0 and 1.0"),
            ValidationRule("performance_monitoring.degradation_threshold", "type", float, "Degradation threshold must be float"),
            ValidationRule("performance_monitoring.degradation_threshold", "range", (0.0, 1.0), "Degradation threshold must be between 0.0 and 1.0"),
            
            # System Rules
            ValidationRule("system.max_concurrent_training", "type", int, "Max concurrent training must be integer"),
            ValidationRule("system.max_concurrent_training", "range", (1, 10), "Max concurrent training must be between 1 and 10"),
            ValidationRule("system.memory_limit_gb", "type", int, "Memory limit must be integer"),
            ValidationRule("system.memory_limit_gb", "range", (1, 128), "Memory limit must be between 1 and 128 GB"),
        ]
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration object from dictionary"""
        # Update each section
        if 'model_training' in config_data:
            self.config.model_training.update(config_data['model_training'])
        
        if 'performance_monitoring' in config_data:
            self.config.performance_monitoring.update(config_data['performance_monitoring'])
        
        if 'data_collection' in config_data:
            self.config.data_collection.update(config_data['data_collection'])
        
        if 'model_management' in config_data:
            self.config.model_management.update(config_data['model_management'])
        
        if 'notifications' in config_data:
            self.config.notifications.update(config_data['notifications'])
        
        if 'system' in config_data:
            self.config.system.update(config_data['system'])
    
    def _apply_updates(self, updates: Dict[str, Any]):
        """Apply configuration updates"""
        def update_nested_dict(target: dict, source: dict):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    update_nested_dict(target[key], value)
                else:
                    target[key] = value
        
        config_dict = asdict(self.config)
        update_nested_dict(config_dict, updates)
        self._update_config_from_dict(config_dict)
    
    def _create_version_backup(self, description: str):
        """Create version backup of current configuration"""
        try:
            if not self.config_path.exists():
                return
            
            # Generate version info
            timestamp = datetime.now()
            version = timestamp.strftime("%Y%m%d_%H%M%S")
            
            # Calculate checksum
            with open(self.config_path, 'rb') as f:
                content = f.read()
                checksum = hashlib.md5(content).hexdigest()
            
            # Create version file
            version_filename = f"config_v{version}.{self.config_path.suffix[1:]}"
            version_path = self.versions_dir / version_filename
            
            shutil.copy2(self.config_path, version_path)
            
            # Create version record
            config_version = ConfigVersion(
                version=version,
                timestamp=timestamp,
                description=description,
                checksum=checksum,
                file_path=str(version_path)
            )
            
            self.config_versions.append(config_version)
            self._save_version_history()
            
            self.logger.info(f"Created configuration version: {version}")
            
        except Exception as e:
            self.logger.error(f"Error creating version backup: {e}")
    
    def _load_version_history(self):
        """Load configuration version history"""
        try:
            history_file = self.versions_dir / "version_history.json"
            
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                self.config_versions = []
                for version_data in history_data:
                    version = ConfigVersion(
                        version=version_data['version'],
                        timestamp=datetime.fromisoformat(version_data['timestamp']),
                        description=version_data['description'],
                        checksum=version_data['checksum'],
                        file_path=version_data['file_path'],
                        created_by=version_data.get('created_by', 'system')
                    )
                    self.config_versions.append(version)
                
                self.logger.info(f"Loaded {len(self.config_versions)} configuration versions")
            
        except Exception as e:
            self.logger.error(f"Error loading version history: {e}")
    
    def _save_version_history(self):
        """Save configuration version history"""
        try:
            history_file = self.versions_dir / "version_history.json"
            
            history_data = []
            for version in self.config_versions:
                version_data = {
                    'version': version.version,
                    'timestamp': version.timestamp.isoformat(),
                    'description': version.description,
                    'checksum': version.checksum,
                    'file_path': version.file_path,
                    'created_by': version.created_by
                }
                history_data.append(version_data)
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving version history: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize configuration system
    config_manager = LearningConfiguration()
    
    print("Learning Configuration System initialized successfully!")
    
    # Test configuration access
    batch_size = config_manager.get_config_value("model_training.batch_size")
    print(f"Current batch size: {batch_size}")
    
    # Test configuration update
    success = config_manager.set_config_value("model_training.batch_size", 64, "Updated batch size for testing")
    print(f"Configuration update successful: {success}")
    
    # Test validation
    valid = config_manager.validate_configuration()
    print(f"Configuration is valid: {valid}")
    
    # Test version history
    versions = config_manager.get_version_history()
    print(f"Configuration versions: {len(versions)}")
    
    print("Learning Configuration System test completed!")