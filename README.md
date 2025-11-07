# Playlist Recommendation Service - MLOps Assignment

A microservices-based playlist recommendation system built with machine learning, containerized with Docker, orchestrated with Kubernetes, and deployed using continuous delivery with ArgoCD.

## 🎯 Project Overview

This project implements a complete MLOps pipeline for a playlist recommendation service featuring:

- **Microservices Architecture**: Decoupled services for scalability and maintainability
- **Machine Learning**: Collaborative filtering-based recommendation engine
- **Containerization**: Docker containers for all services
- **Orchestration**: Kubernetes manifests for cloud deployment
- **CI/CD**: GitHub Actions for continuous integration and ArgoCD for continuous delivery
- **Modern Web Stack**: FastAPI backend, responsive HTML/CSS/JS frontend

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (Nginx + HTML/JS)
│   :80       │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Backend API │ (FastAPI)
│   :8080     │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ ML Service  │ (FastAPI + scikit-learn)
│   :8000     │
└─────────────┘
```

### Components

1. **Frontend Service** (`services/frontend/`)
   - Nginx-based web server
   - Responsive single-page application
   - User interface for playlist recommendations
   - Port: 80

2. **Backend API Service** (`services/backend-api/`)
   - FastAPI-based API gateway
   - Handles client requests and routes to ML service
   - CORS-enabled for frontend access
   - Port: 8080

3. **ML Service** (`services/ml-service/`)
   - FastAPI-based recommendation engine
   - Collaborative filtering algorithm using scikit-learn
   - RESTful API for recommendations
   - Port: 8000

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Kubernetes cluster (for K8s deployment)
- kubectl (for K8s deployment)
- ArgoCD (for continuous delivery)

### Local Development with Docker Compose

1. **Clone the repository**
   ```bash
   git clone https://github.com/caiosgrossi/mlops-assignment.git
   cd mlops-assignment
   ```

2. **Build and run all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8080
   - ML Service: http://localhost:8000

4. **View API documentation**
   - ML Service: http://localhost:8000/docs
   - Backend API: http://localhost:8080/docs

### Running Individual Services Locally

#### ML Service
```bash
cd services/ml-service
pip install -r requirements.txt
python app.py
# Access at http://localhost:8000
```

#### Backend API
```bash
cd services/backend-api
pip install -r requirements.txt
export ML_SERVICE_URL=http://localhost:8000
python app.py
# Access at http://localhost:8080
```

#### Frontend
```bash
cd services/frontend
# Serve with any HTTP server, e.g.:
python -m http.server 3000
# Access at http://localhost:3000
```

## 🧪 Testing

### Run All Tests
```bash
# ML Service tests
cd services/ml-service
pip install pytest pytest-cov httpx
pytest test_app.py -v --cov=app

# Backend API tests
cd services/backend-api
pip install pytest pytest-cov
pytest test_app.py -v --cov=app
```

### Linting
```bash
# Install linting tools
pip install flake8 black

# Lint ML Service
cd services/ml-service
flake8 app.py --max-line-length=100

# Lint Backend API
cd services/backend-api
flake8 app.py --max-line-length=100
```

## 🐳 Docker

### Build Individual Images
```bash
# ML Service
docker build -t ml-service:latest services/ml-service/

# Backend API
docker build -t backend-api:latest services/backend-api/

# Frontend
docker build -t frontend:latest services/frontend/
```

### Run with Docker Compose
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## ☸️ Kubernetes Deployment

### Manual Deployment

1. **Create namespace**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. **Deploy all services**
   ```bash
   kubectl apply -f k8s/ml-service.yaml
   kubectl apply -f k8s/backend-api.yaml
   kubectl apply -f k8s/frontend.yaml
   ```

3. **Check deployment status**
   ```bash
   kubectl get pods -n playlist-recommender
   kubectl get services -n playlist-recommender
   ```

4. **Access the application**
   ```bash
   # Get the frontend service external IP
   kubectl get svc frontend -n playlist-recommender
   ```

### Using ArgoCD (Continuous Delivery)

1. **Install ArgoCD** (if not already installed)
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

2. **Deploy the application**
   ```bash
   kubectl apply -f k8s/.argocd/application.yaml
   ```

3. **Access ArgoCD UI**
   ```bash
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   # Access at https://localhost:8080
   # Default user: admin
   # Get password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
   ```

4. **Sync the application**
   ```bash
   argocd app sync playlist-recommender
   ```

The ArgoCD configuration enables:
- **Automated sync**: Changes in the repository automatically deploy
- **Self-healing**: Automatically corrects configuration drift
- **Auto-pruning**: Removes resources no longer in Git

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

#### CI Workflow (`.github/workflows/ci.yml`)
Triggered on push and pull requests to main/develop branches:
- ✅ Run unit tests for all services
- 🔍 Lint Python code
- 🐳 Build Docker images
- ✔️ Validate Kubernetes manifests
- 📊 Upload code coverage reports

#### CD Workflow (`.github/workflows/cd.yml`)
Triggered on push to main branch:
- 🐳 Build and push Docker images to registry
- 📝 Display ArgoCD deployment instructions
- 🚀 Ready for ArgoCD to sync and deploy

### Setting up CI/CD

1. **Configure Docker Hub secrets** (optional, for pushing images)
   - Go to GitHub repository → Settings → Secrets
   - Add `DOCKER_USERNAME` and `DOCKER_PASSWORD`

2. **Push changes to trigger CI**
   ```bash
   git push origin main
   ```

3. **Monitor workflow**
   - Check GitHub Actions tab for build status

4. **ArgoCD automatically deploys**
   - ArgoCD watches the repository
   - Automatically syncs changes to Kubernetes

## 📊 API Documentation

### ML Service Endpoints

- `GET /` - Health check
- `GET /health` - Health status
- `POST /recommend` - Get recommendations
  ```json
  {
    "user_id": "user1",
    "num_recommendations": 3
  }
  ```
- `GET /playlists` - Get all playlists
- `GET /users` - Get all users

### Backend API Endpoints

- `GET /` - Health check with ML service status
- `GET /health` - Health status
- `POST /api/recommendations` - Get recommendations (proxies to ML service)
- `GET /api/playlists` - Get all playlists
- `GET /api/users` - Get all users

## 🎵 Using the Application

1. **Open the web interface** (http://localhost or your Kubernetes service IP)

2. **Select a user** or enter a custom user ID

3. **Set number of recommendations** (1-10)

4. **Click "Get Recommendations"** to see personalized playlist suggestions

5. **Click "Show All Playlists"** to browse all available playlists

## 🔧 Configuration

### Environment Variables

#### Backend API
- `ML_SERVICE_URL`: URL of the ML service (default: `http://localhost:8000`)

### Kubernetes Resources

Each service has configured:
- **Resource requests**: Minimum guaranteed resources
- **Resource limits**: Maximum allowed resources
- **Health checks**: Liveness and readiness probes
- **Replicas**: 2 replicas for high availability

## 📈 Monitoring and Observability

### Health Checks

All services expose health endpoints:
- ML Service: `http://ml-service:8000/health`
- Backend API: `http://backend-api:8080/health`
- Frontend: `http://frontend/`

### Kubernetes Probes

- **Liveness Probes**: Detect when containers need restart
- **Readiness Probes**: Determine when pods can receive traffic

### Logs

```bash
# View logs in Kubernetes
kubectl logs -f deployment/ml-service -n playlist-recommender
kubectl logs -f deployment/backend-api -n playlist-recommender
kubectl logs -f deployment/frontend -n playlist-recommender

# View logs with Docker Compose
docker-compose logs -f ml-service
docker-compose logs -f backend-api
docker-compose logs -f frontend
```

## 🛠️ Development

### Project Structure
```
.
├── services/
│   ├── ml-service/          # ML recommendation service
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── test_app.py
│   ├── backend-api/         # Backend API gateway
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── test_app.py
│   └── frontend/            # Web frontend
│       ├── index.html
│       ├── nginx.conf
│       └── Dockerfile
├── k8s/                     # Kubernetes manifests
│   ├── namespace.yaml
│   ├── ml-service.yaml
│   ├── backend-api.yaml
│   ├── frontend.yaml
│   └── .argocd/
│       └── application.yaml
├── .github/
│   └── workflows/           # CI/CD workflows
│       ├── ci.yml
│       └── cd.yml
├── docker-compose.yml       # Local development
└── README.md
```

### Adding New Features

1. **Create a feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make changes and test locally**
   ```bash
   docker-compose up --build
   ```

3. **Run tests**
   ```bash
   pytest
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

5. **Create pull request**
   - CI will automatically run tests and builds
   - Merge to main triggers CD pipeline

## 🔒 Security

- All services run as non-root users in containers
- CORS properly configured in backend API
- Health checks prevent unhealthy pods from receiving traffic
- Secrets can be managed via Kubernetes Secrets
- Resource limits prevent resource exhaustion

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

See LICENSE file for details.

## 🆘 Troubleshooting

### Services not connecting

```bash
# Check if all pods are running
kubectl get pods -n playlist-recommender

# Check service endpoints
kubectl get endpoints -n playlist-recommender

# Check logs
kubectl logs -f deployment/backend-api -n playlist-recommender
```

### Docker Compose issues

```bash
# Rebuild images
docker-compose build --no-cache

# Clean up and restart
docker-compose down -v
docker-compose up --build
```

### Port conflicts

If ports 80, 8080, or 8000 are already in use, modify the port mappings in `docker-compose.yml`.

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Built with ❤️ for MLOps**