from datetime import timezone, datetime, timedelta
from models.tickerScores import TickerScore
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import desc

def create_ticker_score(db: Session, score_data: dict):
    try:
        # Get the previous record for this ticker
        prev_score = (
            db.query(TickerScore)
            .filter(TickerScore.ticker_symbol == score_data.get('ticker_symbol'))
            .order_by(desc(TickerScore.created_at))
            .first()
        )
        
        # Calculate score change trend
        current_long_score = score_data.get('long_score', 0)
        score_change_trend = ''
        
        if prev_score:
            if current_long_score > prev_score.long_score:
                score_change_trend = 'Uptrend'
            elif current_long_score < prev_score.long_score:
                score_change_trend = 'Downtrend'
            else:
                score_change_trend = ''
        else:
            score_change_trend = ''

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
            score_change_trend=score_change_trend
        )
        
        print("Inserting ticker score:", db_ticker_score.__dict__)
        
        db.add(db_ticker_score)
        db.commit()
        db.refresh(db_ticker_score)
        return db_ticker_score
    
    except Exception as e:
        db.rollback()
        print(f"Error inserting ticker score: {e}")
        raise

def get_ticker_scores(db: Session, ticker_symbol: str = None):
    query = db.query(TickerScore)
    
    if ticker_symbol:
        query = query.filter(TickerScore.ticker_symbol == ticker_symbol)

    latest_scores_subquery = (
        db.query(TickerScore.ticker_symbol, func.max(TickerScore.created_at).label('max_created_at'))
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

def delete_old_ticker_scores(db: Session, days_to_keep: int = 7):
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    db.query(TickerScore).filter(TickerScore.created_at < cutoff_date).delete()
    db.commit()