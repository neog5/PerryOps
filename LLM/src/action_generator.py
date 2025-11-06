"""
Action generator module for converting structured medical data into patient-facing actions.
"""

import json
import re
from typing import Optional
from src.bedrock_client import converse_json_only, _extract_json
from utils.datetime_utils import compute_stop_time_datetime


def infer_medication_from_instruction(text: Optional[str]) -> Optional[str]:
    """
    Extract medication or product name from instruction text.
    
    Args:
        text: Instruction text that may contain product names
        
    Returns:
        str: Extracted medication/product name, or None
    """
    if not text or not isinstance(text, str):
        return None
    
    candidates = []
    patterns = [
        r"(?:using|use|with)\s+([A-Za-z0-9\-\s]{3,80})",
        r"apply\s+([A-Za-z0-9\-\s]{3,80})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(1)
            raw = re.split(
                r"[.;,\n]|\b(before|after|prior|night|morning|evening|day)\b", 
                raw, 
                maxsplit=1, 
                flags=re.IGNORECASE
            )[0]
            cleaned = raw.strip()
            if cleaned:
                candidates.append(cleaned)
    
    if not candidates:
        # List for known bath products
        known_products = [
            "chlorhexidine", "hibiclens", "antibacterial soap", "antibacterial wash",
            "sage cloth", "surgical scrub"
        ]
        lower_text = text.lower()
        for product in known_products:
            if product in lower_text:
                return product.title() if product.islower() else product
        return None
    
    # Just shortest candidate for now
    best = min(candidates, key=len)
    return best


def generate_actions_from_json_one_by_one(structured_data, model="qwen.qwen3-32b-v1:0"):
    """
    Generate patient-facing actions from structured report data by prompting 
    AWS Bedrock Converse API one item at a time.

    Output contract (single item per call):
    {
      "task": string,            # One of: "Medications", "Fasting", "Bath", "Alcohol and Tobacco"
      "stop_time": string|null,  # Absolute ISO datetime when applicable, else null
      "note": string,            # 1-2 sentences, plain English for the patient, no markdown
      "medication": string|null  # medications task or bath product if present, else null
    }
    
    Args:
        structured_data: Structured medical report data
        model: Model preset key, ID, or ARN to use
        
    Returns:
        list: List of action dictionaries
    """
    actions = []
    system_prompt = (
        "You convert short clinical instructions into patient-facing JSON. "
        "Always reply with a single JSON object containing exactly the keys task, stop_time, and note."
    )

    def build_prompt(task_label: str, content_block: str):
        return (
            "Return ONLY a JSON object with keys task, stop_time, note. No markdown, no extra text.\n"
            f"- task must be \"{task_label}\".\n"
            "- stop_time: concise phrase like \"4 days before surgery\"; use null if no change.\n"
            "- note: Very short notification (no need to mention the drug/shower/fast etc. just mention the time to surgery) \n\n"
            f"Input:\n{content_block}\n\n"
            "Output: JSON only."
        )

    surgery_details = structured_data.get("surgery_details", {}) or {}

    # Process medications
    for medication in structured_data.get("medications_instructions", []):
        task_label = "Medications"
        content = json.dumps(medication, indent=2)
        prompt = build_prompt(task_label, content)
        
        response_text = converse_json_only(
            prompt,
            model_or_profile=model,
            system_prompt=system_prompt,
            max_tokens=256,
            temperature=0.1,
        )
        
        parsed = _extract_json(response_text)
        if parsed:
            st_phrase = parsed.get("stop_time")
            st_abs = compute_stop_time_datetime(surgery_details, st_phrase)
            
            if st_abs is not None:
                parsed["stop_time"] = st_abs.isoformat()
            else:
                fallback_phrase = medication.get("pre_op_action")
                fallback_dt = compute_stop_time_datetime(surgery_details, fallback_phrase)
                if fallback_dt is not None:
                    parsed["stop_time"] = fallback_dt.isoformat()
                elif isinstance(st_phrase, str) and st_phrase.strip().lower() in {"continue", "as usual", "no change"}:
                    parsed["stop_time"] = None
            
            parsed["medication"] = medication.get("medication")
            actions.append(parsed)
        else:
            print("Invalid JSON response for medication. Raw output:", response_text)

    # Process general instructions
    general = structured_data.get("general_pre_op_instructions", {}) or {}
    key_to_task = {
        "fasting": "Fasting",
        "bathing": "Bath",
        "substance_use": "Alcohol and Tobacco",
    }

    for key, instruction in general.items():
        if not instruction:
            continue
        
        task_label = key_to_task.get(key, "Medications")
        content = f"Task: {key}\nInstruction: {instruction}"
        prompt = build_prompt(task_label, content)
        
        response_text = converse_json_only(
            prompt,
            model_or_profile=model,
            system_prompt=system_prompt,
            max_tokens=256,
            temperature=0.1,
        )
        
        parsed = _extract_json(response_text)
        if parsed:
            st_phrase = parsed.get("stop_time")
            fallback_dt = compute_stop_time_datetime(surgery_details, instruction)
            primary_dt = compute_stop_time_datetime(surgery_details, st_phrase)
            chosen_dt = fallback_dt or primary_dt
            
            if chosen_dt is not None:
                parsed["stop_time"] = chosen_dt.isoformat()
            
            if task_label == "Bath":
                product = infer_medication_from_instruction(instruction) or infer_medication_from_instruction(parsed.get("note"))
                if product:
                    parsed["medication"] = product
            
            actions.append(parsed)
        else:
            print(f"Invalid JSON response for instruction [{key}]. Raw output:", response_text)

    return actions
