#!/usr/bin/env python3
"""
Learning Notification System for AI Continuous Learning
Provides comprehensive notification and alerting capabilities
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class NotificationLevel(Enum):
    """Notification levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationChannel(Enum):
    """Notification delivery channels"""
    LOG = "log"
    EMAIL = "email"
    WEBHOOK = "webhook"
    TELEGRAM = "telegram"


class LearningEventType(Enum):
    """Types of learning events"""
    MODEL_TRAINING_STARTED = "model_training_started"
    MODEL_TRAINING_COMPLETED = "model_training_completed"
    MODEL_TRAINING_FAILED = "model_training_failed"
    MODEL_DEPLOYED = "model_deployed"
    MODEL_ROLLBACK = "model_rollback"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RETRAINING_TRIGGERED = "retraining_triggered"
    DATA_QUALITY_ISSUE = "data_quality_issue"


@dataclass
class LearningEventRecord:
    """Record of a learning system event"""
    event_type: LearningEventType
    timestamp: datetime
    success: bool
    event_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class LearningNotificationSystem:
    """Comprehensive notification and alerting system for AI continuous learning"""
    
    def __init__(self, config_path: str = "Config/learning_notifications.json"):
        """Initialize the notification system"""
        self.config_path = config_path
        self.config = self._load_config()
        self.notification_history = []
        self.rate_limits = {}
        self.max_history = 1000
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Create logs directory if it doesn't exist
        os.makedirs("Logs", exist_ok=True)
    
    def send_learning_event_notification(self, event: LearningEventRecord) -> bool:
        """Send notification for learning system event"""
        try:
            level = self._get_notification_level(event.event_type)
            
            if not self._should_send_notification(event.event_type, level):
                return True
            
            message = self._create_event_message(event)
            
            success = self._send_notification(
                level=level,
                title=f"Learning System: {event.event_type.value}",
                message=message,
                event_data=event.event_data or {}
            )
            
            self._record_notification(event.event_type, level, message, success)
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending learning event notification: {e}")
            return False
    
    def send_performance_alert(self, model_name: str, current_performance: float,
                             threshold: float, degradation_percent: float) -> bool:
        """Send performance degradation alert"""
        try:
            level = NotificationLevel.WARNING if degradation_percent < 0.2 else NotificationLevel.ERROR
            
            title = f"Performance Alert: {model_name}"
            message = f"""Model Performance Degradation Detected

Model: {model_name}
Current Performance: {current_performance:.3f}
Threshold: {threshold:.3f}
Degradation: {degradation_percent:.1%}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Action Required: Review model performance and consider retraining."""
            
            event_data = {
                'model_name': model_name,
                'current_performance': current_performance,
                'threshold': threshold,
                'degradation_percent': degradation_percent
            }
            
            return self._send_notification(level, title, message, event_data)
            
        except Exception as e:
            self.logger.error(f"Error sending performance alert: {e}")
            return False
    
    def send_system_health_alert(self, health_status: Dict[str, Any]) -> bool:
        """Send system health alert"""
        try:
            overall_health = health_status.get('overall_health', 0)
            status = health_status.get('status', 'unknown')
            
            if status == 'healthy':
                return True
            
            level = NotificationLevel.WARNING if status == 'degraded' else NotificationLevel.ERROR
            
            title = f"System Health Alert: {status.upper()}"
            message = f"""Learning System Health Issue Detected

Overall Health Score: {overall_health:.1%}
Status: {status}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Component Status:
- Database Connection: {'OK' if health_status.get('database_connection') else 'FAIL'}
- Model Storage: {'OK' if health_status.get('model_storage') else 'FAIL'}
- Active Models: {health_status.get('active_models', 0)}
- System Errors: {health_status.get('system_errors', 0)}

Action Required: Check system components and resolve issues."""
            
            return self._send_notification(level, title, message, health_status)
            
        except Exception as e:
            self.logger.error(f"Error sending system health alert: {e}")
            return False
    
    def send_training_completion_notification(self, training_results: Dict[str, Any]) -> bool:
        """Send training completion notification"""
        try:
            best_model = training_results.get('best_model', {})
            models_trained = training_results.get('trained_models', [])
            
            level = NotificationLevel.INFO
            title = "Model Training Completed"
            message = f"""Model Training Cycle Completed Successfully

Models Trained: {len(models_trained)}
Best Model: {best_model.get('model_name', 'N/A')}
Best Accuracy: {best_model.get('test_accuracy', 0):.3f}
Training Data Size: {training_results.get('training_data_size', 0)}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Trained Models:
{', '.join(models_trained)}"""
            
            return self._send_notification(level, title, message, training_results)
            
        except Exception as e:
            self.logger.error(f"Error sending training completion notification: {e}")
            return False
    
    def send_error_notification(self, error_type: str, error_message: str, 
                              component: str = "Unknown") -> bool:
        """Send error notification"""
        try:
            level = NotificationLevel.ERROR
            title = f"Learning System Error: {error_type}"
            message = f"""Error Detected in Learning System

Component: {component}
Error Type: {error_type}
Error Message: {error_message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Action Required: Investigate and resolve the error."""
            
            event_data = {
                'error_type': error_type,
                'error_message': error_message,
                'component': component
            }
            
            return self._send_notification(level, title, message, event_data)
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False
    
    def send_custom_notification(self, level: NotificationLevel, title: str, 
                               message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Send custom notification"""
        try:
            return self._send_notification(level, title, message, data or {})
        except Exception as e:
            self.logger.error(f"Error sending custom notification: {e}")
            return False
    
    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notification history"""
        try:
            sorted_history = sorted(
                self.notification_history,
                key=lambda x: x['timestamp'],
                reverse=True
            )
            return sorted_history[:limit]
        except Exception as e:
            self.logger.error(f"Error getting notification history: {e}")
            return []
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update notification configuration"""
        try:
            self.config.update(new_config)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info("Notification configuration updated")
            return True
        except Exception as e:
            self.logger.error(f"Error updating notification config: {e}")
            return False
    
    def _load_config(self) -> Dict[str, Any]:
        """Load notification configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = self._get_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
            return config
        except Exception as e:
            self.logger.error(f"Error loading notification config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default notification configuration"""
        return {
            "enabled": True,
            "channels": {
                "log": {
                    "enabled": True,
                    "levels": ["INFO", "WARNING", "ERROR", "CRITICAL"]
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": [],
                    "levels": ["WARNING", "ERROR", "CRITICAL"]
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {},
                    "levels": ["ERROR", "CRITICAL"]
                },
                "telegram": {
                    "enabled": False,
                    "bot_token": "",
                    "chat_id": "",
                    "levels": ["WARNING", "ERROR", "CRITICAL"]
                }
            },
            "rate_limiting": {
                "enabled": True,
                "default_interval_minutes": 5
            },
            "alert_thresholds": {
                "error_count": 5,
                "performance_degradation": 0.1,
                "system_downtime_minutes": 30
            }
        }
    
    def _get_notification_level(self, event_type: LearningEventType) -> NotificationLevel:
        """Determine notification level based on event type"""
        level_mapping = {
            LearningEventType.MODEL_TRAINING_STARTED: NotificationLevel.INFO,
            LearningEventType.MODEL_TRAINING_COMPLETED: NotificationLevel.INFO,
            LearningEventType.MODEL_TRAINING_FAILED: NotificationLevel.ERROR,
            LearningEventType.MODEL_DEPLOYED: NotificationLevel.INFO,
            LearningEventType.MODEL_ROLLBACK: NotificationLevel.WARNING,
            LearningEventType.PERFORMANCE_DEGRADATION: NotificationLevel.WARNING,
            LearningEventType.RETRAINING_TRIGGERED: NotificationLevel.INFO,
            LearningEventType.DATA_QUALITY_ISSUE: NotificationLevel.WARNING
        }
        return level_mapping.get(event_type, NotificationLevel.INFO)
    
    def _should_send_notification(self, event_type: LearningEventType, 
                                level: NotificationLevel) -> bool:
        """Check if notification should be sent (rate limiting)"""
        try:
            if not self.config.get('rate_limiting', {}).get('enabled', True):
                return True
            
            rate_limit_key = f"{event_type.value}_{level.value}"
            
            if rate_limit_key in self.rate_limits:
                last_sent = self.rate_limits[rate_limit_key]
                interval_minutes = self.config.get('rate_limiting', {}).get('default_interval_minutes', 5)
                
                if datetime.now() - last_sent < timedelta(minutes=interval_minutes):
                    return False
            
            self.rate_limits[rate_limit_key] = datetime.now()
            return True
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {e}")
            return True
    
    def _create_event_message(self, event: LearningEventRecord) -> str:
        """Create notification message for learning event"""
        try:
            message = f"""Learning System Event: {event.event_type.value}

Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Success: {'YES' if event.success else 'NO'}"""
            
            if event.event_data:
                message += f"\n\nEvent Data:"
                for key, value in event.event_data.items():
                    message += f"\n- {key}: {value}"
            
            if event.error_message:
                message += f"\n\nError: {event.error_message}"
            
            return message
        except Exception as e:
            self.logger.error(f"Error creating event message: {e}")
            return f"Learning event: {event.event_type.value}"
    
    def _send_notification(self, level: NotificationLevel, title: str, 
                         message: str, event_data: Dict[str, Any]) -> bool:
        """Send notification through configured channels"""
        try:
            if not self.config.get('enabled', True):
                return True
            
            success = True
            channels = self.config.get('channels', {})
            
            for channel_name, channel_config in channels.items():
                if not channel_config.get('enabled', False):
                    continue
                
                channel_levels = channel_config.get('levels', [])
                if level.value not in channel_levels:
                    continue
                
                try:
                    if channel_name == 'log':
                        self._send_log_notification(level, title, message)
                except Exception as channel_error:
                    self.logger.error(f"Error sending notification via {channel_name}: {channel_error}")
                    success = False
            
            return success
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return False
    
    def _send_log_notification(self, level: NotificationLevel, title: str, message: str):
        """Send notification to log"""
        log_message = f"{title}\n{message}"
        
        if level == NotificationLevel.INFO:
            self.logger.info(log_message)
        elif level == NotificationLevel.WARNING:
            self.logger.warning(log_message)
        elif level == NotificationLevel.ERROR:
            self.logger.error(log_message)
        elif level == NotificationLevel.CRITICAL:
            self.logger.critical(log_message)
    
    def _record_notification(self, event_type: LearningEventType, level: NotificationLevel,
                           message: str, success: bool):
        """Record notification in history"""
        try:
            notification_record = {
                'timestamp': datetime.now(),
                'event_type': event_type.value,
                'level': level.value,
                'message': message,
                'success': success
            }
            
            self.notification_history.append(notification_record)
            
            if len(self.notification_history) > self.max_history:
                self.notification_history = self.notification_history[-self.max_history:]
        except Exception as e:
            self.logger.error(f"Error recording notification: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    notification_system = LearningNotificationSystem("Config/test_notifications.json")
    print("Learning Notification System initialized successfully!")
    
    test_event = LearningEventRecord(
        event_type=LearningEventType.MODEL_TRAINING_COMPLETED,
        event_data={'models_trained': 3, 'best_accuracy': 0.85},
        timestamp=datetime.now(),
        success=True
    )
    
    success = notification_system.send_learning_event_notification(test_event)
    print(f"Test notification sent: {success}")
    
    custom_success = notification_system.send_custom_notification(
        NotificationLevel.INFO,
        "Test Notification",
        "This is a test notification from the Learning Notification System"
    )
    print(f"Custom notification sent: {custom_success}")
    
    print("Learning Notification System test completed!")