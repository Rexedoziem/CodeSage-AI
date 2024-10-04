import unittest
import tempfile
import os
from typing import Dict
from advanced_copilot.multi_language.language_detector import LanguageDetector  # Assume the original code is in language_detector.py

class TestLanguageDetector(unittest.TestCase):
    def setUp(self):
        self.detector = LanguageDetector()

    def test_supported_languages(self):
        expected_languages = ['python', 'javascript', 'java', 'ruby', 'go', 'rust']
        self.assertListEqual(sorted(self.detector.get_supported_languages()), sorted(expected_languages))

    def test_detect_language_from_string(self):
        test_cases: Dict[str, str] = {
            'python': 'import os\n\ndef main():\n    print("Hello, World!")',
            'javascript': 'function greet(name) {\n    console.log(`Hello, ${name}!`);\n}',
            'java': 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}',
            'ruby': 'require "date"\n\nclass Greeter\n    def greet(name)\n        puts "Hello, #{name}!"\n    end\nend',
            'go': 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}',
            'rust': 'fn main() {\n    println!("Hello, World!");\n}\n\nstruct Point {\n    x: i32,\n    y: i32,\n}',
        }

        for expected_lang, code in test_cases.items():
            with self.subTest(language=expected_lang):
                detected_lang = self.detector.detect_language(code)
                self.assertEqual(detected_lang, expected_lang)

    def test_detect_language_from_file(self):
        test_cases: Dict[str, str] = {
            'python': ('test.py', 'print("Hello, World!")'),
            'javascript': ('test.js', 'console.log("Hello, World!");'),
            'java': ('Test.java', 'public class Test { }'),
            'ruby': ('test.rb', 'puts "Hello, World!"'),
            'go': ('test.go', 'package main'),
            'rust': ('test.rs', 'fn main() { }'),
        }

        for expected_lang, (filename, content) in test_cases.items():
            with self.subTest(language=expected_lang):
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{filename.split(".")[-1]}', delete=False) as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    detected_lang = self.detector.detect_language(temp_file.name)
                    self.assertEqual(detected_lang, expected_lang)
                os.unlink(temp_file.name)

    def test_unknown_language(self):
        unknown_code = "This is not a valid code in any supported language."
        detected_lang = self.detector.detect_language(unknown_code)
        self.assertEqual(detected_lang, 'unknown')

    def test_preprocess_code(self):
        code_with_comments = '# This is a comment\ndef main():\n    print("Hello")  # Another comment'
        preprocessed_code = self.detector._preprocess_code(code_with_comments)
        self.assertNotIn('#', preprocessed_code)
        self.assertIn('def main():', preprocessed_code)

if __name__ == '__main__':
    unittest.main()