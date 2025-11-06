import re
from typing import Optional

def extract_mermaid_code(prompt: str) -> str:
    """
    Extracts Mermaid code from a prompt that may contain instructions.
    
    Strategy:
    1. Check for markdown code blocks (```...```)
    2. Find line starting with diagram type and extract from there
    3. Stop at first empty line or obvious instruction text
    """
    
    # ============ Method 1: Markdown Code Blocks ============
    # Match: ```mermaid\n...``` or ```\n<diagram_type>...```
    markdown_match = re.search(
        r'```(?:mermaid)?\s*\n?(sequenceDiagram|flowchart|graph|classDiagram|erDiagram|gantt|pie|stateDiagram|C4\w+)(.*?)```',
        prompt,
        re.DOTALL | re.IGNORECASE
    )
    
    if markdown_match:
        diagram_type = markdown_match.group(1)
        content = markdown_match.group(2)
        result = f"{diagram_type}{content}".strip()
        print(f"✓ Extracted from markdown block ({len(result)} chars)")
        return result
    
    # ============ Method 2: Raw Mermaid Code ============
    # Find the diagram type declaration
    diagram_types = [
        'sequenceDiagram', 'flowchart', 'graph TD', 'graph LR', 'graph', 
        'classDiagram', 'erDiagram', 'gantt', 'pie', 'stateDiagram', 
        'gitGraph', 'C4Context', 'C4Container', 'C4Component'
    ]
    
    # Create pattern: find diagram type at start of line
    # Capture everything after it until we hit stopping condition
    for dtype in diagram_types:
        # Pattern: Find diagram type, capture until double newline or end
        pattern = rf'^\s*({re.escape(dtype)})\s*\n((?:(?!\n\s*\n)(?!\n[A-Z][a-z]+:).)*)'
        match = re.search(pattern, prompt, re.MULTILINE | re.DOTALL)
        
        if match:
            diagram_type = match.group(1)
            content = match.group(2)
            result = f"{diagram_type}\n{content}".strip()
            print(f"✓ Extracted raw code ({len(result)} chars)")
            return result
    
    # ============ Method 3: Aggressive Extraction ============
    # Find ANY diagram type and take everything until end or new paragraph
    lines = prompt.split('\n')
    start_idx = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Check if line starts with a diagram type
        for dtype in diagram_types:
            if stripped.startswith(dtype):
                start_idx = i
                break
        if start_idx is not None:
            break
    
    if start_idx is not None:
        # Extract from start until we hit stopping conditions
        extracted_lines = []
        in_diagram = True
        
        for i in range(start_idx, len(lines)):
            line = lines[i]
            
            # Stopping conditions
            if in_diagram:
                # Empty line
                if not line.strip():
                    # Check next line - if it looks like instruction, stop
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Instructions often start with capital letter and are not indented
                        if next_line and next_line[0].isupper() and ':' not in next_line:
                            break
                    extracted_lines.append(line)
                    continue
                
                # Line with diagram content
                extracted_lines.append(line)
            
        result = '\n'.join(extracted_lines).strip()
        if result:
            print(f"✓ Extracted via line-by-line ({len(result)} chars)")
            return result
    
    # ============ Fallback ============
    print("⚠ Could not extract - returning full prompt")
    return prompt.strip()


# ================== TESTS ==================
def run_tests():
    print("="*80)
    print("TESTING MERMAID CODE EXTRACTION")
    print("="*80 + "\n")
    
    tests = [
        # Test 1: Simple markdown
        ("""
```mermaid
sequenceDiagram
    Alice->>Bob: Hello
```
""", "Test 1: Markdown block"),
        
        # Test 2: Your exact case
        ("""
Describe the following diagram in detail:
sequenceDiagram
    participant U as User
    participant S as Server
    participant A as Authentication Service

    U->>+S: Request login
    S-->>-U: Redirect to login page

    U->>+S: Submit credentials
    S->>+A: Validate credentials
    A-->>-S: Token generation request
    S->>+A: Generate JWT token
    A-->>-S: Send JWT token
    S-->>-U: Return JWT token

    U->>+S: Request protected resource with JWT token
    S->>+A: Validate JWT token
    A-->>-S: Token is valid
    S-->>-U: Access granted
""", "Test 2: Your exact case"),
        
        # Test 3: Instructions after
        ("""
sequenceDiagram
    Alice->>Bob: Hello

Please explain this diagram.
""", "Test 3: Instructions after"),
        
        # Test 4: Flowchart
        ("""
Convert this to C4:

flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
""", "Test 4: Flowchart with instructions"),
    ]
    
    for prompt, description in tests:
        print(f"\n{description}")
        print("-" * 80)
        result = extract_mermaid_code(prompt)
        print("\nExtracted:")
        print(result)
        print("\n" + "="*80)


if __name__ == "__main__":
    run_tests()