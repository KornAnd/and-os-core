#!/usr/bin/env python3
"""
tdd_scaffold.py - TDD Test Scaffold Generator for AnD os (Python & Swift).
Extracts classes, functions, and methods from source files and generates comprehensive
test case templates (unittest for Python, XCTest for Swift) to enforce Test-Driven Development.
"""

import sys
import os
import ast
import re
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

def extract_python_symbols(file_path: Path) -> Dict[str, Any]:
    """Parse Python file using AST and extract functions and classes."""
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=str(file_path))
    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                args = [a.arg for a in node.args.args if a.arg != "self"]
                functions.append({"name": node.name, "args": args})
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("__"):
                    args = [a.arg for a in item.args.args if a.arg != "self"]
                    methods.append({"name": item.name, "args": args})
            classes.append({"name": node.name, "methods": methods})

    return {"classes": classes, "functions": functions}

def generate_python_test(source_path: Path, symbols: Dict[str, Any], output_path: Path) -> str:
    """Generate Python unittest scaffold."""
    rel_module = source_path.stem
    import_stmt = f"# Target under test\n# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
    
    code = [
        "#!/usr/bin/env python3",
        f'"""Unit tests for {source_path.name} (Generated via AnD os TDD Scaffold)."""',
        "",
        "import unittest",
        "import sys",
        "from pathlib import Path",
        "",
        import_stmt,
        f"class Test{rel_module.capitalize()}(unittest.TestCase):",
        '    """Test suite for ' + source_path.name + '."""',
        "",
        "    def setUp(self):",
        "        # TODO: Initialize test fixtures and mock objects",
        "        pass",
        "",
        "    def tearDown(self):",
        "        # TODO: Cleanup test artifacts",
        "        pass",
        ""
    ]

    # Add standalone function tests
    for fn in symbols.get("functions", []):
        fn_name = fn["name"]
        code.extend([
            f"    def test_{fn_name}_happy_path(self):",
            f'        """Test standard behavior of {fn_name}()."""',
            "        # GIVEN",
            "        # WHEN",
            f"        # result = {fn_name}()",
            "        # THEN",
            "        self.assertTrue(True)  # Replace with actual assertion",
            "",
            f"    def test_{fn_name}_edge_cases(self):",
            f'        """Test boundary conditions for {fn_name}()."""',
            "        # Empty/None/Invalid input handling",
            "        self.assertTrue(True)",
            ""
        ])

    # Add class tests
    for cls in symbols.get("classes", []):
        cls_name = cls["name"]
        code.extend([
            f"    def test_{cls_name.lower()}_initialization(self):",
            f'        """Verify {cls_name} instantiation and default state."""',
            "        self.assertTrue(True)",
            ""
        ])
        for m in cls.get("methods", []):
            m_name = m["name"]
            code.extend([
                f"    def test_{cls_name.lower()}_{m_name}(self):",
                f'        """Test {cls_name}.{m_name}() contract."""',
                "        self.assertTrue(True)",
                ""
            ])

    if not symbols.get("functions") and not symbols.get("classes"):
        code.extend([
            "    def test_default_contract(self):",
            '        """Default contract check."""',
            "        self.assertTrue(True)",
            ""
        ])

    code.extend([
        "if __name__ == '__main__':",
        "    unittest.main()",
        ""
    ])

    test_content = "\n".join(code)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    return test_content

def extract_swift_symbols(file_path: Path) -> Dict[str, Any]:
    """Extract classes, structs and methods from Swift files using regex."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    classes = re.findall(r'(?:class|struct|actor)\s+([A-Za-z0-9_]+)', content)
    funcs = re.findall(r'func\s+([A-Za-z0-9_]+)\s*\(', content)

    return {"types": classes, "functions": funcs}

def generate_swift_test(source_path: Path, symbols: Dict[str, Any], output_path: Path) -> str:
    """Generate Swift XCTestCase scaffold."""
    module_name = "EscPlanet"
    type_name = symbols["types"][0] if symbols["types"] else source_path.stem
    
    code = [
        "import XCTest",
        f"@testable import {module_name}",
        "",
        f"final class {type_name}Tests: XCTestCase {{",
        "",
        "    override func setUpWithError() throws {",
        "        super.setUp()",
        "        // TODO: Initialize test state",
        "    }",
        "",
        "    override func tearDownWithError() throws {",
        "        // TODO: Clean up test state",
        "        super.tearDown()",
        "    }",
        ""
    ]

    for t in symbols.get("types", []):
        code.extend([
            f"    func test_{t}_initialization() throws {{",
            f"        // Verify {t} initializes properly",
            "        XCTAssertTrue(true)",
            "    }",
            ""
        ])

    for fn in symbols.get("functions", []):
        code.extend([
            f"    func test_{fn}_execution() throws {{",
            f"        // Test execution of {fn}()",
            "        XCTAssertTrue(true)",
            "    }",
            ""
        ])

    if not symbols.get("types") and not symbols.get("functions"):
        code.extend([
            "    func test_default_smoke() throws {",
            "        XCTAssertTrue(true)",
            "    }",
            ""
        ])

    code.extend([
        "}",
        ""
    ])

    test_content = "\n".join(code)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    return test_content

def scaffold(file_path: str, run_test: bool = False, out: Optional[str] = None) -> int:
    path = Path(file_path).resolve()
    if not path.exists():
        print(f"❌ File not found: {path}")
        return 1

    suffix = path.suffix.lower()
    if suffix == ".py":
        symbols = extract_python_symbols(path)
        if out:
            out_path = Path(out).resolve()
        else:
            # Default location: tests/test_<name>.py or beside file
            if "and_os" in str(path):
                out_path = path.parent.parent / "tests" / f"test_{path.name}"
            else:
                out_path = path.parent / f"test_{path.name}"
        
        generate_python_test(path, symbols, out_path)
        print(f"✅ Generated Python test scaffold: {out_path}")
        print(f"   Found: {len(symbols.get('classes', []))} classes, {len(symbols.get('functions', []))} functions")
        
        if run_test:
            print(f"🚀 Running test via unittest: {out_path.name}...")
            res = subprocess.run([sys.executable, str(out_path)], capture_output=True, text=True)
            print(res.stdout)
            if res.stderr:
                print(res.stderr)
            return res.returncode
        return 0

    elif suffix == ".swift":
        symbols = extract_swift_symbols(path)
        if out:
            out_path = Path(out).resolve()
        else:
            out_path = path.parent / f"{path.stem}Tests.swift"
            
        generate_swift_test(path, symbols, out_path)
        print(f"✅ Generated Swift XCTest scaffold: {out_path}")
        print(f"   Found: {len(symbols.get('types', []))} types, {len(symbols.get('functions', []))} functions")
        return 0
    else:
        print(f"❌ Unsupported language extension: {suffix} (Supported: .py, .swift)")
        return 1

def main():
    parser = argparse.ArgumentParser(description="TDD Scaffold Generator for AnD os (Python & Swift)")
    parser.add_argument("file", help="Source file (.py or .swift) to scaffold tests for")
    parser.add_argument("--out", "-o", help="Custom output test file path")
    parser.add_argument("--run", "-r", action="store_true", help="Immediately run generated test")
    
    args = parser.parse_args()
    sys.exit(scaffold(args.file, run_test=args.run, out=args.out))

if __name__ == "__main__":
    main()
