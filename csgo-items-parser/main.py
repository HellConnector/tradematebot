import asyncio
import itertools
import logging
import re
from typing import Any

import aiohttp
import vdf
from sqlalchemy import select

from bot.db import get_async_session, Skin, Container, Sticker, Tool, Agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

NON_STATTRAK_COLLECTIONS = (
    "set_dust",
    "set_aztec",
    "set_militia",
    "set_office",
    "set_assault",
    "set_bravo_ii",
    "set_bank",
    "set_baggage",
    "set_gods_and_monsters",
    "set_chopshop",
    "set_kimono",
    "set_stmarc",
    "set_canals",
    "set_norse",
    "set_op10_ct",
    "set_op10_t",
    "set_train_2021",
    "set_anubis",
)

SOUVENIR_COLLECTIONS = (
    "set_vertigo",
    "set_inferno",
    "set_nuke",
    "set_dust_2",
    "set_train",
    "set_mirage",
    "set_italy",
    "set_lake",
    "set_safehouse",
    "set_overpass",
    "set_cobblestone",
    "set_cache",
    "set_nuke_2",
    "set_inferno_2",
    "set_blacksite",  # this set doesn't exist in any lootlist
    "set_dust_2_2021",
    "set_mirage_2021",
    "set_op10_ancient",
    "set_vertigo_2021",
)


async def get_text_by_url(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def get_texts():
    items_game_url = (
        "https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo"
        "/scripts/items/items_game.txt"
    )
    csgo_english_url = (
        "https://raw.githubusercontent.com/SteamDatabase/GameTracking-CSGO/master/csgo"
        "/resource/csgo_english.txt"
    )
    items_game_cdn_url = (
        "https://raw.githubusercontent.com/SteamDatabase/GameTracking"
        "-CSGO/master/csgo/scripts/items/items_game_cdn.txt"
    )

    results = await asyncio.gather(
        get_text_by_url(items_game_url),
        get_text_by_url(csgo_english_url),
        get_text_by_url(items_game_cdn_url),
    )

    return results


def get_stickers(tokens: dict, sticker_kits: dict) -> set[str]:
    generator = (
        value
        for key, value in tokens.items()
        if re.search(r"StickerKit_(?!.*desc|Default|dh|dz)", key)
        and not re.search(
            r"(2014|2015|2016|2017|2018|2019)_team(_[a-z0-9_]+_)+gold", key
        )
        and not re.search(r"kat2014_(?!esl1|esl2)([_[a-z0-9]+)_+foil", key)
        and not re.search(r"roles_(?!pro)([a-z]+)_*foil", key)
        and key in sticker_kits
    )
    return set(
        (
            f"Sticker | {line}"
            for line in generator
            if "(Foil) | Cologne 2014" not in line
            and "Cologne 2014 (Gold)" not in line
            and "(Gold) | Katowice 2015" not in line
            and "(Gold) | Cologne 2015" not in line
            and "(Gold) | Cluj-Napoca 2015" not in line
            and "(Gold) | MLG Columbus 2016" not in line
            and "(Gold)  | MLG Columbus 2016" not in line  # double space (WTF)
            and "(Gold) | Cologne 2016" not in line
            and "(Gold) | Atlanta 2017" not in line
            and "All-Stars" not in line
        )
    )


def get_cases(tokens: dict) -> set[str]:
    generator = (
        value
        for key, value in tokens.items()
        if re.search(
            (
                r"CSGO_crate_(?!.*_desc|.*tag|.*spray_|.*bundle_|.*radicals_capsule"
                r"|.*pack[0-9+]|.*tinyname|.*key_community|.*_fang|.*_recoil"
                r"|.*surfshop|.*swap|.*pack_op|.*_web|.*_groupname)"
            ),
            key,
        )
    )
    return set(
        (
            line.replace("Holo/Foil", "Holo-Foil")
            for line in generator
            if "Case Key" not in line
        )
    )


def get_keys(tokens: dict) -> set[str]:
    return set(
        value
        for key, value in tokens.items()
        if re.search(
            (
                r"crate_key(?!.*desc|.*Recoil|.*Dreams|.*Fracture|.*Fang|.*Riptide"
                r"|.*Prisma\s2|.*Revolution|.*Shattered|.*Snakebite)"
            ),
            f"{key}{value}",
        )
    )


def get_agents(tokens: dict) -> dict[str, set]:
    agents = {}
    agents["t"] = set()
    agents["ct"] = set()
    generator = (
        (key.lower(), value)
        for key, value in tokens.items()
        if re.search(
            r"(CSGO_CustomPlayer|CSGO_Customplayer)(?!.*(_Desc|_t_|_ct_))", key
        )
    )
    for key, value in generator:
        if key.startswith("csgo_customplayer_t"):
            agents["t"].add(value)
        else:
            agents["ct"].add(value)
    return agents


def get_viewer_passes(tokens: dict) -> set[str]:
    return set(
        value
        for key, value in tokens.items()
        if re.search(
            r"(CSGO_TournamentPass)(?!.*(_Desc|_desc|_title|_tinyname|_charge))", key
        )
    )


def get_operation_passes(tokens: dict) -> set[str]:
    return set(
        value
        for key, value in tokens.items()
        if re.search(r"(CSGO_Ticket)(?!.*(_Desc))", key)
    )


def get_patches(sticker_kits: dict, tokens: dict) -> set[str]:
    return set(
        f"Patch | {tokens.get(item['item_name'].lstrip('#'))}"
        for item in sticker_kits.values()
        if item["item_name"].startswith("#PatchKit") or "_teampatch_" in item["name"]
    )


def get_skins(
    items_game: dict, tokens: dict, items_game_cdn: set[str]
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    items = [
        value
        for value in items_game["items"].values()
        if (prefab := value.get("prefab")) is not None
        and (
            prefab in ("hands_paintable", "melee_unusual")
            or prefab.startswith("weapon_")
        )
        and not prefab.startswith("weapon_case")
        and (name := value.get("name")) is not None
        and name
        not in (
            "weapon_shield",
            "weapon_zone_repulsor",
            "weapon_fists",
            "weapon_breachcharge",
            "weapon_tablet",
            "weapon_diversion",
            "weapon_snowball",
            "weapon_bumpmine",
            "weapon_spanner",
        )
        and "grenade" not in name
    ]
    paintkits: dict = {
        value["name"]: value for value in items_game["paint_kits"].values()
    }

    lootlists: dict = items_game["client_loot_lists"]

    # Needs if wear_remap_min/max don't exist in paint kit
    default_paint_kit = paintkits.get("default")
    all_skins = set()
    all_skins_dict = {}

    def get_market_name(item: dict, prefab: dict) -> str:
        if item_name := item.get("item_name"):
            return tokens.get(item_name.lstrip("#").lower())
        else:
            return tokens.get(prefab["item_name"].lstrip("#").lower())

    def get_paintkit_name(paintkit: dict):
        return tokens.get(paintkit["description_tag"].lstrip("#").lower())

    def get_possible_qualities(paintkit: dict) -> list[str]:
        results = []
        quality_ranges = {
            "Factory New": (0.00, 0.07),
            "Minimal Wear": (0.07, 0.15),
            "Field-Tested": (0.15, 0.38),
            "Well-Worn": (0.38, 0.45),
            "Battle-Scarred": (0.45, 1.00),
        }
        wear_remap_min = paintkit.get("wear_remap_min")
        wear_remap_max = paintkit.get("wear_remap_max")
        if wear_remap_min is None:
            wear_remap_min = default_paint_kit["wear_remap_min"]
        if wear_remap_max is None:
            wear_remap_max = default_paint_kit["wear_remap_max"]

        for quality in quality_ranges:
            if (
                float(wear_remap_min) < quality_ranges[quality][1]
                and float(wear_remap_max) > quality_ranges[quality][0]
            ):
                results.append(quality)

        return results

    def get_all_prefabs(prefab: str) -> set[str] | None:
        results = set()
        results.add(prefab)
        total_prefabs = items_game["prefabs"]
        while (
            temp_prefab := total_prefabs.get(prefab)
        ) is not None and "prefab" in temp_prefab:
            results.add(prefab := temp_prefab["prefab"])
        return results

    def get_lootlist(lootlist_key: str) -> dict | None:
        sub_loot_list_key = None
        for key, value in lootlists.items():
            if lootlist_key in value:
                sub_loot_list_key = key
                break
        if sub_loot_list_key:
            for key, value in lootlists.items():
                if sub_loot_list_key in value:
                    return {key: value}
        return

    def has_souvenir(item_lootlist: dict) -> bool:
        lootlist_key = list(item_lootlist.keys())[0]
        all_item_lootlists = [
            key for key, value in lootlists.items() if lootlist_key in value
        ]

        for item in items_game["items"].values():
            for lootlist in all_item_lootlists:
                if item["name"] == lootlist:
                    prefabs = get_all_prefabs(item["prefab"])
                    if "weapon_case_souvenirpkg" in prefabs:
                        return True

        return False

    for item in items:
        for paintkit_key, paintkit_value in paintkits.items():
            is_default = paintkit_key == "default"
            item_prefab = item["prefab"]

            is_glove = item_prefab == "hands_paintable"
            is_knife = item_prefab == "melee_unusual"

            skin_key = item["name"] if is_default else f"{item['name']}_{paintkit_key}"

            if (
                skin_key.lower() not in items_game_cdn
                or (skin_key.startswith("weapon") and is_default and not is_knife)
                or (is_glove and is_default)
            ):
                continue

            prefab = items_game["prefabs"][item_prefab]
            item_lootlist_key = f"[{paintkit_key}]{item['name']}"
            all_prefabs = get_all_prefabs(item_prefab)
            item_lootlist = get_lootlist(item_lootlist_key)

            is_souvenir = (
                False if item_lootlist is None else has_souvenir(item_lootlist)
            )

            is_stattrak = "statted_item_base" in all_prefabs

            if (
                item_lootlist
                and list(item_lootlist.keys())[0] in SOUVENIR_COLLECTIONS
                # # R8 Bone Mask has Souvenir (WTF!?) and MP5-SD Lab Rat
            ) or skin_key in ("weapon_revolver_sp_tape", "weapon_mp5sd_hy_labrat_mp5"):
                is_souvenir = True

            if (
                item_lootlist
                and not is_souvenir
                and any(
                    map(
                        lambda s: list(item_lootlist.keys())[0].startswith(s),
                        NON_STATTRAK_COLLECTIONS,
                    )
                )
            ):
                is_stattrak = False

            market_name = get_market_name(item, prefab)
            paintkit_name = (
                get_paintkit_name(paintkit_value) if not is_default else None
            )

            qualities = get_possible_qualities(paintkit_value)
            for quality in qualities:
                if (is_knife or is_glove) and not is_default:
                    if is_stattrak:
                        all_skins.add(
                            f"★ StatTrak™ {market_name} | {paintkit_name} ({quality})"
                        )
                    all_skins.add(f"★ {market_name} | {paintkit_name} ({quality})")
                # Guns
                if not is_knife and not is_glove and not is_default:
                    all_skins.add(f"{market_name} | {paintkit_name} ({quality})")
                    if is_souvenir:
                        all_skins.add(
                            f"Souvenir {market_name} | {paintkit_name} ({quality})"
                        )
                    elif is_stattrak:
                        all_skins.add(
                            f"StatTrak™ {market_name} | {paintkit_name} ({quality})"
                        )

            if is_knife and is_default:  # Vanilla knife
                all_skins.add(f"★ {market_name}")
                all_skins.add(f"★ StatTrak™ {market_name}")

            full_name = (
                f"{market_name} | {paintkit_name}"
                if not is_default and paintkit_name is not None
                else market_name
            )
            all_skins_dict[full_name] = {}
            all_skins_dict[full_name]["skin_type"] = (
                "glove" if is_glove else "knife" if is_knife else "gun"
            )
            all_skins_dict[full_name][
                "collection"
            ] = None  # Unused field in database model TODO create migration to remove
            all_skins_dict[full_name]["name"] = market_name
            all_skins_dict[full_name]["skin"] = paintkit_name
            all_skins_dict[full_name]["full_name"] = full_name
            all_skins_dict[full_name]["fn"] = (
                False if is_default and is_knife else "Factory New" in qualities
            )
            all_skins_dict[full_name]["mw"] = (
                False if is_default and is_knife else "Minimal Wear" in qualities
            )
            all_skins_dict[full_name]["ft"] = (
                False if is_default and is_knife else "Field-Tested" in qualities
            )
            all_skins_dict[full_name]["ww"] = (
                False if is_default and is_knife else "Well-Worn" in qualities
            )
            all_skins_dict[full_name]["bs"] = (
                False if is_default and is_knife else "Battle-Scarred" in qualities
            )
            all_skins_dict[full_name]["st"] = (
                True if is_stattrak and not is_souvenir else False
            )
            all_skins_dict[full_name]["sv"] = is_souvenir

    return all_skins_dict, all_skins


async def add_skins_to_database(skins: dict[str, dict]):
    added_count = 0
    async with get_async_session() as session:
        current_db_skins = set((await session.scalars(select(Skin.full_name))).all())
        for skin in skins:
            if skin not in current_db_skins:
                session.add(Skin.from_dict(skins[skin]))
                logger.info(f"Added [{skin}] to [skins] table")
                added_count += 1

    logger.info(f"Added [{added_count}] rows to [skins] table")


async def add_containers_to_database(containers: set[str]):
    added_count = 0
    async with get_async_session() as session:
        current_db_containers = set(
            (await session.scalars(select(Container.name))).all()
        )
        for container in containers:
            if container not in current_db_containers:
                session.add(Container("from_parser", container))
                logger.info(f"Added [{container}] to [containers] table")
                added_count += 1

    logger.info(f"Added [{added_count}] rows to [containers] table")


async def add_patches_to_database(patches: set[str]):
    added_count = 0
    async with get_async_session() as session:
        current_db_patches = set(
            (
                await session.scalars(
                    select(Sticker.full_name).where(Sticker.sticker_type == "patch")
                )
            ).all()
        )
        for patch in patches:
            if patch not in current_db_patches:
                session.add(Sticker.from_hashname("patch", patch))
                logger.info(f"Added [{patch}] to [stickers] table")
                added_count += 1

    logger.info(f"Added [{added_count}] rows to [stickers] table")


async def add_stickers_to_database(stickers: set[str]):
    added_count = 0
    async with get_async_session() as session:
        current_db_stickers = set(
            (
                await session.scalars(
                    select(Sticker.full_name).where(Sticker.sticker_type != "patch")
                )
            ).all()
        )
        for sticker in stickers:
            if (
                sticker := sticker.removeprefix("Sticker | ")
            ) not in current_db_stickers:
                session.add(Sticker.from_hashname("sticker", sticker))
                logger.info(f"Added [{sticker}] to [stickers] table")
                added_count += 1

    logger.info(f"Added [{added_count}] rows to [stickers] table")


async def add_tools_to_database(
    keys: set[str], viewer_passes: set[str], operation_passes: set[str]
):
    added_count = 0
    async with get_async_session() as session:
        current_db_tools = set((await session.scalars(select(Tool.name))).all())
        for tool in itertools.chain(keys, viewer_passes, operation_passes):
            if tool not in current_db_tools:
                session.add(Tool(tool))
                logger.info(f"Added [{tool}] to [tools] table")
                added_count += 1

    logger.info(f"Added [{added_count}] rows to [tools] table")


async def add_agents_to_database(agents: dict[str, set]):
    added_count = 0
    async with get_async_session() as session:
        current_db_agents = set((await session.scalars(select(Agent.name))).all())
        for side, agents_set in agents.items():
            for name in agents_set:
                if name not in current_db_agents:
                    session.add(Agent(side, name))
                    logger.info(f"Added [{side} - {name}] to [agents] table")
                    added_count += 1

    logger.info(f"Added [{added_count}] rows to [agents] table")


async def add_market_items_to_database(
    skins_dict: dict[str, dict[str, Any]],
    cases: set,
    patches: set,
    stickers: set,
    keys: set,
    viewer_passes: set,
    operation_passes: set,
    agents: dict,
):
    await add_skins_to_database(skins_dict)
    await add_containers_to_database(cases)
    await add_patches_to_database(patches)
    await add_stickers_to_database(stickers)
    await add_tools_to_database(keys, viewer_passes, operation_passes)
    await add_agents_to_database(agents)


def save_to_file(filename: str, content: set[str]):
    threshold, content_size = 1000, len(content)
    chunks = content_size // threshold
    content_iterator = iter(content)
    if chunks == 0:
        with open(filename, "w", encoding="utf-8") as file:
            file.write("\n".join(content))
    else:
        for i in range(chunks + 1):
            iteration_count = (
                content_size - threshold * chunks if i == chunks else threshold
            )

            with open(f"{filename}-{i}", "w", encoding="utf-8") as file:
                file.write(
                    "\n".join(next(content_iterator) for _ in range(iteration_count))
                )


if __name__ == "__main__":
    items_game_text, csgo_english_text, items_game_cdn_text = asyncio.run(get_texts())

    items_game = vdf.loads(items_game_text)["items_game"]
    csgo_english = vdf.loads(csgo_english_text)
    items_game_cdn = set(
        line.split("=")[0] for line in items_game_cdn_text.split("\n") if "=" in line
    )
    csgo_english_tokens_lower = {
        key.lower(): value for key, value in csgo_english["lang"]["Tokens"].items()
    }
    csgo_english_tokens = csgo_english["lang"]["Tokens"]

    sticker_kits = {
        value["item_name"].lstrip("#"): value
        for value in items_game["sticker_kits"].values()
        if not value["name"].startswith("spray")
        and not re.search(r"^de(_[a-z0-9]+_)gold$", value["name"])
    }

    agents = get_agents(csgo_english_tokens)
    viewer_passes = get_viewer_passes(csgo_english_tokens)
    operation_passes = get_operation_passes(csgo_english_tokens)

    # Dict is needed to write all skins to database.
    # Set is needed to write all hashnames to file and check for the market price.
    skins_dict, skins_set = get_skins(
        items_game, csgo_english_tokens_lower, items_game_cdn
    )
    cases = get_cases(csgo_english_tokens)

    patches = get_patches(items_game["sticker_kits"], csgo_english_tokens)
    stickers = get_stickers(csgo_english_tokens, sticker_kits)
    keys = get_keys(csgo_english_tokens)

    # save_to_file("cases", cases)  # OK
    # save_to_file("agents", agents)  # OK
    # save_to_file("keys", keys)  # OK
    # save_to_file("patches", patches)  # OK
    # save_to_file("stickers", stickers) # OK
    # save_to_file("skins", skins_set)  # OK
    # save_to_file("viewer_passes", viewer_passes)  # OK
    # save_to_file("operation_passes", operations_passes)  # OK

    asyncio.run(
        add_market_items_to_database(
            skins_dict,
            cases,
            patches,
            stickers,
            keys,
            viewer_passes,
            operation_passes,
            agents,
        )
    )
