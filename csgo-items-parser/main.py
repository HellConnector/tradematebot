import asyncio
import re

import aiohttp
import vdf

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


def get_stickers(tokens: dict) -> set[str]:
    backslash = "\\"
    generator = (
        value
        for key, value in tokens.items()
        if re.search(r"StickerKit_(?!.*desc|Default|dh|dz)", key)
    )
    return set(
        (
            f"Sticker | {re.sub(rf'^StickerKit(_{backslash}w+{backslash}s+)', '', line)}"
            for line in generator
            if "(Gold) | Cluj-Napoca 2015" not in line
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
            re.sub(r"^CSGO_crate(_\w+\s+)", "", line).replace("Holo/Foil", "Holo-Foil")
            for line in generator
            if "Case Key" not in line
        )
    )


def get_keys(tokens: dict) -> set[str]:
    generator = (
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
    return set(re.sub(r"^CSGO(_\w+\s+)", "", line) for line in generator)


def get_agents(tokens: dict) -> set[str]:
    generator = (
        value
        for key, value in tokens.items()
        if re.search(
            r"(CSGO_CustomPlayer|CSGO_Customplayer)(?!.*(_Desc|_t_|_ct_))", key
        )
    )
    return set(
        (
            re.sub(r"(CSGO_CustomPlayer|CSGO_Customplayer)_(\w+\s+)", "", line)
            for line in generator
        )
    )


def get_patches(sticker_kits: dict, tokens: dict) -> set[str]:
    return set(
        f"Patch | {tokens.get(item['item_name'].lstrip('#'))}"
        for item in sticker_kits.values()
        if item["item_name"].startswith("#PatchKit") or "_teampatch_" in item["name"]
    )


def get_skins(items_game: dict, tokens: dict, items_game_cdn: set[str]) -> set[str]:
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
        # and value.get("item_name") is not None
    ]
    paintkits: dict = {
        value["name"]: value for value in items_game["paint_kits"].values()
    }

    lootlists: dict = items_game["client_loot_lists"]

    # Needs if wear_remap_min/max don't exist in paint kit
    default_paint_kit = paintkits.get("default")
    all_skins = set()

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
                and list(item_lootlist.keys())[0] in NON_STATTRAK_COLLECTIONS
            ):
                is_stattrak = False

            if (
                item_lootlist
                and list(item_lootlist.keys())[0] in SOUVENIR_COLLECTIONS
                # # R8 Bone Mask has Souvenir (WTF!?) and MP5-SD Lab Rat
            ) or skin_key in ("weapon_revolver_sp_tape", "weapon_mp5sd_hy_labrat_mp5"):
                is_souvenir = True

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

                pass

    return all_skins


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

    # Get all item's market hashnames
    skins = get_skins(items_game, csgo_english_tokens_lower, items_game_cdn)
    patches = get_patches(items_game["sticker_kits"], csgo_english_tokens)
    stickers = get_stickers(csgo_english_tokens)
    cases = get_cases(csgo_english_tokens)
    keys = get_keys(csgo_english_tokens)
    agents = get_agents(csgo_english_tokens)

    # TODO write item to database

    pass
