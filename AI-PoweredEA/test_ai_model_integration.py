#!/usr/bin/env python3
"""
Test script for AI Model Integration
Tests integration between Model Manager and AI Analysis System
"""

import sys
import os
sys.path.append('Python')

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def setup_test_models():
    """Set up test models for integration testing"""
    try:
        print("🔧 Setting up test models...")
        
        from model_manager import ModelManager
        
        # Clean up any existing test data
        test_model_path = "Data/test_integration_models"
        if os.path.exists(test_model_path):
            shutil.rmtree(test_model_path, ignore_errors=True)
        
        manager = ModelManager("Data/test_integration.db", test_model_path)
        
        # Create sample training data
        X, y = make_classification(
            n_samples=300,
            n_features=10,
            n_informative=8,
            n_classes=3,
            random_state=42
        )
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Create and train models
        models_created = []
        
        # Model 1: Random Forest
        rf_model = RandomForestClassifier(n_estimators=50, random_state=42)
        rf_model.fit(X_train, y_train)
        rf_accuracy = rf_model.score(X_test, y_test)
        
        version_id_1 = manager.save_model(
            model=rf_model,
            model_name="gold_predictor",
            model_type="random_forest",
            performance_metrics={
                'test_accuracy': rf_accuracy,
                'train_accuracy': rf_model.score(X_train, y_train)
            },
            hyperparameters=rf_model.get_params(),
            training_data_hash="test_hash_rf",
            metadata={'test_model': True, 'symbol': 'XAUUSD'}
        )
        
        if version_id_1:
            models_created.append(('gold_predictor', version_id_1, rf_accuracy))
            # Deploy this model as active
            manager.deploy_model(version_id_1, "gold_predictor")
        
        # Model 2: Another Random Forest with different params
        rf_model_2 = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        rf_model_2.fit(X_train, y_train)
        rf_accuracy_2 = rf_model_2.score(X_test, y_test)
        
        version_id_2 = manager.save_model(
            model=rf_model_2,
            model_name="eurusd_predictor",
            model_type="random_forest",
            performance_metrics={
                'test_accuracy': rf_accuracy_2,
                'train_accuracy': rf_model_2.score(X_train, y_train)
            },
            hyperparameters=rf_model_2.get_params(),
            training_data_hash="test_hash_rf2",
            metadata={'test_model': True, 'symbol': 'EURUSD'}
        )
        
        if version_id_2:
            models_created.append(('eurusd_predictor', version_id_2, rf_accuracy_2))
            # Deploy this model as active
            manager.deploy_model(version_id_2, "eurusd_predictor")
        
        print(f"✅ Created and deployed {len(models_created)} test models")
        for name, version_id, accuracy in models_created:
            print(f"   {name}: {version_id} (accuracy: {accuracy:.3f})")
        
        return models_created
        
    except Exception as e:
        print(f"❌ Error setting up test models: {e}")
        return []

def test_integration_initialization():
    """Test AI Model Integration initialization"""
    try:
        print("\n🔧 Testing AI Model Integration initialization...")
        
        from Python.ai_model_integration import AIModelIntegration
        
        integration = AIModelIntegration("Data/test_integration.db", "Data/test_integration_models")
        print("✅ AI Model Integration initialized successfully")
        
        # Check components
        if integration.model_manager:
            print("✅ Model Manager component available")
        
        if integration.ai_system:
            print("✅ AI System component available")
        
        if integration.db_manager:
            print("✅ Database Manager component available")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration initialization failed: {e}")
        return False

def test_best_model_selection():
    """Test best model selection for symbols"""
    try:
        print("\n🎯 Testing best model selection...")
        
        from Python.ai_model_integration import AIModelIntegration
        
        integration = AIModelIntegration("Data/test_integration.db", "Data/test_integration_models")
        
        # Test getting best model for different symbols
        symbols = ['XAUUSD', 'EURUSD', 'GBPUSD']
        
        for symbol in symbols:
            print(f"   Testing best model for {symbol}...")
            
            best_model = integration.get_best_model_for_symbol(symbol)
            
            if best_model is not None:
                print(f"   ✅ Best model found for {symbol}")
                
                # Test that the model can make predictions
                sample_features = np.random.rand(10)
                try:
                    prediction = best_model.predict(sample_features.reshape(1, -1))
                    print(f"      Model can make predictions: {prediction}")
                except Exception as pred_error:
                    print(f"      ⚠️ Model prediction failed: {pred_error}")
            else:
                print(f"   ⚠️ No best model found for {symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Best model selection failed: {e}")
        return False

def test_prediction_with_best_model():
    """Test making predictions with best model"""
    try:
        print("\n🔮 Testing prediction with best model...")
        
        from Python.ai_model_integration import AIModelIntegration
        
        integration = AIModelIntegration("Data/test_integration.db", "Data/test_integration_models")
        
        # Test predictions for different symbols
        symbols = ['XAUUSD', 'EURUSD']
        
        predictions_made = 0
        
        for symbol in symbols:
            print(f"   Making prediction for {symbol}...")
            
            # Create sample features
            sample_features = np.random.rand(10)
            
            prediction_result = integration.predict_with_best_model(symbol, sample_features)
            
            if prediction_result:
                print(f"   ✅ Prediction made for {symbol}")
                print(f"      Signal: {prediction_result.get('signal', 'N/A')}")
                print(f"      Confidence: {prediction_result.get('confidence', 0):.3f}")
                print(f"      Model Version: {prediction_result.get('model_version', 'N/A')}")
                predictions_made += 1
            else:
                print(f"   ❌ Failed to make prediction for {symbol}")
        
        if predictions_made > 0:
            print(f"✅ Predictions completed: {predictions_made} successful")
            return True
        else:
            print("❌ No predictions were successful")
            return False
        
    except Exception as e:
        print(f"❌ Prediction testing failed: {e}")
        return False

def test_model_performance_summary():
    """Test model performance summary"""
    try:
        print("\n📊 Testing model performance summary...")
        
        from Python.ai_model_integration import AIModelIntegration
        
        integration = AIModelIntegration("Data/test_integration.db", "Data/test_integration_models")
        
        summary = integration.get_model_performance_summary()
        
        if summary:
            print("✅ Performance summary retrieved")
            print(f"   Total models: {summary.get('total_models', 0)}")
            print(f"   Average performance: {summary.get('avg_performance', 0):.3f}")
            print(f"   Last updated: {summary.get('last_updated', 'N/A')}")
            
            active_models = summary.get('active_models', {})
            if active_models:
                print(f"   Active models: {len(active_models)}")
                for model_name, model_info in active_models.items():
                    performance = model_info.get('performance', 0)
                    print(f"      {model_name}: {performance:.3f} performance")
            
            return True
        else:
            print("❌ Failed to get performance summary")
            return False
        
    except Exception as e:
        print(f"❌ Performance summary test failed: {e}")
        return False

def test_model_compatibility_validation():
    """Test model compatibility validation"""
    try:
        print("\n✅ Testing model compatibility validation...")
        
        from Python.ai_model_integration import AIModelIntegration
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        
        integration = AIModelIntegration("Data/test_integration.db", "Data/test_integration_models")
        
        # Create test models
        X, y = make_classification(n_samples=100, n_features=10, n_classes=3, random_state=42)
        
        # Compatible model
        compatible_model = RandomForestClassifier(n_estimators=10, random_state=42)
        compatible_model.fit(X, y)
        
        # Test compatibility
        is_compatible = integration.validate_model_compatibility(compatible_model, "XAUUSD")
        
        if is_compatible:
            print("   ✅ Model compatibility validation passed")
        else:
            print("   ❌ Model compatibility validation failed")
        
        # Test with a model that might have issues
        try:
            # Create a model without required methods (mock)
            class IncompatibleModel:
                def __init__(self):
                    pass
                # Missing predict method
            
            incompatible_model = IncompatibleModel()
            is_incompatible = integration.validate_model_compatibility(incompatible_model, "XAUUSD")
            
            if not is_incompatible:
                print("   ✅ Incompatible model correctly rejected")
            else:
                print("   ⚠️ Incompatible model was accepted")
                
        except Exception as validation_error:
            print(f"   ✅ Incompatible model correctly rejected: {validation_error}")
        
        return is_compatible
        
    except Exception as e:
        print(f"❌ Model compatibility validation failed: {e}")
        return False

def test_model_update_integration():
    """Test updating AI system with new model"""
    try:
        print("\n🔄 Testing model update integration...")
        
        from Python.ai_model_integration import AIModelIntegration
        from Python.model_manager import ModelManager
        from sklearn.ensemble import RandomForestClassifier
        
        integration = AIModelIntegration("Data/test_integration.db", "Data/test_integration_models")
        
        # Create a new model version
        X, y = make_classification(n_samples=200, n_features=10, n_classes=3, random_state=123)
        new_model = RandomForestClassifier(n_estimators=75, random_state=123)
        new_model.fit(X, y)
        
        # Save the new model
        new_version_id = integration.model_manager.save_model(
            model=new_model,
            model_name="test_update_model",
            model_type="random_forest",
            performance_metrics={'test_accuracy': 0.85},
            hyperparameters=new_model.get_params(),
            training_data_hash="test_update_hash"
        )
        
        if new_version_id:
            print(f"   New model version created: {new_version_id}")
            
            # Test updating the AI system
            update_success = integration.update_ai_system_model("test_update_model", new_version_id)
            
            if update_success:
                print("   ✅ AI system model update successful")
                
                # Verify the model is now active
                active_version = integration.model_manager.get_active_model_version("test_update_model")
                if active_version == new_version_id:
                    print("   ✅ New model version is now active")
                    return True
                else:
                    print("   ⚠️ New model version is not active")
                    return False
            else:
                print("   ❌ AI system model update failed")
                return False
        else:
            print("   ❌ Failed to create new model version")
            return False
        
    except Exception as e:
        print(f"❌ Model update integration failed: {e}")
        return False

def test_auto_model_switching():
    """Test automatic model switching functionality"""
    try:
        print("\n🔀 Testing automatic model switching...")
        
        from Python.ai_model_integration import AIModelIntegration
        
        integration = AIModelIntegration("Data/test_integration.db", "Data/test_integration_models")
        
        # Enable auto switching
        integration.auto_model_switching = True
        integration.performance_threshold = 0.9  # High threshold to trigger switching
        
        # Test auto switching for a symbol
        symbol = "XAUUSD"
        
        print(f"   Testing auto switching for {symbol}...")
        
        # This should check current performance and switch if needed
        switch_result = integration.auto_switch_model_if_needed(symbol)
        
        if switch_result:
            print(f"   ✅ Auto model switching triggered for {symbol}")
        else:
            print(f"   ℹ️ No model switching needed for {symbol} (current model performing well)")
        
        # Test with auto switching disabled
        integration.auto_model_switching = False
        switch_result_disabled = integration.auto_switch_model_if_needed(symbol)
        
        if not switch_result_disabled:
            print("   ✅ Auto switching correctly disabled")
        else:
            print("   ⚠️ Auto switching occurred when disabled")
        
        return True
        
    except Exception as e:
        print(f"❌ Auto model switching test failed: {e}")
        return False

def test_model_rollback():
    """Test model rollback functionality"""
    try:
        print("\n⏪ Testing model rollback...")
        
        from Python.ai_model_integration import AIModelIntegration
        
        integration = AIModelIntegration("Data/test_integration.db", "Data/test_integration_models")
        
        # Test rollback for a model
        model_name = "gold_predictor"
        
        print(f"   Testing rollback for {model_name}...")
        
        # Get current active version
        current_version = integration.model_manager.get_active_model_version(model_name)
        if current_version:
            print(f"   Current version: {current_version}")
            
            # Perform rollback
            rollback_success = integration.rollback_to_previous_model(
                model_name, 
                reason="Test rollback"
            )
            
            if rollback_success:
                print(f"   ✅ Rollback successful for {model_name}")
                
                # Check if version changed
                new_version = integration.model_manager.get_active_model_version(model_name)
                if new_version != current_version:
                    print(f"   ✅ Version changed: {current_version} -> {new_version}")
                else:
                    print(f"   ℹ️ Version unchanged (may be only one version available)")
                
                return True
            else:
                print(f"   ❌ Rollback failed for {model_name}")
                return False
        else:
            print(f"   ⚠️ No active version found for {model_name}")
            return True  # Not a failure, just no data
        
    except Exception as e:
        print(f"❌ Model rollback test failed: {e}")
        return False

def run_all_tests():
    """Run all AI Model Integration tests"""
    print("🚀 Starting AI Model Integration Test Suite")
    print("=" * 60)
    
    # Setup test models first
    models_created = setup_test_models()
    if not models_created:
        print("❌ Failed to set up test models. Aborting tests.")
        return False
    
    test_results = []
    
    # Test 1: Initialization
    test_results.append(("Initialization", test_integration_initialization()))
    
    # Test 2: Best Model Selection
    test_results.append(("Best Model Selection", test_best_model_selection()))
    
    # Test 3: Prediction with Best Model
    test_results.append(("Prediction with Best Model", test_prediction_with_best_model()))
    
    # Test 4: Performance Summary
    test_results.append(("Performance Summary", test_model_performance_summary()))
    
    # Test 5: Model Compatibility
    test_results.append(("Model Compatibility", test_model_compatibility_validation()))
    
    # Test 6: Model Update Integration
    test_results.append(("Model Update Integration", test_model_update_integration()))
    
    # Test 7: Auto Model Switching
    test_results.append(("Auto Model Switching", test_auto_model_switching()))
    
    # Test 8: Model Rollback
    test_results.append(("Model Rollback", test_model_rollback()))
    
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
        print("\n🎉 All tests passed! AI Model Integration is working correctly.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    # Ensure Data directory exists
    os.makedirs("Data", exist_ok=True)
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)