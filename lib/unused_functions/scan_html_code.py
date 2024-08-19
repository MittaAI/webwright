from bs4 import BeautifulSoup
import os
from typing import Dict, List
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger

logger = get_logger()


def analyze_html_file(file_path: str) -> Dict[str, List[str]]:
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            soup = BeautifulSoup(file, 'html.parser')
            tags = [tag.name for tag in soup.find_all()]
            attributes = list({attr for tag in soup.find_all() for attr in tag.attrs.keys()})
            inline_scripts = [script.string.strip() for script in soup.find_all('script') if script.string]
            inline_styles = [style.string.strip() for style in soup.find_all('style') if style.string]
            return {
                'tags': tags,
                'attributes': attributes,
                'inline_scripts': inline_scripts,
                'inline_styles': inline_styles
            }
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {str(e)}", exc_info=True)
            return {}


@function_info_decorator
def scan_html_repository(code_path: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Scans a repository directory for HTML files, analyzes them, and generates a summary.

    It will analyze each HTML file in the repository and generate a summary of the tags, attributes,
    inline scripts, and inline styles found in the files.

    :param code_path: The path to the repository to scan
    :type code_path: str
    :return: A dictionary containing the scan results and generated summary
    :rtype: dict
    """
    try:
        results = {}
        for root, _, files in os.walk(code_path):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    result = analyze_html_file(file_path)
                    if result:
                        results[file_path] = result
        return {
            "success": True,
            "message": "Repository scanned successfully",
            "scan_results": results
        }
    except Exception as e:
        logger.error("Failed to scan repository: " + str(e), exc_info=True)
        return {
            "success": False,
            "error": "Failed to scan repository",
            "reason": str(e)
        }


# Example usage
if __name__ == "__main__":
    repo_path = './'  # Update this path
    result = scan_html_repository(repo_path)
    if result["success"]:
        print(f"Scan completed. Results: {result['scan_results']}")
    else:
        print(f"Scan failed: {result['error']}")
