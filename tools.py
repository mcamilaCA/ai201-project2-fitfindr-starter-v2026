"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


def _tokenize(text: str) -> set[str]:
    # lowercase word/number chunks, used for both size and keyword matching
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _size_matches(query_size: str, listing_size: str) -> bool:
    # token subset match: "M" -> {"m"} must be subset of "S/M" -> {"s","m"}
    # avoids substring bugs like "s" in "us 9" or "l" in "xl"
    query_tokens = _tokenize(query_size)
    listing_tokens = _tokenize(listing_size)
    return bool(query_tokens) and query_tokens.issubset(listing_tokens)


def _keyword_score(description: str, listing: dict) -> int:
    # raw overlap count between description words and the listing's text
    query_tokens = _tokenize(description)
    listing_text = " ".join([
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("category", ""),
        " ".join(listing.get("style_tags") or []),
        listing.get("brand") or "",
    ])
    return len(query_tokens & _tokenize(listing_text))


def _filter_and_score(
    listings: list[dict],
    description: str,
    size: str | None,
    max_price: float | None,
) -> list[dict]:
    # shared by the strict pass and the relaxed (no max_price) retry
    candidates = listings
    if max_price is not None:
        candidates = [l for l in candidates if l["price"] <= max_price]
    if size is not None:
        candidates = [l for l in candidates if _size_matches(size, l["size"])]

    scored = [(_keyword_score(description, l), l) for l in candidates]
    scored = [pair for pair in scored if pair[0] > 0]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [l for _, l in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    listings = load_listings()

    strict = _filter_and_score(listings, description, size, max_price)
    if strict:
        return strict

    # relaxed retry: drop max_price only, keep size + keyword requirements
    if max_price is not None:
        return _filter_and_score(listings, description, size, None)

    return []


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

_SUGGEST_OUTFIT_SYSTEM = (
    "You are a styling assistant for a thrift-finds app. A user is "
    "considering buying a secondhand item and wants outfit ideas. Respond "
    "with a short paragraph, or a list of up to 4 bullet points — never more "
    "than 4. Each bullet is one complete outfit, not a single piece. Be "
    "concrete: name colors, categories, and specific pieces when they're "
    "given to you."
)


def _describe_item(item: dict) -> str:
    # shared by both prompt builders below — brand is often None, so it's
    # left out rather than printed as "Brand: None"
    colors = ", ".join(item.get("colors") or [])
    style_tags = ", ".join(item.get("style_tags") or [])
    lines = [
        f"Item: {item.get('title')}",
        f"Category: {item.get('category')}",
        f"Colors: {colors}",
        f"Style: {style_tags}",
    ]
    if item.get("description"):
        lines.append(f"Description: {item['description']}")
    return "\n".join(lines)


def _format_wardrobe_items(items: list[dict]) -> str:
    # one line per item, not grouped by category — layering a look can mix
    # categories (top + top, top + bottom), and a flat list lets the model
    # combine any of them freely instead of picking one per group
    lines = []
    for item in items:
        colors = ", ".join(item.get("colors") or [])
        style_tags = ", ".join(item.get("style_tags") or [])
        line = f"- {item['name']} ({item['category']}; colors: {colors}; style: {style_tags})"
        if item.get("notes"):
            line += f" — {item['notes']}"
        lines.append(line)
    return "\n".join(lines)


def _build_specific_prompt(new_item: dict, items: list[dict]) -> str:
    return (
        f"{_describe_item(new_item)}\n\n"
        f"Here's what they already own:\n{_format_wardrobe_items(items)}\n\n"
        "Suggest 1-2 outfits that pair this item with pieces from their "
        "wardrobe. You may combine multiple tops, bottoms, or layers from "
        "the list to build a look."
    )


def _build_general_prompt(new_item: dict) -> str:
    return (
        f"{_describe_item(new_item)}\n\n"
        "This user doesn't have a wardrobe on file yet. Suggest general "
        "styling directions for this item — what colors, categories, or "
        "styles would pair well — without assuming specific pieces they own."
    )


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = wardrobe["items"]
    # branch on what's available to build on: a wardrobe to combine with, or
    # just the item on its own
    if items:
        prompt = _build_specific_prompt(new_item, items)
    else:
        prompt = _build_general_prompt(new_item)
    return generate(prompt, system=_SUGGEST_OUTFIT_SYSTEM)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

_FIT_CARD_SYSTEM = (
    "You write short social media captions for a thrift-finds app. The user "
    "just found a secondhand item and wants a ready-to-post caption about it.\n\n"
    "Rules:\n"
    "- Write 2 to 4 sentences, in the first person, like a real post — not a "
    "product description.\n"
    "- Mention the item, its exact price (e.g. \"$18.00\"), and the platform it "
    "was found on, each exactly once.\n"
    "- Pick ONE look from the outfit ideas and build the caption around it. Do "
    "not list or summarize several outfits.\n"
    "- Commit to a specific vibe (name the mood, era, or aesthetic) instead of "
    "generic praise.\n"
    "- Use at most 1 emoji per sentence.\n"
    "- You may end with 1 to 3 hashtags on their own final line. Hashtags are "
    "optional and are not part of the sentence count.\n"
    "- Output only the caption. No quotes around it, no preamble like \"Here's "
    "your caption\"."
)


def _build_fit_card_prompt(outfit: str, new_item: dict) -> str:
    # price is formatted here, not left to the model, so the exact dollar
    # amount is guaranteed to be in the prompt
    return (
        f"{_describe_item(new_item)}\n"
        f"Price: ${new_item.get('price', 0):.2f}\n"
        f"Platform: {new_item.get('platform')}\n\n"
        f"Outfit ideas:\n{outfit}\n\n"
        "Write the caption."
    )

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return (
            "No outfit was provided, so a fit card couldn't be made. "
            "Get outfit suggestions for this item first, then try again."
        )
    return generate(_build_fit_card_prompt(outfit, new_item), system=_FIT_CARD_SYSTEM).strip()
