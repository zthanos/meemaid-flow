import argparse
import logging
from pathlib import Path

from core.common_types import DiagramType, Diagram_ManagerState
from core.utils import  generate_context, clear_cache, generate_context_all
from mermaid_agent import build_diagram_agent

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def create_diagram(
    llm: ChatOpenAI,
    prompt: str,
    diagram_type: str,
    description: str = "",
    output_file: str = None
):
    """
    Create a Mermaid diagram using the agent.
    
    Args:
        llm: ChatOpenAI instance
        prompt: User prompt describing the diagram
        diagram_type: Type of diagram to create
        description: Additional description
        output_file: Optional file to save the diagram
    """

    
    logger.info(f"Creating {diagram_type} diagram...")
    
    # Build and run agent
    agent = build_diagram_agent()
    
    initial_state = Diagram_ManagerState(
        user_prompt=prompt,
        diagram_type=diagram_type,
        description=description,
        llm=llm
    )
    
    result : Diagram_ManagerState = agent.invoke(initial_state)
    
    # Print results
    print("\n" + "=" * 80)
    print("Generated Mermaid Diagram:")
    print("=" * 80)
    print(result['mermaid_code'])
    print("=" * 80)
    
    # Validation results
    validation = result['validation_result']
    if validation.get("valid"):
        print("✅ Validation: PASSED")
    else:
        print("❌ Validation: FAILED")
        if validation.get("errors"):
            print("\nErrors:")
            for error in validation["errors"]:
                print(f"  - {error}")
    
    if validation.get("warnings"):
        print("\nWarnings:")
        for warning in validation["warnings"]:
            print(f"  ⚠️  {warning}")
    
    print(f"\nIterations: {result['iteration_count']}/{result['max_iterations']}")
    
    if result['errors']:
        print("\nSystem Errors:")
        for error in result['errors']:
            print(f"  ❌ {error}")
    
    # Save to file if specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.mermaid_code)
        
        print(f"\n💾 Diagram saved to: {output_path}")
    
    print("\n🌐 Visualize at: https://mermaid.live/")
    
    return result


def main():
    """Main entry point for the application."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Mermaid Diagram Manager - Generate diagrams and manage templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a diagram
  python main.py --create "User login flow" --type sequenceDiagram -o output.mmd
  
  # Generate all templates
  python main.py --generate-all
  
  # Generate specific template
  python main.py --generate flowchart --use-openai
  
  # Clear cache
  python main.py --clear
        """
    )
    
    # Diagram creation arguments
    create_group = parser.add_argument_group('Diagram Creation')
    create_group.add_argument(
        "--create",
        type=str,
        metavar="PROMPT",
        help="Create a diagram with the given prompt"
    )
    create_group.add_argument(
        "--type",
        type=str,
        choices=[d.value for d in DiagramType],
        default="flowchart",
        help="Type of diagram to create (default: flowchart)"
    )
    create_group.add_argument(
        "--description",
        type=str,
        default="",
        help="Additional description for the diagram"
    )
    create_group.add_argument(
        "-o", "--output",
        type=str,
        metavar="FILE",
        help="Output file to save the diagram (e.g., diagram.mmd)"
    )
    create_group.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum number of generation iterations (default: 3)"
    )
    
    # Template management arguments
    template_group = parser.add_argument_group('Template Management')
    template_group.add_argument(
        "--generate-all",
        action="store_true",
        help="Generate all diagram type templates"
    )
    template_group.add_argument(
        "--generate",
        type=str,
        choices=[d.value for d in DiagramType],
        help="Generate specific diagram type template"
    )
    template_group.add_argument(
        "--clear",
        action="store_true",
        help="Clear all cached templates"
    )
    template_group.add_argument(
        "--clear-type",
        type=str,
        choices=[d.value for d in DiagramType],
        help="Clear specific diagram type template"
    )
    
    # LLM configuration
    llm_group = parser.add_argument_group('LLM Configuration')
    llm_group.add_argument(
        "--use-openai",
        action="store_true",
        help="Use OpenAI instead of local LLM"
    )
    llm_group.add_argument(
        "--model",
        type=str,
        help="Specific model to use (default: gpt-4o-mini for OpenAI, deepseek-coder-v2-lite-instruct for local)"
    )
    llm_group.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:1234/v1",
        help="Base URL for local LLM (default: http://localhost:1234/v1)"
    )
    
    args = parser.parse_args()
    
    # Initialize LLM
    if args.use_openai:
        model = args.model or "gpt-4o-mini"
        llm = ChatOpenAI(
            model=model,
            temperature=0
        )
        logger.info(f"Using OpenAI API with model: {model}")
    else:
        model = args.model or "deepseek-coder-v2-lite-instruct"
        llm = ChatOpenAI(
            base_url=args.base_url,
            model=model, 
            api_key="sk-1234",
            temperature=0
        )
        logger.info(f"Using local LLM at {args.base_url} with model: {model}")
    
    # Execute commands
    if args.create:
        # Create diagram
        create_diagram(
            llm=llm,
            prompt=args.create,
            diagram_type=args.type,
            description=args.description,
            output_file=args.output
        )
    elif args.clear:
        clear_cache()
    elif args.clear_type:
        diagram_type = next(d for d in DiagramType if d.value == args.clear_type)
        clear_cache(diagram_type)
    elif args.generate_all:
        generate_context_all(llm)
    elif args.generate:
        diagram_type = next(d for d in DiagramType if d.value == args.generate)
        generate_context(llm, diagram_type)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()