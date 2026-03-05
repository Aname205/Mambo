import discord
import random
from discord.ext import commands
import asyncio

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

def can_split(hand):
    """Check whether the first two cards have the same rank."""
    if len(hand) == 2:
        return hand[0][0] == hand[1][0]  # Compare rank (index 0)
    return False

class BlackJackView(discord.ui.View):
    def __init__(self, bot, ctx, bet, on_game_end=None):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.bet = bet
        self.on_game_end = on_game_end
        self.cleanup_done = False
        self.message = None
        self.deck = create_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop()]

        # Split variables
        self.is_split = False
        self.split_hand = []
        self.current_hand = 1  # 1 = main hand, 2 = split hand
        self.hand1_done = False
        self.hand1_result = None
        self.hand2_result = None
        self.action_lock = asyncio.Lock()
        self.finalized = False

    def format_hand(self, hand):
        return " ".join([f"{r}{s}" for r,s, _ in hand])

    def can_player_split(self):
        """Check whether the player can split."""
        return can_split(self.player_hand) and not self.is_split

    async def update_message(self, result=None, state="in_progress"):
        player_value = calculate_hand(self.player_hand)
        dealer_value = calculate_hand(self.dealer_hand)

        color_map = {
            "in_progress": discord.Color.light_grey(),
            "win": discord.Color.green(),
            "loss": discord.Color.red(),
        }

        em = discord.Embed(
            title="🃏 Blackjack 🃏",
            color=color_map.get(state, discord.Color.light_grey())
        )
        em.add_field(
            name="",
            value=f"{self.ctx.author.mention} started a new Blackjack game with **{self.bet:,} :coin:**",
            inline=False
        )

        if self.is_split:
            # Show both hands after a split
            hand1_value = calculate_hand(self.player_hand)
            hand2_value = calculate_hand(self.split_hand)

            hand1_status = "👈 Playing" if self.current_hand == 1 and not self.hand1_done else ""
            hand2_status = "👈 Playing" if self.current_hand == 2 else ""

            if self.hand1_result:
                hand1_status = self.hand1_result
            if self.hand2_result:
                hand2_status = self.hand2_result

            em.add_field(
                name=f"Hand 1: {hand1_status}",
                value=f"{self.format_hand(self.player_hand)}\nValue: {hand1_value}",
                inline=True
            )
            em.add_field(
                name=f"Hand 2: {hand2_status}",
                value=f"{self.format_hand(self.split_hand)}\nValue: {hand2_value}",
                inline=True
            )
        else:
            em.add_field(
                name="Your hand:",
                value=f"{self.format_hand(self.player_hand)}\nValue: {player_value}",
            )

        em.add_field(
            name="Dealer's hand:",
            value=f"{self.format_hand(self.dealer_hand)}\nValue: {dealer_value}",
            inline=False
        )

        if result:
            em.add_field(name="", value=result, inline=False)

        return em

    async def dealer_play(self, hand=None):
        """Dealer draws cards and returns the result message"""
        if hand is None:
            hand = self.player_hand

        player_value = calculate_hand(hand)

        # Dealer must hit on 16 or less, stand on 17 or more
        dealer_value = calculate_hand(self.dealer_hand)
        while dealer_value <= 16:
            self.dealer_hand.append(self.deck.pop())
            dealer_value = calculate_hand(self.dealer_hand)

        if dealer_value > 21:
            return "win", f"🎊 Dealer busted! You win **{self.bet}** coins!"
        if dealer_value > player_value:
            return "lose", f"🥀 You lose **{self.bet}** coins!"
        if dealer_value < player_value:
            return "win", f"🎊 You win **{self.bet}** coins!"
        return "tie", "🤝 Push! It's a tie"

    async def cleanup_active_game(self):
        if self.cleanup_done:
            return
        self.cleanup_done = True
        if self.on_game_end:
            await self.on_game_end(self.ctx.author.id)

    async def finish_game(self, interaction):
        """Finish the game and calculate the final result."""
        if self.finalized:
            await self.safe_defer(interaction)
            return

        self.finalized = True
        try:
            if self.is_split:
                # Dealer plays once for both hands
                dealer_value = calculate_hand(self.dealer_hand)
                while dealer_value <= 16:
                    self.dealer_hand.append(self.deck.pop())
                    dealer_value = calculate_hand(self.dealer_hand)

                total_winnings = 0
                results = []

                # Evaluate hand 1 (if not busted)
                if self.hand1_result != "💥 Busted":
                    hand1_value = calculate_hand(self.player_hand)
                    if dealer_value > 21:
                        self.hand1_result = "🎊 Win"
                        total_winnings += self.bet
                    elif dealer_value > hand1_value:
                        self.hand1_result = "🥀 Lose"
                        total_winnings -= self.bet
                    elif dealer_value < hand1_value:
                        self.hand1_result = "🎊 Win"
                        total_winnings += self.bet
                    else:
                        self.hand1_result = "🤝 Tie"
                else:
                    total_winnings -= self.bet

                # Evaluate hand 2 (if not busted)
                if self.hand2_result != "💥 Busted":
                    hand2_value = calculate_hand(self.split_hand)
                    if dealer_value > 21:
                        self.hand2_result = "🎊 Win"
                        total_winnings += self.bet
                    elif dealer_value > hand2_value:
                        self.hand2_result = "🥀 Lose"
                        total_winnings -= self.bet
                    elif dealer_value < hand2_value:
                        self.hand2_result = "🎊 Win"
                        total_winnings += self.bet
                    else:
                        self.hand2_result = "🤝 Tie"
                else:
                    total_winnings -= self.bet

                # Update wallet
                if total_winnings != 0:
                    await self.bot.db.update_wallet(self.ctx.author.id, total_winnings)

                if total_winnings > 0:
                    final_result = f"🎊 Total: You win **{total_winnings}** coins!"
                    final_state = "win"
                elif total_winnings < 0:
                    final_result = f"🥀 Total: You lose **{abs(total_winnings)}** coins!"
                    final_state = "loss"
                else:
                    final_result = "🤝 Total: Break even!"
                    final_state = "in_progress"

                await interaction.response.edit_message(
                    embed=await self.update_message(final_result, state=final_state),
                    view=None
                )
            else:
                result_type, result_msg = await self.dealer_play()
                if result_type == "win":
                    await self.bot.db.update_wallet(self.ctx.author.id, self.bet)
                elif result_type == "lose":
                    await self.bot.db.update_wallet(self.ctx.author.id, -self.bet)

                result_state = "in_progress"
                if result_type == "win":
                    result_state = "win"
                elif result_type == "lose":
                    result_state = "loss"

                await interaction.response.edit_message(
                    embed=await self.update_message(result_msg, state=result_state),
                    view=None
                )
        finally:
            # Stop the view so timeout callback does not fire after game is resolved.
            self.stop()
            await self.cleanup_active_game()

    async def auto_stand(self, interaction):
        """Auto stand when player hits 21"""
        if self.finalized:
            await self.safe_defer(interaction)
            return

        if self.is_split and self.current_hand == 1:
            # Switch to hand 2
            self.hand1_done = True
            self.current_hand = 2
            self.split_hand.append(self.deck.pop())
            await interaction.response.edit_message(embed=await self.update_message(), view=self)
        else:
            await self.finish_game(interaction)

    async def safe_defer(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(label="HIT", style=discord.ButtonStyle.red)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await self.safe_defer(interaction)
            return
        if self.action_lock.locked() or self.finalized:
            await self.safe_defer(interaction)
            return

        async with self.action_lock:
            # Determine which hand is currently active
            if self.is_split and self.current_hand == 2:
                current_hand = self.split_hand
            else:
                current_hand = self.player_hand

            current_hand.append(self.deck.pop())
            player_value = calculate_hand(current_hand)

            if player_value > 21:
                if self.is_split:
                    if self.current_hand == 1:
                        self.hand1_result = "💥 Busted"
                        self.hand1_done = True
                        self.current_hand = 2
                        self.split_hand.append(self.deck.pop())
                        await interaction.response.edit_message(embed=await self.update_message(), view=self)
                    else:
                        self.hand2_result = "💥 Busted"
                        await self.finish_game(interaction)
                else:
                    self.finalized = True
                    await self.bot.db.update_wallet(self.ctx.author.id, -self.bet)
                    await interaction.response.edit_message(
                        embed=await self.update_message(f"💥 You busted! You lose **{self.bet}** coins!", state="loss"),
                        view=None
                    )
                    self.stop()
                    await self.cleanup_active_game()
                return

            # Auto stand when player hits 21
            if player_value == 21:
                await self.auto_stand(interaction)
                return

            await interaction.response.edit_message(embed=await self.update_message(), view=self)

    @discord.ui.button(label="STAND", style=discord.ButtonStyle.green)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await self.safe_defer(interaction)
            return
        if self.action_lock.locked() or self.finalized:
            await self.safe_defer(interaction)
            return

        async with self.action_lock:
            if self.is_split and self.current_hand == 1:
                # Switch to hand 2
                self.hand1_done = True
                self.current_hand = 2
                self.split_hand.append(self.deck.pop())
                await interaction.response.edit_message(embed=await self.update_message(), view=self)
            else:
                await self.finish_game(interaction)

    @discord.ui.button(label="SPLIT", style=discord.ButtonStyle.blurple)
    async def split(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await self.safe_defer(interaction)
            return
        if self.action_lock.locked() or self.finalized:
            await self.safe_defer(interaction)
            return

        async with self.action_lock:
            # Check whether split is allowed
            if not self.can_player_split():
                await self.safe_defer(interaction)
                return

            # Check whether the player can afford both bets
            wallet, _ = await self.bot.db.get_balance(self.ctx.author.id)
            if wallet < self.bet * 2:
                await interaction.response.send_message("You don't have enough money to split!", ephemeral=True)
                return

            # Execute split
            self.is_split = True
            self.split_hand = [self.player_hand.pop()]  # Move the second card to the new hand
            self.player_hand.append(self.deck.pop())  # Draw one card for hand 1

            # Remove the SPLIT button after a successful split
            self.remove_item(button)

            await interaction.response.edit_message(embed=await self.update_message(), view=self)

    async def on_timeout(self):
        # Ignore timeout callbacks for games that already ended.
        if self.cleanup_done:
            return

        self.finalized = True
        self.clear_items()

        if self.message:
            try:
                await self.message.edit(embed=await self.update_message("⌛ Game timed out.", state="in_progress"), view=None)
            except discord.HTTPException:
                pass

        await self.cleanup_active_game()

class BlackJack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_blackjack_users = set()

    async def register_active_game(self, user_id: int) -> bool:
        if user_id in self.active_blackjack_users:
            return False
        self.active_blackjack_users.add(user_id)
        return True

    async def clear_active_game(self, user_id: int):
        self.active_blackjack_users.discard(user_id)

    @commands.command(name="blackjack",aliases=["bj"])
    async def bj(self, ctx, bet=None):
        wallet, bank = await self.bot.db.get_balance(ctx.author.id)

        if bet is None:
            return await ctx.send("You must specify a bet amount")
        if str(bet) == 'all':
            bet = wallet
        else:
            try:
                bet = int(bet)
            except ValueError:
                return await ctx.send("Please enter a valid number")
        if bet < 50:
            return await ctx.send("You must bet 50 or more")
        if wallet < bet:
            return await ctx.send("You don't have enough money")
        if not await self.register_active_game(ctx.author.id):
            return await ctx.send("You are already playing Blackjack. Finish that game first!")

        try:
            view = BlackJackView(self.bot, ctx, bet, on_game_end=self.clear_active_game)

            # Show SPLIT only if splitting is possible and affordable
            if not view.can_player_split() or wallet < bet * 2:
                view.remove_item(view.split)

            # Check for natural blackjack (21 with first 2 cards) - pays 1.5x
            player_value = calculate_hand(view.player_hand)
            if player_value == 21:
                winnings = int(bet * 1.5)
                await self.bot.db.update_wallet(ctx.author.id, winnings)
                await self.clear_active_game(ctx.author.id)
                await ctx.send(embed=await view.update_message(f"🎰 BLACKJACK! You win **{winnings}** coins!", state="win"), view=None)
                return

            view.message = await ctx.send(embed=await view.update_message(state="in_progress"), view=view)
        except Exception:
            await self.clear_active_game(ctx.author.id)
            raise

async def setup(bot):
    await bot.add_cog(BlackJack(bot))
