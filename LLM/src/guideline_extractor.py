"""
Guideline extraction module for parsing PDF guidelines and extracting structured sections.
"""

import os
from statistics import median
from typing import List, Dict, Any, Optional
import pdfplumber


# Common markers that appear in PDF font names for bold faces
BOLD_MARKERS = (
    "bold", "semibold", "demi", "black", "heavy", "medium",  # include Medium if needed
    "bd"  # some generators use 'Bd'
)


def is_bold_font(fontname: str) -> bool:
    """Check if a font name indicates a bold face."""
    if not fontname:
        return False
    f = fontname.lower()
    return any(m in f for m in BOLD_MARKERS)


def roundy(y, tol=1.0):
    """Round y-coordinate to tolerance for grouping chars into lines."""
    return round(y / tol) * tol


def build_lines(page) -> List[Dict[str, Any]]:
    """
    Build text lines from char-level data, keeping font size stats and bold ratio.
    
    Args:
        page: pdfplumber page object
        
    Returns:
        list: List of line dictionaries with text, position, and font metadata
    """
    chars = page.chars or []
    if not chars:
        return []

    # Group chars by approximate baseline (top)
    buckets = {}
    for ch in chars:
        key = roundy(float(ch["top"]), tol=1.2)
        buckets.setdefault(key, []).append(ch)

    lines = []
    for key_y, chs in sorted(buckets.items(), key=lambda kv: kv[0]):
        chs_sorted = sorted(chs, key=lambda c: c["x0"])
        text = "".join(c["text"] for c in chs_sorted).strip()
        if not text:
            continue
        
        x0 = min(float(c["x0"]) for c in chs_sorted)
        x1 = max(float(c["x1"]) for c in chs_sorted)
        y_top = min(float(c["top"]) for c in chs_sorted)
        y_bot = max(float(c["bottom"]) for c in chs_sorted)
        
        sizes = [float(c.get("size", 0.0)) for c in chs_sorted if c.get("size") is not None]
        font_size_avg = sum(sizes) / len(sizes) if sizes else None
        
        bold_count = sum(1 for c in chs_sorted if is_bold_font(c.get("fontname", "")))
        
        lines.append({
            "text": " ".join(text.split()),
            "y_top": y_top,
            "y_bottom": y_bot,
            "x0": x0, 
            "x1": x1,
            "font_size_avg": font_size_avg,
            "n_chars": len(chs_sorted),
            "bold_chars": bold_count,
            "bold_ratio": (bold_count / max(1, len(chs_sorted))),
        })
    
    return lines


def compute_line_spacing(lines: List[Dict[str, Any]]) -> float:
    """Compute median line spacing from a list of lines."""
    if len(lines) < 2:
        return 0.0
    gaps = [b["y_top"] - a["y_top"] for a, b in zip(lines, lines[1:])]
    return median([g for g in gaps if g > 0]) if gaps else 0.0


def infer_levels(headings: List[Dict[str, Any]], max_levels: int = 3) -> None:
    """
    Assign hierarchical levels to headings based on font sizes.
    
    Args:
        headings: List of heading dictionaries (modified in-place)
        max_levels: Maximum number of hierarchy levels
    """
    sizes = sorted({h["font_size"] for h in headings if h["font_size"] is not None}, reverse=True)
    if not sizes:
        for h in headings:
            h["level"] = 2
        return
    
    bands = []
    for sz in sizes:
        if not bands or all(abs(sz - b) > 0.5 for b in bands):
            bands.append(sz)
        if len(bands) >= max_levels:
            break
    
    def lvl(sz):
        if sz is None: 
            return max_levels
        for i, b in enumerate(bands, start=1):
            if sz >= b - 0.25:
                return i
        return max_levels
    
    for h in headings:
        h["level"] = lvl(h["font_size"])


def extract_bold_headings(
    pdf_path: str,
    bold_threshold: float = 0.6,
    ignore_header_footer: bool = True,
    header_frac: float = 0.08,
    footer_frac: float = 0.08,
    min_len: int = 2,
    max_len: int = 140,
    max_levels: int = 3,
) -> List[Dict[str, Any]]:
    """
    Extract lines where ≥ bold_threshold of chars use a bold-ish font.
    
    Args:
        pdf_path: Path to the PDF file
        bold_threshold: Minimum ratio of bold characters to consider a heading
        ignore_header_footer: Drop lines in top/bottom fractions of page height
        header_frac: Fraction of page height to ignore at top
        footer_frac: Fraction of page height to ignore at bottom
        min_len: Minimum heading text length
        max_len: Maximum heading text length
        max_levels: Maximum hierarchy levels to infer
        
    Returns:
        list: List of heading dictionaries with page, text, font_size, position, and level
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    out = []
    with pdfplumber.open(pdf_path) as pdf:
        for pageno, page in enumerate(pdf.pages, start=1):
            lines = build_lines(page)
            if not lines:
                continue
            
            page_h = float(page.height)
            median_gap = compute_line_spacing(lines)

            for i, ln in enumerate(lines):
                txt = ln["text"]
                if not (min_len <= len(txt) <= max_len):
                    continue

                if ignore_header_footer:
                    if ln["y_top"] < page_h * header_frac:  # header area
                        continue
                    if ln["y_bottom"] > page_h * (1 - footer_frac):  # footer area
                        continue

                # Core rule: bold ratio
                if ln["bold_ratio"] < bold_threshold:
                    continue

                # Optional: prefer visually separated lines (bigger gap above)
                separated = True
                if i > 0 and median_gap > 0:
                    gap = ln["y_top"] - lines[i - 1]["y_top"]
                    separated = gap >= median_gap * 1.1  # mild boost, not mandatory

                if separated:
                    out.append({
                        "page": pageno,
                        "text": txt,
                        "font_size": ln["font_size_avg"],
                        "x0": ln["x0"],
                        "y_top": ln["y_top"],
                        "y_bottom": ln["y_bottom"],
                    })

    # Assign simple levels from size bands
    if out:
        infer_levels(out, max_levels=max_levels)

    # De-dup consecutive identical headings
    deduped = []
    last_key = None
    for h in out:
        key = (h["page"], h["text"])
        if key != last_key:
            deduped.append(h)
        last_key = key
    
    return deduped


def headings_to_tree(headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert flat list of headings into a hierarchical tree structure.
    
    Args:
        headings: List of heading dictionaries with 'level' attribute
        
    Returns:
        list: Root-level nodes of the heading tree
    """
    stack, root = [], []
    for h in headings:
        node = {"title": h["text"], "page": h["page"], "level": h["level"], "children": []}
        
        while stack and stack[-1]["level"] >= h["level"]:
            stack.pop()
        
        if stack:
            stack[-1]["children"].append(node)
        else:
            root.append(node)
        
        stack.append(node)
    
    return root


def collect_sections_for_level(
    pdf_path: str,
    headings: Optional[List[Dict[str, Any]]] = None,
    target_level: int = 2,
) -> List[Dict[str, Any]]:
    """
    Gather text that follows each heading at the desired level until the next 
    heading at the same or higher level.
    
    Args:
        pdf_path: Path to the PDF file
        headings: Optional pre-extracted headings (will extract if not provided)
        target_level: Hierarchy level to collect sections for
        
    Returns:
        list: List of section dictionaries with heading, page, level, and content
    """
    if headings is None:
        headings = extract_bold_headings(pdf_path)
    
    if not headings:
        return []

    ordered = sorted(headings, key=lambda h: (h["page"], h["y_top"]))
    sections: List[Dict[str, Any]] = []
    
    with pdfplumber.open(pdf_path) as pdf:
        last_page_index = len(pdf.pages) - 1
        
        for idx, heading in enumerate(ordered):
            if heading.get("level") != target_level:
                continue

            # Find the next heading that should stop this section
            boundary = None
            for future in ordered[idx + 1:]:
                if future.get("level") is not None and future["level"] <= target_level:
                    boundary = future
                    break

            start_page = max(0, heading["page"] - 1)
            end_page = boundary["page"] - 1 if boundary else last_page_index
            content_chunks: List[str] = []

            for page_index in range(start_page, end_page + 1):
                page = pdf.pages[page_index]
                top = heading["y_bottom"] + 1 if page_index == start_page else 0.0
                bottom = (
                    boundary["y_top"] - 1
                    if boundary and page_index == end_page
                    else page.height
                )
                top = max(0.0, min(top, page.height))
                bottom = max(0.0, min(bottom, page.height))
                
                if bottom <= top:
                    continue

                clip = page.within_bbox((0.0, top, page.width, bottom))
                text = clip.extract_text(x_tolerance=2, y_tolerance=2)
                if text:
                    content_chunks.append(text.strip())

            sections.append({
                "heading": heading["text"],
                "page": heading["page"],
                "level": heading.get("level"),
                "content": "\n".join(chunk for chunk in content_chunks if chunk).strip(),
            })
    
    return sections
