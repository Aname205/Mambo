import discord
from discord.ext import commands
import random
import asyncio

TURN_DELAY = 1


def calculate_scaled_damage(attack, defense):
    denom = 100 + max(0, defense)
    return max(0.0, attack * (100 / denom))


class BattleLogView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return False
        return True

    @discord.ui.button(label="OK", style=discord.ButtonStyle.green)
    async def ok(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


# ================= DUNGEON =================

class Dungeon:

    def __init__(self, floor=1, size=7):

        self.floor = floor
        self.size = size

        self.player_x = size // 2
        self.player_y = size // 2

        self.has_key = False

        self.grid = [["empty" for _ in range(size)] for _ in range(size)]

        self.generate()

    def generate(self):

        monster_count = random.randint(6, 10)

        for _ in range(monster_count):

            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)

            if (x, y) != (self.player_x, self.player_y):
                self.grid[y][x] = "monster"

        # spawn key
        while True:

            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)

            if self.grid[y][x] == "empty" and (x, y) != (self.player_x, self.player_y):
                self.grid[y][x] = "key"
                break

        # spawn ladder
        while True:

            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)

            if self.grid[y][x] == "empty":
                self.grid[y][x] = "ladder"
                break

    def move_monsters(self):

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        new_grid = [row[:] for row in self.grid]

        player_x = self.player_x
        player_y = self.player_y

        battle_triggered = False

        for y in range(self.size):
            for x in range(self.size):

                if self.grid[y][x] != "monster":
                    continue

                dx = player_x - x
                dy = player_y - y
                distance = abs(dx) + abs(dy)

                # chase player slightly
                if distance <= 2:
                    if abs(dx) > abs(dy):
                        move_x = 1 if dx > 0 else -1
                        move_y = 0
                    else:
                        move_x = 0
                        move_y = 1 if dy > 0 else -1
                else:
                    move_x, move_y = random.choice(directions)

                nx = x + move_x
                ny = y + move_y

                if not (0 <= nx < self.size and 0 <= ny < self.size):
                    continue

                # monster steps on player
                if nx == player_x and ny == player_y:
                    battle_triggered = True
                    new_grid[y][x] = "empty"
                    continue

                if new_grid[ny][nx] == "empty":
                    new_grid[ny][nx] = "monster"
                    new_grid[y][x] = "empty"

        self.grid = new_grid

        if battle_triggered:
            return "battle"

        return None

    def move(self, dx, dy):

        nx = self.player_x + dx
        ny = self.player_y + dy

        if nx < 0 or ny < 0 or nx >= self.size or ny >= self.size:
            return "wall"

        self.player_x = nx
        self.player_y = ny

        tile = self.grid[ny][nx]

        if tile == "monster":
            self.grid[ny][nx] = "empty"
            return "monster"

        if tile == "key":
            self.grid[ny][nx] = "empty"
            self.has_key = True
            return "key"

        if tile == "ladder":
            if self.has_key:
                return "ladder"
            else:
                return "ladder_locked"

        return "empty"


# ================= RENDER MAP =================

def render_dungeon(dungeon):

    rows = []

    for y in range(dungeon.size):

        row = ""

        for x in range(dungeon.size):

            if x == dungeon.player_x and y == dungeon.player_y:
                row += "🧑"

            else:

                tile = dungeon.grid[y][x]

                if tile == "empty":
                    row += "⬛"

                elif tile == "monster":
                    row += "❓"

                elif tile == "ladder":
                    row += "🪜"

                elif tile == "key":
                    row += "🔑"

        rows.append(row)

    return "\n".join(rows)


# ================= VIEW =================

class DungeonView(discord.ui.View):

    def __init__(self, cog, ctx, dungeon):

        super().__init__(timeout=900)

        self.cog = cog
        self.ctx = ctx
        self.dungeon = dungeon
        self.message = None

    def set_buttons(self, state: bool):
        for child in self.children:
            child.disabled = not state

    async def interaction_check(self, interaction):

        if interaction.user.id != self.ctx.author.id:
            await interaction.response.defer()
            return False

        return True

    async def update_embed(self, interaction, event=None):

        if not interaction.response.is_done():
            await interaction.response.defer()

        description = render_dungeon(self.dungeon)

        embed = discord.Embed(
            description=description,
            color=discord.Color.dark_teal()
        )

        embed.set_author(
            name=f"{self.ctx.author.name} — 🏰 Dungeon Floor {self.dungeon.floor}",
            icon_url=self.ctx.author.display_avatar.url
        )

        if event == "key":

            embed.add_field(
                name="🔑 Key Found",
                value="You picked up the **Dungeon Key**",
                inline=False
            )

        if event == "ladder_locked":

            embed.add_field(
                name="🪜 Locked Ladder",
                value="You need a **🔑 key** to descend",
                inline=False
            )

        if event == "monster":

            self.set_buttons(False)

            dungeon_monster_level = (self.dungeon.floor - 1) // 3 + 1

            monster = await self.cog.bot.db.get_random_monster_by_level(
                dungeon_monster_level
            )

            monster = list(monster)

            embed.add_field(
                name="Encounter",
                value=f"👹 **{monster[1]}** appears",
                inline=False
            )

            player = await self.cog.bot.db.get_player(self.ctx.author.id)

            battle_id = await self.cog.bot.db.start_battle(
                self.ctx.author.id,
                monster[0],

                player[2],
                player[3],
                player[4],
                player[5],
                player[6],
                player[7],
                player[8],

                monster[2],
                monster[3],
                monster[4],
                monster[5],
                monster[6],
                monster[7],
                monster[8],
                monster[9],
                monster[10],
                monster[11],
                monster[12],
                monster[13],
                monster[14]
            )

            await interaction.edit_original_response(embed=embed, view=self)

            asyncio.create_task(
                self.cog.run_monster_battle(self.ctx, battle_id, self)
            )

        if event == "ladder":

            self.dungeon.floor += 1
            self.dungeon = Dungeon(self.dungeon.floor)

            embed = discord.Embed(
                description=render_dungeon(self.dungeon),
                color=discord.Color.dark_teal()
            )

            embed.set_author(
                name=f"{self.ctx.author.name} — 🏰 Dungeon Floor {self.dungeon.floor}",
                icon_url=self.ctx.author.display_avatar.url
            )

            embed.add_field(
                name="🪜 Ladder",
                value=f"You descend to **Floor {self.dungeon.floor}**",
                inline=False
            )

        await self.message.edit(embed=embed, view=self)

    async def move(self, interaction, dx, dy):

        event = self.dungeon.move(dx, dy)

        if event == "wall":
            return await interaction.response.send_message(
                "🚫 You hit a wall.",
                ephemeral=True
            )

        # if player stepped on monster, start battle immediately
        if event == "monster":
            await self.update_embed(interaction, "monster")
            return

        # monsters move after player
        monster_event = self.dungeon.move_monsters()

        if monster_event == "battle":
            await self.update_embed(interaction, "monster")
            return

        await self.update_embed(interaction, event)

    @discord.ui.button(label="⬆️", style=discord.ButtonStyle.secondary)
    async def up(self, interaction, button):
        await self.move(interaction, 0, -1)

    @discord.ui.button(label="⬇️", style=discord.ButtonStyle.secondary)
    async def down(self, interaction, button):
        await self.move(interaction, 0, 1)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def left(self, interaction, button):
        await self.move(interaction, -1, 0)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def right(self, interaction, button):
        await self.move(interaction, 1, 0)


# ================= COG =================

class DungeonGame(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # BATTLE FUNCTION

    async def run_monster_battle(self, ctx, battle_id, view):
        battle = await self.bot.db.get_active_battle(battle_id)

        player_id = battle[1]

        p_hp = battle[3]
        p_damage = battle[4]
        p_armor = battle[5]
        p_speed = battle[6]
        p_break = battle[7]
        p_crit = battle[8]
        p_dodge = battle[9]

        m_hp = battle[10]
        m_damage = battle[11]
        m_armor = battle[12]
        m_tenacity = battle[13]
        m_speed = battle[14]
        m_crit = battle[15]
        m_dodge = battle[16]

        m_level = battle[17]
        m_currency = battle[18]
        m_exp_min = battle[19]
        m_exp_max = battle[20]
        m_modifier = battle[21]
        loot_table_id = battle[22]

        max_tenacity = m_tenacity
        is_stunned = False

        max_gauge = max(p_speed, m_speed)

        p_gauge = 0
        m_gauge = 0

        battle_log = []

        message = await ctx.send("⚔️ **Monster Battle Started**")

        while p_hp > 0 and m_hp > 0:

            if p_gauge < max_gauge and m_gauge < max_gauge:
                p_gauge += p_speed
                m_gauge += m_speed
                continue

            actor = None

            if p_gauge >= max_gauge and m_gauge >= max_gauge:
                actor = 1 if p_gauge >= m_gauge else 2
            elif p_gauge >= max_gauge:
                actor = 1
            elif m_gauge >= max_gauge:
                actor = 2

            # PLAYER TURN
            if actor == 1:

                p_gauge -= max_gauge

                if random.random() < m_dodge and not is_stunned:
                    battle_log.append("👹 Monster **dodged** your attack")
                else:

                    base_damage = calculate_scaled_damage(p_damage, m_armor)
                    damage = int(base_damage * random.uniform(0.8, 1.2))

                    if is_stunned:
                        damage *= 2
                        is_stunned = False
                        m_tenacity = max_tenacity
                        battle_log.append("💫 Stunned monster took double damage!")

                    if random.random() < p_crit:
                        damage *= 2
                        crit = "💥 **CRIT**"
                    else:
                        crit = ""

                    m_hp -= damage

                    battle_log.append(
                        f"{ctx.author.mention} hits monster for **{damage}** {crit}"
                    )

                    if not is_stunned and max_tenacity > 0:
                        m_tenacity -= p_break
                        if m_tenacity <= 0:
                            is_stunned = True
                            m_tenacity = 0
                            battle_log.append("💫 Monster's tenacity broke! It is **Stunned**!")

                await asyncio.sleep(TURN_DELAY)

            # MONSTER TURN
            if actor == 2:

                m_gauge -= max_gauge

                if is_stunned:
                    battle_log.append("💫 Monster is **Stunned** and skips its turn!")
                else:
                    if random.random() < p_dodge:
                        battle_log.append("👟 You **dodged** the monster attack")
                    else:

                        base_damage = calculate_scaled_damage(m_damage, p_armor)
                        damage = int(base_damage * random.uniform(0.8, 1.2))

                        if random.random() < m_crit:
                            damage *= 2
                            crit = "💥 **CRIT**"
                        else:
                            crit = ""

                        p_hp -= damage

                        battle_log.append(
                            f"👹 Monster hits you for **{damage}** {crit}"
                        )

                await asyncio.sleep(TURN_DELAY)

            embed = discord.Embed(
                title="⚔️ Monster Battle",
                description="\n".join(battle_log[-6:]),
                color=discord.Color.dark_red()
            )

            player_stats = (
                f"❤️ HP: **{p_hp}**\n"
                f"⚔️ Damage: **{p_damage}**\n"
                f"🛡️ Armor: **{p_armor}**\n"
                f"💨 Speed: **{p_speed}**\n"
                f"⚡ Break: **{p_break}**\n"
                f"🎯 Crit: **{p_crit * 100:.1f}%**\n"
                f"👟 Dodge: **{p_dodge * 100:.1f}%**"
            )

            monster_stats = (
                f"❤️ HP: **{m_hp}**\n"
                f"⚔️ Damage: **{m_damage}**\n"
                f"🛡️ Armor: **{m_armor}**\n"
                f"💨 Speed: **{m_speed}**\n"
                f"🧱 Tenacity: **{m_tenacity}**\n"
                f"🎯 Crit: **{m_crit * 100:.1f}%**\n"
                f"👟 Dodge: **{m_dodge * 100:.1f}%**\n"
                f"🎖 Level: **{m_level}**\n"
            )

            embed.add_field(
                name=f"🧑 {ctx.author.display_name}",
                value=player_stats,
                inline=True
            )

            embed.add_field(
                name=f"👹 Monster ({m_modifier})",
                value=monster_stats,
                inline=True
            )

            await message.edit(embed=embed)

            if p_hp <= 0 or m_hp <= 0:
                break

        # ===== PLAYER LOST =====
        if p_hp <= 0:

            await self.bot.db.battle_logs.end_battle(battle_id, "lost")

            battle_log.append("💀 You were defeated!")

        # ===== PLAYER WON =====
        else:

            await self.bot.db.battle_logs.end_battle(battle_id, "won")

            battle_log.append("🏆 You defeated the monster")

            # Award EXP
            exp_gained = random.randint(m_exp_min, m_exp_max)
            
            # Get level before adding exp
            player_data_before = await self.bot.db.get_player(player_id)
            level_before = player_data_before[13]
            
            leveled_up = await self.bot.db.add_exp(player_id, exp_gained)

            player_data = await self.bot.db.get_player(player_id)
            current_level = player_data[13]  # level column
            current_exp = player_data[14]    # exp column
            exp_needed = self.bot.db.players.exp_required(current_level + 1)

            if leveled_up:
                levels_gained = current_level - level_before
                health_gain = levels_gained * 10
                damage_gain = levels_gained * 2
                armor_gain = levels_gained * 1
                speed_gain = sum(1 for lvl in range(level_before + 1, current_level + 1) if lvl % 5 == 0)
                ap_gain = levels_gained * 3
                
                stat_text = f"❤️ +{health_gain} HP | ⚔️ +{damage_gain} DMG | 🛡️ +{armor_gain} ARM"
                if speed_gain > 0:
                    stat_text += f" | 💨 +{speed_gain} SPD"
                stat_text += f"\n💎 +{ap_gain} Ability Points"
                
                battle_log.append(f"**-----------------------------------\n⭐ LEVEL UP! You are now level {current_level}!\n{stat_text}\n-----------------------------------**")
            else:
                battle_log.append(f"**-----------------------------------\n✨ You gained {exp_gained} EXP ({current_exp}/{exp_needed})\n-----------------------------------**")

            # Roll loot
            drops = await self.bot.db.roll_loot(loot_table_id, m_modifier)

            if drops or m_currency > 0:
                battle_log.append("🎁 **Drops:**")

                # Add currency as a drop
                if m_currency > 0:
                    await self.bot.db.update_wallet(player_id, m_currency)
                    battle_log.append(f"💰 {m_currency} 🪙")

                # Add item drops
                for drop in drops:
                    item_id = drop["item_id"]
                    tier = drop["tier"]
                    amount = drop["amount"]
                    name = drop["name"]
                    emoji = drop["emoji"]

                    await self.bot.db.add_to_inventory(
                        player_id,
                        item_id,
                        tier,
                        amount
                    )

                    tier_str = f"[{tier}] " if tier else ""
                    battle_log.append(
                        f"{emoji} {tier_str}{name} x{amount}"
                    )
            else:
                battle_log.append("😢 No items dropped")

        embed = discord.Embed(
            title="⚔️ Battle Finished",
            description="\n".join(battle_log[-10:]),
            color=discord.Color.gold()
        )

        embed.add_field(name="Player HP", value=f"{ctx.author.mention} ❤️ {max(0, p_hp)}")
        embed.add_field(name="Monster HP", value=f"👹 ❤️ {max(0, m_hp)}")

        view_ok = BattleLogView(player_id)
        await message.edit(embed=embed, view=view_ok)

        view.set_buttons(True)
        await view.message.edit(view=view)

    @commands.command()
    async def dungeon(self, ctx, floor: int = 1):

        if floor < 1:
            floor = 1

        dungeon = Dungeon(floor)

        embed = discord.Embed(
            description=render_dungeon(dungeon),
            color=discord.Color.dark_teal()
        )

        embed.set_author(
            name=f"{ctx.author.name} — 🏰 Dungeon Floor {floor}",
            icon_url=ctx.author.display_avatar.url
        )

        view = DungeonView(self, ctx, dungeon)

        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


async def setup(bot):
    await bot.add_cog(DungeonGame(bot))