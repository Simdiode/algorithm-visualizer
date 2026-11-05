"""Measured timings with reproducible, algorithm-specific case fixtures."""

import random
import statistics
from time import perf_counter_ns

from algorithms import SORTS, SEARCHES


def balanced_quick_input(values):
    """Arrange unique ascending values for balanced last-pivot partitions.

    Lomuto rotates the first value of the right partition to its end when it
    places a pivot. Undo that rotation when constructing the input recursively.
    """
    n = len(values)
    if n < 2:
        return values[:]
    mid = n // 2
    left = balanced_quick_input(values[:mid])
    right = balanced_quick_input(values[mid + 1:])
    before_rotation = right[-1:] + right[:-1]
    return left + before_rotation + [values[mid]]


def interleaved_merge_input(values):
    """Maximally interleaved halves, recursively (power-of-two sizes)."""
    if len(values) < 2:
        return values[:]
    return (interleaved_merge_input(values[::2]) +
            interleaved_merge_input(values[1::2]))


def fixture(algorithm, case, n):
    values = list(range(n))
    rng = random.Random(2100 + n)
    if algorithm in SORTS:
        if case == "average":
            rng.shuffle(values)
        elif algorithm == "quick" and case == "best":
            values = balanced_quick_input(values)
        elif algorithm == "bubble" and case == "worst":
            values = values[::-1]
        elif algorithm == "merge" and case == "worst":
            values = interleaved_merge_input(values)
        # Sorted ascending is quick's worst and merge/bubble's best fixture.
        return values, [None]
    if case == "worst":
        targets = [n] * 256  # Above maximum: deepest path for these power-of-two sizes.
    elif case == "best":
        targets = [0 if algorithm == "linear" else (n - 1) // 2] * 256
    else:
        targets = [rng.randrange(n) for _ in range(256)]
    return values, targets


def run_benchmarks(group="sort", sizes=(32, 128, 512, 1024), repeats=5):
    functions = SORTS if group == "sort" else SEARCHES
    rows = []
    for name, function in functions.items():
        for case in ("best", "average", "worst"):
            for n in sizes:
                values, targets = fixture(name, case, n)
                # Warm up once, without capturing trace snapshots.
                if group == "sort":
                    function(values[:])
                else:
                    for target in targets:
                        function(values, target)
                samples = []
                count = 0
                for _ in range(repeats):
                    if group == "sort":
                        work = values[:]  # Copying is outside the timed interval.
                        start = perf_counter_ns()
                        stats = function(work)
                        elapsed = perf_counter_ns() - start
                        count = stats.comparisons
                    else:
                        start = perf_counter_ns()
                        count = 0
                        for target in targets:
                            count += function(values, target).comparisons
                        elapsed = (perf_counter_ns() - start) / len(targets)
                        count /= len(targets)
                    samples.append(elapsed / 1_000_000)
                rows.append({"algorithm": name, "case": case, "n": n,
                             "ms": statistics.median(samples),
                             "comparisons": count})
    return {"rows": rows, "repeats": repeats, "sizes": list(sizes),
            "group": group, "search_batch_size": 256,
            "method": "Median of 5 timed samples after warm-up. No trace or animation. "
                      "Sort input copies and binary-search preprocessing are excluded. "
                      "Search samples average 256 lookups; average-case targets vary. "
                      "Python counter/bookkeeping overhead is included. Timings vary by machine."}
