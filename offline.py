"""Tesseract OCR via stdin/stdout; no temporary document files or external API."""
import io
import os
import re
import shutil
import subprocess
from datetime import date
from PIL import Image, ImageOps
from kyc_agent import KYCData, validate_image

LABELS = {
    'name': r'(?:full\s+name|name)',
    'dob': r'(?:date\s+of\s+birth|dob|birth\s+date)',
    'id_number': r'(?:document\s+number|id\s+number|identification\s+number|passport\s+number|nic(?:\s+(?:number|no\.?))?|licen[cs]e\s+(?:number|no\.?))',
}

class EngineUnavailable(RuntimeError):
    pass

def engine_status():
    binary = shutil.which('tesseract')
    languages = os.environ.get('OCR_LANGUAGES', 'eng')
    if not binary or not re.fullmatch(r'[a-zA-Z0-9_]+(?:\+[a-zA-Z0-9_]+)*', languages):
        return {'configured': False, 'engine': 'Tesseract', 'languages': languages, 'available_languages': []}
    try:
        result = subprocess.run([binary, '--list-langs'], capture_output=True, text=True, timeout=5, check=True)
        available = [line.strip() for line in result.stdout.splitlines()[1:] if line.strip()]
        configured = set(languages.split('+')).issubset(available)
    except (OSError, subprocess.SubprocessError):
        available, configured = [], False
    return {'configured': configured, 'engine': 'Tesseract', 'languages': languages, 'available_languages': available}

def parse_lines(lines):
    result = {}
    all_labels = '|'.join(LABELS.values())
    for field, label in LABELS.items():
        candidates = []
        for i, line in enumerate(lines):
            match = re.fullmatch(label + r'(?:\s*[:\-]\s*|\s+|$)(.*)', line.strip(), flags=re.I)
            if not match:
                continue
            value = match.group(1).strip()
            if not value and i + 1 < len(lines):
                candidate = lines[i + 1].strip()
                if not re.match('(?:' + all_labels + ')', candidate, re.I):
                    value = candidate
            if field == 'dob':
                try:
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                        raise ValueError()
                    value = date.fromisoformat(value).isoformat()
                except ValueError:
                    value = None
            candidates.append(value or None)
        distinct = set(candidates)
        result[field] = candidates[0] if len(distinct) == 1 else None
    readable = all(result.get(k) for k in LABELS)
    return KYCData(**result, readable=readable, notes=(
        'Fields were extracted from labels. Review every character against the document.' if readable else
        'Some fields are missing, ambiguous or conflicting. Review the recognized text and enter corrections. Dates require YYYY-MM-DD.'
    ))

def extract_offline(data):
    validate_image(data)
    status = engine_status()
    if not status['configured']:
        raise EngineUnavailable('Install Tesseract and all configured OCR languages.')
    with Image.open(io.BytesIO(data)) as source:
        oriented = ImageOps.exif_transpose(source)
        rgba = oriented.convert('RGBA')
        background = Image.new('RGBA', rgba.size, 'white')
        background.alpha_composite(rgba)
        image = ImageOps.autocontrast(ImageOps.grayscale(background.convert('RGB')))
        normalized = io.BytesIO()
        image.save(normalized, format='PNG')
    process = subprocess.run(
        [shutil.which('tesseract'), 'stdin', 'stdout', '-l', status['languages'], '--psm', '6'],
        input=normalized.getvalue(), capture_output=True, timeout=60, check=True,
        env={**os.environ, 'OMP_THREAD_LIMIT': '1'},
    )
    raw_text = process.stdout.decode('utf-8', errors='replace').strip()
    result = parse_lines(raw_text.splitlines()).model_dump()
    result.update(raw_text=raw_text, engine='Tesseract', languages=status['languages'])
    return result
