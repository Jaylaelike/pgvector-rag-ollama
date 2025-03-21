from fastapi import FastAPI, HTTPException
from sentence_transformers import SentenceTransformer
import psycopg2
import os
from typing import List, Dict
import ollama
from pydantic import BaseModel

# --- Configuration ---
# Use environment variables for sensitive information
DB_NAME = os.environ.get("DB_NAME", "mydb")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "1234")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

# --- Database Connection Function (Reusable) ---

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        return conn
    except psycopg2.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# --- Sentence Transformer (Load Once) ---
embedder = SentenceTransformer("BAAI/bge-m3")

# --- FastAPI Setup ---
app = FastAPI()

# --- Data Models (Pydantic) ---
class Document(BaseModel):
    content: str

class Query(BaseModel):
    query_text: str
    k: int = 5  # Default value for k


# --- API Endpoints ---

@app.post("/add_documents/")
async def add_documents(documents: List[Document]):
    """Adds multiple documents to the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        for doc in documents:
            embedding = embedder.encode(doc.content).tolist()
            cur.execute(
                "INSERT INTO documents (content, embedding) VALUES (%s, %s)",
                (doc.content, embedding),
            )
        conn.commit()
        return {"message": "Documents added successfully"}
    except Exception as e:
        conn.rollback()  # Rollback in case of any error
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/query_postgresal/")
async def query_postgresal(query: Query) -> List[Dict]:
    """Queries the database for similar documents using vector similarity."""
    conn = get_db_connection()
    cur = conn.cursor()
    query_embedding = embedder.encode(query.query_text).tolist()
    query_embedding_str = "[" + ", ".join(map(str, query_embedding)) + "]"
    sql_query = """
        SELECT content, embedding <=> %s::vector AS similarity_score
        FROM documents
        ORDER BY similarity_score ASC
        LIMIT %s;
    """
    try:
        cur.execute(sql_query, (query_embedding_str, query.k))
        results = cur.fetchall()
        formatted_results = [
            {"content": row[0], "similarity_score": row[1]} for row in results
        ]  # More readable output
        return formatted_results
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()



@app.post("/generate_response/")
async def generate_response_endpoint(query: Query) -> Dict:
    """Generates a response using Ollama, based on the query and retrieved documents."""
    try:
        retrieved_docs = await query_postgresal(query)  # Await the coroutine
        context = "\n".join([doc["content"] for doc in retrieved_docs])
        prompt = f"Answer the question based on the following context:\n{context}\nQuestion: {query.query_text}"

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "You are assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return {"response": response["message"]["content"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -- for development --
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)