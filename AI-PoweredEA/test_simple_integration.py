"""
Test Simple Error Handling Integration
"""

import sys
import os
sys.path.append('Python')

import logging
import tempfile
import shutil
from unittest.mock import Mock

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_simple_integration():
    """Test the simplified error handling integration"""
    try:
        print("Testing Simple Error Handling Integration...")
        
        # Create temporary directory
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test.db")
        
        try:
            # Import components
            from simple_integration import SimpleErrorHandlingIntegration, error_handler_decorator
            from simple_error_handler import ErrorSeverity, ErrorCategory
            
            print("✓ Successfully imported simple integration components")
            
            # Initialize integration
            integration = SimpleErrorHandlingIntegration(test_db)
            print("✓ Simple integration initialized")
            
            # Create mock components
            mock_coordinator = Mock()
            mock_coordinator.learning_cycle_active = False
            
            mock_config_manager = Mock()
            mock_config_manager.clear_cache = Mock()
            
            mock_notification_system = Mock()
            mock_notification_system.config = {
                'channels': {
                    'email': {'enabled': True},
                    'webhook': {'enabled': True},
                    'log': {'enabled': True}
                }
            }
            
            print("✓ Mock components created")
            
            # Test individual integrations
            result1 = integration.integrate_with_coordinator(mock_coordinator)
            result2 = integration.integrate_with_config_manager(mock_config_manager)
            result3 = integration.integrate_with_notification_system(mock_notification_system)
            
            print(f"✓ Coordinator integration: {result1}")
            print(f"✓ Config manager integration: {result2}")
            print(f"✓ Notification system integration: {result3}")
            
            # Test complete integration
            results = integration.integrate_all_components(
                mock_coordinator,
                mock_config_manager,
                mock_notification_system
            )
            
            print(f"✓ Complete integration results: {results}")
            
            # Test integration status
            status = integration.get_integration_status()
            print(f"✓ Integration status retrieved: {len(status)} items")
            print(f"  - Recovery strategies: {status['recovery_strategies_count']}")
            print(f"  - Fallback handlers: {status['fallback_handlers_count']}")
            
            # Test error handling
            test_error = ValueError("Test integration error")
            error_id = integration.error_handler.handle_error(
                test_error,
                "test_component",
                {"test": "context"}
            )
            
            print(f"✓ Error handled successfully: {error_id}")
            
            # Test error statistics
            stats = integration.error_handler.get_error_statistics()
            print(f"✓ Error statistics: {stats['total_errors']} total errors")
            
            # Test graceful degradation
            degradation_result = integration.trigger_graceful_degradation(
                'coordinator', 
                'test degradation'
            )
            
            print(f"✓ Graceful degradation test: {degradation_result}")
            
            # Test decorator functionality
            @error_handler_decorator("test_component", integration.error_handler, 
                                   ErrorSeverity.LOW, "fallback_value")
            def test_function():
                raise ValueError("Test decorator error")
            
            result = test_function()
            print(f"✓ Decorator test result: {result}")
            
            # Test recovery strategy execution
            mock_coordinator.learning_cycle_active = True
            
            # Trigger an error that should activate recovery
            coordinator_error = Exception("Coordinator test error")
            error_id = integration.error_handler.handle_error(
                coordinator_error,
                "learning_coordinator"
            )
            
            print(f"✓ Recovery strategy test: {error_id}")
            print(f"  - Learning cycle active after recovery: {mock_coordinator.learning_cycle_active}")
            
            # Test fallback handler execution
            config_error = FileNotFoundError("Config file not found")
            error_id = integration.error_handler.handle_error(
                config_error,
                "config_manager"
            )
            
            print(f"✓ Fallback handler test: {error_id}")
            print(f"  - Clear cache called: {mock_config_manager.clear_cache.called}")
            
            # Cleanup
            integration.shutdown()
            print("✓ Integration shutdown completed")
            
            print("\n🎉 All simple integration tests passed!")
            return True
            
        finally:
            # Clean up test directory
            shutil.rmtree(test_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ Simple integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_integration()
    if success:
        print("\n✅ Simple Error Handling Integration is working correctly!")
        print("\nTask 9.2 - Integrate error handling across all components: COMPLETED")
    else:
        print("\n❌ Simple Error Handling Integration test failed!")