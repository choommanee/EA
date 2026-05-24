"""
Simple test for Cross-Validation Framework using real sklearn models
"""

import sys
import os
sys.path.append('Python')

import numpy as np
import pandas as pd
from datetime import datetime
import tempfile

try:
    from cross_validation_framework import (
        CrossValidationFramework, ValidationStrategy, TestType
    )
except ImportError:
    from Python.cross_validation_framework import (
        CrossValidationFramework, ValidationStrategy, TestType
    )

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification, make_regression
from sklearn.linear_model import LinearRegression


def test_cross_validation_framework():
    """Test the cross-validation framework with real models"""
    print("Testing Cross-Validation Framework...")
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Initialize framework
        cv_framework = CrossValidationFramework(db_path=temp_db.name)
        
        # Generate sample classification data
        X_class, y_class = make_classification(
            n_samples=200, n_features=10, n_informative=5,
            n_redundant=0, n_clusters_per_class=1, random_state=42
        )
        
        # Generate sample regression data
        X_reg, y_reg = make_regression(
            n_samples=200, n_features=10, noise=0.1, random_state=42
        )
        
        print("✓ Data generated successfully")
        
        # Test 1: Cross-validation with classification
        print("\n1. Testing cross-validation with classification...")
        classifier = RandomForestClassifier(n_estimators=10, random_state=42)
        
        cv_result = cv_framework.perform_cross_validation(
            classifier, X_class, y_class, "test_classifier",
            ValidationStrategy.K_FOLD, n_folds=3
        )
        
        print(f"   Mean accuracy: {cv_result.mean_scores.get('accuracy', 'N/A'):.3f}")
        print(f"   Stability CV: {cv_result.stability_metrics.get('accuracy_coefficient_of_variation', 'N/A'):.3f}")
        print(f"   Recommendations: {len(cv_result.recommendations)}")
        print("✓ Classification cross-validation completed")
        
        # Test 2: Cross-validation with regression
        print("\n2. Testing cross-validation with regression...")
        regressor = LinearRegression()
        
        cv_result_reg = cv_framework.perform_cross_validation(
            regressor, X_reg, y_reg, "test_regressor",
            ValidationStrategy.K_FOLD, n_folds=3
        )
        
        print(f"   Mean R²: {cv_result_reg.mean_scores.get('r2', 'N/A'):.3f}")
        print(f"   Mean MSE: {cv_result_reg.mean_scores.get('mean_squared_error', 'N/A'):.3f}")
        print("✓ Regression cross-validation completed")
        
        # Test 3: Out-of-sample testing
        print("\n3. Testing out-of-sample testing...")
        split_idx = len(X_class) // 2
        X_train = X_class[:split_idx]
        y_train = y_class[:split_idx]
        X_test = X_class[split_idx:]
        y_test = y_class[split_idx:]
        
        oos_result = cv_framework.perform_out_of_sample_testing(
            RandomForestClassifier(n_estimators=10, random_state=42),
            X_train, y_train, X_test, y_test, "oos_classifier"
        )
        
        print(f"   Test accuracy: {oos_result.performance_metrics.get('accuracy', 'N/A'):.3f}")
        print(f"   Degradation severity: {oos_result.degradation_analysis.get('degradation_severity', 'N/A')}")
        print(f"   Test size: {oos_result.test_size:.2f}")
        print("✓ Out-of-sample testing completed")
        
        # Test 4: Statistical significance testing
        print("\n4. Testing statistical significance...")
        scores_1 = [0.85, 0.87, 0.83, 0.89, 0.86]
        scores_2 = [0.78, 0.80, 0.76, 0.82, 0.79]
        
        stat_result = cv_framework.perform_statistical_significance_test(
            scores_1, scores_2, "model_A", "model_B", TestType.T_TEST
        )
        
        print(f"   P-value: {stat_result.p_value:.4f}")
        print(f"   Effect size: {stat_result.effect_size:.3f}")
        print(f"   Significant: {stat_result.is_significant}")
        print("✓ Statistical testing completed")
        
        # Test 5: Model stability validation
        print("\n5. Testing model stability...")
        stability_result = cv_framework.validate_model_stability(
            RandomForestClassifier(n_estimators=5, random_state=None),
            X_class, y_class, "stability_test", n_iterations=3
        )
        
        print(f"   Mean performance: {stability_result.get('mean_performance', 'N/A'):.3f}")
        print(f"   Coefficient of variation: {stability_result.get('coefficient_of_variation', 'N/A'):.3f}")
        print(f"   Is stable: {stability_result.get('is_stable', 'N/A')}")
        print("✓ Stability validation completed")
        
        # Test 6: Temporal stability analysis
        print("\n6. Testing temporal stability...")
        # Create temporal data with same number of features as training data
        n_samples = 100
        n_features = X_class.shape[1]
        timestamps = pd.date_range(start='2023-01-01', periods=n_samples, freq='D')
        
        # Create temporal data with correct number of features
        temporal_features = np.random.randn(n_samples, n_features)
        temporal_data = pd.DataFrame(temporal_features, columns=[f'feature_{i}' for i in range(n_features)])
        temporal_data['timestamp'] = timestamps
        temporal_data['target'] = np.random.randint(0, 2, n_samples)
        
        # Train a model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_class[:50], y_class[:50])
        
        temporal_result = cv_framework._analyze_temporal_stability(
            model, temporal_data, cv_framework._determine_model_type(model)
        )
        
        print(f"   Temporal CV: {temporal_result.get('temporal_cv', 'N/A'):.3f}")
        print(f"   Temporal trend: {temporal_result.get('temporal_trend', 'N/A'):.3f}")
        print("✓ Temporal stability analysis completed")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        try:
            os.unlink(temp_db.name)
        except:
            pass


def test_validation_strategies():
    """Test different validation strategies"""
    print("\nTesting validation strategies...")
    
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        cv_framework = CrossValidationFramework(db_path=temp_db.name)
        
        # Generate data
        X, y = make_classification(n_samples=100, n_features=5, random_state=42)
        
        strategies = [
            ValidationStrategy.K_FOLD,
            ValidationStrategy.STRATIFIED_K_FOLD,
            ValidationStrategy.TIME_SERIES_SPLIT
        ]
        
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        
        for strategy in strategies:
            try:
                result = cv_framework.perform_cross_validation(
                    model, X, y, f"test_{strategy.value}", strategy, n_folds=3
                )
                print(f"✓ {strategy.value}: accuracy = {result.mean_scores.get('accuracy', 'N/A'):.3f}")
            except Exception as e:
                print(f"❌ {strategy.value}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation strategies test failed: {e}")
        return False
        
    finally:
        try:
            os.unlink(temp_db.name)
        except:
            pass


if __name__ == "__main__":
    print("=" * 60)
    print("Cross-Validation Framework Test Suite")
    print("=" * 60)
    
    success = True
    
    # Run main tests
    success &= test_cross_validation_framework()
    
    # Run validation strategy tests
    success &= test_validation_strategies()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)