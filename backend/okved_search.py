from sqlalchemy import select, text

from models import Okved

MODEL_NAME = "intfloat/multilingual-e5-base"

_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def encode_passages(names):
    passages = [f"passage: {name}" for name in names]
    vectors = get_model().encode(
        passages,
        batch_size=64,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vectors.tolist()


def encode_query(text):
    vector = get_model().encode(
        f"query: {text}",
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vector.tolist()


HYBRID_SQL = text("""
WITH vec AS (
    SELECT code,
           row_number() OVER (ORDER BY embedding <=> CAST(:vector AS vector)) AS rank
    FROM okved
    ORDER BY embedding <=> CAST(:vector AS vector)
    LIMIT :pool
),
lex AS (
    SELECT code,
           row_number() OVER (
               ORDER BY ts_rank(to_tsvector('russian', name), tsq) DESC
           ) AS rank
    FROM okved,
         to_tsquery(
             'russian',
             array_to_string(
                 tsvector_to_array(to_tsvector('russian', :query)), ' | '
             )
         ) AS tsq
    WHERE to_tsvector('russian', name) @@ tsq
    LIMIT :pool
),
merged AS (
    SELECT COALESCE(vec.code, lex.code) AS code,
           COALESCE(:vector_weight / (:k + vec.rank), 0)
               + COALESCE(:lexical_weight / (:k + lex.rank), 0) AS rrf
    FROM vec
    FULL OUTER JOIN lex ON vec.code = lex.code
)
SELECT okved.code,
       okved.name,
       1 - (okved.embedding <=> CAST(:vector AS vector)) AS score
FROM merged
JOIN okved ON okved.code = merged.code
ORDER BY merged.rrf DESC
LIMIT :limit
""")

MIN_QUERY_LENGTH = 3
POOL_SIZE = 20
RRF_K = 60
VECTOR_WEIGHT = 1.0
LEXICAL_WEIGHT = 0.05


def search(session, query, limit=5):
    query = (query or "").strip()
    if len(query) < MIN_QUERY_LENGTH:
        return []

    vector = encode_query(query)
    rows = session.execute(
        HYBRID_SQL,
        {
            "vector": "[" + ",".join(str(x) for x in vector) + "]",
            "query": query,
            "pool": POOL_SIZE,
            "k": RRF_K,
            "vector_weight": VECTOR_WEIGHT,
            "lexical_weight": LEXICAL_WEIGHT,
            "limit": limit,
        },
    ).all()

    return [
        {"code": row.code, "name": row.name, "score": round(float(row.score), 4)}
        for row in rows
    ]
