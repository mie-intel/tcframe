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
from tcframe.spec.constraint import ConstraintSuite, Verifier, _set_suite, _set_current_subtask
from tcframe.spec.config import GradingConfig, _set_config, _get_config


class ProblemSpecMeta(type):
    """Collect type-annotated variable declarations from the class hierarchy."""

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        parent_vars: dict = {}
        for base in bases:
            parent_vars.update(getattr(base, '_tcframe_var_types', {}))
        own_annotations = {
            k: v for k, v in namespace.get('__annotations__', {}).items()
            if not k.startswith('_')
        }
        cls._tcframe_var_types = {**parent_vars, **own_annotations}
        return cls


class BaseProblemSpec(metaclass=ProblemSpecMeta):
    _tcframe_var_types = {}

    def __init__(self):
        object.__setattr__(self, '_recording', False)
        for var_name in self.__class__._tcframe_var_types:
            object.__setattr__(self, var_name, None)

    # ------------------------------------------------------------------
    # Variable interception during IO recording
    # ------------------------------------------------------------------

    def __getattribute__(self, name: str) -> Any:
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

        # Global constraints
        _set_suite(suite)
        _set_current_subtask(0)
        self.Constraints()

        # Per-subtask constraints
        for i in range(1, 26):
            method = getattr(type(self), f'Subtask{i}', None)
            if method is None:
                break
            try:
                _set_current_subtask(i)
                method(self)
            except NotImplementedError:
                break

        _set_suite(None)
        _set_current_subtask(0)
        return suite, Verifier(suite)

    def _build_grading_config(self) -> GradingConfig:
        cfg = GradingConfig()
        _set_config(cfg)
        try:
            self.GradingConfig()
        except NotImplementedError:
            pass
        _set_config(None)
        return cfg

    # ------------------------------------------------------------------
    # Override points (user implements these)
    # ------------------------------------------------------------------

    def InputFormat(self):
        raise NotImplementedError

    def OutputFormat(self):
        raise NotImplementedError

    def Constraints(self):
        pass

    def GradingConfig(self):
        pass

    def StyleConfig(self):
        pass

    # Subtask1..25 — user implements whichever they need
    def Subtask1(self): raise NotImplementedError
    def Subtask2(self): raise NotImplementedError
    def Subtask3(self): raise NotImplementedError
    def Subtask4(self): raise NotImplementedError
    def Subtask5(self): raise NotImplementedError
    def Subtask6(self): raise NotImplementedError
    def Subtask7(self): raise NotImplementedError
    def Subtask8(self): raise NotImplementedError
    def Subtask9(self): raise NotImplementedError
    def Subtask10(self): raise NotImplementedError
    def Subtask11(self): raise NotImplementedError
    def Subtask12(self): raise NotImplementedError
    def Subtask13(self): raise NotImplementedError
    def Subtask14(self): raise NotImplementedError
    def Subtask15(self): raise NotImplementedError
    def Subtask16(self): raise NotImplementedError
    def Subtask17(self): raise NotImplementedError
    def Subtask18(self): raise NotImplementedError
    def Subtask19(self): raise NotImplementedError
    def Subtask20(self): raise NotImplementedError
    def Subtask21(self): raise NotImplementedError
    def Subtask22(self): raise NotImplementedError
    def Subtask23(self): raise NotImplementedError
    def Subtask24(self): raise NotImplementedError
    def Subtask25(self): raise NotImplementedError
