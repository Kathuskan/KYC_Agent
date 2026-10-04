import io
import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from offline import parse_lines, extract_offline, engine_status, EngineUnavailable
from kyc_agent import validate_image

SAMPLE = Path(__file__).parents[1] / 'static/sample-document.png'

class OfflineTests(unittest.TestCase):
    def test_missing_ambiguous_and_conflicting_fields(self):
        result = parse_lines(['Full name', 'Date of birth', '06/07/2001'])
        self.assertIsNone(result.name)
        self.assertIsNone(result.dob)
        self.assertFalse(result.readable)
        self.assertIsNone(parse_lines(['Name: A', 'Name: B']).name)
        self.assertIsNone(parse_lines(['DOB: 2001-02-29']).dob)

    def test_inline_and_multilingual_value(self):
        result = parse_lines(['Name: குமார்', 'DOB: 2000-02-29', 'NIC: TEST-2'])
        self.assertEqual(result.name, 'குமார்')
        self.assertEqual(result.id_number, 'TEST-2')
        self.assertTrue(result.readable)
        self.assertFalse(result.identity_verified)

    def test_invalid_file_and_dimensions(self):
        with self.assertRaises(ValueError):
            validate_image(b'not an image')
        out = io.BytesIO()
        Image.new('1', (5000, 4100)).save(out, format='PNG')
        with self.assertRaises(ValueError):
            validate_image(out.getvalue())

    def test_engine_unavailable(self):
        with patch('offline.shutil.which', return_value=None):
            self.assertFalse(engine_status()['configured'])
            with self.assertRaises(EngineUnavailable):
                extract_offline(SAMPLE.read_bytes())

    def test_language_configuration(self):
        with patch.dict(os.environ, {'OCR_LANGUAGES': 'eng+sin+tam'}), patch('offline.shutil.which', return_value='/fake/tesseract'), patch('offline.subprocess.run', return_value=subprocess.CompletedProcess([], 0, 'List of available languages (1):\neng\n', '')):
            self.assertFalse(engine_status()['configured'])
        with patch.dict(os.environ, {'OCR_LANGUAGES': '--bad'}):
            self.assertFalse(engine_status()['configured'])

    def test_subprocess_uses_memory_and_timeout(self):
        status = {'configured': True, 'languages': 'eng'}
        with patch('offline.engine_status', return_value=status), patch('offline.shutil.which', return_value='/fake/tesseract'), patch('offline.subprocess.run', return_value=subprocess.CompletedProcess([], 0, b'Name: Example\nDOB: 2000-01-01\nNIC: TEST-9', b'')) as run:
            result = extract_offline(SAMPLE.read_bytes())
            self.assertEqual(result['id_number'], 'TEST-9')
            args, kwargs = run.call_args
            self.assertEqual(args[0][1:3], ['stdin', 'stdout'])
            self.assertEqual(kwargs['timeout'], 60)
            self.assertTrue(kwargs['input'].startswith(b'\x89PNG'))
        with patch('offline.engine_status', return_value=status), patch('offline.subprocess.run', side_effect=subprocess.TimeoutExpired('tesseract', 60)):
            with self.assertRaises(subprocess.TimeoutExpired):
                extract_offline(SAMPLE.read_bytes())

    def test_real_sample_ocr(self):
        # Required integration test: missing Tesseract is a failure, not a skip.
        with patch.dict(os.environ, {'OCR_LANGUAGES': 'eng'}):
            result = extract_offline(SAMPLE.read_bytes())
        self.assertEqual(result['name'], 'Alex Morgan')
        self.assertEqual(result['dob'], '1994-06-18')
        self.assertEqual(result['id_number'], 'DEMO-000123')
        self.assertIn('Alex Morgan', result['raw_text'])
        self.assertFalse(result['identity_verified'])

    def test_real_blank_image(self):
        out = io.BytesIO()
        Image.new('RGB', (600, 400), 'white').save(out, format='PNG')
        with patch.dict(os.environ, {'OCR_LANGUAGES': 'eng'}):
            result = extract_offline(out.getvalue())
        self.assertFalse(result['readable'])
        self.assertEqual(result['raw_text'], '')
