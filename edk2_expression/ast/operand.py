from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from pygments.token import Token

from edk2_expression.ast.core import _DEFAULT_NEST_METHOD, Expression, NestMethod
from edk2_expression.error import EvaluationError, ParseError


def parse_operand(tokens: list[tuple[int, Token, str]]) -> Expression:
    for class_ in (
        Boolean,
        HexNumber,
        Integer,
        MacroVal,
        String,
        Guid,
        MacroDefined,
        PcdName,
        CName,
        Array,
    ):
        if (obj := class_.parse(tokens)) is not None:
            return obj


@dataclass(frozen=True)
class Constant(Expression):
    value: object

    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self.value == other.value
        raise TypeError(
            "'==' not supported between instances of "
            f"'{type(self).__name__}' and '{type(other).__name__}'"
        )

    def __hash__(self) -> int:
        return hash(self.value)

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> object:
        return self.value


@dataclass(frozen=True)
class Integer(Constant):
    value: int

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> Integer | None:
        _, token, text = tokens[0]
        if token in Token.Number.Integer:
            tokens.pop(0)
            return cls(int(text))

    def __int__(self) -> int:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (Integer, int)):
            return self.value == int(other)
        return super().__eq__(other)

    def __lt__(self, other: object) -> bool:
        if isinstance(other, (Integer, int)):
            return self.value < int(other)
        raise TypeError(
            "'<' not supported between instances of "
            f"'{type(self).__name__}' and '{type(other).__name__}'"
        )

    def __le__(self, other: object) -> bool:
        if isinstance(other, (Integer, int)):
            return self.value <= int(other)
        raise TypeError(
            "'<=' not supported between instances of "
            f"'{type(self).__name__}' and '{type(other).__name__}'"
        )

    def __gt__(self, other: object) -> bool:
        if isinstance(other, (Integer, int)):
            return self.value > int(other)
        raise TypeError(
            "'>' not supported between instances of "
            f"'{type(self).__name__}' and '{type(other).__name__}'"
        )

    def __ge__(self, other: object) -> bool:
        if isinstance(other, (Integer, int)):
            return self.value >= int(other)
        raise TypeError(
            "'>=' not supported between instances of "
            f"'{type(self).__name__}' and '{type(other).__name__}'"
        )

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class HexNumber(Integer):
    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> Integer | None:
        _, token, text = tokens[0]
        if token in Token.Number.Hex:
            tokens.pop(0)
            hex_ = text[2:]
            return cls(int(hex_, 16))

    def __str__(self) -> str:
        return f"0x{self.value:x}"


@dataclass(frozen=True)
class Boolean(Constant):
    value: bool

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> Boolean | None:
        _, token, text = tokens[0]
        if token not in Token.Keyword.Constant:
            return

        text = text.lower()
        if text == "true":
            tokens.pop(0)
            return cls(True)
        elif text == "false":
            tokens.pop(0)
            return cls(False)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, bool):
            return self.value == other
        return super().__eq__(other)

    def __bool__(self) -> bool:
        return self.value

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class String(Constant):
    value: str

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> Boolean | None:
        _, _, prefix = tokens[0]
        if prefix not in ('"', "'", 'L"', "L'"):
            return None

        if match_token_types(
            tokens,
            Token.Punctuation,
            Token.String,
            Token.Punctuation,
        ):
            tokens.pop(0)
            _, _, text = tokens.pop(0)
            tokens.pop(0)
            return cls(text)

        if match_token_types(
            tokens,
            Token.Punctuation,
            Token.Punctuation,
        ):
            tokens.pop(0)
            tokens.pop(0)
            return cls("")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    def __str__(self) -> str:
        return f'"{self.value}"'


@dataclass(frozen=True)
class Guid(Constant):
    value: bytes

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> Guid | None:
        _, token, text = tokens[0]
        if (
            True
            and token in Token.Name.Entity
            and re.fullmatch(
                r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                text,
                re.RegexFlag.IGNORECASE,
            )
        ):
            tokens.pop(0)
            return cls(bytes.fromhex(text.replace("-", "")))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Guid):
            return self.value == other.value
        if isinstance(other, uuid.UUID):
            return self.value == other.bytes
        return super().__eq__(other)

    def __str__(self) -> str:
        return str(uuid.UUID(bytes=self.value))

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> object:
        return uuid.UUID(bytes=self.value)


@dataclass(frozen=True)
class MacroVal(Expression):
    macro: str

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> MacroVal | None:
        if not match_token_types(
            tokens,
            Token.Keyword.Declaration,
            Token.Name.Variable,
            Token.Keyword.Declaration,
        ):
            return None

        _, _, prefix = tokens[0]
        if prefix != "$(":
            return None

        tokens.pop(0)  # "$("
        _, _, text = tokens.pop(0)
        tokens.pop(0)  # ")"
        return cls(text)

    def __str__(self) -> str:
        return f"$({self.macro})"

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> object:
        val = context.get(self.macro)
        if val is None:
            raise EvaluationError(f"Macro '{self.macro}' is not defined")
        if isinstance(val, Expression):
            nest = NestMethod(nest)
            if nest == NestMethod.Error:
                raise EvaluationError(f"Nested expression found in '{self}': {val}")
            elif nest == NestMethod.Ignore:
                return self
            elif nest == NestMethod.Evaluate:
                return val.evaluate(context, nest)
        return val


@dataclass(frozen=True)
class MacroDefined(Expression):
    """Function to check if a macro is defined. This is NOT a EDK II standard
    expression and therefore is not enabled by default. See readme for more
    information."""

    macro: str

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> MacroVal | None:
        if not match_token_types(
            tokens,
            Token.Keyword.Type,
            Token.Punctuation,
            Token.Name.Variable,
            Token.Punctuation,
        ):
            return None

        _, _, prefix = tokens[0]
        if prefix != "DEFINED":
            return None

        tokens.pop(0)  # "DEFINED"
        tokens.pop(0)  # "("
        _, _, text = tokens.pop(0)
        tokens.pop(0)  # ")"
        return cls(text)

    def __str__(self) -> str:
        return f"DEFINED({self.macro})"

    def evaluate(
        self, context: dict[str, object], nest: NestMethod | str = _DEFAULT_NEST_METHOD
    ) -> object:
        return self.macro in context


@dataclass(frozen=True)
class CName(Expression):
    name: str

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> CName | None:
        _, token, text = tokens[0]
        if token in Token.Name.Variable:
            tokens.pop(0)
            return cls(text)

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class PcdName(Expression):
    name: str

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> PcdName | None:
        _, token, text = tokens[0]
        if (
            True
            and token in Token.Name.Entity
            and re.fullmatch(r"[a-zA-Z_]\w*\.[a-zA-Z_]\w*", text)
        ):
            tokens.pop(0)
            return cls(text)

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Array(Expression):
    """Array expression - NOT PARSED"""

    raw: str

    @classmethod
    def parse(cls, tokens: list[tuple[int, Token, str]]) -> PcdName | None:
        _, token, text = tokens[0]
        if token not in Token.Punctuation or text != "{":
            return None

        level = 0
        buffer = []
        while tokens:
            end_pos, token, text = tokens.pop(0)
            buffer.append(text)
            if token in Token.Punctuation and text == "{":
                level += 1
            if token in Token.Punctuation and text == "}":
                level -= 1
                if level == 0:
                    break

        expr = "".join(buffer)

        if level != 0:
            raise ParseError(
                f"Unbalanced brackets at position {end_pos}: "
                f"missing closing bracket after '{expr}'"
            )

        return cls(expr)

    def __str__(self) -> str:
        return self.raw


def match_token_types(tokens: list[tuple[int, Token, str]], *expect: Token) -> bool:
    if len(tokens) < len(expect):
        return False
    for expect_type, (_, token_type, _) in zip(expect, tokens):
        if token_type not in expect_type:
            return False
    return True
