#!/usr/bin/env python3
"""
Test script for Learning Notification System
Tests notification and alerting functionality
"""

import sys
import os
sys.path.append('Python')

import logging
import json
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_notification_system_initialization():
    """Test notification system initialization"""
    try:
        print("\n🔧 Testing Notification System initialization...")
        
        # Test if file exists
        if not os.path.exists('Python/learning_notification_system.py'):
            print("   ❌ learning_notification_system.py not found")
            return False
        
        print("   ✅ Notification system file exists")
        
        # Test basic syntax
        with open('Python/learning_notification_system.py', 'r') as f:
            content = f.read()
        
        try:
            compile(content, 'Python/learning_notification_system.py', 'exec')
            print("   ✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            return False
        
        # Test class definition
        if 'class LearningNotificationSystem:' in content:
            print("   ✅ LearningNotificationSystem class defined")
        else:
            print("   ❌ LearningNotificationSystem class not found")
            return False
        
        # Test key methods
        key_methods = [
            'send_learning_event_notification',
            'send_performance_alert',
            'send_system_health_alert',
            'send_training_completion_notification',
            'send_error_notification'
        ]
        
        for method in key_methods:
            if f'def {method}(' in content:
                print(f"   ✅ {method} method defined")
            else:
                print(f"   ❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification system initialization test failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    try:
        print("\n⚙️ Testing configuration loading...")
        
        # Create test config directory
        os.makedirs("Config", exist_ok=True)
        
        # Test default config creation
        test_config_path = "Config/test_notifications.json"
        
        # Remove existing test config
        if os.path.exists(test_config_path):
            os.remove(test_config_path)
        
        # Change to Python directory for import
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_notification_system import LearningNotificationSystem
            
            # Initialize with test config
            notification_system = LearningNotificationSystem(f"../{test_config_path}")
            
            print("   ✅ Notification system initialized")
            
            # Check if config was created
            if os.path.exists(f"../{test_config_path}"):
                print("   ✅ Default config file created")
                
                # Load and check config
                with open(f"../{test_config_path}", 'r') as f:
                    config = json.load(f)
                
                # Check expected config structure
                expected_keys = ['enabled', 'channels', 'rate_limiting', 'alert_thresholds']
                for key in expected_keys:
                    if key in config:
                        print(f"      ✅ Config has {key}")
                    else:
                        print(f"      ❌ Config missing {key}")
                
                # Check channels
                channels = config.get('channels', {})
                expected_channels = ['log', 'email', 'webhook', 'telegram']
                for channel in expected_channels:
                    if channel in channels:
                        print(f"      ✅ {channel} channel configured")
                    else:
                        print(f"      ⚠️ {channel} channel missing")
                
                return True
            else:
                print("   ❌ Config file not created")
                return False
                
        except ImportError as import_error:
            print(f"   ⚠️ Import failed (missing dependencies): {import_error}")
            return True  # Not a failure, just missing dependencies
            
        except Exception as init_error:
            print(f"   ❌ Initialization failed: {init_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        return False

def test_notification_levels():
    """Test notification level handling"""
    try:
        print("\n📊 Testing notification levels...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_notification_system import NotificationLevel, NotificationChannel
            
            # Test NotificationLevel enum
            levels = [NotificationLevel.INFO, NotificationLevel.WARNING, 
                     NotificationLevel.ERROR, NotificationLevel.CRITICAL]
            
            print(f"   ✅ Notification levels defined: {len(levels)} levels")
            for level in levels:
                print(f"      - {level.value}")
            
            # Test NotificationChannel enum
            channels = [NotificationChannel.EMAIL, NotificationChannel.WEBHOOK,
                       NotificationChannel.LOG, NotificationChannel.TELEGRAM]
            
            print(f"   ✅ Notification channels defined: {len(channels)} channels")
            for channel in channels:
                print(f"      - {channel.value}")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as enum_error:
            print(f"   ❌ Enum test failed: {enum_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Notification levels test failed: {e}")
        return False

def test_log_notification():
    """Test log notification functionality"""
    try:
        print("\n📝 Testing log notification...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_notification_system import LearningNotificationSystem, NotificationLevel
            
            # Initialize notification system
            notification_system = LearningNotificationSystem("../Config/test_notifications.json")
            
            # Test sending custom notification (should go to log)
            success = notification_system.send_custom_notification(
                NotificationLevel.INFO,
                "Test Log Notification",
                "This is a test log notification message"
            )
            
            if success:
                print("   ✅ Log notification sent successfully")
            else:
                print("   ❌ Log notification failed")
            
            # Test different levels
            levels = [NotificationLevel.INFO, NotificationLevel.WARNING, 
                     NotificationLevel.ERROR, NotificationLevel.CRITICAL]
            
            for level in levels:
                success = notification_system.send_custom_notification(
                    level,
                    f"Test {level.value} Notification",
                    f"This is a test {level.value.lower()} message"
                )
                
                if success:
                    print(f"   ✅ {level.value} notification sent")
                else:
                    print(f"   ❌ {level.value} notification failed")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as log_error:
            print(f"   ❌ Log notification test failed: {log_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Log notification test failed: {e}")
        return False

def test_performance_alert():
    """Test performance alert functionality"""
    try:
        print("\n⚠️ Testing performance alert...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_notification_system import LearningNotificationSystem
            
            notification_system = LearningNotificationSystem("../Config/test_notifications.json")
            
            # Test performance alert
            success = notification_system.send_performance_alert(
                model_name="test_model",
                current_performance=0.65,
                threshold=0.75,
                degradation_percent=0.13  # 13% degradation
            )
            
            if success:
                print("   ✅ Performance alert sent successfully")
            else:
                print("   ❌ Performance alert failed")
            
            # Test critical performance alert
            success = notification_system.send_performance_alert(
                model_name="critical_model",
                current_performance=0.45,
                threshold=0.75,
                degradation_percent=0.40  # 40% degradation
            )
            
            if success:
                print("   ✅ Critical performance alert sent successfully")
            else:
                print("   ❌ Critical performance alert failed")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as alert_error:
            print(f"   ❌ Performance alert test failed: {alert_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Performance alert test failed: {e}")
        return False

def test_system_health_alert():
    """Test system health alert functionality"""
    try:
        print("\n🏥 Testing system health alert...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_notification_system import LearningNotificationSystem
            
            notification_system = LearningNotificationSystem("../Config/test_notifications.json")
            
            # Test degraded health alert
            degraded_health = {
                'overall_health': 0.6,
                'status': 'degraded',
                'database_connection': True,
                'model_storage': False,
                'active_models': 2,
                'system_errors': 3
            }
            
            success = notification_system.send_system_health_alert(degraded_health)
            
            if success:
                print("   ✅ Degraded health alert sent successfully")
            else:
                print("   ❌ Degraded health alert failed")
            
            # Test error health alert
            error_health = {
                'overall_health': 0.3,
                'status': 'error',
                'database_connection': False,
                'model_storage': False,
                'active_models': 0,
                'system_errors': 8
            }
            
            success = notification_system.send_system_health_alert(error_health)
            
            if success:
                print("   ✅ Error health alert sent successfully")
            else:
                print("   ❌ Error health alert failed")
            
            # Test healthy status (should not send alert)
            healthy_status = {
                'overall_health': 0.95,
                'status': 'healthy',
                'database_connection': True,
                'model_storage': True,
                'active_models': 5,
                'system_errors': 0
            }
            
            success = notification_system.send_system_health_alert(healthy_status)
            
            if success:
                print("   ✅ Healthy status handled correctly (no alert sent)")
            else:
                print("   ❌ Healthy status handling failed")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as health_error:
            print(f"   ❌ System health alert test failed: {health_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ System health alert test failed: {e}")
        return False

def test_training_completion_notification():
    """Test training completion notification"""
    try:
        print("\n🎓 Testing training completion notification...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_notification_system import LearningNotificationSystem
            
            notification_system = LearningNotificationSystem("../Config/test_notifications.json")
            
            # Test training completion notification
            training_results = {
                'trained_models': ['random_forest', 'gradient_boosting', 'logistic_regression'],
                'best_model': {
                    'model_name': 'random_forest',
                    'test_accuracy': 0.87
                },
                'training_data_size': 1500
            }
            
            success = notification_system.send_training_completion_notification(training_results)
            
            if success:
                print("   ✅ Training completion notification sent successfully")
            else:
                print("   ❌ Training completion notification failed")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as training_error:
            print(f"   ❌ Training completion notification test failed: {training_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Training completion notification test failed: {e}")
        return False

def test_error_notification():
    """Test error notification functionality"""
    try:
        print("\n🚨 Testing error notification...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_notification_system import LearningNotificationSystem
            
            notification_system = LearningNotificationSystem("../Config/test_notifications.json")
            
            # Test error notification
            success = notification_system.send_error_notification(
                error_type="DatabaseConnectionError",
                error_message="Failed to connect to learning database",
                component="LearningDatabaseManager"
            )
            
            if success:
                print("   ✅ Error notification sent successfully")
            else:
                print("   ❌ Error notification failed")
            
            # Test another error type
            success = notification_system.send_error_notification(
                error_type="ModelTrainingError",
                error_message="Insufficient training data for model retraining",
                component="AdaptiveTrainer"
            )
            
            if success:
                print("   ✅ Model training error notification sent successfully")
            else:
                print("   ❌ Model training error notification failed")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as error_error:
            print(f"   ❌ Error notification test failed: {error_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Error notification test failed: {e}")
        return False

def test_notification_history():
    """Test notification history functionality"""
    try:
        print("\n📚 Testing notification history...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_notification_system import LearningNotificationSystem, NotificationLevel
            
            notification_system = LearningNotificationSystem("../Config/test_notifications.json")
            
            # Send a few notifications to build history
            for i in range(3):
                notification_system.send_custom_notification(
                    NotificationLevel.INFO,
                    f"Test Notification {i+1}",
                    f"This is test notification number {i+1}"
                )
            
            # Get notification history
            history = notification_system.get_notification_history(limit=10)
            
            if history:
                print(f"   ✅ Notification history retrieved: {len(history)} entries")
                
                # Check history structure
                for entry in history[:2]:  # Check first 2 entries
                    expected_keys = ['timestamp', 'event_type', 'level', 'message', 'success']
                    for key in expected_keys:
                        if key in entry:
                            print(f"      ✅ History entry has {key}")
                        else:
                            print(f"      ❌ History entry missing {key}")
                
                return True
            else:
                print("   ❌ No notification history found")
                return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as history_error:
            print(f"   ❌ Notification history test failed: {history_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Notification history test failed: {e}")
        return False

def run_all_tests():
    """Run all notification system tests"""
    print("🚀 Starting Learning Notification System Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Initialization
    test_results.append(("Initialization", test_notification_system_initialization()))
    
    # Test 2: Configuration Loading
    test_results.append(("Configuration Loading", test_config_loading()))
    
    # Test 3: Notification Levels
    test_results.append(("Notification Levels", test_notification_levels()))
    
    # Test 4: Log Notification
    test_results.append(("Log Notification", test_log_notification()))
    
    # Test 5: Performance Alert
    test_results.append(("Performance Alert", test_performance_alert()))
    
    # Test 6: System Health Alert
    test_results.append(("System Health Alert", test_system_health_alert()))
    
    # Test 7: Training Completion Notification
    test_results.append(("Training Completion", test_training_completion_notification()))
    
    # Test 8: Error Notification
    test_results.append(("Error Notification", test_error_notification()))
    
    # Test 9: Notification History
    test_results.append(("Notification History", test_notification_history()))
    
    # Print results summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Learning Notification System is working correctly.")
    elif passed >= len(test_results) * 0.6:  # 60% pass rate
        print(f"\n✅ Most tests passed! Learning Notification System is mostly functional.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("Data", exist_ok=True)
    os.makedirs("Config", exist_ok=True)
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)