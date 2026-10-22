from opensearchpy import OpenSearch 

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

INDEX_NAME = "research-papers"  # Replace with your index name

def check_connections():
    return client.info()

def create_index():
    if client.indices.exists(index=INDEX_NAME):
        print("Index already exists.")
        return

    mapping = {
        "properties": {
            "id": {"type": "integer"},
            "title": {"type": "text"},
            "year": {"type": "integer"},
        }
    }

    client.indices.create(index=INDEX_NAME,body={"mappings": mapping})
    print(f"Index '{INDEX_NAME}' created successfully.")

def index_sample_papers():
    sample_papers = [
        {
            "id": 1,
            "title": "Large Language Models in Medical Diagnosis",
            "year": 2025,
        },
        {
            "id": 2,
            "title": "Retrieval-Augmented Generation for Research",
            "year": 2024,
        },
        {
            "id": 3,
            "title": "Deep Learning for Medical Image Analysis",
            "year": 2023,
        },
        {
            "id": 4,
            "title": "RAG Systems for Scientific Discovery",
            "year": 2025,
        },
    ]

    for paper in sample_papers:
        client.index(
            index=INDEX_NAME,
            id=paper["id"],
            body=paper,
        )

    client.indices.refresh(index=INDEX_NAME)
    print("Four sample papers indexed.")


def search_papers(query: str, size: int = 10):
    response = client.search(
        index=INDEX_NAME,
        body={
            "size": size,
            "query": {
                "match": {
                    "title": {
                        "query": query
                    }
                }
            },
        },
    )

    results = []

    for hit in response["hits"]["hits"]:
        results.append({
            "score": hit["_score"],
            **hit["_source"],
        })

    return results


if __name__ == "__main__":
    print(check_connections())
    create_index()
    index_sample_papers()

    results = search_papers("medical diagnosis")

    for result in results:
        print(result)