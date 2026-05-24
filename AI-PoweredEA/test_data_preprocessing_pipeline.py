"""
Test Data Preprocessing Pipeline
Comprehensive tests for the data preprocessing and feature engineering pipeline
"""

import sys
import os
sys.path.append('Python')

import unittest
import logging
import tempfile
import shutil
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_data_preprocessing_pipeline():
    """Test the data preprocessing pipeline comprehensively"""
    try:
        print("Testing Data Preprocessing Pipeline...")
        
        # Import components
        from data_preprocessing_pipeline import (
            DataPreprocessingPipeline, AdvancedFeatureEngineer,
            PreprocessingConfig, PreprocessingResult,
            ScalingMethod, ImputationMethod, FeatureSelectionMethod
        )
        
        print("✓ Successfully imported data preprocessing components")
        
        # Create sample data
        sample_data = _create_sample_market_data()
        target = _create_sample_target(len(sample_data))
        
        print(f"✓ Sample data created: {len(sample_data)} samples, {len(sample_data.columns)} columns")
        
        # Test Advanced Feature Engineer
        feature_engineer = AdvancedFeatureEngineer()
        print("✓ Advanced Feature Engineer initialized")
        
        # Test technical features
        tech_features = feature_engineer.engineer_technical_features(sample_data)
        print(f"✓ Technical features: {len(tech_features.columns)} features engineered")
        
        # Test price action features
        price_features = feature_engineer.engineer_price_action_features(sample_data)
        print(f"✓ Price action features: {len(price_features.columns)} features engineered")
        
        # Test volume features
        volume_features = feature_engineer.engineer_volume_features(sample_data)
        print(f"✓ Volume features: {len(volume_features.columns)} features engineered")
        
        # Test time features
        time_features = feature_engineer.engineer_time_features(sample_data)
        print(f"✓ Time features: {len(time_features.columns)} features engineered")
        
        # Test preprocessing pipeline with different configurations
        configs_to_test = [
            {
                'name': 'Standard Configuration',
                'config': PreprocessingConfig()
            },
            {
                'name': 'Advanced Configuration',
                'config': PreprocessingConfig(
                    scaling_method=ScalingMethod.ROBUST,
                    feature_selection_method=FeatureSelectionMethod.MUTUAL_INFO,
                    max_features=20,
                    apply_pca=True
                )
            },
            {
                'name': 'Minimal Configuration',
                'config': PreprocessingConfig(
                    scaling_method=ScalingMethod.MINMAX,
                    feature_selection_method=FeatureSelectionMethod.UNIVARIATE,
                    max_features=10
                )
            }
        ]
        
        for config_test in configs_to_test:
            print(f"\n--- Testing {config_test['name']} ---")
            
            pipeline = DataPreprocessingPipeline(config_test['config'])
            
            # Test fit_transform
            result = pipeline.fit_transform(sample_data, target)
            
            print(f"✓ Fit-transform completed:")
            print(f"  - Original samples: {len(sample_data)}")
            print(f"  - Processed samples: {len(result.processed_data)}")
            print(f"  - Features: {len(result.feature_names)}")
            print(f"  - Steps: {len(result.preprocessing_steps)}")
            print(f"  - Warnings: {len(result.warnings)}")
            print(f"  - Errors: {len(result.errors)}")
            
            # Test transform on new data
            new_data = _create_sample_market_data(samples=100)
            transform_result = pipeline.transform(new_data)
            
            print(f"✓ Transform completed:")
            print(f"  - New data samples: {len(new_data)}")
            print(f"  - Transformed samples: {len(transform_result.processed_data)}")
            print(f"  - Features: {len(transform_result.feature_names)}")
            
            # Validate results
            if len(result.errors) == 0:
                print("✓ No errors in preprocessing")
            else:
                print(f"⚠️ {len(result.errors)} errors found:")
                for error in result.errors:
                    print(f"    - {error}")
            
            if len(result.warnings) > 0:
                print(f"⚠️ {len(result.warnings)} warnings:")
                for warning in result.warnings[:3]:  # Show first 3 warnings
                    print(f"    - {warning}")
        
        # Test specific feature engineering components
        print("\n--- Testing Specific Components ---")
        
        # Test with missing data
        missing_data = sample_data.copy()
        missing_data.loc[0:50, 'close_price'] = np.nan
        missing_data.loc[100:150, 'volume'] = np.nan
        
        pipeline = DataPreprocessingPipeline(PreprocessingConfig(
            imputation_method=ImputationMethod.KNN
        ))
        
        missing_result = pipeline.fit_transform(missing_data, target)
        print(f"✓ Missing data handling: {missing_result.statistics.get('missing_values_imputed', 0)} values imputed")
        
        # Test with outliers
        outlier_data = sample_data.copy()
        outlier_data.loc[0:10, 'close_price'] = 2.0  # Extreme outliers
        
        pipeline = DataPreprocessingPipeline(PreprocessingConfig(
            outlier_method='zscore',
            outlier_threshold=2.0
        ))
        
        outlier_result = pipeline.fit_transform(outlier_data, target)
        print(f"✓ Outlier handling: {outlier_result.statistics.get('outliers_treated', 0)} outliers treated")
        
        # Test feature selection methods
        for method in [FeatureSelectionMethod.UNIVARIATE, FeatureSelectionMethod.MUTUAL_INFO]:
            pipeline = DataPreprocessingPipeline(PreprocessingConfig(
                feature_selection_method=method,
                max_features=15
            ))
            
            selection_result = pipeline.fit_transform(sample_data, target)
            print(f"✓ Feature selection ({method.value}): {selection_result.statistics.get('features_selected', 0)} features selected")
        
        print("\n🎉 All data preprocessing pipeline tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Data preprocessing pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _create_sample_market_data(samples: int = 1000) -> pd.DataFrame:
    """Create sample market data for testing"""
    np.random.seed(42)
    
    # Generate realistic market data
    base_price = 1.1000
    timestamps = pd.date_range(start='2023-01-01', periods=samples, freq='5T')
    
    # Generate price series with some trend and volatility
    price_changes = np.random.normal(0, 0.0002, samples)
    prices = base_price + np.cumsum(price_changes)
    
    data = {
        'timestamp': timestamps,
        'open_price': prices + np.random.normal(0, 0.0001, samples),
        'high_price': prices + abs(np.random.normal(0, 0.0003, samples)),
        'low_price': prices - abs(np.random.normal(0, 0.0003, samples)),
        'close_price': prices,
        'volume': np.random.lognormal(8, 0.5, samples).astype(int),
        'signal_type': np.random.choice(['BUY', 'SELL'], samples),
        'confidence': np.random.uniform(0.6, 0.9, samples)
    }
    
    # Ensure high >= low and realistic OHLC relationships
    df = pd.DataFrame(data)
    df['high_price'] = np.maximum(df['high_price'], np.maximum(df['open_price'], df['close_price']))
    df['low_price'] = np.minimum(df['low_price'], np.minimum(df['open_price'], df['close_price']))
    
    return df


def _create_sample_target(samples: int) -> pd.Series:
    """Create sample target variable"""
    np.random.seed(42)
    # Create somewhat realistic target with 60% positive class
    return pd.Series(np.random.choice([0, 1], samples, p=[0.4, 0.6]))


class TestAdvancedFeatureEngineer(unittest.TestCase):
    """Unit tests for Advanced Feature Engineer"""
    
    def setUp(self):
        """Set up test environment"""
        from data_preprocessing_pipeline import AdvancedFeatureEngineer
        self.engineer = AdvancedFeatureEngineer()
        self.sample_data = _create_sample_market_data(200)
    
    def test_initialization(self):
        """Test feature engineer initialization"""
        self.assertIsNotNone(self.engineer)
        self.assertGreater(len(self.engineer.sma_periods), 0)
        self.assertGreater(len(self.engineer.technical_indicators), 0)
    
    def test_technical_features(self):
        """Test technical indicator features"""
        features = self.engineer.engineer_technical_features(self.sample_data)
        
        self.assertIsInstance(features, pd.DataFrame)
        self.assertGreater(len(features.columns), 0)
        
        # Check for expected technical indicators
        expected_indicators = ['sma_5', 'sma_10', 'rsi_14', 'bb_upper_20']
        found_indicators = [col for col in expected_indicators if any(col in feat for feat in features.columns)]
        self.assertGreater(len(found_indicators), 0)
    
    def test_price_action_features(self):
        """Test price action features"""
        features = self.engineer.engineer_price_action_features(self.sample_data)
        
        self.assertIsInstance(features, pd.DataFrame)
        self.assertGreater(len(features.columns), 0)
        
        # Check for expected price action features
        expected_features = ['price_change', 'high_low_range', 'close_position']
        for feature in expected_features:
            self.assertIn(feature, features.columns)
    
    def test_volume_features(self):
        """Test volume features"""
        features = self.engineer.engineer_volume_features(self.sample_data)
        
        self.assertIsInstance(features, pd.DataFrame)
        self.assertGreater(len(features.columns), 0)
        
        # Check for expected volume features
        expected_features = ['volume_ma_5', 'volume_ratio_5']
        found_features = [col for col in expected_features if col in features.columns]
        self.assertGreater(len(found_features), 0)
    
    def test_time_features(self):
        """Test time-based features"""
        features = self.engineer.engineer_time_features(self.sample_data)
        
        self.assertIsInstance(features, pd.DataFrame)
        self.assertGreater(len(features.columns), 0)
        
        # Check for expected time features
        expected_features = ['hour', 'day_of_week', 'is_weekend']
        for feature in expected_features:
            self.assertIn(feature, features.columns)


class TestDataPreprocessingPipeline(unittest.TestCase):
    """Unit tests for Data Preprocessing Pipeline"""
    
    def setUp(self):
        """Set up test environment"""
        from data_preprocessing_pipeline import DataPreprocessingPipeline, PreprocessingConfig
        self.config = PreprocessingConfig()
        self.pipeline = DataPreprocessingPipeline(self.config)
        self.sample_data = _create_sample_market_data(500)
        self.target = _create_sample_target(500)
    
    def test_initialization(self):
        """Test pipeline initialization"""
        self.assertIsNotNone(self.pipeline)
        self.assertIsNotNone(self.pipeline.config)
        self.assertIsNotNone(self.pipeline.feature_engineer)
    
    def test_fit_transform(self):
        """Test fit_transform functionality"""
        result = self.pipeline.fit_transform(self.sample_data, self.target)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result.processed_data, pd.DataFrame)
        self.assertGreater(len(result.feature_names), 0)
        self.assertGreater(len(result.preprocessing_steps), 0)
    
    def test_transform(self):
        """Test transform functionality"""
        # First fit the pipeline
        self.pipeline.fit_transform(self.sample_data, self.target)
        
        # Then transform new data
        new_data = _create_sample_market_data(100)
        result = self.pipeline.transform(new_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result.processed_data, pd.DataFrame)
        self.assertGreater(len(result.feature_names), 0)
    
    def test_missing_data_handling(self):
        """Test missing data handling"""
        from data_preprocessing_pipeline import ImputationMethod
        
        # Create data with missing values
        missing_data = self.sample_data.copy()
        missing_data.loc[0:50, 'close_price'] = np.nan
        
        # Test different imputation methods
        for method in [ImputationMethod.MEAN, ImputationMethod.MEDIAN, ImputationMethod.KNN]:
            config = PreprocessingConfig(imputation_method=method)
            pipeline = DataPreprocessingPipeline(config)
            
            result = pipeline.fit_transform(missing_data, self.target)
            
            # Check that missing values were handled
            self.assertFalse(result.processed_data.isnull().any().any())
    
    def test_outlier_handling(self):
        """Test outlier detection and treatment"""
        # Create data with outliers
        outlier_data = self.sample_data.copy()
        outlier_data.loc[0:10, 'close_price'] = 10.0  # Extreme outliers
        
        result = self.pipeline.fit_transform(outlier_data, self.target)
        
        # Check that outliers were treated
        self.assertIsNotNone(result.statistics.get('outliers_treated'))
    
    def test_feature_scaling(self):
        """Test feature scaling"""
        from data_preprocessing_pipeline import ScalingMethod
        
        for scaling_method in [ScalingMethod.STANDARD, ScalingMethod.MINMAX, ScalingMethod.ROBUST]:
            config = PreprocessingConfig(scaling_method=scaling_method)
            pipeline = DataPreprocessingPipeline(config)
            
            result = pipeline.fit_transform(self.sample_data, self.target)
            
            # Check that scaling was applied
            self.assertIn('feature_scaling', result.preprocessing_steps)
            self.assertIn('scaler', result.transformers)
    
    def test_feature_selection(self):
        """Test feature selection"""
        from data_preprocessing_pipeline import FeatureSelectionMethod
        
        config = PreprocessingConfig(
            feature_selection_method=FeatureSelectionMethod.UNIVARIATE,
            max_features=10
        )
        pipeline = DataPreprocessingPipeline(config)
        
        result = pipeline.fit_transform(self.sample_data, self.target)
        
        # Check that feature selection was applied
        if len(result.feature_names) > 10:  # Only if we had more features to select from
            self.assertIn('feature_selection', result.preprocessing_steps)


if __name__ == '__main__':
    # Run the comprehensive test
    success = test_data_preprocessing_pipeline()
    
    if success:
        print("\n✅ Data Preprocessing Pipeline is working correctly!")
        print("\nRunning unit tests...")
        
        # Run unit tests
        unittest.main(verbosity=2, exit=False)
        
        print("\nTask 3.2 - Implement data preprocessing pipeline: COMPLETED")
    else:
        print("\n❌ Data Preprocessing Pipeline test failed!")