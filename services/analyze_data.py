from services.trades import process_long_sl_target, process_long_trade, process_short_sl_target, process_short_trade
from database import SessionLocal
from websocket import ConnectionManager
from services.ticker import fetch_yahoo_data
from utils.symbols import get_symbols
import pandas as pd
from datetime import datetime
import pytz


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

async def fetch_and_analyze_data(manager: ConnectionManager, interval="15m"):
    # db = Depends(get_db)
    quantity = 100
    indicator = "TTM"
    db = get_db()
    symbols = get_symbols()
    arr = [];
    for ticker in symbols:
        # ticker = "AAPL"  # Replace with your desired ticker
        # interval = "15m"  # Replace with your desired interval

        candlestick_data, macd_data, vwap_signals, ttm_waves_data, ttm_squeeze_signals= fetch_yahoo_data(ticker, interval)
        print(f"fetched for {interval} ...")
        # Convert arrow_signals to a DataFrame for easier analysis
        ttm_df = pd.DataFrame(ttm_squeeze_signals)
        df = pd.DataFrame(candlestick_data)

        # Get the last row of the DataFrame
        last_ttm_row = ttm_df.tail(1)
        last_row = df.tail(1)
        for index, row in last_row.iterrows():
            time = datetime.fromtimestamp(row['time'], tz=pytz.UTC)
            price = row['close']
            await process_long_sl_target(db,ticker,price,time, back_testing=False, interval=interval)
            await process_short_sl_target(db,ticker,price,time, back_testing=False, interval=interval)

        # Check for signals in the last 3 rows
        for index, row in last_ttm_row.iterrows():
            signal_time = datetime.fromtimestamp(row['time'],tz=pytz.UTC)
            price = row['price']
            # if row['signal_up']:
            #     await manager.broadcast(f"Signal UP detected for {ticker} at {signal_time}")
            #     print(f"Signal UP detected for {ticker} at {signal_time}")
            # if row['signal_down']:
            #     await manager.broadcast(f"[{ticker},{signal_time},{price}]")
            #     print(f"Signal DOWN detected for {ticker} at {signal_time}")
            if row['squeeze_signal_up'] or row['ripster_signal_up']:
                await process_short_trade(db, signal="SignalUp", stock_name=ticker, price=price, time=signal_time, back_testing=False, interval=interval, quantity=quantity, indicator=indicator)
                await process_long_trade(db, signal="SignalUp", stock_name=ticker, price=price, time=signal_time, back_testing=False, interval=interval, quantity=quantity, indicator=indicator)
                await manager.broadcast(f"""["SignalUp","{ticker}","{signal_time}","{price}"]""")
                print(f"Squeeze Signal UP detected for {ticker} at {signal_time}")
            if row['squeeze_signal_down'] or row['ripster_signal_down']:
                await process_short_trade(db, signal="SignalDown", stock_name=ticker, price=price, time=signal_time, back_testing=False, interval=interval, quantity=quantity, indicator=indicator)
                await process_long_trade(db, signal="SignalDown", stock_name=ticker, price=price, time=signal_time, back_testing=False, interval=interval, quantity=quantity, indicator=indicator)
                await manager.broadcast(f"""["SignalDown","{ticker}","{signal_time}","{price}"]""")
                print(f"Squeeze Signal DOWN detected for {ticker} at {signal_time}")
    return arr


async def back_test_the_stock(stockname="NVDA",interval= "15m", quantity=100, indicator="TTM"):
    try:
        db = get_db()
        candlestick_data, macd_data, vwap_signals, ttm_waves_data, ttm_squeeze_signals= fetch_yahoo_data(stockname, interval)
        print(f"fetched for back test interval {interval} ...")
        if indicator == "TTM":
            df = pd.DataFrame(ttm_squeeze_signals)
            print(df.tail(10))
            for index, row in df.iterrows():
                signal_time = datetime.fromtimestamp(row['time'], tz=pytz.UTC)
                price = row['price']
                await process_long_sl_target(db,stockname,price,signal_time, back_testing=True,interval=interval)
                await process_short_sl_target(db,stockname,price,signal_time, back_testing=True,interval=interval)
                if row['squeeze_signal_up'] or row['ripster_signal_up']:
                    await process_short_trade(db, signal="SignalUp", stock_name=stockname, price=price, time=signal_time, back_testing=True, interval=interval, quantity=quantity, indicator=indicator)
                    await process_long_trade(db, signal="SignalUp", stock_name=stockname, price=price, time=signal_time, back_testing=True, interval=interval, quantity=quantity, indicator=indicator)
                    print(f"Squeeze Signal UP detected for {stockname} at {signal_time}")
                if row['squeeze_signal_down'] or row['ripster_signal_down']:
                    await process_short_trade(db, signal="SignalDown", stock_name=stockname, price=price, time=signal_time, back_testing=True,interval=interval, quantity=quantity, indicator=indicator)
                    await process_long_trade(db, signal="SignalDown", stock_name=stockname, price=price, time=signal_time, back_testing=True,interval=interval, quantity=quantity, indicator=indicator)
                    print(f"Squeeze Signal DOWN detected for {stockname} at {signal_time}")
        elif indicator == "Ripster":
            df = pd.DataFrame(vwap_signals)
            for index, row in df.iterrows():
                signal_time = datetime.fromtimestamp(row['time'], tz=pytz.UTC)
                price = row['price']
                await process_long_sl_target(db,stockname,price,signal_time, back_testing=True,interval=interval)
                await process_short_sl_target(db,stockname,price,signal_time, back_testing=True,interval=interval)
                if row['ripster_signal_up']:
                    await process_short_trade(db, signal="SignalUp", stock_name=stockname, price=price, time=signal_time, back_testing=True, interval=interval, quantity=quantity, indicator=indicator)
                    await process_long_trade(db, signal="SignalUp", stock_name=stockname, price=price, time=signal_time, back_testing=True,interval=interval, quantity=quantity, indicator=indicator)
                    print(f"Ripster Signal UP detected for {stockname} at {signal_time}")
                if row['ripster_signal_down']:
                    await process_short_trade(db, signal="SignalDown", stock_name=stockname, price=price, time=signal_time, back_testing=True,interval=interval, quantity=quantity, indicator=indicator)
                    await process_long_trade(db, signal="SignalDown", stock_name=stockname, price=price, time=signal_time, back_testing=True,interval=interval, quantity=quantity, indicator=indicator)
                    print(f"Ripster Signal DOWN detected for {stockname} at {signal_time}") 
        return None
    except Exception as e:
        print(e)
