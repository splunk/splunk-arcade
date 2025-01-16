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