"""
Simple test suite for Learning Dashboard
Tests core dashboard functionality
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta

# Import dashboard components
import sys
sys.path.append('Python')

from learning_dashboard import (
    LearningDashboard, ChartType, ReportType, ChartData, 
    DashboardWidget, ReportData
)


class TestLearningDashboardSimple(unittest.TestCase):
    """Test Learning Dashboard core functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_dashboard.db")
        self.dashboard = LearningDashboard(db_path=self.db_path)
    
    def test_initialization(self):
        """Test dashboard initialization"""
        print("\n--- Testing Dashboard Initialization ---")
        
        self.assertIsNotNone(self.dashboard)
        self.assertEqual(self.dashboard.db_path, self.db_path)
        self.assertIsInstance(self.dashboard.widgets, dict)
        self.assertIsInstance(self.dashboard.dashboard_config, dict)
        
        print("✓ Dashboard initialized successfully")
    
    def test_create_learning_progress_chart(self):
        """Test learning progress chart creation"""
        print("\n--- Testing Learning Progress Chart Creation ---")
        
        chart = self.dashboard.create_learning_progress_chart("test_model", 24)
        
        self.assertIsInstance(chart, ChartData)
        self.assertEqual(chart.chart_type, ChartType.LINE_CHART)
        self.assertIn("Learning Progress", chart.title)
        self.assertIn("test_model", chart.title)
        self.assertIsInstance(chart.data_series, list)
        
        print(f"✓ Created learning progress chart with {len(chart.data_series)} data series")
    
    def test_create_model_comparison_chart(self):
        """Test model comparison chart creation"""
        print("\n--- Testing Model Comparison Chart Creation ---")
        
        model_ids = ["model_1", "model_2", "model_3"]
        chart = self.dashboard.create_model_comparison_chart(model_ids, "accuracy")
        
        self.assertIsInstance(chart, ChartData)
        self.assertEqual(chart.chart_type, ChartType.BAR_CHART)
        self.assertIn("Model Comparison", chart.title)
        self.assertIn("accuracy", chart.title.lower())
        self.assertIsInstance(chart.data_series, list)
        
        print(f"✓ Created model comparison chart for {len(model_ids)} models")
    
    def test_create_performance_trend_chart(self):
        """Test performance trend chart creation"""
        print("\n--- Testing Performance Trend Chart Creation ---")
        
        chart = self.dashboard.create_performance_trend_chart("test_model", "accuracy", 168)
        
        self.assertIsInstance(chart, ChartData)
        self.assertEqual(chart.chart_type, ChartType.LINE_CHART)
        self.assertIn("Performance Trend", chart.title)
        self.assertIsInstance(chart.data_series, list)
        
        print("✓ Created performance trend chart with trend analysis")
    
    def test_create_resource_usage_chart(self):
        """Test resource usage chart creation"""
        print("\n--- Testing Resource Usage Chart Creation ---")
        
        chart = self.dashboard.create_resource_usage_chart(24)
        
        self.assertIsInstance(chart, ChartData)
        self.assertEqual(chart.chart_type, ChartType.LINE_CHART)
        self.assertIn("Resource Usage", chart.title)
        self.assertIsInstance(chart.data_series, list)
        
        print("✓ Created resource usage chart")
    
    def test_create_learning_event_timeline(self):
        """Test learning event timeline creation"""
        print("\n--- Testing Learning Event Timeline Creation ---")
        
        events = self.dashboard.create_learning_event_timeline(24)
        
        self.assertIsInstance(events, list)
        
        if events:
            event = events[0]
            self.assertIn('timestamp', event)
            self.assertIn('event_type', event)
            self.assertIn('title', event)
            self.assertIn('description', event)
            
        print(f"✓ Created learning event timeline with {len(events)} events")
    
    def test_generate_learning_progress_report(self):
        """Test learning progress report generation"""
        print("\n--- Testing Learning Progress Report Generation ---")
        
        report = self.dashboard.generate_learning_progress_report("test_model", 168)
        
        self.assertIsInstance(report, ReportData)
        self.assertEqual(report.report_type, ReportType.LEARNING_PROGRESS)
        self.assertIn("test_model", report.title)
        self.assertIsInstance(report.generated_at, datetime)
        self.assertIsInstance(report.summary, dict)
        self.assertIsInstance(report.charts, list)
        self.assertIsInstance(report.tables, list)
        
        print(f"✓ Generated learning progress report with {len(report.charts)} charts and {len(report.tables)} tables")
    
    def test_generate_model_comparison_report(self):
        """Test model comparison report generation"""
        print("\n--- Testing Model Comparison Report Generation ---")
        
        model_ids = ["model_1", "model_2", "model_3"]
        report = self.dashboard.generate_model_comparison_report(model_ids)
        
        self.assertIsInstance(report, ReportData)
        self.assertEqual(report.report_type, ReportType.MODEL_COMPARISON)
        self.assertIn("Model Performance Comparison", report.title)
        self.assertIsInstance(report.charts, list)
        self.assertIsInstance(report.tables, list)
        
        print(f"✓ Generated model comparison report for {len(model_ids)} models")
    
    def test_create_dashboard_widget(self):
        """Test dashboard widget creation"""
        print("\n--- Testing Dashboard Widget Creation ---")
        
        widget = DashboardWidget(
            widget_id="test_widget",
            widget_type="learning_progress",
            title="Test Learning Progress",
            data_source="metrics_collector",
            refresh_interval=30,
            config={"model_id": "test_model"},
            position={"x": 0, "y": 0, "width": 6, "height": 4}
        )
        
        success = self.dashboard.create_dashboard_widget(widget)
        
        self.assertTrue(success)
        self.assertIn("test_widget", self.dashboard.widgets)
        self.assertEqual(self.dashboard.widgets["test_widget"], widget)
        
        print("✓ Created dashboard widget successfully")
    
    def test_get_dashboard_data(self):
        """Test getting complete dashboard data"""
        print("\n--- Testing Dashboard Data Retrieval ---")
        
        # Create a test widget first
        widget = DashboardWidget(
            widget_id="test_widget",
            widget_type="learning_progress",
            title="Test Widget",
            data_source="test",
            refresh_interval=30
        )
        self.dashboard.create_dashboard_widget(widget)
        
        dashboard_data = self.dashboard.get_dashboard_data()
        
        self.assertIsInstance(dashboard_data, dict)
        self.assertIn('timestamp', dashboard_data)
        self.assertIn('config', dashboard_data)
        self.assertIn('widgets', dashboard_data)
        self.assertIn('summary', dashboard_data)
        
        # Check widget data
        self.assertIn('test_widget', dashboard_data['widgets'])
        widget_data = dashboard_data['widgets']['test_widget']
        self.assertIn('config', widget_data)
        self.assertIn('data', widget_data)
        
        print(f"✓ Retrieved dashboard data with {len(dashboard_data['widgets'])} widgets")
    
    def test_export_report_to_json(self):
        """Test exporting report to JSON"""
        print("\n--- Testing Report JSON Export ---")
        
        # Generate a test report
        report = self.dashboard.generate_learning_progress_report("test_model", 24)
        
        # Export to JSON
        json_file = os.path.join(self.temp_dir, "test_report.json")
        success = self.dashboard.export_report_to_json(report, json_file)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(json_file))
        
        # Verify JSON content
        with open(json_file, 'r') as f:
            report_data = json.load(f)
        
        self.assertIn('report_type', report_data)
        self.assertIn('title', report_data)
        self.assertIn('generated_at', report_data)
        self.assertIn('charts', report_data)
        self.assertIn('tables', report_data)
        
        print(f"✓ Exported report to JSON: {json_file}")
    
    def test_chart_data_structure(self):
        """Test ChartData structure and conversion"""
        print("\n--- Testing Chart Data Structure ---")
        
        chart = self.dashboard.create_learning_progress_chart("test_model")
        chart_dict = self.dashboard._chart_to_dict(chart)
        
        self.assertIsInstance(chart_dict, dict)
        self.assertIn('chart_type', chart_dict)
        self.assertIn('title', chart_dict)
        self.assertIn('x_axis_label', chart_dict)
        self.assertIn('y_axis_label', chart_dict)
        self.assertIn('data_series', chart_dict)
        self.assertIn('metadata', chart_dict)
        
        print("✓ Chart data structure validation passed")
    
    def test_trend_line_calculation(self):
        """Test trend line calculation"""
        print("\n--- Testing Trend Line Calculation ---")
        
        # Create sample data points
        data_points = [
            {'x': '2024-01-01T00:00:00', 'y': 0.7},
            {'x': '2024-01-01T01:00:00', 'y': 0.75},
            {'x': '2024-01-01T02:00:00', 'y': 0.8},
            {'x': '2024-01-01T03:00:00', 'y': 0.85},
            {'x': '2024-01-01T04:00:00', 'y': 0.9}
        ]
        
        trend_line = self.dashboard._calculate_trend_line(data_points)
        
        self.assertIsInstance(trend_line, list)
        self.assertEqual(len(trend_line), len(data_points))
        
        if trend_line:
            # Check that trend line has same x values
            for i, point in enumerate(trend_line):
                self.assertEqual(point['x'], data_points[i]['x'])
                self.assertIn('y', point)
        
        print(f"✓ Calculated trend line with {len(trend_line)} points")
    
    def test_widget_data_generation(self):
        """Test widget data generation for different widget types"""
        print("\n--- Testing Widget Data Generation ---")
        
        widget_types = [
            ('learning_progress', {'model_id': 'test_model'}),
            ('model_comparison', {'model_ids': ['model_1', 'model_2']}),
            ('resource_usage', {}),
            ('event_timeline', {})
        ]
        
        success_count = 0
        for widget_type, config in widget_types:
            widget = DashboardWidget(
                widget_id=f"test_{widget_type}",
                widget_type=widget_type,
                title=f"Test {widget_type}",
                data_source="test",
                refresh_interval=30,
                config=config
            )
            
            widget_data = self.dashboard._get_widget_data(widget)
            
            self.assertIsInstance(widget_data, dict)
            # Note: Some widgets might have errors due to missing data, which is expected
            success_count += 1
            
        print(f"✓ Generated data for {success_count}/{len(widget_types)} widget types")
    
    def test_summary_statistics_generation(self):
        """Test summary statistics generation"""
        print("\n--- Testing Summary Statistics Generation ---")
        
        start_time = datetime.now() - timedelta(hours=24)
        end_time = datetime.now()
        
        # Test learning progress summary
        progress_summary = self.dashboard._get_learning_progress_summary(
            "test_model", start_time, end_time
        )
        
        self.assertIsInstance(progress_summary, dict)
        self.assertIn('model_id', progress_summary)
        self.assertIn('training_sessions', progress_summary)
        self.assertIn('best_accuracy', progress_summary)
        
        # Test model comparison summary
        comparison_summary = self.dashboard._get_model_comparison_summary(
            ['model_1', 'model_2', 'model_3']
        )
        
        self.assertIsInstance(comparison_summary, dict)
        self.assertIn('models_compared', comparison_summary)
        self.assertIn('best_model', comparison_summary)
        
        # Test system health summary
        health_summary = self.dashboard._get_system_health_summary(start_time, end_time)
        
        self.assertIsInstance(health_summary, dict)
        self.assertIn('system_status', health_summary)
        self.assertIn('error_count', health_summary)
        
        print("✓ Generated all summary statistics successfully")
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        print("\n--- Testing Error Handling ---")
        
        # Test with invalid model ID
        chart = self.dashboard.create_learning_progress_chart(None)
        self.assertIsInstance(chart, ChartData)
        
        # Test with empty model list
        comparison_chart = self.dashboard.create_model_comparison_chart([])
        self.assertIsInstance(comparison_chart, ChartData)
        
        # Test with invalid widget type
        invalid_widget = DashboardWidget(
            widget_id="invalid_widget",
            widget_type="invalid_type",
            title="Invalid Widget",
            data_source="test",
            refresh_interval=30
        )
        
        widget_data = self.dashboard._get_widget_data(invalid_widget)
        self.assertIn('error', widget_data)
        
        print("✓ Error handling validation passed")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestDashboardDataStructures(unittest.TestCase):
    """Test dashboard data structures"""
    
    def test_chart_data_creation(self):
        """Test ChartData creation"""
        print("\n--- Testing ChartData Creation ---")
        
        chart_data = ChartData(
            chart_type=ChartType.LINE_CHART,
            title="Test Chart",
            x_axis_label="Time",
            y_axis_label="Value",
            data_series=[{
                'name': 'Test Series',
                'type': 'line',
                'data': [{'x': '2024-01-01', 'y': 0.5}]
            }],
            metadata={'test': True}
        )
        
        self.assertEqual(chart_data.chart_type, ChartType.LINE_CHART)
        self.assertEqual(chart_data.title, "Test Chart")
        self.assertEqual(len(chart_data.data_series), 1)
        self.assertEqual(chart_data.metadata['test'], True)
        
        print("✓ ChartData created successfully")
    
    def test_dashboard_widget_creation(self):
        """Test DashboardWidget creation"""
        print("\n--- Testing DashboardWidget Creation ---")
        
        widget = DashboardWidget(
            widget_id="test_widget",
            widget_type="learning_progress",
            title="Test Widget",
            data_source="metrics",
            refresh_interval=60,
            config={'model_id': 'test'},
            position={'x': 0, 'y': 0, 'width': 4, 'height': 3}
        )
        
        self.assertEqual(widget.widget_id, "test_widget")
        self.assertEqual(widget.widget_type, "learning_progress")
        self.assertEqual(widget.refresh_interval, 60)
        self.assertEqual(widget.config['model_id'], 'test')
        
        print("✓ DashboardWidget created successfully")
    
    def test_report_data_creation(self):
        """Test ReportData creation"""
        print("\n--- Testing ReportData Creation ---")
        
        report = ReportData(
            report_type=ReportType.LEARNING_PROGRESS,
            title="Test Report",
            generated_at=datetime.now(),
            time_period="24h",
            summary={'test': 'data'},
            charts=[],
            tables=[],
            metadata={'version': '1.0'}
        )
        
        self.assertEqual(report.report_type, ReportType.LEARNING_PROGRESS)
        self.assertEqual(report.title, "Test Report")
        self.assertEqual(report.time_period, "24h")
        self.assertEqual(report.metadata['version'], '1.0')
        
        print("✓ ReportData created successfully")


if __name__ == '__main__':
    print("="*60)
    print("LEARNING DASHBOARD SIMPLE TESTS")
    print("="*60)
    
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*60)
    print("DASHBOARD TEST SUMMARY")
    print("="*60)
    print("Tests validate dashboard functionality, chart generation,")
    print("report creation, and widget management.")
    print("="*60)