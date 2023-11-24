from unittest import TestCase

from pygments.token import Token

from edk2_expression.ast import parse
from edk2_expression.error import ParseError
from edk2_expression.lex import Edk2ExpressionLexer


class TestParseExpression(TestCase):
    def setUp(self) -> None:
        self.lexer = Edk2ExpressionLexer()

    def lex(self, text: str) -> list[tuple[Token, str]]:
        return list(self.lexer.get_tokens_unprocessed(text))

    def test_simple(self):
        tree = parse(self.lex("$(FOO)"))
        self.assertEqual(str(tree), "$(FOO)")
        self.assertEqual(tree.evaluate({"FOO": 16}), 16)

    def test_unary(self):
        tree = parse(self.lex("not TRUE"))
        self.assertEqual(str(tree), "!True")
        self.assertEqual(tree.evaluate({}), False)

    def test_binary(self):
        tree = parse(self.lex("2 <3"))
        self.assertEqual(str(tree), "2 < 3")
        self.assertEqual(tree.evaluate({}), True)

    def test_ternary(self):
        tree = parse(self.lex("true ? 5:7"))
        self.assertEqual(str(tree), "True ? 5 : 7")
        self.assertEqual(tree.evaluate({}), 5)

    def test_nested(self):
        tree = parse(self.lex("$(FOO) == 5 ? ($(BAR) +3) :$(BAZ)*3"))
        self.assertEqual(str(tree), "$(FOO) == 5 ? ($(BAR) + 3) : ($(BAZ) * 3)")

        self.assertEqual(tree.evaluate({"FOO": 5, "BAR": 3}), 6)
        self.assertEqual(tree.evaluate({"FOO": 3, "BAZ": 7}), 21)

    def test_unbalance_bracket(self):
        with self.assertRaises(ParseError) as cm:
            parse(self.lex("3 + 5)"))
        self.assertEqual(
            str(cm.exception), "Unbalanced brackets in expression '3 + 5)'"
        )

    def test_missing_operand(self):
        with self.assertRaises(ParseError) as cm:
            parse(self.lex("3+"))
        self.assertEqual(
            str(cm.exception), "Missing operand(s) for operator '+' in expression '3+'"
        )

        with self.assertRaises(ParseError) as cm:
            parse(self.lex("(3+)"))
        self.assertEqual(
            str(cm.exception),
            "Missing operand(s) for operator '+' in expression '(3+)'",
        )

    def test_missing_operator(self):
        with self.assertRaises(ParseError) as cm:
            parse(self.lex("3 5"))
        self.assertEqual(
            str(cm.exception),
            "Unbalanced operators or operands in expression '3 5'",
        )

    def test_comment(self):
        tree = parse(self.lex("$(FOO) # comment\n"))
        self.assertEqual(str(tree), "$(FOO)")

    def test_unknown_token(self):
        with self.assertRaises(ParseError) as cm:
            parse(self.lex("3 +$"))
        self.assertEqual(
            str(cm.exception),
            "Unexpected component '$' from '3 +$' position 3",
        )

    def test_unexpected_operator(self):
        with self.assertRaises(ParseError) as cm:
            parse(self.lex("3 :6"))
        self.assertEqual(str(cm.exception), "Invalid expression '3 :6'")
