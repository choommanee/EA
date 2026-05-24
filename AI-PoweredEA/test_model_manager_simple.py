"""
Simple test for Model Manager to verify core functionality
"""

import sys
import os
sys.path.append('Python')

import tempfile
import shutil
from pathlib import Path

try:
    from model_manager import ModelManager, ModelType, ModelStatus
except ImportError:
    from Python.model_manager import ModelManager, ModelType, ModelStatus

from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification


def test_model_manager():
    """Test core Model Manager functionality"""
    print("Testing Model Manager...")
    
    # Create temporary environment
    temp_dir = tempfile.mkdtemp()
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Initialize model manager
        model_manager = ModelManager(
            db_path=temp_db.name,
            models_directory=os.path.join(temp_dir, "models")
        )
        
        # Create sample model
        X, y = make_classification(n_samples=100, n_features=10, random_state=42)
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        metrics = {"accuracy": 0.95, "precision": 0.94}
        
        print("✓ Model Manager initialized")
        
        # Test 1: Save model
        print("\n1. Testing model saving...")
        model_version = model_manager.save_model(
            model, "test_model", ModelType.CLASSIFICATION, metrics,
            {"algorithm": "RandomForest"}, "Test model"
        )
        
        print(f"   Model saved: {model_version.model_id} v{model_version.version}")
        print(f"   Status: {model_version.status.value}")
        print(f"   File size: {model_version.file_size} bytes")
        print("✓ Model saving completed")
        
        # Test 2: Load model
        print("\n2. Testing model loading...")
        loaded_model, loaded_version = model_manager.load_model(
            model_version.model_id, model_version.version
        )
        
        print(f"   Loaded model: {loaded_version.model_name}")
        print(f"   Has predict method: {hasattr(loaded_model, 'predict')}")
        print("✓ Model loading completed")
        
        # Test 3: Model versioning
        print("\n3. Testing model versioning...")
        version2 = model_manager.save_model(
            model, "test_model", ModelType.CLASSIFICATION, 
            {**metrics, "version": 2}, {"algorithm": "RandomForest", "improved": True}
        )
        
        version3 = model_manager.save_model(
            model, "test_model", ModelType.CLASSIFICATION,
            {**metrics, "version": 3}, {"algorithm": "RandomForest", "final": True}
        )
        
        print(f"   Version 1: {model_version.version}")
        print(f"   Version 2: {version2.version}")
        print(f"   Version 3: {version3.version}")
        print("✓ Model versioning completed")
        
        # Test 4: Model deployment
        print("\n4. Testing model deployment...")
        
        # Update status to allow deployment
        model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        deployment = model_manager.deploy_model(
            model_version.model_id, model_version.version, "staging"
        )
        
        print(f"   Deployment ID: {deployment.deployment_id}")
        print(f"   Environment: {deployment.environment}")
        print(f"   Status: {deployment.status.value}")
        print(f"   Health check: {deployment.health_check_results.get('healthy', 'N/A')}")
        print("✓ Model deployment completed")
        
        # Test 5: List models
        print("\n5. Testing model listing...")
        all_models = model_manager.list_models()
        
        print(f"   Total models: {len(all_models)}")
        for model in all_models:
            print(f"   - {model.model_name} v{model.version} ({model.status.value})")
        print("✓ Model listing completed")
        
        # Test 6: Model metrics
        print("\n6. Testing model metrics...")
        metrics_result = model_manager.get_model_metrics(model_version.model_id)
        
        print(f"   Model info available: {'model_info' in metrics_result}")
        print(f"   Performance metrics: {len(metrics_result.get('performance_metrics', {}))}")
        print(f"   Deployment info: {'deployment_info' in metrics_result}")
        print("✓ Model metrics completed")
        
        # Test 7: Model history
        print("\n7. Testing model history...")
        history = model_manager.get_model_history(model_version.model_id)
        
        print(f"   History entries: {len(history)}")
        for entry in history[:3]:  # Show first 3 entries
            print(f"   - {entry.action} at {entry.timestamp.strftime('%H:%M:%S')}")
        print("✓ Model history completed")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir)
            os.unlink(temp_db.name)
        except:
            pass


if __name__ == "__main__":
    print("=" * 60)
    print("Model Manager Simple Test Suite")
    print("=" * 60)
    
    success = test_model_manager()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)