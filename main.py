import time
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.concurrency import asynccontextmanager
from services.analyze_data import fetch_and_analyze_data
from websocket import ConnectionManager
import yfinance as yf # type: ignore
import pandas as pd
import pandas_ta as ta # type: ignore
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlencode
from api.router import router
import nest_asyncio  # type: ignore
from apscheduler.schedulers.asyncio import AsyncIOScheduler #type: ignore
from apscheduler.jobstores.memory import MemoryJobStore #type: ignore
from models import symbols, tradeBook
from database import engine, Base

Base.metadata.create_all(bind=engine)
manager = ConnectionManager()

jobstores = {
    'default': MemoryJobStore()
}

# Initialize an AsyncIOScheduler with the jobstore
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone='Asia/Kolkata')
# Job running every 10 seconds

  
nest_asyncio.apply()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield


app = FastAPI(lifespan=lifespan)

origins = ["*","localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.middleware("http")
async def flatten_query_string_lists(request: Request, call_next):
    flattened: list[tuple[str, str]] = []
    for key, value in request.query_params.multi_items():
        flattened.extend((key, entry) for entry in value.split(","))

    request.scope["query_string"] = urlencode(flattened, doseq=True).encode("utf-8")

    return await call_next(request)

# WebSocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            # Keep the connection alive, optionally handle messages from frontend
            await websocket.receive_text()
            # await websocket.send_text("Hi")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# @scheduler.scheduled_job('interval', seconds=60)
# async def scheduled_job_1():
#     result = await fetch_and_analyze_data(manager,"1m")
#     print("res",result)
    # await manager.broadcast(result)
    
# @scheduler.scheduled_job('interval', seconds=60 * 15)
# async def scheduled_job_2():
#     result = await fetch_and_analyze_data(manager,"15m")
#     print("res",result)
#     # await manager.broadcast(result)


@app.get("/health")
def health():
    return {"status": "ok"};




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5001,
        reload= True,
    )
