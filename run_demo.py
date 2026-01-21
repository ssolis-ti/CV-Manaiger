"""
[MODULE: INTERFACE / PRESENTATION]
Role: The 'Frontend' (CLI).
Responsibility: Handle user input, display feedback, and execute the pipeline via the Facade.
Flow: User Interaction (Menu) -> CVProcessor -> Visual Feedback (Rich) -> Output Files.
Logic:
- Uses 'rich' library for a Premium CLI experience (Spinners, Colors, Panels).
- Implements Clipboard integration ('pyperclip') for seamless UX.
- Handles local file I/O (saving JSON/Markdown).
"""
import sys
import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.json import JSON
from rich.prompt import Prompt
import pyperclip

# Append path ensuring backend modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cv_formatter.main import CVProcessor
from cv_formatter.utils.logging_config import setup_logging

def json_to_markdown(data: dict) -> str:
    """Converts the CV JSON into a clean Markdown representation."""
    md = f"# {data.get('full_name', 'Unknown Candidate')}\n\n"
    
    # Metadata Badge
    meta = data.get('metadata', {})
    md += f"> **Seniority:** {meta.get('seniority', 'N/A')} | **Style:** {meta.get('writing_style', 'N/A')}\n"
    md += f"> **AI Summary:** *{meta.get('llm_summary', '')}*\n"
    
    # Signals
    if meta.get('strength_signals'):
        md += f"> ✅ **Strengths:** {', '.join(meta['strength_signals'])}\n"
    if meta.get('risk_flags'):
        md += f"> ⚠️ **Risks:** {', '.join(meta['risk_flags'])}\n"
    
    md += "\n"
    
    # Summary
    if data.get('summary'):
        md += f"## Profile\n{data['summary']}\n\n"
        
    # Experience
    if data.get('experience'):
        md += "## Experience\n"
        for exp in data['experience']:
            md += f"### {exp.get('title')} @ {exp.get('company')}\n"
            md += f"*{exp.get('start_date')} - {exp.get('end_date')}*\n\n"
            md += f"{exp.get('description')}\n"
            if exp.get('impact_metrics'):
                md += "**Impact:** " + ", ".join(exp['impact_metrics']) + "\n"
            md += "\n"
            
    # Education
    if data.get('education'):
        md += "## Education\n"
        for edu in data['education']:
            md += f"- **{edu.get('degree')}**, {edu.get('institution')} ({edu.get('year')})\n"
    
    return md

def get_manual_input(console):
    console.print(Panel(
        "[yellow]INSTRUCCIONES:[/yellow]\n"
        "1. Copia el texto de tu CV.\n"
        "2. Pégalo aquí abajo (puede ocupar muchas líneas).\n"
        "3. Cuando termines, escribe [bold white]FIN[/bold white] en una línea nueva y presiona Enter.",
        title="Entrada Manual",
        border_style="blue"
    ))
    
    cv_lines = []
    line_count = 0
    try:
        while True:
            try:
                line = console.input(f"[dim]Línea {line_count+1}:[/dim] ")
            except EOFError:
                break
            
            # Check for SENTINEL
            if line.strip().upper() in ["END", "FIN"]:
                break
                
            lines.append(line)
            # User Feedback
            sys.stdout.write(f"\r\033[K[dim]Líneas capturadas: {len(lines)}[/dim]")
            sys.stdout.flush()
            
        console.print("\n")
        return "\n".join(lines)
    except KeyboardInterrupt:
        return None

def main():
    # Setup Logging
    setup_logging()
    
    # Force UTF-8 for Windows
    if sys.platform == "win32":
        try:
            sys.stdin.reconfigure(encoding='utf-8')
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
    
    console = Console()
    console.print(Panel.fit("[bold cyan]CV Manaiger: AI Resume Processor[/bold cyan]", border_style="cyan"))

    while True:
        console.print("\n[bold]Menú Principal:[/bold]")
        console.print("1. [green]Pegar desde Portapapeles[/green] (Automático)")
        console.print("2. [yellow]Entrada Manual[/yellow] (Copiar/Pegar en consola)")
        console.print("3. [red]Salir[/red]")
        
        choice = Prompt.ask("Selecciona una opción", choices=["1", "2", "3"], default="1")
        
        raw_text = ""
        
        if choice == "3":
            console.print("[bold red]Saliendo...[/bold red]")
            break
            
        elif choice == "1":
            try:
                raw_text = pyperclip.paste()
                if not raw_text.strip():
                    console.print("[bold red]Error:[/bold red] El portapapeles está vacío o no contiene texto.")
                    continue
                console.print(f"[green]¡Texto detectado en portapapeles! ({len(raw_text)} caracteres)[/green]")
            except Exception as e:
                console.print(f"[bold red]Error de portapapeles:[/bold red] {e}")
                continue

        elif choice == "2":
            raw_text = get_manual_input(console)
            if raw_text is None: # Cancelled
                break
        
        if not raw_text or not raw_text.strip():
            console.print("[red]No se proporcionó texto válido.[/red]")
            continue

        # PROCESS
        processor = CVProcessor()
        try:
            with console.status("[bold green]Procesando CV con Inteligencia Artificial...[/bold green]", spinner="dots"):
                result = processor.process_cv(raw_text)
            
            # Generate dynamic filename
            import re
            from datetime import datetime
            
            # Extract candidate name safe for filename
            raw_name = result.get('full_name', 'Unknown_Candidate')
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', raw_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Ensure output directory exists
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            base_filename = os.path.join(output_dir, f"CV_{safe_name}_{timestamp}")
            
            # Save JSON
            output_json = f"{base_filename}.json"
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Save Markdown
            md_output = json_to_markdown(result)
            output_md = f"{base_filename}.md"
            with open(output_md, "w", encoding="utf-8") as f:
                f.write(md_output)

            console.print(f"\n[bold green]¡Éxito! Análisis Completado.[/bold green]")
            console.print(f"[blue]JSON guardado en: {output_json}[/blue]")
            console.print(f"[blue]Markdown exportado a: {output_md}[/blue]")
            
            console.print(Panel("Vista Previa (Primeras 20 líneas)", expand=False))
            console.print(JSON.from_data(result))
            
            # Ask to continue
            if not Prompt.ask("\n¿Procesar otro CV?", choices=["y", "n"], default="y") == "y":
                break
                
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
