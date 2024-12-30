from fastapi import APIRouter, Depends
from services.stock_analyzer import StockRequest, analyze_stock
from models.tickerScores import TickerScore
from services.ticker_score_crud import create_ticker_score, delete_old_ticker_scores, get_ticker_scores
from services.scores import add_ticker_to_file, calculate_ticker_scores_multiframe
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
# Import the function from the original script
from services.dashboard import get_stock_data

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
        await back_test_the_stock(request.stockname, request.interval, request.quantity, request.indicator)
        return HTTPException(status_code=200, detail=f"Back test done...")
    except Exception as e:
        print(e)
        return HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/trades")
def fetch_trades(db: Session = Depends(get_db)):
    return get_trades(db)

@router.get("/stock-data/{ticker}")
def get_stock_info(ticker: str):
    try:
        stock_data = get_stock_data(ticker)
        return stock_data
    except Exception as e:
        print(f"Error in get_stock_info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@router.get("/ticker-scores")
async def fetch_ticker_scores(
    db: Session = Depends(get_db), 
    store_scores: bool = True 
):
    try:
        scores_df, results = calculate_ticker_scores_multiframe()
 
        if store_scores:
            stored_scores = []

            for result in results:
                stored_score = create_ticker_score(db, result)
                stored_scores.append(stored_score)

                ticker_idx = scores_df[scores_df['ticker_symbol'] == result['ticker_symbol']].index[0]
                scores_df.at[ticker_idx, 'score_change_trend'] = stored_score.score_change_trend
        
        return scores_df.to_dict(orient='records')
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/stored-ticker-scores")
def retrieve_stored_ticker_scores(
    db: Session = Depends(get_db),
    ticker_symbol: str = None
):
    try:
        stored_scores = get_ticker_scores(db, ticker_symbol)
        return stored_scores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.delete("/clean-old-ticker-scores")
def clean_old_ticker_scores(
    db: Session = Depends(get_db),
    days_to_keep: int = 3
):
    try:
        delete_old_ticker_scores(db, days_to_keep)
        return {"message": f"Deleted ticker scores older than {days_to_keep} days"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@router.post("/calculate-ticker-score/{ticker_symbol}")
async def calculate_single_ticker_score(
    ticker_symbol: str,
    db: Session = Depends(get_db)
):
    try:
        existing_score = db.query(TickerScore).filter(
            TickerScore.ticker_symbol == ticker_symbol
        ).first()
        
        if existing_score:
            return HTTPException(
                status_code=400, 
                detail=f"Ticker {ticker_symbol} already exists in database"
            )
        was_added, message = add_ticker_to_file(ticker_symbol)
        if not was_added and "already exists" not in message:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to add ticker: {message}"
            )
        scores_df, results = calculate_ticker_scores_multiframe(single_ticker=ticker_symbol)
        
        if not results:
            raise HTTPException(
                status_code=404, 
                detail=f"No data found for ticker {ticker_symbol}"
            )

        stored_score = create_ticker_score(db, results[0]) if was_added else None
        
        response = {**results[0]}
        if stored_score:
            response.update({
                'score_change_trend': stored_score.score_change_trend,
                'created_at': stored_score.created_at
            })
            
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@router.post("/analyze")
async def analyze_endpoint(request: StockRequest):
    try:
        return analyze_stock(request.ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))