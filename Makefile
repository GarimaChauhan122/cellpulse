.PHONY: dev test lint run docker kind monitor
dev: ; pip install -r requirements-dev.txt
test: ; pytest
lint: ; ruff check . && ruff format --check .
run: ; uvicorn app.main:app --reload --port 8080
docker: ; docker build -t cellpulse:local --build-arg GIT_SHA=$$(git rev-parse --short HEAD) .
kind: docker  ## local deploy to a kind cluster
	kind create cluster --name cellpulse || true
	kind load docker-image cellpulse:local --name cellpulse
	helm upgrade --install cellpulse helm/cellpulse --set image.repository=cellpulse --set image.tag=local --set image.pullPolicy=Never --atomic

monitor: ## app + simulator + Prometheus + Grafana (http://localhost:3000)
	docker compose up --build
