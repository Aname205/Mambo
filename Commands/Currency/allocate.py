import discord
from discord.ext import commands

class AllocateView(discord.ui.View):
    def __init__(self, user, bot):
        super().__init__(timeout=60)
        self.user = user
        self.bot = bot

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your allocation menu!", ephemeral=True)
            return False
        return True

    async def update_embed(self, interaction):
        player = await self.bot.db.get_player(self.user.id)
        ability_points = player[15]
        health = player[2]
        damage = player[3]
        armor = player[4]
        speed = player[5]
        break_force = player[6]
        crit = player[7]
        dodge = player[8]
        
        # Get AP spent from tracker columns (indices 16-22)
        ap_health = player[16] if len(player) > 16 else 0
        ap_damage = player[17] if len(player) > 17 else 0
        ap_armor = player[18] if len(player) > 18 else 0
        ap_speed = player[19] if len(player) > 19 else 0
        ap_break = player[20] if len(player) > 20 else 0
        ap_crit = player[21] if len(player) > 21 else 0
        ap_dodge = player[22] if len(player) > 22 else 0

        em = discord.Embed(
            title="💎 Ability Points Allocation",
            description=f"You have **{ability_points}** AP available.\nClick a button to spend 1 AP on that stat.",
            color=discord.Color.purple()
        )

        em.add_field(
            name="Current Stats",
            value=(
                f"❤️ Health: **{health}** (+5 per AP) *[+{ap_health}]*\n"
                f"⚔️ Damage: **{damage}** (+1 per AP) *[+{ap_damage}]*\n"
                f"🛡️ Armor: **{armor}** (+0.5 per AP) *[+{ap_armor}]*\n"
                f"💨 Speed: **{speed}** (+0.2 per AP) *[+{ap_speed}]*\n"
                f"⚡ Break Force: **{break_force}** (+0.2 per AP) *[+{ap_break}]*\n"
                f"🎯 Crit: **{crit * 100:.1f}%** (+0.3% per AP) *[+{ap_crit}]*\n"
                f"👟 Dodge: **{dodge * 100:.1f}%** (+0.1% per AP) *[+{ap_dodge}]*"
            ),
            inline=False
        )

        em.set_footer(text="Reset costs 5000 🪙")

        await interaction.response.edit_message(embed=em, view=self)

    async def spend_point(self, interaction, stat, stat_name, emoji):
        player = await self.bot.db.get_player(self.user.id)
        ability_points = player[15]

        if ability_points < 1:
            await interaction.response.send_message("❌ You don't have any AP to spend!", ephemeral=True)
            return

        success, message, remaining = await self.bot.db.players.spend_ability_point(
            self.user.id,
            stat
        )

        if success:
            await self.update_embed(interaction)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)

    @discord.ui.button(label="Health", emoji="❤️", style=discord.ButtonStyle.primary, row=0)
    async def health_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spend_point(interaction, "health", "Health", "❤️")

    @discord.ui.button(label="Damage", emoji="⚔️", style=discord.ButtonStyle.primary, row=0)
    async def damage_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spend_point(interaction, "damage", "Damage", "⚔️")

    @discord.ui.button(label="Armor", emoji="🛡️", style=discord.ButtonStyle.primary, row=0)
    async def armor_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spend_point(interaction, "armor", "Armor", "🛡️")

    @discord.ui.button(label="Speed", emoji="💨", style=discord.ButtonStyle.primary, row=1)
    async def speed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spend_point(interaction, "speed", "Speed", "💨")

    @discord.ui.button(label="Break Force", emoji="⚡", style=discord.ButtonStyle.primary, row=1)
    async def break_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spend_point(interaction, "break_force", "Break Force", "⚡")

    @discord.ui.button(label="Crit", emoji="🎯", style=discord.ButtonStyle.primary, row=2)
    async def crit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spend_point(interaction, "critical_chance", "Crit", "🎯")

    @discord.ui.button(label="Dodge", emoji="👟", style=discord.ButtonStyle.primary, row=2)
    async def dodge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spend_point(interaction, "dodge_chance", "Dodge", "👟")

    @discord.ui.button(label="Reset AP (5000 🪙)", emoji="🔄", style=discord.ButtonStyle.danger, row=3)
    async def reset_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if player has enough money
        in_hand, in_bank = await self.bot.db.get_balance(self.user.id)
        
        if in_hand < 5000:
            await interaction.response.send_message(
                f"❌ You need 5000 🪙 to reset AP! You have {in_hand} 🪙",
                ephemeral=True
            )
            return
        
        # Deduct money
        await self.bot.db.update_wallet(self.user.id, -5000)
        
        # Reset AP
        success, message, ap_refunded = await self.bot.db.players.reset_ability_points(self.user.id)
        
        if success:
            await interaction.response.send_message(
                f"✅ {message}\n💰 Paid 5000 🪙",
                ephemeral=True
            )
            await self.update_embed(interaction)
        else:
            # Refund money if reset failed
            await self.bot.db.update_wallet(self.user.id, 5000)
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)


class Allocate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["ap", "abilitypoint"])
    async def allocate(self, ctx):
        """
        Open the ability points allocation menu.
        Click buttons to spend 1 AP on each stat.
        """
        
        player = await self.bot.db.get_player(ctx.author.id)
        ability_points = player[15]
        health = player[2]
        damage = player[3]
        armor = player[4]
        speed = player[5]
        break_force = player[6]
        crit = player[7]
        dodge = player[8]
        
        # Get AP spent from tracker columns (indices 16-22)
        ap_health = player[16] if len(player) > 16 else 0
        ap_damage = player[17] if len(player) > 17 else 0
        ap_armor = player[18] if len(player) > 18 else 0
        ap_speed = player[19] if len(player) > 19 else 0
        ap_break = player[20] if len(player) > 20 else 0
        ap_crit = player[21] if len(player) > 21 else 0
        ap_dodge = player[22] if len(player) > 22 else 0

        em = discord.Embed(
            title="💎 Ability Points Allocation",
            description=f"You have **{ability_points}** AP available.\nClick a button to spend 1 AP on that stat.",
            color=discord.Color.purple()
        )

        em.add_field(
            name="Current Stats",
            value=(
                f"❤️ Health: **{health}** (+5 per AP) *[+{ap_health}]*\n"
                f"⚔️ Damage: **{damage}** (+1 per AP) *[+{ap_damage}]*\n"
                f"🛡️ Armor: **{armor}** (+0.5 per AP) *[+{ap_armor}]*\n"
                f"💨 Speed: **{speed}** (+0.2 per AP) *[+{ap_speed}]*\n"
                f"⚡ Break Force: **{break_force}** (+0.2 per AP) *[+{ap_break}]*\n"
                f"🎯 Crit: **{crit * 100:.1f}%** (+0.3% per AP) *[+{ap_crit}]*\n"
                f"👟 Dodge: **{dodge * 100:.1f}%** (+0.1% per AP) *[+{ap_dodge}]*"
            ),
            inline=False
        )

        em.set_footer(text="Reset costs 5000 🪙")

        view = AllocateView(ctx.author, self.bot)
        await ctx.send(embed=em, view=view)

async def setup(bot):
    await bot.add_cog(Allocate(bot))
