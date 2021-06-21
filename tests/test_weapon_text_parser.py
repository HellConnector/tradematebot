import pytest

import bot.names as nm
import bot.parsers as ps

data = pytest.mark.parametrize


@pytest.mark.database
@data('query', ['w beast fn st'])
def test_positive(log, dbs, query):
    names = ps.parse_weapon_text(query, dbs)
    for name in names:
        log.info(f'Проверка скина [{name}]')
        assert name.startswith(nm.ST)
        assert name.endswith(f'({nm.WEAPON_QUALITY["fn"]})')


@pytest.mark.database
@data('quality', nm.WEAPON_QUALITY.keys())
@data('skin_type', ['', 'st', 'sv'])
def test_ak47(log, dbs, quality, skin_type):
    query = f'w ak-47 {quality} {skin_type}'.strip()
    log.info(query)
    names = ps.parse_weapon_text(query, dbs)
    assert len(names) > 0, (f'Нет скинов AK-47 качества [{nm.WEAPON_QUALITY[quality]}] '
                            f'и типом [{skin_type}]')


@pytest.mark.database
@data('query, count', [('a ct', 18), ('a t', 24)])
def test_agents(dbs, query, count):
    assert len(ps.parse_agent_text(query, dbs)) == count, 'Количество агентов неверно'


# TODO @er3mey
@pytest.mark.database
def test_knives(dbs):
    assert len(ps.parse_knife_text('k m9 fn st', dbs)) == 23, 'Количество ножей неверно'


@pytest.mark.database
@data('query,expected', [
    ('s howl', True),
    ('s adren', True),
    ('s sdfadfa', False)
])
def test_stickers(log, dbs, query, expected):
    names = ps.parse_sticker_text(query, dbs)
    log.info('\n'.join(names))
    assert (len(names) > 0) is expected, f'Стикер не найден по запросу [{query}]'
