#!/usr/bin/env python3
"""
Configuration Management Interface for AI Continuous Learning
Provides user-friendly interface for managing learning system configurations
with validation, error handling, and audit trail
"""

import sys
import os
sys.path.append('Python')

import logging
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from learning_configuration import (
    LearningConfiguration, ConfigFormat, ConfigValidationLevel,
    LearningConfig, ConfigVersion
)


class ConfigurationInterface:
    """
    User-friendly interface for configuration management
    Provides high-level methods for common configuration operations
    """
    
    def __init__(self, config_dir: str = "Config", 
                 enable_audit_logging: bool = True):
        """Initialize the configuration interface"""
        self.config_dir = Path(config_dir)
        self.enable_audit_logging = enable_audit_logging
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration manager
        self.config_manager = LearningConfiguration(
            config_dir=str(config_dir),
            enable_versioning=True,
            validation_level=ConfigValidationLevel.STRICT
        )
        
        # Audit log
        self.audit_log = []
        self.max_audit_entries = 1000
        
        # Initialize audit logging
        if self.enable_audit_logging:
            self._setup_audit_logging()
        
        self.logger.info("Configuration Interface initialized")
    
    def get_current_configuration(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        try:
            config = self.config_manager.get_configuration()
            self._log_audit("get_configuration", {"action": "retrieve_config"})
            return config
            
        except Exception as e:
            self.logger.error(f"Error getting current configuration: {e}")
            return {}
    
    def update_model_training_config(self, **kwargs) -> bool:
        """Update model training configuration"""
        try:
            updates = {"model_training": kwargs}
            success = self.config_manager.update_configuration(
                updates, 
                f"Updated model training config: {list(kwargs.keys())}"
            )
            
            if success:
                self._log_audit("update_model_training", kwargs)
                self.logger.info(f"Model training config updated: {list(kwargs.keys())}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating model training config: {e}")
            return False
    
    def update_performance_monitoring_config(self, **kwargs) -> bool:
        """Update performance monitoring configuration"""
        try:
            updates = {"performance_monitoring": kwargs}
            success = self.config_manager.update_configuration(
                updates,
                f"Updated performance monitoring config: {list(kwargs.keys())}"
            )
            
            if success:
                self._log_audit("update_performance_monitoring", kwargs)
                self.logger.info(f"Performance monitoring config updated: {list(kwargs.keys())}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating performance monitoring config: {e}")
            return False
    
    def update_data_collection_config(self, **kwargs) -> bool:
        """Update data collection configuration"""
        try:
            updates = {"data_collection": kwargs}
            success = self.config_manager.update_configuration(
                updates,
                f"Updated data collection config: {list(kwargs.keys())}"
            )
            
            if success:
                self._log_audit("update_data_collection", kwargs)
                self.logger.info(f"Data collection config updated: {list(kwargs.keys())}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating data collection config: {e}")
            return False
    
    def update_system_config(self, **kwargs) -> bool:
        """Update system configuration"""
        try:
            updates = {"system": kwargs}
            success = self.config_manager.update_configuration(
                updates,
                f"Updated system config: {list(kwargs.keys())}"
            )
            
            if success:
                self._log_audit("update_system", kwargs)
                self.logger.info(f"System config updated: {list(kwargs.keys())}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating system config: {e}")
            return False
    
    def update_notification_config(self, **kwargs) -> bool:
        """Update notification configuration"""
        try:
            updates = {"notifications": kwargs}
            success = self.config_manager.update_configuration(
                updates,
                f"Updated notification config: {list(kwargs.keys())}"
            )
            
            if success:
                self._log_audit("update_notifications", kwargs)
                self.logger.info(f"Notification config updated: {list(kwargs.keys())}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating notification config: {e}")
            return False
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path"""
        try:
            value = self.config_manager.get_config_value(key_path, default)
            self._log_audit("get_config_value", {"key_path": key_path, "found": value is not None})
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting config value {key_path}: {e}")
            return default
    
    def set_config_value(self, key_path: str, value: Any, 
                        description: str = "Single value update") -> bool:
        """Set configuration value by dot-separated path"""
        try:
            success = self.config_manager.set_config_value(key_path, value, description)
            
            if success:
                self._log_audit("set_config_value", {
                    "key_path": key_path, 
                    "value": value, 
                    "description": description
                })
                self.logger.info(f"Config value set: {key_path} = {value}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error setting config value {key_path}: {e}")
            return False
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration and return validation results"""
        try:
            is_valid = self.config_manager.validate_configuration()
            
            validation_result = {
                "is_valid": is_valid,
                "timestamp": datetime.now(),
                "errors": [],
                "warnings": []
            }
            
            # Additional validation checks
            config = self.config_manager.get_configuration()
            
            # Check model training config
            model_config = config.get("model_training", {})
            if model_config.get("batch_size", 0) <= 0:
                validation_result["errors"].append("Model training batch_size must be positive")
            
            if model_config.get("learning_rate", 0) <= 0:
                validation_result["errors"].append("Model training learning_rate must be positive")
            
            # Check performance monitoring config
            perf_config = config.get("performance_monitoring", {})
            threshold = perf_config.get("performance_threshold", 0)
            if not 0 <= threshold <= 1:
                validation_result["errors"].append("Performance threshold must be between 0 and 1")
            
            # Check system config
            system_config = config.get("system", {})
            if system_config.get("max_concurrent_training", 0) <= 0:
                validation_result["warnings"].append("Max concurrent training should be positive")
            
            # Update validity based on errors
            if validation_result["errors"]:
                validation_result["is_valid"] = False
            
            self._log_audit("validate_configuration", {
                "is_valid": validation_result["is_valid"],
                "error_count": len(validation_result["errors"]),
                "warning_count": len(validation_result["warnings"])
            })
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
            return {
                "is_valid": False,
                "timestamp": datetime.now(),
                "errors": [f"Validation error: {e}"],
                "warnings": []
            }
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get configuration version history"""
        try:
            versions = self.config_manager.get_version_history()
            
            version_list = []
            for version in versions:
                version_info = {
                    "version": version.version,
                    "timestamp": version.timestamp,
                    "description": version.description,
                    "checksum": version.checksum,
                    "created_by": version.created_by
                }
                version_list.append(version_info)
            
            self._log_audit("get_version_history", {"version_count": len(version_list)})
            return version_list
            
        except Exception as e:
            self.logger.error(f"Error getting version history: {e}")
            return []
    
    def rollback_to_version(self, version: str) -> bool:
        """Rollback configuration to specific version"""
        try:
            success = self.config_manager.rollback_to_version(version)
            
            if success:
                self._log_audit("rollback_configuration", {
                    "target_version": version,
                    "success": True
                })
                self.logger.info(f"Configuration rolled back to version: {version}")
            else:
                self._log_audit("rollback_configuration", {
                    "target_version": version,
                    "success": False
                })
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error rolling back to version {version}: {e}")
            return False
    
    def export_configuration(self, export_path: str, 
                           format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """Export configuration to file"""
        try:
            success = self.config_manager.export_configuration(export_path, format)
            
            if success:
                self._log_audit("export_configuration", {
                    "export_path": export_path,
                    "format": format.value
                })
                self.logger.info(f"Configuration exported to: {export_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_configuration(self, import_path: str, 
                           description: str = "Configuration import") -> bool:
        """Import configuration from file"""
        try:
            success = self.config_manager.import_configuration(import_path, description)
            
            if success:
                self._log_audit("import_configuration", {
                    "import_path": import_path,
                    "description": description
                })
                self.logger.info(f"Configuration imported from: {import_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
    
    def cleanup_old_versions(self, keep_versions: int = 10) -> bool:
        """Clean up old configuration versions"""
        try:
            success = self.config_manager.cleanup_old_versions(keep_versions)
            
            if success:
                self._log_audit("cleanup_versions", {"keep_versions": keep_versions})
                self.logger.info(f"Cleaned up old versions, keeping {keep_versions}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old versions: {e}")
            return False
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        try:
            config = self.config_manager.get_configuration()
            
            summary = {
                "timestamp": datetime.now(),
                "sections": list(config.keys()),
                "model_training": {
                    "batch_size": config.get("model_training", {}).get("batch_size"),
                    "learning_rate": config.get("model_training", {}).get("learning_rate"),
                    "epochs": config.get("model_training", {}).get("epochs")
                },
                "performance_monitoring": {
                    "performance_threshold": config.get("performance_monitoring", {}).get("performance_threshold"),
                    "degradation_threshold": config.get("performance_monitoring", {}).get("degradation_threshold"),
                    "monitoring_interval_minutes": config.get("performance_monitoring", {}).get("monitoring_interval_minutes")
                },
                "system": {
                    "max_concurrent_training": config.get("system", {}).get("max_concurrent_training"),
                    "memory_limit_gb": config.get("system", {}).get("memory_limit_gb"),
                    "debug_mode": config.get("system", {}).get("debug_mode")
                },
                "notifications": {
                    "enabled": config.get("notifications", {}).get("enabled"),
                    "log_level": config.get("notifications", {}).get("log_level")
                }
            }
            
            self._log_audit("get_configuration_summary", {"sections": len(summary["sections"])})
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting configuration summary: {e}")
            return {}
    
    def reset_to_defaults(self, description: str = "Reset to default configuration") -> bool:
        """Reset configuration to default values"""
        try:
            # Create new default configuration
            default_config = LearningConfig()
            config_dict = {
                "model_training": default_config.model_training,
                "performance_monitoring": default_config.performance_monitoring,
                "data_collection": default_config.data_collection,
                "model_management": default_config.model_management,
                "notifications": default_config.notifications,
                "system": default_config.system
            }
            
            success = self.config_manager.update_configuration(config_dict, description)
            
            if success:
                self._log_audit("reset_to_defaults", {"description": description})
                self.logger.info("Configuration reset to defaults")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error resetting to defaults: {e}")
            return False
    
    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        try:
            # Sort by timestamp (most recent first)
            sorted_log = sorted(
                self.audit_log,
                key=lambda x: x['timestamp'],
                reverse=True
            )
            
            return sorted_log[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting audit log: {e}")
            return []
    
    def save_audit_log(self, file_path: str = None) -> bool:
        """Save audit log to file"""
        try:
            if not file_path:
                file_path = self.config_dir / "audit_log.json"
            
            audit_data = {
                "generated_at": datetime.now().isoformat(),
                "total_entries": len(self.audit_log),
                "entries": self.audit_log
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(audit_data, f, indent=2, default=str)
            
            self.logger.info(f"Audit log saved to: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving audit log: {e}")
            return False
    
    def _setup_audit_logging(self):
        """Setup audit logging"""
        try:
            # Create audit log directory
            audit_dir = self.config_dir / "audit"
            audit_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing audit log if available
            audit_file = audit_dir / "audit_log.json"
            if audit_file.exists():
                with open(audit_file, 'r', encoding='utf-8') as f:
                    audit_data = json.load(f)
                    self.audit_log = audit_data.get('entries', [])
                    
                    # Convert timestamp strings back to datetime objects
                    for entry in self.audit_log:
                        if isinstance(entry.get('timestamp'), str):
                            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
            
        except Exception as e:
            self.logger.error(f"Error setting up audit logging: {e}")
    
    def _log_audit(self, action: str, details: Dict[str, Any]):
        """Log audit entry"""
        try:
            if not self.enable_audit_logging:
                return
            
            audit_entry = {
                "timestamp": datetime.now(),
                "action": action,
                "details": details,
                "user": "system"  # Could be extended to track actual users
            }
            
            self.audit_log.append(audit_entry)
            
            # Trim audit log if too long
            if len(self.audit_log) > self.max_audit_entries:
                self.audit_log = self.audit_log[-self.max_audit_entries:]
            
        except Exception as e:
            self.logger.error(f"Error logging audit entry: {e}")


# Convenience functions for common operations
def quick_setup_training_config(batch_size: int = 32, learning_rate: float = 0.001, 
                               epochs: int = 100) -> bool:
    """Quick setup for model training configuration"""
    try:
        interface = ConfigurationInterface()
        return interface.update_model_training_config(
            batch_size=batch_size,
            learning_rate=learning_rate,
            epochs=epochs
        )
    except Exception as e:
        logging.error(f"Error in quick training setup: {e}")
        return False


def quick_setup_monitoring_config(performance_threshold: float = 0.75,
                                 degradation_threshold: float = 0.1,
                                 monitoring_interval: int = 60) -> bool:
    """Quick setup for performance monitoring configuration"""
    try:
        interface = ConfigurationInterface()
        return interface.update_performance_monitoring_config(
            performance_threshold=performance_threshold,
            degradation_threshold=degradation_threshold,
            monitoring_interval_minutes=monitoring_interval
        )
    except Exception as e:
        logging.error(f"Error in quick monitoring setup: {e}")
        return False


def quick_setup_notifications(enabled: bool = True, log_level: str = "INFO",
                             alert_channels: List[str] = None) -> bool:
    """Quick setup for notification configuration"""
    try:
        interface = ConfigurationInterface()
        if alert_channels is None:
            alert_channels = ["log"]
        
        return interface.update_notification_config(
            enabled=enabled,
            log_level=log_level,
            alert_channels=alert_channels
        )
    except Exception as e:
        logging.error(f"Error in quick notification setup: {e}")
        return False


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize configuration interface
    config_interface = ConfigurationInterface()
    
    print("Configuration Interface initialized successfully!")
    
    # Test configuration summary
    summary = config_interface.get_configuration_summary()
    print(f"Configuration summary: {len(summary)} sections")
    
    # Test updating model training config
    success = config_interface.update_model_training_config(
        batch_size=64,
        learning_rate=0.01,
        epochs=200
    )
    print(f"Model training config updated: {success}")
    
    # Test validation
    validation = config_interface.validate_configuration()
    print(f"Configuration is valid: {validation['is_valid']}")
    
    # Test getting specific value
    batch_size = config_interface.get_config_value("model_training.batch_size")
    print(f"Current batch size: {batch_size}")
    
    # Test version history
    versions = config_interface.get_version_history()
    print(f"Configuration versions: {len(versions)}")
    
    # Test audit log
    audit_entries = config_interface.get_audit_log(5)
    print(f"Recent audit entries: {len(audit_entries)}")
    
    print("Configuration Interface test completed!")