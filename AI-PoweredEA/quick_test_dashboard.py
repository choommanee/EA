"""
Quick test for Learning Dashboard
"""

import sys
import os
sys.path.append('Python')

# Test direct import
try:
    from Python.learning_dashboard import LearningDashboard, ChartType, ReportType
    print("✓ Successfully imported LearningDashboard")
    
    # Test initialization
    dashboard = LearningDashboard()
    print("✓ Successfully initialized LearningDashboard")
    
    # Test chart creation
    chart = dashboard.create_learning_progress_chart("test_model", 24)
    print(f"✓ Created chart: {chart.title}")
    
    # Test model comparison
    comparison_chart = dashboard.create_model_comparison_chart(["model_1", "model_2"], "accuracy")
    print(f"✓ Created comparison chart: {comparison_chart.title}")
    
    # Test report generation
    report = dashboard.generate_learning_progress_report("test_model", 24)
    print(f"✓ Generated report: {report.title}")
    
    # Test widget creation
    from Python.learning_dashboard import DashboardWidget
    widget = DashboardWidget(
        widget_id="test_widget",
        widget_type="learning_progress",
        title="Test Widget",
        data_source="test",
        refresh_interval=30
    )
    
    success = dashboard.create_dashboard_widget(widget)
    print(f"✓ Created widget: {success}")
    
    # Test dashboard data
    dashboard_data = dashboard.get_dashboard_data()
    print(f"✓ Retrieved dashboard data with {len(dashboard_data.get('widgets', {}))} widgets")
    
    print("\n🎉 All dashboard tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()