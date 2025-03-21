Key improvements and explanations:

Environment Variables: The database connection details (DB_NAME, DB_USER, etc.) and the Ollama model are loaded from environment variables. This is crucial for security and configurability. You should never hardcode passwords directly in your code.

get_db_connection() function: This function encapsulates the database connection logic, making it reusable and handling potential connection errors with a HTTPException. This is good practice for cleaner code and error handling.

FastAPI: Uses FastAPI for building the API.

Pydantic Models: Document and Query models are defined using Pydantic. This provides automatic data validation and makes your API more robust. For example, if someone tries to send a request to /add_documents/ with data that doesn't match the Document model (e.g., missing the content field), FastAPI will automatically return a helpful error message.

/add_documents/ endpoint: This endpoint allows you to add multiple documents to the database in a single request. It takes a list of Document objects as input.

/query_postgresal/ endpoint: This endpoint performs the vector similarity search against the database. It takes a Query object (containing the query text and the number of results k) and returns a list of dictionaries, each containing the content and similarity_score.

/generate_response/ endpoint: This endpoint uses the query_postgresal endpoint to get relevant documents and then uses Ollama to generate a response, just like your notebook code. It is important to use await.

Error Handling: Uses HTTPException to handle errors gracefully. If there's a database error, or any other exception, the API will return a 500 Internal Server Error with a descriptive message.

Database Transactions and Rollback: The add_documents endpoint uses conn.commit() to commit the changes to the database. It also includes conn.rollback() in a try...except...finally block. This is very important: if any part of adding the documents fails (e.g., a database error), the rollback() will undo any partial changes, ensuring data consistency.

Type Hints: Uses type hints (e.g., List[Document], Dict) throughout the code. This improves code readability and helps catch errors early.

uvicorn server: Added uvicorn server for run app in development.

How to Run and Test:

Install Dependencies:

pip install fastapi uvicorn psycopg2-binary sentence-transformers pydantic python-dotenv
Use code with caution.
Bash
Database Setup:

Make sure you have PostgreSQL installed and running.

Create a database named mydb (or change the DB_NAME environment variable).

Create a user named admin with password 1234 (or change the DB_USER and DB_PASSWORD environment variables).

Create the documents table in your database:

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1024)  -- Adjust the dimension if needed
);
Use code with caution.
SQL
If vector doesn't work try to use 1536

Set Environment Variables:

Option 1: Using a .env file (Recommended for Development):
Create a file named .env in the same directory as your Python script. Add the following lines, adjusting the values as needed:

DB_NAME=mydb
DB_USER=admin
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
OLLAMA_MODEL=llama3.2
Use code with caution.
Then, you need to install python-dotenv: pip install python-dotenv.

The script will automatically load these variables.

Option 2: Setting Environment Variables Directly:
You can set environment variables directly in your shell before running the script:

export DB_NAME=mydb
export DB_USER=admin
# ... (set other variables)
Use code with caution.
Bash
Run the FastAPI Server:

python your_script_name.py
Use code with caution.
Bash
Or, to automatically reload on code changes:

uvicorn your_script_name:app --reload
Use code with caution.
Test the API:

Swagger UI (Automatic Documentation):
Open your web browser and go to http://127.0.0.1:8000/docs. You'll see automatically generated API documentation (Swagger UI). You can use this interface to interact with your API endpoints, send requests, and see the responses. This is extremely useful for testing and understanding your API.

Using curl (or any HTTP client like Postman):

Add Documents:

curl -X 'POST' \
  'http://127.0.0.1:8000/add_documents/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
  {"content": "ชื่อร้าน: ครัวคุณยาย, ประเภทอาหาร: ไทย, ราคาโดยเฉลี่ย: 200-300 บาท, ที่อยู่: สุขุมวิท 21, เบอร์โทร: 02-123-4567"},
  {"content": "ชื่อร้าน: Pizza Palace, ประเภทอาหาร: อิตาเลียน, ราคาโดยเฉลี่ย: 300-500 บาท, ที่อยู่: สีลม, เบอร์โทร: 02-987-6543"}
]'
Use code with caution.
Bash
Query Postgres (get similar documents):

curl -X 'POST' \
  'http://127.0.0.1:8000/query_postgresal/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query_text": "ร้านอาหารไทย",
  "k": 1
}'
Use code with caution.
Bash
You should get a JSON response like:

[
     {
       "content": "ชื่อร้าน: ครัวคุณยาย, ประเภทอาหาร: ไทย, ราคาโดยเฉลี่ย: 200-300 บาท, ที่อยู่: สุขุมวิท 21, เบอร์โทร: 02-123-4567",
       "similarity_score": 0.06845
     }
 ]
Use code with caution.
Json
Generate Response:

curl -X 'POST' \
  'http://127.0.0.1:8000/generate_response/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query_text": "อยากินพิซซ่า",
  "k": 3
}'
Use code with caution.
Bash
This will return a JSON response with the response field containing the text generated by Ollama.

This comprehensive setup provides a robust, secure, and well-documented REST API for your document search and generation functionality. It addresses the key issues of security, error handling, and maintainability, and uses best practices for modern API development. It is also easily deployable to cloud platforms. Remember to install Ollama.