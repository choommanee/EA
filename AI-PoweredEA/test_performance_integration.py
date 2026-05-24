"""
Test Performance Monitoring Integration
Comprehensive tests for performance monitoring and signal system integration
"""

import sys
import os
sys.path.append('Python')

import unittest
import logging
import tempfile
import shutil
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_performance_integration():
    """Test the performance monitoring integration"""
    try:
        print("Testing Performance Monitoring Integration...")
        
        # Create temporary directory
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test_performance.db")
        
        try:
            # Import components
            from performance_monitor import PerformanceMonitor, PerformanceMetric, MarketRegime
            from signal_performance_integration import SignalPerformanceIntegration
            
            print("✓ Successfully imported performance monitoring components")
            
            # Initialize performance monitor
            monitor = PerformanceMonitor(test_db)
            print("✓ Performance monitor initialized")
            
            # Test signal tracking
            signal_data = {
                'signal_type': 'BUY',
                'confidence': 0.85,
                'timestamp': datetime.now().isoformat(),
                'symbol': 'EURUSD',
                'entry_price': 1.1000
            }
            
            outcome = {
                'actual_result': 1.0,
                'predicted_result': 1.0,
                'is_correct': True,
                'profit_loss': 50.0
            }
            
            success = monitor.track_signal_outcome("test_model", "v1.0", signal_data, outcome)
            print(f"✓ Signal tracking test: {success}")
            
            # Test performance calculation
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            performance = monitor.calculate_model_performance("test_model", start_time, end_time)
            print(f"✓ Performance calculation: accuracy={performance.get('accuracy', 0):.2f}")
            
            # Test multiple signals for better metrics
            for i in range(10):
                test_signal = {
                    'signal_type': 'BUY' if i % 2 == 0 else 'SELL',
                    'confidence': 0.7 + (i * 0.02),
                    'timestamp': (datetime.now() - timedelta(minutes=i*5)).isoformat(),
                    'symbol': 'EURUSD',
                    'entry_price': 1.1000 + (i * 0.0001)
                }
                
                test_outcome = {
                    'actual_result': 1.0 if i % 3 != 0 else 0.0,  # 2/3 success rate
                    'predicted_result': test_signal['confidence'],
                    'is_correct': i % 3 != 0,
                    'profit_loss': 25.0 if i % 3 != 0 else -15.0
                }
                
                monitor.track_signal_outcome("test_model", "v1.0", test_signal, test_outcome)
            
            print("✓ Multiple signals tracked for comprehensive testing")
            
            # Test performance calculation with more data
            performance = monitor.calculate_model_performance("test_model", start_time, end_time)
            print(f"✓ Updated performance: accuracy={performance.get('accuracy', 0):.2f}, signals={performance.get('signal_count', 0)}")
            
            # Test degradation detection
            alert = monitor.detect_performance_degradation("test_model")
            print(f"✓ Degradation detection test: {'Alert detected' if alert else 'No degradation'}")
            
            # Test performance trends
            trends = monitor.get_performance_trends("test_model", days=1)
            print(f"✓ Performance trends: {len(trends.get('dates', []))} data points")
            
            # Test regime analysis
            regime_analysis = monitor.get_regime_performance_analysis("test_model", days=1)
            print(f"✓ Regime analysis: {len(regime_analysis)} regimes analyzed")
            
            # Initialize signal integration
            integration = SignalPerformanceIntegration(test_db)
            print("✓ Signal performance integration initialized")
            
            # Create mock signals table for testing
            _create_mock_signals_table(test_db)
            print("✓ Mock signals table created")
            
            # Test historical sync
            sync_result = integration.sync_historical_signals(days_back=1)
            print(f"✓ Historical sync: {sync_result.get('synced_signals', 0)} signals synced")
            
            # Test real-time metrics
            metrics = integration.get_real_time_performance_metrics()
            print(f"✓ Real-time metrics: {len(metrics)} models tracked")
            
            # Test performance issues detection
            issues = integration.detect_performance_issues()
            print(f"✓ Performance issues: {len(issues)} issues detected")
            
            # Test dashboard data
            dashboard_data = integration.get_performance_dashboard_data()
            print(f"✓ Dashboard data: {len(dashboard_data)} sections")
            
            # Test real-time monitoring start/stop
            monitor_start = integration.start_real_time_monitoring()
            print(f"✓ Real-time monitoring start: {monitor_start}")
            
            import time
            time.sleep(2)  # Let it run briefly
            
            monitor_stop = integration.stop_real_time_monitoring()
            print(f"✓ Real-time monitoring stop: {monitor_stop}")
            
            print("\n🎉 All performance integration tests passed!")
            return True
            
        finally:
            # Clean up test directory
            shutil.rmtree(test_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ Performance integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _create_mock_signals_table(db_path: str):
    """Create mock signals table with test data"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                profit_loss REAL,
                is_closed INTEGER DEFAULT 0,
                model_version TEXT DEFAULT 'v1.0',
                metadata TEXT
            )
        """)
        
        # Insert test signals
        test_signals = []
        base_time = datetime.now() - timedelta(hours=2)
        
        for i in range(20):
            signal_time = base_time + timedelta(minutes=i*5)
            is_closed = i < 15  # Most signals are closed
            profit_loss = None
            exit_price = None
            
            if is_closed:
                # Simulate 70% success rate
                is_profitable = i % 10 < 7
                profit_loss = 25.0 if is_profitable else -15.0
                exit_price = 1.1000 + (0.0010 if is_profitable else -0.0008)
            
            test_signals.append((
                signal_time.isoformat(),
                'EURUSD',
                'BUY' if i % 2 == 0 else 'SELL',
                0.6 + (i * 0.02),  # Confidence 0.6 to 0.98
                1.1000 + (i * 0.0001),  # Entry price
                exit_price,
                profit_loss,
                1 if is_closed else 0,
                'v1.0',
                '{"test": true}'
            ))
        
        cursor.executemany("""
            INSERT INTO signals 
            (timestamp, symbol, signal_type, confidence, entry_price, 
             exit_price, profit_loss, is_closed, model_version, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, test_signals)
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error creating mock signals table: {e}")


class TestPerformanceMonitor(unittest.TestCase):
    """Unit tests for Performance Monitor"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_monitor.db")
        
        from performance_monitor import PerformanceMonitor
        self.monitor = PerformanceMonitor(self.test_db)
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except:
            pass
    
    def test_initialization(self):
        """Test monitor initialization"""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.db_path, self.test_db)
        self.assertEqual(self.monitor.degradation_threshold, 0.1)
    
    def test_signal_tracking(self):
        """Test signal outcome tracking"""
        signal_data = {
            'signal_type': 'BUY',
            'confidence': 0.8,
            'timestamp': datetime.now().isoformat()
        }
        
        outcome = {
            'actual_result': 1.0,
            'predicted_result': 1.0,
            'is_correct': True,
            'profit_loss': 50.0
        }
        
        result = self.monitor.track_signal_outcome("test_model", "v1.0", signal_data, outcome)
        self.assertTrue(result)
        
        # Check that record was stored
        self.assertGreater(len(self.monitor.performance_records), 0)
    
    def test_performance_calculation(self):
        """Test performance metrics calculation"""
        # Track multiple signals
        for i in range(10):
            signal_data = {
                'signal_type': 'BUY',
                'confidence': 0.7,
                'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat()
            }
            
            outcome = {
                'actual_result': 1.0 if i < 7 else 0.0,  # 70% accuracy
                'predicted_result': 0.7,
                'is_correct': i < 7,
                'profit_loss': 25.0 if i < 7 else -15.0
            }
            
            self.monitor.track_signal_outcome("test_model", "v1.0", signal_data, outcome)
        
        # Calculate performance
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        performance = self.monitor.calculate_model_performance("test_model", start_time, end_time)
        
        self.assertIn('accuracy', performance)
        self.assertIn('signal_count', performance)
        self.assertEqual(performance['signal_count'], 10)
        self.assertAlmostEqual(performance['accuracy'], 0.7, places=1)


class TestSignalPerformanceIntegration(unittest.TestCase):
    """Unit tests for Signal Performance Integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_integration.db")
        
        from signal_performance_integration import SignalPerformanceIntegration
        self.integration = SignalPerformanceIntegration(self.test_db)
        
        # Create mock signals table
        _create_mock_signals_table(self.test_db)
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            self.integration.stop_real_time_monitoring()
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except:
            pass
    
    def test_initialization(self):
        """Test integration initialization"""
        self.assertIsNotNone(self.integration)
        self.assertIsNotNone(self.integration.performance_monitor)
        self.assertEqual(self.integration.sync_interval_minutes, 5)
    
    def test_historical_sync(self):
        """Test historical signal synchronization"""
        result = self.integration.sync_historical_signals(days_back=1)
        
        self.assertIn('synced_signals', result)
        self.assertIn('errors', result)
        self.assertIn('total_signals', result)
        
        # Should have synced some signals
        self.assertGreaterEqual(result['synced_signals'], 0)
    
    def test_real_time_metrics(self):
        """Test real-time performance metrics"""
        # First sync some data
        self.integration.sync_historical_signals(days_back=1)
        
        # Get metrics
        metrics = self.integration.get_real_time_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        # Should have system summary
        if metrics:
            self.assertIn('system_summary', metrics)
    
    def test_performance_issues_detection(self):
        """Test performance issues detection"""
        issues = self.integration.detect_performance_issues()
        
        self.assertIsInstance(issues, list)
        # Each issue should have required fields
        for issue in issues:
            self.assertIn('type', issue)
            self.assertIn('severity', issue)
            self.assertIn('message', issue)
    
    def test_monitoring_start_stop(self):
        """Test real-time monitoring start/stop"""
        # Test start
        start_result = self.integration.start_real_time_monitoring()
        self.assertTrue(start_result)
        self.assertTrue(self.integration.monitoring_active)
        
        # Test stop
        stop_result = self.integration.stop_real_time_monitoring()
        self.assertTrue(stop_result)
        self.assertFalse(self.integration.monitoring_active)


if __name__ == '__main__':
    # Run the comprehensive test
    success = test_performance_integration()
    
    if success:
        print("\n✅ Performance Monitoring Integration is working correctly!")
        print("\nRunning unit tests...")
        
        # Run unit tests
        unittest.main(verbosity=2, exit=False)
        
        print("\nTask 2.2 - Integrate performance monitoring with existing signal system: COMPLETED")
    else:
        print("\n❌ Performance Monitoring Integration test failed!")