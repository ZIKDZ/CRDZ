# utils/clash_api.py
import aiohttp
import asyncio
import config
import time
from datetime import datetime
from urllib.parse import quote

# Cache for cards to avoid repeated API calls
_card_cache = None
_card_cache_lock = asyncio.Lock()

# Proxy management
formatted_proxies = []  # List of working proxies, fastest first
proxies_lock = asyncio.Lock()
monitor_task = None

# Convert proxy string to aiohttp format
def format_proxy(p):
    ip, port, user, password = p.split(":")
    return f"http://{user}:{password}@{ip}:{port}"

# Synchronous load proxies
def _sync_load_proxies(filename="proxies.txt"):
    try:
        with open(filename, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[WARNING] proxies.txt not found. Running without proxies.")
        return []

# Async load proxies to avoid blocking
async def load_proxies(filename="proxies.txt"):
    return await asyncio.to_thread(_sync_load_proxies, filename)

async def test_proxy(session, proxy, api_key, player_tag="#VL9P90GCL"):
    """Test a single proxy and return (proxy, response_time) or None"""
    encoded_tag = quote(player_tag)
    CR_API = f"https://api.clashroyale.com/v1/players/{encoded_tag}"
    headers = {"Authorization": f"Bearer {api_key}", "User-Agent": "ClashBot/1.0"}

    try:
        start = time.perf_counter()
        async with session.get(CR_API, headers=headers, proxy=proxy, timeout=8) as resp:
            elapsed = time.perf_counter() - start
            if resp.status in (200, 404):
                print(f"[OK] Proxy {proxy} | {elapsed:.2f}s")
                return proxy, elapsed
            else:
                print(f"[FAILED] Proxy {proxy} | Status: {resp.status}")
                return None
    except Exception as e:
        print(f"[ERROR] Proxy {proxy} | {str(e)[:50]}")
        return None

async def monitor_proxies(api_key, player_tag="#VL9P90GCL", interval=600):  # 10 minutes
    """Background task: Test proxies every 10 minutes"""
    print("[PROXY] Starting proxy monitor (every 10 minutes)")
    
    while True:
        try:
            # Load and test proxies
            proxies = await load_proxies("proxies.txt")
            if not proxies:
                print("[PROXY] No proxies found in proxies.txt")
                await asyncio.sleep(interval)
                continue
                
            formatted = [format_proxy(p) for p in proxies]
            working_results = []
            
            async with aiohttp.ClientSession() as session:
                # Test all proxies sequentially
                for proxy in formatted:
                    result = await test_proxy(session, proxy, api_key, player_tag)
                    if result:
                        working_results.append(result)
                        await asyncio.sleep(0.1)  # Small delay between tests
            
            # Update global proxy list
            if working_results:
                working_results.sort(key=lambda x: x[1])  # Sort by response time
                new_proxies = [r[0] for r in working_results]
                async with proxies_lock:
                    formatted_proxies[:] = new_proxies
                print(f"[PROXY] Updated: {len(new_proxies)} working proxies. Fastest: {working_results[0][1]:.2f}s")
            else:
                async with proxies_lock:
                    formatted_proxies.clear()
                print("[PROXY] No working proxies found!")
                
        except Exception as e:
            print(f"[PROXY] Monitor error: {e}")
        
        await asyncio.sleep(interval)

async def start_proxy_monitor():
    """Start the proxy monitoring task once at bot startup"""
    global monitor_task
    if monitor_task is None or monitor_task.done():
        monitor_task = asyncio.create_task(monitor_proxies(config.CR_API_TOKEN))
        # Initial test (faster interval for startup)
        await asyncio.sleep(1)  # Let it start
        print("[PROXY] Initial proxy test completed")

async def make_api_request(url, headers, timeout=10):
    """Make API request with proxy fallback"""
    async with proxies_lock:
        proxy_list = formatted_proxies[:]  # Copy current proxy list
    
    async with aiohttp.ClientSession() as session:
        # Try each proxy in order
        for proxy in proxy_list:
            try:
                print(f"[API] Trying proxy: {proxy}")
                async with session.get(url, headers=headers, proxy=proxy, timeout=timeout) as res:
                    if res.status == 200:
                        print(f"[API] Success with proxy: {proxy}")
                        return await res.json()
                    else:
                        print(f"[API] Proxy {proxy} returned status: {res.status}")
            except Exception as e:
                print(f"[API] Proxy {proxy} failed: {str(e)[:50]}")
                continue
        
        # Fallback: no proxy
        try:
            print("[API] Trying without proxy (fallback)")
            async with session.get(url, headers=headers, timeout=timeout) as res:
                if res.status == 200:
                    print("[API] Success without proxy")
                    return await res.json()
        except Exception as e:
            print(f"[API] Fallback failed: {e}")
        
        return None

async def get_player_data(player_tag: str):
    """Fetch player data from the Clash Royale API (async)."""
    if not player_tag.startswith("#"):
        player_tag = "#" + player_tag
    encoded_tag = player_tag.replace("#", "%23")
    url = f"https://api.clashroyale.com/v1/players/{encoded_tag}"
    headers = {
        "Authorization": f"Bearer {config.CR_API_TOKEN}", 
        "User-Agent": "ClashBot/1.0"
    }
    return await make_api_request(url, headers, timeout=10)

async def get_all_cards_full(force_refresh: bool = False):
    """Fetch and cache all Clash Royale cards by name (async)."""
    global _card_cache
    
    async with _card_cache_lock:
        # Return from cache unless forced refresh
        if _card_cache is not None and not force_refresh:
            return _card_cache
        
        url = "https://api.clashroyale.com/v1/cards"
        headers = {
            "Authorization": f"Bearer {config.CR_API_TOKEN}", 
            "User-Agent": "ClashBot/1.0"
        }
        
        data = await make_api_request(url, headers, timeout=15)
        if data:
            items = data.get("items", data)
            _card_cache = {c["name"]: c for c in items}
            print(f"[CARDS] Cached {len(_card_cache)} cards")
        else:
            print("[CARDS] Failed to fetch cards")
        
        return _card_cache or {}

async def initialize_proxies():
    """Initialize proxy system at bot startup"""
    await start_proxy_monitor()

def get_real_trophies(data: dict) -> int:
    """
    Returns the player's actual current trophies.
    If 'trophies' == 10000, looks recursively for the seasonal-trophy-road-YYYYMM
    and returns its 'trophies' value.
    """
    trophies = data.get("trophies", 0)
    now = datetime.utcnow()
    dynamic_key = f"seasonal-trophy-road-{now.year}{now.month:02d}"

    def find_key_recursively(obj):
        """Search for the seasonal key anywhere in the data."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == dynamic_key and isinstance(v, dict):
                    return v
                found = find_key_recursively(v)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = find_key_recursively(item)
                if found is not None:
                    return found
        return None

    if trophies == 10000:
        seasonal_data = find_key_recursively(data)
        if seasonal_data:
            seasonal_trophies = seasonal_data.get("trophies")
            if seasonal_trophies is not None:
                return seasonal_trophies

    return trophies


