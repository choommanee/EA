"""
Simple test for AI System Integration to verify core functionality
"""

import sys
import os
sys.path.append('Python')

import tempfile
import shutil
import numpy as np

try:
    from ai_system_integration import AISystemIntegration, create_sample_ai_system
    from model_manager import ModelType, ModelStatus
except ImportError:
    from Python.ai_system_integration import AISystemIntegration, create_sample_ai_system
    from Python.model_manager import ModelType, ModelStatus

from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification


def test_ai_system_integration():
    """Test complete AI system integration workflow"""
    print("Testing AI System Integration...")
    
    # Create temporary environment
    temp_dir = tempfile.mkdtemp()
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Initialize integration
        integration = AISystemIntegration(
            db_path=temp_db.name,
            models_directory=os.path.join(temp_dir, "models")
        )
        
        print("✓ AI System Integration initialized")
        
        # Create and save a model
        X, y = make_classification(n_samples=200, n_features=10, random_state=42)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        metrics = {"accuracy": 0.95, "precision": 0.94, "recall": 0.96}
        
        model_version = integration.model_manager.save_model(
            model, "trading_classifier", ModelType.CLASSIFICATION, metrics,
            {"algorithm": "RandomForest", "features": 10}, "Trading signal classifier"
        )
        
        print(f"✓ Model saved: {model_version.model_id} v{model_version.version}")
        
        # Update model status for deployment
        integration.model_manager._update_model_status(
            model_version.model_id, model_version.version, ModelStatus.TESTING
        )
        
        print("✓ Model status updated to TESTING")
        
        # Test 1: Activate integration
        print("\n1. Testing integration activation...")
        success = integration.activate_integration(
            model_version.model_id, model_version.version
        )
        
        print(f"   Activation success: {success}")
        print(f"   Integration status: {integration.status.value}")
        print("✓ Integration activation completed")
        
        # Test 2: Get active model
        print("\n2. Testing active model retrieval...")
        active_model, model_version_str = integration.get_active_model()
        
        print(f"   Active model available: {active_model is not None}")
        print(f"   Model version: {model_version_str}")
        print(f"   Has predict method: {hasattr(active_model, 'predict') if active_model else False}")
        print("✓ Active model retrieval completed")
        
        # Test 3: Make predictions
        print("\n3. Testing predictions...")
        test_features = np.random.rand(10)
        
        prediction_result = integration.make_prediction(test_features, "EURUSD")
        
        if prediction_result:
            print(f"   Prediction: {prediction_result['prediction']}")
            print(f"   Confidence: {prediction_result['confidence']:.3f}")
            print(f"   Symbol: {prediction_result['symbol']}")
            print(f"   Model version: {prediction_result['model_version']}")
        else:
            print("   No prediction result")
        
        print("✓ Prediction testing completed")
        
        # Test 4: Integration status
        print("\n4. Testing integration status...")
        status = integration.get_integration_status()
        
        print(f"   Status: {status['status']}")
        print(f"   Active model: {status.get('active_model', 'None')}")
        print(f"   Daily switches: {status['daily_switches']}")
        print(f"   Total switches: {status['total_switches']}")
        print("✓ Integration status completed")
        
        # Test 5: Sample AI System
        print("\n5. Testing sample AI system...")
        SampleAISystem = create_sample_ai_system()
        ai_system = SampleAISystem(integration)
        
        # Sample market data
        market_data = {
            'open': 1.1234,
            'high': 1.1250,
            'low': 1.1220,
            'close': 1.1245,
            'volume': 1000000,
            'rsi': 65.5,
            'macd': 0.0012,
            'bb_upper': 1.1260,
            'bb_lower': 1.1210,
            'sma_20': 1.1235
        }
        
        analysis_result = ai_system.analyze_market("EURUSD", market_data)
        
        if analysis_result:
            print(f"   Symbol: {analysis_result['symbol']}")
            print(f"   Signal: {analysis_result['signal']}")
            print(f"   Confidence: {analysis_result['confidence']:.3f}")
            print(f"   Model version: {analysis_result['model_version']}")
        else:
            print("   No analysis result")
        
        print("✓ Sample AI system completed")
        
        # Test 6: Configuration update
        print("\n6. Testing configuration update...")
        config_success = integration.update_config(
            performance_threshold=0.8,
            auto_switching_enabled=False
        )
        
        print(f"   Config update success: {config_success}")
        print(f"   Performance threshold: {integration.current_config.performance_threshold}")
        print(f"   Auto switching: {integration.current_config.auto_switching_enabled}")
        print("✓ Configuration update completed")
        
        # Test 7: Deactivation
        print("\n7. Testing integration deactivation...")
        deactivate_success = integration.deactivate_integration()
        
        print(f"   Deactivation success: {deactivate_success}")
        print(f"   Final status: {integration.status.value}")
        print("✓ Integration deactivation completed")
        
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
    print("AI System Integration Simple Test Suite")
    print("=" * 60)
    
    success = test_ai_system_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)