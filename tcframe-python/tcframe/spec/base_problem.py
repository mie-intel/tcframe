"""
BaseProblemSpec — base class for all problem specifications.

Variable declaration via type annotations:
    class ProblemSpec(BaseProblemSpec):
        A: int
        B: int

During InputFormat()/OutputFormat(), self._recording is True, so
__getattribute__ returns VarRef objects for declared variables, allowing
LINE(self.A, self.B) to capture live references rather than snapshot values.
"""

from __future__ import annotations
from typing import Any

from tcframe.spec.io_format import (
    IOFormatBuilder, IOManipulator, VarRef,
    _set_builder, _get_builder,
)
from tcframe.spec.constraint import ConstraintSuite, Verifier, _set_suite


class ProblemSpecMeta(type):
    """Collect type-annotated variable declarations from the class hierarchy."""

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        parent_vars: dict = {}
        for base in bases:
            parent_vars.update(getattr(base, '_tcframe_var_types', {}))
        # Exclude private/dunder names — only user-declared variables allowed
        own_annotations = {
            k: v for k, v in namespace.get('__annotations__', {}).items()
            if not k.startswith('_')
        }
        cls._tcframe_var_types = {**parent_vars, **own_annotations}
        return cls


class BaseProblemSpec(metaclass=ProblemSpecMeta):
    _tcframe_var_types = {}  # populated by ProblemSpecMeta; no annotation to avoid self-inclusion

    def __init__(self):
        object.__setattr__(self, '_recording', False)
        # Initialise declared variables to None
        for var_name in self.__class__._tcframe_var_types:
            object.__setattr__(self, var_name, None)

    # ------------------------------------------------------------------
    # Variable interception during IO recording
    # ------------------------------------------------------------------

    def __getattribute__(self, name: str) -> Any:
        # Always bypass override for private / dunder attributes and methods
        if name.startswith('_'):
            return object.__getattribute__(self, name)

        recording = object.__getattribute__(self, '_recording')
        if recording:
            var_types = object.__getattribute__(self, '_tcframe_var_types')
            if name in var_types:
                return VarRef(self, name, var_types[name])

        return object.__getattribute__(self, name)

    # ------------------------------------------------------------------
    # Build helpers called by core.py
    # ------------------------------------------------------------------

    def _build_io_format(self) -> IOManipulator:
        builder = IOFormatBuilder()
        _set_builder(builder)
        object.__setattr__(self, '_recording', True)

        builder.start_input()
        self.InputFormat()

        builder.start_output()
        try:
            self.OutputFormat()
        except NotImplementedError:
            pass

        object.__setattr__(self, '_recording', False)
        _set_builder(None)
        return IOManipulator(builder.build())

    def _build_constraint_suite(self) -> tuple[ConstraintSuite, Verifier]:
        suite = ConstraintSuite()
        _set_suite(suite)
        self.Constraints()
        _set_suite(None)
        return suite, Verifier(suite)

    # ------------------------------------------------------------------
    # Override points (user implements these)
    # ------------------------------------------------------------------

    def InputFormat(self):
        raise NotImplementedError

    def OutputFormat(self):
        raise NotImplementedError

    def Constraints(self):
        pass  # optional

    def GradingConfig(self):
        pass

    def StyleConfig(self):
        pass
