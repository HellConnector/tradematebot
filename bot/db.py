import os
import typing
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

DB_ADDR = os.getenv('DATABASE_URL')

engine = create_engine(DB_ADDR, echo=False)
Base = declarative_base(bind=engine)


@contextmanager
def get_session(**kwargs) -> typing.ContextManager[Session]:
    """Provide a transactional scope around a series of operations."""
    session = Session(bind=engine, **kwargs)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
