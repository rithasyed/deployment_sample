from fastapi import FastAPI
from services import router  # import the router from services.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Your CORS setup
origins = [
    "https://stcokbot-frontend.vercel.app",
    "http://localhost:3000",  # for local development
]

# Add the CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
# Include the router from services.py
app.include_router(router)
@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "index:app",
        host="0.0.0.0",
        port=5001,
        reload=True,
    )
