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

RELEVANCE_PROMPT = """
Given a research paper's title and abstract, determine if it is relevant to
AI/ML research with practical applications.

Title: {title}
Abstract: {abstract}

Respond with JSON:
{{
    "is_relevant": true/false,
    "relevance_score": <0.0-1.0>,
    "reason": "<brief reason>"
}}
"""
