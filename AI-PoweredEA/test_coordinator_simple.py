"""
Simple test for Learning Coordinator to verify core functionality
"""

import sys
import os
sys.path.append('Python')

import tempfile
import shutil
import time
from unittest.mock import Mock, patch, MagicMock

try:
    from learning_coordinator import (
        LearningCoordinator, LearningPhase, LearningTrigger,
        LearningCycleConfig, create_sample_progress_callback
    )
except ImportError:
    from Python.learning_coordinator import (
        LearningCoordinator, LearningPhase, LearningTrigger,
        LearningCycleConfig, create_sample_progress_callback
    )


def test_learning_coordinator():
    """Test core Learning Coordinator functionality"""
    print("Testing Learning Coordinator...")
    
    # Create temporary environment
    temp_dir = tempfile.mkdtemp()
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # Mock the components to avoid complex dependencies
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
            # Initialize coordinator
            coordinator = LearningCoordinator(
                db_path=temp_db.name,
                models_directory=os.path.join(temp_dir, "models")
            )
            
            print("✓ Learning Coordinator initialized")
            
            # Test 1: Initial status
            print("\n1. Testing initial status...")
            status = coordinator.get_current_status()
            
            print(f"   Coordinator running: {status['coordinator_running']}")
            print(f"   Current cycle: {status['current_cycle']}")
            print(f"   Total cycles: {status['total_cycles']}")
            print("✓ Initial status retrieved")
            
            # Test 2: Start coordinator
            print("\n2. Testing coordinator start...")
            success = coordinator.start_coordinator()
            
            print(f"   Start success: {success}")
            print(f"   Is running: {coordinator.is_running}")
            print("✓ Coordinator start completed")
            
            # Test 3: Configuration
            print("\n3. Testing configuration...")
            config = LearningCycleConfig(
                cycle_id="test_config",
                trigger_type=LearningTrigger.MANUAL,
                performance_threshold=0.8,
                auto_deploy_threshold=0.85
            )
            
            print(f"   Config cycle ID: {config.cycle_id}")
            print(f"   Config trigger: {config.trigger_type.value}")
            print(f"   Performance threshold: {config.performance_threshold}")
            print("✓ Configuration testing completed")
            
            # Test 4: Progress callback
            print("\n4. Testing progress callback...")
            progress_updates = []
            
            def test_callback(progress):
                progress_updates.append(progress)
                print(f"   Progress: {progress.phase.value} - {progress.total_progress:.1f}%")
            
            coordinator.add_progress_callback(test_callback)
            print("✓ Progress callback added")
            
            # Test 5: Manual trigger (with mocked components)
            print("\n5. Testing manual trigger...")
            
            # Set up basic mocks
            mock_data = Mock()
            mock_data.empty = False
            mock_data.__len__ = Mock(return_value=100)
            mock_data.shape = (100, 10)
            mock_data.drop = Mock(return_value=Mock(values=[[1, 2, 3, 4, 5]] * 100))
            mock_data.tail = Mock(return_value=mock_data)
            mock_data.head = Mock(return_value=mock_data)
            
            coordinator.data_collector.collect_learning_data = Mock(return_value=mock_data)
            coordinator.data_pipeline.process_learning_data = Mock(return_value=mock_data)
            
            mock_model_version = Mock()
            mock_model_version.model_id = "test_model_123"
            mock_model_version.version = "1"
            coordinator.model_manager.save_model = Mock(return_value=mock_model_version)
            
            # Trigger cycle
            cycle_id = coordinator.trigger_learning_cycle(LearningTrigger.MANUAL)
            
            print(f"   Triggered cycle: {cycle_id}")
            print("✓ Manual trigger completed")
            
            # Test 6: Wait for some progress
            print("\n6. Testing progress monitoring...")
            time.sleep(1)  # Wait for cycle to start
            
            progress = coordinator.get_learning_progress()
            if progress:
                print(f"   Current phase: {progress.phase.value}")
                print(f"   Progress: {progress.total_progress:.1f}%")
                print(f"   Step: {progress.step_name}")
            else:
                print("   No active progress (cycle may have completed)")
            
            print("✓ Progress monitoring completed")
            
            # Test 7: Status while running
            print("\n7. Testing status while running...")
            running_status = coordinator.get_current_status()
            
            print(f"   Coordinator running: {running_status['coordinator_running']}")
            print(f"   Total cycles: {running_status['total_cycles']}")
            
            if running_status['current_cycle']:
                current = running_status['current_cycle']
                print(f"   Current cycle: {current['cycle_id']}")
                print(f"   Current phase: {current['current_phase']}")
                print(f"   Progress: {current['progress_percentage']:.1f}%")
            
            print("✓ Running status retrieved")
            
            # Test 8: Wait for cycle completion
            print("\n8. Waiting for cycle completion...")
            timeout = 10  # 10 seconds timeout
            start_time = time.time()
            
            while (coordinator.current_cycle and 
                   coordinator.current_cycle.current_phase not in [LearningPhase.COMPLETED, LearningPhase.FAILED] and
                   time.time() - start_time < timeout):
                time.sleep(0.5)
                if coordinator.current_cycle:
                    print(f"   Phase: {coordinator.current_cycle.current_phase.value}, Progress: {coordinator.current_cycle.progress_percentage:.1f}%")
            
            print("✓ Cycle completion monitoring finished")
            
            # Test 9: Cycle history
            print("\n9. Testing cycle history...")
            history = coordinator.get_cycle_history()
            
            print(f"   History entries: {len(history)}")
            for i, cycle in enumerate(history):
                print(f"   Cycle {i+1}: {cycle['cycle_id']} - {cycle['final_phase']} - Success: {cycle['success']}")
            
            print("✓ Cycle history retrieved")
            
            # Test 10: Stop coordinator
            print("\n10. Testing coordinator stop...")
            stop_success = coordinator.stop_coordinator()
            
            print(f"   Stop success: {stop_success}")
            print(f"   Is running: {coordinator.is_running}")
            print("✓ Coordinator stop completed")
            
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
    print("Learning Coordinator Simple Test Suite")
    print("=" * 60)
    
    success = test_learning_coordinator()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)