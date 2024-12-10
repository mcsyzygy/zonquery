from typing import Any
from typing import Optional
import unittest

from core.zonquery import parse
from testing.testing import TestingData
from testing.testing import TestingJsonTestCase
from tests.data import TEST_DATA


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
