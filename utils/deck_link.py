import urllib.parse

def build_deck_link(deck_cards, player_tag, ALL_CARDS_FULL, support_cards=None):
    """
    Builds and returns a Clash Royale deck link string.

    - deck_cards: list of card dicts (currentDeck)
    - player_tag: string (can include leading '#')
    - ALL_CARDS_FULL: dict mapping card name -> card info (including 'id')
    - support_cards: optional list (currentDeckSupportCards) each item is a dict
    """
    player_tag = player_tag.replace("#", "")
    card_ids = []

    # main deck (first 8)
    for c in deck_cards[:8]:
        name = c.get("name")
        card_info = ALL_CARDS_FULL.get(name)
        if card_info:
            card_ids.append(str(card_info.get("id", 0)))
        else:
            card_ids.append("0")

    # default support id (keeps old behavior if none found)
    support_id = "159000000"

    # If support_cards provided, attempt to resolve first support card id
    if support_cards and isinstance(support_cards, (list, tuple)) and len(support_cards) > 0:
        first_support = support_cards[0]
        # If support entry already contains an 'id', prefer that.
        if isinstance(first_support, dict) and first_support.get("id"):
            support_id = str(first_support.get("id"))
        else:
            # otherwise try to resolve by name via ALL_CARDS_FULL
            support_name = None
            if isinstance(first_support, dict):
                support_name = first_support.get("name")
            elif isinstance(first_support, str):
                support_name = first_support

            if support_name:
                support_info = ALL_CARDS_FULL.get(support_name)
                if support_info and support_info.get("id"):
                    support_id = str(support_info.get("id"))

    deck_str = ";".join(card_ids)

    url = (
        f"https://link.clashroyale.com/en?clashroyale://copyDeck?"
        f"deck={deck_str}"
        f"&slots=0;0;0;0;0;0;0;0"
        f"&tt={support_id}"
        f"&l=Royals"
    )
    return url
