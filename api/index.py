from fastapi import FastAPI
from api.services import router  # import the router from services.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Your CORS setup
frontend_url = "https://stcokbot-frontend.vercel.app/"
origins = [frontend_url]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
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
