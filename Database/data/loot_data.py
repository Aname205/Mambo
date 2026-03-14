
# Define loot table data: monster_name -> [(item_name, drop_chance, min, max), ...]
LOOT_DATA = {
    "Slime": [
        ("Rusty Copper Sword", 0.4, 1, 1),
        ("Rusty Copper Armor", 0.4, 1, 1),
        ("Rusty Copper Axe", 0.4, 1, 1),
        ("Rusty Copper Knife", 0.4, 1, 1),
    ],
    "Goblin": [
        ("Rusty Copper Sword", 0.4, 1, 1),
        ("Rusty Copper Armor", 0.4, 1, 1),
        ("Rusty Copper Axe", 0.4, 1, 1),
        ("Rusty Copper Knife", 0.4, 1, 1),
        ("Copper Sword", 0.2, 1, 1),
        ("Copper Armor", 0.2, 1, 1),
    ],
    "Wolf": [
        ("Copper Sword", 0.4, 1, 1),
        ("Copper Armor", 0.4, 1, 1),
    ],
    "Orc": [
        ("Copper Sword", 1.8, 1, 1),
        ("Copper Armor", 1.8, 1, 1),
        ("Orc Mace", 1.4, 1, 1),
        ("Orc Heart", 1.4, 1, 1),
    ],

    "Skeleton": [
        ("Copper Sword", 1.8, 1, 1),
        ("Copper Armor", 1.8, 1, 1),
        ("Cursed Bone", 1.4, 1, 1),
        ("Cursed Skull", 1.4, 1, 1),
    ],

    "Bandit": [
        ("Steel Sword", 1.2, 1, 1),
        ("Steel Armor", 1.2, 1, 1),
        ("Bandit Knife", 0.6, 1, 1),
        ("Ninja Suit", 0.6, 1, 1),
    ],

    "Venus Fly Trap": [
        ("Steel Sword", 1.2, 1, 1),
        ("Steel Armor", 1.2, 1, 1),
        ("Thorn Vine", 0.6, 1, 1),
        ("Life Bloom", 0.6, 1, 1),
    ],

    "Cursed Knight": [
        ("Knight Claymore", 0.6, 1, 1),
        ("Knight Insignia", 0.6, 1, 1),
        ("Knight Armor", 0.6, 1, 1),
    ],

    "Drowned": [
        ("Broken Trident", 0.6, 1, 1),
        ("Sea Prism", 0.6, 1, 1),
    ],

    "Ectoplasm": [
        ("Lost Soul", 0.6, 1, 1),
    ],

    "High Orc": [
        ("King Club", 0.6, 1, 1),
        ("Nazar", 0.6, 1, 1),
    ],

    "Death Root": [
        ("Death Core", 0.6, 1, 1),
        ("Death Whip", 0.6, 1, 1),
    ],

    "Corpse Pile": [
        ("Flesh Armor", 0.6, 1, 1),
        ("Rotten Meat", 0.6, 1, 1),
    ],

    "Shadow Assassin": [
        ("Shadow Coat", 0.6, 1, 1),
        ("Black Knife", 0.6, 1, 1),
    ],

    "Raptor": [
        ("Raptor Claw", 0.6, 1, 1),
    ],

    "Antlion": [
        ("Hour Glass", 0.6, 1, 1),
        ("Revert Hour Glass", 0.6, 1, 1),
        ("Mandible", 0.6, 1, 1),
    ],

    "Snowy": [
        ("Ice Cage", 0.6, 1, 1),
        ("Imbued Ice Cube", 0.6, 1, 1),
    ],

    "Gazer": [
        ("The Eye", 0.6, 1, 1),
    ],

    "Void Crawler": [
        ("Void Fang", 0.6, 1, 1),
    ],

    "Abyss Bat": [
        ("Abyss Cloak", 0.6, 1, 1),
        ("Soul Lantern", 0.6, 1, 1),
    ],

    "Bone Golem": [
        ("Bone Colossus Hammer", 0.6, 1, 1),
    ],

    "Ghoul": [
        ("Ghoul Claw", 0.6, 1, 1),
        ("Necromancer Robe", 0.6, 1, 1),
    ],

    "Plague Rat": [
        ("Plague Dagger", 0.6, 1, 1),
        ("Plague", 0.6, 1, 1),
    ],

    "Cultist": [
        ("Cultist Mask", 0.6, 1, 1),
    ],

    "Stone Gargoyle": [
        ("Gargoyle Armor", 0.6, 1, 1),
        ("Stone Sigil", 0.6, 1, 1),
    ],

    "Cave Stalker": [
        ("Cave Fang Blade", 0.6, 1, 1),
    ],

    "Blood Priest": [
        ("Blood Ritual Knife",0.6, 1, 1),
        ("Blood Pendant", 0.6, 1, 1),
        ("Ritual Robe", 0.6, 1, 1),
    ],

    "Bone Crusher": [
        ("Bone Crusher", 0.6, 1, 1),
    ],

    "Abyss Serpent": [
        ("Serpent Spear", 0.6, 1, 1),
        ("Heart Of The Sea", 0.6, 1, 1),
    ],

    "Dread Knight": [
        ("Dread Knight Greatsword", 0.6, 1, 1),
        ("Dread Plate", 0.6, 1, 1),
    ],

    "Soul Devourer": [
        ("Soul Eater", 0.6, 1, 1),
        ("Soul Phaser", 0.6, 1, 1),
    ],

    "Grave Titan": [
        ("Titan Bone", 0.6, 1, 1),
    ],

    "Nether Hound": [
        ("Nether Edge", 0.6, 1, 1),
    ],

    "Crystal Guardian": [

    ],

    "Void Reaper": [
        ("Void Crown", 0.6, 1, 1),
    ],

    "Ancient Lich": [

    ],

    "Frost Titan": [

    ],

    "Abyss Overlord": [
        ("Abyss Overlord Blade", 0.6, 1, 1),
        ("Overlord Sigil", 0.6, 1, 1),
    ],

    "Storm Chimera": [
        ("Chimera Talon", 0.6, 1, 1),
        ("Colossus Plate", 0.6, 1, 1),
        ("Chimera Scale", 0.6, 1, 1),
    ],
    "Obsidian Colossus": [
        ("Infernal Fang", 0.6, 1, 1),
        ("Matron Veil", 0.6, 1, 1),
        ("Colossus Fragment", 0.6, 1, 1),
    ],
    "Infernal Hound": [
        ("Crystal Pike", 0.6, 1, 1),
        ("Revenant Cloak", 0.6, 1, 1),
        ("Infernal Hide", 0.6, 1, 1),
    ],
    "Spectral Matron": [
        ("Leviathan Trident", 0.6, 1, 1),
        ("Thunder Roc Feather", 0.6, 1, 1),
        ("Matron Veil Scrap", 0.6, 1, 1),
    ],
    "Crystal Basilisk": [
        ("Juggernaut Maul", 0.6, 1, 1),
        ("Steed Bridle", 0.6, 1, 1),
        ("Basilisk Fang", 0.6, 1, 1),
    ],
    "Blood Revenant": [
        ("Seraph Blade", 0.6, 1, 1),
        ("Drake Scale", 0.6, 1, 1),
        ("Revenant Essence", 0.6, 1, 1),
    ],
    "Sunken Leviathan": [
        ("Behemoth Axe", 0.6, 1, 1),
        ("Frost Revenant Hood", 0.6, 1, 1),
        ("Leviathan Scale", 0.6, 1, 1),
    ],
    "Thunder Roc": [
        ("Void Hydra Fang", 0.6, 1, 1),
        ("Starborn Mantle", 0.6, 1, 1),
        ("Roc Feather", 0.6, 1, 1),
    ],
    "Iron Juggernaut": [
        ("Treant Branch", 0.6, 1, 1),
        ("Siren Song", 0.6, 1, 1),
        ("Juggernaut Core", 0.6, 1, 1),
    ],
    "Nightmare Steed": [
        ("Oblivion Knight Sword", 0.6, 1, 1),
        ("Phoenix Feather Cloak", 0.6, 1, 1),
        ("Steed Mane", 0.6, 1, 1),
    ],
    "Celestial Seraph": [
        ("Abyss Leviathan Eye", 0.6, 1, 1),
        ("Harbinger Blade", 0.6, 1, 1),
        ("Seraph Feather", 0.6, 1, 1),
    ],
    "Aether Drake": [
        ("Eclipse Colossus Shield", 0.6, 1, 1),
        ("Lunar Wraith Orb", 0.6, 1, 1),
        ("Drake Claw", 0.6, 1, 1),
    ],
    "Molten Behemoth": [
        ("Titanic Golem Hammer", 0.6, 1, 1),
        ("Astral Chimera Horn", 0.6, 1, 1),
        ("Behemoth Hide", 0.6, 1, 1),
    ],
    "Frost Revenant": [
        ("Elder Kraken Tentacle", 0.6, 1, 1),
        ("Blight Specter Mask", 0.6, 1, 1),
        ("Revenant Shroud", 0.6, 1, 1),
    ],
    "Void Hydra": [
        ("Mythic Basilisk Scale", 0.6, 1, 1),
        ("Storm Djinn Lamp", 0.6, 1, 1),
        ("Hydra Tooth", 0.6, 1, 1),
    ],
    "Starborn Wyrm": [
        ("Eternal Juggernaut Helm", 0.6, 1, 1),
        ("Celestial Valkyrie Wing", 0.6, 1, 1),
        ("Wyrm Scale", 0.6, 1, 1),
    ],
    "Ancient Treant": [
        ("Abyssal Colossus Club", 0.6, 1, 1),
        ("Solar Dragon Scale", 0.6, 1, 1),
        ("Treant Bark", 0.6, 1, 1),
    ],
    "Dread Siren": [
        ("Obsidian Titan Crown", 0.6, 1, 1),
        ("Frost Phoenix Feather", 0.6, 1, 1),
        ("Siren Tear", 0.6, 1, 1),
    ],
    "Oblivion Knight": [
        ("Ancient Leviathan Shell", 0.6, 1, 1),
        ("Thunder Wyrm Claw", 0.6, 1, 1),
        ("Knight Crest", 0.6, 1, 1),
    ],
    "Solar Phoenix": [
        ("Eclipse Behemoth Horn", 0.6, 1, 1),
        ("Lunar Chimera Mane", 0.6, 1, 1),
        ("Phoenix Ash", 0.6, 1, 1),
    ],
    "Abyss Leviathan": [
        ("Void Juggernaut Blade", 0.6, 1, 1),
        ("Starborn Drake Crest", 0.6, 1, 1),
        ("Leviathan Eye", 0.6, 1, 1),
    ],
    "Twilight Harbinger": [
        ("Oblivion Hydra Tooth", 0.6, 1, 1),
        ("Celestial Siren Harp", 0.6, 1, 1),
        ("Harbinger Mask", 0.6, 1, 1),
    ],
    "Eclipse Colossus": [
        ("Titanic Colossus Fist", 0.6, 1, 1),
        ("Solar Valkyrie Halo", 0.6, 1, 1),
        ("Colossus Shard", 0.6, 1, 1),
    ],
    "Lunar Wraith": [
        ("Abyssal Dragon Claw", 0.6, 1, 1),
        ("Frost Djinn Crystal", 0.6, 1, 1),
        ("Wraith Cloak", 0.6, 1, 1),
    ],
    "Titanic Golem": [
        ("Eternal Golem Core", 0.6, 1, 1),
        ("Obsidian Behemoth Plate", 0.6, 1, 1),
        ("Golem Pebble", 0.6, 1, 1),
    ],
    "Astral Chimera": [
        ("Lunar Drake Scale", 0.6, 1, 1),
        ("Void Colossus Shard", 0.6, 1, 1),
        ("Chimera Horn", 0.6, 1, 1),
    ],
    "Elder Kraken": [
        ("Starborn Siren Song", 0.6, 1, 1),
        ("Oblivion Juggernaut Helm", 0.6, 1, 1),
        ("Kraken Ink", 0.6, 1, 1),
    ],
    "Blight Specter": [
        ("Celestial Djinn Lamp", 0.6, 1, 1),
        ("Titanic Dragon Scale", 0.6, 1, 1),
        ("Specter Dust", 0.6, 1, 1),
    ],
    "Mythic Basilisk": [
        ("Solar Siren Lyre", 0.6, 1, 1),
        ("Basilisk Scale", 0.6, 1, 1),
    ],
    "Storm Djinn": [
        ("Djinn Lamp", 0.6, 1, 1),
    ],
    "Eternal Juggernaut": [
        ("Juggernaut Emblem", 0.6, 1, 1),
    ],
    "Celestial Valkyrie": [
        ("Valkyrie Wing", 0.6, 1, 1),
    ],
    "Abyssal Colossus": [
        ("Abyssal Core", 0.6, 1, 1),
    ],
    "Solar Dragon": [
        ("Dragon Scale", 0.6, 1, 1),
    ],
    "Obsidian Titan": [
        ("Titan Shard", 0.6, 1, 1),
    ],
    "Frost Phoenix": [
        ("Phoenix Feather", 0.6, 1, 1),
    ],
    "Ancient Leviathan": [
        ("Leviathan Horn", 0.6, 1, 1),
    ],
    "Thunder Wyrm": [
        ("Wyrm Claw", 0.6, 1, 1),
    ],
    "Eclipse Behemoth": [
        ("Behemoth Tusk", 0.6, 1, 1),
    ],
    "Lunar Chimera": [
        ("Chimera Mane", 0.6, 1, 1),
    ],
    "Void Juggernaut": [
        ("Void Emblem", 0.6, 1, 1),
    ],
    "Starborn Drake": [
        ("Drake Crest", 0.6, 1, 1),
    ],
    "Oblivion Hydra": [
        ("Hydra Scale", 0.6, 1, 1),
    ],
    "Celestial Siren": [
        ("Siren Song", 0.6, 1, 1),
    ],
    "Titanic Colossus": [
        ("Colossus Plate", 0.6, 1, 1),
    ],
    "Solar Valkyrie": [
        ("Valkyrie Halo", 0.6, 1, 1),
    ],
    "Abyssal Dragon": [
        ("Dragon Fang", 0.6, 1, 1),
    ],
    "Frost Djinn": [
        ("Djinn Crystal", 0.6, 1, 1),
    ],
    "Eternal Golem": [
        ("Golem Core", 0.6, 1, 1),
    ],
    "Astral Phoenix": [
        ("Phoenix Plume", 0.6, 1, 1),
    ],
    "Obsidian Behemoth": [
        ("Behemoth Plate", 0.6, 1, 1),
    ],
    "Lunar Drake": [
        ("Drake Scale", 0.6, 1, 1),
    ],
    "Void Colossus": [
        ("Colossus Shard", 0.6, 1, 1),
    ],
    "Starborn Siren": [
        ("Siren Feather", 0.6, 1, 1),
    ],
    "Oblivion Juggernaut": [
        ("Juggernaut Shard", 0.6, 1, 1),
    ],
    "Celestial Djinn": [
        ("Djinn Orb", 0.6, 1, 1),
    ],
    "Titanic Dragon": [
        ("Dragon Heart", 0.6, 1, 1),
    ],
    "Solar Siren": [
        ("Siren Lyre", 0.6, 1, 1),
    ],
}