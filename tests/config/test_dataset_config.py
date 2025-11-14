"""
Dataset Configuration Validation Tests

Tests that dataset configuration files are valid and consistent.
These tests run locally and in GitHub Actions when datasets/ changes.

 PVC PROTECTION WARNING 
This test file must NEVER:
- Mount /home/caiogrossi/project2-pv/
- Call POST /train endpoint
- Write any files to production storage
"""

import unittest
import os
import yaml
import re
import requests


class TestDatasetConfiguration(unittest.TestCase):
    """Test dataset configuration files"""
    
    def setUp(self):
        """Setup test environment"""
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.datasets_dir = os.path.join(self.repo_root, 'datasets')
        self.k8s_dir = os.path.join(self.repo_root, 'k8s')
        
        self.dataset_config_path = os.path.join(self.datasets_dir, 'dataset-config.yaml')
        self.configmap_path = os.path.join(self.k8s_dir, 'configmap-dataset.yaml')
    
    def load_yaml_file(self, filepath):
        """Helper to load YAML file"""
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    def test_dataset_config_file_exists(self):
        """Test that dataset-config.yaml exists"""
        self.assertTrue(
            os.path.exists(self.dataset_config_path),
            f"dataset-config.yaml not found at {self.dataset_config_path}"
        )
    
    def test_dataset_config_has_required_fields(self):
        """Test that dataset-config.yaml has required fields"""
        config = self.load_yaml_file(self.dataset_config_path)
        
        # Check that 'dataset' key exists
        self.assertIn('dataset', config, "Missing 'dataset' key in config file")
        
        dataset = config['dataset']
        required_fields = ['url', 'version', 'name']
        for field in required_fields:
            with self.subTest(field=field):
                self.assertIn(field, dataset, f"Missing required field in dataset: {field}")
    
    def test_dataset_url_format(self):
        """Test that dataset URL is valid HTTP/HTTPS format"""
        config = self.load_yaml_file(self.dataset_config_path)
        
        dataset = config.get('dataset', {})
        url = dataset.get('url', '')
        url_pattern = re.compile(r'^https?://.+')
        
        self.assertTrue(
            url_pattern.match(url),
            f"Dataset URL is not a valid HTTP/HTTPS URL: {url}"
        )
    
    def test_dataset_version_semver(self):
        """Test that dataset version follows semver format (X.Y.Z)"""
        config = self.load_yaml_file(self.dataset_config_path)
        
        dataset = config.get('dataset', {})
        version = dataset.get('version', '')
        semver_pattern = re.compile(r'^\d+\.\d+\.\d+$')
        
        self.assertTrue(
            semver_pattern.match(version),
            f"Dataset version does not follow semver format (X.Y.Z): {version}"
        )
    
    def test_configmap_exists(self):
        """Test that ConfigMap file exists"""
        self.assertTrue(
            os.path.exists(self.configmap_path),
            f"configmap-dataset.yaml not found at {self.configmap_path}"
        )
    
    def test_dataset_config_matches_configmap(self):
        """Test that dataset-config.yaml matches ConfigMap data"""
        dataset_config = self.load_yaml_file(self.dataset_config_path)
        configmap = self.load_yaml_file(self.configmap_path)
        
        dataset = dataset_config.get('dataset', {})
        configmap_data = configmap.get('data', {})
        
        # Check URL consistency
        self.assertEqual(
            dataset.get('url'),
            configmap_data.get('dataset.url'),
            "dataset.url mismatch between dataset-config.yaml and ConfigMap"
        )
        
        # Check version consistency
        self.assertEqual(
            dataset.get('version'),
            configmap_data.get('dataset.version'),
            "dataset.version mismatch between dataset-config.yaml and ConfigMap"
        )
        
        # Check name consistency
        self.assertEqual(
            dataset.get('name'),
            configmap_data.get('dataset.name'),
            "dataset.name mismatch between dataset-config.yaml and ConfigMap"
        )
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true' or os.environ.get('CHECK_URL_ACCESSIBILITY') == 'true',
        "URL accessibility check only runs in CI or when explicitly enabled"
    )
    def test_dataset_url_accessible(self):
        """
        Test that dataset URL is accessible (returns HTTP 200)
        
        Note: This test makes an HTTP request to verify the dataset is reachable.
        Skipped by default in local development.
        """
        config = self.load_yaml_file(self.dataset_config_path)
        dataset = config.get('dataset', {})
        url = dataset.get('url', '')
        
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            self.assertIn(
                response.status_code, [200, 302, 303],
                f"Dataset URL not accessible: {url} (status: {response.status_code})"
            )
            
        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to reach dataset URL {url}: {e}")
    
    def test_deployment_name_matches_version(self):
        """Test that training deployment name includes dataset version"""
        dataset_config = self.load_yaml_file(self.dataset_config_path)
        deployment_path = os.path.join(self.k8s_dir, 'deployment-training.yaml')
        
        if not os.path.exists(deployment_path):
            self.skipTest("deployment-training.yaml not found")
        
        deployment = self.load_yaml_file(deployment_path)
        deployment_name = deployment['metadata']['name']
        
        dataset = dataset_config.get('dataset', {})
        dataset_name = dataset.get('name', '')
        dataset_version = dataset.get('version', '').replace('.', '-')
        
        # The deployment uses a short name like "ds1" not the full name "music-playlists"
        # So we just check that it contains the version pattern
        version_pattern = dataset_version  # e.g., "1-0-0"
        
        self.assertIn(
            version_pattern, deployment_name,
            f"Deployment name should include version '{version_pattern}', got '{deployment_name}'"
        )


if __name__ == '__main__':
    unittest.main()
