"""Turn saved HTML pages into plain text the model can read. Standard library only.

ai_parse_document handles PDFs and images but not HTML. HTML is already text,
so stripping the tags in code is free, exact and testable.
"""

from html.parser import HTMLParser

SKIP = {"script", "style", "noscript", "template", "svg", "head"}
BLOCK = {
    "p", "div", "section", "article", "header", "footer", "li", "ul", "ol", "tr",
    "table", "br", "h1", "h2", "h3", "h4", "h5", "h6", "dt", "dd", "blockquote",
}


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip_depth += 1
        elif tag in BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip_depth:
            self.skip_depth -= 1
        elif tag in BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Visible text, one line per block, with whitespace tidied and blank lines dropped."""
    parser = _TextParser()
    parser.feed(html)
    parser.close()
    lines = (" ".join(line.split()) for line in "".join(parser.parts).splitlines())
    return "\n".join(line for line in lines if line)


def combine_sources(sources: list[tuple[str, str]]) -> str:
    """All of one venue's pages as one text, each headed by the file it came from."""
    return "\n\n".join(f"=== SOURCE: {name} ===\n{text}" for name, text in sources)
