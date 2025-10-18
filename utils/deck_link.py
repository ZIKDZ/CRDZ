import urllib.parse

def build_deck_link(deck_cards, player_tag, ALL_CARDS_FULL):
    """Builds and returns a Clash Royale deck link string."""
    player_tag = player_tag.replace("#", "")
    card_ids = []

    for c in deck_cards[:8]:
        name = c.get("name")
        card_info = ALL_CARDS_FULL.get(name)
        if card_info:
            card_ids.append(str(card_info.get("id", 0)))
        else:
            card_ids.append("0")

    deck_str = ";".join(card_ids)
    url = (
        f"https://link.clashroyale.com/en?clashroyale://copyDeck?"
        f"deck={deck_str}"
        f"&slots=0;0;0;0;0;0;0;0"
        f"&tt=159000000"
        f"&l=Royals"
    )
    return url
