from __future__ import annotations

import xml.etree.ElementTree as ET

import requests


def load_sitemap(source: str, timeout: int = 20) -> list[str]:
    source = (source or "").strip()
    if not source:
        return []

    if source.startswith(("http://", "https://")):
        response = requests.get(source, timeout=timeout, headers={"User-Agent": "Brave Search URL Submit Manager"})
        response.raise_for_status()
        xml_text = response.text
    else:
        with open(source, "r", encoding="utf-8") as handle:
            xml_text = handle.read()

    return parse_sitemap_xml(xml_text)


def parse_sitemap_xml(xml_text: str) -> list[str]:
    root = ET.fromstring(xml_text)
    urls: list[str] = []

    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            urls.append(element.text.strip())

    return urls
