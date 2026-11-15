# Wedding venue finder

We're planning a wedding in Spain, and venue research quickly became a spreadsheet of tabs, brochures
and "please enquire". Every venue spreads its facts across its own site, a few directories and a PDF.
Each one words them differently, and the answer we need (can we bring a band? is there a curfew?) is
often buried or missing.

This project reads those pages with an LLM on Databricks and pulls out the facts that matter to us,
each with a quote from the page. It then checks those facts against hand labels before trusting them.
The end goal is a shortlist that says, for every venue:
- which of our must-haves it passes;
- which it fails;
- which it doesn't answer, written up as questions to email the venue.

It's a side project. It's also a way to learn Databricks' AI functions properly, by building
something I actually need.

## How it works

```
saved venue pages (HTML, PDF)
        │   Unity Catalog volume: /Volumes/workspace/wedding/raw
        ▼
01_load_pages   strip HTML to text in Python, one text per venue   → venue_text
        ▼
02_extract      ai_extract 2.1, schema generated from VenueFacts,
                citations on                                        → extracted_v1
        ▼
03_evaluate     compare with the hand labels, field by field        → evaluation_v1
        ▼
next            the gold table: pass / fail / unknown per rule,
                preference score, questions to ask each venue
```

## Design choices

- **The rules are data, not code.** Everything we care about lives in [`data/rules.yaml`](data/rules.yaml).
  It has three kinds of rule:
  - **hard rules:** fail one and the venue is out;
  - **preferences:** these change the ranking but never rule a venue out;
  - **asks:** questions only the venue can answer.

  Change a number and re-run. A typo in a key is an error, not a silently ignored setting.
- **Unknown is never a pass.** If a page doesn't say whether live bands are allowed, the venue stays
  in, marked "ask them", rather than quietly passing or failing.
- **Every fact comes with a quote.** [`VenueFacts`](src/wedding_venue_finder/schema.py) won't accept a
  value without the words it came from. The evaluation checks that every extracted number is actually
  written in the text the model cited.
- **The model copies, code calculates.** Prices keep the currency on the page, and curfews stay clock
  times. Converting euros to pounds, or "02:00" to hours past midnight, happens in
  [`convert.py`](src/wedding_venue_finder/convert.py), where it can be tested.
- **One source of truth for the schema.** `data/extraction.json` (what `ai_extract` receives) is
  generated from the Pydantic model, and a test fails if the two drift apart.
- **Measured before trusted.** Five venues were labelled by hand from the same saved pages the model
  reads. Every change to the prompt or schema gets a new version and is scored against those labels.

## First results (v1)

| judgements | agree | wrong | missed | invented | numbers not in their quote |
|---|---|---|---|---|---|
| 55 | 42 (76%) | 4 | 2 | 7 | 0 |

The interesting part is *why* they disagreed. The full write-up is in [`docs/results_v1.md`](docs/results_v1.md).

- **The model never made a number up.** Every wrong number is really on the page; it picked the wrong
  one, such as a nightly villa rate instead of the wedding fee. So the fix is to say which number
  we mean.
- **Most of the "errors" were the answer key.** Four of the seven "inventions" were the model
  following our own field description more faithfully than our labels did.
- **Not all errors cost the same.** A miss is cheap: it becomes a question for the venue. The
  dangerous errors make a venue look better than it is:
  - an invented live band passes a hard rule;
  - a low hire fee passes the budget;
  - "curfew: please enquire" read as "no curfew" gets the best possible curfew score.

## Next

1. **v2, one change per version, each measured against v1:**
   - fix the open-bar labels;
   - define which price counts as the venue hire;
   - read "please enquire" as unknown;
   - move live bands to the enquiry questions;
   - tell the model the venue's own site beats a directory.
2. **The gold table:** every rule as pass, fail or unknown, plus a preference score, the supporting
   quote and the questions to email each venue.
3. **More venues,** mostly in Catalonia.

## Running it

Local code and tests (Python 3.12, [uv](https://docs.astral.sh/uv/)):

```
uv sync
uv run pytest
uv run write-extraction
```

`write-extraction` regenerates `data/extraction.json` after you change `VenueFacts`.

On Databricks (built on the Free Edition, serverless):

1. Create the schema `workspace.wedding` and a volume `raw`.
2. Upload each venue's saved pages to `raw/pages/<slug>/`, and `data/labels.csv` to `raw/`.
3. Add this repo as a Git folder and run notebooks 01, 02 and 03 in order.

The venue pages themselves aren't in the repo, because they belong to the venues.
[`data/labels.csv`](data/labels.csv) lists the URLs they came from.

### Your own figures

The public `rules.yaml` uses example figures and leaves the budget out. To use your own, copy it to
`data/rules.local.yaml` and edit that. It's gitignored, and it's loaded instead whenever it exists.

## Layout

```
data/         rules.yaml, hand labels, the generated extraction schema
notebooks/    the three Databricks notebooks
src/          rules, schema, HTML to text, conversions, scoring
tests/        pytest, no Databricks needed
docs/         results for each version
```
