"""Challenge loader tool for AIRTBench."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any
from smolagents import tool


@tool
def load_challenge(challenge_id: str) -> str:
    """Load a specific challenge by ID and return its notebook content in markdown format.
    
    This tool reads the challenge notebook file and converts it to a readable format
    for the agent to understand the challenge requirements.
    
    Args:
        challenge_id: The ID of the challenge to load (e.g., 'bear1', 'hotdog', 'mirage')
        
    Returns:
        Markdown-formatted challenge content
    """
    # Default to current AIRTBench challenge directory structure
    current_dir = Path(__file__).parent.parent.parent.parent.parent
    challenge_dir = current_dir / "airtbench" / "challenges"
    
    # Load challenges manifest
    manifest_path = challenge_dir / ".challenges.yaml"
    
    if not manifest_path.exists():
        return f"Challenges manifest not found at {manifest_path}"
    
    try:
        with open(manifest_path, 'r') as f:
            challenges_manifest = yaml.safe_load(f)
    except Exception as e:
        return f"Error loading challenges manifest: {str(e)}"
    
    # Validate challenge exists
    if challenge_id not in challenges_manifest:
        available_challenges = list(challenges_manifest.keys())
        return f"Challenge '{challenge_id}' not found. Available challenges: {available_challenges}"
    
    challenge_info = challenges_manifest[challenge_id]
    notebook_file = challenge_info.get("notebook")
    
    if not notebook_file:
        return f"No notebook file specified for challenge '{challenge_id}'"
    
    notebook_path = challenge_dir / notebook_file
    
    if not notebook_path.exists():
        return f"Notebook file not found: {notebook_path}"
    
    try:
        # Load and parse the Jupyter notebook
        with open(notebook_path, 'r') as f:
            notebook_data = json.load(f)
        
        # Convert to markdown format
        markdown_content = _notebook_to_markdown(notebook_data, challenge_info)
        
        return markdown_content
        
    except Exception as e:
        return f"Error loading challenge '{challenge_id}': {str(e)}"


def _notebook_to_markdown(notebook_data: Dict[str, Any], challenge_info: Dict[str, Any]) -> str:
    """Convert Jupyter notebook to markdown format.
    
    Args:
        notebook_data: Parsed notebook JSON data
        challenge_info: Challenge metadata from manifest
        
    Returns:
        Markdown-formatted content
    """
    markdown_lines = []
    
    # Add challenge metadata
    markdown_lines.append(f"# Challenge: {challenge_info.get('name', 'Unknown')}")
    markdown_lines.append(f"**Category:** {challenge_info.get('category', 'Unknown')}")
    markdown_lines.append(f"**Difficulty:** {challenge_info.get('difficulty', 'Unknown')}")
    
    if challenge_info.get('is_llm'):
        markdown_lines.append("**Type:** LLM Challenge")
    
    markdown_lines.append("\n---\n")
    
    # Process notebook cells
    cells = notebook_data.get("cells", [])
    
    for cell in cells:
        cell_type = cell.get("cell_type", "")
        source = cell.get("source", [])
        
        # Convert source to string if it's a list
        if isinstance(source, list):
            source_text = "".join(source)
        else:
            source_text = str(source)
        
        if not source_text.strip():
            continue
        
        if cell_type == "markdown":
            markdown_lines.append(source_text.strip())
            markdown_lines.append("")
            
        elif cell_type == "code":
            markdown_lines.append("```python")
            markdown_lines.append(source_text.strip())
            markdown_lines.append("```")
            markdown_lines.append("")
            
            # Add output if available
            outputs = cell.get("outputs", [])
            for output in outputs:
                if output.get("output_type") == "stream":
                    text = "".join(output.get("text", []))
                    if text.strip():
                        markdown_lines.append("Output:")
                        markdown_lines.append("```")
                        markdown_lines.append(text.strip())
                        markdown_lines.append("```")
                        markdown_lines.append("")
                
                elif output.get("output_type") in ["display_data", "execute_result"]:
                    data = output.get("data", {})
                    if "text/plain" in data:
                        text = "".join(data["text/plain"])
                        if text.strip():
                            markdown_lines.append("Output:")
                            markdown_lines.append("```")
                            markdown_lines.append(text.strip())
                            markdown_lines.append("```")
                            markdown_lines.append("")
    
    return "\n".join(markdown_lines)


class ChallengeLoaderTool:
    """Tool wrapper for challenge loading functionality."""
    
    def __init__(self, challenge_dir: Path = None):
        """Initialize the challenge loader.
        
        Args:
            challenge_dir: Path to the challenges directory
        """
        if challenge_dir is None:
            current_dir = Path(__file__).parent.parent.parent.parent.parent
            challenge_dir = current_dir / "airtbench" / "challenges"
        
        self.challenge_dir = Path(challenge_dir)
    
    def __call__(self, challenge_id: str) -> str:
        """Load challenge by ID."""
        return load_challenge(challenge_id)