#!/usr/bin/env python3

from collections import deque
import enum
from enum import Enum
from enum import IntEnum
from enum import StrEnum
from typing import Any
from typing import Iterable
from typing import Optional
from typing import Union

from core.lib import as_json

FUNCTION_PREFIX: str = "f:"
TOP_PRECEDENCE: int = 1_000


class Token:
    word: str
    operator: Optional["Operator"] = None
    precedence: int = TOP_PRECEDENCE
    arity: int = 0
    is_function: bool = False
    is_operator: bool = False
    is_phrase: bool = False

    def __init__(self, word: str, is_phrase: bool = False) -> None:
        self.word = word
        self.is_phrase = is_phrase
        if self.is_phrase:
            return
        self.is_function = Token.isit_function(word)
        self.operator = (Operator.FUNCTION
                         if self.is_function else Operator.parse(word))
        self.is_operator = self.operator is not None
        if self.is_operator:
            self.precedence = self.operator.precedence
            self.arity = int(self.operator.arity)

    @property
    def is_zero_arg_function(self) -> bool:
        return self.is_function and self.arity == 0

    @property
    def isalnum(self) -> bool:
        return self.word.isalnum()

    @property
    def is_delimiter(self) -> bool:
        return self.word in DELIMITERS

    @property
    def is_open_parenthesis(self) -> bool:
        return self.word == Separator.OPEN_PARENTHESIS

    @property
    def is_close_parenthesis(self) -> bool:
        return self.word == Separator.CLOSE_PARENTHESIS

    @property
    def is_open_bracket(self) -> bool:
        return self.word == Separator.OPEN_BRACKET

    @property
    def is_close_bracket(self) -> bool:
        return self.word == Separator.CLOSE_BRACKET

    @property
    def is_right_associative(self) -> bool:
        return (self.is_operator and
                self.operator.associativity is Associativity.RIGHT)

    @property
    def is_right_andable(self) -> bool:
        return self.word in NON_RIGHT_ANDABLE_CHARS

    @property
    def is_unary_operator(self) -> bool:
        return self.is_operator and self.operator.arity is Arity.UNARY

    def is_compound_operator_with(self, char: str) -> bool:
        return (char == Operator.EQUAL.symbol and
                self.word in COMPOUND_OPERATOR_EQUAL_PREFIXES) or (
                    char == self.word and
                    self.word in COMPOUND_OPERATOR_DOUBLED_CHARS)

    @staticmethod
    def isit_function(token: str) -> bool:
        return token.startswith(FUNCTION_PREFIX)

    def __str__(self) -> str:
        return self.word

    def __eq__(self, other):
        if not isinstance(other, (Token, str, StrEnum)):
            return NotImplemented()
        return self.word == other if isinstance(other, str) else str(other)

    def __ne__(self, other):
        if not isinstance(other, (Token, str, StrEnum)):
            return NotImplemented()
        return self.word != other if isinstance(other, str) else str(other)


class Predicate:

    root: "Token"
    operands: list[Union["Token", "Predicate"]]

    def __init__(self, root: "Token"):
        self.root = root
        self.operands = []

    def add_operand(self, stack: deque["Token"]) -> None:
        operand = Predicate.build(stack)
        if operand:
            self.operands.append(operand)

    def reverse_operands(self) -> None:
        if len(self.operands) > 1:
            self.operands.reverse()

    @staticmethod
    def build(
        stack: deque[Union["Token", "Selector"]]
    ) -> Optional[Union["Token", "Predicate", "Selector"]]:
        if not stack:
            return None
        top = stack.pop()
        if isinstance(top, Selector) or not top.is_operator:
            return top

        p = Predicate(top)
        if top.arity > 0:
            for i in range(top.arity):
                p.add_operand(stack)
        p.reverse_operands()
        return p

    @property
    def as_dict(self) -> dict[str, Any]:
        return {
            self.root.word: [
                t if isinstance(t, Token) else t.as_dict for t in self.operands
            ]
        }

    def __str__(self) -> str:
        return as_json(self.as_dict)


class Range:
    range_: tuple[int, int]

    def __init__(self, token: "Token"):
        if Separator.RANGE in (word :=
                               token.word) and not word.startswith(MINUS_CHAR):
            start, end = (int(s) for s in word.split(Separator.RANGE))
            self.range_ = (start, end)
        else:
            self.range_ = (int(token.word),) * 2

    @property
    def as_dict(self) -> dict[str, Any]:
        return dict(
            start=self.range_[0],
            end=self.range_[1],
        )

    def __str__(self) -> str:
        return str(self.range_)


class Function:
    ...


class Argument:
    ...


class Step:
    ranges: Optional[list["Range"]] = None
    predicate: Optional["Predicate"] = None
    node: "Token"

    def __init__(self, node: "Token") -> None:
        self.node = node

    def add_range(self, tokens: list["Token"], start: int, end: int) -> int:
        if self.ranges:
            raise AssertionError(
                f"A Predicate is already defined for step '{self.node}'.")

        if self.ranges is None:
            self.ranges = []

        i = start
        while i < end:
            token = tokens[i]
            i += 1
            if token == Separator.CLOSE_BRACKET:
                break
            self.ranges.append(Range(token))

        return i

    def add_predicate(
        self,
        tokens: list["Token"],
        start: int,
        end: int,
    ) -> int:
        if self.ranges:
            raise AssertionError(
                f"A range is already defined for step '{self.node}'.")

        def print_list(key, ls):
            print(
                as_json({
                    key: [
                        t.word if isinstance(t, Token) else t.as_dict
                        for t in ls
                    ]
                }))

        count: int = 0

        def print_debug():
            nonlocal count
            count += 1
            print(f"### {count} {'#' * 20}")
            print_list("buffer", buffer)
            print_list("operators", operators)

        # Begins executing the Shunting Yard algorithm (for the most part).
        buffer: deque[Token | Selector] = deque()
        operators: deque[Token] = deque()
        i = start

        while i < end:
            token = tokens[i]

            if (token.isalnum and (i + 1) < end and
                    tokens[i + 1] == Separator.DOT):
                selector, i = parse_selector(tokens, i, end)
                buffer.append(selector)
                continue
            else:
                i += 1

            if token == Separator.CLOSE_CURLY_BRACKET:  # Ends the predicate.
                break
            if token.is_function:  # Starts function declaration.
                operators.append(token)
            elif token.is_operator:
                while (operators and (top := operators[-1]) and
                       top.is_operator and not top.is_open_parenthesis and
                       ((token.is_right_associative and
                         token.precedence < top.precedence) or
                        (not token.is_right_associative and
                         token.precedence <= top.precedence))):
                    buffer.append(operators.pop())
                operators.append(token)
            elif token == Separator.COMMA:  # Function argument operator.
                while operators and not operators[-1].is_open_parenthesis:
                    buffer.append(operators.pop())
                if not operators or not operators[-1].is_open_parenthesis:
                    raise ValueError(
                        "Mismatched parentheses or misplaced comma.")
            elif token.is_open_parenthesis:
                operators.append(token)
            elif token.is_close_parenthesis:
                while operators:
                    if operators[-1].is_open_parenthesis:
                        break
                    buffer.append(operators.pop())
                else:
                    raise ValueError("Mismatched parentheses.")
                top = operators.pop()
                if not top.is_open_parenthesis:
                    raise ValueError(
                        f"Expected open parenthesis but got {top} instead.")
                if operators and operators[-1].is_function:
                    buffer.append(operators.pop())
            else:
                buffer.append(token)

        # Flushes remaining operators into buffer.
        while operators:
            top = operators.pop()
            if top.is_open_parenthesis or top.is_close_parenthesis:
                raise ValueError("Mismatched parentheses.")
            buffer.append(top)
        # Ends executing the Shunting Yard algorithm.

        # Builds expression's abstract syntax tree.
        # print_debug()
        predicate = Predicate.build(buffer)
        if isinstance(predicate, Token):
            predicate = Predicate(predicate)
        self.predicate = predicate

        return i

    @property
    def as_dict(self) -> dict[str, Any]:
        return {
            "node":
                self.node,
            **({
                "ranges": [r.as_dict for r in self.ranges]
            } if self.ranges else {}),
            **({
                "predicate": self.predicate.as_dict
            } if self.predicate else {}),
        }

    def __str__(self) -> str:
        return f"step{{{self.node}}}"


class Selector:
    steps: list["Step"]

    def __init__(self) -> None:
        self.steps = []

    def add_step(self, step: "Step") -> None:
        self.steps.append(step)

    @property
    def as_dict(self) -> dict[str, Any]:
        return dict(selector=[s.as_dict for s in self.steps])

    def __str__(self) -> str:
        return f"selector: {[str(s) for s in self.steps]}"


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


def str_ls(ls: list[Any]) -> list[str]:
    return [str(t) for t in ls]


def print_ls(header: str, ls: list[Any]) -> None:
    print(f"{header}: {str_ls(ls)}")


def conjoin(trimmed_tokens: Iterable["Token"]) -> deque["Token"]:
    token_ls: deque[Token] = deque()
    token: Token
    previous: Token
    nesting: deque[Token] = deque([Token(EMPTY)])
    nest: Optional[Token]

    def open_nesting():
        nesting.append(previous if (
            token.is_open_parenthesis and previous.is_function) else token)

    def close_nesting():
        if (token.is_close_parenthesis and not nest.is_function and
                not nest.is_open_parenthesis) or (token.is_close_bracket and
                                                  not nest.is_open_bracket):
            raise ValueError(f"Mismatched nesting {nest} and {token}.")
        if nest.is_function:
            increment_function_arity()
        nesting.pop()

    def increment_function_arity():
        if previous.is_open_parenthesis:
            nest.arity = 0
        elif nest.arity != 0:
            nest.arity = max(nest.arity, 0) + 1

    def is_previous_right_andable() -> bool:
        return (not nest.is_open_bracket and previous and
                not previous.is_right_andable and
                (not previous.is_function or previous.arity == 0))

    for token in trimmed_tokens:
        previous = token_ls[-1] if token_ls else None
        if token.is_open_parenthesis or token.is_open_bracket:
            open_nesting()
        nest = nesting[-1]

        if token == Separator.COMMA:
            if nest.is_function:
                token_ls.append(token)
                increment_function_arity()
            continue
        elif (not token.is_delimiter or token.is_open_parenthesis or
              token.is_unary_operator):
            if is_previous_right_andable():
                # print(f"--> AND {token}")
                token_ls.append(Token(Operator.AND.symbol))
            token_ls.append(token)
        else:
            token_ls.append(token)

        if token.is_close_parenthesis or token.is_close_bracket:
            close_nesting()

    return token_ls


def tokenize(selector: str) -> list["Token"]:
    token_ls: deque[Token] = deque()
    curr_token: deque[str] = deque()
    start_phrase: Optional[str] = None
    quote_count: int = 0  # Used to detect quote mismatches.

    def flush_token(is_phrase: bool = False) -> None:
        if curr_token:
            token_ls.append(Token(EMPTY.join(curr_token), is_phrase))
            curr_token.clear()

    for char in selector:
        if start_phrase and char != start_phrase:  # Builds quoted phrase.
            curr_token.append(char)
        elif char in QUOTE_CHARS:
            if char == start_phrase:  # Closes current quoted phrase.
                flush_token(is_phrase=True)
                quote_count -= 1
                start_phrase = None
            else:  # Opens new quoted phrase.
                quote_count += 1
                start_phrase = char
        elif char.isspace():
            flush_token()
            if token_ls and token_ls[-1].is_function:
                token_ls[-1].arity = 0  # Handles zero-argument functions.
        elif char in SEPARATOR_CHARS:
            flush_token()
            if (previous :=
                (token_ls and token_ls[-1] or
                 None)) and previous.is_compound_operator_with(char):
                # Combines compound operators (e.g. "&&", "<=", "!=")
                token_ls[-1] = Token(previous.word + char)
            else:
                token_ls.append(Token(char))
        else:
            curr_token.append(char)

    flush_token()

    if quote_count != 0:
        raise ValueError(
            f"Mismatched parentheses: {quote_count} are not closed.")

    # print_ls("Before Norm", token_ls)
    # print_ls("After Norm", token_ls)
    return list(conjoin(token_ls))


def parse(query: str) -> "Selector":
    tokens = tokenize(query)
    return parse_selector(
        tokens,
        0,
        len(tokens),
    )[0]


def parse_selector(
    tokens: list["Token"],
    start: int,
    end: int,
) -> tuple["Selector", int]:
    selector = Selector()
    step = None
    i = start
    while i < end:
        token = tokens[i]
        i += 1
        # TODO(alonso): handle nodes declared as phrases.

        if token == Separator.DOT:
            continue
        elif token == Separator.OPEN_CURLY_BRACKET:
            i = step.add_predicate(tokens, i, end)
        elif token == Separator.OPEN_BRACKET:
            i = step.add_range(tokens, i, end)
        elif not token.isalnum:
            i -= 1
            break
        else:
            step = Step(token)
            selector.add_step(step)

    return selector, i
