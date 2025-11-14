"""
Post-Deployment Validation Tests

Tests that run AFTER ArgoCD syncs to verify deployment health.
These tests run in GitHub Actions after deployment.

 PVC PROTECTION WARNING 
This test file must NEVER:
- Mount /home/caiogrossi/project2-pv/
- Call POST /train endpoint (would write models to PVC)
- Call POST /recommend endpoint (if it writes any state)
- Use kubectl exec (could modify files)

ONLY read-only operations:
- kubectl get/describe (read pod status)
- GET /health (health check)
- GET /dataset/info (read environment variables)
"""

import unittest
import subprocess
import os
import requests
import json
import time


class TestPostDeployment(unittest.TestCase):
    """Test deployment health after ArgoCD sync"""
    
    def setUp(self):
        """Setup test environment"""
        self.namespace = os.environ.get('K8S_NAMESPACE', 'caiogrossi')
        self.training_service_url = os.environ.get('TRAINING_SERVICE_URL', 'http://localhost:50005')
        self.recommendation_service_url = os.environ.get('RECOMMENDATION_SERVICE_URL', 'http://localhost:50006')
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true',
        "Deployment test only runs in CI environment with kubectl access"
    )
    def test_training_pod_running(self):
        """Test that training service pod is in Running state"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'pods', '-n', self.namespace, 
                 '-l', 'app=training-service', '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(result.returncode, 0, f"kubectl get pods failed: {result.stderr}")
            
            pods = json.loads(result.stdout)
            self.assertGreater(len(pods['items']), 0, "No training service pods found")
            
            pod = pods['items'][0]
            phase = pod['status']['phase']
            self.assertEqual(phase, 'Running', f"Training pod not running: {phase}")
            
        except subprocess.TimeoutExpired:
            self.fail("kubectl command timed out")
        except json.JSONDecodeError as e:
            self.fail(f"Failed to parse kubectl output: {e}")
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true',
        "Deployment test only runs in CI environment with kubectl access"
    )
    def test_recommendation_pod_running(self):
        """Test that recommendation service pod is in Running state"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'pods', '-n', self.namespace,
                 '-l', 'app=recommendation-service', '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(result.returncode, 0, f"kubectl get pods failed: {result.stderr}")
            
            pods = json.loads(result.stdout)
            self.assertGreater(len(pods['items']), 0, "No recommendation service pods found")
            
            pod = pods['items'][0]
            phase = pod['status']['phase']
            self.assertEqual(phase, 'Running', f"Recommendation pod not running: {phase}")
            
        except subprocess.TimeoutExpired:
            self.fail("kubectl command timed out")
        except json.JSONDecodeError as e:
            self.fail(f"Failed to parse kubectl output: {e}")
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true',
        "Deployment test only runs in CI environment"
    )
    def test_training_service_health_endpoint(self):
        """
        Test that training service /health endpoint responds with 200
        
         GET REQUEST ONLY - NO POST /train CALLS
        """
        max_retries = 5
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{self.training_service_url}/health",
                    timeout=5
                )
                
                if response.status_code == 200:
                    return  # Success
                    
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
        
        self.fail(f"Training service /health endpoint not responding after {max_retries} attempts")
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true',
        "Deployment test only runs in CI environment"
    )
    def test_recommendation_service_health_endpoint(self):
        """
        Test that recommendation service /health endpoint responds with 200
        
         GET REQUEST ONLY - NO POST /recommend CALLS
        """
        max_retries = 5
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    f"{self.recommendation_service_url}/health",
                    timeout=5
                )
                
                if response.status_code == 200:
                    return  # Success
                    
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
        
        self.fail(f"Recommendation service /health endpoint not responding after {max_retries} attempts")
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true',
        "Deployment test only runs in CI environment"
    )
    def test_training_service_dataset_info_endpoint(self):
        """
        Test that training service /dataset/info returns environment variables
        
         GET REQUEST ONLY - Validates that env vars are injected correctly
        """
        try:
            response = requests.get(
                f"{self.training_service_url}/dataset/info",
                timeout=5
            )
            
            self.assertEqual(
                response.status_code, 200,
                f"/dataset/info endpoint failed: {response.status_code}"
            )
            
            data = response.json()
            
            # Verify that environment variables are present
            self.assertIn('dataset_url', data, "Missing dataset_url in response")
            self.assertIn('dataset_version', data, "Missing dataset_version in response")
            
            # Verify URL format
            self.assertTrue(
                data['dataset_url'].startswith('http'),
                f"Invalid dataset_url format: {data['dataset_url']}"
            )
            
        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to reach /dataset/info endpoint: {e}")
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true',
        "Deployment test only runs in CI environment with kubectl access"
    )
    def test_training_pod_env_vars_from_configmap(self):
        """Test that training pod has environment variables from ConfigMap"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'pods', '-n', self.namespace,
                 '-l', 'app=training-service', '-o', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(result.returncode, 0, f"kubectl get pods failed: {result.stderr}")
            
            pods = json.loads(result.stdout)
            self.assertGreater(len(pods['items']), 0, "No training service pods found")
            
            pod = pods['items'][0]
            containers = pod['spec']['containers']
            self.assertGreater(len(containers), 0, "No containers in pod")
            
            container = containers[0]
            env_vars = container.get('env', [])
            env_names = [env['name'] for env in env_vars]
            
            required_env_vars = ['DATASET_URL', 'DATASET_VERSION', 'DATASET_NAME']
            for env_name in required_env_vars:
                with self.subTest(env_var=env_name):
                    self.assertIn(env_name, env_names, f"Missing environment variable: {env_name}")
            
        except subprocess.TimeoutExpired:
            self.fail("kubectl command timed out")
        except json.JSONDecodeError as e:
            self.fail(f"Failed to parse kubectl output: {e}")


if __name__ == '__main__':
    unittest.main()
