from wedding_venue_finder.pages import combine_sources, html_to_text

PAGE = """
<html><head><title>Ignore me</title><style>.x{color:red}</style></head>
<body>
  <script>var tracking = "ignore me too";</script>
  <h1>Masia Example</h1>
  <p>Weddings up to   250 guests</p>
  <ul><li>Swimming Pool Yes</li><li>Curfew No curfew</li></ul>
  <p>Menu from &euro;148,45 per person</p>
</body></html>
"""


def test_visible_text_is_kept_one_line_per_block():
    assert html_to_text(PAGE).splitlines() == [
        "Masia Example",
        "Weddings up to 250 guests",
        "Swimming Pool Yes",
        "Curfew No curfew",
        "Menu from €148,45 per person",
    ]


def test_scripts_styles_and_head_are_dropped():
    text = html_to_text(PAGE)
    assert "ignore me" not in text.lower()
    assert "color:red" not in text


def test_sources_are_combined_with_headers():
    text = combine_sources([("own.html", "A"), ("directory.html", "B")])
    assert text == "=== SOURCE: own.html ===\nA\n\n=== SOURCE: directory.html ===\nB"
