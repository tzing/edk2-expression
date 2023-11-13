# EDK II Expression Parser

This library provides a simple parser that can be used to evaluate the value of an expression which aligns [EDK II Meta-Data Expression Syntax Specification] revision 1.3.

[EDK II Meta-Data Expression Syntax Specification]: https://tianocore-docs.github.io/edk2-MetaDataExpressionSyntaxSpecification/release-1.30/


## Installation

This library requires Python 3.10 or later, and [Pygments].

[Pygments]: https://pygments.org/

This library is intended to be used as part of another project, and I will not make it available on PyPI.

You can use the `pip` to install it from source:

```bash
pip install git+https://github.com/tzing/edk2-expression.git
```

or simply copy the source code into your project.


## Usage

First, parse the expression text into abstract syntax tree (AST):

```python
>>> import edk2_expression
>>> expr = edk2_expression.parse("$(FOO) +2")
```

Then, evaluate the expression with a dictionary of variables:

```python
>>> print(expr.evaluate({"FOO": 1}))
3
```

For nested expression, one can set `nest` to `evaluate` to evaluate it:

```python
>>> expr1 = edk2_expression.parse("True ? $(BAR) + 3 : 0")
>>> print(expr1.evaluate({"FOO": 1, "BAR": expr}, nest="evaluate"))
6
```

See [example/](./example/) directory for more examples.


## Supported Syntax

### Data Fields

| EDK II Data Field Name | Supported      | Evaluate                     |
| ---------------------- | -------------- | ---------------------------- |
| `<Array>`              | No[^array]     | No                           |
| `<CName>`              | Yes            | No                           |
| `<Function>`           | No[^func]      | No                           |
| `<GuidValue>`          | Partial[^guid] | Yes; Returns `uuid.UUID`     |
| `<MacroVal>`           | Yes            | Yes; Returns the macro value |
| `<Number>`             | Yes            | Yes; Returns the number      |
| `<PcdName>`            | Yes            | No                           |
| `<StringLiteral>`      | Yes            | Yes; Returns the string      |
| `<TrueFalse>`          | Yes            | Yes; Returns `True`/`False`  |

[^array]: This library currently reads the array as a string, and does not support any operations or evaluation.

[^func]: Per addressed by EDK II:

    > Functions should only be used if all tools that process the entry in the meta-data file comprehend the function syntax.

    Since this library is designed for general purpose, it does not parse functions.

[^guid]: GUID in `<CformatGuid>` format is currently not parsed.


### Operators

| EDK II Expression Name    | Operator                                     | Supported | Precedence[^prec] |
| ------------------------- | -------------------------------------------- | --------- | ----------------: |
| `<UnaryExpression>`       | `!`, `NOT`, `not`, `~`                       | Yes       |                 2 |
| `<MultiplicativeExpress>` | `*`, `/`, `%`                                | Yes       |                 3 |
| `<AdditiveExpress>`       | `+`, `-`                                     | Yes       |                 4 |
| `<ShiftExpression>`       | `<<`, `>>`                                   | Yes       |                 5 |
| `<RelationalExpress>`     | `<`, `LT`, `<=`, `LE`, `>`, `GT`, `>=`, `GE` | Yes       |                 6 |
| `<EqualityExpression>`    | `==`, `EQ`, `!=`, `NE`                       | Yes       |                 7 |
| `<BitwiseAndExpression>`  | `&`                                          | Yes       |                 8 |
| `<BitwiseXorExpress>`     | `^`                                          | Yes       |                 9 |
| `<BitwiseOrExpress>`      | `\|`                                         | Yes       |                10 |
| `<LogicalAndExpress>`     | `&&`, `AND`, `and`                           | Yes       |                11 |
| `<LogicalXorExpress>`     | `XOR`, `xor`                                 | Yes       |   12[^shift-prec] |
| `<LogicalOrExpress>`      | `\|\|`, `OR`, `or`                           | Yes       |   13[^shift-prec] |
| `<CondExpress>`           | `?:` (ternary conditional)                   | Yes       |   15[^shift-prec] |

[^prec]: The lower the number, the higher the precedence. It is almost the same order as the precedence in C language.

[^shift-prec]: Logical XOR operator does not exist in C language so the precedence below it is shifted.


## Extras

### Pygments lexer

This parser utilizes [Pygments] for expression text tokenization and, as a result, it comes packaged with a lexer.

If you are using Pygments, you can use the lexer directly:

```python
import edk2_expression.lex

lexer = edk2_expression.lex.Edk2ExpressionLexer()
```

### `DEFINED` function

A function that returns `True` if the macro is defined, otherwise `False`.

The syntax is defined as follows in EBNF:

```ebnf
<MacroDefined> ::= "DEFINED(" <CName> ")"
<CName>        ::= (a-zA-Z_) [(a-zA-Z0-9_)]*
```

This function is not defined in EDK II specification therefore it is disabled by default.
To enable it, manually uncomment the lines for `<MacroDefined>` in [lexer](./edk2_expression/lex.py).

## Changelog

See [Changelog.md](./Changelog.md).

## License

This project is licensed under the terms of the MIT license.
