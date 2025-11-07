# Quick Start Guide

Get the Playlist Recommendation Service up and running in minutes!

## Prerequisites

Choose one of the following deployment methods:

### For Docker Compose (Easiest)
- Docker installed (version 20.10 or later)
- Docker Compose installed (version 2.0 or later)

### For Kubernetes
- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl installed and configured
- Docker for building images

### For Local Development
- Python 3.11 or later
- pip package manager

## Option 1: Docker Compose (Recommended for Testing)

The fastest way to run the entire system locally.

### Step 1: Clone the Repository

```bash
git clone https://github.com/caiosgrossi/mlops-assignment.git
cd mlops-assignment
```

### Step 2: Start All Services

```bash
docker-compose up --build
```

This will:
- Build Docker images for all three services
- Start ML service on port 8000
- Start Backend API on port 8080
- Start Frontend on port 80

### Step 3: Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost
- **Backend API Docs**: http://localhost:8080/docs
- **ML Service Docs**: http://localhost:8000/docs

### Step 4: Try It Out

1. The web interface will load automatically
2. Select a user from the dropdown (or enter a custom user ID)
3. Choose the number of recommendations (1-10)
4. Click "Get Recommendations"
5. View your personalized playlist suggestions!

### Step 5: Stop Services

Press `Ctrl+C` in the terminal, then:

```bash
docker-compose down
```

## Option 2: Kubernetes with ArgoCD

For production-like deployment with continuous delivery.

### Step 1: Set Up Kubernetes Cluster

If you don't have a cluster, use minikube:

```bash
# Install minikube (if not installed)
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start --cpus=4 --memory=8192

# Enable metrics
minikube addons enable metrics-server
```

### Step 2: Install ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=5m
```

### Step 3: Access ArgoCD UI

```bash
# Port forward ArgoCD server (run in separate terminal)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo
```

Open https://localhost:8080 in your browser:
- Username: `admin`
- Password: (from command above)

### Step 4: Deploy the Application

```bash
# Clone repository
git clone https://github.com/caiosgrossi/mlops-assignment.git
cd mlops-assignment

# Deploy with ArgoCD
kubectl apply -f k8s/.argocd/application.yaml
```

### Step 5: Monitor Deployment

```bash
# Watch pods starting
kubectl get pods -n playlist-recommender -w

# Check services
kubectl get svc -n playlist-recommender
```

### Step 6: Access the Application

For minikube:

```bash
# Get frontend URL
minikube service frontend -n playlist-recommender
```

For cloud providers:

```bash
# Get external IP
kubectl get svc frontend -n playlist-recommender
# Access via the EXTERNAL-IP
```

## Option 3: Local Development

Run services individually for development.

### Step 1: Clone Repository

```bash
git clone https://github.com/caiosgrossi/mlops-assignment.git
cd mlops-assignment
```

### Step 2: Set Up ML Service

```bash
# Terminal 1
cd services/ml-service
pip install -r requirements.txt
python app.py
```

The ML service will start on http://localhost:8000

### Step 3: Set Up Backend API

```bash
# Terminal 2
cd services/backend-api
pip install -r requirements.txt
export ML_SERVICE_URL=http://localhost:8000
python app.py
```

The backend API will start on http://localhost:8080

### Step 4: Set Up Frontend

```bash
# Terminal 3
cd services/frontend
python -m http.server 3000
```

The frontend will be available at http://localhost:3000

**Note**: You'll need to update the API URL in `index.html` to point to `http://localhost:8080`

## Testing the System

### 1. Check Service Health

```bash
# ML Service
curl http://localhost:8000/health

# Backend API
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ML Recommendation Service"
}
```

### 2. Get Recommendations

```bash
curl -X POST http://localhost:8080/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user1",
    "num_recommendations": 3
  }'
```

Expected response:
```json
{
  "user_id": "user1",
  "recommendations": [
    {
      "playlist_id": 4,
      "name": "Electronic Dreams",
      "genre": "electronic",
      "score": 0.75
    },
    ...
  ],
  "algorithm": "collaborative_filtering"
}
```

### 3. List All Playlists

```bash
curl http://localhost:8080/api/playlists
```

### 4. Test with Web Interface

1. Open http://localhost (or your frontend URL)
2. Select `user1` from dropdown
3. Click "Get Recommendations"
4. You should see 3 recommended playlists
5. Click "Show All Playlists" to see all available playlists

## Using the Makefile

The project includes a Makefile for common operations:

```bash
# Show all available commands
make help

# Run tests
make test

# Run linters
make lint

# Build and start with Docker Compose
make up-build

# View logs
make logs

# Apply Kubernetes manifests
make k8s-apply

# Check Kubernetes status
make k8s-status
```

## Common Issues and Solutions

### Port Already in Use

If port 80, 8000, or 8080 is already in use:

**For Docker Compose:**
Edit `docker-compose.yml` and change port mappings:
```yaml
ports:
  - "8081:80"  # Frontend
  - "8082:8080"  # Backend
  - "8001:8000"  # ML Service
```

**For Local Development:**
Use different ports when starting services:
```bash
python app.py  # Will use default port
# Or specify in code/config
```

### Docker Build Fails

```bash
# Clean Docker cache
docker system prune -af

# Rebuild without cache
docker-compose build --no-cache
```

### Kubernetes Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n playlist-recommender

# Check logs
kubectl logs <pod-name> -n playlist-recommender

# Common issues:
# - Image pull errors: Check image name/availability
# - Resource limits: Adjust in YAML files
# - Health check failures: Check service startup time
```

### Services Not Connecting

Check that services can reach each other:

```bash
# For Docker Compose
docker-compose exec backend-api ping ml-service

# For Kubernetes
kubectl exec -it deployment/backend-api -n playlist-recommender -- curl http://ml-service:8000/health
```

## Next Steps

Now that you have the system running:

1. **Explore the API**: Visit http://localhost:8080/docs for interactive API documentation
2. **Review the Code**: Check out the service implementations
3. **Modify Recommendations**: Edit `services/ml-service/app.py` to change the algorithm
4. **Add New Features**: Extend the services with new endpoints
5. **Set Up Monitoring**: Add Prometheus and Grafana
6. **Configure CI/CD**: Set up GitHub Actions workflows

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options
- Open an issue on GitHub for bugs or questions

## Quick Reference

| Service | Local Port | Docker Port | K8s Service |
|---------|-----------|-------------|-------------|
| Frontend | 3000 | 80 | frontend:80 |
| Backend API | 8080 | 8080 | backend-api:8080 |
| ML Service | 8000 | 8000 | ml-service:8000 |

## Useful Commands Cheat Sheet

```bash
# Docker Compose
docker-compose up -d              # Start in background
docker-compose down               # Stop services
docker-compose logs -f            # View logs
docker-compose restart            # Restart services

# Kubernetes
kubectl get all -n playlist-recommender           # View all resources
kubectl logs -f deployment/ml-service -n playlist-recommender  # View logs
kubectl port-forward svc/frontend 8080:80 -n playlist-recommender  # Port forward
kubectl scale deployment ml-service --replicas=3 -n playlist-recommender  # Scale

# ArgoCD
argocd app list                   # List applications
argocd app sync playlist-recommender  # Sync application
argocd app get playlist-recommender   # Get app details
```

---

**Ready to explore?** Start with Option 1 (Docker Compose) for the quickest setup!
