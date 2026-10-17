"""Semantic domains for asset matching (fill + stock fetch).

Keeps product/software narration from landing on residential B-roll,
and vice versa.
"""
from __future__ import annotations

PLACE = {
    "community", "neighborhood", "house", "home", "street", "suburban",
    "residential", "aerial", "town", "city", "live", "place", "cottage",
    "lawn", "yard", "driveway", "skyline", "family", "suburbs",
}
SOFTWARE = {
    "editor", "editing", "timeline", "software", "screen", "ui", "app",
    "interface", "desktop", "monitor", "workspace", "laptop", "keyboard",
    "code", "script", "microphone", "desk", "creator", "product", "atlas",
    "storyboard", "waveform", "pacing", "reference", "style", "dna",
    "package", "review", "notes", "feedback", "lock", "locked", "beat",
    "caption", "render", "pipeline", "office", "computer", "macbook",
}
NATURE = {
    "forest", "tree", "fog", "pond", "water", "mountain", "park", "bench",
}


def tokens(text: str) -> set:
    import re
    return set(re.findall(r"[a-z0-9]{3,}", (text or "").lower()))


def domains_of(toks: set) -> set:
    d = set()
    if toks & PLACE:
        d.add("place")
    if toks & SOFTWARE:
        d.add("software")
    if toks & NATURE:
        d.add("nature")
    return d


def domain_mismatch_penalty(query: str, asset_text: str) -> float:
    """Negative score when query and asset live in different worlds."""
    q = domains_of(tokens(query))
    a = domains_of(tokens(asset_text))
    if not q or not a:
        return 0.0
    if "software" in q and ("place" in a or "nature" in a):
        return -8.0
    if "place" in q and "software" in a:
        return -4.0
    if q & a:
        return 4.0  # bonus
    return 0.0


def is_software_query(query: str) -> bool:
    return "software" in domains_of(tokens(query))


def is_place_query(query: str) -> bool:
    return "place" in domains_of(tokens(query))
