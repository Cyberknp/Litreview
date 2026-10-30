from hybrid_search import hybrid_search


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


if __name__ == "__main__":
    output = prepare_rag_prompt(
        "What are the symptoms of a heart attack?"
    )

    print(output["prompt"])