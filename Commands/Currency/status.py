import discord
from discord.ext import commands

class   EquipSelect(discord.ui.Select):

    def __init__(self, view, equipments):

        self.parent_view = view
        self.equipments = equipments

        options = []

        for eq in equipments:
            options.append(
                discord.SelectOption(
                    label=f"{eq[4]} {eq[2]}",
                    value=str(eq[0]),
                    emoji=eq[3]
                )
            )

        super().__init__(
            placeholder="Choose equipment",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):

        if interaction.user != self.parent_view.user:
            await interaction.response.defer()
            return

        inv_id = int(self.values[0])
        slot = self.parent_view.slot

        # Find selected equipment
        equipment = next(
            (e for e in self.equipments if e[0] == inv_id),
            None
        )

        await self.parent_view.bot.db.players.equip_item(
            interaction.user.id,
            inv_id,
            slot
        )

        # Refresh player stats
        player = await self.parent_view.bot.db.get_player(interaction.user.id)
        self.parent_view.player = player

        # Refresh inventory
        inventory = await self.parent_view.bot.db.get_inventory(interaction.user.id)
        self.parent_view.inventory = inventory
        
        # Refresh equipped items
        equipped_items = await self.parent_view.bot.db.get_equipped_items(interaction.user.id)
        self.parent_view.equipped_items = equipped_items

        # Rebuild equipment list for the slot
        equipment_type = slot
        if slot in ["accessory_1", "accessory_2"]:
            equipment_type = "accessory"

        equipments = [
            item for item in inventory
            if item[9] == equipment_type
        ]

        # rebuild UI
        self.parent_view.clear_items()

        if equipments:
            self.parent_view.add_item(EquipSelect(self.parent_view, equipments))

        self.parent_view.add_item(self.parent_view.weapon_button)
        self.parent_view.add_item(self.parent_view.armor_button)
        self.parent_view.add_item(self.parent_view.accessory_button_1)
        self.parent_view.add_item(self.parent_view.accessory_button_2)

        message = f"**You have equipped {equipment[4]} {equipment[2]} {equipment[3]}**"
        await interaction.response.edit_message(
            embed=self.parent_view.update_embed(message),
            view=self.parent_view
        )

class StatusView(discord.ui.View):
    def __init__(self, bot ,user, player, inventory, equipped_items):
        super().__init__(timeout=30)

        self.bot = bot
        self.user = user
        self.player = player
        self.inventory = inventory
        self.equipped_items = equipped_items
        self.slot = None

    def update_embed(self, message=None):
        max_health = self.player[2]
        current_health = self.player[24] if self.player[24] is not None else max_health
        damage = self.player[3]
        armor = self.player[4]
        speed = self.player[5]
        break_force = self.player[6]
        crit = self.player[7] or 0
        dodge = self.player[8] or 0
        level = self.player[13] if len(self.player) > 13 else 1
        exp = self.player[14] if len(self.player) > 14 else 0
        ability_points = self.player[15] if len(self.player) > 15 else 0
        next_exp = self.bot.db.players.exp_required(level + 1) if level < 50 else "MAX"

        em = discord.Embed(
            color=discord.Color.green()
        )
        em.set_author(name=f"{self.user.name}'s Equipment", icon_url=self.user.display_avatar.url)

        # Build level/exp header section
        if next_exp == "MAX":
            exp_text = "MAX"
            progress_bar = "[██████████] 100%"
        else:
            percent = min(1.0, exp / next_exp) if next_exp else 0
            filled = int(percent * 10)
            empty = 10 - filled
            progress_bar = f"[{'█' * filled}{'░' * empty}] {percent * 100:.0f}%"
            exp_text = f"{exp}/{next_exp} ({percent * 100:.0f}%)"

        em.add_field(
            name=f"Level: {level}",
            value=f"Experience: {exp_text}\n{progress_bar}\n💎 Ability Points (AP): **{ability_points}**\n_Use `mallocate` to spend AP_",
            inline=False
        )

        em.add_field(
            name="Stats",
            value=(
                f"❤️ Health: {current_health}/{max_health}\n"
                f"⚔️ Damage: {damage}\n"
                f"🛡 Armor: {armor}\n"
                f"💨 Speed: {speed}\n"
                f"⚡ Break Force: {break_force}\n"
                f"🎯 Crit: {crit * 100:.1f}%\n"
                f"👟 Dodge: {dodge * 100:.1f}%"
            ),
            inline=False
        )

        # Find equipped equipment
        weapon_id = self.player[9]
        armor_id = self.player[10]
        accessory_1_id = self.player[11]
        accessory_2_id = self.player[12]

        weapon, armor, accessory_1, accessory_2 = self.equipped_items

        weapon_stats = self.load_stats(weapon)
        armor_stats = self.load_stats(armor)
        accessory_1_stats = self.load_stats(accessory_1)
        accessory_2_stats = self.load_stats(accessory_2)

        em.add_field(
            name="--------------------------------------\nEquipped",
            value=(
                f"{weapon_stats}\n"
                f"{armor_stats}\n"
                f"{accessory_1_stats}\n"
                f"{accessory_2_stats}\n"
            ),
            inline=True
        )

        if message:
            em.add_field(
                name = "",
                value = f"\n**{message}**",
                inline = False
            )

        return em

    def load_stats(self, eq):
        eqs = []

        if not eq:
            return "□"

        inv_id, item_id, name, emoji, tier, _, _, _, eq_type, health, dmg, armor, speed, break_force, crit, dodge = eq

        if health:
            eqs.append(f"❤️ **{health}**")
        if dmg:
            eqs.append(f"⚔️ **{dmg}**")
        if armor:
            eqs.append(f"🛡 **{armor}**")
        if speed:
            eqs.append(f"💨 **{speed}**")
        if break_force:
            eqs.append(f"⚡ **{break_force}**")
        if crit:
            eqs.append(f"🎯 **{crit * 100:.0f}%**")
        if dodge:
            eqs.append(f"👟 **{dodge * 100:.0f}%**")
        eqst = " ".join(eqs)
        return f"**{tier} {name} {emoji}**\n{eqst}"

    def find_item(self, eq_id):
        return next((i for i in self.inventory if i[0] == eq_id), None)

    async def show_equipment(self, interaction, slot):
        self.slot = slot

        # Determine the equipment type to filter by
        equipment_type = slot
        if slot in ["accessory_1", "accessory_2"]:
            equipment_type = "accessory"

        # Filter inventory
        equipments = [
            item for item in self.inventory
            if item[9] == equipment_type
        ]

        if not equipments:
            message = f"You have no {equipment_type}s"
            await interaction.response.edit_message(embed=self.update_embed(message),view=self)
            return

        select = EquipSelect(self, equipments)

        self.clear_items()
        self.add_item(select)
        self.add_item(self.weapon_button)
        self.add_item(self.armor_button)
        self.add_item(self.accessory_button_1)
        self.add_item(self.accessory_button_2)

        await interaction.response.edit_message(embed=self.update_embed(),view=self)

    @discord.ui.button(label="Weapon 🗡️", style=discord.ButtonStyle.primary)
    async def weapon_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.defer()
            return

        await self.show_equipment(interaction, "weapon")

    @discord.ui.button(label="Armor 🛡️", style=discord.ButtonStyle.primary)
    async def armor_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.defer()
            return

        await self.show_equipment(interaction, "armor")

    @discord.ui.button(label="Accessory 💍", style=discord.ButtonStyle.primary)
    async def accessory_button_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.defer()
            return

        await self.show_equipment(interaction, "accessory_1")

    @discord.ui.button(label="Accessory 💍", style=discord.ButtonStyle.primary)
    async def accessory_button_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.defer()
            return

        await self.show_equipment(interaction, "accessory_2")

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["stat"])
    async def status(self, ctx):
        try:
            player = await self.bot.db.get_player(ctx.author.id)
            inventory = await self.bot.db.get_inventory(ctx.author.id)
            equipped_items = await self.bot.db.get_equipped_items(ctx.author.id)
            view = StatusView(self.bot ,ctx.author, player, inventory, equipped_items)

            await ctx.send(embed=view.update_embed(), view=view)

        except Exception as e:
            return await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Status(bot))
