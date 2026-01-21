"""
[MODULE: CONFIGURATION]
Role: Singleton Source of Truth.
Responsibility: specific logic to load environment variables securely.
Flow: User -> .env -> os.environ -> Config Class -> Application.
Warning: Do not hardcode secrets here. Always use os.getenv.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file immediately upon import.
# This ensures that any module importing 'config' has access to loaded vars.
load_dotenv()

class Config:
    """
    Central configuration class.
    Acts as a bridge between the OS environment and the Python application.
    """
    # LLM Credentials (Now supports Inference.net / OpenAI)
    # LLM Credentials (Now supports Inference.net / OpenAI)
    # Default Base Key (fallback)
    _GLOBAL_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Base URL allows switching providers (e.g. OpenAI vs Inference.net vs LocalAI)
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.inference.net/v1")
    
    # --- MODEL CONFIGURATION ---
    # 1. STRUCTURING (ETL/Facts) - Default: Schematron
    MODEL_STRUCTURE = os.getenv("MODEL_STRUCTURE", "google/gemma-3-27b-instruct/bf-16")
    API_KEY_STRUCTURE = os.getenv("API_KEY_STRUCTURE", _GLOBAL_API_KEY)

    # 2. ENRICHMENT (Insights/Ideas) - Default: Gemma 3
    MODEL_ENRICH = os.getenv("MODEL_ENRICH", "google/gemma-3-27b-it")
    API_KEY_ENRICH = os.getenv("API_KEY_ENRICH", _GLOBAL_API_KEY)

    # Deprecated but kept for backward compatibility if needed
    OPENAI_MODEL = MODEL_STRUCTURE
    
    # Path configuration for file operations
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Singleton instance to be imported by other modules
config = Config()
