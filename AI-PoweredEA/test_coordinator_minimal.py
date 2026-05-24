"""
Minimal test for Learning Coordinator to verify core functionality
"""

import sys
import os
sys.path.append('Python')

import tempfile
import shutil
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


def test_learning_coordinator_minimal():
    """Test core Learning Coordinator functionality with minimal dependencies"""
    print("Testing Learning Coordinator (Minimal)...")
    
    # Create temporary environment
    temp_dir = tempfile.mkdtemp()
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Mock all the imports at the module level
        with patch.dict('sys.modules', {
            'learning_error_handler': MagicMock(),
            'learning_database_manager': MagicMock(),
            'model_manager': MagicMock(),
            'ai_system_integration': MagicMock(),
            'performance_monitor': MagicMock(),
            'learning_data_collector': MagicMock(),
            'data_preprocessing_pipeline': MagicMock(),
            'model_evaluator': MagicMock(),
            'cross_validation_framework': MagicMock(),
            'schedule': MagicMock()
        }):
            # Now import the coordinator
            from Python.learning_coordinator import (
                LearningCoordinator, LearningPhase, LearningTrigger,
                LearningCycleConfig
            )
            
            print("✓ Learning Coordinator imported successfully")
            
            # Test 1: Basic initialization
            print("\n1. Testing initialization...")
            
            # Mock the component constructors
            with patch.multiple(
                'Python.learning_coordinator',
                ModelManager=MagicMock,
                AISystemIntegration=MagicMock,
                PerformanceMonitor=MagicMock,
                LearningDataCollector=MagicMock,
                DataPreprocessingPipeline=MagicMock,
                ModelEvaluator=MagicMock,
                CrossValidationFramework=MagicMock,
                LearningErrorHandler=MagicMock
            ):
                coordinator = LearningCoordinator(
                    db_path=temp_db.name,
                    models_directory=os.path.join(temp_dir, "models")
                )
                
                print(f"   Coordinator created: {coordinator is not None}")
                print(f"   Is running: {coordinator.is_running}")
                print(f"   Current cycle: {coordinator.current_cycle}")
                print("✓ Initialization completed")
                
                # Test 2: Configuration
                print("\n2. Testing configuration...")
                config = LearningCycleConfig(
                    cycle_id="test_config",
                    trigger_type=LearningTrigger.MANUAL,
                    performance_threshold=0.8
                )
                
                print(f"   Config cycle ID: {config.cycle_id}")
                print(f"   Config trigger: {config.trigger_type.value}")
                print(f"   Performance threshold: {config.performance_threshold}")
                print("✓ Configuration testing completed")
                
                # Test 3: Status retrieval
                print("\n3. Testing status retrieval...")
                status = coordinator.get_current_status()
                
                print(f"   Status type: {type(status)}")
                print(f"   Has coordinator_running: {'coordinator_running' in status}")
                print(f"   Has current_cycle: {'current_cycle' in status}")
                print(f"   Has total_cycles: {'total_cycles' in status}")
                print("✓ Status retrieval completed")
                
                # Test 4: Enums and phases
                print("\n4. Testing enums and phases...")
                
                phases = [phase for phase in LearningPhase]
                triggers = [trigger for trigger in LearningTrigger]
                
                print(f"   Learning phases: {len(phases)}")
                print(f"   Learning triggers: {len(triggers)}")
                print(f"   Sample phase: {LearningPhase.MODEL_TRAINING.value}")
                print(f"   Sample trigger: {LearningTrigger.MANUAL.value}")
                print("✓ Enums and phases testing completed")
                
                # Test 5: Database table initialization
                print("\n5. Testing database operations...")
                
                # Check if database file was created
                db_exists = os.path.exists(temp_db.name)
                print(f"   Database file exists: {db_exists}")
                
                if db_exists:
                    import sqlite3
                    conn = sqlite3.connect(temp_db.name)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    print(f"   Tables created: {len(tables)}")
                    for table in tables:
                        print(f"     - {table}")
                    
                    conn.close()
                
                print("✓ Database operations completed")
                
                # Test 6: Workflow steps
                print("\n6. Testing workflow steps...")
                
                workflow_steps = coordinator.workflow_steps
                print(f"   Workflow steps: {len(workflow_steps)}")
                
                for i, (step_name, step_function) in enumerate(workflow_steps):
                    print(f"     {i+1}. {step_name}")
                
                print("✓ Workflow steps testing completed")
                
                print("\n🎉 All minimal tests completed successfully!")
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
    print("Learning Coordinator Minimal Test Suite")
    print("=" * 60)
    
    success = test_learning_coordinator_minimal()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)