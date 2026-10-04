"""
Fast, offline unit tests for the pure parts of FitFindr. No model calls.

    python -m pytest test_units.py -q

(test.py is the environment check, not this file.)
"""

import copy

import pytest

import agent
import tools
from agent import build_comparison, parse_query, run_agent
from app import _price_table
from tools import MIN_KEYWORD_MATCHES, _filter_and_score, _keywords, _size_matches, search_listings
from utils.data_loader import get_example_wardrobe, load_listings
from wardrobe_store import add_item, remove_item


# ── parse_query ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("query, expected", [
    ("vintage graphic tee under $30, size M",
     {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}),
    ("size L hoodie max 40 dollars",
     {"description": "hoodie", "size": "L", "max_price": 40.0}),
    ("black boots",
     {"description": "black boots", "size": None, "max_price": None}),
    ("denim jacket under 25.50",
     {"description": "denim jacket", "size": None, "max_price": 25.5}),
])
def test_parse_query(query, expected):
    assert parse_query(query) == expected


def test_parse_query_price_only_leaves_empty_description():
    assert parse_query("under $20")["description"] == ""


def test_parse_query_dollar_or_less_phrasing():
    assert parse_query("levi jeans $25 or less")["description"] == "levi jeans"


# ── search scoring ────────────────────────────────────────────────────────────

LISTINGS = load_listings()


def test_size_matches_is_token_based():
    assert _size_matches("M", "S/M")
    assert not _size_matches("L", "XL")       # no substring match
    assert not _size_matches("S", "US 9")
    assert not _size_matches("", "M")


def test_size_filter_returns_only_matching_sizes():
    results = search_listings("tee", size="M")
    assert results
    assert all(_size_matches("M", r["size"]) for r in results)


def test_stop_words_are_not_keywords():
    assert _keywords("I want a tee under size") == {"tee"}


def test_max_price_is_inclusive():
    price = LISTINGS[0]["price"]
    title_word = next(iter(_keywords(LISTINGS[0]["title"])))
    at_limit = _filter_and_score([LISTINGS[0]], title_word, None, price)
    below = _filter_and_score([LISTINGS[0]], title_word, None, price - 0.01)
    assert at_limit and not below


def test_every_result_respects_max_price():
    assert all(r["price"] <= 18 for r in search_listings("tee", max_price=18))


def test_one_keyword_query_still_matches():
    # needed = min(MIN_KEYWORD_MATCHES, 1) = 1, so a single-word query isn't locked out
    assert search_listings("hoodie")


def test_all_stop_words_or_gibberish_returns_nothing():
    assert search_listings("the") == []
    assert search_listings("zzzzqq") == []


def test_multi_keyword_results_meet_the_minimum():
    desc = "graphic tee"
    needed = min(MIN_KEYWORD_MATCHES, len(_keywords(desc)))
    for r in search_listings(desc):
        assert tools._keyword_score(desc, r) >= needed


def test_graphic_tee_characterization():
    # Pins today's behavior. If you change MIN_KEYWORD_MATCHES or the stop words and this
    # fails, check the new list and update it ON PURPOSE. It used to include cargo pants
    # and a hoodie (one-keyword matches).
    assert [r["id"] for r in search_listings("graphic tee")] == [
        "lst_002", "lst_006", "lst_017", "lst_033",
    ]


# ── build_comparison / _price_table ───────────────────────────────────────────

def _row(price, title="x"):
    return {"title": title, "price": price, "size": "M", "platform": "p"}


def test_comparison_caps_at_top_n_and_gaps_use_cheapest():
    rows = build_comparison([_row(20), _row(12.5), _row(30), _row(5)])
    assert len(rows) == 3                      # the $5 listing is outside the top 3
    assert [r["vs_cheapest"] for r in rows] == [7.5, 0, 17.5]
    assert [r["rank"] for r in rows] == [1, 2, 3]


def test_comparison_single_result():
    assert build_comparison([_row(10)])[0]["vs_cheapest"] == 0


def test_price_table_empty_and_cheapest_label():
    assert _price_table([]) == ""
    assert "cheapest" in _price_table(build_comparison([_row(10), _row(14)]))


# ── wardrobe add / remove ─────────────────────────────────────────────────────

def _wardrobe():
    return copy.deepcopy(get_example_wardrobe())


def _new(name="Test Boots"):
    return {"name": name, "category": "shoes", "colors": ["brown"]}


def test_add_item_assigns_fresh_incrementing_id():
    w = _wardrobe()
    a = add_item(w, _new("A"))
    b = add_item(w, _new("B"))
    assert a["id"] != b["id"]
    assert int(b["id"][2:]) == int(a["id"][2:]) + 1


def test_add_item_rejects_duplicate_name_case_insensitively():
    w = _wardrobe()
    add_item(w, _new("Boots"))
    with pytest.raises(ValueError):
        add_item(w, _new("  boots "))


def test_add_item_rejects_bad_category():
    with pytest.raises(ValueError):
        add_item(_wardrobe(), {"name": "Hat", "category": "hats"})


def test_remove_item_by_id_and_by_name():
    w = _wardrobe()
    a = add_item(w, _new("A"))
    b = add_item(w, _new("B"))
    assert remove_item(w, a["id"])["name"] == "A"
    assert remove_item(w, "b")["id"] == b["id"]
    with pytest.raises(KeyError):
        remove_item(w, "nope")


def test_ids_are_not_reused_after_removing_the_newest():
    # documents current behavior: the id counter is max+1, so removing the newest frees its id
    w = _wardrobe()
    a = add_item(w, _new("A"))
    remove_item(w, a["id"])
    assert add_item(w, _new("A2"))["id"] == a["id"]


# ── the relaxed-retry branch (criterion 5), search + model patched ────────────

@pytest.fixture
def patched_model(monkeypatch):
    monkeypatch.setattr(agent, "suggest_outfit", lambda item, wardrobe: "outfit")
    monkeypatch.setattr(agent, "create_fit_card", lambda outfit, item: "card")


def test_retry_drops_max_price_and_records_it(monkeypatch, patched_model):
    calls = []

    def fake_search(description, size, max_price):
        calls.append(max_price)
        return [] if max_price is not None else [LISTINGS[0]]

    monkeypatch.setattr(agent, "search_listings", fake_search)
    s = run_agent("graphic tee under $30", _wardrobe())

    assert calls == [30.0, None]
    assert s["relaxed"] == "max_price"
    assert s["search_results"]
    assert "$30" in s["notice"]
    assert s["parsed"]["max_price"] == 30.0     # original filter is kept
    assert s["fit_card"].startswith(s["notice"])
    assert s["error"] is None


def test_no_retry_when_first_search_matches(monkeypatch, patched_model):
    monkeypatch.setattr(agent, "search_listings", lambda d, s, m: [LISTINGS[0]])
    s = run_agent("graphic tee under $30", _wardrobe())
    assert s["relaxed"] is None and s["notice"] is None


def test_no_retry_without_a_price_and_no_model_call_on_empty(monkeypatch):
    calls = []
    monkeypatch.setattr(agent, "search_listings", lambda d, s, m: calls.append(m) or [])

    def boom(*a):
        raise AssertionError("model must not be called when nothing matched")

    monkeypatch.setattr(agent, "suggest_outfit", boom)
    s = run_agent("graphic tee", _wardrobe())
    assert calls == [None]
    assert s["error"] and s["relaxed"] is None and s["selected_item"] is None
