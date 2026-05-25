from __future__ import annotations

from xml.etree.ElementTree import Element, fromstring


def element_to_dict(element: Element) -> dict[str, object]:
    children = list(element)
    result: dict[str, object] = {}

    if element.attrib:
        result["@attributes"] = dict(element.attrib)

    text = (element.text or "").strip()
    if text:
        result["#text"] = text

    for child in children:
        value = element_to_dict(child)
        if child.tag in result:
            existing = result[child.tag]
            if isinstance(existing, list):
                existing.append(value)
            else:
                result[child.tag] = [existing, value]
        else:
            result[child.tag] = value

    return result


def xml_to_dict(xml_data: str | bytes) -> dict[str, object]:
    root = fromstring(xml_data)
    return {root.tag: element_to_dict(root)}
