from typing import List

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot import db, constants


async def parse_weapon_text(text: str, s: AsyncSession) -> List[str]:
    """Parser method for weapons.

    Returns a list with the full names of the weapon skin
    for requests on the Steam market.

    Args:
        text (str): query from user.
        s (AsyncSession): database session object.

    Returns:
        List[str]: list with name for http-requests on Steam market.
    """
    names = []
    table = db.Skin
    words = text.split()
    q_idx = [words.index(i) for i in constants.WEAPON_QUALITY if i in words][0]
    short_q, quality = words[q_idx], constants.WEAPON_QUALITY[words[q_idx]]
    st = "st" in words[q_idx:]
    sv = "sv" in words[q_idx:]
    name_keys = words[1:q_idx]
    t = None
    q = table.quality[short_q]
    if st:
        t = table.st
    elif sv:
        t = table.sv

    if t:
        skins = await s.scalars(
            select(table.full_name).filter(
                q.is_(True),
                t.is_(True),
                table.skin_type == "gun",
                and_(
                    func.lower(table.full_name).contains(n) for n in name_keys
                ),
            )
        )
    else:
        skins = await s.scalars(
            select(table.full_name).filter(
                q.is_(True),
                table.skin_type == "gun",
                and_(
                    func.lower(table.full_name).contains(n) for n in name_keys
                ),
            )
        )
    for skin in skins:
        if st:
            name = f"{constants.ST} {skin} ({quality})"
        elif sv:
            name = f"{constants.SV} {skin} ({quality})"
        else:
            name = f"{skin} ({quality})"
        names.append(name)
    return names


async def parse_glove_text(text: str, s: AsyncSession) -> List[str]:
    table = db.Skin
    words = text.split()
    q_idx = [words.index(i) for i in constants.WEAPON_QUALITY if i in words][0]
    short_q, quality = words[q_idx], constants.WEAPON_QUALITY[words[q_idx]]
    name_keys = words[1:q_idx]
    q = table.quality[short_q]

    skins = await s.scalars(
        select(table.full_name).filter(
            q.is_(True),
            table.skin_type == "glove",
            and_(func.lower(table.full_name).contains(n) for n in name_keys),
        )
    )
    return [f"{constants.STAR} {skin} ({quality})" for skin in skins]


async def parse_container_text(text: str, s: AsyncSession) -> List[str]:
    table = db.Container
    words = text.split()
    name_keys = words[1:]
    return list(
        map(
            lambda name: str(name),
            (
                await s.scalars(
                    select(table.name).filter(
                        and_(
                            func.lower(table.name).contains(n)
                            for n in name_keys
                        )
                    )
                )
            ).all(),
        )
    )


async def parse_agent_text(text: str, s: AsyncSession) -> List[str]:
    model = db.Agent
    words = text.split()
    side = words[1] if words[1] in ["t", "ct"] else None
    name_keys = words[2:] if side else words[1:]
    if side and name_keys:
        return list(
            map(
                lambda name: str(name),
                (
                    await s.scalars(
                        select(model.name).filter(
                            model.side == side,
                            and_(
                                func.lower(model.name).contains(n)
                                for n in name_keys
                            ),
                        )
                    )
                ).all(),
            )
        )
    if side and not name_keys:
        return list(
            map(
                lambda name: str(name),
                (
                    await s.scalars(
                        select(model.name).filter(
                            model.side == side,
                        )
                    )
                ).all(),
            )
        )
    if not side and name_keys:
        return list(
            map(
                lambda name: str(name),
                (
                    await s.scalars(
                        select(model.name).filter(
                            and_(
                                func.lower(model.name).contains(n)
                                for n in name_keys
                            ),
                        )
                    )
                ).all(),
            )
        )


async def parse_tool_text(text: str, s: AsyncSession) -> List[str]:
    table = db.Tool
    words = text.split()
    name_keys = words[1:]
    return list(
        map(
            lambda name: str(name),
            (
                await s.scalars(
                    select(table.name).filter(
                        and_(
                            func.lower(table.name).contains(n)
                            for n in name_keys
                        )
                    )
                )
            ).all(),
        )
    )


async def parse_sticker_text(text: str, s: AsyncSession) -> List[str]:
    table = db.Sticker
    words = text.split()
    stickers = await s.scalars(
        select(table.full_name).filter(
            table.sticker_type.not_in(("patch", "charm")),
            and_(func.lower(table.full_name).contains(n) for n in words[1:]),
        )
    )
    return [f"Sticker | {sticker}" for sticker in stickers]


async def parse_patch_text(text: str, s: AsyncSession) -> List[str]:
    table = db.Sticker
    words = text.split()
    name_keys = words[1:]
    return list(
        map(
            lambda name: str(name),
            (
                await s.scalars(
                    select(table.full_name).filter(
                        table.sticker_type == "patch",
                        and_(
                            func.lower(table.full_name).contains(n)
                            for n in name_keys
                        ),
                    )
                )
            ).all(),
        )
    )


async def parse_knife_text(text: str, s: AsyncSession) -> List[str]:
    is_q = False
    q, t = None, None
    table = db.Skin
    names = []
    words = text.split()
    q_idx = [i for i, j in enumerate(words) if j in constants.WEAPON_QUALITY]
    if len(q_idx) > 0:
        q_idx = q_idx[0]
        short_q, quality = words[q_idx], constants.WEAPON_QUALITY[words[q_idx]]
        st = "st" in words[q_idx:]
        t = table.st if st else None
        name_keys = words[1:q_idx]
    else:
        st = "st" in words[1:]
        if st:
            name_keys = words[1 : words.index("st")]
            t = table.st
        else:
            name_keys = words[1:]
        short_q, quality = None, None
        is_q, q = False, None
    if short_q:
        q = table.quality[short_q]
        is_q = True

    if st and is_q:
        skins = await s.scalars(
            select(table).filter(
                q.is_(True),
                t.is_(True),
                table.skin_type == "knife",
                and_(
                    func.lower(table.full_name).contains(n) for n in name_keys
                ),
            )
        )
    elif not st and is_q:
        skins = await s.scalars(
            select(table).filter(
                q.is_(True),
                table.skin_type == "knife",
                and_(
                    func.lower(table.full_name).contains(n) for n in name_keys
                ),
            )
        )
    elif st and not is_q:
        skins = await s.scalars(
            select(table).filter(
                t.is_(True),
                table.skin_type == "knife",
                table.skin.is_(None),
                and_(
                    func.lower(table.full_name).contains(n) for n in name_keys
                ),
            )
        )
    else:
        skins = (
            await s.scalars(
                select(table).filter(
                    table.skin_type == "knife",
                    table.skin.is_(None),
                    and_(
                        func.lower(table.full_name).contains(n)
                        for n in name_keys
                    ),
                )
            )
        ).all()

    for skin in skins:
        name = None
        if st and is_q:
            name = (
                f"{constants.STAR} {constants.ST} {skin.full_name} ({quality})"
            )
        elif not st and is_q:
            name = f"{constants.STAR} {skin.full_name} ({quality})"
        elif st and not is_q:
            names.extend(
                list(
                    map(
                        lambda x: f"{constants.STAR} {constants.ST} {x}",
                        skin.get_names(),
                    )
                )
            )
        elif not st and not is_q:
            names.extend(
                list(map(lambda x: f"{constants.STAR} {x}", skin.get_names()))
            )
        if name:
            names.append(name)
    return names
