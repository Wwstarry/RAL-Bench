from __future__ import annotations

import os
import sys
from pathlib import Path
import textwrap

# Root directory of the benchmark project
ROOT = Path(__file__).resolve().parents[2]

# Decide whether to test the reference repository or the generated one.
target = os.environ.get("MARKDOWN_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "markdown"
else:
    # This should be the path where generated Markdown repositories are stored.
    REPO_ROOT = ROOT / "generation" / "Markdown"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import markdown  # type: ignore  # noqa: E402


def normalize_html(html: str) -> str:
    """Normalize trivial whitespace differences in HTML output."""
    lines = [line.strip() for line in html.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)


def test_large_document_integration() -> None:
    """Integration test on a larger document mixing many Markdown features."""
    src = textwrap.dedent(
        """
        # Project Documentation

        Welcome to the **Markdown** integration test. This document contains
        a bit of everything to exercise the overall pipeline.

        ## Table of Contents

        - [Introduction](#introduction)
        - [Usage](#usage)
        - [API](#api)
        - [License](#license)

        ## Introduction

        Markdown allows you to write *formatted* text using a simple, plain-text syntax.
        It is commonly used for README files, documentation, and static site content.

        ## Usage

        1. Install the package.
        2. Import the `markdown` module.
        3. Call `markdown.markdown(text)` with your Markdown content.

        ```bash
        pip install markdown
        ```

        ## API

        ```python
        import markdown

        html = markdown.markdown("# Title\\n\\nSome text.")
        ```

        > Note: The API may accept additional keyword arguments to customize
        > extensions, output format, and more.

        ## License

        This project is licensed under the MIT License.

        ---
        Generated with Markdown integration test.
        """
    )

    html = markdown.markdown(src)
    norm = normalize_html(html)

    # Basic structural checks
    assert "<h1>" in norm and "</h1>" in norm
    assert "<h2>" in norm and "</h2>" in norm
    assert "<ul>" in norm or "<ol>" in norm
    assert "<code>" in norm
    assert "<blockquote>" in norm
    assert "Project Documentation" in norm
    assert "Markdown integration test" in norm
    assert "MIT License" in norm


def test_batch_conversion_integration() -> None:
    """Integration test for converting multiple documents sequentially."""
    docs = [
        "# Doc 1\n\nFirst document.",
        "## Doc 2\n\nSecond document with *emphasis*.",
        textwrap.dedent(
            """
            # Doc 3

            - item A
            - item B

            ```python
            print("hello")
            ```
            """
        ),
    ]

    html_outputs = [markdown.markdown(src) for src in docs]
    norms = [normalize_html(html) for html in html_outputs]

    assert len(norms) == 3
    assert "Doc 1" in norms[0]
    assert "<h1>" in norms[0] or "<h2>" in norms[0]

    assert "Doc 2" in norms[1]
    assert "<em>" in norms[1] or "<i>" in norms[1]

    assert "Doc 3" in norms[2]
    assert "<ul>" in norms[2]
    assert "<code>" in norms[2]
