# Test Suite for Music Recommendation System

Comprehensive unit and integration tests for both training and recommendation services.

## Overview

This test suite validates:
- ✅ Docker image building
- ✅ Container deployment and running
- ✅ Port exposure and accessibility
- ✅ API endpoint functionality
- ✅ Recommendations using real songs from the dataset
- ✅ Error handling and edge cases
- ✅ Integration with trained models

## Test Structure

```
tests/
├── test_recommendation_service.py  # Recommendation service tests
├── test_training_service.py        # Training service tests
├── requirements.txt                # Test dependencies
├── README.md                       # This file
└── run_all_tests.sh               # Script to run all tests
```

## Prerequisites

1. **Model must be trained first:**
   ```bash
   # Make sure you have a trained model
   ls -l /home/caiogrossi/project2-pv/models/
   
   # Should contain:
   # - metadata.json
   # - association_rules_v*.pkl
   ```

2. **Python 3 with venv support:**
   ```bash
   # Test scripts automatically create and manage virtual environments
   # No manual dependency installation needed!
   ```

3. **Stop any running containers** on ports 5005 and 50005:
   ```bash
   docker stop training-container recommendation-container 2>/dev/null || true
   docker rm training-container recommendation-container 2>/dev/null || true
   ```

## Running Tests

### Run All Tests (Recommended)

The test scripts **automatically create a virtual environment**, install dependencies, run tests, and **clean up** afterwards. No manual setup required!

```bash
# From project root
cd /home/caiogrossi/mlops-assignment

# Run all tests (creates and cleans up venv automatically)
bash tests/run_all_tests.sh

# Or quick test (recommendation service only)
bash tests/quick_test.sh
```

**What happens:**
1. 🔨 Creates isolated virtual environment (`.test_venv` or `.quick_test_venv`)
2. 📦 Installs test dependencies inside venv
3. ✅ Runs all tests
4. 🧹 Automatically removes venv when done

**Benefits:**
- ✅ No pollution of system Python packages
- ✅ Consistent test environment every time
- ✅ Automatic cleanup on success or failure
- ✅ Zero manual configuration needed

### Run Tests Manually

If you prefer to manage dependencies yourself:

```bash
# Install dependencies
pip install -r tests/requirements.txt

# Run recommendation service tests
python3 tests/test_recommendation_service.py

# Run training service tests
python3 tests/test_training_service.py
```

### Run Specific Test Classes

```bash
# Test only Docker building
python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceBuild

# Test only container running
python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceContainer

# Test only API endpoints
python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceAPI

# Test only integration with real songs
python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceIntegration
```

### Run Individual Tests

```bash
# Test Docker build only
python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceBuild.test_04_docker_build

# Test health endpoint only
python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceAPI.test_01_health_endpoint

# Test recommendations with real songs
python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceAPI.test_07_recommender_with_real_songs
```

## Test Details

### TestRecommendationServiceBuild

Tests the Docker image building process:
- ✅ Dockerfile exists
- ✅ requirements.txt exists
- ✅ app.py exists
- ✅ Docker image builds successfully
- ✅ Image is created in Docker

**Expected Duration:** ~30-60 seconds

### TestRecommendationServiceContainer

Tests container deployment and running:
- ✅ Shared models directory exists
- ✅ Container starts successfully
- ✅ Container is running
- ✅ Port 50005 is exposed
- ✅ Container logs show proper startup

**Expected Duration:** ~10-15 seconds

### TestRecommendationServiceAPI

Tests all API endpoints with real data:
- ✅ Health endpoint responds correctly
- ✅ Model is loaded
- ✅ Error handling (empty request, invalid format)
- ✅ Unknown songs return empty list
- ✅ **Real songs from dataset return recommendations**
- ✅ Single song recommendations work
- ✅ Response format is correct
- ✅ Multiple consecutive requests work
- ✅ Model reload endpoint works

**Expected Duration:** ~20-30 seconds

### TestRecommendationServiceIntegration

Integration tests using actual association rules:
- ✅ **High-confidence rules produce expected recommendations**
- ✅ Same input produces consistent output
- ✅ Antecedents from rules return consequents

**Expected Duration:** ~10-15 seconds

### TestTrainingServiceBuild

Tests training service Docker build:
- ✅ Dockerfile exists
- ✅ requirements.txt exists
- ✅ app.py exists
- ✅ Docker image builds successfully

**Expected Duration:** ~30-60 seconds

### TestTrainingServiceContainer

Tests training service container:
- ✅ Container starts successfully
- ✅ Container is running
- ✅ Port 5005 is exposed
- ✅ Health endpoint works

**Expected Duration:** ~10-15 seconds

## Understanding Test Results

### Success Output

```
test_01_health_endpoint (tests.test_recommendation_service.TestRecommendationServiceAPI)
Test /health endpoint ... ok
[INFO] Health check passed: {'status': 'healthy', 'model_loaded': True, ...}

test_07_recommender_with_real_songs (tests.test_recommendation_service.TestRecommendationServiceAPI)
Test recommender with real songs from the model ... ok
[TEST] Testing with real songs: ['0 To 100 / The Catch Up', 'Jumpman']
[INFO] Recommendations: ['Energy', 'Legend', 'Know Yourself']
```

### What Tests Verify

1. **Docker Build Test**: Ensures the image can be built from Dockerfile
2. **Container Run Test**: Verifies container starts and runs on correct port
3. **Health Check**: Confirms service is responding and model is loaded
4. **Empty/Invalid Input**: Tests error handling
5. **Unknown Songs**: Verifies graceful handling (empty list, not error)
6. **Real Songs**: **Uses actual songs from the model to verify recommendations work**
7. **Integration Tests**: **Tests using association rules to verify expected recommendations**

## Key Features

### Automatic Song Discovery

The tests automatically:
1. Load the trained model from `/home/caiogrossi/project2-pv/models/`
2. Extract real song names from frequent itemsets
3. Identify songs that have association rules
4. Use these songs for testing recommendations

This ensures tests use **actual data from your dataset**, not hardcoded values.

### Integration Testing

The integration tests:
1. Extract high-confidence association rules
2. Use rule antecedents as input
3. Verify that consequents appear in recommendations
4. Test consistency across multiple requests

## Example Test Output

```
======================================================================
TEST SUMMARY
======================================================================
Tests run: 28
Successes: 28
Failures: 0
Errors: 0
======================================================================
```

## Troubleshooting

### No Sample Songs Available

**Problem:** Tests skip because no model is loaded

**Solution:**
```bash
# Train a model first
curl -X POST http://localhost:5005/train \
  -H "Content-Type: application/json" \
  -d '{"dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"}'

# Wait for training to complete (~5-10 minutes)

# Then run tests
python3 tests/test_recommendation_service.py
```

### Port Already in Use

**Problem:** Container fails to start because port is in use

**Solution:**
```bash
# Stop existing containers
docker stop training-container recommendation-container caio-recommendation-container
docker rm training-container recommendation-container caio-recommendation-container

# Or kill process using the port
sudo lsof -i :50005
sudo kill -9 <PID>
```

### Docker Build Fails

**Problem:** Docker image fails to build

**Solution:**
```bash
# Check Docker is running
docker ps

# Check disk space
df -h

# Try building manually to see full error
cd recommendation-service
docker build -t test-build .
```

### Tests Fail Due to Timeout

**Problem:** API requests timeout

**Solution:**
```bash
# Check if container is running
docker ps | grep recommendation

# Check container logs
docker logs <container-id>

# Increase timeout in test file (default is 10 seconds)
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Install dependencies
      run: pip install -r tests/requirements.txt
    - name: Run tests
      run: |
        python3 tests/test_recommendation_service.py
        python3 tests/test_training_service.py
```

## Adding New Tests

To add new tests:

1. Add test method to appropriate test class
2. Follow naming convention: `test_XX_description`
3. Use descriptive assertions
4. Add print statements for debugging
5. Clean up resources in tearDown methods

Example:
```python
def test_12_new_feature(self):
    """Test new feature description"""
    print("\n[TEST] Testing new feature...")
    
    # Your test code here
    response = requests.get(f"{self.base_url}/new-endpoint")
    
    self.assertEqual(response.status_code, 200)
    print(f"[INFO] New feature test passed")
```

## Test Coverage

Current test coverage:
- ✅ Docker building
- ✅ Container deployment
- ✅ Port exposure
- ✅ Health checks
- ✅ API functionality
- ✅ Error handling
- ✅ Real dataset integration
- ✅ Association rules validation
- ✅ Response consistency

## Performance Benchmarks

Typical test execution times:
- Build tests: ~1 minute
- Container tests: ~15 seconds
- API tests: ~30 seconds
- Integration tests: ~15 seconds
- **Total:** ~2 minutes

## Notes

- Tests create temporary Docker images with `-test` suffix
- Temporary containers are cleaned up automatically
- Tests can run multiple times without conflicts
- Each test class has independent setup/teardown
- Tests use real model data for realistic validation
