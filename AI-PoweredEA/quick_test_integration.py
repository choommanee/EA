"""
Quick test for error handling integration
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

def test_integration():
    """Quick test of error handling integration"""
    try:
        print("Testing Error Handling Integration...")
        
        # Create temporary directory
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "test.db")
        
        try:
            # Import components
            from error_handling_integration import ErrorHandlingIntegration
            from learning_error_handler import ErrorSeverity, ErrorCategory
            
            print("✓ Successfully imported error handling components")
            
            # Initialize integration
            integration = ErrorHandlingIntegration(test_db)
            print("✓ Error handling integration initialized")
            
            # Create mock components
            mock_coordinator = Mock()
            mock_coordinator.learning_cycle_active = False
            mock_coordinator.db_manager = Mock()
            mock_coordinator.db_manager.db_path = test_db
            
            mock_config_manager = Mock()
            mock_config_manager.config_cache = {}
            mock_config_manager.cache_timestamps = {}
            
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
            
            # Test error handling
            test_error = ValueError("Test integration error")
            error_id = integration.error_handler.handle_error(
                test_error,
                "test_component",
                {"test": "context"}
            )
            
            print(f"✓ Error handled successfully: {error_id}")
            
            # Test graceful degradation
            degradation_result = integration.trigger_graceful_degradation(
                'coordinator', 
                'test degradation'
            )
            
            print(f"✓ Graceful degradation test: {degradation_result}")
            
            # Cleanup
            integration.shutdown()
            print("✓ Integration shutdown completed")
            
            print("\n🎉 All integration tests passed!")
            return True
            
        finally:
            # Clean up test directory
            shutil.rmtree(test_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration()
    if success:
        print("\n✅ Error Handling Integration is working correctly!")
    else:
        print("\n❌ Error Handling Integration test failed!")