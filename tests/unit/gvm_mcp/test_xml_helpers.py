from gvm_mcp.utils.xml_helpers import xml_to_dict


def test_xml_to_dict_handles_attributes_and_nested_nodes() -> None:
    xml = """
    <get_targets_response status=\"200\" status_text=\"OK\">
      <target id=\"abc\">
        <name>Web</name>
        <hosts>192.168.1.1</hosts>
      </target>
    </get_targets_response>
    """

    parsed = xml_to_dict(xml)

    root = parsed["get_targets_response"]
    assert isinstance(root, dict)
    attrs = root["@attributes"]
    assert isinstance(attrs, dict)
    assert attrs["status"] == "200"
    target = root["target"]
    assert isinstance(target, dict)
    assert target["name"]["#text"] == "Web"
