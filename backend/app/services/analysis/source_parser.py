"""
Source Code Parser — Tree-sitter based multi-language parser.

Extracts structural elements (classes, functions, imports, calls) from source
files to build the code dependency graph.
"""
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from app.core.logging import logger


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    UNKNOWN = "unknown"


@dataclass
class SymbolInfo:
    """Represents an extracted code symbol (function, class, import, etc.)."""
    name: str
    kind: str  # "function", "class", "method", "import", "call"
    file_path: str
    start_line: int
    end_line: int
    signature: str = ""
    parent: Optional[str] = None  # Parent class for methods
    targets: List[str] = field(default_factory=list)  # Call targets or import sources


@dataclass
class FileAnalysis:
    """Complete structural analysis of a single source file."""
    file_path: str
    language: Language
    classes: List[SymbolInfo] = field(default_factory=list)
    functions: List[SymbolInfo] = field(default_factory=list)
    methods: List[SymbolInfo] = field(default_factory=list)
    imports: List[SymbolInfo] = field(default_factory=list)
    calls: List[SymbolInfo] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def symbol_count(self) -> int:
        return len(self.classes) + len(self.functions) + len(self.methods)


EXTENSION_LANGUAGE_MAP = {
    ".py": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".java": Language.JAVA,
    ".go": Language.GO,
}


def detect_language(file_path: str) -> Language:
    """Detect programming language from file extension."""
    _, ext = os.path.splitext(file_path.lower())
    return EXTENSION_LANGUAGE_MAP.get(ext, Language.UNKNOWN)


class PythonParser:
    """Regex-based Python source parser for extracting structural elements.

    Uses line-by-line analysis for reliable extraction without tree-sitter
    binary dependency issues on all platforms.
    """

    @staticmethod
    def parse(content: str, file_path: str) -> FileAnalysis:
        analysis = FileAnalysis(file_path=file_path, language=Language.PYTHON)
        lines = content.split("\n")
        current_class: Optional[str] = None
        class_indent: int = 0

        for i, line in enumerate(lines, start=1):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            # Track class scope
            if current_class and indent <= class_indent and stripped and not stripped.startswith("#"):
                current_class = None

            # Import detection
            if stripped.startswith("import ") or stripped.startswith("from "):
                import_info = PythonParser._parse_import(stripped, file_path, i)
                if import_info:
                    analysis.imports.append(import_info)

            # Class detection
            elif stripped.startswith("class "):
                class_info = PythonParser._parse_class(stripped, file_path, i, lines, i - 1)
                if class_info:
                    analysis.classes.append(class_info)
                    current_class = class_info.name
                    class_indent = indent

            # Function/Method detection
            elif stripped.startswith("def "):
                func_info = PythonParser._parse_function(stripped, file_path, i, lines, i - 1, current_class)
                if func_info:
                    if current_class:
                        func_info.kind = "method"
                        func_info.parent = current_class
                        analysis.methods.append(func_info)
                    else:
                        analysis.functions.append(func_info)

            # Call detection (simple function calls)
            if "(" in stripped and not stripped.startswith(("def ", "class ", "import ", "from ", "#", "@")):
                calls = PythonParser._extract_calls(stripped, file_path, i)
                analysis.calls.extend(calls)

        return analysis

    @staticmethod
    def _parse_import(line: str, file_path: str, line_num: int) -> Optional[SymbolInfo]:
        try:
            if line.startswith("from "):
                parts = line.split()
                if len(parts) >= 4 and parts[2] == "import":
                    module = parts[1]
                    imported = [p.strip().rstrip(",") for p in parts[3:] if p.strip() and p.strip() != "("]
                    return SymbolInfo(
                        name=module,
                        kind="import",
                        file_path=file_path,
                        start_line=line_num,
                        end_line=line_num,
                        targets=imported,
                    )
            elif line.startswith("import "):
                parts = line.split()
                modules = [p.strip().rstrip(",") for p in parts[1:] if p.strip() and p != "as" and not p.startswith("as")]
                for mod in modules:
                    if mod and not mod.startswith("#"):
                        return SymbolInfo(
                            name=mod,
                            kind="import",
                            file_path=file_path,
                            start_line=line_num,
                            end_line=line_num,
                            targets=[mod],
                        )
        except Exception:
            pass
        return None

    @staticmethod
    def _parse_class(line: str, file_path: str, line_num: int, lines: List[str], start_idx: int) -> Optional[SymbolInfo]:
        try:
            name_part = line[6:]  # Remove "class "
            paren_idx = name_part.find("(")
            colon_idx = name_part.find(":")
            if paren_idx >= 0:
                name = name_part[:paren_idx].strip()
            elif colon_idx >= 0:
                name = name_part[:colon_idx].strip()
            else:
                name = name_part.strip()

            if not name or not name.isidentifier():
                return None

            end_line = PythonParser._find_block_end(lines, start_idx)
            return SymbolInfo(
                name=name,
                kind="class",
                file_path=file_path,
                start_line=line_num,
                end_line=end_line,
                signature=line.strip().rstrip(":"),
            )
        except Exception:
            return None

    @staticmethod
    def _parse_function(
        line: str, file_path: str, line_num: int, lines: List[str],
        start_idx: int, parent_class: Optional[str]
    ) -> Optional[SymbolInfo]:
        try:
            name_part = line[4:]  # Remove "def "
            paren_idx = name_part.find("(")
            if paren_idx < 0:
                return None
            name = name_part[:paren_idx].strip()
            if not name or not name.isidentifier():
                return None

            end_line = PythonParser._find_block_end(lines, start_idx)
            sig_end = line.find(":")
            signature = line[:sig_end].strip() if sig_end > 0 else line.strip()

            return SymbolInfo(
                name=name,
                kind="function",
                file_path=file_path,
                start_line=line_num,
                end_line=end_line,
                signature=signature,
                parent=parent_class,
            )
        except Exception:
            return None

    @staticmethod
    def _extract_calls(line: str, file_path: str, line_num: int) -> List[SymbolInfo]:
        calls = []
        import re
        # Match function calls: word(
        for match in re.finditer(r'(\b[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)\s*\(', line):
            call_name = match.group(1)
            # Skip built-in keywords and common non-call patterns
            if call_name in {"if", "elif", "while", "for", "with", "return", "print",
                            "range", "len", "str", "int", "float", "list", "dict",
                            "set", "tuple", "type", "isinstance", "issubclass",
                            "super", "property", "staticmethod", "classmethod"}:
                continue
            calls.append(SymbolInfo(
                name=call_name,
                kind="call",
                file_path=file_path,
                start_line=line_num,
                end_line=line_num,
                targets=[call_name],
            ))
        return calls

    @staticmethod
    def _find_block_end(lines: List[str], start_idx: int) -> int:
        """Find the end of a Python block by indentation."""
        if start_idx >= len(lines):
            return start_idx + 1

        start_line = lines[start_idx]
        base_indent = len(start_line) - len(start_line.lstrip())

        for i in range(start_idx + 1, min(start_idx + 500, len(lines))):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            current_indent = len(line) - len(stripped)
            if current_indent <= base_indent:
                return i  # 1-indexed handled by caller
        return len(lines)


class JavaScriptParser:
    """Line-based JavaScript/TypeScript parser for extracting structural elements."""

    @staticmethod
    def parse(content: str, file_path: str) -> FileAnalysis:
        lang = Language.TYPESCRIPT if file_path.endswith((".ts", ".tsx")) else Language.JAVASCRIPT
        analysis = FileAnalysis(file_path=file_path, language=lang)
        lines = content.split("\n")
        import re

        brace_depth = 0
        current_class: Optional[str] = None
        class_brace_depth: int = 0

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Track braces for scope
            brace_depth += stripped.count("{") - stripped.count("}")

            # Track class scope
            if current_class and brace_depth < class_brace_depth:
                current_class = None

            # Import detection
            if stripped.startswith("import ") or stripped.startswith("const ") and "require(" in stripped:
                imp = JavaScriptParser._parse_import(stripped, file_path, i)
                if imp:
                    analysis.imports.append(imp)

            # Class detection
            class_match = re.match(r'(?:export\s+)?(?:default\s+)?class\s+(\w+)', stripped)
            if class_match:
                name = class_match.group(1)
                analysis.classes.append(SymbolInfo(
                    name=name,
                    kind="class",
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    signature=stripped.split("{")[0].strip(),
                ))
                current_class = name
                class_brace_depth = brace_depth

            # Function detection
            func_patterns = [
                # function keyword
                re.compile(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\('),
                # Arrow functions assigned to const/let/var
                re.compile(r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\('),
                # Arrow functions with single param
                re.compile(r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\w+\s*=>'),
            ]

            for pattern in func_patterns:
                match = pattern.match(stripped)
                if match:
                    name = match.group(1)
                    kind = "method" if current_class else "function"
                    info = SymbolInfo(
                        name=name,
                        kind=kind,
                        file_path=file_path,
                        start_line=i,
                        end_line=i,
                        signature=stripped.split("{")[0].strip() if "{" in stripped else stripped,
                        parent=current_class,
                    )
                    if kind == "method":
                        analysis.methods.append(info)
                    else:
                        analysis.functions.append(info)
                    break

            # Method detection inside class
            if current_class:
                method_match = re.match(r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*{', stripped)
                if method_match and method_match.group(1) not in {"if", "while", "for", "switch", "catch"}:
                    name = method_match.group(1)
                    analysis.methods.append(SymbolInfo(
                        name=name,
                        kind="method",
                        file_path=file_path,
                        start_line=i,
                        end_line=i,
                        signature=stripped.split("{")[0].strip(),
                        parent=current_class,
                    ))

        return analysis

    @staticmethod
    def _parse_import(line: str, file_path: str, line_num: int) -> Optional[SymbolInfo]:
        import re
        # import X from 'module'
        match = re.search(r"""from\s+['"]([^'"]+)['"]""", line)
        if match:
            module = match.group(1)
            return SymbolInfo(
                name=module,
                kind="import",
                file_path=file_path,
                start_line=line_num,
                end_line=line_num,
                targets=[module],
            )
        # require('module')
        match = re.search(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", line)
        if match:
            module = match.group(1)
            return SymbolInfo(
                name=module,
                kind="import",
                file_path=file_path,
                start_line=line_num,
                end_line=line_num,
                targets=[module],
            )
        return None


# Parser Registry
PARSERS = {
    Language.PYTHON: PythonParser,
    Language.JAVASCRIPT: JavaScriptParser,
    Language.TYPESCRIPT: JavaScriptParser,
}


def parse_file(file_path: str, content: str) -> FileAnalysis:
    """Parse a source file and return structural analysis.

    Args:
        file_path: Path of the file (used for language detection and graph node identity).
        content: The file's source code content.

    Returns:
        FileAnalysis with extracted classes, functions, methods, imports, and calls.
    """
    language = detect_language(file_path)
    parser_cls = PARSERS.get(language)

    if not parser_cls:
        return FileAnalysis(
            file_path=file_path,
            language=language,
            errors=[f"No parser available for language: {language.value}"],
        )

    try:
        return parser_cls.parse(content, file_path)
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}", exc_info=True)
        return FileAnalysis(
            file_path=file_path,
            language=language,
            errors=[f"Parse error: {str(e)}"],
        )


def parse_diff_files(
    diff_files: List[Dict[str, Any]],
) -> List[FileAnalysis]:
    """Parse multiple files from a PR diff payload.

    Args:
        diff_files: List of dicts with 'path' and 'content' keys.

    Returns:
        List of FileAnalysis results for parseable files.
    """
    results = []
    for file_info in diff_files:
        path = file_info.get("path", "")
        content = file_info.get("content", "")
        language = detect_language(path)
        if language == Language.UNKNOWN:
            continue
        analysis = parse_file(path, content)
        results.append(analysis)
    return results
