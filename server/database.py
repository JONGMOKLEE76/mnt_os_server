from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.sqlite import insert
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mnt_data.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    import models
    Base.metadata.create_all(bind=engine)

def upsert_dataframe(df, model_class, batch_size=5000):
    """
    Upserts a pandas DataFrame into the database using the model_class.
    Processes data in batches to avoid SQLite's parameter limits.
    Uses a single transaction for the entire DataFrame for performance.
    """
    data = df.to_dict(orient='records')
    if not data:
        return 0

    unique_keys = ['Planweek', 'Created_at', 'Division', 'From Site', 'To Site', 'Mapping Model.Suffix', 'Category', 'Week Name']
    total_affected = 0

    # Use a single transaction for the entire chunk
    with engine.begin() as conn:
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            stmt = insert(model_class).values(batch)
            update_cols = {c.name: c for c in stmt.excluded if c.name not in unique_keys and c.name != 'id'}
            
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=unique_keys,
                set_=update_cols
            )
            
            result = conn.execute(upsert_stmt)
            total_affected += result.rowcount
            
    return total_affected
