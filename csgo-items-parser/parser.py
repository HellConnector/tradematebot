import re
import vdf


def get_content_by_pattern(file_content: list[str], pattern: str) -> list[str]:
    return [line for line in file_content if re.search(pattern, line)]


def get_file_content(file: str) -> list[str]:
    with open(file, encoding="utf-8") as f:
        return [line.replace('"', "").strip() for line in f]


def parse_stickers(content: list[str]) -> set[str]:
    backslash = "\\"
    return set(
        (
            f"Sticker | {re.sub(rf'^StickerKit(_{backslash}w+{backslash}s+)', '', line)}"
            for line in content
            if "(Gold) | Cluj-Napoca 2015" not in line
        )
    )


def parse_agents(content: list[str]) -> set[str]:
    return set(
        (
            re.sub(r"(CSGO_CustomPlayer|CSGO_Customplayer)_(\w+\s+)", "", line)
            for line in content
        )
    )


def parse_cases(content: list[str]) -> set[str]:
    return set(
        (
            re.sub(r"^CSGO_crate(_\w+\s+)", "", line).replace("Holo/Foil", "Holo-Foil")
            for line in content
            if "Case Key" not in line
        )
    )


def parse_keys(content: list[str]) -> set[str]:
    return set(re.sub(r"^CSGO(_\w+\s+)", "", line) for line in content)


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
    is_save = False
    csgo_english = get_file_content("csgo_english.txt")

    d = vdf.parse(open("items_game.txt"))

    stickers = parse_stickers(
        get_content_by_pattern(csgo_english, r"StickerKit_(?!.*desc|Default|dh|dz)")
    )

    cases = parse_cases(
        get_content_by_pattern(
            csgo_english,
            (
                r"CSGO_crate_(?!.*_desc|.*tag|.*spray_|.*bundle_|.*radicals_capsule"
                r"|.*pack[0-9+]|.*tinyname|.*key_community|.*_fang|.*_recoil"
                r"|.*surfshop|.*swap|.*pack_op|.*_web|.*_groupname)"
            ),
        )
    )

    agents = parse_agents(
        get_content_by_pattern(
            csgo_english, r"(CSGO_CustomPlayer|CSGO_Customplayer)(?!.*(_Desc|_t_|_ct_))"
        )
    )

    keys = parse_keys(
        get_content_by_pattern(
            csgo_english,
            (
                r"crate_key(?!.*desc|.*Recoil|.*Dreams|.*Fracture|.*Fang|.*Riptide"
                r"|.*Prisma\s2|.*Revolution|.*Shattered|.*Snakebite)"
            ),
        )
    )

    if is_save:
        save_to_file("stickers", stickers)
        save_to_file("cases", cases)
        save_to_file("agents", agents)
        save_to_file("keys", keys)
