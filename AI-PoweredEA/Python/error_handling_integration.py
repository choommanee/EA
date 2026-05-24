"""
Error Handling Integration
Integrates comprehensive error handling across all learning system components
"""

import sys
import os
sys.path.append('Python')

import logging
import functools
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
import warnings
warnings.filterwarnings('ignore')

from learning_error_handler import LearningErrorHandler, ErrorSeverity, ErrorCategory
from learning_coordinator import LearningCoordinator
from learning_config_manager import LearningConfigManager
from learning_notification_system import LearningNotificationSystem, NotificationLevel


def error_handler_decorator(component_name: str, error_handler: LearningErrorHandler,
                          severity: Optional[ErrorSeverity] = None,
                          fallback_return: Any = None):
    """Decorator to add error handling to component methods"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Handle the error
                error_id = error_handler.handle_error(
                    error=e,
                    component=component_name,
                    context={
                        'function': func.__name__,
                        'args': str(args)[:200],  # Truncate long args
                        'kwargs': str(kwargs)[:200]
                    },
                    severity=severity
                )
                
                # Return fallback value or re-raise based on severity
                if severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
                    return fallback_return
                else:
                    raise
        
        return wrapper
    return decorator


class ErrorHandlingIntegration:
    """Integrates error handling across all learning system components"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db",
                 log_dir: str = "Logs"):
        self.logger = logging.getLogger(__name__)
        
        # Initialize error handler
        self.error_handler = LearningErrorHandler(db_path, log_dir)
        
        # Component references
        self.coordinator = None
        self.config_manager = None
        self.notification_system = None
        
        # Integration status
        self.integration_status = {}
        self.recovery_strategies_registered = False
        
        self.logger.info("Error Handling Integration initialized")
    
    def integrate_with_coordinator(self, coordinator: LearningCoordinator) -> bool:
        """Integrate error handling with Learning Coordinator"""
        try:
            self.coordinator = coordinator
            
            # Register recovery strategies for coordinator
            self._register_coordinator_recovery_strategies()
            
            # Add error handling to coordinator methods
            self._wrap_coordinator_methods()
            
            # Register fallback handlers
            self._register_coordinator_fallbacks()
            
            self.integration_status['coordinator'] = 'integrated'
            self.logger.info("Error handling integrated with Learning Coordinator")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error integrating with coordinator: {e}")
            self.integration_status['coordinator'] = 'failed'
            return False
    
    def integrate_with_config_manager(self, config_manager: LearningConfigManager) -> bool:
        """Integrate error handling with Configuration Manager"""
        try:
            self.config_manager = config_manager
            
            # Register recovery strategies for config manager
            self._register_config_manager_recovery_strategies()
            
            # Add error handling to config manager methods
            self._wrap_config_manager_methods()
            
            # Register fallback handlers
            self._register_config_manager_fallbacks()
            
            self.integration_status['config_manager'] = 'integrated'
            self.logger.info("Error handling integrated with Configuration Manager")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error integrating with config manager: {e}")
            self.integration_status['config_manager'] = 'failed'
            return False
    
    def integrate_with_notification_system(self, notification_system: LearningNotificationSystem) -> bool:
        """Integrate error handling with Notification System"""
        try:
            self.notification_system = notification_system
            
            # Register recovery strategies for notification system
            self._register_notification_recovery_strategies()
            
            # Add error handling to notification system methods
            self._wrap_notification_methods()
            
            # Register fallback handlers
            self._register_notification_fallbacks()
            
            self.integration_status['notification_system'] = 'integrated'
            self.logger.info("Error handling integrated with Notification System")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error integrating with notification system: {e}")
            self.integration_status['notification_system'] = 'failed'
            return False
    
    def integrate_all_components(self, coordinator: LearningCoordinator,
                               config_manager: LearningConfigManager,
                               notification_system: LearningNotificationSystem) -> Dict[str, bool]:
        """Integrate error handling with all components"""
        try:
            results = {}
            
            # Integrate with each component
            results['coordinator'] = self.integrate_with_coordinator(coordinator)
            results['config_manager'] = self.integrate_with_config_manager(config_manager)
            results['notification_system'] = self.integrate_with_notification_system(notification_system)
            
            # Setup cross-component error handling
            self._setup_cross_component_error_handling()
            
            # Register global recovery strategies
            self._register_global_recovery_strategies()
            
            self.logger.info(f"Error handling integration completed: {results}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in complete integration: {e}")
            return {'error': str(e)}
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        try:
            status = {
                'integration_status': self.integration_status.copy(),
                'error_handler_status': {
                    'active': True,
                    'circuit_breakers': self.error_handler.get_circuit_breaker_status(),
                    'error_statistics': self.error_handler.get_error_statistics()
                },
                'recovery_strategies_count': len(self.error_handler.recovery_strategies),
                'fallback_handlers_count': len(self.error_handler.fallback_handlers)
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting integration status: {e}")
            return {'error': str(e)}
    
    def trigger_graceful_degradation(self, component: str, reason: str) -> bool:
        """Trigger graceful degradation for a component"""
        try:
            self.logger.warning(f"Triggering graceful degradation for {component}: {reason}")
            
            # Execute component-specific degradation
            if component == 'coordinator' and self.coordinator:
                return self._degrade_coordinator()
            elif component == 'config_manager' and self.config_manager:
                return self._degrade_config_manager()
            elif component == 'notification_system' and self.notification_system:
                return self._degrade_notification_system()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in graceful degradation: {e}")
            return False
    
    def _register_coordinator_recovery_strategies(self):
        """Register recovery strategies for coordinator"""
        try:
            # Learning cycle failure recovery
            def learning_cycle_recovery(error_record) -> bool:
                try:
                    if self.coordinator and hasattr(self.coordinator, 'learning_cycle_active'):
                        self.coordinator.learning_cycle_active = False
                        self.logger.info("Learning cycle reset after error")
                        return True
                    return False
                except:
                    return False
            
            self.error_handler.register_recovery_strategy(
                "Exception", "learning_coordinator", learning_cycle_recovery
            )
            
            # Database connection recovery for coordinator
            def coordinator_db_recovery(error_record) -> bool:
                try:
                    if self.coordinator and hasattr(self.coordinator, 'db_manager'):
                        # Attempt to reconnect database
                        self.coordinator.db_manager = type(self.coordinator.db_manager)(
                            self.coordinator.db_manager.db_path
                        )
                        return True
                    return False
                except:
                    return False
            
            self.error_handler.register_recovery_strategy(
                "DatabaseError", "learning_coordinator", coordinator_db_recovery
            )
            
        except Exception as e:
            self.logger.error(f"Error registering coordinator recovery strategies: {e}")
    
    def _register_config_manager_recovery_strategies(self):
        """Register recovery strategies for config manager"""
        try:
            # Configuration loading failure recovery
            def config_loading_recovery(error_record) -> bool:
                try:
                    if self.config_manager:
                        # Clear cache and try to load default config
                        self.config_manager.clear_cache()
                        return True
                    return False
                except:
                    return False
            
            self.error_handler.register_recovery_strategy(
                "FileNotFoundError", "config_manager", config_loading_recovery
            )
            
            # Configuration validation failure recovery
            def config_validation_recovery(error_record) -> bool:
                try:
                    if self.config_manager:
                        # Load default configuration
                        from learning_config_manager import LearningConfiguration
                        default_config = LearningConfiguration()
                        self.config_manager.save_config(default_config, "recovery_config")
                        return True
                    return False
                except:
                    return False
            
            self.error_handler.register_recovery_strategy(
                "ValidationError", "config_manager", config_validation_recovery
            )
            
        except Exception as e:
            self.logger.error(f"Error registering config manager recovery strategies: {e}")
    
    def _register_notification_recovery_strategies(self):
        """Register recovery strategies for notification system"""
        try:
            # Email sending failure recovery
            def email_recovery(error_record) -> bool:
                try:
                    if self.notification_system:
                        # Disable email temporarily and use log fallback
                        if 'channels' in self.notification_system.config:
                            self.notification_system.config['channels']['email']['enabled'] = False
                        return True
                    return False
                except:
                    return False
            
            self.error_handler.register_recovery_strategy(
                "SMTPException", "notification_system", email_recovery
            )
            
            # Webhook failure recovery
            def webhook_recovery(error_record) -> bool:
                try:
                    if self.notification_system:
                        # Disable webhook temporarily
                        if 'channels' in self.notification_system.config:
                            self.notification_system.config['channels']['webhook']['enabled'] = False
                        return True
                    return False
                except:
                    return False
            
            self.error_handler.register_recovery_strategy(
                "ConnectionError", "notification_system", webhook_recovery
            )
            
        except Exception as e:
            self.logger.error(f"Error registering notification recovery strategies: {e}")
    
    def _register_coordinator_fallbacks(self):
        """Register fallback handlers for coordinator"""
        try:
            def coordinator_fallback(error_record):
                try:
                    # Emergency stop if too many errors
                    if self.coordinator and error_record.severity == ErrorSeverity.CRITICAL:
                        self.coordinator.trigger_emergency_stop(
                            f"Critical error: {error_record.error_message}"
                        )
                    
                    # Send notification about fallback
                    if self.notification_system:
                        self.notification_system.send_error_notification(
                            error_record.error_type,
                            f"Fallback activated: {error_record.error_message}",
                            "learning_coordinator"
                        )
                        
                except Exception as fallback_error:
                    self.logger.error(f"Coordinator fallback error: {fallback_error}")
            
            self.error_handler.register_fallback_handler("learning_coordinator", coordinator_fallback)
            
        except Exception as e:
            self.logger.error(f"Error registering coordinator fallbacks: {e}")
    
    def _register_config_manager_fallbacks(self):
        """Register fallback handlers for config manager"""
        try:
            def config_manager_fallback(error_record):
                try:
                    # Use default configuration as fallback
                    if error_record.category == ErrorCategory.CONFIGURATION_ERROR:
                        self.logger.warning("Using default configuration as fallback")
                        
                    # Send notification about configuration issue
                    if self.notification_system:
                        self.notification_system.send_error_notification(
                            error_record.error_type,
                            f"Configuration fallback: {error_record.error_message}",
                            "config_manager"
                        )
                        
                except Exception as fallback_error:
                    self.logger.error(f"Config manager fallback error: {fallback_error}")
            
            self.error_handler.register_fallback_handler("config_manager", config_manager_fallback)
            
        except Exception as e:
            self.logger.error(f"Error registering config manager fallbacks: {e}")
    
    def _register_notification_fallbacks(self):
        """Register fallback handlers for notification system"""
        try:
            def notification_fallback(error_record):
                try:
                    # Always ensure log notification works as last resort
                    self.logger.error(f"Notification system fallback: {error_record.error_message}")
                    
                    # Try to send basic log notification
                    if error_record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                        self.logger.critical(f"Critical notification failure: {error_record.error_message}")
                        
                except Exception as fallback_error:
                    # Last resort - print to console
                    print(f"CRITICAL: Notification fallback failed: {fallback_error}")
            
            self.error_handler.register_fallback_handler("notification_system", notification_fallback)
            
        except Exception as e:
            self.logger.error(f"Error registering notification fallbacks: {e}")
    
    def _wrap_coordinator_methods(self):
        """Add error handling to coordinator methods"""
        try:
            if not self.coordinator:
                return
            
            # Wrap critical methods with error handling
            original_execute_cycle = self.coordinator.execute_learning_cycle
            
            @error_handler_decorator("learning_coordinator", self.error_handler, 
                                   ErrorSeverity.HIGH, {'status': 'error', 'error': 'Learning cycle failed'})
            def wrapped_execute_cycle(*args, **kwargs):
                return original_execute_cycle(*args, **kwargs)
            
            self.coordinator.execute_learning_cycle = wrapped_execute_cycle
            
            # Wrap start/stop methods
            original_start = self.coordinator.start_learning_system
            
            @error_handler_decorator("learning_coordinator", self.error_handler, 
                                   ErrorSeverity.CRITICAL, False)
            def wrapped_start(*args, **kwargs):
                return original_start(*args, **kwargs)
            
            self.coordinator.start_learning_system = wrapped_start
            
        except Exception as e:
            self.logger.error(f"Error wrapping coordinator methods: {e}")
    
    def _wrap_config_manager_methods(self):
        """Add error handling to config manager methods"""
        try:
            if not self.config_manager:
                return
            
            # Wrap configuration loading
            original_load_config = self.config_manager.load_config
            
            @error_handler_decorator("config_manager", self.error_handler, 
                                   ErrorSeverity.MEDIUM, None)
            def wrapped_load_config(*args, **kwargs):
                return original_load_config(*args, **kwargs)
            
            self.config_manager.load_config = wrapped_load_config
            
            # Wrap configuration saving
            original_save_config = self.config_manager.save_config
            
            @error_handler_decorator("config_manager", self.error_handler, 
                                   ErrorSeverity.HIGH, False)
            def wrapped_save_config(*args, **kwargs):
                return original_save_config(*args, **kwargs)
            
            self.config_manager.save_config = wrapped_save_config
            
        except Exception as e:
            self.logger.error(f"Error wrapping config manager methods: {e}")
    
    def _wrap_notification_methods(self):
        """Add error handling to notification system methods"""
        try:
            if not self.notification_system:
                return
            
            # Wrap notification sending
            original_send_notification = self.notification_system._send_notification
            
            @error_handler_decorator("notification_system", self.error_handler, 
                                   ErrorSeverity.MEDIUM, False)
            def wrapped_send_notification(*args, **kwargs):
                return original_send_notification(*args, **kwargs)
            
            self.notification_system._send_notification = wrapped_send_notification
            
        except Exception as e:
            self.logger.error(f"Error wrapping notification methods: {e}")
    
    def _setup_cross_component_error_handling(self):
        """Setup error handling between components"""
        try:
            # Connect error handler to notification system
            if self.notification_system:
                # Override error handler's notification sending
                original_send_error_notification = self.error_handler.notification_system.send_error_notification
                
                def enhanced_error_notification(error_type, error_message, component):
                    try:
                        # Try primary notification system first
                        return self.notification_system.send_error_notification(
                            error_type, error_message, component
                        )
                    except:
                        # Fallback to original
                        return original_send_error_notification(error_type, error_message, component)
                
                self.error_handler.notification_system.send_error_notification = enhanced_error_notification
            
        except Exception as e:
            self.logger.error(f"Error setting up cross-component error handling: {e}")
    
    def _register_global_recovery_strategies(self):
        """Register global recovery strategies"""
        try:
            # Memory error recovery
            def memory_error_recovery(error_record) -> bool:
                try:
                    import gc
                    gc.collect()  # Force garbage collection
                    self.logger.info("Memory cleanup performed")
                    return True
                except:
                    return False
            
            self.error_handler.register_recovery_strategy(
                "MemoryError", "global", memory_error_recovery
            )
            
            # General connection error recovery
            def connection_error_recovery(error_record) -> bool:
                try:
                    import time
                    time.sleep(5)  # Wait before retry
                    self.logger.info("Connection retry delay applied")
                    return True
                except:
                    return False
            
            self.error_handler.register_recovery_strategy(
                "ConnectionError", "global", connection_error_recovery
            )
            
        except Exception as e:
            self.logger.error(f"Error registering global recovery strategies: {e}")
    
    def _degrade_coordinator(self) -> bool:
        """Gracefully degrade coordinator functionality"""
        try:
            if self.coordinator:
                # Stop learning cycles but keep monitoring
                self.coordinator.learning_cycle_active = False
                self.logger.warning("Coordinator degraded: Learning cycles disabled")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error degrading coordinator: {e}")
            return False
    
    def _degrade_config_manager(self) -> bool:
        """Gracefully degrade config manager functionality"""
        try:
            if self.config_manager:
                # Clear cache and use defaults
                self.config_manager.clear_cache()
                self.logger.warning("Config manager degraded: Using cached/default configurations")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error degrading config manager: {e}")
            return False
    
    def _degrade_notification_system(self) -> bool:
        """Gracefully degrade notification system functionality"""
        try:
            if self.notification_system:
                # Disable all channels except log
                for channel in self.notification_system.config.get('channels', {}):
                    if channel != 'log':
                        self.notification_system.config['channels'][channel]['enabled'] = False
                
                self.logger.warning("Notification system degraded: Only log notifications active")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error degrading notification system: {e}")
            return False
    
    def shutdown(self):
        """Shutdown error handling integration"""
        try:
            if self.error_handler:
                self.error_handler.shutdown()
            
            self.logger.info("Error handling integration shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during integration shutdown: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize integration
    integration = ErrorHandlingIntegration("Data/test_integration.db")
    
    print("Error Handling Integration initialized successfully!")
    
    # Test integration status
    status = integration.get_integration_status()
    print(f"Integration status: {status}")
    
    print("Error Handling Integration test completed!")