ENTITY_EXTRACTION_PROMPT = """
Extract key entities from this research paper:

Title: {title}
Abstract: {abstract}

Extract the following entities:
1. Methods/Models: Named models, architectures, or methods
2. Datasets: Named datasets used
3. Metrics: Performance metrics mentioned
4. Tools/Frameworks: Software tools or frameworks

Respond with JSON:
{{
    "methods": ["<method name>", ...],
    "datasets": ["<dataset name>", ...],
    "metrics": ["<metric name>", ...],
    "tools": ["<tool/framework>", ...]
}}
"""

TECH_ANALYSIS_PROMPT = """
Analyze the technology stack used in this repository:

Repository: {repo_name}
Description: {description}
Primary Language: {language}
Dependencies: {dependencies}

Identify:
1. Core frameworks and libraries
2. Architecture patterns
3. ML/AI techniques used

Respond with JSON:
{{
    "frameworks": ["<framework>", ...],
    "patterns": ["<pattern>", ...],
    "techniques": ["<technique>", ...],
    "category": "<main category>"
}}
"""
