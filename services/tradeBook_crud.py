from sqlalchemy.orm import Session
from models.tradeBook import Tradebook
from schemas.tradeBook_schema import TradebookCreate, TradebookUpdate



# Retrieve a single trade by its ID
def get_trade(db: Session, trade_id: int):
    return db.query(Tradebook).filter(Tradebook.id == trade_id).first()

# Retrieve all trades
def get_trades(db: Session):
    return db.query(Tradebook).all()


# Delete a trade by its ID
def delete_trade(db: Session, trade_id: int):
    db_trade = db.query(Tradebook).filter(Tradebook.id == trade_id).first()
    if db_trade:
        db.delete(db_trade)
        db.commit()
    return db_trade


# Create a new trade in the database
def create_trade(db: Session, trade_data: dict):
    db_trade = Tradebook(
        stockname=trade_data['stockName'],
        entry_price=trade_data['entry_price'],
        exit_price=trade_data['exit_price'],
        pnl=trade_data['pnl'],
        status=trade_data['status'],
        entry_time=trade_data['entry_time'],
        exit_time=trade_data['exit_time'],
        stoploss=trade_data['stoploss'],
        target=trade_data['target'],
        quantity=trade_data['quantity'],
        capital=trade_data['capital'],
        tradetype=trade_data['tradetype'],
        indicator=trade_data['indicator'],
        back_testing=trade_data['back_testing'],
        interval=trade_data['interval'],
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

# Update an existing trade in the database
def update_trade(db: Session, trade, trade_data: dict):
    trade.exit_price = trade_data['exit_price']
    trade.exit_time = trade_data['exit_time']
    trade.pnl = trade_data['pnl']
    trade.ROI = trade_data['ROI']
    trade.profit = trade_data['profit']
    trade.remarks = trade_data['remarks']
    trade.status = trade_data['status']
    db.commit()
    db.refresh(trade)
    return trade

