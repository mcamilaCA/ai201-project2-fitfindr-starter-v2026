# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->
This system is meant to help find thrift items and simultaneously creating outfits and providing a quick caption to use in social media. It uses 'search_listings' to give individual items lists, 'suggest_outfit' to create the outfits based on item selected and wardrobe, and 'create_fit_card' which is where your social media caption comes from. 


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** It looks for items that match the provided description. Similar to a shopping assistant in a store. 
- **Inputs:** 'description' (string), 'size' (string), 'max_price' (float)
- **Returns:** A list of disctionaries that contains the outfit matches. For each piece of the outfit you get their  id, title, description, category, style_tags, size, condition, price, colors, brand, and platform. Similar to going to a fitting room with outfits and looking at the price tags of each outfit instead of trying them on. 
- **When it has nothing:** It returns an empty list 

### `suggest_outfit`

- **What it does:** Based on a determines piece of clothing, the system checks your wardrobe and finds potential outfit matches containing the piece of clothing you already selected. Pretty much like choosing your favorite shirt in a store and trying to match it with clothes you already own.
- **Inputs:** new_item (dictionary), and wardrobe (dictionary)
- **Returns:** A sentence (string) with the potential outfits you can wear
- **When it has nothing:** Gives you a default outfit, similar to when you are lazy and put in your comfy clothes 

### `create_fit_card`

- **What it does:** Gives you a ready-to-post caption in case you want to post on social media
- **Inputs:** 'outfit' (string), 'new_item' (dictionary)
- **Returns:** Two to four sentences of a potential caption for your outfit. 
- **When it has nothing:** If `outfit` is empty or whitespace, it returns a descriptive message string (e.g. explaining that no outfit was provided, so no fit card could be made) instead of raising or calling the model.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If search_listings returns an empty list, drop the "max_price" and call "search_listings" again. If there was a match, highlight the change to the user in session['notice'] and fit_card and provide the result. If no match was found, write a message in the session and stop.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** regex, in `parse_query()`. One pattern pulls `max_price` from phrases like "under $30", and one pulls `size` from "size M". Both are stripped out, and what's left is the description. The query is parsed once; a retry reuses the same description and size with `max_price=None`.

**What moves through the session:** `new_session()` takes an optional `relaxed` parameter, set to `"max_price"` when the retry drops the price limit. `session["parsed"]` keeps the user's original filters. The flow:
parsed (regex from raw query) -> search_results ->
1) if empty and a max_price was given -> search again with max_price=None -> if matched -> set session["relaxed"] = "max_price" and session["notice"] -> selected_item -> suggest_outfit -> fit card (notice is prepended)
2) if still empty -> session['error'] (built from `_suggest_changes`) -> return before any model call
3) if more than one result -> session["comparison"] (top 3 with price gap to the cheapest) -> printed by `app.py::_price_table`

A listing needs at least 2 keyword matches (`MIN_KEYWORD_MATCHES` in `tools.py`), so a query with too many unmatched words can reach the error path.


---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
python app.py ask 'vintage graphic tee under $1'                                  

```
Output: 

  Note:     Nothing matched under $1, so I searched again without the price limit. This result may cost more than youwanted.

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   * Pair the butterfly baby tee with the dark wash baggy straight-leg jeans, layered under the slightly cropped vintage black denim jacket, and finish with chunky white sneakers and the black crossbody bag for an effortless Y2K streetwear look.
* Tuck the baby tee into the wide-leg khaki trousers, add the brown leather belt at the waist, and wear the black combat boots to lean into a vintage, earth-toned aesthetic.

  Fit card: Nothing matched under $1, so I searched again without the price limit. This result may cost more than youwanted.

Scored this gorgeous pink and purple butterfly baby tee on Depop for just $18.00. 🦋 I'm styling it for an effortlessY2K streetwear look with dark wash baggy straight-leg jeans, a cropped vintage black denim jacket, and chunky white sneakers. 👖✨

#Y2KStreetwear #ThriftFinds

0 model calls this session, 2 served from cache

**The three tools, tested one at a time**

```
$ python3 -c "from tools import search_listings; print([(l['id'], l['title'], l['size'], l['price']) for l in search_listings('graphic tee', max_price=30)])"
[('lst_002', 'Y2K Baby Tee — Butterfly Print', 'S/M', 18.0), ('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 'L', 24.0), ('lst_017', 'Mesh Long-Sleeve Top — Black', 'S/M', 15.0), ('lst_033', 'Vintage Band Tee — Faded Grey', 'L', 19.0), ('lst_011', 'Low-Rise Cargo Pants — Khaki', 'W29', 27.0), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 'L', 26.0)]
```

```
$ python3 -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()).replace(chr(10), ' '))"
* Tuck the white ribbed tank top into the 501s, layer the oversized grey crewneck sweatshirt on top, and finish with chunky white sneakers and the black crossbody bag. * Pair the 501s with the black cropped zip hoodie, vintage black denim jacket, and black combat boots for an all-denim streetwear look.
```

```
$ python3 -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]).replace(chr(10), ' '))"
Scored these classic medium wash 501s on Depop for just $38.00 and I am fully leaning into that effortless 90s skater aesthetic today. 👖 I tossed them on with my favorite crisp white sneakers for that no-fuss, everyday cool-girl look. 👟 Honestly, the slight fading at the knees gives them that broken-in character you just can't fake. ✨  #VintageDenim #DepopFinds #StreetwearStyle
```

(The `.replace(chr(10), ' ')` just collapses the model's newlines so each tool's output is one line.)

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* Help for best designing parctices for outfit design 
- *What came back:* An explanation broken down in steps on things to consider
- *What I changed:* I made the designing decisions (what should a "relaxed" state run do, and what would happen if it did not return anything? What things could potentially break the code? which items can differ from one function to another in integration time and how to tackle it, etc)

**Moment 2**

- *What I asked for:*  I asked for running the program with several clothes parameters 
- *What came back:* output of the runs with some issues (item not found, or item found but the match made no sense)
- *What I changed:* adding stop words and a minimum score for matching criteria

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

|           Criterion             | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 |  Verdict  |
|---------------------------------|--------|-------|-------|-------|-------|-------|-----------|
| 1. matching query completes     | 4 of 5 |  PASS | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 2. impossible query stops early | 5 of 5 |  PASS | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 3. selected item id is correct  | 5 of 5 |  PASS | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 4. fit card at most 4 sentences | 4 of 5 |  PASS | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 5. relax run drops max_price    | 5 of 5 |  PASS | PASS  | PASS  | PASS  | PASS  | MET (5/5) |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

Criterion 5, try 1 (`jeans under $25`, example wardrobe). The trace comes from
`agent.py::run_agent` (loop, retry and notice), the Fit card from
`tools.py::create_fit_card`, and the run was driven by `run_eval.py::run_once`.

```
- stopped early: no
- selected_item: Vintage Levi's 501 Jeans — Medium Wash ($38.0, depop)
- search_results: 3

Outfit suggestion:
* Pair the medium wash Levi's 501s with the white ribbed tank top tucked in, layered under the slightly cropped vintage black denim jacket, and finish with the chunky white sneakers and black crossbody bag.
* Style the jeans with the oversized grey crewneck sweatshirt worn loose over the top, accessorized with the brown leather belt, and ground the look with the black combat boots.

Fit card:
Nothing matched under $25, so I searched again without the price limit. This result may cost more than you wanted.

Scored these vintage Levi's 501 jeans on depop for just $38.00 and they already have that perfect worn-in look. I am leaning fully into effortless 90s streetwear by wearing them with an oversized grey crewneck sweatshirt. A brown leather belt and black combat boots finish the slouchy vibe. 👟
#VintageDenim #DepopFinds #StreetwearStyle

Trace:
[1] parse_query
      in:  jeans under $25
      out: {'description': 'jeans', 'size': None, 'max_price': 25.0}
[2] search_listings (via MCP)
      in:  description='jeans', size=None, max_price=25.0
      out: [] (empty)
      →    empty — retrying without max_price
[3] search_listings (via MCP)
      in:  description='jeans', size=None, max_price=None
      out: 3 items: Vintage Levi's 501 Jeans — Medium Wash, Baggy Carpenter Jeans — Dark Wash, Straight Leg Black Jeans — Faded
[4] build_comparison
      in:  3 results
      out: 3 rows
      →    branch: more than one match, comparing prices
[5] suggest_outfit
      in:  item="Vintage Levi's 501 Jeans — Medium Wash", wardrobe_items=10
[6] create_fit_card
      in:  item="Vintage Levi's 501 Jeans — Medium Wash", outfit from step above
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | All five tries ran `search_listings`, `suggest_outfit` and `create_fit_card` and returned a fit card. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | All five tries returned no results, stopped before any model call, and the message listed what to change. |
| 3 | `selected_item` matches what `suggest_outfit` receives | 5 of 5 | MET (5/5) | In all five tries the selected item and the item in the `suggest_outfit` trace step were both "Denim Jacket — Light Wash, Cropped". The log shows titles, not ids. |
| 4 | Fit card caption is at most 4 sentences | 4 of 5 | MET (5/5) | I counted sentences in the five captions, excluding hashtags. Each had 3. |
| 5 | Relaxed retry drops `max_price` | 5 of 5 | MET (5/5) | In all five tries the first search was empty, the retry returned 3 results, and the "Nothing matched under $25" notice was prepended to the fit card. |

**Diagnoses**

No criterion missed, so there is no failure to diagnose. One earlier run (16:32) is not counted: the API key was rejected, every model call failed, and criteria 1 and 4 could not be measured. That was an environment problem, not a miss in the loop, a tool, the session or the model's output. After fixing the key I reran, and the table above is from that run.

Two limits on these results. Criterion 3 was checked by item title because the log doesn't print ids. Criterion 4 had only five captions, all at 3 sentences, so it doesn't show the model can't run over 4 at temperature 0.9.



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 5 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +2 more
[3] build_comparison
      in:  5 results
      out: 3 rows
      →    branch: more than one match, comparing prices
[4] suggest_outfit
      in:  item='Y2K Baby Tee — Butterfly Print', wardrobe_items=10
      out: * Pair the butterfly baby tee with the dark wash baggy straight-leg jeans, layered under the slightly cropped …
[5] create_fit_card
      in:  item='Y2K Baby Tee — Butterfly Print', outfit from step above
      out: Scored this gorgeous pink and purple butterfly baby tee on Depop for just $18.00. 🦋 I'm styling it for an effo…
```

**Empty search**

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  description='designer ballgown', size=XXS, max_price=5.0
      out: [] (empty)
      →    empty — retrying without max_price
[3] search_listings (via MCP)
      in:  description='designer ballgown', size=XXS, max_price=None
      out: [] (empty)
      →    empty — nothing left to relax
[4] branch: no results
      out: 3 items: description: no listing contains 'ballgown', 'designer'. Che…
      →    stopping before any model call; fit_card stays None
```

**On the MCP move:** I moved `search_listings` (only that one tool) behind an MCP server. In `mcp_server.py` I registered it with `@mcp.tool()`, typed the inputs (`description: str`, `size: str | None`, `max_price: float | None`) and gave it a docstring that says what it returns, including the empty-list case. The function just calls the real implementation in `tools.py`, imported under an alias so the tool doesn't call itself. In `agent.py`, the direct `search_listings(...)` call in the loop was replaced with `mcp_client.call_tool("search_listings", {...})`. The old call is left commented out above it.

Nothing about the results changed: the call returns the same list of dicts, so the retry-without-price branch, the empty-search branch and the price comparison all work as before. The trace labels the step `search_listings (via MCP)` so the hop is visible. The one thing that behaved differently was the environment. Running the app with the system `python3` fails with `MCPError: Couldn't call 'search_listings' over MCP: No module named 'mcp'`, because the `mcp` package is only installed in the project's `.venv`. The server is started as a subprocess on every call, so it needs the same environment as the agent. Running with `.venv/bin/python app.py ...` works.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## Stretch Features:

### 1. Price Comparison

When a search returns two or more listings, `python app.py ask` prints a table comparing the top 3 results between the found item and the outfit suggestion. The table is formatted by `_price_table()` in `app.py` from `session["comparison"]`, which the second branch below fills. It adds no tool calls and no model calls.

```
  Price comparison (top 3):
  #  title                                      price  vs cheapest size        condition   platform
  ----------------------------------------------------------------------------------------------------
  1  Y2K Baby Tee — Butterfly Print             18.00  cheapest    S/M         excellent   depop
  2  Graphic Tee — 2003 Tour Bootleg Style      24.00  +$6.00      L           good        depop
  3  Vintage Band Tee — Faded Grey              19.00  +$1.00      L           fair        depop
```

- Rows keep the search ranking (best match first), not price order. The **vs cheapest** column shows the price gap.
- With fewer than two results there is nothing to compare, so the table is skipped.
- It only appears in the CLI `ask` output. The agent's `_show()` and the eval output are unchanged.

### 2. Second Branch: Compare When More Than One Match

**Branch rule:** If `search_listings` returns more than one listing, build a price comparison of the top 3 and put it in `session["comparison"]`. If exactly one matched, there is nothing to compare, so `session["comparison"]` stays empty. Either way the loop goes on to `suggest_outfit` with the first result. If nothing matched, the first branch (the empty-search error) has already returned, so this one never runs.

**Where it lives:** `agent.py::run_agent`, with the rows built by `agent.py::build_comparison`. It sits after the empty-search branch and before `suggest_outfit`.

Each row holds `rank`, `title`, `price`, `vs_cheapest`, `size`, `condition` and `platform`. I checked all three paths without the model:

| Query | Results | `session["comparison"]` | Error |
|---|---|---|---|
| vintage graphic tee under $30 | 5 | 3 rows | no |
| (one listing matched) | 1 | empty | no |
| designer ballgown size XXS under $5 | 0 | empty | yes, stopped before any model call |

### 3. Style Memory

The wardrobe is saved to `data/my_wardrobe.json` (gitignored — it's the user's own closet), so it carries over between runs. The logic is in `wardrobe_store.py`; `run_agent` and the three tools are unchanged, because the saved file has the same shape as the example wardrobe.

```
python app.py wardrobe                                   show what's saved
python app.py wardrobe seed                              start from the 10-item example wardrobe
python app.py wardrobe add 'Red cardigan' --category tops --colors red --tags vintage,cozy
python app.py wardrobe remove w_003                      by id or by name
python app.py wardrobe clear
python app.py ask 'vintage graphic tee under $30' --save add the item you find to your wardrobe
```

- **Which wardrobe `ask` uses:** `--empty-wardrobe` -> an empty one; otherwise the saved wardrobe if there is one; otherwise the example wardrobe (the old behaviour). It prints `(using your saved wardrobe: N items)` when it loads one.
- **`--save`:** after a successful search, the selected listing becomes a wardrobe item (title, category, colors, style tags, and a note with the platform and price) with the next `w_NNN` id. With no saved wardrobe it starts a new empty one instead of copying the example. It saves nothing when the search failed, and refuses duplicate names.
- **Failure handling:** a missing, corrupt or wrongly-shaped file is treated as "nothing saved" instead of crashing, and a read never overwrites it. Writes go through a temp file and a rename, so a crash can't leave a half-written wardrobe.
- **Not touched:** `run_eval.py` and `serve.py` still use the example/empty wardrobes, so eval runs stay repeatable and don't depend on whatever one person has saved.

Checked without the model: add, duplicate name, bad category, remove by id/name, seed (and refusing to overwrite without `--force`), clear, a corrupt file, and `--save` after a no-match query (saves nothing). Checked with the model: `ask ... --save` saved `w_001`, the next `ask` loaded it, and saving the same item again was rejected.



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
