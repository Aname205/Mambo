import discord
from discord.ext import commands
import asyncio
import random

TURN_DELAY = 1


def calculate_scaled_damage(attack, defense):
    """Common mitigation formula: atk * (100 / (100 + def))."""
    denom = 100 + max(0, defense)
    return max(0.0, attack * (100 / denom))


class Hunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    async def run_monster_battle(self, ctx, battle_id):

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
                armor_gain = sum(1 for lvl in range(level_before + 1, current_level + 1) if lvl % 2 == 0)
                speed_gain = sum(1 for lvl in range(level_before + 1, current_level + 1) if lvl % 5 == 0)
                ap_gain = levels_gained * 3
                
                stat_text = f"❤️ +{health_gain} HP | ⚔️ +{damage_gain} DMG"
                if armor_gain > 0:
                    stat_text += f" | 🛡️ +{armor_gain} ARM"
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

        embed.add_field(name="Player HP", value=f"{ctx.author.mention} ❤️ {max(0,p_hp)}")
        embed.add_field(name="Monster HP", value=f"👹 ❤️ {max(0,m_hp)}")

        await message.edit(embed=embed)

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
                # Formula: sum over tiers of (tier_chance × (1/items_in_tier) × drop_chance)
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
                            # P(this tier) × P(pick this item | tier) × P(drop | picked)
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
        try:
            player = await self.bot.db.players.get_player(ctx.author.id)

            monster = await self.bot.db.monsters.get_random_monster()

            battle_id = await self.bot.db.battle_logs.start_battle(
                ctx.author.id,
                monster[0],  # monster_id
                player[2],  # p_health
                player[3],  # p_damage
                player[4],  # p_armor
                player[5],  # p_speed
                player[6],  # p_break
                player[7],  # p_crit
                player[8],  # p_dodge
                monster[2],  # m_health
                monster[3],  # m_damage
                monster[4],  # m_armor
                monster[5],  # m_tenacity
                monster[6],  # m_speed
                monster[7],  # m_crit
                monster[8],  # m_dodge
                monster[9],  # m_level
                monster[10], # m_currency
                monster[11], # m_exp_min
                monster[12], # m_exp_max
                monster[13], # m_modifier
                monster[14]  # m_loot_table_id
            )

            await ctx.send(f"👹 A **{monster[1]}** appeared!")

            asyncio.create_task(self.run_monster_battle(ctx, battle_id))

        except Exception as e:
            return await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(Hunt(bot))
