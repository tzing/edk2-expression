from __future__ import annotations

import enum
import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass

from edk2_expression.error import NotSupported

if typing.TYPE_CHECKING:
    from pygments.token import Token


class NestMethod(str, enum.Enum):
    Error = "error"
    """Raise an error if a nested expression is encountered."""

    Ignore = "ignore"
    """Ignore nested expressions and return the original expression."""

    Evaluate = "evaluate"
    """Evaluate nested expressions and return the result."""

    @classmethod
    def _missing_(cls, value: str) -> NestMethod | None:
        name = value.lower()
        for member in cls:
            if member.value == name:
                return member


_DEFAULT_NEST_METHOD = NestMethod.Error


@dataclass(frozen=True)
class Expression(ABC):
    """Base class for all expressions."""

    @classmethod
    @abstractmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> Expression | None:
        """Parse a list of tokens into an expression AST. This method may pop
        items from the list when a expression is parsed.

        :param tokens: A list of tokens.
        :type tokens: list[tuple[int, Token, str]]
        :return: The parsed expression. The return value may be None if the
            input does not match format for this class.
        :rtype: Expression | None
        """

    @abstractmethod
    def __str__(self) -> str:
        """Return a string representation of the expression."""

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> object:
        """Evaluate the expression and return the result.

        :param context: A dictionary of macro definitions.
        :type context: dict[str, object]
        :param nest: How to handle nested expressions. Use ``NestMethod.Ignore``
            ("ignore") to ignore nested expressions and return the original
            expression. Use ``NestMethod.Evaluate`` ("evaluate") to evaluate
            nested expressions and return the result. Default to ``NestMethod.Error``
            ("error") for raising an error if a nested expression is encountered.
        :type nest: NestMethod | str
        :return: The result of the evaluation.
        :rtype: object
        :raises NotSupported: If the expression cannot be evaluated.
        """
        raise NotSupported(
            f"Evaluation not supported for {type(self).__name__}: {self}"
        )
