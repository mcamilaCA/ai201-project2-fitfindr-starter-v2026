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
This system is meant to help find thrift items and simmultaneously creating outfits and providing a quick caption to use in social media. It uses 'search_listings' to give individual items lists, 'outfit_suggest' to create the outfits based on item selected and wardrobe, and 'create_fit_card' which is where your social media caption comes from. 


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

**Branch rule:** If search_listings returns an empty string, drop the tightest filter (in most cases this will be "max_price") and call "search_listings" again. If there was a match, highlight the change to the user and provide the result. If no match was found, write a message in the session and stop.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** will use regex to see the "under $" in the "max_price" parameter, then will strip the substrings and use the leftover string as new description to send to "parse_query()" once more.

**What moves through the session:** would create a new "relaxed" optional parameter to new_session() to use when a retry is needed, the flow would the look like: 
parsed (regex from raw query) -> search_results -> 
1) if empty -> parsed (drop max_price from raw query) -> set session to "relaxed" -> if matched -> override session["search_results"] with new results -> selected_item -> suggest_outfit -> fit card 
2) if still empty -> session['error'] and return 


---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

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

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



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

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



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
