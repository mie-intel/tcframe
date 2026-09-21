"""
IO format: segments (LINE, LINES, GRID, EMPTY_LINE), VarRef, IOManipulator.

During InputFormat()/OutputFormat() recording, BaseProblemSpec.__getattribute__
returns VarRef objects instead of actual values.  The module-level LINE/LINES/GRID/
EMPTY_LINE functions register segments into the active IOFormatBuilder via a
thread-local context.  At generation time, IOManipulator writes the current
variable values to a stream.
"""

import threading
from typing import Any, List, Optional

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
# IO segments
# ---------------------------------------------------------------------------

def _val(ref: Any) -> Any:
    """Unwrap VarRef to its current value; pass through plain values."""
    return ref.get() if isinstance(ref, VarRef) else ref


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


class EmptyLineSegment:
    def write(self, stream) -> None:
        stream.write('\n')


# ---------------------------------------------------------------------------
# Builder & format
# ---------------------------------------------------------------------------

class IOFormat:
    def __init__(self, input_segments: list, output_segments: list):
        self.input_segments = input_segments
        self.output_segments = output_segments


class IOFormatBuilder:
    def __init__(self):
        self._input: list = []
        self._output: list = []
        self._active: Optional[list] = None

    def start_input(self) -> None:
        self._active = self._input

    def start_output(self) -> None:
        self._active = self._output

    def add(self, seg: Any) -> None:
        if self._active is not None:
            self._active.append(seg)

    def build(self) -> IOFormat:
        return IOFormat(self._input, self._output)


class IOManipulator:
    def __init__(self, io_format: IOFormat):
        self._fmt = io_format

    def write_input(self, stream) -> None:
        for seg in self._fmt.input_segments:
            seg.write(stream)

    def write_output(self, stream) -> None:
        for seg in self._fmt.output_segments:
            seg.write(stream)


# ---------------------------------------------------------------------------
# Thread-local context helpers
# ---------------------------------------------------------------------------

def _get_builder() -> Optional[IOFormatBuilder]:
    return getattr(_ctx, 'builder', None)


def _set_builder(builder: Optional[IOFormatBuilder]) -> None:
    _ctx.builder = builder


# ---------------------------------------------------------------------------
# Public DSL functions (used inside InputFormat / OutputFormat)
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
