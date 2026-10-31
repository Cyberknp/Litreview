from db import get_connection
from semantic_search import client, embed_text
from chunking import chunk_text
from opensearchpy.helpers import bulk


INDEX_NAME = "research-paper-chunks"


def fetch_papers():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, year, abstract
                FROM papers
                ORDER BY id
            """)

            return cursor.fetchall()

    finally:
        conn.close()


def ingest_chunks():
    papers = fetch_papers()

    actions = []

    for paper in papers:
        paper_id = paper["id"]
        title = paper["title"]
        year = paper["year"]
        abstract = paper["abstract"]

        # Divide the abstract into smaller chunks.
        chunks = chunk_text(
            abstract,
            chunk_size=200,
            overlap=40,
        )

        # Remove old chunks for this paper before re-indexing.
        client.delete_by_query(
            index=INDEX_NAME,
            body={
                "query": {
                    "term": {
                        "paper_id": paper_id
                    }
                }
            },
            refresh=True,
            conflicts="proceed",
        )

        for chunk_id, chunk in enumerate(chunks, start=1):

            # Include title to give the embedding useful context.
            embedding_text = f"{title}\n{chunk}"

            vector = embed_text(embedding_text)

            actions.append({
                "_index": INDEX_NAME,
                "_id": f"{paper_id}_{chunk_id}",
                "_source": {
                    "paper_id": paper_id,
                    "chunk_id": chunk_id,
                    "title": title,
                    "year": year,
                    "chunk_text": chunk,
                    "text_vector": vector,
                },
            })

    if not actions:
        print("No chunks found.")
        return

    success, errors = bulk(
        client,
        actions,
        refresh=True,
        raise_on_error=False,
    )

    print(f"Successfully indexed chunks: {success}")
    print(f"Failed chunks: {len(errors)}")

    if errors:
        print(errors)


if __name__ == "__main__":
    ingest_chunks()