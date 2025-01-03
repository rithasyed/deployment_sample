from datetime import timezone, datetime, timedelta
from models.tickerScores import TickerScore
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from sqlalchemy import desc

def delete_old_ticker_scores(db: Session, days: int = 3):
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        deleted_count = db.query(TickerScore).filter(TickerScore.created_at < cutoff_date).delete()
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        print(f"Error deleting old ticker scores: {e}")
        raise

def create_ticker_score(db: Session, score_data: dict):
    try:
        current_time = datetime.now(timezone.utc)
        previous_record = (
            db.query(TickerScore)
            .filter(TickerScore.ticker_symbol == score_data.get('ticker_symbol'))
            .order_by(desc(TickerScore.created_at))
            .first()
        )

        is_deleted = previous_record.is_deleted if previous_record else False
        
        existing_score = (
            db.query(TickerScore)
            .filter(
                and_(
                    TickerScore.ticker_symbol == score_data.get('ticker_symbol'),
                    func.date(TickerScore.created_at) == func.date(score_data.get('created_at')) 
                    if score_data.get('created_at') 
                    else func.date(TickerScore.created_at) == func.date(current_time)
                )
            )
            .first()
        )
        
        prev_score = previous_record 
        
        current_long_score = score_data.get('long_score', 0)
        score_change_trend = ''
        
        if prev_score and prev_score.created_at != current_time:
            score_change_trend = current_long_score - prev_score.long_score
        else:
            score_change_trend = " "

        if existing_score:
            for key, value in score_data.items():
                if hasattr(existing_score, key) and key != 'created_at':
                    setattr(existing_score, key, value)
            existing_score.score_change_trend = score_change_trend
            existing_score.is_deleted = is_deleted 
            db_ticker_score = existing_score
            print("Updating existing ticker score record")
        else:
            db_ticker_score = TickerScore(
                ticker_symbol=score_data.get('ticker_symbol', ''),
                ticker_name=score_data.get('ticker_name', ''),
                
                w_score=score_data.get('w_score'),
                w_squeeze=score_data.get('w_squeeze'),
                d_score=score_data.get('d_score'),
                d_squeeze=score_data.get('d_squeeze'),
                five_d_score=score_data.get('five_d_score'),
                five_d_squeeze=score_data.get('five_d_squeeze'),
                one_h_score=score_data.get('one_h_score'),
                one_h_squeeze=score_data.get('one_h_squeeze'),
                ninety_m_score=score_data.get('ninety_m_score'),
                ninety_m_squeeze=score_data.get('ninety_m_squeeze'),
                thirty_m_score=score_data.get('thirty_m_score'),
                thirty_m_squeeze=score_data.get('thirty_m_squeeze'),
                fifteen_m_score=score_data.get('fifteen_m_score'),
                fifteen_m_squeeze=score_data.get('fifteen_m_squeeze'),
                
                long_score=current_long_score,
                short_score=score_data.get('short_score'),
                long_rank=score_data.get('long_rank'),
                short_rank=score_data.get('short_rank'),
                trend=score_data.get('trend'),
                score_change_trend=score_change_trend,
                current_price=score_data.get('current_price'),
                created_at=score_data.get('created_at', current_time),
                sector=score_data.get('sector'),
                category_id=score_data.get('category_id'),
                is_deleted=is_deleted
            )
            db.add(db_ticker_score)

        db.commit()
        db.refresh(db_ticker_score)

        delete_old_ticker_scores(db)
        
        return db_ticker_score
    
    except Exception as e:
        db.rollback()
        print(f"Error inserting/updating ticker score: {e}")
        raise

def get_ticker_scores(db: Session, ticker_symbol: str = None):
    query = db.query(TickerScore).filter(TickerScore.is_deleted == False)
    
    if ticker_symbol:
        query = query.filter(TickerScore.ticker_symbol == ticker_symbol)

    latest_scores_subquery = (
        db.query(TickerScore.ticker_symbol, func.max(TickerScore.created_at).label('max_created_at'))
        .filter(TickerScore.is_deleted == False)
        .group_by(TickerScore.ticker_symbol)
        .subquery()
    )

    latest_scores = ( 
        query
        .join(
            latest_scores_subquery, 
            (TickerScore.ticker_symbol == latest_scores_subquery.c.ticker_symbol) & 
            (TickerScore.created_at == latest_scores_subquery.c.max_created_at)
        )
        .order_by(desc(TickerScore.created_at))
        .all()
    )
    
    return latest_scores
def soft_delete_ticker_score(db: Session, ticker_symbol: str):
    scores = db.query(TickerScore).filter(TickerScore.ticker_symbol == ticker_symbol).filter(TickerScore.is_deleted == False).all()

    if scores:
        for score in scores:
            score.is_deleted = True
        db.commit()
        return scores
    else:
        return None