import re
import unicodedata
from cv_formatter.utils.logging_config import get_logger

logger = get_logger(__name__)

def clean_text(text: str) -> str:
    """
    Normalizes and cleans the input text to ensure consistent processing.
    
    Args:
        text (str): Raw input text from the CV.
        
    Returns:
        str: Cleaned and normalized text.
    """
    if not text:
        logger.debug("clean_text received empty input.")
        return ""
    
    logger.debug(f"Cleaning text of size {len(text)}")
    
    # --- STAGE 1: UNICODE NORMALIZATION ---
    # Ensures consistent representation of characters (e.g., 'ñ', 'é').
    # 'NFKC' compatibly decomposes characters which helps in regex matching.
    text = unicodedata.normalize('NFKC', text)
    
    # --- STAGE 2: VISUAL ARTIFACTS REMOVAL ---
    # Replaces fancy designer bullets with standard ASCII dashes.
    # This prepares the text for Markdown-like structure analysis.
    text = re.sub(r'[\u2022\u2023\u25E6\u2043\u2219]', '-', text)
    
    # --- STAGE 3: ENCODING FIXES ---
    text = text.replace('\ufffd', '')
    
    # --- STAGE 4: WHITESPACE COLLAPSE ---
    # Critical step: Reduces "   " to " ".
    # WARNING: We preserve \n because they indicate structure (paragraphs/lists).
    text = re.sub(r'[ \t]+', ' ', text)
    
    # --- STAGE 5: VERTICAL SPACING ---
    # Standardizes paragraph breaks to exactly 2 newlines.
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 6. Trim leading/trailing whitespace
    return text.strip()
