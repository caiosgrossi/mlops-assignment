# Kubernetes 

This directory contains all Kubernetes manifests for the music recommendation system. These manifests are automatically updated by GitHub Actions workflows whenever code changes or dataset updates occur.

## Manifest Files

### `configmap-dataset.yaml`
ConfigMap containing dataset configuration (URL, version, name). ConfigMaps are Kubernetes objects that store configuration data as key-value pairs, making it accessible to pods without hardcoding values in container images.

### `deployment-recommender.yaml`
Deployment manifest for the Flask API service that serves music recommendations. Defines the desired state for running API pods, including container images, resource limits, and health checks.

### `job-training.yaml`
Kubernetes Job manifest for the ML training service. Jobs create pods that run to completion and then terminate, perfect for batch processing tasks like model training.

### `pvc-models.yaml`
PersistentVolumeClaim for model storage. PVCs request persistent storage from the cluster, allowing trained models to persist across pod restarts and be shared between training and API services.

### `service-recommendation.yaml`
Service manifest that exposes the API deployment internally within the cluster. Services provide stable network endpoints for accessing pods.

## Automated Updates

All manifests are automatically modified by GitHub Actions workflows:

- **Code Changes**: When ML training code or API code is updated, workflows increment version numbers and update image tags in `job-training.yaml` and `deployment-recommender.yaml`
- **Dataset Changes**: When `datasets/dataset-url.txt` is modified, workflows update the ConfigMap with new dataset information and trigger training jobs

This GitOps approach ensures infrastructure changes are version-controlled and automatically applied without manual intervention.