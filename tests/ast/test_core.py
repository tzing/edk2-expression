from unittest import TestCase
from unittest.mock import patch

from edk2_expression.ast.core import Expression, NestMethod
from edk2_expression.error import NotSupported


class TestNestMethod(TestCase):
    def test_missing(self):
        self.assertEqual(NestMethod("ignore"), NestMethod.Ignore)
        self.assertEqual(NestMethod("ERROR"), NestMethod.Error)
        self.assertEqual(NestMethod("Error"), NestMethod.Error)

        with self.assertRaises(ValueError):
            NestMethod("foo")


class TestExpression(TestCase):
    def test_evaluate(self):
        with (
            patch.object(Expression, "__abstractmethods__", set()),
            patch.object(Expression, "__str__", return_value="<EVAL>"),
            self.assertRaises(NotSupported) as cm,
        ):
            Expression().evaluate({})
        self.assertEqual(
            str(cm.exception), "Evaluation not supported for Expression: <EVAL>"
        )
