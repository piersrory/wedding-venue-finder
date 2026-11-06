# Databricks notebook source
# MAGIC %md
# MAGIC # 3. Score the extraction against the hand labels
# MAGIC
# MAGIC For every venue and field: the label, what the model extracted, the outcome
# MAGIC (correct, wrong, missed, invented, both_unknown), and the quote the model cited.
# MAGIC For numbers, it also checks the number is actually written in the cited text.
# MAGIC
# MAGIC **In:** tables `labels`, `venue_text`, `extracted_<version>`; file `data/rules.yaml` (exchange rate)
# MAGIC **Out:** table `evaluation_<version>`

# COMMAND ----------

import json
import os
import sys

import yaml

sys.path.append(os.path.abspath("../src"))

from wedding_venue_finder.evaluate import score_venue  # noqa: E402

CATALOG, SCHEMA = "workspace", "wedding"

with open("../data/extraction.json", encoding="utf-8") as f:
    VERSION = json.load(f)["version"]
with open("../data/rules.yaml", encoding="utf-8") as f:
    EUR_TO_GBP = yaml.safe_load(f)["currency"]["eur_to_gbp"]

print("scoring", VERSION, "at", EUR_TO_GBP, "GBP per EUR")

# COMMAND ----------

labels = {r.slug: r.asDict() for r in spark.table(f"{CATALOG}.{SCHEMA}.labels").collect()}
texts = {r.slug: r.text for r in spark.table(f"{CATALOG}.{SCHEMA}.venue_text").collect()}
results = {
    r.slug: json.loads(r.j)
    for r in spark.sql(f"SELECT slug, to_json(result) AS j FROM {CATALOG}.{SCHEMA}.extracted_{VERSION}").collect()
}

rows = []
for slug, result in sorted(results.items()):
    if slug not in labels:
        print("no label for", slug, "- skipped")
        continue
    rows.extend(score_venue(slug, labels[slug], result, texts[slug], EUR_TO_GBP))

evaluation = spark.createDataFrame(
    rows,
    "slug string, field string, label string, extracted string, outcome string, "
    "number_in_quote boolean, quote string",
)
evaluation.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"{CATALOG}.{SCHEMA}.evaluation_{VERSION}"
)
TABLE = f"{CATALOG}.{SCHEMA}.evaluation_{VERSION}"

# COMMAND ----------

# MAGIC %md ## Overall

# COMMAND ----------

display(spark.sql(f"""
    SELECT
      count(*) AS judgements,
      count_if(outcome IN ('correct', 'both_unknown')) AS agree,
      round(100 * count_if(outcome IN ('correct', 'both_unknown')) / count(*), 1) AS agree_pct,
      count_if(outcome = 'wrong') AS wrong,
      count_if(outcome = 'missed') AS missed,
      count_if(outcome = 'invented') AS invented,
      count_if(number_in_quote = false) AS number_not_in_quote
    FROM {TABLE}
"""))

# COMMAND ----------

# MAGIC %md ## By field: which facts does it read badly?

# COMMAND ----------

display(spark.sql(f"""
    SELECT field,
      count_if(outcome = 'correct') AS correct,
      count_if(outcome = 'both_unknown') AS both_unknown,
      count_if(outcome = 'wrong') AS wrong,
      count_if(outcome = 'missed') AS missed,
      count_if(outcome = 'invented') AS invented
    FROM {TABLE}
    GROUP BY field
    ORDER BY wrong + missed + invented DESC, field
"""))

# COMMAND ----------

# MAGIC %md ## Every disagreement, with the quote the model cited

# COMMAND ----------

display(spark.sql(f"""
    SELECT slug, field, outcome, label, extracted, number_in_quote, quote
    FROM {TABLE}
    WHERE outcome NOT IN ('correct', 'both_unknown')
    ORDER BY outcome, field, slug
"""))
