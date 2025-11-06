from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from typing import Dict, List, Literal
import re

from core.common_types import DiagramType, Diagram_ManagerState
from core.utils import get_or_generate_syntax
from tools import (
    describe_diagram, 
    transform_diagram, 
    generate_diagram, 
    validate_mermaid, 
    detect_intent
)

def diagram_syntax_reference(state: Diagram_ManagerState) -> Dict:
    """
    Fetch and summarize Mermaid diagram syntax reference.
    Returns updates to be merged into state.
    """
    try:
        diagram_type = DiagramType(state.diagram_type)
        context = get_or_generate_syntax(state.llm, diagram_type)
        
        return {
            "diagram_type_context": context,
            "diagram_type": state.diagram_type
        }
        
    except Exception as e:
        return {
            "errors": state.errors + [f"Failed to fetch syntax reference: {str(e)}"],
            "diagram_type_context": f"Basic {state.diagram_type} syntax",
            "diagram_type": state.diagram_type
        }

def should_retry(state: Diagram_ManagerState) -> Literal["generate_diagram", "end"]:
    """
    Decide whether to retry generation or end based on validation.
    """
    validation = state.validation_result
    print(f'validation: {validation}')
    
    if validation.get("valid", False):
        return "end"
    
    if state.iteration_count >= state.max_iterations:
        return "end"
    
    return "generate_diagram"

def route_by_action(state: Diagram_ManagerState) -> str:
    """
    Route based on action stored in state.
    """
    action = state.action
    print(f"🛣️  Routing based on action: {action}")
    
    # Fallback logic
    if not action:
        print("⚠️  No action found, defaulting to generate")
        return "generate"
    
    return action

def build_diagram_agent():
    """Build and return the compiled LangGraph agent with action-based routing."""
    agent_builder = StateGraph(Diagram_ManagerState)
    
    # Add nodes
    agent_builder.add_node('detect_intent', detect_intent)
    agent_builder.add_node('diagram_syntax_reference', diagram_syntax_reference)
    agent_builder.add_node('generate_diagram', generate_diagram)
    agent_builder.add_node('validate_mermaid', validate_mermaid)
    agent_builder.add_node('describe_diagram', describe_diagram)
    agent_builder.add_node('transform_diagram', transform_diagram)
    
    # Start with intent detection
    agent_builder.add_edge(START, 'detect_intent')
    
    # Routing based on action in state
    agent_builder.add_conditional_edges(
        'detect_intent',
        route_by_action,
        {
            "generate": "diagram_syntax_reference",
            "describe": "describe_diagram", 
            "transform": "transform_diagram"
        }
    )
    
    # Generate flow
    agent_builder.add_edge('diagram_syntax_reference', 'generate_diagram')
    agent_builder.add_edge('generate_diagram', 'validate_mermaid')
    
    # Transform flow 
    agent_builder.add_edge('transform_diagram', 'validate_mermaid')
    
    # Validation decision
    agent_builder.add_conditional_edges(
        'validate_mermaid',
        should_retry,
        {
            "generate_diagram": "generate_diagram",
            "end": END
        }
    )
    
    # Describe goes directly to end
    agent_builder.add_edge('describe_diagram', END)
    
    return agent_builder.compile()