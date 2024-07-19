import unittest
import os
from lib.functions.scan_html_code_patch import analyze_html_file


class TestHTMLScanner(unittest.TestCase):
    def setUp(self):
        # Create a sample HTML file for testing
        self.test_file_path = 'sample_test.html'
        with open(self.test_file_path, 'w', encoding='utf-8') as file:
            file.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test HTML</title>
                <style>
                    .test-class { color: red; }
                </style>
            </head>
            <body>
                <h1 class="test-class">Hello, World!</h1>
                <script>
                    console.log('Hello, World!');
                </script>
            </body>
            </html>
            """)

    def tearDown(self):
        # Remove the sample HTML file after testing
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_analyze_html_file(self):
        result = analyze_html_file(self.test_file_path)
        expected_tags = ['html', 'head', 'title', 'style', 'body', 'h1', 'script']
        expected_attributes = ['class']
        expected_inline_scripts = ["console.log('Hello, World!');"]
        expected_inline_styles = ['.test-class { color: red; }']

        self.assertEqual(result['tags'], expected_tags)
        self.assertEqual(result['attributes'], expected_attributes)
        self.assertEqual(result['inline_scripts'], expected_inline_scripts)
        self.assertEqual(result['inline_styles'], expected_inline_styles)


if __name__ == '__main__':
    unittest.main()