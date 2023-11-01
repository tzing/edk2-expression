"""A demo script to parse DSC file and evaluate !if expression.
"""
import argparse
import enum
import logging
import re

import edk2_expression
import edk2_expression.error

logger = logging.getLogger("dsc-parser")


class Format(str, enum.Enum):
    Valid = "\033[1;32m+\033[0;32m "
    Invalid = "\033[1;31m-\033[0;31m "
    NotRelated = "\033[2;37m:\033[0m "
    Reset = "\033[0m"

    def __str__(self) -> str:
        return self.value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="input file")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )

    with open(args.file) as fd:
        file_content = fd.read()

    context = {}
    criteria = []
    for line in file_content.splitlines():
        # exclude comment and whitespaces
        clean_line = line.rsplit("#", 1)[0]
        clean_line = clean_line.strip()

        if not clean_line:
            continue

        # parse
        if m := re.fullmatch(r"DEFINE +(\w+) *= *(.+)", clean_line):
            name, raw_expr = m.groups()
            expr = edk2_expression.parse(raw_expr)
            logger.debug(f"Parse {name} = {expr!r}")

            if not criteria or criteria[-1]:
                context[name] = expr
                prefix = Format.Valid
            else:
                prefix = Format.Invalid
            print(f"{prefix}{line}{Format.Reset}")

        elif m := re.fullmatch(r"!(?:else)?if (.+)", clean_line):
            raw_expr = m.group(1)
            expr = edk2_expression.parse(raw_expr)

            if any(criteria):
                logger.debug(f"Stop evaluate !if {expr!r}")
                result = False
            else:
                result = bool(expr.evaluate(context, "evaluate"))
                logger.debug(f"Evaluate !if {expr!r} = {result}")

            criteria.append(result)
            prefix = Format.Valid if result else Format.Invalid
            print(f"{prefix}{line}{Format.Reset}")

        elif re.fullmatch(r"!else", clean_line):
            result = not any(criteria)
            criteria.append(result)

            prefix = Format.Valid if result else Format.Invalid
            print(f"{prefix}{line}{Format.Reset}")

        elif re.fullmatch(r"!endif", clean_line):
            print(f"{Format.Valid}{line}{Format.Reset}")
            criteria = []

        else:
            print(f"{Format.NotRelated}{line}{Format.Reset}")


if __name__ == "__main__":
    exit(main())
