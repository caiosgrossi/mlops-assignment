# Training Job (brief)

This directory contains the training job implementation used to generate association-rule models.

Key points
- The training job is designed to run as a Kubernetes `Job` (one-shot). The CI/CD workflow updates the job image and manifest when code or dataset changes.
- When the dataset URL (in `datasets/dataset-url.txt` or the dataset ConfigMap) changes, GitHub Actions updates the manifest and ArgoCD syncs the new job to the cluster.

Run locally (optional)
1. Build image:
```bash
cd project-delivery/ml-training
docker build -f ../docker/Dockerfile.training -t training-job:latest .
```
2. Run container (produces models under mounted directory):
```bash
docker run --rm \
  -v /path/to/models:/app/models \
  -e DATASET_URL='https://your-dataset.csv' \
  -e DATASET_VERSION='1.0' \
  -e DATASET_NAME='local-test' \
  training-job:latest python train_job.py
```

Notes
- In-cluster usage is preferred: the Kubernetes `job-training.yaml` manifest runs the same image with env vars from the dataset ConfigMap and mounts the PVC at `/app/models`.
- The job writes models and `metadata.json` to `/app/models` so the API can load the latest model.
- The repository's workflows automate building and tagging images; ArgoCD performs the sync when manifests are updated.
