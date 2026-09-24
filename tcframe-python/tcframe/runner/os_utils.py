import subprocess
import sys
from typing import Optional

# Signals that typically indicate memory exhaustion under RLIMIT_AS
_MLE_SIGNALS = frozenset((6, 7, 11))           # SIGABRT, SIGBUS, SIGSEGV
# Shell-wrapped signal exit codes (128 + signal) for the same signals
_MLE_SHELL_EXIT_CODES = frozenset((134, 135, 139))


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
    Returns (exit_code, verdict_hint) where verdict_hint is '' on success
    or a human-readable reason on failure ('time limit exceeded', 'memory
    limit exceeded', 'exit code N', etc.).
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

        rc = result.returncode
        if rc == 0:
            return 0, ''
        # Negative: killed directly by signal (no shell wrapper)
        if rc < 0:
            sig = -rc
            if sig in _MLE_SIGNALS:
                return rc, 'memory limit exceeded'
            return rc, f'killed by signal {sig}'
        # Positive 128+N: shell-wrapped signal exit code
        if memory_limit is not None and rc in _MLE_SHELL_EXIT_CODES:
            return rc, 'memory limit exceeded'
        return rc, f'exit code {rc}'

    except subprocess.TimeoutExpired:
        return -1, f'time limit exceeded ({time_limit}s)'
    except MemoryError:
        return -1, 'memory limit exceeded'
    except FileNotFoundError:
        return -1, 'solution not found'
    except Exception as exc:
        return -1, str(exc)
