from __future__ import annotations

import typing
from abc import abstractmethod
from dataclasses import dataclass

from edk2_expression.ast.core import _DEFAULT_NEST_METHOD, Expression, NestMethod
from edk2_expression.error import ParseError

if typing.TYPE_CHECKING:
    from typing import NoReturn

    from pygments.token import Token

OPERATOR_PRECEDENCE = {
    # https://en.cppreference.com/w/c/language/operator_precedence
    "!": 2,
    "~": 2,
    "*": 3,
    "/": 3,
    "%": 3,
    "+": 4,
    "-": 4,
    "<<": 5,
    ">>": 5,
    "<": 6,
    "<=": 6,
    ">": 6,
    ">=": 6,
    "==": 7,
    "!=": 7,
    "&": 8,
    "^": 9,
    "|": 10,
    "&&": 11,
    "xor": 12,  # not in C
    "||": 13,  # shifted
    ":": 14,  # not in C
    "?": 15,  # shifted
    "(": 99,
}

OPERATOR_REMAP = {
    "NOT": "!",
    "not": "!",
    "LT": "<",
    "LE": "<=",
    "GT": ">",
    "GE": ">=",
    "EQ": "==",
    "NE": "!=",
    "AND": "&&",
    "and": "&&",
    "OR": "||",
    "or": "||",
    "XOR": "xor",
}


def push_operator(
    current_operator: str, operator_stack: list[str], output_stack: list[Expression]
) -> None:
    """Push an operator to operator stack but make sure the precedence is correct.
    This function performs the push operator step in shunting yard algorithm.

    :param current_operator: The operator to push.
    :type current_operator: str
    :param operator_stack: The operator stack.
    :type operator_stack: list[str]
    :param output_stack: The output stack.
    :type output_stack: list[Expression]
    """
    # insert operator based on precedence table
    operator = OPERATOR_REMAP.get(current_operator, current_operator)
    current_precedence = OPERATOR_PRECEDENCE.get(operator)
    if not current_precedence:
        raise ParseError(f"Unknown operator '{current_operator}'")

    # stack empty, direct insert
    if not operator_stack:
        operator_stack.append(operator)
        return

    last_precedence = OPERATOR_PRECEDENCE[operator_stack[-1]]
    if current_precedence < last_precedence:
        operator_stack.append(operator)
        return

    # pop last operator and retry
    pop_operator(operator_stack, output_stack)
    return push_operator(operator, operator_stack, output_stack)


def pop_operator(
    operator_stack: list[str], output_stack: list[Expression]
) -> str | None:
    """Pop operator from operator stack, create `Expression` instance and push
    to output stack. This function performs the pop operator step in shunting
    yard algorithm.

    :param operator_stack: The operator stack.
    :type operator_stack: list[str]
    :param output_stack: The output stack.
    :type output_stack: list[Expression]
    :returns: The popped operator.
    :rtype: str
    :raises ParseError: If the operator is unknown or missing operands.
    """
    OPERATOR_CLASS = {
        "(": (None, None),
        "!": (1, LogicalNot),
        "~": (1, BitwiseNot),
        "*": (2, Multiplication),
        "/": (2, Division),
        "%": (2, Modulo),
        "+": (2, Addition),
        "-": (2, Subtraction),
        "<<": (2, BitwiseLeftShift),
        ">>": (2, BitwiseRightShift),
        "<": (2, LessThan),
        "<=": (2, LessEqual),
        ">": (2, GreaterThan),
        ">=": (2, GreaterEqual),
        "==": (2, Equal),
        "!=": (2, NotEqual),
        "&": (2, BitwiseAnd),
        "^": (2, BitwiseXor),
        "|": (2, BitwiseOr),
        "&&": (2, LogicalAnd),
        "||": (2, LogicalOr),
        "xor": (2, LogicalXor),
        ":": (2, TernaryOp.Decision),
        "?": (2, TernaryOp),  # values should be wrapped by ':' first
    }

    num_operands, operator_class = OPERATOR_CLASS.get(
        last_operator := operator_stack.pop(),
        (-1, None),
    )
    if num_operands is None:
        return last_operator
    if operator_class is None:
        # unknown operator should be blocked by push_operator() instead of here
        raise RuntimeError(f"Unknown operator '{last_operator}'")

    if len(output_stack) < num_operands:
        raise ParseError(f"Missing operand(s) for operator '{last_operator}'")

    # pop operands from output stack
    # the stack is managed by the caller so use pop() instead of slice
    operands = reversed([output_stack.pop() for _ in range(num_operands)])
    output_stack.append(operator_class(*operands))

    return last_operator


@dataclass(frozen=True)
class Operator(Expression):
    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> NoReturn:
        """``Operator.parse()`` should not be called.

        :raises RuntimeError: Always.
        """
        raise RuntimeError("Operator.parse() should not be called")


@dataclass(frozen=True)
class UnaryOp(Operator):
    sub: Expression

    @abstractmethod
    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> object:
        """Evaluate the operator with the given context."""


@dataclass(frozen=True)
class LogicalNot(UnaryOp):
    def __str__(self) -> str:
        return f"!{self.sub}"

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> bool:
        return not self.sub.evaluate(context, nest)


@dataclass(frozen=True)
class BitwiseNot(UnaryOp):
    def __str__(self) -> str:
        return f"~{self.sub}"

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> int:
        return ~self.sub.evaluate(context, nest)


@dataclass(frozen=True)
class BinaryOp(Operator):
    left: Expression
    right: Expression

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> object:
        left_value = self.left.evaluate(context, nest)
        right_value = self.right.evaluate(context, nest)
        if isinstance(left_value, Expression) or isinstance(right_value, Expression):
            nest = NestMethod(nest)
            if nest == NestMethod.Ignore:
                return self
            else:
                raise RuntimeError("Unknown error for nested expression")
        return self.compare(left_value, right_value)

    @classmethod
    @abstractmethod
    def compare(self, a: object, b: object) -> bool:
        """Compare two objects and return the result."""


@dataclass(frozen=True)
class Multiplication(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} * {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a * b


@dataclass(frozen=True)
class Division(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} / {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a / b


@dataclass(frozen=True)
class Modulo(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} % {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a % b


@dataclass(frozen=True)
class Addition(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} + {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a + b


@dataclass(frozen=True)
class Subtraction(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} - {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a - b


@dataclass(frozen=True)
class BitwiseLeftShift(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} << {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a << b


@dataclass(frozen=True)
class BitwiseRightShift(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} >> {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a >> b


@dataclass(frozen=True)
class LessThan(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} < {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a < b


@dataclass(frozen=True)
class LessEqual(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} <= {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a <= b


@dataclass(frozen=True)
class GreaterThan(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} > {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a > b


@dataclass(frozen=True)
class GreaterEqual(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} >= {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a >= b


@dataclass(frozen=True)
class Equal(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} == {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a == b


@dataclass(frozen=True)
class NotEqual(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} != {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a != b


@dataclass(frozen=True)
class BitwiseAnd(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} & {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a & b


@dataclass(frozen=True)
class BitwiseXor(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} ^ {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a ^ b


@dataclass(frozen=True)
class BitwiseOr(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} | {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return a | b


@dataclass(frozen=True)
class LogicalAnd(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} && {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return bool(a) and bool(b)


@dataclass(frozen=True)
class LogicalXor(BinaryOp):
    def __str__(self) -> str:
        return f"{self.left} xor {self.right}"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return bool(a) != bool(b)


@dataclass(frozen=True)
class LogicalOr(BinaryOp):
    def __str__(self) -> str:
        return f"({self.left} || {self.right})"

    @classmethod
    def compare(self, a: object, b: object) -> bool:
        return bool(a) or bool(b)


@dataclass(frozen=True)
class TernaryOp(Operator):
    @dataclass(frozen=True)
    class Decision(Operator):
        """Value holder for ternary operator."""

        true: Expression
        false: Expression

        def __str__(self) -> str:
            return f"{self.true} : {self.false}"

    condition: Expression
    decision: Decision

    def __post_init__(self):
        if not isinstance(self.decision, self.Decision):
            raise ParseError(
                "Right hand side for '?' must be operands separated by ':'. "
                f"Got '{self.decision}'"
            )

    def __str__(self) -> str:
        return f"{self.condition} ? {self.decision}"

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> object:
        if self.condition.evaluate(context):
            return self.decision.true.evaluate(context, nest)
        else:
            return self.decision.false.evaluate(context, nest)
