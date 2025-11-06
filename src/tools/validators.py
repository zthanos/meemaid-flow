import re
from typing import Dict, List, Tuple
from core.common_types import Diagram_ManagerState, DiagramType



class SequenceDiagramValidator:
    """Validates sequence diagram specific syntax and semantics."""
    
    def __init__(self):
        self.participants = set()
        self.active_participants = {}  # participant -> activation_count
        
    def validate(self, code: str) -> Tuple[List[str], List[str]]:
        """
        Validate sequence diagram code.
        
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        lines = code.split("\n")
        
        # Track participants
        for line in lines:
            line = line.strip()
            if not line or line.startswith("%%"):
                continue
            
            # Extract participants
            if line.startswith("participant ") or line.startswith("actor "):
                parts = line.split()
                if len(parts) >= 2:
                    participant = parts[1]
                    self.participants.add(participant)
        
        # Validate arrows and activation/deactivation
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("%%"):
                continue
            
            # Check for activation/deactivation syntax
            arrow_errors = self._validate_arrow_line(line, line_num)
            errors.extend(arrow_errors)
        
        # Check for balanced activations
        for participant, count in self.active_participants.items():
            if count != 0:
                if count > 0:
                    warnings.append(
                        f"Participant '{participant}' has {count} unmatched activation(s)"
                    )
                else:
                    errors.append(
                        f"Participant '{participant}' has {abs(count)} extra deactivation(s)"
                    )
        
        return errors, warnings
    
    def _validate_arrow_line(self, line: str, line_num: int) -> List[str]:
        """Validate a line containing an arrow."""
        errors = []
        
        # Pattern for sequence diagram arrows with activation/deactivation
        # Format: Participant1->>+Participant2: Message
        # + = activate, - = deactivate
        arrow_patterns = [
            r'(\w+)\s*->>([+-]?)\s*(\w+)',  # ->>
            r'(\w+)\s*-->>([+-]?)\s*(\w+)', # -->>
            r'(\w+)\s*->([+-]?)\s*(\w+)',   # ->
            r'(\w+)\s*-->([+-]?)\s*(\w+)',  # -->
            r'(\w+)\s*-x([+-]?)\s*(\w+)',   # -x
            r'(\w+)\s*--x([+-]?)\s*(\w+)',  # --x
            r'(\w+)\s*-\)([+-]?)\s*(\w+)',  # -)
            r'(\w+)\s*--\)([+-]?)\s*(\w+)', # --)
        ]
        
        for pattern in arrow_patterns:
            match = re.search(pattern, line)
            if match:
                source = match.group(1)
                modifier = match.group(2)  # +, -, or empty
                target = match.group(3)
                
                # Add implicit participants
                self.participants.add(source)
                self.participants.add(target)
                
                # Initialize activation tracking
                if source not in self.active_participants:
                    self.active_participants[source] = 0
                if target not in self.active_participants:
                    self.active_participants[target] = 0
                
                # Check activation/deactivation
                if '+' in modifier:
                    # Activate target
                    self.active_participants[target] += 1
                elif '-' in modifier:
                    # Deactivate source
                    if self.active_participants[source] <= 0:
                        errors.append(
                            f"Line {line_num}: Trying to deactivate inactive participant '{source}'"
                        )
                    else:
                        self.active_participants[source] -= 1
                
                break
        
        return errors

def validate_mermaid(state: Diagram_ManagerState) -> Dict:
    """
    Validate the generated Mermaid diagram code.
    Returns validation results and errors if any.
    """
    mermaid_code = state.mermaid_code
    errors = []
    warnings = []
    
    # Basic syntax checks
    if not mermaid_code:
        errors.append("No Mermaid code generated")
        return {
            "validation_result": {
                "valid": False,
                "errors": errors,
                "warnings": warnings
            }
        }
    
    # Check if diagram type declaration exists
    diagram_types = [
        "sequenceDiagram", "flowchart", "graph", "classDiagram", 
        "stateDiagram", "erDiagram", "gantt", "pie", "gitGraph"
    ]
    
    has_diagram_type = any(dt in mermaid_code for dt in diagram_types)
    if not has_diagram_type:
        errors.append("Missing diagram type declaration")
    
    # Check for common syntax errors
    lines = mermaid_code.split("\n")
    
    # Check for balanced brackets/parentheses (skip lines with arrows)
    for line_num, line in enumerate(lines, 1):
        # Skip arrow lines for bracket checking (they can have intentional : in them)
        if any(arrow in line for arrow in ['->', '-->>', '-->', '->>', '-x', '--x', '-)', '--)']):
            continue
            
        stack = []
        for char in line:
            if char in '[({':
                stack.append(char)
            elif char in '])}':
                brackets = {'[': ']', '(': ')', '{': '}'}
                if not stack:
                    errors.append(f"Line {line_num}: Unexpected closing bracket '{char}'")
                    break
                opening = stack.pop()
                if brackets[opening] != char:
                    errors.append(f"Line {line_num}: Mismatched brackets")
                    break
        
        if stack:
            errors.append(f"Line {line_num}: Unclosed brackets")
    
    # Diagram-specific validation
    if state.diagram_type == DiagramType.SEQUENCE_DIAGRAM.value:
        validator = SequenceDiagramValidator()
        seq_errors, seq_warnings = validator.validate(mermaid_code)
        errors.extend(seq_errors)
        warnings.extend(seq_warnings)
        
        # Check for valid arrows
        valid_arrows = ["->", "->>", "-->", "-->>", "-x", "--x", "-)", "--)", "->+", "-->+", "->>+", "-->>+"]
        has_arrow = any(arrow in mermaid_code for arrow in valid_arrows)
        if not has_arrow:
            errors.append("No valid sequence diagram arrows found")
    
    elif state.diagram_type == "flowchart":
        # Check for node connections
        if "-->" not in mermaid_code and "---" not in mermaid_code:
            errors.append("No valid flowchart connections found")
        
        # Check for proper node definitions
        node_pattern = r'\w+\[.*?\]|\w+\(.*?\)|\w+\{.*?\}'
        if not re.search(node_pattern, mermaid_code):
            warnings.append("No explicitly defined nodes found (may be using implicit nodes)")
    
    elif state.diagram_type == "classDiagram":
        # Check for class definitions
        if "class " not in mermaid_code and "<<" not in mermaid_code:
            warnings.append("No explicit class definitions found")
    
    elif state.diagram_type == "stateDiagram":
        # Check for state transitions
        if "-->" not in mermaid_code:
            errors.append("No state transitions found")
    
    elif state.diagram_type == "erDiagram":
        # Check for relationships
        relationship_patterns = [r'\|\|--\|\|', r'\}o--o\{', r'\|\|--o\{', r'\}o--\|\|']
        has_relationship = any(re.search(pattern, mermaid_code) for pattern in relationship_patterns)
        if not has_relationship:
            warnings.append("No entity relationships found")
    
    # Check for extremely short diagrams
    non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith("%%")]
    if len(non_empty_lines) < 3:
        warnings.append("Diagram seems too short, may be incomplete")
    
    is_valid = len(errors) == 0
    
    return {
        "validation_result": {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings
        }
    }


def fix_sequence_diagram_activations(code: str) -> str:
    """
    Attempt to automatically fix activation/deactivation issues in sequence diagrams.
    
    Args:
        code: Original Mermaid code
        
    Returns:
        Fixed Mermaid code
    """
    lines = code.split("\n")
    fixed_lines = []
    
    for line in lines:
        # Remove deactivation modifiers that are problematic
        # Replace ->>- with ->> (remove deactivation)
        fixed_line = re.sub(r'(->>|-->|->|-->)([+-])', r'\1', line)
        fixed_lines.append(fixed_line)
    
    return "\n".join(fixed_lines)


# Example usage for testing
if __name__ == "__main__":
    from core.common_types import Diagram_ManagerState
    
    # Test case 1: The problematic code
    test_code = """sequenceDiagram
    participant Client
    participant Server
    participant AuthService

    Client->>+Server: Request for authentication
    Server-->>-Client: Challenge (e.g., nonce)
    Client->>+AuthService: Validate challenge with credentials
    AuthService-->>-Client: Authentication token (JWT)
    Client->>-Server: Submit JWT
    Server->>+Database: Verify JWT signature and claims
    Database-->>-Server: Authorization decision
    Server-->>-Client: Access granted or denied"""
    
    test_state = Diagram_ManagerState(
        user_prompt="test",
        diagram_type="sequenceDiagram",
        mermaid_code=test_code
    )
    
    result = validate_mermaid(test_state)
    
    print("Validation Results:")
    print(f"Valid: {result['validation_result']['valid']}")
    
    if result['validation_result']['errors']:
        print("\nErrors:")
        for error in result['validation_result']['errors']:
            print(f"  ❌ {error}")
    
    if result['validation_result']['warnings']:
        print("\nWarnings:")
        for warning in result['validation_result']['warnings']:
            print(f"  ⚠️  {warning}")
    
    # Try to fix
    print("\n" + "="*80)
    print("Attempting to fix...")
    fixed_code = fix_sequence_diagram_activations(test_code)
    print("\nFixed code:")
    print(fixed_code)