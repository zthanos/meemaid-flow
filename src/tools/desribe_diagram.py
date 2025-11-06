from typing import Dict
from core.common_types import Diagram_ManagerState, DiagramType
from core.utils import get_or_generate_syntax


def describe_diagram(state: Diagram_ManagerState) -> Dict:
    """
    Describe/explain an existing Mermaid diagram.
    Returns a natural language description of what the diagram represents.
    """
    print("meramaid code")
    mermaid_code = state.user_prompt.strip()
    print(mermaid_code)
    
    if not mermaid_code:
        return {
            "description": "No diagram code provided to describe.",
            "errors": state.errors + ["No mermaid code to describe"]
        }
    print('diagram_type')
    # Get diagram type from code
    diagram_type = state.diagram_type
    if not diagram_type:
        for dt in ["sequenceDiagram", "flowchart", "classDiagram", "stateDiagram", 
                   "erDiagram", "gantt", "pie", "gitGraph"]:
            if dt in mermaid_code:
                diagram_type = dt
                break
    print('context')
    # Get syntax context for better understanding
    context = ""
    if diagram_type:
        try:
            diagram_type_enum = DiagramType(diagram_type)
            print(diagram_type_enum)
            context = get_or_generate_syntax(state.llm, diagram_type_enum)
        except:
            pass
    
    prompt = f"""You are a Mermaid diagram expert. Analyze and describe the following Mermaid diagram in natural language.

{f"Diagram Type: {diagram_type}" if diagram_type else ""}
{f"Syntax Context:\n{context}\n" if context else ""}

Mermaid Code:
```
{mermaid_code}
```

Provide a comprehensive description that includes:
1. What type of diagram this is
2. The main components/participants/nodes
3. The relationships and flows shown
4. The purpose or use case this diagram represents
5. Any notable patterns or design decisions

Be clear, concise, and educational in your explanation."""
    
    try:
        print(f"\n{'='*80}")
        print("DESCRIBING DIAGRAM")
        print(f"{'='*80}")
        
        response = state.llm.invoke(prompt)
        description = response.content.strip()
        
        return {
            "description": description,
            "diagram_type": diagram_type
        }
        
    except Exception as e:
        return {
            "description": f"Failed to describe diagram: {str(e)}",
            "errors": state['errors'] + [f"Failed to describe diagram: {str(e)}"]
        }


