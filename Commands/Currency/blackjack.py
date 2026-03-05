import discord
import random
from discord.ext import commands

def create_deck():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = {
        "2": 2, "3": 3, "4": 4, "5": 5,
        "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 10, "Q": 10, "K": 10,
        "A": 11
    }
    deck = [(rank,suit,value) for suit in suits for rank,value in ranks.items()]
    random.shuffle(deck)
    return deck

def calculate_hand(hand):
    value = sum(card[2] for card in hand)
    aces = sum(1 for card in hand if card[0] == "A")
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

class BlackJackView(discord.ui.View):
    def __init__(self, bot, ctx, bet):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.bet = bet
        self.deck = create_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop()]

    def format_hand(self, hand):
        return " ".join([f"{r}{s}" for r,s, _ in hand])

    async def update_message(self, result=None):
        player_value = calculate_hand(self.player_hand)
        dealer_value = calculate_hand(self.dealer_hand)

        em = discord.Embed(
            title="🃏 Blackjack 🃏",
            color=discord.Color.red()
        )
        em.add_field(
            name="",
            value=f"{self.ctx.author.mention} started a new Blackjack game",
            inline = False
        )
        em.add_field(
            name="Your hand:",
            value=f"{self.format_hand(self.player_hand)}\nValue:{player_value}",
        )
        em.add_field(
            name="Dealer's hand:",
            value=f"{self.format_hand(self.dealer_hand)}\nValue:{dealer_value}",
        )

        if result:
            em.add_field(name="", value=result, inline=False)

        return em

    @discord.ui.button(label="HIT", style=discord.ButtonStyle.red)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        self.player_hand.append(self.deck.pop())
        player_value = calculate_hand(self.player_hand)
        if player_value > 21:
            await interaction.response.edit_message(
                embed=await self.update_message("💥 You busted! You lose"),
                view=None
            )

        await interaction.response.edit_message(embed=await self.update_message(), view=self)

    @discord.ui.button(label="STAND", style=discord.ButtonStyle.green)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.defer()
            return

        player_value = calculate_hand(self.player_hand)
        dealer_value = calculate_hand(self.dealer_hand)

        # Dealer draw logic
        while dealer_value < player_value:
            self.dealer_hand.append(self.deck.pop())
            dealer_value = calculate_hand(self.dealer_hand)
        if dealer_value == player_value:
            if random.choice([True, False]):
                self.dealer_hand.append(self.deck.pop())

        # After STAND logic
        dealer_value = calculate_hand(self.dealer_hand)

        if dealer_value > 21:
            await interaction.response.edit_message(
                embed=await self.update_message("🎊 Dealer busted! You win"),
                view=None
            )
        if dealer_value > player_value:
            await interaction.response.edit_message(
                embed=await self.update_message("🥀 You lose"),
                view=None
            )

        await interaction.response.edit_message(embed=await self.update_message(), view=self)

class BlackJack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="blackjack",aliases=["bj"])
    async def bj(self, ctx, bet: int = None):
        wallet, bank = await self.bot.db.get_balance(ctx.author.id)

        if bet is None:
            return await ctx.send("You must specify a bet amount")
        if bet < 50:
            return await ctx.send("You must bet 50 or more")
        if wallet < bet:
            return await ctx.send("You don't have enough money")

        view = BlackJackView(self.bot, ctx, bet)
        await ctx.send(embed=await view.update_message(), view=view)

async def setup(bot):
    await bot.add_cog(BlackJack(bot))
