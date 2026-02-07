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
