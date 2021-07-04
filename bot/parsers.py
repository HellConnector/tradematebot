from typing import List

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

import bot.models as mdl
import bot.names as nm


def parse_weapon_text(text: str, s: Session) -> List[str]:
    """Parser method for weapons.

    Returns a list with the full names of the weapon skin for requests on the Steam market.

    Args:
        text (str): query from user.
        s (Session): database session object.

    Returns:
        List[str]: list with name for http-requests on Steam market.
    """
    names = []
    table = mdl.Skin
    words = text.split()
    q_idx = [words.index(i) for i in nm.WEAPON_QUALITY if i in words][0]
    short_q, quality = words[q_idx], nm.WEAPON_QUALITY[words[q_idx]]
    st = 'st' in words[q_idx:]
    sv = 'sv' in words[q_idx:]
    name_keys = words[1:q_idx]
    t = None
    q = table.quality[short_q]
    if st:
        t = table.st
    elif sv:
        t = table.sv

    if t:
        skins = s.query(table).filter(q.is_(True), t.is_(True), table.skin_type == 'gun', and_(
            func.lower(table.full_name).contains(n) for n in name_keys)).all()
    else:
        skins = s.query(table).filter(q.is_(True), table.skin_type == 'gun', and_(
            func.lower(table.full_name).contains(n) for n in name_keys)).all()
    for skin in skins:
        if st:
            name = f'{nm.ST} {skin.full_name} ({quality})'
        elif sv:
            name = f'{nm.SV} {skin.full_name} ({quality})'
        else:
            name = f'{skin.full_name} ({quality})'
        names.append(name)
    return names


def parse_glove_text(text: str, s: Session) -> List[str]:
    names = []
    table = mdl.Skin
    words = text.split()
    q_idx = [words.index(i) for i in nm.WEAPON_QUALITY if i in words][0]
    short_q, quality = words[q_idx], nm.WEAPON_QUALITY[words[q_idx]]
    name_keys = words[1:q_idx]
    q = table.quality[short_q]

    skins = s.query(table).filter(q.is_(True), table.skin_type == 'glove', and_(
        func.lower(table.full_name).contains(n) for n in name_keys)).all()
    for skin in skins:
        name = f'{nm.STAR} {skin.full_name} ({quality})'
        names.append(name)
    return names


def parse_container_text(text: str, s: Session) -> List[str]:
    names = []
    table = mdl.Container
    words = text.split()
    name_keys = words[1:]
    containers = s.query(table).filter(and_(
        func.lower(table.name).contains(n) for n in name_keys)).all()
    if containers:
        for container in containers:
            names.append(container.name)
    return names


def parse_agent_text(text: str, s: Session) -> List[str]:
    names = []
    table = mdl.Agent
    words = text.split()
    side = words[1] if words[1] in ['t', 'ct'] else None
    name_keys = words[2:] if side else words[1:]
    if side:
        agents = s.query(table).filter(table.side == side, and_(
            func.lower(table.name).contains(n) for n in name_keys)).all()
    else:
        agents = s.query(table).filter(and_(
            func.lower(table.name).contains(n) for n in name_keys)).all()
    for agent in agents:
        names.append(agent.name)
    return names


def parse_tool_text(text: str, s: Session) -> List[str]:
    names = []
    table = mdl.Tool
    words = text.split()
    name_keys = words[1:]
    tools = s.query(table).filter(and_(
        func.lower(table.name).contains(n) for n in name_keys)).all()
    if tools:
        for tool in tools:
            names.append(tool.name)
    return names


def parse_sticker_text(text: str, s: Session) -> List[str]:
    names = []
    table = mdl.Sticker
    words = text.split()
    stickers = s.query(table).filter(table.sticker_type.in_(("tournament", "regular")), and_(
        func.lower(table.full_name).contains(n) for n in words[1:])).all()
    for sticker in stickers:
        names.append(f'Sticker | {sticker.full_name}')
    return names


def parse_patch_text(text: str, s: Session) -> List[str]:
    names = []
    table = mdl.Sticker
    words = text.split()
    name_keys = words[1:]
    patches = s.query(table).filter(table.sticker_type == 'patch', and_(
        func.lower(table.full_name).contains(n) for n in name_keys)).all()
    if patches:
        for patch in patches:
            names.append(patch.full_name)
    return names


def parse_knife_text(text: str, s: Session) -> List[str]:
    table = mdl.Skin
    names = []
    words = text.split()
    q_idx = [i for i, j in enumerate(words) if j in nm.WEAPON_QUALITY]
    if len(q_idx) > 0:
        q_idx = q_idx[0]
        short_q, quality = words[q_idx], nm.WEAPON_QUALITY[words[q_idx]]
        st = 'st' in words[q_idx:]
        t = table.st if st else None
        name_keys = words[1:q_idx]
    else:
        st = 'st' in words[1:]
        if st:
            name_keys = words[1:words.index('st')]
            t = table.st
        else:
            name_keys = words[1:]
        short_q, quality = None, None
        is_q, q = False, None
    if short_q:
        q = table.quality[short_q]
        is_q = True

    if st and is_q:
        skins = s.query(table).filter(q.is_(True), t.is_(True), table.skin_type == 'knife', and_(
            func.lower(table.full_name).contains(n) for n in name_keys)).all()
    elif not st and is_q:
        skins = s.query(table).filter(q.is_(True), table.skin_type == 'knife', and_(
            func.lower(table.full_name).contains(n) for n in name_keys)).all()
    elif st and not is_q:
        skins = s.query(table).filter(
            t.is_(True), table.skin_type == 'knife', table.skin.is_(None),
            and_(func.lower(table.full_name).contains(n) for n in name_keys)).all()
    else:
        skins = s.query(table).filter(table.skin_type == 'knife', table.skin.is_(None), and_(
            func.lower(table.full_name).contains(n) for n in name_keys)).all()

    for skin in skins:
        name = None
        if st and is_q:
            name = f'{nm.STAR} {nm.ST} {skin.full_name} ({quality})'
        elif not st and is_q:
            name = f'{nm.STAR} {skin.full_name} ({quality})'
        elif st and not is_q:
            names.extend(list(map(lambda x: f'{nm.STAR} {nm.ST} {x}', skin.get_names())))
        elif not st and not is_q:
            names.extend(list(map(lambda x: f'{nm.STAR} {x}', skin.get_names())))
        if name:
            names.append(name)
    return names
