from backend.main import app  # re-export FastAPI app

if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
