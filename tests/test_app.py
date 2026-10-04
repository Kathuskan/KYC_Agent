import io
import unittest
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient
from app import app, OCR_SLOT
from offline import EngineUnavailable

class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        out = io.BytesIO()
        Image.new('RGB', (10, 10), 'white').save(out, format='PNG')
        self.image = out.getvalue()
        self.headers = {'Content-Type': 'image/png', 'X-Consent': 'process-locally'}

    def test_private_files_and_security_headers(self):
        for path in ['/static/IMG_8747.jpeg', '/kyc_agent.py', '/docs/information-security.md']:
            self.assertEqual(self.client.get(path).status_code, 404)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertIn("frame-ancestors 'none'", response.headers['content-security-policy'])

    def test_input_controls(self):
        self.assertEqual(self.client.post('/api/extract', content=self.image).status_code, 400)
        self.assertEqual(self.client.post('/api/extract', headers=self.headers, content=b'fake').status_code, 400)
        self.assertEqual(self.client.post('/api/extract', headers=self.headers, content=b'x'*(10*1024*1024+1)).status_code, 413)
        headers = {**self.headers, 'Content-Type': 'text/plain'}
        self.assertEqual(self.client.post('/api/extract', headers=headers, content=self.image).status_code, 415)
        self.assertEqual(self.client.get('/', headers={'Host': 'attacker.example'}).status_code, 400)

    def test_missing_engine(self):
        with patch('app.extract_offline', side_effect=EngineUnavailable()):
            self.assertEqual(self.client.post('/api/extract', headers=self.headers, content=self.image).status_code, 503)

    def test_error_hides_details_and_releases_slot(self):
        with patch('app.extract_offline', side_effect=RuntimeError('private ID detail')):
            response = self.client.post('/api/extract', headers=self.headers, content=self.image)
            self.assertEqual(response.status_code, 502)
            self.assertNotIn('private ID detail', response.text)
        self.assertTrue(OCR_SLOT.acquire(blocking=False))
        OCR_SLOT.release()

    def test_busy(self):
        OCR_SLOT.acquire()
        try:
            self.assertEqual(self.client.post('/api/extract', headers=self.headers, content=self.image).status_code, 429)
        finally:
            OCR_SLOT.release()

    def test_response_keeps_nonverification(self):
        with patch('app.extract_offline', return_value={'name': 'Example', 'identity_verified': False}):
            response = self.client.post('/api/extract', headers=self.headers, content=self.image)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()['identity_verified'])
