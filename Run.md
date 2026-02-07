Buoc 1: Tao file .env

  cd /Users/nhdandz/Documents/code/RRI
  cp .env.example .env

  Sau do mo file .env va cap nhat cac API key:
  Key: GITHUB_TOKEN
  Bat buoc?: Co
  Cach lay: GitHub > Settings > Developer settings > Personal access tokens > Generate new token
    (classic), chon scope public_repo
  ────────────────────────────────────────
  Key: OPENAI_API_KEY
  Bat buoc?: Khong (neu dung Ollama local)
  Cach lay: https://platform.openai.com/api-keys
  ────────────────────────────────────────
  Key: SEMANTIC_SCHOLAR_API_KEY
  Bat buoc?: Khong (tang rate limit)
  Cach lay: https://www.semanticscholar.org/product/api
  ────────────────────────────────────────
  Key: HUGGINGFACE_TOKEN
  Bat buoc?: Khong (tang rate limit)
  Cach lay: https://huggingface.co/settings/tokens
  Toi thieu ban chi can GITHUB_TOKEN la chay duoc. He thong se dung Ollama (LLM local) thay vi OpenAI.

  Buoc 2: Khoi dong tat ca services

  # Khoi dong toan bo he thong (lan dau se build image, mat 5-10 phut)
  docker-compose up -d

  Kiem tra tat ca services dang chay:

  docker-compose ps

  Ban se thay 8 services:
  ┌──────────┬───────┬─────────────────────────────────┐
  │ Service  │ Port  │            Chuc nang            │
  ├──────────┼───────┼─────────────────────────────────┤
  │ postgres │ 5432  │ Database chinh                  │
  ├──────────┼───────┼─────────────────────────────────┤
  │ redis    │ 6379  │ Cache & message broker          │
  ├──────────┼───────┼─────────────────────────────────┤
  │ qdrant   │ 6333  │ Vector database                 │
  ├──────────┼───────┼─────────────────────────────────┤
  │ ollama   │ 11434 │ Local LLM                       │
  ├──────────┼───────┼─────────────────────────────────┤
  │ app      │ 8000  │ FastAPI backend                 │
  ├──────────┼───────┼─────────────────────────────────┤
  │ worker   │ -     │ Celery worker (background jobs) │
  ├──────────┼───────┼─────────────────────────────────┤
  │ beat     │ -     │ Celery beat (scheduled tasks)   │
  ├──────────┼───────┼─────────────────────────────────┤
  │ frontend │ 3000  │ Next.js dashboard               │
  └──────────┴───────┴─────────────────────────────────┘
  Buoc 3: Pull LLM model cho Ollama

  # Download model llama3 (~4.7GB, mat vai phut)
  make pull-model

  Hoac:
  docker-compose exec ollama ollama pull llama3:8b-instruct-q4_K_M

  Buoc 4: Chay database migration

  # Tao database migration
  docker-compose exec app alembic revision --autogenerate -m "initial"

  # Apply migration
  make migrate

  Hoac:
  docker-compose exec app alembic upgrade head

  Buoc 5: Khoi tao Qdrant collections

  make init-qdrant

  Buoc 6: Seed du lieu mau (tuy chon)

  make seed

  Buoc 7: Truy cap he thong
  ┌─────────────────────────────────┬────────────────────────────┐
  │               URL               │         Giao dien          │
  ├─────────────────────────────────┼────────────────────────────┤
  │ http://localhost:3000           │ Frontend Dashboard         │
  ├─────────────────────────────────┼────────────────────────────┤
  │ http://localhost:8000           │ Backend API                │
  ├─────────────────────────────────┼────────────────────────────┤
  │ http://localhost:8000/docs      │ Swagger API docs (tu dong) │
  ├─────────────────────────────────┼────────────────────────────┤
  │ http://localhost:6333/dashboard │ Qdrant vector DB UI        │
  └─────────────────────────────────┴────────────────────────────┘
  ---
  Cac lenh huu ich

  # Xem logs tat ca services
  make logs

  # Xem logs 1 service cu the
  docker-compose logs -f app
  docker-compose logs -f worker

  # Dung he thong
  make down

  # Dung va xoa data (reset hoan toan)
  docker-compose down -v

  # Rebuild sau khi sua code
  docker-compose up -d --build app
  docker-compose up -d --build frontend

  Xu ly loi thuong gap

  1. Port da bi chiem:
  # Kiem tra port 8000/3000/5432 co bi dung chua
  lsof -i :8000
  # Neu bi chiem, dung process do hoac doi port trong docker-compose.yml

  2. Ollama het RAM:
  - Giam concurrency=4 trong docker-compose (worker command) xuong concurrency=2
  - Hoac dung OpenAI thay vi Ollama: set OPENAI_API_KEY trong .env

  3. Database connection refused:
  # Doi postgres khoi dong xong roi moi chay migrate
  docker-compose up -d postgres
  sleep 5
  make migrate

  4. Frontend build loi:
  # Cai dependencies truoc khi build
  cd frontend && npm install && cd ..
  docker-compose up -d --build frontend

✻ Sautéed for 41s