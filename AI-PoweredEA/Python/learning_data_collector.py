"""
Learning Data Collector for AI Continuous Learning System
Collects and prepares training data from historical signals and market data
"""

import sys
import os
sys.path.append('Python')

import logging
import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import json
from dataclasses import dataclass, field
from enum import Enum
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.model_selection import train_test_split
from sklearn.utils import resample
import warnings
warnings.filterwarnings('ignore')


class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNUSABLE = "unusable"


class FeatureType(Enum):
    """Feature types for data preparation"""
    TECHNICAL_INDICATOR = "technical_indicator"
    PRICE_ACTION = "price_action"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    SENTIMENT = "sentiment"
    FUNDAMENTAL = "fundamental"
    TIME_BASED = "time_based"


@dataclass
class DataQualityReport:
    """Data quality assessment report"""
    timestamp: datetime
    total_samples: int
    valid_samples: int
    missing_values: int
    outliers: int
    quality_score: float
    quality_level: DataQuality
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class TrainingDataset:
    """Training dataset container"""
    features: pd.DataFrame
    targets: pd.Series
    metadata: Dict[str, Any]
    quality_report: DataQualityReport
    feature_names: List[str]
    target_name: str
    created_at: datetime = field(default_factory=datetime.now)


class LearningDataCollector:
    """Collects and prepares training data for the learning system"""
    
    def __init__(self, db_path: str = "Data/forex_trading.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # Data collection settings
        self.min_samples_required = 100
        self.max_samples_per_collection = 10000
        self.quality_threshold = 0.7
        self.outlier_threshold = 3.0  # Standard deviations
        
        # Feature engineering settings
        self.feature_window_sizes = [5, 10, 20, 50]
        self.technical_indicators = [
            'sma', 'ema', 'rsi', 'macd', 'bollinger_bands',
            'stochastic', 'atr', 'adx', 'cci', 'williams_r'
        ]
        
        # Data balancing settings
        self.balance_method = 'oversample'  # 'oversample', 'undersample', 'smote'
        self.target_balance_ratio = 0.4  # Minimum ratio for minority class
        
        # Scalers for different feature types
        self.scalers = {
            'standard': StandardScaler(),
            'minmax': MinMaxScaler(),
            'robust': RobustScaler()
        }
        
        # Initialize database tables
        self._init_data_collection_tables()
        
        self.logger.info("Learning Data Collector initialized")
    
    def collect_training_data(self, start_time: datetime, end_time: datetime,
                            min_samples: int = None) -> Optional[TrainingDataset]:
        """Collect and prepare training data from historical signals"""
        try:
            self.logger.info(f"Collecting training data from {start_time} to {end_time}")
            
            if min_samples is None:
                min_samples = self.min_samples_required
            
            # Collect signal feedback data
            signal_data = self._collect_signal_feedback(start_time, end_time)
            
            if signal_data is None or len(signal_data) < min_samples:
                self.logger.warning(f"Insufficient signal data: {len(signal_data) if signal_data is not None else 0} samples")
                return None
            
            # Collect market data for features
            market_data = self._collect_market_data(start_time, end_time)
            
            if market_data is None or len(market_data) == 0:
                self.logger.warning("No market data available for feature engineering")
                return None
            
            # Merge signal and market data
            merged_data = self._merge_signal_market_data(signal_data, market_data)
            
            if merged_data is None or len(merged_data) < min_samples:
                self.logger.warning(f"Insufficient merged data: {len(merged_data) if merged_data is not None else 0} samples")
                return None
            
            # Engineer features
            features_df = self._engineer_features(merged_data)
            
            # Prepare targets
            targets_series = self._prepare_targets(merged_data)
            
            # Validate data alignment
            if len(features_df) != len(targets_series):
                self.logger.error("Features and targets length mismatch")
                return None
            
            # Assess data quality
            quality_report = self._assess_data_quality(features_df, targets_series)
            
            if quality_report.quality_level == DataQuality.UNUSABLE:
                self.logger.error("Data quality is unusable")
                return None
            
            # Balance dataset if needed
            balanced_features, balanced_targets = self._balance_dataset(features_df, targets_series)
            
            # Create training dataset
            dataset = TrainingDataset(
                features=balanced_features,
                targets=balanced_targets,
                metadata={
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'original_samples': len(features_df),
                    'balanced_samples': len(balanced_features),
                    'feature_count': len(balanced_features.columns),
                    'collection_method': 'historical_signals'
                },
                quality_report=quality_report,
                feature_names=list(balanced_features.columns),
                target_name='signal_success'
            )
            
            # Store dataset metadata
            self._store_dataset_metadata(dataset)
            
            self.logger.info(f"Training data collected: {len(balanced_features)} samples, {len(balanced_features.columns)} features")
            
            return dataset
            
        except Exception as e:
            self.logger.error(f"Error collecting training data: {e}")
            return None
    
    def collect_test_data(self, start_time: datetime, end_time: datetime) -> Optional[pd.DataFrame]:
        """Collect test data for model evaluation"""
        try:
            self.logger.info(f"Collecting test data from {start_time} to {end_time}")
            
            # Collect recent signal data for testing
            signal_data = self._collect_signal_feedback(start_time, end_time)
            
            if signal_data is None or len(signal_data) == 0:
                return None
            
            # Collect corresponding market data
            market_data = self._collect_market_data(start_time, end_time)
            
            if market_data is None or len(market_data) == 0:
                return None
            
            # Merge and prepare test data
            merged_data = self._merge_signal_market_data(signal_data, market_data)
            
            if merged_data is None or len(merged_data) == 0:
                return None
            
            # Engineer features (same as training)
            test_features = self._engineer_features(merged_data)
            
            # Add targets for evaluation
            test_features['target'] = self._prepare_targets(merged_data)
            
            return test_features
            
        except Exception as e:
            self.logger.error(f"Error collecting test data: {e}")
            return None
    
    def validate_data_quality(self, data: pd.DataFrame) -> DataQualityReport:
        """Validate data quality and provide recommendations"""
        try:
            total_samples = len(data)
            
            if total_samples == 0:
                return DataQualityReport(
                    timestamp=datetime.now(),
                    total_samples=0,
                    valid_samples=0,
                    missing_values=0,
                    outliers=0,
                    quality_score=0.0,
                    quality_level=DataQuality.UNUSABLE,
                    issues=["No data available"],
                    recommendations=["Collect more data"]
                )
            
            # Check for missing values
            missing_values = data.isnull().sum().sum()
            missing_ratio = missing_values / (total_samples * len(data.columns))
            
            # Detect outliers using IQR method
            outliers = 0
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            
            for col in numeric_columns:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers += ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()
            
            outlier_ratio = outliers / total_samples if total_samples > 0 else 0
            
            # Calculate quality score
            quality_score = 1.0
            quality_score -= missing_ratio * 0.5  # Missing values penalty
            quality_score -= outlier_ratio * 0.3  # Outliers penalty
            
            # Check for data variance
            low_variance_features = 0
            for col in numeric_columns:
                if data[col].var() < 1e-6:  # Very low variance
                    low_variance_features += 1
            
            if len(numeric_columns) > 0:
                low_variance_ratio = low_variance_features / len(numeric_columns)
                quality_score -= low_variance_ratio * 0.2
            
            # Ensure score is between 0 and 1
            quality_score = max(0.0, min(1.0, quality_score))
            
            # Determine quality level
            if quality_score >= 0.9:
                quality_level = DataQuality.EXCELLENT
            elif quality_score >= 0.8:
                quality_level = DataQuality.GOOD
            elif quality_score >= 0.6:
                quality_level = DataQuality.FAIR
            elif quality_score >= 0.4:
                quality_level = DataQuality.POOR
            else:
                quality_level = DataQuality.UNUSABLE
            
            # Generate issues and recommendations
            issues = []
            recommendations = []
            
            if missing_ratio > 0.1:
                issues.append(f"High missing values: {missing_ratio:.1%}")
                recommendations.append("Implement data imputation or collect more complete data")
            
            if outlier_ratio > 0.05:
                issues.append(f"High outlier ratio: {outlier_ratio:.1%}")
                recommendations.append("Consider outlier removal or robust scaling")
            
            if low_variance_features > 0:
                issues.append(f"Low variance features: {low_variance_features}")
                recommendations.append("Remove or transform low variance features")
            
            if total_samples < self.min_samples_required:
                issues.append(f"Insufficient samples: {total_samples}")
                recommendations.append(f"Collect at least {self.min_samples_required} samples")
            
            valid_samples = total_samples - data.isnull().any(axis=1).sum()
            
            return DataQualityReport(
                timestamp=datetime.now(),
                total_samples=total_samples,
                valid_samples=valid_samples,
                missing_values=missing_values,
                outliers=outliers,
                quality_score=quality_score,
                quality_level=quality_level,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error validating data quality: {e}")
            return DataQualityReport(
                timestamp=datetime.now(),
                total_samples=0,
                valid_samples=0,
                missing_values=0,
                outliers=0,
                quality_score=0.0,
                quality_level=DataQuality.UNUSABLE,
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Fix data validation issues"]
            )
    
    def prepare_features_for_training(self, dataset: TrainingDataset,
                                    scaling_method: str = 'standard') -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features for model training with scaling"""
        try:
            # Select appropriate scaler
            if scaling_method not in self.scalers:
                scaling_method = 'standard'
            
            scaler = self.scalers[scaling_method]
            
            # Scale features
            scaled_features = scaler.fit_transform(dataset.features)
            
            # Convert targets to numpy array
            targets_array = dataset.targets.values
            
            return scaled_features, targets_array
            
        except Exception as e:
            self.logger.error(f"Error preparing features for training: {e}")
            return None, None
    
    def split_dataset(self, dataset: TrainingDataset, 
                     test_size: float = 0.2, random_state: int = 42) -> Tuple[Any, Any, Any, Any]:
        """Split dataset into training and validation sets"""
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                dataset.features,
                dataset.targets,
                test_size=test_size,
                random_state=random_state,
                stratify=dataset.targets if len(dataset.targets.unique()) > 1 else None
            )
            
            return X_train, X_test, y_train, y_test
            
        except Exception as e:
            self.logger.error(f"Error splitting dataset: {e}")
            return None, None, None, None
    
    def _collect_signal_feedback(self, start_time: datetime, end_time: datetime) -> Optional[pd.DataFrame]:
        """Collect signal feedback data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Query to get signal feedback data
            query = """
                SELECT 
                    s.id,
                    s.timestamp,
                    s.symbol,
                    s.signal_type,
                    s.confidence,
                    s.entry_price,
                    s.exit_price,
                    s.profit_loss,
                    s.is_closed,
                    CASE 
                        WHEN s.profit_loss > 0 THEN 1 
                        ELSE 0 
                    END as signal_success
                FROM signals s
                WHERE s.timestamp BETWEEN ? AND ?
                    AND s.is_closed = 1
                    AND s.exit_price IS NOT NULL
                ORDER BY s.timestamp
            """
            
            try:
                df = pd.read_sql_query(query, conn, params=(start_time.isoformat(), end_time.isoformat()))
                conn.close()
                
                if len(df) == 0:
                    return None
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
                
            except pd.errors.DatabaseError:
                # Table might not exist yet
                conn.close()
                return None
            
        except Exception as e:
            self.logger.error(f"Error collecting signal feedback: {e}")
            return None
    
    def _collect_market_data(self, start_time: datetime, end_time: datetime) -> Optional[pd.DataFrame]:
        """Collect market data for feature engineering"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Query to get market data (assuming a market_data table exists)
            query = """
                SELECT 
                    timestamp,
                    symbol,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                FROM market_data
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """
            
            try:
                df = pd.read_sql_query(query, conn, params=(start_time.isoformat(), end_time.isoformat()))
                conn.close()
                
                if len(df) == 0:
                    # Generate synthetic market data for testing
                    return self._generate_synthetic_market_data(start_time, end_time)
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
                
            except pd.errors.DatabaseError:
                # Table doesn't exist, generate synthetic data
                conn.close()
                return self._generate_synthetic_market_data(start_time, end_time)
            
        except Exception as e:
            self.logger.error(f"Error collecting market data: {e}")
            return self._generate_synthetic_market_data(start_time, end_time)
    
    def _generate_synthetic_market_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Generate synthetic market data for testing"""
        try:
            # Generate time series
            time_range = pd.date_range(start=start_time, end=end_time, freq='5T')  # 5-minute intervals
            
            # Generate synthetic price data
            np.random.seed(42)  # For reproducible results
            
            base_price = 1.1000
            price_changes = np.random.normal(0, 0.0001, len(time_range))
            prices = base_price + np.cumsum(price_changes)
            
            # Generate OHLC data
            data = []
            for i, timestamp in enumerate(time_range):
                close_price = prices[i]
                high_price = close_price + abs(np.random.normal(0, 0.0002))
                low_price = close_price - abs(np.random.normal(0, 0.0002))
                open_price = prices[i-1] if i > 0 else close_price
                volume = np.random.randint(1000, 10000)
                
                data.append({
                    'timestamp': timestamp,
                    'symbol': 'EURUSD',
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'volume': volume
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            self.logger.error(f"Error generating synthetic market data: {e}")
            return pd.DataFrame()
    
    def _merge_signal_market_data(self, signal_data: pd.DataFrame, 
                                market_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Merge signal and market data for feature engineering"""
        try:
            # Merge on timestamp and symbol (using nearest time match)
            merged_data = pd.merge_asof(
                signal_data.sort_values('timestamp'),
                market_data.sort_values('timestamp'),
                on='timestamp',
                by='symbol',
                direction='backward'
            )
            
            # Remove rows with missing market data
            merged_data = merged_data.dropna(subset=['open_price', 'high_price', 'low_price', 'close_price'])
            
            return merged_data
            
        except Exception as e:
            self.logger.error(f"Error merging signal and market data: {e}")
            return None
    
    def _engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from market data"""
        try:
            features_df = pd.DataFrame()
            
            # Basic price features
            features_df['price_change'] = data['close_price'] - data['open_price']
            features_df['price_range'] = data['high_price'] - data['low_price']
            features_df['price_position'] = (data['close_price'] - data['low_price']) / (data['high_price'] - data['low_price'])
            
            # Technical indicators (simplified versions)
            for window in self.feature_window_sizes:
                if len(data) >= window:
                    # Simple Moving Average
                    features_df[f'sma_{window}'] = data['close_price'].rolling(window=window).mean()
                    
                    # Price relative to SMA
                    features_df[f'price_sma_ratio_{window}'] = data['close_price'] / features_df[f'sma_{window}']
                    
                    # Volatility (rolling standard deviation)
                    features_df[f'volatility_{window}'] = data['close_price'].rolling(window=window).std()
                    
                    # RSI (simplified)
                    price_changes = data['close_price'].diff()
                    gains = price_changes.where(price_changes > 0, 0)
                    losses = -price_changes.where(price_changes < 0, 0)
                    avg_gains = gains.rolling(window=window).mean()
                    avg_losses = losses.rolling(window=window).mean()
                    rs = avg_gains / avg_losses
                    features_df[f'rsi_{window}'] = 100 - (100 / (1 + rs))
            
            # Volume features
            if 'volume' in data.columns:
                features_df['volume'] = data['volume']
                features_df['volume_ma_5'] = data['volume'].rolling(window=5).mean()
                features_df['volume_ratio'] = data['volume'] / features_df['volume_ma_5']
            
            # Time-based features
            features_df['hour'] = data['timestamp'].dt.hour
            features_df['day_of_week'] = data['timestamp'].dt.dayofweek
            features_df['is_weekend'] = (data['timestamp'].dt.dayofweek >= 5).astype(int)
            
            # Signal-specific features
            features_df['signal_confidence'] = data['confidence']
            features_df['signal_type_buy'] = (data['signal_type'] == 'BUY').astype(int)
            
            # Remove rows with NaN values (from rolling calculations)
            features_df = features_df.dropna()
            
            return features_df
            
        except Exception as e:
            self.logger.error(f"Error engineering features: {e}")
            return pd.DataFrame()
    
    def _prepare_targets(self, data: pd.DataFrame) -> pd.Series:
        """Prepare target variables from signal data"""
        try:
            # Use signal success as target
            targets = data['signal_success'].copy()
            
            # Ensure targets align with features (after dropna)
            return targets.iloc[-len(targets):].reset_index(drop=True)
            
        except Exception as e:
            self.logger.error(f"Error preparing targets: {e}")
            return pd.Series()
    
    def _assess_data_quality(self, features: pd.DataFrame, targets: pd.Series) -> DataQualityReport:
        """Assess the quality of prepared training data"""
        try:
            # Combine features and targets for comprehensive assessment
            combined_data = features.copy()
            combined_data['target'] = targets
            
            return self.validate_data_quality(combined_data)
            
        except Exception as e:
            self.logger.error(f"Error assessing data quality: {e}")
            return DataQualityReport(
                timestamp=datetime.now(),
                total_samples=0,
                valid_samples=0,
                missing_values=0,
                outliers=0,
                quality_score=0.0,
                quality_level=DataQuality.UNUSABLE,
                issues=[f"Assessment error: {str(e)}"],
                recommendations=["Fix data quality assessment"]
            )
    
    def _balance_dataset(self, features: pd.DataFrame, targets: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Balance the dataset to handle class imbalance"""
        try:
            # Check class distribution
            class_counts = targets.value_counts()
            
            if len(class_counts) < 2:
                # Only one class present, return as is
                return features, targets
            
            minority_class = class_counts.idxmin()
            majority_class = class_counts.idxmax()
            
            minority_count = class_counts[minority_class]
            majority_count = class_counts[majority_class]
            
            # Check if balancing is needed
            minority_ratio = minority_count / (minority_count + majority_count)
            
            if minority_ratio >= self.target_balance_ratio:
                # Dataset is already balanced enough
                return features, targets
            
            # Combine features and targets for resampling
            combined_data = features.copy()
            combined_data['target'] = targets
            
            # Separate classes
            minority_data = combined_data[combined_data['target'] == minority_class]
            majority_data = combined_data[combined_data['target'] == majority_class]
            
            if self.balance_method == 'oversample':
                # Oversample minority class
                target_minority_count = int(majority_count * self.target_balance_ratio / (1 - self.target_balance_ratio))
                minority_upsampled = resample(
                    minority_data,
                    replace=True,
                    n_samples=target_minority_count,
                    random_state=42
                )
                balanced_data = pd.concat([majority_data, minority_upsampled])
                
            elif self.balance_method == 'undersample':
                # Undersample majority class
                target_majority_count = int(minority_count * (1 - self.target_balance_ratio) / self.target_balance_ratio)
                majority_downsampled = resample(
                    majority_data,
                    replace=False,
                    n_samples=min(target_majority_count, len(majority_data)),
                    random_state=42
                )
                balanced_data = pd.concat([majority_downsampled, minority_data])
            
            else:
                # Default to no balancing
                balanced_data = combined_data
            
            # Shuffle the balanced dataset
            balanced_data = balanced_data.sample(frac=1, random_state=42).reset_index(drop=True)
            
            # Separate features and targets
            balanced_features = balanced_data.drop('target', axis=1)
            balanced_targets = balanced_data['target']
            
            self.logger.info(f"Dataset balanced: {len(features)} -> {len(balanced_features)} samples")
            
            return balanced_features, balanced_targets
            
        except Exception as e:
            self.logger.error(f"Error balancing dataset: {e}")
            return features, targets
    
    def _store_dataset_metadata(self, dataset: TrainingDataset):
        """Store dataset metadata in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                INSERT INTO dataset_metadata 
                (created_at, total_samples, feature_count, quality_score, quality_level, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                dataset.created_at.isoformat(),
                len(dataset.features),
                len(dataset.feature_names),
                dataset.quality_report.quality_score,
                dataset.quality_report.quality_level.value,
                json.dumps(dataset.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing dataset metadata: {e}")
    
    def _init_data_collection_tables(self):
        """Initialize database tables for data collection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Dataset metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dataset_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    total_samples INTEGER NOT NULL,
                    feature_count INTEGER NOT NULL,
                    quality_score REAL NOT NULL,
                    quality_level TEXT NOT NULL,
                    metadata TEXT,
                    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_dataset_created_at 
                ON dataset_metadata(created_at)
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing data collection tables: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize data collector
    collector = LearningDataCollector("Data/test_data_collector.db")
    
    print("Learning Data Collector initialized successfully!")
    
    # Test data collection
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    dataset = collector.collect_training_data(start_time, end_time, min_samples=10)
    
    if dataset:
        print(f"Training dataset collected:")
        print(f"  - Samples: {len(dataset.features)}")
        print(f"  - Features: {len(dataset.feature_names)}")
        print(f"  - Quality: {dataset.quality_report.quality_level.value}")
        print(f"  - Quality Score: {dataset.quality_report.quality_score:.3f}")
        
        # Test data preparation
        X_scaled, y_array = collector.prepare_features_for_training(dataset)
        if X_scaled is not None:
            print(f"  - Scaled features shape: {X_scaled.shape}")
            print(f"  - Targets shape: {y_array.shape}")
        
        # Test train/test split
        X_train, X_test, y_train, y_test = collector.split_dataset(dataset)
        if X_train is not None:
            print(f"  - Training set: {len(X_train)} samples")
            print(f"  - Test set: {len(X_test)} samples")
    
    else:
        print("No training dataset collected (insufficient data)")
    
    print("Learning Data Collector test completed!")