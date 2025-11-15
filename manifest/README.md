# ArgoCD

This directory contains the ArgoCD App-of-Apps manifests (there are 2) that implement a hierarchical GitOps deployment pattern.

## Architecture Overview

The App-of-Apps pattern creates a parent ArgoCD Application that manages child applications, enabling centralized control over multiple Kubernetes resources.

## Key Benefits

- **Automatic Synchronization**: Changes to the parent application manifest automatically sync all child applications without manual redeployment
- **Resource Efficiency**: No additional Kubernetes resources required beyond the standard ArgoCD setup
- **Centralized Management**: Single point of control for managing complex multi-service deployments
- **GitOps Compliance**: All changes are version-controlled and automatically applied

## Manifest Structure

- `manifest-argoapp.yaml`: Parent application that defines and manages child applications
- `manifest-argosystem.yaml`: ArgoCD system configuration for the namespace

## How It Works

1. The parent application (`manifest-argoapp.yaml`) references child application manifests
2. ArgoCD monitors the parent application for changes
3. When the parent manifest is updated, ArgoCD automatically syncs all referenced child applications
4. No manual intervention or additional deployments required

This architecture enables seamless updates to the entire application stack through Git commits alone.