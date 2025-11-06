from typing import Dict
from core.common_types import Diagram_ManagerState
import re 

def detect_intent(state: Diagram_ManagerState) -> Dict:
    """
    Detect user intent with improved logic that considers both
    the prompt content and explicit user instructions.
    """
    # ✅ Respect pre-set action
    if state.action and state.action in ["generate", "describe", "transform"]:
        print(f"✓ Action pre-set: {state.action} (skipping intent detection)")
        return {"action": state.action}
    
    user_prompt = state.user_prompt.strip()
    target_diagram_type = state.diagram_type

    # Extract the source diagram type from the code
    source_diagram_type = None
    diagram_type_match = re.search(
        r"^\s*(graph|sequenceDiagram|classDiagram|erDiagram|gitGraph|gantt|pie|stateDiagram|flowchart|C4Context|C4Container|C4Component)", 
        user_prompt, 
        re.IGNORECASE | re.MULTILINE
    )
    
    if diagram_type_match:
        source_diagram_type = diagram_type_match.group(1)
    
    # Analyze user instructions (text before the diagram code)
    user_instructions = user_prompt.lower()
    
    # Keywords for different actions
    transform_keywords = ["convert", "transform", "change to", "into", "generate a c4", "create a c4"]
    describe_keywords = ["describe", "explain", "what does", "what is", "meaning", "analyze", "tell me about"]
    
    has_transform_keyword = any(keyword in user_instructions for keyword in transform_keywords)
    has_describe_keyword = any(keyword in user_instructions for keyword in describe_keywords)
    
    # ✅ IMPROVED LOGIC: Priority order matters
    
    # 1. If explicit describe keywords + has diagram → describe
    if has_describe_keyword and source_diagram_type:
        action = "describe"
        print(f"📖 Intent: {action} (describe keywords found)")
    
    # 2. If transform keywords OR (has source + different target type) → transform
    elif has_transform_keyword or (
        source_diagram_type 
        and target_diagram_type 
        and target_diagram_type not in ["", "unknown"]
        and source_diagram_type.lower() != target_diagram_type.lower()
    ):
        action = "transform"
        print(f"🔄 Intent: {action} (transform detected)")
    
    # 3. If has diagram but no clear instruction → describe (safe default)
    elif source_diagram_type:
        action = "describe"
        print(f"📖 Intent: {action} (default for existing diagram)")
    
    # 4. No diagram found → generate
    else:
        action = "generate"
        print(f"🔨 Intent: {action} (no existing diagram)")

    return {"action": action}