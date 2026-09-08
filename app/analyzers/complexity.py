import ast
from app.analyzers.base import Analyzer
from app.domain.models import CodeSubmission, Finding, Severity

MAX_COMPLEXITY = 10
MAX_FUNCTION_LINES = 50
MAX_PARAMS = 5
MAX_NESTING = 4
 
def _cyclomatic_complexity(node: ast.AST) -> int:
    complexity = 1
    decision_types = (ast.If,ast.While,ast.For,ast.Try,ast.With,ast.ExceptHandler,ast.BoolOp,ast.Assert)

    for child in ast.walk(node):
        if isinstance(child,decision_types):
            complexity += 1
    return complexity

def _max_nesting_depth(node: ast.AST,depth: int = 0) -> int:
    nesting_nodes  = (ast.If,ast.For,ast.While,ast.Try,ast.With)
    best = depth

    for child in ast.iter_child_nodes(node):
        child_depth = depth + 1 if isinstance(child,nesting_nodes) else depth
        best = max(best,_max_nesting_depth(child,child_depth))

    return best

class ComplexityAnalyzer(Analyzer):
   name = "complexity"

   def analyze(self,submission: CodeSubmission) -> list[Finding]:
        findings : list[Finding] = []

        try:
            tree = ast.parse(submission.code,filename=submission.filename)
        except SyntaxError as e:
            return [Finding(analyzer=self.name, severity=Severity.CRITICAL, category="syntax", message = f"Code does not parse: {e.msg}", line = e.lineno)]

        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            complexity = _cyclomatic_complexity(node)

            if complexity > MAX_COMPLEXITY:
                findings.append(Finding(analyzer = self.name, severity = Severity.HIGH, category="complexity", message=f"Function '{node.name}' has cyclomatic complexity "
                            f"{complexity} (threshold {MAX_COMPLEXITY}).",line = node.lineno, suggestion="Extract branches into smaller helper functions.",))

            n_lines = (node.end_lineno or node.lineno) - node.lineno

            if n_lines > MAX_FUNCTION_LINES:
                findings.append(Finding(analyzer = self.name, severity = Severity.MEDIUM, category="complexity",message=f"Function '{node.name}' is {n_lines} lines long "
                f"(threshold {MAX_FUNCTION_LINES}).",suggestion="Consider splitting into smaller, single-purpose functions.",line = node.lineno))

            n_params = len(node.args.args) + len(node.args.kwonlyargs)
            if n_params > MAX_PARAMS:
                findings.append(Finding(
                    analyzer=self.name, severity=Severity.LOW, category="complexity",
                    line=node.lineno,
                    message=f"Function '{node.name}' takes {n_params} parameters "
                            f"(threshold {MAX_PARAMS}).",
                    suggestion="Group related parameters into a dataclass or config object.",
                ))

            depth = _max_nesting_depth(node)
            if depth > MAX_NESTING:
                findings.append(Finding(
                    analyzer=self.name, severity=Severity.MEDIUM, category="complexity",
                    line=node.lineno,
                    message=f"Function '{node.name}' nests {depth} levels deep "
                            f"(threshold {MAX_NESTING}).",
                    suggestion="Use early returns / guard clauses to flatten nesting.",
                ))

        return findings