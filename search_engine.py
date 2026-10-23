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


ADVANCED_INDEX = "research-papers-v2"

def create_advanced_index():
    if client.indices.exists(index=ADVANCED_INDEX):
        print("Advanced index already exists.")
        return

    mapping = {
        "properties": {
            "id": {"type": "integer"},
            "title": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                },
            },
            "abstract": {"type": "text"},
            "year": {"type": "integer"},
        }
    }

    client.indices.create(index=ADVANCED_INDEX, body={"mappings": mapping})
    print(f"Advanced index '{ADVANCED_INDEX}' created successfully.")

    
def index_advanced_papers():
    sample_papers = [
        {
            "id": 1,
            "title": "Large Language Models in Medical Diagnosis",
            "abstract": (
                "This study explores language models for "
                "clinical reasoning and medical question answering."
            ),
            "year": 2025,
        },
        {
            "id": 2,
            "title": "Retrieval-Augmented Generation for Research",
            "abstract": (
                "This paper examines retrieving external documents "
                "to ground language model responses."
            ),
            "year": 2024,
        },
        {
            "id": 3,
            "title": "Deep Learning for Medical Image Analysis",
            "abstract": (
                "This study investigates neural networks "
                "for interpreting medical images."
            ),
            "year": 2023,
        },
        {
            "id": 4,
            "title": "RAG Systems for Scientific Discovery",
            "abstract": (
                "This paper explores document retrieval and "
                "language models for scientific literature."
            ),
            "year": 2025,
        },
    ]

    for paper in sample_papers:
        client.index(
            index=ADVANCED_INDEX,
            id=paper["id"],
            body=paper,
        )

    client.indices.refresh(index=ADVANCED_INDEX)
    print("Advanced sample papers indexed.")


def advanced_search(
    query: str,
    year: int | None = None,
    page: int = 1,
    page_size: int = 10,
):
    if page < 1:
        raise ValueError("page must be at least 1")

    if not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100")

    search_query = {
        "multi_match": {
            "query": query,
            "fields": ["title^3", "abstract"],
            "type": "best_fields",
        }
    }

    body = {
        "from": (page - 1) * page_size,
        "size": page_size,
        "query": {
            "bool": {
                "must": [search_query],
            }
        },
        "sort": [
            {"_score": {"order": "desc"}},
            {"id": {"order": "asc"}},
        ],
    }

    if year is not None:
        body["query"]["bool"]["filter"] = [
            {"term": {"year": year}}
        ]

    response = client.search(
        index=ADVANCED_INDEX,
        body=body,
    )

    return {
        "total": response["hits"]["total"]["value"],
        "page": page,
        "page_size": page_size,
        "results": [
            {
                **hit["_source"],
                "score": hit["_score"],
            }
            for hit in response["hits"]["hits"]
        ],
    }


if __name__ == "__main__":
    print(check_connections())
    create_advanced_index()
    index_advanced_papers()

    result = advanced_search(
        query="medical diagnosis",
        year=2025,
        page=1,
        page_size=10,
    )

    print(result)
