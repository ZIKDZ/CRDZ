import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import config
from .clash_api import get_all_cards_full  # async now


async def generate_deck_image(deck_cards, player_level):
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
