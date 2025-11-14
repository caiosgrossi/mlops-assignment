# Kubernetes Configuration - Playlist Recommender System

This directory contains all Kubernetes manifests required to deploy the Playlist Recommender System on a Kubernetes cluster.

##  Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Prerequisites](#prerequisites)
- [Deployment Instructions](#deployment-instructions)
- [Configuration Details](#configuration-details)
- [Troubleshooting](#troubleshooting)

##  Overview

The Kubernetes deployment consists of:
- **2 Deployments**: Training service and Recommendation service
- **2 Services**: For routing traffic to the deployments
- **1 PersistentVolumeClaim**: Shared storage for ML models

All resources are deployed in the `caiogrossi` namespace.

##  Components

### 1. Persistent Volume Claim (`pvc-models.yaml`)

Provides shared storage for ML models between training and recommendation services.

**Specifications:**
- **Name:** `model-pvc`
- **Storage Class:** `default-storage-class-caiogrossi`
- **Access Mode:** `ReadWriteMany` (allows multiple pods to read/write)
- **Storage Size:** `1Gi`
- **Volume Name:** `project2-pv-caiogrossi`

**Purpose:** 
- Store trained ML models (`.pkl` files)
- Share models between training and recommendation services
- Persist models across pod restarts

### 2. Training Service Deployment (`deployment-training.yaml`)

Runs the model training service that creates and updates ML models.

**Specifications:**
- **Name:** `playlist-recommender-system-trainer`
- **Replicas:** `1` (single instance for training)
- **Image:** `caiosgrossi/playlist-recommender-system:training-service-0.1`
- **Container Port:** `50005`
- **App Label:** `caiogrossi-recommender-trainer`

**Volume Mounts:**
- `/app/models` (Read-Write access to model-pvc)

**Health Checks:**
- **Liveness Probe:** HTTP GET `/health` on port 50005
  - Initial Delay: 30s
  - Period: 10s
- **Readiness Probe:** HTTP GET `/health` on port 50005
  - Initial Delay: 10s
  - Period: 5s

**Resource Limits:**
- **Requests:** 512Mi memory, 250m CPU
- **Limits:** 1Gi memory, 500m CPU

### 3. Training Service (`service-training.yaml`)

Exposes the training service within the cluster.

**Specifications:**
- **Name:** `training-service`
- **Type:** `ClusterIP` (internal only)
- **Port Mapping:** `5005` (service) → `50005` (container)
- **Selector:** `app: caiogrossi-recommender-trainer`

### 4. Recommendation Service Deployment (`deployment-recommender.yaml`)

Runs the recommendation service that serves predictions using trained models.

**Specifications:**
- **Name:** `playlist-recommender-system`
- **Replicas:** `2` (scaled for availability)
- **Image:** `caiosgrossi/playlist-recommender-system:recommendation-service-0.1`
- **Container Port:** `50005`
- **App Label:** `caiogrossi-recommender`

**Volume Mounts:**
- `/app/models` (Read-Only access to model-pvc)

**Health Checks:**
- **Liveness Probe:** HTTP GET `/health` on port 50005
  - Initial Delay: 30s
  - Period: 10s
- **Readiness Probe:** HTTP GET `/health` on port 50005
  - Initial Delay: 10s
  - Period: 5s

**Resource Limits:**
- **Requests:** 512Mi memory, 250m CPU
- **Limits:** 1Gi memory, 500m CPU

### 5. Recommendation Service (`service-recommendation.yaml`)

Exposes the recommendation service within the cluster.

**Specifications:**
- **Name:** `recommendation-service`
- **Type:** `ClusterIP` (internal only)
- **Port Mapping:** `5006` (service) → `50005` (container)
- **Selector:** `app: caiogrossi-recommender`

### 6. Legacy Service (`service.yaml`)

 **Note:** This appears to be a legacy/unused service configuration.

**Specifications:**
- **Name:** `playlist-recommender-service`
- **Port Mapping:** `5008` → `5008`
- **Selector:** `app: caiogrossi-playlist-recommender` (no matching deployment)

**Status:** This service doesn't match any current deployment and may be outdated.

##  Prerequisites

Before deploying, ensure you have:

1. **Kubernetes Cluster Access**
   ```bash
   kubectl cluster-info
   ```

2. **Namespace Created**
   ```bash
   kubectl get namespace caiogrossi
   ```

3. **Storage Class Available**
   ```bash
   kubectl get storageclass default-storage-class-caiogrossi
   ```

4. **Persistent Volume Created**
   ```bash
   kubectl get pv project2-pv-caiogrossi
   ```

5. **Docker Images Available**
   - `caiosgrossi/playlist-recommender-system:training-service-0.1`
   - `caiosgrossi/playlist-recommender-system:recommendation-service-0.1`

##  Deployment Instructions

### Full Deployment

Deploy all components in the correct order:

```bash
# 1. Create namespace (if not exists)
kubectl create namespace caiogrossi

# 2. Deploy Persistent Volume Claim
kubectl apply -f pvc-models.yaml -n caiogrossi

# 3. Verify PVC is bound
kubectl get pvc -n caiogrossi

# 4. Deploy Training Service
kubectl apply -f deployment-training.yaml -n caiogrossi
kubectl apply -f service-training.yaml -n caiogrossi

# 5. Deploy Recommendation Service
kubectl apply -f deployment-recommender.yaml -n caiogrossi
kubectl apply -f service-recommendation.yaml -n caiogrossi

# 6. Verify all resources
kubectl get all -n caiogrossi
```

### Verify Deployment

```bash
# Check pods are running
kubectl get pods -n caiogrossi

# Check services
kubectl get svc -n caiogrossi

# Check PVC is bound
kubectl get pvc -n caiogrossi

# View logs for training service
kubectl logs -n caiogrossi -l app=caiogrossi-recommender-trainer --tail=50

# View logs for recommendation service
kubectl logs -n caiogrossi -l app=caiogrossi-recommender --tail=50
```

### Access Services

Since services are ClusterIP type, access them from within the cluster or use port-forwarding:

```bash
# Access training service
kubectl port-forward -n caiogrossi svc/training-service 5005:5005

# Access recommendation service
kubectl port-forward -n caiogrossi svc/recommendation-service 5006:5006
```

Then access via:
- Training Service: `http://localhost:5005`
- Recommendation Service: `http://localhost:5006`

##  Configuration Details

### Resource Allocation

Both services have identical resource configurations:

| Resource | Request | Limit |
|----------|---------|-------|
| Memory   | 512Mi   | 1Gi   |
| CPU      | 250m    | 500m  |

**Considerations:**
- Training service processes datasets and may need more resources during training
- Recommendation service handles concurrent requests and benefits from more replicas
- Adjust based on actual workload and cluster capacity

### High Availability

- **Recommendation Service:** 2 replicas for load balancing and fault tolerance
- **Training Service:** 1 replica (training is typically not parallelized)

### Storage

**Shared Volume Pattern:**
- Training service writes models with read-write access
- Recommendation service reads models with read-only access
- `ReadWriteMany` access mode enables this pattern

**Model Versioning:**
- Models are saved as `association_rules_v{version}.pkl`
- Metadata stored in `metadata.json`
- Recommendation service can detect and reload new models

### Health Checks

Both services implement health probes:

**Liveness Probe:**
- Ensures pod is restarted if unhealthy
- 30s initial delay allows for startup
- Checked every 10s

**Readiness Probe:**
- Controls traffic routing to the pod
- 10s initial delay for faster availability
- Checked every 5s

### Networking

**Port Configuration:**

| Service              | Service Port | Target Port | Container Port |
|----------------------|--------------|-------------|----------------|
| training-service     | 5005         | 50005       | 50005          |
| recommendation-service | 5006       | 50005       | 50005          |

**Note:** Both containers listen on port 50005, but services expose different external ports.

##  Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod -n caiogrossi <pod-name>

# Common issues:
# 1. Image pull errors - verify image exists in registry
# 2. PVC not bound - check PV and storage class
# 3. Resource constraints - check cluster capacity
```

### PVC Not Binding

```bash
# Check PVC status
kubectl describe pvc -n caiogrossi model-pvc

# Verify PV exists and matches selector
kubectl get pv project2-pv-caiogrossi

# Check if storage class exists
kubectl get storageclass default-storage-class-caiogrossi
```

### Health Check Failures

```bash
# View pod logs
kubectl logs -n caiogrossi <pod-name>

# Check if /health endpoint is responding
kubectl exec -n caiogrossi <pod-name> -- curl localhost:50005/health

# Common issues:
# 1. Application not starting correctly
# 2. Port mismatch
# 3. Insufficient startup time (adjust initialDelaySeconds)
```

### Service Connection Issues

```bash
# Test service DNS resolution
kubectl run -n caiogrossi test-pod --image=busybox --rm -it -- nslookup training-service

# Test service connectivity
kubectl run -n caiogrossi test-pod --image=curlimages/curl --rm -it -- curl http://training-service:5005/health

# Check endpoints
kubectl get endpoints -n caiogrossi
```

### Model Sharing Issues

```bash
# Verify volume is mounted
kubectl exec -n caiogrossi <pod-name> -- ls -la /app/models

# Check PVC is mounted to both services
kubectl get pods -n caiogrossi -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.volumes[*].persistentVolumeClaim.claimName}{"\n"}{end}'

# Verify read/write permissions
kubectl exec -n caiogrossi <training-pod-name> -- touch /app/models/test-file
kubectl exec -n caiogrossi <recommender-pod-name> -- ls /app/models/test-file
```

##  Update Procedures

### Update Training Service

```bash
# Update image version in deployment-training.yaml
kubectl apply -f deployment-training.yaml -n caiogrossi

# Monitor rollout
kubectl rollout status deployment/playlist-recommender-system-trainer -n caiogrossi

# Rollback if needed
kubectl rollout undo deployment/playlist-recommender-system-trainer -n caiogrossi
```

### Update Recommendation Service

```bash
# Update image version in deployment-recommender.yaml
kubectl apply -f deployment-recommender.yaml -n caiogrossi

# Monitor rollout (gradual with 2 replicas)
kubectl rollout status deployment/playlist-recommender-system -n caiogrossi

# Rollback if needed
kubectl rollout undo deployment/playlist-recommender-system -n caiogrossi
```

### Scale Services

```bash
# Scale recommendation service for higher load
kubectl scale deployment/playlist-recommender-system -n caiogrossi --replicas=3

# Scale down
kubectl scale deployment/playlist-recommender-system -n caiogrossi --replicas=2
```

##  Cleanup

### Remove All Resources

```bash
# Delete deployments
kubectl delete -f deployment-training.yaml -n caiogrossi
kubectl delete -f deployment-recommender.yaml -n caiogrossi

# Delete services
kubectl delete -f service-training.yaml -n caiogrossi
kubectl delete -f service-recommendation.yaml -n caiogrossi

# Delete PVC (caution: this deletes stored models)
kubectl delete -f pvc-models.yaml -n caiogrossi

# Verify cleanup
kubectl get all -n caiogrossi
```

### Keep Storage but Remove Services

```bash
# Delete only deployments and services (keep PVC)
kubectl delete -f deployment-training.yaml -n caiogrossi
kubectl delete -f deployment-recommender.yaml -n caiogrossi
kubectl delete -f service-training.yaml -n caiogrossi
kubectl delete -f service-recommendation.yaml -n caiogrossi
```