# Music Recommendation Training Service

Flask-based service that trains association rule models using the Eclat algorithm for music recommendations.

## Overview

This service downloads datasets, trains the Eclat algorithm to discover association rules between songs, and saves the resulting models to a shared volume for use by the recommendation service.

## Architecture

- **Port:** 5005
- **Models Directory:** `/app/models` (mounted from `/home/caiogrossi/project2-pv/models`)
- **Access:** Read/Write access to models
- **Algorithm:** Eclat (min_support=0.05, min_confidence=0.3)

## API Endpoints

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "music-recommendation-eclat",
  "timestamp": "2025-11-09T20:00:00",
  "port": 5005
}
```

### 2. Train Model
```bash
POST /train
Content-Type: application/json

{
  "dataset_url": "https://example.com/dataset.csv"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "model_path": "/app/models/association_rules_v1.0.pkl",
  "version": "1.0",
  "timestamp": "2025-11-09T20:00:00",
  "num_rules": 234,
  "num_itemsets": 1567,
  "dataset_stats": {
    "total_transactions": 241458,
    "total_playlists": 2306,
    "unique_items": 5593
  }
}
```

**Error Responses:**
- `400`: Invalid request (missing URL, invalid format)
- `500`: Training error (dataset download failed, processing error)

### 3. Model Info
```bash
GET /model/info
```

**Response:**
```json
{
  "current_version": "2.0",
  "last_modified": "2025-11-09T20:00:00",
  "model_path": "/app/models/association_rules_v2.0.pkl",
  "num_rules": 234,
  "num_itemsets": 1567,
  "available_versions": ["1.0", "2.0"]
}
```

## Building and Running

### Build Docker Image
```bash
cd /home/caiogrossi/mlops-assignment/training-service
docker build -t training-service .
```

### Run Container
```bash
docker run -d -p 5005:5005 \
  -v /home/caiogrossi/project2-pv/models:/app/models \
  --name training-container \
  training-service
```

### View Logs
```bash
docker logs -f training-container
```

### Stop Container
```bash
docker stop training-container
docker rm training-container
```

## Usage Examples

### Test Health
```bash
curl http://localhost:5005/health
```

### Train Model
```bash
curl -X POST http://localhost:5005/train \
  -H "Content-Type: application/json" \
  -d '{"dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"}'
```

**Note:** Training takes approximately 5-10 minutes depending on dataset size.

### Check Model Info
```bash
curl http://localhost:5005/model/info
```

## Algorithm Details

### Eclat (Equivalence Class Transformation)

The service uses the Eclat algorithm for association rule mining:

**Parameters (hard-coded):**
- `min_support`: 0.05 (5%)
- `min_confidence`: 0.3 (30%)

**How it works:**
1. **Vertical Database:** Convert transactions to tid-lists (transaction ID sets)
2. **Frequent Itemsets:** Find itemsets with support ≥ min_support using DFS
3. **Rule Generation:** Create rules from frequent itemsets with confidence ≥ min_confidence
4. **Metrics:** Calculate support, confidence, and lift for each rule

### Output Format

The trained model is saved as a pickle file containing:
```python
{
  'frequent_itemsets': [
    {'itemset': ['Song1,Artist1'], 'support': 0.15},
    {'itemset': ['Song1,Artist1', 'Song2,Artist2'], 'support': 0.08}
  ],
  'rules': [
    {
      'antecedent': ['Song1,Artist1'],
      'consequent': ['Song2,Artist2'],
      'support': 0.08,
      'confidence': 0.53,
      'lift': 3.2
    }
  ],
  'num_rules': 234,
  'num_itemsets': 1567
}
```

## Model Versioning

Models are versioned automatically:
- First model: `v1.0`
- Second model: `v2.0`
- Third model: `v3.0`
- etc.

Metadata is stored in `metadata.json`:
```json
{
  "current_version": "2.0",
  "models": {
    "1.0": {
      "path": "/app/models/association_rules_v1.0.pkl",
      "timestamp": "2025-11-09T20:00:00",
      "num_rules": 234,
      "num_itemsets": 1567
    },
    "2.0": {
      "path": "/app/models/association_rules_v2.0.pkl",
      "timestamp": "2025-11-09T21:00:00",
      "num_rules": 256,
      "num_itemsets": 1623
    }
  }
}
```

## Dataset Requirements

The CSV dataset must contain the following columns:
- `pid`: Playlist ID
- `track_name`: Song name
- `artist_name`: Artist name

Example:
```csv
pid,track_name,artist_name
1,Yesterday,Beatles
1,Hey Jude,Beatles
2,Bohemian Rhapsody,Queen
```

## Performance

- **Training Time:** 5-10 minutes for ~240K transactions
- **Memory:** 1-2 GB during training
- **Workers:** 2 Gunicorn workers
- **Timeout:** 600 seconds (10 minutes)
- **Max Itemset Size:** 5 items (configurable in code)

## Development

### Local Testing (without Docker)
```bash
cd training-service
pip install -r requirements.txt

# Create models directory
mkdir -p /tmp/models
export MODELS_DIR=/tmp/models

# Run Flask app
python app.py
```

The service will be available at `http://localhost:5005`.

## Troubleshooting

### Training takes too long
- Check dataset size (large datasets take longer)
- Monitor progress in logs: `docker logs -f training-container`
- Training timeout is 600 seconds (10 minutes)

### Out of memory
- Reduce dataset size
- Increase Docker memory limits
- Increase min_support threshold (edit code)

### No rules generated
- Dataset may be too sparse
- Lower min_confidence threshold (edit code)
- Check if dataset has enough playlists

### SSL Certificate Errors
- The service disables SSL verification for dataset downloads
- This is intentional for development environments

## Integration with Recommendation Service

After training completes:

1. **Training service** writes:
   - Model pickle file: `association_rules_v1.0.pkl`
   - Metadata file: `metadata.json`

2. **Recommendation service** reads:
   - Loads model on startup
   - Can hot-reload via `/reload-model` endpoint

Both services share the volume at `/home/caiogrossi/project2-pv/models`.
# Test automated deployment
