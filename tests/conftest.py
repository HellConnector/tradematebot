import logging

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import bot.db as db


@pytest.fixture(scope='session', autouse=True)
def log() -> logging.Logger:
    """Сессионная фикстура для логирования.

    Инициаллизирует логгер в начале тестовой сессии. Рассчитывает и выводит
    время выполнения всей тестовой сессии.

    Returns:
        logging.Logger: Экземпляр логгера.
    """
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
    """Хук для pytest.

    Изменяет представление параметров, передаваемых через parametrize.
    Нужен для корректного отображения кириллицы в консоли и в PyCharm.

    Args:
        argname (str): Имя параметра (аргумент)
        config (_pytest.config.Config): Объект конфигурации pytest
        val (str): Значение параметра.

    Returns:
        str: ID для теста.
    """
    return f'{argname} -> {repr(val)}'
