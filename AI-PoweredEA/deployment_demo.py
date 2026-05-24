"""
Deployment Manager Demonstration

This script demonstrates the comprehensive deployment automation features
of the Learning Deployment Manager.
"""

import os
import json
import tempfile
import shutil
from datetime import datetime
from Python.learning_deployment_manager import LearningDeploymentManager


def demonstrate_deployment_features():
    """Demonstrate key deployment automation features."""
    print("🚀 AI Continuous Learning System - Deployment Manager Demo")
    print("=" * 70)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'demo_deployment_config.json')
    backup_dir = os.path.join(temp_dir, 'backups')
    logs_dir = os.path.join(temp_dir, 'logs')
    
    # Create demo configuration
    demo_config = {
        'deployment_root': temp_dir,
        'backup_dir': backup_dir,
        'logs_dir': logs_dir,
        'python_executable': 'python',
        'required_python_version': '3.8',
        'required_packages': [
            'json',  # Built-in for demo
        ],
        'database_files': [
            'demo_performance.db',
            'demo_audit.db',
            'demo_privacy.db'
        ],
        'config_files': [
            'demo_learning_config.json',
            'demo_security_config.json'
        ],
        'python_modules': [
            'demo_performance_monitor.py',
            'demo_learning_coordinator.py',
            'demo_model_manager.py'
        ],
        'health_check_endpoints': [
            'performance_monitor',
            'learning_coordinator',
            'model_manager'
        ],
        'deployment_environments': ['development', 'staging', 'production'],
        'backup_retention_days': 30,
        'health_check_timeout': 30
    }
    
    with open(config_path, 'w') as f:
        json.dump(demo_config, f, indent=2)
    
    # Create demo files
    demo_files = {
        'demo_performance.db': 'database',
        'demo_audit.db': 'database',
        'demo_privacy.db': 'database',
        'demo_learning_config.json': {'learning': {'enabled': True}},
        'demo_security_config.json': {'security': {'encryption': True}},
        'demo_performance_monitor.py': '# Performance Monitor Module\nclass PerformanceMonitor:\n    pass\n',
        'demo_learning_coordinator.py': '# Learning Coordinator Module\nclass LearningCoordinator:\n    pass\n',
        'demo_model_manager.py': '# Model Manager Module\nclass ModelManager:\n    pass\n'
    }
    
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Create demo files
        for filename, content in demo_files.items():
            filepath = os.path.join(temp_dir, filename)
            if filename.endswith('.db'):
                # Create demo database
                import sqlite3
                conn = sqlite3.connect(filepath)
                conn.execute('CREATE TABLE demo (id INTEGER, name TEXT)')
                conn.execute('INSERT INTO demo VALUES (1, "demo_data")')
                conn.commit()
                conn.close()
            elif filename.endswith('.json'):
                with open(filepath, 'w') as f:
                    json.dump(content, f, indent=2)
            else:
                with open(filepath, 'w') as f:
                    f.write(content)
        
        # Initialize deployment manager
        print("\n1. 🚀 Initializing Deployment Manager...")
        deployment_manager = LearningDeploymentManager(config_path)
        print("   ✅ Deployment manager initialized successfully")
        print(f"   📁 Deployment root: {temp_dir}")
        print(f"   💾 Backup directory: {backup_dir}")
        print(f"   📋 Logs directory: {logs_dir}")
        
        # Demonstrate environment validation
        print("\n2. 🔍 Environment Validation...")
        validation_result = deployment_manager.validate_environment()
        
        print(f"   🐍 Python Version: {'✅ PASS' if validation_result['python_version'] else '❌ FAIL'}")
        print(f"   📦 Required Packages: {'✅ PASS' if validation_result['required_packages'] else '❌ FAIL'}")
        print(f"   📝 File Permissions: {'✅ PASS' if validation_result['file_permissions'] else '❌ FAIL'}")
        print(f"   💾 Disk Space: {'✅ PASS' if validation_result['disk_space'] else '❌ FAIL'}")
        print(f"   🗄️ Database Access: {'✅ PASS' if validation_result['database_access'] else '❌ FAIL'}")
        
        overall_status = "✅ PASSED" if validation_result['overall_status'] else "❌ FAILED"
        print(f"   🎯 Overall Status: {overall_status}")
        
        if validation_result['errors']:
            print("   ⚠️ Errors found:")
            for error in validation_result['errors']:
                print(f"      • {error}")
        
        if validation_result['warnings']:
            print("   ⚠️ Warnings:")
            for warning in validation_result['warnings']:
                print(f"      • {warning}")
        
        # Demonstrate backup creation
        print("\n3. 💾 Backup Management...")
        
        print("   📦 Creating system backup...")
        backup_path = deployment_manager.create_backup('demo_backup')
        print(f"   ✅ Backup created: {os.path.basename(backup_path)}")
        
        # Show backup contents
        import zipfile
        with zipfile.ZipFile(backup_path, 'r') as backup_zip:
            file_count = len(backup_zip.namelist())
            print(f"   📊 Files in backup: {file_count}")
            
            # Read metadata
            try:
                metadata_content = backup_zip.read('backup_metadata.json')
                metadata = json.loads(metadata_content.decode('utf-8'))
                print(f"   📅 Backup timestamp: {metadata['created_at'][:19]}")
                print(f"   🐍 Python version: {metadata['python_version'][:10]}...")
            except:
                print("   📋 Metadata: Not available")
        
        # Demonstrate database migration
        print("\n4. 🗄️ Database Migration...")
        
        migration_results = deployment_manager.migrate_databases()
        print(f"   📊 Databases processed: {len(migration_results)}")
        
        for db_name, success in migration_results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"   {status} {db_name}")
        
        successful_migrations = sum(migration_results.values())
        total_migrations = len(migration_results)
        print(f"   🎯 Migration success rate: {successful_migrations}/{total_migrations}")
        
        # Demonstrate health check
        print("\n5. 🏥 System Health Check...")
        
        health_results = deployment_manager.perform_health_check()
        
        print("   🔧 Component Health:")
        for component, status in health_results['components'].items():
            status_icon = "✅" if status else "❌"
            print(f"      {status_icon} {component}")
        
        print("   🗄️ Database Health:")
        for db_name, status in health_results['database_status'].items():
            status_icon = "✅" if status else "❌"
            print(f"      {status_icon} {db_name}")
        
        print("   📁 File Integrity:")
        for file_path, status in health_results['file_integrity'].items():
            status_icon = "✅" if status else "❌"
            filename = os.path.basename(file_path)
            print(f"      {status_icon} {filename}")
        
        if 'performance_metrics' in health_results:
            print("   📊 Performance Metrics:")
            metrics = health_results['performance_metrics']
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    print(f"      📈 {metric}: {value:.1f}%")
                else:
                    print(f"      📋 {metric}: {value}")
        
        overall_health = "🟢 HEALTHY" if health_results['overall_status'] else "🔴 UNHEALTHY"
        print(f"   🎯 Overall Health: {overall_health}")
        
        # Demonstrate deployment process
        print("\n6. 🚀 Full Deployment Process...")
        
        print("   🎯 Deploying to development environment...")
        deployment_result = deployment_manager.deploy_system(
            environment='development',
            skip_backup=False
        )
        
        print(f"   🌍 Target Environment: {deployment_result['environment']}")
        print(f"   ⏰ Start Time: {deployment_result['start_time'][:19]}")
        
        print("   📋 Deployment Steps:")
        for step_name, step_result in deployment_result['steps'].items():
            status_icon = "✅" if step_result else "❌"
            step_display = step_name.replace('_', ' ').title()
            print(f"      {status_icon} {step_display}")
        
        if 'end_time' in deployment_result:
            print(f"   ⏰ End Time: {deployment_result['end_time'][:19]}")
        
        overall_success = "✅ SUCCESS" if deployment_result['overall_success'] else "❌ FAILED"
        print(f"   🎯 Deployment Result: {overall_success}")
        
        if 'backup_path' in deployment_result:
            backup_name = os.path.basename(deployment_result['backup_path'])
            print(f"   💾 Pre-deployment backup: {backup_name}")
        
        # Demonstrate deployment status
        print("\n7. 📊 Deployment Status...")
        
        status = deployment_manager.get_deployment_status()
        
        print(f"   📁 Deployment Root: {status['deployment_root']}")
        print(f"   🐍 Python Version: {status['python_version'][:20]}...")
        print(f"   💾 Backup Count: {status['backup_count']}")
        print(f"   📋 Log Files: {len(status['log_files'])}")
        
        print("   🗄️ Database Files:")
        for db_name, db_info in status['database_files'].items():
            exists_icon = "✅" if db_info['exists'] else "❌"
            size_kb = db_info['size'] / 1024 if db_info['size'] > 0 else 0
            print(f"      {exists_icon} {db_name} ({size_kb:.1f} KB)")
        
        print("   📁 Module Files:")
        for module_name, module_info in status['module_files'].items():
            exists_icon = "✅" if module_info['exists'] else "❌"
            size_bytes = module_info['size']
            filename = os.path.basename(module_name)
            print(f"      {exists_icon} {filename} ({size_bytes} bytes)")
        
        # Demonstrate backup cleanup
        print("\n8. 🧹 Backup Cleanup...")
        
        # Create some old backup files for demo
        old_backup1 = os.path.join(backup_dir, 'old_backup_1.zip')
        old_backup2 = os.path.join(backup_dir, 'old_backup_2.zip')
        
        with open(old_backup1, 'w') as f:
            f.write('old backup 1')
        with open(old_backup2, 'w') as f:
            f.write('old backup 2')
        
        # Set old timestamps
        from datetime import timedelta
        old_time = datetime.now() - timedelta(days=35)
        os.utime(old_backup1, (old_time.timestamp(), old_time.timestamp()))
        os.utime(old_backup2, (old_time.timestamp(), old_time.timestamp()))
        
        print(f"   📦 Backups before cleanup: {len([f for f in os.listdir(backup_dir) if f.endswith('.zip')])}")
        
        cleaned_count = deployment_manager.cleanup_old_backups()
        
        remaining_backups = len([f for f in os.listdir(backup_dir) if f.endswith('.zip')])
        print(f"   🗑️ Old backups cleaned: {cleaned_count}")
        print(f"   📦 Backups remaining: {remaining_backups}")
        
        # Demonstrate backup restore
        print("\n9. 🔄 Backup Restore...")
        
        # Modify a file to test restore
        config_file = 'demo_learning_config.json'
        print(f"   📝 Modifying {config_file}...")
        with open(config_file, 'w') as f:
            json.dump({'modified': 'content'}, f)
        
        print(f"   🔄 Restoring from backup...")
        restore_success = deployment_manager.restore_backup(backup_path)
        
        if restore_success:
            print("   ✅ Backup restored successfully")
            # Verify restoration
            with open(config_file, 'r') as f:
                restored_content = json.load(f)
                if 'learning' in restored_content:
                    print("   ✅ File content verified as restored")
                else:
                    print("   ⚠️ File content may not be fully restored")
        else:
            print("   ❌ Backup restore failed")
        
        print("\n🎉 Deployment Manager Demo Completed Successfully!")
        print("=" * 70)
        print("\n📋 Key Deployment Features Demonstrated:")
        print("   • 🔍 Comprehensive environment validation")
        print("   • 💾 Automated backup creation and management")
        print("   • 🗄️ Database migration and setup automation")
        print("   • 🏥 System health checks and monitoring")
        print("   • 🚀 Complete deployment automation workflow")
        print("   • 📊 Deployment status and reporting")
        print("   • 🧹 Automated backup cleanup and retention")
        print("   • 🔄 Backup restore and rollback capabilities")
        print("\n🚀 Your AI learning system is now deployment-ready!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    demonstrate_deployment_features()