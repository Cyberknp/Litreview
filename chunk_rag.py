from chunk_search import chunk_search
from llm_client import generate_response
from rag_pipeline import build_prompt


def build_chunk_context(results: list[dict]) -> str:
    context_parts = []

    for index, chunk in enumerate(results, start=1):
        title = chunk.get("title", "Untitled")
        chunk_text = chunk.get("chunk_text", "No text available")

        context_parts.append(
            f"""
Source {index}
Title: {title}
Passage: {chunk_text}
"""
        )

    return "\n".join(context_parts)


def answer_with_chunks(question: str, limit: int = 5) -> dict:
    results = chunk_search(question, limit=limit)

    if not results:
        return {
            "question": question,
            "answer": "I could not find relevant research sources.",
            "sources": [],
        }

    context = build_chunk_context(results)
    prompt = build_prompt(question, context)
    answer = generate_response(prompt)

    return {
        "question": question,
        "answer": answer,
        "sources": results,
    }


if __name__ == "__main__":
    result = answer_with_chunks(
        "How can artificial intelligence support clinical diagnosis?"
    )

    print("\nQUESTION:")
    print(result["question"])

    print("\nGENERATED ANSWER:")
    print(result["answer"])

    print("\nSOURCES:")
    for source in result["sources"]:
        print("-", source["title"], f"(chunk {source['chunk_id']})")
