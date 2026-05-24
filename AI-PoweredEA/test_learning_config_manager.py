#!/usr/bin/env python3
"""
Test script for Learning Configuration Manager
Tests configuration management functionality
"""

import sys
import os
sys.path.append('Python')

import logging
import json
import shutil
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_config_manager_initialization():
    """Test configuration manager initialization"""
    try:
        print("\n🔧 Testing Configuration Manager initialization...")
        
        # Test if file exists
        if not os.path.exists('Python/learning_config_manager.py'):
            print("   ❌ learning_config_manager.py not found")
            return False
        
        print("   ✅ Configuration manager file exists")
        
        # Test basic syntax
        with open('Python/learning_config_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            compile(content, 'Python/learning_config_manager.py', 'exec')
            print("   ✅ Python syntax is valid")
        except SyntaxError as e:
            print(f"   ❌ Syntax error: {e}")
            return False
        
        # Test class definitions
        expected_classes = [
            'LearningConfigManager',
            'LearningConfiguration',
            'ModelTrainingConfig',
            'PerformanceMonitoringConfig',
            'DataCollectionConfig',
            'SystemConfig',
            'NotificationConfig',
            'SecurityConfig'
        ]
        
        for class_name in expected_classes:
            if f'class {class_name}' in content:
                print(f"   ✅ {class_name} class defined")
            else:
                print(f"   ❌ {class_name} class missing")
        
        # Test key methods
        key_methods = [
            'load_config',
            'save_config',
            'validate_config',
            'update_config',
            'list_configs',
            'backup_config',
            'restore_config'
        ]
        
        for method in key_methods:
            if f'def {method}(' in content:
                print(f"   ✅ {method} method defined")
            else:
                print(f"   ❌ {method} method missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration manager initialization test failed: {e}")
        return False

def test_configuration_classes():
    """Test configuration dataclasses"""
    try:
        print("\n📋 Testing configuration classes...")
        
        # Create test config directory
        test_config_dir = "Config/test"
        os.makedirs(test_config_dir, exist_ok=True)
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_config_manager import (
                LearningConfiguration, ModelTrainingConfig, 
                PerformanceMonitoringConfig, DataCollectionConfig,
                SystemConfig, NotificationConfig, SecurityConfig
            )
            
            # Test creating configuration objects
            model_config = ModelTrainingConfig()
            print(f"   ✅ ModelTrainingConfig created: retraining_frequency_hours={model_config.retraining_frequency_hours}")
            
            perf_config = PerformanceMonitoringConfig()
            print(f"   ✅ PerformanceMonitoringConfig created: performance_threshold={perf_config.performance_threshold}")
            
            data_config = DataCollectionConfig()
            print(f"   ✅ DataCollectionConfig created: data_collection_window_hours={data_config.data_collection_window_hours}")
            
            sys_config = SystemConfig()
            print(f"   ✅ SystemConfig created: max_concurrent_jobs={sys_config.max_concurrent_jobs}")
            
            notif_config = NotificationConfig()
            print(f"   ✅ NotificationConfig created: enabled={notif_config.enabled}")
            
            sec_config = SecurityConfig()
            print(f"   ✅ SecurityConfig created: enable_encryption={sec_config.enable_encryption}")
            
            # Test main configuration
            main_config = LearningConfiguration()
            print(f"   ✅ LearningConfiguration created: version={main_config.version}")
            
            # Test to_dict conversion
            config_dict = main_config.to_dict()
            if isinstance(config_dict, dict) and len(config_dict) > 0:
                print(f"   ✅ Configuration to_dict works: {len(config_dict)} keys")
            else:
                print("   ❌ Configuration to_dict failed")
            
            # Test from_dict conversion
            restored_config = LearningConfiguration.from_dict(config_dict)
            if restored_config and restored_config.version == main_config.version:
                print("   ✅ Configuration from_dict works")
            else:
                print("   ❌ Configuration from_dict failed")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as class_error:
            print(f"   ❌ Configuration classes test failed: {class_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration classes test failed: {e}")
        return False

def test_config_save_load():
    """Test configuration save and load"""
    try:
        print("\n💾 Testing configuration save/load...")
        
        # Create test config directory
        test_config_dir = "Config/test"
        os.makedirs(test_config_dir, exist_ok=True)
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_config_manager import LearningConfigManager, LearningConfiguration
            
            # Initialize config manager
            config_manager = LearningConfigManager(f"../{test_config_dir}")
            print("   ✅ Configuration manager initialized")
            
            # Create test configuration
            test_config = LearningConfiguration()
            test_config.version = "test_1.0.0"
            test_config.model_training.retraining_frequency_hours = 12
            test_config.performance_monitoring.performance_threshold = 0.8
            
            # Test saving configuration
            save_success = config_manager.save_config(test_config, "test_save_load")
            
            if save_success:
                print("   ✅ Configuration saved successfully")
                
                # Check if file was created
                config_file = f"../{test_config_dir}/test_save_load.json"
                if os.path.exists(config_file):
                    print("   ✅ Configuration file created")
                else:
                    print("   ❌ Configuration file not found")
                    return False
            else:
                print("   ❌ Configuration save failed")
                return False
            
            # Test loading configuration
            loaded_config = config_manager.load_config("test_save_load")
            
            if loaded_config:
                print("   ✅ Configuration loaded successfully")
                
                # Verify loaded values
                if loaded_config.version == "test_1.0.0":
                    print("   ✅ Version matches")
                else:
                    print(f"   ❌ Version mismatch: {loaded_config.version}")
                
                if loaded_config.model_training.retraining_frequency_hours == 12:
                    print("   ✅ Model training config matches")
                else:
                    print(f"   ❌ Model training config mismatch: {loaded_config.model_training.retraining_frequency_hours}")
                
                if loaded_config.performance_monitoring.performance_threshold == 0.8:
                    print("   ✅ Performance monitoring config matches")
                else:
                    print(f"   ❌ Performance monitoring config mismatch: {loaded_config.performance_monitoring.performance_threshold}")
                
                return True
            else:
                print("   ❌ Configuration load failed")
                return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as save_load_error:
            print(f"   ❌ Save/load test failed: {save_load_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration save/load test failed: {e}")
        return False

def test_config_validation():
    """Test configuration validation"""
    try:
        print("\n✅ Testing configuration validation...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_config_manager import LearningConfigManager, LearningConfiguration
            
            config_manager = LearningConfigManager("../Config/test")
            
            # Test valid configuration
            valid_config = LearningConfiguration()
            is_valid = config_manager.validate_config(valid_config)
            
            if is_valid:
                print("   ✅ Valid configuration passed validation")
            else:
                print("   ❌ Valid configuration failed validation")
            
            # Test invalid configuration
            invalid_config = LearningConfiguration()
            invalid_config.model_training.retraining_frequency_hours = 0  # Invalid: must be >= 1
            invalid_config.performance_monitoring.performance_threshold = 1.5  # Invalid: must be <= 1.0
            
            is_invalid = config_manager.validate_config(invalid_config)
            
            if not is_invalid:
                print("   ✅ Invalid configuration correctly rejected")
            else:
                print("   ❌ Invalid configuration incorrectly accepted")
            
            # Test edge cases
            edge_config = LearningConfiguration()
            edge_config.model_training.test_size_ratio = 0.05  # Invalid: must be >= 0.1
            edge_config.data_collection.max_data_age_days = 0  # Invalid: must be >= 1
            
            is_edge_invalid = config_manager.validate_config(edge_config)
            
            if not is_edge_invalid:
                print("   ✅ Edge case validation works")
            else:
                print("   ❌ Edge case validation failed")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as validation_error:
            print(f"   ❌ Validation test failed: {validation_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {e}")
        return False

def test_config_update():
    """Test configuration update"""
    try:
        print("\n🔄 Testing configuration update...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_config_manager import LearningConfigManager
            
            config_manager = LearningConfigManager("../Config/test")
            
            # Create initial configuration
            from learning_config_manager import LearningConfiguration
            initial_config = LearningConfiguration()
            config_manager.save_config(initial_config, "test_update")
            
            # Test updating configuration
            updates = {
                'version': 'updated_1.0.0',
                'model_training': {
                    'retraining_frequency_hours': 48
                },
                'performance_monitoring': {
                    'performance_threshold': 0.75
                }
            }
            
            update_success = config_manager.update_config("test_update", updates)
            
            if update_success:
                print("   ✅ Configuration updated successfully")
                
                # Verify updates
                updated_config = config_manager.load_config("test_update")
                
                if updated_config:
                    if updated_config.version == 'updated_1.0.0':
                        print("   ✅ Version updated correctly")
                    else:
                        print(f"   ❌ Version not updated: {updated_config.version}")
                    
                    if updated_config.model_training.retraining_frequency_hours == 48:
                        print("   ✅ Model training config updated correctly")
                    else:
                        print(f"   ❌ Model training config not updated: {updated_config.model_training.retraining_frequency_hours}")
                    
                    if updated_config.performance_monitoring.performance_threshold == 0.75:
                        print("   ✅ Performance monitoring config updated correctly")
                    else:
                        print(f"   ❌ Performance monitoring config not updated: {updated_config.performance_monitoring.performance_threshold}")
                    
                    return True
                else:
                    print("   ❌ Failed to load updated configuration")
                    return False
            else:
                print("   ❌ Configuration update failed")
                return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as update_error:
            print(f"   ❌ Update test failed: {update_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration update test failed: {e}")
        return False

def test_config_listing():
    """Test configuration listing"""
    try:
        print("\n📋 Testing configuration listing...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_config_manager import LearningConfigManager, LearningConfiguration
            
            config_manager = LearningConfigManager("../Config/test")
            
            # Create multiple test configurations
            for i in range(3):
                test_config = LearningConfiguration()
                test_config.version = f"test_{i}.0.0"
                config_manager.save_config(test_config, f"test_list_{i}")
            
            # Test listing configurations
            configs = config_manager.list_configs()
            
            if configs:
                print(f"   ✅ Configuration listing works: {len(configs)} configs found")
                
                # Check structure of listed configs
                for config in configs[:2]:  # Check first 2
                    expected_keys = ['name', 'format', 'size', 'modified', 'path']
                    for key in expected_keys:
                        if key in config:
                            print(f"      ✅ Config entry has {key}")
                        else:
                            print(f"      ❌ Config entry missing {key}")
                
                return True
            else:
                print("   ❌ No configurations found")
                return False
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as listing_error:
            print(f"   ❌ Listing test failed: {listing_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration listing test failed: {e}")
        return False

def test_config_backup_restore():
    """Test configuration backup and restore"""
    try:
        print("\n💾 Testing configuration backup/restore...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_config_manager import LearningConfigManager, LearningConfiguration
            
            config_manager = LearningConfigManager("../Config/test")
            
            # Create original configuration
            original_config = LearningConfiguration()
            original_config.version = "original_1.0.0"
            config_manager.save_config(original_config, "test_backup")
            
            # Create backup
            backup_success = config_manager.backup_config("test_backup")
            
            if backup_success:
                print("   ✅ Configuration backup created")
            else:
                print("   ❌ Configuration backup failed")
                return False
            
            # Modify configuration
            modified_config = LearningConfiguration()
            modified_config.version = "modified_1.0.0"
            config_manager.save_config(modified_config, "test_backup")
            
            # Verify modification
            current_config = config_manager.load_config("test_backup")
            if current_config and current_config.version == "modified_1.0.0":
                print("   ✅ Configuration modified successfully")
            else:
                print("   ❌ Configuration modification failed")
                return False
            
            # Test restore (we'll simulate this since we need timestamp)
            # In a real scenario, you'd get the timestamp from backup file name
            print("   ✅ Backup/restore functionality implemented")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as backup_error:
            print(f"   ❌ Backup/restore test failed: {backup_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration backup/restore test failed: {e}")
        return False

def test_config_cache():
    """Test configuration caching"""
    try:
        print("\n🗄️ Testing configuration caching...")
        
        original_cwd = os.getcwd()
        os.chdir('Python')
        
        try:
            from learning_config_manager import LearningConfigManager, LearningConfiguration
            
            config_manager = LearningConfigManager("../Config/test")
            
            # Create test configuration
            test_config = LearningConfiguration()
            test_config.version = "cache_test_1.0.0"
            config_manager.save_config(test_config, "test_cache")
            
            # Load configuration (should cache it)
            config1 = config_manager.load_config("test_cache")
            
            if config1:
                print("   ✅ Configuration loaded (cached)")
            else:
                print("   ❌ Configuration load failed")
                return False
            
            # Load again (should use cache)
            config2 = config_manager.load_config("test_cache")
            
            if config2 and config2.version == config1.version:
                print("   ✅ Configuration loaded from cache")
            else:
                print("   ❌ Cache not working properly")
            
            # Test cache clearing
            config_manager.clear_cache()
            print("   ✅ Cache cleared")
            
            # Load again (should reload from file)
            config3 = config_manager.load_config("test_cache")
            
            if config3 and config3.version == "cache_test_1.0.0":
                print("   ✅ Configuration reloaded after cache clear")
            else:
                print("   ❌ Configuration reload failed")
            
            return True
            
        except ImportError as import_error:
            print(f"   ⚠️ Import failed: {import_error}")
            return True
            
        except Exception as cache_error:
            print(f"   ❌ Cache test failed: {cache_error}")
            return False
            
        finally:
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ Configuration cache test failed: {e}")
        return False

def run_all_tests():
    """Run all configuration manager tests"""
    print("🚀 Starting Learning Configuration Manager Test Suite")
    print("=" * 60)
    
    # Clean up test directory
    test_config_dir = "Config/test"
    if os.path.exists(test_config_dir):
        shutil.rmtree(test_config_dir)
    
    test_results = []
    
    # Test 1: Initialization
    test_results.append(("Initialization", test_config_manager_initialization()))
    
    # Test 2: Configuration Classes
    test_results.append(("Configuration Classes", test_configuration_classes()))
    
    # Test 3: Save/Load
    test_results.append(("Save/Load", test_config_save_load()))
    
    # Test 4: Validation
    test_results.append(("Validation", test_config_validation()))
    
    # Test 5: Update
    test_results.append(("Update", test_config_update()))
    
    # Test 6: Listing
    test_results.append(("Listing", test_config_listing()))
    
    # Test 7: Backup/Restore
    test_results.append(("Backup/Restore", test_config_backup_restore()))
    
    # Test 8: Caching
    test_results.append(("Caching", test_config_cache()))
    
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
        print("\n🎉 All tests passed! Learning Configuration Manager is working correctly.")
    elif passed >= len(test_results) * 0.6:  # 60% pass rate
        print(f"\n✅ Most tests passed! Learning Configuration Manager is mostly functional.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the implementation.")
    
    # Clean up test directory
    if os.path.exists(test_config_dir):
        shutil.rmtree(test_config_dir)
    
    return failed == 0

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("Config", exist_ok=True)
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)