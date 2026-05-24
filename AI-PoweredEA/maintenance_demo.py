"""
Maintenance Manager Demonstration

This script demonstrates the comprehensive maintenance and cleanup utilities
of the Learning Maintenance Manager.
"""

import os
import json
import tempfile
import shutil
import sqlite3
from datetime import datetime, timedelta
from Python.learning_maintenance_manager import LearningMaintenanceManager


def demonstrate_maintenance_features():
    """Demonstrate key maintenance and cleanup features."""
    print("🧹 AI Continuous Learning System - Maintenance Manager Demo")
    print("=" * 70)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, 'demo_maintenance_config.json')
    archive_dir = os.path.join(temp_dir, 'archives')
    temp_files_dir = os.path.join(temp_dir, 'temp')
    logs_dir = os.path.join(temp_dir, 'logs')
    models_dir = os.path.join(temp_dir, 'models')
    
    # Create demo configuration
    demo_config = {
        'maintenance_root': temp_dir,
        'archive_dir': archive_dir,
        'temp_dir': temp_files_dir,
        'logs_dir': logs_dir,
        'database_files': [
            'demo_performance.db',
            'demo_audit.db',
            'demo_privacy.db'
        ],
        'model_directories': ['models'],
        'log_files': [
            'demo_performance.log',
            'demo_security.log',
            'demo_privacy.log'
        ],
        'cleanup_policies': {
            'old_data_days': 30,
            'old_logs_days': 14,
            'old_models_days': 60,
            'temp_files_hours': 24,
            'archive_retention_days': 365
        },
        'optimization_settings': {
            'database_vacuum_enabled': True,
            'model_compression_enabled': True,
            'memory_cleanup_enabled': True,
            'disk_cleanup_enabled': True
        },
        'maintenance_schedule': {
            'daily_cleanup_time': '02:00',
            'weekly_optimization_day': 'sunday',
            'weekly_optimization_time': '03:00',
            'monthly_archive_day': 1,
            'monthly_archive_time': '04:00'
        },
        'performance_thresholds': {
            'max_cpu_percent': 80,
            'max_memory_percent': 85,
            'max_disk_percent': 90,
            'min_free_space_gb': 5
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(demo_config, f, indent=2)
    
    # Create demo directories
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(temp_files_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    try:
        # Create demo data
        _create_demo_databases(temp_dir)
        _create_demo_log_files(logs_dir)
        _create_demo_model_files(models_dir)
        _create_demo_temp_files(temp_files_dir)
        
        # Initialize maintenance manager
        print("\n1. 🚀 Initializing Maintenance Manager...")
        maintenance_manager = LearningMaintenanceManager(config_path)
        print("   ✅ Maintenance manager initialized successfully")
        print(f"   📁 Maintenance root: {temp_dir}")
        print(f"   📦 Archive directory: {archive_dir}")
        print(f"   🗂️ Temp directory: {temp_files_dir}")
        print(f"   📋 Logs directory: {logs_dir}")
        
        # Demonstrate system status
        print("\n2. 📊 System Status Assessment...")
        status = maintenance_manager.get_system_status()
        
        print(f"   💾 Disk Usage: {status.get('disk_usage_percent', 0):.1f}%")
        print(f"   💿 Free Space: {status.get('free_space_gb', 0):.2f} GB")
        print(f"   🗄️ Database Files: {len(status.get('database_sizes_mb', {}))}")
        print(f"   📋 Log Files: {len(status.get('log_sizes_mb', {}))}")
        print(f"   🤖 Model Files: {status.get('model_count', 0)}")
        print(f"   🗂️ Temp Files: {status.get('temp_files_count', 0)}")
        print(f"   📦 Archives: {status.get('archive_count', 0)}")
        
        if status.get('database_sizes_mb'):
            print("   📊 Database Sizes:")
            for db_name, size_mb in status['database_sizes_mb'].items():
                print(f"      • {db_name}: {size_mb:.2f} MB")
        
        if status.get('log_sizes_mb'):
            print("   📋 Log File Sizes:")
            for log_name, size_mb in status['log_sizes_mb'].items():
                print(f"      • {log_name}: {size_mb:.2f} MB")
        
        maintenance_needed = "🔴 YES" if status.get('maintenance_needed', False) else "🟢 NO"
        print(f"   🔧 Maintenance Needed: {maintenance_needed}")
        
        if status.get('recommendations'):
            print("   💡 Recommendations:")
            for rec in status['recommendations']:
                print(f"      • {rec}")
        
        # Demonstrate old data cleanup
        print("\n3. 🧹 Old Data Cleanup...")
        
        cleanup_results = maintenance_manager.cleanup_old_data()
        
        print(f"   🗄️ Databases Cleaned: {len(cleanup_results.get('databases_cleaned', {}))}")
        for db_name, count in cleanup_results.get('databases_cleaned', {}).items():
            print(f"      • {db_name}: {count} old records removed")
        
        print(f"   📋 Log Files Cleaned: {len(cleanup_results.get('logs_cleaned', {}))}")
        for log_name, info in cleanup_results.get('logs_cleaned', {}).items():
            lines = info.get('lines_removed', 0)
            space = info.get('space_freed_mb', 0)
            print(f"      • {log_name}: {lines} lines removed ({space:.2f} MB freed)")
        
        print(f"   🗂️ Temp Files Cleaned: {cleanup_results.get('temp_files_cleaned', 0)}")
        print(f"   💾 Total Space Freed: {cleanup_results.get('total_space_freed_mb', 0):.2f} MB")
        
        if cleanup_results.get('errors'):
            print("   ⚠️ Cleanup Errors:")
            for error in cleanup_results['errors']:
                print(f"      • {error}")
        
        # Demonstrate model optimization
        print("\n4. 🤖 Model Optimization...")
        
        optimization_results = maintenance_manager.optimize_models()
        
        print(f"   🔧 Models Optimized: {optimization_results.get('models_optimized', 0)}")
        print(f"   📦 Models Compressed: {optimization_results.get('models_compressed', 0)}")
        print(f"   🗑️ Old Models Removed: {optimization_results.get('old_models_removed', 0)}")
        print(f"   💾 Space Saved: {optimization_results.get('space_saved_mb', 0):.2f} MB")
        
        if optimization_results.get('errors'):
            print("   ⚠️ Optimization Errors:")
            for error in optimization_results['errors']:
                print(f"      • {error}")
        
        # Demonstrate database optimization
        print("\n5. 🗄️ Database Optimization...")
        
        db_optimization_results = maintenance_manager.optimize_databases()
        
        print(f"   🔧 Databases Vacuumed: {db_optimization_results.get('databases_vacuumed', 0)}")
        print(f"   📊 Indexes Rebuilt: {db_optimization_results.get('indexes_rebuilt', 0)}")
        print(f"   💾 Space Reclaimed: {db_optimization_results.get('space_reclaimed_mb', 0):.2f} MB")
        
        if db_optimization_results.get('errors'):
            print("   ⚠️ Database Optimization Errors:")
            for error in db_optimization_results['errors']:
                print(f"      • {error}")
        
        # Demonstrate memory cleanup
        print("\n6. 🧠 Memory Cleanup...")
        
        memory_cleanup_results = maintenance_manager.cleanup_memory()
        
        memory_before = memory_cleanup_results.get('memory_before_mb', 0)
        memory_after = memory_cleanup_results.get('memory_after_mb', 0)
        memory_freed = memory_cleanup_results.get('memory_freed_mb', 0)
        garbage_collected = memory_cleanup_results.get('garbage_collected', 0)
        
        print(f"   📊 Memory Before: {memory_before:.2f} MB")
        print(f"   📊 Memory After: {memory_after:.2f} MB")
        print(f"   💾 Memory Freed: {memory_freed:.2f} MB")
        print(f"   🗑️ Objects Collected: {garbage_collected}")
        
        # Demonstrate data archival
        print("\n7. 📦 Data Archival...")
        
        archival_results = maintenance_manager.archive_old_data()
        
        print(f"   📦 Archives Created: {archival_results.get('archives_created', 0)}")
        print(f"   📁 Files Archived: {archival_results.get('files_archived', 0)}")
        print(f"   💾 Space Saved: {archival_results.get('space_saved_mb', 0):.2f} MB")
        
        if archival_results.get('errors'):
            print("   ⚠️ Archival Errors:")
            for error in archival_results['errors']:
                print(f"      • {error}")
        
        # List created archives
        if os.path.exists(archive_dir):
            archives = [f for f in os.listdir(archive_dir) if f.endswith('.zip')]
            if archives:
                print("   📦 Created Archives:")
                for archive in archives:
                    archive_path = os.path.join(archive_dir, archive)
                    size_mb = os.path.getsize(archive_path) / (1024 * 1024)
                    print(f"      • {archive} ({size_mb:.2f} MB)")
        
        # Demonstrate full maintenance cycle
        print("\n8. 🔄 Full Maintenance Cycle...")
        
        maintenance_results = maintenance_manager.run_full_maintenance()
        
        print(f"   ⏰ Start Time: {maintenance_results.get('start_time', '')[:19]}")
        print(f"   ⏰ End Time: {maintenance_results.get('end_time', '')[:19]}")
        
        print("   📋 Maintenance Steps:")
        steps = maintenance_results.get('steps', {})
        step_names = {
            'data_cleanup': 'Data Cleanup',
            'model_optimization': 'Model Optimization',
            'database_optimization': 'Database Optimization',
            'memory_cleanup': 'Memory Cleanup',
            'archival': 'Data Archival'
        }
        
        for step_key, step_name in step_names.items():
            if step_key in maintenance_results:
                step_data = maintenance_results[step_key]
                if isinstance(step_data, dict) and not step_data.get('errors'):
                    print(f"      ✅ {step_name}")
                else:
                    print(f"      ⚠️ {step_name} (with issues)")
        
        overall_success = "✅ SUCCESS" if maintenance_results.get('overall_success', False) else "❌ FAILED"
        print(f"   🎯 Overall Result: {overall_success}")
        print(f"   💾 Total Space Saved: {maintenance_results.get('total_space_saved_mb', 0):.2f} MB")
        
        # Demonstrate scheduled maintenance
        print("\n9. ⏰ Scheduled Maintenance...")
        
        try:
            import schedule
            print("   📅 Starting scheduled maintenance...")
            maintenance_manager.start_scheduled_maintenance()
            
            if maintenance_manager.scheduler_running:
                print("   ✅ Scheduled maintenance started successfully")
                print("   📋 Scheduled Tasks:")
                print("      • Daily cleanup at 02:00")
                print("      • Weekly optimization on Sunday at 03:00")
                print("      • Weekly archival on Sunday at 04:00")
                
                # Stop scheduler
                maintenance_manager.stop_scheduled_maintenance()
                print("   🛑 Scheduled maintenance stopped")
            else:
                print("   ❌ Failed to start scheduled maintenance")
                
        except ImportError:
            print("   ⚠️ Schedule module not available - manual maintenance only")
        
        # Final system status
        print("\n10. 📊 Final System Status...")
        
        final_status = maintenance_manager.get_system_status()
        
        print(f"   💾 Final Disk Usage: {final_status.get('disk_usage_percent', 0):.1f}%")
        print(f"   💿 Final Free Space: {final_status.get('free_space_gb', 0):.2f} GB")
        print(f"   🗂️ Final Temp Files: {final_status.get('temp_files_count', 0)}")
        print(f"   📦 Final Archives: {final_status.get('archive_count', 0)}")
        
        maintenance_needed = "🔴 YES" if final_status.get('maintenance_needed', False) else "🟢 NO"
        print(f"   🔧 Maintenance Still Needed: {maintenance_needed}")
        
        print("\n🎉 Maintenance Manager Demo Completed Successfully!")
        print("=" * 70)
        print("\n📋 Key Maintenance Features Demonstrated:")
        print("   • 📊 System status monitoring and assessment")
        print("   • 🧹 Automated old data cleanup and removal")
        print("   • 🤖 Model optimization and compression")
        print("   • 🗄️ Database vacuum and index optimization")
        print("   • 🧠 Memory cleanup and garbage collection")
        print("   • 📦 Data archival and compression")
        print("   • 🔄 Complete maintenance cycle automation")
        print("   • ⏰ Scheduled maintenance task management")
        print("\n🧹 Your AI learning system is now optimized and maintained!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


def _create_demo_databases(temp_dir):
    """Create demo database files with sample data."""
    databases = ['demo_performance.db', 'demo_audit.db', 'demo_privacy.db']
    
    for db_name in databases:
        db_path = os.path.join(temp_dir, db_name)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create sample tables with old and new data
        if 'performance' in db_name:
            cursor.execute('''
                CREATE TABLE performance_records (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    accuracy REAL,
                    created_at TEXT
                )
            ''')
            
            # Insert old and new records
            old_date = (datetime.now() - timedelta(days=45)).isoformat()
            new_date = datetime.now().isoformat()
            
            for i in range(10):
                cursor.execute('INSERT INTO performance_records VALUES (?, ?, ?, ?)', 
                             (i, old_date, 0.85 + i*0.01, old_date))
            
            for i in range(10, 15):
                cursor.execute('INSERT INTO performance_records VALUES (?, ?, ?, ?)', 
                             (i, new_date, 0.90 + (i-10)*0.01, new_date))
        
        elif 'audit' in db_name:
            cursor.execute('''
                CREATE TABLE audit_log (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    user_id TEXT,
                    operation TEXT
                )
            ''')
            
            old_date = (datetime.now() - timedelta(days=35)).isoformat()
            new_date = datetime.now().isoformat()
            
            for i in range(20):
                cursor.execute('INSERT INTO audit_log VALUES (?, ?, ?, ?)', 
                             (i, old_date, f"user{i}", "test_operation"))
            
            for i in range(20, 25):
                cursor.execute('INSERT INTO audit_log VALUES (?, ?, ?, ?)', 
                             (i, new_date, f"user{i}", "recent_operation"))
        
        elif 'privacy' in db_name:
            cursor.execute('''
                CREATE TABLE data_records (
                    id TEXT PRIMARY KEY,
                    created_at TEXT,
                    expires_at TEXT,
                    data_category TEXT
                )
            ''')
            
            old_date = (datetime.now() - timedelta(days=40)).isoformat()
            new_date = datetime.now().isoformat()
            
            for i in range(15):
                cursor.execute('INSERT INTO data_records VALUES (?, ?, ?, ?)', 
                             (f"record_{i}", old_date, old_date, "old_data"))
            
            for i in range(15, 20):
                cursor.execute('INSERT INTO data_records VALUES (?, ?, ?, ?)', 
                             (f"record_{i}", new_date, new_date, "new_data"))
        
        conn.commit()
        conn.close()


def _create_demo_log_files(logs_dir):
    """Create demo log files with sample entries."""
    log_files = ['demo_performance.log', 'demo_security.log', 'demo_privacy.log']
    
    for log_file in log_files:
        log_path = os.path.join(logs_dir, log_file)
        
        with open(log_path, 'w') as f:
            # Write old log entries
            old_date = (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d %H:%M:%S')
            for i in range(50):
                f.write(f"{old_date} - INFO - Old log entry {i} for {log_file}\n")
            
            # Write new log entries
            new_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for i in range(10):
                f.write(f"{new_date} - INFO - Recent log entry {i} for {log_file}\n")


def _create_demo_model_files(models_dir):
    """Create demo model files."""
    # Create old model files
    for i in range(3):
        old_model = os.path.join(models_dir, f'old_model_{i}.pkl')
        with open(old_model, 'w') as f:
            f.write(f'Old model data {i} ' * 100)  # Make it larger for compression demo
        
        # Set old timestamp
        old_time = (datetime.now() - timedelta(days=70)).timestamp()
        os.utime(old_model, (old_time, old_time))
    
    # Create new model files
    for i in range(2):
        new_model = os.path.join(models_dir, f'new_model_{i}.pkl')
        with open(new_model, 'w') as f:
            f.write(f'New model data {i} ' * 200)  # Larger for compression


def _create_demo_temp_files(temp_files_dir):
    """Create demo temporary files."""
    # Create old temp files
    for i in range(5):
        old_temp = os.path.join(temp_files_dir, f'old_temp_{i}.tmp')
        with open(old_temp, 'w') as f:
            f.write(f'Old temporary data {i}')
        
        # Set old timestamp
        old_time = (datetime.now() - timedelta(hours=30)).timestamp()
        os.utime(old_temp, (old_time, old_time))
    
    # Create new temp files
    for i in range(3):
        new_temp = os.path.join(temp_files_dir, f'new_temp_{i}.tmp')
        with open(new_temp, 'w') as f:
            f.write(f'New temporary data {i}')


if __name__ == "__main__":
    demonstrate_maintenance_features()