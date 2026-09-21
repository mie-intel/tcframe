"""
tcframe.run() — main entry point.

Usage (at the bottom of spec.py):
    tcframe.run(ProblemSpec, TestSpec)
"""

from __future__ import annotations
import inspect
import sys
from pathlib import Path
from typing import Type

from tcframe.spec.base_problem import BaseProblemSpec
from tcframe.spec.base_test import BaseTestSpec
from tcframe.spec.random import rnd
from tcframe.runner.generator import Generator, GenerationOptions


def _slug_from_file(path: str) -> str:
    p = Path(path)
    # spec.py → use parent directory name (mirrors C++ tcframe convention)
    if p.stem == 'spec':
        parent = p.parent.name
        return parent if parent else 'problem'
    return p.stem


class _TcFrame:
    def run(
        self,
        problem_spec_cls: Type[BaseProblemSpec],
        test_spec_cls: Type[BaseTestSpec],
        *,
        seed: int = 0,
        output_dir: str = 'tc',
        solution: str = './solution',
    ) -> None:
        # Derive slug from the caller's file (the spec.py)
        caller = inspect.stack()[1]
        slug = _slug_from_file(caller.filename)

        print(f"Generating test cases for '{slug}'...")

        # Set random seed before TestCases() evaluates any rnd.nextInt() calls
        rnd.setSeed(seed)

        # Build problem spec artifacts
        problem = problem_spec_cls()
        io_manipulator = problem._build_io_format()
        _, verifier = problem._build_constraint_suite()

        # Build test suite (CASE() closures capture `problem` for variable assignment)
        test_spec = test_spec_cls()
        test_suite = test_spec._build_test_suite(slug, problem)

        options = GenerationOptions(
            slug=slug,
            output_dir=output_dir,
            solution_command=solution,
            seed=seed,
        )

        generator = Generator(problem, io_manipulator, verifier, test_suite)
        generator.generate(options)


tcframe = _TcFrame()
