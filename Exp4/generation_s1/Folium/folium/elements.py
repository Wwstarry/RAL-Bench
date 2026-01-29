from __future__ import annotations

from collections import OrderedDict
import uuid
from typing import Any, Optional


class Element:
    _name: str = "element"

    def __init__(self) -> None:
        self._id = uuid.uuid4().hex[:12]
        self._children: "OrderedDict[str, Element]" = OrderedDict()
        self.parent: Optional["Element"] = None

    def get_name(self) -> str:
        base = getattr(self, "_name", self.__class__.__name__).lower()
        base = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in base)
        if not base or base[0].isdigit():
            base = f"e_{base}"
        return f"{base}_{self._id}"

    def add_child(self, child: "Element", name: Optional[str] = None, index: Optional[int] = None) -> "Element":
        if name is None:
            name = child.get_name()
        child.parent = self
        if index is None or index >= len(self._children):
            self._children[name] = child
        else:
            items = list(self._children.items())
            items.insert(index, (name, child))
            self._children = OrderedDict(items)
        return child

    def add_to(self, parent: "Element") -> "Element":
        parent.add_child(self)
        return self

    def get_root(self) -> "Element":
        node: Element = self
        while node.parent is not None:
            node = node.parent
        return node

    def render(self, **kwargs: Any) -> str:
        parts = []
        for child in self._children.values():
            parts.append(child.render(**kwargs))
        return "".join(parts)


class _HtmlContainer(Element):
    _name = "container"

    def __init__(self, tag: str = "div", attrs: Optional[dict] = None) -> None:
        super().__init__()
        self.tag = tag
        self.attrs = attrs or {}

    def render(self, **kwargs: Any) -> str:
        attr_str = "".join(f' {k}="{v}"' for k, v in self.attrs.items())
        inner = super().render(**kwargs)
        return f"<{self.tag}{attr_str}>{inner}</{self.tag}>"


class Figure(Element):
    _name = "figure"

    def __init__(self) -> None:
        super().__init__()
        self.header = _HtmlContainer("head")
        self.html = _HtmlContainer("body", attrs={"style": "margin:0;padding:0;"})
        self.script = _HtmlContainer("script")
        self._asset_keys: set[str] = set()

    def add_asset(self, key: str) -> bool:
        if key in self._asset_keys:
            return False
        self._asset_keys.add(key)
        return True

    def render(self, **kwargs: Any) -> str:
        # Render root children into the script area by default (e.g., Map + layers).
        # This ensures m.get_root().render() includes map init/layers.
        script_inner = "".join(child.render(**kwargs) for child in self._children.values())
        if script_inner and (not self.script._children):
            # Insert as raw string container child for stability.
            self.script.add_child(_Raw(script_inner))

        head_inner = (
            '<meta charset="utf-8"/>'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>'
            + self.header.render(**kwargs)
        )
        body_inner = self.html.render(**kwargs) + self.script.render(**kwargs)
        return f"<!DOCTYPE html><html>{head_inner}{body_inner}</html>"


class _Raw(Element):
    _name = "raw"

    def __init__(self, html: str) -> None:
        super().__init__()
        self.html = html

    def render(self, **kwargs: Any) -> str:
        return self.html


class MacroElement(Element):
    _name: str = "macro_element"

    def __init__(self) -> None:
        super().__init__()

    def _template(self) -> str:
        return super().render()

    def render(self, **kwargs: Any) -> str:
        return self._template()