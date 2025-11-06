"""
Model configuration and presets for AWS Bedrock and other LLM services.
"""

MODEL_PRESETS = {
    "qwen32b": "qwen.qwen3-32b-v1:0",
    "llama8b": "meta.llama3-1-8b-instruct-v1:0",
    "llama70b": "meta.llama3-1-70b-instruct-v1:0",
    "amazon-nova-micro": "amazon.nova-micro-v1:0",
    "amazon-nova-pro": "amazon.nova-pro-v1:0",
    # "deepseek-r1": "your-inference-profile-arn-here",
}

# Ollama default settings
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_DEFAULT_MODEL = "amsaravi/medgemma-4b-it:q8"

# AWS Bedrock default settings
AWS_DEFAULT_REGION = "us-east-2"


def get_model_or_profile(key_or_id_or_arn: str):
    """
    Resolve a model preset key to its full model ID or ARN.
    
    Args:
        key_or_id_or_arn: Either a preset key (e.g., 'qwen32b'), 
                         a full model ID, or an inference profile ARN
                         
    Returns:
        str: The resolved model ID or ARN
    """
    if not isinstance(key_or_id_or_arn, str):
        return key_or_id_or_arn
    
    k = key_or_id_or_arn.strip()
    if k in MODEL_PRESETS and MODEL_PRESETS[k]:
        return MODEL_PRESETS[k]
    
    return k
