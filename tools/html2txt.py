"""Extract the plain text of an archived HTML page (archives/docs/*.htm) for grep.

Usage: python tools/html2txt.py <page.htm> <out.txt>
The charset comes from the page's <meta> tag, with windows-1252 as fallback (FEB pages).
"""

import html.parser
import re
import sys
from pathlib import Path
from typing import ClassVar


class _Text(html.parser.HTMLParser):
    BLOCK: ClassVar[set[str]] = {
        "p",
        "br",
        "div",
        "tr",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "table",
    }

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def main(src: str, dst: str) -> None:
    raw = Path(src).read_bytes()
    m = re.search(rb"charset=[\"']?([\w-]+)", raw[:4000], re.IGNORECASE)
    charset = m.group(1).decode() if m else "windows-1252"
    p = _Text()
    p.feed(raw.decode(charset, errors="replace"))
    lines = (" ".join(line.split()) for line in "".join(p.parts).splitlines())
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
    Path(dst).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
