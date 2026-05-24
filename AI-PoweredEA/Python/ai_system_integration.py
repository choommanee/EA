"""
AI System Integration for Model Management
Integrates ModelManager with existing AI analysis system for seamless model switching
"""

import sys
import os
sys.path.append('Python')

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import json
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

try:
    from model_manager import ModelManager, ModelStatus, ModelType
    from performance_monitor import PerformanceMonitor
    from model_evaluator import ModelEvaluator
except ImportError:
    from Python.model_manager import ModelManager, ModelStatus, ModelType
    from Python.performance_monitor import PerformanceMonitor
    from Python.model_evaluator import ModelEvaluator


class IntegrationStatus(Enum):
    """Integration status types"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SWITCHING = "switching"
    ERROR = "error"


@dataclass
class ModelSwitchEvent:
    """Model switching event information"""
    event_id: str
    from_model_id: str
    from_version: str
    to_model_id: str
    to_version: str
    switch_reason: str
    switch_timestamp: datetime
    performance_before: float
    performance_after: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class AISystemConfig:
    """AI system configuration"""
    active_model_id: str
    active_version: str
    fallback_model_id: Optional[str] = None
    fallback_version: Optional[str] = None
    auto_switching_enabled: bool = True
    performance_threshold: float = 0.7
    switch_cooldown_minutes: int = 30
    max_daily_switches: int = 5


class AISystemIntegration:
    """Integration layer between ModelManager and AI analysis system"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db", 
                 models_directory: str = "Models"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # Initialize components
        self.model_manager = ModelManager(db_path, models_directory)
        self.performance_monitor = PerformanceMonitor(db_path)
        self.model_evaluator = ModelEvaluator(db_path)
        
        # Integration state
        self.status = IntegrationStatus.INACTIVE
        self.current_config = None
        self.last_switch_time = None
        self.daily_switch_count = 0
        self.switch_history = []
        
        # Model cache for performance
        self.active_model_cache = {}
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=15)
        
        # Initialize database tables
        self._init_integration_tables()
        
        # Load current configuration
        self._load_current_config()
        
        self.logger.info("AI System Integration initialized")
    
    def activate_integration(self, model_id: str, version: str, 
                           fallback_model_id: Optional[str] = None,
                           fallback_version: Optional[str] = None) -> bool:
        """Activate integration with specified model"""
        try:
            self.logger.info(f"Activating AI system integration with model: {model_id} v{version}")
            
            # Verify model exists and is deployable
            model_version = self.model_manager._get_model_version(model_id, version)
            if not model_version:
                raise ValueError(f"Model version not found: {model_id} v{version}")
            
            if model_version.status == ModelStatus.DEVELOPMENT:
                raise ValueError(f"Cannot activate development model: {model_id} v{version}")
            
            # Load and validate model
            model, _ = self.model_manager.load_model(model_id, version)
            if not self._validate_model_for_ai_system(model):
                raise ValueError(f"Model validation failed: {model_id} v{version}")
            
            # Create configuration
            config = AISystemConfig(
                active_model_id=model_id,
                active_version=version,
                fallback_model_id=fallback_model_id,
                fallback_version=fallback_version
            )
            
            # Deploy model to production
            deployment = self.model_manager.deploy_model(model_id, version, "production")
            if not deployment.health_check_results.get('healthy', False):
                raise ValueError(f"Model health check failed: {model_id} v{version}")
            
            # Update configuration
            self._save_config(config)
            self.current_config = config
            self.status = IntegrationStatus.ACTIVE
            
            # Clear cache
            self._clear_model_cache()
            
            # Log activation
            self._log_integration_event("integration_activated", {
                "model_id": model_id,
                "version": version,
                "fallback_model_id": fallback_model_id,
                "fallback_version": fallback_version
            })
            
            self.logger.info(f"AI system integration activated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error activating integration: {e}")
            self.status = IntegrationStatus.ERROR
            return False
    
    def get_active_model(self) -> Tuple[Optional[Any], Optional[str]]:
        """Get the currently active model for AI system"""
        try:
            if self.status != IntegrationStatus.ACTIVE or not self.current_config:
                return None, None
            
            # Check cache first
            if self._is_cache_valid():
                cached_model = self.active_model_cache.get('model')
                cached_version = self.active_model_cache.get('version')
                if cached_model and cached_version:
                    return cached_model, cached_version
            
            # Load active model
            model, model_version = self.model_manager.load_model(
                self.current_config.active_model_id,
                self.current_config.active_version
            )
            
            # Update cache
            self.active_model_cache = {
                'model': model,
                'version': f"{model_version.model_id}_v{model_version.version}",
                'model_version': model_version
            }
            self.cache_timestamp = datetime.now()
            
            return model, self.active_model_cache['version']
            
        except Exception as e:
            self.logger.error(f"Error getting active model: {e}")
            return None, None
    
    def make_prediction(self, features: np.ndarray, symbol: str = "default") -> Optional[Dict[str, Any]]:
        """Make prediction using active model"""
        try:
            model, model_version = self.get_active_model()
            if not model:
                self.logger.warning("No active model available for prediction")
                return None
            
            # Ensure features are in correct format
            if len(features.shape) == 1:
                features = features.reshape(1, -1)
            
            # Make prediction
            prediction = model.predict(features)[0]
            
            # Get prediction probability if available
            confidence = 0.5  # Default confidence
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(features)[0]
                confidence = float(np.max(probabilities))
            
            # Create result
            result = {
                'prediction': int(prediction),
                'confidence': confidence,
                'model_version': model_version,
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'features_shape': features.shape
            }
            
            # Log prediction for monitoring
            self._log_prediction(result, features)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            return None
    
    def check_model_performance_and_switch(self, force_check: bool = False) -> bool:
        """Check model performance and switch if needed"""
        try:
            if self.status != IntegrationStatus.ACTIVE or not self.current_config:
                return False
            
            if not self.current_config.auto_switching_enabled and not force_check:
                return False
            
            # Check cooldown period
            if not force_check and self._is_in_cooldown():
                return False
            
            # Check daily switch limit
            if not force_check and self._exceeded_daily_limit():
                return False
            
            # Get current model performance
            current_performance = self._get_current_model_performance()
            
            # Check if performance is below threshold
            if current_performance >= self.current_config.performance_threshold and not force_check:
                return False
            
            self.logger.info(f"Current model performance: {current_performance:.3f}, threshold: {self.current_config.performance_threshold}")
            
            # Find better model
            better_model = self._find_better_model(current_performance)
            if not better_model:
                self.logger.info("No better model found")
                return False
            
            # Perform model switch
            return self._switch_to_model(
                better_model['model_id'],
                better_model['version'],
                f"Performance improvement: {current_performance:.3f} -> {better_model['performance']:.3f}"
            )
            
        except Exception as e:
            self.logger.error(f"Error checking model performance: {e}")
            return False
    
    def switch_to_model(self, model_id: str, version: str, reason: str = "Manual switch") -> bool:
        """Manually switch to a specific model"""
        try:
            return self._switch_to_model(model_id, version, reason)
            
        except Exception as e:
            self.logger.error(f"Error switching to model {model_id} v{version}: {e}")
            return False
    
    def rollback_to_previous_model(self, reason: str = "Performance degradation") -> bool:
        """Rollback to the previous model"""
        try:
            if not self.switch_history:
                self.logger.warning("No previous model to rollback to")
                return False
            
            # Get last successful switch
            last_switch = None
            for switch in reversed(self.switch_history):
                if switch.success:
                    last_switch = switch
                    break
            
            if not last_switch:
                self.logger.warning("No successful previous model found")
                return False
            
            # Rollback to previous model
            return self._switch_to_model(
                last_switch.from_model_id,
                last_switch.from_version,
                f"Rollback: {reason}"
            )
            
        except Exception as e:
            self.logger.error(f"Error rolling back model: {e}")
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status and metrics"""
        try:
            status_info = {
                'status': self.status.value,
                'active_model': None,
                'performance': None,
                'last_switch': None,
                'daily_switches': self.daily_switch_count,
                'total_switches': len(self.switch_history),
                'config': None
            }
            
            if self.current_config:
                status_info['config'] = {
                    'active_model_id': self.current_config.active_model_id,
                    'active_version': self.current_config.active_version,
                    'auto_switching_enabled': self.current_config.auto_switching_enabled,
                    'performance_threshold': self.current_config.performance_threshold
                }
                
                # Get active model info
                model, model_version = self.get_active_model()
                if model:
                    status_info['active_model'] = model_version
                    status_info['performance'] = self._get_current_model_performance()
            
            # Get last switch info
            if self.switch_history:
                last_switch = self.switch_history[-1]
                status_info['last_switch'] = {
                    'timestamp': last_switch.switch_timestamp.isoformat(),
                    'reason': last_switch.switch_reason,
                    'success': last_switch.success,
                    'from_model': f"{last_switch.from_model_id}_v{last_switch.from_version}",
                    'to_model': f"{last_switch.to_model_id}_v{last_switch.to_version}"
                }
            
            return status_info
            
        except Exception as e:
            self.logger.error(f"Error getting integration status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def update_config(self, **kwargs) -> bool:
        """Update integration configuration"""
        try:
            if not self.current_config:
                self.logger.error("No active configuration to update")
                return False
            
            # Update configuration fields
            for key, value in kwargs.items():
                if hasattr(self.current_config, key):
                    setattr(self.current_config, key, value)
                    self.logger.info(f"Updated config: {key} = {value}")
            
            # Save updated configuration
            self._save_config(self.current_config)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
    
    def deactivate_integration(self) -> bool:
        """Deactivate the integration"""
        try:
            self.logger.info("Deactivating AI system integration")
            
            self.status = IntegrationStatus.INACTIVE
            self.current_config = None
            self._clear_model_cache()
            
            # Log deactivation
            self._log_integration_event("integration_deactivated", {
                "deactivated_at": datetime.now().isoformat()
            })
            
            self.logger.info("AI system integration deactivated")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deactivating integration: {e}")
            return False
    
    def _switch_to_model(self, model_id: str, version: str, reason: str) -> bool:
        """Internal method to switch to a specific model"""
        try:
            self.logger.info(f"Switching to model: {model_id} v{version} (reason: {reason})")
            self.status = IntegrationStatus.SWITCHING
            
            # Get current model info
            current_model_id = self.current_config.active_model_id
            current_version = self.current_config.active_version
            current_performance = self._get_current_model_performance()
            
            # Create switch event
            switch_event = ModelSwitchEvent(
                event_id=f"switch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                from_model_id=current_model_id,
                from_version=current_version,
                to_model_id=model_id,
                to_version=version,
                switch_reason=reason,
                switch_timestamp=datetime.now(),
                performance_before=current_performance
            )
            
            try:
                # Verify new model
                model_version = self.model_manager._get_model_version(model_id, version)
                if not model_version:
                    raise ValueError(f"Model version not found: {model_id} v{version}")
                
                # Load and validate new model
                new_model, _ = self.model_manager.load_model(model_id, version)
                if not self._validate_model_for_ai_system(new_model):
                    raise ValueError(f"Model validation failed: {model_id} v{version}")
                
                # Deploy new model
                deployment = self.model_manager.deploy_model(model_id, version, "production")
                if not deployment.health_check_results.get('healthy', False):
                    raise ValueError(f"Model health check failed: {model_id} v{version}")
                
                # Update configuration
                self.current_config.active_model_id = model_id
                self.current_config.active_version = version
                self._save_config(self.current_config)
                
                # Clear cache
                self._clear_model_cache()
                
                # Update switch event
                switch_event.success = True
                switch_event.performance_after = self._get_current_model_performance()
                
                # Update tracking
                self.last_switch_time = datetime.now()
                self.daily_switch_count += 1
                self.status = IntegrationStatus.ACTIVE
                
                self.logger.info(f"Model switch successful: {model_id} v{version}")
                
            except Exception as switch_error:
                switch_event.success = False
                switch_event.error_message = str(switch_error)
                self.status = IntegrationStatus.ERROR
                raise switch_error
            
            finally:
                # Store switch event
                self.switch_history.append(switch_event)
                self._store_switch_event(switch_event)
            
            return switch_event.success
            
        except Exception as e:
            self.logger.error(f"Error switching to model: {e}")
            self.status = IntegrationStatus.ERROR
            return False
    
    def _get_current_model_performance(self) -> float:
        """Get current model performance"""
        try:
            if not self.current_config:
                return 0.0
            
            # Get recent performance data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)  # Last 24 hours
            
            # Use performance monitor to get metrics
            performance_data = self.performance_monitor.get_performance_summary(
                start_time=start_time,
                end_time=end_time
            )
            
            if not performance_data or 'accuracy' not in performance_data:
                return 0.5  # Default performance
            
            return float(performance_data['accuracy'])
            
        except Exception as e:
            self.logger.error(f"Error getting current model performance: {e}")
            return 0.0
    
    def _find_better_model(self, current_performance: float) -> Optional[Dict[str, Any]]:
        """Find a better performing model"""
        try:
            # Get available models
            available_models = self.model_manager.list_models(
                status_filter=ModelStatus.PRODUCTION
            )
            
            best_model = None
            best_performance = current_performance
            
            for model_version in available_models:
                # Skip current model
                if (model_version.model_id == self.current_config.active_model_id and 
                    model_version.version == self.current_config.active_version):
                    continue
                
                # Get model performance
                performance = self._estimate_model_performance(model_version)
                
                # Check if significantly better (at least 5% improvement)
                if performance > best_performance + 0.05:
                    best_performance = performance
                    best_model = {
                        'model_id': model_version.model_id,
                        'version': model_version.version,
                        'performance': performance
                    }
            
            return best_model
            
        except Exception as e:
            self.logger.error(f"Error finding better model: {e}")
            return None
    
    def _estimate_model_performance(self, model_version) -> float:
        """Estimate model performance based on stored metrics"""
        try:
            # Use stored performance metrics
            if 'accuracy' in model_version.performance_metrics:
                return float(model_version.performance_metrics['accuracy'])
            
            # Fallback to other metrics
            if 'f1_score' in model_version.performance_metrics:
                return float(model_version.performance_metrics['f1_score'])
            
            return 0.5  # Default if no metrics available
            
        except Exception as e:
            self.logger.error(f"Error estimating model performance: {e}")
            return 0.0 
   
    def _validate_model_for_ai_system(self, model) -> bool:
        """Validate model compatibility with AI system"""
        try:
            # Check required methods
            required_methods = ['predict']
            for method in required_methods:
                if not hasattr(model, method):
                    self.logger.error(f"Model missing required method: {method}")
                    return False
            
            # Test with sample data
            try:
                sample_features = np.random.rand(1, 10)  # Assuming 10 features
                prediction = model.predict(sample_features)
                
                if prediction is None or len(prediction) == 0:
                    self.logger.error("Model prediction test failed")
                    return False
                    
            except Exception as test_error:
                self.logger.error(f"Model prediction test error: {test_error}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating model: {e}")
            return False
    
    def _is_cache_valid(self) -> bool:
        """Check if model cache is still valid"""
        if not self.cache_timestamp:
            return False
        
        return datetime.now() - self.cache_timestamp < self.cache_duration
    
    def _clear_model_cache(self):
        """Clear the model cache"""
        self.active_model_cache.clear()
        self.cache_timestamp = None
        self.logger.debug("Model cache cleared")
    
    def _is_in_cooldown(self) -> bool:
        """Check if we're in cooldown period after last switch"""
        if not self.last_switch_time or not self.current_config:
            return False
        
        cooldown_period = timedelta(minutes=self.current_config.switch_cooldown_minutes)
        return datetime.now() - self.last_switch_time < cooldown_period
    
    def _exceeded_daily_limit(self) -> bool:
        """Check if daily switch limit is exceeded"""
        if not self.current_config:
            return False
        
        return self.daily_switch_count >= self.current_config.max_daily_switches
    
    def _log_prediction(self, result: Dict[str, Any], features: np.ndarray):
        """Log prediction for monitoring"""
        try:
            # Store prediction for performance monitoring
            prediction_data = {
                'model_version': result['model_version'],
                'prediction': result['prediction'],
                'confidence': result['confidence'],
                'symbol': result['symbol'],
                'features': features.tolist(),
                'timestamp': result['timestamp']
            }
            
            # This could be stored in database for monitoring
            self.logger.debug(f"Prediction logged: {result['symbol']} -> {result['prediction']}")
            
        except Exception as e:
            self.logger.error(f"Error logging prediction: {e}")
    
    def _log_integration_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log integration events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO integration_events (
                    event_type, event_data, timestamp
                ) VALUES (?, ?, ?)
            ''', (
                event_type,
                json.dumps(event_data),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error logging integration event: {e}")
    
    def _load_current_config(self):
        """Load current configuration from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT config_data FROM integration_config 
                WHERE is_active = 1 
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                config_data = json.loads(row[0])
                self.current_config = AISystemConfig(**config_data)
                self.status = IntegrationStatus.ACTIVE
                self.logger.info("Loaded active configuration")
            else:
                self.logger.info("No active configuration found")
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
    
    def _save_config(self, config: AISystemConfig):
        """Save configuration to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Deactivate previous configs
            cursor.execute('UPDATE integration_config SET is_active = 0')
            
            # Save new config
            config_data = {
                'active_model_id': config.active_model_id,
                'active_version': config.active_version,
                'fallback_model_id': config.fallback_model_id,
                'fallback_version': config.fallback_version,
                'auto_switching_enabled': config.auto_switching_enabled,
                'performance_threshold': config.performance_threshold,
                'switch_cooldown_minutes': config.switch_cooldown_minutes,
                'max_daily_switches': config.max_daily_switches
            }
            
            cursor.execute('''
                INSERT INTO integration_config (
                    config_data, is_active, created_at
                ) VALUES (?, ?, ?)
            ''', (
                json.dumps(config_data),
                1,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def _store_switch_event(self, switch_event: ModelSwitchEvent):
        """Store model switch event in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO model_switch_events (
                    event_id, from_model_id, from_version, to_model_id, to_version,
                    switch_reason, switch_timestamp, performance_before, performance_after,
                    success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                switch_event.event_id,
                switch_event.from_model_id,
                switch_event.from_version,
                switch_event.to_model_id,
                switch_event.to_version,
                switch_event.switch_reason,
                switch_event.switch_timestamp.isoformat(),
                switch_event.performance_before,
                switch_event.performance_after,
                switch_event.success,
                switch_event.error_message
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing switch event: {e}")
    
    def _init_integration_tables(self):
        """Initialize database tables for integration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Integration configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS integration_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_data TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    created_at DATETIME NOT NULL
                )
            ''')
            
            # Integration events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS integration_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            ''')
            
            # Model switch events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_switch_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    from_model_id TEXT NOT NULL,
                    from_version TEXT NOT NULL,
                    to_model_id TEXT NOT NULL,
                    to_version TEXT NOT NULL,
                    switch_reason TEXT NOT NULL,
                    switch_timestamp DATETIME NOT NULL,
                    performance_before REAL,
                    performance_after REAL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT
                )
            ''')
            
            # Prediction logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prediction_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_version TEXT NOT NULL,
                    prediction INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    symbol TEXT NOT NULL,
                    features TEXT NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_integration_config_active ON integration_config(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_integration_events_type ON integration_events(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_switch_events_timestamp ON model_switch_events(switch_timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prediction_logs_timestamp ON prediction_logs(timestamp)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Integration database tables initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing integration tables: {e}")
            raise


# Utility functions for AI system integration
def create_sample_ai_system():
    """Create a sample AI system for testing"""
    class SampleAISystem:
        def __init__(self, integration: AISystemIntegration):
            self.integration = integration
            self.logger = logging.getLogger(__name__)
        
        def analyze_market(self, symbol: str, market_data: Dict[str, float]) -> Optional[Dict[str, Any]]:
            """Analyze market data and make trading decision"""
            try:
                # Extract features from market data
                features = np.array([
                    market_data.get('open', 0),
                    market_data.get('high', 0),
                    market_data.get('low', 0),
                    market_data.get('close', 0),
                    market_data.get('volume', 0),
                    market_data.get('rsi', 50),
                    market_data.get('macd', 0),
                    market_data.get('bb_upper', 0),
                    market_data.get('bb_lower', 0),
                    market_data.get('sma_20', 0)
                ])
                
                # Make prediction using integrated model
                prediction_result = self.integration.make_prediction(features, symbol)
                
                if not prediction_result:
                    return None
                
                # Convert prediction to trading signal
                signal_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
                signal = signal_map.get(prediction_result['prediction'], 'HOLD')
                
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': prediction_result['confidence'],
                    'model_version': prediction_result['model_version'],
                    'timestamp': prediction_result['timestamp']
                }
                
            except Exception as e:
                self.logger.error(f"Error analyzing market for {symbol}: {e}")
                return None
        
        def check_and_update_models(self):
            """Check model performance and update if needed"""
            return self.integration.check_model_performance_and_switch()
    
    return SampleAISystem


if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create integration
    integration = AISystemIntegration()
    
    print("AI System Integration initialized successfully!")
    
    # Get status
    status = integration.get_integration_status()
    print(f"Integration status: {status}")
    
    print("AI System Integration test completed!")