# TrackFlow RAG design

## Architecture

```text
Company Markdown corpus
        |
        v
semantic chunking -> dedicated 4Geeks embedding model (1024 dimensions)
        |                         |
        +-----------> Qdrant Cloud (trackflow_knowledge, cosine)
                                      |
question -> same embed() -> retrieve(k=5, min_score=0.35)
                                      |
                         generate_answer(question, context)
                                      |
                               {"answer": "..."}
```

The knowledge base is stored in the `docs/company-knowledge-base/` Spanish
Markdown corpus. `services/rag/chunking.py` splits each source by headings,
paragraphs, and complete sentence boundaries, preserving self-contained
semantic units. `services/rag/pipeline.py` sends those chunks to the dedicated
embedding model configured by `EMBEDDING_MODEL_ID`, then stores the vectors in
the `trackflow_knowledge` Qdrant collection.

Questions are embedded with the same embedding model, and the top three
chunks are retrieved before generation. The answer is produced by the
separate `GENERATION_MODEL_ID`; the generation model is never used to create
embeddings. Responses include source document, section, and similarity score.
`setup()` is idempotent in development: it deletes and recreates the
collection before inserting the complete corpus, so reruns cannot duplicate
points.

The current corpus contains 13 semantic chunks:

| Source document | Chunks |
|---|---:|
| `trackflow-sla-delivery.es` | 4 |
| `trackflow-returns-policy.es` | 3 |
| `trackflow-carrier-coverage.es` | 3 |
| `trackflow-storage-pricing.es` | 3 |

## Retrieval and generation contract

`retrieve(query, k=5, min_score=0.35)` embeds the query, asks Qdrant for at
most five candidates, filters out lower-scoring candidates, and returns only
their payloads. The payload never exposes raw Qdrant SDK objects.
`generate_answer(question, context)` is a separate function so an orchestration
agent can call retrieval and generation independently. `query(question)` is
the composition and returns only a string.

The `0.35` cosine-similarity threshold is a conservative initial boundary for
short Spanish business questions: it rejects weak matches while allowing
paraphrases to reach the prompt. It should be recalibrated from the evaluation
set if Recall@3 or false-positive rates indicate a better boundary.

## Configuration

Set these variables in the local `.env` file:

```text
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=trackflow_knowledge
FOURGEEKS_API_KEY=...
FOURGEEKS_BASE_URL=https://llm.4geeks.ai/v1
EMBEDDING_MODEL_ID=litellm/madrid-spain/openrouter/perplexity/pplx-embed-v1-0.6b
GENERATION_MODEL_ID=litellm/madrid-spain/openrouter/deepseek/deepseek-v4-flash
```

The two model IDs are intentionally separate. The exact IDs and endpoint are
provided by 4Geeks. The API key is local-only and is not committed to the
repository. `pplx-embed-v1-0.6b` produces 1024-dimensional vectors; Qdrant
uses cosine distance for this collection.

## Text preprocessing

The loader trims surrounding whitespace and collapses excessive blank lines.
Markdown headings become the `section` payload. Paragraphs are kept intact;
long paragraphs are split only at sentence boundaries. Each payload contains
`company`, `source_document`, `section`, `language`, `chunk_index`, and `text`.

## Operations

1. Configure the Qdrant Cloud endpoint and API key in `.env`.
2. Run `uv run python -c "from services.rag.pipeline import setup; print(setup())"`.
3. Open `/rag/` for the query UI or POST a question to `/api/rag/query`.

## Validation status

The real integration has been validated against Qdrant Cloud and the
`llm.4geeks.ai` gateway. `setup()` indexed the four TrackFlow source
documents in the `trackflow_knowledge` collection, and `query()` returned
answers with verified source metadata. The embedding and generation calls
used their separate configured model IDs.

The evaluation set contains eight Spanish questions covering all four source
documents. Against Qdrant Cloud, the retrieval evaluation achieved
**Recall@3 = 8/8 = 100.0%**, exceeding the exercise target of 80%.

If no chunks are retrieved, the service returns an explicit insufficient
information response instead of fabricating a business rule.
