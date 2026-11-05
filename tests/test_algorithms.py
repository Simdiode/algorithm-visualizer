"""Run with: python -m unittest discover -s tests -v"""

import itertools
import math
import random
import unittest

from algorithms import SORTS, SEARCHES, visualize
from benchmark import fixture, run_benchmarks


class SortingTests(unittest.TestCase):
    def test_exhaustive_small_arrays(self):
        for n in range(7):
            for values in itertools.product((-1, 0, 1), repeat=n):
                expected = sorted(values)  # Test oracle only, never production logic.
                for name, function in SORTS.items():
                    a = list(values)
                    function(a)
                    self.assertEqual(a, expected, (name, values))

    def test_random_arrays_and_trace_integrity(self):
        rng = random.Random(21)
        for _ in range(35):
            a = [rng.randint(-999, 999) for _ in range(rng.randrange(49))]
            for name, function in SORTS.items():
                data = visualize(name, a)
                self.assertEqual(data["result"], sorted(a))
                self.assertEqual(data["steps"][0]["values"], a)
                self.assertEqual(data["steps"][-1]["values"], sorted(a))
                work = a[:]
                s = function(work)
                self.assertEqual(data["steps"][-1]["comparisons"], s.comparisons)
                self.assertEqual(data["steps"][-1]["swaps"], s.swaps)
                self.assertEqual(data["steps"][-1]["writes"], s.writes)
                previous = (0, 0, 0)
                for frame in data["steps"]:
                    self.assertEqual(len(frame["values"]), len(a))
                    for i in frame["active"] + frame["fixed"]:
                        self.assertTrue(0 <= i < len(a))
                    self.assertTrue(frame["pivot"] == -1 or 0 <= frame["pivot"] < len(a))
                    counts = (frame["comparisons"], frame["swaps"], frame["writes"])
                    self.assertTrue(all(x >= y for x, y in zip(counts, previous)))
                    previous = counts

    def test_bubble_counts_and_early_exit(self):
        s = SORTS["bubble"]([4, 3, 2, 1])
        self.assertEqual((s.comparisons, s.swaps, s.writes), (6, 6, 12))
        s = SORTS["bubble"]([1, 2, 3, 4])
        self.assertEqual((s.comparisons, s.swaps, s.writes), (3, 0, 0))

    def test_stability_of_bubble_and_merge(self):
        class Item:
            def __init__(self, key, label):
                self.key, self.label = key, label

            def __gt__(self, other):
                return self.key > other.key

            def __le__(self, other):
                return self.key <= other.key

        for name in ("bubble", "merge"):
            a = [Item(2, "a"), Item(1, "b"), Item(2, "c"), Item(1, "d")]
            SORTS[name](a)
            self.assertEqual([x.label for x in a], ["b", "d", "a", "c"])

    def test_quick_degenerate_input_avoids_recursion_overflow(self):
        for a in (list(range(2048)), [7] * 2048):
            s = SORTS["quick"](a)
            self.assertEqual(s.comparisons, 2048 * 2047 // 2)
            self.assertEqual(a, sorted(a))


class SearchTests(unittest.TestCase):
    def test_exhaustive_search(self):
        for n in range(6):
            for values in itertools.product((-1, 0, 1), repeat=n):
                for target in (-2, -1, 0, 1, 2):
                    a = list(values)
                    expected = a.index(target) if target in a else -1
                    self.assertEqual(SEARCHES["linear"](a, target).index, expected)
                    a.sort()  # Test input preparation only.
                    result = SEARCHES["binary"](a, target).index
                    self.assertEqual(result >= 0, target in a)
                    if result >= 0:
                        self.assertEqual(a[result], target)

    def test_binary_sorted_copy_and_index(self):
        values = [5, -2, 5, 0]
        data = visualize("binary", values, -2)
        self.assertTrue(data["prepared"])
        self.assertEqual(data["result"], [-2, 0, 5, 5])
        self.assertEqual(data["index"], 0)
        self.assertEqual(values, [5, -2, 5, 0])
        self.assertEqual(data["steps"][-1]["writes"], 0)
        self.assertFalse(visualize("binary", [-1, 0, 1], 1)["prepared"])

    def test_empty_missing_and_search_counts(self):
        for name in SEARCHES:
            data = visualize(name, [], 5)
            self.assertEqual(data["index"], -1)
            self.assertEqual(data["steps"][-1]["comparisons"], 0)
            self.assertEqual(data["steps"][-1]["kind"], "missing")
        self.assertEqual(SEARCHES["linear"]([1, 2, 3], 8).comparisons, 3)
        self.assertEqual(SEARCHES["binary"]([1, 2, 3], 2).comparisons, 1)
        self.assertEqual(SEARCHES["binary"]([1, 2, 3], 3).comparisons, 3)


class BenchmarkTests(unittest.TestCase):
    def test_case_generators_and_operation_counts(self):
        for n in (8, 32, 128, 512, 1024):
            for name, function in SORTS.items():
                counts = {}
                for case in ("best", "average", "worst"):
                    a, _ = fixture(name, case, n)
                    self.assertEqual(sorted(a), list(range(n)))
                    counts[case] = function(a).comparisons
                    self.assertEqual(a, list(range(n)))
                if name == "bubble":
                    self.assertEqual(counts["best"], n - 1)
                    self.assertEqual(counts["worst"], n * (n - 1) // 2)
                elif name == "merge":
                    self.assertEqual(counts["best"], n * int(math.log2(n)) // 2)
                    self.assertEqual(counts["worst"], n * int(math.log2(n)) - n + 1)
                else:
                    self.assertLessEqual(counts["best"], n * math.ceil(math.log2(n)))
                    self.assertEqual(counts["worst"], n * (n - 1) // 2)
            for name, function in SEARCHES.items():
                for case in ("best", "average", "worst"):
                    a, targets = fixture(name, case, n)
                    for target in targets:
                        result = function(a, target)
                        self.assertEqual(result.index >= 0, case != "worst")
                        if case == "best":
                            self.assertEqual(result.comparisons, 1)
                        elif case == "worst":
                            expected = n if name == "linear" else 2 * (int(math.log2(n)) + 1)
                            self.assertEqual(result.comparisons, expected)

    def test_benchmark_produces_measured_rows(self):
        for group, expected in (("sort", 9), ("search", 6)):
            result = run_benchmarks(group, sizes=(32,), repeats=5)
            self.assertEqual(len(result["rows"]), expected)
            for row in result["rows"]:
                self.assertGreater(row["ms"], 0)
                self.assertGreater(row["comparisons"], 0)


if __name__ == "__main__":
    unittest.main()
