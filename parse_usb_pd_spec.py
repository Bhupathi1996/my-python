"""
USB PD Specification TOC Parser
Author: [Your Name]
Date: [2025-07-30]

Description:
This script parses the Table of Contents (ToC) from a USB Power Delivery PDF specification
and generates a structured JSONL file representing the document hierarchy.

Dependencies:
- pdfplumber
- jsonlines
- re
"""

import pdfplumber
import re
import jsonlines
import os
from typing import Optional, List

# ---------- Utility Functions ----------
def get_toc_lines(pdf_path: str, toc_page_range=(1, 30)) -> List[str]:
    """
    Extract potential Table of Contents lines from the first few pages of the PDF.
    """
    toc_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(toc_page_range[0] - 1, min(toc_page_range[1], len(pdf.pages))):
            page = pdf.pages[i]
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                toc_lines.extend(lines)
    return toc_lines

def parse_toc_line(line: str):
    """
    Parses a single TOC line. Supports both numbered and non-numbered lines.
    """
    line = line.strip()

    # Pattern for numbered TOC lines, e.g., 1.2.3 Title ............. 34
    pattern = r'^(\d+(?:\.\d+)*)(?:\s+)(.*?)(?:\.{3,}|\s+)(\d{1,4})$'
    match = re.match(pattern, line)
    if match:
        section_id = match.group(1)
        title = match.group(2).strip()
        page = int(match.group(3))
        level = section_id.count('.') + 1
        parent_id = '.'.join(section_id.split('.')[:-1]) if '.' in section_id else None
        return {
            "section_id": section_id,
            "title": title,
            "page": page,
            "level": level,
            "parent_id": parent_id,
            "full_path": f"{section_id} {title}"
        }

    # Fallback: title-only lines (e.g., Editors ........... 6)
    fallback = re.match(r'^(.*?)(?:\.{3,}|\s+)(\d{1,4})$', line)
    if fallback:
        title = fallback.group(1).strip()
        page = int(fallback.group(2))
        return {
            "section_id": None,
            "title": title,
            "page": page,
            "level": 0,
            "parent_id": None,
            "full_path": title
        }

    return None

def extract_doc_title(pdf_path: str) -> str:
    """
    Extracts the document title from the first page.
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
        if not text:
            return "USB Power Delivery Specification"
        for line in text.split('\n'):
            if "USB" in line and "Power" in line:
                return line.strip()
    return "USB Power Delivery Specification"

def write_jsonl(output_path: str, toc_data: List[dict]):
    """
    Write parsed ToC data into a JSONL file.
    """
    with jsonlines.open(output_path, mode='w') as writer:
        for entry in toc_data:
            writer.write(entry)

# ---------- Main Execution ----------
def main():
    pdf_path = "USB_PD_R3_2 V1.1 2024-10.pdf"  # Replace with actual filename
    output_path = "usb_pd_spec.jsonl"

    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return

    try:
        doc_title = extract_doc_title(pdf_path)
        lines = get_toc_lines(pdf_path)
    except Exception as e:
        print(f"❌ Failed to read PDF: {e}")
        return

    toc_entries = []
    unparsed_lines = []

    for line in lines:
        parsed = parse_toc_line(line)
        if parsed:
            parsed["doc_title"] = doc_title
            parsed["tags"] = []
            toc_entries.append(parsed)
        else:
            unparsed_lines.append(line)

    write_jsonl(output_path, toc_entries)

    print(f"\n✅ TOC parsed and saved to {output_path} with {len(toc_entries)} entries.")
    if unparsed_lines:
        print(f"⚠️  {len(unparsed_lines)} lines could not be parsed. Sample:")
        for line in unparsed_lines[:5]:
            print(f"   ❌ {line}")

if __name__ == "__main__":
    main()