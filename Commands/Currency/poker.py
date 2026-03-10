import discord
import random
import asyncio
from discord.ext import commands

SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
VALUE = {r: i for i, r in enumerate(RANKS, 2)}

# --- MAPPING CARDS TO EMOJIS ---
# Bạn có thể thay thế các ký tự này bằng ID Emoji của Server bạn nếu có bộ bài riêng
CARD_EMOJIS = {
    "♠": "♠️",
    "♥": "♥️",
    "♦": "♦️",
    "♣": "♣️"
}

# --- UI HELPER FUNCTIONS ---
def format_card(card_tuple):
    rank, suit = card_tuple
    # Hiển thị theo kiểu: [A ♠️]
    return f"**[{rank}{CARD_EMOJIS[suit]}]**"


def create_deck():
    deck = [(r, s) for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck


def fmt(cards):
    return " ".join(format_card(c) for c in cards)


# --- POKER LOGIC ---
def evaluate(cards):
    vals = sorted([VALUE[r] for r, s in cards], reverse=True)
    suits = [s for r, s in cards]
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    groups = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

    flush_suit = None
    for s in SUITS:
        if suits.count(s) >= 5: flush_suit = s

    uniq = sorted(set(vals))
    if 14 in uniq: uniq.insert(0, 1)
    straight_high = None
    for i in range(len(uniq) - 4):
        if uniq[i] + 4 == uniq[i + 4]: straight_high = uniq[i + 4]

    if flush_suit:
        flush_cards = sorted(set([VALUE[r] for r, s in cards if s == flush_suit]))
        if 14 in flush_cards: flush_cards.insert(0, 1)
        for i in range(len(flush_cards) - 4):
            if flush_cards[i] + 4 == flush_cards[i + 4]: return (8, flush_cards[i + 4])

    if groups[0][1] == 4:
        return (7, groups[0][0], max([v for v in vals if v != groups[0][0]]))
    if groups[0][1] == 3 and groups[1][1] >= 2:
        return (6, groups[0][0], groups[1][0])
    if flush_suit:
        return (5, *sorted([VALUE[r] for r, s in cards if s == flush_suit], reverse=True)[:5])
    if straight_high:
        return (4, straight_high)
    if groups[0][1] == 3:
        return (3, groups[0][0], *[v for v in vals if v != groups[0][0]][:2])
    if groups[0][1] == 2 and groups[1][1] == 2:
        return (2, groups[0][0], groups[1][0], max([v for v in vals if v not in (groups[0][0], groups[1][0])]))
    if groups[0][1] == 2:
        return (1, groups[0][0], *[v for v in vals if v != groups[0][0]][:3])
    return (0, *vals[:5])


def hand_name(score):
    names = {8: "Straight Flush", 7: "Four of a Kind", 6: "Full House", 5: "Flush",
             4: "Straight", 3: "Three of a Kind", 2: "Two Pair", 1: "Pair", 0: "High Card"}
    return names.get(score, "Unknown")


# --- GAME EMBED BUILDER ---
def build_embed(game):
    community = game["community"]
    pot = game["pot"]
    last_action = game.get("last_action", "Game Starting...")
    turn_player = game.get("turn")

    # Hiển thị các lá bài chung
    cards_display = [format_card(c) for c in community]
    while len(cards_display) < 5:
        cards_display.append("` ? `") # Hình ảnh mặt sau lá bài
    board_str = " ".join(cards_display)

    embed = discord.Embed(
        title="♠️ Mampoker Table ♠️",
        color=0x2ecc71 if turn_player else 0x2f3136
    )
    embed.add_field(name="💰 Pot", value=f"`{pot:,}` coins", inline=True)
    embed.add_field(name="🔔 Last Action", value=f"**{last_action}**", inline=True)
    embed.add_field(name="🃏 Community Cards", value=f"\n{board_str}\n", inline=False)

    players_text = ""
    for p in game["players"]:
        if p in game["folded"]:
            status = "❌ *Folded*"
        elif p == turn_player:
            status = "⏳ **Thinking...**"
        else:
            action = game["actions"].get(p, "Waiting")
            status = f"✅ {action}"
        players_text += f"{'👉 ' if p == turn_player else ''}**{p.display_name}**: {status}\n"

    embed.add_field(name="👥 Players Status", value=players_text, inline=False)
    embed.set_footer(text="Mampoker • Good luck, have fun!")
    return embed


# --- LOBBY BUTTONS ---
class PokerLobbyView(discord.ui.View):
    def __init__(self, ctx, bet, bot):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bet = bet
        self.bot = bot
        self.players = [ctx.author]
        self.started = False
        self.cancelled = False

    @discord.ui.button(label="Join", style=discord.ButtonStyle.green, emoji="➕")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user in self.players:
            return await interaction.response.send_message("You are already in the lobby!", ephemeral=True)

        wallet, _ = await self.bot.db.get_balance(interaction.user.id)
        if wallet < self.bet:
            return await interaction.response.send_message(f"You don't have enough coins ({self.bet:,} required)!",
                                                           ephemeral=True)

        self.players.append(interaction.user)
        embed = interaction.message.embeds[0]
        embed.clear_fields()
        for i, p in enumerate(self.players, 1):
            embed.add_field(name=f"Player {i}", value=p.display_name, inline=True)

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.blurple, emoji="▶️")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Only the host can start the game!", ephemeral=True)
        if len(self.players) < 2:
            return await interaction.response.send_message("Need at least 2 players to start!", ephemeral=True)

        self.started = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Only the host can cancel the lobby!", ephemeral=True)

        self.cancelled = True
        self.stop()
        embed = interaction.message.embeds[0]
        embed.title = "❌ Lobby Cancelled"
        embed.description = f"Game cancelled by {interaction.user.mention}"
        embed.color = discord.Color.red()
        embed.clear_fields()
        await interaction.response.edit_message(embed=embed, view=None)


# --- IN-GAME BUTTONS ---
class RaiseModal(discord.ui.Modal, title="Raise Bet"):
    amount = discord.ui.TextInput(label="Amount to raise", placeholder="Enter coins...")

    def __init__(self, game):
        super().__init__()
        self.game = game

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amt = int(self.amount.value)
            if amt <= 0: raise ValueError
        except:
            return await interaction.response.send_message("Please enter a valid number!", ephemeral=True)

        wallet, _ = await self.game["bot"].db.get_balance(interaction.user.id)
        if wallet < amt:
            return await interaction.response.send_message("You don't have enough coins!", ephemeral=True)

        await self.game["bot"].db.update_wallet(interaction.user.id, -amt)
        self.game["pot"] += amt
        self.game["actions"][interaction.user] = f"Raised {amt:,}"
        self.game["last_action"] = f"{interaction.user.display_name} raised `{amt:,}`"
        self.game["event"].set()
        await interaction.response.defer()


class PokerView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=40)
        self.game = game

    async def interaction_check(self, interaction):
        if interaction.user != self.game["turn"]:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="View My Cards", style=discord.ButtonStyle.gray, emoji="👀")
    async def view_cards(self, interaction, button):
        cards = self.game["hands"].get(interaction.user)
        await interaction.response.send_message(f"Your Cards: {fmt(cards)}", ephemeral=True)

    @discord.ui.button(label="Check / Call", style=discord.ButtonStyle.green, emoji="✅")
    async def call(self, interaction, button):
        self.game["actions"][interaction.user] = "Check/Call"
        self.game["last_action"] = f"{interaction.user.display_name} checked/called"
        self.game["event"].set()
        await interaction.response.defer()

    @discord.ui.button(label="Raise", style=discord.ButtonStyle.blurple, emoji="💰")
    async def raise_btn(self, interaction, button):
        await interaction.response.send_modal(RaiseModal(self.game))

    @discord.ui.button(label="Fold", style=discord.ButtonStyle.red, emoji="🏳️")
    async def fold(self, interaction, button):
        self.game["folded"].append(interaction.user)
        self.game["actions"][interaction.user] = "Folded"
        self.game["last_action"] = f"{interaction.user.display_name} folded"
        self.game["event"].set()
        await interaction.response.defer()


# --- POKER COG ---
class Poker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def betting_round(self, ctx, game):
        for p in game["players"]:
            if p in game["folded"]: continue

            game["turn"] = p
            game["event"] = asyncio.Event()
            await game["msg"].edit(embed=build_embed(game), view=PokerView(game))

            try:
                await asyncio.wait_for(game["event"].wait(), timeout=40)
            except asyncio.TimeoutError:
                game["folded"].append(p)
                game["actions"][p] = "Timed Out"
                game["last_action"] = f"{p.display_name} auto-folded (timeout)"

            alive = [x for x in game["players"] if x not in game["folded"]]
            if len(alive) == 1:
                return alive[0]
        return None

    @commands.command()
    async def poker(self, ctx, bet: int):
        wallet, _ = await self.bot.db.get_balance(ctx.author.id)
        if wallet < bet: return await ctx.send("You don't have enough coins to start!")

        embed = discord.Embed(
            title="🃏 Mampoker Lobby 🃏",
            description=(
                f"**Host:** {ctx.author.mention}\n"
                f"**Buy-in:** `{bet:,}` 💰\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                "Click the buttons below to join or manage the lobby."
            ),
            color=0x2f3136
        )
        embed.set_thumbnail(
            url="https://images.steamusercontent.com/ugc/12797985907801958865/DCC8C6080ECA5E718D1433D31FDBD7E676ACA66C/?imw=637&imh=358&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=true")
        embed.add_field(name="Player 1", value=ctx.author.display_name, inline=True)

        view = PokerLobbyView(ctx, bet, self.bot)
        msg = await ctx.send(embed=embed, view=view)

        await view.wait()

        if view.cancelled:
            return

        if not view.started:
            embed.description = "⏰ **Lobby timed out.**"
            return await msg.edit(embed=embed, view=None)

        # --- START GAME ---
        await msg.edit(view=None)
        players = view.players
        deck = create_deck()
        hands = {p: [deck.pop(), deck.pop()] for p in players}
        community = []

        for p in players:
            await self.bot.db.update_wallet(p.id, -bet)

        game = {
            "bot": self.bot, "players": players, "hands": hands, "community": community,
            "folded": [], "pot": bet * len(players), "msg": msg, "actions": {}
        }

        phases = [0, 3, 1, 1]
        phase_names = ["Pre-flop", "The Flop", "The Turn", "The River"]

        winner = None
        for i, count in enumerate(phases):
            for _ in range(count): community.append(deck.pop())
            game["last_action"] = f"Dealing: {phase_names[i]}"
            winner = await self.betting_round(ctx, game)
            if winner: break

        if not winner:
            scores = {p: evaluate(hands[p] + community) for p in players if p not in game["folded"]}
            winner = max(scores, key=lambda x: scores[x])

        # SHOWDOWN & REWARDS
        await self.bot.db.update_wallet(winner.id, game["pot"])
        final_embed = build_embed(game)
        final_embed.title = "🏆 SHOWDOWN RESULTS"
        final_embed.set_thumbnail(url=winner.display_avatar.url)
        final_embed.description = f"🎊 {winner.mention} swept the pot of **{game['pot']:,}** coins!"

        for p in players:
            if p in game["folded"]:
                val = "🗑️ *Folded*"
            else:
                score = evaluate(hands[p] + community)
                val = f"{fmt(hands[p])}\n└─ **{hand_name(score[0])}**"
            final_embed.add_field(name=f"{'👑 ' if p == winner else ''}{p.display_name}", value=val, inline=False)

        await msg.edit(embed=final_embed, view=None)


async def setup(bot):
    await bot.add_cog(Poker(bot))