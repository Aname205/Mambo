import discord
from discord.ext import commands

class Items(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Show the list of items
    @commands.command()
    async def items(self, ctx):
        items = await self.bot.db.get_all_items()

        em = discord.Embed(title="Items", color=discord.Color.green())

        for item_id, item_name, item_emoji, item_type in items:
            em.add_field(
                name=f"{item_name} {item_emoji}",
                value=f"ID: {item_id}",
                inline=False
            )

        await ctx.send(embed=em)

    # Show info of one item by name
    @commands.command(aliases=["if"])
    async def iteminfo(self, ctx, item_name: str = None):
        if item_name is None:
            return await ctx.send("Please name the item you are looking for")

        try:
            items = await self.bot.db.get_item_by_name(f"%{item_name}%")

            if not items:
                return await ctx.send("Item not found")

            first_item = items[0]
            (_, name, emoji, item_type, _,
             fishing_description, _,
             market_description, _,
             equipment_damage, equipment_armor, equipment_speed, equipment_break_force, equipment_price, equipment_critical_chance, equipment_dodge_chance
             ) = first_item
            description = fishing_description if fishing_description is not None else market_description or ""

            em = discord.Embed(
                title=f"{name} {emoji}",
                color=discord.Color.yellow()
            )

            em.set_footer(text=description)

            # Collect all tiers and prices
            fish_tiers_list = []
            fish_prices_list = []
            equipment_tiers_list = []
            equipment_damage_list = []
            equipment_armor_list = []
            equipment_speed_list = []
            equipment_break_force_list = []
            equipment_prices_list = []
            equipment_critical_chance_list = []
            equipment_dodge_chance_list = []
            
            for item_data in items:
                id, name, emoji, item_type, fishing_price, _, market_price, _, tier, \
                equipment_damage, equipment_armor, equipment_speed, equipment_break_force, equipment_price, equipment_critical_chance, equipment_dodge_chance \
                    = item_data
                
                if item_type == 'fish':
                    fish_tiers_list.append(tier)
                    fish_prices_list.append(f"{fishing_price} 🪙")

                if item_type == 'equipment':
                    equipment_tiers_list.append(tier)
                    equipment_damage_list.append(f"{equipment_damage}")
                    equipment_armor_list.append(f"{equipment_armor}")
                    equipment_speed_list.append(f"{equipment_speed}")
                    equipment_break_force_list.append(f"{equipment_break_force}")
                    equipment_prices_list.append(f"{equipment_price} 🪙")
                    equipment_critical_chance_list.append(f"{equipment_critical_chance * 100:.0f}%")
                    equipment_dodge_chance_list.append(f"{equipment_dodge_chance * 100:.0f}%")

            if fish_tiers_list:
                em.add_field(name="Tiers", value="\n".join(fish_tiers_list), inline=True)
                em.add_field(name="Prices", value="\n".join(fish_prices_list), inline=True)

            if equipment_tiers_list:
                em.add_field(name="Tiers", value="\n".join(equipment_tiers_list), inline=True)
                em.add_field(name="Damage 🗡️", value="\n".join(equipment_damage_list), inline=True)
                em.add_field(name="Armor 🛡", value="\n".join(equipment_armor_list), inline=True)
                em.add_field(name="Speed 💨", value="\n".join(equipment_speed_list), inline=True)
                em.add_field(name="Break Force ⚡", value="\n".join(equipment_break_force_list), inline=True)
                em.add_field(name="Prices", value="\n".join(equipment_prices_list), inline=True)
                em.add_field(name="Critical Chance 🎯", value="\n".join(equipment_critical_chance_list), inline=True)
                em.add_field(name="Dodge Chance 👟", value="\n".join(equipment_dodge_chance_list), inline=True)

            return await ctx.send(embed=em)
        except Exception as e:
            return await ctx.send(f"Error: {e}")

    # Clear all items in the database
    @commands.command()
    async def clearitem(self, ctx):
        await self.bot.db.clear_all_items()
        return await ctx.send("Cleared all items")

async def setup(bot):
    await bot.add_cog(Items(bot))