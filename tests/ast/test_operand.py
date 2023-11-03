import uuid
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

from pygments.token import Token

import edk2_expression.ast.operand as t
from edk2_expression.ast.core import Expression
from edk2_expression.error import EvaluationError, ParseError


class TestParseOperand(TestCase):
    def test(self):
        self.assertEqual(
            t.parse_operand([(0, Token.Keyword.Constant, "true")]), t.Boolean(True)
        )
        self.assertEqual(
            t.parse_operand([(0, Token.Number.Hex, "0xFF")]), t.HexNumber(255)
        )
        self.assertEqual(
            t.parse_operand([(0, Token.Number.Integer, "0")]), t.Integer(0)
        )


class TestConstant(TestCase):
    @patch.object(t.Constant, "__abstractmethods__", set())
    def test_eq(self):
        self.assertEqual(t.Constant(0), t.Constant(0))

        with self.assertRaises(TypeError) as cm:
            self.assertNotEqual(t.Constant(0), t.Integer(0))
        self.assertEqual(
            str(cm.exception),
            "'==' not supported between instances of 'Integer' and 'Constant'",
        )

    @patch.object(t.Constant, "__abstractmethods__", set())
    def test_hash(self):
        self.assertEqual(hash(t.Constant(0)), hash(0))
        self.assertEqual(hash(t.Constant("foo")), hash("foo"))


class TestInteger(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.Integer.parse([(0, Token.Number.Integer, "0")]), t.Integer(0)
        )
        self.assertIsNone(t.Integer.parse([(0, Token.Number, "0")]))

    def test_eq(self):
        self.assertEqual(t.Integer(0), t.Integer(0))
        self.assertEqual(t.Integer(0), 0)
        self.assertNotEqual(t.Integer(0), t.Integer(1))
        self.assertNotEqual(t.Integer(0), 1)
        with self.assertRaises(TypeError):
            t.Integer(0) == "NaN"

    def test_lt(self):
        self.assertLess(t.Integer(0), t.Integer(1))
        self.assertLess(t.Integer(0), 1)
        with self.assertRaises(TypeError):
            t.Integer(0) < "NaN"

    def test_le(self):
        self.assertLessEqual(t.Integer(0), t.Integer(1))
        self.assertLessEqual(t.Integer(0), 0)
        with self.assertRaises(TypeError):
            t.Integer(0) <= "NaN"

    def test_gt(self):
        self.assertGreater(t.Integer(1), t.Integer(0))
        self.assertGreater(t.Integer(1), 0)
        with self.assertRaises(TypeError):
            t.Integer(0) > "NaN"

    def test_ge(self):
        self.assertGreaterEqual(t.Integer(1), t.Integer(0))
        self.assertGreaterEqual(t.Integer(1), 1)
        with self.assertRaises(TypeError):
            t.Integer(0) >= "NaN"

    def test_str(self):
        self.assertEqual(str(t.Integer(0)), "0")

    def test_evaluate(self):
        self.assertEqual(t.Integer(0).evaluate({}), 0)


class TestHexNumber(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.HexNumber.parse([(0, Token.Number.Hex, "0xFF")]), t.HexNumber(255)
        )
        self.assertIsNone(t.Integer.parse([(0, Token.Number, "0xFF")]))

    def test_str(self):
        self.assertEqual(str(t.HexNumber(10)), "0xa")


class TestBoolean(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.Boolean.parse([(0, Token.Keyword.Constant, "True")]), t.Boolean(True)
        )
        self.assertEqual(
            t.Boolean.parse([(0, Token.Keyword.Constant, "FALSE")]), t.Boolean(False)
        )
        self.assertIsNone(t.Boolean.parse([(0, Token.Keyword.Constant, "foo")]))
        self.assertIsNone(t.Boolean.parse([(0, Token.String, "True")]))

    def test_eq(self):
        self.assertEqual(t.Boolean(True), t.Boolean(True))
        self.assertEqual(t.Boolean(False), False)
        self.assertNotEqual(t.Boolean(True), t.Boolean(False))
        with self.assertRaises(TypeError):
            t.Boolean(True) == "True"

    def test_bool(self):
        self.assertTrue(t.Boolean(True))

    def test_str(self):
        self.assertEqual(str(t.Boolean(True)), "True")


class TestString(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.String.parse(
                [
                    (0, Token.Punctuation, '"'),
                    (1, Token.String, "foo"),
                    (4, Token.Punctuation, '"'),
                ]
            ),
            t.String("foo"),
        )
        self.assertEqual(
            t.String.parse(
                [
                    (0, Token.Punctuation, '"'),
                    (1, Token.Punctuation, '"'),
                ]
            ),
            t.String(""),
        )
        self.assertIsNone(
            t.String.parse(
                [
                    (0, Token.Punctuation, "("),
                ]
            )
        )

    def test_eq(self):
        self.assertEqual(t.String("a"), t.String("a"))
        self.assertEqual(t.String("foo"), "foo")

    def test_str(self):
        self.assertEqual(str(t.String("foo")), '"foo"')


class TestGuid(TestCase):
    def setUp(self) -> None:
        self.guid = t.Guid(b"\x12>Eg\xe8\x9b\x12\xd3\xa4VBfUD\x00\x00")

    def test_parse(self):
        obj = t.Guid.parse(
            [(0, Token.Name.Entity, "123e4567-e89b-12d3-a456-426655440000")]
        )
        self.assertEqual(obj, t.Guid(b"\x12>Eg\xe8\x9b\x12\xd3\xa4VBfUD\x00\x00"))

    def test_eq(self):
        self.assertEqual(
            self.guid,
            uuid.UUID("123e4567-e89b-12d3-a456-426655440000"),
        )
        with self.assertRaises(TypeError):
            self.guid == "123e4567-e89b-12d3-a456-426655440000"

    def test_str(self):
        self.assertEqual(
            str(self.guid),
            "123e4567-e89b-12d3-a456-426655440000",
        )

    def test_evaluate(self):
        self.assertEqual(
            self.guid.evaluate({}),
            uuid.UUID("123e4567-e89b-12d3-a456-426655440000"),
        )


class TestMacroVal(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.MacroVal.parse(
                [
                    (0, Token.Keyword.Declaration, "$("),
                    (2, Token.Name.Variable, "FOO"),
                    (5, Token.Keyword.Declaration, ")"),
                ]
            ),
            t.MacroVal("FOO"),
        )
        self.assertIsNone(
            t.MacroVal.parse(
                [
                    (0, Token.Keyword.Declaration, "$("),
                    (2, Token.Error, "err"),
                    (5, Token.Keyword.Declaration, ")"),
                ]
            )
        )
        self.assertIsNone(
            t.MacroVal.parse(
                [
                    (0, Token.Keyword.Declaration, "#("),
                    (2, Token.Name.Variable, "FOO"),
                    (5, Token.Keyword.Declaration, ")"),
                ]
            )
        )

    def test_str(self):
        self.assertEqual(str(t.MacroVal("FOO")), "$(FOO)")

    def test_evaluate_plain(self):
        self.assertEqual(t.MacroVal("FOO").evaluate({"FOO": 16}), 16)
        with self.assertRaises(EvaluationError):
            t.MacroVal("FOO").evaluate({})

    def test_evaluate_nested_const(self):
        inner = Mock(spec=t.Constant)
        inner.evaluate.return_value = 3
        self.assertEqual(t.MacroVal("FOO").evaluate({"FOO": inner}), 3)

    def test_evaluate_nested_error(self):
        inner = MagicMock(spec=Expression)
        inner.__str__.return_value = "<Expr>"
        with self.assertRaises(EvaluationError) as cm:
            t.MacroVal("FOO").evaluate({"FOO": inner}, "error")
        self.assertEqual(
            str(cm.exception),
            "Nested expression found in '$(FOO)': <Expr>",
        )

    def test_evaluate_nested_ignore(self):
        inner = Mock(spec=Expression)
        obj = t.MacroVal("FOO")
        self.assertIs(obj.evaluate({"FOO": inner}, "ignore"), obj)

    def test_evaluate_nested_evaluate(self):
        inner = Mock(spec=Expression)
        inner.evaluate.return_value = 3
        self.assertEqual(t.MacroVal("FOO").evaluate({"FOO": inner}, "evaluate"), 3)


class TestMacroDefined(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.MacroDefined.parse(
                [
                    (0, Token.Keyword.Type, "DEFINED"),
                    (7, Token.Punctuation, "("),
                    (8, Token.Name.Variable, "FOO"),
                    (11, Token.Punctuation, ")"),
                ]
            ),
            t.MacroDefined("FOO"),
        )
        self.assertIsNone(
            t.MacroDefined.parse(
                [
                    (0, Token.Keyword.Type, "DEFINED"),
                ]
            )
        )
        self.assertIsNone(
            t.MacroDefined.parse(
                [
                    (0, Token.Keyword.Type, "TEST"),
                    (7, Token.Punctuation, "("),
                    (8, Token.Name.Variable, "FOO"),
                    (11, Token.Punctuation, ")"),
                ]
            )
        )

    def test_str(self):
        self.assertEqual(str(t.MacroDefined("FOO")), "DEFINED(FOO)")

    def test_evaluate(self):
        self.assertTrue(t.MacroDefined("FOO").evaluate({"FOO": None}))
        self.assertFalse(t.MacroDefined("FOO").evaluate({}))


class TestCName(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.CName.parse([(0, Token.Name.Variable, "foo")]), t.CName("foo")
        )

    def test_str(self):
        self.assertEqual(str(t.CName("foo")), "foo")


class TestPcdName(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.PcdName.parse([(0, Token.Name.Entity, "foo.bar")]), t.PcdName("foo.bar")
        )
        self.assertIsNone(t.PcdName.parse([(0, Token.Name.Entity, "foo")]))

    def test_str(self):
        self.assertEqual(str(t.PcdName("foo.bar")), "foo.bar")


class TestArray(TestCase):
    def test_parse(self):
        self.assertEqual(
            t.Array.parse(
                [
                    (0, Token.Punctuation, "{"),
                    (1, Token.Punctuation, "}"),
                ]
            ),
            t.Array("{}"),
        )
        self.assertEqual(
            t.Array.parse(
                [
                    (0, Token.Punctuation, "{"),
                    (1, Token.Whitespace, " "),
                    (2, Token.Punctuation, "}"),
                ]
            ),
            t.Array("{ }"),
        )
        self.assertEqual(
            t.Array.parse(
                [
                    (0, Token.Punctuation, "{"),
                    (1, Token.Keyword.Type, "LABEL"),
                    (6, Token.Punctuation, "("),
                    (7, Token.Name.Variable, "testLabel"),
                    (16, Token.Punctuation, ")"),
                    (17, Token.Punctuation, "}"),
                ]
            ),
            t.Array("{LABEL(testLabel)}"),
        )
        self.assertIsNone(
            t.Array.parse(
                [
                    (0, Token.Punctuation, "'"),
                ]
            )
        )

        with self.assertRaises(ParseError):
            t.Array.parse(
                [
                    (0, Token.Punctuation, "{"),
                ]
            )
        with self.assertRaises(ParseError):
            t.Array.parse(
                [
                    (0, Token.Punctuation, "{"),
                    (1, Token.Punctuation, "{"),
                    (2, Token.Punctuation, "}"),
                ]
            )

    def test_str(self):
        self.assertEqual(str(t.Array("{}")), "{}")
        self.assertEqual(str(t.Array("{ }")), "{ }")
        self.assertEqual(str(t.Array("{LABEL(testLabel)}")), "{LABEL(testLabel)}")
