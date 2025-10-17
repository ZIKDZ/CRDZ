import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import os
import asyncio
import io
from PIL import Image, ImageDraw, ImageFont

# ----------------- CONFIG -----------------
DISCORD_TOKEN = "MTQyODQ1NjA5MjQ5NjgyMjQwMw.GsLw0i.8dWeQQ2rvW3id1rT6RYaAn5KGAjuvZMi0ir_m8"  # fill
CR_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjhkOTI2ZDlkLTUxNzItNDk4Mi1hZTQ0LTQyNGIwMTVmNGU3MCIsImlhdCI6MTc2MDcwNjU2Miwic3ViIjoiZGV2ZWxvcGVyLzI1YzM0MGEwLWU4YmItNGE5OS05YmNmLTJkNGYwODMwMWJhNiIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyI0MS4xMDguMTg0LjEzMCJdLCJ0eXBlIjoiY2xpZW50In1dfQ.5xvvLI-GsSzp1NwQQzCedO8xxQ593En8QJ98n7xicCuKjkwrImCqd81MVCxK8hE0TKXCuEsXbCEBAWpInEHRCg"   # fill

# Role IDs
ROLE_UNDER_5K = 1387057587161141320
ROLE_ABOVE_5K = 1387057541254480014
ROLE_ABOVE_10K = 1390689724469088317

# Emojis
EMOJI_LAUGH = "<:CRDZ_laugh:1427739131370537000>"
EMOJI_TROPHY = "<:CRDZ_trophy:1428463338051862650>"
EMOJI_SAD = "<:CRDZ_sad:1388154333840937160>"
EMOJI_THINK = "<:CRDZ_think:1427741091439968286>"
EMOJI_COOL = "<:CRDZ_cool:1388153069421727915>"
# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- JSON DATA -----------------
DATA_FILE = "players.json"
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ----------------- Clash Royale helpers -----------------
def get_player_data(player_tag: str):
    if not player_tag.startswith("#"):
        player_tag = "#" + player_tag
    encoded_tag = player_tag.replace("#", "%23")
    url = f"https://api.clashroyale.com/v1/players/{encoded_tag}"
    headers = {"Authorization": f"Bearer {CR_API_TOKEN}"}
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
        return res.json()
    return None

def get_all_cards_full():
    """
    Returns dict: card_name -> full card object (including iconUrls and elixirCost and id)
    """
    url = "https://api.clashroyale.com/v1/cards"
    headers = {"Authorization": f"Bearer {CR_API_TOKEN}"}
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
        items = res.json().get("items") or res.json()
        mapping = {}
        for c in items:
            mapping[c["name"]] = c
        return mapping
    return {}

# Cache full card info at startup
ALL_CARDS_FULL = {}
@bot.event
async def cache_cards_on_ready():
    global ALL_CARDS_FULL
    try:
        ALL_CARDS_FULL = get_all_cards_full()
        print(f"Cached {len(ALL_CARDS_FULL)} cards.")
    except Exception as e:
        print("Failed to cache cards:", e)

# ----------------- Image generation (4x2 grid, with evo rules + elixir avg) -----------------
def generate_deck_image(deck_cards, player_level):
    """
    deck_cards: list of card dicts from player data (each with "name" and iconUrls maybe)
    player_level: int (from player data -> expLevel)
    returns: bytes buffer of PNG image
    """
    import io
    import requests
    from PIL import Image, ImageDraw, ImageFont

    card_w, card_h = 200, 300
    padding = 18
    cols, rows = 4, 2
    bg_width = cols * card_w + (cols + 1) * padding
    bg_height = rows * card_h + (rows + 1) * padding + 70  # extra header space

    # Colors (Clash Royale style)
    bg_color = (13, 37, 69)
    panel_color = (21, 115, 190)
    gold = (218, 172, 54)
    offwhite = (245, 245, 245)

    img = Image.new("RGBA", (bg_width, bg_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        font_path = "arial.ttf"
        font_small = ImageFont.truetype(font_path, 18)
        font_big = ImageFont.truetype(font_path, 28)
    except Exception:
        font_small = ImageFont.load_default()
        font_big = ImageFont.load_default()

    # Header bar
    header_h = 58
    draw.rounded_rectangle([(10, 10), (bg_width - 10, 10 + header_h)], radius=12, fill=panel_color)
    draw.text((20, 18), "Deck", font=font_big, fill=offwhite)

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

    # Elixir values
    elixir_vals = []

    # Evolution rule
    evo_limit = 1 if player_level < 30 else 2

    # Paste cards
    for idx in range(min(len(deck_cards), cols * rows)):
        card = deck_cards[idx]
        name = card.get("name", "Unknown")
        icons = card.get("iconUrls", {}) or {}
        url = None

        # � Evo rule logic
        if idx < evo_limit and card.get("evolutionLevel", 0) >= 1:
            url = icons.get("evolutionMedium") or icons.get("medium")
        else:
            url = icons.get("medium")

        # Try fallback cache if needed
        card_info = ALL_CARDS_FULL.get(name) if "ALL_CARDS_FULL" in globals() else None
        if not url and card_info:
            if idx < evo_limit and card.get("evolutionLevel", 0) >= 1:
                url = (card_info.get("iconUrls", {}) or {}).get("evolutionMedium")
            if not url:
                url = (card_info.get("iconUrls", {}) or {}).get("medium")

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

        # Draw the card
        x1, y1, x2, y2 = card_positions[idx]
        if not url:
            draw.text((x1 + 10, y1 + 10), name[:20], font=font_small, fill=offwhite)
            continue

        try:
            r = requests.get(url, timeout=10)
            card_img = Image.open(io.BytesIO(r.content)).convert("RGBA")
            card_img.thumbnail((card_w - 24, card_h - 60), Image.LANCZOS)
            paste_x = x1 + (card_w - card_img.width) // 2
            paste_y = y1 + 18
            img.paste(card_img, (paste_x, paste_y), card_img)

            # Card name text
            nm = name if len(name) <= 20 else name[:17] + "..."
            draw.text((x1 + 10, paste_y + card_img.height + 6), nm, font=font_small, fill=offwhite)

        except Exception as e:
            print(f"[DeckGen] Error loading card {name}: {e}")
            draw.text((x1 + 10, y1 + 10), name[:20], font=font_small, fill=offwhite)

    # Average elixir
    if elixir_vals:
        avg_elixir = round(sum(elixir_vals) / len(elixir_vals), 2)
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




# ----------------- Bot commands -----------------

# Admin profile-setup (keeps as you already have)
@bot.tree.command(
    name="profile-setup",
    description="(Admins only) Link a Clash Royale profile to a Discord user and save their tag."
)
@app_commands.checks.has_permissions(manage_nicknames=True)
@app_commands.describe(
    user="The Discord user to link the profile to",
    tag="The Clash Royale player tag (e.g. #Y9R22RQ2)"
)
async def profile_setup(interaction: discord.Interaction, user: discord.Member, tag: str):
    await interaction.response.defer(ephemeral=True)
    data = get_player_data(tag)
    if data is None:
        await interaction.followup.send(f"{EMOJI_SAD} Couldn't find that player tag. Please check and try again.")
        return

    cr_name = data.get("name")
    trophies = data.get("trophies", 0)
    old_name = user.display_name
    new_name = f"{old_name} | {cr_name}"

    # Update nickname
    try:
        await user.edit(nick=new_name)
        msg = f"{EMOJI_LAUGH} Nickname updated for {user.mention} → **{new_name}**!\n{EMOJI_TROPHY} Trophies: {trophies}"
    except discord.Forbidden:
        msg = f"{EMOJI_SAD} I don't have permission to change {user.mention}'s nickname."
    except Exception as e:
        msg = f"{EMOJI_THINK} Error updating nickname: {e}"

    guild = interaction.guild
    role_under = guild.get_role(ROLE_UNDER_5K)
    role_above5 = guild.get_role(ROLE_ABOVE_5K)
    role_above10 = guild.get_role(ROLE_ABOVE_10K)

    # Role logic
    target_role = None
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
            msg += f"\n{EMOJI_TROPHY} Added role: {target_role.name}"
        except Exception:
            msg += "\n⚠️ Failed to assign the role."

    # Save the tag
    saved_data = load_data()
    saved_data[str(user.id)] = {"tag": tag}
    save_data(saved_data)
    msg += "\n💾 Player tag saved successfully."
    await interaction.followup.send(msg)

@profile_setup.error
async def profile_setup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("🚫 You don’t have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ An error occurred: {error}", ephemeral=True)

# ----------------- Player command with deck image, avg elixir & Copy Deck button -----------------
class CopyDeckView(discord.ui.View):
    def __init__(self, copy_text: str):
        super().__init__(timeout=None)
        self.copy_text = copy_text

    @discord.ui.button(label="Copy Deck", style=discord.ButtonStyle.primary)
    async def copy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Send ephemeral message with copyable deck info
        await interaction.response.send_message(
            f"📋 **Copy this deck**\n\n{self.copy_text}",
            ephemeral=True
        )

@bot.tree.command(
    name="player",
    description="View Clash Royale data of a linked Discord user."
)
@app_commands.describe(user="The Discord user whose Clash Royale data you want to view")
async def player(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.defer(ephemeral=False)

    saved_data = load_data()
    user_id = str(user.id)
    if user_id not in saved_data:
        await interaction.followup.send(f"{EMOJI_SAD} {user.mention} has not been linked yet!")
        return

    tag = saved_data[user_id]["tag"]
    data = get_player_data(tag)
    if data is None:
        await interaction.followup.send(f"{EMOJI_SAD} Could not fetch data for {user.mention}. Try again later.")
        return

    # Extract fields
    name = data.get("name", "Unknown")
    exp = data.get("expLevel", "N/A")
    trophies = data.get("trophies", "N/A")
    arena = data.get("arena", {}).get("name", "Unknown Arena")
    clan = data.get("clan", {}).get("name", "No Clan")
    fav_card = data.get("currentFavouriteCard", {}).get("name", "Unknown")

    # current deck (list of card objects with name etc.)
    current_deck = data.get("currentDeck", [])
    # ensure length up to 8
    deck_cards = current_deck[:8]

    # Build list of card names and compute average elixir
    card_names = []
    elixir_vals = []
    for c in deck_cards:
        nm = c.get("name")
        card_names.append(nm)
        # try to find elixir in cached data
        card_info = ALL_CARDS_FULL.get(nm)
        elx = None
        if card_info:
            elx = card_info.get("elixir") or card_info.get("elixirCost")
        if elx is None:
            elx = c.get("elixirCost") or c.get("elixir")
        try:
            if elx is not None:
                elixir_vals.append(float(elx))
        except Exception:
            pass

    avg_elixir = round(sum(elixir_vals) / len(elixir_vals), 2) if elixir_vals else "N/A"
    deck_text = ", ".join(card_names) if card_names else "No current deck found."

    # Create embed (gold/blue theme)
    embed = discord.Embed(
        title=f"{EMOJI_TROPHY} Clash Royale Profile",
        description=f"**{user.display_name}**'s Linked Account — {name}",
        color=0xE6B72D  # gold-ish
    )
    embed.add_field(name="👤 Name", value=name, inline=True)
    embed.add_field(name="🧠 EXP Level", value=str(exp), inline=True)
    embed.add_field(name="🏆 Trophies", value=str(trophies), inline=True)
    embed.add_field(name="🏰 Arena", value=arena, inline=True)
    embed.add_field(name="🛡 Clan", value=clan, inline=True)
    embed.add_field(name="🃏 Favorite Card", value=fav_card, inline=True)
    embed.add_field(name="🎴 Current Deck", value=deck_text, inline=False)
    embed.set_footer(text=f"Player Tag: {tag} • Avg Elixir: {avg_elixir}")

    # Generate deck image (4x2) and attach
    # If there are less than 8 cards, pad with placeholders to keep layout
    while len(deck_cards) < 8:
        deck_cards.append({"name": "Unknown", "iconUrls": {}})

    buf = generate_deck_image(deck_cards, exp)
    # Reopen buffer to modify avg elixir text (quick hack: draw over header area)
    # We'll draw avg elixir onto the image before sending:
    try:
        img = Image.open(buf)
        draw = ImageDraw.Draw(img)
        try:
            font_path = "arial.ttf"
            font_small = ImageFont.truetype(font_path, 18)
        except Exception:
            font_small = ImageFont.load_default()
        avg_text = f"Avg Elixir: {avg_elixir}"
        w, h = draw.textsize(avg_text, font=font_small)
        draw.text((img.width - w - 20, 22), avg_text, font=font_small, fill=(245,245,245))
        out_buf = io.BytesIO()
        img.save(out_buf, format="PNG")
        out_buf.seek(0)
    except Exception:
        # fallback to original buffer
        buf.seek(0)
        out_buf = buf

    file = discord.File(fp=out_buf, filename="deck.png")
    embed.set_image(url="attachment://deck.png")

    # Prepare copyable deck text (names + tag + deck list)
    copy_lines = [
        f"Player: {name} ({tag})",
        f"Avg Elixir: {avg_elixir}",
        "Deck:"
    ]
    for i, nm in enumerate(card_names, start=1):
        copy_lines.append(f"{i}. {nm}")
    copy_text = "\n".join(copy_lines)

    view = CopyDeckView(copy_text=copy_text)

    await interaction.followup.send(embed=embed, file=file, view=view)


# discord api command test
@bot.tree.command(
    name="check-api",
    description="Check if the Clash Royale API connection is working."
)
async def check_api(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    test_url = "https://api.clashroyale.com/v1/cards"
    headers = {"Authorization": f"Bearer {CR_API_TOKEN}"}

    try:
        res = requests.get(test_url, headers=headers, timeout=8)
        if res.status_code == 200:
            items = res.json().get("items", [])
            await interaction.followup.send(
                f"{EMOJI_COOL} API connected successfully!"
            )
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



# ----------------- on_ready & cache -----------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    # Cache cards in background (so ALL_CARDS_FULL is ready)
    await bot.loop.create_task(asyncio.to_thread(lambda: globals().update({"ALL_CARDS_FULL": get_all_cards_full()})))
    # Set custom status
    activity = discord.Game(name="🏆 Clash Royale")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# ----------- Run the Bot -----------
bot.run(DISCORD_TOKEN)
