import ast
import re
from app.analyzers.base import Analyzer
from app.domain.models import CodeSubmission, Finding, Severity


MAX_LINE_LENGTH = 100
SNAKE_CASE = re.compile(r"^[a-z_][a-z0-9_]*$")
PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")

class StyleAnalyzer(Analyzer):
    name = "style"

    def analyze(self, submission: CodeSubmission) -> list[Finding]:
        findings: list[Finding] = []

        for i, line in enumerate(submission.lines, start=1):
            if len(line) > MAX_LINE_LENGTH:
                findings.append(Finding(
                    analyzer=self.name, severity=Severity.LOW, category="style",
                    line=i, message=f"Line exceeds {MAX_LINE_LENGTH} characters "
                                     f"({len(line)}).",
                ))
            if line != line.rstrip():
                findings.append(Finding(
                    analyzer=self.name, severity=Severity.INFO, category="style",
                    line=i, message="Trailing whitespace.",
                ))

        try:
            tree = ast.parse(submission.code, filename=submission.filename)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not SNAKE_CASE.match(node.name) and not node.name.startswith("__"):
                    findings.append(Finding(
                        analyzer=self.name, severity=Severity.LOW, category="style",
                        line=node.lineno,
                        message=f"Function '{node.name}' should be snake_case.",
                    ))
                if not ast.get_docstring(node) and not node.name.startswith("_"):
                    findings.append(Finding(
                        analyzer=self.name, severity=Severity.INFO, category="style",
                        line=node.lineno,
                        message=f"Public function '{node.name}' has no docstring.",
                    ))
            if isinstance(node, ast.ClassDef):
                if not PASCAL_CASE.match(node.name):
                    findings.append(Finding(
                        analyzer=self.name, severity=Severity.LOW, category="style",
                        line=node.lineno,
                        message=f"Class '{node.name}' should be PascalCase.",
                    ))

        return findings

        