"""
Unified Tool Registry for JARVIS.
Defines all tools, parameter schemas, target devices, and safety ratings.
"""

from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
from core.permissions import RiskLevel


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    risk_level: RiskLevel = RiskLevel.LOW
    device: str = "windows"  # windows, android, universal


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
        risk_level: RiskLevel = RiskLevel.LOW,
        device: str = "windows",
    ):
        """Registers a tool with metadata and executable handler."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            risk_level=risk_level,
            device=device,
        )

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_tool_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """Formats tool definitions for LLM function calling / tools format."""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": f"[{tool.device.upper()}] {tool.description}",
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                    },
                },
            })
        return schemas


tool_registry = ToolRegistry()
