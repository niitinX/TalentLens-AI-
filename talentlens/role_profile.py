from __future__ import annotations

from pathlib import Path

ROLE_NAME = "Intelligent Candidate Discovery & Ranking"

DEFAULT_JOB_DESCRIPTION_PATHS = (
    Path("India_runs_data_and_ai_challenge") / "job_description.docx",
    Path("job_description.docx"),
)

POSITIVE_CAREER_TERMS = {
    "machine learning",
    "ml",
    "llm",
    "retrieval",
    "ranking",
    "search",
    "recommendation",
    "embedding",
    "embeddings",
    "nlp",
    "information retrieval",
    "recommender",
    "vector",
    "semantic search",
    "hybrid search",
    "dense retrieval",
    "hybrid retrieval",
    "rerank",
    "re-ranking",
    "production",
    "deployed",
    "scaled",
    "launched",
    "optimized",
    "evaluation",
    "ndcg",
    "mrr",
    "map",
    "ab test",
    "a/b",
    "lora",
    "qlora",
    "peft",
    "sentence-transformers",
    "bge",
    "e5",
    "faiss",
    "milvus",
    "pinecone",
    "weaviate",
    "qdrant",
    "opensearch",
    "elasticsearch",
    "fastapi",
    "spark",
    "airflow",
    "python",
    "pytorch",
    "tensorflow",
}

NEGATIVE_TITLES = {
    "hr",
    "human resources",
    "content writer",
    "marketing",
    "sales",
    "talent acquisition",
    "recruiter",
    "operations manager",
    "project manager",
    "customer support",
    "graphic designer",
    "accountant",
    "civil engineer",
    "mechanical engineer",
}

RESEARCH_ONLY_TERMS = {
    "research only",
    "academic",
    "phd",
    "professor",
    "paper",
    "publication",
    "theory",
}

PRODUCT_TERMS = {
    "product",
    "production",
    "real users",
    "ship",
    "deployed",
    "scaled",
    "launched",
    "end-to-end",
    "platform",
    "search",
    "ranking",
    "recommendation",
}
