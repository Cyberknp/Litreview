from hybrid_search import hybrid_search
from llm_client import generate_response 

def build_context(
    results: list[dict],
) -> str:
    context_parts = []

    for index, paper in enumerate(results, start=1):
        title = paper.get("title", "Untitled")
        abstract = paper.get("abstract", "No abstract available")

        context_parts.append(
            f"""
Source {index}
Title: {title}
Abstract: {abstract}
"""
        )

    return "\n".join(context_parts)


def build_prompt(
    question: str,
    context: str,
) -> str:
    return f"""
You are a research assistant.

Answer the question using only the
provided research context.

If the answer is not available in the
context, clearly say that you do not
have enough information.

Question:
{question}

Research context:
{context}

Provide a clear answer and mention
which sources support it.
"""


def prepare_rag_prompt(question: str) -> dict:
    results = hybrid_search(question, limit=5)

    context = build_context(results)

    prompt = build_prompt(question, context)

    return {
        "question": question,
        "retrieved_count": len(results),
        "sources": results,
        "context": context,
        "prompt": prompt,
    }


def answer_question(question: str) -> dict:
    rag_data = prepare_rag_prompt(question)

    if not rag_data["sources"]:
        return {
            "question": question,
            "answer": "I could not find relevant research sources.",
            "sources": [],
        }

    answer = generate_response(rag_data["prompt"])

    return {
        "question": question,
        "answer": answer,
        "sources": rag_data["sources"],
    }


if __name__ == "__main__":
    result = answer_question(
        "What are the symptoms of a heart attack?"
    )

    print("\nQUESTION:")
    print(result["question"])

    print("\nGENERATED ANSWER:")
    print(result["answer"])

    print("\nSOURCES:")
    for source in result["sources"]:
        print("-", source["title"])