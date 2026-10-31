from semantic_search import client, embed_text

INDEX_NAME = "research-paper-chunks"


def chunk_search(
    query: str,
    limit: int = 5,
) -> list[dict]:

    if not query.strip():
        raise ValueError("Query cannot be empty")

    query_vector = embed_text(query)

    response = client.search(
        index=INDEX_NAME,
        body={
            "size": limit,
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

    results = []

    for hit in response["hits"]["hits"]:
        source = hit["_source"]

        results.append({
            "paper_id": source["paper_id"],
            "chunk_id": source["chunk_id"],
            "title": source["title"],
            "chunk_text": source["chunk_text"],
            "score": hit["_score"],
        })

    return results


if __name__ == "__main__":
    results = chunk_search(
        "How can artificial intelligence support clinical diagnosis?"
    )

    for result in results:
        print("\nTitle:", result["title"])
        print("Paper ID:", result["paper_id"])
        print("Chunk ID:", result["chunk_id"])
        print("Text:", result["chunk_text"])
        print("Score:", result["score"])