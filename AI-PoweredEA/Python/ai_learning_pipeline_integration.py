"""
AI Learning Pipeline Integration
Connects the learning system to the existing AI analysis pipeline
"""

import sys
import os
sys.path.append('Python')

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import sqlite3
import json
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Import learning system components
try:
    from performance_monitor import PerformanceMonitor
    from model_manager import ModelManager
    from ai_system_integration import AISystemIntegration
    from learning_metrics_collector import LearningMetricsCollector
    from learning_notification_system import LearningNotificationSystem
    from learning_configuration import LearningConfiguration
    LEARNING_COMPONENTS_AVAILABLE = True
except ImportError as e:
    LEARNING_COMPONENTS_AVAILABLE = False
    logging.warning(f"Learning components not available: {e}")


class IntegrationStatus(Enum):
    """Integration status types"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class DataFlowDirection(Enum):
    """Data flow direction types"""
    AI_TO_LEARNING = "ai_to_learning"
    LEARNING_TO_AI = "learning_to_ai"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class IntegrationConfig:
    """Integration configuration"""
    enable_performance_monitoring: bool = True
    enable_model_switching: bool = True
    enable_data_collection: bool = True
    enable_real_time_updates: bool = True
    performance_check_interval: int = 300  # 5 minutes
    model_switch_threshold: float = 0.05  # 5% improvement
    data_collection_batch_size: int = 100
    max_retry_attempts: int = 3
    connection_timeout: int = 30


@dataclass
class SignalData:
    """Signal data structure for integration"""
    signal_id: str
    timestamp: datetime
    symbol: str
    signal_type: str
    confidence: float
    features: Dict[str, Any]
    model_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalOutcome:
    """Signal outcome data structure"""
    signal_id: str
    timestamp: datetime
    outcome: str  # WIN, LOSS, PENDING
    profit_loss: float
    duration_minutes: int
    actual_price: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AILearningPipelineIntegration:
    """Integrates learning system with AI analysis pipeline"""
    
    def __init__(self, config: Optional[IntegrationConfig] = None,
                 db_path: str = "Data/ai_learning_integration.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.config = config or IntegrationConfig()
        
        # Integration status
        self.status = IntegrationStatus.DISCONNECTED
        self.last_connection_check = None
        self.connection_errors = 0
        
        # Component references
        self.performance_monitor = None
        self.model_manager = None
        self.ai_system = None
        self.metrics_collector = None
        self.notification_system = None
        self.learning_config = None
        
        # Data flow management
        self.signal_queue = []
        self.outcome_queue = []
        self.processing_thread = None
        self.is_processing = False
        
        # Performance tracking
        self.performance_history = {}
        self.model_performance_cache = {}
        self.last_model_switch = None
        
        # Callbacks for external integration
        self.signal_callbacks = []
        self.outcome_callbacks = []
        self.model_switch_callbacks = []
        
        # Initialize database
        self._init_integration_database()
        
        self.logger.info("AI Learning Pipeline Integration initialized")
    
    def initialize_integration(self) -> bool:
        """Initialize integration with learning system components"""
        try:
            self.status = IntegrationStatus.CONNECTING
            
            if not LEARNING_COMPONENTS_AVAILABLE:
                self.logger.error("Learning components not available")
                self.status = IntegrationStatus.ERROR
                return False
            
            # Initialize learning system components
            self.performance_monitor = PerformanceMonitor(self.db_path)
            self.model_manager = ModelManager()
            self.ai_system = AISystemIntegration()
            
            if hasattr(self, 'LearningMetricsCollector'):
                self.metrics_collector = LearningMetricsCollector()
            
            if hasattr(self, 'LearningNotificationSystem'):
                self.notification_system = LearningNotificationSystem()
            
            if hasattr(self, 'LearningConfiguration'):
                self.learning_config = LearningConfiguration()
            
            # Initialize AI system integration
            ai_init_success = self.ai_system.initialize_integration()
            if not ai_init_success:
                self.logger.warning("AI system integration initialization failed")
            
            # Start processing thread
            self._start_processing_thread()
            
            self.status = IntegrationStatus.CONNECTED
            self.last_connection_check = datetime.now()
            
            self.logger.info("AI Learning Pipeline Integration initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing integration: {e}")
            self.status = IntegrationStatus.ERROR
            return False
    
    def connect_signal_generation(self, signal_generator_callback: Callable) -> bool:
        """Connect to signal generation system"""
        try:
            # Register callback for new signals
            self.signal_callbacks.append(signal_generator_callback)
            
            self.logger.info("Connected to signal generation system")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to signal generation: {e}")
            return False
    
    def process_new_signal(self, signal_data: SignalData) -> bool:
        """Process new signal from AI analysis pipeline"""
        try:
            # Add to processing queue
            self.signal_queue.append(signal_data)
            
            # Record signal for performance monitoring
            if self.performance_monitor and self.config.enable_performance_monitoring:
                # This will be matched with outcome later
                self._record_signal_for_monitoring(signal_data)
            
            # Collect data for learning
            if self.config.enable_data_collection:
                self._collect_signal_data(signal_data)
            
            # Update metrics
            if self.metrics_collector:
                self._update_signal_metrics(signal_data)
            
            self.logger.debug(f"Processed new signal: {signal_data.signal_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing new signal: {e}")
            return False
    
    def process_signal_outcome(self, outcome_data: SignalOutcome) -> bool:
        """Process signal outcome from trading system"""
        try:
            # Add to processing queue
            self.outcome_queue.append(outcome_data)
            
            # Record outcome for performance monitoring
            if self.performance_monitor and self.config.enable_performance_monitoring:
                self._record_signal_outcome(outcome_data)
            
            # Update performance metrics
            if self.metrics_collector:
                self._update_outcome_metrics(outcome_data)
            
            # Check if model switching is needed
            if self.config.enable_model_switching:
                self._check_model_performance(outcome_data)
            
            self.logger.debug(f"Processed signal outcome: {outcome_data.signal_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing signal outcome: {e}")
            return False
    
    def get_current_model_info(self) -> Optional[Dict[str, Any]]:
        """Get current active model information"""
        try:
            if not self.model_manager:
                return None
            
            current_model = self.model_manager.get_current_model()
            if not current_model:
                return None
            
            model_info = {
                'model_id': current_model.get('model_id'),
                'version': current_model.get('version'),
                'created_at': current_model.get('created_at'),
                'performance_metrics': current_model.get('performance_metrics', {}),
                'status': 'active'
            }
            
            return model_info
            
        except Exception as e:
            self.logger.error(f"Error getting current model info: {e}")
            return None
    
    def switch_model(self, new_model_id: str, reason: str = "manual") -> bool:
        """Switch to a different model"""
        try:
            if not self.model_manager:
                self.logger.error("Model manager not available")
                return False
            
            # Get current model for comparison
            current_model = self.get_current_model_info()
            
            # Switch model
            success = self.model_manager.switch_to_model(new_model_id)
            
            if success:
                # Record model switch
                self._record_model_switch(current_model, new_model_id, reason)
                
                # Notify callbacks
                for callback in self.model_switch_callbacks:
                    try:
                        callback(current_model, new_model_id, reason)
                    except Exception as callback_error:
                        self.logger.error(f"Error in model switch callback: {callback_error}")
                
                # Send notification
                if self.notification_system:
                    self.notification_system.send_learning_event_notification(
                        event_type="model_switched",
                        message=f"Model switched to {new_model_id}",
                        details={'reason': reason, 'previous_model': current_model}
                    )
                
                self.last_model_switch = datetime.now()
                self.logger.info(f"Successfully switched to model: {new_model_id}")
                return True
            else:
                self.logger.error(f"Failed to switch to model: {new_model_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error switching model: {e}")
            return False
    
    def get_performance_summary(self, time_hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for integration monitoring"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_hours)
            
            summary = {
                'integration_status': self.status.value,
                'last_connection_check': self.last_connection_check.isoformat() if self.last_connection_check else None,
                'connection_errors': self.connection_errors,
                'signals_processed': len(self.signal_queue),
                'outcomes_processed': len(self.outcome_queue),
                'last_model_switch': self.last_model_switch.isoformat() if self.last_model_switch else None,
                'current_model': self.get_current_model_info(),
                'performance_data': self._get_recent_performance_data(start_time, end_time)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}
    
    def register_signal_callback(self, callback: Callable) -> bool:
        """Register callback for signal processing"""
        try:
            self.signal_callbacks.append(callback)
            return True
        except Exception as e:
            self.logger.error(f"Error registering signal callback: {e}")
            return False
    
    def register_outcome_callback(self, callback: Callable) -> bool:
        """Register callback for outcome processing"""
        try:
            self.outcome_callbacks.append(callback)
            return True
        except Exception as e:
            self.logger.error(f"Error registering outcome callback: {e}")
            return False
    
    def register_model_switch_callback(self, callback: Callable) -> bool:
        """Register callback for model switching"""
        try:
            self.model_switch_callbacks.append(callback)
            return True
        except Exception as e:
            self.logger.error(f"Error registering model switch callback: {e}")
            return False
    
    def start_real_time_monitoring(self) -> bool:
        """Start real-time performance monitoring"""
        try:
            if not self.config.enable_real_time_updates:
                return False
            
            # Start monitoring thread
            monitoring_thread = threading.Thread(
                target=self._real_time_monitoring_loop,
                daemon=True
            )
            monitoring_thread.start()
            
            self.logger.info("Started real-time monitoring")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting real-time monitoring: {e}")
            return False
    
    def stop_integration(self) -> bool:
        """Stop integration and cleanup resources"""
        try:
            self.is_processing = False
            self.status = IntegrationStatus.DISCONNECTED
            
            # Wait for processing thread to finish
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5.0)
            
            # Clear queues
            self.signal_queue.clear()
            self.outcome_queue.clear()
            
            self.logger.info("AI Learning Pipeline Integration stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping integration: {e}")
            return False
    
    def _start_processing_thread(self):
        """Start background processing thread"""
        self.is_processing = True
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()
    
    def _processing_loop(self):
        """Main processing loop for signals and outcomes"""
        while self.is_processing:
            try:
                # Process signal queue
                while self.signal_queue:
                    signal_data = self.signal_queue.pop(0)
                    self._process_signal_internal(signal_data)
                
                # Process outcome queue
                while self.outcome_queue:
                    outcome_data = self.outcome_queue.pop(0)
                    self._process_outcome_internal(outcome_data)
                
                # Sleep briefly to avoid busy waiting
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                time.sleep(1.0)
    
    def _real_time_monitoring_loop(self):
        """Real-time monitoring loop"""
        while self.is_processing:
            try:
                # Check performance and model switching
                if self.config.enable_model_switching:
                    self._check_automatic_model_switching()
                
                # Update connection status
                self._check_connection_health()
                
                # Sleep for monitoring interval
                time.sleep(self.config.performance_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _record_signal_for_monitoring(self, signal_data: SignalData):
        """Record signal for performance monitoring"""
        try:
            # Store signal data for later matching with outcome
            signal_record = {
                'signal_id': signal_data.signal_id,
                'timestamp': signal_data.timestamp,
                'symbol': signal_data.symbol,
                'signal_type': signal_data.signal_type,
                'confidence': signal_data.confidence,
                'model_id': signal_data.model_id,
                'features': signal_data.features
            }
            
            # Store in database for later outcome matching
            self._store_signal_record(signal_record)
            
        except Exception as e:
            self.logger.error(f"Error recording signal for monitoring: {e}")
    
    def _record_signal_outcome(self, outcome_data: SignalOutcome):
        """Record signal outcome for performance analysis"""
        try:
            # Get original signal data
            signal_record = self._get_signal_record(outcome_data.signal_id)
            
            if signal_record and self.performance_monitor:
                # Track signal outcome
                self.performance_monitor.track_signal_outcome(
                    model_id=signal_record.get('model_id', 'unknown'),
                    model_version='current',
                    signal_data=signal_record,
                    outcome={
                        'result': outcome_data.outcome,
                        'profit_loss': outcome_data.profit_loss,
                        'duration': outcome_data.duration_minutes,
                        'timestamp': outcome_data.timestamp
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error recording signal outcome: {e}")
    
    def _collect_signal_data(self, signal_data: SignalData):
        """Collect signal data for learning"""
        try:
            # This would integrate with learning data collector
            # For now, just log the data collection
            self.logger.debug(f"Collecting signal data for learning: {signal_data.signal_id}")
            
        except Exception as e:
            self.logger.error(f"Error collecting signal data: {e}")
    
    def _update_signal_metrics(self, signal_data: SignalData):
        """Update metrics for new signal"""
        try:
            if self.metrics_collector:
                # Record signal generation metrics
                self.metrics_collector.record_training_metrics(
                    model_id=signal_data.model_id or 'unknown',
                    training_time=0.0,  # Signal generation time
                    samples_processed=1,
                    batch_size=1,
                    learning_rate=0.0
                )
            
        except Exception as e:
            self.logger.error(f"Error updating signal metrics: {e}")
    
    def _update_outcome_metrics(self, outcome_data: SignalOutcome):
        """Update metrics for signal outcome"""
        try:
            if self.metrics_collector:
                # Record outcome metrics
                accuracy = 1.0 if outcome_data.outcome == 'WIN' else 0.0
                self.metrics_collector.record_model_performance(
                    model_id='current',
                    metrics={'accuracy': accuracy, 'profit_loss': outcome_data.profit_loss}
                )
            
        except Exception as e:
            self.logger.error(f"Error updating outcome metrics: {e}")
    
    def _check_model_performance(self, outcome_data: SignalOutcome):
        """Check if model performance warrants switching"""
        try:
            if not self.model_manager:
                return
            
            # Get recent performance
            current_performance = self._get_recent_model_performance()
            
            if current_performance and current_performance.get('accuracy', 0) < 0.5:
                # Performance is poor, consider switching
                available_models = self.model_manager.list_available_models()
                
                if available_models:
                    # Find best performing alternative model
                    best_model = self._find_best_alternative_model(available_models)
                    
                    if best_model:
                        self.switch_model(best_model['model_id'], "performance_degradation")
            
        except Exception as e:
            self.logger.error(f"Error checking model performance: {e}")
    
    def _check_automatic_model_switching(self):
        """Check for automatic model switching opportunities"""
        try:
            if not self.config.enable_model_switching:
                return
            
            # Check if enough time has passed since last switch
            if self.last_model_switch:
                time_since_switch = datetime.now() - self.last_model_switch
                if time_since_switch.total_seconds() < 3600:  # 1 hour minimum
                    return
            
            # Get current model performance
            current_performance = self._get_recent_model_performance()
            
            if current_performance:
                current_accuracy = current_performance.get('accuracy', 0)
                
                # Check if there's a better model available
                available_models = self.model_manager.list_available_models()
                
                for model in available_models:
                    model_perf = model.get('performance_metrics', {})
                    model_accuracy = model_perf.get('accuracy', 0)
                    
                    # Switch if improvement exceeds threshold
                    if model_accuracy > current_accuracy + self.config.model_switch_threshold:
                        self.switch_model(model['model_id'], "automatic_improvement")
                        break
            
        except Exception as e:
            self.logger.error(f"Error in automatic model switching check: {e}")
    
    def _check_connection_health(self):
        """Check connection health and update status"""
        try:
            # Simple health check
            if self.ai_system:
                status = self.ai_system.get_integration_status()
                if status.get('active', False):
                    self.status = IntegrationStatus.CONNECTED
                    self.connection_errors = 0
                else:
                    self.connection_errors += 1
                    if self.connection_errors > self.config.max_retry_attempts:
                        self.status = IntegrationStatus.ERROR
            
            self.last_connection_check = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error checking connection health: {e}")
            self.connection_errors += 1
    
    def _process_signal_internal(self, signal_data: SignalData):
        """Internal signal processing"""
        try:
            # Call registered callbacks
            for callback in self.signal_callbacks:
                try:
                    callback(signal_data)
                except Exception as callback_error:
                    self.logger.error(f"Error in signal callback: {callback_error}")
            
        except Exception as e:
            self.logger.error(f"Error in internal signal processing: {e}")
    
    def _process_outcome_internal(self, outcome_data: SignalOutcome):
        """Internal outcome processing"""
        try:
            # Call registered callbacks
            for callback in self.outcome_callbacks:
                try:
                    callback(outcome_data)
                except Exception as callback_error:
                    self.logger.error(f"Error in outcome callback: {callback_error}")
            
        except Exception as e:
            self.logger.error(f"Error in internal outcome processing: {e}")
    
    def _record_model_switch(self, previous_model: Optional[Dict], new_model_id: str, reason: str):
        """Record model switch event"""
        try:
            switch_record = {
                'timestamp': datetime.now().isoformat(),
                'previous_model': previous_model,
                'new_model_id': new_model_id,
                'reason': reason
            }
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO model_switches 
                (timestamp, previous_model_id, new_model_id, reason, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                switch_record['timestamp'],
                previous_model.get('model_id') if previous_model else None,
                new_model_id,
                reason,
                json.dumps(switch_record)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error recording model switch: {e}")
    
    def _get_recent_model_performance(self) -> Optional[Dict[str, Any]]:
        """Get recent model performance data"""
        try:
            if not self.performance_monitor:
                return None
            
            current_model = self.get_current_model_info()
            if not current_model:
                return None
            
            # Get performance for current model
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            performance = self.performance_monitor.calculate_model_performance(
                current_model['model_id'],
                start_time,
                end_time
            )
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error getting recent model performance: {e}")
            return None
    
    def _find_best_alternative_model(self, available_models: List[Dict]) -> Optional[Dict]:
        """Find best alternative model from available models"""
        try:
            best_model = None
            best_accuracy = 0
            
            for model in available_models:
                performance = model.get('performance_metrics', {})
                accuracy = performance.get('accuracy', 0)
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_model = model
            
            return best_model
            
        except Exception as e:
            self.logger.error(f"Error finding best alternative model: {e}")
            return None
    
    def _get_recent_performance_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get recent performance data for summary"""
        try:
            # Get performance data from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) as signal_count,
                       AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) as accuracy,
                       AVG(profit_loss) as avg_profit_loss
                FROM signal_outcomes 
                WHERE timestamp BETWEEN ? AND ?
            """, (start_time.isoformat(), end_time.isoformat()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'signal_count': result[0],
                    'accuracy': result[1] or 0.0,
                    'avg_profit_loss': result[2] or 0.0
                }
            else:
                return {'signal_count': 0, 'accuracy': 0.0, 'avg_profit_loss': 0.0}
                
        except Exception as e:
            self.logger.error(f"Error getting recent performance data: {e}")
            return {'signal_count': 0, 'accuracy': 0.0, 'avg_profit_loss': 0.0}
    
    def _store_signal_record(self, signal_record: Dict[str, Any]):
        """Store signal record in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO signal_records 
                (signal_id, timestamp, symbol, signal_type, confidence, model_id, features)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_record['signal_id'],
                signal_record['timestamp'].isoformat(),
                signal_record['symbol'],
                signal_record['signal_type'],
                signal_record['confidence'],
                signal_record['model_id'],
                json.dumps(signal_record['features'])
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing signal record: {e}")
    
    def _get_signal_record(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get signal record from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT signal_id, timestamp, symbol, signal_type, confidence, model_id, features
                FROM signal_records 
                WHERE signal_id = ?
            """, (signal_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'signal_id': result[0],
                    'timestamp': result[1],
                    'symbol': result[2],
                    'signal_type': result[3],
                    'confidence': result[4],
                    'model_id': result[5],
                    'features': json.loads(result[6]) if result[6] else {}
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting signal record: {e}")
            return None
    
    def _init_integration_database(self):
        """Initialize integration database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Signal records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signal_records (
                    signal_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    model_id TEXT,
                    features TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Signal outcomes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signal_outcomes (
                    signal_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    profit_loss REAL NOT NULL,
                    duration_minutes INTEGER,
                    actual_price REAL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Model switches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_switches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    previous_model_id TEXT,
                    new_model_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_records_timestamp ON signal_records(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_outcomes_timestamp ON signal_outcomes(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_switches_timestamp ON model_switches(timestamp)")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing integration database: {e}")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize integration
    config = IntegrationConfig(
        enable_performance_monitoring=True,
        enable_model_switching=True,
        performance_check_interval=60
    )
    
    integration = AILearningPipelineIntegration(config)
    
    print("AI Learning Pipeline Integration initialized successfully!")
    
    # Initialize integration
    success = integration.initialize_integration()
    print(f"Integration initialization: {'Success' if success else 'Failed'}")
    
    # Test signal processing
    test_signal = SignalData(
        signal_id="test_signal_001",
        timestamp=datetime.now(),
        symbol="EURUSD",
        signal_type="BUY",
        confidence=0.75,
        features={"rsi": 30, "macd": 0.5},
        model_id="test_model"
    )
    
    signal_success = integration.process_new_signal(test_signal)
    print(f"Signal processing: {'Success' if signal_success else 'Failed'}")
    
    # Test outcome processing
    test_outcome = SignalOutcome(
        signal_id="test_signal_001",
        timestamp=datetime.now(),
        outcome="WIN",
        profit_loss=100.0,
        duration_minutes=30
    )
    
    outcome_success = integration.process_signal_outcome(test_outcome)
    print(f"Outcome processing: {'Success' if outcome_success else 'Failed'}")
    
    # Get performance summary
    summary = integration.get_performance_summary()
    print(f"Performance summary: {summary}")
    
    # Stop integration
    integration.stop_integration()
    
    print("AI Learning Pipeline Integration test completed!")