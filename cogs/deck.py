import discord
from utils.deck_link import build_deck_link

class CopyDeckView(discord.ui.View):
    """Reusable 'Copy Deck' button view for Clash Royale decks."""
    def __init__(self, deck_cards, player_tag, player_name, all_cards_full, support_cards=None):
        super().__init__(timeout=None)
        self.deck_cards = deck_cards
        self.player_tag = player_tag
        self.player_name = player_name
        self.all_cards_full = all_cards_full
        self.support_cards = support_cards

        # Build the deck URL using the cached full card data
        url = build_deck_link(deck_cards, player_tag, all_cards_full, support_cards)

        # Add the link button
        self.add_item(discord.ui.Button(
            label="Copy Deck",
            style=discord.ButtonStyle.link,
            url=url
        ))

# Required so this cog can be loaded properly
async def setup(bot):
    pass
