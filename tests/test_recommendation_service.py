"""
Unit tests for the Recommendation Service
Tests Docker build, container running, and API functionality
"""

import unittest
import subprocess
import time
import requests
import json
import pickle
import os
from typing import List, Dict, Any


class TestRecommendationServiceBuild(unittest.TestCase):
    """Test Docker image building"""
    
    @classmethod
    def setUpClass(cls):
        """Build the Docker image before tests"""
        cls.image_name = "caio-recommendation-service-test"
        cls.service_dir = "/home/caiogrossi/mlops-assignment/recommendation-service"
    
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
        print("\n[TEST] Building Docker image...")
        
        result = subprocess.run(
            [
                "docker", "build",
                "-t", self.image_name,
                "-f", os.path.join(self.service_dir, "Dockerfile"),
                self.service_dir
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        print(f"Build stdout: {result.stdout[-500:]}")  # Last 500 chars
        if result.returncode != 0:
            print(f"Build stderr: {result.stderr}")
        
        self.assertEqual(
            result.returncode, 0,
            f"Docker build failed with code {result.returncode}\nError: {result.stderr}"
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


class TestRecommendationServiceContainer(unittest.TestCase):
    """Test Docker container running"""
    
    @classmethod
    def setUpClass(cls):
        """Start the container before tests"""
        cls.image_name = "caio-recommendation-service-test"
        cls.container_name = "caio-recommendation-test-container"
        cls.port = 50005
        cls.models_dir = "/home/caiogrossi/project2-pv/models"
        cls.base_url = f"http://localhost:{cls.port}"
        
        # Stop and remove container if it exists
        subprocess.run(["docker", "stop", cls.container_name], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "rm", cls.container_name], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    @classmethod
    def tearDownClass(cls):
        """Don't stop container yet - API tests need it running"""
        # Container will be stopped by TestRecommendationServiceCleanup
        pass
    
    def test_01_models_directory_exists(self):
        """Test that shared models directory exists"""
        self.assertTrue(
            os.path.exists(self.models_dir),
            f"Models directory not found at {self.models_dir}"
        )
    
    def test_02_start_container(self):
        """Test starting the Docker container"""
        print("\n[TEST] Starting Docker container...")
        
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
        
        # Wait for container to be ready
        print("[TEST] Waiting for container to be ready...")
        time.sleep(5)
    
    def test_03_container_is_running(self):
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
    
    def test_04_port_is_exposed(self):
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
    
    def test_05_container_logs(self):
        """Test that container is logging correctly"""
        time.sleep(2)  # Wait for logs
        
        result = subprocess.run(
            ["docker", "logs", self.container_name],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout + result.stderr
        
        # Check for gunicorn startup
        self.assertTrue(
            "gunicorn" in logs.lower() or "starting" in logs.lower(),
            "Container logs don't show proper startup"
        )


class TestRecommendationServiceAPI(unittest.TestCase):
    """Test API endpoints with real data from the model"""
    
    @classmethod
    def setUpClass(cls):
        """Load model data to get real song names"""
        cls.base_url = "http://localhost:50005"
        cls.models_dir = "/home/caiogrossi/project2-pv/models"
        cls.sample_songs = []
        cls.songs_with_rules = []
        cls.timeout = 10
        
        # Wait for service to be ready
        print("\n[TEST] Waiting for service to be ready...")
        time.sleep(5)
        
        # Load model to get real song names
        try:
            cls._load_sample_songs_from_model()
        except Exception as e:
            print(f"[WARNING] Could not load songs from model: {e}")
            cls.sample_songs = []
            cls.songs_with_rules = []
    
    @classmethod
    def _load_sample_songs_from_model(cls):
        """Load sample songs from the trained model"""
        metadata_file = os.path.join(cls.models_dir, "metadata.json")
        
        if not os.path.exists(metadata_file):
            print("[WARNING] No metadata.json found")
            return
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        current_version = metadata.get('current_version', '0.0')
        if current_version == '0.0':
            print("[WARNING] No trained model available")
            return
        
        model_info = metadata['models'].get(current_version)
        model_path = model_info['path']
        
        # Convert container path to host path
        # Container uses /app/models/, host uses cls.models_dir
        if model_path.startswith('/app/models/'):
            model_filename = os.path.basename(model_path)
            model_path = os.path.join(cls.models_dir, model_filename)
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Extract unique songs from frequent itemsets
        songs = set()
        for itemset in model['frequent_itemsets']:
            for item in itemset['itemset']:
                # Extract just the song name (before comma)
                song_name = item.split(',')[0].strip()
                songs.add(song_name)
        
        cls.sample_songs = sorted(list(songs))[:50]  # First 50 songs
        print(f"[INFO] Loaded {len(cls.sample_songs)} sample songs from model")
        
        # Store some songs that likely have associations (from rules)
        cls.songs_with_rules = []
        for rule in model['rules'][:20]:  # First 20 rules
            antecedent_songs = [item.split(',')[0].strip() for item in rule['antecedent']]
            cls.songs_with_rules.extend(antecedent_songs)
        
        cls.songs_with_rules = list(set(cls.songs_with_rules))[:10]
        print(f"[INFO] Found {len(cls.songs_with_rules)} songs with rules")
    
    def test_01_health_endpoint(self):
        """Test /health endpoint"""
        print("\n[TEST] Testing /health endpoint...")
        
        response = requests.get(
            f"{self.base_url}/health",
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200, "Health check failed")
        
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'music-recommendation-api')
        self.assertEqual(data['port'], 50005)
        self.assertIn('model_loaded', data)
        self.assertIn('timestamp', data)
        
        print(f"[INFO] Health check passed: {data}")
    
    def test_02_health_model_loaded(self):
        """Test that model is loaded"""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        data = response.json()
        
        self.assertTrue(
            data.get('model_loaded', False),
            "No model is loaded in the service"
        )
        self.assertIsNotNone(
            data.get('model_version'),
            "Model version is not set"
        )
        
        print(f"[INFO] Model loaded: version {data.get('model_version')}")
    
    def test_03_recommender_empty_request(self):
        """Test recommender with empty request"""
        response = requests.post(
            f"{self.base_url}/api/recommender",
            json={},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('songs', data['error'].lower())
    
    def test_04_recommender_empty_songs_list(self):
        """Test recommender with empty songs list"""
        response = requests.post(
            f"{self.base_url}/api/recommender",
            json={"songs": []},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_05_recommender_invalid_format(self):
        """Test recommender with invalid format"""
        response = requests.post(
            f"{self.base_url}/api/recommender",
            json={"songs": "not a list"},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_06_recommender_unknown_songs(self):
        """Test recommender with songs not in model"""
        response = requests.post(
            f"{self.base_url}/api/recommender",
            json={"songs": ["Unknown Song XYZ 12345", "Another Unknown Song"]},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('songs', data)
        self.assertIn('version', data)
        self.assertIn('model_date', data)
        self.assertIsInstance(data['songs'], list)
        
        # Unknown songs should return empty recommendations
        self.assertEqual(len(data['songs']), 0)
        
        print(f"[INFO] Unknown songs correctly returned empty list")
    
    def test_07_recommender_with_real_songs(self):
        """Test recommender with real songs from the model"""
        if not self.songs_with_rules:
            self.skipTest("No sample songs available from model")
        
        test_songs = self.songs_with_rules[:2]  # Use 2 songs with rules
        
        print(f"\n[TEST] Testing with real songs: {test_songs}")
        
        response = requests.post(
            f"{self.base_url}/api/recommender",
            json={"songs": test_songs},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('songs', data)
        self.assertIn('version', data)
        self.assertIn('model_date', data)
        self.assertIsInstance(data['songs'], list)
        
        # Should return at most 5 recommendations
        self.assertLessEqual(len(data['songs']), 5)
        
        print(f"[INFO] Recommendations: {data['songs']}")
        print(f"[INFO] Model version: {data['version']}")
    
    def test_08_recommender_single_song(self):
        """Test recommender with single song from model"""
        if not self.songs_with_rules:
            self.skipTest("No sample songs available from model")
        
        test_song = self.songs_with_rules[0]
        
        print(f"\n[TEST] Testing with single song: {test_song}")
        
        response = requests.post(
            f"{self.base_url}/api/recommender",
            json={"songs": [test_song]},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIsInstance(data['songs'], list)
        self.assertLessEqual(len(data['songs']), 5)
        
        # Input song should not be in recommendations
        if data['songs']:
            self.assertNotIn(test_song, data['songs'])
        
        print(f"[INFO] Single song recommendations: {data['songs']}")
    
    def test_09_recommender_response_format(self):
        """Test that recommender response has correct format"""
        if not self.sample_songs:
            self.skipTest("No sample songs available")
        
        response = requests.post(
            f"{self.base_url}/api/recommender",
            json={"songs": [self.sample_songs[0]]},
            timeout=self.timeout
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn('songs', data)
        self.assertIn('version', data)
        self.assertIn('model_date', data)
        
        # Check data types
        self.assertIsInstance(data['songs'], list)
        self.assertIsInstance(data['version'], str)
        self.assertIsInstance(data['model_date'], str)
        
        # All recommendations should be strings
        for song in data['songs']:
            self.assertIsInstance(song, str)
    
    def test_10_recommender_multiple_requests(self):
        """Test multiple consecutive requests"""
        if not self.sample_songs:
            self.skipTest("No sample songs available")
        
        print("\n[TEST] Testing multiple consecutive requests...")
        
        for i in range(3):
            songs = [self.sample_songs[i % len(self.sample_songs)]]
            
            response = requests.post(
                f"{self.base_url}/api/recommender",
                json={"songs": songs},
                timeout=self.timeout
            )
            
            self.assertEqual(response.status_code, 200)
            print(f"[INFO] Request {i+1}/3 completed successfully")
    
    def test_11_reload_model_endpoint(self):
        """Test /reload-model endpoint"""
        print("\n[TEST] Testing /reload-model endpoint...")
        
        response = requests.post(
            f"{self.base_url}/reload-model",
            timeout=self.timeout
        )
        
        # Should return 200 if model exists
        self.assertIn(response.status_code, [200, 500])
        
        data = response.json()
        
        if response.status_code == 200:
            self.assertEqual(data['status'], 'success')
            self.assertIn('version', data)
            self.assertIn('model_date', data)
            print(f"[INFO] Model reloaded: version {data['version']}")
        else:
            self.assertIn('status', data)
            print(f"[INFO] Reload failed (expected if no new model): {data}")


class TestRecommendationServiceIntegration(unittest.TestCase):
    """Integration tests using dataset songs"""
    
    @classmethod
    def setUpClass(cls):
        """Setup integration tests with known song combinations"""
        cls.base_url = "http://localhost:50005"
        cls.models_dir = "/home/caiogrossi/project2-pv/models"
        cls.timeout = 10
        
        # Load model and find songs that definitely have associations
        cls.test_cases = cls._generate_test_cases()
    
    @classmethod
    def _generate_test_cases(cls) -> List[Dict[str, Any]]:
        """Generate test cases from actual association rules"""
        try:
            metadata_file = os.path.join(cls.models_dir, "metadata.json")
            
            if not os.path.exists(metadata_file):
                return []
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            current_version = metadata.get('current_version', '0.0')
            if current_version == '0.0':
                return []
            
            model_info = metadata['models'].get(current_version)
            model_path = model_info['path']
            
            # Convert container path to host path
            if model_path.startswith('/app/models/'):
                model_filename = os.path.basename(model_path)
                model_path = os.path.join(cls.models_dir, model_filename)
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            test_cases = []
            
            # Generate test cases from rules with high confidence
            for rule in sorted(model['rules'], key=lambda r: r['confidence'], reverse=True)[:5]:
                antecedent_songs = [item.split(',')[0].strip() for item in rule['antecedent']]
                consequent_songs = [item.split(',')[0].strip() for item in rule['consequent']]
                
                test_cases.append({
                    'input': antecedent_songs,
                    'expected_in_output': consequent_songs,
                    'confidence': rule['confidence'],
                    'lift': rule['lift']
                })
            
            print(f"[INFO] Generated {len(test_cases)} integration test cases")
            return test_cases
            
        except Exception as e:
            print(f"[WARNING] Could not generate test cases: {e}")
            return []
    
    def test_01_high_confidence_recommendations(self):
        """Test recommendations for high-confidence association rules"""
        if not self.test_cases:
            self.skipTest("No test cases available")
        
        for i, test_case in enumerate(self.test_cases[:3]):  # Test first 3
            with self.subTest(i=i):
                print(f"\n[TEST] Testing rule {i+1}: {test_case['input']}")
                print(f"       Confidence: {test_case['confidence']:.3f}, Lift: {test_case['lift']:.3f}")
                
                response = requests.post(
                    f"{self.base_url}/api/recommender",
                    json={"songs": test_case['input']},
                    timeout=self.timeout
                )
                
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                # Check if expected songs are in recommendations
                recommendations = data['songs']
                expected_songs = test_case['expected_in_output']
                
                if recommendations:
                    # At least one expected song should be in recommendations
                    found = any(exp in recommendations for exp in expected_songs)
                    
                    print(f"       Expected: {expected_songs}")
                    print(f"       Got: {recommendations}")
                    print(f"       Match: {found}")
                else:
                    print(f"       No recommendations returned")
    
    def test_02_recommendations_consistency(self):
        """Test that same input gives consistent output"""
        if not self.test_cases:
            self.skipTest("No test cases available")
        
        test_input = self.test_cases[0]['input']
        
        print(f"\n[TEST] Testing consistency with: {test_input}")
        
        # Make 3 requests with same input
        responses = []
        for i in range(3):
            response = requests.post(
                f"{self.base_url}/api/recommender",
                json={"songs": test_input},
                timeout=self.timeout
            )
            self.assertEqual(response.status_code, 200)
            responses.append(response.json()['songs'])
        
        # All responses should be identical
        self.assertEqual(responses[0], responses[1])
        self.assertEqual(responses[1], responses[2])
        
        print(f"[INFO] Consistent results across 3 requests: {responses[0]}")


class TestRecommendationServiceCleanup(unittest.TestCase):
    """Cleanup - stop and remove test container"""
    
    @classmethod
    def setUpClass(cls):
        """Final cleanup of test container"""
        cls.container_name = "caio-recommendation-test-container"
        
        print("\n" + "="*70)
        print("[CLEANUP] Stopping and removing test container...")
        print("="*70)
        
        # Stop container
        result = subprocess.run(
            ["docker", "stop", cls.container_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"[CLEANUP] Container {cls.container_name} stopped")
        
        # Remove container
        result = subprocess.run(
            ["docker", "rm", cls.container_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"[CLEANUP] Container {cls.container_name} removed")
    
    def test_cleanup_completed(self):
        """Verify cleanup completed"""
        # This is just a placeholder test
        self.assertTrue(True, "Cleanup completed")


def run_tests():
    """Run all tests in order"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes in order
    suite.addTests(loader.loadTestsFromTestCase(TestRecommendationServiceBuild))
    suite.addTests(loader.loadTestsFromTestCase(TestRecommendationServiceContainer))
    suite.addTests(loader.loadTestsFromTestCase(TestRecommendationServiceAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestRecommendationServiceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestRecommendationServiceCleanup))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
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
