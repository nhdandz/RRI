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


# ── Curated GitHub topics for AI/ML repos ──────────────────────────
# Dùng cho: topic distribution chart, frontend filter pills.
# Muốn thêm topic → thêm vào đây, cả backend + frontend tự cập nhật.
KNOWN_TOPICS: list[str] = [
    # --- Core AI/ML ---
    "machine-learning",
    "deep-learning",
    "artificial-intelligence",
    "neural-network",
    "data-science",
    "data-mining",
    "statistics",
    "automl",
    "feature-engineering",
    # --- LLM & NLP ---
    "llm",
    "large-language-models",
    "natural-language-processing",
    "transformers",
    "generative-ai",
    "text-generation",
    "chatbot",
    "chatgpt",
    "gpt",
    "bert",
    "language-model",
    "text-classification",
    "sentiment-analysis",
    "named-entity-recognition",
    "question-answering",
    "summarization",
    "machine-translation",
    "tokenizer",
    "embedding",
    "vector-database",
    "semantic-search",
    # --- RAG & Agents ---
    "rag",
    "retrieval-augmented-generation",
    "ai-agents",
    "autonomous-agents",
    "langchain",
    "llamaindex",
    "function-calling",
    "prompt-engineering",
    "chain-of-thought",
    # --- Computer Vision ---
    "computer-vision",
    "image-classification",
    "object-detection",
    "image-segmentation",
    "image-generation",
    "stable-diffusion",
    "diffusion-model",
    "gan",
    "generative-adversarial-network",
    "ocr",
    "optical-character-recognition",
    "face-recognition",
    "video-understanding",
    "3d-vision",
    "point-cloud",
    # --- Multimodal ---
    "multimodal",
    "vision-language",
    "text-to-image",
    "text-to-video",
    "text-to-speech",
    "speech-recognition",
    "speech-to-text",
    "audio-processing",
    # --- Reinforcement Learning ---
    "reinforcement-learning",
    "rlhf",
    "robotics",
    "gym",
    "simulation",
    # --- Frameworks & Libraries ---
    "pytorch",
    "tensorflow",
    "jax",
    "keras",
    "scikit-learn",
    "huggingface",
    "onnx",
    "mlflow",
    "wandb",
    "ray",
    "triton",
    "vllm",
    "trl",
    # --- MLOps & Infra ---
    "mlops",
    "model-serving",
    "model-deployment",
    "distributed-training",
    "federated-learning",
    "edge-ai",
    "tensorrt",
    "quantization",
    "pruning",
    "knowledge-distillation",
    "model-compression",
    # --- Specific Domains ---
    "recommendation-system",
    "time-series",
    "graph-neural-network",
    "knowledge-graph",
    "anomaly-detection",
    "drug-discovery",
    "bioinformatics",
    "medical-imaging",
    "autonomous-driving",
    "weather-prediction",
    # --- Data ---
    "dataset",
    "benchmark",
    "data-augmentation",
    "synthetic-data",
    "annotation",
    "data-labeling",
    # --- Web Development ---
    "web",
    "frontend",
    "backend",
    "fullstack",
    "react",
    "nextjs",
    "vue",
    "angular",
    "svelte",
    "nodejs",
    "express",
    "fastapi",
    "django",
    "flask",
    "rest-api",
    "graphql",
    "websocket",
    "jamstack",
    "progressive-web-app",
    # --- Mobile ---
    "mobile",
    "android",
    "ios",
    "react-native",
    "flutter",
    "swift",
    "kotlin",
    "cross-platform",
    # --- DevOps & Cloud ---
    "devops",
    "docker",
    "kubernetes",
    "terraform",
    "ansible",
    "ci-cd",
    "github-actions",
    "aws",
    "azure",
    "gcp",
    "serverless",
    "microservices",
    "infrastructure-as-code",
    "monitoring",
    "observability",
    # --- Security ---
    "security",
    "cybersecurity",
    "penetration-testing",
    "vulnerability",
    "cryptography",
    "authentication",
    "oauth",
    "zero-trust",
    "devsecops",
    # --- Blockchain & Web3 ---
    "blockchain",
    "ethereum",
    "solidity",
    "smart-contracts",
    "web3",
    "defi",
    "nft",
    "cryptocurrency",
    # --- Database & Storage ---
    "database",
    "sql",
    "nosql",
    "postgresql",
    "mongodb",
    "redis",
    "elasticsearch",
    "sqlite",
    "data-engineering",
    "etl",
    "data-pipeline",
    "apache-spark",
    "apache-kafka",
    "streaming",
    # --- Systems & Low-level ---
    "rust",
    "golang",
    "cpp",
    "systems-programming",
    "operating-system",
    "compiler",
    "embedded",
    "iot",
    "wasm",
    "webassembly",
    "performance",
    # --- Game Development ---
    "game-development",
    "unity",
    "unreal-engine",
    "godot",
    "game-engine",
    "opengl",
    "vulkan",
    "3d",
    "graphics",
    # --- Design & UI ---
    "design-system",
    "ui",
    "ux",
    "css",
    "tailwindcss",
    "animation",
    "design-tools",
    "figma",
    "accessibility",
    # --- Productivity & Tools ---
    "cli",
    "command-line",
    "developer-tools",
    "automation",
    "testing",
    "linter",
    "formatter",
    "documentation",
    "api",
    "sdk",
    "package-manager",
    "monorepo",
    # --- Scientific Computing ---
    "scientific-computing",
    "physics",
    "chemistry",
    "biology",
    "genomics",
    "astronomy",
    "climate",
    "geospatial",
    "visualization",
    "data-visualization",
    "plotting",
    # --- Education ---
    "education",
    "tutorial",
    "awesome-list",
    "learning-resources",
    "interview-preparation",
    "algorithms",
    "data-structures",
    "competitive-programming",
    "open-source",
]


class LinkType(str, Enum):
    OFFICIAL = "official"
    COMMUNITY = "community"
    MENTIONED = "mentioned"
    INFERRED = "inferred"


class AlertType(str, Enum):
    SOTA_SHIFT = "sota_shift"
    NEW_TRENDING = "new_trending"
    RELEASE_UPDATE = "release_update"
    MILESTONE_REACHED = "milestone_reached"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class EntityType(str, Enum):
    PAPER = "paper"
    REPOSITORY = "repository"


class CrawlJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Source(str, Enum):
    ARXIV = "arxiv"
    GITHUB = "github"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    HUGGINGFACE = "huggingface"
    PAPERS_WITH_CODE = "papers_with_code"
    OJS_VIETNAM = "ojs_vietnam"
