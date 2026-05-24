"""
AI System Learning Compatibility Updates
Updates existing AI system to support learning integration
"""

import sys
import os
sys.path.append('Python')

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import sqlite3
import json
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Import existing AI system components
try:
    from ai_system_integration import AISystemIntegration
    from learning_configuration import LearningConfiguration
    from ai_learning_pipeline_integration import AILearningPipelineIntegration, SignalData, SignalOutcome
    AI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    AI_COMPONENTS_AVAILABLE = False
    logging.warning(f"AI components not available: {e}")


class LearningMode(Enum):
    """Learning mode types"""
    DISABLED = "disabled"
    PASSIVE = "passive"  # Collect data only
    ACTIVE = "active"    # Collect data and switch models
    AGGRESSIVE = "aggressive"  # Frequent model switching


class ModelSwitchStrategy(Enum):
    """Model switching strategies"""
    PERFORMANCE_BASED = "performance_based"
    TIME_BASED = "time_based"
    HYBRID = "hybrid"
    MANUAL = "manual"


@dataclass
class LearningCompatibilityConfig:
    """Configuration for learning compatibility"""
    learning_mode: LearningMode = LearningMode.ACTIVE
    model_switch_strategy: ModelSwitchStrategy = ModelSwitchStrategy.PERFORMANCE_BASED
    enable_data_collection: bool = True
    enable_model_switching: bool = True
    enable_performance_tracking: bool = True
    data_collection_interval: int = 60  # seconds
    model_evaluation_interval: int = 300  # 5 minutes
    performance_threshold: float = 0.05  # 5% improvement
    min_signals_for_switch: int = 50
    max_model_age_hours: int = 168  # 1 week
    backup_model_count: int = 3


class AISystemLearningCompatibility:
    """Updates AI system for learning compatibility"""
    
    def __init__(self, config: Optional[LearningCompatibilityConfig] = None,
                 ai_system: Optional[AISystemIntegration] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or LearningCompatibilityConfig()
        
        # AI system components
        self.ai_system = ai_system or AISystemIntegration()
        self.learning_config = LearningConfiguration()
        self.pipeline_integration = None
        
        # Learning state
        self.learning_enabled = False
        self.current_model_id = None
        self.model_performance_history = {}
        self.signal_count = 0
        self.last_model_evaluation = None
        
        # Data collection hooks
        self.signal_hooks = []
        self.outcome_hooks = []
        self.model_switch_hooks = []
        
        # Threading
        self.monitoring_thread = None
        self.is_monitoring = False
        
        self.logger.info("AI System Learning Compatibility initialized")
    
    def enable_learning_compatibility(self) -> bool:
        """Enable learning compatibility in AI system"""
        try:
            # Initialize pipeline integration
            self.pipeline_integration = AILearningPipelineIntegration()
            integration_success = self.pipeline_integration.initialize_integration()
            
            if not integration_success:
                self.logger.error("Failed to initialize pipeline integration")
                return False
            
            # Update AI system configuration
            self._update_ai_system_config()
            
            # Install data collection hooks
            self._install_data_collection_hooks()
            
            # Start monitoring if enabled
            if self.config.learning_mode != LearningMode.DISABLED:
                self._start_learning_monitoring()
            
            self.learning_enabled = True
            self.logger.info("Learning compatibility enabled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling learning compatibility: {e}")
            return False
    
    def disable_learning_compatibility(self) -> bool:
        """Disable learning compatibility"""
        try:
            self.learning_enabled = False
            
            # Stop monitoring
            self._stop_learning_monitoring()
            
            # Remove hooks
            self._remove_data_collection_hooks()
            
            # Reset AI system configuration
            self._reset_ai_system_config()
            
            self.logger.info("Learning compatibility disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling learning compatibility: {e}")
            return False
    
    def update_learning_mode(self, mode: LearningMode) -> bool:
        """Update learning mode"""
        try:
            old_mode = self.config.learning_mode
            self.config.learning_mode = mode
            
            # Restart monitoring with new mode
            if self.is_monitoring:
                self._stop_learning_monitoring()
                if mode != LearningMode.DISABLED:
                    self._start_learning_monitoring()
            
            self.logger.info(f"Learning mode updated: {old_mode.value} → {mode.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating learning mode: {e}")
            return False
    
    def install_signal_generation_hook(self, hook_function: Callable) -> bool:
        """Install hook for signal generation"""
        try:
            self.signal_hooks.append(hook_function)
            self.logger.info("Signal generation hook installed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing signal hook: {e}")
            return False
    
    def install_outcome_tracking_hook(self, hook_function: Callable) -> bool:
        """Install hook for outcome tracking"""
        try:
            self.outcome_hooks.append(hook_function)
            self.logger.info("Outcome tracking hook installed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing outcome hook: {e}")
            return False
    
    def process_signal_with_learning(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process signal with learning data collection"""
        try:
            # Create SignalData object
            learning_signal = SignalData(
                signal_id=signal_data.get('signal_id', f"signal_{int(time.time())}"),
                timestamp=datetime.now(),
                symbol=signal_data.get('symbol', 'UNKNOWN'),
                signal_type=signal_data.get('signal_type', 'UNKNOWN'),
                confidence=signal_data.get('confidence', 0.0),
                features=signal_data.get('features', {}),
                model_id=self.current_model_id
            )
            
            # Process through pipeline integration
            if self.pipeline_integration and self.config.enable_data_collection:
                self.pipeline_integration.process_new_signal(learning_signal)
            
            # Call signal hooks
            for hook in self.signal_hooks:
                try:
                    hook(learning_signal)
                except Exception as hook_error:
                    self.logger.error(f"Error in signal hook: {hook_error}")
            
            # Update signal count
            self.signal_count += 1
            
            # Process signal through original AI system
            result = self._process_signal_original(signal_data)
            
            # Add learning metadata to result
            result['learning_metadata'] = {
                'model_id': self.current_model_id,
                'signal_count': self.signal_count,
                'learning_enabled': self.learning_enabled,
                'learning_mode': self.config.learning_mode.value
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing signal with learning: {e}")
            return self._process_signal_original(signal_data)
    
    def process_outcome_with_learning(self, outcome_data: Dict[str, Any]) -> bool:
        """Process outcome with learning tracking"""
        try:
            # Create SignalOutcome object
            learning_outcome = SignalOutcome(
                signal_id=outcome_data.get('signal_id', 'unknown'),
                timestamp=datetime.now(),
                outcome=outcome_data.get('outcome', 'UNKNOWN'),
                profit_loss=outcome_data.get('profit_loss', 0.0),
                duration_minutes=outcome_data.get('duration_minutes', 0),
                actual_price=outcome_data.get('actual_price')
            )
            
            # Process through pipeline integration
            if self.pipeline_integration and self.config.enable_performance_tracking:
                self.pipeline_integration.process_signal_outcome(learning_outcome)
            
            # Call outcome hooks
            for hook in self.outcome_hooks:
                try:
                    hook(learning_outcome)
                except Exception as hook_error:
                    self.logger.error(f"Error in outcome hook: {hook_error}")
            
            # Update performance history
            self._update_performance_history(learning_outcome)
            
            # Check if model switching is needed
            if self.config.enable_model_switching:
                self._evaluate_model_switching()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing outcome with learning: {e}")
            return False
    
    def switch_model_with_learning(self, new_model_id: str, reason: str = "manual") -> bool:
        """Switch model with learning integration"""
        try:
            old_model_id = self.current_model_id
            
            # Switch model in AI system
            switch_success = self._switch_ai_system_model(new_model_id)
            
            if switch_success:
                self.current_model_id = new_model_id
                
                # Notify pipeline integration
                if self.pipeline_integration:
                    self.pipeline_integration.switch_model(new_model_id, reason)
                
                # Call model switch hooks
                for hook in self.model_switch_hooks:
                    try:
                        hook(old_model_id, new_model_id, reason)
                    except Exception as hook_error:
                        self.logger.error(f"Error in model switch hook: {hook_error}")
                
                # Reset signal count for new model
                self.signal_count = 0
                
                # Update configuration
                self._update_model_config(new_model_id)
                
                self.logger.info(f"Model switched with learning: {old_model_id} → {new_model_id}")
                return True
            else:
                self.logger.error(f"Failed to switch model in AI system: {new_model_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error switching model with learning: {e}")
            return False
    
    def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status"""
        try:
            status = {
                'learning_enabled': self.learning_enabled,
                'learning_mode': self.config.learning_mode.value,
                'model_switch_strategy': self.config.model_switch_strategy.value,
                'current_model_id': self.current_model_id,
                'signal_count': self.signal_count,
                'last_model_evaluation': self.last_model_evaluation.isoformat() if self.last_model_evaluation else None,
                'monitoring_active': self.is_monitoring,
                'performance_tracking': self.config.enable_performance_tracking,
                'data_collection': self.config.enable_data_collection,
                'model_switching': self.config.enable_model_switching
            }
            
            # Add performance summary if available
            if self.pipeline_integration:
                performance_summary = self.pipeline_integration.get_performance_summary(24)
                status['performance_summary'] = performance_summary
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting learning status: {e}")
            return {'error': str(e)}
    
    def update_learning_configuration(self, config_updates: Dict[str, Any]) -> bool:
        """Update learning configuration"""
        try:
            # Update configuration object
            for key, value in config_updates.items():
                if hasattr(self.config, key):
                    if key == 'learning_mode' and isinstance(value, str):
                        setattr(self.config, key, LearningMode(value))
                    elif key == 'model_switch_strategy' and isinstance(value, str):
                        setattr(self.config, key, ModelSwitchStrategy(value))
                    else:
                        setattr(self.config, key, value)
            
            # Update learning configuration system
            learning_config_updates = {
                'learning_compatibility': {
                    'learning_mode': self.config.learning_mode.value,
                    'model_switch_strategy': self.config.model_switch_strategy.value,
                    'enable_data_collection': self.config.enable_data_collection,
                    'enable_model_switching': self.config.enable_model_switching,
                    'performance_threshold': self.config.performance_threshold
                }
            }
            
            self.learning_config.update_configuration(learning_config_updates)
            
            self.logger.info("Learning configuration updated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating learning configuration: {e}")
            return False
    
    def _update_ai_system_config(self):
        """Update AI system configuration for learning"""
        try:
            # Get current AI system configuration
            current_config = self.ai_system.current_config or {}
            
            # Add learning-specific configuration
            learning_config = {
                'learning_enabled': True,
                'learning_mode': self.config.learning_mode.value,
                'model_switching_enabled': self.config.enable_model_switching,
                'data_collection_enabled': self.config.enable_data_collection,
                'performance_tracking_enabled': self.config.enable_performance_tracking,
                'model_evaluation_interval': self.config.model_evaluation_interval,
                'performance_threshold': self.config.performance_threshold
            }
            
            # Merge configurations
            updated_config = {**current_config, **learning_config}
            
            # Update AI system
            self.ai_system.update_config(updated_config)
            
        except Exception as e:
            self.logger.error(f"Error updating AI system config: {e}")
    
    def _install_data_collection_hooks(self):
        """Install data collection hooks in AI system"""
        try:
            # Install signal processing hook
            def signal_collection_hook(signal_data):
                if self.config.enable_data_collection:
                    self.process_signal_with_learning(signal_data)
            
            # Install outcome tracking hook
            def outcome_collection_hook(outcome_data):
                if self.config.enable_performance_tracking:
                    self.process_outcome_with_learning(outcome_data)
            
            # Register hooks with AI system (if supported)
            if hasattr(self.ai_system, 'register_signal_hook'):
                self.ai_system.register_signal_hook(signal_collection_hook)
            
            if hasattr(self.ai_system, 'register_outcome_hook'):
                self.ai_system.register_outcome_hook(outcome_collection_hook)
            
        except Exception as e:
            self.logger.error(f"Error installing data collection hooks: {e}")
    
    def _remove_data_collection_hooks(self):
        """Remove data collection hooks from AI system"""
        try:
            # Remove hooks from AI system (if supported)
            if hasattr(self.ai_system, 'clear_signal_hooks'):
                self.ai_system.clear_signal_hooks()
            
            if hasattr(self.ai_system, 'clear_outcome_hooks'):
                self.ai_system.clear_outcome_hooks()
            
        except Exception as e:
            self.logger.error(f"Error removing data collection hooks: {e}")
    
    def _start_learning_monitoring(self):
        """Start learning monitoring thread"""
        try:
            if self.is_monitoring:
                return
            
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._learning_monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            
            self.logger.info("Learning monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting learning monitoring: {e}")
    
    def _stop_learning_monitoring(self):
        """Stop learning monitoring thread"""
        try:
            self.is_monitoring = False
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5.0)
            
            self.logger.info("Learning monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping learning monitoring: {e}")
    
    def _learning_monitoring_loop(self):
        """Learning monitoring loop"""
        while self.is_monitoring:
            try:
                # Evaluate model performance
                if self.config.enable_model_switching:
                    self._evaluate_model_switching()
                
                # Collect system metrics
                if self.config.enable_performance_tracking:
                    self._collect_system_metrics()
                
                # Sleep for monitoring interval
                time.sleep(self.config.model_evaluation_interval)
                
            except Exception as e:
                self.logger.error(f"Error in learning monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _evaluate_model_switching(self):
        """Evaluate if model switching is needed"""
        try:
            if not self.config.enable_model_switching:
                return
            
            # Check if enough signals have been processed
            if self.signal_count < self.config.min_signals_for_switch:
                return
            
            # Check time since last evaluation
            now = datetime.now()
            if self.last_model_evaluation:
                time_since_eval = now - self.last_model_evaluation
                if time_since_eval.total_seconds() < self.config.model_evaluation_interval:
                    return
            
            self.last_model_evaluation = now
            
            # Get current model performance
            current_performance = self._get_current_model_performance()
            
            if current_performance is None:
                return
            
            # Evaluate switching based on strategy
            if self.config.model_switch_strategy == ModelSwitchStrategy.PERFORMANCE_BASED:
                self._evaluate_performance_based_switching(current_performance)
            elif self.config.model_switch_strategy == ModelSwitchStrategy.TIME_BASED:
                self._evaluate_time_based_switching()
            elif self.config.model_switch_strategy == ModelSwitchStrategy.HYBRID:
                self._evaluate_hybrid_switching(current_performance)
            
        except Exception as e:
            self.logger.error(f"Error evaluating model switching: {e}")
    
    def _evaluate_performance_based_switching(self, current_performance: Dict[str, float]):
        """Evaluate performance-based model switching"""
        try:
            current_accuracy = current_performance.get('accuracy', 0.0)
            
            # Get available models and their performance
            available_models = self._get_available_models()
            
            best_model = None
            best_accuracy = current_accuracy
            
            for model in available_models:
                model_performance = model.get('performance_metrics', {})
                model_accuracy = model_performance.get('accuracy', 0.0)
                
                # Check if model is significantly better
                if model_accuracy > best_accuracy + self.config.performance_threshold:
                    best_accuracy = model_accuracy
                    best_model = model
            
            # Switch to best model if found
            if best_model:
                self.switch_model_with_learning(
                    best_model['model_id'], 
                    "performance_improvement"
                )
            
        except Exception as e:
            self.logger.error(f"Error in performance-based switching evaluation: {e}")
    
    def _evaluate_time_based_switching(self):
        """Evaluate time-based model switching"""
        try:
            # Check model age
            model_age = self._get_current_model_age()
            
            if model_age and model_age.total_seconds() > (self.config.max_model_age_hours * 3600):
                # Find newest available model
                available_models = self._get_available_models()
                
                if available_models:
                    # Sort by creation time (newest first)
                    newest_model = max(available_models, 
                                     key=lambda m: m.get('created_at', ''))
                    
                    if newest_model['model_id'] != self.current_model_id:
                        self.switch_model_with_learning(
                            newest_model['model_id'], 
                            "time_based_refresh"
                        )
            
        except Exception as e:
            self.logger.error(f"Error in time-based switching evaluation: {e}")
    
    def _evaluate_hybrid_switching(self, current_performance: Dict[str, float]):
        """Evaluate hybrid model switching"""
        try:
            # Combine performance and time-based evaluation
            self._evaluate_performance_based_switching(current_performance)
            self._evaluate_time_based_switching()
            
        except Exception as e:
            self.logger.error(f"Error in hybrid switching evaluation: {e}")
    
    def _process_signal_original(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process signal through original AI system"""
        try:
            # This would call the original AI system signal processing
            # For now, return a mock result
            return {
                'signal_id': signal_data.get('signal_id'),
                'processed': True,
                'timestamp': datetime.now().isoformat(),
                'result': 'processed_by_ai_system'
            }
            
        except Exception as e:
            self.logger.error(f"Error in original signal processing: {e}")
            return {'error': str(e)}
    
    def _switch_ai_system_model(self, model_id: str) -> bool:
        """Switch model in AI system"""
        try:
            # This would call the AI system's model switching functionality
            if hasattr(self.ai_system, 'switch_to_model'):
                return self.ai_system.switch_to_model(model_id)
            else:
                # Mock successful switch
                return True
                
        except Exception as e:
            self.logger.error(f"Error switching AI system model: {e}")
            return False
    
    def _update_performance_history(self, outcome: SignalOutcome):
        """Update performance history"""
        try:
            if self.current_model_id not in self.model_performance_history:
                self.model_performance_history[self.current_model_id] = []
            
            performance_record = {
                'timestamp': outcome.timestamp,
                'outcome': outcome.outcome,
                'profit_loss': outcome.profit_loss,
                'accuracy': 1.0 if outcome.outcome == 'WIN' else 0.0
            }
            
            self.model_performance_history[self.current_model_id].append(performance_record)
            
            # Keep only recent history (last 1000 records)
            if len(self.model_performance_history[self.current_model_id]) > 1000:
                self.model_performance_history[self.current_model_id] = \
                    self.model_performance_history[self.current_model_id][-1000:]
            
        except Exception as e:
            self.logger.error(f"Error updating performance history: {e}")
    
    def _get_current_model_performance(self) -> Optional[Dict[str, float]]:
        """Get current model performance"""
        try:
            if not self.current_model_id or self.current_model_id not in self.model_performance_history:
                return None
            
            history = self.model_performance_history[self.current_model_id]
            
            if not history:
                return None
            
            # Calculate recent performance (last 100 signals)
            recent_history = history[-100:]
            
            total_signals = len(recent_history)
            wins = sum(1 for record in recent_history if record['outcome'] == 'WIN')
            total_profit = sum(record['profit_loss'] for record in recent_history)
            
            return {
                'accuracy': wins / total_signals if total_signals > 0 else 0.0,
                'total_profit': total_profit,
                'signal_count': total_signals,
                'avg_profit_per_signal': total_profit / total_signals if total_signals > 0 else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting current model performance: {e}")
            return None
    
    def _get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models"""
        try:
            # This would get models from the model manager
            # For now, return mock models
            return [
                {
                    'model_id': 'model_v1',
                    'created_at': '2024-01-01T00:00:00',
                    'performance_metrics': {'accuracy': 0.75}
                },
                {
                    'model_id': 'model_v2',
                    'created_at': '2024-01-02T00:00:00',
                    'performance_metrics': {'accuracy': 0.80}
                }
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return []
    
    def _get_current_model_age(self) -> Optional[timedelta]:
        """Get current model age"""
        try:
            if not self.current_model_id:
                return None
            
            # This would get model creation time from model manager
            # For now, return mock age
            return timedelta(hours=24)
            
        except Exception as e:
            self.logger.error(f"Error getting current model age: {e}")
            return None
    
    def _update_model_config(self, model_id: str):
        """Update model configuration"""
        try:
            model_config = {
                'current_model_id': model_id,
                'model_switched_at': datetime.now().isoformat(),
                'switch_count': getattr(self, 'switch_count', 0) + 1
            }
            
            self.learning_config.update_configuration({'model_config': model_config})
            setattr(self, 'switch_count', model_config['switch_count'])
            
        except Exception as e:
            self.logger.error(f"Error updating model config: {e}")
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # This would collect system performance metrics
            # For now, just log the collection
            self.logger.debug("Collecting system metrics for learning")
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _reset_ai_system_config(self):
        """Reset AI system configuration"""
        try:
            # Remove learning-specific configuration
            if hasattr(self.ai_system, 'current_config') and self.ai_system.current_config:
                config = self.ai_system.current_config.copy()
                
                # Remove learning keys
                learning_keys = [
                    'learning_enabled', 'learning_mode', 'model_switching_enabled',
                    'data_collection_enabled', 'performance_tracking_enabled'
                ]
                
                for key in learning_keys:
                    config.pop(key, None)
                
                self.ai_system.update_config(config)
            
        except Exception as e:
            self.logger.error(f"Error resetting AI system config: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize learning compatibility
    config = LearningCompatibilityConfig(
        learning_mode=LearningMode.ACTIVE,
        model_switch_strategy=ModelSwitchStrategy.PERFORMANCE_BASED,
        enable_data_collection=True,
        enable_model_switching=True
    )
    
    compatibility = AISystemLearningCompatibility(config)
    
    print("AI System Learning Compatibility initialized successfully!")
    
    # Enable learning compatibility
    success = compatibility.enable_learning_compatibility()
    print(f"Learning compatibility enabled: {'Success' if success else 'Failed'}")
    
    # Test signal processing
    test_signal = {
        'signal_id': 'test_001',
        'symbol': 'EURUSD',
        'signal_type': 'BUY',
        'confidence': 0.75,
        'features': {'rsi': 30, 'macd': 0.5}
    }
    
    result = compatibility.process_signal_with_learning(test_signal)
    print(f"Signal processing result: {result}")
    
    # Test outcome processing
    test_outcome = {
        'signal_id': 'test_001',
        'outcome': 'WIN',
        'profit_loss': 100.0,
        'duration_minutes': 30
    }
    
    outcome_success = compatibility.process_outcome_with_learning(test_outcome)
    print(f"Outcome processing: {'Success' if outcome_success else 'Failed'}")
    
    # Get learning status
    status = compatibility.get_learning_status()
    print(f"Learning status: {status}")
    
    # Disable learning compatibility
    compatibility.disable_learning_compatibility()
    
    print("AI System Learning Compatibility test completed!")