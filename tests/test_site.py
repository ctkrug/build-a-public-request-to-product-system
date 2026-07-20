from html.parser import HTMLParser
from pathlib import Path


SITE_PATH = Path(__file__).parents[1] / "site" / "index.html"
REPOSITORY_URL = "https://github.com/ctkrug/build-a-public-request-to-product-system"
PORTFOLIO_URL = "https://apps.charliekrug.com"
FORBIDDEN_COPY = {
    "cutting-edge",
    "effortless",
    "empower",
    "game-changing",
    "groundbreaking",
    "harness",
    "leverage",
    "revolutionary",
    "seamless",
    "supercharge",
    "transformative",
    "unlock",
}


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_copy = 0
        self.copy: list[str] = []
        self.links: list[str] = []
        self.meta: list[dict[str, str | None]] = []
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in {"script", "style"}:
            self.skip_copy += 1
        if tag == "title":
            self.in_title = True
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
        if tag == "meta":
            self.meta.append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skip_copy -= 1
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if not self.skip_copy and data.strip():
            self.copy.append(data.strip())


def _parse_site() -> tuple[str, SiteParser]:
    html = SITE_PATH.read_text()
    parser = SiteParser()
    parser.feed(html)
    return html, parser


def test_site_has_required_metadata_and_links():
    html, parser = _parse_site()
    title = "".join(parser.title_parts)
    named_meta = {item.get("name"): item.get("content") for item in parser.meta if item.get("name")}
    property_meta = {
        item.get("property"): item.get("content") for item in parser.meta if item.get("property")
    }

    assert title.startswith("Wishwright · ")
    assert 1 <= len(named_meta["description"] or "") <= 160
    assert property_meta["og:title"]
    assert property_meta["og:description"]
    assert "og:url" not in property_meta
    assert "og:image" not in property_meta
    assert 'rel="icon"' in html and "data:image/svg+xml" in html
    assert REPOSITORY_URL in parser.links
    assert PORTFOLIO_URL in parser.links


def test_site_copy_passes_the_closeout_gate():
    _html, parser = _parse_site()
    copy = " ".join(parser.copy)
    lowered = copy.lower()

    assert 300 <= len(copy.split()) <= 600
    assert "—" not in copy
    assert not {term for term in FORBIDDEN_COPY if term in lowered}
    assert "Wishwright" in copy
    assert "Current integration boundary" in copy
