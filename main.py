from fastapi import FastAPI

app=FastAPI(title="Litreview:Research paper review")

papers = [
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
]

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/papers")
def get_papers():
    return {"papers": papers}

@app.get("/search")
def search_papers(q:str):
    results=[
        paper for paper in papers if q.lower() in paper["title"].lower()
    ]

    return {"query": q, "results": results}