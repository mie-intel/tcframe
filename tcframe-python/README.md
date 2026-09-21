# tcframe-python

Python abstraction layer for [tcframe](https://tcframe.toki.id) — a test case generation framework for competitive programming problems.

## What is this?

`tcframe-python` lets you write tcframe test case specs in **Python** instead of C++. It is designed for problem setters who are not fluent in C++ but still want to use the structured test generation workflow that tcframe provides.

Your spec runs entirely in Python (no compilation step), while the solution binary you provide still runs as a native executable.

**Key advantages over writing C++ specs:**
- Native big integers — `10**1000` just works, no overflow concerns
- Full Python standard library available for test case generation
- Cross-platform: Windows, Linux, macOS
- Simple install: `pip install tcframe`

## Install

```bash
pip install tcframe
# or
uv add tcframe
```

Requires Python ≥ 3.10.

## Quick start

Create a `spec.py` next to your compiled solution:

```python
from tcframe import *

class ProblemSpec(BaseProblemSpec):
    A: int
    B: int
    result: int

    def InputFormat(self):
        LINE(self.A, self.B)

    def OutputFormat(self):
        LINE(self.result)

    def Constraints(self):
        CONS(lambda: 1 <= self.A <= 1000)
        CONS(lambda: 1 <= self.B <= 1000)

class TestSpec(BaseTestSpec):
    def SampleTestCase1(self):
        self.Input(["2 8"])
        self.Output(["10"])

    def TestCases(self):
        CASE(A=1, B=1)
        CASE(A=1000, B=1000)
        CASE(A=rnd.nextInt(1, 1000), B=rnd.nextInt(1, 1000))
        # Python big ints work natively:
        CASE(A=10**500, B=10**500)

tcframe.run(ProblemSpec, TestSpec)
```

Run it:

```bash
python spec.py
```

This generates `tc/` containing `.in` and `.out` files (`.out` files are produced by running `./solution`).

## API overview

| Symbol | Purpose |
|--------|---------|
| `BaseProblemSpec` | Base class — declare variables as type annotations, implement `InputFormat`, `OutputFormat`, `Constraints` |
| `BaseTestSpec` | Base class — implement `SampleTestCaseN`, `TestCases` (or `TestGroupN`) |
| `LINE(a, b, ...)` | Write space-separated values on one line |
| `LINES(vec) % SIZE(n)` | Write one value per line |
| `GRID(mat) % SIZE(r, c)` | Write a 2-D matrix, space-separated rows |
| `EMPTY_LINE()` | Write a blank line |
| `CONS(lambda: expr)` | Declare a constraint — checked for each test case |
| `CASE(A=1, B=2)` | Declare a test case by assigning variable values |
| `rnd.nextInt(lo, hi)` | Random integer in [lo, hi] (inclusive) |
| `rnd.nextDouble(lo, hi)` | Random float in [lo, hi] |
| `tcframe.run(ProblemSpec, TestSpec)` | Entry point — call at the bottom of `spec.py` |

## Options

```python
tcframe.run(
    ProblemSpec,
    TestSpec,
    seed=42,               # random seed (default 0)
    output_dir='tc',       # output directory (default 'tc')
    solution='./solution', # solution command (default './solution')
)
```

## Full design

See [`DESIGN.md`](../DESIGN.md) at the repo root for the full architecture and design decisions.
