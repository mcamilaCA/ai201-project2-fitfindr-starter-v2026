#!/usr/bin/env python3
"""
FitFindr — command line.

    python app.py ask 'vintage graphic tee under $30, size M'
    python app.py ask                     keep asking until you quit
    python app.py ask --empty-wardrobe    run as a user with nothing saved
    python app.py listings                browse the data  (Milestone 1)
    python app.py fields                  what fields a listing has
    python app.py examples                queries worth trying, including a dud
    python app.py wardrobe                show your saved wardrobe (style memory)
    python app.py ask '...' --save        keep the item you find in that wardrobe

Add --trace to any `ask` to print the loop step by step.

⚠️ Quote your query with SINGLE quotes. In PowerShell, "under $30" in double
quotes silently becomes "under " — PowerShell reads $30 as a variable and
substitutes nothing, so you search with no price ceiling and get no error
telling you why. Single quotes are literal in PowerShell, bash and zsh alike.
"""

import argparse
import sys

import config

# Every query here except the last one has something real to find in
# data/listings.json. If you add your own, check it against the data first — a
# query that finds nothing because the item doesn't exist looks exactly like a
# search tool that's broken.
EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "silk slip dress in midi length under $40",
    "platform sneakers size 8",
    "denim jacket under $50",
    "designer ballgown size XXS under $5",   # matches nothing, on purpose
]


def cmd_fields(args):
    """Milestone 1 — you can't filter on a field that isn't there."""
    from utils.data_loader import load_listings, get_example_wardrobe

    listing = load_listings()[0]
    print("A listing has these fields:\n")
    for key, value in listing.items():
        shown = str(value)
        if len(shown) > 58:
            shown = shown[:58] + "…"
        print(f"  {key:<14} {type(value).__name__:<6} {shown}")

    item = get_example_wardrobe()["items"][0]
    print("\nA wardrobe item has these fields:\n")
    for key, value in item.items():
        shown = str(value)
        if len(shown) > 58:
            shown = shown[:58] + "…"
        print(f"  {key:<14} {type(value).__name__:<6} {shown}")

    print(
        "\nThese are what search_listings can filter on. Read a few whole "
        "listings\nwith `python app.py listings` before you write it."
    )


def cmd_listings(args):
    """Milestone 1 — read the data before you write tools against it."""
    from utils.data_loader import load_listings

    listings = load_listings()

    if args.full:
        import json
        for listing in listings[: args.n]:
            print(json.dumps(listing, indent=2))
            print()
        return

    print(f"{len(listings)} listings.\n")
    print(f"{'id':<6}{'price':>8}  {'size':<22}{'platform':<11}title")
    print("-" * 92)
    for listing in listings[: args.n]:
        print(
            f"{str(listing['id']):<6}"
            f"{listing['price']:>8.2f}  "
            f"{str(listing['size']):<22}"
            f"{listing['platform']:<11}"
            f"{listing['title'][:38]}"
        )
    if len(listings) > args.n:
        print(f"\n… {len(listings) - args.n} more. Use -n {len(listings)} to see them all.")
    print("\nRead five or six all the way through: python app.py listings --full -n 6")


def cmd_examples(args):
    print("Queries worth trying:\n")
    for query in EXAMPLE_QUERIES[:-1]:
        print(f"  python app.py ask '{query}'")
    print(f"\nAnd one the data cannot match — this is the empty-search branch:\n")
    print(f"  python app.py ask '{EXAMPLE_QUERIES[-1]}'")
    print(
        "\nSingle quotes on purpose. In PowerShell a query in \"double quotes\"\n"
        "loses the $30 — it gets read as a variable — and you search with no\n"
        "price ceiling, with nothing to tell you it happened."
    )


def _price_table(rows):
    """Format session["comparison"] rows as a table. Empty rows -> empty string."""
    if not rows:
        return ""
    lines = [
        f"  {'#':<3}{'title':<40}{'price':>8}  {'vs cheapest':<12}{'size':<12}{'condition':<12}platform",
        "  " + "-" * 100,
    ]
    for r in rows:
        vs = "cheapest" if r["vs_cheapest"] == 0 else f"+${r['vs_cheapest']:.2f}"
        title = r["title"] if len(r["title"]) <= 38 else r["title"][:37] + "…"
        lines.append(
            f"  {r['rank']:<3}{title:<40}{r['price']:>8.2f}  {vs:<12}"
            f"{str(r['size'])[:11]:<12}{str(r['condition'] or '-')[:11]:<12}{r['platform']}"
        )
    return "\n".join(lines)


def _ask_one(query, wardrobe, use_trace):
    from agent import run_agent
    import trace as trace_module

    if use_trace:
        trace_module.start_trace()

    session = run_agent(query, wardrobe)

    print()
    if session["error"]:
        print(f"  {session['error']}")
    else:
        if session["notice"]:
            print(f"  Note:     {session['notice']}")
            print()
        item = session["selected_item"] or {}
        print(f"  Found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
        table = _price_table(session["comparison"])
        if table:
            print()
            print("  Price comparison (top 3):")
            print(table)
        print()
        print(f"  Outfit:   {session['outfit_suggestion']}")
        print()
        print(f"  Fit card: {session['fit_card']}")
    print()

    if use_trace:
        text = trace_module.get_trace()
        if not text:
            print(
                "  (--trace printed nothing. You haven't added trace.step() calls to\n"
                "   run_agent() yet — that's unit 4, Milestone 2.)\n"
            )
    return session


def _save_found_item(session, wardrobe):
    """--save: add the item the run found to the saved wardrobe (style memory)."""
    import wardrobe_store

    item = session["selected_item"]
    if session["error"] or not item:
        print("  (--save: nothing was found, so nothing was saved)\n")
        return
    try:
        stored = wardrobe_store.add_item(wardrobe, wardrobe_store.listing_to_item(item))
    except ValueError as exc:
        print(f"  (--save: {exc})\n")
        return
    wardrobe_store.save_wardrobe(wardrobe)
    print(f"  Saved {stored['id']} \"{stored['name']}\" to your wardrobe "
          f"({len(wardrobe['items'])} items).\n")


def cmd_ask(args):
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe
    import generate
    import wardrobe_store

    if args.empty_wardrobe:
        wardrobe = get_empty_wardrobe()
        print("(running with an empty wardrobe)")
    else:
        wardrobe = wardrobe_store.load_wardrobe()
        if wardrobe is not None:
            print(f"(using your saved wardrobe: {len(wardrobe['items'])} items)")
        else:
            wardrobe = get_example_wardrobe()
            if args.save:
                # --save needs somewhere to save to: start a new, empty closet
                wardrobe = get_empty_wardrobe()
                print("(no saved wardrobe yet — starting one; --save will add what you find)")

    try:
        if args.query:
            session = _ask_one(args.query, wardrobe, args.trace)
            if args.save:
                _save_found_item(session, wardrobe)
        else:
            print("Ask for something, or press Enter on an empty line to quit.\n")
            while True:
                try:
                    query = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if not query:
                    break
                session = _ask_one(query, wardrobe, args.trace)
                if args.save:
                    _save_found_item(session, wardrobe)
    finally:
        print(generate.usage())


def cmd_wardrobe(args):
    """Style memory — view and edit the wardrobe saved between runs."""
    import wardrobe_store as store
    from utils.data_loader import get_example_wardrobe

    wardrobe = store.load_wardrobe()

    if args.action == "seed":
        if wardrobe is not None and wardrobe["items"] and not args.force:
            print(f"You already have {len(wardrobe['items'])} saved items. "
                  "Use --force to replace them with the example wardrobe.")
            return
        store.save_wardrobe(get_example_wardrobe())
        print("Saved the example wardrobe (10 items). Edit it with add / remove.")
        return

    if args.action == "clear":
        if wardrobe is None:
            print("Nothing saved.")
            return
        store.save_wardrobe({"items": []})
        print("Wardrobe cleared.")
        return

    if wardrobe is None:
        wardrobe = {"items": []}

    if args.action == "add":
        if not args.name or not args.category:
            raise SystemExit("add needs a name and --category, e.g. "
                             "python app.py wardrobe add 'Red cardigan' --category tops")
        stored = store.add_item(wardrobe, {
            "name": args.name,
            "category": args.category,
            "colors": [c.strip() for c in args.colors.split(",") if c.strip()],
            "style_tags": [t.strip() for t in args.tags.split(",") if t.strip()],
            "notes": args.notes,
        })
        store.save_wardrobe(wardrobe)
        print(f"Added {stored['id']} \"{stored['name']}\" ({len(wardrobe['items'])} items).")
    elif args.action == "remove":
        if not args.name:
            raise SystemExit("remove needs an id or name, e.g. python app.py wardrobe remove w_003")
        try:
            gone = store.remove_item(wardrobe, args.name)
        except KeyError as exc:
            raise SystemExit(str(exc).strip("'\""))
        store.save_wardrobe(wardrobe)
        print(f"Removed {gone['id']} \"{gone['name']}\" ({len(wardrobe['items'])} items left).")
    else:  # show
        if not wardrobe["items"]:
            print("No saved wardrobe yet. Start one with:\n"
                  "  python app.py wardrobe seed                 (copy the example wardrobe)\n"
                  "  python app.py wardrobe add 'Name' --category tops\n"
                  "  python app.py ask '...' --save              (keep what you find)")
            return
        print(f"{len(wardrobe['items'])} saved items  ({store.WARDROBE_PATH})\n")
        print(f"  {'id':<7}{'category':<12}{'name':<44}colors")
        print("  " + "-" * 80)
        for it in wardrobe["items"]:
            print(f"  {it['id']:<7}{it['category']:<12}{it['name'][:42]:<44}{', '.join(it['colors'])}")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="FitFindr",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fields = sub.add_parser("fields", help="what fields the data has")
    p_fields.set_defaults(func=cmd_fields)

    p_list = sub.add_parser("listings", help="browse the listings data")
    p_list.add_argument("-n", type=int, default=15, help="how many to show")
    p_list.add_argument("--full", action="store_true", help="print whole records")
    p_list.set_defaults(func=cmd_listings)

    p_ex = sub.add_parser("examples", help="queries worth trying")
    p_ex.set_defaults(func=cmd_examples)

    p_ask = sub.add_parser("ask", help="run the agent")
    p_ask.add_argument("query", nargs="?")
    p_ask.add_argument("--trace", action="store_true", help="print the loop step by step")
    p_ask.add_argument(
        "--empty-wardrobe",
        action="store_true",
        help="run as a user with nothing saved — one of unit 4's failure modes",
    )
    p_ask.add_argument(
        "--save",
        action="store_true",
        help="add the item you find to your saved wardrobe (style memory)",
    )
    p_ask.set_defaults(func=cmd_ask)

    p_w = sub.add_parser("wardrobe", help="view or edit the wardrobe saved between runs")
    p_w.add_argument("action", nargs="?", default="show",
                     choices=["show", "add", "remove", "seed", "clear"])
    p_w.add_argument("name", nargs="?", help="item name (add) or id/name (remove)")
    p_w.add_argument("--category", help="tops, bottoms, outerwear, shoes or accessories")
    p_w.add_argument("--colors", default="", help="comma-separated")
    p_w.add_argument("--tags", default="", help="comma-separated style tags")
    p_w.add_argument("--notes", default=None)
    p_w.add_argument("--force", action="store_true", help="seed: replace existing items")
    p_w.set_defaults(func=cmd_wardrobe)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001 — students read this, not a traceback
        print(f"\n{type(exc).__name__}: {exc}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
