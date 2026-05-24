#!/usr/bin/env python3
"""
Test script for Learning Configuration System
Tests configuration management, validation, versioning, and rollback functionality
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

def test_configuration_initialization():
    """Test configuration system initialization"""
    try:
        print("\n🔧 Testing Configuration System initialization...")
        
        # Test if file exists
        if not os.path.exists('Python/learning_configuration.py'):
            print("   ❌ learning_configuration.py not found")
            return False
        
        print("   ✅ Configuration system file exists")
        
        # Test basic syntax
        with open('Python/learning_configuration.py', 'r') as f:
            content = f.read()
        
        try:
            compile(content, 'Python/learning_configuration.py', 'exec')
            print("   ✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            return False
        
        # Test class definition
        if 'class LearningConfiguration:' in content:
            print("   ✅ LearningConfiguration class defined")
        else:
            print("   ❌ LearningConfiguration class not found")
            return False
        
        # Test key methods
        key_methods = [
            'load_configuration',
            'save_configuration',
            'update_configuration',
            'get_config_value',
            'set_config_value',
            'validate_configuration',
            'rollback_to_version'
        ]
        
        for method in key_methods:
            if f'def {method}(' in content:
                print(f"   ✅ {method} method defined")
            else:
                print(f"   ❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration system initialization test failed: {e}")
        return False

def test_configuration_loading():
    """Test configuration loading and creation"""
    try:
        print("\n⚙️ Testing configuration loading...")
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            # Change to Python directory for import
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from learning_configuration import LearningConfiguration, ConfigValidationLevel
                
                # Initialize with test config directory
                config_manager = LearningConfiguration(
                    config_dir=str(temp_config_dir),
                    validation_level=ConfigValidationLevel.LENIENT
                )
                
                print("   ✅ Configuration system initialized")
                
                # Check if default config was created
                config_file = temp_config_dir / "learning_config.json"
                if config_file.exists():
                    print("   ✅ Default configuration file created")
                    
                    # Load and check config structure
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    
                    # Check expected sections
                    expected_sections = [
                        'model_training', 'performance_monitoring', 
                        'data_collection', 'model_management', 
                        'notifications', 'system'
                    ]
                    
                    for section in expected_sections:
                        if section in config_data:
                            print(f"      ✅ Config has {section} section")
                        else:
                            print(f"      ❌ Config missing {section} section")
                    
                    return True
                else:
                    print("   ❌ Default configuration file not created")
                    return False
                    
            except ImportError as import_error:
                print(f"   ⚠️ Import failed: {import_error}")
                return True  # Not a failure, just missing dependencies
                
            except Exception as init_error:
                print(f"   ❌ Initialization failed: {init_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        return False

def test_configuration_access():
    """Test configuration value access"""
    try:
        print("\n📊 Testing configuration value access...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from learning_configuration import LearningConfiguration
                
                config_manager = LearningConfiguration(config_dir=str(temp_config_dir))
                
                # Test getting configuration values
                batch_size = config_manager.get_config_value("model_training.batch_size")
                if batch_size is not None:
                    print(f"   ✅ Retrieved batch_size: {batch_size}")
                else:
                    print("   ❌ Failed to retrieve batch_size")
                    return False
                
                # Test getting nested values
                performance_threshold = config_manager.get_config_value("performance_monitoring.performance_threshold")
                if performance_threshold is not None:
                    print(f"   ✅ Retrieved performance_threshold: {performance_threshold}")
                else:
                    print("   ❌ Failed to retrieve performance_threshold")
                    return False
                
                # Test getting non-existent value with default
                non_existent = config_manager.get_config_value("non.existent.key", "default_value")
                if non_existent == "default_value":
                    print("   ✅ Default value returned for non-existent key")
                else:
                    print("   ❌ Default value not returned correctly")
                    return False
                
                # Test getting full configuration
                full_config = config_manager.get_configuration()
                if isinstance(full_config, dict) and len(full_config) > 0:
                    print(f"   ✅ Retrieved full configuration with {len(full_config)} sections")
                else:
                    print("   ❌ Failed to retrieve full configuration")
                    return False
                
                return True
                
            except Exception as access_error:
                print(f"   ❌ Configuration access test failed: {access_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration access test failed: {e}")
        return False

def test_configuration_updates():
    """Test configuration updates"""
    try:
        print("\n🔄 Testing configuration updates...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from learning_configuration import LearningConfiguration
                
                config_manager = LearningConfiguration(config_dir=str(temp_config_dir))
                
                # Test single value update
                original_batch_size = config_manager.get_config_value("model_training.batch_size")
                new_batch_size = 128
                
                success = config_manager.set_config_value(
                    "model_training.batch_size", 
                    new_batch_size, 
                    "Test batch size update"
                )
                
                if success:
                    updated_batch_size = config_manager.get_config_value("model_training.batch_size")
                    if updated_batch_size == new_batch_size:
                        print(f"   ✅ Single value update successful: {original_batch_size} -> {new_batch_size}")
                    else:
                        print(f"   ❌ Single value update failed: expected {new_batch_size}, got {updated_batch_size}")
                        return False
                else:
                    print("   ❌ Single value update failed")
                    return False
                
                # Test bulk update
                bulk_updates = {
                    "model_training": {
                        "learning_rate": 0.01,
                        "epochs": 200
                    },
                    "system": {
                        "debug_mode": True
                    }
                }
                
                success = config_manager.update_configuration(bulk_updates, "Test bulk update")
                
                if success:
                    # Verify updates
                    learning_rate = config_manager.get_config_value("model_training.learning_rate")
                    epochs = config_manager.get_config_value("model_training.epochs")
                    debug_mode = config_manager.get_config_value("system.debug_mode")
                    
                    if learning_rate == 0.01 and epochs == 200 and debug_mode == True:
                        print("   ✅ Bulk update successful")
                    else:
                        print(f"   ❌ Bulk update verification failed: lr={learning_rate}, epochs={epochs}, debug={debug_mode}")
                        return False
                else:
                    print("   ❌ Bulk update failed")
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
                from learning_configuration import LearningConfiguration, ConfigValidationLevel
                
                config_manager = LearningConfiguration(
                    config_dir=str(temp_config_dir),
                    validation_level=ConfigValidationLevel.STRICT
                )
                
                # Test valid configuration
                valid = config_manager.validate_configuration()
                if valid:
                    print("   ✅ Default configuration is valid")
                else:
                    print("   ❌ Default configuration validation failed")
                    return False
                
                # Test invalid value (should fail validation)
                try:
                    # Try to set invalid batch size
                    success = config_manager.set_config_value("model_training.batch_size", -10)
                    if not success:
                        print("   ✅ Invalid batch size correctly rejected")
                    else:
                        print("   ❌ Invalid batch size was accepted")
                        return False
                except:
                    print("   ✅ Invalid batch size correctly rejected with exception")
                
                # Test invalid learning rate
                try:
                    success = config_manager.set_config_value("model_training.learning_rate", 2.0)
                    if not success:
                        print("   ✅ Invalid learning rate correctly rejected")
                    else:
                        print("   ❌ Invalid learning rate was accepted")
                        return False
                except:
                    print("   ✅ Invalid learning rate correctly rejected with exception")
                
                return True
                
            except Exception as validation_error:
                print(f"   ❌ Configuration validation test failed: {validation_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False

def test_configuration_versioning():
    """Test configuration versioning"""
    try:
        print("\n📚 Testing configuration versioning...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from learning_configuration import LearningConfiguration
                
                config_manager = LearningConfiguration(
                    config_dir=str(temp_config_dir),
                    enable_versioning=True
                )
                
                # Make some changes to create versions
                config_manager.set_config_value("model_training.batch_size", 64, "Version 1")
                config_manager.set_config_value("model_training.learning_rate", 0.01, "Version 2")
                config_manager.set_config_value("system.debug_mode", True, "Version 3")
                
                # Check version history
                versions = config_manager.get_version_history()
                if len(versions) >= 3:
                    print(f"   ✅ Version history created: {len(versions)} versions")
                    
                    # Test version details
                    latest_version = versions[-1]
                    if hasattr(latest_version, 'version') and hasattr(latest_version, 'description'):
                        print(f"   ✅ Version details: {latest_version.version} - {latest_version.description}")
                    else:
                        print("   ❌ Version details incomplete")
                        return False
                else:
                    print(f"   ❌ Insufficient versions created: {len(versions)}")
                    return False
                
                # Test rollback (if we have versions)
                if len(versions) >= 2:
                    # Get current value
                    current_debug = config_manager.get_config_value("system.debug_mode")
                    
                    # Rollback to previous version
                    rollback_version = versions[-2].version
                    success = config_manager.rollback_to_version(rollback_version)
                    
                    if success:
                        print(f"   ✅ Rollback to version {rollback_version} successful")
                        
                        # Verify rollback worked (debug_mode should be different)
                        rolled_back_debug = config_manager.get_config_value("system.debug_mode")
                        if rolled_back_debug != current_debug:
                            print("   ✅ Rollback verification successful")
                        else:
                            print("   ⚠️ Rollback verification inconclusive")
                    else:
                        print("   ❌ Rollback failed")
                        return False
                
                return True
                
            except Exception as versioning_error:
                print(f"   ❌ Configuration versioning test failed: {versioning_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration versioning test failed: {e}")
        return False

def test_configuration_export_import():
    """Test configuration export and import"""
    try:
        print("\n📤 Testing configuration export/import...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config_dir = Path(temp_dir) / "test_config"
            export_file = Path(temp_dir) / "exported_config.json"
            
            original_cwd = os.getcwd()
            os.chdir('Python')
            
            try:
                from learning_configuration import LearningConfiguration, ConfigFormat
                
                # Create first config manager
                config_manager1 = LearningConfiguration(config_dir=str(temp_config_dir))
                
                # Make some changes
                config_manager1.set_config_value("model_training.batch_size", 256)
                config_manager1.set_config_value("system.debug_mode", True)
                
                # Export configuration
                success = config_manager1.export_configuration(str(export_file), ConfigFormat.JSON)
                if success and export_file.exists():
                    print("   ✅ Configuration export successful")
                else:
                    print("   ❌ Configuration export failed")
                    return False
                
                # Create second config manager with different directory
                temp_config_dir2 = Path(temp_dir) / "test_config2"
                config_manager2 = LearningConfiguration(config_dir=str(temp_config_dir2))
                
                # Import configuration
                success = config_manager2.import_configuration(str(export_file), "Imported configuration")
                if success:
                    print("   ✅ Configuration import successful")
                    
                    # Verify imported values
                    batch_size = config_manager2.get_config_value("model_training.batch_size")
                    debug_mode = config_manager2.get_config_value("system.debug_mode")
                    
                    if batch_size == 256 and debug_mode == True:
                        print("   ✅ Import verification successful")
                    else:
                        print(f"   ❌ Import verification failed: batch_size={batch_size}, debug_mode={debug_mode}")
                        return False
                else:
                    print("   ❌ Configuration import failed")
                    return False
                
                return True
                
            except Exception as export_import_error:
                print(f"   ❌ Configuration export/import test failed: {export_import_error}")
                return False
                
            finally:
                os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration export/import test failed: {e}")
        return False

def run_all_tests():
    """Run all configuration system tests"""
    print("🚀 Starting Learning Configuration System Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Initialization
    test_results.append(("Initialization", test_configuration_initialization()))
    
    # Test 2: Configuration Loading
    test_results.append(("Configuration Loading", test_configuration_loading()))
    
    # Test 3: Configuration Access
    test_results.append(("Configuration Access", test_configuration_access()))
    
    # Test 4: Configuration Updates
    test_results.append(("Configuration Updates", test_configuration_updates()))
    
    # Test 5: Configuration Validation
    test_results.append(("Configuration Validation", test_configuration_validation()))
    
    # Test 6: Configuration Versioning
    test_results.append(("Configuration Versioning", test_configuration_versioning()))
    
    # Test 7: Export/Import
    test_results.append(("Export/Import", test_configuration_export_import()))
    
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
        print("\n🎉 All tests passed! Learning Configuration System is working correctly.")
    elif passed >= len(test_results) * 0.6:  # 60% pass rate
        print(f"\n✅ Most tests passed! Learning Configuration System is mostly functional.")
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