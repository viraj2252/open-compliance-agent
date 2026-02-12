from fastapi import FastAPI

app = FastAPI(title="Compliance Assistant RAG")

@app.get("/")
async def root():
    return {"message": "Compliance Assistant RAG API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
