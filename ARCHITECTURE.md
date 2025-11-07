# Architecture Overview

## System Architecture

The Playlist Recommendation Service is built using a microservices architecture with three main components:

```
┌──────────────────────────────────────────────────────────────┐
│                         User Browser                          │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ HTTP/HTTPS
                   │
┌──────────────────▼───────────────────────────────────────────┐
│                      Frontend Service                         │
│                   (Nginx + HTML/JS/CSS)                       │
│                         Port: 80                              │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ REST API
                   │
┌──────────────────▼───────────────────────────────────────────┐
│                    Backend API Service                        │
│                        (FastAPI)                              │
│                        Port: 8080                             │
│                                                               │
│  Features:                                                    │
│  - API Gateway                                                │
│  - CORS handling                                              │
│  - Request routing                                            │
│  - Health checks                                              │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   │ Internal REST API
                   │
┌──────────────────▼───────────────────────────────────────────┐
│                      ML Service                               │
│              (FastAPI + scikit-learn)                         │
│                     Port: 8000                                │
│                                                               │
│  Features:                                                    │
│  - Collaborative Filtering                                    │
│  - Recommendation Engine                                      │
│  - User-Playlist Matrix                                       │
│  - Cosine Similarity                                          │
└───────────────────────────────────────────────────────────────┘
```

## Data Flow

### Recommendation Request Flow

1. **User Interaction**: User selects user ID and clicks "Get Recommendations"
2. **Frontend**: Sends POST request to `/api/recommendations`
3. **Backend API**: Receives request, validates, forwards to ML Service
4. **ML Service**: 
   - Builds user-item interaction matrix
   - Calculates user similarities using cosine similarity
   - Generates weighted recommendations
   - Returns top N recommendations
5. **Backend API**: Returns response to frontend
6. **Frontend**: Displays recommendations in UI

### Health Check Flow

1. **Frontend**: Polls `/health` endpoint on page load
2. **Backend API**: Checks own health and ML service health
3. **Frontend**: Displays service status indicator

## Component Details

### 1. Frontend Service

**Technology Stack:**
- Nginx (Web server)
- HTML5 (Structure)
- CSS3 (Styling)
- Vanilla JavaScript (Logic)

**Responsibilities:**
- Serve static web content
- Provide user interface
- Handle user interactions
- Display recommendations
- Show service status

**Key Features:**
- Responsive design
- Real-time status updates
- Error handling
- Loading states
- User selection
- Recommendation display

**Endpoints:**
- `GET /` - Main application page
- Proxies `/api/*` to backend
- Proxies `/health` to backend

### 2. Backend API Service

**Technology Stack:**
- Python 3.11+
- FastAPI (Web framework)
- Uvicorn (ASGI server)
- httpx (HTTP client)
- Pydantic (Data validation)

**Responsibilities:**
- API Gateway pattern
- Request validation
- Service orchestration
- CORS handling
- Error handling
- Health monitoring

**Key Features:**
- RESTful API
- Async/await support
- Automatic API documentation
- Request/response validation
- Comprehensive error handling

**Endpoints:**
- `GET /` - Health check with service status
- `GET /health` - Detailed health status
- `POST /api/recommendations` - Get recommendations
- `GET /api/playlists` - List all playlists
- `GET /api/users` - List all users

**Environment Variables:**
- `ML_SERVICE_URL` - URL of ML service (default: `http://localhost:8000`)

### 3. ML Service

**Technology Stack:**
- Python 3.11+
- FastAPI (Web framework)
- Uvicorn (ASGI server)
- scikit-learn (ML library)
- NumPy (Numerical computing)
- Pydantic (Data validation)

**Responsibilities:**
- Machine learning inference
- Recommendation generation
- User similarity calculation
- Data processing

**Algorithm: Collaborative Filtering**

The service implements user-based collaborative filtering:

1. **User-Item Matrix Creation:**
   ```python
   matrix = [
       [1, 1, 1, 0, 0, 0],  # user1
       [0, 1, 1, 1, 0, 0],  # user2
       [1, 0, 0, 1, 1, 0],  # user3
       [0, 0, 1, 0, 1, 1],  # user4
   ]
   ```

2. **Similarity Calculation:**
   - Uses cosine similarity between users
   - Formula: `similarity = cos(θ) = (A · B) / (||A|| ||B||)`

3. **Weighted Recommendation:**
   - Combines similar users' preferences
   - Weights by similarity score
   - Filters out already consumed items

4. **Fallback for New Users:**
   - Returns most popular items
   - Based on popularity scores

**Sample Data:**
- 4 predefined users
- 6 playlists across different genres
- User-playlist interaction history
- Genre preferences

**Endpoints:**
- `GET /` - Health check
- `GET /health` - Health status
- `POST /recommend` - Generate recommendations
- `GET /playlists` - List all playlists
- `GET /users` - List all users

## Deployment Architecture

### Docker Deployment

```
┌─────────────────────────────────────────────────────────┐
│              Docker Compose Network                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Frontend   │  │  Backend API │  │  ML Service  │  │
│  │   Container  │◄─┤   Container  │◄─┤   Container  │  │
│  │   Port: 80   │  │  Port: 8080  │  │  Port: 8000  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Isolated containers
- Bridge network
- Volume persistence (optional)
- Health checks
- Auto-restart policies

### Kubernetes Deployment

```
┌───────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                      │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │              Namespace: playlist-recommender       │   │
│  │                                                    │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │  LoadBalancer Service (frontend:80)         │  │   │
│  │  └─────────────┬───────────────────────────────┘  │   │
│  │                │                                   │   │
│  │  ┌─────────────▼───────────────────────────────┐  │   │
│  │  │  Frontend Deployment (2 replicas)           │  │   │
│  │  │  - Pod 1: frontend:80                       │  │   │
│  │  │  - Pod 2: frontend:80                       │  │   │
│  │  └─────────────┬───────────────────────────────┘  │   │
│  │                │                                   │   │
│  │  ┌─────────────▼───────────────────────────────┐  │   │
│  │  │  ClusterIP Service (backend-api:8080)       │  │   │
│  │  └─────────────┬───────────────────────────────┘  │   │
│  │                │                                   │   │
│  │  ┌─────────────▼───────────────────────────────┐  │   │
│  │  │  Backend API Deployment (2 replicas)        │  │   │
│  │  │  - Pod 1: backend-api:8080                  │  │   │
│  │  │  - Pod 2: backend-api:8080                  │  │   │
│  │  └─────────────┬───────────────────────────────┘  │   │
│  │                │                                   │   │
│  │  ┌─────────────▼───────────────────────────────┐  │   │
│  │  │  ClusterIP Service (ml-service:8000)        │  │   │
│  │  └─────────────┬───────────────────────────────┘  │   │
│  │                │                                   │   │
│  │  ┌─────────────▼───────────────────────────────┐  │   │
│  │  │  ML Service Deployment (2 replicas)         │  │   │
│  │  │  - Pod 1: ml-service:8000                   │  │   │
│  │  │  - Pod 2: ml-service:8000                   │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
└───────────────────────────────────────────────────────────┘
```

**Features:**
- High availability (2 replicas per service)
- Auto-scaling capability
- Health monitoring
- Resource limits
- Service discovery
- Load balancing

## CI/CD Pipeline

### Continuous Integration (GitHub Actions)

```
┌─────────────────────────────────────────────────────────┐
│              Developer pushes code                      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│            GitHub Actions CI Workflow                   │
│                                                         │
│  1. Checkout code                                       │
│  2. Set up Python 3.11                                  │
│  3. Install dependencies                                │
│  4. Run unit tests (pytest)                             │
│  5. Run linters (flake8, black)                         │
│  6. Build Docker images                                 │
│  7. Validate Kubernetes manifests                       │
│  8. Upload coverage reports                             │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              Tests Pass / Fail                          │
└─────────────────────────────────────────────────────────┘
```

### Continuous Delivery (ArgoCD)

```
┌─────────────────────────────────────────────────────────┐
│         Code merged to main branch                      │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│          GitHub Actions CD Workflow                     │
│                                                         │
│  1. Build Docker images                                 │
│  2. Tag images (latest + SHA)                           │
│  3. Push to Docker registry                             │
│  4. Update Git repository                               │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              ArgoCD detects changes                     │
│                                                         │
│  1. Pull latest from Git                                │
│  2. Compare with cluster state                          │
│  3. Sync changes to cluster                             │
│  4. Apply Kubernetes manifests                          │
│  5. Monitor rollout status                              │
│  6. Self-heal if drift detected                         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│         Application deployed in Kubernetes              │
└─────────────────────────────────────────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling

All services support horizontal scaling:

```bash
# Scale ML Service
kubectl scale deployment ml-service --replicas=5 -n playlist-recommender

# Scale Backend API
kubectl scale deployment backend-api --replicas=3 -n playlist-recommender
```

### Auto-scaling

Kubernetes HorizontalPodAutoscaler can be configured:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Load Balancing

- **Frontend**: LoadBalancer service distributes traffic
- **Backend API**: ClusterIP with service mesh
- **ML Service**: Internal load balancing via Kubernetes Service

## Security Considerations

### Current Implementation

1. **Network Isolation**: Microservices communicate via internal network
2. **CORS**: Configured in backend API
3. **Health Checks**: Prevent unhealthy pods from receiving traffic
4. **Resource Limits**: Prevent resource exhaustion
5. **Non-root Containers**: All services run as non-root users

### Future Enhancements

1. **Authentication**: JWT tokens, OAuth2
2. **Authorization**: RBAC, policy enforcement
3. **Secrets Management**: Kubernetes Secrets, HashiCorp Vault
4. **TLS/SSL**: HTTPS encryption
5. **API Rate Limiting**: Prevent abuse
6. **Network Policies**: Restrict pod-to-pod communication
7. **Image Scanning**: Vulnerability detection
8. **Pod Security Policies**: Enforce security standards

## Monitoring and Observability

### Health Endpoints

All services expose health endpoints for monitoring:

- `GET /health` - Returns service status
- Kubernetes liveness probes
- Kubernetes readiness probes

### Logging

- Container logs via `kubectl logs`
- Docker Compose logs via `docker-compose logs`
- Centralized logging (future): ELK, Loki

### Metrics (Future)

- Prometheus metrics exposition
- Grafana dashboards
- Application performance monitoring
- Resource utilization tracking

## Future Enhancements

### Technical Improvements

1. **Database Integration**: PostgreSQL for persistent storage
2. **Caching**: Redis for frequently accessed data
3. **Message Queue**: RabbitMQ/Kafka for async processing
4. **Model Training Pipeline**: MLflow for ML lifecycle
5. **A/B Testing**: Feature flags and experimentation
6. **API Versioning**: Support multiple API versions

### ML Enhancements

1. **Deep Learning Models**: Neural collaborative filtering
2. **Hybrid Recommendations**: Content + collaborative filtering
3. **Real-time Training**: Online learning
4. **Personalization**: User context, time, location
5. **Diversity**: Avoid filter bubbles
6. **Explainability**: Why recommendations were made

### Infrastructure Improvements

1. **Multi-region Deployment**: Global distribution
2. **CDN**: Edge caching for frontend
3. **Service Mesh**: Istio/Linkerd for advanced traffic management
4. **Disaster Recovery**: Backup and restore procedures
5. **Cost Optimization**: Right-sizing resources
