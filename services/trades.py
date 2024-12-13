from datetime import datetime
from services.tradeBook_crud import update_trade, create_trade
from sqlalchemy.orm import Session
from models.tradeBook import Tradebook
def calculate_percentage(amount, percentage):
    return amount * (percentage / 100)

async def process_long_sl_target(db: Session, stock_name: str, price: str, time: datetime, back_testing: bool, interval: str):
    # Find the ongoing long trade for the same stock
    existing_long_trade = None
    if back_testing:
        existing_long_trade = db.query(Tradebook).filter_by(stockname=stock_name, status="Ongoing", tradetype="long", back_testing=True, interval=interval).first()
    else:
        existing_long_trade = db.query(Tradebook).filter_by(stockname=stock_name, status="Ongoing", tradetype="long", interval=interval).first()

    if existing_long_trade:
        price = float(price)
        target = float(existing_long_trade.target)
        stoploss = float(existing_long_trade.stoploss)
        entry_price = float(existing_long_trade.entry_price)
        quantity = float(existing_long_trade.quantity)
        capital = float(existing_long_trade.capital)
        pnl = round(price - entry_price, 2)
        roi = float(quantity) * float(pnl)
        if price >= target:
            # Close the existing long trade
            updated_trade_data = {
                'exit_price': price,
                'exit_time': time,
                'pnl': pnl,
                'ROI': roi,
                'profit': str(round((roi / capital)*100, 2)) + "%",
                'status': "Closed",
                'remarks': "Target achieved."
            }
            return update_trade(db, existing_long_trade, updated_trade_data)
        elif price <= stoploss:
            # Close the existing long trade
            updated_trade_data = {
                'exit_price': price,
                'exit_time': time,
                'pnl': pnl,
                'ROI': roi,
                'profit': str(round((roi / capital)*100, 2)) + "%",
                'status': "Closed",
                'remarks': "Stoploss triggered."
            }
            return update_trade(db, existing_long_trade, updated_trade_data)

    return None

async def process_short_sl_target(db: Session, stock_name: str, price: str, time: datetime, back_testing: bool, interval: str):
    # Find the ongoing short trade for the same stock and interval
    existing_short_trade = None
    if back_testing:
        existing_short_trade = db.query(Tradebook).filter_by(
            stockname=stock_name, status="Ongoing", tradetype="short", back_testing=True, interval=interval
        ).first()
    else:
        existing_short_trade = db.query(Tradebook).filter_by(
            stockname=stock_name, status="Ongoing", tradetype="short", interval=interval
        ).first()

    if existing_short_trade:
        price = float(price)
        target = float(existing_short_trade.target)
        stoploss = float(existing_short_trade.stoploss)
        entry_price = float(existing_short_trade.entry_price)
        quantity = float(existing_short_trade.quantity)
        capital = float(existing_short_trade.capital)
        pnl = round(float(entry_price - price), 2)
        
        # Make sure both are converted to float before multiplication
        roi = float(quantity) * float(pnl)
        
        # Check if the target or stoploss condition is met
        if price <= target:
            # Close the existing short trade due to target achievement
            updated_trade_data = {
                'exit_price': price,
                'exit_time': time,
                'pnl': pnl,
                'ROI': roi,
                'profit': str(round((roi / capital)*100, 2)) + "%",
                'status': "Closed",
                'remarks': "Target achieved."
            }
            return update_trade(db, existing_short_trade, updated_trade_data)
        elif price >= stoploss:
            # Close the existing short trade due to stoploss being triggered
            updated_trade_data = {
                'exit_price': price,
                'exit_time': time,
                'pnl': pnl,
                'ROI': roi,
                'profit': str(round((roi / capital)*100, 2)) + "%",
                'status': "Closed",
                'remarks': "Stoploss triggered."
            }
            return update_trade(db, existing_short_trade, updated_trade_data)

    return None


async def process_short_trade(db: Session, signal: str, stock_name: str, price: str, time: datetime, back_testing: bool, interval: str, quantity: int, indicator: str):
    # Check if a trade already exists for the same stock, interval, and signal time, regardless of status
    existing_trade = db.query(Tradebook).filter_by(
        stockname=stock_name, interval=interval, tradetype="short", status="Ongoing", back_testing=back_testing
    ).first()
    
    existing_trade_with_same_time = db.query(Tradebook).filter_by(
        stockname=stock_name, interval=interval, entry_time=time, tradetype="short", back_testing=back_testing, indicator=indicator
    ).first()
    # Skip if a trade with the same signal time and interval already exists (Closed)
    # if existing_trade is not None and existing_trade.status == "Closed":
    #     return None

    price = float(price)
    sl = round(price + calculate_percentage(float(price), 10))
    target = round(price + calculate_percentage(float(price), -30))
    capital = quantity * round(price, 2)
    
    # Create a new short trade if the signal is "RipsterUp" and no ongoing trade exists
    if signal == "SignalDown" and (existing_trade is None or existing_trade.status != "Ongoing"):
        # Create a new trade entry
        if existing_trade_with_same_time:
            return None
        new_trade_data = {
            'stockName': stock_name,
            'entry_price': price,
            'exit_price': "--",
            'pnl': "--",
            'status': "Ongoing",
            'entry_time': time,
            'exit_time': None,
            'stoploss': sl,
            'target': target,
            'quantity': quantity,
            'capital': capital,
            'back_testing': back_testing,
            'indicator': indicator,
            'tradetype': "short",  # Set tradetype to short
            'interval': interval
        }
        return create_trade(db, new_trade_data)

    # Close an existing ongoing short trade if the signal is "RipsterDown" and intervals match
    elif (signal == "SignalUp" or signal == "WarningSignalUp") and existing_trade and existing_trade.status == "Ongoing":
        # Ensure the interval matches before closing the trade
        if existing_trade.interval != interval:
            return None

        # Check the time. always exit_time will be greater than entry_time.
        if time < existing_trade.entry_time:
            return None

        quantity = float(existing_trade.quantity)
        capital = float(existing_trade.capital)
        pnl = round(float(existing_trade.entry_price) - float(price), 2)
        roi = float(quantity) * float(pnl)
        
        # Close the existing short trade
        updated_trade_data = {
            'exit_price': price,
            'exit_time': time,
            'pnl': pnl,
            'ROI': roi,
            'profit': str(round((roi / capital)*100, 2)) + "%",
            'status': "Closed",
            'remarks': "Signal Down detected."
        }
        return update_trade(db, existing_trade, updated_trade_data)
    
    return None


async def process_long_trade(db: Session, signal: str, stock_name: str, price: str, time: datetime, back_testing: bool, interval: str, quantity: int, indicator: str):
    # Check if a trade already exists for the same stock, interval, and signal time, regardless of status
    existing_trade = db.query(Tradebook).filter_by(
        stockname=stock_name, interval=interval, tradetype="long", status="Ongoing", back_testing=back_testing
    ).first()
    existing_trade_with_same_time = db.query(Tradebook).filter_by(
        stockname=stock_name, interval=interval, entry_time=time, tradetype="long", back_testing=back_testing, indicator=indicator
    ).first()

    price = float(price)
    sl = round(price + calculate_percentage(float(price), -10))
    target = round(price + calculate_percentage(float(price), 30))
    capital = quantity * round(price, 2)
    
    # Create a new long trade if the signal is "RipsterDown" and no existing ongoing trade exists
    if signal == "SignalUp" and (existing_trade is None or existing_trade.status != "Ongoing"):
        if existing_trade_with_same_time:
            return None
        new_trade_data = {
            'stockName': stock_name,
            'entry_price': price,
            'exit_price': "--",
            'pnl': "--",
            'status': "Ongoing",
            'entry_time': time,
            'exit_time': None,
            'stoploss': sl,
            'target': target,
            'quantity': quantity,
            'capital': capital,
            'back_testing': back_testing,
            'indicator': indicator,
            'tradetype': "long",
            "interval": interval
        }
        return create_trade(db, new_trade_data)

    # Close an existing ongoing trade if the signal is "RipsterUp" and intervals match
    elif (signal == "SignalDown" or signal == "WarningSignalDown") and existing_trade and existing_trade.status == "Ongoing":
        # Ensure the interval matches before closing the trade
        if existing_trade.interval != interval:
            return None
        
         # Check the time. always exit_time will be greater than entry_time.
        if time < existing_trade.entry_time:
            return None

        quantity = float(existing_trade.quantity)
        capital = float(existing_trade.capital)
        pnl = round(float(price) - float(existing_trade.entry_price), 2)
        roi = float(quantity) * float(pnl)
        
        # Close the existing long trade
        updated_trade_data = {
            'exit_price': price,
            'exit_time': time,
            'pnl': pnl,
            'ROI': roi,
            'profit': str(round((roi / capital)*100, 2)) + "%",
            'status': "Closed",
            'remarks': "Signal Up detected."
        }
        return update_trade(db, existing_trade, updated_trade_data)
    
    return None
