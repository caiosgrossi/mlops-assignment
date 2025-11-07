.PHONY: help build test lint clean run-local deploy-k8s

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-ml: ## Install ML service dependencies
	cd services/ml-service && pip install -r requirements.txt

install-backend: ## Install backend API dependencies
	cd services/backend-api && pip install -r requirements.txt

install: install-ml install-backend ## Install all dependencies

test-ml: ## Test ML service
	cd services/ml-service && pytest test_app.py -v --cov=app

test-backend: ## Test backend API
	cd services/backend-api && pytest test_app.py -v --cov=app

test: test-ml test-backend ## Run all tests

lint-ml: ## Lint ML service
	cd services/ml-service && flake8 app.py --max-line-length=100 --ignore=E501,W503

lint-backend: ## Lint backend API
	cd services/backend-api && flake8 app.py --max-line-length=100 --ignore=E501,W503

lint: lint-ml lint-backend ## Run all linters

run-ml: ## Run ML service locally
	cd services/ml-service && python app.py

run-backend: ## Run backend API locally (set ML_SERVICE_URL env var)
	cd services/backend-api && python app.py

run-frontend: ## Run frontend locally
	cd services/frontend && python -m http.server 3000

build: ## Build all Docker images
	docker-compose build

up: ## Start all services with Docker Compose
	docker-compose up

up-build: ## Build and start all services
	docker-compose up --build

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

build-ml: ## Build ML service Docker image
	docker build -t ml-service:latest services/ml-service/

build-backend: ## Build backend API Docker image
	docker build -t backend-api:latest services/backend-api/

build-frontend: ## Build frontend Docker image
	docker build -t frontend:latest services/frontend/

k8s-apply: ## Apply all Kubernetes manifests
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/ml-service.yaml
	kubectl apply -f k8s/backend-api.yaml
	kubectl apply -f k8s/frontend.yaml

k8s-delete: ## Delete all Kubernetes resources
	kubectl delete -f k8s/frontend.yaml --ignore-not-found
	kubectl delete -f k8s/backend-api.yaml --ignore-not-found
	kubectl delete -f k8s/ml-service.yaml --ignore-not-found
	kubectl delete -f k8s/namespace.yaml --ignore-not-found

k8s-status: ## Check Kubernetes deployment status
	kubectl get all -n playlist-recommender

k8s-logs-ml: ## View ML service logs in Kubernetes
	kubectl logs -f deployment/ml-service -n playlist-recommender

k8s-logs-backend: ## View backend API logs in Kubernetes
	kubectl logs -f deployment/backend-api -n playlist-recommender

k8s-logs-frontend: ## View frontend logs in Kubernetes
	kubectl logs -f deployment/frontend -n playlist-recommender

argocd-install: ## Install ArgoCD
	kubectl create namespace argocd
	kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

argocd-password: ## Get ArgoCD admin password
	kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo

argocd-deploy: ## Deploy application with ArgoCD
	kubectl apply -f k8s/.argocd/application.yaml

argocd-status: ## Check ArgoCD application status
	kubectl get applications -n argocd

format: ## Format Python code with black
	black services/ml-service/app.py services/backend-api/app.py

validate-k8s: ## Validate Kubernetes manifests
	@echo "Validating Kubernetes manifests..."
	@for file in k8s/*.yaml; do \
		echo "Checking $$file..."; \
		kubectl apply --dry-run=client -f $$file || exit 1; \
	done
	@echo "All manifests are valid!"
