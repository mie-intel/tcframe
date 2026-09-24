from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from tcframe.runner.os_utils import run_solution

if TYPE_CHECKING:
    from tcframe.spec.base_problem import BaseProblemSpec
    from tcframe.spec.io_format import IOManipulator
    from tcframe.spec.constraint import Verifier
    from tcframe.spec.testcase import TestSuite
    from tcframe.spec.config import GradingConfig


@dataclass
class GenerationOptions:
    slug: str
    output_dir: str = 'tc'
    solution_command: str = './solution'
    seed: int = 0
    time_limit: Optional[int] = None
    memory_limit: Optional[int] = None


class Generator:
    def __init__(
        self,
        problem_spec: 'BaseProblemSpec',
        io_manipulator: 'IOManipulator',
        verifier: 'Verifier',
        test_suite: 'TestSuite',
    ):
        self._spec = problem_spec
        self._io = io_manipulator
        self._verifier = verifier
        self._suite = test_suite

    def generate(self, options: GenerationOptions) -> None:
        out_dir = Path(options.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        if options.time_limit is not None:
            print(f"  time limit   : {options.time_limit}s")
        if options.memory_limit is not None:
            print(f"  memory limit : {options.memory_limit} MB")

        ok_count = fail_count = 0

        for tc in self._suite.test_cases:
            if tc.is_sample:
                self._write_sample(tc, out_dir)
                print(f"  {tc.name}: OK")
                ok_count += 1
            else:
                if self._generate_official(tc, out_dir, options):
                    print(f"  {tc.name}: OK")
                    ok_count += 1
                else:
                    fail_count += 1

        print()
        print(f"{ok_count} test case(s) generated.", end='')
        if fail_count:
            print(f"  {fail_count} test case(s) FAILED.", end='')
        print()

    # ------------------------------------------------------------------

    def _write_sample(self, tc, out_dir: Path) -> None:
        if tc.sample_input is not None:
            (out_dir / f"{tc.name}.in").write_text(tc.sample_input)
        if tc.sample_output is not None:
            (out_dir / f"{tc.name}.out").write_text(tc.sample_output)

    def _generate_official(self, tc, out_dir: Path, options: GenerationOptions) -> bool:
        in_path = out_dir / f"{tc.name}.in"
        out_path = out_dir / f"{tc.name}.out"

        tc.apply()

        failures = self._verifier.verify(tc.subtask_ids if tc.subtask_ids else None)
        if failures:
            print(f"  {tc.name}: FAILED")
            for msg in failures:
                print(f"    * Does not satisfy: {msg}")
            return False

        with open(in_path, 'w') as f:
            self._io.write_input(f)

        ret, reason = run_solution(
            options.solution_command,
            str(in_path),
            str(out_path),
            time_limit=options.time_limit,
            memory_limit=options.memory_limit,
        )
        if ret != 0:
            print(f"  {tc.name}: FAILED ({reason})")
            return False

        return True
