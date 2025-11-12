# MLOps Assignment - Music Recommendation System

A microservices-based music recommendation system using association rule mining (Eclat algorithm). The system consists of two services: a training service that discovers patterns in music playlists, and a recommendation service that provides real-time song suggestions.

## 📋 Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Services](#services)
- [Quick Start](#quick-start)
- [Complete Workflow](#complete-workflow)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Development](#development)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATIONS                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │    Training Service (Port 50005)      │
         │  - Train Eclat models                │
         │  - Process datasets                  │
         │  - Save models & metadata            │
         └──────────────────┬───────────────────┘
                            │
                            ▼
         ┌─────────────────────────────────────────┐
         │   Shared Volume: /project2-pv/models    │
         │  - association_rules_v*.pkl             │
         │  - metadata.json                        │
         └─────────────────┬───────────────────────┘
                           │
                           ▼
         ┌──────────────────────────────────────┐
         │  Recommendation Service (Port 50005) │
         │  - Load trained models               │
         │  - Serve recommendations             │
         │  - Hot-reload capability             │
         └──────────────────────────────────────┘
```

## 📁 Project Structure

```
mlops-assignment/
├── training-service/              # Model Training Service
│   ├── app.py                     # Flask app with Eclat algorithm
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Container image
│   ├── .dockerignore              # Docker ignore patterns
│   └── README.md                  # Service documentation
│
├── recommendation-service/        # Recommendation API Service
│   ├── app.py                     # Flask app for recommendations
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Container image
│   ├── .dockerignore              # Docker ignore patterns
│   └── README.md                  # Service documentation
│
├── tests/                         # Unit and Integration Tests
│   ├── test_recommendation_service.py  # Recommendation tests
│   ├── test_training_service.py        # Training tests
│   ├── requirements.txt                # Test dependencies
│   ├── run_all_tests.sh                # Run all tests
│   ├── quick_test.sh                   # Quick test script
│   └── README.md                       # Testing documentation
│
├── DATA_ANALYSIS.md               # Dataset analysis documentation
design
├── BUILD_GUIDE.md                 # Build and deployment guide
└── README.md                      # This file
```

## 🔧 Services

### Training Service (Port 50005)

**Purpose:** Train association rule models using the Eclat algorithm

**Key Features:**
- Downloads and processes CSV datasets
- Mines association rules from playlists
- Saves versioned models with metadata
- Hard-coded parameters: min_support=0.05, min_confidence=0.3

**Endpoints:**
- `GET /health` - Health check
- `POST /train` - Train new model
- `GET /model/info` - Get current model info

### Recommendation Service (Port 50005)

**Purpose:** Provide real-time song recommendations

**Key Features:**
- Loads pre-trained models
- Generates recommendations using association rules
- Partial song name matching
- Hot-reload models without restart

**Endpoints:**
- `GET /health` - Health check
- `POST /api/recommender` - Get recommendations
- `POST /reload-model` - Reload latest model

## 🚀 Quick Start

### Prerequisites

- Docker installed
- Shared volume directory created: `/home/caiogrossi/project2-pv/models`

### Setup Shared Volume

```bash
# Create shared models directory
mkdir -p /home/caiogrossi/project2-pv/models
chmod 755 /home/caiogrossi/project2-pv/models
```

### Build Services

```bash
# Build training service
cd training-service
docker build -t training-service .

# Build recommendation service
cd ../recommendation-service
docker build -t recommendation-service .
```

### Run Services

```bash
# Run training service
docker run -d -p 50005:50005 \
  -v /home/caiogrossi/project2-pv/models:/app/models \
  --name training-container \
  training-service

# Run recommendation service
docker run -d -p 50005:50005 \
  -v /home/caiogrossi/project2-pv/models:/app/models \
  --name recommendation-container \
  recommendation-service
```

### Verify Services

```bash
# Check training service
curl http://localhost:50005/health

# Check recommendation service
curl http://localhost:50005/health
```

## 🔄 Complete Workflow

### Step 1: Train a Model

```bash
curl -X POST http://localhost:50005/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "model_path": "/app/models/association_rules_v1.0.pkl",
  "version": "1.0",
  "timestamp": "2025-11-12T20:00:00",
  "num_rules": 234,
  "num_itemsets": 1567,
  "dataset_stats": {
    "total_transactions": 241458,
    "total_playlists": 2306,
    "unique_items": 5593
  }
}
```

⏱️ **Training Time:** Approximately 5-10 minutes

### Step 2: Reload Model in Recommendation Service

```bash
curl -X POST http://localhost:50005/reload-model
```

**Expected Response:**
```json
{
  "status": "success",
  "version": "1.0",
  "model_date": "2025-11-12T20:00:00"
}
```

### Step 3: Get Recommendations

```bash
curl -X POST http://localhost:50005/api/recommender \
  -H "Content-Type: application/json" \
  -d '{
    "songs": ["Paradise", "Fix You"]
  }'
```

**Expected Response:**
```json
{
  "songs": [
    "Viva La Vida",
    "The Scientist",
    "Clocks",
    "Yellow",
    "Speed of Sound"
  ],
  "version": "1.0",
  "model_date": "2025-11-12T20:00:00"
}
```

## 📚 API Documentation

### Training Service API

#### Train Model
```bash
POST http://localhost:50005/train
Content-Type: application/json

{
  "dataset_url": "https://example.com/dataset.csv"
}
```

**Dataset Requirements:**
- CSV format
- Required columns: `pid`, `track_name`, `artist_name`

#### Check Model Info
```bash
GET http://localhost:50005/model/info
```

### Recommendation Service API

#### Get Recommendations
```bash
POST http://localhost:50005/api/recommender
Content-Type: application/json

{
  "songs": ["Song Name 1", "Song Name 2"]
}
```

**Rules:**
- `songs` must be a non-empty list of strings
- Song names are case-insensitive
- Returns top 5 recommendations by default

#### Reload Model
```bash
POST http://localhost:50005/reload-model
```

Hot-reload the latest trained model without restarting the service.

## 🧪 Testing

The project includes comprehensive unit and integration tests for both services.

### Run All Tests

```bash
cd /home/caiogrossi/mlops-assignment

# Run all tests (training + recommendation services)
bash tests/run_all_tests.sh
```

### Run Specific Tests

```bash
# Test only recommendation service
python3 tests/test_recommendation_service.py

# Test only training service
python3 tests/test_training_service.py

# Quick test (recommendation service only)
bash tests/quick_test.sh
```

### What Tests Cover

**Recommendation Service Tests:**
- ✅ Docker image building
- ✅ Container deployment on port 50005
- ✅ Health endpoint functionality
- ✅ API error handling (empty input, invalid format)
- ✅ **Recommendations using real songs from the dataset**
- ✅ **Integration tests with association rules**
- ✅ Response format validation
- ✅ Consistency across multiple requests

**Training Service Tests:**
- ✅ Docker image building
- ✅ Container deployment on port 50005
- ✅ Health endpoint functionality
- ✅ Model training workflow

### Key Features

The tests automatically:
1. Load the trained model from shared volume
2. Extract real song names from the dataset
3. Identify songs with association rules
4. Test recommendations with actual data
5. Verify high-confidence rules produce expected results

**Example Test Output:**
```
[TEST] Testing with real songs: ['0 To 100 / The Catch Up', 'Jumpman']
[INFO] Recommendations: ['Energy', 'Legend', 'Know Yourself']
[INFO] Model version: 4.0
```

### Test Results

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

See [tests/README.md](tests/README.md) for detailed testing documentation.

## 🛠️ Development

### Local Development (Training Service)

```bash
cd training-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Local Development (Recommendation Service)

```bash
cd recommendation-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### View Logs

```bash
# Training service logs
docker logs -f training-container

# Recommendation service logs
docker logs -f recommendation-container
```

### Stop Services

```bash
docker stop training-container recommendation-container
docker rm training-container recommendation-container
```

## 📊 Performance Characteristics

### Training Service
- **Training Time:** 5-10 minutes for ~240K transactions
- **Memory Usage:** 1-2 GB during training
- **Timeout:** 600 seconds (10 minutes)
- **Workers:** 2 Gunicorn workers

### Recommendation Service
- **Response Time:** <100ms for typical requests
- **Memory Usage:** 100-200 MB
- **Timeout:** 120 seconds (2 minutes)
- **Workers:** 2 Gunicorn workers

## 🧪 Testing

### Test Training Service

```bash
# Health check
curl http://localhost:50005/health

# Train with sample dataset
curl -X POST http://localhost:50005/train \
  -H "Content-Type: application/json" \
  -d '{"dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"}'

# Check model info
curl http://localhost:50005/model/info
```

### Test Recommendation Service

```bash
# Health check
curl http://localhost:50005/health

# Get recommendations
curl -X POST http://localhost:50005/api/recommender \
  -H "Content-Type: application/json" \
  -d '{"songs": ["Yesterday", "Hey Jude"]}'

# Test error handling (empty list)
curl -X POST http://localhost:50005/api/recommender \
  -H "Content-Type: application/json" \
  -d '{"songs": []}'
```

## 🐛 Troubleshooting

### Training Service Returns 500
- Check dataset URL is accessible
- Verify CSV has required columns: `pid`, `track_name`, `artist_name`
- Check available memory (needs 1-2 GB)
- View logs: `docker logs training-container`

### Recommendation Service Returns 503
- Model hasn't been trained yet - run training first
- Shared volume not mounted correctly
- Check if `metadata.json` exists in `/home/caiogrossi/project2-pv/models`

### Empty Recommendations
- This is normal if:
  - Input songs are unknown to the model
  - No association rules match the input
  - Try different song combinations

### Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :50005
sudo lsof -i :50005

# Kill the process or use different ports
```

## 📝 Algorithm Details

### Eclat Algorithm

The system uses the **Eclat (Equivalence Class Transformation)** algorithm:

1. **Vertical Database:** Converts playlists to transaction ID sets
2. **Frequent Itemsets:** Discovers item combinations using DFS and set intersection
3. **Rule Generation:** Creates association rules with confidence and lift metrics
4. **Filtering:** Applies minimum support and confidence thresholds

**Parameters:**
- `min_support = 0.05` (5% of playlists must contain the itemset)
- `min_confidence = 0.3` (30% confidence for rules)

### Recommendation Logic

1. Normalize input song names (lowercase, strip whitespace)
2. Find association rules where all antecedents match input
3. Calculate score: `confidence × lift`
4. Collect consequent songs
5. Filter out songs already in input
6. Rank by score and return top 5

## 📄 License

This project is part of an MLOps assignment.

## 👥 Authors

- Caio Grossi

## 🔗 Related Documents

- [DATA_ANALYSIS.md](DATA_ANALYSIS.md) - Dataset analysis
- [DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md) - Deployment guidelines
- [SERVICE_PLAN.md](SERVICE_PLAN.md) - Original service design
- [RECOMMENDATION_SERVICE_PLAN.md](RECOMMENDATION_SERVICE_PLAN.md) - Recommendation service design
