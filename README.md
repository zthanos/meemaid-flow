# mermaid-flow

**Mermaid Diagram Agent** for generating, describing, transforming, and validating Mermaid diagrams using LangGraph and LangChain.

Supports:

* Automatic **intent detection** (generate / describe / transform)
* **Mermaid code extraction** from mixed natural language and code prompts
* **Diagram transformation** (e.g., sequence → C4)
* **Description** of existing diagrams in natural language
* **Validation** of syntax and structure (participants, activations, brackets, etc.)
* **Syntax caching** from mermaid.js.org for better context understanding

---

## Features

* **Intent detection**: Determines whether to generate, describe, or transform a diagram based on keywords and code presence.
* **Mermaid extraction**: Extracts valid Mermaid blocks from markdown or inline text.
* **Generate**: Creates diagrams based on user prompts, using syntax references per diagram type.
* **Describe**: Generates textual explanations of existing diagrams.
* **Transform**: Converts diagrams from one type to another while preserving meaning.
* **Validate & Auto-fix**: Checks syntax and applies minor fixes (e.g., for sequence activations).

---

## Installation

### From PyPI

```bash
pip install mermaid-flow
```

### From Source

```bash
git clone https://github.com/<your-org>/mermaid-flow.git
cd mermaid-flow
pip install -e .
```

---

## Quick Start

```python
from langchain_openai import ChatOpenAI
from mermaid_flow.mermaid_agent import build_diagram_agent
from mermaid_flow.common_types import Diagram_ManagerState

llm = ChatOpenAI(openai_api_base="http://localhost:1234/v1", model="local/any")
agent = build_diagram_agent()

state = Diagram_ManagerState(
    user_prompt="Create a flowchart: Start → Process → Decision → End",
    diagram_type="flowchart",
    llm=llm
)

result = agent.invoke(state)
print(result.mermaid_code)
```

---

## Examples

### 1) Describe an Existing Diagram

````python
state = Diagram_ManagerState(
    user_prompt="""
    ```mermaid
    sequenceDiagram
      participant U as User
      participant S as Server
      U->>S: login
      S-->>U: token
   ```


""",
diagram_type="sequenceDiagram",
llm=llm
)

out = agent.invoke(state)
print(out.description)

````

### 2) Transform a Diagram
````python
state = Diagram_ManagerState(
    user_prompt="""
Convert this to a C4 Container:

```mermaid
    sequenceDiagram
      participant Client
      participant API
      Client->>API: GET /orders
      API-->>Client: 200 OK
    ```

""",
diagram_type="C4Container",
llm=llm
)

out = agent.invoke(state)
print(out.mermaid_code)

````

---

## Architecture & Modules

- **mermaid_agent.py**: Builds the LangGraph workflow: intent → (generate/describe/transform) → validate.
- **detect_intent.py**: Determines user intent based on keywords and context.
- **extract_mermaid_code.py**: Extracts raw Mermaid code from text.
- **generate_diagram.py**: Produces diagrams with syntax-aware prompting.
- **describe_diagram.py**: Analyzes diagrams and produces natural-language summaries.
- **transform_diagram.py**: Converts one diagram type to another.
- **validators.py**: Validates diagram syntax and fixes common errors.
- **utils.py**: Fetches and caches syntax references from mermaid.js.org.
- **common_types.py**: Defines shared types and state management.

---

## Validation Notes

- Sequence validator detects activation/deactivation mismatches.
- Includes `fix_sequence_diagram_activations()` helper for auto-correction.

---

## CLI Usage (Optional)

```python
# mermaid_flow/__main__.py
import sys, json
from langchain_openai import ChatOpenAI
from mermaid_flow.mermaid_agent import build_diagram_agent
from mermaid_flow.common_types import Diagram_ManagerState

def main():
    llm = ChatOpenAI(openai_api_base="http://localhost:1234/v1", model="local/any")
    agent = build_diagram_agent()
    user_prompt = sys.stdin.read()
    state = Diagram_ManagerState(user_prompt=user_prompt, diagram_type="sequenceDiagram", llm=llm)
    out = agent.invoke(state)
    print(json.dumps(out.model_dump(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
````

Usage:

````bash
echo "Describe this:\n\n```mermaid\nsequenceDiagram\nA->>B: ping\n```" | mermaid-flow
````

---

## Roadmap

* Expand support for C4 Context/Container/Component diagrams.
* Add validators for class, state, and ER diagrams.
* Provide prompt presets for common system flows (API, ETL, E2E auth).
* Add optional web preview interface.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Run tests and linters before submitting.
3. Submit a pull request with clear examples and explanation.

---

## License

MIT License (see LICENSE file)

---


### LLM Integration Notes

* The agent expects an `llm` handle in the state (`ChatOpenAI` instance).
* Syntax templates are cached under `templates/<diagram>.txt` and loaded automatically.

---
