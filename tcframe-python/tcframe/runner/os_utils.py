import subprocess
import sys
from typing import Optional


def _make_memory_preexec(limit_mb: int):
    """Return a preexec_fn that sets RLIMIT_AS to limit_mb MB (Linux only)."""
    try:
        import resource
        limit_bytes = limit_mb * 1024 * 1024
        def preexec():
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        return preexec
    except ImportError:
        return None


def run_solution(
    command: str,
    in_path: str,
    out_path: str,
    time_limit: Optional[int] = None,
    memory_limit: Optional[int] = None,
) -> tuple[int, str]:
    """
    Run solution with stdin from in_path, stdout to out_path.
    Returns (exit_code, verdict_suffix) where verdict_suffix is '' on success
    or a human-readable reason string on failure.
    """
    preexec_fn = None
    if memory_limit is not None and sys.platform != 'win32':
        preexec_fn = _make_memory_preexec(memory_limit)

    try:
        with open(in_path, 'r') as stdin_f, open(out_path, 'w') as stdout_f:
            result = subprocess.run(
                command,
                stdin=stdin_f,
                stdout=stdout_f,
                stderr=subprocess.PIPE,
                shell=True,
                timeout=time_limit,
                preexec_fn=preexec_fn,
            )
        if result.returncode != 0:
            return result.returncode, f"exit code {result.returncode}"
        return 0, ''
    except subprocess.TimeoutExpired:
        return -1, f"time limit exceeded ({time_limit}s)"
    except MemoryError:
        return -1, "memory limit exceeded"
    except FileNotFoundError:
        return -1, "solution not found"
    except Exception as exc:
        return -1, str(exc)
