"""
Cross-Validation and Testing Framework for AI Continuous Learning System
Comprehensive framework for model validation, testing, and statistical analysis
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
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from sklearn.model_selection import (
    KFold, StratifiedKFold, TimeSeriesSplit, cross_val_score,
    cross_validate, validation_curve, learning_curve
)
from sklearn.metrics import make_scorer
import warnings
warnings.filterwarnings('ignore')

try:
    from model_evaluator import ModelEvaluator, EvaluationResult, ModelType, EvaluationMetric
except ImportError:
    from Python.model_evaluator import ModelEvaluator, EvaluationResult, ModelType, EvaluationMetric


class ValidationStrategy(Enum):
    """Cross-validation strategies"""
    K_FOLD = "k_fold"
    STRATIFIED_K_FOLD = "stratified_k_fold"
    TIME_SERIES_SPLIT = "time_series_split"
    LEAVE_ONE_OUT = "leave_one_out"
    MONTE_CARLO = "monte_carlo"


class TestType(Enum):
    """Types of statistical tests"""
    T_TEST = "t_test"
    WILCOXON = "wilcoxon"
    MANN_WHITNEY = "mann_whitney"
    FRIEDMAN = "friedman"
    BOOTSTRAP = "bootstrap"


@dataclass
class CrossValidationResult:
    """Result of cross-validation analysis"""
    model_name: str
    validation_strategy: ValidationStrategy
    n_folds: int
    scores: Dict[str, List[float]]
    mean_scores: Dict[str, float]
    std_scores: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    stability_metrics: Dict[str, float]
    validation_timestamp: datetime
    recommendations: List[str] = field(default_factory=list)


@dataclass
class OutOfSampleResult:
    """Result of out-of-sample testing"""
    model_name: str
    test_period: str
    test_size: float
    performance_metrics: Dict[str, float]
    degradation_analysis: Dict[str, Any]
    temporal_stability: Dict[str, float]
    recommendations: List[str] = field(default_factory=list)


@dataclass
class StatisticalTestResult:
    """Result of statistical significance testing"""
    test_type: TestType
    models_compared: List[str]
    test_statistic: float
    p_value: float
    effect_size: float
    confidence_level: float
    is_significant: bool
    interpretation: str
    recommendations: List[str] = field(default_factory=list)


class CrossValidationFramework:
    """Comprehensive cross-validation and testing framework"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.model_evaluator = ModelEvaluator(db_path)
        
        # Default settings
        self.default_cv_folds = 5
        self.confidence_level = 0.95
        self.significance_threshold = 0.05
        self.stability_threshold = 0.1  # 10% coefficient of variation
        
        # Initialize database tables
        self._init_cv_tables()
        
        self.logger.info("Cross-Validation Framework initialized")
    
    def perform_cross_validation(self, model: Any, X: np.ndarray, y: np.ndarray,
                                model_name: str, strategy: ValidationStrategy = ValidationStrategy.K_FOLD,
                                n_folds: int = 5, scoring_metrics: Optional[List[str]] = None) -> CrossValidationResult:
        """Perform comprehensive cross-validation analysis"""
        try:
            self.logger.info(f"Performing cross-validation for {model_name} using {strategy.value}")
            
            # Determine model type
            model_type = self._determine_model_type(model)
            
            # Set default scoring metrics
            if scoring_metrics is None:
                scoring_metrics = self._get_default_scoring_metrics(model_type)
            
            # Create cross-validation strategy
            cv_strategy = self._create_cv_strategy(strategy, n_folds, y)
            
            # Perform cross-validation
            cv_results = cross_validate(
                model, X, y, cv=cv_strategy, scoring=scoring_metrics,
                return_train_score=True, n_jobs=-1
            )
            
            # Process results
            scores = {}
            mean_scores = {}
            std_scores = {}
            confidence_intervals = {}
            
            for metric in scoring_metrics:
                test_scores = cv_results[f'test_{metric}']
                train_scores = cv_results[f'train_{metric}']
                
                # Handle negative scores (convert to positive)
                if metric.startswith('neg_'):
                    test_scores = -test_scores
                    train_scores = -train_scores
                    metric_name = metric[4:]  # Remove 'neg_' prefix
                else:
                    metric_name = metric
                
                scores[metric_name] = {
                    'test_scores': test_scores.tolist(),
                    'train_scores': train_scores.tolist()
                }
                
                mean_scores[metric_name] = float(np.mean(test_scores))
                std_scores[metric_name] = float(np.std(test_scores))
                
                # Calculate confidence intervals
                ci_lower, ci_upper = self._calculate_confidence_interval(
                    test_scores, self.confidence_level
                )
                confidence_intervals[metric_name] = (ci_lower, ci_upper)
            
            # Calculate stability metrics
            stability_metrics = self._calculate_stability_metrics(scores)
            
            # Generate recommendations
            recommendations = self._generate_cv_recommendations(
                scores, stability_metrics, mean_scores, std_scores
            )
            
            # Create result
            result = CrossValidationResult(
                model_name=model_name,
                validation_strategy=strategy,
                n_folds=n_folds,
                scores=scores,
                mean_scores=mean_scores,
                std_scores=std_scores,
                confidence_intervals=confidence_intervals,
                stability_metrics=stability_metrics,
                validation_timestamp=datetime.now(),
                recommendations=recommendations
            )
            
            # Store result
            self._store_cv_result(result)
            
            self.logger.info(f"Cross-validation completed for {model_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error performing cross-validation for {model_name}: {e}")
            raise
    
    def perform_out_of_sample_testing(self, model: Any, X_train: np.ndarray, y_train: np.ndarray,
                                    X_test: np.ndarray, y_test: np.ndarray, model_name: str,
                                    test_period: str = "recent", temporal_data: Optional[pd.DataFrame] = None) -> OutOfSampleResult:
        """Perform comprehensive out-of-sample testing"""
        try:
            self.logger.info(f"Performing out-of-sample testing for {model_name}")
            
            # Train model on training data
            model.fit(X_train, y_train)
            
            # Make predictions on test data
            y_pred = model.predict(X_test)
            
            # Determine model type
            model_type = self._determine_model_type(model)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_oos_metrics(y_test, y_pred, model_type)
            
            # Analyze performance degradation
            degradation_analysis = self._analyze_performance_degradation(
                model, X_train, y_train, X_test, y_test, model_type
            )
            
            # Analyze temporal stability if temporal data provided
            temporal_stability = {}
            if temporal_data is not None:
                temporal_stability = self._analyze_temporal_stability(
                    model, temporal_data, model_type
                )
            
            # Generate recommendations
            recommendations = self._generate_oos_recommendations(
                performance_metrics, degradation_analysis, temporal_stability
            )
            
            # Calculate test size
            test_size = len(X_test) / (len(X_train) + len(X_test))
            
            # Create result
            result = OutOfSampleResult(
                model_name=model_name,
                test_period=test_period,
                test_size=test_size,
                performance_metrics=performance_metrics,
                degradation_analysis=degradation_analysis,
                temporal_stability=temporal_stability,
                recommendations=recommendations
            )
            
            # Store result
            self._store_oos_result(result)
            
            self.logger.info(f"Out-of-sample testing completed for {model_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error performing out-of-sample testing for {model_name}: {e}")
            raise
    
    def perform_statistical_significance_test(self, model_scores_1: List[float], model_scores_2: List[float],
                                            model_name_1: str, model_name_2: str,
                                            test_type: TestType = TestType.T_TEST) -> StatisticalTestResult:
        """Perform statistical significance testing between two models"""
        try:
            self.logger.info(f"Performing {test_type.value} between {model_name_1} and {model_name_2}")
            
            # Perform statistical test
            test_result = self._perform_statistical_test(
                model_scores_1, model_scores_2, test_type
            )
            
            # Calculate effect size
            effect_size = self._calculate_effect_size(model_scores_1, model_scores_2)
            
            # Determine significance
            is_significant = test_result['p_value'] < self.significance_threshold
            
            # Generate interpretation
            interpretation = self._interpret_statistical_test(
                test_result, effect_size, is_significant
            )
            
            # Generate recommendations
            recommendations = self._generate_statistical_recommendations(
                test_result, effect_size, is_significant
            )
            
            # Create result
            result = StatisticalTestResult(
                test_type=test_type,
                models_compared=[model_name_1, model_name_2],
                test_statistic=test_result['statistic'],
                p_value=test_result['p_value'],
                effect_size=effect_size,
                confidence_level=self.confidence_level,
                is_significant=is_significant,
                interpretation=interpretation,
                recommendations=recommendations
            )
            
            # Store result
            self._store_statistical_test_result(result)
            
            self.logger.info(f"Statistical test completed: {interpretation}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error performing statistical test: {e}")
            raise
    
    def validate_model_stability(self, model: Any, X: np.ndarray, y: np.ndarray,
                               model_name: str, n_iterations: int = 10) -> Dict[str, Any]:
        """Validate model stability across multiple training iterations"""
        try:
            self.logger.info(f"Validating stability for {model_name} over {n_iterations} iterations")
            
            model_type = self._determine_model_type(model)
            all_scores = []
            
            # Perform multiple training iterations with different random states
            for i in range(n_iterations):
                try:
                    # Create a copy of the model with different random state
                    model_copy = self._create_model_copy(model, random_state=i)
                    
                    # Perform cross-validation
                    cv_result = self.perform_cross_validation(
                        model_copy, X, y, f"{model_name}_iter_{i}",
                        strategy=ValidationStrategy.K_FOLD, n_folds=3
                    )
                    
                    # Extract primary metric scores
                    primary_metric = 'accuracy' if model_type == ModelType.CLASSIFICATION else 'mean_squared_error'
                    if primary_metric in cv_result.mean_scores:
                        all_scores.append(cv_result.mean_scores[primary_metric])
                    
                except Exception as iter_error:
                    self.logger.warning(f"Error in iteration {i}: {iter_error}")
                    continue
            
            if not all_scores:
                raise ValueError("No successful iterations completed")
            
            # Calculate stability metrics
            stability_analysis = {
                'n_iterations': len(all_scores),
                'mean_performance': float(np.mean(all_scores)),
                'std_performance': float(np.std(all_scores)),
                'coefficient_of_variation': float(np.std(all_scores) / np.mean(all_scores)) if np.mean(all_scores) != 0 else float('inf'),
                'min_performance': float(np.min(all_scores)),
                'max_performance': float(np.max(all_scores)),
                'performance_range': float(np.max(all_scores) - np.min(all_scores)),
                'is_stable': float(np.std(all_scores) / np.mean(all_scores)) < self.stability_threshold if np.mean(all_scores) != 0 else False,
                'all_scores': all_scores
            }
            
            # Generate recommendations
            if stability_analysis['is_stable']:
                stability_analysis['recommendations'] = [
                    "Model shows good stability across iterations",
                    "Performance is consistent and reliable"
                ]
            else:
                stability_analysis['recommendations'] = [
                    "Model shows instability across iterations",
                    "Consider increasing training data or regularization",
                    "Review hyperparameter settings",
                    "Consider ensemble methods for better stability"
                ]
            
            self.logger.info(f"Stability validation completed for {model_name}")
            return stability_analysis
            
        except Exception as e:
            self.logger.error(f"Error validating model stability: {e}")
            raise
    
    def _create_cv_strategy(self, strategy: ValidationStrategy, n_folds: int, y: np.ndarray):
        """Create cross-validation strategy"""
        if strategy == ValidationStrategy.K_FOLD:
            return KFold(n_splits=n_folds, shuffle=True, random_state=42)
        elif strategy == ValidationStrategy.STRATIFIED_K_FOLD:
            return StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
        elif strategy == ValidationStrategy.TIME_SERIES_SPLIT:
            return TimeSeriesSplit(n_splits=n_folds)
        else:
            return KFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    def _get_default_scoring_metrics(self, model_type: ModelType) -> List[str]:
        """Get default scoring metrics based on model type"""
        if model_type == ModelType.CLASSIFICATION:
            return ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']
        else:
            return ['neg_mean_squared_error', 'neg_mean_absolute_error', 'r2']
    
    def _determine_model_type(self, model: Any) -> ModelType:
        """Determine model type"""
        try:
            model_name = type(model).__name__.lower()
            if 'classifier' in model_name or 'classification' in model_name:
                return ModelType.CLASSIFICATION
            elif 'regressor' in model_name or 'regression' in model_name:
                return ModelType.REGRESSION
            else:
                return ModelType.CLASSIFICATION
        except:
            return ModelType.CLASSIFICATION
    
    def _calculate_confidence_interval(self, scores: np.ndarray, confidence_level: float) -> Tuple[float, float]:
        """Calculate confidence interval for scores"""
        try:
            alpha = 1 - confidence_level
            mean_score = np.mean(scores)
            std_error = np.std(scores) / np.sqrt(len(scores))
            
            # Use t-distribution for small samples
            from scipy import stats
            t_value = stats.t.ppf(1 - alpha/2, len(scores) - 1)
            margin_error = t_value * std_error
            
            return (mean_score - margin_error, mean_score + margin_error)
            
        except ImportError:
            # Fallback without scipy
            std_error = np.std(scores) / np.sqrt(len(scores))
            margin_error = 1.96 * std_error  # Approximate 95% CI
            mean_score = np.mean(scores)
            return (mean_score - margin_error, mean_score + margin_error)
    
    def _calculate_stability_metrics(self, scores: Dict[str, Dict[str, List[float]]]) -> Dict[str, float]:
        """Calculate stability metrics from cross-validation scores"""
        stability_metrics = {}
        
        for metric_name, score_dict in scores.items():
            test_scores = np.array(score_dict['test_scores'])
            
            # Coefficient of variation
            cv = np.std(test_scores) / np.mean(test_scores) if np.mean(test_scores) != 0 else float('inf')
            stability_metrics[f'{metric_name}_coefficient_of_variation'] = float(cv)
            
            # Stability score (inverse of CV, capped at 1)
            stability_score = min(1.0, 1.0 / (1.0 + cv)) if cv != float('inf') else 0.0
            stability_metrics[f'{metric_name}_stability_score'] = float(stability_score)
            
            # Range normalized by mean
            score_range = np.max(test_scores) - np.min(test_scores)
            normalized_range = score_range / np.mean(test_scores) if np.mean(test_scores) != 0 else float('inf')
            stability_metrics[f'{metric_name}_normalized_range'] = float(normalized_range)
        
        return stability_metrics    

    def _generate_cv_recommendations(self, scores: Dict[str, Dict[str, List[float]]],
                                   stability_metrics: Dict[str, float],
                                   mean_scores: Dict[str, float],
                                   std_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on cross-validation results"""
        recommendations = []
        
        # Check stability
        for metric_name in mean_scores.keys():
            cv_key = f'{metric_name}_coefficient_of_variation'
            if cv_key in stability_metrics:
                cv_value = stability_metrics[cv_key]
                if cv_value > self.stability_threshold:
                    recommendations.append(f"High variability in {metric_name} (CV: {cv_value:.3f}). Consider regularization or more data.")
                else:
                    recommendations.append(f"Good stability in {metric_name} (CV: {cv_value:.3f})")
        
        # Check performance levels
        for metric_name, mean_score in mean_scores.items():
            if metric_name in ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']:
                if mean_score < 0.7:
                    recommendations.append(f"Low {metric_name} ({mean_score:.3f}). Consider feature engineering or model tuning.")
                elif mean_score > 0.9:
                    recommendations.append(f"High {metric_name} ({mean_score:.3f}). Check for overfitting.")
            elif metric_name in ['r2']:
                if mean_score < 0.5:
                    recommendations.append(f"Low {metric_name} ({mean_score:.3f}). Model may not be capturing patterns well.")
        
        return recommendations
    
    def _calculate_oos_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, model_type: ModelType) -> Dict[str, float]:
        """Calculate out-of-sample performance metrics"""
        from sklearn.metrics import accuracy_score, mean_squared_error, r2_score, f1_score
        
        metrics = {}
        
        if model_type == ModelType.CLASSIFICATION:
            metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
            metrics['f1_score'] = float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
        else:
            metrics['mse'] = float(mean_squared_error(y_true, y_pred))
            metrics['rmse'] = float(np.sqrt(metrics['mse']))
            metrics['r2_score'] = float(r2_score(y_true, y_pred))
        
        return metrics
    
    def _analyze_performance_degradation(self, model: Any, X_train: np.ndarray, y_train: np.ndarray,
                                       X_test: np.ndarray, y_test: np.ndarray, model_type: ModelType) -> Dict[str, Any]:
        """Analyze performance degradation from training to test set"""
        # Training performance
        y_train_pred = model.predict(X_train)
        train_metrics = self._calculate_oos_metrics(y_train, y_train_pred, model_type)
        
        # Test performance
        y_test_pred = model.predict(X_test)
        test_metrics = self._calculate_oos_metrics(y_test, y_test_pred, model_type)
        
        # Calculate degradation
        degradation_analysis = {
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'degradation': {},
            'overall_degradation': 0.0,
            'degradation_severity': 'none'
        }
        
        total_degradation = 0.0
        metric_count = 0
        
        for metric in train_metrics.keys():
            if metric in test_metrics:
                train_val = train_metrics[metric]
                test_val = test_metrics[metric]
                
                # Calculate degradation (positive means performance dropped)
                if metric in ['mse', 'rmse']:  # Lower is better
                    degradation = (test_val - train_val) / max(train_val, 1e-8)
                else:  # Higher is better
                    degradation = (train_val - test_val) / max(train_val, 1e-8)
                
                degradation_analysis['degradation'][metric] = float(degradation)
                total_degradation += abs(degradation)
                metric_count += 1
        
        if metric_count > 0:
            degradation_analysis['overall_degradation'] = float(total_degradation / metric_count)
            
            # Determine severity
            overall_deg = degradation_analysis['overall_degradation']
            if overall_deg < 0.1:
                degradation_analysis['degradation_severity'] = 'none'
            elif overall_deg < 0.2:
                degradation_analysis['degradation_severity'] = 'mild'
            elif overall_deg < 0.3:
                degradation_analysis['degradation_severity'] = 'moderate'
            else:
                degradation_analysis['degradation_severity'] = 'severe'
        
        return degradation_analysis
    
    def _analyze_temporal_stability(self, model: Any, temporal_data: pd.DataFrame, model_type: ModelType) -> Dict[str, float]:
        """Analyze temporal stability of model performance"""
        if 'timestamp' not in temporal_data.columns or 'target' not in temporal_data.columns:
            return {'error': 'Temporal data must contain timestamp and target columns'}
        
        # Sort by timestamp
        temporal_data = temporal_data.sort_values('timestamp')
        
        # Split into time windows
        n_windows = 5
        window_size = len(temporal_data) // n_windows
        window_performances = []
        
        for i in range(n_windows):
            start_idx = i * window_size
            end_idx = (i + 1) * window_size if i < n_windows - 1 else len(temporal_data)
            
            window_data = temporal_data.iloc[start_idx:end_idx]
            X_window = window_data.drop(['timestamp', 'target'], axis=1).values
            y_window = window_data['target'].values
            
            if len(X_window) > 0:
                y_pred = model.predict(X_window)
                window_metrics = self._calculate_oos_metrics(y_window, y_pred, model_type)
                
                # Use primary metric
                primary_metric = 'accuracy' if model_type == ModelType.CLASSIFICATION else 'r2_score'
                if primary_metric in window_metrics:
                    window_performances.append(window_metrics[primary_metric])
        
        if len(window_performances) < 2:
            return {'error': 'Insufficient data for temporal analysis'}
        
        # Calculate temporal stability metrics
        temporal_stability = {
            'temporal_mean': float(np.mean(window_performances)),
            'temporal_std': float(np.std(window_performances)),
            'temporal_cv': float(np.std(window_performances) / np.mean(window_performances)) if np.mean(window_performances) != 0 else float('inf'),
            'temporal_trend': float(np.corrcoef(range(len(window_performances)), window_performances)[0, 1]) if len(window_performances) > 1 else 0.0,
            'temporal_range': float(np.max(window_performances) - np.min(window_performances)),
            'window_performances': window_performances
        }
        
        return temporal_stability
    
    def _generate_oos_recommendations(self, performance_metrics: Dict[str, float],
                                    degradation_analysis: Dict[str, Any],
                                    temporal_stability: Dict[str, float]) -> List[str]:
        """Generate recommendations based on out-of-sample testing"""
        recommendations = []
        
        # Performance recommendations
        for metric, value in performance_metrics.items():
            if metric in ['accuracy', 'f1_score'] and value < 0.7:
                recommendations.append(f"Low out-of-sample {metric} ({value:.3f}). Model may not generalize well.")
            elif metric == 'r2_score' and value < 0.5:
                recommendations.append(f"Low out-of-sample R² ({value:.3f}). Consider model improvements.")
        
        # Degradation recommendations
        severity = degradation_analysis.get('degradation_severity', 'none')
        if severity == 'severe':
            recommendations.append("Severe performance degradation detected. Model is likely overfitting.")
        elif severity == 'moderate':
            recommendations.append("Moderate performance degradation. Consider regularization techniques.")
        elif severity == 'mild':
            recommendations.append("Mild performance degradation is normal and acceptable.")
        
        # Temporal stability recommendations
        if 'temporal_cv' in temporal_stability:
            temporal_cv = temporal_stability['temporal_cv']
            if temporal_cv > 0.2:
                recommendations.append(f"High temporal instability (CV: {temporal_cv:.3f}). Model performance varies significantly over time.")
            
            temporal_trend = temporal_stability.get('temporal_trend', 0.0)
            if abs(temporal_trend) > 0.5:
                if temporal_trend > 0:
                    recommendations.append("Positive temporal trend detected. Model performance is improving over time.")
                else:
                    recommendations.append("Negative temporal trend detected. Model performance is degrading over time.")
        
        return recommendations
    
    def _perform_statistical_test(self, scores_1: List[float], scores_2: List[float], test_type: TestType) -> Dict[str, float]:
        """Perform statistical test between two sets of scores"""
        try:
            from scipy import stats
            
            if test_type == TestType.T_TEST:
                statistic, p_value = stats.ttest_ind(scores_1, scores_2)
            elif test_type == TestType.WILCOXON:
                statistic, p_value = stats.wilcoxon(scores_1, scores_2)
            elif test_type == TestType.MANN_WHITNEY:
                statistic, p_value = stats.mannwhitneyu(scores_1, scores_2)
            else:
                # Default to t-test
                statistic, p_value = stats.ttest_ind(scores_1, scores_2)
            
            return {'statistic': float(statistic), 'p_value': float(p_value)}
            
        except ImportError:
            # Fallback without scipy
            mean_1 = np.mean(scores_1)
            mean_2 = np.mean(scores_2)
            std_1 = np.std(scores_1)
            std_2 = np.std(scores_2)
            n_1 = len(scores_1)
            n_2 = len(scores_2)
            
            # Simple t-test approximation
            pooled_std = np.sqrt(((n_1 - 1) * std_1**2 + (n_2 - 1) * std_2**2) / (n_1 + n_2 - 2))
            t_stat = (mean_1 - mean_2) / (pooled_std * np.sqrt(1/n_1 + 1/n_2))
            
            # Approximate p-value (very rough)
            p_value = 2 * (1 - 0.5 * (1 + np.tanh(abs(t_stat) / 2)))
            
            return {'statistic': float(t_stat), 'p_value': float(p_value)}
    
    def _calculate_effect_size(self, scores_1: List[float], scores_2: List[float]) -> float:
        """Calculate Cohen's d effect size"""
        mean_1 = np.mean(scores_1)
        mean_2 = np.mean(scores_2)
        std_1 = np.std(scores_1)
        std_2 = np.std(scores_2)
        n_1 = len(scores_1)
        n_2 = len(scores_2)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n_1 - 1) * std_1**2 + (n_2 - 1) * std_2**2) / (n_1 + n_2 - 2))
        
        # Cohen's d
        cohens_d = (mean_1 - mean_2) / pooled_std if pooled_std > 0 else 0.0
        
        return float(abs(cohens_d))
    
    def _interpret_statistical_test(self, test_result: Dict[str, float], effect_size: float, is_significant: bool) -> str:
        """Interpret statistical test results"""
        p_value = test_result['p_value']
        
        significance_text = "statistically significant" if is_significant else "not statistically significant"
        
        # Effect size interpretation
        if effect_size < 0.2:
            effect_text = "negligible"
        elif effect_size < 0.5:
            effect_text = "small"
        elif effect_size < 0.8:
            effect_text = "medium"
        else:
            effect_text = "large"
        
        interpretation = f"The difference between models is {significance_text} (p={p_value:.4f}) with a {effect_text} effect size (d={effect_size:.3f})."
        
        return interpretation
    
    def _generate_statistical_recommendations(self, test_result: Dict[str, float], effect_size: float, is_significant: bool) -> List[str]:
        """Generate recommendations based on statistical test results"""
        recommendations = []
        
        if is_significant:
            if effect_size >= 0.5:
                recommendations.append("Significant difference with meaningful effect size. Consider using the better performing model.")
            else:
                recommendations.append("Statistically significant but small effect size. Practical significance may be limited.")
        else:
            recommendations.append("No significant difference between models. Either model can be used.")
            if effect_size >= 0.5:
                recommendations.append("Large effect size despite non-significance. Consider collecting more data.")
        
        return recommendations
    
    def _create_model_copy(self, model: Any, random_state: int = None):
        """Create a copy of the model with different random state"""
        try:
            # Try to clone the model
            from sklearn.base import clone
            model_copy = clone(model)
            
            # Set random state if possible
            if hasattr(model_copy, 'random_state'):
                model_copy.random_state = random_state
            
            return model_copy
            
        except ImportError:
            # Fallback: return original model
            return model
    
    def _init_cv_tables(self):
        """Initialize database tables for cross-validation results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Cross-validation results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cv_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    validation_strategy TEXT NOT NULL,
                    n_folds INTEGER NOT NULL,
                    mean_scores TEXT NOT NULL,
                    std_scores TEXT NOT NULL,
                    confidence_intervals TEXT NOT NULL,
                    stability_metrics TEXT NOT NULL,
                    validation_timestamp DATETIME NOT NULL,
                    recommendations TEXT
                )
            ''')
            
            # Out-of-sample results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS oos_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    test_period TEXT NOT NULL,
                    test_size REAL NOT NULL,
                    performance_metrics TEXT NOT NULL,
                    degradation_analysis TEXT NOT NULL,
                    temporal_stability TEXT NOT NULL,
                    recommendations TEXT,
                    test_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Statistical test results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistical_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_type TEXT NOT NULL,
                    models_compared TEXT NOT NULL,
                    test_statistic REAL NOT NULL,
                    p_value REAL NOT NULL,
                    effect_size REAL NOT NULL,
                    confidence_level REAL NOT NULL,
                    is_significant BOOLEAN NOT NULL,
                    interpretation TEXT NOT NULL,
                    recommendations TEXT,
                    test_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Cross-validation database tables initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing CV database tables: {e}")
    
    def _store_cv_result(self, result: CrossValidationResult):
        """Store cross-validation result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO cv_results (
                    model_name, validation_strategy, n_folds, mean_scores,
                    std_scores, confidence_intervals, stability_metrics,
                    validation_timestamp, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.model_name,
                result.validation_strategy.value,
                result.n_folds,
                json.dumps(result.mean_scores),
                json.dumps(result.std_scores),
                json.dumps({k: list(v) for k, v in result.confidence_intervals.items()}),
                json.dumps(result.stability_metrics),
                result.validation_timestamp.isoformat(),
                json.dumps(result.recommendations)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing CV result: {e}")
    
    def _store_oos_result(self, result: OutOfSampleResult):
        """Store out-of-sample result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO oos_results (
                    model_name, test_period, test_size, performance_metrics,
                    degradation_analysis, temporal_stability, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.model_name,
                result.test_period,
                result.test_size,
                json.dumps(result.performance_metrics),
                json.dumps(result.degradation_analysis),
                json.dumps(result.temporal_stability),
                json.dumps(result.recommendations)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing OOS result: {e}")
    
    def _store_statistical_test_result(self, result: StatisticalTestResult):
        """Store statistical test result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO statistical_test_results (
                    test_type, models_compared, test_statistic, p_value,
                    effect_size, confidence_level, is_significant,
                    interpretation, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.test_type.value,
                json.dumps(result.models_compared),
                result.test_statistic,
                result.p_value,
                result.effect_size,
                result.confidence_level,
                result.is_significant,
                result.interpretation,
                json.dumps(result.recommendations)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing statistical test result: {e}")


# Example usage and testing functions
def create_sample_models():
    """Create sample models for testing"""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    
    models = {
        'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'logistic_regression': LogisticRegression(random_state=42),
        'svm': SVC(random_state=42, probability=True)
    }
    
    return models


def generate_sample_data(n_samples: int = 1000, n_features: int = 10, classification: bool = True):
    """Generate sample data for testing"""
    from sklearn.datasets import make_classification, make_regression
    
    if classification:
        X, y = make_classification(
            n_samples=n_samples, n_features=n_features, n_informative=n_features//2,
            n_redundant=0, n_clusters_per_class=1, random_state=42
        )
    else:
        X, y = make_regression(
            n_samples=n_samples, n_features=n_features, noise=0.1, random_state=42
        )
    
    return X, y


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create framework
    cv_framework = CrossValidationFramework()
    
    # Generate sample data
    X, y = generate_sample_data(n_samples=500, n_features=8, classification=True)
    
    # Create sample models
    models = create_sample_models()
    
    # Test cross-validation
    for model_name, model in models.items():
        try:
            cv_result = cv_framework.perform_cross_validation(
                model, X, y, model_name, ValidationStrategy.K_FOLD, n_folds=5
            )
            print(f"\nCross-validation results for {model_name}:")
            print(f"Mean scores: {cv_result.mean_scores}")
            print(f"Stability metrics: {cv_result.stability_metrics}")
            print(f"Recommendations: {cv_result.recommendations}")
            
        except Exception as e:
            print(f"Error testing {model_name}: {e}")
    
    print("\nCross-validation framework testing completed!")