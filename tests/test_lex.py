import unittest

from pygments.token import Token

from edk2_expression.lex import Edk2ExpressionLexer


class TestEdk2ExpressionLexer(unittest.TestCase):
    def setUp(self) -> None:
        self.lexer = Edk2ExpressionLexer()

    def lex(self, text: str) -> list[tuple[Token, str]]:
        tokens = []
        for _, token, text in self.lexer.get_tokens_unprocessed(text):
            tokens.append((token, text))
        return tokens

    def test_StringLiteral(self):
        self.assertEqual(
            self.lex("L'SampleString'"),
            [
                (Token.Punctuation, "L'"),
                (Token.String, "SampleString"),
                (Token.Punctuation, "'"),
            ],
        )
        self.assertEqual(
            self.lex('"AnotherString"'),
            [
                (Token.Punctuation, '"'),
                (Token.String, "AnotherString"),
                (Token.Punctuation, '"'),
            ],
        )

    def test_TrueFalse(self):
        self.assertEqual(
            self.lex("TRUE"),
            [
                (Token.Keyword.Constant, "TRUE"),
            ],
        )
        self.assertEqual(
            self.lex("False"),
            [
                (Token.Keyword.Constant, "False"),
            ],
        )

    def test_HexNumber(self):
        self.assertEqual(
            self.lex("0XFF"),
            [
                (Token.Number.Hex, "0XFF"),
            ],
        )

    def test_Integer(self):
        self.assertEqual(
            self.lex("12345"),
            [
                (Token.Number.Integer, "12345"),
            ],
        )
        self.assertEqual(
            self.lex("6"),
            [
                (Token.Number.Integer, "6"),
            ],
        )

    def test_PcdName(self):
        self.assertEqual(
            self.lex("gUefiCpuPkgTokenSpaceGuid.PcdCpuLocalApicBaseAddress"),
            [
                (
                    Token.Name.Entity,
                    "gUefiCpuPkgTokenSpaceGuid.PcdCpuLocalApicBaseAddress",
                ),
            ],
        )

    def test_GuidValue(self):
        self.assertEqual(
            self.lex("123e4567-e89b-12d3-a456-426655440000"),
            [
                (Token.Name.Entity, "123e4567-e89b-12d3-a456-426655440000"),
            ],
        )
        self.assertEqual(
            self.lex(
                "{0x123e4567, 0xe89b, 0x12d3, {0xa4, 0x56, 0x42, 0x66, 0x55, 0x44, 0x00, 0x00}}"
            ),
            [
                (Token.Punctuation, "{"),
                (Token.Literal.Number.Hex, "0x123e4567"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0xe89b"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0x12d3"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Punctuation, "{"),
                (Token.Literal.Number.Hex, "0xa4"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0x56"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0x42"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0x66"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0x55"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0x44"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0x00"),
                (Token.Punctuation, ","),
                (Token.Text.Whitespace, " "),
                (Token.Literal.Number.Hex, "0x00"),
                (Token.Punctuation, "}"),
                (Token.Punctuation, "}"),
            ],
        )

    def test_MACROVAL(self):
        self.assertEqual(
            self.lex("$(TEST)"),
            [
                (Token.Keyword.Declaration, "$("),
                (Token.Name.Variable, "TEST"),
                (Token.Keyword.Declaration, ")"),
            ],
        )

    def test_CName(self):
        self.assertEqual(
            self.lex("testName"),
            [
                (Token.Name.Variable, "testName"),
            ],
        )
        self.assertEqual(
            self.lex("notKeyword"),
            [
                (Token.Name.Variable, "notKeyword"),
            ],
        )

    def test_UintMac(self):
        self.assertEqual(
            self.lex("{UINT8(8)}"),
            [
                (Token.Punctuation, "{"),
                (Token.Keyword.Type, "UINT8"),
                (Token.Punctuation, "("),
                (Token.Number.Integer, "8"),
                (Token.Punctuation, ")"),
                (Token.Punctuation, "}"),
            ],
        )

    def test_Label(self):
        self.assertEqual(
            self.lex("{LABEL(testLabel)}"),
            [
                (Token.Punctuation, "{"),
                (Token.Keyword.Type, "LABEL"),
                (Token.Punctuation, "("),
                (Token.Name.Variable, "testLabel"),
                (Token.Punctuation, ")"),
                (Token.Punctuation, "}"),
            ],
        )

    def test_Offset(self):
        self.assertEqual(
            self.lex("{OFFSET_OF(test)}"),
            [
                (Token.Punctuation, "{"),
                (Token.Keyword.Type, "OFFSET_OF"),
                (Token.Punctuation, "("),
                (Token.Name.Variable, "test"),
                (Token.Punctuation, ")"),
                (Token.Punctuation, "}"),
            ],
        )

    def test_DevicePath(self):
        self.assertEqual(
            self.lex('{DEVICE_PATH(".")}'),
            [
                (Token.Punctuation, "{"),
                (Token.Keyword.Type, "DEVICE_PATH"),
                (Token.Punctuation, '("'),
                (Token.String, "."),
                (Token.Punctuation, '")'),
                (Token.Punctuation, "}"),
            ],
        )

    def test_GuidStr(self):
        self.assertEqual(
            self.lex('{GUID("123e4567-e89b-12d3-a456-426655440000")}'),
            [
                (Token.Punctuation, "{"),
                (Token.Keyword.Type, "GUID"),
                (Token.Punctuation, '("'),
                (Token.Name.Entity, "123e4567-e89b-12d3-a456-426655440000"),
                (Token.Punctuation, '")'),
                (Token.Punctuation, "}"),
            ],
        )
        self.assertEqual(
            self.lex("{GUID(test)}"),
            [
                (Token.Punctuation, "{"),
                (Token.Keyword.Type, "GUID"),
                (Token.Punctuation, "("),
                (Token.Name.Variable, "test"),
                (Token.Punctuation, ")"),
                (Token.Punctuation, "}"),
            ],
        )

        ll = self.lex(
            "{GUID({0x123e4567, 0xe89b, 0x12d3, {0xa4, 0x56, 0x42, 0x66, 0x55, 0x44, 0x00, 0x00}})}"
        )
        self.assertEqual(
            ll[:5],
            [
                (Token.Punctuation, "{"),
                (Token.Keyword.Type, "GUID"),
                (Token.Punctuation, "("),
                (Token.Punctuation, "{"),
                (Token.Literal.Number.Hex, "0x123e4567"),
            ],
        )
        self.assertEqual(
            ll[-5:],
            [
                (Token.Literal.Number.Hex, "0x00"),
                (Token.Punctuation, "}"),
                (Token.Punctuation, "}"),
                (Token.Punctuation, ")"),
                (Token.Punctuation, "}"),
            ],
        )

    def test_UnaryOp(self):
        self.assertEqual(
            self.lex("NOT gExample.Test"),
            [
                (Token.Operator, "NOT"),
                (Token.Text.Whitespace, " "),
                (Token.Name.Entity, "gExample.Test"),
            ],
        )
        self.assertEqual(
            self.lex("-16"),
            [
                (Token.Operator, "-"),
                (Token.Number.Integer, "16"),
            ],
        )

    def test_BinaryOp(self):
        self.assertEqual(
            self.lex("1 +2"),
            [
                (Token.Number.Integer, "1"),
                (Token.Text.Whitespace, " "),
                (Token.Operator, "+"),
                (Token.Number.Integer, "2"),
            ],
        )
        self.assertEqual(
            self.lex("True OR FALSE"),
            [
                (Token.Keyword.Constant, "True"),
                (Token.Text.Whitespace, " "),
                (Token.Operator, "OR"),
                (Token.Text.Whitespace, " "),
                (Token.Keyword.Constant, "FALSE"),
            ],
        )

    def test_TernaryOp(self):
        self.assertEqual(
            self.lex("foo ? bar : baz"),
            [
                (Token.Name.Variable, "foo"),
                (Token.Text.Whitespace, " "),
                (Token.Operator, "?"),
                (Token.Text.Whitespace, " "),
                (Token.Name.Variable, "bar"),
                (Token.Text.Whitespace, " "),
                (Token.Operator, ":"),
                (Token.Text.Whitespace, " "),
                (Token.Name.Variable, "baz"),
            ],
        )

    def test_nested(self):
        self.assertEqual(
            self.lex("(!FALSE)"),
            [
                (Token.Punctuation, "("),
                (Token.Operator, "!"),
                (Token.Keyword.Constant, "FALSE"),
                (Token.Punctuation, ")"),
            ],
        )

        self.assertEqual(
            self.lex("$(FOO) > (5-3)"),
            [
                (Token.Keyword.Declaration, "$("),
                (Token.Name.Variable, "FOO"),
                (Token.Keyword.Declaration, ")"),
                (Token.Text.Whitespace, " "),
                (Token.Operator, ">"),
                (Token.Text.Whitespace, " "),
                (Token.Punctuation, "("),
                (Token.Number.Integer, "5"),
                (Token.Operator, "-"),
                (Token.Number.Integer, "3"),
                (Token.Punctuation, ")"),
            ],
        )

    def test_comment(self):
        self.assertEqual(
            self.lex("1 # comment"),
            [
                (Token.Number.Integer, "1"),
                (Token.Text.Whitespace, " "),
                (Token.Comment.Single, "# comment"),
            ],
        )
