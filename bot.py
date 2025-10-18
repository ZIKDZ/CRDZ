import discord
from discord.ext import commands
from utils.clash_api import get_all_cards_full
import config
import asyncio
import requests

# ------------------- DISCORD SETUP -------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------- LOAD COGS -------------------
async def load_cogs():
    for cog in ["cogs.player", "cogs.deck", "cogs.emote", "cogs.admin"]:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load cog {cog}: {e}")

# ------------------- BOT READY EVENT -------------------
@bot.event
async def on_ready():
    """Handle bot startup and set status."""
    print(f"\n✅ Logged in as {bot.user} (ID: {bot.user.id})")

    # Fetch and print host public IP
    try:
        ip = requests.get("https://api.ipify.org").text
        print(f"🌍 Public IP Address: {ip}")
    except Exception as e:
        print(f"⚠️ Could not fetch public IP: {e}")

    # Preload Clash Royale data
    await get_all_cards_full()

    # Set bot status
    activity = discord.Game(name="🏆 Clash Royale")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# ------------------- MAIN -------------------
if __name__ == "__main__":
    asyncio.run(load_cogs())
    bot.run(config.DISCORD_TOKEN)
