from unittest import TestCase
from unittest.mock import patch

from edk2_expression.ast.core import Expression
from edk2_expression.error import NotSupported


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
