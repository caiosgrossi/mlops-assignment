# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the Music Playlist Recommender System.

## Workflows

### 1. `ci-build-and-validate.yml`

**Triggers:** 
- Push to main branch
- Pull request to main branch

**Purpose:** Run tests and build Docker images

**Jobs:**
1. **test-validation** - Run CI and config tests
   - Validates K8s manifests
   - Validates dataset configuration
   - Duration: ~1-2 minutes

2. **build-training** - Build training service Docker image
   - Only runs if tests pass
   - Pushes to Docker Hub
   - Tags: `training-service-{SHA}` and `training-service-latest`
   - Duration: ~2-3 minutes

3. **build-recommendation** - Build recommendation service Docker image
   - Only runs if tests pass
   - Pushes to Docker Hub
   - Tags: `recommendation-service-{SHA}` and `recommendation-service-latest`
   - Duration: ~2-3 minutes

**Total Duration:** ~4-5 minutes

---

### 2. `deploy-verify.yml`

**Triggers:**
- After `ci-build-and-validate.yml` completes successfully

**Purpose:** Verify deployment health after ArgoCD sync

**Jobs:**
1. **wait-for-argocd** - Wait for ArgoCD to sync and pods to be ready
   - Polls pod status every 5 seconds
   - Timeout: 2 minutes
   - Checks both training and recommendation services

2. **verify-deployment** - Run post-deployment tests
   - Sets up port forwarding to services
   - Runs health checks
   - Verifies environment variables
   - Duration: ~1-2 minutes

**Total Duration:** ~2-3 minutes (after ArgoCD sync)

---

### 3. `dataset-config-check.yml`

**Triggers:**
- Changes to `datasets/**`
- Changes to `k8s/configmap-dataset.yaml`

**Purpose:** Validate dataset configuration changes

**Jobs:**
1. **validate-dataset-config** - Run dataset configuration tests
   - Validates URL format
   - Checks version follows semver
   - Verifies ConfigMap consistency
   - Tests URL accessibility
   - Duration: ~1 minute

**Total Duration:** ~1 minute

---

## Required Secrets

Configure these in repository settings: `Settings > Secrets and variables > Actions`

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `DOCKERHUB_USERNAME` | Docker Hub username | Your Docker Hub account username |
| `DOCKERHUB_TOKEN` | Docker Hub access token | Create at hub.docker.com/settings/security |
| `KUBECONFIG` | Base64-encoded kubeconfig | `cat ~/.kube/config \| base64 -w 0` |

### Setting up KUBECONFIG

```bash
# On your machine with kubectl configured
cat ~/.kube/config | base64 -w 0

# Copy the output and add it as a secret in GitHub
```

---

## Workflow Execution Flow

```
Developer pushes to main
         |
         v
ci-build-and-validate.yml starts
         |
         |--> test-validation (run tests)
         |
         v
    Tests pass?
         |
    Yes  |  No --> STOP (notify failure)
         |
         v
    Build Docker images (parallel)
         |--> build-training
         |--> build-recommendation
         |
         v
    Push images to Docker Hub
         |
         v
ArgoCD detects new images (~3 min)
         |
         v
ArgoCD syncs to cluster
         |
         v
deploy-verify.yml starts
         |
         |--> wait-for-argocd (wait for pods)
         |--> verify-deployment (run health checks)
         |
         v
    Tests pass?
         |
    Yes  |  No --> Alert (check logs)
         |
         v
DEPLOYMENT SUCCESSFUL
```

---

## Test Protection

**CRITICAL:** All tests use READ-ONLY operations

**Tests will NEVER:**
- Mount `/home/caiogrossi/project2-pv/` (production PVC)
- Call `POST /train` endpoint (would write models)
- Call `POST /recommend` with actual training
- Use `kubectl exec` (could modify files)

**Tests only use:**
- `kubectl get/describe` (read pod status)
- `GET /health` (health checks)
- `GET /dataset/info` (read environment variables)
- YAML file validation (local files)

---

## Monitoring Workflow Status

### GitHub UI
- Go to repository → Actions tab
- View workflow runs
- Check logs for failures

### Status Badges
Add to README.md:

```markdown
![CI Build](https://github.com/caiosgrossi/mlops-assignment/actions/workflows/ci-build-and-validate.yml/badge.svg)
![Deployment](https://github.com/caiosgrossi/mlops-assignment/actions/workflows/deploy-verify.yml/badge.svg)
```

---

## Troubleshooting

### Workflow not triggering
- Check workflow file syntax (YAML)
- Verify branch name is correct (`main`)
- Check repository permissions

### Docker build failing
- Verify Docker Hub secrets are set correctly
- Check Dockerfile syntax
- Review build logs in Actions tab

### Deployment tests failing
- Check if pods are actually running: `kubectl get pods -n caiogrossi`
- Verify KUBECONFIG secret is correct
- Check service endpoints are accessible
- Review pod logs: `kubectl logs -n caiogrossi <pod-name>`

### ArgoCD sync timeout
- Check ArgoCD UI for sync status
- Verify ArgoCD application is healthy
- Check for resource conflicts in cluster
- May need to increase timeout in workflow

---

## Local Testing

Test workflows locally before pushing:

```bash
# Run tests locally
cd tests
python3 run_tests.py -v

# Build Docker images locally
docker build -t training-service-test training-service/
docker build -t recommendation-service-test recommendation-service/

# Validate K8s manifests
cd k8s
for f in *.yaml; do yamllint $f; done
```

---

## Next Steps

1. Configure GitHub secrets (DOCKERHUB_USERNAME, DOCKERHUB_TOKEN, KUBECONFIG)
2. Push a commit to main to trigger the workflow
3. Monitor the Actions tab for execution
4. Verify ArgoCD syncs the new images
5. Check deployment verification passes

---

**Status:** Workflows ready for use  
**Last Updated:** November 14, 2025
