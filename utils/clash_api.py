# utils/clash_api.py
import aiohttp
import asyncio
import config

# Cache for cards to avoid repeated API calls
_card_cache = None
_card_cache_lock = asyncio.Lock()

async def get_player_data(player_tag: str):
    """Fetch player data from the Clash Royale API (async)."""
    if not player_tag.startswith("#"):
        player_tag = "#" + player_tag
    encoded_tag = player_tag.replace("#", "%23")
    url = f"https://api.clashroyale.com/v1/players/{encoded_tag}"
    headers = {"Authorization": f"Bearer {config.CR_API_TOKEN}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=10) as res:
            if res.status == 200:
                return await res.json()
            return None


async def get_all_cards_full(force_refresh: bool = False):
    """Fetch and cache all Clash Royale cards by name (async)."""
    global _card_cache

    async with _card_cache_lock:
        # Return from cache unless forced refresh
        if _card_cache is not None and not force_refresh:
            return _card_cache

        url = "https://api.clashroyale.com/v1/cards"
        headers = {"Authorization": f"Bearer {config.CR_API_TOKEN}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as res:
                if res.status == 200:
                    data = await res.json()
                    items = data.get("items", data)
                    _card_cache = {c["name"]: c for c in items}
                    return _card_cache

        # fallback
        return _card_cache or {}
