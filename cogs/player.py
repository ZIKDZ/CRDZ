import discord
from discord import app_commands
from discord.ext import commands
import config
from utils.clash_api import get_player_data, get_all_cards_full
from utils.data_store import load_data, save_data
from utils.deck_utils import generate_deck_image
from PIL import Image, ImageDraw, ImageFont
import asyncio
import io

class Player(commands.Cog):
    """Cog for player profile commands."""

    def __init__(self, bot):
        self.bot = bot

    # ------------------- PROFILE LINK -------------------
    @app_commands.command(
        name="profile-link",
        description="(Admins only) Link a Clash Royale profile to a Discord user and save their tag."
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        user="The Discord user to link the profile to",
        tag="The Clash Royale player tag (e.g. #Y9R22RQ2)"
    )
    async def profile_setup(self, interaction: discord.Interaction, user: discord.Member, tag: str):
        await interaction.response.defer(ephemeral=True)

        data = await get_player_data(tag)
        if data is None:
            await interaction.followup.send(f"{config.EMOJI_SAD} Couldn't find that player tag. Please check and try again.")
            return

        cr_name = data.get("name")
        trophies = data.get("trophies", 0)

        msg = f"{config.EMOJI_LAUGH} Linked **{cr_name}** to {user.mention}!\n{config.EMOJI_TROPHY} Trophies: {trophies}"

        # Role logic
        guild = interaction.guild
        role_under = guild.get_role(config.ROLE_UNDER_5K)
        role_above5 = guild.get_role(config.ROLE_ABOVE_5K)
        role_above10 = guild.get_role(config.ROLE_ABOVE_10K)

        if trophies >= 10000:
            target_role = role_above10
        elif trophies >= 5000:
            target_role = role_above5
        else:
            target_role = role_under

        current_roles = {r.id for r in user.roles}
        roles_to_remove = [
            r for r in [role_under, role_above5, role_above10]
            if r and r.id in current_roles and r != target_role
        ]

        if roles_to_remove:
            try:
                await user.remove_roles(*roles_to_remove)
                await asyncio.sleep(0.5)
            except Exception:
                pass

        if target_role and target_role.id not in current_roles:
            try:
                await user.add_roles(target_role)
                msg += f"\n{config.EMOJI_TROPHY} Added role: {target_role.name}"
            except Exception:
                msg += "\n⚠️ Failed to assign the role."

        # Save tag
        saved_data = load_data()
        saved_data[str(user.id)] = {"tag": tag}
        save_data(saved_data)
        msg += "\n✅ Player tag saved successfully."
        await interaction.followup.send(msg)

    # ------------------- PROFILE UNLINK -------------------
    @app_commands.command(
        name="profile-unlink",
        description="(Mods only) Unlink a Clash Royale profile from a Discord user."
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        user="The Discord user to unlink the profile from"
    )
    async def profile_unlink(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)

        saved_data = load_data()
        user_id = str(user.id)
        if user_id not in saved_data:
            await interaction.followup.send(f"{config.EMOJI_SAD} {user.mention} has no linked profile.")
            return

        # Remove roles
        guild = interaction.guild
        for role_id in [config.ROLE_UNDER_5K, config.ROLE_ABOVE_5K, config.ROLE_ABOVE_10K]:
            role = guild.get_role(role_id)
            if role and role in user.roles:
                try:
                    await user.remove_roles(role)
                except Exception:
                    pass

        # Remove from saved data
        del saved_data[user_id]
        save_data(saved_data)
        await interaction.followup.send(f"{config.EMOJI_LAUGH} Unlinked Clash Royale profile for {user.mention}.")    

    # ------------------- PLAYER PROFILE -------------------
    @app_commands.command(
        name="player",
        description="View Clash Royale data of a linked Discord user."
    )
    @app_commands.describe(user="The Discord user whose Clash Royale data you want to view")
    async def player(self, interaction: discord.Interaction, user: discord.Member):
        # ... existing player command code stays THE SAME ...
        await interaction.response.defer(ephemeral=False)

        saved_data = load_data()
        user_id = str(user.id)
        if user_id not in saved_data:
            await interaction.followup.send(f"{config.EMOJI_SAD} {user.mention} has not been linked yet!")
            return

        tag = saved_data[user_id]["tag"]
        data = await get_player_data(tag)
        if data is None:
            await interaction.followup.send(f"{config.EMOJI_SAD} Could not fetch data for {user.mention}. Try again later.")
            return

        # Extract basic info
        name = data.get("name", "Unknown")
        exp = data.get("expLevel", "N/A")
        trophies = data.get("trophies", "N/A")
        arena = data.get("arena", {}).get("name", "Unknown Arena")
        clan = data.get("clan", {}).get("name", "No Clan")
        fav_card = data.get("currentFavouriteCard", {}).get("name", "Unknown")
        current_deck = data.get("currentDeck", [])
        deck_cards = current_deck[:8]
        support_cards = data.get("currentDeckSupportCards", [])
        tower_troop_name = support_cards[0].get("name") if support_cards else "None"

        # Fetch card database once
        ALL_CARDS_FULL = await get_all_cards_full()

        # Compute average elixir
        card_names, elixir_vals = [], []
        for c in deck_cards:
            nm = c.get("name")
            if nm:
                card_names.append(nm)
                card_info = ALL_CARDS_FULL.get(nm)
                elx = card_info.get("elixir") or card_info.get("elixirCost") if card_info else c.get("elixirCost")
                if elx:
                    try:
                        elixir_vals.append(float(elx))
                    except Exception:
                        pass

        avg_elixir = round(sum(elixir_vals) / len(elixir_vals), 1) if elixir_vals else "N/A"
        deck_text = ", ".join(card_names[:8]) if card_names else "No current deck found."

        # Embed
        embed = discord.Embed(
            title=f"{config.EMOJI_TROPHY} Clash Royale Profile",
            description=f"**{user.display_name}**'s Linked Account — {name}",
            color=0xE6B72D
        )
        embed.add_field(name="👤 Name", value=name, inline=True)
        embed.add_field(name="⭐ EXP Level", value=str(exp), inline=True)
        embed.add_field(name="🏆 Trophies", value=str(trophies), inline=True)
        embed.add_field(name="⚔️ Arena", value=arena, inline=True)
        embed.add_field(name="👥 Clan", value=clan, inline=True)
        embed.add_field(name="🗼 Tower", value=tower_troop_name, inline=True)
        embed.add_field(name="📋 Current Deck", value=deck_text, inline=False)
        embed.set_footer(text=f"Player Tag: {tag} • Avg Elixir: {avg_elixir}")
        
        # Support card thumbnail
        if support_cards and len(support_cards) > 0:
            support_card = support_cards[0]
            icon_url = support_card.get("iconUrls", {}).get("medium")
            if icon_url:
                embed.set_thumbnail(url=icon_url)
        
        # Generate deck image
        while len(deck_cards) < 8:
            deck_cards.append({"name": "Unknown", "iconUrls": {}})

        buf = await generate_deck_image(deck_cards, exp)
        try:
            out_buf = buf
        except Exception as e:
            print(f"Deck image error: {e}")
            buf.seek(0)
            out_buf = buf

        file = discord.File(fp=out_buf, filename="deck.png")
        embed.set_image(url="attachment://deck.png")

        # Deck view
        from cogs.deck import CopyDeckView
        view = CopyDeckView(
            deck_cards=deck_cards,
            player_tag=tag,
            player_name=name,
            all_cards_full=ALL_CARDS_FULL,
            support_cards=support_cards
        )
        await interaction.followup.send(embed=embed, file=file, view=view)

    # ------------------- FIXED ERROR HANDLER -------------------
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle app command errors for profile-link, profile-unlink, and player."""
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
    await bot.add_cog(Player(bot))