from typing import Dict
from core.common_types import Diagram_ManagerState, DiagramType
from core.utils import get_or_generate_syntax
import re # Χρειάζεται για την εξαγωγή του κώδικα
from tools.extract_mermaid_code import extract_mermaid_code



# # --- ΝΕΑ ΣΥΝΑΡΤΗΣΗ ΒΟΗΘΕΙΑΣ ---
# def extract_mermaid_code(prompt: str) -> str:
#     """
#     Extracts the raw Mermaid code block from a user prompt, 
#     which may contain additional instructions.
    
#     Tries to find the block starting with a known diagram type.
#     """
#     # Regex για την εύρεση της αρχής ενός διαγράμματος (π.χ. 'sequenceDiagram', 'graph TD', κλπ.)
#     # και όλα τα περιεχόμενα μέχρι να τελειώσει το block ή το prompt.
#     # Λαμβάνουμε υπόψη ότι μπορεί να υπάρχει Markdown block (```) ή όχι.
    
#     # 1. Έλεγχος για κώδικα μέσα σε Markdown blocks (```mermaid ... ```)
#     markdown_match = re.search(r"```(?:\w*\s)?(sequenceDiagram|flowchart|graph|classDiagram|erDiagram|gantt|pie|stateDiagram|C4\w+).*?```", prompt, re.DOTALL | re.IGNORECASE)
#     if markdown_match:
#         # Επιστρέφουμε το περιεχόμενο του block (αφαιρώντας τα ```)
#         return markdown_match.group(0).replace("```", "").strip()

#     # 2. Έλεγχος για κώδικα χωρίς Markdown blocks, ξεκινώντας από τον τύπο διαγράμματος
#     # Θα βρει την πρώτη εμφάνιση ενός τύπου διαγράμματος και θα συνεχίσει μέχρι το τέλος
#     raw_match = re.search(r"^\s*(sequenceDiagram|flowchart|graph|classDiagram|erDiagram|gantt|pie|stateDiagram|C4\w+).*$", prompt, re.DOTALL | re.IGNORECASE)
#     if raw_match:
#         # Επειδή το DOTALL πιάνει μέχρι το τέλος, επιστρέφουμε το prompt
#         # (αργότερα θα φιλτράρουμε τις οδηγίες)
#         return raw_match.group(0).strip()
    
#     # Αν δεν βρεθεί τυπικό Mermaid, επιστρέφουμε όλο το prompt (το LLM θα το χειριστεί)
#     return prompt.strip()

def transform_diagram(state: Diagram_ManagerState) -> Dict:
    """
    Transform an existing Mermaid diagram to a different type.
    E.g., sequence diagram -> C4 diagram, flowchart -> state diagram, etc.
    """
    # --- ΒΑΣΙΚΗ ΑΛΛΑΓΗ ΕΔΩ: Εξάγουμε τον κώδικα από το user_prompt ---

    full_prompt = state.user_prompt.strip()
    source_code = extract_mermaid_code(full_prompt)
    target_type = state.diagram_type

    
    print(f'source_code \n{source_code}')
    if not source_code:
        return {
            "errors": state.errors + ["No source diagram provided for transformation"],
            "mermaid_code": ""
        }
    
    if not target_type:
        # Αν δεν υπάρχει target_type, δεν μπορούμε να μετατρέψουμε
        # Επιστρέφουμε τον source_code ως έχει.
        return {
            "errors": state.errors + ["No target diagram type specified"],
            "mermaid_code": source_code
        }
    
    # Detect source diagram type
    source_type = None
    # Βελτιωμένη λίστα για να συμπεριλάβει τους C4 τύπους
    mermaid_types = ["sequenceDiagram", "flowchart", "graph", "classDiagram", 
                     "stateDiagram", "erDiagram", "gantt", "pie", "gitGraph", "C4Context", "C4Container", "C4Component"]
                     
    for dt in mermaid_types:
        # Αναζητούμε τον τύπο στην αρχή του εξαγόμενου κώδικα
        if source_code.strip().lower().startswith(dt.lower()):
            source_type = dt
            break
            
    # Αν δεν βρεθεί τύπος, επιστρέφουμε σφάλμα
    if not source_type:
        return {
            "errors": state.errors + ["Could not detect source diagram type in the extracted code"],
            "mermaid_code": source_code
        }
    
    # --- Το υπόλοιπο του κώδικα παραμένει ίδιο, χρησιμοποιώντας το source_code ---
    
    # Get target syntax context
    try:
        # Διασφαλίζουμε ότι το target_type είναι σε μορφή Enum για τη συνάρτηση
        target_type_enum = DiagramType(target_type) 
        target_context = get_or_generate_syntax(state.llm, target_type_enum)
    except:
        target_context = f"Basic {target_type} syntax"
    
    # First, describe the source diagram to understand its meaning
    describe_prompt = f"""Analyze this {source_type} diagram and extract its key information:

Source Diagram:
{source_code}

Provide a structured analysis:
1. Main entities/participants/components
2. Key relationships and interactions
3. Flow and sequence of events
4. Business logic or process depicted
5. Data or state changes

Focus on the MEANING and PURPOSE, not the syntax."""
    
    try:
        print(f"\n{'='*80}")
        print(f"TRANSFORMING: {source_type} → {target_type}")
        print(f"{'='*80}")
        
        # Step 1: Understand source diagram
        describe_response = state.llm.invoke(describe_prompt)
        source_understanding = describe_response.content.strip()
        
        print("\n📊 Source diagram analyzed")
        
        # Step 2: Transform to target type
        transform_prompt = f"""You are a Mermaid diagram expert. Transform the following diagram to a {target_type} diagram.

SOURCE DIAGRAM TYPE: {source_type}
TARGET DIAGRAM TYPE: {target_type}

Understanding of source diagram:
{source_understanding}

Target Diagram Syntax Reference:
{target_context}

Original Source Code (for final check):

{source_code}

TRANSFORMATION GUIDELINES:
- Preserve the core meaning and relationships from the source
- Adapt the representation to fit the target diagram type's semantics
- For sequence → C4: Extract systems/containers and their relationships
- For flowchart → state: Convert decision points and actions to states
- For class → ER: Convert classes to entities and associations to relationships
- Ensure the target diagram is valid and follows proper syntax

Generate ONLY the transformed Mermaid {target_type} code.
Do not include markdown code blocks, explanations, or any other text.
Just the raw Mermaid syntax for the {target_type} diagram."""
        
        # Υποθέτουμε ότι η 'state' έχει πρόσβαση στο 'llm'
        response = state.llm.invoke(transform_prompt)
        transformed_code = response.content.strip()
        
        # Clean up markdown code blocks if present
        if transformed_code.startswith("```"):
            lines = transformed_code.split("\n")
            # Αφαιρούμε την πρώτη και την τελευταία γραμμή (τα ```)
            transformed_code = "\n".join(lines[1:-1]).strip() 
        
        print(f"✅ Transformation complete: {source_type} → {target_type}")
        
        return {
            "mermaid_code": transformed_code,
            "diagram_type": target_type,
            "description": f"Transformed from {source_type} to {target_type}",
            # Υποθέτουμε ότι το iteration_count είναι ένα ακέραιο
            "iteration_count": state.iteration_count + 1 
        }
        
    except Exception as e:
        # Αν αποτύχει η κλήση του LLM ή η διαδικασία
        return {
            "errors": state.errors + [f"Failed to transform diagram: {str(e)}"],
            "mermaid_code": source_code
        }