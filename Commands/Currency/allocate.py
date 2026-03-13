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

        em = discord.Embed(
            title="💎 Ability Points Allocation",
            description=f"You have **{ability_points}** AP available.\nClick a button to spend 1 AP on that stat.",
            color=discord.Color.purple()
        )

        em.add_field(
            name="Current Stats",
            value=(
                f"❤️ Health: **{health}** (+5 per AP)\n"
                f"⚔️ Damage: **{damage}** (+1 per AP)\n"
                f"🛡️ Armor: **{armor}** (+0.5 per AP)\n"
                f"💨 Speed: **{speed}** (+0.3 per AP)\n"
                f"⚡ Break Force: **{break_force}** (+0.2 per AP)\n"
                f"🎯 Crit: **{crit * 100:.1f}%** (+0.3% per AP)\n"
                f"👟 Dodge: **{dodge * 100:.1f}%** (+0.1% per AP)"
            ),
            inline=False
        )

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

        em = discord.Embed(
            title="💎 Ability Points Allocation",
            description=f"You have **{ability_points}** AP available.\nClick a button to spend 1 AP on that stat.",
            color=discord.Color.purple()
        )

        em.add_field(
            name="Current Stats",
            value=(
                f"❤️ Health: **{health}** (+5 per AP)\n"
                f"⚔️ Damage: **{damage}** (+1 per AP)\n"
                f"🛡️ Armor: **{armor}** (+0.5 per AP)\n"
                f"💨 Speed: **{speed}** (+0.3 per AP)\n"
                f"⚡ Break Force: **{break_force}** (+0.2 per AP)\n"
                f"🎯 Crit: **{crit * 100:.1f}%** (+0.3% per AP)\n"
                f"👟 Dodge: **{dodge * 100:.1f}%** (+0.1% per AP)"
            ),
            inline=False
        )

        view = AllocateView(ctx.author, self.bot)
        await ctx.send(embed=em, view=view)

async def setup(bot):
    await bot.add_cog(Allocate(bot))
