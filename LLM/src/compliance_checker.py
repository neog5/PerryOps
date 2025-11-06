"""
Compliance checker module for auditing medical instructions against clinical guidelines.
"""

import json
from src.ollama_client import call_ollama_api


def _extract_json(raw_text: str):
    """
    Extract JSON from model output that may include markdown code blocks.
    
    Args:
        raw_text: Raw text output from model
        
    Returns:
        dict: Parsed JSON object, or None if parsing fails
    """
    if not raw_text:
        return None
    
    text = raw_text.strip()
    
    # Remove markdown code blocks
    if text.startswith("```") and text.endswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    
    # Try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON object from text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                return None
        return None


def check_guideline_compliance(
    structured_data, 
    guideline_sections, 
    *, 
    model_name="amsaravi/medgemma-4b-it:q8", 
    max_section_chars=2000
):
    """
    Iteratively audit each instruction: model picks headings, then audits against content.
    
    Args:
        structured_data: Structured medical report data with medications and instructions
        guideline_sections: List of guideline sections with headings and content
        model_name: Ollama model to use for compliance checking
        max_section_chars: Maximum characters to include from each section
        
    Returns:
        dict: Compliance report with summary and flagged items
    """
    if not structured_data:
        print("Structured report data is required for compliance checking.")
        return None
    
    if not guideline_sections:
        print("Guideline sections are required for compliance checking.")
        return None

    def _truncate(text: str) -> str:
        """Truncate text to max_section_chars."""
        if max_section_chars and len(text) > max_section_chars:
            return text[:max_section_chars].rstrip() + "..."
        return text

    def _heading_summary():
        """Create a summary of available guideline headings."""
        lines = []
        for idx, section in enumerate(guideline_sections, start=1):
            heading = section.get("heading", "") or "(missing heading)"
            page = section.get("page")
            lines.append(f"- H{idx} | {heading} (page {page})")
        return "\n".join(lines)

    def _select_relevant_headings(item_bundle, heading_summary_text):
        """Ask model to pick which heading IDs are relevant for this item."""
        prompt = (
            "You are choosing which guideline headings are relevant for one perioperative instruction.\n"
            "Instruction JSON:\n"
            f"{json.dumps(item_bundle, indent=2)}\n\n"
            "AVAILABLE GUIDELINE HEADINGS (IDs and titles):\n"
            f"{heading_summary_text}\n\n"
            "Pick ALL relevant heading IDs (you can pick multiple if needed).\n"
            "Return only JSON: {\"selected_heading_ids\": [<ids>]} with the IDs in relevance order."
        )
        
        response_text = call_ollama_api(
            prompt,
            model_name,
            output_format="json",
        )
        
        parsed = _extract_json(response_text)
        if not parsed:
            return []
        
        ids = parsed.get("selected_heading_ids")
        if not isinstance(ids, list):
            return []
        
        cleaned = []
        for entry in ids:
            if isinstance(entry, str) and entry.strip():
                cleaned.append(entry.strip())
        
        return cleaned

    def _audit_item(item_bundle, selected_sections):
        """Audit one item against content from selected sections."""
        # Build simple content string from selected sections
        content_parts = []
        for section in selected_sections:
            heading = section.get("heading", "Unknown")
            content = _truncate(section.get("content", ""))
            content_parts.append(f"### {heading}\n{content}")
        
        combined_content = "\n\n".join(content_parts)
        
        prompt = (
            "You are a strict medical compliance auditor checking ONE perioperative instruction.\n\n"
            "INSTRUCTION TO AUDIT:\n"
            f"{json.dumps(item_bundle, indent=2)}\n\n"
            "GUIDELINE CONTENT:\n"
            f"{combined_content}\n\n"
            "COMPLIANCE RULES (READ CAREFULLY):\n"
            "1. If instruction says 'Continue' but guideline says 'Hold/Stop', that is NON-COMPLIANT.\n"
            "2. NSAIDs like ibuprofen, naproxen, aspirin, etc. MUST be held before surgery if guidelines say so.\n"
            "3. More conservative = COMPLIANT. Less conservative = NON-COMPLIANT.\n\n"
            "SPECIFIC EXAMPLES:\n"
            "NON-COMPLIANT: Guideline says 'Hold ibuprofen 3 days before surgery' but instruction says 'Continue ibuprofen'\n"
            "COMPLIANT: Guideline says 'Hold 4 days' and instruction says 'Hold 4 days'\n"
            "COMPLIANT: Guideline says 'Hold 2 days' and instruction says 'Hold 3 days' (stricter)\n"
            "NON-COMPLIANT: Guideline says 'Hold 2 days' but instruction says 'Hold day of' (less strict)\n\n"
            "YOUR TASK:\n"
            "Read the instruction and guideline carefully. If the instruction violates the guideline (less safe), return is_compliant=false with issues.\n"
            "If the instruction matches or exceeds the guideline safety, return is_compliant=true with empty issues.\n\n"
            "For NON-COMPLIANT items, you MUST provide:\n"
            "1. The complete corrected entry in the EXACT same format as the original\n"
            "2. A brief explanation of what changed and why\n\n"
            "OUTPUT FORMAT (JSON only):\n"
            "{\n"
            "  \"is_compliant\": boolean,\n"
            "  \"issues\": [{\n"
            "    \"issue\": \"description\",\n"
            "    \"suggested_entry\": {<complete corrected entry in same format>},\n"
            "    \"explanation\": \"one line explanation of what changed and why\"\n"
            "  }]\n"
            "}\n\n"
            "JSON OUTPUT:"
        )
        
        response_text = call_ollama_api(
            prompt,
            model_name,
            output_format="json",
        )
        
        print(f"  [DEBUG] Model response: {response_text[:200]}...")
        
        parsed = _extract_json(response_text) or {}
        
        # Extract is_compliant
        is_compliant = parsed.get("is_compliant")
        if isinstance(is_compliant, str):
            is_compliant = is_compliant.strip().lower() in {"true", "yes", "1"}
        is_compliant = bool(is_compliant)
        
        # Extract issues
        issues = parsed.get("issues")
        if isinstance(issues, list) and issues:
            filtered = [issue for issue in issues if isinstance(issue, dict)]
        else:
            filtered = []
        
        # Only return issues if not compliant AND we have actual issues
        if is_compliant or not filtered:
            return []
        
        # Add metadata from the first selected section
        if selected_sections:
            first_section = selected_sections[0]
            for issue in filtered:
                if "guideline_heading" not in issue:
                    issue["guideline_heading"] = first_section.get("heading")
                if "guideline_page" not in issue:
                    issue["guideline_page"] = first_section.get("page")
        
        return filtered

    heading_summary = _heading_summary()

    # Build list of items to check
    items_to_check = []
    
    for med in structured_data.get("medications_instructions", []) or []:
        if not isinstance(med, dict):
            continue
        name = med.get("medication") or "Unknown medication"
        items_to_check.append({
            "item_type": "medication",
            "name": name,
            "details": med
        })

    general = structured_data.get("general_pre_op_instructions", {}) or {}
    for key, instruction in general.items():
        if not instruction:
            continue
        items_to_check.append({
            "item_type": "general_instruction",
            "name": key,
            "details": {"instruction": instruction}
        })

    # Process each item iteratively
    all_flagged = []
    for item in items_to_check:
        # Step 1: Model picks relevant headings
        heading_ids = _select_relevant_headings(item, heading_summary)
        print(f"[Compliance] {item.get('item_type')} '{item.get('name')}' -> headings {heading_ids or 'none'}")
        
        if not heading_ids:
            continue
        
        # Step 2: Get selected sections
        selected_sections = []
        for hid in heading_ids:
            # Extract index from "H1", "H2", etc.
            if hid.startswith("H") and hid[1:].isdigit():
                idx = int(hid[1:]) - 1
                if 0 <= idx < len(guideline_sections):
                    selected_sections.append(guideline_sections[idx])
        
        if not selected_sections:
            continue
        
        # Step 3: Audit with selected content
        flagged = _audit_item(item, selected_sections)
        for entry in flagged:
            if not isinstance(entry, dict):
                continue
            # Add the original entry details
            entry.setdefault("item_type", item.get("item_type"))
            entry.setdefault("name", item.get("name"))
            entry["old_entry"] = item.get("details")  # Add the complete original entry
            all_flagged.append(entry)

    summary_text = f"Processed {len(items_to_check)} items; flagged {len(all_flagged)} potential issues."
    
    return {
        "compliance_summary": summary_text,
        "flagged_items": all_flagged
    }
