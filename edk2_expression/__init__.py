"""EDK II expression parser"""
from __future__ import annotations

__version__ = "0.2.0"

import edk2_expression.ast
import edk2_expression.lex
from edk2_expression.ast import Expression, NestMethod


def parse(text: str) -> edk2_expression.ast.Expression:
    lexer = edk2_expression.lex.Edk2ExpressionLexer()
    tokens = list(lexer.get_tokens_unprocessed(text))
    return edk2_expression.ast.parse(tokens)
