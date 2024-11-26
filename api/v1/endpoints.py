from fastapi import APIRouter, Depends
from services.ticker import fetch_yahoo_data
import pandas as pd
from fastapi import HTTPException
import yfinance as yf #type: ignore
from database import get_db
from sqlalchemy.orm import Session
from requests import request
from datetime import datetime, timedelta
from database import SessionLocal
from services.tradeBook_crud import get_trades
from schemas.tradeBook_schema import backTestCreate
from services.analyze_data import back_test_the_stock

router = APIRouter()

@router.get('/data/{ticker}/{interval}/{ema_period}/{vwap_period}/{vwap_std_dev}')
def get_data(ticker: str, interval: str, ema_period: int, vwap_period: int, vwap_std_dev: float):
    try:
        candlestick_data, macd_data, vwap_signals, ttm_waves_data, ttm_squeeze_signals = fetch_yahoo_data(
            ticker, interval, ema_period=ema_period, vwap_period=vwap_period, vwap_std_dev=vwap_std_dev
        )
        return {
            'candlestick': candlestick_data,
            # 'ema': ema_data,
            'macd': macd_data,
            # 'vwap': vwap_data,
            'vwap_signals': vwap_signals,
            'ttm_waves':ttm_waves_data,
            'ttm_squeeze_signals': ttm_squeeze_signals
        }
    except Exception as e:
        print(f"Error in get_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# @router.get('/symbols')
# def get_symbols():
#     with open('symbols.txt') as f:
#         symbols = [line.strip() for line in f]
#     return symbols

@router.post('/back-test')
async def analyze_the_stock(request: backTestCreate):
    try:
        await back_test_the_stock(request.stockname, request.interval)
        return HTTPException(status_code=200, detail=f"Back test done...")
    except Exception as e:
        print(e)
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/trades")
def fetch_trades(db: Session = Depends(get_db)):
    return get_trades(db)
