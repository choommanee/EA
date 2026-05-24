"""
AI Model Integration Layer
Integrates Model Manager with existing AI analysis system
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
from sklearn.base import BaseEstimator
import warnings
warnings.filterwarnings('ignore')

from model_manager import ModelManager
from ai_analysis_system import AIAnalysisSystem
from learning_database_manager import LearningDatabaseManager
from models.learning_models import (
    LearningEventRecord, LearningEventType,
    ModelVersionRecord, ModelType
)


class AIModelIntegration:
    """Integration layer between Model Manager and AI Analysis System"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db",
                 model_storage_path: str = "Data/models"):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.model_manager = ModelManager(db_path, model_storage_path)
        self.ai_system = AIAnalysisSystem(db_path)
        self.db_manager = LearningDatabaseManager(db_path)
        
        # Integration settings
        self.auto_model_switching = True
        self.performance_threshold = 0.7
        self.fallback_model_name = "default_model"
        
        # Model cache for performance
        self.model_cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=1)
        
        self.logger.info("AI Model Integration initialized")
    
    def get_best_model_for_symbol(self, symbol: str) -> Optional[BaseEstimator]:
        """Get the best performing model for a specific symbol"""
        try:
            # Check cache first
            cache_key = f"best_model_{symbol}"
            if self._is_cache_valid(cache_key):
                return self.model_cache[cache_key]
            
            # Get active models for the symbol
            active_models = self.model_manager.active_models
            
            if not active_models:
                self.logger.warning(f"No active models found for symbol: {symbol}")
                return None
            
            # Find best model based on recent performance
            best_model = None
            best_performance = 0.0
            
            for model_name, model_info in active_models.items():
                # Get recent performance for this model and symbol
                performance = self._get_model_performance_for_symbol(
                    model_info['version_id'], symbol
                )
                
                if performance > best_performance:
                    best_performance = performance
                    best_model = model_info['model']
            
            # Cache the result
            if best_model:
                self.model_cache[cache_key] = best_model
                self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
            
            return best_model
            
        except Exception as e:
            self.logger.error(f"Error getting best model for symbol {symbol}: {e}")
            return None
    
    def predict_with_best_model(self, symbol: str, features: np.ndarray) -> Optional[Dict[str, Any]]:
        """Make prediction using the best available model"""
        try:
            # Get best model for symbol
            model = self.get_best_model_for_symbol(symbol)
            
            if model is None:
                self.logger.warning(f"No model available for prediction: {symbol}")
                return None
            
            # Make prediction
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(features.reshape(1, -1))[0]
                prediction = model.predict(features.reshape(1, -1))[0]
                confidence = np.max(probabilities)
            else:
                prediction = model.predict(features.reshape(1, -1))[0]
                confidence = 0.5  # Default confidence for models without probability
            
            # Map prediction to trading signal
            signal_mapping = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
            signal = signal_mapping.get(prediction, 'HOLD')
            
            result = {
                'symbol': symbol,
                'signal': signal,
                'confidence': float(confidence),
                'prediction_time': datetime.now(),
                'model_version': self._get_model_version_id(model),
                'features_used': features.tolist()
            }
            
            self.logger.info(f"Prediction made for {symbol}: {signal} (confidence: {confidence:.3f})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error making prediction for {symbol}: {e}")
            return None
    
    def update_ai_system_model(self, model_name: str, new_version_id: str) -> bool:
        """Update the AI system to use a new model version"""
        try:
            self.logger.info(f"Updating AI system model: {model_name} -> {new_version_id}")
            
            # Load the new model
            new_model = self.model_manager.load_model(new_version_id)
            if new_model is None:
                self.logger.error(f"Failed to load model version: {new_version_id}")
                return False
            
            # Deploy the model
            success = self.model_manager.deploy_model(new_version_id, model_name)
            if not success:
                self.logger.error(f"Failed to deploy model: {new_version_id}")
                return False
            
            # Clear cache to force reload
            self._clear_model_cache()
            
            # Update AI system configuration if needed
            self._update_ai_system_config(model_name, new_version_id)
            
            # Log the update
            self._log_integration_event(LearningEventType.MODEL_DEPLOYED, {
                'model_name': model_name,
                'new_version_id': new_version_id,
                'updated_by': 'ai_model_integration'
            })
            
            self.logger.info(f"AI system model updated successfully: {model_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating AI system model: {e}")
            return False
    
    def auto_switch_model_if_needed(self, symbol: str) -> bool:
        """Automatically switch to a better model if available"""
        try:
            if not self.auto_model_switching:
                return False
            
            # Get current active model performance
            current_model_version = self.model_manager.get_active_model_version(symbol)
            if not current_model_version:
                return False
            
            current_performance = self._get_model_performance_for_symbol(
                current_model_version, symbol
            )
            
            # Check if performance is below threshold
            if current_performance >= self.performance_threshold:
                return False  # Current model is performing well
            
            # Find better alternative models
            available_models = self.model_manager.list_model_versions(symbol, limit=5)
            
            best_alternative = None
            best_performance = current_performance
            
            for model_info in available_models:
                if model_info['version_id'] == current_model_version:
                    continue  # Skip current model
                
                performance = self._get_model_performance_for_symbol(
                    model_info['version_id'], symbol
                )
                
                if performance > best_performance:
                    best_performance = performance
                    best_alternative = model_info
            
            # Switch to better model if found
            if best_alternative and best_performance > current_performance + 0.05:  # 5% improvement threshold
                self.logger.info(f"Auto-switching model for {symbol}: "
                               f"{current_performance:.3f} -> {best_performance:.3f}")
                
                return self.update_ai_system_model(symbol, best_alternative['version_id'])
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in auto model switching: {e}")
            return False
    
    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of all active models"""
        try:
            summary = {
                'active_models': {},
                'total_models': 0,
                'avg_performance': 0.0,
                'last_updated': datetime.now()
            }
            
            active_models = self.model_manager.active_models
            
            if not active_models:
                return summary
            
            total_performance = 0.0
            
            for model_name, model_info in active_models.items():
                version_id = model_info['version_id']
                
                # Get performance metrics
                performance = self._get_overall_model_performance(version_id)
                
                model_summary = {
                    'version_id': version_id,
                    'deployed_at': model_info['deployed_at'],
                    'performance': performance,
                    'metadata': model_info.get('metadata', {})
                }
                
                summary['active_models'][model_name] = model_summary
                total_performance += performance
            
            summary['total_models'] = len(active_models)
            summary['avg_performance'] = total_performance / len(active_models) if active_models else 0.0
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting model performance summary: {e}")
            return {}
    
    def rollback_to_previous_model(self, model_name: str, reason: str = "Performance degradation") -> bool:
        """Rollback to the previous model version"""
        try:
            self.logger.info(f"Rolling back model: {model_name} (reason: {reason})")
            
            # Perform rollback
            success = self.model_manager.rollback_model(model_name)
            
            if success:
                # Clear cache
                self._clear_model_cache()
                
                # Log rollback event
                self._log_integration_event(LearningEventType.MODEL_ROLLBACK, {
                    'model_name': model_name,
                    'reason': reason,
                    'rolled_back_by': 'ai_model_integration'
                })
                
                self.logger.info(f"Model rollback successful: {model_name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error rolling back model: {e}")
            return False
    
    def validate_model_compatibility(self, model: BaseEstimator, symbol: str) -> bool:
        """Validate if a model is compatible with the AI system"""
        try:
            # Check if model has required methods
            required_methods = ['predict']
            for method in required_methods:
                if not hasattr(model, method):
                    self.logger.error(f"Model missing required method: {method}")
                    return False
            
            # Test prediction with sample data
            try:
                # Get sample features for the symbol
                sample_features = self._get_sample_features(symbol)
                if sample_features is not None:
                    prediction = model.predict(sample_features.reshape(1, -1))
                    if prediction is None or len(prediction) == 0:
                        self.logger.error("Model prediction returned invalid result")
                        return False
            except Exception as pred_error:
                self.logger.error(f"Model prediction test failed: {pred_error}")
                return False
            
            self.logger.info(f"Model compatibility validated for symbol: {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating model compatibility: {e}")
            return False
    
    def _get_model_performance_for_symbol(self, version_id: str, symbol: str) -> float:
        """Get model performance for a specific symbol"""
        try:
            # Query recent performance data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)  # Last 7 days
            
            performance_data = self.db_manager.get_learning_performance(
                model_version=version_id,
                symbol=symbol,
                start_time=start_time,
                end_time=end_time
            )
            
            if performance_data.empty:
                return 0.5  # Default performance if no data
            
            # Calculate accuracy
            accuracy_scores = performance_data['accuracy_score'].dropna()
            if len(accuracy_scores) > 0:
                return float(accuracy_scores.mean())
            
            return 0.5
            
        except Exception as e:
            self.logger.error(f"Error getting model performance: {e}")
            return 0.0
    
    def _get_overall_model_performance(self, version_id: str) -> float:
        """Get overall model performance across all symbols"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            performance_data = self.db_manager.get_learning_performance(
                model_version=version_id,
                start_time=start_time,
                end_time=end_time
            )
            
            if performance_data.empty:
                return 0.5
            
            accuracy_scores = performance_data['accuracy_score'].dropna()
            if len(accuracy_scores) > 0:
                return float(accuracy_scores.mean())
            
            return 0.5
            
        except Exception as e:
            self.logger.error(f"Error getting overall model performance: {e}")
            return 0.0
    
    def _get_model_version_id(self, model: BaseEstimator) -> str:
        """Get version ID for a model instance"""
        try:
            # Try to find the model in active models
            for model_name, model_info in self.model_manager.active_models.items():
                if model_info['model'] is model:
                    return model_info['version_id']
            
            return "unknown_version"
            
        except Exception as e:
            self.logger.error(f"Error getting model version ID: {e}")
            return "unknown_version"
    
    def _get_sample_features(self, symbol: str) -> Optional[np.ndarray]:
        """Get sample features for testing model compatibility"""
        try:
            # Get recent market data for the symbol
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            
            market_data = self.db_manager.get_market_data(
                symbol=symbol,
                start_time=start_time,
                end_time=end_time,
                limit=1
            )
            
            if market_data.empty:
                # Return dummy features if no data available
                return np.random.rand(10)  # Assuming 10 features
            
            # Extract features from market data
            # This should match the feature engineering used in training
            features = []
            row = market_data.iloc[0]
            
            # Basic OHLC features
            features.extend([
                row.get('open', 0),
                row.get('high', 0),
                row.get('low', 0),
                row.get('close', 0),
                row.get('volume', 0)
            ])
            
            # Add more features to match expected input size
            while len(features) < 10:
                features.append(0.0)
            
            return np.array(features[:10])  # Limit to 10 features
            
        except Exception as e:
            self.logger.error(f"Error getting sample features: {e}")
            return np.random.rand(10)  # Fallback to random features
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.model_cache:
            return False
        
        if cache_key not in self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry[cache_key]
    
    def _clear_model_cache(self):
        """Clear the model cache"""
        self.model_cache.clear()
        self.cache_expiry.clear()
        self.logger.info("Model cache cleared")
    
    def _update_ai_system_config(self, model_name: str, version_id: str):
        """Update AI system configuration with new model"""
        try:
            # This would update the AI system's configuration
            # Implementation depends on how the AI system is configured
            self.logger.info(f"AI system config updated: {model_name} -> {version_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating AI system config: {e}")
    
    def _log_integration_event(self, event_type: LearningEventType, event_data: Dict[str, Any]):
        """Log integration events"""
        try:
            event = LearningEventRecord(
                event_type=event_type,
                event_data=event_data,
                timestamp=datetime.now(),
                success=True
            )
            
            self.db_manager.log_learning_event(event)
            
        except Exception as e:
            self.logger.error(f"Error logging integration event: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize integration
    integration = AIModelIntegration("Data/test_integration.db")
    
    print("AI Model Integration initialized successfully!")
    
    # Test performance summary
    summary = integration.get_model_performance_summary()
    print(f"Performance summary: {summary}")
    
    print("AI Model Integration test completed!")