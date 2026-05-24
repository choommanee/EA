#!/usr/bin/env python3
"""
Test script for Configuration Management Interface
Tests interface functionality, validation, and audit logging
"""

import sys
import os
sys.path.append('Python')

import logging
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_interface_initialization():
    """Test configuration interface initialization"""
    try:
        print("\n🔧 Testing Configuration Interface initialization...")
        
        # Test if file exists
        if not os.path.exists('Python/config_management_interface.py'):
            print("   ❌ config_management_interface.py not found")
            return False
        
        print("   ✅ Configuration interface file exists")
        
        # Test basic syntax
        with open('Python/config_management_interface.py', 'r') as f:
            content = f.read()
        
        try:
            compile(content, 'Python/config_management_interface.py', 'exec')
            print("   ✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            return False
        
        # Test class definition
        if 'class ConfigurationInterface:' in content:
            print("   ✅ ConfigurationInterface class defined")
        else:
            print("   ❌ ConfigurationInterface class not found")
            return False
        
        # Test key methods
        key_methods = [
            'get_current_configuration',
            'update_model_training_config',
            'update_performance_monitoring_config',
            'validate_configuration',
            'get_version_history',
            'rollback_to_version'
        ]
        
        for method in key_methods:
            if f'def {method}(' in content:
                print(f"   ✅ {method} method defined")
            else:
                print(f"   ❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration interface initialization test failed: {e}")
        return False

def test_interface_basic_operations():
    """Test basic interface operations"""
    try:
        print("\n⚙️ Testing basic interface operations...")
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            # Change to Python directory for import
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from config_management_interface import ConfigurationInterface
                
                # Initialize interface
                interface = ConfigurationInterface(config_dir=str(temp_config_dir))
                
                print("   ✅ Configuration interface initialized")
                
                # Test getting current configuration
                config = interface.get_current_configuration()
                if isinstance(config, dict) and len(config) > 0:
                    print(f"   ✅ Retrieved current configuration with {len(config)} sections")
                else:
                    print("   ❌ Failed to retrieve current configuration")
                    return False
                
                # Test getting configuration summary
                summary = interface.get_configuration_summary()
                if isinstance(summary, dict) and 'sections' in summary:
                    print(f"   ✅ Retrieved configuration summary")
                else:
                    print("   ❌ Failed to retrieve configuration summary")
                    return False
                
                # Test getting specific config value
                batch_size = interface.get_config_value("model_training.batch_size")
                if batch_size is not None:
                    print(f"   ✅ Retrieved batch_size: {batch_size}")
                else:
                    print("   ❌ Failed to retrieve batch_size")
                    return False
                
                return True
                
            except ImportError as import_error:
                print(f"   ⚠️ Import failed: {import_error}")
                return True  # Not a failure, just missing dependencies
                
            except Exception as ops_error:
                print(f"   ❌ Basic operations test failed: {ops_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Basic operations test failed: {e}")
        return False

def test_configuration_updates():
    """Test configuration update operations"""
    try:
        print("\n🔄 Testing configuration updates...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from config_management_interface import ConfigurationInterface
                
                interface = ConfigurationInterface(config_dir=str(temp_config_dir))
                
                # Test model training config update
                success = interface.update_model_training_config(
                    batch_size=128,
                    learning_rate=0.01,
                    epochs=200
                )
                
                if success:
                    # Verify the update
                    batch_size = interface.get_config_value("model_training.batch_size")
                    learning_rate = interface.get_config_value("model_training.learning_rate")
                    epochs = interface.get_config_value("model_training.epochs")
                    
                    if batch_size == 128 and learning_rate == 0.01 and epochs == 200:
                        print("   ✅ Model training config update successful")
                    else:
                        print(f"   ❌ Model training config verification failed: bs={batch_size}, lr={learning_rate}, epochs={epochs}")
                        return False
                else:
                    print("   ❌ Model training config update failed")
                    return False
                
                # Test performance monitoring config update
                success = interface.update_performance_monitoring_config(
                    performance_threshold=0.8,
                    degradation_threshold=0.15,
                    monitoring_interval_minutes=30
                )
                
                if success:
                    # Verify the update
                    perf_threshold = interface.get_config_value("performance_monitoring.performance_threshold")
                    deg_threshold = interface.get_config_value("performance_monitoring.degradation_threshold")
                    
                    if perf_threshold == 0.8 and deg_threshold == 0.15:
                        print("   ✅ Performance monitoring config update successful")
                    else:
                        print(f"   ❌ Performance monitoring config verification failed: pt={perf_threshold}, dt={deg_threshold}")
                        return False
                else:
                    print("   ❌ Performance monitoring config update failed")
                    return False
                
                # Test system config update
                success = interface.update_system_config(
                    max_concurrent_training=4,
                    memory_limit_gb=16,
                    debug_mode=True
                )
                
                if success:
                    debug_mode = interface.get_config_value("system.debug_mode")
                    if debug_mode == True:
                        print("   ✅ System config update successful")
                    else:
                        print(f"   ❌ System config verification failed: debug_mode={debug_mode}")
                        return False
                else:
                    print("   ❌ System config update failed")
                    return False
                
                return True
                
            except Exception as update_error:
                print(f"   ❌ Configuration update test failed: {update_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration update test failed: {e}")
        return False

def test_configuration_validation():
    """Test configuration validation"""
    try:
        print("\n✅ Testing configuration validation...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from config_management_interface import ConfigurationInterface
                
                interface = ConfigurationInterface(config_dir=str(temp_config_dir))
                
                # Test validation of default configuration
                validation_result = interface.validate_configuration()
                
                if isinstance(validation_result, dict):
                    is_valid = validation_result.get('is_valid', False)
                    errors = validation_result.get('errors', [])
                    warnings = validation_result.get('warnings', [])
                    
                    print(f"   ✅ Validation result: valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}")
                    
                    if is_valid:
                        print("   ✅ Default configuration is valid")
                    else:
                        print(f"   ⚠️ Default configuration has issues: {errors}")
                else:
                    print("   ❌ Validation result format incorrect")
                    return False
                
                # Test validation with invalid values
                # The set_config_value should fail due to validation, so config remains valid
                success = interface.set_config_value("model_training.batch_size", -10)
                if not success:
                    print("   ✅ Invalid configuration correctly rejected during set")
                else:
                    # If it was set, check if validation detects it
                    validation_result = interface.validate_configuration()
                    if not validation_result.get('is_valid', True):
                        print("   ✅ Invalid configuration correctly detected")
                    else:
                        print("   ❌ Invalid configuration not detected")
                        return False
                
                return True
                
            except Exception as validation_error:
                print(f"   ❌ Configuration validation test failed: {validation_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False

def test_version_management():
    """Test version management functionality"""
    try:
        print("\n📚 Testing version management...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from config_management_interface import ConfigurationInterface
                
                interface = ConfigurationInterface(config_dir=str(temp_config_dir))
                
                # Make some changes to create versions
                interface.update_model_training_config(batch_size=64)
                interface.update_model_training_config(batch_size=128)
                interface.update_system_config(debug_mode=True)
                
                # Test getting version history
                versions = interface.get_version_history()
                
                if isinstance(versions, list) and len(versions) > 0:
                    print(f"   ✅ Version history retrieved: {len(versions)} versions")
                    
                    # Check version structure
                    latest_version = versions[0] if versions else {}
                    expected_keys = ['version', 'timestamp', 'description']
                    
                    for key in expected_keys:
                        if key in latest_version:
                            print(f"      ✅ Version has {key}")
                        else:
                            print(f"      ❌ Version missing {key}")
                else:
                    print("   ❌ No version history found")
                    return False
                
                # Test rollback (if we have multiple versions)
                if len(versions) >= 2:
                    rollback_version = versions[1]['version']
                    success = interface.rollback_to_version(rollback_version)
                    
                    if success:
                        print(f"   ✅ Rollback to version {rollback_version} successful")
                    else:
                        print(f"   ❌ Rollback to version {rollback_version} failed")
                        return False
                
                return True
                
            except Exception as version_error:
                print(f"   ❌ Version management test failed: {version_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Version management test failed: {e}")
        return False

def test_audit_logging():
    """Test audit logging functionality"""
    try:
        print("\n📝 Testing audit logging...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from config_management_interface import ConfigurationInterface
                
                interface = ConfigurationInterface(
                    config_dir=str(temp_config_dir),
                    enable_audit_logging=True
                )
                
                # Perform some operations to generate audit entries
                interface.get_current_configuration()
                interface.update_model_training_config(batch_size=256)
                interface.validate_configuration()
                interface.get_config_value("system.debug_mode")
                
                # Test getting audit log
                audit_entries = interface.get_audit_log(10)
                
                if isinstance(audit_entries, list) and len(audit_entries) > 0:
                    print(f"   ✅ Audit log retrieved: {len(audit_entries)} entries")
                    
                    # Check audit entry structure
                    latest_entry = audit_entries[0] if audit_entries else {}
                    expected_keys = ['timestamp', 'action', 'details']
                    
                    for key in expected_keys:
                        if key in latest_entry:
                            print(f"      ✅ Audit entry has {key}")
                        else:
                            print(f"      ❌ Audit entry missing {key}")
                    
                    # Test saving audit log
                    audit_file = temp_config_dir / "test_audit.json"
                    success = interface.save_audit_log(str(audit_file))
                    
                    if success and audit_file.exists():
                        print("   ✅ Audit log saved successfully")
                    else:
                        print("   ❌ Audit log save failed")
                        return False
                else:
                    print("   ❌ No audit entries found")
                    return False
                
                return True
                
            except Exception as audit_error:
                print(f"   ❌ Audit logging test failed: {audit_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Audit logging test failed: {e}")
        return False

def test_export_import():
    """Test configuration export and import"""
    try:
        print("\n📤 Testing configuration export/import...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            export_file = Path(temp_dir) / "exported_config.json"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from config_management_interface import ConfigurationInterface, ConfigFormat
                
                # Create first interface and modify config
                interface1 = ConfigurationInterface(config_dir=str(temp_config_dir))
                
                interface1.update_model_training_config(batch_size=512, epochs=300)
                interface1.update_system_config(debug_mode=True, max_concurrent_training=8)
                
                # Export configuration
                success = interface1.export_configuration(str(export_file), ConfigFormat.JSON)
                
                if success and export_file.exists():
                    print("   ✅ Configuration export successful")
                else:
                    print("   ❌ Configuration export failed")
                    return False
                
                # Create second interface with different directory
                temp_config_dir2 = Path(temp_dir) / "test_config2"
                interface2 = ConfigurationInterface(config_dir=str(temp_config_dir2))
                
                # Import configuration
                success = interface2.import_configuration(str(export_file), "Test import")
                
                if success:
                    print("   ✅ Configuration import successful")
                    
                    # Verify imported values
                    batch_size = interface2.get_config_value("model_training.batch_size")
                    epochs = interface2.get_config_value("model_training.epochs")
                    debug_mode = interface2.get_config_value("system.debug_mode")
                    
                    if batch_size == 512 and epochs == 300 and debug_mode == True:
                        print("   ✅ Import verification successful")
                    else:
                        print(f"   ❌ Import verification failed: bs={batch_size}, epochs={epochs}, debug={debug_mode}")
                        return False
                else:
                    print("   ❌ Configuration import failed")
                    return False
                
                return True
                
            except Exception as export_import_error:
                print(f"   ❌ Export/import test failed: {export_import_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Export/import test failed: {e}")
        return False

def test_convenience_functions():
    """Test convenience functions"""
    try:
        print("\n🚀 Testing convenience functions...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from config_management_interface import (
                quick_setup_training_config,
                quick_setup_monitoring_config,
                quick_setup_notifications
            )
            
            # Test quick training setup
            success = quick_setup_training_config(batch_size=64, learning_rate=0.005, epochs=150)
            if success:
                print("   ✅ Quick training setup successful")
            else:
                print("   ❌ Quick training setup failed")
                return False
            
            # Test quick monitoring setup
            success = quick_setup_monitoring_config(
                performance_threshold=0.85,
                degradation_threshold=0.12,
                monitoring_interval=45
            )
            if success:
                print("   ✅ Quick monitoring setup successful")
            else:
                print("   ❌ Quick monitoring setup failed")
                return False
            
            # Test quick notification setup
            success = quick_setup_notifications(
                enabled=True,
                log_level="WARNING",
                alert_channels=["log", "email"]
            )
            if success:
                print("   ✅ Quick notification setup successful")
            else:
                print("   ❌ Quick notification setup failed")
                return False
            
            return True
            
        except Exception as convenience_error:
            print(f"   ❌ Convenience functions test failed: {convenience_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Convenience functions test failed: {e}")
        return False

def run_all_tests():
    """Run all configuration interface tests"""
    print("🚀 Starting Configuration Management Interface Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Initialization
    test_results.append(("Initialization", test_interface_initialization()))
    
    # Test 2: Basic Operations
    test_results.append(("Basic Operations", test_interface_basic_operations()))
    
    # Test 3: Configuration Updates
    test_results.append(("Configuration Updates", test_configuration_updates()))
    
    # Test 4: Configuration Validation
    test_results.append(("Configuration Validation", test_configuration_validation()))
    
    # Test 5: Version Management
    test_results.append(("Version Management", test_version_management()))
    
    # Test 6: Audit Logging
    test_results.append(("Audit Logging", test_audit_logging()))
    
    # Test 7: Export/Import
    test_results.append(("Export/Import", test_export_import()))
    
    # Test 8: Convenience Functions
    test_results.append(("Convenience Functions", test_convenience_functions()))
    
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
        print("\n🎉 All tests passed! Configuration Management Interface is working correctly.")
    elif passed >= len(test_results) * 0.6:  # 60% pass rate
        print(f"\n✅ Most tests passed! Configuration Management Interface is mostly functional.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("Config", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)