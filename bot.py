import discord
from discord.ext import commands
from utils.clash_api import get_all_cards_full
import config
import asyncio

# Discord intents setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load cogs
async def load_cogs():
    for cog in ["cogs.player", "cogs.deck", "cogs.emote", "cogs.admin"]:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load cog {cog}: {e}")

@bot.event
async def on_ready():
    """Handle bot startup and set status."""
    print(f"✅ Logged in as {bot.user}")

    await get_all_cards_full()

    activity = discord.Game(name="🏆 Clash Royale")
    await bot.change_presence(status=discord.Status.online, activity=activity)


    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# Bot startup
if __name__ == "__main__":
    asyncio.run(load_cogs())
    bot.run(config.DISCORD_TOKEN)