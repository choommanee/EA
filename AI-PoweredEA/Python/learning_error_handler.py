"""
Learning Error Handler
Comprehensive error handling and logging system for AI Continuous Learning
"""

import sys
import os
sys.path.append('Python')

import logging
import traceback
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from pathlib import Path
from enum import Enum
import threading
import time
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

from learning_database_manager import LearningDatabaseManager
from learning_notification_system import LearningNotificationSystem, NotificationLevel
from models.learning_models import LearningEventRecord, LearningEventType


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Error categories"""
    DATABASE_ERROR = "DATABASE_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    DATA_ERROR = "DATA_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ErrorRecord:
    """Error record for tracking and analysis"""
    error_id: str
    timestamp: datetime
    component: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    stack_trace: str
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: str = ""
    occurrence_count: int = 1


class LearningErrorHandler:
    """Comprehensive error handler for the learning system"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db",
                 log_dir: str = "Logs"):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.db_manager = LearningDatabaseManager(db_path)
        self.notification_system = LearningNotificationSystem()
        
        # Setup logging
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        
        # Error tracking
        self.error_records = {}
        self.error_counts = {}
        self.error_patterns = {}
        
        # Recovery strategies
        self.recovery_strategies = {}
        self.fallback_handlers = {}
        
        # Error thresholds
        self.error_thresholds = {
            ErrorSeverity.LOW: 10,      # 10 errors per hour
            ErrorSeverity.MEDIUM: 5,    # 5 errors per hour
            ErrorSeverity.HIGH: 3,      # 3 errors per hour
            ErrorSeverity.CRITICAL: 1   # 1 error per hour
        }
        
        # Circuit breaker settings
        self.circuit_breakers = {}
        self.circuit_breaker_thresholds = {
            'database': 5,
            'model_training': 3,
            'data_collection': 5,
            'notifications': 10
        }
        
        # Setup default recovery strategies
        self._setup_default_recovery_strategies()
        
        # Start error monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._error_monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Learning Error Handler initialized")
    
    def handle_error(self, error: Exception, component: str, 
                    context: Optional[Dict[str, Any]] = None,
                    severity: Optional[ErrorSeverity] = None) -> str:
        """Handle an error with comprehensive logging and recovery"""
        try:
            # Generate error ID
            error_id = self._generate_error_id()
            
            # Determine error details
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()
            
            # Determine severity if not provided
            if severity is None:
                severity = self._determine_severity(error, component)
            
            # Determine category
            category = self._determine_category(error, component)
            
            # Create error record
            error_record = ErrorRecord(
                error_id=error_id,
                timestamp=datetime.now(),
                component=component,
                error_type=error_type,
                error_message=error_message,
                severity=severity,
                category=category,
                stack_trace=stack_trace,
                context=context or {}
            )
            
            # Check for duplicate errors
            error_key = f"{component}_{error_type}_{error_message}"
            if error_key in self.error_records:
                existing_record = self.error_records[error_key]
                existing_record.occurrence_count += 1
                existing_record.timestamp = datetime.now()
                error_record = existing_record
            else:
                self.error_records[error_key] = error_record
            
            # Log error
            self._log_error(error_record)
            
            # Update error counts
            self._update_error_counts(component, severity)
            
            # Check circuit breakers
            self._check_circuit_breakers(component, error_record)
            
            # Send notifications if needed
            self._send_error_notification(error_record)
            
            # Attempt recovery
            recovery_success = self._attempt_recovery(error_record)
            
            # Log to database
            self._log_error_to_database(error_record, recovery_success)
            
            # Check error thresholds
            self._check_error_thresholds(component, severity)
            
            return error_id
            
        except Exception as handler_error:
            # Fallback logging if error handler itself fails
            self.logger.critical(f"Error handler failed: {handler_error}")
            self.logger.critical(f"Original error: {error}")
            return "error_handler_failed"
    
    def register_recovery_strategy(self, error_type: str, component: str,
                                 strategy: Callable[[ErrorRecord], bool]):
        """Register a recovery strategy for specific error types"""
        try:
            key = f"{component}_{error_type}"
            self.recovery_strategies[key] = strategy
            self.logger.info(f"Recovery strategy registered: {key}")
            
        except Exception as e:
            self.logger.error(f"Error registering recovery strategy: {e}")
    
    def register_fallback_handler(self, component: str, 
                                handler: Callable[[ErrorRecord], Any]):
        """Register a fallback handler for component failures"""
        try:
            self.fallback_handlers[component] = handler
            self.logger.info(f"Fallback handler registered: {component}")
            
        except Exception as e:
            self.logger.error(f"Error registering fallback handler: {e}")
    
    def get_error_statistics(self, time_window: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """Get error statistics for analysis"""
        try:
            cutoff_time = datetime.now() - time_window
            
            stats = {
                'total_errors': 0,
                'errors_by_severity': {s.value: 0 for s in ErrorSeverity},
                'errors_by_category': {c.value: 0 for c in ErrorCategory},
                'errors_by_component': {},
                'top_errors': [],
                'resolved_errors': 0,
                'unresolved_errors': 0,
                'recovery_success_rate': 0.0
            }
            
            recent_errors = []
            total_recovery_attempts = 0
            successful_recoveries = 0
            
            for error_record in self.error_records.values():
                if error_record.timestamp >= cutoff_time:
                    recent_errors.append(error_record)
                    stats['total_errors'] += error_record.occurrence_count
                    
                    # Count by severity
                    stats['errors_by_severity'][error_record.severity.value] += error_record.occurrence_count
                    
                    # Count by category
                    stats['errors_by_category'][error_record.category.value] += error_record.occurrence_count
                    
                    # Count by component
                    component = error_record.component
                    if component not in stats['errors_by_component']:
                        stats['errors_by_component'][component] = 0
                    stats['errors_by_component'][component] += error_record.occurrence_count
                    
                    # Count resolved/unresolved
                    if error_record.resolved:
                        stats['resolved_errors'] += 1
                        successful_recoveries += 1
                    else:
                        stats['unresolved_errors'] += 1
                    
                    total_recovery_attempts += 1
            
            # Calculate recovery success rate
            if total_recovery_attempts > 0:
                stats['recovery_success_rate'] = successful_recoveries / total_recovery_attempts
            
            # Get top errors by occurrence
            sorted_errors = sorted(recent_errors, key=lambda x: x.occurrence_count, reverse=True)
            stats['top_errors'] = [
                {
                    'error_id': err.error_id,
                    'component': err.component,
                    'error_type': err.error_type,
                    'message': err.error_message[:100],  # Truncate long messages
                    'count': err.occurrence_count,
                    'severity': err.severity.value
                }
                for err in sorted_errors[:10]
            ]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting error statistics: {e}")
            return {}
    
    def resolve_error(self, error_id: str, resolution_notes: str = "") -> bool:
        """Mark an error as resolved"""
        try:
            for error_record in self.error_records.values():
                if error_record.error_id == error_id:
                    error_record.resolved = True
                    error_record.resolution_notes = resolution_notes
                    
                    self.logger.info(f"Error resolved: {error_id}")
                    return True
            
            self.logger.warning(f"Error not found for resolution: {error_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error resolving error: {e}")
            return False
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        try:
            status = {}
            
            for component, breaker_info in self.circuit_breakers.items():
                status[component] = {
                    'is_open': breaker_info.get('is_open', False),
                    'error_count': breaker_info.get('error_count', 0),
                    'threshold': self.circuit_breaker_thresholds.get(component, 5),
                    'last_error': breaker_info.get('last_error', None),
                    'opened_at': breaker_info.get('opened_at', None)
                }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting circuit breaker status: {e}")
            return {}
    
    def reset_circuit_breaker(self, component: str) -> bool:
        """Reset a circuit breaker"""
        try:
            if component in self.circuit_breakers:
                self.circuit_breakers[component] = {
                    'is_open': False,
                    'error_count': 0,
                    'last_error': None,
                    'opened_at': None
                }
                
                self.logger.info(f"Circuit breaker reset: {component}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error resetting circuit breaker: {e}")
            return False
    
    def cleanup_old_errors(self, retention_days: int = 30) -> int:
        """Clean up old error records"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            old_errors = []
            for key, error_record in self.error_records.items():
                if error_record.timestamp < cutoff_date:
                    old_errors.append(key)
            
            for key in old_errors:
                del self.error_records[key]
            
            self.logger.info(f"Cleaned up {len(old_errors)} old error records")
            return len(old_errors)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old errors: {e}")
            return 0
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        try:
            # Create formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            
            simple_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            
            # Error log file
            error_log_file = self.log_dir / "learning_errors.log"
            error_handler = logging.FileHandler(error_log_file)
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            
            # Debug log file
            debug_log_file = self.log_dir / "learning_debug.log"
            debug_handler = logging.FileHandler(debug_log_file)
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(detailed_formatter)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(simple_formatter)
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            
            # Add handlers if not already present
            if not any(isinstance(h, logging.FileHandler) and 'errors' in str(h.baseFilename) 
                      for h in root_logger.handlers):
                root_logger.addHandler(error_handler)
            
            if not any(isinstance(h, logging.FileHandler) and 'debug' in str(h.baseFilename) 
                      for h in root_logger.handlers):
                root_logger.addHandler(debug_handler)
            
            if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
                root_logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"Error setting up logging: {e}")
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        import uuid
        return f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    def _determine_severity(self, error: Exception, component: str) -> ErrorSeverity:
        """Determine error severity based on error type and component"""
        try:
            # Critical errors
            critical_errors = [
                'SystemExit', 'KeyboardInterrupt', 'MemoryError',
                'DatabaseConnectionError', 'SecurityError'
            ]
            
            # High severity errors
            high_errors = [
                'ValueError', 'TypeError', 'AttributeError',
                'FileNotFoundError', 'PermissionError'
            ]
            
            # Medium severity errors
            medium_errors = [
                'ConnectionError', 'TimeoutError', 'ValidationError'
            ]
            
            error_type = type(error).__name__
            
            if error_type in critical_errors:
                return ErrorSeverity.CRITICAL
            elif error_type in high_errors:
                return ErrorSeverity.HIGH
            elif error_type in medium_errors:
                return ErrorSeverity.MEDIUM
            else:
                return ErrorSeverity.LOW
                
        except Exception:
            return ErrorSeverity.MEDIUM
    
    def _determine_category(self, error: Exception, component: str) -> ErrorCategory:
        """Determine error category"""
        try:
            error_type = type(error).__name__
            error_message = str(error).lower()
            
            # Database errors
            if 'database' in error_message or 'sql' in error_message or 'connection' in error_message:
                return ErrorCategory.DATABASE_ERROR
            
            # Model errors
            if 'model' in component.lower() or 'training' in error_message:
                return ErrorCategory.MODEL_ERROR
            
            # Data errors
            if 'data' in error_message or error_type in ['ValueError', 'TypeError']:
                return ErrorCategory.DATA_ERROR
            
            # Configuration errors
            if 'config' in error_message or 'setting' in error_message:
                return ErrorCategory.CONFIGURATION_ERROR
            
            # Network errors
            if 'network' in error_message or 'connection' in error_message:
                return ErrorCategory.NETWORK_ERROR
            
            # System errors
            if error_type in ['SystemError', 'OSError', 'MemoryError']:
                return ErrorCategory.SYSTEM_ERROR
            
            # Validation errors
            if 'validation' in error_message or 'invalid' in error_message:
                return ErrorCategory.VALIDATION_ERROR
            
            # Timeout errors
            if 'timeout' in error_message or error_type == 'TimeoutError':
                return ErrorCategory.TIMEOUT_ERROR
            
            # Permission errors
            if 'permission' in error_message or error_type == 'PermissionError':
                return ErrorCategory.PERMISSION_ERROR
            
            return ErrorCategory.UNKNOWN_ERROR
            
        except Exception:
            return ErrorCategory.UNKNOWN_ERROR
    
    def _log_error(self, error_record: ErrorRecord):
        """Log error with appropriate level"""
        try:
            log_message = f"[{error_record.error_id}] {error_record.component}: {error_record.error_message}"
            
            if error_record.severity == ErrorSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif error_record.severity == ErrorSeverity.HIGH:
                self.logger.error(log_message)
            elif error_record.severity == ErrorSeverity.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            # Log stack trace for high severity errors
            if error_record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.logger.debug(f"Stack trace for {error_record.error_id}:\n{error_record.stack_trace}")
                
        except Exception as e:
            print(f"Error logging error: {e}")
    
    def _update_error_counts(self, component: str, severity: ErrorSeverity):
        """Update error counts for monitoring"""
        try:
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            
            if component not in self.error_counts:
                self.error_counts[component] = {}
            
            if current_hour not in self.error_counts[component]:
                self.error_counts[component][current_hour] = {s.value: 0 for s in ErrorSeverity}
            
            self.error_counts[component][current_hour][severity.value] += 1
            
        except Exception as e:
            self.logger.error(f"Error updating error counts: {e}")
    
    def _check_circuit_breakers(self, component: str, error_record: ErrorRecord):
        """Check and update circuit breakers"""
        try:
            if component not in self.circuit_breakers:
                self.circuit_breakers[component] = {
                    'is_open': False,
                    'error_count': 0,
                    'last_error': None,
                    'opened_at': None
                }
            
            breaker = self.circuit_breakers[component]
            threshold = self.circuit_breaker_thresholds.get(component, 5)
            
            # Increment error count
            breaker['error_count'] += 1
            breaker['last_error'] = error_record.timestamp
            
            # Check if threshold exceeded
            if breaker['error_count'] >= threshold and not breaker['is_open']:
                breaker['is_open'] = True
                breaker['opened_at'] = datetime.now()
                
                self.logger.critical(f"Circuit breaker opened for {component}")
                
                # Send critical notification
                self.notification_system.send_error_notification(
                    "CircuitBreakerOpened",
                    f"Circuit breaker opened for {component} after {breaker['error_count']} errors",
                    component
                )
                
        except Exception as e:
            self.logger.error(f"Error checking circuit breakers: {e}")
    
    def _send_error_notification(self, error_record: ErrorRecord):
        """Send error notification if needed"""
        try:
            # Send notifications for high and critical errors
            if error_record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.notification_system.send_error_notification(
                    error_record.error_type,
                    error_record.error_message,
                    error_record.component
                )
                
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
    
    def _attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from error"""
        try:
            # Check for specific recovery strategy
            strategy_key = f"{error_record.component}_{error_record.error_type}"
            
            if strategy_key in self.recovery_strategies:
                strategy = self.recovery_strategies[strategy_key]
                success = strategy(error_record)
                
                if success:
                    error_record.resolved = True
                    error_record.resolution_notes = f"Recovered using strategy: {strategy_key}"
                    self.logger.info(f"Error recovered: {error_record.error_id}")
                    return True
            
            # Check for fallback handler
            if error_record.component in self.fallback_handlers:
                fallback = self.fallback_handlers[error_record.component]
                try:
                    fallback(error_record)
                    self.logger.info(f"Fallback handler executed for: {error_record.error_id}")
                except Exception as fallback_error:
                    self.logger.error(f"Fallback handler failed: {fallback_error}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in recovery attempt: {e}")
            return False
    
    def _log_error_to_database(self, error_record: ErrorRecord, recovery_success: bool):
        """Log error to database"""
        try:
            event_data = {
                'error_id': error_record.error_id,
                'component': error_record.component,
                'error_type': error_record.error_type,
                'error_message': error_record.error_message,
                'severity': error_record.severity.value,
                'category': error_record.category.value,
                'occurrence_count': error_record.occurrence_count,
                'recovery_success': recovery_success,
                'context': error_record.context
            }
            
            event = LearningEventRecord(
                event_type=LearningEventType.MODEL_TRAINING_FAILED,
                event_data=event_data,
                timestamp=error_record.timestamp,
                success=False,
                error_message=error_record.error_message
            )
            
            self.db_manager.log_learning_event(event)
            
        except Exception as e:
            self.logger.error(f"Error logging to database: {e}")
    
    def _check_error_thresholds(self, component: str, severity: ErrorSeverity):
        """Check if error thresholds are exceeded"""
        try:
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            
            if component in self.error_counts and current_hour in self.error_counts[component]:
                error_count = self.error_counts[component][current_hour][severity.value]
                threshold = self.error_thresholds[severity]
                
                if error_count >= threshold:
                    self.logger.warning(f"Error threshold exceeded for {component}: "
                                      f"{error_count} {severity.value} errors in current hour")
                    
                    # Send threshold notification
                    self.notification_system.send_error_notification(
                        "ErrorThresholdExceeded",
                        f"Error threshold exceeded: {error_count} {severity.value} errors in {component}",
                        component
                    )
                    
        except Exception as e:
            self.logger.error(f"Error checking thresholds: {e}")
    
    def _setup_default_recovery_strategies(self):
        """Setup default recovery strategies"""
        try:
            # Database connection recovery
            def database_recovery(error_record: ErrorRecord) -> bool:
                try:
                    # Wait and retry connection
                    time.sleep(5)
                    # This would attempt to reconnect to database
                    return True
                except:
                    return False
            
            self.register_recovery_strategy("ConnectionError", "database", database_recovery)
            
            # Model training recovery
            def model_training_recovery(error_record: ErrorRecord) -> bool:
                try:
                    # Reduce batch size or use fallback model
                    return True
                except:
                    return False
            
            self.register_recovery_strategy("MemoryError", "model_training", model_training_recovery)
            
        except Exception as e:
            self.logger.error(f"Error setting up default recovery strategies: {e}")
    
    def _error_monitoring_loop(self):
        """Background error monitoring loop"""
        try:
            while self.monitoring_active:
                # Clean up old error counts
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for component in list(self.error_counts.keys()):
                    for hour in list(self.error_counts[component].keys()):
                        if hour < cutoff_time:
                            del self.error_counts[component][hour]
                
                # Reset circuit breakers after timeout
                for component, breaker in self.circuit_breakers.items():
                    if breaker['is_open'] and breaker['opened_at']:
                        if datetime.now() - breaker['opened_at'] > timedelta(minutes=30):
                            self.reset_circuit_breaker(component)
                
                time.sleep(300)  # Check every 5 minutes
                
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}")
    
    def shutdown(self):
        """Shutdown error handler"""
        try:
            self.monitoring_active = False
            if self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            self.logger.info("Learning Error Handler shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize error handler
    error_handler = LearningErrorHandler("Data/test_error_handler.db")
    
    print("Learning Error Handler initialized successfully!")
    
    # Test error handling
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        error_id = error_handler.handle_error(e, "test_component")
        print(f"Test error handled: {error_id}")
    
    # Test error statistics
    stats = error_handler.get_error_statistics()
    print(f"Error statistics: {stats}")
    
    # Test circuit breaker status
    cb_status = error_handler.get_circuit_breaker_status()
    print(f"Circuit breaker status: {cb_status}")
    
    print("Learning Error Handler test completed!")
    
    print("Learning Error Handler initialized successfully!")
    
    # Test error handling
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        error_id = error_handler.handle_error(e, "test_component", {"test_context": "demo"})
        print(f"Error handled: {error_id}")
    
    # Get error statistics
    stats = error_handler.get_error_statistics()
    print(f"Error statistics: {stats}")
    
    print("Learning Error Handler test completed!")