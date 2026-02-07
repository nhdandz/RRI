WEEKLY_REPORT_PROMPT = """
Generate a weekly research digest based on the following data:

Period: {period_start} to {period_end}

New Papers ({paper_count} total):
{papers_summary}

Trending Repositories ({repo_count} total):
{repos_summary}

Notable Changes:
{changes_summary}

Write a concise weekly report covering:
1. Key highlights (2-3 most important developments)
2. Trending topics and emerging technologies
3. Notable new papers and their implications
4. Active repositories and community momentum

Format as markdown.
"""

TECH_RADAR_PROMPT = """
Based on the following research trends and repository activity data,
categorize technologies into a Tech Radar format:

Data:
{data}

Categorize each technology into one of:
- ADOPT: Proven, recommended for use
- TRIAL: Worth exploring, showing promise
- ASSESS: Interesting, keep an eye on
- HOLD: Declining or replaced by better alternatives

Respond with JSON:
{{
    "adopt": [{{"name": "...", "reason": "..."}}],
    "trial": [{{"name": "...", "reason": "..."}}],
    "assess": [{{"name": "...", "reason": "..."}}],
    "hold": [{{"name": "...", "reason": "..."}}]
}}
"""
