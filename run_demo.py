import sys
import os
from cv_formatter.main import CVProcessor

def main():
    print("=== CV Manaiger: CLI Demo ===")
    
    # Simple multi-line input
    print("Paste your CV text below (Press Ctrl+D or Ctrl+Z on Windows + Enter to finish):")
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
        print("\nAborted.")
        return

    if not raw_text.strip():
        print("No text provided.")
        return

    print("\nProcessing... Please wait (calling OpenAI)...")
    
    processor = CVProcessor()
    try:
        result = processor.process_cv(raw_text)
        
        print("\n=== RESULT (JSON) ===\n")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
