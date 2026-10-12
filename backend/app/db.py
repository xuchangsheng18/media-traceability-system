import os

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True, pool_size=4, max_overflow=2)


def health():
    with engine.connect() as connection:
        return connection.execute(text("SELECT 1")).scalar() == 1
