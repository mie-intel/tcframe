# Python TCFrame MVP — Design Spec

**Date:** 2026-09-21  
**Status:** Draft

---

## Goal

Python abstraction layer for tcframe so users not fluent in C++ can write test case specs in Python. Generated `.in`/`.out` files remain compatible with the existing C++ tcframe ecosystem.

Key properties:
- Cross-platform (Windows, Linux, macOS)
- Easy to install: `pip install tcframe` or `uv add tcframe`
- Easy to run: `python spec.py`
- API mirrors C++ tcframe so existing docs stay relevant
- Python advantages: big integers (`10**1000` just works), rich stdlib, easy syntax

---

## MVP Scope

**In:**
- Input/output formatting: `LINE`, `LINES`, `GRID`, `EMPTY_LINE`
- Constraint declaration: `CONS()`
- Test case declaration: `CASE()`, `SampleTestCaseN()`, `TestCases()`
- Running `./solution` to produce `.out` files (cross-platform subprocess)
- Writing generated files to `tc/` directory
- Basic constraint violation reporting

**Out:**
- Local grading with time/memory limits
- Subtasks
- Interactive problems
- Custom scorer
- `RAW_LINE`, `RAW_LINES`
- Multiple test cases per file

---

## Usage

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
        CASE(A=rnd.nextInt(1, 1000), B=rnd.nextInt(1, 1000))
        CASE(A=10**500, B=10**500)  # Python big int, no C++ equivalent needed

tcframe.run(ProblemSpec, TestSpec)
```

Run with:
```bash
python spec.py
# or
uv run spec.py
```

Output in `tc/`:
```
tc/
  spec_sample_1.in   spec_sample_1.out
  spec_1.in          spec_1.out
  spec_2.in          spec_2.out
  spec_3.in          spec_3.out
```

---

## Architecture

### Execution flow

```
python spec.py
  └─ tcframe.run(ProblemSpec, TestSpec)
       ├─ SlugParser: derive slug from spec.py filename
       ├─ build IO format from InputFormat() / OutputFormat() calls
       ├─ build constraint suite from Constraints() calls
       ├─ build test suite from SampleTestCaseN() / TestCases() calls
       └─ Generator:
            for each test case:
              1. call CASE() closure to assign variable values
              2. verify CONS() lambdas → report failure + skip if violated
              3. write .in file using IO format
              4. run ./solution < .in > .out (subprocess)
```

### Variable declaration

Class-level type annotations on `BaseProblemSpec` define the variables.
A metaclass reads annotations at class definition time and creates instance attributes.

Supported types for MVP: `int`, `float`, `str`, `list[int]`, `list[float]`, `list[str]`, `list[list[int]]`.

### IO format (LINE, LINES, GRID)

`InputFormat()` / `OutputFormat()` are called during setup with a recording context active.
`LINE(self.A, self.B)` does NOT write anything immediately — it registers an `IOSegment` holding references to the spec's variables.

At generation time, `IOManipulator` walks the segment list and writes values to the output stream.

| Macro | Writes |
|-------|--------|
| `LINE(a, b, ...)` | space-separated values, one line |
| `LINES(vec) % SIZE(N)` | one value per line, N lines |
| `GRID(mat) % SIZE(R, C)` | space-separated rows |
| `EMPTY_LINE()` | blank line |

`SIZE(N)` attaches a size callable to `LINES`/`GRID` via Python `%` operator overloading (mirrors C++ tcframe).

### CONS() — constraints

MVP uses explicit lambda for reliability:
```python
CONS(lambda: 1 <= self.A <= 1000)
```
`CONS` records the lambda. At verification time (after variable assignment), each lambda is called. If it returns `False`, the test case is marked failed. Error message is extracted from the lambda source via `inspect.getsource`.

### CASE() — test cases

`CASE()` takes keyword arguments mapping variable names to values:
```python
CASE(A=1, B=2)
CASE(A=rnd.nextInt(1, 1000), B=rnd.nextInt(1, 1000))
```
Each call registers a closure that assigns `self.A = 1; self.B = 2` on the spec instance when invoked.

### rnd — random helper

Module-level `Random` instance:
- `rnd.nextInt(lo, hi)` → `random.randint(lo, hi)` (inclusive, works with Python big ints)
- `rnd.nextDouble(lo, hi)` → `random.uniform(lo, hi)`
- `rnd.setSeed(seed)`

### Cross-platform solution execution

```python
subprocess.run(
    solution_command,
    stdin=open(in_path),
    stdout=open(out_path, "w"),
    shell=True,
)
```

No `ulimit`. MVP does not enforce time/memory limits. Works on Windows, Linux, macOS.

---

## Package structure (monorepo)

```
tcframe-python/              # sits alongside include/, src/, test/, web/
  pyproject.toml
  tcframe/
    __init__.py              # exports: BaseProblemSpec, BaseTestSpec, tcframe, rnd,
                             #          CONS, CASE, LINE, LINES, GRID, EMPTY_LINE, SIZE
    spec/
      base_problem.py        # BaseProblemSpec + variable metaclass
      base_test.py           # BaseTestSpec, SampleTestCaseN, TestCases
      io_format.py           # IOFormat, LineSegment, LinesSegment, GridSegment, IOManipulator
      constraint.py          # ConstraintSuite, Constraint, Verifier
      testcase.py            # TestSuite, TestCase
      random.py              # Random (rnd)
    runner/
      generator.py           # Generator, GenerationOptions
      os_utils.py            # run_solution() cross-platform
    core.py                  # tcframe.run(), SlugParser
```

Zero runtime dependencies. Pure Python ≥ 3.10.

---

## Installation

```toml
# pyproject.toml
[project]
name = "tcframe"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []
```

```bash
pip install tcframe
uv add tcframe
```
