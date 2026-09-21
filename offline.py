"""Local Apple Vision OCR with conservative, label-based field parsing."""
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from kyc_agent import KYCData, validate_image
BINARY = Path(__file__).parent / 'native/akshaya-ocr'
LABELS = {'name': r'(?:full\s+name|name)', 'dob': r'(?:date\s+of\s+birth|dob|birth\s+date)', 'id_number': r'(?:document\s+number|id\s+number|identification\s+number|passport\s+number)'}

def parse_lines(lines):
    result = {}
    all_labels = '|'.join(LABELS.values())
    for field, label in LABELS.items():
        for i, line in enumerate(lines):
            match = re.fullmatch(label + r'\s*[:\-]?\s*(.*)', line.strip(), flags=re.I)
            if not match:
                continue
            value = match.group(1).strip()
            if not value and i+1 < len(lines):
                candidate = lines[i+1].strip()
                if not re.match('(?:'+all_labels+')', candidate, re.I):
                    value = candidate
            if field == 'dob':
                try:
                    value = date.fromisoformat(value).isoformat()
                except ValueError:
                    value = None
            result[field] = value or None
            break
    readable = all(result.get(k) for k in LABELS)
    return KYCData(**result, readable=readable, notes='Read locally on your Mac. Review every field against the image.' if readable else 'Some labeled fields could not be read. Enter missing details manually. Dates must be unambiguous YYYY-MM-DD.')

def extract_offline(data):
    validate_image(data)
    process = subprocess.run([str(BINARY)], input=data, capture_output=True, timeout=60, check=True)
    lines = json.loads(process.stdout)
    result = parse_lines(lines).model_dump()
    result['raw_text'] = '\n'.join(lines)
    result['engine'] = 'Apple Vision (offline)'
    return result
