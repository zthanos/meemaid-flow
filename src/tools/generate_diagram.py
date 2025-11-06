from typing import Dict
from langchain_openai import ChatOpenAI
from core.common_types import Diagram_ManagerState

def generate_diagram(state: Diagram_ManagerState) -> Dict:
    """
    Generate Mermaid diagram code based on user prompt and syntax context.
    Returns updates to be merged into state.
    """
    error_context = ""

    


    previous_code_context = ""
    if state.mermaid_code and state.iteration_count > 0:
        validation_result = state.validation_result
        if validation_result.get("errors"):
            error_context = "\n\n⚠️ PREVIOUS ATTEMPT HAD ERRORS - PLEASE FIX THEM:\n"
            for i, error in enumerate(validation_result["errors"], 1):
                error_context += f"{i}. {error}\n"
            error_context += "\nMake sure to address ALL of these issues in your new diagram.\n"
        
        if validation_result.get("warnings"):
            error_context += "\n⚠️ WARNINGS FROM PREVIOUS ATTEMPT:\n"
            for i, warning in enumerate(validation_result["warnings"], 1):
                error_context += f"{i}. {warning}\n"    

        previous_code_context = f"\n\nPrevious (INVALID) code that failed validation:\n```\n{state.mermaid_code}\n```\n"


    prompt = f"""You are a Mermaid diagram expert. Generate a valid Mermaid diagram based on the user's request.

Syntax Reference for {state.diagram_type}:
{state.diagram_type_context}

User Request: {state.user_prompt}
{f"Description: {state.description}" if state.description else ""}
{previous_code_context}
{error_context}

Generate ONLY the Mermaid diagram code. Start with the diagram type declaration.
Do not include markdown code blocks, explanations, or any other text.
Just the raw Mermaid syntax."""
    
    try:
        response = state.llm.invoke(prompt)
        mermaid_code = response.content.strip()
        
        # Καθάρισμα από markdown code blocks αν υπάρχουν
        if mermaid_code.startswith("```"):
            lines = mermaid_code.split("\n")
            mermaid_code = "\n".join(lines[1:-1]) if len(lines) > 2 else mermaid_code
        
        # Return μόνο τα updates
        return {
            "mermaid_code": mermaid_code,
            "iteration_count": state.iteration_count + 1
        }
        
    except Exception as e:
        # Return updates με error
        return {
            "errors": state.errors + [f"Failed to generate diagram: {str(e)}"],
            "iteration_count": state.iteration_count + 1
        }
