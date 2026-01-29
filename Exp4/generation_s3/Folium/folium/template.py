from __future__ import annotations


LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"

# MarkerCluster plugin (external references only; do not inline large assets)
MARKERCLUSTER_CSS = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
MARKERCLUSTER_CSS_DEFAULT = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"
MARKERCLUSTER_JS = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"


def html_page(title: str, head_extras: list[str], body: str, script: str) -> str:
    head_bits = "\n".join(head_extras)
    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        '  <meta charset="utf-8"/>\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>\n'
        f"  <title>{title}</title>\n"
        f"{head_bits}\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "<script>\n"
        f"{script}\n"
        "</script>\n"
        "</body>\n"
        "</html>\n"
    )