"""
Test suite for Learning System UAT Manager

This module provides comprehensive tests for the user acceptance testing
and documentation functionality of the AI continuous learning system.
"""

import unittest
import tempfile
import shutil
import os
import json
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the Python directory to the path to import our modules
sys.path.append('Python')

try:
    from learning_system_uat_manager import LearningSystemUATManager
except ImportError as e:
    print(f"Warning: Could not import LearningSystemUATManager: {e}")
    LearningSystemUATManager = None


class TestLearningSystemUATManager(unittest.TestCase):
    """Test cases for Learning System UAT Manager."""
    
    def setUp(self):
        """Set up test environment."""
        if LearningSystemUATManager is None:
            self.skipTest("LearningSystemUATManager not available")
        
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_uat_config.json')
        
        # Create test configuration
        test_config = {
            'uat_root': self.test_dir,
            'docs_dir': os.path.join(self.test_dir, 'docs'),
            'user_scenarios': ['trader_onboarding', 'signal_analysis'],
            'acceptance_criteria': {
                'performance': {
                    'signal_processing_time_ms': 100,
                    'model_switching_time_ms': 1000,
                    'dashboard_load_time_ms': 2000,
                    'system_availability_percent': 99.0
                },
                'usability': {
                    'max_clicks_to_feature': 3,
                    'max_learning_time_minutes': 30,
                    'error_message_clarity_score': 8
                },
                'functionality': {
                    'feature_completeness_percent': 95,
                    'integration_success_rate': 98,
                    'data_accuracy_percent': 99
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        self.uat_manager = LearningSystemUATManager(self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_uat_manager_initialization(self):
        """Test UAT manager initialization."""
        self.assertIsNotNone(self.uat_manager)
        self.assertEqual(self.uat_manager.uat_config_path, self.config_path)
        self.assertIsNotNone(self.uat_manager.config)
        self.assertIsNotNone(self.uat_manager.logger)
    
    def test_uat_config_loading(self):
        """Test UAT configuration loading."""
        config = self.uat_manager.config
        
        self.assertIn('user_scenarios', config)
        self.assertIn('acceptance_criteria', config)
        self.assertIn('trader_onboarding', config['user_scenarios'])
        self.assertIn('signal_analysis', config['user_scenarios'])
    
    def test_uat_environment_setup(self):
        """Test UAT environment setup."""
        try:
            self.uat_manager._setup_uat_environment()
            
            # Check if UAT databases were created
            perf_db = os.path.join(self.test_dir, 'uat_performance.db')
            feedback_db = os.path.join(self.test_dir, 'uat_user_feedback.db')
            
            self.assertTrue(os.path.exists(perf_db))
            self.assertTrue(os.path.exists(feedback_db))
            
            # Check if configuration files were created
            config_file = os.path.join(self.test_dir, 'uat_learning_config.json')
            self.assertTrue(os.path.exists(config_file))
            
        except Exception as e:
            self.fail(f"UAT environment setup failed: {e}")
    
    def test_trader_onboarding_scenario(self):
        """Test trader onboarding user scenario."""
        try:
            result = self.uat_manager._test_trader_onboarding()
            
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('steps_completed', result)
            self.assertIn('user_experience_score', result)
            self.assertIn('time_to_complete_minutes', result)
            
            # Check that some steps were completed
            self.assertGreater(len(result['steps_completed']), 0)
            self.assertGreater(result['user_experience_score'], 0)
            
        except Exception as e:
            self.fail(f"Trader onboarding test failed: {e}")
    
    def test_signal_analysis_scenario(self):
        """Test signal analysis user scenario."""
        try:
            result = self.uat_manager._test_signal_analysis()
            
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('signals_analyzed', result)
            self.assertIn('analysis_accuracy', result)
            self.assertIn('performance_metrics', result)
            
            # Check performance metrics
            self.assertIn('avg_analysis_time_ms', result['performance_metrics'])
            self.assertIn('success_rate', result['performance_metrics'])
            
        except Exception as e:
            self.fail(f"Signal analysis test failed: {e}")
    
    def test_acceptance_criteria_validation(self):
        """Test acceptance criteria validation."""
        try:
            result = self.uat_manager._validate_acceptance_criteria()
            
            self.assertIsInstance(result, dict)
            self.assertIn('performance', result)
            self.assertIn('usability', result)
            self.assertIn('functionality', result)
            self.assertIn('overall_success', result)
            
            # Check performance criteria
            perf_result = result['performance']
            self.assertIn('all_passed', perf_result)
            
        except Exception as e:
            self.fail(f"Acceptance criteria validation failed: {e}")
    
    def test_documentation_generation(self):
        """Test user documentation generation."""
        try:
            result = self.uat_manager._generate_user_documentation()
            
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('documents_generated', result)
            self.assertIn('generated_files', result)
            
            # Check if documentation files were created
            docs_dir = self.uat_manager.docs_dir
            if os.path.exists(docs_dir):
                doc_files = os.listdir(docs_dir)
                self.assertGreater(len(doc_files), 0)
            
        except Exception as e:
            self.fail(f"Documentation generation failed: {e}")
    
    def test_user_guide_content(self):
        """Test user guide content generation."""
        try:
            content = self.uat_manager._get_user_guide_content()
            
            self.assertIsInstance(content, str)
            self.assertIn('AI Continuous Learning System', content)
            self.assertIn('Getting Started', content)
            self.assertIn('Signal Analysis', content)
            
        except Exception as e:
            self.fail(f"User guide content generation failed: {e}")
    
    def test_api_documentation_content(self):
        """Test API documentation content generation."""
        try:
            content = self.uat_manager._get_api_documentation_content()
            
            self.assertIsInstance(content, str)
            self.assertIn('API Documentation', content)
            self.assertIn('Endpoints', content)
            self.assertIn('Authentication', content)
            
        except Exception as e:
            self.fail(f"API documentation content generation failed: {e}")
    
    def test_performance_criteria_validation(self):
        """Test performance criteria validation."""
        try:
            criteria = {
                'signal_processing_time_ms': 100,
                'model_switching_time_ms': 1000,
                'dashboard_load_time_ms': 2000,
                'system_availability_percent': 99.0
            }
            
            result = self.uat_manager._validate_performance_criteria(criteria)
            
            self.assertIsInstance(result, dict)
            self.assertIn('all_passed', result)
            self.assertIn('signal_processing_time', result)
            self.assertIn('model_switching_time', result)
            
        except Exception as e:
            self.fail(f"Performance criteria validation failed: {e}")
    
    def test_usability_criteria_validation(self):
        """Test usability criteria validation."""
        try:
            criteria = {
                'max_clicks_to_feature': 3,
                'max_learning_time_minutes': 30,
                'error_message_clarity_score': 8
            }
            
            result = self.uat_manager._validate_usability_criteria(criteria)
            
            self.assertIsInstance(result, dict)
            self.assertIn('all_passed', result)
            self.assertIn('clicks_to_feature', result)
            self.assertIn('learning_time', result)
            
        except Exception as e:
            self.fail(f"Usability criteria validation failed: {e}")
    
    def test_error_handling_scenario(self):
        """Test error handling user scenario."""
        try:
            result = self.uat_manager._test_error_handling()
            
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('error_scenarios_tested', result)
            self.assertIn('recovery_success_rate', result)
            
        except Exception as e:
            self.fail(f"Error handling test failed: {e}")
    
    def test_complete_uat_suite(self):
        """Test complete UAT suite execution."""
        try:
            # Mock some methods to speed up testing
            with patch.object(self.uat_manager, '_setup_uat_environment'):
                with patch.object(self.uat_manager, '_cleanup_uat_environment'):
                    result = self.uat_manager.run_complete_uat_suite()
            
            self.assertIsInstance(result, dict)
            self.assertIn('overall_success', result)
            self.assertIn('user_scenarios', result)
            self.assertIn('acceptance_criteria', result)
            self.assertIn('documentation_status', result)
            self.assertIn('start_time', result)
            self.assertIn('end_time', result)
            
        except Exception as e:
            self.fail(f"Complete UAT suite failed: {e}")
    
    def test_uat_cleanup(self):
        """Test UAT environment cleanup."""
        try:
            # Create some temporary files
            temp_file = os.path.join(self.test_dir, 'temp_file.txt')
            with open(temp_file, 'w') as f:
                f.write('test content')
            
            # Test cleanup (should not remove our test directory since it's not in temp)
            self.uat_manager._cleanup_uat_environment()
            
            # File should still exist since we're not using a temp directory
            self.assertTrue(os.path.exists(temp_file))
            
        except Exception as e:
            self.fail(f"UAT cleanup failed: {e}")


class TestUATIntegration(unittest.TestCase):
    """Integration tests for UAT functionality."""
    
    def setUp(self):
        """Set up integration test environment."""
        if LearningSystemUATManager is None:
            self.skipTest("LearningSystemUATManager not available")
        
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'integration_config.json')
        
        # Create minimal configuration for integration testing
        config = {
            'uat_root': self.test_dir,
            'docs_dir': os.path.join(self.test_dir, 'integration_docs'),
            'user_scenarios': ['trader_onboarding'],
            'acceptance_criteria': {
                'performance': {'signal_processing_time_ms': 100},
                'usability': {'max_clicks_to_feature': 3},
                'functionality': {'feature_completeness_percent': 95}
            },
            'documentation_types': ['user_guide']
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
    
    def tearDown(self):
        """Clean up integration test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_end_to_end_uat_workflow(self):
        """Test complete end-to-end UAT workflow."""
        try:
            uat_manager = LearningSystemUATManager(self.config_path)
            
            # Run minimal UAT suite
            with patch.object(uat_manager, '_cleanup_uat_environment'):
                results = uat_manager.run_complete_uat_suite()
            
            # Verify results structure
            self.assertIn('overall_success', results)
            self.assertIn('user_scenarios', results)
            self.assertIn('acceptance_criteria', results)
            self.assertIn('documentation_status', results)
            
            # Verify scenario results
            self.assertIn('trader_onboarding', results['user_scenarios'])
            
            # Verify documentation was generated
            docs_status = results['documentation_status']
            self.assertIn('success', docs_status)
            
        except Exception as e:
            self.fail(f"End-to-end UAT workflow failed: {e}")


def run_uat_tests():
    """Run all UAT tests."""
    print("Running Learning System UAT Manager Tests...")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestLearningSystemUATManager))
    test_suite.addTest(unittest.makeSuite(TestUATIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall Result: {'PASS' if success else 'FAIL'}")
    
    return success


if __name__ == "__main__":
    success = run_uat_tests()
    exit(0 if success else 1)