from __future__ import annotations

from pygments.lexer import RegexLexer, bygroups, include, words
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Whitespace,
)


class Edk2ExpressionLexer(RegexLexer):
    name = "EDK II Expression Syntax"
    aliases = []
    filenames = []
    mimetypes = []

    CCHAR = r'(?:[\x21\x23-\x26\x28-\x5b\x5d-\x7e\x20\x09]|\\[ntfrb0\\"\'])'
    CName = r"[a-zA-Z_][a-zA-Z0-9_]*"

    tokens = {
        "root": [
            include("whitespace"),
            (r"\n", Whitespace, "#pop"),
            (r"#.*", Comment.Single),
            (words(("{")), Punctuation, "array"),
            (words(("(")), Punctuation, "#push"),
            (words((")")), Punctuation, "#pop"),
            (
                words(
                    (
                        # fmt: off
                        "EQ", "NE", "LT", "GT", "LE", "GE", "AND", "and", "XOR"
                        "xor", "OR", "or", "NOT", "not",
                        # fmt: on
                    ),
                    prefix=r"\b",
                    suffix=r"\b",
                ),
                Operator,
            ),
            (
                words(
                    (
                        # fmt: off
                        "+", "-", "*", "/", "%", "<<", ">>", "==", "!=", "<", ">",
                        "<=", ">=", "|", "^", "&", "&&", "||", "!", "~", "?", ":"
                        # fmt: on
                    )
                ),
                Operator,
            ),
            (rf"\b{CName}\.{CName}\b", Name.Entity),  # <PcdName>
            (  # <RformatGuid>
                r"\b[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}\b",
                Name.Entity,
            ),
            include("constants"),
            (  # <MACROVAL>
                r"(\$\()([A-Z][A-Z0-9_]*)(\))",
                bygroups(Keyword.Declaration, Name.Variable, Keyword.Declaration),
            ),
            # (  # <MacroDefined>
            #     rf"\b(DEFINED)(\()({CName})(\))",
            #     bygroups(Keyword.Type, Punctuation, Name.Variable, Punctuation),
            # ),
            (rf"\b{CName}\b", Name.Variable),  # <CName>
        ],
        "array": [
            (words(("{")), Punctuation, "#push"),
            (words(("}", ")")), Punctuation, "#pop"),
            include("whitespace"),
            (words((",")), Punctuation),
            (  # <UintMac>
                r"\b(UINT(?:8|16|32|64))(\()(\d+)(\))",
                bygroups(Keyword.Type, Punctuation, Number.Integer, Punctuation),
            ),
            (  # <Label> & <Offset>
                rf"\b(LABEL|OFFSET_OF)(\()({CName})(\))",
                bygroups(Keyword.Type, Punctuation, Name.Variable, Punctuation),
            ),
            (  # <DevicePath>
                r'\b(DEVICE_PATH)(\(")([.]+?)("\))',
                bygroups(Keyword.Type, Punctuation, String, Punctuation),
            ),
            (  # <GuidStr> that uses <RformatGuid>
                r'\b(GUID)(\(")([a-fA-F0-9-]{36})("\))',
                bygroups(Keyword.Type, Punctuation, Name.Entity, Punctuation),
            ),
            (  # <GuidStr> that uses <CformatGuid>
                r"\b(GUID)(\()(\{)",
                bygroups(Keyword.Type, Punctuation, Punctuation),
                ("#push", "#push"),
            ),
            (  # <GuidStr> that uses <CName>
                rf"\b(GUID)(\()({CName})(\))",
                bygroups(Keyword.Type, Punctuation, Name.Variable, Punctuation),
            ),
            include("constants"),
        ],
        "constants": [
            (  # QuotedString
                rf'(L?")({CCHAR}*)(")',
                bygroups(Punctuation, String, Punctuation),
            ),
            (  # <SglQuotedString>
                rf"(L?')({CCHAR}*)(')",
                bygroups(Punctuation, String, Punctuation),
            ),
            (  # <TrueFalse>
                words(
                    ("TRUE", "True", "true", "FALSE", "False", "false"),
                    prefix=r"\b",
                    suffix=r"\b",
                ),
                Keyword.Constant,
            ),
            (r"\b0[xX][a-fA-F0-9]{2,8}\b", Number.Hex),  # <HexNumber>
            (r"\b\d+\b", Number.Integer),  # <Integer>
        ],
        "whitespace": [
            (r"[\x20\x09]+", Whitespace),
        ],
    }
