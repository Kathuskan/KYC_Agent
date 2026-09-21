import unittest
from pathlib import Path
from offline import parse_lines, extract_offline, BINARY
class OfflineTests(unittest.TestCase):
    def test_missing_and_ambiguous(self):
        data=parse_lines(['Full name', 'Date of birth', '06/07/2001'])
        self.assertIsNone(data.name)
        self.assertIsNone(data.dob)
        self.assertFalse(data.readable)
    def test_inline(self):
        data=parse_lines(['Name: Casey Example', 'DOB: 2000-02-29', 'ID number: TEST-2'])
        self.assertEqual(data.name,'Casey Example')
        self.assertTrue(data.readable)
    @unittest.skipUnless(BINARY.is_file(),'Compile native helper first')
    def test_real_sample_ocr(self):
        result=extract_offline((Path(__file__).parents[1]/'static/sample-document.png').read_bytes())
        self.assertEqual(result['name'],'Alex Morgan')
        self.assertEqual(result['dob'],'1994-06-18')
        self.assertEqual(result['id_number'],'DEMO-000123')
