"""GitHub Discussions API client via GraphQL."""

from datetime import datetime

import httpx

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

TARGET_REPOS = [
    "huggingface/transformers",
    "langchain-ai/langchain",
    "openai/openai-python",
    "pytorch/pytorch",
    "tensorflow/tensorflow",
    "microsoft/autogen",
    "run-llama/llama_index",
    "vllm-project/vllm",
    "ggerganov/llama.cpp",
    "mlflow/mlflow",
]

SEARCH_QUERY = """
query($query: String!, $first: Int!, $after: String) {
  search(query: $query, type: DISCUSSION, first: $first, after: $after) {
    discussionCount
    edges {
      node {
        ... on Discussion {
          id
          title
          body
          url
          createdAt
          upvoteCount
          author {
            login
          }
          category {
            name
          }
          labels(first: 10) {
            nodes {
              name
            }
          }
          comments(first: 3) {
            totalCount
            nodes {
              body
              createdAt
              author {
                login
              }
            }
          }
          repository {
            nameWithOwner
          }
          answer {
            id
          }
        }
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""


async def fetch_github_discussions(
    token: str,
    query: str = "AI",
    repos: list[str] | None = None,
    limit: int = 50,
) -> list[dict]:
    """Fetch GitHub Discussions via GraphQL and normalize to GitHubDiscussion format."""
    target_repos = repos or TARGET_REPOS
    all_discussions = []
    seen_ids: set[str] = set()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        for repo in target_repos:
            search_query = f"repo:{repo} {query}"
            after = None

            while len(all_discussions) < limit:
                variables = {
                    "query": search_query,
                    "first": min(25, limit - len(all_discussions)),
                    "after": after,
                }

                try:
                    resp = await client.post(
                        GITHUB_GRAPHQL_URL,
                        headers=headers,
                        json={"query": SEARCH_QUERY, "variables": variables},
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    search_data = data.get("data", {}).get("search", {})
                    edges = search_data.get("edges", [])

                    if not edges:
                        break

                    for edge in edges:
                        node = edge.get("node") or {}
                        disc_id = node.get("id", "")
                        if not disc_id or disc_id in seen_ids:
                            continue
                        seen_ids.add(disc_id)

                        created_at_str = node.get("createdAt")
                        published_at = None
                        if created_at_str:
                            try:
                                dt = datetime.fromisoformat(
                                    created_at_str.replace("Z", "+00:00")
                                )
                                published_at = dt.replace(tzinfo=None)
                            except (ValueError, TypeError):
                                pass

                        author_data = node.get("author") or {}
                        category_data = node.get("category") or {}
                        labels_data = node.get("labels", {}).get("nodes", [])
                        comments_data = node.get("comments") or {}
                        repo_data = node.get("repository") or {}

                        top_comments = [
                            {
                                "body": c.get("body", "")[:500],
                                "author": (c.get("author") or {}).get("login", ""),
                                "created_at": c.get("createdAt"),
                            }
                            for c in comments_data.get("nodes", [])
                        ]

                        all_discussions.append({
                            "discussion_id": disc_id,
                            "repo_full_name": repo_data.get("nameWithOwner", repo),
                            "title": node.get("title", ""),
                            "body": (node.get("body") or "")[:2000],
                            "url": node.get("url", ""),
                            "author": author_data.get("login", ""),
                            "category": category_data.get("name"),
                            "labels": [l.get("name", "") for l in labels_data],
                            "upvotes": node.get("upvoteCount", 0),
                            "comments_count": comments_data.get("totalCount", 0),
                            "answer_chosen": node.get("answer") is not None,
                            "top_comments": top_comments,
                            "published_at": published_at,
                        })

                    page_info = search_data.get("pageInfo", {})
                    if not page_info.get("hasNextPage"):
                        break
                    after = page_info.get("endCursor")

                except Exception:
                    break

    return all_discussions[:limit]
