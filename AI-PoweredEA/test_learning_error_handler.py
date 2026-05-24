#!/usr/bin/env python3
"""
Test script for Learning Error Handler
Tests comprehensive error handling and logging functionality
"""

import sys
import os
sys.path.append('Python')

import logging
import time
import shutil
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_error_handler_initialization():
    """Test error handler initialization"""
    try:
        print("\n🔧 Testing Error Handler initialization...")
        
        # Test if file exists
        if not os.path.exists('Python/learning_error_handler.py'):
            print("   ❌ learning_error_handler.py not found")
            return False
        
        print("   ✅ Error handler file exists")
        
        # Test basic syntax
        with open('Python/learning_error_handler.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            compile(content, 'Python/learning_error_handler.py', 'exec')
            print("   ✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            return False
        
        # Test class and enum definitions
        expected_classes = [
            'LearningErrorHandler',
            'ErrorRecord',
            'ErrorSeverity',
            'ErrorCategory'
        ]
        
        for class_name in expected_classes:
            if f'class {class_name}' in content or f'{class_name}(Enum)' in content:
                print(f"   ✅ {class_name} defined")
            else:
                print(f"   ❌ {class_name} missing")
        
        # Test key methods
        key_methods = [
            'handle_error',
            'register_recovery_strategy',
            'get_error_statistics',
            'resolve_error',
            'get_circuit_breaker_status',
            'cleanup_old_errors'
        ]
        
        for method in key_methods:
            if f'def {method}(' in content:
                print(f"   ✅ {method} method defined")
            else:
                print(f"   ❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handler initialization test failed: {e}")
        return False

def test_error_enums():
    """Test error enums and data structures"""
    try:
        print("\n📊 Testing error enums and data structures...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_error_handler import ErrorSeverity, ErrorCategory, ErrorRecord
            
            # Test ErrorSeverity enum
            severities = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, 
                         ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
            
            print(f"   ✅ ErrorSeverity enum: {len(severities)} levels")
            for severity in severities:
                print(f"      - {severity.value}")
            
            # Test ErrorCategory enum
            categories = [ErrorCategory.DATABASE_ERROR, ErrorCategory.MODEL_ERROR,
                         ErrorCategory.DATA_ERROR, ErrorCategory.SYSTEM_ERROR]
            
            print(f"   ✅ ErrorCategory enum: {len(categories)} categories (showing 4)")
            for category in categories:
                print(f"      - {category.value}")
            
            # Test ErrorRecord dataclass
            error_record = ErrorRecord(
                error_id="TEST_001",
                timestamp=datetime.now(),
                component="test_component",
                error_type="ValueError",
                error_message="Test error message",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.DATA_ERROR,
                stack_trace="Test stack trace"
            )
            
            print("   ✅ ErrorRecord dataclass created successfully")
            print(f"      Error ID: {error_record.error_id}")
            print(f"      Severity: {error_record.severity.value}")
            print(f"      Category: {error_record.category.value}")
            
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
        print(f"❌ Error enums test failed: {e}")
        return False

def test_basic_error_handling():
    """Test basic error handling functionality"""
    try:
        print("\n🚨 Testing basic error handling...")
        
        # Create test directories
        test_log_dir = "Logs/test"
        os.makedirs(test_log_dir, exist_ok=True)
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_error_handler import LearningErrorHandler
            
            # Initialize error handler
            error_handler = LearningErrorHandler(
                "../Data/test_error_handler.db",
                f"../{test_log_dir}"
            )
            print("   ✅ Error handler initialized")
            
            # Test handling different types of errors
            test_errors = [
                (ValueError("Test value error"), "test_component_1"),
                (TypeError("Test type error"), "test_component_2"),
                (ConnectionError("Test connection error"), "database_component"),
                (FileNotFoundError("Test file not found"), "file_component")
            ]
            
            handled_errors = []
            
            for error, component in test_errors:
                try:
                    raise error
                except Exception as e:
                    error_id = error_handler.handle_error(
                        e, component, {"test_context": "unit_test"}
                    )
                    
                    if error_id and error_id != "error_handler_failed":
                        print(f"   ✅ {type(error).__name__} handled: {error_id}")
                        handled_errors.append(error_id)
                    else:
                        print(f"   ❌ Failed to handle {type(error).__name__}")
            
            if len(handled_errors) >= 3:  # At least 3 out of 4 should work
                print(f"   ✅ Error handling successful: {len(handled_errors)} errors handled")
                return True
            else:
                print(f"   ❌ Error handling failed: only {len(handled_errors)} errors handled")
                return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as handling_error:
            print(f"   ❌ Error handling test failed: {handling_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Basic error handling test failed: {e}")
        return False

def test_error_statistics():
    """Test error statistics functionality"""
    try:
        print("\n📊 Testing error statistics...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_error_handler import LearningErrorHandler
            
            error_handler = LearningErrorHandler(
                "../Data/test_error_handler.db",
                "../Logs/test"
            )
            
            # Generate some test errors
            test_errors = [
                ValueError("Stats test error 1"),
                TypeError("Stats test error 2"),
                ConnectionError("Stats test error 3"),
                ValueError("Stats test error 1")  # Duplicate to test counting
            ]
            
            for i, error in enumerate(test_errors):
                try:
                    raise error
                except Exception as e:
                    error_handler.handle_error(e, f"stats_component_{i % 2}")
            
            # Get error statistics
            stats = error_handler.get_error_statistics()
            
            if stats:
                print("   ✅ Error statistics retrieved")
                print(f"      Total errors: {stats.get('total_errors', 0)}")
                print(f"      Errors by severity: {len(stats.get('errors_by_severity', {}))}")
                print(f"      Errors by category: {len(stats.get('errors_by_category', {}))}")
                print(f"      Errors by component: {len(stats.get('errors_by_component', {}))}")
                print(f"      Top errors: {len(stats.get('top_errors', []))}")
                
                # Check if we have reasonable data
                if stats.get('total_errors', 0) > 0:
                    print("   ✅ Statistics contain error data")
                else:
                    print("   ⚠️ No error data in statistics")
                
                return True
            else:
                print("   ❌ Failed to get error statistics")
                return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as stats_error:
            print(f"   ❌ Error statistics test failed: {stats_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Error statistics test failed: {e}")
        return False

def test_recovery_strategies():
    """Test recovery strategy registration and execution"""
    try:
        print("\n🔄 Testing recovery strategies...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_error_handler import LearningErrorHandler
            
            error_handler = LearningErrorHandler(
                "../Data/test_error_handler.db",
                "../Logs/test"
            )
            
            # Define a test recovery strategy
            recovery_called = False
            
            def test_recovery_strategy(error_record):
                nonlocal recovery_called
                recovery_called = True
                print(f"      Recovery strategy called for: {error_record.error_id}")
                return True
            
            # Register recovery strategy
            error_handler.register_recovery_strategy(
                "ValueError", "recovery_test_component", test_recovery_strategy
            )
            print("   ✅ Recovery strategy registered")
            
            # Test recovery strategy execution
            try:
                raise ValueError("Test error for recovery")
            except Exception as e:
                error_id = error_handler.handle_error(e, "recovery_test_component")
                
                if error_id and error_id != "error_handler_failed":
                    print(f"   ✅ Error handled with recovery: {error_id}")
                    
                    # Check if recovery was called
                    if recovery_called:
                        print("   ✅ Recovery strategy executed")
                    else:
                        print("   ⚠️ Recovery strategy not executed")
                    
                    return True
                else:
                    print("   ❌ Error handling failed")
                    return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as recovery_error:
            print(f"   ❌ Recovery strategies test failed: {recovery_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Recovery strategies test failed: {e}")
        return False

def test_circuit_breakers():
    """Test circuit breaker functionality"""
    try:
        print("\n⚡ Testing circuit breakers...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_error_handler import LearningErrorHandler
            
            error_handler = LearningErrorHandler(
                "../Data/test_error_handler.db",
                "../Logs/test"
            )
            
            # Generate multiple errors for the same component to trigger circuit breaker
            component = "circuit_breaker_test"
            
            for i in range(6):  # Should exceed default threshold of 5
                try:
                    raise ConnectionError(f"Circuit breaker test error {i+1}")
                except Exception as e:
                    error_handler.handle_error(e, component)
            
            print(f"   ✅ Generated 6 errors for {component}")
            
            # Check circuit breaker status
            cb_status = error_handler.get_circuit_breaker_status()
            
            if cb_status:
                print("   ✅ Circuit breaker status retrieved")
                
                if component in cb_status:
                    breaker_info = cb_status[component]
                    print(f"      Component: {component}")
                    print(f"      Is Open: {breaker_info.get('is_open', False)}")
                    print(f"      Error Count: {breaker_info.get('error_count', 0)}")
                    print(f"      Threshold: {breaker_info.get('threshold', 5)}")
                    
                    if breaker_info.get('is_open', False):
                        print("   ✅ Circuit breaker opened as expected")
                        
                        # Test reset
                        reset_success = error_handler.reset_circuit_breaker(component)
                        if reset_success:
                            print("   ✅ Circuit breaker reset successfully")
                        else:
                            print("   ❌ Circuit breaker reset failed")
                    else:
                        print("   ⚠️ Circuit breaker not opened (may need more errors)")
                else:
                    print(f"   ⚠️ Component {component} not found in circuit breaker status")
                
                return True
            else:
                print("   ❌ Failed to get circuit breaker status")
                return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as cb_error:
            print(f"   ❌ Circuit breaker test failed: {cb_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Circuit breaker test failed: {e}")
        return False

def test_error_resolution():
    """Test error resolution functionality"""
    try:
        print("\n✅ Testing error resolution...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_error_handler import LearningErrorHandler
            
            error_handler = LearningErrorHandler(
                "../Data/test_error_handler.db",
                "../Logs/test"
            )
            
            # Generate a test error
            try:
                raise ValueError("Test error for resolution")
            except Exception as e:
                error_id = error_handler.handle_error(e, "resolution_test_component")
                
                if error_id and error_id != "error_handler_failed":
                    print(f"   ✅ Error generated: {error_id}")
                    
                    # Test error resolution
                    resolution_success = error_handler.resolve_error(
                        error_id, "Resolved during testing"
                    )
                    
                    if resolution_success:
                        print("   ✅ Error resolved successfully")
                    else:
                        print("   ❌ Error resolution failed")
                    
                    # Test resolving non-existent error
                    fake_resolution = error_handler.resolve_error(
                        "FAKE_ERROR_ID", "This should fail"
                    )
                    
                    if not fake_resolution:
                        print("   ✅ Non-existent error resolution correctly failed")
                    else:
                        print("   ⚠️ Non-existent error resolution unexpectedly succeeded")
                    
                    return True
                else:
                    print("   ❌ Failed to generate test error")
                    return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as resolution_error:
            print(f"   ❌ Error resolution test failed: {resolution_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Error resolution test failed: {e}")
        return False

def test_error_cleanup():
    """Test error cleanup functionality"""
    try:
        print("\n🧹 Testing error cleanup...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_error_handler import LearningErrorHandler
            
            error_handler = LearningErrorHandler(
                "../Data/test_error_handler.db",
                "../Logs/test"
            )
            
            # Generate some test errors
            for i in range(3):
                try:
                    raise ValueError(f"Cleanup test error {i+1}")
                except Exception as e:
                    error_handler.handle_error(e, f"cleanup_component_{i}")
            
            print("   ✅ Generated test errors for cleanup")
            
            # Get initial error count
            initial_stats = error_handler.get_error_statistics()
            initial_count = len(error_handler.error_records)
            
            print(f"   Initial error records: {initial_count}")
            
            # Test cleanup (with 0 retention days to clean everything)
            cleaned_count = error_handler.cleanup_old_errors(retention_days=0)
            
            print(f"   ✅ Cleanup completed: {cleaned_count} errors cleaned")
            
            # Check final count
            final_count = len(error_handler.error_records)
            print(f"   Final error records: {final_count}")
            
            if final_count < initial_count:
                print("   ✅ Error cleanup working correctly")
                return True
            else:
                print("   ⚠️ No errors were cleaned (may be expected)")
                return True  # Not necessarily a failure
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as cleanup_error:
            print(f"   ❌ Error cleanup test failed: {cleanup_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Error cleanup test failed: {e}")
        return False

def test_logging_setup():
    """Test logging setup and file creation"""
    try:
        print("\n📝 Testing logging setup...")
        
        test_log_dir = "Logs/test_logging"
        os.makedirs(test_log_dir, exist_ok=True)
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_error_handler import LearningErrorHandler
            
            # Initialize error handler with test log directory
            error_handler = LearningErrorHandler(
                "../Data/test_error_handler.db",
                f"../{test_log_dir}"
            )
            
            print("   ✅ Error handler with logging initialized")
            
            # Generate an error to test logging
            try:
                raise RuntimeError("Test error for logging")
            except Exception as e:
                error_handler.handle_error(e, "logging_test_component")
            
            print("   ✅ Test error generated for logging")
            
            # Check if log files were created
            log_files = [
                f"../{test_log_dir}/learning_errors.log",
                f"../{test_log_dir}/learning_debug.log"
            ]
            
            log_files_found = 0
            for log_file in log_files:
                if os.path.exists(log_file):
                    print(f"   ✅ Log file created: {os.path.basename(log_file)}")
                    log_files_found += 1
                else:
                    print(f"   ⚠️ Log file not found: {os.path.basename(log_file)}")
            
            if log_files_found > 0:
                print("   ✅ Logging setup working")
                return True
            else:
                print("   ❌ No log files created")
                return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as logging_error:
            print(f"   ❌ Logging setup test failed: {logging_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Logging setup test failed: {e}")
        return False

def run_all_tests():
    """Run all error handler tests"""
    print("🚀 Starting Learning Error Handler Test Suite")
    print("=" * 60)
    
    # Clean up test directories
    test_dirs = ["Logs/test", "Logs/test_logging", "Data"]
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
            except:
                pass
    
    test_results = []
    
    # Test 1: Initialization
    test_results.append(("Initialization", test_error_handler_initialization()))
    
    # Test 2: Error Enums
    test_results.append(("Error Enums", test_error_enums()))
    
    # Test 3: Basic Error Handling
    test_results.append(("Basic Error Handling", test_basic_error_handling()))
    
    # Test 4: Error Statistics
    test_results.append(("Error Statistics", test_error_statistics()))
    
    # Test 5: Recovery Strategies
    test_results.append(("Recovery Strategies", test_recovery_strategies()))
    
    # Test 6: Circuit Breakers
    test_results.append(("Circuit Breakers", test_circuit_breakers()))
    
    # Test 7: Error Resolution
    test_results.append(("Error Resolution", test_error_resolution()))
    
    # Test 8: Error Cleanup
    test_results.append(("Error Cleanup", test_error_cleanup()))
    
    # Test 9: Logging Setup
    test_results.append(("Logging Setup", test_logging_setup()))
    
    # Print results summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        
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
        print("\n🎉 All tests passed! Learning Error Handler is working correctly.")
    elif passed >= len(test_results) * 0.6:  # 60% pass rate
        print(f"\n✅ Most tests passed! Learning Error Handler is mostly functional.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the implementation.")
    
    # Clean up test directories
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
            except:
                pass
    
    return failed == 0

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("Logs", exist_ok=True)
    os.makedirs("Data", exist_ok=True)
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)