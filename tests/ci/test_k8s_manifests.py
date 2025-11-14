"""
Kubernetes Manifest Validation Tests

Tests that K8s YAML files are valid and properly configured.
These tests run locally and in GitHub Actions CI pipeline.

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


class TestK8sManifests(unittest.TestCase):
    """Test Kubernetes manifest files"""
    
    def setUp(self):
        """Setup test environment"""
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.k8s_dir = os.path.join(self.repo_root, 'k8s')
        self.datasets_dir = os.path.join(self.repo_root, 'datasets')
    
    def load_yaml_file(self, filename):
        """Helper to load YAML file"""
        filepath = os.path.join(self.k8s_dir, filename)
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    
    def test_all_yaml_files_valid_syntax(self):
        """Test that all YAML files in k8s/ have valid syntax"""
        yaml_files = [f for f in os.listdir(self.k8s_dir) if f.endswith('.yaml')]
        self.assertGreater(len(yaml_files), 0, "No YAML files found in k8s/")
        
        for yaml_file in yaml_files:
            with self.subTest(file=yaml_file):
                filepath = os.path.join(self.k8s_dir, yaml_file)
                try:
                    with open(filepath, 'r') as f:
                        yaml.safe_load(f)
                except yaml.YAMLError as e:
                    self.fail(f"Invalid YAML syntax in {yaml_file}: {e}")
    
    def test_configmap_dataset_has_required_keys(self):
        """Test that ConfigMap has required dataset keys"""
        # Check if configmap-dataset.yaml exists (new naming) or use deployment files
        configmap_file = 'configmap-dataset.yaml'
        if not os.path.exists(os.path.join(self.k8s_dir, configmap_file)):
            self.skipTest("configmap-dataset.yaml not found, checking deployments instead")
        
        configmap = self.load_yaml_file(configmap_file)
        
        self.assertEqual(configmap['kind'], 'ConfigMap', "File should contain a ConfigMap")
        self.assertIn('data', configmap, "ConfigMap should have 'data' field")
        
        data = configmap['data']
        required_keys = ['dataset.url', 'dataset.version', 'dataset.name']
        
        for key in required_keys:
            with self.subTest(key=key):
                self.assertIn(key, data, f"ConfigMap missing required key: {key}")
    
    def test_configmap_dataset_url_valid_format(self):
        """Test that dataset.url in ConfigMap is a valid HTTP/HTTPS URL"""
        configmap_file = 'configmap-dataset.yaml'
        if not os.path.exists(os.path.join(self.k8s_dir, configmap_file)):
            self.skipTest("configmap-dataset.yaml not found")
        
        configmap = self.load_yaml_file(configmap_file)
        dataset_url = configmap['data']['dataset.url']
        
        url_pattern = re.compile(r'^https?://.+')
        self.assertTrue(
            url_pattern.match(dataset_url),
            f"dataset.url is not a valid HTTP/HTTPS URL: {dataset_url}"
        )
    
    def test_configmap_dataset_version_semver(self):
        """Test that dataset.version follows semver format"""
        configmap_file = 'configmap-dataset.yaml'
        if not os.path.exists(os.path.join(self.k8s_dir, configmap_file)):
            self.skipTest("configmap-dataset.yaml not found")
        
        configmap = self.load_yaml_file(configmap_file)
        dataset_version = configmap['data']['dataset.version']
        
        semver_pattern = re.compile(r'^\d+\.\d+\.\d+$')
        self.assertTrue(
            semver_pattern.match(dataset_version),
            f"dataset.version does not follow semver format (X.Y.Z): {dataset_version}"
        )
    
    def test_training_deployment_has_env_vars(self):
        """Test that training deployment has environment variables from ConfigMap"""
        deployment = self.load_yaml_file('deployment-training.yaml')
        
        self.assertEqual(deployment['kind'], 'Deployment', "File should contain a Deployment")
        
        containers = deployment['spec']['template']['spec']['containers']
        self.assertGreater(len(containers), 0, "Deployment should have at least one container")
        
        container = containers[0]
        self.assertIn('env', container, "Container should have 'env' field")
        
        env_vars = container['env']
        env_names = [env['name'] for env in env_vars]
        
        required_env_vars = ['DATASET_URL', 'DATASET_VERSION', 'DATASET_NAME']
        for env_name in required_env_vars:
            with self.subTest(env_var=env_name):
                self.assertIn(env_name, env_names, f"Missing environment variable: {env_name}")
    
    def test_training_deployment_env_vars_from_configmap(self):
        """Test that training deployment env vars reference ConfigMap"""
        deployment = self.load_yaml_file('deployment-training.yaml')
        
        containers = deployment['spec']['template']['spec']['containers']
        container = containers[0]
        env_vars = container['env']
        
        for env in env_vars:
            if env['name'] in ['DATASET_URL', 'DATASET_VERSION', 'DATASET_NAME']:
                with self.subTest(env_var=env['name']):
                    self.assertIn('valueFrom', env, f"{env['name']} should use valueFrom")
                    self.assertIn('configMapKeyRef', env['valueFrom'], 
                                f"{env['name']} should reference ConfigMap")
    
    def test_training_deployment_has_volume_mount(self):
        """Test that training deployment has volume mount for models"""
        deployment = self.load_yaml_file('deployment-training.yaml')
        
        containers = deployment['spec']['template']['spec']['containers']
        container = containers[0]
        
        self.assertIn('volumeMounts', container, "Container should have volumeMounts")
        
        volume_mounts = container['volumeMounts']
        mount_paths = [vm['mountPath'] for vm in volume_mounts]
        
        self.assertIn('/app/models', mount_paths, "Should have /app/models mount")
        
        # Check that volume mount uses subPath
        models_mount = next(vm for vm in volume_mounts if vm['mountPath'] == '/app/models')
        self.assertIn('subPath', models_mount, "Volume mount should use subPath")
    
    def test_deployment_name_includes_version(self):
        """Test that training deployment name includes dataset version"""
        deployment = self.load_yaml_file('deployment-training.yaml')
        
        deployment_name = deployment['metadata']['name']
        
        # Should include dataset version pattern: ds1-0-0 or similar
        # The full name can be: playlist-recommender-system-trainer-ds1-0-0
        version_pattern = re.compile(r'ds\d+-\d+-\d+')
        self.assertTrue(
            version_pattern.search(deployment_name),
            f"Deployment name should include dataset version (e.g., ds1-0-0): {deployment_name}"
        )


if __name__ == '__main__':
    unittest.main()
