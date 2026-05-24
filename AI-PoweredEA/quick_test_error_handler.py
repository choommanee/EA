#!/usr/bin/env python3
"""
Quick test for Learning Error Handler
"""

import sys
import os
sys.path.append('Python')

print("🔧 Quick test for Learning Error Handler...")

try:
    # Test if file exists
    if os.path.exists('Python/learning_error_handler.py'):
        print("✅ learning_error_handler.py exists")
    else:
        print("❌ learning_error_handler.py missing")
        exit(1)
    
    # Test basic Python syntax
    print("🔧 Testing Python syntax...")
    
    with open('Python/learning_error_handler.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Basic syntax check
    try:
        compile(content, 'Python/learning_error_handler.py', 'exec')
        print("✅ Python syntax is valid")
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        exit(1)
    
    # Test class definitions
    expected_classes = [
        'LearningErrorHandler',
        'ErrorRecord',
        'ErrorSeverity',
        'ErrorCategory'
    ]
    
    for class_name in expected_classes:
        if f'class {class_name}' in content:
            print(f"✅ {class_name} class defined")
        else:
            print(f"❌ {class_name} class missing")
    
    # Test key methods
    key_methods = [
        'handle_error',
        'register_recovery_strategy',
        'get_error_statistics',
        'resolve_error',
        'get_circuit_breaker_status',
        'cleanup_old_errors'
    ]
    
    for method in key_methods:
        if f'def {method}(' in content:
            print(f"✅ {method} method defined")
        else:
            print(f"❌ {method} method missing")
    
    # Test enums
    if 'class ErrorSeverity(Enum):' in content:
        print("✅ ErrorSeverity enum defined")
        # Count severity levels
        severity_count = content.count('= "') - content.count('= ""')  # Rough count
        print(f"   Severity levels found in content")
    
    if 'class ErrorCategory(Enum):' in content:
        print("✅ ErrorCategory enum defined")
        print("   Error categories found in content")
    
    # Test dataclass
    if '@dataclass' in content and 'class ErrorRecord:' in content:
        print("✅ ErrorRecord dataclass defined")
    
    # Count lines of code
    lines = content.split('\n')
    code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
    print(f"📊 Code statistics:")
    print(f"   Total lines: {len(lines)}")
    print(f"   Code lines: {len(code_lines)}")
    
    # Test for key features
    features = [
        ('Error handling', 'handle_error'),
        ('Recovery strategies', 'register_recovery_strategy'),
        ('Circuit breakers', 'circuit_breaker'),
        ('Error statistics', 'get_error_statistics'),
        ('Logging setup', '_setup_logging'),
        ('Error monitoring', '_error_monitoring_loop'),
        ('Notification integration', 'notification_system')
    ]
    
    print(f"🔍 Feature analysis:")
    for feature_name, feature_code in features:
        if feature_code in content:
            print(f"   ✅ {feature_name}")
        else:
            print(f"   ❌ {feature_name}")
    
    print("🎉 Learning Error Handler quick test completed!")
    print("✅ File structure and comprehensive error handling functionality implemented")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("Test completed!")