import os
import json
import logging
from cv_formatter.enricher.engine import EnrichmentService
import sys
from cv_formatter.utils.logging_config import setup_logging
# Mock the User's Provided JSON (Flawed extraction: Empty Skills, Floating Dates)
FLAWED_JSON = {
  "id": "dexmaxilion-urban-desideleo",
  "full_name": "DEXMAXILION URBAN DESIDELEO",
  "email": "TEEST@gmail.com",
  "location": "Chile",
  "summary": "Técnico de Soporte TI N1–N2...",
  "metadata": { "risk_flags": [], "strength_signals": [] },
  "experience": [],
  "education": [],
  "skills": { "hard_skills": [], "soft_skills": [] },  # <--- EMPTY!
  "raw_text": "DEXMAXILION URBAN DESIDELEO ... SKILLS Soporte TI: Soporte N1/N2 ... Sistemas: Windows 10/11, Windows Server básico, Active Directory ... Herramientas: Jira, Zendesk, ServiceNow ..." # <--- DATA IS HERE
}

def run_debug():
    setup_logging()
    print("Running Enrichment on Flawed JSON (Empty Hard Skills)...")
    
    enricher = EnrichmentService()
    
    # Run Enrichment
    try:
        result = enricher.enrich_cv(FLAWED_JSON, FLAWED_JSON["id"])
        
        if result:
            print("[SUCCESS] Enrichment returned data!")
            
            # Check if Gemma found the stack that Schematron missed
            stack = result.market_signals.stack_detected
            tools = result.market_signals.tools_detected
            
            print(f"Stack Detected (Gemma): {stack}")
            print(f"Tools Detected (Gemma): {tools}")
            
            if "Windows" in str(stack) or "Jira" in str(tools):
                print("\n[VERDICT] ✅ SUCCESS: Gemma rescued the data from raw_text!")
            else:
                print("\n[VERDICT] ❌ FAILURE: Gemma also missed the stack.")
                
        else:
            print("[FAILURE] Enrichment returned None")
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")

if __name__ == "__main__":
    run_debug()
