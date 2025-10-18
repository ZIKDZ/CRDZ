import aiohttp
import asyncio
import time
import statistics
from config import CR_API_TOKEN  # Import from your bot's config

async def get_player_data(player_tag: str):
    """Fetch player data from Clash Royale API (async)."""
    if not player_tag.startswith("#"):
        player_tag = "#" + player_tag
    encoded_tag = player_tag.replace("#", "%23")
    url = f"https://api.clashroyale.com/v1/players/{encoded_tag}"
    headers = {"Authorization": f"Bearer {CR_API_TOKEN}"}
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        async with session.get(url, headers=headers, timeout=10) as res:
            elapsed = time.time() - start_time
            if res.status == 200:
                return elapsed, await res.json()
            else:
                return elapsed, None

async def get_all_cards_full():
    """Fetch all Clash Royale cards (async)."""
    url = "https://api.clashroyale.com/v1/cards"
    headers = {"Authorization": f"Bearer {CR_API_TOKEN}"}
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        async with session.get(url, headers=headers, timeout=10) as res:
            elapsed = time.time() - start_time
            if res.status == 200:
                data = await res.json()
                items = data.get("items", data)
                return elapsed, items
            else:
                return elapsed, None

async def test_api_response_time(iterations=5, player_tag="#Y9R22RQ2"):
    """Test API response times for player and cards endpoints."""
    print(f"Testing Clash Royale API response times ({iterations} iterations)...")
    
    player_times = []
    cards_times = []
    
    for i in range(iterations):
        print(f"\nIteration {i + 1}/{iterations}")
        
        # Test player data endpoint
        try:
            elapsed, data = await get_player_data(player_tag)
            player_times.append(elapsed)
            status = "Success" if data else f"Failed (Status: {res.status})"
            print(f"Player Data ({player_tag}): {elapsed:.3f} seconds - {status}")
        except Exception as e:
            print(f"Player Data ({player_tag}): Error - {e}")
            player_times.append(float("inf"))
        
        # Test cards endpoint
        try:
            elapsed, data = await get_all_cards_full()
            cards_times.append(elapsed)
            status = "Success" if data else f"Failed (Status: {res.status})"
            print(f"All Cards: {elapsed:.3f} seconds - {status}")
        except Exception as e:
            print(f"All Cards: Error - {e}")
            cards_times.append(float("inf"))
        
        await asyncio.sleep(0.5)  # Avoid rate limiting
    
    # Calculate statistics
    def print_stats(times, name):
        valid_times = [t for t in times if t != float("inf")]
        if valid_times:
            avg = statistics.mean(valid_times)
            min_time = min(valid_times)
            max_time = max(valid_times)
            print(f"\n{name} Stats:")
            print(f"  Average: {avg:.3f} seconds")
            print(f"  Min: {min_time:.3f} seconds")
            print(f"  Max: {max_time:.3f} seconds")
            print(f"  Success Rate: {len(valid_times)/iterations*100:.1f}%")
        else:
            print(f"\n{name} Stats: All requests failed")
    
    print_stats(player_times, "Player Data")
    print_stats(cards_times, "All Cards")

if __name__ == "__main__":
    asyncio.run(test_api_response_time(iterations=5, player_tag="#Y9R22RQ2"))