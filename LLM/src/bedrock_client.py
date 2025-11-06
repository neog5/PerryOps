"""
AWS Bedrock client for medical data extraction and LLM inference.
"""

import os
import json
import boto3
from config.model_config import MODEL_PRESETS, get_model_or_profile


def _get_bedrock_client_and_kwargs(model_or_profile: str):
    """
    Return a Bedrock client and kwargs for converse based on model/profile input.
    
    Args:
        model_or_profile: Model ID or inference profile ARN
        
    Returns:
        tuple: (boto3 client, dict of invoke kwargs)
    """
    if isinstance(model_or_profile, str) and model_or_profile.startswith("arn:aws:bedrock:") and ":inference-profile/" in model_or_profile:
        arn_parts = model_or_profile.split(":")
        region = arn_parts[3] if len(arn_parts) > 3 else None
        client = boto3.client('bedrock-runtime', region_name=region) if region else boto3.client('bedrock-runtime')
        return client, {"inferenceProfileArn": model_or_profile}
    
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-2"
    client = boto3.client('bedrock-runtime', region_name=region)
    return client, {"modelId": model_or_profile}


def _extract_json(text: str):
    """
    Extract JSON from model output that may include markdown code blocks.
    
    Args:
        text: Raw text output from model
        
    Returns:
        dict: Parsed JSON object, or None if parsing fails
    """
    t = text.strip()

    if t.startswith("```") and t.endswith("```"):
        t = t.strip("`").strip()
    
    # direct parsing
    try:
        return json.loads(t)
    except Exception:
        pass
    
    # Try to extract JSON object from text
    start = t.find("{")
    if start == -1:
        return None
    
    depth = 0
    for i, ch in enumerate(t[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                candidate = t[start:i+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    break
    
    return None


def structure_data_with_bedrock(text_content, model_or_profile="qwen.qwen3-32b-v1:0"):
    """
    Sends text to AWS Bedrock using the Converse API to extract structured data.
    
    Args:
        text_content: Raw text extracted from medical report
        model_or_profile: Friendly key (e.g., 'qwen32b'), a modelId, or an inference profile ARN
        
    Returns:
        dict: Structured JSON data extracted from the text, or None if extraction fails
    """
    if not text_content:
        print("Error: No text content provided to structure.")
        return None

    model_or_profile = get_model_or_profile(model_or_profile)
    if model_or_profile == "deepseek-r1" or (model_or_profile in MODEL_PRESETS and MODEL_PRESETS[model_or_profile] is None):
        print("DeepSeek preset requires an inference profile ARN for your account/region. Provide its ARN.")
        return None
    
    system_prompt = """You are an automated medical information extraction engine. Your sole and exclusive purpose is to analyze medical text and convert it into a perfectly structured JSON object. You must never output any text, explanation, or conversational-style content. Your entire response must be only the valid JSON object based on the user's requested schema. If you cannot find information, you must use null as the value and not invent data.

Field-specific guidelines:
1) medications_instructions (list):
- "medication": drug name (+ dose only if specified, e.g., "Metformin 500mg").
- "pre_op_action": the surgery-related action (e.g., "Hold 7 hours before surgery", "Continue").

Rules:
- "Atenolol - Continue" -> medication="Atenolol", pre_op_action="Continue".
- "Metformin 500mg daily - Hold one day before surgery" -> medication="Metformin", pre_op_action="Hold 1 day before surgery".

2) general_pre_op_instructions:
- "fasting": not eating/drinking instructions
- "bathing": shower/bathing instructions
- "substance_use": smoking/alcohol restrictions

If information is missing, use null. Output must be only the JSON object."""

    user_prompt = f"""
Analyze the following medical report text and extract the relevant information into a JSON object.
The JSON should strictly follow this structure:
{{
  "patient_info": {{
    "age": "number | null",
    "sex": "string | null",
    "bmi": "number | null"
  }},
  "surgery_details": {{
    "procedure": "string | null",
    "date": "string (YYYY-MM-DD) | null",
    "time": "string (HH:MM) | null"
  }},
  "medications_instructions": [
    {{
      "medication": "string | null",
      "pre_op_action": "string | null"
    }}
  ],
  "general_pre_op_instructions": {{
    "fasting": "string | null",
    "bathing": "string | null",
    "substance_use": "string | null"
  }}
}}

Report Text:
---
{text_content}
---

JSON Output:
"""

    system = [{"text": system_prompt}]
    messages = [{"role": "user", "content": [{"text": user_prompt}]}]

    client, invoke_kwargs = _get_bedrock_client_and_kwargs(model_or_profile)
    inference_config = {"maxTokens": 2048, "temperature": 0.1, "topP": 0.9}

    try:
        response = client.converse(
            system=system, 
            messages=messages, 
            inferenceConfig=inference_config, 
            **invoke_kwargs
        )
        
        output = response.get("output", {})
        message = output.get("message", {})
        content = message.get("content", [])
        texts = [part.get("text") for part in content if isinstance(part, dict) and part.get("text")]
        generated_text = "\n".join(texts) if texts else None
        
        if not generated_text:
            print(f"Unexpected converse response: {response}")
            return None
        
        structured_data = _extract_json(generated_text)
        if structured_data is None:
            print("Error parsing JSON from model output. Raw output follows:\n", generated_text[:1000])
            return None
        
        return structured_data
        
    except Exception as e:
        print(f"Error calling Bedrock Converse API: {e}")
        return None


def converse_json_only(prompt_text, model_or_profile="qwen.qwen3-32b-v1:0", system_prompt=None, *, max_tokens=512, temperature=0.2):
    """
    Helper to call Bedrock Converse for lightweight JSON-formatted responses.
    
    Args:
        prompt_text: The prompt to send to the model
        model_or_profile: Model preset key, ID, or ARN
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        
    Returns:
        str: Raw text response from the model, or None if call fails
    """
    if not prompt_text:
        return None

    model_or_profile = get_model_or_profile(model_or_profile)
    if model_or_profile == "deepseek-r1" or (model_or_profile in MODEL_PRESETS and MODEL_PRESETS[model_or_profile] is None):
        print("DeepSeek preset requires an inference profile ARN for your account/region. Provide its ARN.")
        return None

    client, invoke_kwargs = _get_bedrock_client_and_kwargs(model_or_profile)
    system = [{"text": system_prompt}] if system_prompt else []
    messages = [{"role": "user", "content": [{"text": prompt_text}]}]
    inference_config = {"maxTokens": max_tokens, "temperature": temperature, "topP": 0.9}

    try:
        response = client.converse(
            system=system, 
            messages=messages, 
            inferenceConfig=inference_config, 
            **invoke_kwargs
        )
        
        output = response.get("output", {})
        message = output.get("message", {})
        content = message.get("content", [])
        texts = [part.get("text") for part in content if isinstance(part, dict) and part.get("text")]
        generated_text = "\n".join(texts) if texts else None
        
        if not generated_text:
            print(f"Unexpected converse response: {response}")
            return None
        
        return generated_text
        
    except Exception as e:
        print(f"Error calling Bedrock Converse API: {e}")
        return None
