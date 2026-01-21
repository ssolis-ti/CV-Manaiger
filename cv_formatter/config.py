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
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "inference-net/schematron-8b")
    # Base URL allows switching providers (e.g. OpenAI vs Inference.net vs LocalAI)
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.inference.net/v1")
    
    # Path configuration for file operations
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Singleton instance to be imported by other modules
config = Config()
