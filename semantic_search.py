
from sentence_transformers import SentenceTransformer
from opensearchpy import OpenSearch

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_NAME = "research-papers-semantic"

model = SentenceTransformer(MODEL_NAME)

papers = [
    {
        "id": 1,
        "title": "Large Language Models in Medical Diagnosis",
        "abstract": (
            "Language models support clinical reasoning "
            "and medical question answering."
        ),
        "year": 2025,
    },
    {
        "id": 2,
        "title": "Retrieval-Augmented Generation for Research",
        "abstract": (
            "Retrieving external documents can ground "
            "language model responses in evidence."
        ),
        "year": 2024,
    },
    {
        "id": 3,
        "title": "Myocardial Infarction: Diagnosis and Treatment",
        "abstract": (
            "Heart attacks require timely recognition, "
            "clinical evaluation, and appropriate treatment."
        ),
        "year": 2025,
    },
    {
        "id": 4,
        "title": "Deep Learning for Medical Image Analysis",
        "abstract": (
            "Neural networks help interpret medical images."
        ),
        "year": 2023,
    },
]


def embed_text(text: str) -> list[float]:
    vector = model.encode(
        text,
        normalize_embeddings=True,
    )
    return vector.tolist()


def create_index():
    if client.indices.exists(index=INDEX_NAME):
        print("Semantic index already exists.")
        return

    client.indices.create(
        index=INDEX_NAME,
        body={
            "settings": {
                "index": {"knn": True}
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "text"},
                    "abstract": {"type": "text"},
                    "year": {"type": "integer"},
                    "text_vector": {
                        "type": "knn_vector",
                        "dimension": 384,
                        "method": {
                            "name": "hnsw",
                            "engine": "lucene",
                            "space_type": "cosinesimil",
                        },
                    },
                }
            },
        },
    )

    print("Semantic index created.")


def index_papers():
    for paper in papers:
        text = paper["title"] + ". " + paper["abstract"]
        vector = embed_text(text)

        document = {
            **paper,
            "text_vector": vector,
        }

        client.index(
            index=INDEX_NAME,
            id=paper["id"],
            body=document,
        )

    client.indices.refresh(index=INDEX_NAME)
    print(f"Indexed {len(papers)} papers.")


def semantic_search(query: str, k: int = 3):
    query_vector = embed_text(query)

    response = client.search(
        index=INDEX_NAME,
        body={
            "size": k,
            "query": {
                "knn": {
                    "text_vector": {
                        "vector": query_vector,
                        "k": k,
                    }
                }
            },
            "_source": [
                "id",
                "title",
                "abstract",
                "year",
            ],
        },
    )

    return [
        {
            **hit["_source"],
            "score": hit["_score"],
        }
        for hit in response["hits"]["hits"]
    ]


if __name__ == "__main__":
    create_index()
    index_papers()

    results = semantic_search("heart attack diagnosis")

    for result in results:
        print(result)
