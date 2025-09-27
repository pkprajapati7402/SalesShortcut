import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create the FastAPI application object
app = FastAPI()

# Define a simple health check endpoint
@app.get("/health")
def read_root():
    """Returns a simple JSON response indicating the service is healthy."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "message": "Minimal test service is running!"}
    )

# It's good practice to have a root endpoint too
@app.get("/")
def root():
    return {"message": "Welcome to the minimal test service."}

# This part is for local testing and is not used by the Dockerfile CMD
if __name__ == "__main__":
    import uvicorn
    # Use 8080 for local testing to mimic Cloud Run's default
    uvicorn.run(app, host="0.0.0.0", port=8080)