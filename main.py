from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi import HTTPException
from search_engine import advanced_search 


from db import get_connection

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


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/papers", response_model=PaperResponse)
def get_papers():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, year
            FROM papers
            ORDER BY id
            """
        ).fetchall()

    return {"papers": rows}


@app.get("/search", response_model=SearchResponse)
def search_papers(q: str = Query(min_length=1)):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, year
            FROM papers
            WHERE title ILIKE %s
            ORDER BY id
            """,
            (f"%{q}%",),
        ).fetchall()

    return {"query": q, "results": rows}


@app.get("/search/advanced")
def search_advanced( q: str = Query(min_length=1, max_length=200),
    year: int | None = Query(default=None, ge=1900, le=2100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100)):

    try:
        return advanced_search(
            query=q,
            year=year,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

