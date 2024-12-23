# seeder.py
from sqlalchemy.orm import Session
from models.symbols import Symbols  # Adjust import based on your project structure
from database import engine, SessionLocal
from sqlalchemy import inspect
from utils.symbols import get_symbols

def is_database_empty(session: Session, model):
    """
    Check if a specific table is empty
    """
    inspector = inspect(engine)
    if not inspector.has_table(model.__tablename__):
        return True
    
    return session.query(model).first() is None

def seed_symbols(session: Session):
    """
    Seed initial symbols if the table is empty
    """
    if is_database_empty(session, Symbols):
        symbols_list = get_symbols()
        initial_symbols = []
        for item in symbols_list:
            symbol = Symbols(name=item)
            initial_symbols.append(symbol)
        
        # Add and commit the initial users
        session.add_all(initial_symbols)
        session.commit()
        print(f"Seeded {len(initial_symbols)} symbols")
    else:
        print("Symbols table already contains data. Skipping seeding.")

def seed_database():
    """
    Main seeding function to run all seeders
    """
    # Create all tables
    from database import Base  # Import your base model
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    session = SessionLocal()
    
    try:
        # Run different seeders
        seed_symbols(session)
        # Add more seed functions for other models as needed
        
    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        session.close()

        