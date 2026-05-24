"""
Model Evaluator for AI Continuous Learning System
Comprehensive model evaluation, comparison, and validation framework
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
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    mean_squared_error, mean_absolute_error, r2_score
)
from sklearn.model_selection import cross_val_score, learning_curve
import warnings
warnings.filterwarnings('ignore')


class EvaluationMetric(Enum):
    """Available evaluation metrics"""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ROC_AUC = "roc_auc"
    CONFUSION_MATRIX = "confusion_matrix"
    MSE = "mse"
    MAE = "mae"
    R2_SCORE = "r2_score"
    PROFIT_LOSS = "profit_loss"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    RISK_RETURN_RATIO = "risk_return_ratio"


class ModelType(Enum):
    """Model types for evaluation"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    ENSEMBLE = "ensemble"
    NEURAL_NETWORK = "neural_network"
    TREE_BASED = "tree_based"


@dataclass
class EvaluationResult:
    """Result of model evaluation"""
    model_id: str
    model_name: str
    model_type: ModelType
    evaluation_timestamp: datetime
    metrics: Dict[str, float]
    detailed_metrics: Dict[str, Any]
    validation_scores: Dict[str, List[float]]
    overfitting_analysis: Dict[str, Any]
    comparison_results: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ModelComparison:
    """Result of model comparison"""
    comparison_id: str
    models_compared: List[str]
    comparison_timestamp: datetime
    primary_metric: str
    comparison_results: Dict[str, Dict[str, float]]
    statistical_significance: Dict[str, Dict[str, float]]
    ranking: List[Tuple[str, float]]
    recommendations: List[str]
    best_model: str
    confidence_level: float


class ModelEvaluator:
    """Comprehensive model evaluation and comparison system"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # Evaluation settings
        self.default_cv_folds = 5
        self.significance_threshold = 0.05
        self.overfitting_threshold = 0.1  # 10% difference between train/val
        
        # Metric configurations
        self.classification_metrics = [
            EvaluationMetric.ACCURACY, EvaluationMetric.PRECISION,
            EvaluationMetric.RECALL, EvaluationMetric.F1_SCORE,
            EvaluationMetric.ROC_AUC
        ]
        
        self.regression_metrics = [
            EvaluationMetric.MSE, EvaluationMetric.MAE,
            EvaluationMetric.R2_SCORE
        ]
        
        self.trading_metrics = [
            EvaluationMetric.PROFIT_LOSS, EvaluationMetric.SHARPE_RATIO,
            EvaluationMetric.MAX_DRAWDOWN, EvaluationMetric.WIN_RATE,
            EvaluationMetric.RISK_RETURN_RATIO
        ]
        
        # Initialize database tables
        self._init_evaluation_tables()
        
        self.logger.info("Model Evaluator initialized")
    
    def evaluate_model(self, model: Any, X_test: np.ndarray, y_test: np.ndarray,
                      model_name: str, model_type: ModelType = ModelType.CLASSIFICATION,
                      X_train: Optional[np.ndarray] = None, y_train: Optional[np.ndarray] = None,
                      trading_data: Optional[pd.DataFrame] = None) -> EvaluationResult:
        """Comprehensive model evaluation"""
        try:
            self.logger.info(f"Evaluating model: {model_name}")
            
            model_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Basic predictions
            y_pred = model.predict(X_test)
            y_pred_proba = None
            
            if hasattr(model, 'predict_proba') and model_type == ModelType.CLASSIFICATION:
                y_pred_proba = model.predict_proba(X_test)
            
            # Calculate metrics
            metrics = self._calculate_metrics(y_test, y_pred, y_pred_proba, model_type, trading_data)
            
            # Detailed metrics
            detailed_metrics = self._calculate_detailed_metrics(y_test, y_pred, y_pred_proba, model_type)
            
            # Cross-validation scores
            validation_scores = {}
            if X_train is not None and y_train is not None:
                validation_scores = self._perform_cross_validation(model, X_train, y_train, model_type)
            
            # Overfitting analysis
            overfitting_analysis = {}
            if X_train is not None and y_train is not None:
                overfitting_analysis = self._analyze_overfitting(
                    model, X_train, y_train, X_test, y_test, model_type
                )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                metrics, overfitting_analysis, validation_scores
            )
            
            # Create evaluation result
            result = EvaluationResult(
                model_id=model_id,
                model_name=model_name,
                model_type=model_type,
                evaluation_timestamp=datetime.now(),
                metrics=metrics,
                detailed_metrics=detailed_metrics,
                validation_scores=validation_scores,
                overfitting_analysis=overfitting_analysis,
                recommendations=recommendations
            )
            
            # Store evaluation result
            self._store_evaluation_result(result)
            
            self.logger.info(f"Model evaluation completed: {model_name}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error evaluating model {model_name}: {e}")
            raise
    
    def compare_models(self, models: Dict[str, Any], X_test: np.ndarray, y_test: np.ndarray,
                      primary_metric: str = "accuracy", X_train: Optional[np.ndarray] = None,
                      y_train: Optional[np.ndarray] = None) -> ModelComparison:
        """Compare multiple models and determine the best performer"""
        try:
            self.logger.info(f"Comparing {len(models)} models")
            
            comparison_id = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            model_results = {}
            
            # Evaluate each model
            for model_name, model in models.items():
                try:
                    # Determine model type
                    model_type = self._determine_model_type(model)
                    
                    # Evaluate model
                    result = self.evaluate_model(
                        model, X_test, y_test, model_name, model_type, X_train, y_train
                    )
                    
                    model_results[model_name] = result
                    
                except Exception as model_error:
                    self.logger.warning(f"Error evaluating model {model_name}: {model_error}")
                    continue
            
            if not model_results:
                raise ValueError("No models could be evaluated successfully")
            
            # Extract comparison metrics
            comparison_results = {}
            for model_name, result in model_results.items():
                comparison_results[model_name] = result.metrics
            
            # Statistical significance testing
            statistical_significance = self._test_statistical_significance(
                model_results, primary_metric
            )
            
            # Rank models
            ranking = self._rank_models(comparison_results, primary_metric)
            
            # Determine best model
            best_model = ranking[0][0] if ranking else list(models.keys())[0]
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(
                statistical_significance, primary_metric
            )
            
            # Generate recommendations
            recommendations = self._generate_comparison_recommendations(
                comparison_results, statistical_significance, ranking
            )
            
            # Create comparison result
            comparison = ModelComparison(
                comparison_id=comparison_id,
                models_compared=list(models.keys()),
                comparison_timestamp=datetime.now(),
                primary_metric=primary_metric,
                comparison_results=comparison_results,
                statistical_significance=statistical_significance,
                ranking=ranking,
                recommendations=recommendations,
                best_model=best_model,
                confidence_level=confidence_level
            )
            
            # Store comparison result
            self._store_comparison_result(comparison)
            
            self.logger.info(f"Model comparison completed. Best model: {best_model}")
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing models: {e}")
            raise 
   
    def detect_overfitting(self, model: Any, X_train: np.ndarray, y_train: np.ndarray,
                          X_val: np.ndarray, y_val: np.ndarray,
                          model_type: ModelType = ModelType.CLASSIFICATION) -> Dict[str, Any]:
        """Detect overfitting in model performance"""
        try:
            # Train predictions
            y_train_pred = model.predict(X_train)
            train_metrics = self._calculate_basic_metrics(y_train, y_train_pred, model_type)
            
            # Validation predictions
            y_val_pred = model.predict(X_val)
            val_metrics = self._calculate_basic_metrics(y_val, y_val_pred, model_type)
            
            # Calculate overfitting indicators
            overfitting_analysis = {
                'train_metrics': train_metrics,
                'validation_metrics': val_metrics,
                'metric_differences': {},
                'overfitting_detected': False,
                'overfitting_severity': 'none',
                'recommendations': []
            }
            
            # Analyze differences
            for metric, train_value in train_metrics.items():
                if metric in val_metrics:
                    val_value = val_metrics[metric]
                    difference = abs(train_value - val_value)
                    relative_difference = difference / max(train_value, 1e-8)
                    
                    overfitting_analysis['metric_differences'][metric] = {
                        'absolute_difference': difference,
                        'relative_difference': relative_difference,
                        'train_value': train_value,
                        'validation_value': val_value
                    }
                    
                    # Check for overfitting
                    if relative_difference > self.overfitting_threshold:
                        overfitting_analysis['overfitting_detected'] = True
            
            # Determine severity
            if overfitting_analysis['overfitting_detected']:
                max_difference = max(
                    diff['relative_difference'] 
                    for diff in overfitting_analysis['metric_differences'].values()
                )
                
                if max_difference > 0.3:
                    overfitting_analysis['overfitting_severity'] = 'severe'
                elif max_difference > 0.2:
                    overfitting_analysis['overfitting_severity'] = 'moderate'
                else:
                    overfitting_analysis['overfitting_severity'] = 'mild'
            
            # Generate recommendations
            if overfitting_analysis['overfitting_detected']:
                severity = overfitting_analysis['overfitting_severity']
                if severity == 'severe':
                    overfitting_analysis['recommendations'].extend([
                        'Consider reducing model complexity',
                        'Increase regularization strength',
                        'Collect more training data',
                        'Use dropout or early stopping'
                    ])
                elif severity == 'moderate':
                    overfitting_analysis['recommendations'].extend([
                        'Apply regularization techniques',
                        'Consider cross-validation',
                        'Monitor validation metrics during training'
                    ])
                else:
                    overfitting_analysis['recommendations'].extend([
                        'Monitor training progress',
                        'Consider slight regularization'
                    ])
            
            return overfitting_analysis
            
        except Exception as e:
            self.logger.error(f"Error detecting overfitting: {e}")
            return {'error': str(e)}
    
    def evaluate_current_model(self, model: Any, test_data: pd.DataFrame,
                             model_name: str = "current_model") -> Dict[str, float]:
        """Evaluate current model performance on test data"""
        try:
            if 'target' not in test_data.columns:
                raise ValueError("Test data must contain 'target' column")
            
            # Separate features and target
            X_test = test_data.drop('target', axis=1).values
            y_test = test_data['target'].values
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Determine model type
            model_type = ModelType.CLASSIFICATION if len(np.unique(y_test)) <= 10 else ModelType.REGRESSION
            
            # Calculate metrics
            metrics = self._calculate_basic_metrics(y_test, y_pred, model_type)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error evaluating current model: {e}")
            return {'error': str(e)}
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                          y_pred_proba: Optional[np.ndarray], model_type: ModelType,
                          trading_data: Optional[pd.DataFrame]) -> Dict[str, float]:
        """Calculate comprehensive metrics based on model type"""
        metrics = {}
        
        try:
            if model_type == ModelType.CLASSIFICATION:
                # Classification metrics
                metrics['accuracy'] = accuracy_score(y_true, y_pred)
                metrics['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
                metrics['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
                metrics['f1_score'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
                
                # ROC AUC for binary classification
                if len(np.unique(y_true)) == 2 and y_pred_proba is not None:
                    metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba[:, 1])
                
                # Win rate (for trading)
                metrics['win_rate'] = np.mean(y_pred == 1) if len(np.unique(y_true)) == 2 else metrics['accuracy']
                
            elif model_type == ModelType.REGRESSION:
                # Regression metrics
                metrics['mse'] = mean_squared_error(y_true, y_pred)
                metrics['mae'] = mean_absolute_error(y_true, y_pred)
                metrics['rmse'] = np.sqrt(metrics['mse'])
                metrics['r2_score'] = r2_score(y_true, y_pred)
            
            # Trading-specific metrics
            if trading_data is not None:
                trading_metrics = self._calculate_trading_metrics(y_true, y_pred, trading_data)
                metrics.update(trading_metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_basic_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                               model_type: ModelType) -> Dict[str, float]:
        """Calculate basic metrics for overfitting detection"""
        metrics = {}
        
        try:
            if model_type == ModelType.CLASSIFICATION:
                metrics['accuracy'] = accuracy_score(y_true, y_pred)
                metrics['f1_score'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
            else:
                metrics['mse'] = mean_squared_error(y_true, y_pred)
                metrics['r2_score'] = r2_score(y_true, y_pred)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating basic metrics: {e}")
            return {}
    
    def _calculate_detailed_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                                  y_pred_proba: Optional[np.ndarray],
                                  model_type: ModelType) -> Dict[str, Any]:
        """Calculate detailed metrics including confusion matrix and classification report"""
        detailed = {}
        
        try:
            if model_type == ModelType.CLASSIFICATION:
                # Confusion matrix
                cm = confusion_matrix(y_true, y_pred)
                detailed['confusion_matrix'] = cm.tolist()
                
                # Classification report
                report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
                detailed['classification_report'] = report
                
                # Class distribution
                unique, counts = np.unique(y_true, return_counts=True)
                detailed['class_distribution'] = dict(zip(unique.tolist(), counts.tolist()))
                
            # Prediction statistics
            detailed['prediction_stats'] = {
                'mean_prediction': float(np.mean(y_pred)),
                'std_prediction': float(np.std(y_pred)),
                'min_prediction': float(np.min(y_pred)),
                'max_prediction': float(np.max(y_pred))
            }
            
            # True value statistics
            detailed['true_value_stats'] = {
                'mean_true': float(np.mean(y_true)),
                'std_true': float(np.std(y_true)),
                'min_true': float(np.min(y_true)),
                'max_true': float(np.max(y_true))
            }
            
            return detailed
            
        except Exception as e:
            self.logger.error(f"Error calculating detailed metrics: {e}")
            return {'error': str(e)} 
   
    def _calculate_trading_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                                 trading_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate trading-specific performance metrics"""
        metrics = {}
        
        try:
            if 'profit_loss' in trading_data.columns:
                # Align predictions with trading data
                profits = trading_data['profit_loss'].values[:len(y_pred)]
                
                # Total profit/loss
                total_pnl = np.sum(profits)
                metrics['total_profit_loss'] = float(total_pnl)
                
                # Average profit per trade
                metrics['avg_profit_per_trade'] = float(np.mean(profits))
                
                # Win rate
                winning_trades = np.sum(profits > 0)
                total_trades = len(profits)
                metrics['win_rate'] = float(winning_trades / total_trades) if total_trades > 0 else 0.0
                
                # Profit factor
                gross_profit = np.sum(profits[profits > 0])
                gross_loss = abs(np.sum(profits[profits < 0]))
                metrics['profit_factor'] = float(gross_profit / gross_loss) if gross_loss > 0 else float('inf')
                
                # Sharpe ratio (simplified)
                if len(profits) > 1:
                    returns = profits / np.abs(profits).mean() if np.abs(profits).mean() > 0 else profits
                    metrics['sharpe_ratio'] = float(np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0.0
                else:
                    metrics['sharpe_ratio'] = 0.0
                
                # Maximum drawdown
                cumulative_returns = np.cumsum(profits)
                running_max = np.maximum.accumulate(cumulative_returns)
                drawdown = cumulative_returns - running_max
                metrics['max_drawdown'] = float(np.min(drawdown))
                
                # Risk-return ratio
                if metrics['max_drawdown'] < 0:
                    metrics['risk_return_ratio'] = float(total_pnl / abs(metrics['max_drawdown']))
                else:
                    metrics['risk_return_ratio'] = float('inf') if total_pnl > 0 else 0.0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating trading metrics: {e}")
            return {}
    
    def _perform_cross_validation(self, model: Any, X: np.ndarray, y: np.ndarray,
                                model_type: ModelType) -> Dict[str, List[float]]:
        """Perform cross-validation and return scores"""
        validation_scores = {}
        
        try:
            # Determine scoring metrics based on model type
            if model_type == ModelType.CLASSIFICATION:
                scoring_metrics = ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']
            else:
                scoring_metrics = ['neg_mean_squared_error', 'neg_mean_absolute_error', 'r2']
            
            # Perform cross-validation for each metric
            for metric in scoring_metrics:
                try:
                    scores = cross_val_score(model, X, y, cv=self.default_cv_folds, scoring=metric)
                    # Convert negative scores to positive for error metrics
                    if metric.startswith('neg_'):
                        scores = -scores
                        metric = metric[4:]  # Remove 'neg_' prefix
                    
                    validation_scores[metric] = scores.tolist()
                    
                except Exception as metric_error:
                    self.logger.warning(f"Error calculating {metric} in cross-validation: {metric_error}")
                    continue
            
            return validation_scores
            
        except Exception as e:
            self.logger.error(f"Error performing cross-validation: {e}")
            return {}
    
    def _analyze_overfitting(self, model: Any, X_train: np.ndarray, y_train: np.ndarray,
                           X_test: np.ndarray, y_test: np.ndarray,
                           model_type: ModelType) -> Dict[str, Any]:
        """Analyze overfitting using learning curves"""
        try:
            # Generate learning curves
            train_sizes, train_scores, val_scores = learning_curve(
                model, X_train, y_train, cv=3, n_jobs=-1,
                train_sizes=np.linspace(0.1, 1.0, 10),
                scoring='accuracy' if model_type == ModelType.CLASSIFICATION else 'neg_mean_squared_error'
            )
            
            # Calculate mean and std for train and validation scores
            train_mean = np.mean(train_scores, axis=1)
            train_std = np.std(train_scores, axis=1)
            val_mean = np.mean(val_scores, axis=1)
            val_std = np.std(val_scores, axis=1)
            
            # Convert negative scores to positive for regression
            if model_type == ModelType.REGRESSION:
                train_mean = -train_mean
                val_mean = -val_mean
            
            # Analyze overfitting
            final_train_score = train_mean[-1]
            final_val_score = val_mean[-1]
            score_gap = abs(final_train_score - final_val_score)
            relative_gap = score_gap / max(final_train_score, 1e-8)
            
            overfitting_analysis = {
                'train_sizes': train_sizes.tolist(),
                'train_scores_mean': train_mean.tolist(),
                'train_scores_std': train_std.tolist(),
                'validation_scores_mean': val_mean.tolist(),
                'validation_scores_std': val_std.tolist(),
                'final_train_score': float(final_train_score),
                'final_validation_score': float(final_val_score),
                'score_gap': float(score_gap),
                'relative_gap': float(relative_gap),
                'overfitting_detected': relative_gap > self.overfitting_threshold,
                'overfitting_severity': self._determine_overfitting_severity(relative_gap)
            }
            
            return overfitting_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing overfitting: {e}")
            return {'error': str(e)}
    
    def _determine_overfitting_severity(self, relative_gap: float) -> str:
        """Determine the severity of overfitting"""
        if relative_gap <= self.overfitting_threshold:
            return 'none'
        elif relative_gap <= 0.2:
            return 'mild'
        elif relative_gap <= 0.3:
            return 'moderate'
        else:
            return 'severe'
    
    def _determine_model_type(self, model: Any) -> ModelType:
        """Determine the type of model"""
        try:
            model_name = type(model).__name__.lower()
            
            if 'classifier' in model_name or 'classification' in model_name:
                return ModelType.CLASSIFICATION
            elif 'regressor' in model_name or 'regression' in model_name:
                return ModelType.REGRESSION
            elif 'ensemble' in model_name or 'forest' in model_name or 'boosting' in model_name:
                return ModelType.ENSEMBLE
            elif 'neural' in model_name or 'mlp' in model_name:
                return ModelType.NEURAL_NETWORK
            elif 'tree' in model_name or 'decision' in model_name:
                return ModelType.TREE_BASED
            else:
                # Default to classification
                return ModelType.CLASSIFICATION
                
        except Exception as e:
            self.logger.warning(f"Could not determine model type: {e}")
            return ModelType.CLASSIFICATION
    
    def _test_statistical_significance(self, model_results: Dict[str, EvaluationResult],
                                     primary_metric: str) -> Dict[str, Dict[str, float]]:
        """Test statistical significance between model performances"""
        significance_results = {}
        
        try:
            model_names = list(model_results.keys())
            
            for i, model1 in enumerate(model_names):
                significance_results[model1] = {}
                
                for j, model2 in enumerate(model_names):
                    if i != j:
                        # Get cross-validation scores for both models
                        scores1 = model_results[model1].validation_scores.get(primary_metric, [])
                        scores2 = model_results[model2].validation_scores.get(primary_metric, [])
                        
                        if scores1 and scores2:
                            # Perform t-test (simplified)
                            from scipy import stats
                            try:
                                t_stat, p_value = stats.ttest_ind(scores1, scores2)
                                significance_results[model1][model2] = {
                                    't_statistic': float(t_stat),
                                    'p_value': float(p_value),
                                    'significant': p_value < self.significance_threshold
                                }
                            except ImportError:
                                # Fallback if scipy not available
                                mean_diff = np.mean(scores1) - np.mean(scores2)
                                significance_results[model1][model2] = {
                                    'mean_difference': float(mean_diff),
                                    'significant': abs(mean_diff) > 0.05
                                }
                        else:
                            significance_results[model1][model2] = {
                                'significant': False,
                                'note': 'Insufficient data for significance testing'
                            }
            
            return significance_results
            
        except Exception as e:
            self.logger.error(f"Error testing statistical significance: {e}")
            return {}
    
    def _rank_models(self, comparison_results: Dict[str, Dict[str, float]],
                    primary_metric: str) -> List[Tuple[str, float]]:
        """Rank models based on primary metric"""
        try:
            model_scores = []
            
            for model_name, metrics in comparison_results.items():
                if primary_metric in metrics:
                    score = metrics[primary_metric]
                    model_scores.append((model_name, score))
            
            # Sort by score (descending for most metrics, ascending for error metrics)
            reverse_sort = primary_metric not in ['mse', 'mae', 'max_drawdown']
            model_scores.sort(key=lambda x: x[1], reverse=reverse_sort)
            
            return model_scores
            
        except Exception as e:
            self.logger.error(f"Error ranking models: {e}")
            return [] 
   
    def _calculate_confidence_level(self, statistical_significance: Dict[str, Dict[str, float]],
                                   primary_metric: str) -> float:
        """Calculate confidence level for model comparison"""
        try:
            if not statistical_significance:
                return 0.5  # Low confidence without significance testing
            
            significant_comparisons = 0
            total_comparisons = 0
            
            for model1, comparisons in statistical_significance.items():
                for model2, result in comparisons.items():
                    if 'significant' in result:
                        total_comparisons += 1
                        if result['significant']:
                            significant_comparisons += 1
            
            if total_comparisons == 0:
                return 0.5
            
            # Confidence based on proportion of significant comparisons
            confidence = significant_comparisons / total_comparisons
            return min(max(confidence, 0.1), 0.95)  # Clamp between 0.1 and 0.95
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence level: {e}")
            return 0.5
    
    def _generate_recommendations(self, metrics: Dict[str, float],
                                overfitting_analysis: Dict[str, Any],
                                validation_scores: Dict[str, List[float]]) -> List[str]:
        """Generate recommendations based on evaluation results"""
        recommendations = []
        
        try:
            # Performance-based recommendations
            accuracy = metrics.get('accuracy', 0)
            if accuracy < 0.6:
                recommendations.append("Model accuracy is low. Consider feature engineering or different algorithms.")
            elif accuracy > 0.95:
                recommendations.append("Very high accuracy detected. Check for data leakage or overfitting.")
            
            # Overfitting recommendations
            if overfitting_analysis.get('overfitting_detected', False):
                severity = overfitting_analysis.get('overfitting_severity', 'mild')
                if severity == 'severe':
                    recommendations.append("Severe overfitting detected. Reduce model complexity or increase regularization.")
                elif severity == 'moderate':
                    recommendations.append("Moderate overfitting detected. Consider regularization techniques.")
                else:
                    recommendations.append("Mild overfitting detected. Monitor validation performance.")
            
            # Cross-validation recommendations
            if validation_scores:
                for metric, scores in validation_scores.items():
                    if len(scores) > 1:
                        cv_std = np.std(scores)
                        cv_mean = np.mean(scores)
                        cv_coefficient = cv_std / cv_mean if cv_mean > 0 else 0
                        
                        if cv_coefficient > 0.1:
                            recommendations.append(f"High variance in {metric} across folds. Model may be unstable.")
            
            # Trading-specific recommendations
            if 'win_rate' in metrics:
                win_rate = metrics['win_rate']
                if win_rate < 0.4:
                    recommendations.append("Low win rate. Consider adjusting signal thresholds or strategy.")
                elif win_rate > 0.8:
                    recommendations.append("Very high win rate. Verify signal quality and check for look-ahead bias.")
            
            if 'sharpe_ratio' in metrics:
                sharpe = metrics['sharpe_ratio']
                if sharpe < 1.0:
                    recommendations.append("Low Sharpe ratio. Risk-adjusted returns could be improved.")
                elif sharpe > 3.0:
                    recommendations.append("Excellent Sharpe ratio. Validate results and consider position sizing.")
            
            # Default recommendation if no specific issues found
            if not recommendations:
                recommendations.append("Model performance appears satisfactory. Continue monitoring.")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations. Manual review recommended."]
    
    def _generate_comparison_recommendations(self, comparison_results: Dict[str, Dict[str, float]],
                                           statistical_significance: Dict[str, Dict[str, float]],
                                           ranking: List[Tuple[str, float]]) -> List[str]:
        """Generate recommendations based on model comparison"""
        recommendations = []
        
        try:
            if not ranking:
                return ["No models could be ranked. Check evaluation results."]
            
            best_model, best_score = ranking[0]
            
            # Performance gap analysis
            if len(ranking) > 1:
                second_best_score = ranking[1][1]
                performance_gap = abs(best_score - second_best_score)
                
                if performance_gap < 0.01:
                    recommendations.append("Top models have very similar performance. Consider ensemble methods.")
                elif performance_gap > 0.1:
                    recommendations.append(f"{best_model} significantly outperforms other models.")
            
            # Statistical significance analysis
            if statistical_significance:
                significant_wins = 0
                total_comparisons = 0
                
                if best_model in statistical_significance:
                    for comparison in statistical_significance[best_model].values():
                        if 'significant' in comparison:
                            total_comparisons += 1
                            if comparison['significant']:
                                significant_wins += 1
                
                if total_comparisons > 0:
                    significance_ratio = significant_wins / total_comparisons
                    if significance_ratio < 0.5:
                        recommendations.append("Best model's superiority is not statistically significant.")
                    elif significance_ratio > 0.8:
                        recommendations.append("Best model shows statistically significant improvement.")
            
            # Model diversity recommendations
            model_types = set()
            for model_name in comparison_results.keys():
                # Simple heuristic to identify model types
                if 'forest' in model_name.lower() or 'tree' in model_name.lower():
                    model_types.add('tree_based')
                elif 'neural' in model_name.lower() or 'mlp' in model_name.lower():
                    model_types.add('neural_network')
                elif 'svm' in model_name.lower():
                    model_types.add('svm')
                else:
                    model_types.add('other')
            
            if len(model_types) < 3:
                recommendations.append("Consider testing more diverse model types for better comparison.")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating comparison recommendations: {e}")
            return ["Error generating comparison recommendations."]
    
    def _store_evaluation_result(self, result: EvaluationResult):
        """Store evaluation result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                INSERT INTO model_evaluations 
                (model_id, model_name, model_type, evaluation_timestamp, metrics, 
                 detailed_metrics, validation_scores, overfitting_analysis, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                result.model_id,
                result.model_name,
                result.model_type.value,
                result.evaluation_timestamp.isoformat(),
                json.dumps(result.metrics),
                json.dumps(result.detailed_metrics),
                json.dumps(result.validation_scores),
                json.dumps(result.overfitting_analysis),
                json.dumps(result.recommendations)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing evaluation result: {e}")
    
    def _store_comparison_result(self, comparison: ModelComparison):
        """Store model comparison result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                INSERT INTO model_comparisons 
                (comparison_id, models_compared, comparison_timestamp, primary_metric,
                 comparison_results, statistical_significance, ranking, recommendations,
                 best_model, confidence_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                comparison.comparison_id,
                json.dumps(comparison.models_compared),
                comparison.comparison_timestamp.isoformat(),
                comparison.primary_metric,
                json.dumps(comparison.comparison_results),
                json.dumps(comparison.statistical_significance),
                json.dumps(comparison.ranking),
                json.dumps(comparison.recommendations),
                comparison.best_model,
                comparison.confidence_level
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing comparison result: {e}")
    
    def _init_evaluation_tables(self):
        """Initialize database tables for model evaluation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Model evaluations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    evaluation_timestamp TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    detailed_metrics TEXT,
                    validation_scores TEXT,
                    overfitting_analysis TEXT,
                    recommendations TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Model comparisons table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_id TEXT NOT NULL,
                    models_compared TEXT NOT NULL,
                    comparison_timestamp TEXT NOT NULL,
                    primary_metric TEXT NOT NULL,
                    comparison_results TEXT NOT NULL,
                    statistical_significance TEXT,
                    ranking TEXT NOT NULL,
                    recommendations TEXT,
                    best_model TEXT NOT NULL,
                    confidence_level REAL NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_evaluations_model_name 
                ON model_evaluations(model_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_evaluations_timestamp 
                ON model_evaluations(evaluation_timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_comparisons_timestamp 
                ON model_comparisons(comparison_timestamp)
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing evaluation tables: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize model evaluator
    evaluator = ModelEvaluator("Data/test_model_evaluator.db")
    
    print("Model Evaluator initialized successfully!")
    
    # Create sample data for testing
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    
    # Generate sample data
    X, y = make_classification(n_samples=1000, n_features=20, n_classes=2, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # Train sample models
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    
    lr_model = LogisticRegression(random_state=42)
    lr_model.fit(X_train, y_train)
    
    # Test single model evaluation
    rf_result = evaluator.evaluate_model(
        rf_model, X_test, y_test, "RandomForest", ModelType.CLASSIFICATION, X_train, y_train
    )
    
    print(f"RandomForest evaluation:")
    print(f"  - Accuracy: {rf_result.metrics.get('accuracy', 0):.3f}")
    print(f"  - F1 Score: {rf_result.metrics.get('f1_score', 0):.3f}")
    print(f"  - Overfitting detected: {rf_result.overfitting_analysis.get('overfitting_detected', False)}")
    print(f"  - Recommendations: {len(rf_result.recommendations)}")
    
    # Test model comparison
    models = {
        'RandomForest': rf_model,
        'LogisticRegression': lr_model
    }
    
    comparison = evaluator.compare_models(models, X_test, y_test, 'accuracy', X_train, y_train)
    
    print(f"\nModel comparison:")
    print(f"  - Best model: {comparison.best_model}")
    print(f"  - Confidence level: {comparison.confidence_level:.3f}")
    print(f"  - Models compared: {len(comparison.models_compared)}")
    print(f"  - Recommendations: {len(comparison.recommendations)}")
    
    print("Model Evaluator test completed!")