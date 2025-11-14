# CI/CD Testing Suite# Test Suite for Music Recommendation System



This directory contains automated tests for the MLOps Assignment CI/CD pipeline.Comprehensive unit and integration tests for both training and recommendation services.



## Test Philosophy## Overview



These tests focus on **CI/CD pipeline reliability** rather than deep functionality testing, since the system is already working. Tests validate:This test suite validates:

- Docker images build correctly-  Docker image building

- K8s manifests are valid-  Container deployment and running

- ArgoCD can deploy successfully-  Port exposure and accessibility

- Services are reachable after deployment-  API endpoint functionality

- Configuration changes propagate correctly-  Recommendations using real songs from the dataset

-  Error handling and edge cases

## Test Structure-  Integration with trained models



```## Test Structure

tests/

├── ci/                          # CI Pipeline Tests```

│   ├── test_docker_builds.py    # Docker build validation (2 Dockerfiles, 2 build tests)tests/

│   └── test_k8s_manifests.py    # K8s YAML validation (9 tests) test_recommendation_service.py  # Recommendation service tests

│ test_training_service.py        # Training service tests

├── config/                      # Configuration Tests requirements.txt                # Test dependencies

│   └── test_dataset_config.py   # Dataset config validation (8 tests) README.md                       # This file

│ run_all_tests.sh               # Script to run all tests

├── deploy/                      # Deployment Tests```

│   └── test_post_deploy.py      # Post-deployment health checks (6 tests)

│## Prerequisites

└── run_tests.py                 # Test runner

```1. **Model must be trained first:**

   ```bash

## Test Categories   # Make sure you have a trained model

   ls -l /home/caiogrossi/project2-pv/models/

### 1. CI Tests (`ci/`)   

Run during GitHub Actions CI pipeline:   # Should contain:

- **Docker Builds** (4 tests): Verify both services' Dockerfiles exist and build successfully   # - metadata.json

- **K8s Manifests** (9 tests): Validate YAML syntax, ConfigMap keys, deployment structure   # - association_rules_v*.pkl

   ```

### 2. Config Tests (`config/`)

Run locally and in CI:2. **Python 3 with venv support:**

- **Dataset Configuration** (8 tests): Validate dataset-config.yaml consistency, URL format, semver   ```bash

   # Test scripts automatically create and manage virtual environments

### 3. Deploy Tests (`deploy/`)   # No manual dependency installation needed!

Run after ArgoCD deployment:   ```

- **Post-Deployment** (6 tests): Verify pods running, health endpoints responding, env vars injected

3. **Stop any running containers** on ports 5005 and 50005:

**Total: 26 tests (17 local, 9 CI-only)**   ```bash

   docker stop training-container recommendation-container 2>/dev/null || true

## Running Tests   docker rm training-container recommendation-container 2>/dev/null || true

   ```

### Run All Tests (Including CI-Skipped)

```bash## Running Tests

cd tests

source test_venv/bin/activate### Run All Tests (Recommended)

python3 run_tests.py

```The test scripts **automatically create a virtual environment**, install dependencies, run tests, and **clean up** afterwards. No manual setup required!



### Run Local Tests Only```bash

```bash# From project root

python3 run_tests.py --localcd /home/caiogrossi/mlops-assignment

```

# Run all tests (creates and cleans up venv automatically)

### Run CI Tests Onlybash tests/run_all_tests.sh

```bash

python3 run_tests.py --ci-only# Or quick test (recommendation service only)

```bash tests/quick_test.sh

```

### Verbose Output

```bash**What happens:**

python3 run_tests.py -v1.  Creates isolated virtual environment (`.test_venv` or `.quick_test_venv`)

```2.  Installs test dependencies inside venv

3.  Runs all tests

## Test Results4.  Automatically removes venv when done



**Current Status:****Benefits:**

-  17 tests pass locally-  No pollution of system Python packages

-  9 tests skip (require CI environment with Docker/kubectl)-  Consistent test environment every time

-  0 failures-  Automatic cleanup on success or failure

-  Zero manual configuration needed

**Local Tests:**

- Config validation: 8/8 passing### Run Tests Manually

- Dockerfile existence: 2/2 passing

- K8s manifest validation: 7/7 passing (local subset)If you prefer to manage dependencies yourself:



**CI-Only Tests (Skipped Locally):**```bash

- Docker builds: 2 tests (require Docker daemon)# Install dependencies

- Pod health checks: 2 tests (require kubectl access)pip install -r tests/requirements.txt

- Service endpoints: 3 tests (require deployed services)

- Env var validation: 2 tests (require deployed pods)# Run recommendation service tests

python3 tests/test_recommendation_service.py

##  PVC Protection

# Run training service tests

**CRITICAL: All tests are READ-ONLY operations**python3 tests/test_training_service.py

```

These tests will **NEVER**:

- Mount `/home/caiogrossi/project2-pv/` (production PVC)### Run Specific Test Classes

- Call `POST /train` endpoint (would write models)

- Call `POST /recommend` with actual training```bash

- Use `kubectl exec` (could modify files)# Test only Docker building

python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceBuild

All tests use **ONLY**:

- `kubectl get/describe` (read pod status)# Test only container running

- `GET /health` (health checks)python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceContainer

- `GET /dataset/info` (read env vars)

- YAML file validation (local files)# Test only API endpoints

python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceAPI

## CI/CD Integration

# Test only integration with real songs

These tests are designed for GitHub Actions workflows:python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceIntegration

```

1. **`ci-build-and-validate.yml`** (on push to main)

   - Runs `ci/` tests (Docker builds, manifest validation)### Run Individual Tests

   - Runs `config/` tests (dataset config validation)

```bash

2. **`deploy-verify.yml`** (after deployment)# Test Docker build only

   - Runs `deploy/` tests (pod health, service endpoints)python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceBuild.test_04_docker_build



3. **`dataset-update.yml`** (on dataset changes)# Test health endpoint only

   - Runs `config/` tests (URL accessibility, consistency checks)python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceAPI.test_01_health_endpoint



## Virtual Environment# Test recommendations with real songs

python3 -m unittest tests.test_recommendation_service.TestRecommendationServiceAPI.test_07_recommender_with_real_songs

Tests use an isolated virtual environment:```



```bash## Test Details

# Create (if needed)

python3 -m venv test_venv### TestRecommendationServiceBuild



# ActivateTests the Docker image building process:

source test_venv/bin/activate-  Dockerfile exists

-  requirements.txt exists

# Install dependencies-  app.py exists

pip install -r requirements.txt-  Docker image builds successfully

```-  Image is created in Docker



## Dependencies**Expected Duration:** ~30-60 seconds



- `requests==2.31.0` - HTTP client for endpoint testing### TestRecommendationServiceContainer

- `pyyaml==6.0.1` - YAML parsing and validation

- `flask==3.0.0` - For testing Flask appsTests container deployment and running:

- `pandas==2.1.3` - For dataset validation-  Shared models directory exists

-  Container starts successfully

## Test Coverage-  Container is running

-  Port 50005 is exposed

### What We Test-  Container logs show proper startup

 Build process (Docker images compile)  

 Deployment process (K8s manifests valid)  **Expected Duration:** ~10-15 seconds

 Configuration management (ConfigMap changes)  

 Service health (pods start, services respond)### TestRecommendationServiceAPI



### What We DON'T TestTests all API endpoints with real data:

 Algorithm correctness (system already works)  -  Health endpoint responds correctly

 Business logic (not CI/CD focus)  -  Model is loaded

 Performance (out of scope)  -  Error handling (empty request, invalid format)

 Deep functionality (validated separately)-  Unknown songs return empty list

-  **Real songs from dataset return recommendations**

## Next Steps-  Single song recommendations work

-  Response format is correct

See `CI_CD_TESTING_PLAN.md` for:-  Multiple consecutive requests work

- GitHub Actions workflow implementation-  Model reload endpoint works

- Pre-commit hooks setup

- Deployment pipeline details**Expected Duration:** ~20-30 seconds

- Testing strategy and phases

### TestRecommendationServiceIntegration

Integration tests using actual association rules:
-  **High-confidence rules produce expected recommendations**
-  Same input produces consistent output
-  Antecedents from rules return consequents

**Expected Duration:** ~10-15 seconds

### TestTrainingServiceBuild

Tests training service Docker build:
-  Dockerfile exists
-  requirements.txt exists
-  app.py exists
-  Docker image builds successfully

**Expected Duration:** ~30-60 seconds

### TestTrainingServiceContainer

Tests training service container:
-  Container starts successfully
-  Container is running
-  Port 5005 is exposed
-  Health endpoint works

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
-  Docker building
-  Container deployment
-  Port exposure
-  Health checks
-  API functionality
-  Error handling
-  Real dataset integration
-  Association rules validation
-  Response consistency

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
