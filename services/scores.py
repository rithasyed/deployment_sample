from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def calculate_ticker_scores_multiframe(tickers=[
            'QQQ', 'SPY', 'IWM', 'DIA', 'RSP', 'BTC-USD', 'RTY=F', 'YM=F', 'GC=F', 'NQ=F', 'ES',
            'XLK', 'SMH', 'XLF', 'XLV', 'XLE', 'XLC', 'IYR', 'ARKK', 'XLU', 'XLB', 'IYT', 'XLI', 'IBB', 'GBTC',
            'AMZN', 'PLTR', 'NFLX', 'META', 'TSLA', 'WMT', 'CRM', 'ORCL', 'AAPL', 'C', 'MSFT', 'PTON', 'JPM', 'UAL', 'GOOG', 'LMND', 'NVDA', 'WFC', 'OKTA', 'SMCI', 'AMD', 'INTC'
        ],
        intervals=['15m', '30m', '90m', '1h', '1d', '5d', '1wk']):
        
    def calculate_ticker_score_from_data(data, atr_period=9, atr_factor=2.4):

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
            
            data['md'] = safe_macd(data['Close'])
            data['sma200'] = safe_ta_calc(ta.sma, data['Close'], length=min(200, len(data)))
            data['sma50'] = safe_ta_calc(ta.sma, data['Close'], length=min(50, len(data)))
            data['ema8'] = safe_ta_calc(ta.ema, data['Close'], length=min(8, len(data)))
            data['ema34'] = safe_ta_calc(ta.ema, data['Close'], length=min(34, len(data)))
            data['ema21'] = safe_ta_calc(ta.ema, data['Close'], length=min(21, len(data)))
            data['ema5'] = safe_ta_calc(ta.ema, data['Close'], length=min(5, len(data)))
            
            # Fill NaN values with 0 or forward/backward fill
            data = data.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            data['is_sloping_lower_50'] = data['sma50'] < data['sma50'].shift(1).fillna(0)
            data['is_sloping_lower_21'] = data['ema21'] < data['ema21'].shift(1).fillna(0)
            data['is_sloping_lower_200'] = data['sma200'] < data['sma200'].shift(1).fillna(0)
            data['is_sloping_higher_50'] = data['sma50'] > data['sma50'].shift(1).fillna(0)
            data['is_sloping_higher_21'] = data['ema21'] > data['ema21'].shift(1).fillna(0)
            data['is_sloping_higher_200'] = data['sma200'] > data['sma200'].shift(1).fillna(0)
            
            # ATR Trailing Stop
            tr = ta.true_range(data['High'], data['Low'], data['Close'], length=min(atr_period, len(data)))
            tr = tr.fillna(0)
            data['trail'] = data['Close'] - (atr_factor * tr.rolling(window=min(atr_period, len(data))).mean().fillna(0))
            
            # Trend Conditions
            data['sp'] = ((data['ema5'] > data['ema8']) & 
                        (data['ema8'] > data['ema21']) & 
                        (data['ema21'] > data['ema34']))
            data['sn'] = ((data['ema5'] < data['ema8']) & 
                        (data['ema8'] < data['ema21']) & 
                        (data['ema21'] < data['ema34']))
            
            # Scoring Logic
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

            return int(data['score'].iloc[-1]) if not pd.isna(data['score'].iloc[-1]) else 0
        
        except Exception as e:
            print(f"Error in score calculation: {e}")
            return 0

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
        # Define the rank order
        rank_order = ["F", "D", "C", "B", "A", "A+", "A++", "B--"]
        
        # Get the index of long and short ranks
        long_index = rank_order.index(long_rank) if long_rank in rank_order else -1
        short_index = rank_order.index(short_rank) if short_rank in rank_order else -1
        
        # Determine trend based on rank comparison
        if  short_index > long_index:
            return "Uptrend"
        elif short_index < long_index:
            return "Downtrend"
        else:
            return ""  

    results = []

    ticker_names = {
        'QQQ': 'INVSC QQQ TRUST SRS 1 ETF',
        'SPY': 'SPDR S&P 500 ETF',
        'IWM': 'ISHARES RUSSELL 2000 ETF',
        'DIA': 'SPDR DOW JONES INDUSTRIAL AVRG ETF',
        'RSP': 'INVSC S P 500 EQUAL WEIGHT ETF IV',
        'BTC-USD': 'Bitcoin Futures',
        'RTY=F': 'E-mini Russell 2000 Index Futures',
        'YM=F': 'Mini Dow Jones Industrial Average Futures,ETH',
        'GC=F': 'Gold Futures, ETH',
        'NQ=F': 'E-mini Nasdaq 100 Index Futures,ETH',
        'ES': 'E-mini S&P 500 Futures,ETH',
        'XLK': 'TECHNOLOGY SELECT SECTOR SPDR ETF IV',
        'SMH': 'VANECK SEMICONDUCTOR ETF',
        'XLF': 'SELECT STR FINANCIAL SELECT SPDR ETF',
        'XLV': 'SELECT SECTOR HEALTH CARE SPDR ETF',
        'XLE': 'ENERGY SELECT SECTOR SPDR ETF',
        'XLC': 'COMMUNICAT SVS SLCT SEC SPDR ETF',
        'IYR':'ISHARES US REAL ESTATE ETF IV',
        'ARKK':'ARK INNOVATION ETF',
        'XLU': 'SELECT SECTOR UTI SELECT SPDR ETF',
        'XLB': 'SPDR FUND MATERIALS SELECT SECTR ETF',
        'IYT': 'ISHARES US TRANSPORTATION ETF',
        'XLI': 'SELECT SECTOR INDUSTRIAL SPDR ETF',
        'IBB': 'iShares Nasdaq Biotechnology Index Fund',
        'GBTC': 'GRAYSCALE BITCOIN TR BTC',
        'AMZN': 'Amazon.com Inc',
        'PLTR': 'PALANTIR TECHNOLOGIE A',
        'NFLX': 'NETFLIX INC',
        'META': 'META PLATFORMS INC A',
        'TSLA': 'TESLA INC',
        'WMT': 'WALMART INC',
        'CRM': 'Salesforce Inc',
        'ORCL': 'ORACLE CORP',
        'AAPL': 'APPLE INC',
        'C': 'Citigroup Inc',
        'MSFT': 'Microsoft Corp',
        'PTON': 'PELOTON INTERACTIVE',
        'JPM': 'JPMORGAN CHASE & CO',
        'UAL': 'United Airlines Hldg',
        'GOOG': 'ALPHABET INC C',
        'LMND': 'LEMONADE INC',
        'NVDA': 'NVIDIA CORP',
        'WFC': 'WELLS FARGO & CO',
        'OKTA': 'OKTA INC A',
        'SMCI': 'SUPER MICRO COMPUTER',
        'AMD': 'Advanced Micro Devic',
        'INTC': 'INTEL CORP'
    }


    # Modify the download and processing logic
    for ticker in tickers:
        ticker_result = {
            'TICKER SYMBOL': ticker,
            'TICKER NAME': ticker_names.get(ticker, ticker)
        }
        
        for interval in intervals:
            end_date = datetime.now()
            
            # Adjust start date based on interval
            if interval in ['1m', '5m']:
                start_date = end_date - timedelta(days=7)       
            elif interval in ['15m', '30m', '60m', '90m']:
                start_date = end_date - timedelta(days=60)
            elif interval in ['1d', '5d']:
                start_date = end_date - timedelta(days=365*5)
            elif interval in ['1wk', '1mo']:
                start_date = end_date - timedelta(days=365*5)
            
            try:
                # Attempt to download data
                data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
                
                # Check if data is empty
                if data.empty:
                    print(f"No data available for {ticker} at {interval}")
                    continue
                
                # Calculate score
                score = calculate_ticker_score_from_data(data)
                
                # Store score if valid
                if score is not None:
                    if interval == '1wk':
                        ticker_result['W'] = score
                    elif interval == '1d':
                        ticker_result['D'] = score
                    elif interval == '5d':
                        ticker_result['5D'] = score
                    elif interval == '1h':
                        ticker_result['1H'] = score
                    elif interval == '90m':
                        ticker_result['90M'] = score
                    elif interval == '30m':
                        ticker_result['30M'] = score
                    elif interval == '15m':
                        ticker_result['15M'] = score
            
            except Exception as e:
                print(f"Error processing {ticker} at {interval}: {e}")

        # Calculate long and short scores
        long_score_columns = ['W', 'D', '5D', '1H', '90M', '30M', '15M']
        ticker_result['LONG SCORE'] = sum(ticker_result.get(col, 0) for col in long_score_columns if col in ticker_result)

        short_score_columns = ['15M', '30M', '90M', '1H']
        ticker_result['SHORT SCORE'] = sum(ticker_result.get(col, 0) for col in short_score_columns if col in ticker_result)

        ticker_result['LONG RANK'] = get_long_rank(ticker_result['LONG SCORE'])
        ticker_result['SHORT RANK'] = get_short_rank(ticker_result['SHORT SCORE'])

        ticker_result['TREND'] = determine_trend(ticker_result['LONG RANK'], ticker_result['SHORT RANK'])

        results.append(ticker_result)

    results_df = pd.DataFrame(results)

    columns_order = ['TICKER SYMBOL', 'TICKER NAME', 'W', 'D', '5D', '1H', '90M', '30M', '15M', 'LONG SCORE', 'SHORT SCORE', 'LONG RANK', 'SHORT RANK','TREND']
    results_df = results_df[columns_order]
    
    return results_df