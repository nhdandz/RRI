# OSINT Research Automation System

## 🎯 Project Overview

Hệ thống tự động thu thập, phân tích và tổng hợp thông tin từ các nguồn nghiên cứu khoa học (ArXiv, Semantic Scholar) và mã nguồn (GitHub, Hugging Face), với khả năng:

- **Thu thập tự động** papers và repositories mới nhất
- **Liên kết Paper ↔ Code** với confidence scoring
- **Phân tích xu hướng** (trending technologies, SOTA shifts)
- **RAG-based Q&A** trên knowledge base đã thu thập
- **Báo cáo tự động** weekly digest, tech radar
- **Hỗ trợ tiếng Việt** (VAST journals, Vietnamese NLP)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ORCHESTRATION LAYER                              │
│                         Celery Beat + APScheduler                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Daily Jobs  │  │ Hourly Jobs │  │ Weekly Jobs │  │ On-demand   │        │
│  │ (Papers)    │  │ (Trending)  │  │ (Reports)   │  │ (User req)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            COLLECTION LAYER                                 │
│                                                                             │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │  ArXiv    │ │  GitHub   │ │ Semantic  │ │ Hugging   │ │  Vietnam  │    │
│  │ Collector │ │ Collector │ │ Scholar   │ │   Face    │ │  Sources  │    │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘    │
│        │             │             │             │             │           │
│        │    ┌────────┴─────────────┴─────────────┴─────────────┘           │
│        │    │                                                              │
│        ▼    ▼                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  Rate Limiter   │  │  Retry Handler  │  │ Circuit Breaker │            │
│  │  (per source)   │  │  (exp backoff)  │  │                 │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MESSAGE QUEUE (Redis)                              │
│                                                                             │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│    │ raw_papers   │  │ raw_repos    │  │ process_queue│  │ alert_queue  │  │
│    │    queue     │  │    queue     │  │              │  │              │  │
│    └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROCESSING LAYER                                  │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Classifier    │  │   Summarizer    │  │ Entity Extractor│             │
│  │    Worker       │  │     Worker      │  │     Worker      │             │
│  │  (Llama-3-8B)   │  │ (Llama/GPT-4o)  │  │  (Llama + NER)  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Paper-Code     │  │    Trending     │  │   Embedding     │             │
│  │    Linker       │  │   Calculator    │  │   Generator     │             │
│  │                 │  │                 │  │ (BGE/PhoBERT)   │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STORAGE LAYER                                    │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   PostgreSQL    │  │     Qdrant      │  │      Redis      │             │
│  │                 │  │                 │  │                 │             │
│  │  • papers       │  │  • paper_embeds │  │  • cache        │             │
│  │  • repositories │  │  • repo_embeds  │  │  • rate_limits  │             │
│  │  • paper_repo   │  │  • chunk_embeds │  │  • sessions     │             │
│  │  • metrics      │  │                 │  │  • leaderboards │             │
│  │  • alerts       │  │                 │  │                 │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                      │
│                                                                             │
│                        ┌─────────────────┐                                  │
│                        │    FastAPI      │                                  │
│                        │    Backend      │                                  │
│                        └────────┬────────┘                                  │
│                                 │                                           │
│          ┌──────────────────────┼──────────────────────┐                   │
│          ▼                      ▼                      ▼                   │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐               │
│  │   Dashboard   │    │   RAG Chat    │    │    Export     │               │
│  │   (Next.js)   │    │   Interface   │    │   Service     │               │
│  └───────────────┘    └───────────────┘    └───────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Language** | Python | 3.11+ | Main backend |
| **Async HTTP** | httpx | 0.27+ | Async API calls |
| **Task Queue** | Celery | 5.3+ | Background jobs |
| **Message Broker** | Redis | 7.0+ | Queue + Cache |
| **SQL Database** | PostgreSQL | 16+ | Structured data |
| **Vector Database** | Qdrant | 1.9+ | Embeddings |
| **ORM** | SQLAlchemy | 2.0+ | Async ORM |
| **API Framework** | FastAPI | 0.110+ | REST API |
| **LLM Local** | vLLM / Ollama | latest | Local inference |
| **LLM Cloud** | OpenAI | gpt-4o | Complex tasks |
| **Embeddings** | sentence-transformers | 2.5+ | Text embeddings |
| **Frontend** | Next.js | 14+ | Dashboard |
| **UI Components** | shadcn/ui | latest | UI library |
| **Charts** | Apache ECharts | 5.5+ | Visualizations |
| **Containerization** | Docker Compose | 2.24+ | Development |

---

## 📁 Project Structure

```
osint-research/
│
├── docker-compose.yml              # All services
├── docker-compose.dev.yml          # Dev overrides
├── Dockerfile                      # Main app image
├── pyproject.toml                  # Python dependencies
├── alembic.ini                     # DB migrations config
├── .env.example                    # Environment template
├── Makefile                        # Common commands
│
├── src/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry
│   │
│   ├── core/                       # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py               # Settings (Pydantic)
│   │   ├── logging.py              # Structured logging
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── constants.py            # Enums, constants
│   │
│   ├── collectors/                 # Data collection
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract collector
│   │   ├── arxiv.py                # ArXiv API
│   │   ├── github.py               # GitHub GraphQL
│   │   ├── semantic_scholar.py     # S2 API
│   │   ├── huggingface.py          # HF Hub API
│   │   ├── papers_with_code.py     # PWC API
│   │   ├── openal ex.py             # OpenAlex API
│   │   └── vietnam/
│   │       ├── __init__.py
│   │       ├── ojs_client.py       # OJS API client
│   │       └── sources.py          # VN source configs
│   │
│   ├── processors/                 # Data processing
│   │   ├── __init__.py
│   │   ├── classifier.py           # Topic classification
│   │   ├── summarizer.py           # Paper summarization
│   │   ├── entity_extractor.py     # NER extraction
│   │   ├── paper_code_linker.py    # Paper↔Code matching
│   │   ├── tech_analyzer.py        # Tech stack analysis
│   │   ├── trending.py             # Score calculation
│   │   ├── embedding.py            # Vector generation
│   │   └── vietnamese/
│   │       ├── __init__.py
│   │       ├── tokenizer.py        # VN word segmentation
│   │       └── ner.py              # VN entity extraction
│   │
│   ├── storage/                    # Data layer
│   │   ├── __init__.py
│   │   ├── database.py             # DB connection
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── paper.py
│   │   │   ├── repository.py
│   │   │   ├── link.py
│   │   │   ├── metrics.py
│   │   │   └── alert.py
│   │   ├── repositories/           # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── paper_repo.py
│   │   │   ├── github_repo.py
│   │   │   └── metrics_repo.py
│   │   ├── vector/
│   │   │   ├── __init__.py
│   │   │   └── qdrant_client.py
│   │   └── cache/
│   │       ├── __init__.py
│   │       └── redis_client.py
│   │
│   ├── workers/                    # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py           # Celery config
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── collection.py       # Collection tasks
│   │   │   ├── processing.py       # Processing tasks
│   │   │   ├── reporting.py        # Report generation
│   │   │   └── alerts.py           # Alert tasks
│   │   └── schedules.py            # Beat schedules
│   │
│   ├── llm/                        # LLM integration
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract LLM client
│   │   ├── ollama_client.py        # Local Ollama
│   │   ├── vllm_client.py          # Local vLLM
│   │   ├── openai_client.py        # OpenAI API
│   │   ├── prompts/                # Prompt templates
│   │   │   ├── __init__.py
│   │   │   ├── classification.py
│   │   │   ├── summarization.py
│   │   │   ├── extraction.py
│   │   │   └── analysis.py
│   │   └── router.py               # LLM routing logic
│   │
│   ├── rag/                        # RAG system
│   │   ├── __init__.py
│   │   ├── retriever.py            # Hybrid retrieval
│   │   ├── reranker.py             # Cross-encoder
│   │   ├── generator.py            # Answer generation
│   │   └── pipeline.py             # Full RAG pipeline
│   │
│   ├── api/                        # FastAPI routes
│   │   ├── __init__.py
│   │   ├── deps.py                 # Dependencies
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── papers.py
│   │   │   ├── repositories.py
│   │   │   ├── search.py
│   │   │   ├── trending.py
│   │   │   ├── reports.py
│   │   │   ├── chat.py
│   │   │   ├── alerts.py
│   │   │   └── health.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── paper.py
│   │       ├── repository.py
│   │       ├── search.py
│   │       └── report.py
│   │
│   └── services/                   # Business logic
│       ├── __init__.py
│       ├── paper_service.py
│       ├── repo_service.py
│       ├── link_service.py
│       ├── trending_service.py
│       ├── report_service.py
│       └── export_service.py
│
├── frontend/                       # Next.js app
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                # Dashboard home
│   │   ├── papers/
│   │   │   ├── page.tsx            # Papers list
│   │   │   └── [id]/page.tsx       # Paper detail
│   │   ├── repos/
│   │   │   ├── page.tsx
│   │   │   └── [id]/page.tsx
│   │   ├── trending/
│   │   │   └── page.tsx            # Trending dashboard
│   │   ├── tech-radar/
│   │   │   └── page.tsx            # Tech radar view
│   │   ├── chat/
│   │   │   └── page.tsx            # RAG chat interface
│   │   └── reports/
│   │       └── page.tsx            # Reports list
│   ├── components/
│   │   ├── ui/                     # shadcn components
│   │   ├── charts/
│   │   │   ├── TrendingChart.tsx
│   │   │   ├── TechRadar.tsx
│   │   │   └── CitationGraph.tsx
│   │   ├── papers/
│   │   ├── repos/
│   │   └── layout/
│   └── lib/
│       ├── api.ts                  # API client
│       └── utils.ts
│
├── migrations/                     # Alembic migrations
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_collectors/
│   │   ├── test_processors/
│   │   └── test_services/
│   ├── integration/
│   │   ├── test_api/
│   │   └── test_workers/
│   └── e2e/
│
├── scripts/
│   ├── seed_data.py                # Initial data
│   ├── backfill_embeddings.py      # Backfill vectors
│   └── export_report.py            # Manual export
│
└── docs/
    ├── api.md                      # API documentation
    ├── deployment.md               # Deployment guide
    └── contributing.md
```

---

## 🗄️ Database Schema

### PostgreSQL Tables

```sql
-- ============================================
-- PAPERS TABLE
-- ============================================
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identifiers
    arxiv_id VARCHAR(20) UNIQUE,
    doi VARCHAR(100) UNIQUE,
    semantic_scholar_id VARCHAR(50),
    
    -- Basic info
    title TEXT NOT NULL,
    title_normalized VARCHAR(500),  -- lowercase, no special chars
    abstract TEXT,
    summary TEXT,                    -- LLM generated 3-line summary
    
    -- Authors (JSONB array)
    authors JSONB DEFAULT '[]',
    -- Format: [{"name": "...", "affiliation": "...", "email": "..."}]
    
    -- Classification
    categories VARCHAR(50)[],        -- ["cs.AI", "cs.CL"]
    topics VARCHAR(100)[],           -- LLM classified topics
    keywords VARCHAR(100)[],
    
    -- Dates
    published_date DATE,
    updated_date DATE,
    
    -- Source
    source VARCHAR(50) NOT NULL,     -- arxiv, semantic_scholar, ojs_vietnam
    source_url TEXT,
    pdf_url TEXT,
    
    -- Metrics (denormalized for fast queries)
    citation_count INTEGER DEFAULT 0,
    influential_citation_count INTEGER DEFAULT 0,
    
    -- Processing status
    is_processed BOOLEAN DEFAULT FALSE,
    is_relevant BOOLEAN,             -- NULL = not classified yet
    relevance_score FLOAT,
    
    -- Vietnamese specific
    is_vietnamese BOOLEAN DEFAULT FALSE,
    vietnam_entities JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_papers_arxiv_id ON papers(arxiv_id);
CREATE INDEX idx_papers_published_date ON papers(published_date DESC);
CREATE INDEX idx_papers_categories ON papers USING GIN(categories);
CREATE INDEX idx_papers_topics ON papers USING GIN(topics);
CREATE INDEX idx_papers_is_relevant ON papers(is_relevant) WHERE is_relevant = TRUE;

-- ============================================
-- REPOSITORIES TABLE
-- ============================================
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identifiers
    github_id BIGINT UNIQUE,
    full_name VARCHAR(200) NOT NULL UNIQUE,  -- owner/repo
    
    -- Basic info
    name VARCHAR(100) NOT NULL,
    owner VARCHAR(100) NOT NULL,
    description TEXT,
    readme_content TEXT,
    readme_summary TEXT,             -- LLM generated
    
    -- URLs
    html_url TEXT NOT NULL,
    clone_url TEXT,
    homepage_url TEXT,
    
    -- Tech stack
    primary_language VARCHAR(50),
    languages JSONB DEFAULT '{}',    -- {"Python": 80, "JavaScript": 20}
    topics VARCHAR(100)[],
    
    -- Dependencies (parsed from requirements.txt, package.json)
    dependencies JSONB DEFAULT '{}',
    frameworks VARCHAR(100)[],       -- ["pytorch", "transformers"]
    
    -- Metrics (current)
    stars_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    watchers_count INTEGER DEFAULT 0,
    open_issues_count INTEGER DEFAULT 0,
    
    -- Activity
    last_commit_at TIMESTAMPTZ,
    last_release_at TIMESTAMPTZ,
    last_release_tag VARCHAR(50),
    commit_count_30d INTEGER DEFAULT 0,
    
    -- Quality indicators
    has_readme BOOLEAN DEFAULT FALSE,
    has_license BOOLEAN DEFAULT FALSE,
    has_tests BOOLEAN DEFAULT FALSE,
    has_docker BOOLEAN DEFAULT FALSE,
    has_ci BOOLEAN DEFAULT FALSE,
    
    -- Processing
    is_processed BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    repo_created_at TIMESTAMPTZ,
    repo_updated_at TIMESTAMPTZ
);

CREATE INDEX idx_repos_full_name ON repositories(full_name);
CREATE INDEX idx_repos_stars ON repositories(stars_count DESC);
CREATE INDEX idx_repos_language ON repositories(primary_language);
CREATE INDEX idx_repos_topics ON repositories USING GIN(topics);
CREATE INDEX idx_repos_frameworks ON repositories USING GIN(frameworks);

-- ============================================
-- PAPER-REPO LINKS TABLE
-- ============================================
CREATE TABLE paper_repo_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    repo_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Link metadata
    link_type VARCHAR(50) NOT NULL,  -- official, community, mentioned, inferred
    confidence_score FLOAT NOT NULL, -- 0.0 - 1.0
    
    -- Evidence (why we think they're linked)
    evidence JSONB DEFAULT '{}',
    -- Format: {
    --   "author_match": 0.8,
    --   "readme_contains_arxiv": true,
    --   "papers_with_code": true,
    --   "huggingface_link": false,
    --   "timing_score": 0.7
    -- }
    
    -- Source of link discovery
    discovered_via VARCHAR(50),      -- pdf_extraction, pwc, huggingface, manual
    
    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ,
    verified_by VARCHAR(100),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(paper_id, repo_id)
);

CREATE INDEX idx_links_paper ON paper_repo_links(paper_id);
CREATE INDEX idx_links_repo ON paper_repo_links(repo_id);
CREATE INDEX idx_links_confidence ON paper_repo_links(confidence_score DESC);
CREATE INDEX idx_links_type ON paper_repo_links(link_type);

-- ============================================
-- METRICS HISTORY TABLE
-- ============================================
CREATE TABLE metrics_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference
    entity_type VARCHAR(20) NOT NULL,  -- paper, repository
    entity_id UUID NOT NULL,
    
    -- Metrics snapshot
    metrics JSONB NOT NULL,
    -- For papers: {"citations": 100, "influential_citations": 20}
    -- For repos: {"stars": 500, "forks": 50, "open_issues": 10}
    
    -- Calculated velocities
    velocity_1d FLOAT,               -- change in last 24h
    velocity_7d FLOAT,               -- change in last 7 days
    velocity_30d FLOAT,              -- change in last 30 days
    
    recorded_at DATE NOT NULL,
    
    UNIQUE(entity_type, entity_id, recorded_at)
);

CREATE INDEX idx_metrics_entity ON metrics_history(entity_type, entity_id);
CREATE INDEX idx_metrics_date ON metrics_history(recorded_at DESC);

-- ============================================
-- TRENDING SCORES TABLE
-- ============================================
CREATE TABLE trending_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    entity_type VARCHAR(20) NOT NULL,
    entity_id UUID NOT NULL,
    
    -- Component scores
    activity_score FLOAT DEFAULT 0,
    community_score FLOAT DEFAULT 0,
    academic_score FLOAT DEFAULT 0,
    recency_score FLOAT DEFAULT 0,
    
    -- Combined score
    total_score FLOAT NOT NULL,
    
    -- Ranking within category
    category VARCHAR(100),           -- llm, rag, computer-vision, etc.
    rank_in_category INTEGER,
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(entity_type, entity_id, period_start)
);

CREATE INDEX idx_trending_score ON trending_scores(total_score DESC);
CREATE INDEX idx_trending_category ON trending_scores(category, rank_in_category);

-- ============================================
-- ALERTS TABLE
-- ============================================
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    alert_type VARCHAR(50) NOT NULL,
    -- Types: sota_shift, new_trending, release_update, milestone_reached
    
    -- Related entities
    entity_type VARCHAR(20),
    entity_id UUID,
    related_entity_id UUID,          -- e.g., the challenger repo
    
    -- Alert content
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity VARCHAR(20) DEFAULT 'info',  -- info, warning, critical
    
    -- Additional data
    metadata JSONB DEFAULT '{}',
    
    -- Status
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMPTZ,
    sent_channels VARCHAR(50)[],     -- ["slack", "email", "telegram"]
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX idx_alerts_unsent ON alerts(is_sent) WHERE is_sent = FALSE;

-- ============================================
-- CRAWL JOBS TABLE (for monitoring)
-- ============================================
CREATE TABLE crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    source VARCHAR(50) NOT NULL,
    job_type VARCHAR(50) NOT NULL,   -- full, incremental, backfill
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    -- pending, running, completed, failed, cancelled
    
    -- Progress
    total_items INTEGER,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Error tracking
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    
    -- Parameters used
    params JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_crawl_jobs_source ON crawl_jobs(source, status);
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);

-- ============================================
-- API RATE LIMITS TRACKING
-- ============================================
CREATE TABLE api_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    api_name VARCHAR(50) NOT NULL UNIQUE,
    
    -- Current limits
    requests_remaining INTEGER,
    requests_limit INTEGER,
    reset_at TIMESTAMPTZ,
    
    -- Daily tracking
    requests_today INTEGER DEFAULT 0,
    last_request_at TIMESTAMPTZ,
    
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- USER SUBSCRIPTIONS (for alerts)
-- ============================================
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- User identification (can be email, user_id, etc.)
    subscriber_id VARCHAR(200) NOT NULL,
    subscriber_type VARCHAR(50) DEFAULT 'email',
    
    -- What to subscribe to
    subscription_type VARCHAR(50) NOT NULL,
    -- Types: topic, paper, repo, author, keyword
    
    target_value VARCHAR(500) NOT NULL,
    -- e.g., "llm", "arxiv:2401.12345", "github:langchain-ai/langchain"
    
    -- Notification preferences
    channels VARCHAR(50)[] DEFAULT ARRAY['email'],
    frequency VARCHAR(20) DEFAULT 'daily',  -- instant, daily, weekly
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(subscriber_id, subscription_type, target_value)
);

CREATE INDEX idx_subs_subscriber ON subscriptions(subscriber_id);
CREATE INDEX idx_subs_target ON subscriptions(subscription_type, target_value);
```

### Qdrant Collections

```python
# Collection configurations for Qdrant

COLLECTIONS = {
    "papers": {
        "vectors": {
            "abstract": {
                "size": 768,  # BGE-base dimension
                "distance": "Cosine"
            }
        },
        "payload_schema": {
            "arxiv_id": "keyword",
            "title": "text",
            "categories": "keyword[]",
            "topics": "keyword[]",
            "published_date": "datetime",
            "citation_count": "integer",
            "is_vietnamese": "bool"
        }
    },
    
    "repositories": {
        "vectors": {
            "readme": {
                "size": 768,
                "distance": "Cosine"
            }
        },
        "payload_schema": {
            "full_name": "keyword",
            "description": "text",
            "primary_language": "keyword",
            "topics": "keyword[]",
            "frameworks": "keyword[]",
            "stars_count": "integer"
        }
    },
    
    "chunks": {  # For RAG - chunked content
        "vectors": {
            "content": {
                "size": 768,
                "distance": "Cosine"
            }
        },
        "payload_schema": {
            "source_type": "keyword",  # paper, repo
            "source_id": "keyword",
            "chunk_index": "integer",
            "content": "text"
        }
    }
}
```

---

## 📦 Module Specifications

### 1. Collectors Module

#### Base Collector (Abstract)

```python
# src/collectors/base.py

from abc import ABC, abstractmethod
from typing import AsyncIterator, TypeVar, Generic
from dataclasses import dataclass
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

T = TypeVar('T')

@dataclass
class CollectorConfig:
    """Configuration for a collector."""
    name: str
    base_url: str
    rate_limit_per_minute: int = 60
    max_retries: int = 3
    timeout_seconds: int = 30
    
@dataclass  
class CollectorResult(Generic[T]):
    """Result from a collector."""
    data: T
    source: str
    collected_at: datetime
    raw_response: dict | None = None

class BaseCollector(ABC):
    """
    Abstract base class for all collectors.
    Provides: rate limiting, retries, circuit breaker, logging.
    """
    
    def __init__(self, config: CollectorConfig):
        self.config = config
        self.client: httpx.AsyncClient = None
        self._rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout_seconds,
            headers=self._get_headers()
        )
        return self
    
    async def __aexit__(self, *args):
        await self.client.aclose()
    
    @abstractmethod
    def _get_headers(self) -> dict:
        """Return headers for API requests."""
        pass
    
    @abstractmethod
    async def collect(self, **kwargs) -> AsyncIterator[CollectorResult]:
        """Main collection method. Yields results."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the source is available."""
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60)
    )
    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make a rate-limited, retrying request."""
        await self._rate_limiter.acquire()
        
        if not self._circuit_breaker.can_execute():
            raise CircuitBreakerOpen(f"Circuit open for {self.config.name}")
        
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            self._circuit_breaker.record_success()
            return response
        except Exception as e:
            self._circuit_breaker.record_failure()
            raise
```

#### ArXiv Collector

```python
# src/collectors/arxiv.py

"""
ArXiv API Collector

API Docs: https://info.arxiv.org/help/api/index.html
Rate Limit: 1 request per 3 seconds
"""

from dataclasses import dataclass
from datetime import date
import xml.etree.ElementTree as ET

@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: list[dict]
    categories: list[str]
    published_date: date
    updated_date: date
    pdf_url: str
    comment: str | None = None

class ArxivCollector(BaseCollector):
    """
    Collects papers from ArXiv API.
    
    Usage:
        async with ArxivCollector() as collector:
            async for paper in collector.collect(
                categories=["cs.AI", "cs.CL"],
                date_from=date(2024, 1, 1),
                max_results=100
            ):
                process(paper)
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    def __init__(self):
        super().__init__(CollectorConfig(
            name="arxiv",
            base_url=self.BASE_URL,
            rate_limit_per_minute=20,  # 1 per 3 seconds
        ))
    
    def _get_headers(self) -> dict:
        return {"User-Agent": "OSINT-Research-Bot/1.0"}
    
    async def collect(
        self,
        categories: list[str] | None = None,
        search_query: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        max_results: int = 100,
        sort_by: str = "submittedDate",
        sort_order: str = "descending"
    ) -> AsyncIterator[CollectorResult[ArxivPaper]]:
        """
        Collect papers from ArXiv.
        
        Args:
            categories: List of ArXiv categories (e.g., ["cs.AI", "cs.CL"])
            search_query: Free text search query
            date_from: Start date filter
            date_to: End date filter
            max_results: Maximum papers to return
            sort_by: submittedDate, lastUpdatedDate, relevance
            sort_order: ascending, descending
        """
        query = self._build_query(categories, search_query, date_from, date_to)
        
        start = 0
        batch_size = min(100, max_results)  # ArXiv max is 100 per request
        
        while start < max_results:
            params = {
                "search_query": query,
                "start": start,
                "max_results": batch_size,
                "sortBy": sort_by,
                "sortOrder": sort_order
            }
            
            response = await self._request("GET", self.BASE_URL, params=params)
            papers = self._parse_response(response.text)
            
            if not papers:
                break
            
            for paper in papers:
                yield CollectorResult(
                    data=paper,
                    source="arxiv",
                    collected_at=datetime.utcnow()
                )
            
            start += len(papers)
            if len(papers) < batch_size:
                break
    
    def _build_query(
        self,
        categories: list[str] | None,
        search_query: str | None,
        date_from: date | None,
        date_to: date | None
    ) -> str:
        """Build ArXiv query string."""
        parts = []
        
        if categories:
            cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
            parts.append(f"({cat_query})")
        
        if search_query:
            parts.append(f"all:{search_query}")
        
        if date_from or date_to:
            # ArXiv uses submittedDate:[YYYYMMDDTTTT TO YYYYMMDDTTTT]
            from_str = date_from.strftime("%Y%m%d0000") if date_from else "*"
            to_str = date_to.strftime("%Y%m%d2359") if date_to else "*"
            parts.append(f"submittedDate:[{from_str} TO {to_str}]")
        
        return " AND ".join(parts) if parts else "all:*"
    
    def _parse_response(self, xml_content: str) -> list[ArxivPaper]:
        """Parse ArXiv API XML response."""
        root = ET.fromstring(xml_content)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        
        papers = []
        for entry in root.findall("atom:entry", ns):
            # Extract ArXiv ID from the id URL
            id_url = entry.find("atom:id", ns).text
            arxiv_id = id_url.split("/abs/")[-1]
            
            # Extract authors
            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns).text
                affiliation = author.find("arxiv:affiliation", ns)
                authors.append({
                    "name": name,
                    "affiliation": affiliation.text if affiliation is not None else None
                })
            
            # Extract categories
            categories = [
                cat.get("term") 
                for cat in entry.findall("atom:category", ns)
            ]
            
            papers.append(ArxivPaper(
                arxiv_id=arxiv_id,
                title=entry.find("atom:title", ns).text.strip(),
                abstract=entry.find("atom:summary", ns).text.strip(),
                authors=authors,
                categories=categories,
                published_date=parse_date(entry.find("atom:published", ns).text),
                updated_date=parse_date(entry.find("atom:updated", ns).text),
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                comment=getattr(entry.find("arxiv:comment", ns), "text", None)
            ))
        
        return papers
    
    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET", 
                self.BASE_URL, 
                params={"search_query": "all:test", "max_results": 1}
            )
            return response.status_code == 200
        except:
            return False
```

#### GitHub Collector

```python
# src/collectors/github.py

"""
GitHub GraphQL API Collector

API Docs: https://docs.github.com/en/graphql
Rate Limit: 5000 points/hour (authenticated)
"""

REPO_QUERY = """
query($query: String!, $first: Int!, $after: String) {
  search(query: $query, type: REPOSITORY, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        id
        databaseId
        nameWithOwner
        name
        owner {
          login
        }
        description
        url
        homepageUrl
        
        stargazerCount
        forkCount
        watchers {
          totalCount
        }
        
        primaryLanguage {
          name
        }
        languages(first: 10) {
          edges {
            size
            node {
              name
            }
          }
        }
        
        repositoryTopics(first: 20) {
          nodes {
            topic {
              name
            }
          }
        }
        
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 1) {
                totalCount
                nodes {
                  committedDate
                }
              }
            }
          }
        }
        
        releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            tagName
            publishedAt
          }
        }
        
        # Check for key files
        readme: object(expression: "HEAD:README.md") {
          ... on Blob {
            text
          }
        }
        license: object(expression: "HEAD:LICENSE") {
          ... on Blob {
            text
          }
        }
        dockerfile: object(expression: "HEAD:Dockerfile") {
          ... on Blob {
            text
          }
        }
        requirements: object(expression: "HEAD:requirements.txt") {
          ... on Blob {
            text
          }
        }
        pyproject: object(expression: "HEAD:pyproject.toml") {
          ... on Blob {
            text
          }
        }
        
        hasIssuesEnabled
        openIssues: issues(states: OPEN) {
          totalCount
        }
        
        createdAt
        updatedAt
        pushedAt
      }
    }
  }
  rateLimit {
    limit
    cost
    remaining
    resetAt
  }
}
"""

@dataclass
class GitHubRepo:
    github_id: int
    full_name: str
    name: str
    owner: str
    description: str | None
    html_url: str
    homepage_url: str | None
    
    stars_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    
    primary_language: str | None
    languages: dict[str, int]
    topics: list[str]
    
    readme_content: str | None
    has_license: bool
    has_dockerfile: bool
    dependencies: list[str]
    
    last_commit_at: datetime | None
    last_release_tag: str | None
    last_release_at: datetime | None
    
    created_at: datetime
    updated_at: datetime

class GitHubCollector(BaseCollector):
    """
    Collects repositories from GitHub GraphQL API.
    
    Usage:
        async with GitHubCollector(token="ghp_xxx") as collector:
            # Search for ML repos
            async for repo in collector.search(
                query="machine learning",
                language="python",
                min_stars=100,
                created_after=date(2024, 1, 1)
            ):
                process(repo)
            
            # Get trending repos
            async for repo in collector.get_trending(
                language="python",
                since="weekly"
            ):
                process(repo)
    """
    
    GRAPHQL_URL = "https://api.github.com/graphql"
    
    def __init__(self, token: str):
        self.token = token
        super().__init__(CollectorConfig(
            name="github",
            base_url=self.GRAPHQL_URL,
            rate_limit_per_minute=80,  # ~5000/hour
        ))
    
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def search(
        self,
        query: str | None = None,
        language: str | None = None,
        topics: list[str] | None = None,
        min_stars: int | None = None,
        created_after: date | None = None,
        pushed_after: date | None = None,
        max_results: int = 100
    ) -> AsyncIterator[CollectorResult[GitHubRepo]]:
        """
        Search GitHub repositories.
        
        Args:
            query: Search keywords
            language: Filter by primary language
            topics: Filter by topics
            min_stars: Minimum star count
            created_after: Created after this date
            pushed_after: Pushed after this date (activity filter)
            max_results: Maximum repos to return
        """
        search_query = self._build_search_query(
            query, language, topics, min_stars, created_after, pushed_after
        )
        
        cursor = None
        collected = 0
        
        while collected < max_results:
            batch_size = min(100, max_results - collected)
            
            variables = {
                "query": search_query,
                "first": batch_size,
                "after": cursor
            }
            
            response = await self._request(
                "POST",
                self.GRAPHQL_URL,
                json={"query": REPO_QUERY, "variables": variables}
            )
            
            data = response.json()
            
            # Update rate limit tracking
            rate_limit = data.get("data", {}).get("rateLimit", {})
            await self._update_rate_limit(rate_limit)
            
            search_data = data.get("data", {}).get("search", {})
            nodes = search_data.get("nodes", [])
            
            if not nodes:
                break
            
            for node in nodes:
                repo = self._parse_repo(node)
                if repo:
                    yield CollectorResult(
                        data=repo,
                        source="github",
                        collected_at=datetime.utcnow(),
                        raw_response=node
                    )
                    collected += 1
            
            page_info = search_data.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
    
    async def get_repo(self, owner: str, name: str) -> GitHubRepo | None:
        """Get a single repository by owner/name."""
        # Implementation...
        pass
    
    async def get_trending(
        self,
        language: str | None = None,
        since: str = "daily"  # daily, weekly, monthly
    ) -> AsyncIterator[CollectorResult[GitHubRepo]]:
        """
        Get trending repositories.
        Note: GitHub doesn't have official trending API, 
        so we simulate with search + sort by stars gained recently.
        """
        # Calculate date range based on 'since'
        days = {"daily": 1, "weekly": 7, "monthly": 30}[since]
        date_from = date.today() - timedelta(days=days)
        
        async for result in self.search(
            language=language,
            min_stars=50,
            pushed_after=date_from,
            max_results=100
        ):
            yield result
    
    def _build_search_query(
        self,
        query: str | None,
        language: str | None,
        topics: list[str] | None,
        min_stars: int | None,
        created_after: date | None,
        pushed_after: date | None
    ) -> str:
        """Build GitHub search query string."""
        parts = []
        
        if query:
            parts.append(query)
        
        if language:
            parts.append(f"language:{language}")
        
        if topics:
            for topic in topics:
                parts.append(f"topic:{topic}")
        
        if min_stars:
            parts.append(f"stars:>={min_stars}")
        
        if created_after:
            parts.append(f"created:>={created_after.isoformat()}")
        
        if pushed_after:
            parts.append(f"pushed:>={pushed_after.isoformat()}")
        
        # Always sort by stars for relevance
        parts.append("sort:stars")
        
        return " ".join(parts)
    
    def _parse_repo(self, node: dict) -> GitHubRepo | None:
        """Parse GraphQL response into GitHubRepo."""
        if not node:
            return None
        
        # Parse languages
        languages = {}
        for edge in (node.get("languages", {}).get("edges") or []):
            lang_name = edge["node"]["name"]
            languages[lang_name] = edge["size"]
        
        # Parse topics
        topics = [
            t["topic"]["name"] 
            for t in (node.get("repositoryTopics", {}).get("nodes") or [])
        ]
        
        # Parse dependencies from requirements.txt or pyproject.toml
        dependencies = []
        if node.get("requirements"):
            dependencies = self._parse_requirements(node["requirements"].get("text", ""))
        elif node.get("pyproject"):
            dependencies = self._parse_pyproject(node["pyproject"].get("text", ""))
        
        # Get last commit date
        last_commit_at = None
        branch_ref = node.get("defaultBranchRef")
        if branch_ref and branch_ref.get("target"):
            history = branch_ref["target"].get("history", {}).get("nodes", [])
            if history:
                last_commit_at = parse_datetime(history[0]["committedDate"])
        
        # Get last release
        releases = node.get("releases", {}).get("nodes", [])
        last_release_tag = releases[0]["tagName"] if releases else None
        last_release_at = parse_datetime(releases[0]["publishedAt"]) if releases else None
        
        return GitHubRepo(
            github_id=node["databaseId"],
            full_name=node["nameWithOwner"],
            name=node["name"],
            owner=node["owner"]["login"],
            description=node.get("description"),
            html_url=node["url"],
            homepage_url=node.get("homepageUrl"),
            
            stars_count=node["stargazerCount"],
            forks_count=node["forkCount"],
            watchers_count=node.get("watchers", {}).get("totalCount", 0),
            open_issues_count=node.get("openIssues", {}).get("totalCount", 0),
            
            primary_language=node.get("primaryLanguage", {}).get("name") if node.get("primaryLanguage") else None,
            languages=languages,
            topics=topics,
            
            readme_content=node.get("readme", {}).get("text") if node.get("readme") else None,
            has_license=node.get("license") is not None,
            has_dockerfile=node.get("dockerfile") is not None,
            dependencies=dependencies,
            
            last_commit_at=last_commit_at,
            last_release_tag=last_release_tag,
            last_release_at=last_release_at,
            
            created_at=parse_datetime(node["createdAt"]),
            updated_at=parse_datetime(node["updatedAt"])
        )
    
    def _parse_requirements(self, content: str) -> list[str]:
        """Parse requirements.txt content."""
        deps = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove version specifiers
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0]
                deps.append(pkg.strip())
        return deps
    
    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "POST",
                self.GRAPHQL_URL,
                json={"query": "{ viewer { login } }"}
            )
            return "data" in response.json()
        except:
            return False
```

#### Semantic Scholar Collector

```python
# src/collectors/semantic_scholar.py

"""
Semantic Scholar API Collector

API Docs: https://api.semanticscholar.org/
Rate Limit: 100 requests/5 min (authenticated), 10/5min (unauthenticated)
"""

@dataclass
class SemanticScholarPaper:
    s2_id: str
    arxiv_id: str | None
    doi: str | None
    title: str
    abstract: str | None
    authors: list[dict]
    year: int | None
    venue: str | None
    citation_count: int
    influential_citation_count: int
    references_count: int
    fields_of_study: list[str]
    is_open_access: bool
    external_ids: dict

class SemanticScholarCollector(BaseCollector):
    """
    Collects paper metadata and citations from Semantic Scholar.
    
    Best used for:
    - Enriching ArXiv papers with citation data
    - Finding influential papers
    - Building citation graphs
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        super().__init__(CollectorConfig(
            name="semantic_scholar",
            base_url=self.BASE_URL,
            rate_limit_per_minute=20 if api_key else 2,
        ))
    
    def _get_headers(self) -> dict:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers
    
    async def search(
        self,
        query: str,
        year_range: tuple[int, int] | None = None,
        fields_of_study: list[str] | None = None,
        open_access_only: bool = False,
        max_results: int = 100
    ) -> AsyncIterator[CollectorResult[SemanticScholarPaper]]:
        """Search for papers."""
        fields = "paperId,externalIds,title,abstract,authors,year,venue,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,isOpenAccess"
        
        offset = 0
        limit = min(100, max_results)
        
        while offset < max_results:
            params = {
                "query": query,
                "fields": fields,
                "offset": offset,
                "limit": limit
            }
            
            if year_range:
                params["year"] = f"{year_range[0]}-{year_range[1]}"
            
            if fields_of_study:
                params["fieldsOfStudy"] = ",".join(fields_of_study)
            
            if open_access_only:
                params["openAccessPdf"] = ""
            
            response = await self._request(
                "GET",
                f"{self.BASE_URL}/paper/search",
                params=params
            )
            
            data = response.json()
            papers = data.get("data", [])
            
            if not papers:
                break
            
            for paper_data in papers:
                paper = self._parse_paper(paper_data)
                yield CollectorResult(
                    data=paper,
                    source="semantic_scholar",
                    collected_at=datetime.utcnow()
                )
            
            offset += len(papers)
            if len(papers) < limit:
                break
    
    async def get_paper(self, paper_id: str) -> SemanticScholarPaper | None:
        """
        Get a single paper by ID.
        
        Args:
            paper_id: Can be S2 ID, ArXiv ID (arxiv:2401.12345), DOI (doi:10.xxx)
        """
        fields = "paperId,externalIds,title,abstract,authors,year,venue,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,isOpenAccess"
        
        response = await self._request(
            "GET",
            f"{self.BASE_URL}/paper/{paper_id}",
            params={"fields": fields}
        )
        
        return self._parse_paper(response.json())
    
    async def get_papers_batch(
        self,
        paper_ids: list[str]
    ) -> list[SemanticScholarPaper]:
        """
        Get multiple papers in a single request (up to 500).
        """
        fields = "paperId,externalIds,title,abstract,authors,year,venue,citationCount,influentialCitationCount,referenceCount,fieldsOfStudy,isOpenAccess"
        
        results = []
        
        # Batch in groups of 500
        for i in range(0, len(paper_ids), 500):
            batch = paper_ids[i:i+500]
            
            response = await self._request(
                "POST",
                f"{self.BASE_URL}/paper/batch",
                params={"fields": fields},
                json={"ids": batch}
            )
            
            for paper_data in response.json():
                if paper_data:
                    results.append(self._parse_paper(paper_data))
        
        return results
    
    async def get_citations(
        self,
        paper_id: str,
        max_results: int = 100
    ) -> list[SemanticScholarPaper]:
        """Get papers that cite this paper."""
        # Implementation...
        pass
    
    def _parse_paper(self, data: dict) -> SemanticScholarPaper:
        """Parse API response into SemanticScholarPaper."""
        external_ids = data.get("externalIds", {})
        
        authors = [
            {
                "name": a.get("name"),
                "author_id": a.get("authorId")
            }
            for a in (data.get("authors") or [])
        ]
        
        return SemanticScholarPaper(
            s2_id=data["paperId"],
            arxiv_id=external_ids.get("ArXiv"),
            doi=external_ids.get("DOI"),
            title=data.get("title", ""),
            abstract=data.get("abstract"),
            authors=authors,
            year=data.get("year"),
            venue=data.get("venue"),
            citation_count=data.get("citationCount", 0),
            influential_citation_count=data.get("influentialCitationCount", 0),
            references_count=data.get("referenceCount", 0),
            fields_of_study=data.get("fieldsOfStudy") or [],
            is_open_access=data.get("isOpenAccess", False),
            external_ids=external_ids
        )
    
    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET",
                f"{self.BASE_URL}/paper/arxiv:2301.00001"
            )
            return response.status_code == 200
        except:
            return False
```

#### Hugging Face Collector

```python
# src/collectors/huggingface.py

"""
Hugging Face Hub API Collector

API Docs: https://huggingface.co/docs/hub/api
Rate Limit: Generous (authenticated), moderate (unauthenticated)
"""

@dataclass
class HFModel:
    model_id: str
    author: str
    model_name: str
    sha: str
    pipeline_tag: str | None
    tags: list[str]
    downloads: int
    likes: int
    library_name: str | None
    linked_arxiv_ids: list[str]
    created_at: datetime
    last_modified: datetime

@dataclass
class HFDataset:
    dataset_id: str
    author: str
    dataset_name: str
    tags: list[str]
    downloads: int
    likes: int
    created_at: datetime
    last_modified: datetime

class HuggingFaceCollector(BaseCollector):
    """
    Collects models and datasets from Hugging Face Hub.
    
    Key feature: Link models back to their source papers via ArXiv tags.
    """
    
    BASE_URL = "https://huggingface.co/api"
    
    def __init__(self, token: str | None = None):
        self.token = token
        super().__init__(CollectorConfig(
            name="huggingface",
            base_url=self.BASE_URL,
            rate_limit_per_minute=60,
        ))
    
    def _get_headers(self) -> dict:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def search_models(
        self,
        query: str | None = None,
        author: str | None = None,
        tags: list[str] | None = None,
        pipeline_tag: str | None = None,
        library: str | None = None,
        arxiv_id: str | None = None,
        sort: str = "downloads",
        direction: str = "-1",
        max_results: int = 100
    ) -> AsyncIterator[CollectorResult[HFModel]]:
        """
        Search models on Hugging Face.
        
        Args:
            query: Search query
            author: Filter by author/organization
            tags: Filter by tags (e.g., ["text-generation", "pytorch"])
            pipeline_tag: Filter by pipeline (e.g., "text-generation")
            library: Filter by library (e.g., "transformers")
            arxiv_id: Find models linked to specific ArXiv paper
            sort: Sort by (downloads, likes, lastModified, createdAt)
            direction: Sort direction (-1 desc, 1 asc)
            max_results: Maximum results
        """
        params = {
            "sort": sort,
            "direction": direction,
            "limit": min(100, max_results)
        }
        
        if query:
            params["search"] = query
        if author:
            params["author"] = author
        if pipeline_tag:
            params["pipeline_tag"] = pipeline_tag
        if library:
            params["library"] = library
        if tags:
            params["tags"] = ",".join(tags)
        
        # Special handling for ArXiv linking
        if arxiv_id:
            params["tags"] = f"arxiv:{arxiv_id}"
        
        response = await self._request(
            "GET",
            f"{self.BASE_URL}/models",
            params=params
        )
        
        for model_data in response.json():
            model = self._parse_model(model_data)
            yield CollectorResult(
                data=model,
                source="huggingface",
                collected_at=datetime.utcnow()
            )
    
    async def get_models_for_paper(
        self,
        arxiv_id: str
    ) -> list[HFModel]:
        """
        Find all HF models linked to an ArXiv paper.
        This is the primary Paper -> Code linking method.
        """
        results = []
        async for result in self.search_models(arxiv_id=arxiv_id, max_results=50):
            results.append(result.data)
        return results
    
    async def get_model(self, model_id: str) -> HFModel | None:
        """Get details of a specific model."""
        response = await self._request(
            "GET",
            f"{self.BASE_URL}/models/{model_id}"
        )
        return self._parse_model(response.json())
    
    def _parse_model(self, data: dict) -> HFModel:
        """Parse API response into HFModel."""
        model_id = data.get("modelId") or data.get("id", "")
        parts = model_id.split("/")
        author = parts[0] if len(parts) > 1 else ""
        model_name = parts[1] if len(parts) > 1 else parts[0]
        
        # Extract linked ArXiv IDs from tags
        tags = data.get("tags", [])
        arxiv_ids = [
            tag.replace("arxiv:", "")
            for tag in tags
            if tag.startswith("arxiv:")
        ]
        
        return HFModel(
            model_id=model_id,
            author=author,
            model_name=model_name,
            sha=data.get("sha", ""),
            pipeline_tag=data.get("pipeline_tag"),
            tags=tags,
            downloads=data.get("downloads", 0),
            likes=data.get("likes", 0),
            library_name=data.get("library_name"),
            linked_arxiv_ids=arxiv_ids,
            created_at=parse_datetime(data.get("createdAt")),
            last_modified=parse_datetime(data.get("lastModified"))
        )
    
    async def health_check(self) -> bool:
        try:
            response = await self._request(
                "GET",
                f"{self.BASE_URL}/models",
                params={"limit": 1}
            )
            return response.status_code == 200
        except:
            return False
```

---

### 2. Processors Module

#### Classifier

```python
# src/processors/classifier.py

"""
Topic Classification Processor

Uses local LLM to classify papers/repos into predefined topics.
"""

from enum import Enum

class Topic(str, Enum):
    LLM = "large-language-models"
    RAG = "retrieval-augmented-generation"
    AGENTS = "ai-agents"
    MULTIMODAL = "multimodal"
    COMPUTER_VISION = "computer-vision"
    NLP = "natural-language-processing"
    REINFORCEMENT_LEARNING = "reinforcement-learning"
    ROBOTICS = "robotics"
    OPTIMIZATION = "optimization"
    OTHER = "other"

CLASSIFICATION_PROMPT = """
You are a research paper classifier. Given the title and abstract of a paper,
classify it into one or more of the following topics:

Topics:
- large-language-models: LLMs, transformers, GPT, BERT, language modeling
- retrieval-augmented-generation: RAG, retrieval systems, knowledge bases
- ai-agents: Autonomous agents, tool use, planning, reasoning
- multimodal: Vision-language, audio, video understanding
- computer-vision: Image classification, detection, segmentation
- natural-language-processing: NLP tasks not covered by LLM
- reinforcement-learning: RL, policy learning, reward modeling
- robotics: Robot control, manipulation, navigation
- optimization: Training optimization, hyperparameters, efficiency
- other: Does not fit above categories

Paper Title: {title}

Abstract: {abstract}

Respond with a JSON object:
{{
    "primary_topic": "<topic>",
    "secondary_topics": ["<topic>", ...],
    "confidence": <0.0-1.0>,
    "keywords": ["<keyword>", ...]
}}
"""

class TopicClassifier:
    """
    Classifies papers into research topics using LLM.
    
    Usage:
        classifier = TopicClassifier(llm_client)
        result = await classifier.classify(paper)
    """
    
    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client
    
    async def classify(
        self,
        title: str,
        abstract: str
    ) -> ClassificationResult:
        """
        Classify a paper into topics.
        
        Returns:
            ClassificationResult with primary_topic, secondary_topics, confidence
        """
        prompt = CLASSIFICATION_PROMPT.format(
            title=title,
            abstract=abstract[:2000]  # Truncate long abstracts
        )
        
        response = await self.llm.generate(
            prompt,
            max_tokens=200,
            temperature=0.1  # Low temp for consistent classification
        )
        
        # Parse JSON response
        try:
            result = json.loads(response)
            return ClassificationResult(
                primary_topic=Topic(result["primary_topic"]),
                secondary_topics=[Topic(t) for t in result.get("secondary_topics", [])],
                confidence=result.get("confidence", 0.5),
                keywords=result.get("keywords", [])
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse classification: {e}")
            return ClassificationResult(
                primary_topic=Topic.OTHER,
                secondary_topics=[],
                confidence=0.0,
                keywords=[]
            )
    
    async def classify_batch(
        self,
        papers: list[tuple[str, str]]  # List of (title, abstract)
    ) -> list[ClassificationResult]:
        """Classify multiple papers concurrently."""
        tasks = [
            self.classify(title, abstract)
            for title, abstract in papers
        ]
        return await asyncio.gather(*tasks)
    
    async def is_relevant(
        self,
        title: str,
        abstract: str,
        target_topics: list[Topic]
    ) -> bool:
        """Quick relevance check - is paper about any target topics?"""
        result = await self.classify(title, abstract)
        
        all_topics = [result.primary_topic] + result.secondary_topics
        return any(topic in target_topics for topic in all_topics)
```

#### Summarizer

```python
# src/processors/summarizer.py

"""
Paper/Repo Summarization Processor

Generates concise 3-line summaries:
1. Problem being solved
2. Proposed solution/approach
3. Key results/findings
"""

PAPER_SUMMARY_PROMPT = """
You are a research paper summarizer. Create a concise 3-line summary:

1. PROBLEM: What problem does this paper address?
2. APPROACH: What is the proposed solution/method?
3. RESULTS: What are the key findings/achievements?

Title: {title}

Abstract: {abstract}

Respond with exactly 3 lines, each starting with the label:
PROBLEM: ...
APPROACH: ...
RESULTS: ...
"""

README_SUMMARY_PROMPT = """
You are a code repository analyzer. Summarize this README in 3 lines:

1. PURPOSE: What does this project do?
2. FEATURES: What are the key features/capabilities?
3. USAGE: How is it typically used?

README Content:
{readme}

Respond with exactly 3 lines:
PURPOSE: ...
FEATURES: ...
USAGE: ...
"""

@dataclass
class Summary:
    line1: str
    line2: str
    line3: str
    full_text: str
    
    @classmethod
    def from_lines(cls, lines: list[str]) -> "Summary":
        return cls(
            line1=lines[0] if len(lines) > 0 else "",
            line2=lines[1] if len(lines) > 1 else "",
            line3=lines[2] if len(lines) > 2 else "",
            full_text="\n".join(lines)
        )

class Summarizer:
    """
    Generates concise summaries for papers and repositories.
    
    Uses:
    - Local LLM for bulk processing
    - Cloud LLM for complex/important items
    """
    
    def __init__(
        self,
        local_llm: BaseLLMClient,
        cloud_llm: BaseLLMClient | None = None
    ):
        self.local_llm = local_llm
        self.cloud_llm = cloud_llm
    
    async def summarize_paper(
        self,
        title: str,
        abstract: str,
        use_cloud: bool = False
    ) -> Summary:
        """Summarize a research paper."""
        llm = self.cloud_llm if use_cloud and self.cloud_llm else self.local_llm
        
        prompt = PAPER_SUMMARY_PROMPT.format(
            title=title,
            abstract=abstract[:3000]
        )
        
        response = await llm.generate(
            prompt,
            max_tokens=300,
            temperature=0.3
        )
        
        return self._parse_summary(response)
    
    async def summarize_readme(
        self,
        readme_content: str,
        use_cloud: bool = False
    ) -> Summary:
        """Summarize a repository README."""
        llm = self.cloud_llm if use_cloud and self.cloud_llm else self.local_llm
        
        # Truncate very long READMEs
        truncated = readme_content[:5000] if len(readme_content) > 5000 else readme_content
        
        prompt = README_SUMMARY_PROMPT.format(readme=truncated)
        
        response = await llm.generate(
            prompt,
            max_tokens=300,
            temperature=0.3
        )
        
        return self._parse_summary(response)
    
    def _parse_summary(self, response: str) -> Summary:
        """Parse LLM response into Summary object."""
        lines = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line:
                # Remove labels like "PROBLEM:", "PURPOSE:", etc.
                if ":" in line:
                    line = line.split(":", 1)[1].strip()
                lines.append(line)
        
        return Summary.from_lines(lines[:3])
```

#### Paper-Code Linker

```python
# src/processors/paper_code_linker.py

"""
Paper-Code Linking Processor

Finds and validates connections between papers and code repositories.

Strategies:
1. Direct extraction from PDF
2. Papers With Code lookup
3. Hugging Face model tags
4. GitHub code search
5. Author matching
"""

import re
from dataclasses import dataclass
from enum import Enum

class LinkType(str, Enum):
    OFFICIAL = "official"       # Author's implementation
    COMMUNITY = "community"     # Third-party implementation
    MENTIONED = "mentioned"     # Just mentioned, not implementation
    INFERRED = "inferred"       # Algorithmically inferred

@dataclass
class LinkEvidence:
    """Evidence supporting a paper-code link."""
    author_name_match: float = 0.0      # Fuzzy match score
    readme_contains_arxiv: bool = False
    readme_contains_title: bool = False
    papers_with_code_link: bool = False
    huggingface_link: bool = False
    timing_score: float = 0.0           # Repo created near paper date
    github_in_pdf: bool = False         # GitHub URL found in paper PDF
    
    def calculate_confidence(self) -> float:
        """Calculate overall confidence score."""
        score = 0.0
        
        # Strong signals
        if self.papers_with_code_link:
            score += 0.25
        if self.huggingface_link:
            score += 0.25
        if self.github_in_pdf:
            score += 0.20
        
        # Medium signals
        score += self.author_name_match * 0.15
        if self.readme_contains_arxiv:
            score += 0.15
        
        # Weak signals
        score += self.timing_score * 0.10
        if self.readme_contains_title:
            score += 0.05
        
        return min(1.0, score)
    
    def determine_link_type(self) -> LinkType:
        """Determine if link is official or community."""
        confidence = self.calculate_confidence()
        
        if confidence >= 0.8:
            return LinkType.OFFICIAL
        elif confidence >= 0.5:
            return LinkType.COMMUNITY
        elif confidence >= 0.3:
            return LinkType.INFERRED
        else:
            return LinkType.MENTIONED

@dataclass
class PaperCodeLink:
    paper_id: str
    repo_id: str
    link_type: LinkType
    confidence: float
    evidence: LinkEvidence
    discovered_via: str

class PaperCodeLinker:
    """
    Finds and validates links between papers and code repositories.
    
    Usage:
        linker = PaperCodeLinker(github_collector, hf_collector, pwc_client)
        
        # Find repos for a paper
        links = await linker.find_repos_for_paper(paper)
        
        # Find papers for a repo
        papers = await linker.find_papers_for_repo(repo)
    """
    
    GITHUB_URL_PATTERN = re.compile(
        r'github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)',
        re.IGNORECASE
    )
    
    ARXIV_ID_PATTERN = re.compile(
        r'arxiv[:\s]*(\d{4}\.\d{4,5})',
        re.IGNORECASE
    )
    
    def __init__(
        self,
        github_collector: GitHubCollector,
        hf_collector: HuggingFaceCollector,
        pwc_client: PapersWithCodeClient,
        pdf_extractor: PDFTextExtractor
    ):
        self.github = github_collector
        self.hf = hf_collector
        self.pwc = pwc_client
        self.pdf = pdf_extractor
    
    async def find_repos_for_paper(
        self,
        paper: Paper
    ) -> list[PaperCodeLink]:
        """
        Find all code repositories linked to a paper.
        
        Tries multiple strategies in parallel.
        """
        links = []
        
        # Run all strategies concurrently
        results = await asyncio.gather(
            self._search_papers_with_code(paper),
            self._search_huggingface(paper),
            self._extract_from_pdf(paper),
            self._search_github_readme(paper),
            return_exceptions=True
        )
        
        # Flatten and deduplicate
        seen_repos = set()
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Link search failed: {result}")
                continue
            
            for link in result:
                if link.repo_id not in seen_repos:
                    seen_repos.add(link.repo_id)
                    links.append(link)
        
        # Sort by confidence
        links.sort(key=lambda x: x.confidence, reverse=True)
        
        return links
    
    async def _search_papers_with_code(
        self,
        paper: Paper
    ) -> list[PaperCodeLink]:
        """Search Papers With Code for linked repos."""
        if not paper.arxiv_id:
            return []
        
        try:
            pwc_data = await self.pwc.get_paper(paper.arxiv_id)
            if not pwc_data or not pwc_data.get("repositories"):
                return []
            
            links = []
            for repo_data in pwc_data["repositories"]:
                evidence = LinkEvidence(
                    papers_with_code_link=True
                )
                
                links.append(PaperCodeLink(
                    paper_id=paper.id,
                    repo_id=repo_data["url"],
                    link_type=evidence.determine_link_type(),
                    confidence=evidence.calculate_confidence(),
                    evidence=evidence,
                    discovered_via="papers_with_code"
                ))
            
            return links
        
        except Exception as e:
            logger.warning(f"PWC search failed: {e}")
            return []
    
    async def _search_huggingface(
        self,
        paper: Paper
    ) -> list[PaperCodeLink]:
        """Search Hugging Face for models linked to paper."""
        if not paper.arxiv_id:
            return []
        
        try:
            models = await self.hf.get_models_for_paper(paper.arxiv_id)
            
            links = []
            for model in models:
                evidence = LinkEvidence(
                    huggingface_link=True
                )
                
                # Check author match
                if paper.authors:
                    author_score = self._fuzzy_author_match(
                        paper.authors,
                        model.author
                    )
                    evidence.author_name_match = author_score
                
                links.append(PaperCodeLink(
                    paper_id=paper.id,
                    repo_id=f"huggingface:{model.model_id}",
                    link_type=evidence.determine_link_type(),
                    confidence=evidence.calculate_confidence(),
                    evidence=evidence,
                    discovered_via="huggingface"
                ))
            
            return links
        
        except Exception as e:
            logger.warning(f"HF search failed: {e}")
            return []
    
    async def _extract_from_pdf(
        self,
        paper: Paper
    ) -> list[PaperCodeLink]:
        """Extract GitHub URLs from paper PDF."""
        if not paper.pdf_url:
            return []
        
        try:
            # Download and extract text from PDF
            text = await self.pdf.extract_text(paper.pdf_url)
            
            # Find GitHub URLs
            matches = self.GITHUB_URL_PATTERN.findall(text)
            
            links = []
            for owner, repo in matches:
                full_name = f"{owner}/{repo}"
                
                # Verify repo exists
                repo_info = await self.github.get_repo(owner, repo)
                if not repo_info:
                    continue
                
                evidence = LinkEvidence(
                    github_in_pdf=True
                )
                
                # Check author match
                if paper.authors:
                    evidence.author_name_match = self._fuzzy_author_match(
                        paper.authors,
                        owner
                    )
                
                # Check timing
                if paper.published_date and repo_info.created_at:
                    evidence.timing_score = self._calculate_timing_score(
                        paper.published_date,
                        repo_info.created_at.date()
                    )
                
                links.append(PaperCodeLink(
                    paper_id=paper.id,
                    repo_id=full_name,
                    link_type=evidence.determine_link_type(),
                    confidence=evidence.calculate_confidence(),
                    evidence=evidence,
                    discovered_via="pdf_extraction"
                ))
            
            return links
        
        except Exception as e:
            logger.warning(f"PDF extraction failed: {e}")
            return []
    
    async def _search_github_readme(
        self,
        paper: Paper
    ) -> list[PaperCodeLink]:
        """Search GitHub for repos mentioning paper in README."""
        # Search for ArXiv ID or paper title
        queries = []
        
        if paper.arxiv_id:
            queries.append(f'"{paper.arxiv_id}" in:readme')
        
        # Use first 50 chars of title for search
        title_query = paper.title[:50].replace('"', '')
        queries.append(f'"{title_query}" in:readme')
        
        links = []
        for query in queries:
            try:
                async for result in self.github.search(
                    query=query,
                    max_results=10
                ):
                    repo = result.data
                    
                    evidence = LinkEvidence()
                    
                    # Check README for ArXiv link
                    if repo.readme_content and paper.arxiv_id:
                        if paper.arxiv_id in repo.readme_content:
                            evidence.readme_contains_arxiv = True
                    
                    # Check for title match
                    if repo.readme_content:
                        title_lower = paper.title.lower()
                        if title_lower[:30] in repo.readme_content.lower():
                            evidence.readme_contains_title = True
                    
                    # Author match
                    if paper.authors:
                        evidence.author_name_match = self._fuzzy_author_match(
                            paper.authors,
                            repo.owner
                        )
                    
                    if evidence.calculate_confidence() > 0.2:
                        links.append(PaperCodeLink(
                            paper_id=paper.id,
                            repo_id=repo.full_name,
                            link_type=evidence.determine_link_type(),
                            confidence=evidence.calculate_confidence(),
                            evidence=evidence,
                            discovered_via="github_search"
                        ))
            
            except Exception as e:
                logger.warning(f"GitHub search failed for query: {e}")
        
        return links
    
    def _fuzzy_author_match(
        self,
        paper_authors: list[dict],
        github_user: str
    ) -> float:
        """
        Calculate fuzzy match score between paper authors and GitHub user.
        
        Returns 0.0 - 1.0
        """
        from rapidfuzz import fuzz
        
        github_user_lower = github_user.lower()
        
        best_score = 0.0
        for author in paper_authors:
            name = author.get("name", "").lower()
            
            # Try full name match
            score = fuzz.ratio(name, github_user_lower) / 100
            
            # Try last name only
            parts = name.split()
            if parts:
                last_name_score = fuzz.ratio(parts[-1], github_user_lower) / 100
                score = max(score, last_name_score)
            
            best_score = max(best_score, score)
        
        return best_score
    
    def _calculate_timing_score(
        self,
        paper_date: date,
        repo_date: date
    ) -> float:
        """
        Score based on timing between paper and repo creation.
        
        Best: Repo created within 30 days after paper
        Good: Within 90 days
        OK: Within 180 days
        """
        days_diff = (repo_date - paper_date).days
        
        if days_diff < 0:
            # Repo before paper - suspicious but could be pre-release
            return max(0, 0.5 + days_diff / 60)  # Penalize old repos
        elif days_diff <= 30:
            return 1.0
        elif days_diff <= 90:
            return 0.8
        elif days_diff <= 180:
            return 0.5
        else:
            return 0.2
```

#### Trending Calculator

```python
# src/processors/trending.py

"""
Trending Score Calculator

Calculates and tracks trending scores for papers and repositories.
"""

from dataclasses import dataclass
from datetime import date, timedelta

@dataclass
class TrendingScores:
    activity_score: float
    community_score: float
    academic_score: float
    recency_score: float
    total_score: float

class TrendingCalculator:
    """
    Calculates trending scores for papers and repositories.
    
    Scoring Weights:
    - Activity (40%): Recent commits, issues activity
    - Community (30%): Star/fork velocity
    - Academic (20%): Citation velocity
    - Recency (10%): Time since last update
    """
    
    # Weights
    W_ACTIVITY = 0.40
    W_COMMUNITY = 0.30
    W_ACADEMIC = 0.20
    W_RECENCY = 0.10
    
    def __init__(self, metrics_repo: MetricsRepository):
        self.metrics = metrics_repo
    
    async def calculate_repo_score(
        self,
        repo: Repository,
        period_days: int = 7
    ) -> TrendingScores:
        """
        Calculate trending score for a repository.
        """
        # Get historical metrics
        history = await self.metrics.get_history(
            entity_type="repository",
            entity_id=repo.id,
            days=period_days
        )
        
        # Activity Score
        activity = self._calculate_activity_score(repo, history)
        
        # Community Score (star velocity)
        community = self._calculate_community_score(repo, history)
        
        # Academic Score (linked paper citations)
        academic = await self._calculate_academic_score_for_repo(repo)
        
        # Recency Score
        recency = self._calculate_recency_score(repo.last_commit_at)
        
        # Weighted total
        total = (
            activity * self.W_ACTIVITY +
            community * self.W_COMMUNITY +
            academic * self.W_ACADEMIC +
            recency * self.W_RECENCY
        )
        
        return TrendingScores(
            activity_score=activity,
            community_score=community,
            academic_score=academic,
            recency_score=recency,
            total_score=total
        )
    
    async def calculate_paper_score(
        self,
        paper: Paper,
        period_days: int = 30
    ) -> TrendingScores:
        """
        Calculate trending score for a paper.
        """
        history = await self.metrics.get_history(
            entity_type="paper",
            entity_id=paper.id,
            days=period_days
        )
        
        # Activity Score (not applicable, set to neutral)
        activity = 0.5
        
        # Community Score (social media mentions, would need additional data)
        community = 0.5
        
        # Academic Score (citation velocity)
        academic = self._calculate_citation_velocity(paper, history)
        
        # Recency Score
        recency = self._calculate_recency_score(
            datetime.combine(paper.published_date, datetime.min.time())
            if paper.published_date else None
        )
        
        total = (
            activity * self.W_ACTIVITY +
            community * self.W_COMMUNITY +
            academic * self.W_ACADEMIC +
            recency * self.W_RECENCY
        )
        
        return TrendingScores(
            activity_score=activity,
            community_score=community,
            academic_score=academic,
            recency_score=recency,
            total_score=total
        )
    
    def _calculate_activity_score(
        self,
        repo: Repository,
        history: list[MetricsSnapshot]
    ) -> float:
        """
        Activity score based on:
        - Recent commits
        - Issue activity (open/closed ratio)
        - PR activity
        """
        score = 0.0
        
        # Commit frequency (30 commits/month = 1.0)
        if repo.commit_count_30d:
            score += min(1.0, repo.commit_count_30d / 30) * 0.5
        
        # Issue activity
        if repo.open_issues_count > 0:
            # Some open issues = active project
            score += min(1.0, repo.open_issues_count / 50) * 0.3
        
        # Has recent activity
        if repo.last_commit_at:
            days_since = (datetime.utcnow() - repo.last_commit_at).days
            if days_since < 7:
                score += 0.2
            elif days_since < 30:
                score += 0.1
        
        return min(1.0, score)
    
    def _calculate_community_score(
        self,
        repo: Repository,
        history: list[MetricsSnapshot]
    ) -> float:
        """
        Community score based on star/fork velocity.
        
        Formula: (new_stars / total_stars) - measures relative growth
        """
        if not history or len(history) < 2:
            # No history, use absolute stars
            return min(1.0, repo.stars_count / 10000)
        
        old_stars = history[-1].metrics.get("stars", repo.stars_count)
        new_stars = repo.stars_count - old_stars
        
        if repo.stars_count == 0:
            return 0.0
        
        # Velocity as percentage of total
        velocity = new_stars / repo.stars_count
        
        # Scale: 10% growth in period = 1.0 score
        return min(1.0, velocity * 10)
    
    def _calculate_citation_velocity(
        self,
        paper: Paper,
        history: list[MetricsSnapshot]
    ) -> float:
        """
        Academic score based on citation growth rate.
        """
        if not history or len(history) < 2:
            # No history, use absolute citations
            return min(1.0, paper.citation_count / 100)
        
        old_citations = history[-1].metrics.get("citations", paper.citation_count)
        new_citations = paper.citation_count - old_citations
        
        # Influential citations weighted higher
        influential_ratio = (
            paper.influential_citation_count / paper.citation_count
            if paper.citation_count > 0 else 0
        )
        
        # Base velocity score
        velocity_score = min(1.0, new_citations / 10)
        
        # Boost for influential citations
        quality_boost = influential_ratio * 0.5
        
        return min(1.0, velocity_score + quality_boost)
    
    def _calculate_recency_score(
        self,
        last_activity: datetime | None
    ) -> float:
        """
        Recency score: how recently was there activity?
        
        1.0 = today
        0.5 = 7 days ago
        0.0 = 30+ days ago
        """
        if not last_activity:
            return 0.0
        
        days_ago = (datetime.utcnow() - last_activity).days
        
        if days_ago <= 0:
            return 1.0
        elif days_ago <= 7:
            return 1.0 - (days_ago / 14)
        elif days_ago <= 30:
            return 0.5 - ((days_ago - 7) / 46)
        else:
            return max(0.0, 0.2 - ((days_ago - 30) / 150))
    
    async def detect_sota_shift(
        self,
        category: str,
        threshold: float = 0.1
    ) -> list[SOTAShiftAlert]:
        """
        Detect when a new repo/paper surpasses the leader in a category.
        
        Returns alerts for significant shifts.
        """
        # Get current rankings
        current_rankings = await self.get_category_rankings(category)
        
        # Get last week's rankings
        previous_rankings = await self.get_category_rankings(
            category,
            as_of=date.today() - timedelta(days=7)
        )
        
        alerts = []
        
        if not current_rankings or not previous_rankings:
            return alerts
        
        current_leader = current_rankings[0]
        previous_leader_id = previous_rankings[0].entity_id
        
        # Check if leader changed
        if current_leader.entity_id != previous_leader_id:
            # Find the old leader's new position
            old_leader_rank = next(
                (i for i, r in enumerate(current_rankings)
                 if r.entity_id == previous_leader_id),
                None
            )
            
            alerts.append(SOTAShiftAlert(
                category=category,
                new_leader_id=current_leader.entity_id,
                old_leader_id=previous_leader_id,
                new_leader_score=current_leader.total_score,
                old_leader_new_rank=old_leader_rank,
                shift_magnitude=current_leader.total_score - (
                    previous_rankings[0].total_score if previous_rankings else 0
                )
            ))
        
        # Check for close challengers
        if len(current_rankings) > 1:
            challenger = current_rankings[1]
            gap = current_leader.total_score - challenger.total_score
            
            if gap < threshold and gap < (current_leader.total_score * 0.1):
                alerts.append(SOTAShiftAlert(
                    category=category,
                    new_leader_id=current_leader.entity_id,
                    challenger_id=challenger.entity_id,
                    gap=gap,
                    is_potential_shift=True
                ))
        
        return alerts
```

---

### 3. RAG Module

```python
# src/rag/pipeline.py

"""
RAG (Retrieval-Augmented Generation) Pipeline

Enables Q&A over the collected research knowledge base.
"""

from dataclasses import dataclass

@dataclass
class RAGResponse:
    answer: str
    sources: list[dict]  # Referenced papers/repos
    confidence: float

class RAGPipeline:
    """
    Full RAG pipeline for research Q&A.
    
    Flow:
    1. Query Understanding (optional rewrite)
    2. Hybrid Retrieval (BM25 + Vector)
    3. Reranking (Cross-encoder)
    4. Answer Generation (with citations)
    
    Usage:
        rag = RAGPipeline(retriever, reranker, generator)
        response = await rag.query("What are the latest RAG techniques?")
    """
    
    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        generator: AnswerGenerator
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.generator = generator
    
    async def query(
        self,
        question: str,
        top_k: int = 10,
        rerank_top_k: int = 5,
        filters: dict | None = None
    ) -> RAGResponse:
        """
        Answer a question using the knowledge base.
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve
            rerank_top_k: Number of documents after reranking
            filters: Optional filters (date, category, etc.)
        """
        # 1. Retrieve relevant documents
        retrieved = await self.retriever.retrieve(
            query=question,
            top_k=top_k,
            filters=filters
        )
        
        if not retrieved:
            return RAGResponse(
                answer="I couldn't find relevant information to answer this question.",
                sources=[],
                confidence=0.0
            )
        
        # 2. Rerank for relevance
        reranked = await self.reranker.rerank(
            query=question,
            documents=retrieved,
            top_k=rerank_top_k
        )
        
        # 3. Generate answer with citations
        answer, citations = await self.generator.generate(
            query=question,
            context=reranked
        )
        
        # 4. Build response
        sources = [
            {
                "id": doc.id,
                "type": doc.source_type,
                "title": doc.title,
                "url": doc.url,
                "relevance_score": doc.score
            }
            for doc in reranked
        ]
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            confidence=self._calculate_confidence(reranked)
        )
    
    def _calculate_confidence(self, documents: list) -> float:
        """Calculate confidence based on retrieval scores."""
        if not documents:
            return 0.0
        
        # Average of top 3 scores
        top_scores = [d.score for d in documents[:3]]
        return sum(top_scores) / len(top_scores)


# src/rag/retriever.py

class HybridRetriever:
    """
    Hybrid retrieval combining:
    - BM25 (keyword matching)
    - Vector search (semantic similarity)
    """
    
    def __init__(
        self,
        vector_store: QdrantClient,
        bm25_index: BM25Index,
        embedding_model: EmbeddingModel
    ):
        self.vector_store = vector_store
        self.bm25 = bm25_index
        self.embeddings = embedding_model
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
        alpha: float = 0.5  # Balance between BM25 and vector
    ) -> list[RetrievedDocument]:
        """
        Retrieve documents using hybrid approach.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Qdrant filters
            alpha: Weight for vector search (1-alpha for BM25)
        """
        # Get query embedding
        query_embedding = await self.embeddings.embed(query)
        
        # Vector search
        vector_results = await self.vector_store.search(
            collection_name="papers",  # or "repositories"
            query_vector=query_embedding,
            limit=top_k * 2,
            query_filter=self._build_filter(filters)
        )
        
        # BM25 search
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        
        # Merge and rerank using Reciprocal Rank Fusion
        merged = self._rrf_merge(
            vector_results,
            bm25_results,
            alpha=alpha
        )
        
        return merged[:top_k]
    
    def _rrf_merge(
        self,
        vector_results: list,
        bm25_results: list,
        alpha: float,
        k: int = 60
    ) -> list[RetrievedDocument]:
        """
        Merge results using Reciprocal Rank Fusion.
        
        RRF score = sum(1 / (k + rank))
        """
        scores = {}
        
        # Score vector results
        for rank, doc in enumerate(vector_results):
            doc_id = doc.id
            scores[doc_id] = scores.get(doc_id, 0) + alpha / (k + rank)
            
        # Score BM25 results
        for rank, doc in enumerate(bm25_results):
            doc_id = doc.id
            scores[doc_id] = scores.get(doc_id, 0) + (1 - alpha) / (k + rank)
        
        # Sort by combined score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        # Build result list
        # ... (fetch full documents by IDs)
        pass


# src/rag/generator.py

GENERATION_PROMPT = """
You are a research assistant. Answer the question based on the provided context.

Rules:
1. Only use information from the provided context
2. Cite sources using [1], [2], etc.
3. If you're not sure, say so
4. Be concise but thorough

Context:
{context}

Question: {question}

Answer:
"""

class AnswerGenerator:
    """
    Generates answers with citations from retrieved context.
    """
    
    def __init__(self, llm_client: BaseLLMClient):
        self.llm = llm_client
    
    async def generate(
        self,
        query: str,
        context: list[RetrievedDocument]
    ) -> tuple[str, list[dict]]:
        """
        Generate answer with citations.
        
        Returns:
            Tuple of (answer_text, citations_list)
        """
        # Format context
        context_str = self._format_context(context)
        
        prompt = GENERATION_PROMPT.format(
            context=context_str,
            question=query
        )
        
        response = await self.llm.generate(
            prompt,
            max_tokens=1000,
            temperature=0.3
        )
        
        # Extract citations
        citations = self._extract_citations(response, context)
        
        return response, citations
    
    def _format_context(self, documents: list[RetrievedDocument]) -> str:
        """Format documents as numbered context."""
        parts = []
        for i, doc in enumerate(documents, 1):
            parts.append(f"[{i}] {doc.title}\n{doc.content[:500]}...")
        return "\n\n".join(parts)
    
    def _extract_citations(
        self,
        answer: str,
        documents: list[RetrievedDocument]
    ) -> list[dict]:
        """Extract which documents were cited in the answer."""
        import re
        
        # Find all [N] citations
        citation_pattern = re.compile(r'\[(\d+)\]')
        cited_indices = set(int(m) for m in citation_pattern.findall(answer))
        
        citations = []
        for idx in sorted(cited_indices):
            if 1 <= idx <= len(documents):
                doc = documents[idx - 1]
                citations.append({
                    "index": idx,
                    "document_id": doc.id,
                    "title": doc.title,
                    "url": doc.url
                })
        
        return citations
```

---

### 4. API Endpoints

```python
# src/api/routers/papers.py

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

router = APIRouter(prefix="/papers", tags=["Papers"])

@router.get("/", response_model=PaginatedResponse[PaperResponse])
async def list_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    topic: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    has_code: Optional[bool] = None,
    is_vietnamese: Optional[bool] = None,
    sort_by: str = Query("published_date", enum=["published_date", "citations", "trending"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    service: PaperService = Depends(get_paper_service)
):
    """
    List papers with filtering and pagination.
    """
    papers, total = await service.list_papers(
        skip=skip,
        limit=limit,
        filters={
            "category": category,
            "topic": topic,
            "date_from": date_from,
            "date_to": date_to,
            "has_code": has_code,
            "is_vietnamese": is_vietnamese
        },
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return PaginatedResponse(
        items=[PaperResponse.from_model(p) for p in papers],
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{paper_id}", response_model=PaperDetailResponse)
async def get_paper(
    paper_id: str,
    service: PaperService = Depends(get_paper_service)
):
    """
    Get paper details including linked repositories.
    """
    paper = await service.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get linked repos
    links = await service.get_paper_links(paper_id)
    
    return PaperDetailResponse(
        paper=PaperResponse.from_model(paper),
        linked_repos=[LinkResponse.from_model(l) for l in links]
    )

@router.get("/{paper_id}/similar", response_model=list[PaperResponse])
async def get_similar_papers(
    paper_id: str,
    limit: int = Query(5, ge=1, le=20),
    service: PaperService = Depends(get_paper_service)
):
    """
    Find semantically similar papers.
    """
    similar = await service.find_similar(paper_id, limit=limit)
    return [PaperResponse.from_model(p) for p in similar]


# src/api/routers/search.py

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2),
    type: Optional[str] = Query(None, enum=["papers", "repos", "all"]),
    limit: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service)
):
    """
    Full-text and semantic search across papers and repositories.
    """
    results = await service.search(
        query=q,
        entity_types=[type] if type and type != "all" else ["papers", "repos"],
        limit=limit
    )
    
    return SearchResponse(
        query=q,
        results=results,
        total=len(results)
    )


# src/api/routers/trending.py

router = APIRouter(prefix="/trending", tags=["Trending"])

@router.get("/papers", response_model=list[TrendingPaperResponse])
async def get_trending_papers(
    period: str = Query("week", enum=["day", "week", "month"]),
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    service: TrendingService = Depends(get_trending_service)
):
    """
    Get trending papers by citation velocity.
    """
    return await service.get_trending_papers(
        period=period,
        category=category,
        limit=limit
    )

@router.get("/repos", response_model=list[TrendingRepoResponse])
async def get_trending_repos(
    period: str = Query("week", enum=["day", "week", "month"]),
    language: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    service: TrendingService = Depends(get_trending_service)
):
    """
    Get trending repositories by star velocity.
    """
    return await service.get_trending_repos(
        period=period,
        language=language,
        topic=topic,
        limit=limit
    )

@router.get("/tech-radar", response_model=TechRadarResponse)
async def get_tech_radar(
    period: str = Query("month", enum=["week", "month", "quarter"]),
    service: TrendingService = Depends(get_trending_service)
):
    """
    Get technology radar - emerging and declining technologies.
    """
    return await service.get_tech_radar(period=period)


# src/api/routers/chat.py

router = APIRouter(prefix="/chat", tags=["RAG Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Ask questions about the research knowledge base.
    
    Example questions:
    - "What are the latest advances in RAG techniques?"
    - "Compare FlashAttention and PagedAttention"
    - "Find papers about Vietnamese NLP with code"
    """
    response = await rag.query(
        question=request.question,
        filters=request.filters
    )
    
    return ChatResponse(
        answer=response.answer,
        sources=response.sources,
        confidence=response.confidence
    )


# src/api/routers/reports.py

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(
    week: Optional[date] = None,  # Start of week, defaults to current
    topics: Optional[list[str]] = Query(None),
    service: ReportService = Depends(get_report_service)
):
    """
    Get weekly digest report.
    """
    return await service.get_weekly_report(
        week=week or get_week_start(date.today()),
        topics=topics
    )

@router.post("/generate", response_model=ReportGenerationResponse)
async def generate_report(
    request: ReportGenerationRequest,
    service: ReportService = Depends(get_report_service)
):
    """
    Generate custom report on specific topic/time range.
    """
    report_id = await service.generate_report(
        topic=request.topic,
        date_from=request.date_from,
        date_to=request.date_to,
        format=request.format  # markdown, pdf
    )
    
    return ReportGenerationResponse(
        report_id=report_id,
        status="generating",
        estimated_time_seconds=30
    )

@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format: str = Query("markdown", enum=["markdown", "pdf"]),
    service: ReportService = Depends(get_report_service)
):
    """
    Download generated report.
    """
    content, filename = await service.get_report_file(report_id, format)
    
    media_type = "text/markdown" if format == "markdown" else "application/pdf"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# src/api/routers/alerts.py

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/", response_model=list[AlertResponse])
async def list_alerts(
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_read: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    service: AlertService = Depends(get_alert_service)
):
    """
    List recent alerts.
    """
    return await service.list_alerts(
        alert_type=alert_type,
        severity=severity,
        is_read=is_read,
        limit=limit
    )

@router.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    request: SubscribeRequest,
    service: AlertService = Depends(get_alert_service)
):
    """
    Subscribe to alerts for a topic, paper, or repo.
    
    subscription_type: topic, paper, repo, author, keyword
    """
    subscription = await service.create_subscription(
        subscriber_id=request.email,
        subscription_type=request.subscription_type,
        target_value=request.target_value,
        channels=request.channels,
        frequency=request.frequency
    )
    
    return SubscriptionResponse.from_model(subscription)
```

---

## ⚙️ Configuration

```python
# src/core/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "OSINT Research"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/osint"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    
    # API Keys
    GITHUB_TOKEN: str
    SEMANTIC_SCHOLAR_API_KEY: str | None = None
    HUGGINGFACE_TOKEN: str | None = None
    OPENAI_API_KEY: str | None = None
    
    # LLM Settings
    LOCAL_LLM_URL: str = "http://localhost:11434"  # Ollama
    LOCAL_LLM_MODEL: str = "llama3:8b-instruct-q4_K_M"
    CLOUD_LLM_MODEL: str = "gpt-4o"
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "BAAI/bge-base-en-v1.5"
    EMBEDDING_DIMENSION: int = 768
    
    # Collection Settings
    ARXIV_CATEGORIES: list[str] = ["cs.AI", "cs.CL", "cs.CV", "cs.LG"]
    COLLECTION_INTERVAL_HOURS: int = 6
    
    # Rate Limits
    GITHUB_REQUESTS_PER_HOUR: int = 5000
    S2_REQUESTS_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```env
# .env.example

# App
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://osint:password@postgres:5432/osint

# Redis
REDIS_URL=redis://redis:6379/0

# Vector DB
QDRANT_URL=http://qdrant:6333

# API Keys (Required)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# API Keys (Optional - improves rate limits)
SEMANTIC_SCHOLAR_API_KEY=
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# LLM Settings
LOCAL_LLM_URL=http://ollama:11434
LOCAL_LLM_MODEL=llama3:8b-instruct-q4_K_M
CLOUD_LLM_MODEL=gpt-4o

# Embedding
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
```

---

## 🐳 Docker Setup

```yaml
# docker-compose.yml

version: '3.8'

services:
  # Main application
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://osint:password@postgres:5432/osint
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - LOCAL_LLM_URL=http://ollama:11434
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
      - qdrant
      - ollama
    volumes:
      - ./src:/app/src
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  # Celery Worker
  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql+asyncpg://osint:password@postgres:5432/osint
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - LOCAL_LLM_URL=http://ollama:11434
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
      - qdrant
      - ollama
    command: celery -A src.workers.celery_app worker --loglevel=info --concurrency=4

  # Celery Beat (Scheduler)
  beat:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - redis
      - worker
    command: celery -A src.workers.celery_app beat --loglevel=info

  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: osint
      POSTGRES_PASSWORD: password
      POSTGRES_DB: osint
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  # Qdrant Vector DB
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"

  # Ollama (Local LLM)
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Frontend (Next.js)
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  ollama_data:
```

```dockerfile
# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📅 Development Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Setup Docker environment
- [ ] Initialize PostgreSQL schema
- [ ] Setup Qdrant collections
- [ ] Configure Celery + Redis
- [ ] Basic FastAPI skeleton
- [ ] Logging and error handling

### Phase 2: Data Collection (Week 3-5)
- [ ] ArXiv Collector
- [ ] GitHub Collector
- [ ] Semantic Scholar Collector
- [ ] Hugging Face Collector
- [ ] Papers With Code Client
- [ ] Rate limiting & retry logic
- [ ] Celery scheduled tasks

### Phase 3: Processing Pipeline (Week 6-8)
- [ ] LLM client (Ollama + OpenAI)
- [ ] Topic Classifier
- [ ] Summarizer
- [ ] Entity Extractor
- [ ] Paper-Code Linker
- [ ] Embedding Generator
- [ ] Vietnamese NLP support

### Phase 4: API & Basic UI (Week 9-10)
- [ ] Complete REST API
- [ ] Search endpoints
- [ ] Trending endpoints
- [ ] Next.js dashboard setup
- [ ] Paper/Repo list views
- [ ] Basic search UI

### Phase 5: Intelligence Features (Week 11-13)
- [ ] RAG pipeline
- [ ] Chat interface
- [ ] Trending calculations
- [ ] Tech Radar
- [ ] SOTA Shift detection
- [ ] Alert system

### Phase 6: Reports & Polish (Week 14-16)
- [ ] Weekly digest generation
- [ ] PDF export
- [ ] Email notifications
- [ ] Dashboard charts
- [ ] Performance optimization
- [ ] Documentation

---

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourname/osint-research.git
cd osint-research

# 2. Copy environment file
cp .env.example .env
# Edit .env with your API keys

# 3. Start services
docker-compose up -d

# 4. Run migrations
docker-compose exec app alembic upgrade head

# 5. Pull Ollama model
docker-compose exec ollama ollama pull llama3:8b-instruct-q4_K_M

# 6. Initialize Qdrant collections
docker-compose exec app python scripts/init_qdrant.py

# 7. Seed initial data (optional)
docker-compose exec app python scripts/seed_data.py

# 8. Access services
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Frontend: http://localhost:3000
# Qdrant UI: http://localhost:6333/dashboard
```

---

## 📊 Monitoring

```python
# Key metrics to track

METRICS = {
    # Collection
    "papers_collected_total": Counter,
    "repos_collected_total": Counter,
    "collection_duration_seconds": Histogram,
    "collection_errors_total": Counter,
    
    # Processing
    "papers_processed_total": Counter,
    "processing_duration_seconds": Histogram,
    "llm_inference_duration_seconds": Histogram,
    
    # API
    "api_requests_total": Counter,
    "api_latency_seconds": Histogram,
    
    # Queue
    "celery_queue_length": Gauge,
    "celery_task_duration_seconds": Histogram,
    
    # Storage
    "database_connections_active": Gauge,
    "vector_store_documents_total": Gauge
}
```

---

## 📝 License

MIT License - feel free to use and modify.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

**Happy Vibe Coding! 🚀**
