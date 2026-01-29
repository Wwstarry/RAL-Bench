from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict


class Element:
    """
    Base class for renderable objects.
    """

    def __init__(self, name: Optional[str] = None):
        self._name = name
        self._parent: Optional["Element"] = None

    def add_to(self, parent: "Element") -> "Element":
        parent.add_child(self)
        return self

    def add_child(self, child: "Element", name: Optional[str] = None) -> "Element":
        raise NotImplementedError

    def get_root(self) -> "Element":
        obj: Element = self
        while obj._parent is not None:
            obj = obj._parent
        return obj

    def render(self, **kwargs: Any) -> str:
        raise NotImplementedError


@dataclass
class Figure(Element):
    """
    Root HTML document.
    """
    width: str = "100%"
    height: str = "100%"
    header: List[str] = field(default_factory=list)
    html: List[str] = field(default_factory=list)
    script: List[str] = field(default_factory=list)
    children: List[Element] = field(default_factory=list)

    def __post_init__(self):
        super().__init__(name="figure")

    def add_child(self, child: Element, name: Optional[str] = None) -> Element:
        child._parent = self
        self.children.append(child)
        return child

    def add_header(self, s: str) -> None:
        self.header.append(s)

    def add_html(self, s: str) -> None:
        self.html.append(s)

    def add_script(self, s: str) -> None:
        self.script.append(s)

    def render(self, **kwargs: Any) -> str:
        # Render children first; they typically populate figure html/script.
        for ch in list(self.children):
            ch.render(**kwargs)

        header = "\n".join(self.header)
        body_html = "\n".join(self.html)
        body_script = "\n".join(self.script)

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
{header}
<style>
html, body {{ width: 100%; height: 100%; margin: 0; padding: 0; }}
</style>
</head>
<body>
{body_html}
<script>
{body_script}
</script>
</body>
</html>"""


class MacroElement(Element):
    """
    Element with child management and script/html hooks.
    """
    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name)
        self._children: List[Element] = []

    def add_child(self, child: Element, name: Optional[str] = None) -> Element:
        child._parent = self
        self._children.append(child)
        return child

    def iter_children(self) -> List[Element]:
        return list(self._children)

    def render_children(self, **kwargs: Any) -> str:
        out = []
        for ch in self._children:
            out.append(ch.render(**kwargs))
        return "\n".join([x for x in out if x])