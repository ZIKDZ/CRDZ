# cogs/admin.py
import discord
from discord import app_commands
from discord.ext import commands
from utils.clash_api import get_all_cards_full, formatted_proxies, proxies_lock

class Admin(commands.Cog):
    """Cog for admin-related commands."""

    def __init__(self, bot):
        self.bot = bot

    # ------------------- CHECK API (ADMIN ONLY) -------------------
    @app_commands.command(
        name="check-api",
        description="Check if the Clash Royale API connection is working. (Admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def check_api(self, interaction: discord.Interaction):
        """Test the Clash Royale API connection with proxy status."""
        await interaction.response.defer(ephemeral=True)

        try:
            # Get current proxy status
            async with proxies_lock:
                proxy_count = len(formatted_proxies)
                fastest_proxy = formatted_proxies[0] if formatted_proxies else "None"
            
            # Test API with proxy system
            cards_data = await get_all_cards_full(force_refresh=True)
            
            if cards_data:
                card_count = len(cards_data)
                status = "🟢 **API + PROXIES: WORKING PERFECTLY!** 🟢"
                
                if proxy_count > 0:
                    clean_proxy = fastest_proxy.split('@')[1] if '@' in fastest_proxy else fastest_proxy
                    proxy_info = f"**Fastest**: `{clean_proxy}`\n"
                    proxy_info += f"**Total**: {proxy_count} working (fastest-first)"
                else:
                    proxy_info = "**⚠️ No working proxies** (direct connection)"
                
                embed = discord.Embed(title="🔍 API Connection Test", description=status, color=0x00ff00)
                embed.add_field(name="📊 Cards Fetched", value=f"{card_count} cards", inline=True)
                embed.add_field(name="🔗 Proxy Status", value=proxy_info, inline=False)
                embed.set_footer(text=f"Checked by: {interaction.user.display_name}")
            else:
                status = "🔴 **API FAILED** 🔴"
                embed = discord.Embed(title="🔍 API Connection Test", description=status, color=0xff0000)
                embed.add_field(name="📊 Cards Fetched", value="0 cards", inline=True)
                embed.add_field(name="🔗 Proxy Status", 
                              value=f"**{proxy_count} proxies** - all failed or unavailable", 
                              inline=False)
                embed.set_footer(text="Check API token & proxies.txt")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ API Test Failed",
                description=f"**Error**: `{str(e)[:100]}...`",
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)

    # ------------------- PROXY STATUS (ADMIN ONLY) -------------------
    @app_commands.command(
        name="proxy-status",
        description="Show current proxy status and performance. (Admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def proxy_status(self, interaction: discord.Interaction):
        """Show detailed proxy status."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            async with proxies_lock:
                proxy_count = len(formatted_proxies)
                
            if proxy_count == 0:
                embed = discord.Embed(
                    title="🔌 Proxy Status",
                    description="**❌ No working proxies!**\n\n• Check `proxies.txt` file\n• Verify credentials\n• Wait for next test (~10min)",
                    color=0xffaa00
                )
            else:
                top_proxies = []
                async with proxies_lock:
                    for i, proxy in enumerate(formatted_proxies[:3]):
                        clean_proxy = proxy.split('@')[1] if '@' in proxy else proxy
                        top_proxies.append(f"`{i+1}. {clean_proxy}`")
                
                embed = discord.Embed(
                    title="🔌 Proxy Status",
                    description=f"**🟢 {proxy_count} WORKING PROXIES** (fastest-first)",
                    color=0x00ff00
                )
                embed.add_field(name="🏆 Top 3 Fastest", value="\n".join(top_proxies) or "None", inline=False)
                embed.add_field(name="⏰ Next Test", value="**Every 10 minutes** (background)", inline=True)
                embed.add_field(name="🔄 Last Update", value="**Startup + every 10min**", inline=True)
                embed.set_footer(text=f"Checked by: {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Proxy status error: `{str(e)}`")

    # ------------------- FIXED ERROR HANDLER -------------------
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle app command errors (NOT cog_command_error!)."""
        # Handle MissingPermissions from @app_commands.checks.has_permissions()
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 **Access Denied**",
                description="**You don't have permission to use this command.**\n\n**Required:** `Administrator` permission",
                color=0xff0000
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            return  # STOP ERROR PROPAGATION
        
        # Handle other AppCommandErrors
        if isinstance(error, app_commands.AppCommandError):
            embed = discord.Embed(
                title="❌ **Command Error**",
                description=f"`{str(error)}`",
                color=0xff0000
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            return  # STOP ERROR PROPAGATION

async def setup(bot):
    await bot.add_cog(Admin(bot))