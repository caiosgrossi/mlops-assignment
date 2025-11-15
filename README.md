# Playlist Recommender — Repo Overview (concise)

This repository implements a GitOps MLOps pipeline for a playlist recommender using association rules.

Core idea
- Any change to the application code (API or training) or to the dataset URL triggers an automated workflow (GitHub Actions) that builds a new training image or API image and updates the Kubernetes manifests.
- ArgoCD (App-of-Apps) watches the manifests and automatically syncs the cluster, causing the training job to run (one-shot) and the API to pick up the new model. No manual redeploy is required.

Quick start options

1) Quick test with the client (no cluster required)
- Use the provided `client.sh` to call the API running locally or in-cluster:
```bash
./client.sh "Don't Let Me Down"
```

2) Deploy everything in-cluster (recommended)
- Apply ArgoCD system and app manifests to let ArgoCD manage the stack:
```bash
kubectl apply -f manifest/manifest-argosystem.yaml
kubectl apply -f manifest/manifest-argoapp.yaml
```
- ArgoCD will create the child applications and begin syncing. The pipelines will build images and update manifests when code or dataset changes are pushed to Git.

Build & run Docker images locally
- Build API image:
```bash
cd project-delivery/flask-api
docker build -f ../docker/Dockerfile.api -t recommendation-api:latest .
```
- Build training image:
```bash
cd project-delivery/ml-training
docker build -f ../docker/Dockerfile.training -t training-job:latest .
```
- Run the API (mount host models dir):
```bash
docker run -d --name recommendation-api -p 50005:50005 \
  -v /path/to/models:/app/models:ro recommendation-api:latest
```
- Run the training image locally for testing (writes models to host dir):
```bash
docker run --rm -v /path/to/models:/app/models \
  -e DATASET_URL='https://...' \
  training-job:latest python train_job.py
```

Models location
- In the cluster the PVC mounted at `/app/models` is backed by the host path `/home/caiogrossi/project2-pv/production`. Model artifacts and `metadata.json` are written to that location and are available to the API via the mount.

Where to look
- Kubernetes manifests: `project-delivery/kubernetes/` (also `k8s/` for the working manifests)
- ArgoCD manifests: `manifest/manifest-argoapp.yaml`, `manifest/manifest-argosystem.yaml`
- CI workflows: `.github/workflows/` (they contain image build and manifest update steps)

Why this matters
- The repo implements a full GitOps loop: change -> CI builds -> manifest update -> ArgoCD sync -> training job -> new model -> API serves updated model.
- This minimizes manual operations and keeps production reproducible and auditable.
