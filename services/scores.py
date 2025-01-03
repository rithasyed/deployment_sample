from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from requests import Session
import yfinance as yf
import pandas_ta as ta
import warnings
from schemas.symbols_schema import SymbolCreate
from services.symbol_crud import create_symbol, get_symbol_names
warnings.simplefilter(action='ignore', category=FutureWarning)

def calculate_ticker_score_from_data(data, atr_period=9, atr_factor=2.4, bb_num_dev=2.0, bb_length=20, kc_factor=1.75):
    if len(data) < 50:
        return None
    
    try:
        def safe_macd(close_series):
            try:
                return ta.macd(close_series, fast=24, slow=52, signal=9)['MACDh_24_52_9']
            except Exception:
                return pd.Series([0] * len(close_series), index=close_series.index)
        
        def safe_ta_calc(func, series, **kwargs):
            try:
                return func(series, **kwargs)
            except Exception:
                return pd.Series([0] * len(series), index=series.index)
        
        def calculate_squeeze(close, high, low, bb_length=20):
            atr_length = 14
            atr1_multiplier = 1.5
            atr = ta.atr(high, low, close, length=atr_length)
            atr1 = atr * atr1_multiplier

            bb_mult = 2.0
            kc_mult_high = 1.0
            kc_mult_mid = 1.5
            kc_mult_low = 2.0

            bb = ta.bbands(close, length=bb_length, std=bb_mult)
            bb_basis = bb['BBM_20_2.0']
            bb_upper = bb['BBU_20_2.0']
            bb_lower = bb['BBL_20_2.0']

            tr = ta.true_range(high, low, close)
            atr = ta.sma(tr, bb_length)
            kc_basis = ta.sma(close, bb_length)

            kc_upper_high = kc_basis + atr * kc_mult_high
            kc_lower_high = kc_basis - atr * kc_mult_high
            kc_upper_mid = kc_basis + atr * kc_mult_mid
            kc_lower_mid = kc_basis - atr * kc_mult_mid
            kc_upper_low = kc_basis + atr * kc_mult_low
            kc_lower_low = kc_basis - atr * kc_mult_low

            no_sqz = (bb_lower < kc_lower_low) | (bb_upper > kc_upper_low)
            low_sqz = (bb_lower >= kc_lower_low) | (bb_upper <= kc_upper_low)
            mid_sqz = (bb_lower >= kc_lower_mid) | (bb_upper <= kc_upper_mid)
            high_sqz = (bb_lower >= kc_lower_high) | (bb_upper <= kc_upper_high)

            if high_sqz.iloc[-1]:
                return "high squeeze"
            elif mid_sqz.iloc[-1]:
                return "mid squeeze"
            elif low_sqz.iloc[-1]:
                return "low squeeze"
            else:
                return "no squeeze"
        
        data['md'] = safe_macd(data['Close'])
        data['sma200'] = safe_ta_calc(ta.sma, data['Close'], length=min(200, len(data)))
        data['sma50'] = safe_ta_calc(ta.sma, data['Close'], length=min(50, len(data)))
        data['ema8'] = safe_ta_calc(ta.ema, data['Close'], length=min(8, len(data)))
        data['ema34'] = safe_ta_calc(ta.ema, data['Close'], length=min(34, len(data)))
        data['ema21'] = safe_ta_calc(ta.ema, data['Close'], length=min(21, len(data)))
        data['ema5'] = safe_ta_calc(ta.ema, data['Close'], length=min(5, len(data)))
        
        data = data.fillna(method='ffill').fillna(method='bfill').fillna(0)
        
        data['is_sloping_lower_50'] = data['sma50'] < data['sma50'].shift(1).fillna(0)
        data['is_sloping_lower_21'] = data['ema21'] < data['ema21'].shift(1).fillna(0)
        data['is_sloping_lower_200'] = data['sma200'] < data['sma200'].shift(1).fillna(0)
        data['is_sloping_higher_50'] = data['sma50'] > data['sma50'].shift(1).fillna(0)
        data['is_sloping_higher_21'] = data['ema21'] > data['ema21'].shift(1).fillna(0)
        data['is_sloping_higher_200'] = data['sma200'] > data['sma200'].shift(1).fillna(0)
        
        tr = ta.true_range(data['High'], data['Low'], data['Close'], length=min(atr_period, len(data)))
        tr = tr.fillna(0)
        data['trail'] = data['Close'] - (atr_factor * tr.rolling(window=min(atr_period, len(data))).mean().fillna(0))
        
        data['sp'] = ((data['ema5'] > data['ema8']) & 
                    (data['ema8'] > data['ema21']) & 
                    (data['ema21'] > data['ema34']))
        data['sn'] = ((data['ema5'] < data['ema8']) & 
                    (data['ema8'] < data['ema21']) & 
                    (data['ema21'] < data['ema34']))

        bull_conditions = [
            data['md'] > 0,
            data['is_sloping_higher_50'],
            data['is_sloping_higher_21'],
            data['is_sloping_higher_200'],
            data['sp'],
            data['Close'] > data['ema21'],
            data['Close'] > data['sma50'],
            data['Close'] > data['sma200'],
            data['ema8'] > data['ema21'],
            data['ema8'] > data['sma50'],
            data['ema8'] > data['sma200'],
            data['ema21'] > data['sma50'],
            data['ema21'] > data['sma200'],
            data['sma50'] > data['sma200'],
            data['Close'] > data['trail'],
        ]
        
        bear_conditions = [
            data['md'] < 0,
            data['is_sloping_lower_50'],
            data['is_sloping_lower_21'],
            data['is_sloping_lower_200'],
            data['sn'],
            data['Close'] < data['ema21'],
            data['Close'] < data['sma50'],
            data['Close'] < data['sma200'],
            data['ema8'] < data['ema21'],
            data['ema21'] < data['sma50'],
            data['ema8'] < data['sma200'],
            data['ema21'] < data['sma50'],
            data['ema21'] < data['sma200'],
            data['sma50'] < data['sma200'],
            data['Close'] < data['trail'],
        ]
        
        data['bull_score'] = sum(cond.astype(int) for cond in bull_conditions)
        data['bear_score'] = sum(cond.astype(int) for cond in bear_conditions)
        data['score'] = data['bull_score'] - data['bear_score']

        squeeze = calculate_squeeze(
            data['Close'], 
            data['High'], 
            data['Low'], 
            bb_length=bb_length
        )
        
        score = int(data['score'].iloc[-1]) if not pd.isna(data['score'].iloc[-1]) else 0
        return score, squeeze
    
    except Exception as e:
        print(f"Error in score calculation: {e}")
        return 0, False

def get_long_rank(long_score):
    if long_score == 120:
        return "A++"
    elif long_score == -120:
        return "B--"
    elif long_score >= 80:
        return "A+"
    elif long_score >= 40:
        return "A"
    elif long_score >= 0:
        return "B"
    elif long_score > -40:
        return "C"
    elif long_score > -80:
        return "D"
    else:
        return "F"

def get_short_rank(short_score):
    if short_score == 60:
        return "A++"
    elif short_score == -60:
        return "B--"
    elif short_score >= 30:
        return "A+"
    elif short_score >= 10:
        return "A"
    elif short_score >= 0:
        return "B"
    elif short_score > -10:
        return "C"
    elif short_score > -30:
        return "D"
    else:
        return "F"

def determine_trend(long_rank, short_rank):
    rank_order = ["F", "D", "C", "B", "A", "A+", "A++", "B--"]
    long_index = rank_order.index(long_rank) if long_rank in rank_order else -1
    short_index = rank_order.index(short_rank) if short_rank in rank_order else -1
    
    if short_index > long_index:
        return "Uptrend"
    elif short_index < long_index:
        return "Downtrend"
    else:
        return ""
    
def add_ticker_to_file_and_db(
    ticker: str, 
    category_id: int, 
    db: Session,
    filename: str = 'tickers.txt'
) -> Tuple[bool, str]:
    valid_category_ids = {1, 2, 3, 4, 5}
    
    if category_id not in valid_category_ids:
        return False, f"Invalid category ID. Must be one of: {', '.join(map(str, valid_category_ids))}"

    try:
        # Verify if it's a valid ticker using yfinance
        ticker_info = yf.Ticker(ticker)
        ticker_name = ticker_info.info.get('longName', ticker)
        
        # Check if ticker exists in database
        existing_symbols = get_symbol_names(db)
        if (ticker,) in existing_symbols:
            return False, "Ticker already exists in database"
        
        # Read existing tickers from file
        existing_tickers = set()
        try:
            with open(filename, 'r') as f:
                for line in f:
                    if line.strip():
                        symbol = line.strip().split('|')[0]
                        existing_tickers.add(symbol)
        except FileNotFoundError:
            # Create file if it doesn't exist
            pass

        # If ticker already exists in file, return False
        if ticker in existing_tickers:
            return False, "Ticker already exists in file"

        # Create new symbol in database
        symbol_data = SymbolCreate(
            name=ticker,
            full_name=ticker_name,
            category_id=category_id
        )
        create_symbol(db, symbol_data)

        # Append the new ticker to file
        with open(filename, 'a') as f:
            f.write(f"\n{ticker}|{ticker_name}|{category_id}")
        
        return True, "Ticker added successfully to both file and database"
    
    except Exception as e:
        return False, f"Error adding ticker: {str(e)}"

def load_tickers(filename: str) -> Tuple[List[str], Dict[str, str], Dict[str, int]]:
    tickers = []
    ticker_names = {}
    ticker_categories = {}
    
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('|')
                    symbol = parts[0]
                    name = parts[1]
                    category_id = int(parts[2]) if len(parts) > 2 else 1 
                    
                    tickers.append(symbol)
                    ticker_names[symbol] = name
                    ticker_categories[symbol] = category_id
    except FileNotFoundError:
        with open(filename, 'w') as f:
            pass
    
    return tickers, ticker_names, ticker_categories

def calculate_ticker_scores_multiframe(
    tickers_file='tickers.txt',
    intervals=['15m', '30m', '90m', '1h', '1d', '5d', '1wk'],
    batch_size=10,
    single_ticker=None,
    category_id=None  
):
    if single_ticker:
        if category_id is None:
            raise ValueError("category_id must be provided when adding a single ticker")
        
        tickers = [single_ticker]
        ticker_names = {single_ticker: single_ticker}
        ticker_categories = {single_ticker: category_id}
        
    else:
        tickers, ticker_names, ticker_categories = load_tickers(tickers_file)

    ticker_batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
    all_results = []
    
    for batch_num, ticker_batch in enumerate(ticker_batches, 1):
        print(f"Processing batch {batch_num}/{len(ticker_batches)} ({len(ticker_batch)} tickers)")
        batch_results = []

        current_prices = {}
        sectors = {}
        for ticker in ticker_batch:
            try:
                stock = yf.Ticker(ticker)
                price = stock.info.get('currentPrice')
                if price is not None and pd.notna(price) and not np.isinf(price):
                    current_prices[ticker] = float(price)
                else:
                    price = stock.info.get('navPrice')
                    if price is not None and pd.notna(price) and not np.isinf(price):
                        current_prices[ticker] = float(price)
                    else:
                        current_prices[ticker] = None

                sector = stock.info.get('sector', 'N/A')
                sectors[ticker] = sector

            except Exception as e:
                print(f"Error fetching data for {ticker}: {str(e)}")
                current_prices[ticker] = None
                sectors[ticker] = 'N/A'

        for interval in intervals:
            end_date = datetime.now()
            
            if interval in ['1m', '5m']:
                start_date = end_date - timedelta(days=7)       
            elif interval in ['15m', '30m', '60m', '90m']:
                start_date = end_date - timedelta(days=60)
            else:
                start_date = end_date - timedelta(days=365*2)
            
            try:
                multi_data = yf.download(
                    ticker_batch,
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    progress=False
                )
                
                if multi_data.empty:
                    continue

                for ticker in ticker_batch:
                    try:
                        if isinstance(multi_data.columns, pd.MultiIndex):
                            ticker_data = pd.DataFrame({
                                'Close': multi_data[('Close', ticker)],
                                'High': multi_data[('High', ticker)],
                                'Low': multi_data[('Low', ticker)],
                                'Open': multi_data[('Open', ticker)],
                                'Volume': multi_data[('Volume', ticker)]
                            })
                        else:
                            ticker_data = multi_data

                        if ticker_data.empty:
                            continue

                        score, squeeze = calculate_ticker_score_from_data(ticker_data)
                        
                        ticker_result = next((r for r in batch_results if r['ticker_symbol'] == ticker), None)
                        if ticker_result is None:
                            ticker_result = {
                                'ticker_symbol': ticker,
                                'ticker_name': ticker_names.get(ticker, ticker),
                                'current_price': current_prices[ticker] if current_prices[ticker] is not None else 0.0,
                                'sector': sectors[ticker],
                                'category_id': ticker_categories.get(ticker)
                            }
                            batch_results.append(ticker_result)

                        if score is not None:
                            interval_mapping = {
                                '1wk': ('w_score', 'w_squeeze'),
                                '1d': ('d_score', 'd_squeeze'),
                                '5d': ('five_d_score', 'five_d_squeeze'),
                                '1h': ('one_h_score', 'one_h_squeeze'),
                                '90m': ('ninety_m_score', 'ninety_m_squeeze'),
                                '30m': ('thirty_m_score', 'thirty_m_squeeze'),
                                '15m': ('fifteen_m_score', 'fifteen_m_squeeze')
                            }
                            
                            if interval in interval_mapping:
                                score_key, squeeze_key = interval_mapping[interval]
                                ticker_result[score_key] = score
                                ticker_result[squeeze_key] = squeeze

                    except Exception as e:
                        print(f"Error processing {ticker} in {interval}: {str(e)}")
                        continue

                del multi_data
                
            except Exception as e:
                print(f"Error processing interval {interval}: {str(e)}")
                continue
        
        for ticker_result in batch_results:
            long_score_columns = ['w_score', 'd_score', 'five_d_score', 'one_h_score', 
                                'ninety_m_score', 'thirty_m_score', 'fifteen_m_score']
            short_score_columns = ['fifteen_m_score', 'thirty_m_score', 'ninety_m_score', 'one_h_score']
            
            ticker_result['long_score'] = sum(ticker_result.get(col, 0) for col in long_score_columns)
            ticker_result['short_score'] = sum(ticker_result.get(col, 0) for col in short_score_columns)
            
            ticker_result['long_rank'] = get_long_rank(ticker_result['long_score'])
            ticker_result['short_rank'] = get_short_rank(ticker_result['short_score'])
            ticker_result['trend'] = determine_trend(ticker_result['long_rank'], ticker_result['short_rank'])
        
        all_results.extend(batch_results)
        del batch_results
    
    if not all_results:
        return pd.DataFrame()
    
    results_df = pd.DataFrame(all_results)

    if 'current_price' in results_df.columns:
        results_df['current_price'] = results_df['current_price'].fillna(0.0)
        results_df['current_price'] = results_df['current_price'].replace([float('inf'), float('-inf')], 0.0)
    
    columns_order = [
        'ticker_symbol', 'ticker_name', 'current_price', 'sector', 'category_id',
        'w_score', 'w_squeeze', 
        'd_score', 'd_squeeze', 
        'five_d_score', 'five_d_squeeze', 
        'one_h_score', 'one_h_squeeze', 
        'ninety_m_score', 'ninety_m_squeeze', 
        'thirty_m_score', 'thirty_m_squeeze', 
        'fifteen_m_score', 'fifteen_m_squeeze', 
        'long_score', 'short_score', 
        'long_rank', 'short_rank', 'trend'
    ]
    
    results_df = results_df.reindex(columns=columns_order, fill_value=0)
    
    return results_df, all_results