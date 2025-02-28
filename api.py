from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_databases, get_schemas, get_tables_and_views, stream_data_from_table
from data_process import process_data_and_analyze

app = FastAPI()

class QueryRequest(BaseModel):
    database: str
    schema: str
    tables: list[str]
    chunk_size: int = 10000
    query: str = None

@app.get("/databases")
async def list_databases():
    try:
        databases = get_databases()
        return {"databases": databases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching databases: {str(e)}")

@app.get("/schemas/{database}")
async def list_schemas(database: str):
    try:
        schemas, _ = get_schemas(database)
        return {"schemas": schemas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching schemas: {str(e)}")

@app.get("/tables/{database}/{schema}")
async def list_tables(database: str, schema: str):
    try:
        _, engine = get_schemas(database)
        tables, views = get_tables_and_views(engine, schema)
        return {"tables": tables, "views": views}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tables: {str(e)}")

@app.post("/analyze")
async def analyze_data(request: QueryRequest):
    try:
        _, engine = get_schemas(request.database)
        result = process_data_and_analyze(engine, request.schema, request.tables, request.chunk_size, request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)