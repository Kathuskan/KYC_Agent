import io
import os
import unittest
from unittest.mock import patch
from PIL import Image
from fastapi.testclient import TestClient
from app import app
from kyc_agent import KYCData, validate_image

class AppTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        out=io.BytesIO();Image.new('RGB',(10,10),'white').save(out,format='PNG');self.image=out.getvalue()
        self.headers={'Content-Type':'image/png','X-Consent':'process-locally'}
    def test_home_and_private_files(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.get('/static/app.js').status_code,200)
        self.assertEqual(self.client.get('/static/IMG_8747.jpeg').status_code,404)
        self.assertEqual(self.client.get('/kyc_agent.py').status_code,404)
    def test_missing_consent(self):
        self.assertEqual(self.client.post('/api/extract',content=self.image).status_code,400)
    def test_bad_image(self):
        self.assertEqual(self.client.post('/api/extract',headers=self.headers,content=b'fake').status_code,400)
    def test_size_limit(self):
        self.assertEqual(self.client.post('/api/extract',headers=self.headers,content=b'x'*(10*1024*1024+1)).status_code,413)
    def test_missing_engine(self):
        with patch('app.BINARY') as binary:
            binary.is_file.return_value=False
            self.assertFalse(self.client.get('/api/status').json()['configured'])
            self.assertEqual(self.client.post('/api/extract',headers=self.headers,content=self.image).status_code,503)
    def test_extract(self):
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test'}), patch('app.extract_offline',return_value=KYCData(name='Sample',readable=True,notes='Review').model_dump()):
            response=self.client.post('/api/extract',headers=self.headers,content=self.image)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['name'],'Sample')
            self.assertEqual(response.headers['cache-control'],'no-store')
    def test_upstream_error_hides_details(self):
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test'}), patch('app.extract_offline',side_effect=RuntimeError('private detail')):
            response=self.client.post('/api/extract',headers=self.headers,content=self.image)
            self.assertEqual(response.status_code,502)
            self.assertNotIn('private detail',response.text)
    def test_mime_and_host(self):
        self.assertEqual(validate_image(self.image),'image/png')
        self.assertEqual(self.client.get('/',headers={'Host':'attacker.example'}).status_code,400)

if __name__=='__main__':unittest.main()
