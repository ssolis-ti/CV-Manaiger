import tiktoken

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Returns the number of tokens in a text string.
    Uses encoding for GPT-4o by default.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback for newer models not yet in tiktoken metadata or unknown aliases
        encoding = tiktoken.get_encoding("cl100k_base")
        
    num_tokens = len(encoding.encode(text))
    return num_tokens

def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
    """
    Crude estimation of cost based on public pricing (approximate).
    Update rates as needed.
    """
    # Pricing per 1M tokens (approx as of late 2024/2025)
    # GPT-4o-mini: Input $0.15, Output $0.60
    
    rates = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00}
    }
    
    # Default to mini if unknown
    rate = rates.get(model, rates["gpt-4o-mini"])
    
    input_cost = (input_tokens / 1_000_000) * rate["input"]
    output_cost = (output_tokens / 1_000_000) * rate["output"]
    
    return round(input_cost + output_cost, 6)
