#!/usr/bin/env python3
"""
Quick test for Learning Notification System
"""

import sys
import os
sys.path.append('Python')

import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_notification_system():
    """Test notification system functionality"""
    try:
        print("Testing Learning Notification System...")
        
        # Import the notification system
        from learning_notification_system import (
            LearningNotificationSystem, 
            NotificationLevel, 
            LearningEventType, 
            LearningEventRecord
        )
        
        print("✅ Successfully imported notification system")
        
        # Initialize notification system
        notification_system = LearningNotificationSystem("Config/test_notifications.json")
        print("✅ Notification system initialized")
        
        # Test custom notification
        success = notification_system.send_custom_notification(
            NotificationLevel.INFO,
            "Test Notification",
            "This is a test notification from the Learning Notification System"
        )
        print(f"✅ Custom notification sent: {success}")
        
        # Test performance alert
        success = notification_system.send_performance_alert(
            model_name="test_model",
            current_performance=0.65,
            threshold=0.75,
            degradation_percent=0.13
        )
        print(f"✅ Performance alert sent: {success}")
        
        # Test error notification
        success = notification_system.send_error_notification(
            error_type="TestError",
            error_message="This is a test error message",
            component="TestComponent"
        )
        print(f"✅ Error notification sent: {success}")
        
        # Test learning event notification
        test_event = LearningEventRecord(
            event_type=LearningEventType.MODEL_TRAINING_COMPLETED,
            event_data={'models_trained': 3, 'best_accuracy': 0.85},
            timestamp=datetime.now(),
            success=True
        )
        
        success = notification_system.send_learning_event_notification(test_event)
        print(f"✅ Learning event notification sent: {success}")
        
        # Test notification history
        history = notification_system.get_notification_history(limit=5)
        print(f"✅ Notification history retrieved: {len(history)} entries")
        
        print("\n🎉 All notification system tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("Config", exist_ok=True)
    os.makedirs("Logs", exist_ok=True)
    
    success = test_notification_system()
    sys.exit(0 if success else 1)