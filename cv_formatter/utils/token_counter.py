"""
[MODULE: OPTIMIZATION]
Role: Cost & Efficiency Guard.
Responsibility: Estimate token usage before calling expensive APIs.
Flow: Text -> Encoding (Tiktoken) -> Integer Count -> Cost Estimation.
Logic:
- Uses 'tiktoken' to replicate GPT/LLM tokenization rules locally.
- Provides 'estimate_cost' based on configurable pricing (defaulting to GPT-4o-mini rates).
Warning: Pricing is hardcoded ($0.15/$0.60 per 1M). outcomes may vary if model changes.
"""
import tiktoken
import logging

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Returns the exact number of tokens in a text string for a given model.
    
    Logic:
    - Uses 'tiktoken' to get the specific encoding for the requested model.
    - Fallbacks to 'cl100k_base' (standard for GPT-3.5/4) if model is unknown.
    - This is crucial for Pre-flight checks (preventing Context Window errors).
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback for newer models or fine-tuned variants
        encoding = tiktoken.get_encoding("cl100k_base")
        
    num_tokens = len(encoding.encode(text))
    return num_tokens

def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
    """
    Calculates estimated cost based on Usage Pricing (USD).
    
    Rates (approx. Jan 2026):
    - gpt-4o-mini: Input $0.15/1M, Output $0.60/1M
    - gpt-4o:      Input $2.50/1M, Output $10.00/1M
    
    Returns:
        float: Estimated Cost in Dollars ($).
    """
    # Pricing per 1M tokens
    rates = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00}
    }
    
    # Default to mini if unknown
    rate = rates.get(model, rates["gpt-4o-mini"])
    
    input_cost = (input_tokens / 1_000_000) * rate["input"]
    output_cost = (output_tokens / 1_000_000) * rate["output"]
    
    return round(input_cost + output_cost, 6)
