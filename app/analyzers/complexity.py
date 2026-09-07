import ast


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