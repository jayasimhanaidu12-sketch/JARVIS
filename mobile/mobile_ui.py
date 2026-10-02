"""
Android Mobile UI hierarchy inspection.
Parses UI dump XML to locate text, buttons, inputs, and their tap coordinates.
"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from mobile.adb import adb_manager


class MobileUIElement:
    def __init__(self, text: str, resource_id: str, class_name: str, bounds: Tuple[int, int, int, int]):
        self.text = text
        self.resource_id = resource_id
        self.class_name = class_name
        self.bounds = bounds  # x1, y1, x2, y2

    @property
    def center(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bounds
        return (x1 + x2) // 2, (y1 + y2) // 2


class MobileUIInspector:
    def dump_hierarchy_xml(self) -> str:
        """Triggers uiautomator dump on Android and retrieves XML hierarchy."""
        if adb_manager.is_simulator_mode or not adb_manager.get_connected_devices():
            # Mock XML for simulated testing
            return """<hierarchy rotation="0">
                <node text="YouTube" resource-id="com.google.android.youtube:id/title" bounds="[100,200][400,300]"/>
                <node text="Search" resource-id="com.google.android.youtube:id/search_box" bounds="[500,200][800,300]"/>
                <node text="Play" resource-id="com.google.android.youtube:id/player_control" bounds="[450,900][550,1000]"/>
            </hierarchy>"""

        adb_manager.execute_shell("uiautomator dump /sdcard/window_dump.xml")
        success, content = adb_manager.execute_shell("cat /sdcard/window_dump.xml")
        return content if success else ""

    def parse_elements(self, xml_content: str) -> List[MobileUIElement]:
        """Extracts UI nodes from hierarchy XML."""
        elements: List[MobileUIElement] = []
        if not xml_content.strip():
            return elements

        try:
            root = ET.fromstring(xml_content)
            for node in root.iter("node"):
                text = node.attrib.get("text", "") or node.attrib.get("content-desc", "")
                res_id = node.attrib.get("resource-id", "")
                cls_name = node.attrib.get("class", "")
                bounds_str = node.attrib.get("bounds", "")

                bounds = (0, 0, 0, 0)
                # Parse bounds format: [x1,y1][x2,y2]
                match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
                if match:
                    bounds = tuple(map(int, match.groups()))

                if text or res_id:
                    elements.append(MobileUIElement(text, res_id, cls_name, bounds))
        except Exception as e:
            print(f"Failed to parse Android UI XML: {e}")

        return elements

    def find_element_by_text(self, text_query: str) -> Optional[MobileUIElement]:
        """Locates element matching text substring."""
        xml = self.dump_hierarchy_xml()
        elements = self.parse_elements(xml)
        query_lower = text_query.lower()
        for elem in elements:
            if query_lower in elem.text.lower():
                return elem
        return None


mobile_ui = MobileUIInspector()
