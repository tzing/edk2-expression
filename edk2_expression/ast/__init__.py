from __future__ import annotations

from pygments.token import Token

from edk2_expression.ast.core import Expression, NestMethod
from edk2_expression.ast.operand import parse_operand
from edk2_expression.ast.operator import pop_operator, push_operator
from edk2_expression.error import ParseError


def parse(tokens: list[tuple[int, Token, str]]) -> Expression:
    """Parse a list of tokens into an expression AST.

    :param tokens: A list of tokens to parse.
       The tokens is the output of ``RegexLexer.get_tokens_unprocessed`` from
       Pygments, which is a list of tuples of ``(position, token_type, token_text)``.
    :type tokens: list[tuple[int, Token, str]]
    :return: The parsed expression AST.
    :rtype: Expression
    :raises ParseError: If the tokens cannot be parsed into an expression AST.
    """
    raw_expression = "".join(token[2] for token in tokens)

    # use shunting yard algorithm
    output_stack = []
    operator_stack = []
    while tokens:
        head_token_pos, head_token_type, head_token_text = tokens[0]

        # ignore whitespace
        if head_token_type in Token.Text.Whitespace or head_token_type in Token.Comment:
            tokens.pop(0)

        # parse operand
        elif (operand := parse_operand(tokens)) is not None:
            output_stack.append(operand)

        # opening bracket - force insert
        elif head_token_type in Token.Punctuation and head_token_text == "(":
            tokens.pop(0)
            operator_stack.append("(")

        # operators
        elif head_token_type in Token.Operator:
            tokens.pop(0)
            push_operator(head_token_text, operator_stack, output_stack)

        # closing bracket
        elif head_token_type in Token.Punctuation and head_token_text == ")":
            done = False
            while operator_stack:
                try:
                    popped = pop_operator(operator_stack, output_stack)
                except ParseError as e:
                    raise ParseError(f"{e} in expression '{raw_expression}'")
                if popped == "(":
                    tokens.pop(0)
                    done = True
                    break
            if not done:
                raise ParseError(
                    f"Unbalanced brackets in expression '{raw_expression}'"
                )

        else:
            raise ParseError(
                f"Unexpected component '{head_token_text}' from '{raw_expression}' position {head_token_pos}"
            )

    while operator_stack:
        try:
            pop_operator(operator_stack, output_stack)
        except ParseError as e:
            raise ParseError(f"{e} in expression '{raw_expression}'")

    if len(output_stack) != 1:
        raise ParseError(
            f"Unbalanced operators or operands in expression '{raw_expression}'"
        )

    output = output_stack[0]
    if not isinstance(output, Expression):
        raise ParseError(f"Invalid expression '{raw_expression}'")

    return output
