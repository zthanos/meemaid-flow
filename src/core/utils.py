# core.utils.py
from multiprocessing import get_logger
from pathlib import Path
from langchain_openai import ChatOpenAI
import requests
from bs4 import BeautifulSoup

from core.common_types import DiagramType
from logging import getLogger

logger = getLogger(__name__)
# Constants
TEMPLATES_DIR = Path("templates")

def fetch_page_content(url: str) -> str:
    """Fetch and extract text content from a web page."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        logger.error(f"Failed to fetch content from {url}: {e}")
        raise

def get_url_for_diagram_type(diagram_type: str) -> str:
    # Mapping για specific documentation URLs

    dynamic_url = f"https://mermaid.js.org/syntax/{diagram_type.value}.html"
    logger.warning(f"URL not in mapping for {diagram_type.value}, trying: {dynamic_url}")

    try:
        response = requests.head(dynamic_url, timeout=5)
        if response.status_code == 200:
            logger.info(f"Dynamic URL works: {dynamic_url}")
            return dynamic_url
    except Exception as e:
        logger.debug(f"Dynamic URL check failed: {e}")        

    # Final fallback
    fallback_url = "https://mermaid.js.org/intro/syntax-reference.html"
    logger.warning(f"Falling back to general reference: {fallback_url}")
    return fallback_url



    
def generate_summarized_syntax(llm: ChatOpenAI, content: str, diagram_type: str) -> str:
    """Send content to LLM for summarization of syntax rules."""
    
    prompt = f"""You are a technical documentation assistant. 
Please summarize the Mermaid.js syntax rules for {diagram_type} diagrams from the following documentation.

Focus on:
- Basic syntax structure
- Key commands and keywords
- Common patterns and examples
- Important rules and constraints

Keep the summary concise but complete enough to be used as context for diagram generation.

Documentation content:
{content}

Provide a clear, structured summary:"""
    
    response = llm.invoke(prompt)
    return response.content

def generate_context(llm: ChatOpenAI, diagram_type: DiagramType):
    try:
        logger.info(f"Generating context for {diagram_type.value}...")

        url = get_url_for_diagram_type(diagram_type)
        content = fetch_page_content(url)
        context = generate_summarized_syntax(llm, content, diagram_type)

        context_file = get_file_name(diagram_type)
        with open(context_file, "w", encoding="utf-8") as f:
                f.write(context)            

        logger.info(f"✅ Context saved to {context_file}")
        
    except Exception as e:
        logger.error(f"❌ Unable to generate context for {diagram_type.value}: {e}")
        raise


def generate_context_all(llm):
    for d in DiagramType:
        generate_context(llm, d)


def get_cached_syntax(diagram_type: DiagramType) -> str:
    """
    Get cached syntax context for a diagram type.
    
    Args:
        diagram_type: The diagram type to get context for
        
    Returns:
        Cached syntax context as string
        
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    context_file = get_file_name(diagram_type)
    
    if not context_file.exists():
        raise FileNotFoundError(f"Template file not found: {context_file}")
    
    with open(context_file, "r", encoding="utf-8") as f:
        return f.read()        

def get_or_generate_syntax(llm: ChatOpenAI, diagram_type: DiagramType) -> str:
    """
    Get cached syntax or generate if not available.
    
    Args:
        llm: ChatOpenAI instance for summarization
        diagram_type: The diagram type to get context for
        
    Returns:
        Syntax context as string
    """
    try:
        context = get_cached_syntax(diagram_type)
        logger.info(f"✅ Using cached context for {diagram_type.value}")
        return context
    except FileNotFoundError:
        logger.warning(f"⚠️  Template file not found for {diagram_type.value}. Generating new...")
        generate_context(llm, diagram_type)
        return get_cached_syntax(diagram_type)


def clear_cache(diagram_type: DiagramType = None) -> None:
    """
    Clear cached templates.
    
    Args:
        diagram_type: Specific type to clear, or None to clear all
    """
    if diagram_type:
        # Clear specific type
        context_file = get_file_name(diagram_type)
        if context_file.exists():
            context_file.unlink()
            logger.info(f"🗑️  Cleared cache for {diagram_type.value}")
    else:
        # Clear all
        if TEMPLATES_DIR.exists():
            for file in TEMPLATES_DIR.glob("*.txt"):
                file.unlink()
            logger.info("🗑️  Cleared all cached templates")        



def get_file_name(diagram_type: DiagramType) -> Path:
    """Get the cache file path for a diagram type."""
    # Δημιουργία templates directory αν δεν υπάρχει
    TEMPLATES_DIR.mkdir(exist_ok=True)
    return TEMPLATES_DIR / f"{diagram_type.value}.txt"
