import ast
import re
from app.analyzers.base import Analyzer
from app.domain.models import CodeSubmission, Finding, Severity

DANGEROUS_CALLS = {
    "eval": Severity.CRITICAL,
    "exec": Severity.CRITICAL,
    "pickle.loads": Severity.HIGH,
    "yaml.load": Severity.HIGH,
    "os.system": Severity.HIGH,
    "subprocess.call": Severity.MEDIUM,
}

SECRET_PATTERN = re.compile(
    r'(?i)\b(api_key|secret|password|token|passwd)\b\s*=\s*["\'][^"\']{4,}["\']'
)


def _call_full_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = []
        cur = func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            return ".".join(reversed(parts))
    return None


class SecurityAnalyzer(Analyzer):
    name = "security"

    def analyze(self, submission: CodeSubmission) -> list[Finding]:
        findings: list[Finding] = []
        try:
            tree = ast.parse(submission.code, filename=submission.filename)
        except SyntaxError:
            return []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                full_name = _call_full_name(node)
                if full_name in DANGEROUS_CALLS:
                    findings.append(Finding(
                        analyzer=self.name, severity=DANGEROUS_CALLS[full_name],
                        category="security", line=node.lineno,
                        message=f"Use of '{full_name}()' is a common injection/"
                                f"deserialization risk.",
                        suggestion="Avoid dynamic execution / unsafe deserialization "
                                   "on untrusted input; use a safe alternative.",
                    ))
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    findings.append(Finding(
                        analyzer=self.name, severity=Severity.MEDIUM,
                        category="security", line=node.lineno,
                        message="Bare 'except:' silently swallows all errors, "
                                "including ones you want to know about.",
                        suggestion="Catch specific exception types instead.",
                    ))

        for i, line in enumerate(submission.lines, start=1):
            if SECRET_PATTERN.search(line):
                findings.append(Finding(
                    analyzer=self.name, severity=Severity.CRITICAL,
                    category="security", line=i,
                    message="Possible hardcoded secret/credential.",
                    suggestion="Load secrets from environment variables or a secret manager.",
                ))

        return findings