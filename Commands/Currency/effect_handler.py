"""
Effect Handler — Weapon Passive System
Each passive is a function that receives a BattleState and returns a log string (or None).
EFFECT_HANDLERS is a dict mapping: effect_name -> callable
"""

import random


# ─────────────────────────────────────────────
# BattleState: holds all mutable battle state passed into each handler
# ─────────────────────────────────────────────
class BattleState:
    def __init__(
        self,
        p_hp: int,
        p_max_hp: int,
        p_damage: int,
        m_hp: int,
        m_max_hp: int,
        m_armor: int,
        m_speed: int,
        m_gauge: float,
        max_gauge: float,
    ):
        self.p_hp = p_hp
        self.p_max_hp = p_max_hp
        self.p_damage = p_damage

        self.m_hp = m_hp
        self.m_max_hp = m_max_hp
        self.m_armor = m_armor
        self.m_speed = m_speed
        self.m_gauge = m_gauge
        self.max_gauge = max_gauge

        # Accumulated state — reset each battle
        self.blood_loss_accumulated = 0   # total damage accumulated for blood_loss trigger
        self.frost_hit_count = 0          # hit counter for frost_bite
        self.frost_active = False         # whether frost debuff is currently active
        self.frost_turns_left = 0
        self.m_speed_original = m_speed   # original monster speed for frost restore
        self.corrosion_stacks = 0         # corrosion stack count (max 5)
        self.corrosion_m_armor_original = None  # set on first corrosion hit
        self.skip_next_turn = False       # overcharge penalty flag
        self.stun_turns_left = 0          # remaining stun turns from passive
        self.poison_turns_left = 0        # remaining monster turns for poison DoT
        self.rot_turns_left = 0           # remaining monster turns for scarlet rot DoT


# ─────────────────────────────────────────────
# Handlers — called after the player lands a hit
# ─────────────────────────────────────────────

def handle_blood_loss(state: BattleState, base_damage: int) -> str | None:
    threshold = state.m_max_hp * 0.20
    state.blood_loss_accumulated += base_damage
    if state.blood_loss_accumulated >= threshold:
        shock = int(state.m_max_hp * 0.05)
        state.m_hp -= shock
        state.blood_loss_accumulated = 0
        return f"🩸 **Blood Loss** triggered! Monster takes **{shock}** shock damage"
    return None


def handle_frost_bite(state: BattleState) -> str | None:
    if state.frost_active:
        return None
    state.frost_hit_count += 1
    if state.frost_hit_count >= 5:
        state.frost_hit_count = 0
        state.frost_active = True
        state.frost_turns_left = 2
        state.m_speed = max(1, int(state.m_speed * 0.80))
        return "❄️ **Frost Bite**! Monster slowed (−20% speed) and takes +10% damage for 2 turns"
    return None


def apply_frost_damage_bonus(state: BattleState, damage: int) -> int:
    if state.frost_active and state.frost_turns_left > 0:
        return int(damage * 1.10)
    return damage


def tick_frost(state: BattleState) -> str | None:
    if state.frost_active and state.frost_turns_left > 0:
        state.frost_turns_left -= 1
        if state.frost_turns_left <= 0:
            state.frost_active = False
            state.m_speed = state.m_speed_original
            return "❄️ Frost effect wore off — monster speed restored"
    return None


def handle_poison(state: BattleState) -> str | None:
    """Deals 20% of weapon damage each monster turn. Active only while turns_left > 0."""
    if state.poison_turns_left <= 0:
        return None
    dot = int(state.p_damage * 0.20)
    state.m_hp -= dot
    return f"🟢 **Poison** deals **{dot}** damage"


def handle_scarlet_rot(state: BattleState) -> str | None:
    """Deals 5% of monster max HP each monster turn. Active only while turns_left > 0."""
    if state.rot_turns_left <= 0:
        return None
    dot = int(state.m_max_hp * 0.05)
    state.m_hp -= dot
    return f"🟤 **Scarlet Rot** deals **{dot}** damage"


def refresh_poison(state: BattleState) -> str | None:
    """Called on player hit — refreshes poison to 2 turns."""
    state.poison_turns_left = 2
    return "🟤 **Poison** applied (2 turns)"


def refresh_scarlet_rot(state: BattleState) -> str | None:
    """Called on player hit — refreshes scarlet rot to 2 turns."""
    state.rot_turns_left = 2
    return "🟤 **Scarlet Rot** applied (2 turns)"


def tick_dot(state: BattleState) -> list[str]:
    """Tick down poison and rot counters each monster turn. Returns expiry messages."""
    logs = []
    if state.poison_turns_left > 0:
        state.poison_turns_left -= 1
        if state.poison_turns_left <= 0:
            logs.append("Poison wore off")
    if state.rot_turns_left > 0:
        state.rot_turns_left -= 1
        if state.rot_turns_left <= 0:
            logs.append("Scarlet Rot wore off")
    return logs


def handle_stun(state: BattleState) -> str | None:
    if random.random() < 0.10:
        state.stun_turns_left = 1
        return "💥 **Stun**! Monster is stunned for 1 turn"
    return None


def handle_madness(state: BattleState, damage: int) -> tuple[int, str | None]:
    cost = max(1, int(state.p_max_hp * 0.01))
    state.p_hp -= cost
    boosted = int(damage * 1.20)
    return boosted, f"🌀 **Madness** (+20% dmg, −{cost} HP)"


def handle_life_steal(state: BattleState, damage: int) -> str | None:
    heal = int(damage * 0.20)
    state.p_hp = min(state.p_max_hp, state.p_hp + heal)
    return f"💚 **Life Steal** heals **{heal}** HP"


def handle_swift(state: BattleState, damage: int) -> tuple[int, str | None]:
    if random.random() < 0.20:
        return damage * 2, "⚡ **Swift Strike**! Double hit!"
    return damage, None


def handle_gravity(state: BattleState) -> str | None:
    if random.random() < 0.2:
        state.m_gauge = 0
        return "🌑 **Gravity Pull**! Monster's turn delayed"
    return None


def handle_corrosion(state: BattleState) -> str | None:
    """Each hit adds a stack (max 5), each stack reduces armor by 5% of original armor."""
    if state.corrosion_stacks < 5:
        if state.corrosion_m_armor_original is None:
            state.corrosion_m_armor_original = state.m_armor
        state.corrosion_stacks += 1
        reduction = int(state.corrosion_m_armor_original * 0.05)
        state.m_armor = max(0, state.corrosion_m_armor_original - reduction * state.corrosion_stacks)
        return f"🧪 **Corrosion** ({state.corrosion_stacks}/5) reduces monster armor by {reduction}"
    return None


def tick_corrosion(state: BattleState) -> str | None:
    """Called each monster turn — removes 1 corrosion stack and restores armor by 5% of original."""
    if state.corrosion_stacks <= 0:
        return None
    state.corrosion_stacks -= 1
    if state.corrosion_stacks == 0:
        if state.corrosion_m_armor_original is not None:
            state.m_armor = state.corrosion_m_armor_original
            state.corrosion_m_armor_original = None
        return "🧪 Corrosion wore off — monster armor restored"
    reduction_per_stack = int(state.corrosion_m_armor_original * 0.05)
    state.m_armor = max(0, state.corrosion_m_armor_original - reduction_per_stack * state.corrosion_stacks)
    return f"🧪 **Corrosion** fading ({state.corrosion_stacks}/5 stacks left)"


def handle_overcharge(state: BattleState, damage: int) -> tuple[int, str | None]:
    boosted = int(damage * 1.50)
    log = "⚠️ **Overcharge** (+50% dmg)"
    if random.random() < 0.10:
        state.skip_next_turn = True
        log += " — **Unstable!** You lose your next turn"
    return boosted, log


def handle_execute(state: BattleState) -> str | None:
    if state.m_hp <= state.m_max_hp * 0.10:
        execute_dmg = state.m_hp
        state.m_hp = 0
        return f"💀 **Execute**! Monster slain ({execute_dmg} overkill)"
    return None


# ─────────────────────────────────────────────
# EFFECT_HANDLERS — main dispatch dictionary
# ─────────────────────────────────────────────
EFFECT_HANDLERS: dict[str, callable] = {
    "blood_loss":  handle_blood_loss,
    "frost_bite":  handle_frost_bite,
    "poison":      handle_poison,
    "scarlet_rot": handle_scarlet_rot,
    "stun":        handle_stun,
    "madness":     handle_madness,
    "life_steal":  handle_life_steal,
    "swift":       handle_swift,
    "gravity":     handle_gravity,
    "corrosion":   handle_corrosion,
    "overcharge":  handle_overcharge,
    "execute":     handle_execute,
}

# DoT effects — triggered at the start of the monster's turn
DOT_EFFECTS = {"poison", "scarlet_rot"}

# On-hit effects — triggered after the player lands a hit
ON_HIT_EFFECTS = {
    "blood_loss", "frost_bite", "stun",
    "madness", "life_steal", "swift",
    "gravity", "corrosion", "overcharge", "execute",
    "poison", "scarlet_rot",
}


# ─────────────────────────────────────────────
# apply_on_hit_passives — call in player turn after damage is calculated
# ─────────────────────────────────────────────
def apply_on_hit_passives(
    state: BattleState,
    damage: int,
    base_damage: int,
    weapon_passives: list[str],
) -> tuple[int, list[str]]:
    logs = []

    for effect in weapon_passives:
        if effect not in ON_HIT_EFFECTS:
            continue

        if effect == "blood_loss":
            log = handle_blood_loss(state, base_damage)
        elif effect == "frost_bite":
            log = handle_frost_bite(state)
        elif effect == "stun":
            log = handle_stun(state)
        elif effect == "madness":
            damage, log = handle_madness(state, damage)
        elif effect == "life_steal":
            log = handle_life_steal(state, damage)
        elif effect == "swift":
            damage, log = handle_swift(state, damage)
        elif effect == "gravity":
            log = handle_gravity(state)
        elif effect == "corrosion":
            log = handle_corrosion(state)
        elif effect == "overcharge":
            damage, log = handle_overcharge(state, damage)
        elif effect == "execute":
            log = handle_execute(state)
        elif effect == "poison":
            log = refresh_poison(state)
        elif effect == "scarlet_rot":
            log = refresh_scarlet_rot(state)
        else:
            log = None

        if log:
            logs.append(log)

    return damage, logs


# ─────────────────────────────────────────────
# apply_dot_passives — call at the start of the monster's turn
# ─────────────────────────────────────────────
def apply_dot_passives(
    state: BattleState,
    weapon_passives: list[str],
) -> list[str]:
    logs = []

    if "poison" in weapon_passives:
        log = handle_poison(state)
        if log:
            logs.append(log)

    if "scarlet_rot" in weapon_passives:
        log = handle_scarlet_rot(state)
        if log:
            logs.append(log)

    return logs
