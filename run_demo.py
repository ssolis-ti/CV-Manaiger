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

def get_manual_input(console):
    console.print("\n[yellow]Pega el texto de tu CV abajo.[/yellow]")
    console.print("[dim]Escribe [bold white]FIN[/bold white] en una línea nueva y presiona Enter para procesar:[/dim]")
    
    lines = []
    try:
        while True:
            try:
                line = input()
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
            
            # Save to file
            output_file = "cv_output.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
                
            console.print(f"\n[bold green]¡Éxito! Análisis Completado.[/bold green]")
            console.print(f"[blue]JSON guardado en: {output_file}[/blue]")
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
