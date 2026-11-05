# Algorithm Visualiser


## Run

Requires **Python 3.9 or newer** and a current browser. No pip packages, Node,
API keys, internet connection or database are needed.

1. Extract the ZIP completely.
2. On Windows, double-click **run.bat**. Or open a terminal in this folder and run:

   ```sh
   python server.py
   ```

   On macOS/Linux, use `python3 server.py` if `python` is unavailable.
3. The browser opens at **http://127.0.0.1:8000**. Keep the terminal open.
4. Press **Ctrl+C** in the terminal to stop.

If port 8000 is occupied, run `python server.py --port 8001` and open the address
it prints. If the browser does not open automatically, open the address manually.
Do not open `web/index.html` directly: it needs the local Python server.

## Features

- Bubble Sort, Merge Sort, Quick Sort, Linear Search and Binary Search.
- Animated array bars, active comparisons, swaps/writes, fixed values and pivots.
- Merge Sort shows its actual temporary buffers and read pointers.
- Play/pause, restart, forward/backward steps, seek slider and speed controls.
- Click any execution-trace entry to inspect that exact frame.
- Current pseudocode line, comparison/swap/write counts and complexity summaries.
- Custom arrays, random/sorted/reversed/duplicate presets, signed integers and empty arrays.
- Actual best/average/worst-case timings for input sizes 32, 128, 512 and 1,024.
- Sorting/searching comparisons, timing tables and benchmark CSV export.
- Responsive layout, keyboard controls and reduced-motion support.

## Implementation

| File | Purpose |
| --- | --- |
| `algorithms.py` | All five algorithms, counters and optional execution snapshots |
| `benchmark.py` | Input-case generators and measured benchmark runs |
| `server.py` | Standard-library HTTP server and validated JSON endpoints |
| `web/index.html` | Browser interface |
| `web/style.css` | Layout, highlights and transitions |
| `web/app.js` | Playback, rendering, controls and benchmark chart |
| `tests/test_algorithms.py` | Correctness, trace and case-fixture tests |
| `run.bat` | Windows launcher |
| `package.json` | Optional development-preview launcher; npm is not required |
| `api/trace.py`, `api/benchmark.py` | Vercel Python Function entry points |
| `vercel.json` | Static frontend and Python Function deployment configuration |

Python lists represent arrays and auxiliary buffers. Core operations are written
from scratch: no `sort()`, `sorted()`, `bisect`, NumPy or library DS shortcuts.
Standard-library randomization is used only to prepare sample datasets.
JavaScript handles display and playback; it does not run the sorting/searching algorithms.
There is no report, presentation or team-role assignment in this package.

## Correctness and conventions

- Indices start at 0. Empty arrays are supported; an absent target returns −1.
- Linear Search returns the first match. Binary Search returns any matching index.
- Binary Search requires ascending input. If needed, Python Merge Sort prepares
  a **sorted copy**, with a visible notice. Result indices refer to that displayed
  copy, and sorting is excluded from the search statistics.
- Bubble and Merge Sort are stable. This Quick Sort implementation is unstable
  and uses a last-element pivot with Lomuto partitioning.
- Quick Sort recurses only on the smaller partition and iterates over the larger.
  Its stack is O(log n) in the worst case; its worst-case time is still O(n²).
- Comparisons count value comparisons, not loop bounds. Binary Search counts
  equality plus, when needed, one ordering check. A swap between distinct indices
  counts as two main-array writes. Writes to the Merge Sort buffer are excluded.
- The UI permits at most 48 integers in [−999, 999] to keep traces readable and bounded.

| Algorithm | Best time | Average time | Worst time | Algorithm extra space |
| --- | --- | --- | --- | --- |
| Bubble Sort, early exit | O(n) | O(n²) | O(n²) | O(1) |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) |
| Quick Sort, smaller-side recursion | O(n log n) | O(n log n) | O(n²) | O(log n) |
| Linear Search | O(1) | O(n) | O(n) | O(1) |
| Binary Search, already sorted input | O(1) | O(log n) | O(log n) | O(1) |

Space figures describe the algorithms **without trace capture**. The visualizer
stores an array copy per step for backward playback, so a trace uses O(n × steps)
memory, up to O(n³) for these quadratic-sort traces. Trace creation is limited to
48 values; benchmark mode never captures it.

## Benchmark method

Benchmarks call the same Python functions as the visualizer, with tracing disabled.
One warm-up precedes five samples; the median is shown. `perf_counter_ns()` measures
elapsed wall time. Sort input copies and binary-search preprocessing are outside
the timed interval. Counters and normal Python function/loop overhead are included.

For searches, each sample averages 256 lookups. Average-case queries uniformly
sample valid indices using a fixed seed. Best-case queries hit the first element
(linear) or initial midpoint (binary); worst-case queries are absent above the maximum.
Binary-search timings assume an already sorted array and are not end-to-end sort-plus-search times.

Sorting fixtures are algorithm-specific. Bubble uses ascending/shuffled/descending
input; Merge uses ascending/shuffled/recursively interleaved halves; Quick uses
balanced-partition/shuffled/ascending input. These are controlled teaching cases,
not a claim that all real-world inputs fit one universal best/worst dataset.
The chart uses a logarithmic y-axis; the table and CSV show exact measured values.
Small timings vary with Python version, machine load and timer noise.

## Verify

```sh
python -m unittest discover -s tests -v
```

The local server binds to loopback by default and is intended for a local classroom
demo. It serves a fixed file allowlist and validates JSON requests. Hosted Vercel
deployments use Python Functions rather than running this local server process.

## Vercel deployment

This source includes Vercel configuration, but source preparation alone does not
publish a deployment. Account authorization and a successful Vercel deployment
are still required before there is a live URL.

- Use a personal Hobby account for this non-commercial classroom project.
- The frontend is served from `web/` and the two Python Functions handle
  `/api/trace` and `/api/benchmark`. No framework installation or build is needed.
- Import the complete project root, preserving `api/`, the root Python files and
  `vercel.json`. Framework preset: Other; output directory: `web`.
- Alternatively, with the official Vercel CLI installed, run `vercel --prod` in
  this folder and select the intended personal account.
- No application environment variables, API keys or database are required.
- Hosted benchmark timings measure the Vercel function's machine, not the
  visitor's device. The first request can include a Python runtime cold start
  before the separately timed algorithm samples.
