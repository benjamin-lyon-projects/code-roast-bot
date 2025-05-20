import unittest
from code_roast_bot.utils import validate_ast, scan_for_dangerous_patterns, redact_code, detect_obfuscated_strings

class TestUtils(unittest.TestCase):

    def test_validate_ast_valid(self):
        self.assertTrue(validate_ast("print('Hello')"))

    def test_validate_ast_invalid(self):
        self.assertFalse(validate_ast("def bad(:"))

    def test_scan_and_redact(self):
        bad_code = '''
api_key = "123"
password = "abc"
os.system('rm -rf /')
eval("2 + 2")
'''
        flags, patterns = scan_for_dangerous_patterns(bad_code)
        self.assertIn("Hardcoded API key", flags)
        self.assertIn("Hardcoded password", flags)
        self.assertIn("os.system usage", flags)
        self.assertIn("eval usage", flags)
        redacted = redact_code(bad_code, patterns)
        self.assertNotIn("123", redacted)
        self.assertNotIn("abc", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_detect_obfuscated_strings(self):
        concat = 'token = "sec" + "ret"'
        join = 'token = "".join(["a", "b", "c"])'
        plain = 'token = "secret"'
        self.assertIn("String literal concatenation in assignment", detect_obfuscated_strings(concat))
        self.assertIn("String join from literals in assignment", detect_obfuscated_strings(join))
        self.assertEqual(detect_obfuscated_strings(plain), [])

if __name__ == '__main__':
    unittest.main()