import pkgutil

from sqlalchemy import text

import bot.db as db
import bot.models as mdl
import bot.utils as bu
from bot.logger import log

steam_tables = [
    mdl.Skin.__table__, mdl.Agent.__table__, mdl.Container.__table__,
    mdl.Sticker.__table__, mdl.Tool.__table__
]


def fill_steam_items():
    tables = ('agents', 'containers', 'skins', 'stickers', 'tools')
    db.Base.metadata.drop_all(db.engine, tables=steam_tables)
    db.Base.metadata.create_all(db.engine, tables=steam_tables)
    with db.get_session() as s:
        for table in tables:
            query = text(pkgutil.get_data('resources', f'{table}.sql').decode('utf-8'))
            s.execute(query)

    log.info('Database initialized')


if __name__ == '__main__':
    db.Base.metadata.create_all(db.engine)
    bu.update_price_limits()
    fill_steam_items()
