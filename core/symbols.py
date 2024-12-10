import enum
from enum import Enum
from enum import IntEnum
from enum import StrEnum
from typing import Optional

FUNCTION_PREFIX: str = "f:"
TOP_PRECEDENCE: int = 1_000


@enum.verify(enum.UNIQUE)
class Arity(IntEnum):
    NARY = -1
    UNARY = 1
    BINARY = 2


@enum.verify(enum.UNIQUE, enum.CONTINUOUS)
class Associativity(IntEnum):
    LEFT = 0
    RIGHT = 1


@enum.verify(enum.UNIQUE)
class Operator(Enum):
    FUNCTION = (FUNCTION_PREFIX, 7, Arity.NARY, Associativity.LEFT)

    # Relational operators.
    GREATER = (">", 6, Arity.BINARY, Associativity.LEFT)
    GREATER_OR_EQUAL = (">=", 6, Arity.BINARY, Associativity.LEFT)
    LESS = ("<", 6, Arity.BINARY, Associativity.LEFT)
    LESS_OR_EQUAL = ("<=", 6, Arity.BINARY, Associativity.LEFT)

    EQUAL = ("=", 5, Arity.BINARY, Associativity.LEFT)
    EQUAL_2 = ("==", 5, Arity.BINARY, Associativity.LEFT)
    NOT_EQUAL = ("!=", 5, Arity.BINARY, Associativity.LEFT)

    # Logical operators
    NOT = ("NOT", 4, Arity.UNARY, Associativity.RIGHT)
    NOT_2 = ("!", 4, Arity.UNARY, Associativity.RIGHT)
    NOT_3 = ("~", 4, Arity.UNARY, Associativity.RIGHT)
    AND = ("AND", 3, Arity.BINARY, Associativity.LEFT)
    AND_2 = ("&&", 3, Arity.BINARY, Associativity.LEFT)
    XOR = ("XOR", 2, Arity.BINARY, Associativity.LEFT)
    XOR_2 = ("^", 2, Arity.BINARY, Associativity.LEFT)
    OR = ("OR", 1, Arity.BINARY, Associativity.LEFT)
    OR_2 = ("||", 1, Arity.BINARY, Associativity.LEFT)

    @property
    def symbol(self) -> str:
        return self.value[0]

    @property
    def precedence(self) -> int:
        return self.value[1]

    @property
    def arity(self) -> Arity:
        return self.value[2]

    @property
    def associativity(self) -> Associativity:
        return self.value[3]

    @staticmethod
    def parse(token: str) -> Optional["Operator"]:
        return Operator._MAP.get(token, None)

    @staticmethod
    def get_precedence(token: str) -> int:
        return (op.precedence if
                (op := Operator.parse(token)) else TOP_PRECEDENCE)

    def __str__(self) -> str:
        return self.symbol


Operator._MAP = {str(t): t for t in Operator}


@enum.verify(enum.UNIQUE)
class Separator(StrEnum):
    COMMA = ","
    DOT = "."
    RANGE = "-"
    SPACE = " "

    OPEN_CURLY_BRACKET = "{"
    CLOSE_CURLY_BRACKET = "}"
    OPEN_BRACKET = "["
    CLOSE_BRACKET = "]"
    OPEN_PARENTHESIS = "("
    CLOSE_PARENTHESIS = ")"


EMPTY: str = ""
MINUS_CHAR: str = "-"
QUOTE_CHARS: set[str] = set("\"'")

DELIMITERS: set[str] = set(Separator) | set(Operator._MAP.keys())
NON_RIGHT_ANDABLE_CHARS: set[str] = DELIMITERS - {Separator.CLOSE_PARENTHESIS}
SEPARATOR_CHARS: set[str] = DELIMITERS - {Separator.RANGE} | QUOTE_CHARS

COMPOUND_OPERATOR_EQUAL_PREFIXES = {
    op.symbol[0] for op in (
        Operator.LESS_OR_EQUAL,
        Operator.GREATER_OR_EQUAL,
        Operator.NOT_EQUAL,
    )
}
COMPOUND_OPERATOR_DOUBLED_CHARS = {
    op.symbol[0] for op in (
        Operator.EQUAL_2,
        Operator.AND_2,
        Operator.OR_2,
    )
}
