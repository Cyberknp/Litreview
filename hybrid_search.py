from semantic_search import (
    client,
    embed_text,
    INDEX_NAME,
)

RRF_K = 60


def hybrid_search(query: str, limit: int = 5) -> list[dict]:
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100")

    keyword_response = client.search(
        index=INDEX_NAME,
        body={
            "size": limit,
            "_source": ["id", "title", "abstract", "year"],
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "abstract"],
                    "type": "best_fields",
                }
            },
        },
    )

    query_vector = embed_text(query)

    vector_response = client.search(
        index=INDEX_NAME,
        body={
            "size": limit,
            "_source": ["id", "title", "abstract", "year"],
            "query": {
                "knn": {
                    "text_vector": {
                        "vector": query_vector,
                        "k": limit,
                    }
                }
            },
        },
    )

    fused: dict[str, dict] = {}

    for response in (keyword_response, vector_response):
        for rank, hit in enumerate(response["hits"]["hits"], start=1):
            doc_id = hit["_id"]

            if doc_id not in fused:
                fused[doc_id] = {
                    **hit["_source"],
                    "score": 0.0,
                }

            fused[doc_id]["score"] += 1.0 / (RRF_K + rank)

    results = sorted(
        fused.values(),
        key=lambda paper: paper["score"],
        reverse=True,
    )

    return results[:limit]


if __name__ == "__main__":
    for result in hybrid_search("heart attack diagnosis"):
        print(result)
