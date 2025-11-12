# Build and Deployment Guide

Quick reference for building and deploying the Music Recommendation System.

## Prerequisites

```bash
# Create shared volume directory
mkdir -p /home/caiogrossi/project2-pv/models
chmod 755 /home/caiogrossi/project2-pv/models
```

## Build Docker Images

### Training Service

```bash
cd /home/caiogrossi/mlops-assignment/training-service
docker build -t training-service:latest .
```

### Recommendation Service

```bash
cd /home/caiogrossi/mlops-assignment/recommendation-service
docker build -t caio-recommendation-service:latest .
```

## Run Containers

### Training Service (Port 50005)

```bash
docker run -d \
  --name caio-training-container \
  -p 50005:50005 \
  -v /home/caiogrossi/project2-pv/models:/app/models \
  caio-training-service:latest
```

### Recommendation Service (Port 50005)

```bash
docker run -d \
  --name caio-recommendation-container \
  -p 50005:50005 \
  -v /home/caiogrossi/project2-pv/models:/app/models \
  caio-recommendation-service:latest
```

## Verify Deployment

```bash
# Check containers are running
docker ps

# Test training service
curl http://localhost:50005/health

# Test recommendation service
curl http://localhost:50005/health
```

## Complete Workflow Test

### 1. Train Model

```bash
curl -X POST http://localhost:50005/train \
  -H "Content-Type: application/json" \
  -d '{"dataset_url": "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"}'
```

**Wait:** 5-10 minutes for training to complete

**Monitor progress:**
```bash
docker logs -f training-container
```

### 2. Reload Model

```bash
curl -X POST http://localhost:50005/reload-model
```

### 3. Get Recommendations

```bash
curl -X POST http://localhost:50005/api/recommender \
  -H "Content-Type: application/json" \
  -d '{"songs": ["What's The Difference", "Help Me Lose My Mind"]}'
```

## Management Commands

### View Logs

```bash
# Training service
docker logs -f training-container

# Recommendation service
docker logs -f recommendation-container
```

### Restart Services

```bash
# Restart training service
docker restart training-container

# Restart recommendation service
docker restart recommendation-container
```

### Stop Services

```bash
# Stop both services
docker stop training-container recommendation-container

# Remove containers
docker rm training-container recommendation-container
```

### Clean Up

```bash
# Remove containers
docker rm -f training-container recommendation-container

# Remove images
docker rmi training-service:latest recommendation-service:latest

# Clean up models (CAUTION: deletes all trained models)
rm -rf /home/caiogrossi/project2-pv/models/*
```

## Rebuild After Changes

```bash
# Stop and remove old containers
docker stop training-container recommendation-container
docker rm training-container recommendation-container

# Rebuild images
cd /home/caiogrossi/mlops-assignment/training-service
docker build -t training-service:latest .

cd /home/caiogrossi/mlops-assignment/recommendation-service
docker build -t recommendation-service:latest .

# Run new containers
docker run -d --name training-container -p 5005:5005 \
  -v /home/caiogrossi/project2-pv/models:/app/models \
  training-service:latest

docker run -d --name recommendation-container -p 50005:50005 \
  -v /home/caiogrossi/project2-pv/models:/app/models \
  recommendation-service:latest
```

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker logs training-container
docker logs recommendation-container

# Check if ports are in use
sudo lsof -i :5005
sudo lsof -i :50005
```

### Training fails

```bash
# Check available disk space
df -h

# Check available memory
free -h

# Verify dataset URL is accessible
curl -I "https://homepages.dcc.ufmg.br/~cunha/hosted/cloudcomp-2023s2-datasets/2023_spotify_ds1.csv"
```

### Recommendation service returns 503

```bash
# Check if model exists
ls -lh /home/caiogrossi/project2-pv/models/

# Check metadata
cat /home/caiogrossi/project2-pv/models/metadata.json

# Train a model first if none exists
```

## Production Deployment

For production deployment, consider:

1. **Use docker-compose** for orchestration
2. **Add reverse proxy** (nginx) for SSL/TLS
3. **Implement monitoring** (Prometheus + Grafana)
4. **Add persistent logging** (centralized logging)
5. **Set resource limits** in Docker
6. **Use health checks** in orchestration
7. **Implement backup** for models directory

### Example docker-compose.yml

```yaml
version: '3.8'

services:
  training:
    image: training-service:latest
    ports:
      - "5005:5005"
    volumes:
      - /home/caiogrossi/project2-pv/models:/app/models
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5005/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  recommendation:
    image: recommendation-service:latest
    ports:
      - "50005:50005"
    volumes:
      - /home/caiogrossi/project2-pv/models:/app/models
    restart: unless-stopped
    depends_on:
      - training
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:50005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Quick Reference

| Service | Port | Health Check | Main Endpoint |
|---------|------|--------------|---------------|
| Training | 5005 | `GET /health` | `POST /train` |
| Recommendation | 50005 | `GET /health` | `POST /api/recommender` |

**Shared Volume:** `/home/caiogrossi/project2-pv/models`

**Container Names:**
- `training-container`
- `recommendation-container`

**Image Tags:**
- `training-service:latest`
- `recommendation-service:latest`
