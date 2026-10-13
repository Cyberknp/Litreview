from fastapi import FastAPI
from pydantic import BaseModel

app=FastAPI(title="Litreview:Research paper review")

#defining the structure of a single paper 
class paper(BaseModel):
    id:int
    title:str
    year:int

#defining the structure the /paper api gets 
class PaperResponse(BaseModel):
    papers:list[paper]

class SearchResponse(BaseModel):
    query:str
    results:list[paper]

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

@app.get("/papers", response_model=PaperResponse)
def get_papers():
    return {"papers": papers}

@app.get("/search", response_model=SearchResponse)
def search_papers(q: str = Query(min_length=1)):
    results=[
        paper for paper in papers if q.lower() in paper["title"].lower()
    ]

    return {"query": q, "results": results}