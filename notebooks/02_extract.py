# Databricks notebook source
# MAGIC %md
# MAGIC # 2. Extract the facts with `ai_extract`
# MAGIC
# MAGIC Runs `ai_extract` (version 2.1) over each venue's text, using the schema and instructions
# MAGIC in `data/extraction.json`. That file is generated from `VenueFacts` in `schema.py`, so the
# MAGIC Pydantic model stays the single source of truth.
# MAGIC
# MAGIC Citations are on: for each value, the model returns where in the text it found it.
# MAGIC Cutting the text at those positions gives the quote for the quote check.
# MAGIC
# MAGIC **In:** table `venue_text`, file `data/extraction.json`
# MAGIC **Out:** table `extracted_<version>`, e.g. `extracted_v1`

# COMMAND ----------

import json

CATALOG, SCHEMA = "workspace", "wedding"

with open("../data/extraction.json", encoding="utf-8") as f:
    config = json.load(f)

VERSION = config["version"]
schema_json = json.dumps(config["schema"], ensure_ascii=False)
instructions = config["instructions"]

# Both go inside '...' in the SQL below, so they must not contain quotes or backslashes.
# (A test in the repo checks this too.)
for text in (schema_json, instructions):
    assert "'" not in text and "\\" not in text

TABLE = f"{CATALOG}.{SCHEMA}.extracted_{VERSION}"
print("writing", TABLE)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {TABLE} AS
SELECT
  slug,
  '{VERSION}' AS version,
  current_timestamp() AS extracted_at,
  ai_extract(
    text,
    '{schema_json}',
    options => map(
      'version', '2.1',
      'instructions', '{instructions}',
      'enableCitations', 'true'
    )
  ) AS result
FROM {CATALOG}.{SCHEMA}.venue_text
""")

display(spark.sql(f"""
    SELECT slug, result:error_message::string AS error, to_json(result:response) AS response
    FROM {TABLE} ORDER BY slug
"""))

# COMMAND ----------

# One venue in full, to see the shape of the answer: values, citation ids and metadata.
row = spark.sql(f"SELECT to_json(result) AS j FROM {TABLE} WHERE slug = 'el-convent-blanes'").first()
print(json.dumps(json.loads(row.j), indent=2, ensure_ascii=False))
