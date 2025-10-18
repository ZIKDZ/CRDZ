import discord
from discord import app_commands
from discord.ext import commands
import requests
import config

class Admin(commands.Cog):
    """Cog for admin-related commands."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="check-api",
        description="Check if the Clash Royale API connection is working."
    )
    async def check_api(self, interaction: discord.Interaction):
        """Test the Clash Royale API connection."""
        await interaction.response.defer(ephemeral=True)

        test_url = "https://api.clashroyale.com/v1/cards"
        headers = {"Authorization": f"Bearer {config.CR_API_TOKEN}"}

        try:
            res = requests.get(test_url, headers=headers, timeout=8)
            if res.status_code == 200:
                items = res.json().get("items", [])
                await interaction.followup.send(f"{config.EMOJI_COOL} API connected successfully!")
            elif res.status_code == 403:
                await interaction.followup.send("❌ Invalid or expired API token (403 Forbidden).")
            elif res.status_code == 401:
                await interaction.followup.send("❌ Unauthorized – your CR_API_TOKEN might be wrong.")
            else:
                await interaction.followup.send(f"⚠️ Unexpected API response: {res.status_code}")
        except requests.exceptions.Timeout:
            await interaction.followup.send("⏰ API request timed out.")
        except Exception as e:
            await interaction.followup.send(f"❌ Error checking API connection: {e}")

async def setup(bot):
    await bot.add_cog(Admin(bot))