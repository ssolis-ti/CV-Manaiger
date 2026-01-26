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

def safe_input(console, prompt: str) -> str:
    """Safely captures input handling potential encoding errors."""
    try:
        return console.input(prompt)
    except UnicodeDecodeError:
        # Fallback for Windows consoles with bad encoding
        return input(prompt)

def get_manual_input(console):
    console.print(Panel(
        "[yellow]INSTRUCCIONES:[/yellow]\n"
        "1. Copia el texto de tu CV.\n"
        "2. Pégalo aquí abajo (puede ocupar muchas líneas).\n"
        "3. Cuando termines, escribe [bold white]///[/bold white] (tres barras) o [bold white]EOF[/bold white] en una línea nueva y presiona Enter.\n"
        "[dim]Nota: No uses 'FIN' ni 'END' ya que podrían ser parte del texto.[/dim]",
        title="Entrada Manual",
        border_style="blue"
    ))
    
    cv_lines = []
    line_count = 0
    try:
        while True:
            try:
                line = safe_input(console, f"[dim]Línea {line_count+1}:[/dim] ")
            except EOFError:
                break
            
            # Check for SENTINEL
            stripped = line.strip().upper()
            if stripped in ["///", "EOF"]:
                break
                
            cv_lines.append(line)
            line_count += 1
            
            # User Feedback (only update every 10 lines to reduce flicker)
            if line_count % 10 == 0:
                sys.stdout.write(f"\r\033[K[dim]Líneas capturadas: {line_count}[/dim]")
                sys.stdout.flush()
            
        console.print(f"\n[green]¡Captura finalizada! {len(cv_lines)} líneas recibidas.[/green]\n")
        return "\n".join(cv_lines)
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
    
    # Show Active Configuration
    from cv_formatter.config import config
    console.print(f"[dim]🔌 Provider: {config.OPENAI_BASE_URL}[/dim]")
    console.print(f"[dim]🧠 Structure Model: {config.MODEL_STRUCTURE}[/dim]")
    console.print(f"[dim]✨ Enrichment Model: {config.MODEL_ENRICH}[/dim]")

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

        # --- VERIFICATION STEP ---
        clean_preview = raw_text.strip()
        preview_start = clean_preview[:200].replace('\n', ' ')
        preview_end = clean_preview[-200:].replace('\n', ' ')
        
        console.print(Panel(
            f"[bold]Inicio:[/bold] {preview_start}...\n\n"
            f"[bold]Fin:[/bold] ...{preview_end}\n\n"
            f"[dim]Total: {len(raw_text)} caracteres[/dim]",
            title="Vista Previa del Texto Capturado",
            border_style="yellow"
        ))
        
        if Prompt.ask("¿Es este el texto completo?", choices=["s", "n"], default="s") != "s":
            console.print("[yellow]Operación cancelada. Intenta copiar nuevamente.[/yellow]")
            continue
            
        # PROCESS
        processor = CVProcessor()
        try:
            with console.status("[bold green]Procesando CV con Inteligencia Artificial...[/bold green]", spinner="dots"):
                result = processor.process_cv(raw_text)
            
            # Result is now a dict { "source_cv": ..., "enrichment": ... }
            cv_data = result["source_cv"]
            enrichment_data = result["enrichment"]
            
            # --- PHASE 6 VISUALIZATION: ATS & TRIAGE ---
            ats_data = cv_data.get('ats_analysis', {})
            if ats_data:
                score_color = "green" if ats_data.get('score', 0) > 80 else "yellow" if ats_data.get('score', 0) > 50 else "red"
                ats_panel = Panel(
                    f"Score: [{score_color}]{ats_data.get('score', 0)}/100[/{score_color}]\n" + 
                    f"Parsable: {'✅' if ats_data.get('is_parsable') else '❌'}\n" +
                    f"Issues: {len(ats_data.get('issues', []))}\n" +
                    f"[dim]{', '.join(ats_data.get('issues', [])[:3])}[/dim]",
                    title="🕵️ ATS Inspector",
                    border_style="blue"
                )
                console.print(ats_panel)

            # Generate dynamic filename
            import re
            from datetime import datetime
            
            # Extract candidate name safe for filename
            raw_name = cv_data.get('full_name', 'Unknown_Candidate')
            # 1. Replace one or more spaces with a SINGLE underscore
            safe_name = re.sub(r'\s+', '_', raw_name.strip())
            # 2. Remove any remaining non-alphanumeric chars (except underscore and dash)
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', safe_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Ensure output directory exists
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            base_filename = os.path.join(output_dir, f"CV_{safe_name}_{timestamp}")
            
            # 1. Save Source JSON (Validation Facts)
            output_json = f"{base_filename}.json"
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(cv_data, f, indent=2, ensure_ascii=False)
            
            # 2. Save Insights JSON (Enrichment) - if available
            output_insights = f"{base_filename}_INSIGHTS.json"
            if enrichment_data:
                with open(output_insights, "w", encoding="utf-8") as f:
                    json.dump(enrichment_data, f, indent=2, ensure_ascii=False)
            
            # 3. Save Markdown (Source CV)
            md_output = json_to_markdown(cv_data)
            output_md = f"{base_filename}.md"
            with open(output_md, "w", encoding="utf-8") as f:
                f.write(md_output)

            console.print(f"\n[bold green]¡Éxito! Análisis Completado.[/bold green]")
            
            # Show Insight Preview if available
            if enrichment_data:
                # PHASE 6.5: TIMELINE & SWOT
                timeline = enrichment_data.get('timeline_analysis', {})
                profile = enrichment_data.get('profile_signals', {})
                market = enrichment_data.get('market_signals', {})
                
                # Stack
                stack = market.get('stack_detected', [])
                
                insight_text = f"[bold yellow]Stack Detectado:[/bold yellow] {', '.join(stack[:6])}...\n\n"
                
                if timeline:
                    insight_text += f"[bold cyan]Timeline Logic (Math):[/bold cyan]\n"
                    insight_text += f"• Exp Total: {timeline.get('total_years_experience')} años\n"
                    insight_text += f"• Estabilidad: {timeline.get('stability_score')}/10 | Promedio: {timeline.get('avg_tenure_months')} meses/rol\n"
                    if timeline.get('detected_gaps'):
                        insight_text += f"• [red]GAPS:[/red] {len(timeline['detected_gaps'])} detectados.\n"
                    insight_text += "\n"
                
                if profile:
                    insight_text += f"[bold magenta]SWOT (LLM):[/bold magenta]\n"
                    if profile.get('strengths'):
                        insight_text += f"• ✅ {profile['strengths'][0]}\n"
                    if profile.get('risk_flags'):
                        insight_text += f"• 🚩 {profile['risk_flags'][0]}\n"
                    
                console.print(Panel(insight_text, title="🤖 Insights de Gemma 3 (Enrichment v2)", border_style="magenta"))
            
            # Ask to continue
            if not Prompt.ask("\n¿Procesar otro CV?", choices=["y", "n"], default="y") == "y":
                break
                
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
