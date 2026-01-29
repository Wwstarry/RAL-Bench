import re
import html

class Markdown:
    """
    Markdown class for converting Markdown text to HTML.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """
        Reset the internal state for processing a new document.
        """
        pass

    def convert(self, text):
        """
        Convert Markdown text to HTML.

        :param text: Unicode Markdown string.
        :return: Unicode HTML string.
        """
        return self._convert_blocks(text)

    def _convert_blocks(self, text):
        """
        Process block-level elements.
        """
        lines = text.split("\n")
        html_output = []
        buffer = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                # Empty line indicates end of a block
                if buffer:
                    html_output.append(self._process_block(buffer))
                    buffer = []
            else:
                buffer.append(line)

        # Process any remaining buffer
        if buffer:
            html_output.append(self._process_block(buffer))

        return "\n".join(html_output)

    def _process_block(self, lines):
        """
        Process a single block of lines.
        """
        first_line = lines[0].strip()

        # ATX-style headings
        if first_line.startswith("#"):
            level = len(first_line.split(" ")[0])
            content = first_line[level:].strip()
            return f"<h{level}>{html.escape(content)}</h{level}>"

        # Blockquotes
        if first_line.startswith(">"):
            content = " ".join(line.lstrip("> ").strip() for line in lines)
            return f"<blockquote>{html.escape(content)}</blockquote>"

        # Fenced or indented code blocks
        if first_line.startswith("```") or all(line.startswith("    ") for line in lines):
            code_content = "\n".join(line.lstrip("    ") for line in lines if not line.startswith("```"))
            return f"<pre><code>{html.escape(code_content)}</code></pre>"

        # Ordered lists
        if re.match(r"^\d+\.", first_line):
            list_items = "\n".join(f"<li>{html.escape(line.split('.', 1)[1].strip())}</li>" for line in lines)
            return f"<ol>\n{list_items}\n</ol>"

        # Unordered lists
        if first_line.startswith(("-", "+", "*")):
            list_items = "\n".join(f"<li>{html.escape(line[1:].strip())}</li>" for line in lines)
            return f"<ul>\n{list_items}\n</ul>"

        # Paragraphs
        return f"<p>{html.escape(' '.join(lines))}</p>"


def markdown(text, **kwargs):
    """
    Convert Markdown text to HTML.

    :param text: Unicode Markdown string.
    :param kwargs: Additional options (not implemented in this basic version).
    :return: Unicode HTML string.
    """
    md = Markdown()
    return md.convert(text)


def markdownFromFile(input_file=None, output_file=None, encoding="utf-8", **kwargs):
    """
    Convert Markdown text from a file to HTML.

    :param input_file: Path to the input Markdown file.
    :param output_file: Path to the output HTML file (optional).
    :param encoding: File encoding (default: utf-8).
    :param kwargs: Additional options (not implemented in this basic version).
    """
    if input_file is None:
        raise ValueError("input_file must be specified")

    with open(input_file, "r", encoding=encoding) as f:
        text = f.read()

    html_output = markdown(text, **kwargs)

    if output_file:
        with open(output_file, "w", encoding=encoding) as f:
            f.write(html_output)

    return html_output