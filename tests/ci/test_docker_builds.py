"""
CI Build Validation Tests

Tests that Docker images build successfully for both services.
These tests run in GitHub Actions CI pipeline.

 PVC PROTECTION WARNING 
This test file must NEVER:
- Mount /home/caiogrossi/project2-pv/
- Call POST /train endpoint
- Write any files to production storage
"""

import unittest
import subprocess
import os


class TestDockerBuilds(unittest.TestCase):
    """Test that Docker images build successfully"""
    
    def setUp(self):
        """Setup test environment"""
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.training_service_dir = os.path.join(self.repo_root, 'training-service')
        self.recommendation_service_dir = os.path.join(self.repo_root, 'recommendation-service')
    
    def test_training_service_dockerfile_exists(self):
        """Test that training-service Dockerfile exists"""
        dockerfile_path = os.path.join(self.training_service_dir, 'Dockerfile')
        self.assertTrue(
            os.path.exists(dockerfile_path),
            f"Dockerfile not found at {dockerfile_path}"
        )
    
    def test_recommendation_service_dockerfile_exists(self):
        """Test that recommendation-service Dockerfile exists"""
        dockerfile_path = os.path.join(self.recommendation_service_dir, 'Dockerfile')
        self.assertTrue(
            os.path.exists(dockerfile_path),
            f"Dockerfile not found at {dockerfile_path}"
        )
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true',
        "Docker build test only runs in CI environment"
    )
    def test_training_service_builds(self):
        """Test that training-service Docker image builds successfully"""
        try:
            result = subprocess.run(
                [
                    'docker', 'build',
                    '-t', 'training-service-test:latest',
                    '-f', os.path.join(self.training_service_dir, 'Dockerfile'),
                    self.training_service_dir
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            self.assertEqual(
                result.returncode, 0,
                f"Docker build failed: {result.stderr}"
            )
        except subprocess.TimeoutExpired:
            self.fail("Docker build timed out after 5 minutes")
    
    @unittest.skipUnless(
        os.environ.get('CI') == 'true',
        "Docker build test only runs in CI environment"
    )
    def test_recommendation_service_builds(self):
        """Test that recommendation-service Docker image builds successfully"""
        try:
            result = subprocess.run(
                [
                    'docker', 'build',
                    '-t', 'recommendation-service-test:latest',
                    '-f', os.path.join(self.recommendation_service_dir, 'Dockerfile'),
                    self.recommendation_service_dir
                ],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            self.assertEqual(
                result.returncode, 0,
                f"Docker build failed: {result.stderr}"
            )
        except subprocess.TimeoutExpired:
            self.fail("Docker build timed out after 5 minutes")


if __name__ == '__main__':
    unittest.main()
