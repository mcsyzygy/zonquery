#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2024 Alonso R.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                                     ║
║  ZonQuery                                                                           ║
║  A library for parsing selectors and building ASTs for JSON data queries.           ║
║                                                                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

*** WORK IN PROGRESS ***

This Python 3.12 library parses string selectors for extracting nodes from JSON
data and builds an Abstract Syntax Tree (AST) to be interpreted for node retrieval. 
The selector syntax is inspired by jQuery, CSS selectors, and AWK.

Notable Features:
- Supports function calls with or without arguments.
- Allows rich expressions with logical and relational operators, 
  adhering to operator precedence and associativity.
- Enables expression grouping using parentheses.
- Handles indexes and ranges for precise node targeting.
- Nested selectors are supported, including embedding within expressions.

Current Status:
- AST parser implementation is nearly complete.
- Interpreter implementation is pending and will be added soon.

Dependencies:
- Zero external dependencies.

Sample Input and Output:
- A couple of examples are listed below for reference.
- More examples are included in the unittest at the end of this file.

This library is designed to be lightweight (~600 lines), and self-contained.

════════════════════════════════════════════════════════════════════════════════
#
# Example 1 of 2: A valid input selector.
#

insurance {
    f:lookup(
        f:verify(
            this.plans.benefits.status {
                this.statusDetails = 'Vingt "Mille Lieues" sous les mers'
                } = 'Active Coverage',
            amount  <=  8_000
            type == MH
            ) 27 ! Visit NOT Percent )
    f:get_current_out_of_pocket("Year to Date", Remaining)
    f:validate_network(0, 3, 9, Rantanplan, 
            statusCode = 789, 
            foo = "Marsupilami & Fantasio",
            timePeriod <= 1234567)
    f:len  f:len2()  f:len3(   ) "f:len4"    (Athos Porthos Aramis)
}
.benefits [
     1
     2-9
     15-20
     33
  ]
.amounts {
  this.coInsurance{ insuranceType = "A" ~!!a && b} != this.plans{ 
    name = "Dental Care" }
}
.deductibles [0, -1]


#
# Example 2 of 2: Another input selector and the resulting AST.
#

### INPUT:

a {
    f:sin(
        f:max(
            this.kk1.jj2.ii3 {
                this.val1 = 'Vingt Mille Lieues sous les mers'
                } = 'jean valjean',
            z  <  3
            ) 3 π )
    f:min(11, 17)
}

.b [
     1
     2-9
     15-20
     33
  ]

### OUTPUT

{
  "selector": [
    {
      "node": "a",
      "predicate": {
        "AND": [
          {
            "f:sin": [
              {
                "AND": [
                  {
                    "AND": [
                      {
                        "f:max": [
                          {
                            "=": [
                              {
                                "selector": [
                                  {"node": "this"},
                                  {"node": "kk1"},
                                  {"node": "jj2"},
                                  {
                                    "node": "ii3",
                                    "predicate": {
                                      "=": [
                                        {
                                          "selector": [
                                            {"node": "this"},
                                            {"node": "val1"} ] },
                                        "Vingt Mille Lieues sous les mers"
                                      ] } } ] },
                              "jean valjean"
                            ] },
                          {"<": ["z", "3"]}
                        ] },
                      "3"
                    ] },
                  "π"
                ] } ] },
          { "f:min": ["11", "17"] }
        ] } },
    {
      "node": "b",
      "ranges": [
        {"start": 1, "end": 1},
        {"start": 2, "end": 9},
        {"start": 15, "end": 20},
        {"start": 33, "end": 33} ] } ] }
"""

from collections import deque
import enum
from enum import Enum
from enum import IntEnum
from enum import StrEnum
import timeit
from typing import Any
from typing import Iterable
from typing import Optional
from typing import Union
import unittest

try:
    # from truth.truth import AssertThat
    import orjson as json
    from rich.console import Console

    console = Console()
    print = console.print
    JSON_OPTIONS = dict(option=json.OPT_INDENT_2)

except ImportError:
    import json

    JSON_OPTIONS = dict(indent=2)


def as_json(data: dict[str, Any]) -> str:
    return json.dumps(data, **JSON_OPTIONS).decode("utf-8")


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
        return (char == EQUAL_CHAR and
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


DELIMITERS: set[str] = {str(s) for s in Separator} | {str(s) for s in Operator}
NON_RIGHT_ANDABLE_CHARS: set[str] = set(DELIMITERS) - {")"}

SEPARATOR_CHARS: set[str] = set(".,=<>!\"'{}[]()")
QUOTE_CHARS: set[str] = set("\"'")
COMPOUND_OPERATOR_EQUAL_PREFIXES = set("<>!")
COMPOUND_OPERATOR_DOUBLED_CHARS = set("=&|")
EMPTY: str = ""
EQUAL_CHAR: str = "="
MINUS_CHAR: str = "-"


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


def main():
    TestSample().run()


if __name__ == "__main__":
    main()


def benchmark(selector: int = 1, reps: int = 10_000):
    data = TestingData(TEST_DATA[selector - 1])
    print(f"─── Selector {selector} ───")
    print(f"⌦{data.selector}⌫")

    def fn():
        parse(data.selector)

    run_time = timeit.timeit(fn, number=reps)
    print(f"Average run time: {(run_time / reps ) * 1_000_000:,.0f} µs")


class TestingData:
    selector: Optional[str] = None
    ast: Optional[dict[str, Any]] = None

    def __init__(self, raw_data: str):
        buffer: list[str] = []
        data: dict[str, str] = {}
        key: str = ""
        line: str

        def flush_buffer():
            nonlocal buffer
            if key:
                data[key] = "\n".join(buffer)
                buffer = []

        for line in raw_data.split("\n"):
            ltrim = line.lstrip()
            if ltrim.startswith("#"):
                flush_buffer()
                key, line = ltrim[1:].split(":", 1)
                key = key.strip()

            if key:
                buffer.append(line)
        flush_buffer()

        for k, v in data.items():
            if k in ("ast",):
                v = json.loads(v)
            if hasattr(self, k):
                setattr(self, k, v)


class TestingJsonTestCase(unittest.TestCase):

    flush_to_disk_on_error: bool = False
    flush_dest: Optional[str] = None

    def assertJsonEqual(self, first, second, msg=None):
        values = []
        for v in (first, second):
            if isinstance(v, str):
                v = json.loads(v)
            elif d := getattr(v, "as_dict", None):
                v = d
            values.append(v)
        expected, actual = values

        if actual == expected:
            return

        # Formats the output to use double quotes.
        actual = as_json(actual)
        formatted_msg = (f"\nExpected :\n{as_json(expected)}"
                         f"\nActual   :\n{actual}")
        msg = f"{msg or ''}{formatted_msg}"
        print(f"ERROR: Test failed: {msg}")

        if self.flush_to_disk_on_error:
            with open(self.flush_dest, "w") as f:
                f.write(actual)

        self.fail(msg)


class TestSample(TestingJsonTestCase):
    maxDiff = None
    FLUSH_TO_DISK_ON_ERROR: bool = False
    FLUSH_DEST: Optional[str] = "/tmp/zonquery-actual-output.json"

    SELECTORS: tuple[Any, ...] = ()
    PRINT_WIDTH: int = 80

    @classmethod
    def setUpClass(cls):
        TestingJsonTestCase.flush_to_disk_on_error = cls.FLUSH_TO_DISK_ON_ERROR
        TestingJsonTestCase.flush_dest = cls.FLUSH_DEST

    def setUp(self):
        print("\nSTART TEST")

    def print_header(self, header: str) -> None:
        prefix = f"{'═' * 3} {header} "
        print(f"\n\n{prefix}{'═' * (self.PRINT_WIDTH - len(prefix))}")

    def run_sample(self, *one_based_indices: int):
        size = len(TEST_DATA)
        for i in one_based_indices:
            self.print_header(f"TESTING SAMPLE {i}/{size}")
            data = TestingData(TEST_DATA[i - 1])
            print(f"─── Selector {i} ───")
            print(f"⌦{data.selector}⌫")
            self.assertJsonEqual(data.ast, parse(data.selector))

    def test_parse_selected(self):
        for i in (1, 2, 3):
            with self.subTest(name=f"Selector {i}"):
                self.run_sample(i)

    def test_parse_one(self):
        self.run_sample(1)

    def test_parse_last(self):
        self.run_sample(len(TEST_DATA))

    def test_parse(self):
        for i in range(1, len(TEST_DATA) + 1):
            with self.subTest(name=f"Selector {i}"):
                self.run_sample(i)

    @unittest.skip("Skip this scratch test.")
    def test_parse_experiment(self):
        count: int = -1
        start = False
        for selector, expected in self.SELECTORS:
            count += 1
            if selector == 1:
                break
            elif selector == 0:
                start = True
                continue
            if start:
                # self.assertEqual(expected, tokenize(selector))
                print(f"{count} - Input: {selector}")
                print(parse(selector))
                break


### Test Data
TEST_DATA: list[str] = [
    ### . ###
    r"""
# selector:
insurance {
    f:lookup(
        f:verify(
            this.plans.benefits.status {
                this.statusDetails = 'Vingt "Mille Lieues" sous les mers'
                } = 'Active Coverage',
            amount  <=  8_000
            type == MH
            ) 3 ! π NOT Percent  )
    f:get_current_out_of_pocket(11, 17)
    f:validate_network(0, 7, 9, Rantanplan,
            statusCode = 789,
            foo = "Marsupilami & Fantasio",
            timePeriod <= 1234567)
    f:len  f:len2()  f:len3(   ) "f:len4"    (Athos Porthos Aramis)
}
.benefits [
     1
     2-9
     15-20
     33
  ]
.amounts {
  this.coInsurance{ insuranceType = "A" ~!!a && b} != this.plans{ name = "Dental Care" }
}
.deductibles [0, -1]

# ast:
{"selector": [
    {
      "node": "insurance",
      "predicate": {
        "AND": [
          {
            "AND": [
              {
                "AND": [
                  {
                    "AND": [
                      {
                        "AND": [
                          {
                            "AND": [
                              {
                                "AND": [
                                  {
                                    "f:lookup": [
                                      {
                                        "AND": [
                                          {
                                            "AND": [
                                              {
                                                "AND": [
                                                  {
                                                    "f:verify": [
                                                      {
                                                        "=": [
                                                          {
                                                            "selector": [
                                                              {"node": "this"},
                                                              {"node": "plans"},
                                                              {"node": "benefits"},
                                                              {
                                                                "node": "status",
                                                                "predicate": {
                                                                  "=": [
                                                                    {
                                                                      "selector": [
                                                                        {"node": "this"},
                                                                        {"node": "statusDetails"}
                                                                      ]},
                                                                    "Vingt \"Mille Lieues\" sous les mers"
                                                                  ]}}]},
                                                          "Active Coverage"
                                                        ]},
                                                      {
                                                        "AND": [
                                                          {"<=": ["amount", "8_000"]},
                                                          {"==": ["type", "MH"]}
                                                        ]}]},
                                                  "3"
                                                ]},
                                              {"!": ["π"]}
                                            ]},
                                          {"NOT": ["Percent"]}
                                        ]
                                      }
                                    ]
                                  },
                                  {"f:get_current_out_of_pocket": ["11", "17"]}
                                ]
                              },
                              {
                                "f:validate_network": [
                                  "0",
                                  "7",
                                  "9",
                                  "Rantanplan",
                                  {"=": ["statusCode", "789"]},
                                  {"=": ["foo", "Marsupilami & Fantasio"]},
                                  {"<=": ["timePeriod", "1234567"]}
                                ]}]},
                          {"f:len": []}
                        ]},
                      {"f:len2": []}
                    ]},
                  {"f:len3": []}
                ]},
              "f:len4"
            ]
          },
          {"AND": [{"AND": ["Athos", "Porthos"]}, "Aramis"]}
        ]}},
    {
      "node": "benefits",
      "ranges": [
        {"start": 1, "end": 1},
        {"start": 2, "end": 9},
        {"start": 15, "end": 20},
        {"start": 33, "end": 33}
      ]},
    {
      "node": "amounts",
      "predicate": {
        "!=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "coInsurance",
                "predicate": {
                  "&&": [
                    {
                      "AND": [
                        {"=": ["insuranceType", "A"]},
                        {"~": [{"!": [{"!": ["a"]}]}]}
                      ]},
                    "b"
                  ]}}]},
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"=": ["name", "Dental Care"]}}]}]}},
    {
      "node": "deductibles",
      "ranges": [
        {"start": 0, "end": 0},
        {"start": -1, "end": -1}]}]}
""",
    ### . ###
    """
# selector   :       a  .  b  .  c.   d      \t
# ast  :
{
  "selector": [
    { "node": "a" },
    { "node": "b" },
    { "node": "c" },
    { "node": "d" } ] }
""",
    ### . ###
    """
# selector:
a{3 OR 4    AND    2   777      AND ( 1 OR 5 )}

# ast:
{
  "selector": [
    {
      "node": "a",
      "predicate": {
        "OR": [
          "3",
          {
            "AND": [
              {"AND": [{"AND": ["4", "2"]}, "777"]},
              {"OR": ["1", "5"]} ] } ] } } ] }
    """,
    ### . ###
    """
# selector:  
a {
    f:sin(
        f:max(
            this.kk1.jj2.ii3 {
                this.val1 = 'Vingt Mille Lieues sous les mers'
                } = 'jean valjean',
            z  <  3
            ) 3 π )
    f:min(11, 17)
}
.b [
     1
     2-9
     15-20
     33
  ]        

# ast:
{
  "selector": [
    {
      "node": "a",
      "predicate": {
        "AND": [
          {
            "f:sin": [
              {
                "AND": [
                  {
                    "AND": [
                      {
                        "f:max": [
                          {
                            "=": [
                              {
                                "selector": [
                                  {"node": "this"},
                                  {"node": "kk1"},
                                  {"node": "jj2"},
                                  {
                                    "node": "ii3",
                                    "predicate": {
                                      "=": [
                                        {
                                          "selector": [
                                            {"node": "this"},
                                            {"node": "val1"} ] },
                                        "Vingt Mille Lieues sous les mers"
                                      ] } } ] },
                              "jean valjean"
                            ] },
                          {"<": ["z", "3"]}
                        ] },
                      "3"
                    ] },
                  "π"
                ] } ] },
          { "f:min": ["11", "17"] } ] } },
    {
      "node": "b",
      "ranges": [
        {"start": 1, "end": 1},
        {"start": 2, "end": 9},
        {"start": 15, "end": 20},
        {"start": 33, "end": 33}
      ] } ] }        
""",
    ### . ###
    """
# selector:
a {
    f:sin(
        f:max(
            this.kk1.jj2.ii3 {
                this.val1 = 'Vingt Mille Lieues sous les mers'
                } = 'jean valjean',
            z  <  3
            ) 3 π )
    f:min(11, 17, 8, 9)
    f:len   (Athos Porthos Aramis)
}
.b [
     1
     2-9
     15-20
     33
  ]        

# ast:
{
  "selector": [
    {
      "node": "a",
      "predicate": {
        "AND": [
          {
            "AND": [
              {
                "AND": [
                  {
                    "f:sin": [
                      {
                        "AND": [
                          {
                            "AND": [
                              {
                                "f:max": [
                                  {
                                    "=": [
                                      {
                                        "selector": [
                                          {"node": "this"},
                                          {"node": "kk1"},
                                          {"node": "jj2"},
                                          {
                                            "node": "ii3",
                                            "predicate": {
                                              "=": [
                                                {
                                                  "selector": [
                                                    {"node": "this"},
                                                    {"node": "val1"} ] },
                                                "Vingt Mille Lieues sous les mers"
                                              ] } } ] },
                                      "jean valjean"
                                    ] },
                                  {"<": ["z", "3"]}
                                ] },
                              "3"
                            ] },
                          "π"
                        ] } ] },
                  {"f:min": ["11", "17", "8", "9"]}
                ] },
              {"f:len": []}
            ] },
          {"AND": [{"AND": ["Athos", "Porthos"]}, "Aramis"]}
        ] } },
    {
      "node": "b",
      "ranges": [
        {"start": 1, "end": 1},
        {"start": 2, "end": 9},
        {"start": 15, "end": 20},
        {"start": 33, "end": 33}
      ] } ] }
""",
    ### . ###
    """
# selector: n {3 AND NOT a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"NOT": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND NOT a NOT b}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          {"AND": ["3", {"NOT": ["a"]}]},
          {"NOT": ["b"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND ! a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"!": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND !a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"!": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 NOT a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"NOT": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 ! a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"!": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 !a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": ["3", {"!": ["a"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND NOT a NOT b}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          {"AND": ["3", {"NOT": ["a"]}]},
          {"NOT": ["b"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND !a !b}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          {"AND": ["3", {"!": ["a"]}]},
          {"!": ["b"]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND NOT NOT a}
# ast: {"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          "3",
          {"NOT": [{"NOT": ["a"]}]}]}}]}
""",
    ### . ###
    """
# selector: n {3 AND !!a}
# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          "3",
          {
            "!": [
              {"!": ["a"]}
            ]}]}}]}
""",
    ### . ###
    """
# selector: n {3 !a !b}
# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          {"AND": ["3", {"!": ["a"]}]},
          {"!": ["b"]}]}}]}

""",
    ### . ###
    """
# selector: n {3 NOT NOT a}
# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          "3",
          {
            "NOT": [
              {"NOT": ["a"]}
            ]}]}}]}
""",
    ### . ###
    """
# selector: n {3 !!a}
# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "AND": [
          "3",
          {
            "!": [
              {"!": ["a"]}
            ]}]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{ name = "A" ~!!a && b} = this.plans{ name = "B" }  
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {
                  "&&": [
                    {
                      "AND": [
                        {"=": ["name", "A"]},
                        {"~": [{"!": [{"!": ["a"]}]}]}
                      ]},
                    "b"
                  ]}}]},
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"=": ["name", "B"]}}]}]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{ name = "A" ~!!a && b} != this.plans{ name = "B" }  
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "!=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {
                  "&&": [
                    {
                      "AND": [
                        {"=": ["name", "A"]},
                        {"~": [{"!": [{"!": ["a"]}]}]}
                      ]},
                    "b"
                  ]}}]},
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"=": ["name", "B"]}}]}]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{aaa} = bbb
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"aaa": []}
              }]},
          "bbb"]}}]}
""",
    ### . ###
    """
# selector: 
n {
  this.plans{a} = this.plans{b}
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {"node": "plans", "predicate": {"a": []}}
            ]},
          {
            "selector": [
              {"node": "this"},
              {"node": "plans", "predicate": {"b": []}}]}]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{ name = "A c d" } = B
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {"node": "plans", "predicate": {"=": ["name", "A c d"]}}
            ]},
          "B"]}}]}
""",
    ### . ###
    """
# selector:
n {
  this.plans{ name = "A c d" ~!!a && b} = this.plans{ name = B }
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "=": [
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {
                  "&&": [
                    {
                      "AND": [
                        {"=": ["name", "A c d"]},
                        {"~": [{"!": [{"!": ["a"]}]}]}
                      ]},
                    "b"
                  ]}}]},
          {
            "selector": [
              {"node": "this"},
              {
                "node": "plans",
                "predicate": {"=": ["name", "B"]}
              }]}]}}]}
""",
    ### . ###
    """
# selector: 
n {
  a != b
}

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {"!=": ["a", "b"]}
    }]}
""",
]

TEST_DATA_BUFFER: list[str] = [
    ### . ###
    """
    # selector:
    a { NOT b}
    # ast:
    {}
        """,
    ### . ###
    """
# selector: 
a { 
  a1{ b.c{ d.e = 3, z < 3 } = 4 } = v1 
}.a1.a2{}

# ast:
{}
""",
    ### . ###
    """
# selector: 
a { 
 f.max(
   this.b { bbb <= 1 } = "Vingt Mille Lieues sous les mers",
   z <= 3
 )
  
}.a1.a2{}

# ast:
{}
""",
    ### . ###
    """
# selector: 
n { 3 + 4 * 2 / ( 1 _ 5 ) ^ 2 ^ 3 }

# ast:
{"selector": [
    {
      "node": "n",
      "predicate": {
        "+": [
          "3",
          {
            "/": [
              {"*": ["4", "2"]},
              {"^": [
                  {"_": ["1", "5"]},
                  {"^": ["2", "3"]}
                ]}
            ]
          }
        ]}}]}
    """,
    ### . ###
    ### . ###
    ### . ###
    ### . ###
    ### . ###
]

SELECTOR_SAMPLE: str = """
        a.b{f:f1 f:f2 (f:f3 OR f:f4) f:f5}.c[1-3, 7, f:f5]

        # Is that really needed? Doesn't seem so
        a.b{f:f1 f:f2 (f:f3 OR f:f4) f:f5}.c[1-3, 7, f:f5]:node

        a.b{f:f1 f:f2 (f:f3 OR v=w1 w2 w3) f:f5}.c[1-3, 7, f:f5]

        a.b{f:f1 f:f2 (f:f3 OR v="w1 w2 w3 'w4' \"w5\" w6") f:f5}.c[1-3, 7, f:f5]

        a.b.c{d.e.k = 3 AND x.y > 5}

        a.b.c{f:f1 = 137 AND f:f2(p1, p2) = "  abc... z  "}

        DEFINITION: def f:f1(node, context, a, b, c,  …)

raw.1659.plans[0].benefits[8].status
raw.[1659].plans[0].benefits[8].status
raw.[1659].plans[0].benefits[8].status
raw.1659.plans{name = ABC}.benefits[8].status
raw.1659.plans{f:has_name}.benefits[8].status
raw.1659.plans{f:has_name(plan = ABC)}.benefits[8].status
raw.1659.plans{ name = ABC }.benefits[8].status
raw.1659.plans{ name == ABC }.benefits[8].status
raw.1659.plans{ name > 1 }.benefits[8].status
raw.1659.plans{ name != 1 }.benefits[8].status
raw.1659.plans{ name < 1 }.benefits[8].status
raw.1659.plans{ name = ABC }.benefits[0, 1-5, 8].status
raw.1659.plans{ name = ABC }.benefits[*].status
raw.1659.plans{ name = ABC }.benefits[a.b.c = 123].status
raw.1659.plans{ name = ABC, type = 123 }.benefits[8].status
raw.1659.plans{ name = ABC AND type = 123 }.benefits[8].status
raw.1659.plans{ name = ABC OR type = 123 }.benefits[8].status
raw.1659.plans{ name = ABC -type = 123 }.benefits[8].status
raw.1659.plans{ name = ABC NOT type = 123 }.benefits[8].status
raw.1659.plans[0].benefits[8].status
"""

MORE_SELECTOR_SAMPLE: tuple[tuple[str, list[str]] | tuple[int, int], ...] = (
    ("  a  .  b  .  c.   d   ", ["a", "b", "c", "d"]),
    ("a{(3 OR 4) AND (2 OR 1)}", []),
    ("a{3 OR 4 AND 2 AND ( 1 OR 5 )}", []),
    ("a{3 OR 4    AND    2   777      AND ( 1 OR 5 )}", []),
    ("a{f:sin( f:max( 2, 3 ) AND 3 AND π )}", []),
    ("a{f:sin( f:max( 2, 3 ) 3 π ) f:min(11, 17)}", []),
    ("a{f:sin( f:max( x =  2, z  <  3  ) 3 π ) f:min(11, 17)}", []),
    ("a{f:sin( f:max( k.j.i =  2, z  <  3  ) 3 π ) f:min(11, 17)}", []),
    (
        "a{f:sin( f:max( kk1.jj2.ii3 = 'jean valjean', z  <  3  ) 3 π ) f:min(11, 17)}.b[1, 2-9 15-20   ,   33]",
        [],
    ),
    (
        "a{f:sin( f:max( this.kk1.jj2.ii3{this.val1 = 'Vingt Mille Lieues sous les mers'} = 'jean valjean', z  <  3  ) 3 π ) f:min(11, 17)}.b[1, 2-9 15-20   ,   33]",
        [],
    ),
    (0, 0),
    (
        """
        a {
            f:sin(
                f:max(
                    this.kk1.jj2.ii3 {
                        this.val1 = 'Vingt Mille Lieues sous les mers'
                        } = 'jean valjean',
                    z  <  3
                    ) 3 π )
            f:min(11, 17)
            f:len (Athos Porthos Aramis)
        }

        .b [
             1
             2-9
             15-20
             33
          ]            
        """,
        [],
    ),
    (
        "a{f:sin( f:max( kk1.jj2.ii3 =  2, z  <  3  ) 3 π ) f:min(11, 17)}.b[1, 2-9 15-20, 33]",
        [],
    ),
    ("a{f:sin( f:max( 2, 3 ) AND 3 AND π ) f:min(11, 17)}", []),
    (0, 0),
    ("  a{f:f1(x, y) f:f2(k1, k2) (A OR B) k = ABC}", []),
    (1, 1),
    ("  a.b.c.d   ", ["a", "b", "c", "d"]),
    ("  a.b[1, 2-9 15-20, 33].c.d[2, 3-9]   ", []),
    (0, 0),
    (
        "  a.b{f:f1(x, y) f:f2(k1, k2) (A OR B) k = ABC}.c.d[1, 2-9 15-20, 33]   ",
        [],
    ),
    (
        "  a.b{f:f1(x = 1, y) f:f2(k1, k2) (A OR B) k = ABC}.c.d[1, 2-9 15-20, 33]   ",
        [],
    ),
    ("  a.b{f:f1 f:f2 (A OR B) k = ABC}.c.d[1, 2-9 15-20, 33]   ", []),
    (1, 1),
    (
        "  a.b  {  f:f1 f:f2 (A OR B) f:f3(a = 1, b=2)} .c.d   ",
        ["a", "b", "c", "d"],
    ),
    (
        'a.b{f:f1 f:f2 (f:f3 OR v="w1 w2 w3 \'w4\' " w5 " w6") f:f5}.c[1-3, 7, f:f5]',
        [],
    ),
    (
        'a.b  {   f:f1 f:f2 (   f:f3 OR v="w1 w2 w3 \'w4\' " w5 " w6") f:f5  } .c   [   1-3, 7, f:f5]',
        [],
    ),
    ("a.b{f:f1  f:f2 (f:f3 OR f:f4) f5}.c[1-3,  7 , f5]", []),
    ("  a.b {f:f1  f:f2 (f:f3 OR f:f4) f5}.c [1-3,  7 , f5]  ", []),
    ("a.b{f:f1  f:f2 (f:f3 AND (f:f4 OR w0)) f5}.c[1-3,  7 , f5]", []),
    ("a.b{f:f1  f:f2 (f:f3 AND(f:f4 OR w0)) f5}.c[1-3,  7 , f5]", []),
    ("a.b{f:f1 f:f2 (f:f3 OR v=w1 w2 w3) f:f5}.c[1-3, 7, f:f5]", []),
    (
        'a.b{f:f1 f:f2 (f:f3 OR v="w1 w2 w3 \'w4\' "w5" w6") f:f5}.c[1-3, 7, f:f5]',
        [],
    ),
    ("a.b.c{d.e.k = 3 AND x.y > 5}", []),
    ('a.b.c{f:f1 = 137 AND f:f2(p1, p2) = "  abc... z  "}', []),
)
