from enum import Enum
from typing import Dict, List

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class DiagramType(Enum):
    SEQUENCE_DIAGRAM = "sequenceDiagram"
    FLOWCHART = "flowchart"
    CLASS_DIAGRAM = "classDiagram"
    STATE_DIAGRAM = "stateDiagram"
    ENTITY_RELATIONSHIP_DIAGRAM = "entityRelationshipDiagram"
    GANTT = "gantt"
    PIE = "pie"
    USER_JOURNEY = "userJourney"
    QUADRANT_CHART = "quadrantChart"
    REQUIREMENTDIAGRAM = "requirementDiagram"
    GIT_GRAPH = "gitgraph"
    C4Context = "c4"
    C4Container = "c4"
    C4Component = "c4"
    MINDMAP = "mindmap"
    TIMELINE = "timeline"
    ZEN_UML = "zenuml"
    SANKEY ="sankey"
    XYCHART = "xychart"
    BLOCK = "block"
    PACKET = "packet"
    KANBAN = "kanban"
    ARCHITECTURE = "architecture"
    RADAR = "radar"
    TREEMAP = "treemap"


class Diagram_ManagerState(BaseModel):
    user_prompt: str
    action: str =""
    mermaid_code: str = ""
    validation_result: Dict = {}
    description: str = ""
    diagram_type: str = ""
    diagram_type_context: str = ""
    iteration_count: int = 0
    max_iterations: int = 3
    errors: List[str] = []
    syntax_rules: Dict = {}
    llm: ChatOpenAI