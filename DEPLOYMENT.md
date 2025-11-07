# Deployment Guide

This guide provides step-by-step instructions for deploying the Playlist Recommendation Service.

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [ArgoCD Setup](#argocd-setup)
- [CI/CD Configuration](#cicd-configuration)

## Local Development

### 1. Run ML Service Locally
```bash
cd services/ml-service
pip install -r requirements.txt
python app.py
```
Access at: http://localhost:8000/docs

### 2. Run Backend API Locally
```bash
cd services/backend-api
pip install -r requirements.txt
export ML_SERVICE_URL=http://localhost:8000
python app.py
```
Access at: http://localhost:8080/docs

### 3. Run Frontend Locally
```bash
cd services/frontend
# Use any HTTP server
python -m http.server 3000
```
Access at: http://localhost:3000

## Docker Deployment

### Using Docker Compose (Recommended for Local Testing)

1. **Build and start all services:**
```bash
docker-compose up --build
```

2. **Access the application:**
- Frontend: http://localhost
- Backend API: http://localhost:8080
- ML Service: http://localhost:8000

3. **View logs:**
```bash
docker-compose logs -f
```

4. **Stop services:**
```bash
docker-compose down
```

### Build Individual Docker Images

```bash
# ML Service
docker build -t ml-service:latest ./services/ml-service

# Backend API
docker build -t backend-api:latest ./services/backend-api

# Frontend
docker build -t frontend:latest ./services/frontend
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (local: minikube/kind, cloud: EKS/GKE/AKS)
- kubectl configured
- Docker images built and pushed to a registry (optional for local clusters)

### Option 1: Manual Deployment

1. **Create namespace:**
```bash
kubectl apply -f k8s/namespace.yaml
```

2. **Deploy all services:**
```bash
kubectl apply -f k8s/ml-service.yaml
kubectl apply -f k8s/backend-api.yaml
kubectl apply -f k8s/frontend.yaml
```

3. **Verify deployment:**
```bash
kubectl get pods -n playlist-recommender
kubectl get services -n playlist-recommender
```

4. **Access the application:**
```bash
# For LoadBalancer (cloud)
kubectl get svc frontend -n playlist-recommender

# For local (port-forward)
kubectl port-forward svc/frontend 8080:80 -n playlist-recommender
# Access at http://localhost:8080
```

### Option 2: Using Kustomize

```bash
kubectl apply -k k8s/
```

### Option 3: Using Helm (if Helm charts are created)

```bash
helm install playlist-recommender ./helm-charts/
```

## ArgoCD Setup

### 1. Install ArgoCD

```bash
# Create ArgoCD namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s
```

### 2. Access ArgoCD UI

```bash
# Port forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Access at: https://localhost:8080
- Username: `admin`
- Password: (from command above)

### 3. Deploy Application with ArgoCD

#### Option A: Using kubectl
```bash
kubectl apply -f k8s/.argocd/application.yaml
```

#### Option B: Using ArgoCD CLI
```bash
# Install ArgoCD CLI
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/

# Login to ArgoCD
argocd login localhost:8080

# Create application
argocd app create playlist-recommender \
  --repo https://github.com/caiosgrossi/mlops-assignment.git \
  --path k8s \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace playlist-recommender

# Enable auto-sync
argocd app set playlist-recommender --sync-policy automated

# Sync application
argocd app sync playlist-recommender
```

#### Option C: Using ArgoCD UI
1. Click "New App"
2. Fill in details:
   - Application Name: `playlist-recommender`
   - Project: `default`
   - Sync Policy: `Automatic`
   - Repository URL: `https://github.com/caiosgrossi/mlops-assignment.git`
   - Path: `k8s`
   - Cluster: `https://kubernetes.default.svc`
   - Namespace: `playlist-recommender`
3. Click "Create"

### 4. Monitor Deployment

```bash
# Watch ArgoCD application status
argocd app get playlist-recommender

# Watch Kubernetes resources
kubectl get all -n playlist-recommender -w

# View ArgoCD sync status
argocd app list
```

## CI/CD Configuration

### GitHub Actions Setup

The repository includes two workflows:
1. **CI Workflow** (`.github/workflows/ci.yml`) - Runs on all pushes/PRs
2. **CD Workflow** (`.github/workflows/cd.yml`) - Runs on main branch

### Configure Secrets (Optional for Docker Push)

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Add secrets:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub password or access token

### Workflow Triggers

- **CI**: Automatically runs on:
  - Push to `main` or `develop` branches
  - Pull requests to `main` or `develop` branches

- **CD**: Automatically runs on:
  - Push to `main` branch
  - Manual trigger via GitHub Actions UI

### What CI/CD Does

#### CI Pipeline:
1. Tests ML Service with pytest
2. Tests Backend API with pytest
3. Lints Python code with flake8
4. Builds Docker images
5. Validates Kubernetes manifests
6. Uploads code coverage

#### CD Pipeline:
1. Builds Docker images
2. Pushes images to Docker registry (if configured)
3. Displays ArgoCD deployment instructions

### ArgoCD Auto-Sync

With ArgoCD configured for auto-sync:
1. Developer pushes code to `main` branch
2. GitHub Actions CI runs tests and builds
3. GitHub Actions CD builds and pushes Docker images
4. ArgoCD detects Git repository changes
5. ArgoCD automatically syncs and deploys to Kubernetes

## Testing the Deployment

### 1. Health Checks

```bash
# ML Service
curl http://<ml-service-url>:8000/health

# Backend API
curl http://<backend-api-url>:8080/health

# Frontend
curl http://<frontend-url>/
```

### 2. Get Recommendations

```bash
curl -X POST http://<backend-api-url>:8080/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "num_recommendations": 3}'
```

### 3. List Playlists

```bash
curl http://<backend-api-url>:8080/api/playlists
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n playlist-recommender

# Describe pod for issues
kubectl describe pod <pod-name> -n playlist-recommender

# Check logs
kubectl logs <pod-name> -n playlist-recommender
```

### Service Not Accessible

```bash
# Check services
kubectl get svc -n playlist-recommender

# Check endpoints
kubectl get endpoints -n playlist-recommender
```

### ArgoCD Sync Issues

```bash
# Check application health
argocd app get playlist-recommender

# Refresh application
argocd app refresh playlist-recommender

# Force sync
argocd app sync playlist-recommender --force
```

### Docker Compose Issues

```bash
# Rebuild without cache
docker-compose build --no-cache

# View logs
docker-compose logs -f <service-name>

# Remove volumes
docker-compose down -v
```

## Scaling

### Scale Deployments

```bash
# Scale ML Service
kubectl scale deployment ml-service --replicas=3 -n playlist-recommender

# Scale Backend API
kubectl scale deployment backend-api --replicas=3 -n playlist-recommender

# Scale Frontend
kubectl scale deployment frontend --replicas=2 -n playlist-recommender
```

### Auto-scaling

Create HorizontalPodAutoscaler:

```bash
kubectl autoscale deployment ml-service \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n playlist-recommender
```

## Monitoring

### View Logs

```bash
# All pods
kubectl logs -l app=ml-service -n playlist-recommender --tail=100 -f

# Specific pod
kubectl logs <pod-name> -n playlist-recommender -f
```

### Check Resource Usage

```bash
kubectl top nodes
kubectl top pods -n playlist-recommender
```

## Cleanup

### Remove Application

```bash
# ArgoCD
argocd app delete playlist-recommender

# Kubernetes
kubectl delete namespace playlist-recommender

# Docker Compose
docker-compose down -v
```

## Next Steps

1. **Set up monitoring** with Prometheus and Grafana
2. **Configure ingress** for better routing
3. **Add persistent storage** for ML models
4. **Implement authentication** for API endpoints
5. **Set up logging** with ELK stack or Loki
6. **Add database** for user data and playlists
7. **Implement caching** with Redis

## Support

For issues or questions:
- Check the main README.md
- Review GitHub Issues
- Check ArgoCD documentation
- Review Kubernetes troubleshooting guides
