import pytest
from app.services.analysis.source_parser import (
    FileAnalysis,
    Language,
    SymbolInfo,
    detect_language,
    parse_file,
)


def test_detect_language():
    assert detect_language("app/main.py") == Language.PYTHON
    assert detect_language("src/index.js") == Language.JAVASCRIPT
    assert detect_language("src/components/App.tsx") == Language.TYPESCRIPT
    assert detect_language("src/utils/helpers.ts") == Language.TYPESCRIPT
    assert detect_language("backend/main.go") == Language.GO
    assert detect_language("backend/Main.java") == Language.JAVA
    assert detect_language("docs/README.md") == Language.UNKNOWN


def test_parse_python_file():
    code = '''"""Module docstring."""
import os
from datetime import datetime, timezone

class BaseWorker:
    """Base worker class."""
    pass

class DataProcessor(BaseWorker):
    def __init__(self, name: str):
        self.name = name

    def process(self, data: dict) -> bool:
        """Process incoming data."""
        clean_data = self._clean(data)
        return bool(clean_data)

    def _clean(self, raw):
        return raw

def global_handler(event):
    processor = DataProcessor("worker-1")
    return processor.process(event)
'''
    parsed: FileAnalysis = parse_file("app/processor.py", code)
    assert parsed.file_path == "app/processor.py"
    assert parsed.language == Language.PYTHON
    assert len(parsed.errors) == 0

    # Verify imports
    import_names = {imp.name for imp in parsed.imports}
    assert any("os" in imp for imp in import_names)
    assert any("datetime" in imp for imp in import_names)

    # Verify classes
    class_names = {c.name for c in parsed.classes}
    assert "BaseWorker" in class_names
    assert "DataProcessor" in class_names

    # Verify methods
    method_names = {m.name for m in parsed.methods}
    assert "__init__" in method_names or "process" in method_names or "_clean" in method_names

    # Verify functions
    func_names = {f.name for f in parsed.functions}
    assert "global_handler" in func_names


def test_parse_typescript_file():
    code = '''import React, { useState } from 'react';
import { api } from '../services/api';

export class UserService {
    private token: string;

    constructor(token: string) {
        this.token = token;
    }

    async getUser(id: string) {
        return api.getMe();
    }
}

export function renderUserBadge(role: string) {
    return role.toUpperCase();
}
'''
    parsed: FileAnalysis = parse_file("src/components/UserComponent.tsx", code)
    assert parsed.file_path == "src/components/UserComponent.tsx"
    assert parsed.language == Language.TYPESCRIPT
    assert len(parsed.errors) == 0

    # Verify classes
    class_names = {c.name for c in parsed.classes}
    assert "UserService" in class_names

    # Verify functions
    func_names = {f.name for f in parsed.functions}
    assert "renderUserBadge" in func_names


def test_parse_syntax_error_resilience():
    code = """def invalid_python_syntax(
        unclosed parenthesis and bad code {{{
    """
    parsed = parse_file("broken.py", code)
    assert parsed.file_path == "broken.py"
    # Should safely return FileAnalysis without unhandled crash
    assert isinstance(parsed, FileAnalysis)
    assert parsed.language == Language.PYTHON
