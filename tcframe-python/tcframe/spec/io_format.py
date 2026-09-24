"""
IO format: segments (LINE, LINES, GRID, RAW_LINE, RAW_LINES, EMPTY_LINE),
VarRef, IOManipulator.

During InputFormat()/OutputFormat() recording, BaseProblemSpec.__getattribute__
returns VarRef objects instead of actual values.  The module-level DSL functions
register segments into the active IOFormatBuilder via a thread-local context.
At generation time, IOManipulator writes the current variable values to a stream.
"""

import threading
from typing import Any, List, Optional, Tuple

_ctx = threading.local()


# ---------------------------------------------------------------------------
# Variable reference (live pointer into a spec instance attribute)
# ---------------------------------------------------------------------------

class VarRef:
    """Live reference to a named attribute on a spec instance."""

    def __init__(self, spec: Any, name: str, var_type: type):
        self._spec = spec
        self._name = name
        self._type = var_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def var_type(self) -> type:
        return self._type

    def get(self) -> Any:
        return object.__getattribute__(self._spec, self._name)

    def set(self, value: Any) -> None:
        object.__setattr__(self._spec, self._name, value)

    def __mod__(self, size_expr: 'SizeExpr') -> 'VectorWithSize':
        return VectorWithSize(self, size_expr)


# ---------------------------------------------------------------------------
# SIZE helpers
# ---------------------------------------------------------------------------

class SizeExpr:
    def __init__(self, ref_or_value: Any):
        self._v = ref_or_value

    def evaluate(self) -> int:
        if isinstance(self._v, VarRef):
            return int(self._v.get())
        if callable(self._v):
            return int(self._v())
        return int(self._v)


class MatrixSize:
    def __init__(self, rows: SizeExpr, cols: SizeExpr):
        self.rows = rows
        self.cols = cols


class VectorWithSize:
    def __init__(self, var_ref: VarRef, size: SizeExpr):
        self.var_ref = var_ref
        self.size = size


def SIZE(*args) -> 'SizeExpr | MatrixSize':
    if len(args) == 1:
        a = args[0]
        return SizeExpr(a)
    if len(args) == 2:
        return MatrixSize(SizeExpr(args[0]), SizeExpr(args[1]))
    raise ValueError("SIZE takes 1 or 2 arguments")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _val(ref: Any) -> Any:
    """Unwrap VarRef to its current value; pass through plain values."""
    return ref.get() if isinstance(ref, VarRef) else ref


def _count_scalar_tokens(var_refs: list) -> int:
    """Count expected number of space-separated tokens for a set of var_refs."""
    n = 0
    for ref in var_refs:
        v = _val(ref)
        if isinstance(v, list):
            n += len(v)
        else:
            n += 1
    return n


# ---------------------------------------------------------------------------
# IO segments
# ---------------------------------------------------------------------------

class LineSegment:
    """LINE(a, b, ...) — space-separated on one line."""

    def __init__(self, var_refs: list):
        self.var_refs = var_refs

    def write(self, stream) -> None:
        tokens: List[str] = []
        for ref in self.var_refs:
            v = _val(ref)
            if isinstance(v, list):
                tokens.extend(str(x) for x in v)
            else:
                tokens.append(str(v))
        stream.write(' '.join(tokens) + '\n')

    def _verify(self, lines: List[str], pos: int) -> Tuple[bool, str, int]:
        if pos >= len(lines):
            return False, f'expected a line at position {pos + 1}', 0
        expected = _count_scalar_tokens(self.var_refs)
        tokens = lines[pos].split()
        if len(tokens) != expected:
            return False, (
                f'line {pos + 1}: expected {expected} token(s), got {len(tokens)}'
            ), 1
        return True, '', 1


class LinesSegment:
    """LINES(vec, ...) % SIZE(n) — one row per line."""

    def __init__(self, var_refs: list):
        self.var_refs = var_refs
        self.size: Optional[SizeExpr] = None

    def __mod__(self, size_expr) -> 'LinesSegment':
        if isinstance(size_expr, SizeExpr):
            self.size = size_expr
        return self

    def write(self, stream) -> None:
        if len(self.var_refs) == 1:
            v = _val(self.var_refs[0])
            n = self.size.evaluate() if self.size else len(v)
            for i in range(n):
                stream.write(str(v[i]) + '\n')
        else:
            vals = [_val(r) for r in self.var_refs]
            n = self.size.evaluate() if self.size else len(vals[0])
            for i in range(n):
                stream.write(' '.join(str(v[i]) for v in vals) + '\n')

    def _verify(self, lines: List[str], pos: int) -> Tuple[bool, str, int]:
        try:
            n = self.size.evaluate() if self.size else len(_val(self.var_refs[0]))
        except Exception:
            n = 0
        if pos + n > len(lines):
            return False, f'expected {n} line(s) from position {pos + 1}', 0
        return True, '', n


class GridSegment:
    """GRID(mat) % SIZE(r, c) — 2-D matrix, space-separated rows."""

    def __init__(self, var_refs: list):
        self.var_refs = var_refs
        self.size: Optional[MatrixSize] = None

    def __mod__(self, size_expr) -> 'GridSegment':
        if isinstance(size_expr, MatrixSize):
            self.size = size_expr
        return self

    def write(self, stream) -> None:
        mat = _val(self.var_refs[0])
        r = self.size.rows.evaluate() if self.size else len(mat)
        c = self.size.cols.evaluate() if self.size else (len(mat[0]) if mat else 0)
        for i in range(r):
            stream.write(' '.join(str(mat[i][j]) for j in range(c)) + '\n')

    def _verify(self, lines: List[str], pos: int) -> Tuple[bool, str, int]:
        try:
            if self.size:
                r = self.size.rows.evaluate()
                c = self.size.cols.evaluate()
            else:
                mat = _val(self.var_refs[0])
                r, c = len(mat), (len(mat[0]) if mat else 0)
        except Exception:
            return True, '', 0
        if pos + r > len(lines):
            return False, f'expected {r} grid line(s) from position {pos + 1}', 0
        for i in range(r):
            tokens = lines[pos + i].split()
            if len(tokens) != c:
                return False, (
                    f'line {pos + i + 1}: expected {c} token(s), got {len(tokens)}'
                ), r
        return True, '', r


class EmptyLineSegment:
    def write(self, stream) -> None:
        stream.write('\n')

    def _verify(self, lines: List[str], pos: int) -> Tuple[bool, str, int]:
        if pos >= len(lines):
            return False, f'expected blank line at position {pos + 1}', 0
        if lines[pos].strip():
            return False, f'line {pos + 1} should be blank, got: {lines[pos]!r}', 1
        return True, '', 1


class RawLineSegment:
    """RAW_LINE(s) — write str variable as-is with trailing newline."""

    def __init__(self, var_ref):
        self.var_ref = var_ref

    def write(self, stream) -> None:
        s = str(_val(self.var_ref))
        stream.write(s if s.endswith('\n') else s + '\n')

    def _verify(self, lines: List[str], pos: int) -> Tuple[bool, str, int]:
        if pos >= len(lines):
            return False, f'expected a raw line at position {pos + 1}', 0
        return True, '', 1


class RawLinesSegment:
    """RAW_LINES(vs) % SIZE(n) — write each string element as a line."""

    def __init__(self, var_ref):
        self.var_ref = var_ref
        self.size: Optional[SizeExpr] = None

    def __mod__(self, size_expr) -> 'RawLinesSegment':
        if isinstance(size_expr, SizeExpr):
            self.size = size_expr
        return self

    def write(self, stream) -> None:
        v = _val(self.var_ref)
        n = self.size.evaluate() if self.size else len(v)
        for i in range(n):
            s = str(v[i])
            stream.write(s if s.endswith('\n') else s + '\n')

    def _verify(self, lines: List[str], pos: int) -> Tuple[bool, str, int]:
        try:
            v = _val(self.var_ref)
            n = self.size.evaluate() if self.size else (len(v) if isinstance(v, list) else 0)
        except Exception:
            n = 0
        if pos + n > len(lines):
            return False, f'expected {n} raw line(s) from position {pos + 1}', 0
        return True, '', n


# ---------------------------------------------------------------------------
# Builder & format
# ---------------------------------------------------------------------------

class IOFormat:
    def __init__(
        self,
        input_segments: list,
        output_segments: list,
        output_variants: Optional[List[list]] = None,
    ):
        self.input_segments = input_segments
        self.output_segments = output_segments
        self.output_variants: List[list] = output_variants or []


class IOFormatBuilder:
    def __init__(self):
        self._input: list = []
        self._output: list = []
        self._output_variants: List[list] = []
        self._active: Optional[list] = None

    def start_input(self) -> None:
        self._active = self._input

    def start_output(self) -> None:
        self._active = self._output

    def start_output_variant(self, n: int) -> None:
        """Switch active list to OutputFormatN() variant (n = 1..5)."""
        while len(self._output_variants) < n:
            self._output_variants.append([])
        self._active = self._output_variants[n - 1]

    def add(self, seg: Any) -> None:
        if self._active is not None:
            self._active.append(seg)

    def build(self) -> IOFormat:
        return IOFormat(self._input, self._output, list(self._output_variants))


class IOManipulator:
    def __init__(self, io_format: IOFormat):
        self._fmt = io_format

    def write_input(self, stream) -> None:
        for seg in self._fmt.input_segments:
            seg.write(stream)

    def write_output(self, stream) -> None:
        for seg in self._fmt.output_segments:
            seg.write(stream)

    def verify_output(self, filepath: str) -> Tuple[bool, str]:
        """
        Structural format check: try primary output format, then each variant.
        Returns (ok, error_message). Called after solution runs in generator mode.
        """
        all_variants = [self._fmt.output_segments] + self._fmt.output_variants
        active = [v for v in all_variants if v]
        if not active:
            return True, ''  # no output format declared — skip check

        primary_err = ''
        for i, segments in enumerate(active):
            ok, msg = self._try_verify(filepath, segments)
            if ok:
                return True, ''
            if i == 0:
                primary_err = msg  # report primary format's error when all fail
        return False, primary_err

    def _try_verify(self, filepath: str, segments: list) -> Tuple[bool, str]:
        try:
            with open(filepath) as f:
                raw = f.readlines()
            lines = [l.rstrip('\n') for l in raw]
            while lines and not lines[-1].strip():
                lines.pop()
            pos = 0
            for seg in segments:
                ok, msg, consumed = seg._verify(lines, pos)
                if not ok:
                    return False, msg
                pos += consumed
            if pos < len(lines):
                extra = len(lines) - pos
                return False, f'{extra} unexpected extra line(s) after format'
            return True, ''
        except FileNotFoundError:
            return False, 'output file not found'
        except Exception as e:
            return False, str(e)


# ---------------------------------------------------------------------------
# Thread-local context helpers
# ---------------------------------------------------------------------------

def _get_builder() -> Optional[IOFormatBuilder]:
    return getattr(_ctx, 'builder', None)


def _set_builder(builder: Optional[IOFormatBuilder]) -> None:
    _ctx.builder = builder


# ---------------------------------------------------------------------------
# Public DSL functions (used inside InputFormat / OutputFormat / OutputFormatN)
# ---------------------------------------------------------------------------

def _require_builder(fn_name: str) -> IOFormatBuilder:
    b = _get_builder()
    if b is None:
        raise RuntimeError(f"{fn_name}() must be called inside InputFormat() or OutputFormat()")
    return b


def LINE(*args) -> LineSegment:
    b = _require_builder('LINE')
    seg = LineSegment(list(args))
    b.add(seg)
    return seg


def LINES(*args) -> LinesSegment:
    b = _require_builder('LINES')
    seg = LinesSegment(list(args))
    b.add(seg)
    return seg


def GRID(*args) -> GridSegment:
    b = _require_builder('GRID')
    seg = GridSegment(list(args))
    b.add(seg)
    return seg


def EMPTY_LINE() -> EmptyLineSegment:
    b = _require_builder('EMPTY_LINE')
    seg = EmptyLineSegment()
    b.add(seg)
    return seg


def RAW_LINE(var) -> RawLineSegment:
    """RAW_LINE(self.S) — write string variable as-is (no token splitting)."""
    b = _require_builder('RAW_LINE')
    seg = RawLineSegment(var)
    b.add(seg)
    return seg


def RAW_LINES(var) -> RawLinesSegment:
    """RAW_LINES(self.lines) % SIZE(n) — write each string in a list as a line."""
    b = _require_builder('RAW_LINES')
    seg = RawLinesSegment(var)
    b.add(seg)
    return seg
