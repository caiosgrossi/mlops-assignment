"""
Unit tests for the Training Service
Tests Docker build, container running, and training functionality
"""

import unittest
import subprocess
import time
import requests
import json
import os


class TestTrainingServiceBuild(unittest.TestCase):
    """Test Docker image building for training service"""
    
    @classmethod
    def setUpClass(cls):
        """Setup before building"""
        cls.image_name = "caio-training-service-test"
        cls.service_dir = "/home/caiogrossi/mlops-assignment/training-service"
    
    def test_01_dockerfile_exists(self):
        """Test that Dockerfile exists"""
        dockerfile_path = os.path.join(self.service_dir, "Dockerfile")
        self.assertTrue(
            os.path.exists(dockerfile_path),
            f"Dockerfile not found at {dockerfile_path}"
        )
    
    def test_02_requirements_exists(self):
        """Test that requirements.txt exists"""
        requirements_path = os.path.join(self.service_dir, "requirements.txt")
        self.assertTrue(
            os.path.exists(requirements_path),
            f"requirements.txt not found at {requirements_path}"
        )
    
    def test_03_app_exists(self):
        """Test that app.py exists"""
        app_path = os.path.join(self.service_dir, "app.py")
        self.assertTrue(
            os.path.exists(app_path),
            f"app.py not found at {app_path}"
        )
    
    def test_04_docker_build(self):
        """Test building the Docker image"""
        print("\n[TEST] Building Training Service Docker image...")
        
        result = subprocess.run(
            [
                "docker", "build",
                "-t", self.image_name,
                "-f", os.path.join(self.service_dir, "Dockerfile"),
                self.service_dir
            ],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(f"Build stdout: {result.stdout[-500:]}")
        if result.returncode != 0:
            print(f"Build stderr: {result.stderr}")
        
        self.assertEqual(
            result.returncode, 0,
            f"Docker build failed: {result.stderr}"
        )
    
    def test_05_image_exists(self):
        """Test that the Docker image was created"""
        result = subprocess.run(
            ["docker", "images", "-q", self.image_name],
            capture_output=True,
            text=True
        )
        
        self.assertTrue(
            result.stdout.strip() != "",
            f"Docker image {self.image_name} was not created"
        )


class TestTrainingServiceContainer(unittest.TestCase):
    """Test Docker container for training service"""
    
    @classmethod
    def setUpClass(cls):
        """Start the container before tests"""
        cls.image_name = "caio-training-service-test"
        cls.container_name = "caio-training-test-container"
        cls.port = 50005
        cls.models_dir = "/home/caiogrossi/project2-pv/models"
        cls.base_url = f"http://localhost:{cls.port}"
        
        # Stop and remove container if exists
        subprocess.run(["docker", "stop", cls.container_name],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "rm", cls.container_name],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    @classmethod
    def tearDownClass(cls):
        """Stop and remove container after tests"""
        print("\n[CLEANUP] Stopping training test container...")
        subprocess.run(["docker", "stop", cls.container_name],
                      capture_output=True)
        subprocess.run(["docker", "rm", cls.container_name],
                      capture_output=True)
    
    def test_01_start_container(self):
        """Test starting the training service container"""
        print("\n[TEST] Starting Training Service container...")
        
        result = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", self.container_name,
                "-p", f"{self.port}:{self.port}",
                "-v", f"{self.models_dir}:/app/models",
                self.image_name
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Container start stderr: {result.stderr}")
        
        self.assertEqual(
            result.returncode, 0,
            f"Failed to start container: {result.stderr}"
        )
        
        print("[TEST] Waiting for container to be ready...")
        time.sleep(5)
    
    def test_02_container_is_running(self):
        """Test that container is running"""
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={self.container_name}"],
            capture_output=True,
            text=True
        )
        
        self.assertTrue(
            result.stdout.strip() != "",
            f"Container {self.container_name} is not running"
        )
    
    def test_03_port_is_exposed(self):
        """Test that port 50005 is exposed"""
        result = subprocess.run(
            ["docker", "port", self.container_name],
            capture_output=True,
            text=True
        )
        
        self.assertIn(
            f"{self.port}/tcp",
            result.stdout,
            f"Port {self.port} is not exposed"
        )
    
    def test_04_health_endpoint(self):
        """Test /health endpoint"""
        print("\n[TEST] Testing training service /health endpoint...")
        
        response = requests.get(
            f"{self.base_url}/health",
            timeout=10
        )
        
        self.assertEqual(response.status_code, 200, "Health check failed")
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['port'], 50005)
        
        print(f"[INFO] Training service health: {data}")


def run_tests():
    """Run all training service tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestTrainingServiceBuild))
    suite.addTests(loader.loadTestsFromTestCase(TestTrainingServiceContainer))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("TRAINING SERVICE TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
