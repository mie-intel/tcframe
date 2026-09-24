"""
tcframe.run() — main entry point.

Usage (at the bottom of spec.py):
    tcframe.run(ProblemSpec, TestSpec)

CLI:
    python spec.py [grade] [--solution ./sol] [--output tc] [--seed N]
                   [--time-limit S] [--no-time-limit]
                   [--memory-limit MB] [--no-memory-limit]
                   [--brief] [--scorer ./scorer]
"""

from __future__ import annotations
import inspect
import sys
from pathlib import Path
from typing import Type

from tcframe.spec.base_problem import BaseProblemSpec
from tcframe.spec.base_test import BaseTestSpec
from tcframe.spec.random import rnd
from tcframe.runner.args import parse_args
from tcframe.runner.generator import Generator, GenerationOptions
from tcframe.runner.grader import Grader, GradingOptions


def _slug_from_file(path: str) -> str:
    p = Path(path)
    if p.stem == 'spec':
        parent = p.parent.name
        return parent if parent else 'problem'
    return p.stem


class _TcFrame:
    def run(
        self,
        problem_spec_cls: Type[BaseProblemSpec],
        test_spec_cls: Type[BaseTestSpec],
    ) -> None:
        caller = inspect.stack()[1]
        slug = _slug_from_file(caller.filename)

        args = parse_args()

        rnd.setSeed(args.seed)

        # Build spec artifacts
        problem = problem_spec_cls()
        io_manipulator = problem._build_io_format()
        constraint_suite, verifier = problem._build_constraint_suite()
        grading_cfg = problem._build_grading_config()

        test_spec = test_spec_cls()
        test_suite = test_spec._build_test_suite(slug, problem)

        # Resolve effective time/memory limits:
        # CLI flag overrides spec; --no-X disables the limit entirely
        def _resolve_limit(cli_val, no_flag, spec_val):
            if no_flag:
                return None
            if cli_val is not None:
                return cli_val
            return spec_val

        time_limit = _resolve_limit(args.time_limit, args.no_time_limit, grading_cfg.time_limit)
        memory_limit = _resolve_limit(args.memory_limit, args.no_memory_limit, grading_cfg.memory_limit)

        if args.command == 'generate':
            print(f"Generating test cases for '{slug}'...")
            options = GenerationOptions(
                slug=slug,
                output_dir=args.output_dir,
                solution_command=args.solution,
                seed=args.seed,
                time_limit=time_limit,
                memory_limit=memory_limit,
            )
            generator = Generator(problem, io_manipulator, verifier, test_suite)
            generator.generate(options)

        else:  # grade
            subtask_points = constraint_suite.subtask_points()
            options = GradingOptions(
                slug=slug,
                output_dir=args.output_dir,
                solution_command=args.solution,
                time_limit=time_limit,
                memory_limit=memory_limit,
                subtask_points=subtask_points,
                brief=args.brief,
            )
            grader = Grader(test_suite)
            grader.grade(options)


tcframe = _TcFrame()
