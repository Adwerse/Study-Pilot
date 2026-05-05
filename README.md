# StudyPilot

## Vector Store

Sprint 5 uses `pgvector` as the primary vector store. It was chosen because
the project already runs on PostgreSQL, deployment stays simpler, and it is
enough for the MVP RAG workload.

Local development uses the `pgvector/pgvector:pg16` Docker image. The document
migration enables the `vector` extension and creates `document_chunks.embedding`
as `vector(1536)`, which must stay aligned with `EMBEDDING_DIMENSIONS`.

Relevant settings:
- `VECTOR_STORE_PROVIDER=pgvector`
- `EMBEDDING_DIMENSIONS=1536`
- `VECTOR_SEARCH_TOP_K_DEFAULT=8`
- `VECTOR_SEARCH_SCORE_THRESHOLD=0.2`
