import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import urllib.parse
import config
from .clash_api import get_all_cards_full  # async function

# ============================================================
#  Deck Image Generator (in case of a fallback)
# ============================================================

async def fallback_deck_image(deck_cards, player_level):
    """Generate a 4x2 deck image with card icons and average elixir (rarity-based levels)."""
    # Layout constants
    card_w, card_h = 200, 300
    padding = 18
    cols, rows = 4, 2
    bg_width = cols * card_w + (cols + 1) * padding
    bg_height = rows * card_h + (rows + 1) * padding + 70

    # Colors (Clash Royale theme)
    bg_color = (13, 37, 69)
    panel_color = (21, 115, 190)
    offwhite = (245, 245, 245)

    img = Image.new("RGBA", (bg_width, bg_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Font setup
    try:
        font_small = ImageFont.truetype(config.FONT_PATH, 18)
        font_big = ImageFont.truetype(config.FONT_PATH, 28)
    except Exception:
        font_small = ImageFont.load_default()
        font_big = ImageFont.load_default()
        font_path = None
    else:
        font_path = config.FONT_PATH

    def fit_text_to_width(draw, text, max_width, font_path, start_size=22):
        """Dynamically adjust font size to fit text within width."""
        if not font_path:
            return ImageFont.load_default()
        size = start_size
        while size > 10:
            f = ImageFont.truetype(font_path, size)
            bbox = draw.textbbox((0, 0), text, font=f)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                return f
            size -= 1
        return ImageFont.truetype(font_path, 10)

    # Header
    header_h = 58
    draw.rounded_rectangle([(10, 10), (bg_width - 10, 10 + header_h)], radius=12, fill=panel_color)
    draw.text((20, 18), "Battle Deck", font=font_big, fill=offwhite)

    # Card slots
    card_positions = []
    start_x = padding
    start_y = padding + header_h
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * (card_w + padding)
            y = start_y + r * (card_h + padding)
            draw.rounded_rectangle([(x, y), (x + card_w, y + card_h)], radius=12, fill=(30, 30, 30))
            card_positions.append((x, y, x + card_w, y + card_h))

    # Evolution rules and elixir tracking
    evo_limit = 1 if player_level < 30 else 2
    elixir_vals = []

    # Fetch global card info once
    ALL_CARDS_FULL = await get_all_cards_full()

    async with aiohttp.ClientSession() as session:
        for idx in range(min(len(deck_cards), cols * rows)):
            card = deck_cards[idx]
            name = card.get("name", "Unknown")
            icons = card.get("iconUrls", {}) or {}
            url = None

            # Evolution logic
            if idx < evo_limit and card.get("evolutionLevel", 0) >= 1:
                url = icons.get("evolutionMedium") or icons.get("medium")
            else:
                url = icons.get("medium")

            # Fallback to global card data
            card_info = ALL_CARDS_FULL.get(name)
            if not url and card_info:
                icon_urls = card_info.get("iconUrls", {}) or {}
                if idx < evo_limit and card.get("evolutionLevel", 0) >= 1:
                    url = icon_urls.get("evolutionMedium")
                if not url:
                    url = icon_urls.get("medium")

            # Elixir tracking
            elixir = (
                card.get("elixirCost")
                or card.get("elixir")
                or (card_info.get("elixirCost") if card_info else None)
                or (card_info.get("elixir") if card_info else None)
            )
            if elixir is not None:
                try:
                    elixir_vals.append(float(elixir))
                except Exception:
                    pass

            x1, y1, x2, y2 = card_positions[idx]
            if not url:
                draw.text((x1 + 10, y1 + 10), name[:20], font=font_small, fill=offwhite)
                continue

            try:
                async with session.get(url, timeout=10) as r:
                    if r.status == 200:
                        img_bytes = await r.read()
                        card_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                        card_img.thumbnail((card_w - 24, card_h - 60), Image.LANCZOS)
                        paste_x = x1 + (card_w - card_img.width) // 2
                        paste_y = y1 + 18
                        img.paste(card_img, (paste_x, paste_y), card_img)

                        # Rarity-based real level
                        level = card.get("level") or card.get("currentLevel") or 0
                        rarity = (card.get("rarity") or (card_info.get("rarity") if card_info else "")).lower()
                        if rarity == "rare":
                            real_level = 2 + int(level)
                        elif rarity == "epic":
                            real_level = 5 + int(level)
                        elif rarity == "legendary":
                            real_level = 8 + int(level)
                        elif rarity == "champion":
                            real_level = 10 + int(level)
                        else:
                            real_level = int(level)

                        nm = f"Level {real_level}"
                        font_dynamic = fit_text_to_width(draw, nm, card_w - 24, font_path, start_size=20)
                        text_bbox = draw.textbbox((0, 0), nm, font=font_dynamic)
                        text_w = text_bbox[2] - text_bbox[0]
                        text_x = x1 + (card_w - text_w) // 2
                        text_y = paste_y + card_img.height + 2
                        draw.text((text_x, text_y), nm, font=font_dynamic, fill=offwhite)

            except Exception as e:
                print(f"[DeckGen] Error loading card {name}: {e}")
                draw.text((x1 + 10, y1 + 10), name[:20], font=font_small, fill=offwhite)

    # Average elixir
    if elixir_vals:
        avg_elixir = round(sum(elixir_vals) / len(elixir_vals), 1)
        avg_text = f"Avg Elixir: {avg_elixir}"
    else:
        avg_text = "Avg Elixir: N/A"

    bbox = draw.textbbox((0, 0), avg_text, font=font_small)
    w = bbox[2] - bbox[0]
    draw.text((bg_width - w - 20, 20), avg_text, font=font_small, fill=offwhite)

    # Save to buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ============================================================
#  Deck Image Generator
# ============================================================

async def generate_deck_image(deck_cards, player_level):
    """Generate a deck image using official background, fallback if needed."""
    try:
        # Load background
        bg_path = "assets/Deck_Background.png"
        bg = Image.open(bg_path).convert("RGBA")
        img = bg.copy()
        draw = ImageDraw.Draw(img)
        bg_width, bg_height = img.size

        # Fonts
        try:
            font_small = ImageFont.truetype(config.FONT_PATH, 28)
            font_big = ImageFont.truetype(config.FONT_PATH, 40)
        except Exception:
            font_small = ImageFont.load_default()
            font_big = ImageFont.load_default()

        # Card coordinates + sizes
        card_positions = [
            (36, 187, 223, 323),
            (294, 187, 223, 323),
            (552, 223, 230, 347),
            (817, 223, 230, 347),
            (33, 648, 230, 347),
            (294, 648, 230, 347),
            (555, 648, 230, 347),
            (816, 648, 230, 347)
        ]

        evo_limit = 1 if player_level < 30 else 2
        elixir_vals = []
        ALL_CARDS_FULL = await get_all_cards_full()

        # Helper
        def pick_best_icon(icon_dict, prefer_evo=False):
            if not icon_dict:
                return None
            order = []
            if prefer_evo:
                order += ["evolutionLarge", "evolutionMedium", "evolutionSmall"]
            order += ["large", "medium", "small", "icon", "thumbnail"]
            for k in order:
                if k in icon_dict and icon_dict[k]:
                    return icon_dict[k]
            for v in icon_dict.values():
                if v:
                    return v
            return None

        async with aiohttp.ClientSession() as session:
            for idx, (x, y, w, h) in enumerate(card_positions):
                if idx >= len(deck_cards):
                    break
                card = deck_cards[idx]
                name = card.get("name", "Unknown")
                icons = card.get("iconUrls", {}) or {}
                card_info = ALL_CARDS_FULL.get(name) or {}
                has_evo = card.get("evolutionLevel", 0) >= 1

                if idx in (0, 1) and not has_evo:
                    if idx == 0:
                        x, y, w, h = 36, 187, 223, 279
                    else:
                        x, y, w, h = 294, 231, 223, 279

                prefer_evo = (idx < evo_limit and has_evo)
                url = pick_best_icon(icons, prefer_evo=prefer_evo)
                if not url:
                    url = pick_best_icon(card_info.get("iconUrls", {}) or {}, prefer_evo=prefer_evo)

                elixir = (
                    card.get("elixirCost")
                    or card.get("elixir")
                    or (card_info.get("elixirCost") if card_info else None)
                    or (card_info.get("elixir") if card_info else None)
                )
                if elixir is not None:
                    try:
                        elixir_vals.append(float(elixir))
                    except Exception:
                        pass

                if not url:
                    draw.text((x + 10, y + 10), name[:20], font=font_small, fill=(255, 255, 255))
                    continue

                try:
                    async with session.get(url, timeout=15) as r:
                        if r.status != 200:
                            raise RuntimeError(f"HTTP {r.status}")
                        img_bytes = await r.read()
                        card_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                        try:
                            alpha = card_img.split()[-1]
                            bbox = alpha.getbbox()
                        except Exception:
                            bbox = card_img.getbbox()
                        if bbox:
                            card_img = card_img.crop(bbox)
                        card_img = card_img.resize((w, h), Image.LANCZOS)
                        img.paste(card_img, (x, y), card_img)

                        # Card level
                        level = card.get("level") or card.get("currentLevel") or 0
                        rarity = (card.get("rarity") or (card_info.get("rarity") if card_info else "")).lower()
                        if rarity == "rare":
                            real_level = 2 + int(level)
                        elif rarity == "epic":
                            real_level = 5 + int(level)
                        elif rarity == "legendary":
                            real_level = 8 + int(level)
                        elif rarity == "champion":
                            real_level = 10 + int(level)
                        else:
                            real_level = int(level)

                        lvl_text = f"Lvl {real_level}"
                        text_w = draw.textlength(lvl_text, font=font_small)
                        lvl_y = y + h + 8 if idx in (0, 1) else y + h - 64
                        draw.text((x + (w - text_w) // 2, lvl_y), lvl_text, font=font_small, fill=(255, 255, 255))

                except Exception as e:
                    print(f"[DeckGen] Error loading/pasting card {name}: {e}")
                    # fallback on this card
                    buf = await fallback_deck_image(deck_cards, player_level)
                    return buf

        # Average elixir
        avg_text = f"{round(sum(elixir_vals) / len(elixir_vals), 1)}" if elixir_vals else "N/A"
        draw.text((150, bg_height - 115), avg_text, font=font_big, fill=(255, 255, 255))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

    except Exception as e:
        print(f"[DeckGen] Main generator failed, using fallback: {e}")
        return await fallback_deck_image(deck_cards, player_level)


# ============================================================
#  Deck Link Builder
# ============================================================

def build_deck_link(deck_cards, player_tag, ALL_CARDS_FULL, support_cards=None):
    """
    Builds and returns a Clash Royale deck link string.

    - deck_cards: list of card dicts (currentDeck)
    - player_tag: string (can include leading '#')
    - ALL_CARDS_FULL: dict mapping card name -> card info (including 'id')
    - support_cards: optional list (currentDeckSupportCards)
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
        if isinstance(first_support, dict) and first_support.get("id"):
            support_id = str(first_support.get("id"))
        else:
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
