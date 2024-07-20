import ast
import os
from typing import Dict, List, Any
from lib.function_wrapper import function_info_decorator
from lib.util import get_logger

logger = get_logger()

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.decorators = []
        self.functions = []
        self.function_calls = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                self.decorators.append(decorator.id)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    self.decorators.append(decorator.func.id)
        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = self.get_full_name(node.func)
        if func_name:
            self.function_calls.append(func_name)
        self.generic_visit(node)

    def get_full_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_full_name(node.value)}.{node.attr}"
        return None

def analyze_file(file_path: str) -> Dict[str, List[str]]:
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            tree = ast.parse(file.read())
            analyzer = CodeAnalyzer()
            analyzer.visit(tree)
            return {
                'imports': analyzer.imports,
                'decorators': analyzer.decorators,
                'functions': analyzer.functions,
                'function_calls': analyzer.function_calls
            }
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {str(e)}", exc_info=True)
            return {}

@function_info_decorator
def scan_repository(code_path: str) -> Dict[str, Any]:
    """
    Scans a repository directory for Python files, analyzes them, and generates a function file.

    It will analyze each Python file in the repository and generate a function file with the summary of the scan results.

    Use this in conjunction with cat_file to read the file directly. 

    :param code_path: The path to the repository to scan
    :type code_path: str
    :return: A dictionary containing the scan results and generated function file path
    :rtype: dict
    """
    try:
        results = {}
        for root, _, files in os.walk(code_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    result = analyze_file(file_path)
                    if result:
                        results[file_path] = result

        # Generate function file
        function_file_path = os.path.join(code_path, 'function_summary.py')
        with open(function_file_path, 'w', encoding='utf-8') as f:
            f.write("# Function Summary\n\n")
            for file_path, data in results.items():
                f.write(f"# File: {file_path}\n")
                f.write("def file_summary():\n")
                f.write(f"    imports = {data['imports']}\n")
                f.write(f"    decorators = {data['decorators']}\n")
                f.write(f"    functions = {data['functions']}\n")
                f.write(f"    function_calls = {data['function_calls']}\n")
                f.write("    return {\n")
                f.write("        'imports': imports,\n")
                f.write("        'decorators': decorators,\n")
                f.write("        'functions': functions,\n")
                f.write("        'function_calls': function_calls\n")
                f.write("    }\n\n")

        return {
            "success": True,
            "message": "Repository scanned successfully",
            "scan_results": results,
            "function_file_path": function_file_path
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
    result = scan_repository(repo_path)
    if result["success"]:
        print(f"Scan completed. Function file generated at: {result['function_file_path']}")
    else:
        print(f"Scan failed: {result['error']}")