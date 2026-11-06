# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Load the pages and labels
# MAGIC
# MAGIC Reads every saved page from the `raw` volume, strips the HTML to text, and joins each
# MAGIC venue's pages into one text (the folder name is the venue's `slug`). Also loads the
# MAGIC hand labels as a table.
# MAGIC
# MAGIC **In:** `/Volumes/workspace/wedding/raw/pages/<slug>/*.html` and `raw/labels.csv`
# MAGIC **Out:** tables `venue_text` and `labels`

# COMMAND ----------

import os
import sys

# The repo's own code lives in ../src (this notebook runs inside the Git folder).
sys.path.append(os.path.abspath("../src"))

from wedding_venue_finder.pages import combine_sources, html_to_text  # noqa: E402

CATALOG, SCHEMA = "workspace", "wedding"
RAW = f"/Volumes/{CATALOG}/{SCHEMA}/raw"

# COMMAND ----------

# One row per venue: its slug, the files it came from, and all its text together.
rows = []
for slug in sorted(os.listdir(f"{RAW}/pages")):
    folder = f"{RAW}/pages/{slug}"
    if not os.path.isdir(folder):
        continue
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith((".html", ".htm")))
    sources = []
    for name in files:
        with open(f"{folder}/{name}", encoding="utf-8", errors="replace") as f:
            sources.append((name, html_to_text(f.read())))
    rows.append((slug, files, combine_sources(sources)))

venue_text = spark.createDataFrame(rows, "slug string, files array<string>, text string")
venue_text.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{CATALOG}.{SCHEMA}.venue_text"
)

display(spark.sql(f"""
    SELECT slug, size(files) AS n_files, files, length(text) AS chars
    FROM {CATALOG}.{SCHEMA}.venue_text ORDER BY slug
"""))

# COMMAND ----------

# The answer key. Everything is read as text; the evaluation converts types itself,
# so a blank stays a blank (not a 0 or false).
labels = (
    spark.read.option("header", True)
    .option("quote", '"')
    .option("escape", '"')
    .csv(f"{RAW}/labels.csv")
)
labels.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{SCHEMA}.labels")

display(spark.table(f"{CATALOG}.{SCHEMA}.labels"))

# COMMAND ----------

# Every labelled venue should have pages, and every venue with pages should be labelled.
pages = {r.slug for r in spark.table(f"{CATALOG}.{SCHEMA}.venue_text").select("slug").collect()}
labelled = {r.slug for r in spark.table(f"{CATALOG}.{SCHEMA}.labels").select("slug").collect()}
print("labelled but no pages:", sorted(labelled - pages) or "none")
print("pages but not labelled:", sorted(pages - labelled) or "none")
