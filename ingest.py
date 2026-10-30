from db import get_connection
from semantic_search import client,embed_text,INDEX_NAME
from opensearchpy.helpers import bulk

def fetch_papers():
    conn=get_connection()

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

def ingest_papers():
    papers=fetch_papers()

    actions = []

    for paper in papers:
        # Combine title and abstract for embedding.
        text = (
            f"{paper['title']}\n"
            f"{paper['abstract']}"
        )

        vector = embed_text(text)

        actions.append({
            "_index": INDEX_NAME,
            "_id": str(paper["id"]),
            "_source": {
                "id": paper["id"],
                "title": paper["title"],
                "year": paper["year"],
                "abstract": paper["abstract"],
                "text_vector": vector,
            },
        })

    if not actions:
        print("No papers found.")
        return

    success, errors = bulk(
        client,
        actions,
        refresh=True,
        raise_on_error=False,
    )

    print(f"Successfully indexed: {success}")
    print(f"Failed documents: {len(errors)}")

    if errors:
        print(errors)


if __name__ == "__main__":
    ingest_papers()