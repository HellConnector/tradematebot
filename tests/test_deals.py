import pytest
from sqlalchemy import func

import bot.models as mdl


@pytest.mark.database
def test_item_has_deal(dbs):
    items = dbs.query(mdl.Item).order_by(func.random()).limit(5).all()
    for item in items:
        deals = dbs.query(mdl.Deal).filter(mdl.Deal.item_id == item.id).all()
        assert len(deals) > 0, f'Для предмета [{item.name}] нет сделок'
