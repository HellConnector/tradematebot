import logging

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import bot.db as db


@pytest.fixture(scope='session', autouse=True)
def log() -> logging.Logger:
    log_s = logging.getLogger('LOG')
    return log_s


@pytest.fixture(scope='session')
def db_engine():
    return create_engine(db.DB_ADDR, echo=False)


@pytest.fixture(scope='module')
def dbs(db_engine) -> Session:
    session = Session(bind=db_engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def pytest_make_parametrize_id(config, val, argname) -> str:
    return f'{argname} -> {repr(val)}'
