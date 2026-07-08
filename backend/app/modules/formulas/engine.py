"""AST-based safe expression evaluator for PlantOS formulas.

Allowed:
- Numeric literals (int, float)
- Variable names (resolved from signal inputs)
- Binary operators: + - * / ** %
- Unary operators: + -
- Comparison: > >= < <= == !=
- Boolean: and or not
- Function calls from registered whitelist
- Ternary: x if cond else y  (or if(cond, x, y))

Forbidden:
- Attribute access, subscript, lambda, comprehension
- Assignment, loop, class/function definition
- __import__, __builtins__, eval, exec
- File/network/db access
"""

import ast
import operator
from typing import Any


class FormulaError(Exception):
    """Raised when formula is invalid or execution fails."""
    pass


class SafeFormulaEngine:
    """AST-based safe expression evaluator."""

    # Allowed built-in functions (whitelist)
    ALLOWED_FUNCTIONS = {
        'abs': abs, 'round': round,
        'min': min, 'max': max, 'sum': sum,
        'clamp': lambda x, lo, hi: max(lo, min(x, hi)),
        'normalize': lambda x, lo, hi: (x - lo) / (hi - lo) if hi != lo else 0,
    }

    ALLOWED_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg, ast.UAdd: operator.pos,
        ast.Eq: operator.eq, ast.NotEq: operator.ne,
        ast.Lt: operator.lt, ast.LtE: operator.le,
        ast.Gt: operator.gt, ast.GtE: operator.ge,
    }

    def validate(self, formula: str, input_names: list[str]) -> list[str]:
        """Parse formula and return list of validation errors (empty = valid)."""
        errors = []
        try:
            tree = ast.parse(formula.strip(), mode='eval')
        except SyntaxError as e:
            return [f"Syntax error: {e.msg}"]
        except Exception as e:
            return [f"Parse error: {e}"]

        visitor = _ValidatorVisitor(input_names, self.ALLOWED_FUNCTIONS)
        visitor.visit(tree)
        return visitor.errors

    def evaluate(self, formula: str, inputs: dict[str, float]) -> float:
        """Execute formula against input values. Raises FormulaError on failure."""
        try:
            tree = ast.parse(formula.strip(), mode='eval')
        except SyntaxError as e:
            raise FormulaError(f"Syntax error: {e.msg}")

        evaluator = _EvaluatorVisitor(inputs, self.ALLOWED_FUNCTIONS, self.ALLOWED_OPS)
        result = evaluator.visit(tree.body)
        if result is None:
            raise FormulaError("Formula returned None")
        return float(result)


class _ValidatorVisitor(ast.NodeVisitor):
    """Walk AST and collect all violations."""

    def __init__(self, input_names: list[str], allowed_funcs: dict):
        self.input_names = set(input_names)
        self.allowed_funcs = set(allowed_funcs)
        self.errors: list[str] = []

    def visit_Name(self, node: ast.Name):
        if node.id not in self.input_names and node.id not in self.allowed_funcs:
            self.errors.append(f"Unknown variable or function: '{node.id}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id not in self.allowed_funcs:
                self.errors.append(f"Forbidden function: '{node.func.id}'")
        else:
            self.errors.append("Only simple function calls are allowed (e.g. clamp(A, 0, 100))")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.errors.append(f"Forbidden: attribute access (e.g. {ast.unparse(node)})")
        # Stop visiting children to avoid cascading errors

    def visit_Subscript(self, node: ast.Subscript):
        self.errors.append("Forbidden: subscript/slice access")

    def visit_Lambda(self, node: ast.Lambda):
        self.errors.append("Forbidden: lambda expressions")

    def visit_ListComp(self, node: ast.ListComp):
        self.errors.append("Forbidden: list comprehensions")


class _EvaluatorVisitor(ast.NodeVisitor):
    """Walk AST and compute result."""

    def __init__(self, inputs: dict[str, float], allowed_funcs: dict, allowed_ops: dict):
        self.inputs = inputs
        self.funcs = allowed_funcs
        self.ops = allowed_ops

    def visit_Expression(self, node: ast.Expression):
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise FormulaError(f"Unsupported constant type: {type(node.value)}")

    def visit_Name(self, node: ast.Name):
        if node.id in self.inputs:
            return float(self.inputs[node.id])
        if node.id in self.funcs:
            return self.funcs[node.id]
        raise FormulaError(f"Unknown variable: '{node.id}'")

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        op_func = self.ops.get(type(node.op))
        if op_func is None:
            raise FormulaError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_func(operand)

    def visit_BinOp(self, node: ast.BinOp):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_func = self.ops.get(type(node.op))
        if op_func is None:
            raise FormulaError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(left, right)

    def visit_BoolOp(self, node: ast.BoolOp):
        values = [self.visit(v) for v in node.values]
        if isinstance(node.op, ast.And):
            return float(all(values))
        elif isinstance(node.op, ast.Or):
            return float(any(values))
        raise FormulaError("Unsupported boolean operator")

    def visit_Compare(self, node: ast.Compare):
        left = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            op_func = self.ops.get(type(op))
            if op_func is None:
                raise FormulaError(f"Unsupported comparison: {type(op).__name__}")
            if not op_func(left, right):
                return 0.0
        return 1.0

    def visit_IfExp(self, node: ast.IfExp):
        cond = self.visit(node.test)
        if cond:
            return self.visit(node.body)
        return self.visit(node.orelse)

    def visit_Call(self, node: ast.Call):
        func = self.visit(node.func)
        if not callable(func):
            raise FormulaError(f"'{ast.unparse(node.func)}' is not callable")
        args = [self.visit(a) for a in node.args]
        try:
            return float(func(*args))
        except Exception as e:
            raise FormulaError(f"Function call error: {e}")

    def generic_visit(self, node):
        raise FormulaError(f"Unsupported expression: {type(node).__name__}")
