"""
World data for Legend of Dragon's Legacy.

Defines the map graph (node connections), NPCs per region,
and travel time calculations.
"""

from typing import Dict, List, Set


# ============================================================
# HUMAN RACE MAP GRAPH (node structure)
# Settlement of Klesva -> Baurwill Town -> King's Tomb
#   -> Light Square -> O'Delvays City Center
# ============================================================

HUMAN_MAP_GRAPH: Dict[str, List[str]] = {
    "Settlement of Klesva": ["Baurwill Town"],
    "Baurwill Town": ["Settlement of Klesva", "King's Tomb"],
    "King's Tomb": ["Baurwill Town", "Light Square"],
    "Light Square": ["King's Tomb", "O'Delvays City Center"],
    "O'Delvays City Center": ["Light Square"],
}

# All valid human region names (for validation)
HUMAN_REGIONS: Set[str] = set(HUMAN_MAP_GRAPH.keys())


# ============================================================
# NPCs PER REGION
# ============================================================

REGION_NPCS: Dict[str, List[Dict[str, str]]] = {
    "Settlement of Klesva": [
        {"name": "Elder Mirwen", "role": "Village Elder", "description": "A wise old woman who guides newcomers."},
        {"name": "Torvak the Smith", "role": "Blacksmith", "description": "Forges basic weapons and armor for adventurers."},
        {"name": "Lina", "role": "Herbalist", "description": "Sells potions and healing herbs."},
    ],
    "Baurwill Town": [
        {"name": "Captain Roderick", "role": "Guard Captain", "description": "Maintains order in the town and offers bounty quests."},
        {"name": "Mara the Merchant", "role": "General Merchant", "description": "Buys and sells a variety of goods."},
        {"name": "Old Gregor", "role": "Tavern Keeper", "description": "Runs the local tavern; a good source of rumors."},
        {"name": "Sister Alia", "role": "Healer", "description": "Provides healing services to weary travelers."},
    ],
    "King's Tomb": [
        {"name": "Warden Duskhelm", "role": "Tomb Guardian", "description": "Guards the ancient tomb and warns of dangers within."},
        {"name": "Spirit of King Aldric", "role": "Ancient Spirit", "description": "The restless spirit of the fallen king, seeking peace."},
    ],
    "Light Square": [
        {"name": "Archmage Solenne", "role": "Magic Instructor", "description": "Teaches the arcane arts to those with potential."},
        {"name": "Trader Fenwick", "role": "Rare Goods Merchant", "description": "Deals in rare and enchanted items."},
        {"name": "Bard Elowen", "role": "Bard", "description": "Sings tales of old and shares news from distant lands."},
    ],
    "O'Delvays City Center": [
        {"name": "King Aldenvale III", "role": "King", "description": "The ruler of the human realm, seated on his throne."},
        {"name": "Chancellor Voss", "role": "Royal Advisor", "description": "The king's trusted advisor on matters of state."},
        {"name": "Guildmaster Theron", "role": "Adventurer's Guild", "description": "Manages the adventurer's guild and assigns high-level quests."},
        {"name": "Master Armorer Kael", "role": "Master Blacksmith", "description": "Crafts the finest weapons and armor in the realm."},
        {"name": "Sage Orinthal", "role": "Lorekeeper", "description": "Keeper of ancient knowledge and forgotten histories."},
    ],
}


# ============================================================
# TRAVEL TIME CALCULATION
# Max level: 10
# Level 1: 10 seconds base
# Levels 2-5: +15 seconds per level
# Levels 6-10: +10 seconds per level
# ============================================================

MAX_LEVEL = 10


def get_travel_time(level: int) -> int:
    """
    Calculate travel time in seconds based on character level.

    Level 1:  10s
    Level 2:  25s  (10 + 15)
    Level 3:  40s  (10 + 30)
    Level 4:  55s  (10 + 45)
    Level 5:  70s  (10 + 60)
    Level 6:  80s  (70 + 10)
    Level 7:  90s  (70 + 20)
    Level 8:  100s (70 + 30)
    Level 9:  110s (70 + 40)
    Level 10: 120s (70 + 50)
    """
    clamped_level = max(1, min(level, MAX_LEVEL))

    base = 10  # level 1

    if clamped_level <= 5:
        return base + (clamped_level - 1) * 15
    else:
        # levels 2-5 contribute 4 * 15 = 60
        return base + 60 + (clamped_level - 5) * 10


def get_connected_regions(current_map: str) -> List[str]:
    """Return the list of regions directly connected to the given map."""
    return HUMAN_MAP_GRAPH.get(current_map, [])


def is_valid_travel(current_map: str, destination: str) -> bool:
    """Check if travel from current_map to destination is valid (adjacent)."""
    return destination in HUMAN_MAP_GRAPH.get(current_map, [])


def get_npcs_for_region(region: str) -> List[Dict[str, str]]:
    """Return the list of NPCs in the given region."""
    return REGION_NPCS.get(region, [])