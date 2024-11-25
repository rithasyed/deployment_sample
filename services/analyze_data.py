from services.trades import process_long_sl_target, process_long_trade, process_short_sl_target, process_short_trade
from database import SessionLocal
from websocket import ConnectionManager
from services.ticker import fetch_yahoo_data
from utils.symbols import get_symbols
import pandas as pd
from datetime import datetime


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
async def fetch_and_analyze_data(manager: ConnectionManager, interval="15m"):
    # db = Depends(get_db)
    db = get_db()
    symbols = get_symbols()
    arr = [];
    for ticker in symbols:
        # ticker = "AAPL"  # Replace with your desired ticker
        # interval = "15m"  # Replace with your desired interval

        candlestick_data, ema_data, macd_data, vwap_data, arrow_signals, ttm_waves_data = fetch_yahoo_data(ticker, interval)
        print(f"fetched for {interval} ...")
        # Convert arrow_signals to a DataFrame for easier analysis
        ripster_df = pd.DataFrame(arrow_signals)
        df = pd.DataFrame(candlestick_data)

        # Get the last row of the DataFrame
        last_ripster_row = ripster_df.tail(1)
        last_row = df.tail(1)
        for index, row in last_row.iterrows():
            time = datetime.fromtimestamp(row['time'])
            price = row['close']
            await process_long_sl_target(db,ticker,price,time, back_testing=False, interval=interval)
            await process_short_sl_target(db,ticker,price,time, back_testing=False, interval=interval)

        # Check for signals in the last 3 rows
        for index, row in last_ripster_row.iterrows():
            signal_time = datetime.fromtimestamp(row['time'])
            price = row['price']
            # if row['signal_up']:
            #     await manager.broadcast(f"Signal UP detected for {ticker} at {signal_time}")
            #     print(f"Signal UP detected for {ticker} at {signal_time}")
            # if row['signal_down']:
            #     await manager.broadcast(f"[{ticker},{signal_time},{price}]")
            #     print(f"Signal DOWN detected for {ticker} at {signal_time}")
            if row['ripster_signal_up']:
                await process_short_trade(db, signal="RipsterUp", stock_name=ticker, price=price, time=signal_time, back_testing=False, interval=interval)
                await process_long_trade(db, signal="RipsterUp", stock_name=ticker, price=price, time=signal_time, back_testing=False, interval=interval)
                await manager.broadcast(f"""["RipsterUp","{ticker}","{signal_time}","{price}"]""")
                print(f"Ripster Signal UP detected for {ticker} at {signal_time}")
            if row['ripster_signal_down']:
                await process_short_trade(db, signal="RipsterDown", stock_name=ticker, price=price, time=signal_time, back_testing=False, interval=interval)
                await process_long_trade(db, signal="RipsterDown", stock_name=ticker, price=price, time=signal_time, back_testing=False, interval=interval)
                await manager.broadcast(f"""["RipsterDown","{ticker}","{signal_time}","{price}"]""")
                print(f"Ripster Signal DOWN detected for {ticker} at {signal_time}")
    return arr


async def back_test_the_stock(stockname="NVDA",interval= "15m"):
    db = get_db()
    candlestick_data, ema_data, macd_data, vwap_data, arrow_signals, ttm_waves_data = fetch_yahoo_data(stockname, interval)
    print(f"fetched for back test interval {interval} ...")
    df = pd.DataFrame(arrow_signals)
    for index, row in df.iterrows():
        signal_time = datetime.fromtimestamp(row['time'])
        price = row['price']
        await process_long_sl_target(db,stockname,price,signal_time, back_testing=True,interval=interval)
        await process_short_sl_target(db,stockname,price,signal_time, back_testing=True,interval=interval)
        if row['ripster_signal_up']:
            await process_short_trade(db, signal="RipsterUp", stock_name=stockname, price=price, time=signal_time, back_testing=True, interval=interval)
            await process_long_trade(db, signal="RipsterUp", stock_name=stockname, price=price, time=signal_time, back_testing=True,interval=interval)
            print(f"Ripster Signal UP detected for {stockname} at {signal_time}")
        if row['ripster_signal_down']:
            await process_short_trade(db, signal="RipsterDown", stock_name=stockname, price=price, time=signal_time, back_testing=True,interval=interval)
            await process_long_trade(db, signal="RipsterDown", stock_name=stockname, price=price, time=signal_time, back_testing=True,interval=interval)
            print(f"Ripster Signal DOWN detected for {stockname} at {signal_time}")
            
    return None
