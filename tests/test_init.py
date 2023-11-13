from unittest import TestCase

import edk2_expression
from edk2_expression.ast import Expression


class Test(TestCase):
    def test_parse(self):
        expr = edk2_expression.parse("$(FOO) > 5")
        self.assertIsInstance(expr, Expression)
        self.assertTrue(expr.evaluate({"FOO": 6}))
        self.assertFalse(expr.evaluate({"FOO": 4}))
