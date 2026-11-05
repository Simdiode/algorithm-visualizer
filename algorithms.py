"""Project 21: array algorithms written from scratch, with optional trace snapshots.

The same functions power animation and benchmarking. Python lists are used only
as arrays; no built-in sorting/searching or library data structures are used.
"""

from dataclasses import dataclass


@dataclass
class Stats:
    comparisons: int = 0  # Comparisons between data values, excluding loop bounds.
    swaps: int = 0        # Exchanges of two distinct indices.
    writes: int = 0       # Writes to the main array (each swap is two writes).
    index: int = -1


class Trace:
    """Stores complete frames so the UI can move both forward and backward."""

    def __init__(self):
        self.steps = []
        self.fixed = []

    def emit(self, a, stats, line, message, active=(), kind="inspect",
             bounds=None, pivot=-1, buffers=None):
        self.steps.append({
            "values": a[:], "active": list(active), "fixed": self.fixed[:],
            "kind": kind, "line": line, "message": message,
            "bounds": bounds, "pivot": pivot, "buffers": buffers,
            "comparisons": stats.comparisons, "swaps": stats.swaps,
            "writes": stats.writes, "index": stats.index,
        })


def bubble_sort(a, trace=None):
    s = Stats()
    for end in range(len(a) - 1, 0, -1):
        changed = False
        for j in range(end):
            s.comparisons += 1
            if trace:
                trace.emit(a, s, 2, f"Compare {a[j]} and {a[j + 1]}.", (j, j + 1))
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                s.swaps += 1
                s.writes += 2
                changed = True
                if trace:
                    trace.emit(a, s, 3, "Out of order: swap the adjacent values.",
                               (j, j + 1), "swap")
        if trace:
            trace.fixed.append(end)
            trace.emit(a, s, 4, f"Pass complete. Index {end} is in its final position.")
        if not changed:
            if trace:
                trace.emit(a, s, 5, "No swaps in this pass. The array is sorted.")
            break
    return s


def merge_sort(a, trace=None):
    s = Stats()
    temp = [0] * len(a)

    def split(lo, hi):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        if trace:
            trace.emit(a, s, 1, f"Split [{lo}, {hi}] at index {mid}.",
                       bounds=[lo, hi], kind="partition")
        split(lo, mid)
        split(mid + 1, hi)
        for k in range(lo, hi + 1):
            temp[k] = a[k]
        i, j, k = lo, mid + 1, lo

        def buffers():
            # Show the actual source buffers, rather than stale positions in a.
            return {"left": temp[lo:mid + 1], "right": temp[mid + 1:hi + 1],
                    "i": i - lo, "j": j - mid - 1}

        if trace:
            trace.emit(a, s, 3, f"Merge the two sorted halves of [{lo}, {hi}].",
                       bounds=[lo, hi], buffers=buffers())
        while i <= mid and j <= hi:
            s.comparisons += 1
            if trace:
                trace.emit(a, s, 4, f"Compare buffer values {temp[i]} and {temp[j]}.",
                           bounds=[lo, hi], buffers=buffers())
            # <= preserves the order of equal elements (stable sort).
            if temp[i] <= temp[j]:
                a[k] = temp[i]
                i += 1
            else:
                a[k] = temp[j]
                j += 1
            s.writes += 1
            if trace:
                trace.emit(a, s, 5, f"Write {a[k]} to index {k}.", (k,), "write",
                           [lo, hi], buffers=buffers())
            k += 1
        while i <= mid:
            a[k] = temp[i]
            s.writes += 1
            i += 1
            if trace:
                trace.emit(a, s, 6, f"Copy remaining left value {a[k]} to index {k}.",
                           (k,), "write", [lo, hi], buffers=buffers())
            k += 1
        while j <= hi:
            a[k] = temp[j]
            s.writes += 1
            j += 1
            if trace:
                trace.emit(a, s, 6, f"Copy remaining right value {a[k]} to index {k}.",
                           (k,), "write", [lo, hi], buffers=buffers())
            k += 1

    split(0, len(a) - 1)
    return s


def quick_sort(a, trace=None):
    """Lomuto partition, last-element pivot, smaller-side recursion.

    Recursing only on the smaller partition bounds call-stack use by O(log n),
    even when the time is O(n^2). No library stack is needed.
    """
    s = Stats()

    def swap(i, j, lo, hi, pivot, line):
        if i != j:
            a[i], a[j] = a[j], a[i]
            s.swaps += 1
            s.writes += 2
            if trace:
                trace.emit(a, s, line, f"Swap indices {i} and {j}.", (i, j),
                           "swap", [lo, hi], pivot)

    def partition(lo, hi):
        pivot = a[hi]
        i = lo
        if trace:
            trace.emit(a, s, 1, f"Choose {pivot} at index {hi} as the pivot.",
                       bounds=[lo, hi], pivot=hi, kind="partition")
        for j in range(lo, hi):
            s.comparisons += 1
            if trace:
                trace.emit(a, s, 3, f"Compare {a[j]} with pivot {pivot}.", (j,),
                           bounds=[lo, hi], pivot=hi)
            if a[j] <= pivot:
                swap(i, j, lo, hi, hi, 4)
                i += 1
        swap(i, hi, lo, hi, i, 5)
        if trace:
            trace.fixed.append(i)
            trace.emit(a, s, 5, f"Pivot {pivot} is now fixed at index {i}.",
                       bounds=[lo, hi], pivot=i)
        return i

    def sort(lo, hi):
        while lo < hi:
            p = partition(lo, hi)
            if p - lo < hi - p:
                sort(lo, p - 1)
                lo = p + 1
            else:
                sort(p + 1, hi)
                hi = p - 1
        if lo == hi and trace:
            trace.fixed.append(lo)

    sort(0, len(a) - 1)
    return s


def linear_search(a, target, trace=None):
    s = Stats()
    for i in range(len(a)):
        s.comparisons += 1
        if trace:
            trace.emit(a, s, 1, f"Compare {a[i]} at index {i} with target {target}.",
                       (i,), bounds=[i, len(a) - 1])
        if a[i] == target:
            s.index = i
            if trace:
                trace.emit(a, s, 2, f"Found {target} at index {i}.", (i,), "found")
            return s
    return s


def binary_search(a, target, trace=None):
    """a must already be sorted in ascending order. Returns any matching index."""
    s = Stats()
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s.comparisons += 1
        if trace:
            trace.emit(a, s, 2, f"low={lo}, mid={mid}, high={hi}. Is {a[mid]} = {target}?",
                       (mid,), bounds=[lo, hi])
        if a[mid] == target:
            s.index = mid
            if trace:
                trace.emit(a, s, 3, f"Found {target} at sorted-array index {mid}.",
                           (mid,), "found", [lo, hi])
            return s
        s.comparisons += 1
        if a[mid] < target:
            lo = mid + 1
            message, line = "Target is larger. Discard the left half.", 4
        else:
            hi = mid - 1
            message, line = "Target is smaller. Discard the right half.", 5
        if trace:
            trace.emit(a, s, line, message, bounds=[lo, hi])
    return s


SORTS = {"bubble": bubble_sort, "merge": merge_sort, "quick": quick_sort}
SEARCHES = {"linear": linear_search, "binary": binary_search}


def visualize(algorithm, values, target=None):
    """Build a bounded animation trace. Input is validated by the HTTP layer."""
    a = values[:]
    prepared = False
    if algorithm == "binary":
        # Preprocessing is explicit and excluded from search statistics.
        for i in range(1, len(a)):
            if a[i - 1] > a[i]:
                merge_sort(a)
                prepared = True
                break
    trace = Trace()
    trace.emit(a, Stats(), -1, "Ready. Press Play or advance one step.", kind="ready")
    if algorithm in SORTS:
        stats = SORTS[algorithm](a, trace)
        trace.fixed = list(range(len(a)))
        message = "Sorted. Every value is in ascending order."
        kind = "done"
    else:
        stats = SEARCHES[algorithm](a, target, trace)
        message = (f"Found {target} at index {stats.index}." if stats.index >= 0
                   else f"{target} is not present in the array.")
        kind = "found" if stats.index >= 0 else "missing"
    trace.emit(a, stats, -1, message, kind=kind)
    return {"algorithm": algorithm, "steps": trace.steps,
            "prepared": prepared, "original": values, "result": a,
            "index": stats.index}
