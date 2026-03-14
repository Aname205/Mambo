import discord
from discord.ext import commands
import asyncio
import random
import datetime
from collections import defaultdict, deque

TURN_DELAY = 1


def scale_monster_to_player(monster, player_level):
    """
    Scale a monster tuple's stats so that it matches the given player_level.

    Hard cap: a monster can never be scaled beyond its own base_level + 5.
        e.g. Slime (base 1) caps at level 6.

    Scaling formula:
        scaled_level   = min(player_level, base_level + 5)
        level_ratio    = scaled_level / max(base_level, 1)
        stat_mult      = level_ratio ^ 0.75   (sub-linear – avoids runaway growth)
        reward_mult    = level_ratio ^ 0.80   (slightly steeper for rewards)

    Returns a *list* copy of the monster with replaced values.
    """
    base_level = max(monster[9], 1)

    # Cap: monster can never scale beyond base + 5
    scaled_level = min(max(player_level, base_level), base_level + 5)

    ratio = scaled_level / base_level
    stat_mult   = ratio ** 0.75
    reward_mult = ratio ** 0.80

    m = list(monster)
    m[2]  = max(1, int(monster[2]  * stat_mult))   # health
    m[3]  = max(1, int(monster[3]  * stat_mult))   # damage
    m[4]  = max(0, int(monster[4]  * stat_mult))   # armor
    m[5]  = max(0, int(monster[5]  * stat_mult))   # tenacity
    m[6]  = max(1, int(monster[6]  * stat_mult))   # speed
    # crit/dodge are capped at sensible maximums
    m[7]  = min(0.75, round(monster[7]  * (1 + (ratio - 1) * 0.05), 4))  # crit
    m[8]  = min(0.60, round(monster[8]  * (1 + (ratio - 1) * 0.05), 4))  # dodge
    
    # Calculate modifier bonus to just layer onto the final displayed level
    modifier = monster[13] if len(monster) > 13 else "normal"
    mod_bonus = 0
    if modifier == "mystic":
        mod_bonus = 1
    elif modifier in ["brutal", "chaos"]:
        mod_bonus = 2
    elif modifier == "giant":
        mod_bonus = 3
        
    m[9]  = scaled_level + mod_bonus                       # effective level
    m[10] = max(1, int(monster[10] * reward_mult)) # currency_reward
    m[11] = max(1, int(monster[11] * reward_mult)) # exp_min
    m[12] = max(m[11], int(monster[12] * reward_mult))  # exp_max
    return m


def calculate_scaled_damage(attack, defense):
    """Common mitigation formula: atk * (100 / (100 + def))."""
    denom = 100 + max(0, defense)
    return max(0.0, attack * (100 / denom))


class Hunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_hunts = set()  # Track users currently in a hunt
        self.hunt_wins = defaultdict(lambda: deque(maxlen=10))  # Track hunt wins for rate limiting
        self.death_cooldowns = {}

    async def _resolve_monster(self, monster_name: str):
        """Resolve a monster by exact/prefix/contains matching. Returns (monster, error_message)."""
        query = monster_name.strip().lower()
        if not query:
            return None, "Please provide a monster name."

        all_monsters = await self.bot.db.get_all_monsters()
        if not all_monsters:
            return None, "No monsters found in database."

        exact = [m for m in all_monsters if str(m[1]).lower() == query]
        if exact:
            return exact[0], None

        prefix = [m for m in all_monsters if str(m[1]).lower().startswith(query)]
        if len(prefix) == 1:
            return prefix[0], None
        if len(prefix) > 1:
            options = ", ".join(m[1] for m in prefix[:5])
            return None, f"Multiple monsters matched: **{options}**. Please be more specific."

        contains = [m for m in all_monsters if query in str(m[1]).lower()]
        if len(contains) == 1:
            return contains[0], None
        if len(contains) > 1:
            options = ", ".join(m[1] for m in contains[:5])
            return None, f"Multiple monsters matched: **{options}**. Please be more specific."

        return None, f"Monster **{monster_name}** not found. Use a more specific name."

    async def run_monster_battle(self, ctx, battle_id, win_count):
        try:
            battle = await self.bot.db.get_active_battle(battle_id)

            player_id = battle[1]
            player_data = await self.bot.db.get_player(player_id)
            p_hp = player_data[24] if player_data[24] is not None else player_data[2]

            p_damage = player_data[3]
            p_armor = player_data[4]
            p_speed = player_data[5]
            p_break = player_data[6]
            p_crit = player_data[7]
            p_dodge = player_data[8]

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

            # Fetch the monster's base level from the DB for loot tier scaling
            monster_id = battle[2]
            raw_monster = await self.bot.db.get_monster(monster_id)
            m_base_level = raw_monster[9] if raw_monster else 1

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
                player_data = await self.bot.db.get_player(player_id)
                max_health = player_data[2]
                await self.bot.db.players.update_current_health(player_id, max_health // 2)
                self.death_cooldowns[player_id] = datetime.datetime.now() + datetime.timedelta(seconds=60)

            # ===== PLAYER WON =====
            else:
                await self.bot.db.battle_logs.end_battle(battle_id, "won")
                await self.bot.db.players.update_current_health(player_id, p_hp)
                battle_log.append("🏆 You defeated the monster")

                # Award EXP
                exp_gained = random.randint(m_exp_min, m_exp_max)
                
                player_data_before = await self.bot.db.get_player(player_id)
                level_before = player_data_before[13]
                
                leveled_up, new_level, total_ap_gained = await self.bot.db.add_exp(player_id, exp_gained)

                player_data = await self.bot.db.get_player(player_id)
                current_exp = player_data[14]
                exp_needed = self.bot.db.players.exp_required(new_level + 1)

                if leveled_up:
                    levels_gained = new_level - level_before
                    health_gain = levels_gained * 10
                    damage_gain = levels_gained * 2
                    armor_gain = sum(1 for lvl in range(level_before + 1, new_level + 1) if lvl % 2 == 0)
                    speed_gain = sum(1 for lvl in range(level_before + 1, new_level + 1) if lvl % 5 == 0)
                    
                    stat_text = f"❤️ +{health_gain} HP | ⚔️ +{damage_gain} DMG"
                    if armor_gain > 0:
                        stat_text += f" | 🛡️ +{armor_gain} ARM"
                    if speed_gain > 0:
                        stat_text += f" | 💨 +{speed_gain} SPD"
                    stat_text += f"\n💎 +{total_ap_gained} Ability Points"
                    
                    battle_log.append(f"**-----------------------------------\n⭐ LEVEL UP! You are now level {new_level}!\n{stat_text}\n-----------------------------------**")
                else:
                    battle_log.append(f"**-----------------------------------\n✨ You gained {exp_gained} EXP ({current_exp}/{exp_needed})\n-----------------------------------**")

                # Roll loot — tier chances scale with how far above base level the monster is
                drops = await self.bot.db.roll_loot(loot_table_id, m_modifier, m_level, m_base_level)

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

            embed.add_field(name="Player HP", value=f"{ctx.author.mention} ❤️ {max(0,p_hp)}")
            embed.add_field(name="Monster HP", value=f"👹 ❤️ {max(0,m_hp)}")
            
            if p_hp > 0:
                # embed.set_footer(text=f"Battle Won: {win_count}/10")
                embed.set_footer(text=f"Battle Won: {win_count}")
            await message.edit(embed=embed)
        finally:
            self.active_hunts.discard(ctx.author.id)

    @commands.command(name="monsterinfo", aliases=["mi"])
    async def monsterinfo(self, ctx, *, name: str = None):
        """Show detailed monster information by name."""
        if not name:
            return await ctx.send("Usage: `mmonsterinfo <name>`")

        # Prefer Normal variant when user provides base monster name (e.g., 'slime').
        selected_monster = None
        query = name.strip().lower()
        modifiers = {"normal", "mystic", "brutal", "chaos", "giant"}
        tokens = query.split()

        if tokens and tokens[0] not in modifiers:
            all_monsters = await self.bot.db.get_all_monsters()
            normal_name = f"normal {query}"
            normal_match = [m for m in all_monsters if str(m[1]).lower() == normal_name]
            if normal_match:
                selected_monster = normal_match[0]

        if selected_monster is None:
            selected_monster, error = await self._resolve_monster(name)
            if error:
                return await ctx.send(error)

        monster = selected_monster

        (
            monster_id,
            monster_name,
            health,
            damage,
            armor,
            tenacity,
            speed,
            critical_chance,
            dodge_chance,
            level,
            currency_reward,
            exp_min,
            exp_max,
            monster_modifier,
            loot_table_id,
        ) = monster

        em = discord.Embed(title=f"👹 {monster_name}", color=discord.Color.dark_red())
        em.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        em.add_field(name="ID", value=str(monster_id), inline=True)
        em.add_field(name="Modifier", value=monster_modifier, inline=True)
        em.add_field(name="Level", value=str(level), inline=True)

        em.add_field(
            name="Stats",
            value=(
                f"❤️ Health: **{health}**\n"
                f"⚔️ Damage: **{damage}**\n"
                f"🛡️ Armor: **{armor}**\n"
                f"🧱 Tenacity: **{tenacity}**\n"
                f"💨 Speed: **{speed}**\n"
                f"🎯 Crit: **{critical_chance * 100:.1f}%**\n"
                f"👟 Dodge: **{dodge_chance * 100:.1f}%**\n"
                f"💰 Reward: **{currency_reward}** 🪙"
            ),
            inline=False,
        )

        if loot_table_id:
            loot_items = await self.bot.db.get_loot_items(loot_table_id)
            if loot_items:
                # Tier base chances (normal modifier)
                tier_chances = {
                    "common": 0.745,
                    "uncommon": 0.15,
                    "rare": 0.08,
                    "epic": 0.02,
                    "legendary": 0.005
                }

                # Group by (item_id, tier) to count items per tier
                # and group unique items
                tier_item_count = {}  # tier -> count of items
                item_info = {}        # item_id -> {name, emoji, drop_chance, tiers: []}

                for item in loot_items:
                    item_id, drop_chance, min_amount, max_amount, item_name, emoji, item_type, item_tier = item

                    # Count items per tier
                    if item_tier:
                        tier_item_count[item_tier] = tier_item_count.get(item_tier, 0) + 1

                    # Store item info (dedupe by item_id)
                    if item_id not in item_info:
                        item_info[item_id] = {
                            "name": item_name,
                            "emoji": emoji,
                            "drop_chance": drop_chance,
                            "min_amount": min_amount,
                            "max_amount": max_amount,
                            "tiers": []
                        }
                    if item_tier and item_tier not in item_info[item_id]["tiers"]:
                        item_info[item_id]["tiers"].append(item_tier)

                # Calculate actual drop rate per item per roll
                # Formula: sum over tiers of (tier_chance × (1/items_in_tier) × data['drop_chance']
                lines = []
                for item_id, data in item_info.items():
                    tiers = data["tiers"]
                    if not tiers:
                        actual_rate = data['drop_chance']
                    else:
                        actual_rate = 0
                        for tier in tiers:
                            t_chance = tier_chances.get(tier, 0)
                            items_in_tier = tier_item_count.get(tier, 1)
                            # P(this tier) × P(pick this item | tier) × data['drop_chance']
                            actual_rate += t_chance * (1 / items_in_tier) * data['drop_chance']

                    lines.append(
                        f"{data['emoji']} **{data['name']}** - {actual_rate * 100:.1f}% x{data['min_amount']}-{data['max_amount']}"
                    )
                em.add_field(name="Loot Table", value="\n".join(lines), inline=False)
            else:
                em.add_field(name="Loot Table", value="No loot entries.", inline=False)
        else:
            em.add_field(name="Loot Table", value="No loot table assigned.", inline=False)

        await ctx.send(embed=em)

    @commands.command()
    async def hunt(self, ctx):
        now = datetime.datetime.now()
        user_id = ctx.author.id

        # Concurrency Check
        if user_id in self.active_hunts:
            return await ctx.send("You are already on a hunt! Please finish your current hunt first.")

        # Death Cooldown Check
        if user_id in self.death_cooldowns and now < self.death_cooldowns[user_id]:
            remaining = self.death_cooldowns[user_id] - now
            return await ctx.send(f"You are recovering from a recent defeat. You can hunt again in {remaining.seconds} seconds.")

        # Rate Limit Check
        self.hunt_wins[user_id] = deque(
            [ts for ts in self.hunt_wins[user_id] if (now - ts) < datetime.timedelta(hours=1)],
            # maxlen=10
        )

        # if len(self.hunt_wins[user_id]) >= 10:
        #     return await ctx.send("You have hunted too many monsters recently. Please wait before hunting again.")

        self.active_hunts.add(user_id)

        try:
            player = await self.bot.db.players.get_player(ctx.author.id)
            player_level = player[13]  # level column

            # Only pick monsters whose:
            # 1. Cap level (base + 5) can reach the player's level -> pool_min = player_level - 5
            # 2. Base level is no more than 1 level above the player -> pool_max = player_level + 1
            pool_min = max(1, player_level - 5)
            pool_max = player_level + 1
            raw_monster = await self.bot.db.monsters.get_random_monster_in_level_range(pool_min, pool_max)

            if raw_monster is None:
                await ctx.send("No monsters found. Try again later!")
                return

            # Roll the fight level in [player_level - 1, player_level + 1],
            # never below the monster's own base level,
            # and never above base_level + 5 (hard monster cap).
            base_level = raw_monster[9]
            if player_level == 1:
                min_level = 1
            else:
                min_level = max(base_level, player_level - 1)
            max_level = min(player_level + 1, base_level + 5)
            # Ensure min <= max (e.g. if base_level + 5 < player_level - 1)
            max_level = max(min_level, max_level)
            scaled_level = random.randint(min_level, max_level)

            # Scale the monster's stats to the chosen fight level
            monster = scale_monster_to_player(raw_monster, scaled_level)

            battle_id = await self.bot.db.battle_logs.start_battle(
                ctx.author.id,
                monster[0],  # monster_id
                player[2],   # p_health
                player[3],   # p_damage
                player[4],   # p_armor
                player[5],   # p_speed
                player[6],   # p_break
                player[7],   # p_crit
                player[8],   # p_dodge
                monster[2],  # m_health  (scaled)
                monster[3],  # m_damage  (scaled)
                monster[4],  # m_armor   (scaled)
                monster[5],  # m_tenacity (scaled)
                monster[6],  # m_speed   (scaled)
                monster[7],  # m_crit    (scaled)
                monster[8],  # m_dodge   (scaled)
                monster[9],  # m_level   (= player_level)
                monster[10], # m_currency (scaled)
                monster[11], # m_exp_min  (scaled)
                monster[12], # m_exp_max  (scaled)
                monster[13], # m_modifier
                monster[14]  # m_loot_table_id
            )

            await ctx.send(f"👹 A **{monster[1]}** (Lv.**{monster[9]}**) appeared!")

            await self.run_monster_battle(ctx, battle_id, len(self.hunt_wins[user_id]) + 1)

            # If the player won, add a timestamp to the win history
            self.hunt_wins[user_id].append(datetime.datetime.now())

        except Exception as e:
            return await ctx.send(f"Error: {e}")

        finally:
            # Ensure the user is removed from the active hunts set, even if there's an error
            self.active_hunts.discard(ctx.author.id)

async def setup(bot):
    await bot.add_cog(Hunt(bot))
