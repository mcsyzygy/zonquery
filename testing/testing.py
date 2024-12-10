import timeit
from typing import Any
from typing import Optional
import unittest

from core.lib import as_json
from core.lib import json
from core.zonquery import parse


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


def benchmark(data: "TestingData", reps: int = 10_000):
    # data = TestingData(TEST_DATA[selector - 1])
    print("─── Selector ───")
    print(f"⌦{data.selector}⌫")

    def fn():
        parse(data.selector)

    run_time = timeit.timeit(fn, number=reps)
    print(f"Average run time: {(run_time / reps ) * 1_000_000:,.0f} µs")
