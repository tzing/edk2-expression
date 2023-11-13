from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import edk2_expression.ast.operator as t
from edk2_expression.ast.core import Expression
from edk2_expression.error import ParseError


class TestPushOperator(TestCase):
    def test_direct(self):
        operator_stack = []
        output_stack = []
        t.push_operator("NOT", operator_stack, output_stack)
        self.assertEqual(operator_stack, ["!"])
        self.assertEqual(output_stack, [])

    def test_higher(self):
        operator_stack = ["-"]
        output_stack = [Mock(spec=Expression), Mock(spec=Expression)]
        t.push_operator("*", operator_stack, output_stack)
        self.assertEqual(operator_stack, ["-", "*"])
        self.assertEqual(len(output_stack), 2)

    def test_lower(self):
        operator_stack = ["*"]
        output_stack = [Mock(spec=Expression), Mock(spec=Expression)]
        t.push_operator("-", operator_stack, output_stack)
        self.assertEqual(operator_stack, ["-"])
        self.assertEqual(len(output_stack), 1)

    def test_error(self):
        with self.assertRaises(ParseError):
            t.push_operator("Unknown", [], [])


class TestPopOperator(TestCase):
    def test_ignore(self):
        self.assertEqual(t.pop_operator(["("], []), "(")

    def test_unary(self):
        sub = MagicMock(spec=Expression)
        operator_stack = ["!"]
        output_stack = [sub]
        self.assertEqual(t.pop_operator(operator_stack, output_stack), "!")
        self.assertEqual(operator_stack, [])
        self.assertEqual(output_stack, [t.LogicalNot(sub)])

    def test_binary(self):
        left = MagicMock(spec=Expression)
        right = MagicMock(spec=Expression)
        operator_stack = ["!", "-"]
        output_stack = [left, right]
        self.assertEqual(t.pop_operator(operator_stack, output_stack), "-")
        self.assertEqual(operator_stack, ["!"])
        self.assertEqual(output_stack, [t.Subtraction(left, right)])

    def test_unknown_operator(self):
        with self.assertRaises(RuntimeError):
            t.pop_operator(["Unknown"], [])

    def test_missing_operand(self):
        with self.assertRaises(ParseError) as cm:
            t.pop_operator(["!"], [])
        self.assertEqual(str(cm.exception), "Missing operand(s) for operator '!'")


class TestOperator(TestCase):
    def test_parse(self):
        with self.assertRaises(RuntimeError):
            t.Operator.parse([])


class TestUnaryOp(TestCase):
    def setUp(self):
        self.expr = MagicMock(spec=Expression)
        self.expr.evaluate.return_value = 7
        self.expr.__str__.return_value = "foo"

    def test_LogicalNot(self):
        expr = t.LogicalNot(self.expr)
        self.assertFalse(expr.evaluate({}))
        self.assertEqual(str(expr), "!foo")

    def test_BitwiseNot(self):
        expr = t.BitwiseNot(self.expr)
        self.assertEqual(expr.evaluate({}), -8)  # +0b0111 -> -0b1000
        self.assertEqual(str(expr), "~foo")


class TestBinaryOp(TestCase):
    def setUp(self):
        self.left = MagicMock(spec=Expression)
        self.left.__str__.return_value = "foo"

        self.right = MagicMock(spec=Expression)
        self.right.__str__.return_value = "bar"

    @patch.object(t.BinaryOp, "__abstractmethods__", set())
    def test_evaluate_nested(self):
        expr = t.BinaryOp(self.left, self.right)

        self.left.evaluate.return_value = Mock(spec=Expression)
        self.right.evaluate.return_value = 2

        self.assertIs(expr.evaluate({}, nest="ignore"), expr)

        with self.assertRaises(RuntimeError):
            expr.evaluate({}, nest="evaluate")

    def test_Multiplication(self):
        expr = t.Multiplication(self.left, self.right)

        self.left.evaluate.return_value = 2
        self.right.evaluate.return_value = 3
        self.assertEqual(expr.evaluate({}), 6)

        self.assertEqual(str(expr), "(foo * bar)")

    def test_Division(self):
        expr = t.Division(self.left, self.right)

        self.left.evaluate.return_value = 6
        self.right.evaluate.return_value = 3
        self.assertEqual(expr.evaluate({}), 2)

        self.assertEqual(str(expr), "(foo / bar)")

    def test_Modulo(self):
        expr = t.Modulo(self.left, self.right)

        self.left.evaluate.return_value = 7
        self.right.evaluate.return_value = 3
        self.assertEqual(expr.evaluate({}), 1)

        self.assertEqual(str(expr), "(foo % bar)")

    def test_Addition(self):
        expr = t.Addition(self.left, self.right)

        self.left.evaluate.return_value = 1
        self.right.evaluate.return_value = 2
        self.assertEqual(expr.evaluate({}), 3)

        self.assertEqual(str(expr), "(foo + bar)")

    def test_Subtraction(self):
        expr = t.Subtraction(self.left, self.right)

        self.left.evaluate.return_value = 1
        self.right.evaluate.return_value = 2
        self.assertEqual(expr.evaluate({}), -1)

        self.assertEqual(str(expr), "(foo - bar)")

    def test_BitwiseLeftShift(self):
        expr = t.BitwiseLeftShift(self.left, self.right)

        self.left.evaluate.return_value = 1
        self.right.evaluate.return_value = 2
        self.assertEqual(expr.evaluate({}), 4)

        self.assertEqual(str(expr), "(foo << bar)")

    def test_BitwiseRightShift(self):
        expr = t.BitwiseRightShift(self.left, self.right)

        self.left.evaluate.return_value = 4
        self.right.evaluate.return_value = 2
        self.assertEqual(expr.evaluate({}), 1)

        self.assertEqual(str(expr), "(foo >> bar)")

    def test_LessThan(self):
        expr = t.LessThan(self.left, self.right)

        self.left.evaluate.return_value = 1
        self.right.evaluate.return_value = 2
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = 1
        self.assertFalse(expr.evaluate({}))

        self.assertEqual(str(expr), "foo < bar")

    def test_LessEqual(self):
        expr = t.LessEqual(self.left, self.right)

        self.left.evaluate.return_value = 1
        self.right.evaluate.return_value = 2
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = 1
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = 0
        self.assertFalse(expr.evaluate({}))

        self.assertEqual(str(expr), "foo <= bar")

    def test_GreaterThan(self):
        expr = t.GreaterThan(self.left, self.right)

        self.left.evaluate.return_value = 2
        self.right.evaluate.return_value = 1
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = 2
        self.assertFalse(expr.evaluate({}))

        self.assertEqual(str(expr), "foo > bar")

    def test_GreaterEqual(self):
        expr = t.GreaterEqual(self.left, self.right)

        self.left.evaluate.return_value = 2
        self.right.evaluate.return_value = 1
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = 2
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = 3
        self.assertFalse(expr.evaluate({}))

        self.assertEqual(str(expr), "foo >= bar")

    def test_Equality(self):
        expr = t.Equal(self.left, self.right)

        self.left.evaluate.return_value = 1
        self.right.evaluate.return_value = 1
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = 2
        self.assertFalse(expr.evaluate({}))

        self.assertEqual(str(expr), "foo == bar")

    def test_NotEquality(self):
        expr = t.NotEqual(self.left, self.right)

        self.left.evaluate.return_value = 1
        self.right.evaluate.return_value = 2
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = 1
        self.assertFalse(expr.evaluate({}))

        self.assertEqual(str(expr), "foo != bar")

    def test_BitwiseAnd(self):
        expr = t.BitwiseAnd(self.left, self.right)

        self.left.evaluate.return_value = 0b101
        self.right.evaluate.return_value = 0b011
        self.assertEqual(expr.evaluate({}), 0b001)

        self.assertEqual(str(expr), "foo & bar")

    def test_BitwiseXor(self):
        expr = t.BitwiseXor(self.left, self.right)

        self.left.evaluate.return_value = 0b101
        self.right.evaluate.return_value = 0b011
        self.assertEqual(expr.evaluate({}), 0b110)

        self.assertEqual(str(expr), "foo ^ bar")

    def test_BitwiseOr(self):
        expr = t.BitwiseOr(self.left, self.right)

        self.left.evaluate.return_value = 0b101
        self.right.evaluate.return_value = 0b011
        self.assertEqual(expr.evaluate({}), 0b111)

        self.assertEqual(str(expr), "(foo | bar)")

    def test_LogicalXor(self):
        expr = t.LogicalXor(self.left, self.right)

        self.left.evaluate.return_value = True
        self.right.evaluate.return_value = False
        self.assertTrue(expr.evaluate({}))

        self.right.evaluate.return_value = True
        self.assertFalse(expr.evaluate({}))

        self.assertEqual(str(expr), "foo xor bar")


class TestLogicalAnd(TestCase):
    def setUp(self):
        self.left = MagicMock(spec=Expression)
        self.right = MagicMock(spec=Expression)
        self.expr = t.LogicalAnd(self.left, self.right)

    def test_str(self):
        self.left.__str__.return_value = "foo"
        self.right.__str__.return_value = "bar"
        self.assertEqual(str(self.expr), "foo && bar")

    def test_evaluate_1(self):
        # basic
        self.left.evaluate.return_value = True
        self.right.evaluate.side_effect = [True, False]
        self.assertIs(self.expr.evaluate({}), True)
        self.assertIs(self.expr.evaluate({}), False)

    def test_evaluate_2(self):
        # make sure right hand side is not evaluated when left hand side is False
        self.left.evaluate.return_value = False
        self.right.evaluate.side_effect = RuntimeError
        self.assertIs(self.expr.evaluate({}), False)

    def test_evaluate_3(self):
        # nested
        self.right.evaluate.return_value = Mock(spec=Expression)
        self.assertIs(self.expr.evaluate({}, nest="ignore"), self.expr)

    def test_evaluate_4(self):
        # early escape on nested expression
        self.left.evaluate.return_value = Mock(spec=Expression)
        self.right.evaluate.side_effect = RuntimeError
        self.assertIs(self.expr.evaluate({}, nest="ignore"), self.expr)

    def test_evaluate_5(self):
        # nested expression error
        self.left.evaluate.return_value = Mock(spec=Expression)
        with self.assertRaises(RuntimeError):
            self.expr.evaluate({}, nest="evaluate")


class TestLogicalOr(TestCase):
    def setUp(self):
        self.left = MagicMock(spec=Expression)
        self.right = MagicMock(spec=Expression)
        self.expr = t.LogicalOr(self.left, self.right)

    def test_str(self):
        self.left.__str__.return_value = "foo"
        self.right.__str__.return_value = "bar"
        self.assertEqual(str(self.expr), "(foo || bar)")

    def test_evaluate_1(self):
        # basic
        self.left.evaluate.side_effect = [False, False, True]
        self.right.evaluate.side_effect = [True, False, True]
        self.assertIs(self.expr.evaluate({}), True)
        self.assertIs(self.expr.evaluate({}), False)
        self.assertIs(self.expr.evaluate({}), True)

    def test_evaluate_2(self):
        # early escape on nested expression
        self.left.evaluate.side_effect = t.LazyEvaluated.Skip
        self.assertIs(self.expr.evaluate({}), self.expr)


class TestTernaryOp(TestCase):
    def test_str(self):
        cond = MagicMock(spec=Expression)
        cond.__str__.return_value = "condition"

        true = MagicMock(spec=Expression)
        true.__str__.return_value = "foo"

        false = MagicMock(spec=Expression)
        false.__str__.return_value = "bar"

        expr = t.TernaryOp(cond, t.TernaryOp.Decision(true, false))
        self.assertEqual(str(expr), "condition ? foo : bar")

    def test_ensure_colon(self):
        invalid_expr = MagicMock(spec=Expression)
        invalid_expr.__str__.return_value = "<invalid>"

        with self.assertRaises(ParseError) as cm:
            t.TernaryOp(Mock(spec=Expression), invalid_expr)
        self.assertEqual(
            str(cm.exception),
            "Right hand side for '?' must be operands separated by ':'. "
            "Got '<invalid>'",
        )

    def test_true(self):
        cond = Mock(spec=Expression)
        cond.evaluate.return_value = True

        true = Mock(spec=Expression)
        true.evaluate.return_value = 1

        false = Mock(spec=Expression)

        expr = t.TernaryOp(cond, t.TernaryOp.Decision(true, false))
        self.assertEqual(expr.evaluate({}), 1)

    def test_false(self):
        cond = Mock(spec=Expression)
        cond.evaluate.return_value = False

        true = Mock(spec=Expression)

        false = Mock(spec=Expression)
        false.evaluate.return_value = 2

        expr = t.TernaryOp(cond, t.TernaryOp.Decision(true, false))
        self.assertEqual(expr.evaluate({}), 2)
