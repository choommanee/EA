"""
Learning Coordinator for AI Continuous Learning System
Orchestrates the complete learning workflow with scheduling, execution, and monitoring
"""

import sys
import os
sys.path.append('Python')

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import json
import sqlite3
import threading
import time
import schedule
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

try:
    from model_manager import ModelManager, ModelStatus, ModelType
    from ai_system_integration import AISystemIntegration
    from performance_monitor import PerformanceMonitor
    from learning_data_collector import LearningDataCollector
    from data_preprocessing_pipeline import DataPreprocessingPipeline
    from model_evaluator import ModelEvaluator
    from cross_validation_framework import CrossValidationFramework
    from learning_error_handler import LearningErrorHandler
except ImportError:
    from Python.model_manager import ModelManager, ModelStatus, ModelType
    from Python.ai_system_integration import AISystemIntegration
    from Python.performance_monitor import PerformanceMonitor
    from Python.learning_data_collector import LearningDataCollector
    from Python.data_preprocessing_pipeline import DataPreprocessingPipeline
    from Python.model_evaluator import ModelEvaluator
    from Python.cross_validation_framework import CrossValidationFramework
    from Python.learning_error_handler import LearningErrorHandler


class LearningPhase(Enum):
    """Learning workflow phases"""
    IDLE = "idle"
    DATA_COLLECTION = "data_collection"
    DATA_PREPROCESSING = "data_preprocessing"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_DEPLOYMENT = "model_deployment"
    PERFORMANCE_MONITORING = "performance_monitoring"
    ERROR_RECOVERY = "error_recovery"
    COMPLETED = "completed"
    FAILED = "failed"


class LearningTrigger(Enum):
    """Learning cycle triggers"""
    SCHEDULED = "scheduled"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_THRESHOLD = "data_threshold"
    MANUAL = "manual"
    ERROR_RECOVERY = "error_recovery"


@dataclass
class LearningCycleConfig:
    """Configuration for learning cycles"""
    cycle_id: str
    trigger_type: LearningTrigger
    schedule_interval_hours: int = 24
    performance_threshold: float = 0.7
    data_threshold_days: int = 7
    max_training_time_minutes: int = 120
    auto_deploy_threshold: float = 0.8
    enable_cross_validation: bool = True
    enable_model_comparison: bool = True
    max_retries: int = 3
    retry_delay_minutes: int = 30


@dataclass
class LearningCycleStatus:
    """Status of a learning cycle"""
    cycle_id: str
    trigger_type: LearningTrigger
    current_phase: LearningPhase
    start_time: datetime
    end_time: Optional[datetime] = None
    progress_percentage: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningProgress:
    """Learning progress tracking"""
    cycle_id: str
    phase: LearningPhase
    step_name: str
    step_progress: float
    total_progress: float
    estimated_completion: Optional[datetime] = None
    current_metrics: Dict[str, float] = field(default_factory=dict)
    message: str = ""


class LearningCoordinator:
    """Orchestrates the complete learning workflow"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db", 
                 models_directory: str = "Models"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # Initialize components
        self.model_manager = ModelManager(db_path, models_directory)
        self.ai_integration = AISystemIntegration(db_path, models_directory)
        self.performance_monitor = PerformanceMonitor(db_path)
        self.data_collector = LearningDataCollector(db_path)
        self.data_pipeline = DataPreprocessingPipeline()
        self.model_evaluator = ModelEvaluator(db_path)
        self.cv_framework = CrossValidationFramework(db_path)
        self.error_handler = LearningErrorHandler(db_path)
        
        # Coordinator state
        self.is_running = False
        self.current_cycle = None
        self.cycle_history = []
        self.scheduler_thread = None
        self.progress_callbacks = []
        
        # Configuration
        self.default_config = LearningCycleConfig(
            cycle_id="default",
            trigger_type=LearningTrigger.SCHEDULED
        )
        
        # Learning workflow steps
        self.workflow_steps = [
            ("data_collection", self._execute_data_collection),
            ("data_preprocessing", self._execute_data_preprocessing),
            ("model_training", self._execute_model_training),
            ("model_evaluation", self._execute_model_evaluation),
            ("model_deployment", self._execute_model_deployment),
            ("performance_monitoring", self._execute_performance_monitoring)
        ]
        
        # Initialize database tables
        self._init_coordinator_tables()
        
        self.logger.info("Learning Coordinator initialized")
    
    def start_coordinator(self, config: Optional[LearningCycleConfig] = None) -> bool:
        """Start the learning coordinator with scheduling"""
        try:
            if self.is_running:
                self.logger.warning("Learning coordinator is already running")
                return False
            
            self.logger.info("Starting Learning Coordinator")
            
            # Use provided config or default
            if config:
                self.default_config = config
            
            # Set up scheduling
            self._setup_scheduling()
            
            # Start scheduler thread
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            self.is_running = True
            
            # Log coordinator start
            self._log_coordinator_event("coordinator_started", {
                "config": self._config_to_dict(self.default_config),
                "start_time": datetime.now().isoformat()
            })
            
            self.logger.info("Learning Coordinator started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting Learning Coordinator: {e}")
            return False
    
    def stop_coordinator(self) -> bool:
        """Stop the learning coordinator"""
        try:
            self.logger.info("Stopping Learning Coordinator")
            
            self.is_running = False
            
            # Clear scheduled jobs
            schedule.clear()
            
            # Wait for current cycle to complete if running
            if self.current_cycle and self.current_cycle.current_phase != LearningPhase.IDLE:
                self.logger.info("Waiting for current learning cycle to complete...")
                timeout = 300  # 5 minutes timeout
                start_time = time.time()
                
                while (self.current_cycle and 
                       self.current_cycle.current_phase not in [LearningPhase.COMPLETED, LearningPhase.FAILED] and
                       time.time() - start_time < timeout):
                    time.sleep(5)
            
            # Log coordinator stop
            self._log_coordinator_event("coordinator_stopped", {
                "stop_time": datetime.now().isoformat(),
                "cycles_completed": len(self.cycle_history)
            })
            
            self.logger.info("Learning Coordinator stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping Learning Coordinator: {e}")
            return False
    
    def trigger_learning_cycle(self, trigger_type: LearningTrigger = LearningTrigger.MANUAL,
                             config: Optional[LearningCycleConfig] = None) -> str:
        """Manually trigger a learning cycle"""
        try:
            if self.current_cycle and self.current_cycle.current_phase != LearningPhase.IDLE:
                raise ValueError("Another learning cycle is already in progress")
            
            # Generate cycle ID
            cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{trigger_type.value}"
            
            # Use provided config or default
            cycle_config = config or self.default_config
            cycle_config.cycle_id = cycle_id
            cycle_config.trigger_type = trigger_type
            
            self.logger.info(f"Triggering learning cycle: {cycle_id} ({trigger_type.value})")
            
            # Execute learning cycle in background thread
            cycle_thread = threading.Thread(
                target=self._execute_learning_cycle,
                args=(cycle_config,),
                daemon=True
            )
            cycle_thread.start()
            
            return cycle_id
            
        except Exception as e:
            self.logger.error(f"Error triggering learning cycle: {e}")
            raise
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current coordinator and cycle status"""
        try:
            status = {
                "coordinator_running": self.is_running,
                "current_cycle": None,
                "total_cycles": len(self.cycle_history),
                "last_cycle": None,
                "next_scheduled": None
            }
            
            # Current cycle info
            if self.current_cycle:
                status["current_cycle"] = {
                    "cycle_id": self.current_cycle.cycle_id,
                    "trigger_type": self.current_cycle.trigger_type.value,
                    "current_phase": self.current_cycle.current_phase.value,
                    "progress_percentage": self.current_cycle.progress_percentage,
                    "current_step": self.current_cycle.current_step,
                    "completed_steps": self.current_cycle.completed_steps,
                    "total_steps": self.current_cycle.total_steps,
                    "start_time": self.current_cycle.start_time.isoformat(),
                    "error_count": self.current_cycle.error_count,
                    "metrics": self.current_cycle.metrics
                }
            
            # Last cycle info
            if self.cycle_history:
                last_cycle = self.cycle_history[-1]
                status["last_cycle"] = {
                    "cycle_id": last_cycle.cycle_id,
                    "trigger_type": last_cycle.trigger_type.value,
                    "final_phase": last_cycle.current_phase.value,
                    "start_time": last_cycle.start_time.isoformat(),
                    "end_time": last_cycle.end_time.isoformat() if last_cycle.end_time else None,
                    "success": last_cycle.current_phase == LearningPhase.COMPLETED
                }
            
            # Next scheduled cycle
            jobs = schedule.jobs
            if jobs:
                next_job = min(jobs, key=lambda x: x.next_run)
                status["next_scheduled"] = next_job.next_run.isoformat()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting coordinator status: {e}")
            return {"error": str(e)}
    
    def get_learning_progress(self) -> Optional[LearningProgress]:
        """Get current learning progress"""
        try:
            if not self.current_cycle:
                return None
            
            # Calculate estimated completion
            estimated_completion = None
            if self.current_cycle.progress_percentage > 0:
                elapsed_time = datetime.now() - self.current_cycle.start_time
                total_estimated = elapsed_time / (self.current_cycle.progress_percentage / 100)
                estimated_completion = self.current_cycle.start_time + total_estimated
            
            return LearningProgress(
                cycle_id=self.current_cycle.cycle_id,
                phase=self.current_cycle.current_phase,
                step_name=self.current_cycle.current_step,
                step_progress=self.current_cycle.completed_steps / max(self.current_cycle.total_steps, 1) * 100,
                total_progress=self.current_cycle.progress_percentage,
                estimated_completion=estimated_completion,
                current_metrics=self.current_cycle.metrics,
                message=f"Phase: {self.current_cycle.current_phase.value}, Step: {self.current_cycle.current_step}"
            )
            
        except Exception as e:
            self.logger.error(f"Error getting learning progress: {e}")
            return None
    
    def add_progress_callback(self, callback: Callable[[LearningProgress], None]):
        """Add a callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[LearningProgress], None]):
        """Remove a progress callback"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def get_cycle_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get learning cycle history"""
        try:
            history = []
            
            for cycle in self.cycle_history[-limit:]:
                cycle_info = {
                    "cycle_id": cycle.cycle_id,
                    "trigger_type": cycle.trigger_type.value,
                    "final_phase": cycle.current_phase.value,
                    "start_time": cycle.start_time.isoformat(),
                    "end_time": cycle.end_time.isoformat() if cycle.end_time else None,
                    "duration_minutes": None,
                    "success": cycle.current_phase == LearningPhase.COMPLETED,
                    "error_count": cycle.error_count,
                    "final_metrics": cycle.metrics,
                    "artifacts": cycle.artifacts
                }
                
                # Calculate duration
                if cycle.end_time:
                    duration = cycle.end_time - cycle.start_time
                    cycle_info["duration_minutes"] = duration.total_seconds() / 60
                
                history.append(cycle_info)
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting cycle history: {e}")
            return []
    
    def _execute_learning_cycle(self, config: LearningCycleConfig):
        """Execute a complete learning cycle"""
        cycle_status = LearningCycleStatus(
            cycle_id=config.cycle_id,
            trigger_type=config.trigger_type,
            current_phase=LearningPhase.IDLE,
            start_time=datetime.now(),
            total_steps=len(self.workflow_steps)
        )
        
        self.current_cycle = cycle_status
        
        try:
            self.logger.info(f"Starting learning cycle: {config.cycle_id}")
            
            # Update phase to data collection
            self._update_cycle_phase(LearningPhase.DATA_COLLECTION, "Starting learning cycle")
            
            # Execute workflow steps
            for step_index, (step_name, step_function) in enumerate(self.workflow_steps):
                try:
                    self.logger.info(f"Executing step: {step_name}")
                    
                    # Update current step
                    cycle_status.current_step = step_name
                    cycle_status.completed_steps = step_index
                    cycle_status.progress_percentage = (step_index / len(self.workflow_steps)) * 100
                    
                    # Notify progress callbacks
                    self._notify_progress_callbacks()
                    
                    # Execute step with retry logic
                    step_result = self._execute_step_with_retry(step_function, config)
                    
                    # Store step result
                    cycle_status.artifacts[step_name] = step_result
                    
                    self.logger.info(f"Completed step: {step_name}")
                    
                except Exception as step_error:
                    self.logger.error(f"Error in step {step_name}: {step_error}")
                    cycle_status.error_count += 1
                    cycle_status.last_error = str(step_error)
                    
                    # Handle error based on severity
                    if not self._handle_step_error(step_error, step_name, config):
                        raise step_error
            
            # Mark cycle as completed
            self._update_cycle_phase(LearningPhase.COMPLETED, "Learning cycle completed successfully")
            cycle_status.progress_percentage = 100.0
            cycle_status.completed_steps = len(self.workflow_steps)
            
            self.logger.info(f"Learning cycle completed successfully: {config.cycle_id}")
            
        except Exception as e:
            self.logger.error(f"Learning cycle failed: {config.cycle_id} - {e}")
            
            # Mark cycle as failed
            self._update_cycle_phase(LearningPhase.FAILED, f"Learning cycle failed: {str(e)}")
            cycle_status.last_error = str(e)
            
            # Attempt error recovery
            self._attempt_error_recovery(e, config)
            
        finally:
            # Finalize cycle
            cycle_status.end_time = datetime.now()
            self.cycle_history.append(cycle_status)
            
            # Store cycle in database
            self._store_cycle_status(cycle_status)
            
            # Final progress notification
            self._notify_progress_callbacks()
            
            # Reset current cycle
            self.current_cycle = None
    
    def _execute_step_with_retry(self, step_function: Callable, config: LearningCycleConfig) -> Any:
        """Execute a step with retry logic"""
        last_error = None
        
        for attempt in range(config.max_retries + 1):
            try:
                return step_function(config)
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Step attempt {attempt + 1} failed: {e}")
                
                if attempt < config.max_retries:
                    self.logger.info(f"Retrying in {config.retry_delay_minutes} minutes...")
                    time.sleep(config.retry_delay_minutes * 60)
                else:
                    self.logger.error(f"Step failed after {config.max_retries + 1} attempts")
                    raise last_error
        
        raise last_error
    
    def _execute_data_collection(self, config: LearningCycleConfig) -> Dict[str, Any]:
        """Execute data collection step"""
        self._update_cycle_phase(LearningPhase.DATA_COLLECTION, "Collecting learning data")
        
        # Collect recent data for training
        end_time = datetime.now()
        start_time = end_time - timedelta(days=config.data_threshold_days)
        
        # Collect data using data collector
        collected_data = self.data_collector.collect_learning_data(
            start_time=start_time,
            end_time=end_time,
            min_samples=100
        )
        
        if collected_data.empty:
            raise ValueError("No data collected for learning")
        
        self.logger.info(f"Collected {len(collected_data)} samples for learning")
        
        return {
            "samples_collected": len(collected_data),
            "date_range": f"{start_time.date()} to {end_time.date()}",
            "data_quality": self.data_collector.validate_data_quality(collected_data)
        }
    
    def _execute_data_preprocessing(self, config: LearningCycleConfig) -> Dict[str, Any]:
        """Execute data preprocessing step"""
        self._update_cycle_phase(LearningPhase.DATA_PREPROCESSING, "Preprocessing learning data")
        
        # Get collected data (in real implementation, this would be passed between steps)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=config.data_threshold_days)
        
        raw_data = self.data_collector.collect_learning_data(start_time, end_time)
        
        # Preprocess data
        processed_data = self.data_pipeline.process_learning_data(raw_data)
        
        # Validate processed data
        validation_results = self.data_pipeline.validate_processed_data(processed_data)
        
        self.logger.info(f"Preprocessed {len(processed_data)} samples")
        
        return {
            "processed_samples": len(processed_data),
            "validation_results": validation_results,
            "feature_count": processed_data.shape[1] - 1 if not processed_data.empty else 0
        }
    
    def _execute_model_training(self, config: LearningCycleConfig) -> Dict[str, Any]:
        """Execute model training step"""
        self._update_cycle_phase(LearningPhase.MODEL_TRAINING, "Training new model")
        
        # Get preprocessed data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=config.data_threshold_days)
        
        raw_data = self.data_collector.collect_learning_data(start_time, end_time)
        processed_data = self.data_pipeline.process_learning_data(raw_data)
        
        if processed_data.empty:
            raise ValueError("No processed data available for training")
        
        # Prepare training data
        X = processed_data.drop('target', axis=1).values
        y = processed_data['target'].values
        
        # Train model (using a simple RandomForest for this example)
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Calculate training metrics
        from sklearn.metrics import accuracy_score, classification_report
        y_pred = model.predict(X)
        training_accuracy = accuracy_score(y, y_pred)
        
        # Save model
        model_version = self.model_manager.save_model(
            model, f"learning_cycle_{config.cycle_id}", ModelType.CLASSIFICATION,
            {"accuracy": training_accuracy, "training_samples": len(X)},
            {"cycle_id": config.cycle_id, "trigger": config.trigger_type.value},
            f"Model trained in learning cycle {config.cycle_id}"
        )
        
        self.logger.info(f"Model trained with accuracy: {training_accuracy:.3f}")
        
        return {
            "model_id": model_version.model_id,
            "model_version": model_version.version,
            "training_accuracy": training_accuracy,
            "training_samples": len(X),
            "features": X.shape[1]
        }
    
    def _execute_model_evaluation(self, config: LearningCycleConfig) -> Dict[str, Any]:
        """Execute model evaluation step"""
        self._update_cycle_phase(LearningPhase.MODEL_EVALUATION, "Evaluating trained model")
        
        # Get the latest trained model from artifacts
        training_result = self.current_cycle.artifacts.get("model_training", {})
        model_id = training_result.get("model_id")
        model_version = training_result.get("model_version")
        
        if not model_id or not model_version:
            raise ValueError("No trained model found for evaluation")
        
        # Load the model
        model, model_info = self.model_manager.load_model(model_id, model_version)
        
        # Get test data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=config.data_threshold_days)
        
        raw_data = self.data_collector.collect_learning_data(start_time, end_time)
        processed_data = self.data_pipeline.process_learning_data(raw_data)
        
        # Split data for evaluation (use last 20% as test set)
        test_size = int(len(processed_data) * 0.2)
        test_data = processed_data.tail(test_size)
        
        X_test = test_data.drop('target', axis=1).values
        y_test = test_data['target'].values
        
        # Evaluate model
        evaluation_result = self.model_evaluator.evaluate_model(
            model, X_test, y_test, f"cycle_{config.cycle_id}_evaluation",
            ModelType.CLASSIFICATION
        )
        
        # Cross-validation if enabled
        cv_result = None
        if config.enable_cross_validation:
            train_data = processed_data.head(len(processed_data) - test_size)
            X_train = train_data.drop('target', axis=1).values
            y_train = train_data['target'].values
            
            cv_result = self.cv_framework.perform_cross_validation(
                model, X_train, y_train, f"cycle_{config.cycle_id}_cv"
            )
        
        self.logger.info(f"Model evaluation completed. Accuracy: {evaluation_result.metrics.get('accuracy', 0):.3f}")
        
        return {
            "model_id": model_id,
            "model_version": model_version,
            "evaluation_metrics": evaluation_result.metrics,
            "cv_metrics": cv_result.mean_scores if cv_result else None,
            "test_samples": len(X_test),
            "recommendations": evaluation_result.recommendations
        }
    
    def _execute_model_deployment(self, config: LearningCycleConfig) -> Dict[str, Any]:
        """Execute model deployment step"""
        self._update_cycle_phase(LearningPhase.MODEL_DEPLOYMENT, "Deploying evaluated model")
        
        # Get evaluation results
        evaluation_result = self.current_cycle.artifacts.get("model_evaluation", {})
        model_id = evaluation_result.get("model_id")
        model_version = evaluation_result.get("model_version")
        evaluation_metrics = evaluation_result.get("evaluation_metrics", {})
        
        if not model_id or not model_version:
            raise ValueError("No evaluated model found for deployment")
        
        # Check if model meets deployment threshold
        model_accuracy = evaluation_metrics.get("accuracy", 0)
        
        if model_accuracy < config.auto_deploy_threshold:
            self.logger.warning(f"Model accuracy {model_accuracy:.3f} below deployment threshold {config.auto_deploy_threshold}")
            return {
                "deployed": False,
                "reason": f"Accuracy {model_accuracy:.3f} below threshold {config.auto_deploy_threshold}",
                "model_id": model_id,
                "model_version": model_version
            }
        
        # Update model status for deployment
        self.model_manager._update_model_status(model_id, model_version, ModelStatus.TESTING)
        
        # Deploy model through AI integration
        deployment_success = False
        try:
            # Check if integration is active
            integration_status = self.ai_integration.get_integration_status()
            
            if integration_status['status'] == 'active':
                # Switch to new model
                deployment_success = self.ai_integration.switch_to_model(
                    model_id, model_version, f"Learning cycle {config.cycle_id} deployment"
                )
            else:
                # Activate integration with new model
                deployment_success = self.ai_integration.activate_integration(
                    model_id, model_version
                )
            
        except Exception as deploy_error:
            self.logger.error(f"Deployment error: {deploy_error}")
            deployment_success = False
        
        if deployment_success:
            self.logger.info(f"Model deployed successfully: {model_id} v{model_version}")
        else:
            self.logger.warning(f"Model deployment failed: {model_id} v{model_version}")
        
        return {
            "deployed": deployment_success,
            "model_id": model_id,
            "model_version": model_version,
            "deployment_accuracy": model_accuracy,
            "deployment_threshold": config.auto_deploy_threshold
        }
    
    def _execute_performance_monitoring(self, config: LearningCycleConfig) -> Dict[str, Any]:
        """Execute performance monitoring step"""
        self._update_cycle_phase(LearningPhase.PERFORMANCE_MONITORING, "Setting up performance monitoring")
        
        # Get deployment results
        deployment_result = self.current_cycle.artifacts.get("model_deployment", {})
        
        if not deployment_result.get("deployed", False):
            return {
                "monitoring_setup": False,
                "reason": "Model was not deployed"
            }
        
        # Set up monitoring for the deployed model
        model_id = deployment_result.get("model_id")
        model_version = deployment_result.get("model_version")
        
        # Initialize performance tracking
        monitoring_config = {
            "model_id": model_id,
            "model_version": model_version,
            "cycle_id": config.cycle_id,
            "monitoring_start": datetime.now().isoformat(),
            "performance_threshold": config.performance_threshold
        }
        
        # Store monitoring configuration
        self._store_monitoring_config(monitoring_config)
        
        self.logger.info(f"Performance monitoring setup for model: {model_id} v{model_version}")
        
        return {
            "monitoring_setup": True,
            "model_id": model_id,
            "model_version": model_version,
            "monitoring_config": monitoring_config
        }
    
    def _update_cycle_phase(self, phase: LearningPhase, message: str):
        """Update current cycle phase"""
        if self.current_cycle:
            self.current_cycle.current_phase = phase
            self.current_cycle.current_step = message
            self.logger.info(f"Learning cycle phase: {phase.value} - {message}")
    
    def _notify_progress_callbacks(self):
        """Notify all progress callbacks"""
        try:
            progress = self.get_learning_progress()
            if progress:
                for callback in self.progress_callbacks:
                    try:
                        callback(progress)
                    except Exception as e:
                        self.logger.error(f"Error in progress callback: {e}")
        except Exception as e:
            self.logger.error(f"Error notifying progress callbacks: {e}")
    
    def _handle_step_error(self, error: Exception, step_name: str, config: LearningCycleConfig) -> bool:
        """Handle step error and determine if cycle should continue"""
        try:
            # Use error handler to categorize and handle error
            error_info = self.error_handler.handle_error(error, {
                "step_name": step_name,
                "cycle_id": config.cycle_id,
                "phase": self.current_cycle.current_phase.value if self.current_cycle else "unknown"
            })
            
            # Determine if error is recoverable
            if error_info.get("severity") in ["low", "medium"]:
                self.logger.warning(f"Recoverable error in {step_name}: {error}")
                return True  # Continue cycle
            else:
                self.logger.error(f"Critical error in {step_name}: {error}")
                return False  # Stop cycle
                
        except Exception as handler_error:
            self.logger.error(f"Error in error handler: {handler_error}")
            return False  # Stop cycle on handler error
    
    def _attempt_error_recovery(self, error: Exception, config: LearningCycleConfig):
        """Attempt to recover from cycle error"""
        try:
            self._update_cycle_phase(LearningPhase.ERROR_RECOVERY, "Attempting error recovery")
            
            # Use error handler for recovery
            recovery_result = self.error_handler.attempt_recovery(error, {
                "cycle_id": config.cycle_id,
                "trigger_type": config.trigger_type.value
            })
            
            if recovery_result.get("recovered", False):
                self.logger.info("Error recovery successful")
            else:
                self.logger.warning("Error recovery failed")
                
        except Exception as recovery_error:
            self.logger.error(f"Error during recovery attempt: {recovery_error}")
    
    def _setup_scheduling(self):
        """Set up learning cycle scheduling"""
        try:
            # Clear existing schedules
            schedule.clear()
            
            # Schedule regular learning cycles
            if self.default_config.schedule_interval_hours > 0:
                schedule.every(self.default_config.schedule_interval_hours).hours.do(
                    self._scheduled_learning_cycle
                )
                
                self.logger.info(f"Scheduled learning cycles every {self.default_config.schedule_interval_hours} hours")
            
            # Schedule performance checks (more frequent)
            schedule.every(1).hours.do(self._check_performance_triggers)
            
            self.logger.info("Learning cycle scheduling configured")
            
        except Exception as e:
            self.logger.error(f"Error setting up scheduling: {e}")
    
    def _run_scheduler(self):
        """Run the scheduler in background thread"""
        self.logger.info("Learning cycle scheduler started")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler: {e}")
                time.sleep(60)
        
        self.logger.info("Learning cycle scheduler stopped")
    
    def _scheduled_learning_cycle(self):
        """Execute scheduled learning cycle"""
        try:
            if self.current_cycle and self.current_cycle.current_phase != LearningPhase.IDLE:
                self.logger.info("Skipping scheduled cycle - another cycle is running")
                return
            
            self.logger.info("Triggering scheduled learning cycle")
            self.trigger_learning_cycle(LearningTrigger.SCHEDULED)
            
        except Exception as e:
            self.logger.error(f"Error in scheduled learning cycle: {e}")
    
    def _check_performance_triggers(self):
        """Check for performance-based learning triggers"""
        try:
            # Get current AI system performance
            integration_status = self.ai_integration.get_integration_status()
            
            if integration_status['status'] != 'active':
                return
            
            current_performance = integration_status.get('performance', 1.0)
            
            # Check if performance is below threshold
            if current_performance < self.default_config.performance_threshold:
                self.logger.info(f"Performance trigger detected: {current_performance:.3f} < {self.default_config.performance_threshold}")
                
                # Trigger learning cycle if not already running
                if not self.current_cycle or self.current_cycle.current_phase == LearningPhase.IDLE:
                    self.trigger_learning_cycle(LearningTrigger.PERFORMANCE_DEGRADATION)
                    
        except Exception as e:
            self.logger.error(f"Error checking performance triggers: {e}")
    
    def _config_to_dict(self, config: LearningCycleConfig) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "cycle_id": config.cycle_id,
            "trigger_type": config.trigger_type.value,
            "schedule_interval_hours": config.schedule_interval_hours,
            "performance_threshold": config.performance_threshold,
            "data_threshold_days": config.data_threshold_days,
            "max_training_time_minutes": config.max_training_time_minutes,
            "auto_deploy_threshold": config.auto_deploy_threshold,
            "enable_cross_validation": config.enable_cross_validation,
            "enable_model_comparison": config.enable_model_comparison,
            "max_retries": config.max_retries,
            "retry_delay_minutes": config.retry_delay_minutes
        }
    
    def _log_coordinator_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log coordinator events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO coordinator_events (
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
            self.logger.error(f"Error logging coordinator event: {e}")
    
    def _store_cycle_status(self, cycle_status: LearningCycleStatus):
        """Store cycle status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO learning_cycles (
                    cycle_id, trigger_type, current_phase, start_time, end_time,
                    progress_percentage, completed_steps, total_steps, error_count,
                    last_error, metrics, artifacts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cycle_status.cycle_id,
                cycle_status.trigger_type.value,
                cycle_status.current_phase.value,
                cycle_status.start_time.isoformat(),
                cycle_status.end_time.isoformat() if cycle_status.end_time else None,
                cycle_status.progress_percentage,
                cycle_status.completed_steps,
                cycle_status.total_steps,
                cycle_status.error_count,
                cycle_status.last_error,
                json.dumps(cycle_status.metrics),
                json.dumps(cycle_status.artifacts)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing cycle status: {e}")
    
    def _store_monitoring_config(self, config: Dict[str, Any]):
        """Store monitoring configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO monitoring_configs (
                    model_id, model_version, cycle_id, config_data, created_at
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                config["model_id"],
                config["model_version"],
                config["cycle_id"],
                json.dumps(config),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing monitoring config: {e}")
    
    def _init_coordinator_tables(self):
        """Initialize database tables for coordinator"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Coordinator events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS coordinator_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            ''')
            
            # Learning cycles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle_id TEXT UNIQUE NOT NULL,
                    trigger_type TEXT NOT NULL,
                    current_phase TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    progress_percentage REAL DEFAULT 0,
                    completed_steps INTEGER DEFAULT 0,
                    total_steps INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    metrics TEXT,
                    artifacts TEXT
                )
            ''')
            
            # Monitoring configurations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitoring_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    cycle_id TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    created_at DATETIME NOT NULL
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_coordinator_events_type ON coordinator_events(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_cycles_id ON learning_cycles(cycle_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_monitoring_configs_model ON monitoring_configs(model_id, model_version)')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Learning coordinator database tables initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing coordinator tables: {e}")
            raise


# Utility functions for learning coordination
def create_sample_progress_callback():
    """Create a sample progress callback for testing"""
    def progress_callback(progress: LearningProgress):
        print(f"Learning Progress: {progress.phase.value} - {progress.total_progress:.1f}% - {progress.message}")
    
    return progress_callback


if __name__ == "__main__":
    # Example usage and testing
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create coordinator
    coordinator = LearningCoordinator()
    
    # Add progress callback
    progress_callback = create_sample_progress_callback()
    coordinator.add_progress_callback(progress_callback)
    
    print("Learning Coordinator initialized successfully!")
    
    # Get status
    status = coordinator.get_current_status()
    print(f"Coordinator status: {status}")
    
    # Test manual trigger (commented out for safety)
    # cycle_id = coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
    # print(f"Triggered learning cycle: {cycle_id}")
    
    print("Learning Coordinator test completed!")