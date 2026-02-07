.PHONY: up down logs migrate test lint

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

migrate:
	docker-compose exec app alembic upgrade head

migrate-create:
	docker-compose exec app alembic revision --autogenerate -m "$(msg)"

test:
	pytest tests/ -v --cov=src

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/

seed:
	docker-compose exec app python scripts/seed_data.py

init-qdrant:
	docker-compose exec app python scripts/init_qdrant.py

pull-model:
	docker-compose exec ollama ollama pull llama3:8b-instruct-q4_K_M
