import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import random
import io
import re
import config

EMOTE_CACHE = []

async def get_random_emote_image_url(width=None, height=None):
    """
    Much faster version — caches emote URLs after the first call.
    Later calls just pick from cache.
    """
    global EMOTE_CACHE

    # ✅ use cached emotes if already fetched
    if EMOTE_CACHE:
        chosen_url = random.choice(EMOTE_CACHE)
    else:
        url = "https://clashroyale.fandom.com/wiki/Category:Emote_Files"
        headers = {"User-Agent": "Mozilla/5.0"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        images = soup.select("div.category-page__member-left img")
        EMOTE_CACHE = [img.get('data-src', img.get('src')) for img in images if img.get('src')]

        if not EMOTE_CACHE:
            return None

        chosen_url = random.choice(EMOTE_CACHE)

    # ✅ Adjust width and height quickly (no regex if unnecessary)
    if width and height and "/smart/width/" in chosen_url:
        chosen_url = re.sub(
            r"/smart/width/\d+/height/\d+",
            f"/smart/width/{width}/height/{height}",
            chosen_url
        )
    else:
        chosen_url = re.sub(r"/revision/.*", "", chosen_url)

    return chosen_url

class Emote(commands.Cog):
    """Cog for emote-related commands."""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="emote",
        description="Send a random Clash Royale emote!"
    )
    async def emote(self, interaction: discord.Interaction):
        """Fetch and send a random Clash Royale emote as an image."""
        await interaction.response.defer()

        try:
            img_url = await get_random_emote_image_url(240, 180)
            if not img_url:
                await interaction.followup.send(f"{config.EMOJI_SAD} Could not find an emote right now. Try again later.")
                return

            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url, timeout=10) as resp:
                    image_data = io.BytesIO(await resp.read())

            # Prepare the image for Discord
            file = discord.File(image_data, filename="emote.png")

            # Build the embed
            embed = discord.Embed(
                title="🎭 Random Clash Royale Emote",
                color=discord.Color.gold()
            )
            embed.set_image(url="attachment://emote.png")

            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            await interaction.followup.send(f"{config.EMOJI_SAD} Error fetching emote: `{str(e)[:1900]}`")

async def setup(bot):
    await bot.add_cog(Emote(bot))