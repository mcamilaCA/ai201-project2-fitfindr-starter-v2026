# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**

`search_listings` scores listings by plain keyword overlap between the query's
description and each listing's title, description, and style_tags — no
synonym handling, no stemming. That means a listing can be a genuine match in
plain English and still score zero, just because the query used a different
word for the same thing ("tee" vs. a listing that only says "t-shirt"). Five
"matching" queries picked by a person won't all phrase things the way the
data happens to, so I'd expect to lose one in five to word choice alone, not
to a bug in the loop. If I ever want 5/5 here, the fix is in the scoring
function, not the test.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**

Criterion 1 depends on the keyword-overlap score finding a match, which is a
fuzzy judgment about phrasing — that's where the uncertainty in criterion 1
comes from. This criterion doesn't touch that scoring logic at all: by the
time the branch runs, `search_listings` has already returned its answer, and
the branch is just `if not results: stop`, a plain emptiness check on a
Python list with no judgment call left in it. There's no equivalent to a
missed synonym on this side — either the list is empty or it isn't, and an
`if` statement doesn't have an off day. If this ever misses 5/5, that points
at a real bug in the branch, not at expected variance.

---

## 3. Something about state

Given a query that matches at least one listing, `session["selected_item"]["id"]`
equals the `new_item["id"]` that `suggest_outfit` actually receives — 5 of 5
tries.

**Why this target:**

In unit 3, `selected_item` goes straight from the session into `suggest_outfit`
as the same Python object — nothing serializes it or reconstructs it in
between, so there's no honest mechanism for the two ids to disagree today.
5/5 is the right target precisely because this is the number to watch once
that stops being true: next unit, `search_listings` moves onto MCP, and its
results start crossing a real boundary (JSON out, JSON back). That's a
concrete way for an id to get dropped, coerced, or swapped without any tool
raising an error — it would just look like `suggest_outfit` producing a
slightly odd outfit, not like a state bug. Catching that requires this exact
check, which is why it's worth writing down now, before the rewire, rather
than after.

---

## 4. Something about the fit card

Given the same item and outfit suggestion, run `create_fit_card` 5 times; the
caption stays at or under 4 sentences — matching the tool's own documented
return contract — in at least 4 of 5 tries.

**Why this target:**

`create_fit_card`'s own spec (`tools.py`) says it returns a two-to-four
sentence caption — so this criterion is just holding the tool to the contract
it already claims for itself, not inventing a new one. It's not 5 of 5 because
the prompt can tell the model to stay in that range, but it can't force
sentence count the way code can enforce a loop condition — at TEMPERATURE > 0,
the model paces itself, and occasionally running one sentence long is the kind
of variance that's expected from a generative tool rather than a sign the
prompt is wrong. If it misses by more than one in five, that points at the
prompt, not at the model being noisy.

---

## 5. Your choice — the relaxed retry

Given a query that fails to match under its stated `max_price` but would match
with that filter dropped, the agent retries with `max_price` removed, sets
`session["relaxed"]` to `True`, ends up with a non-empty `search_results`, and
returns output that names the filter it dropped — 5 of 5 tries.

**Why this target:**

This is the branch rule I already committed to in my README's Planning Loop
section, so it deserves the same scrutiny as the other branches. 5 of 5 is
reasonable here, unlike criterion 1, because the retry only has one job once
it fires: strip `max_price` from the parsed query and search again — there's
no keyword-matching ambiguity at that step, since the description and size
are untouched between the two attempts. The real risk isn't the retry search
missing — it's the regex that extracts `max_price` not recognizing the
phrasing in the query, so the branch never fires at all. I'm controlling for
that by only testing queries that use the "under $X" phrasing my regex is
built to catch; a query phrased some other way is a parsing problem, which
belongs to criterion 1, not this one.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
