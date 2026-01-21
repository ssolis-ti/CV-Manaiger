import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.json import JSON

# Append path ensuring backend modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cv_formatter.main import CVProcessor
from cv_formatter.utils.logging_config import setup_logging

def main():
    # Setup Logging (RichHandler will be used automatically)
    setup_logging()
    
    console = Console()
    console.print(Panel.fit("[bold cyan]CV Manaiger: AI Resume Processor[/bold cyan]", border_style="cyan"))

    console.print("[yellow]Paste your CV text below (Press Ctrl+D or Ctrl+Z + Enter to finish):[/yellow]")
    
    # Capture Multi-line Input
    try:
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            lines.append(line)
        raw_text = "\n".join(lines)
    except KeyboardInterrupt:
        console.print("\n[red]Aborted.[/red]")
        return

    if not raw_text.strip():
        console.print("[red]No text provided.[/red]")
        return

    console.print("\n")
    
    processor = CVProcessor()
    
    try:
        # Use a Spinner Status while processing
        with console.status("[bold green]Processing CV with AI Models...[/bold green]", spinner="dots"):
            result = processor.process_cv(raw_text)
        
        console.print("\n[bold green]Success! Analysis Complete.[/bold green]")
        console.print(Panel("Result JSON", expand=False))
        
        # Pretty Print JSON
        console.print(JSON.from_data(result))
        
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
