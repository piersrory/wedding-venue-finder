# Extraction v1: results

Run on 7 Nov 2026 on Databricks Free Edition (serverless). `ai_extract` version 2.1, with citations,
over 5 hand-labelled venues × 11 fields. Tables: `extracted_v1` and `evaluation_v1`.

## Overall

| judgements | agree | agree % | wrong | missed | invented | number not in quote |
|---|---|---|---|---|---|---|
| 55 | 42 | 76.4 | 4 | 2 | 7 | 0 |

"Agree" counts both `correct` and `both_unknown`, where neither the page nor the model gives a value.

**Number not in quote = 0.** Every number the model got wrong is really written in the text it
cited. It picked the wrong number off the page; it never made one up. So the fix is to say which
number we mean, not to stop it hallucinating.

## By field

| field | correct | both unknown | wrong | missed | invented |
|---|---|---|---|---|---|
| open_bar_available | 1 | 0 | 0 | 0 | 4 |
| curfew | 3 | 0 | 0 | 1 | 1 |
| live_band_allowed | 0 | 3 | 0 | 0 | 2 |
| venue_hire | 2 | 1 | 2 | 0 | 0 |
| bring_your_own_drinks_allowed | 0 | 4 | 0 | 1 | 0 |
| catering_pp | 2 | 2 | 1 | 0 | 0 |
| max_guests | 4 | 0 | 1 | 0 | 0 |
| bar_pp | 1 | 4 | 0 | 0 | 0 |
| has_pool | 5 | 0 | 0 | 0 | 0 |
| outside_catering_allowed | 5 | 0 | 0 | 0 | 0 |
| sleeps_on_site | 5 | 0 | 0 | 0 | 0 |

## The 13 disagreements, by cause

Only 2 or 3 are clearly the model's fault. The rest are our answer key or our field definitions.

### The labels contradict our own definition (4)

| venue | field | label | model | what the page says |
|---|---|---|---|---|
| casa-nova-estate, finca-la-gloria, la-dehesa-de-don-pedro, la-farinera-sant-lluis | open_bar_available | blank | true | "Drink Packages Cost PP From POA" |

The field description says "open bar or drinks package is offered or included", so the model is
right by our own rule. Either set the labels to true, or tighten the description.

### The definition is unclear (6)

| venue | field | label | model | cause |
|---|---|---|---|---|
| casa-nova-estate | venue_hire | 9,900 | 4,250 | "€4,250 per night" is the villa rental rate, not the wedding fee |
| finca-la-gloria | venue_hire | 17,500 | 7,500 | A €7,500 celebration fee and a €17,500 package that includes the compulsory 3-night stay |
| el-convent-blanes | max_guests | 200 | 220 | The photographer's guide (220) disagrees with the venue's own site (200) |
| el-convent-blanes | catering_pp | 148.45 | 131 | The guide says "from €131" three times. That is also "the lowest if several" |
| casa-nova-estate | live_band_allowed | blank | true | Inferred from "an evening of music and dancing" |
| finca-la-gloria | live_band_allowed | blank | true | Inferred from "Music till 2am" |

We say the venue's own site wins over directories, but the model can't apply that: the source
headers are only filenames, and the instructions don't mention it.

### Model errors (2, maybe 3)

| venue | field | label | model | note |
|---|---|---|---|---|
| la-farinera-sant-lluis | curfew | blank | none | The page says "Curfew Please Enquire". "None" scores 32, the best possible curfew |
| el-convent-blanes | curfew | 27 | missed | The own site says 3am (extendable to 4am) and the guide says 5am. The model gave up on the conflict |
| el-convent-blanes | bring_your_own_drinks_allowed | false | missed | Check the label: if it was inferred from "exclusive catering", the page never says it |

## What it teaches

- **Not all errors cost the same.** The dangerous ones make a venue look better than it is:
  - an invented live band passes a hard rule
  - a low hire fee passes the budget
  - "Please enquire" read as "no curfew" gets the best curfew score

  A miss is cheap, because it becomes a question for the venue.
- **Check the answer key before blaming the model.** Here, most "errors" were our labels or definitions.
- **live_band_allowed is a hard rule that no page answers**, for any venue. It belongs in `ask`.

## Next: v2, one change per version

1. Fix the open_bar labels. This only needs a re-score, not a new model run.
2. venue_hire: "the minimum price to hold the wedding, including any compulsory stay; not a nightly
   or weekly rental rate".
3. curfew: "Please enquire / on request means unknown (null), not none".
4. live_band_allowed: true only for an explicit live band; move it to `ask` in `rules.yaml`.
5. Name each source as "venue website" or "directory", and say that the venue website wins.

For each change: bump `VERSION`, regenerate `data/extraction.json`, rerun notebooks 02 and 03, and
compare with v1.
