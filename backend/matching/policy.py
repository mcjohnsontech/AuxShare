# backend/matching/policy.py
from typing import Dict, Set

# Version policy table - configurable
VERSION_POLICY = {
    # Tags treated as same recording (configurable)
    "remaster": True,
    "remastered": True,
    "deluxe": True,
    "radio edit": True,
    "radio version": True,
    "single version": True,
    "album version": True,
    "edit": False,  # Be conservative
    # Tags treated as different recording (hard penalty/reject)
    "live": False,
    "acoustic": False,
    "unplugged": False,
    "remix": False,
    "instrumental": False,
    "sped up": False,
    "slowed": False,
    "slowed + reverb": False,
    "nightcore": False,
    "cover": False,
    "tribute": False,
    "karaoke": False,
    "demo": False,
    "session": False,
}

HARD_REJECT_TAGS = {"live", "remix", "instrumental", "cover", "tribute", "karaoke", "demo"}

SOFT_ACCEPT_TAGS = {"remaster", "remastered", "deluxe", "radio edit", "radio version", "single version"}


def is_same_recording_allowed(version_tags: Set[str]) -> bool:
    for tag in version_tags:
        tag_lower = tag.lower()
        if tag_lower in HARD_REJECT_TAGS:
            return False
        if tag_lower in VERSION_POLICY and VERSION_POLICY[tag_lower] is False:
            # Check if it's in hard reject
            if tag_lower in HARD_REJECT_TAGS:
                return False
    return True


def get_policy_score_adjustment(version_tags: Set[str]) -> float:
    adjustment = 0.0
    for tag in version_tags:
        tag_lower = tag.lower()
        if tag_lower in HARD_REJECT_TAGS:
            return -1.0  # Hard penalty
        if tag_lower in SOFT_ACCEPT_TAGS:
            adjustment += 0.0  # Neutral/slight positive
    return adjustment
