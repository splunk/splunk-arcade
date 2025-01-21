.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

docker-lint: ## Run linters for all the arcade service images
	hadolint cabinet/Dockerfile
	hadolint player-router/Dockerfile
	hadolint portal/Dockerfile
	hadolint quiz/Dockerfile
	hadolint scoreboard/Dockerfile
	hadolint dev.go.Dockerfile
	hadolint dev.py.Dockerfile

# python deps should mostly be the same, but keeping requirements in their own packages for easy
# docker-ing
python-deps: ## Install the deps for all the python packages (for dev reasons only)
	python -m pip install -r cabinet/requirements.txt
	python -m pip install -r portal/requirements.txt
	python -m pip install -r quiz/requirements.txt
	python -m pip install -r scoreboard/requirements.txt
	python -m pip install -r requirements-dev.txt

python-fmt: ## Run formatter on all python bits
	venv/bin/python -m ruff check --select I --fix cabinet/
	venv/bin/python -m ruff check --select I --fix portal/
	venv/bin/python -m ruff check --select I --fix quiz/
	venv/bin/python -m ruff check --select I --fix scoreboard/
	venv/bin/python -m ruff format cabinet/
	venv/bin/python -m ruff format portal/
	venv/bin/python -m ruff format quiz/
	venv/bin/python -m ruff format scoreboard/

python-lint: python-fmt ## Run linter on all the python bits
	venv/bin/python -m ruff check cabinet/
	venv/bin/python -m ruff check portal/
	venv/bin/python -m ruff check quiz/
	venv/bin/python -m ruff check scoreboard/

clean-pvcs: ## Cleanup any pvcs for redis/postgres
	kubectl delete pvc \
		data-splunk-arcade-postgresql-0 \
		redis-data-splunk-arcade-redis-master-0 \
		redis-data-splunk-arcade-redis-replicas-0 \
		redis-data-splunk-arcade-redis-replicas-1 \
		redis-data-splunk-arcade-redis-replicas-2 || true

clean-players: ## Cleanup any created player deployments
	kubectl get deployments -l "app.kubernetes.io/name=splunk-arcade-player" \
		--no-headers -o custom-columns=":metadata.name" \
		| xargs -I {} kubectl delete deployment {}
	kubectl get services -l "app.kubernetes.io/name=splunk-arcade-player" \
		--no-headers -o custom-columns=":metadata.name" \
		| xargs -I {} kubectl delete service {}

clean-all: clean-players clean-pvcs ## Cleanup all cruft from cluster