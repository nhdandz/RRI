import re
from collections import Counter

import httpx

HF_API_BASE = "https://huggingface.co/api"

STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "with", "on",
    "is", "are", "was", "were", "be", "been", "being", "by", "at", "from",
    "as", "into", "through", "its", "it", "this", "that", "these", "those",
    "not", "but", "if", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "has", "have", "had", "no",
    "nor", "so", "than", "too", "very", "just", "about", "above", "after",
    "again", "all", "also", "am", "any", "because", "before", "between",
    "both", "each", "few", "further", "here", "how", "i", "me", "more",
    "most", "my", "new", "now", "only", "other", "our", "out", "own",
    "same", "she", "he", "some", "such", "there", "then", "their", "them",
    "they", "we", "what", "when", "where", "which", "while", "who", "whom",
    "why", "you", "your", "up", "down", "over", "under", "using", "via",
    "based", "towards", "toward", "without", "within", "during",
})

POPULAR_PIPELINE_TAGS = [
    "text-generation",
    "text-classification",
    "token-classification",
    "question-answering",
    "summarization",
    "translation",
    "fill-mask",
    "text2text-generation",
    "image-classification",
    "object-detection",
    "image-segmentation",
    "image-to-text",
    "text-to-image",
    "text-to-speech",
    "automatic-speech-recognition",
    "audio-classification",
    "feature-extraction",
    "sentence-similarity",
    "zero-shot-classification",
    "reinforcement-learning",
]


async def get_trending_models(
    task: str | None = None,
    search: str | None = None,
    sort: str = "downloads",
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict], int]:
    params: dict = {
        "sort": sort,
        "direction": "-1",
        "limit": limit,
        "offset": offset,
        "full": "true",
    }
    if task:
        params["filter"] = task
    if search:
        params["search"] = search

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{HF_API_BASE}/models", params=params)
        resp.raise_for_status()
        raw = resp.json()

    models = []
    for m in raw:
        architecture = None
        config = m.get("config") or {}
        architectures = config.get("architectures")
        if architectures and isinstance(architectures, list):
            architecture = architectures[0]

        models.append({
            "model_id": m.get("modelId") or m.get("id", ""),
            "downloads": m.get("downloads", 0),
            "likes": m.get("likes", 0),
            "pipeline_tag": m.get("pipeline_tag"),
            "architecture": architecture,
        })

    # HF API doesn't return total count easily; estimate from results
    total = offset + len(raw)
    if len(raw) == limit:
        total = offset + limit + 1  # signal there are more

    return models, total


async def get_daily_papers() -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{HF_API_BASE}/daily_papers")
        resp.raise_for_status()
        raw = resp.json()

    papers = []
    all_titles: list[str] = []

    for item in raw:
        paper = item.get("paper") or {}
        title = item.get("title") or paper.get("title", "")
        authors_raw = paper.get("authors") or []
        authors = [a.get("name", "") for a in authors_raw if a.get("name")]

        papers.append({
            "title": title,
            "arxiv_id": paper.get("id"),
            "upvotes": item.get("paper", {}).get("upvotes", 0),
            "authors": authors,
            "published_at": paper.get("publishedAt"),
        })
        all_titles.append(title)

    # Keyword trends from titles
    word_counter: Counter[str] = Counter()
    for title in all_titles:
        words = re.findall(r"[a-zA-Z]{3,}", title.lower())
        for w in words:
            if w not in STOPWORDS:
                word_counter[w] += 1

    keyword_trends = [
        {"keyword": kw, "count": cnt}
        for kw, cnt in word_counter.most_common(15)
    ]

    return {
        "papers": papers,
        "keyword_trends": keyword_trends,
    }


async def get_model_detail(model_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{HF_API_BASE}/models/{model_id}")
        resp.raise_for_status()
        m = resp.json()

    architecture = None
    config = m.get("config") or {}
    architectures = config.get("architectures")
    if architectures and isinstance(architectures, list):
        architecture = architectures[0]

    model_type = config.get("model_type")

    # Parameter count from safetensors
    parameter_count = None
    safetensors = m.get("safetensors")
    if safetensors and isinstance(safetensors, dict):
        total = safetensors.get("total")
        if total:
            parameter_count = total

    # Extract languages from tags
    tags = m.get("tags") or []
    languages = [t.replace("language:", "") for t in tags if t.startswith("language:")]

    # License
    license_val = None
    card_data = m.get("cardData") or {}
    license_val = card_data.get("license") or m.get("license")

    author = m.get("author") or (m.get("modelId", "").split("/")[0] if "/" in m.get("modelId", "") else None)

    return {
        "model_id": m.get("modelId") or m.get("id", ""),
        "author": author,
        "downloads": m.get("downloads", 0),
        "likes": m.get("likes", 0),
        "pipeline_tag": m.get("pipeline_tag"),
        "architecture": architecture,
        "model_type": model_type,
        "library_name": m.get("library_name"),
        "tags": tags,
        "languages": languages,
        "license": license_val,
        "parameter_count": parameter_count,
        "created_at": m.get("createdAt"),
        "last_modified": m.get("lastModified"),
    }


def get_model_filters() -> dict:
    return {"pipeline_tags": POPULAR_PIPELINE_TAGS}
