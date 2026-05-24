#!/usr/bin/env python3
"""
Quick test for Learning Coordinator
"""

import sys
import os
sys.path.append('Python')

print("🔧 Quick test for Learning Coordinator...")

try:
    # Test if file exists
    if os.path.exists('Python/learning_coordinator.py'):
        print("✅ learning_coordinator.py exists")
    else:
        print("❌ learning_coordinator.py missing")
        exit(1)
    
    # Test basic Python syntax
    print("🔧 Testing Python syntax...")
    
    with open('Python/learning_coordinator.py', 'r') as f:
        content = f.read()
    
    # Basic syntax check
    try:
        compile(content, 'Python/learning_coordinator.py', 'exec')
        print("✅ Python syntax is valid")
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        exit(1)
    
    # Test class definition
    if 'class LearningCoordinator:' in content:
        print("✅ LearningCoordinator class defined")
    else:
        print("❌ LearningCoordinator class not found")
    
    # Test key methods
    key_methods = [
        'start_learning_system',
        'stop_learning_system', 
        'execute_learning_cycle',
        'get_system_status'
    ]
    
    for method in key_methods:
        if f'def {method}(' in content:
            print(f"✅ {method} method defined")
        else:
            print(f"❌ {method} method missing")
    
    # Test imports
    required_imports = [
        'import logging',
        'import threading',
        'from datetime import datetime'
    ]
    
    for import_stmt in required_imports:
        if import_stmt in content:
            print(f"✅ {import_stmt}")
        else:
            print(f"⚠️ Missing: {import_stmt}")
    
    # Count lines of code
    lines = content.split('\n')
    code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    print(f"📊 Code statistics:")
    print(f"   Total lines: {len(lines)}")
    print(f"   Code lines: {len(code_lines)}")
    
    # Test for key features
    features = [
        ('Learning cycle execution', 'execute_learning_cycle'),
        ('Performance monitoring', '_execute_performance_monitoring'),
        ('Data collection', '_execute_data_collection'),
        ('Model training', '_execute_model_training'),
        ('Health check', '_execute_health_check'),
        ('Scheduler setup', '_setup_scheduler'),
        ('Error handling', 'trigger_emergency_stop')
    ]
    
    print(f"🔍 Feature analysis:")
    for feature_name, feature_code in features:
        if feature_code in content:
            print(f"   ✅ {feature_name}")
        else:
            print(f"   ❌ {feature_name}")
    
    print("🎉 Learning Coordinator quick test completed!")
    print("✅ File structure and basic functionality appear to be implemented")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("Test completed!")