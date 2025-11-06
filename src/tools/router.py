from typing import Literal
from core.common_types import Diagram_ManagerState
from langchain.tools import BaseTool
from .detect_intent import detect_intent

class ToolRouter:
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, name: str, tool):
        self.tools[name] = tool
    
    def route(self, state: Diagram_ManagerState) -> str:
        intent = detect_intent(state)
        return {
            "generate": "generate_diagram",
            "describe": "describe_diagram",
            "transform": "transform_diagram"
        }[intent]