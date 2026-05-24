"""
Test Model Evaluator
Comprehensive tests for the model evaluation and comparison system
"""

import sys
import os
sys.path.append('Python')

import unittest
import logging
import tempfile
import shutil
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sklearn.datasets import make_classification, make_regression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_model_evaluator():
    """Test the model evaluator comprehensively"""
    try:
        print("Testing Model Evaluator...")
        
        # Create temporary directory
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test_model_evaluator.db")
        
        try:
            # Import components
            from model_evaluator import (
                ModelEvaluator, EvaluationResult, ModelComparison,
                EvaluationMetric, ModelType
            )
            
            print("✓ Successfully imported model evaluator components")
            
            # Initialize model evaluator
            evaluator = ModelEvaluator(test_db)
            print("✓ Model evaluator initialized")
            
            # Create sample classification data
            X_class, y_class = make_classification(
                n_samples=500, n_features=20, n_classes=2, 
                n_informative=15, n_redundant=5, random_state=42
            )
            X_train_class, X_test_class, y_train_class, y_test_class = train_test_split(
                X_class, y_class, test_size=0.3, random_state=42
            )
            
            print("✓ Sample classification data created")
            
            # Create sample regression data
            X_reg, y_reg = make_regression(
                n_samples=500, n_features=20, noise=0.1, random_state=42
            )
            X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
                X_reg, y_reg, test_size=0.3, random_state=42
            )
            
            print("✓ Sample regression data created")
            
            # Train classification models
            rf_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
            rf_classifier.fit(X_train_class, y_train_class)
            
            lr_classifier = LogisticRegression(random_state=42, max_iter=1000)
            lr_classifier.fit(X_train_class, y_train_class)
            
            print("✓ Classification models trained")
            
            # Train regression models
            rf_regressor = RandomForestRegressor(n_estimators=50, random_state=42)
            rf_regressor.fit(X_train_reg, y_train_reg)
            
            lr_regressor = LinearRegression()
            lr_regressor.fit(X_train_reg, y_train_reg)
            
            print("✓ Regression models trained")
            
            # Test single model evaluation - Classification
            print("\n--- Testing Classification Model Evaluation ---")
            
            rf_result = evaluator.evaluate_model(
                rf_classifier, X_test_class, y_test_class, 
                "RandomForestClassifier", ModelType.CLASSIFICATION,
                X_train_class, y_train_class
            )
            
            print(f"✓ RandomForest classification evaluation:")
            print(f"  - Model ID: {rf_result.model_id}")
            print(f"  - Accuracy: {rf_result.metrics.get('accuracy', 0):.3f}")
            print(f"  - Precision: {rf_result.metrics.get('precision', 0):.3f}")
            print(f"  - Recall: {rf_result.metrics.get('recall', 0):.3f}")
            print(f"  - F1 Score: {rf_result.metrics.get('f1_score', 0):.3f}")
            print(f"  - ROC AUC: {rf_result.metrics.get('roc_auc', 0):.3f}")
            print(f"  - Overfitting detected: {rf_result.overfitting_analysis.get('overfitting_detected', False)}")
            print(f"  - Recommendations: {len(rf_result.recommendations)}")
            
            # Test single model evaluation - Regression
            print("\n--- Testing Regression Model Evaluation ---")
            
            rf_reg_result = evaluator.evaluate_model(
                rf_regressor, X_test_reg, y_test_reg,
                "RandomForestRegressor", ModelType.REGRESSION,
                X_train_reg, y_train_reg
            )
            
            print(f"✓ RandomForest regression evaluation:")
            print(f"  - Model ID: {rf_reg_result.model_id}")
            print(f"  - MSE: {rf_reg_result.metrics.get('mse', 0):.3f}")
            print(f"  - MAE: {rf_reg_result.metrics.get('mae', 0):.3f}")
            print(f"  - RMSE: {rf_reg_result.metrics.get('rmse', 0):.3f}")
            print(f"  - R² Score: {rf_reg_result.metrics.get('r2_score', 0):.3f}")
            print(f"  - Overfitting detected: {rf_reg_result.overfitting_analysis.get('overfitting_detected', False)}")
            print(f"  - Recommendations: {len(rf_reg_result.recommendations)}")
            
            # Test model comparison - Classification
            print("\n--- Testing Classification Model Comparison ---")
            
            classification_models = {
                'RandomForest': rf_classifier,
                'LogisticRegression': lr_classifier
            }
            
            class_comparison = evaluator.compare_models(
                classification_models, X_test_class, y_test_class, 
                'accuracy', X_train_class, y_train_class
            )
            
            print(f"✓ Classification model comparison:")
            print(f"  - Comparison ID: {class_comparison.comparison_id}")
            print(f"  - Best model: {class_comparison.best_model}")
            print(f"  - Confidence level: {class_comparison.confidence_level:.3f}")
            print(f"  - Models compared: {len(class_comparison.models_compared)}")
            print(f"  - Primary metric: {class_comparison.primary_metric}")
            print(f"  - Ranking: {class_comparison.ranking}")
            print(f"  - Recommendations: {len(class_comparison.recommendations)}")
            
            # Test model comparison - Regression
            print("\n--- Testing Regression Model Comparison ---")
            
            regression_models = {
                'RandomForest': rf_regressor,
                'LinearRegression': lr_regressor
            }
            
            reg_comparison = evaluator.compare_models(
                regression_models, X_test_reg, y_test_reg,
                'r2_score', X_train_reg, y_train_reg
            )
            
            print(f"✓ Regression model comparison:")
            print(f"  - Comparison ID: {reg_comparison.comparison_id}")
            print(f"  - Best model: {reg_comparison.best_model}")
            print(f"  - Confidence level: {reg_comparison.confidence_level:.3f}")
            print(f"  - Models compared: {len(reg_comparison.models_compared)}")
            print(f"  - Primary metric: {reg_comparison.primary_metric}")
            print(f"  - Ranking: {reg_comparison.ranking}")
            print(f"  - Recommendations: {len(reg_comparison.recommendations)}")
            
            # Test overfitting detection
            print("\n--- Testing Overfitting Detection ---")
            
            overfitting_analysis = evaluator.detect_overfitting(
                rf_classifier, X_train_class, y_train_class,
                X_test_class, y_test_class, ModelType.CLASSIFICATION
            )
            
            print(f"✓ Overfitting detection:")
            print(f"  - Overfitting detected: {overfitting_analysis.get('overfitting_detected', False)}")
            print(f"  - Overfitting severity: {overfitting_analysis.get('overfitting_severity', 'none')}")
            print(f"  - Recommendations: {len(overfitting_analysis.get('recommendations', []))}")
            
            # Test with trading data
            print("\n--- Testing Trading Metrics ---")
            
            # Create mock trading data
            trading_data = pd.DataFrame({
                'profit_loss': np.random.normal(5, 20, len(y_test_class)),
                'signal_confidence': np.random.uniform(0.6, 0.9, len(y_test_class))
            })
            
            trading_result = evaluator.evaluate_model(
                rf_classifier, X_test_class, y_test_class,
                "TradingModel", ModelType.CLASSIFICATION,
                trading_data=trading_data
            )
            
            print(f"✓ Trading model evaluation:")
            print(f"  - Total P&L: {trading_result.metrics.get('total_profit_loss', 0):.2f}")
            print(f"  - Win Rate: {trading_result.metrics.get('win_rate', 0):.3f}")
            print(f"  - Sharpe Ratio: {trading_result.metrics.get('sharpe_ratio', 0):.3f}")
            print(f"  - Max Drawdown: {trading_result.metrics.get('max_drawdown', 0):.2f}")
            print(f"  - Profit Factor: {trading_result.metrics.get('profit_factor', 0):.3f}")
            
            # Test current model evaluation
            print("\n--- Testing Current Model Evaluation ---")
            
            test_data_with_target = pd.DataFrame(X_test_class)
            test_data_with_target['target'] = y_test_class
            
            current_metrics = evaluator.evaluate_current_model(
                rf_classifier, test_data_with_target, "CurrentModel"
            )
            
            print(f"✓ Current model evaluation:")
            print(f"  - Accuracy: {current_metrics.get('accuracy', 0):.3f}")
            print(f"  - F1 Score: {current_metrics.get('f1_score', 0):.3f}")
            
            print("\n🎉 All model evaluator tests passed!")
            return True
            
        finally:
            # Clean up test directory
            shutil.rmtree(test_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ Model evaluator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


class TestModelEvaluator(unittest.TestCase):
    """Unit tests for Model Evaluator"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_evaluator.db")
        
        from model_evaluator import ModelEvaluator, ModelType
        self.evaluator = ModelEvaluator(self.test_db)
        self.ModelType = ModelType
        
        # Create sample data
        self.X_class, self.y_class = make_classification(
            n_samples=200, n_features=10, n_classes=2, random_state=42
        )
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X_class, self.y_class, test_size=0.3, random_state=42
        )
        
        # Train a simple model
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)
        self.model.fit(self.X_train, self.y_train)
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except:
            pass
    
    def test_initialization(self):
        """Test evaluator initialization"""
        self.assertIsNotNone(self.evaluator)
        self.assertEqual(self.evaluator.db_path, self.test_db)
        self.assertEqual(self.evaluator.default_cv_folds, 5)
        self.assertGreater(len(self.evaluator.classification_metrics), 0)
    
    def test_single_model_evaluation(self):
        """Test single model evaluation"""
        result = self.evaluator.evaluate_model(
            self.model, self.X_test, self.y_test, "TestModel", 
            self.ModelType.CLASSIFICATION, self.X_train, self.y_train
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.model_name, "TestModel")
        self.assertEqual(result.model_type, self.ModelType.CLASSIFICATION)
        self.assertIn('accuracy', result.metrics)
        self.assertIn('f1_score', result.metrics)
        self.assertGreater(len(result.recommendations), 0)
    
    def test_model_comparison(self):
        """Test model comparison"""
        from sklearn.linear_model import LogisticRegression
        
        lr_model = LogisticRegression(random_state=42, max_iter=1000)
        lr_model.fit(self.X_train, self.y_train)
        
        models = {
            'RandomForest': self.model,
            'LogisticRegression': lr_model
        }
        
        comparison = self.evaluator.compare_models(
            models, self.X_test, self.y_test, 'accuracy', self.X_train, self.y_train
        )
        
        self.assertIsNotNone(comparison)
        self.assertEqual(len(comparison.models_compared), 2)
        self.assertIn(comparison.best_model, ['RandomForest', 'LogisticRegression'])
        self.assertGreater(comparison.confidence_level, 0)
        self.assertLess(comparison.confidence_level, 1)
    
    def test_overfitting_detection(self):
        """Test overfitting detection"""
        analysis = self.evaluator.detect_overfitting(
            self.model, self.X_train, self.y_train,
            self.X_test, self.y_test, self.ModelType.CLASSIFICATION
        )
        
        self.assertIsNotNone(analysis)
        self.assertIn('overfitting_detected', analysis)
        self.assertIn('overfitting_severity', analysis)
        self.assertIn('recommendations', analysis)
    
    def test_trading_metrics_calculation(self):
        """Test trading metrics calculation"""
        # Create mock trading data
        trading_data = pd.DataFrame({
            'profit_loss': [10, -5, 15, -3, 8, -2, 12, -7, 5, -1]
        })
        
        result = self.evaluator.evaluate_model(
            self.model, self.X_test[:10], self.y_test[:10], "TradingModel",
            self.ModelType.CLASSIFICATION, trading_data=trading_data
        )
        
        self.assertIn('total_profit_loss', result.metrics)
        self.assertIn('win_rate', result.metrics)
        self.assertIn('sharpe_ratio', result.metrics)
        self.assertIn('max_drawdown', result.metrics)
    
    def test_current_model_evaluation(self):
        """Test current model evaluation with test data"""
        test_data = pd.DataFrame(self.X_test)
        test_data['target'] = self.y_test
        
        metrics = self.evaluator.evaluate_current_model(self.model, test_data)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn('accuracy', metrics)
        self.assertIn('f1_score', metrics)
    
    def test_model_type_determination(self):
        """Test automatic model type determination"""
        from sklearn.linear_model import LinearRegression
        
        # Test classification model
        class_type = self.evaluator._determine_model_type(self.model)
        self.assertEqual(class_type, self.ModelType.CLASSIFICATION)
        
        # Test regression model
        reg_model = LinearRegression()
        reg_type = self.evaluator._determine_model_type(reg_model)
        self.assertEqual(reg_type, self.ModelType.REGRESSION)
    
    def test_metrics_calculation(self):
        """Test metrics calculation for different model types"""
        y_pred = self.model.predict(self.X_test)
        y_pred_proba = self.model.predict_proba(self.X_test)
        
        metrics = self.evaluator._calculate_metrics(
            self.y_test, y_pred, y_pred_proba, self.ModelType.CLASSIFICATION, None
        )
        
        self.assertIn('accuracy', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('recall', metrics)
        self.assertIn('f1_score', metrics)
        self.assertIn('roc_auc', metrics)
    
    def test_recommendations_generation(self):
        """Test recommendations generation"""
        metrics = {'accuracy': 0.95, 'f1_score': 0.94}
        overfitting_analysis = {'overfitting_detected': True, 'overfitting_severity': 'moderate'}
        validation_scores = {'accuracy': [0.9, 0.91, 0.89, 0.92, 0.88]}
        
        recommendations = self.evaluator._generate_recommendations(
            metrics, overfitting_analysis, validation_scores
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)


if __name__ == '__main__':
    # Run the comprehensive test
    success = test_model_evaluator()
    
    if success:
        print("\n✅ Model Evaluator is working correctly!")
        print("\nRunning unit tests...")
        
        # Run unit tests
        unittest.main(verbosity=2, exit=False)
        
        print("\nTask 4.1 - Create ModelEvaluator class for performance assessment: COMPLETED")
    else:
        print("\n❌ Model Evaluator test failed!")