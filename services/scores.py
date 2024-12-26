from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import warnings
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

def calculate_ticker_scores_multiframe(
    tickers=['ABBV', 'AI', 'AMAT', 'AMD', 'AMZN', 'ARKK', 'ASTS', 'AAPL', 'AVGO', 'BA', 'BABA', 'BAC', 'BIDU',
    'BKNG', 'BTC-USD', 'CAT', 'C', 'CMG', 'COST', 'CRSP', 'CVX', 'DDOG', 'DE', 'DIA', 'DOCU',
    'DUK', 'EOG', 'ES', 'FSLR', 'GBTC', 'GC=F', 'GE', 'GLD', 'GOOG', 'GOOGL', 'GS', 'GTLB', 'HD', 'IBM',
    'IBB', 'IWM', 'IYR', 'IYT', 'JNJ', 'JPM', 'KO', 'LLY', 'LMND', 'LMT', 'LOW', 'LRCX', 'LULU', 'MCD',
    'META', 'MP', 'MRK', 'MSFT', 'MU', 'NEE', 'NET', 'NFLX', 'NKE', 'NQ=F', 'NVDA', 'OKTA', 'OUST',
    'ORCL', 'PEP', 'PG', 'PLTR', 'PTON', 'PSNL', 'QCOM', 'QQQ', 'RBRK', 'RIVN', 'ROKU', 'RSP', 'RTX',
    'RTY=F', 'SHOP', 'SLV', 'SMCI', 'SMH', 'SO', 'SOFI', 'SQ', 'SU', 'SBUX', 'TGT', 'TJX', 'TSM',
    'TSLA', 'UNH', 'UNP', 'UPS', 'VLO', 'WFC', 'WMT', 'XLB', 'XLC', 'XLE', 'XLK', 'XLI', 'XLU', 'XLV',
    'XOM', 'YM=F', 'Z', 'ZM', 'SPY', 'XLF'],
    intervals=['15m', '30m', '90m', '1h', '1d', '5d', '1wk'],
    batch_size=10
):
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
        'IYR': 'ISHARES US REAL ESTATE ETF IV',
        'ARKK': 'ARK INNOVATION ETF',
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
        'INTC': 'INTEL CORP',
        'ABBV': 'ABBVIE INC',
        'BABA': 'ALIBABA GROUP HLDG L ADR',
        'GOOGL': 'ALPHABET INC A',
        'AVGO': 'BROADCOM INC',
        'BA': 'BOEING CO',
        'BKNG': 'BOOKING HLDGS INC',
        'SQ': 'Block Inc A',
        'CAT': 'CATERPILLAR INC',
        'CVX': 'CHEVRON CORP NEW',
        'CMG': 'CHIPOTLE MEXICAN GRI',
        'NET': 'CLOUDFLARE INC A',
        'CRSP': 'CRISPR THERAPEUTICS',
        'DDOG': 'DATADOG INC A',
        'DE': 'DEERE & CO',
        'TSM': 'TAIWAN SEMICONDUCTOR ADR',
        'DUK': 'DUKE ENERGY CORP NEW',
        'LLY': 'ELi Lilly and Co',
        'EOG': 'EOG RES INC',
        'XOM': 'EXXON MOBIL CORP',
        'FSLR': 'FIRST SOLAR INC',
        'GE': 'GE Aerospace',
        'GTLB': 'GITLAB INC A',
        'GS': 'GOLDMAN SACHS GROUP',
        'SOFI': 'SOFI TECHNOLOGIES IN',
        'HD': 'HOME DEPOT INC',
        'IBM': 'IBM CORP',
        'RIVN': 'RIVIAN AUTOMOTIVE IN A',
        'RTX': 'RTX CORP',
        'RBRK': 'RUBRIK INC A',
        'AI': 'C3 AI INC A',
        'MU': 'MICRON TECHNOLOGY IN',
        'MRK': 'Merck & Co. Inc.',
        'NEE': 'NEXTERA ENERGY INC',
        'NKE': 'NIKE INC B',
        'OUST': 'OUSTER INC A',
        'PEP': 'PEPSICO INC',
        'PSNL': 'PERSONALIS INC',
        'PG': 'PROCTER & GAMBLE CO',
        'QCOM': 'QUALCOMM INC',
        'ROKU': 'ROKU INC A',
        'SHOP': 'SHOPIFY INC A',
        'SO': 'SOUTHERN CO',
        'SBUX': 'STARBUCKS CORP',
        'SU': 'SUNCOR ENERGY INC NE',
        'TGT': 'TARGET CORP',
        'TJX': 'TJX COS INC NEW',
        'KO': 'The Coca-Cola Co',
        'UNP': 'UNION PAC CORP',
        'UPS': 'UNITED PARCEL SVC IN B',
        'UNH': 'UNITEDHEALTH GROUP I',
        'VLO': 'VALERO ENERGY CORP N',
        'COST': 'COSTCO WHSL CORP NEW',
        'Z': 'ZILLOW GROUP INC Z',
        'ZM': 'ZOOM COMMUNICATIONS A',
        'AMAT': 'APPLIED MATLS INC',
        'ASTS': 'AST SPACEMOBILE INC A',
        'BAC': 'BANK OF AMERICA CORP',
        'BIDU': 'BAIDU INC A ADR',
        'BRK/B': 'BERKSHIRE HATHAWAY B',
        'DOCU': 'DOCUSIGN INC',
        'JNJ': 'JOHNSON & JOHNSON',
        'LMT': 'LOCKHEED MARTIN CORP',
        'LOW': 'LOWES COS INC',
        'LRCX': 'LAM RESH CORP Equity',
        'LULU': 'LULULEMON ATHLETICA',
        'MCD': 'MCDONALDS CORP',
        'MP': 'MP MATLS CORP A',
        'SLV': 'ISHARES SILVER TRUST ETF IV',
        'SPX': 'S & P 500 INDEX'
        }

    ticker_batches = [tickers[i:i + batch_size] for i in range(0, len(tickers), batch_size)]
    all_results = []
    
    for batch_num, ticker_batch in enumerate(ticker_batches, 1):
        print(f"Processing batch {batch_num}/{len(ticker_batches)} ({len(ticker_batch)} tickers)")
        batch_results = []

        current_prices = {}
        for ticker in ticker_batch:
            try:
                stock = yf.Ticker(ticker)
                price = stock.info.get('currentPrice')
                if price is not None and pd.notna(price) and not np.isinf(price):
                    current_prices[ticker] = float(price)
                else:
                    price = stock.info.get('regularMarketPrice')
                    if price is not None and pd.notna(price) and not pd.isinf(price):
                        current_prices[ticker] = float(price)
                    else:
                        current_prices[ticker] = None
            except Exception as e:
                print(f"Error fetching current price for {ticker}: {str(e)}")
                current_prices[ticker] = None

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
                                'current_price': current_prices[ticker] if current_prices[ticker] is not None else 0.0 
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
        'ticker_symbol', 'ticker_name', 'current_price',
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