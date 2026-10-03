"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py            runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card, unmatched_keywords
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict, relaxed: str | None = None) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        "relaxed": relaxed,          # set when the retry dropped a filter, e.g. "max_price"
        "notice": None,              # user-facing message about the relaxed retry
        "suggestions": [],           # which fields to change when nothing matched
    }


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE_RE = re.compile(
    r"\b(?:under|below|less than|max(?:imum)?|up to)\s*\$?\s*(\d+(?:\.\d+)?)(?:\s*(?:dollars?|bucks|usd)\b)?"
    r"|\$\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE_RE = re.compile(r"\bsize\s+([A-Za-z0-9/]+)", re.IGNORECASE)


def parse_query(query: str) -> dict:
    """Regex-parse a plain-language query into description / size / max_price."""
    max_price = None
    size = None
    description = query

    m = _PRICE_RE.search(description)
    if m:
        max_price = float(m.group(1) or m.group(2))
        description = description.replace(m.group(0), " ")

    m = _SIZE_RE.search(description)
    if m:
        size = m.group(1)
        description = description.replace(m.group(0), " ")

    description = re.sub(r"[,;]+", " ", description)
    description = re.sub(r"\s+", " ", description).strip()
    return {"description": description, "size": size, "max_price": max_price}


def _suggest_changes(parsed: dict) -> list[str]:
    """Work out which field(s) to change after a search with every filter relaxed that still failed."""
    suggestions = []
    description, size = parsed["description"], parsed["size"]

    # Size: would dropping it produce a match?
    if size is not None:
        without_size = search_listings(description, None, None)
        if without_size:
            sizes = sorted({r["size"] for r in without_size})
            suggestions.append(
                f"size: nothing matched in size {size}, but \"{description}\" exists in "
                f"{', '.join(sizes[:5])}. Try one of those sizes or leave size out."
            )
            return suggestions

    # Description: otherwise the words are the problem.
    unknown = unmatched_keywords(description)
    if unknown:
        suggestions.append(
            f"description: no listing contains {', '.join(repr(w) for w in unknown)}. "
            "Check the spelling or replace it with a more general word."
        )
    suggestions.append(
        "description: use fewer, broader words (e.g. the item type like 'tee' or "
        "'jacket' plus one style word) — a listing needs at least 2 of your keywords."
    )
    if parsed["max_price"] is not None:
        suggestions.append("max_price: raising it won't help — nothing matched even with no price limit.")
    return suggestions


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    count = 0

    # Parse once from the raw query. session["parsed"] keeps the user's original
    # filters, even after a retry drops one — session["relaxed"] records that.
    session["parsed"] = parse_query(query)

    # Attempt 1 uses every filter. Attempt 2 (the branch) drops max_price —
    # but only if there was a max_price to drop.
    attempts = [session["parsed"]["max_price"]]
    if session["parsed"]["max_price"] is not None:
        attempts.append(None)

    for max_price in attempts:
        count += 1
        trace.check_iterations(count)

        session["search_results"] = search_listings(
            session["parsed"]["description"], session["parsed"]["size"], max_price
        )
        if session["search_results"]:
            if max_price is None and session["parsed"]["max_price"] is not None:
                session["relaxed"] = "max_price"
                session["notice"] = (
                    f"Nothing matched under ${session['parsed']['max_price']:g}, so I "
                    "searched again without the price limit. This result may cost "
                    "more than you wanted."
                )
            break

    # THE BRANCH: nothing matched even after relaxing — stop before any model call.
    if not session["search_results"]:
        p = session["parsed"]
        tried = f" under ${p['max_price']:g}" if p["max_price"] is not None else ""
        size = f" in size {p['size']}" if p["size"] else ""
        session["suggestions"] = _suggest_changes(p)
        session["error"] = (
            f"No match was found for \"{p['description']}\"{size}{tried}"
            f"{', even without the price limit' if p['max_price'] is not None else ''}. What to change:\n- "
            + "\n- ".join(session["suggestions"])
        )
        return session

    session["selected_item"] = session["search_results"][0]

    try:
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"], session["wardrobe"]
        )
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )
        if session["notice"]:
            session["fit_card"] = f"{session['notice']}\n\n{session['fit_card']}"
    except ModelUnavailable as e:
        session["error"] = f"The model isn't available right now: {e}"
    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    if session["notice"]:
        print(f"  note:     {session['notice']}")
    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
