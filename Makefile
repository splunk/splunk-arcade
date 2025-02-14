.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

docker-lint: ## Run linters for all the arcade service images
	hadolint cabinet/Dockerfile
	hadolint player-router/Dockerfile
	hadolint portal/Dockerfile
	hadolint player-content/Dockerfile
	hadolint scoreboard/Dockerfile
	hadolint dev.go.Dockerfile
	hadolint dev.py.Dockerfile

# python deps should mostly be the same, but keeping requirements in their own packages for easy
# docker-ing
python-deps: ## Install the deps for all the python packages (for dev reasons only)
	python -m pip install -r cabinet/requirements.txt
	python -m pip install -r portal/requirements.txt
	python -m pip install -r player-content/requirements.txt
	python -m pip install -r scoreboard/requirements.txt
	python -m pip install -r requirements-dev.txt

python-fmt: ## Run formatter on all python bits
	venv/bin/python -m ruff check --select I --fix cabinet/
	venv/bin/python -m ruff check --select I --fix portal/
	venv/bin/python -m ruff check --select I --fix player-content/
	venv/bin/python -m ruff check --select I --fix scoreboard/
	venv/bin/python -m ruff format cabinet/
	venv/bin/python -m ruff format portal/
	venv/bin/python -m ruff format player-content/
	venv/bin/python -m ruff format scoreboard/

python-lint: python-fmt ## Run linter on all the python bits
	venv/bin/python -m ruff check cabinet/
	venv/bin/python -m ruff check portal/
	venv/bin/python -m ruff check player-content/
	venv/bin/python -m ruff check scoreboard/

build-tailwind: ## Builds tailwind css output files for ui components
	cd portal && npm run tailwind-build

clean-pvcs: ## Cleanup any pvcs for redis/postgres
	kubectl delete pvc \
		data-splunk-arcade-postgresql-0 \
		data-splunk-arcade-postgresql-primary-0 \
		data-splunk-arcade-postgresql-read-0 \
		data-splunk-arcade-postgresql-read-1 \
		data-splunk-arcade-postgresql-read-2 \
		data-splunk-arcade-postgresql-read-3 \
		data-splunk-arcade-postgresql-read-4 \
		redis-data-splunk-arcade-redis-master-0 \
		redis-data-splunk-arcade-redis-replicas-0 \
		redis-data-splunk-arcade-redis-replicas-1 \
		redis-data-splunk-arcade-redis-replicas-2 || true

clean-players: ## Cleanup any created player deployments
	kubectl get deployments -l "app.kubernetes.io/name=splunk-arcade-cabinet" \
		--no-headers -o custom-columns=":metadata.name" \
		| xargs -I {} kubectl delete deployment {}
	kubectl get services -l "app.kubernetes.io/name=splunk-arcade-cabinet" \
		--no-headers -o custom-columns=":metadata.name" \
		| xargs -I {} kubectl delete service {}
	kubectl get jobs -l "app.kubernetes.io/name=splunk-arcade-player-cloud" \
		--no-headers -o custom-columns=":metadata.name" \
		| xargs -I {} kubectl delete jobs {}

clean-hanging-configmaps-and-secrets: ## Cleans any secrets/configmaps that didnt get cleaned up
	kubectl get configmaps -l "app.kubernetes.io/name=splunk-arcade-player-cloud-outputs" \
		--no-headers -o custom-columns=":metadata.name" \
		| xargs -I {} kubectl delete configmaps {}
	kubectl get secrets -l "app.kubernetes.io/name=splunk-arcade-player-cloud-state" \
		--no-headers -o custom-columns=":metadata.name" \
		| xargs -I {} kubectl delete secrets {}


clean-all: clean-players clean-hanging-configmaps-and-secrets clean-pvcs ## Cleanup all cruft from cluster