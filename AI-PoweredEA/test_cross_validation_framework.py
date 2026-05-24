"""
Test suite for Cross-Validation Framework
Comprehensive tests for cross-validation, out-of-sample testing, and statistical analysis
"""

import sys
import os
sys.path.append('Python')

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import tempfile
import sqlite3
from unittest.mock import Mock, patch

try:
    from cross_validation_framework import (
        CrossValidationFramework, ValidationStrategy, TestType,
        CrossValidationResult, OutOfSampleResult, StatisticalTestResult
    )
    from model_evaluator import ModelType
except ImportError:
    from Python.cross_validation_framework import (
        CrossValidationFramework, ValidationStrategy, TestType,
        CrossValidationResult, OutOfSampleResult, StatisticalTestResult
    )
    from Python.model_evaluator import ModelType


class TestCrossValidationFramework(unittest.TestCase):
    """Test cases for CrossValidationFramework"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize framework
        self.cv_framework = CrossValidationFramework(db_path=self.temp_db.name)
        
        # Create sample data
        self.X_classification, self.y_classification = self._create_classification_data()
        self.X_regression, self.y_regression = self._create_regression_data()
        
        # Create mock models
        self.mock_classifier = self._create_mock_classifier()
        self.mock_regressor = self._create_mock_regressor()
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_classification_data(self):
        """Create sample classification data"""
        np.random.seed(42)
        n_samples = 200
        n_features = 5
        
        X = np.random.randn(n_samples, n_features)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        
        return X, y
    
    def _create_regression_data(self):
        """Create sample regression data"""
        np.random.seed(42)
        n_samples = 200
        n_features = 5
        
        X = np.random.randn(n_samples, n_features)
        y = X[:, 0] + 2 * X[:, 1] + np.random.randn(n_samples) * 0.1
        
        return X, y
    
    def _create_mock_classifier(self):
        """Create mock classifier"""
        mock_model = Mock()
        mock_model.fit = Mock(return_value=mock_model)
        mock_model.predict = Mock(return_value=np.random.randint(0, 2, 50))
        mock_model.predict_proba = Mock(return_value=np.random.rand(50, 2))
        mock_model.__class__.__name__ = 'MockClassifier'
        return mock_model
    
    def _create_mock_regressor(self):
        """Create mock regressor"""
        mock_model = Mock()
        mock_model.fit = Mock(return_value=mock_model)
        mock_model.predict = Mock(return_value=np.random.randn(50))
        mock_model.__class__.__name__ = 'MockRegressor'
        return mock_model
    
    def test_initialization(self):
        """Test framework initialization"""
        self.assertIsInstance(self.cv_framework, CrossValidationFramework)
        self.assertEqual(self.cv_framework.default_cv_folds, 5)
        self.assertEqual(self.cv_framework.confidence_level, 0.95)
        self.assertEqual(self.cv_framework.significance_threshold, 0.05)
        
        # Check database tables were created
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['cv_results', 'oos_results', 'statistical_test_results']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    @patch('sklearn.model_selection.cross_validate')
    def test_perform_cross_validation_classification(self, mock_cross_validate):
        """Test cross-validation for classification models"""
        # Mock cross_validate results
        mock_cross_validate.return_value = {
            'test_accuracy': np.array([0.8, 0.85, 0.82, 0.88, 0.83]),
            'train_accuracy': np.array([0.9, 0.92, 0.91, 0.93, 0.89]),
            'test_f1_weighted': np.array([0.79, 0.84, 0.81, 0.87, 0.82]),
            'train_f1_weighted': np.array([0.89, 0.91, 0.90, 0.92, 0.88])
        }
        
        result = self.cv_framework.perform_cross_validation(
            self.mock_classifier, self.X_classification, self.y_classification,
            "test_classifier", ValidationStrategy.K_FOLD, n_folds=5
        )
        
        # Verify result structure
        self.assertIsInstance(result, CrossValidationResult)
        self.assertEqual(result.model_name, "test_classifier")
        self.assertEqual(result.validation_strategy, ValidationStrategy.K_FOLD)
        self.assertEqual(result.n_folds, 5)
        
        # Verify scores
        self.assertIn('accuracy', result.mean_scores)
        self.assertIn('f1_weighted', result.mean_scores)
        self.assertAlmostEqual(result.mean_scores['accuracy'], 0.836, places=2)
        
        # Verify stability metrics
        self.assertIn('accuracy_coefficient_of_variation', result.stability_metrics)
        self.assertIn('accuracy_stability_score', result.stability_metrics)
        
        # Verify confidence intervals
        self.assertIn('accuracy', result.confidence_intervals)
        self.assertEqual(len(result.confidence_intervals['accuracy']), 2)
        
        # Verify recommendations
        self.assertIsInstance(result.recommendations, list)
    
    @patch('sklearn.model_selection.cross_validate')
    def test_perform_cross_validation_regression(self, mock_cross_validate):
        """Test cross-validation for regression models"""
        # Mock cross_validate results
        mock_cross_validate.return_value = {
            'test_neg_mean_squared_error': np.array([-0.1, -0.12, -0.11, -0.09, -0.13]),
            'train_neg_mean_squared_error': np.array([-0.05, -0.06, -0.055, -0.045, -0.065]),
            'test_r2': np.array([0.85, 0.82, 0.84, 0.87, 0.81]),
            'train_r2': np.array([0.92, 0.91, 0.93, 0.94, 0.90])
        }
        
        result = self.cv_framework.perform_cross_validation(
            self.mock_regressor, self.X_regression, self.y_regression,
            "test_regressor", ValidationStrategy.K_FOLD, n_folds=5
        )
        
        # Verify result structure
        self.assertIsInstance(result, CrossValidationResult)
        self.assertEqual(result.model_name, "test_regressor")
        
        # Verify scores (negative scores should be converted to positive)
        self.assertIn('mean_squared_error', result.mean_scores)
        self.assertIn('r2', result.mean_scores)
        self.assertGreater(result.mean_scores['mean_squared_error'], 0)  # Should be positive
        
        # Verify stability metrics
        self.assertIn('mean_squared_error_coefficient_of_variation', result.stability_metrics)
        self.assertIn('r2_stability_score', result.stability_metrics)
    
    def test_perform_out_of_sample_testing(self):
        """Test out-of-sample testing functionality"""
        # Split data
        split_idx = len(self.X_classification) // 2
        X_train = self.X_classification[:split_idx]
        y_train = self.y_classification[:split_idx]
        X_test = self.X_classification[split_idx:]
        y_test = self.y_classification[split_idx:]
        
        # Configure mock predictions
        self.mock_classifier.predict.side_effect = [
            np.random.randint(0, 2, len(y_train)),  # Training predictions
            np.random.randint(0, 2, len(y_test))    # Test predictions
        ]
        
        result = self.cv_framework.perform_out_of_sample_testing(
            self.mock_classifier, X_train, y_train, X_test, y_test,
            "test_oos_classifier", "recent"
        )
        
        # Verify result structure
        self.assertIsInstance(result, OutOfSampleResult)
        self.assertEqual(result.model_name, "test_oos_classifier")
        self.assertEqual(result.test_period, "recent")
        self.assertGreater(result.test_size, 0)
        self.assertLess(result.test_size, 1)
        
        # Verify performance metrics
        self.assertIn('accuracy', result.performance_metrics)
        self.assertIn('f1_score', result.performance_metrics)
        
        # Verify degradation analysis
        self.assertIn('train_metrics', result.degradation_analysis)
        self.assertIn('test_metrics', result.degradation_analysis)
        self.assertIn('degradation', result.degradation_analysis)
        self.assertIn('degradation_severity', result.degradation_analysis)
        
        # Verify recommendations
        self.assertIsInstance(result.recommendations, list)
    
    def test_perform_statistical_significance_test(self):
        """Test statistical significance testing"""
        # Create sample scores
        scores_1 = [0.8, 0.82, 0.85, 0.83, 0.81]
        scores_2 = [0.75, 0.77, 0.79, 0.76, 0.78]
        
        result = self.cv_framework.perform_statistical_significance_test(
            scores_1, scores_2, "model_1", "model_2", TestType.T_TEST
        )
        
        # Verify result structure
        self.assertIsInstance(result, StatisticalTestResult)
        self.assertEqual(result.test_type, TestType.T_TEST)
        self.assertEqual(result.models_compared, ["model_1", "model_2"])
        
        # Verify statistical measures
        self.assertIsInstance(result.test_statistic, float)
        self.assertIsInstance(result.p_value, float)
        self.assertIsInstance(result.effect_size, float)
        self.assertIsInstance(result.is_significant, bool)
        
        # Verify interpretation and recommendations
        self.assertIsInstance(result.interpretation, str)
        self.assertIsInstance(result.recommendations, list)
        
        # P-value should be between 0 and 1
        self.assertGreaterEqual(result.p_value, 0)
        self.assertLessEqual(result.p_value, 1)
        
        # Effect size should be non-negative
        self.assertGreaterEqual(result.effect_size, 0)
    
    def test_validate_model_stability(self):
        """Test model stability validation"""
        # Configure mock for multiple iterations
        def mock_cross_validate_side_effect(*args, **kwargs):
            # Return slightly different results for each iteration
            base_score = 0.8
            variation = np.random.normal(0, 0.02)
            return {
                'test_accuracy': np.array([base_score + variation] * 3),
                'train_accuracy': np.array([base_score + 0.1 + variation] * 3)
            }
        
        with patch('sklearn.model_selection.cross_validate', side_effect=mock_cross_validate_side_effect):
            result = self.cv_framework.validate_model_stability(
                self.mock_classifier, self.X_classification, self.y_classification,
                "stability_test", n_iterations=5
            )
        
        # Verify result structure
        self.assertIn('n_iterations', result)
        self.assertIn('mean_performance', result)
        self.assertIn('std_performance', result)
        self.assertIn('coefficient_of_variation', result)
        self.assertIn('is_stable', result)
        self.assertIn('recommendations', result)
        
        # Verify data types
        self.assertIsInstance(result['n_iterations'], int)
        self.assertIsInstance(result['mean_performance'], float)
        self.assertIsInstance(result['std_performance'], float)
        self.assertIsInstance(result['is_stable'], bool)
        self.assertIsInstance(result['recommendations'], list)
        
        # Verify reasonable values
        self.assertGreater(result['n_iterations'], 0)
        self.assertGreaterEqual(result['mean_performance'], 0)
        self.assertGreaterEqual(result['std_performance'], 0)
    
    def test_confidence_interval_calculation(self):
        """Test confidence interval calculation"""
        scores = np.array([0.8, 0.82, 0.85, 0.83, 0.81])
        
        ci_lower, ci_upper = self.cv_framework._calculate_confidence_interval(scores, 0.95)
        
        # Verify confidence interval structure
        self.assertIsInstance(ci_lower, float)
        self.assertIsInstance(ci_upper, float)
        self.assertLess(ci_lower, ci_upper)
        
        # Mean should be within confidence interval
        mean_score = np.mean(scores)
        self.assertGreaterEqual(mean_score, ci_lower)
        self.assertLessEqual(mean_score, ci_upper)
    
    def test_stability_metrics_calculation(self):
        """Test stability metrics calculation"""
        scores = {
            'accuracy': {
                'test_scores': [0.8, 0.82, 0.85, 0.83, 0.81],
                'train_scores': [0.9, 0.92, 0.95, 0.93, 0.91]
            }
        }
        
        stability_metrics = self.cv_framework._calculate_stability_metrics(scores)
        
        # Verify metrics structure
        self.assertIn('accuracy_coefficient_of_variation', stability_metrics)
        self.assertIn('accuracy_stability_score', stability_metrics)
        self.assertIn('accuracy_normalized_range', stability_metrics)
        
        # Verify data types
        for metric_value in stability_metrics.values():
            self.assertIsInstance(metric_value, float)
        
        # Verify reasonable values
        cv = stability_metrics['accuracy_coefficient_of_variation']
        stability_score = stability_metrics['accuracy_stability_score']
        
        self.assertGreaterEqual(cv, 0)
        self.assertGreaterEqual(stability_score, 0)
        self.assertLessEqual(stability_score, 1)
    
    def test_effect_size_calculation(self):
        """Test effect size calculation"""
        scores_1 = [0.8, 0.82, 0.85, 0.83, 0.81]
        scores_2 = [0.75, 0.77, 0.79, 0.76, 0.78]
        
        effect_size = self.cv_framework._calculate_effect_size(scores_1, scores_2)
        
        # Verify effect size
        self.assertIsInstance(effect_size, float)
        self.assertGreaterEqual(effect_size, 0)
        
        # Test with identical scores (should be 0)
        effect_size_zero = self.cv_framework._calculate_effect_size(scores_1, scores_1)
        self.assertAlmostEqual(effect_size_zero, 0, places=5)
    
    def test_temporal_stability_analysis(self):
        """Test temporal stability analysis"""
        # Create temporal data
        n_samples = 100
        timestamps = pd.date_range(start='2023-01-01', periods=n_samples, freq='D')
        
        temporal_data = pd.DataFrame({
            'timestamp': timestamps,
            'feature_1': np.random.randn(n_samples),
            'feature_2': np.random.randn(n_samples),
            'target': np.random.randint(0, 2, n_samples)
        })
        
        # Configure mock predictions
        self.mock_classifier.predict.return_value = np.random.randint(0, 2, 20)
        
        stability_result = self.cv_framework._analyze_temporal_stability(
            self.mock_classifier, temporal_data, ModelType.CLASSIFICATION
        )
        
        # Verify result structure
        self.assertIn('temporal_mean', stability_result)
        self.assertIn('temporal_std', stability_result)
        self.assertIn('temporal_cv', stability_result)
        self.assertIn('temporal_trend', stability_result)
        self.assertIn('window_performances', stability_result)
        
        # Verify data types
        for key, value in stability_result.items():
            if key != 'window_performances':
                self.assertIsInstance(value, float)
        
        self.assertIsInstance(stability_result['window_performances'], list)
    
    def test_database_storage(self):
        """Test database storage functionality"""
        # Create sample results
        cv_result = CrossValidationResult(
            model_name="test_model",
            validation_strategy=ValidationStrategy.K_FOLD,
            n_folds=5,
            scores={'accuracy': {'test_scores': [0.8, 0.82], 'train_scores': [0.9, 0.92]}},
            mean_scores={'accuracy': 0.81},
            std_scores={'accuracy': 0.01},
            confidence_intervals={'accuracy': (0.79, 0.83)},
            stability_metrics={'accuracy_cv': 0.012},
            validation_timestamp=datetime.now(),
            recommendations=["Good performance"]
        )
        
        # Store result
        self.cv_framework._store_cv_result(cv_result)
        
        # Verify storage
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cv_results")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
        cursor.execute("SELECT model_name, validation_strategy FROM cv_results")
        row = cursor.fetchone()
        self.assertEqual(row[0], "test_model")
        self.assertEqual(row[1], "k_fold")
        
        conn.close()
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with invalid data
        with self.assertRaises(Exception):
            self.cv_framework.perform_cross_validation(
                None, self.X_classification, self.y_classification, "invalid_model"
            )
        
        # Test with empty data
        with self.assertRaises(Exception):
            self.cv_framework.perform_cross_validation(
                self.mock_classifier, np.array([]), np.array([]), "empty_data"
            )
        
        # Test statistical test with insufficient data
        with self.assertRaises(Exception):
            self.cv_framework.perform_statistical_significance_test(
                [], [0.8], "model1", "model2"
            )


class TestValidationStrategies(unittest.TestCase):
    """Test different validation strategies"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.cv_framework = CrossValidationFramework(db_path=self.temp_db.name)
        
        # Create sample data
        np.random.seed(42)
        self.X = np.random.randn(100, 5)
        self.y = np.random.randint(0, 3, 100)  # Multi-class
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_k_fold_strategy(self):
        """Test K-Fold validation strategy"""
        cv_strategy = self.cv_framework._create_cv_strategy(
            ValidationStrategy.K_FOLD, 5, self.y
        )
        
        # Verify strategy type
        from sklearn.model_selection import KFold
        self.assertIsInstance(cv_strategy, KFold)
        self.assertEqual(cv_strategy.n_splits, 5)
    
    def test_stratified_k_fold_strategy(self):
        """Test Stratified K-Fold validation strategy"""
        cv_strategy = self.cv_framework._create_cv_strategy(
            ValidationStrategy.STRATIFIED_K_FOLD, 5, self.y
        )
        
        # Verify strategy type
        from sklearn.model_selection import StratifiedKFold
        self.assertIsInstance(cv_strategy, StratifiedKFold)
        self.assertEqual(cv_strategy.n_splits, 5)
    
    def test_time_series_split_strategy(self):
        """Test Time Series Split validation strategy"""
        cv_strategy = self.cv_framework._create_cv_strategy(
            ValidationStrategy.TIME_SERIES_SPLIT, 5, self.y
        )
        
        # Verify strategy type
        from sklearn.model_selection import TimeSeriesSplit
        self.assertIsInstance(cv_strategy, TimeSeriesSplit)
        self.assertEqual(cv_strategy.n_splits, 5)


if __name__ == '__main__':
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)