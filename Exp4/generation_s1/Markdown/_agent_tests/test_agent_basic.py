import io
import re
from pathlib import Path

import markdown as mdlib


def norm(s: str) -> str:
    # Ignore insignificant whitespace between tags
    return re.sub(r">\s+<", "><", s.strip())


def test_public_api_surface():
    assert hasattr(mdlib, "markdown")
    assert hasattr(mdlib, "markdownFromFile")
    assert hasattr(mdlib, "Markdown")
    out = mdlib.markdown("hi")
    assert isinstance(out, str)
    m = mdlib.Markdown()
    assert m.reset() is m
    out2 = m.convert("hi")
    assert isinstance(out2, str)


def test_headings_and_paragraphs():
    src = "# Title\n\nA para\n\n## Sub"
    html = mdlib.markdown(src)
    assert "<h1>Title</h1>" in html
    assert "<p>A para</p>" in html
    assert "<h2>Sub</h2>" in html


def test_emphasis_strong_and_code_and_escape():
    src = "a *em* and **strong** and `1 < 2 & 3` and x < y & z"
    html = mdlib.markdown(src)
    assert "<em>em</em>" in html
    assert "<strong>strong</strong>" in html
    assert "<code>1 &lt; 2 &amp; 3</code>" in html
    assert "x &lt; y &amp; z" in html
    # ensure raw '<' not present outside code
    assert "< y" not in html


def test_fenced_and_indented_code_blocks():
    src = "```\n<x>\n```\n\n    <y>\n"
    html = mdlib.markdown(src)
    assert "<pre><code>&lt;x&gt;" in html
    assert "<pre><code>&lt;y&gt;" in html


def test_lists_blockquotes_links_images():
    src = "\n".join(
        [
            "- a",
            "- b",
            "",
            "1. one",
            "2. two",
            "",
            "> q",
            ">",
            "> r",
            "",
            "[t](http://example.com?a=1&b=2)",
            "",
            "![alt](img.png)",
        ]
    )
    html = mdlib.markdown(src)
    h = norm(html)
    assert "<ul><li>a</li><li>b</li></ul>" in h
    assert "<ol><li>one</li><li>two</li></ol>" in h
    assert "<blockquote><p>q</p><p>r</p></blockquote>" in h
    assert '<a href="http://example.com?a=1&amp;b=2">t</a>' in html
    assert '<img alt="alt" src="img.png" />' in html


def test_markdown_from_file(tmp_path: Path):
    p = tmp_path / "in.md"
    p.write_text("# X\n\nY & Z\n", encoding="utf-8")

    html = mdlib.markdownFromFile(input=str(p))
    assert "<h1>X</h1>" in html
    assert "Y &amp; Z" in html

    outp = tmp_path / "out.html"
    ret = mdlib.markdownFromFile(input=str(p), output=str(outp))
    assert ret is None
    written = outp.read_text(encoding="utf-8")
    assert "<h1>X</h1>" in written