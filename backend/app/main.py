# Import FastAPI so we can create our API application.
from fastapi import FastAPI

# Create the FastAPI application.
app = FastAPI(title="StyleDNA API")


# Health endpoint.
# We use this to quickly verify that the backend server is running.
@app.get("/health")
def health_check():
    return {"status": "ok"}