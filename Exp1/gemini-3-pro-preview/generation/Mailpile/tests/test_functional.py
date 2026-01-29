import unittest
import sys
import os

# Ensure we can import the local mailpile package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mailpile.safe_popen import SafePopen, PopenPipeline
from mailpile.util import CleanText, int2b36, b362int, md5_hex
from mailpile.vcard import VCardLine, ParseVCard
from mailpile.i18n import _, ngettext

class TestMailpileSlice(unittest.TestCase):

    def test_safe_popen(self):
        print("\nTesting SafePopen...")
        # Test basic echo
        proc = SafePopen(["echo", "hello world"])
        out, err = proc.communicate()
        self.assertEqual(out.strip().decode(), "hello world")

        # Test string command splitting
        proc = SafePopen("echo split me")
        out, err = proc.communicate()
        self.assertEqual(out.strip().decode(), "split me")

    def test_pipeline(self):
        print("Testing PopenPipeline...")
        # echo "hello" | cat
        # Note: 'cat' might not exist on Windows, so we use python for cross-platform echo
        cmd1 = [sys.executable, "-c", "print('pipeline_test')"]
        cmd2 = [sys.executable, "-c", "import sys; print(sys.stdin.read().strip() + '_suffix')"]
        
        last_proc, all_procs = PopenPipeline([cmd1, cmd2])
        out, err = last_proc.communicate()
        self.assertEqual(out.strip().decode(), "pipeline_test_suffix")

    def test_util_cleantext(self):
        print("Testing CleanText...")
        html = "<html><body><h1>Hello</h1> <p>World&nbsp;&amp;&nbsp;Friends</p></body></html>"
        cleaned = CleanText(html)
        self.assertEqual(cleaned, "Hello World & Friends")
        
        dirty_spaces = "foo   bar\n\tbaz"
        self.assertEqual(CleanText(dirty_spaces, clean_html=False), "foo bar baz")

    def test_util_base36(self):
        print("Testing Base36 conversion...")
        num = 123456789
        b36 = int2b36(num)
        self.assertEqual(b36, "21i3v9")
        self.assertEqual(b362int(b36), num)
        
        self.assertEqual(int2b36(0), "0")
        self.assertEqual(b362int("0"), 0)

    def test_util_md5(self):
        print("Testing MD5 helper...")
        self.assertEqual(md5_hex("mailpile"), "e8354672150033602506822b39920153")

    def test_vcard_parsing(self):
        print("Testing VCard parsing...")
        line_str = "EMAIL;TYPE=WORK;PREF:user@example.com"
        obj = VCardLine.parse(line_str)
        self.assertEqual(obj.name, "EMAIL")
        self.assertEqual(obj.value, "user@example.com")
        self.assertEqual(obj.params['TYPE'], "WORK")
        self.assertTrue('PREF' in obj.params)
        
        # Test serialization round-trip
        # Note: params dict order might vary, but our __str__ sorts them
        reconstructed = str(obj)
        self.assertIn("TYPE=WORK", reconstructed)
        self.assertIn("PREF=None", reconstructed) # Our simple parser assigns None to valueless params
        self.assertTrue(reconstructed.startswith("EMAIL;"))
        self.assertTrue(reconstructed.endswith(":user@example.com"))

    def test_vcard_block(self):
        print("Testing VCard block parsing with unfolding...")
        vcard_data = """BEGIN:VCARD
VERSION:3.0
FN:Mail Pile
N:Pile;Mail;;;
EMAIL;TYPE=INTERNET:team@mail
 pile.is
END:VCARD"""
        lines = ParseVCard(vcard_data)
        self.assertEqual(len(lines), 5)
        
        email_line = [l for l in lines if l.name == 'EMAIL'][0]
        self.assertEqual(email_line.value, "team@mailpile.is")

    def test_i18n(self):
        print("Testing i18n passthrough...")
        self.assertEqual(_("Hello"), "Hello")
        self.assertEqual(ngettext("File", "Files", 1), "File")
        self.assertEqual(ngettext("File", "Files", 5), "Files")

if __name__ == '__main__':
    unittest.main()