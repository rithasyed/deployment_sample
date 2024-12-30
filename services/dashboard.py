from fastapi import HTTPException
import yfinance as yf
import numpy as np
import pandas as pd

def convert_data(data):
    if isinstance(data, (pd.DataFrame, pd.Series, np.ndarray)):
        # Convert to dictionary, replacing NaN with None
        if isinstance(data, pd.DataFrame):
            return data.where(pd.notnull(data), None).to_dict()
        elif isinstance(data, pd.Series):
            return data.where(pd.notnull(data), None).to_dict()
        else:
            return data.tolist()
    
    if isinstance(data, dict):
        return {k: convert_data(v) for k, v in data.items()}
    
    if isinstance(data, (np.integer, np.floating)):
        # Convert numpy numeric types to Python native types
        if np.isnan(data) or np.isinf(data):
            return None
        return data.item()
    
    return data

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if 'currentPrice' in info:
            current_price = info['currentPrice']
        elif 'navPrice' in info:
            current_price = info['navPrice']
        else:
            raise HTTPException(status_code=404, detail="Price information not available for the given ticker.")
        previous_close = stock.info['previousClose']

        absolute_Change = current_price - previous_close
        percentage_change = (absolute_Change / previous_close) * 100

        financials = convert_data(stock.financials) if stock.financials is not None else None
        recommendations = convert_data(stock.recommendations) if stock.recommendations is not None else None
        cash_flow = convert_data(stock.cashflow) if stock.cashflow is not None else None

        ticker_symbols = [
            "AAPL",
            "MSFT",
            "AMZN",
            "NVDA",
            "GOOGL",
            "TSLA",
            "META",
            "UNH",
            "XOM",
            "QQQ",
            "IWM",
            "NFLX",
            "SPY"
        ]
        logo_urls = {
            "AAPL": "https://logo.clearbit.com/apple.com",
            "MSFT": "https://logo.clearbit.com/microsoft.com",
            "AMZN": "https://logo.clearbit.com/amazon.com",
            "NVDA": "https://logo.clearbit.com/nvidia.com",
            "GOOGL": "https://logo.clearbit.com/google.com",
            "TSLA": "https://logo.clearbit.com/tesla.com",
            "META": "https://logo.clearbit.com/meta.com",
            "UNH": "https://logo.clearbit.com/unitedhealthgroup.com",
            "XOM": "https://logo.clearbit.com/exxonmobil.com",
            "QQQ": "https://logo.clearbit.com/invesco.com",
            "IWM": "https://logo.clearbit.com/ishares.com",
            "NFLX": "https://logo.clearbit.com/netflix.com",
            "SPY": "https://logo.clearbit.com/spdrs.com",
        }

        return_data = {
            'ticker': ticker,
            'current_price': current_price,
            'previous_close': previous_close,
            'absolute_change': absolute_Change,
            'percentage_change': percentage_change,
            'financials': financials,
            'recommendations': recommendations,
            'cash_flow':cash_flow,
            'info': info,
            'ticker_symbols': ticker_symbols,
            'logo_url': logo_urls.get(ticker, "/placeholder.svg")
        }
        
        return return_data
    
    except Exception as e:
        print(f"Error in get_stock_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")