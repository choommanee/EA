"""
Data Preprocessing Pipeline for AI Continuous Learning System
Advanced feature engineering, data cleaning, and validation pipeline
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
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, PowerTransformer,
    QuantileTransformer, LabelEncoder, OneHotEncoder
)
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.feature_selection import (
    SelectKBest, f_classif, mutual_info_classif, RFE, SelectFromModel
)
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')


class PreprocessingStep(Enum):
    """Preprocessing step types"""
    CLEANING = "cleaning"
    IMPUTATION = "imputation"
    SCALING = "scaling"
    ENCODING = "encoding"
    FEATURE_SELECTION = "feature_selection"
    DIMENSIONALITY_REDUCTION = "dimensionality_reduction"
    VALIDATION = "validation"


class ImputationMethod(Enum):
    """Imputation methods"""
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    CONSTANT = "constant"
    KNN = "knn"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"


class ScalingMethod(Enum):
    """Scaling methods"""
    STANDARD = "standard"
    MINMAX = "minmax"
    ROBUST = "robust"
    QUANTILE_UNIFORM = "quantile_uniform"
    QUANTILE_NORMAL = "quantile_normal"
    POWER = "power"


class FeatureSelectionMethod(Enum):
    """Feature selection methods"""
    UNIVARIATE = "univariate"
    MUTUAL_INFO = "mutual_info"
    RFE = "rfe"
    MODEL_BASED = "model_based"
    VARIANCE_THRESHOLD = "variance_threshold"


@dataclass
class PreprocessingConfig:
    """Configuration for preprocessing pipeline"""
    # Cleaning parameters
    remove_duplicates: bool = True
    outlier_method: str = "iqr"  # 'iqr', 'zscore', 'isolation_forest'
    outlier_threshold: float = 3.0
    
    # Imputation parameters
    imputation_method: ImputationMethod = ImputationMethod.MEDIAN
    knn_neighbors: int = 5
    
    # Scaling parameters
    scaling_method: ScalingMethod = ScalingMethod.STANDARD
    
    # Feature selection parameters
    feature_selection_method: FeatureSelectionMethod = FeatureSelectionMethod.UNIVARIATE
    max_features: int = 50
    feature_selection_threshold: float = 0.01
    
    # Dimensionality reduction parameters
    apply_pca: bool = False
    pca_variance_threshold: float = 0.95
    
    # Validation parameters
    min_samples: int = 100
    max_missing_ratio: float = 0.3
    min_variance: float = 1e-6


@dataclass
class PreprocessingResult:
    """Result of preprocessing pipeline"""
    processed_data: pd.DataFrame
    feature_names: List[str]
    preprocessing_steps: List[str]
    transformers: Dict[str, Any]
    statistics: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class AdvancedFeatureEngineer:
    """Advanced feature engineering for market data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Technical indicator parameters
        self.sma_periods = [5, 10, 20, 50, 100, 200]
        self.ema_periods = [12, 26, 50]
        self.rsi_periods = [14, 21]
        self.bb_periods = [20]
        self.macd_params = [(12, 26, 9)]
        
        # Price action parameters
        self.price_change_periods = [1, 3, 5, 10]
        self.volatility_periods = [10, 20, 50]
        
    def engineer_technical_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer technical indicator features"""
        try:
            features = pd.DataFrame(index=data.index)
            
            if 'close_price' not in data.columns:
                self.logger.warning("No close_price column found for technical indicators")
                return features
            
            close_prices = data['close_price']
            
            # Simple Moving Averages
            for period in self.sma_periods:
                if len(data) >= period:
                    sma = close_prices.rolling(window=period).mean()
                    features[f'sma_{period}'] = sma
                    features[f'price_sma_ratio_{period}'] = close_prices / sma
                    features[f'sma_slope_{period}'] = sma.diff(5)
            
            # Exponential Moving Averages
            for period in self.ema_periods:
                if len(data) >= period:
                    ema = close_prices.ewm(span=period).mean()
                    features[f'ema_{period}'] = ema
                    features[f'price_ema_ratio_{period}'] = close_prices / ema
            
            # RSI (Relative Strength Index)
            for period in self.rsi_periods:
                if len(data) >= period:
                    rsi = self._calculate_rsi(close_prices, period)
                    features[f'rsi_{period}'] = rsi
                    features[f'rsi_oversold_{period}'] = (rsi < 30).astype(int)
                    features[f'rsi_overbought_{period}'] = (rsi > 70).astype(int)
            
            # Bollinger Bands
            for period in self.bb_periods:
                if len(data) >= period:
                    bb_upper, bb_lower, bb_middle = self._calculate_bollinger_bands(close_prices, period)
                    features[f'bb_upper_{period}'] = bb_upper
                    features[f'bb_lower_{period}'] = bb_lower
                    features[f'bb_middle_{period}'] = bb_middle
                    features[f'bb_width_{period}'] = (bb_upper - bb_lower) / bb_middle
                    features[f'bb_position_{period}'] = (close_prices - bb_lower) / (bb_upper - bb_lower)
            
            # MACD
            for fast, slow, signal in self.macd_params:
                if len(data) >= slow:
                    macd_line, macd_signal, macd_histogram = self._calculate_macd(close_prices, fast, slow, signal)
                    features[f'macd_{fast}_{slow}'] = macd_line
                    features[f'macd_signal_{fast}_{slow}_{signal}'] = macd_signal
                    features[f'macd_histogram_{fast}_{slow}_{signal}'] = macd_histogram
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error engineering technical features: {e}")
            return pd.DataFrame(index=data.index)
    
    def engineer_price_action_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer price action features"""
        try:
            features = pd.DataFrame(index=data.index)
            
            required_cols = ['open_price', 'high_price', 'low_price', 'close_price']
            if not all(col in data.columns for col in required_cols):
                self.logger.warning("Missing OHLC columns for price action features")
                return features
            
            open_prices = data['open_price']
            high_prices = data['high_price']
            low_prices = data['low_price']
            close_prices = data['close_price']
            
            # Basic price features
            features['price_change'] = close_prices - open_prices
            features['price_change_pct'] = (close_prices - open_prices) / open_prices
            features['high_low_range'] = high_prices - low_prices
            features['high_low_range_pct'] = (high_prices - low_prices) / close_prices
            
            # Price position within range
            features['close_position'] = (close_prices - low_prices) / (high_prices - low_prices)
            features['open_position'] = (open_prices - low_prices) / (high_prices - low_prices)
            
            # Candlestick patterns (simplified)
            body_size = abs(close_prices - open_prices)
            upper_shadow = high_prices - np.maximum(open_prices, close_prices)
            lower_shadow = np.minimum(open_prices, close_prices) - low_prices
            
            features['body_size'] = body_size
            features['upper_shadow'] = upper_shadow
            features['lower_shadow'] = lower_shadow
            features['body_shadow_ratio'] = body_size / (upper_shadow + lower_shadow + 1e-8)
            
            # Price changes over different periods
            for period in self.price_change_periods:
                if len(data) >= period:
                    features[f'price_change_{period}d'] = close_prices.pct_change(period)
                    features[f'high_change_{period}d'] = high_prices.pct_change(period)
                    features[f'low_change_{period}d'] = low_prices.pct_change(period)
            
            # Volatility measures
            for period in self.volatility_periods:
                if len(data) >= period:
                    returns = close_prices.pct_change()
                    features[f'volatility_{period}d'] = returns.rolling(window=period).std()
                    features[f'volatility_ratio_{period}d'] = features[f'volatility_{period}d'] / features[f'volatility_{period}d'].rolling(window=period*2).mean()
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error engineering price action features: {e}")
            return pd.DataFrame(index=data.index)
    
    def engineer_volume_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer volume-based features"""
        try:
            features = pd.DataFrame(index=data.index)
            
            if 'volume' not in data.columns:
                self.logger.warning("No volume column found for volume features")
                return features
            
            volume = data['volume']
            close_prices = data.get('close_price', pd.Series(index=data.index))
            
            # Volume moving averages
            for period in [5, 10, 20, 50]:
                if len(data) >= period:
                    vol_ma = volume.rolling(window=period).mean()
                    features[f'volume_ma_{period}'] = vol_ma
                    features[f'volume_ratio_{period}'] = volume / vol_ma
            
            # Volume-price relationships
            if not close_prices.empty:
                price_change = close_prices.pct_change()
                features['volume_price_trend'] = volume * np.sign(price_change)
                features['volume_weighted_price'] = close_prices * volume
            
            # Volume patterns
            features['volume_spike'] = (volume > volume.rolling(window=20).mean() + 2 * volume.rolling(window=20).std()).astype(int)
            features['volume_dry_up'] = (volume < volume.rolling(window=20).mean() - volume.rolling(window=20).std()).astype(int)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error engineering volume features: {e}")
            return pd.DataFrame(index=data.index)
    
    def engineer_time_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer time-based features"""
        try:
            features = pd.DataFrame(index=data.index)
            
            if 'timestamp' not in data.columns:
                self.logger.warning("No timestamp column found for time features")
                return features
            
            timestamps = pd.to_datetime(data['timestamp'])
            
            # Basic time features
            features['hour'] = timestamps.dt.hour
            features['day_of_week'] = timestamps.dt.dayofweek
            features['day_of_month'] = timestamps.dt.day
            features['month'] = timestamps.dt.month
            features['quarter'] = timestamps.dt.quarter
            
            # Market session features (assuming forex market)
            features['is_asian_session'] = ((timestamps.dt.hour >= 0) & (timestamps.dt.hour < 8)).astype(int)
            features['is_european_session'] = ((timestamps.dt.hour >= 8) & (timestamps.dt.hour < 16)).astype(int)
            features['is_american_session'] = ((timestamps.dt.hour >= 16) & (timestamps.dt.hour < 24)).astype(int)
            
            # Weekend/weekday
            features['is_weekend'] = (timestamps.dt.dayofweek >= 5).astype(int)
            features['is_monday'] = (timestamps.dt.dayofweek == 0).astype(int)
            features['is_friday'] = (timestamps.dt.dayofweek == 4).astype(int)
            
            # Cyclical encoding for time features
            features['hour_sin'] = np.sin(2 * np.pi * timestamps.dt.hour / 24)
            features['hour_cos'] = np.cos(2 * np.pi * timestamps.dt.hour / 24)
            features['day_sin'] = np.sin(2 * np.pi * timestamps.dt.dayofweek / 7)
            features['day_cos'] = np.cos(2 * np.pi * timestamps.dt.dayofweek / 7)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error engineering time features: {e}")
            return pd.DataFrame(index=data.index)
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            return pd.Series(index=prices.index)
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        try:
            middle = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return upper, lower, middle
            
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return pd.Series(index=prices.index), pd.Series(index=prices.index), pd.Series(index=prices.index)
    
    def _calculate_macd(self, prices: pd.Series, fast: int, slow: int, signal: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            
            macd_line = ema_fast - ema_slow
            macd_signal = macd_line.ewm(span=signal).mean()
            macd_histogram = macd_line - macd_signal
            
            return macd_line, macd_signal, macd_histogram
            
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            return pd.Series(index=prices.index), pd.Series(index=prices.index), pd.Series(index=prices.index)


class DataPreprocessingPipeline:
    """Comprehensive data preprocessing pipeline"""
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or PreprocessingConfig()
        
        # Initialize feature engineer
        self.feature_engineer = AdvancedFeatureEngineer()
        
        # Initialize transformers
        self.transformers = {}
        self.fitted_transformers = {}
        
        # Statistics tracking
        self.preprocessing_stats = {}
        
        self.logger.info("Data Preprocessing Pipeline initialized")
    
    def fit_transform(self, data: pd.DataFrame, target: Optional[pd.Series] = None) -> PreprocessingResult:
        """Fit and transform data through the complete preprocessing pipeline"""
        try:
            self.logger.info(f"Starting preprocessing pipeline on {len(data)} samples")
            
            result = PreprocessingResult(
                processed_data=data.copy(),
                feature_names=[],
                preprocessing_steps=[],
                transformers={},
                statistics={}
            )
            
            # Step 1: Feature Engineering
            result = self._apply_feature_engineering(result)
            
            # Step 2: Data Cleaning
            result = self._apply_data_cleaning(result)
            
            # Step 3: Handle Missing Values
            result = self._apply_imputation(result)
            
            # Step 4: Outlier Detection and Treatment
            result = self._apply_outlier_treatment(result)
            
            # Step 5: Feature Encoding
            result = self._apply_feature_encoding(result)
            
            # Step 6: Feature Scaling
            result = self._apply_feature_scaling(result)
            
            # Step 7: Feature Selection
            if target is not None:
                result = self._apply_feature_selection(result, target)
            
            # Step 8: Dimensionality Reduction
            if self.config.apply_pca:
                result = self._apply_dimensionality_reduction(result)
            
            # Step 9: Final Validation
            result = self._apply_final_validation(result)
            
            # Update feature names
            result.feature_names = list(result.processed_data.columns)
            
            # Store fitted transformers
            self.fitted_transformers = result.transformers.copy()
            
            self.logger.info(f"Preprocessing completed: {len(result.processed_data)} samples, {len(result.feature_names)} features")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in preprocessing pipeline: {e}")
            result.errors.append(f"Pipeline error: {str(e)}")
            return result
    
    def transform(self, data: pd.DataFrame) -> PreprocessingResult:
        """Transform new data using fitted transformers"""
        try:
            self.logger.info(f"Transforming new data: {len(data)} samples")
            
            result = PreprocessingResult(
                processed_data=data.copy(),
                feature_names=[],
                preprocessing_steps=[],
                transformers=self.fitted_transformers.copy(),
                statistics={}
            )
            
            # Apply the same transformations as during fitting
            # Note: This is a simplified version - in practice, you'd need to store
            # and apply each transformation step in the same order
            
            if 'scaler' in self.fitted_transformers:
                scaler = self.fitted_transformers['scaler']
                numeric_columns = result.processed_data.select_dtypes(include=[np.number]).columns
                result.processed_data[numeric_columns] = scaler.transform(result.processed_data[numeric_columns])
                result.preprocessing_steps.append('scaling')
            
            result.feature_names = list(result.processed_data.columns)
            
            self.logger.info(f"Transform completed: {len(result.processed_data)} samples, {len(result.feature_names)} features")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error transforming data: {e}")
            result = PreprocessingResult(
                processed_data=data,
                feature_names=list(data.columns),
                preprocessing_steps=[],
                transformers={},
                statistics={},
                errors=[f"Transform error: {str(e)}"]
            )
            return result
    
    def _apply_feature_engineering(self, result: PreprocessingResult) -> PreprocessingResult:
        """Apply feature engineering"""
        try:
            original_features = len(result.processed_data.columns)
            
            # Technical indicators
            tech_features = self.feature_engineer.engineer_technical_features(result.processed_data)
            if not tech_features.empty:
                result.processed_data = pd.concat([result.processed_data, tech_features], axis=1)
            
            # Price action features
            price_features = self.feature_engineer.engineer_price_action_features(result.processed_data)
            if not price_features.empty:
                result.processed_data = pd.concat([result.processed_data, price_features], axis=1)
            
            # Volume features
            volume_features = self.feature_engineer.engineer_volume_features(result.processed_data)
            if not volume_features.empty:
                result.processed_data = pd.concat([result.processed_data, volume_features], axis=1)
            
            # Time features
            time_features = self.feature_engineer.engineer_time_features(result.processed_data)
            if not time_features.empty:
                result.processed_data = pd.concat([result.processed_data, time_features], axis=1)
            
            # Remove NaN values created by rolling calculations
            result.processed_data = result.processed_data.dropna()
            
            new_features = len(result.processed_data.columns)
            result.preprocessing_steps.append('feature_engineering')
            result.statistics['features_engineered'] = new_features - original_features
            
            self.logger.info(f"Feature engineering: {original_features} -> {new_features} features")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in feature engineering: {e}")
            result.errors.append(f"Feature engineering error: {str(e)}")
            return result
    
    def _apply_data_cleaning(self, result: PreprocessingResult) -> PreprocessingResult:
        """Apply data cleaning"""
        try:
            original_samples = len(result.processed_data)
            
            # Remove duplicates
            if self.config.remove_duplicates:
                result.processed_data = result.processed_data.drop_duplicates()
                duplicates_removed = original_samples - len(result.processed_data)
                if duplicates_removed > 0:
                    result.warnings.append(f"Removed {duplicates_removed} duplicate rows")
            
            # Remove columns with all NaN values
            result.processed_data = result.processed_data.dropna(axis=1, how='all')
            
            # Remove rows with too many missing values
            missing_threshold = len(result.processed_data.columns) * self.config.max_missing_ratio
            result.processed_data = result.processed_data.dropna(thresh=len(result.processed_data.columns) - missing_threshold)
            
            cleaned_samples = len(result.processed_data)
            result.preprocessing_steps.append('data_cleaning')
            result.statistics['samples_removed'] = original_samples - cleaned_samples
            
            self.logger.info(f"Data cleaning: {original_samples} -> {cleaned_samples} samples")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in data cleaning: {e}")
            result.errors.append(f"Data cleaning error: {str(e)}")
            return result
    
    def _apply_imputation(self, result: PreprocessingResult) -> PreprocessingResult:
        """Apply missing value imputation"""
        try:
            numeric_columns = result.processed_data.select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) == 0:
                return result
            
            # Check if imputation is needed
            missing_values = result.processed_data[numeric_columns].isnull().sum().sum()
            if missing_values == 0:
                return result
            
            # Select imputation method
            if self.config.imputation_method == ImputationMethod.KNN:
                imputer = KNNImputer(n_neighbors=self.config.knn_neighbors)
            else:
                strategy_map = {
                    ImputationMethod.MEAN: 'mean',
                    ImputationMethod.MEDIAN: 'median',
                    ImputationMethod.MODE: 'most_frequent',
                    ImputationMethod.CONSTANT: 'constant'
                }
                strategy = strategy_map.get(self.config.imputation_method, 'median')
                imputer = SimpleImputer(strategy=strategy)
            
            # Apply imputation
            result.processed_data[numeric_columns] = imputer.fit_transform(result.processed_data[numeric_columns])
            result.transformers['imputer'] = imputer
            result.preprocessing_steps.append('imputation')
            result.statistics['missing_values_imputed'] = missing_values
            
            self.logger.info(f"Imputation: {missing_values} missing values imputed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in imputation: {e}")
            result.errors.append(f"Imputation error: {str(e)}")
            return result
    
    def _apply_outlier_treatment(self, result: PreprocessingResult) -> PreprocessingResult:
        """Apply outlier detection and treatment"""
        try:
            numeric_columns = result.processed_data.select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) == 0:
                return result
            
            outliers_removed = 0
            
            if self.config.outlier_method == 'iqr':
                for col in numeric_columns:
                    Q1 = result.processed_data[col].quantile(0.25)
                    Q3 = result.processed_data[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outlier_mask = (result.processed_data[col] < lower_bound) | (result.processed_data[col] > upper_bound)
                    outliers_removed += outlier_mask.sum()
                    
                    # Cap outliers instead of removing them
                    result.processed_data[col] = result.processed_data[col].clip(lower_bound, upper_bound)
            
            elif self.config.outlier_method == 'zscore':
                for col in numeric_columns:
                    z_scores = np.abs((result.processed_data[col] - result.processed_data[col].mean()) / result.processed_data[col].std())
                    outlier_mask = z_scores > self.config.outlier_threshold
                    outliers_removed += outlier_mask.sum()
                    
                    # Cap outliers
                    mean_val = result.processed_data[col].mean()
                    std_val = result.processed_data[col].std()
                    lower_bound = mean_val - self.config.outlier_threshold * std_val
                    upper_bound = mean_val + self.config.outlier_threshold * std_val
                    result.processed_data[col] = result.processed_data[col].clip(lower_bound, upper_bound)
            
            result.preprocessing_steps.append('outlier_treatment')
            result.statistics['outliers_treated'] = outliers_removed
            
            if outliers_removed > 0:
                self.logger.info(f"Outlier treatment: {outliers_removed} outliers capped")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in outlier treatment: {e}")
            result.errors.append(f"Outlier treatment error: {str(e)}")
            return result
    
    def _apply_feature_encoding(self, result: PreprocessingResult) -> PreprocessingResult:
        """Apply feature encoding for categorical variables"""
        try:
            categorical_columns = result.processed_data.select_dtypes(include=['object', 'category']).columns
            
            if len(categorical_columns) == 0:
                return result
            
            encoders = {}
            
            for col in categorical_columns:
                unique_values = result.processed_data[col].nunique()
                
                if unique_values <= 10:  # Use one-hot encoding for low cardinality
                    encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
                    encoded_data = encoder.fit_transform(result.processed_data[[col]])
                    encoded_columns = [f"{col}_{cat}" for cat in encoder.categories_[0]]
                    
                    # Add encoded columns
                    encoded_df = pd.DataFrame(encoded_data, columns=encoded_columns, index=result.processed_data.index)
                    result.processed_data = pd.concat([result.processed_data, encoded_df], axis=1)
                    
                else:  # Use label encoding for high cardinality
                    encoder = LabelEncoder()
                    result.processed_data[f"{col}_encoded"] = encoder.fit_transform(result.processed_data[col])
                
                encoders[col] = encoder
                
                # Remove original categorical column
                result.processed_data = result.processed_data.drop(col, axis=1)
            
            result.transformers['encoders'] = encoders
            result.preprocessing_steps.append('feature_encoding')
            result.statistics['categorical_features_encoded'] = len(categorical_columns)
            
            self.logger.info(f"Feature encoding: {len(categorical_columns)} categorical features encoded")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in feature encoding: {e}")
            result.errors.append(f"Feature encoding error: {str(e)}")
            return result
    
    def _apply_feature_scaling(self, result: PreprocessingResult) -> PreprocessingResult:
        """Apply feature scaling"""
        try:
            numeric_columns = result.processed_data.select_dtypes(include=[np.number]).columns
            
            if len(numeric_columns) == 0:
                return result
            
            # Select scaler
            scaler_map = {
                ScalingMethod.STANDARD: StandardScaler(),
                ScalingMethod.MINMAX: MinMaxScaler(),
                ScalingMethod.ROBUST: RobustScaler(),
                ScalingMethod.QUANTILE_UNIFORM: QuantileTransformer(output_distribution='uniform'),
                ScalingMethod.QUANTILE_NORMAL: QuantileTransformer(output_distribution='normal'),
                ScalingMethod.POWER: PowerTransformer()
            }
            
            scaler = scaler_map.get(self.config.scaling_method, StandardScaler())
            
            # Apply scaling
            result.processed_data[numeric_columns] = scaler.fit_transform(result.processed_data[numeric_columns])
            result.transformers['scaler'] = scaler
            result.preprocessing_steps.append('feature_scaling')
            result.statistics['features_scaled'] = len(numeric_columns)
            
            self.logger.info(f"Feature scaling: {len(numeric_columns)} features scaled using {self.config.scaling_method.value}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in feature scaling: {e}")
            result.errors.append(f"Feature scaling error: {str(e)}")
            return result
    
    def _apply_feature_selection(self, result: PreprocessingResult, target: pd.Series) -> PreprocessingResult:
        """Apply feature selection"""
        try:
            original_features = len(result.processed_data.columns)
            
            if original_features <= self.config.max_features:
                return result
            
            # Align target with processed data
            target_aligned = target.loc[result.processed_data.index]
            
            # Select feature selection method
            if self.config.feature_selection_method == FeatureSelectionMethod.UNIVARIATE:
                selector = SelectKBest(score_func=f_classif, k=min(self.config.max_features, original_features))
            elif self.config.feature_selection_method == FeatureSelectionMethod.MUTUAL_INFO:
                selector = SelectKBest(score_func=mutual_info_classif, k=min(self.config.max_features, original_features))
            elif self.config.feature_selection_method == FeatureSelectionMethod.RFE:
                estimator = RandomForestClassifier(n_estimators=50, random_state=42)
                selector = RFE(estimator, n_features_to_select=min(self.config.max_features, original_features))
            elif self.config.feature_selection_method == FeatureSelectionMethod.MODEL_BASED:
                estimator = RandomForestClassifier(n_estimators=50, random_state=42)
                selector = SelectFromModel(estimator, max_features=self.config.max_features)
            else:
                return result
            
            # Apply feature selection
            selected_features = selector.fit_transform(result.processed_data, target_aligned)
            selected_feature_names = result.processed_data.columns[selector.get_support()].tolist()
            
            result.processed_data = pd.DataFrame(selected_features, columns=selected_feature_names, index=result.processed_data.index)
            result.transformers['feature_selector'] = selector
            result.preprocessing_steps.append('feature_selection')
            result.statistics['features_selected'] = len(selected_feature_names)
            result.statistics['features_removed'] = original_features - len(selected_feature_names)
            
            self.logger.info(f"Feature selection: {original_features} -> {len(selected_feature_names)} features")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in feature selection: {e}")
            result.errors.append(f"Feature selection error: {str(e)}")
            return result
    
    def _apply_dimensionality_reduction(self, result: PreprocessingResult) -> PreprocessingResult:
        """Apply dimensionality reduction using PCA"""
        try:
            original_features = len(result.processed_data.columns)
            
            # Apply PCA
            pca = PCA(n_components=self.config.pca_variance_threshold)
            reduced_features = pca.fit_transform(result.processed_data)
            
            # Create new column names
            pca_columns = [f'pca_{i}' for i in range(reduced_features.shape[1])]
            result.processed_data = pd.DataFrame(reduced_features, columns=pca_columns, index=result.processed_data.index)
            
            result.transformers['pca'] = pca
            result.preprocessing_steps.append('dimensionality_reduction')
            result.statistics['pca_components'] = len(pca_columns)
            result.statistics['explained_variance_ratio'] = pca.explained_variance_ratio_.sum()
            
            self.logger.info(f"PCA: {original_features} -> {len(pca_columns)} components, {pca.explained_variance_ratio_.sum():.3f} variance explained")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in dimensionality reduction: {e}")
            result.errors.append(f"Dimensionality reduction error: {str(e)}")
            return result
    
    def _apply_final_validation(self, result: PreprocessingResult) -> PreprocessingResult:
        """Apply final validation checks"""
        try:
            # Check minimum samples
            if len(result.processed_data) < self.config.min_samples:
                result.warnings.append(f"Dataset has only {len(result.processed_data)} samples, minimum recommended: {self.config.min_samples}")
            
            # Check for infinite values
            inf_values = np.isinf(result.processed_data.select_dtypes(include=[np.number])).sum().sum()
            if inf_values > 0:
                result.processed_data = result.processed_data.replace([np.inf, -np.inf], np.nan)
                result.processed_data = result.processed_data.dropna()
                result.warnings.append(f"Removed {inf_values} infinite values")
            
            # Check feature variance
            numeric_columns = result.processed_data.select_dtypes(include=[np.number]).columns
            low_variance_features = []
            
            for col in numeric_columns:
                if result.processed_data[col].var() < self.config.min_variance:
                    low_variance_features.append(col)
            
            if low_variance_features:
                result.processed_data = result.processed_data.drop(columns=low_variance_features)
                result.warnings.append(f"Removed {len(low_variance_features)} low variance features")
            
            result.preprocessing_steps.append('final_validation')
            result.statistics['final_samples'] = len(result.processed_data)
            result.statistics['final_features'] = len(result.processed_data.columns)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in final validation: {e}")
            result.errors.append(f"Final validation error: {str(e)}")
            return result


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data
    np.random.seed(42)
    n_samples = 1000
    
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=n_samples, freq='5T'),
        'open_price': 1.1000 + np.random.normal(0, 0.001, n_samples),
        'high_price': 1.1005 + np.random.normal(0, 0.001, n_samples),
        'low_price': 1.0995 + np.random.normal(0, 0.001, n_samples),
        'close_price': 1.1000 + np.random.normal(0, 0.001, n_samples),
        'volume': np.random.randint(1000, 10000, n_samples),
        'signal_type': np.random.choice(['BUY', 'SELL'], n_samples),
        'confidence': np.random.uniform(0.6, 0.9, n_samples)
    })
    
    # Create target variable
    target = pd.Series(np.random.choice([0, 1], n_samples, p=[0.4, 0.6]))
    
    # Initialize preprocessing pipeline
    config = PreprocessingConfig(
        max_features=30,
        apply_pca=False,
        feature_selection_method=FeatureSelectionMethod.UNIVARIATE
    )
    
    pipeline = DataPreprocessingPipeline(config)
    
    print("Data Preprocessing Pipeline initialized successfully!")
    
    # Test preprocessing
    result = pipeline.fit_transform(sample_data, target)
    
    print(f"Preprocessing completed:")
    print(f"  - Original samples: {len(sample_data)}")
    print(f"  - Processed samples: {len(result.processed_data)}")
    print(f"  - Features: {len(result.feature_names)}")
    print(f"  - Steps: {', '.join(result.preprocessing_steps)}")
    print(f"  - Warnings: {len(result.warnings)}")
    print(f"  - Errors: {len(result.errors)}")
    
    if result.warnings:
        print("  Warnings:")
        for warning in result.warnings:
            print(f"    - {warning}")
    
    if result.errors:
        print("  Errors:")
        for error in result.errors:
            print(f"    - {error}")
    
    print("Data Preprocessing Pipeline test completed!")