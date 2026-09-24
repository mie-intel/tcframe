import threading
from dataclasses import dataclass, field
from typing import Optional

_grading_ctx = threading.local()
_style_ctx = threading.local()
_multi_ctx = threading.local()

DEFAULT_TIME_LIMIT = 2    # seconds
DEFAULT_MEMORY_LIMIT = 64  # MB


# ---------------------------------------------------------------------------
# GradingConfig
# ---------------------------------------------------------------------------

@dataclass
class GradingConfig:
    time_limit: int = DEFAULT_TIME_LIMIT
    memory_limit: int = DEFAULT_MEMORY_LIMIT


def _set_grading_config(cfg: Optional[GradingConfig]) -> None:
    _grading_ctx.config = cfg


def _get_grading_config() -> Optional[GradingConfig]:
    return getattr(_grading_ctx, 'config', None)


# keep old name for back-compat with base_problem.py
_set_config = _set_grading_config
_get_config = _get_grading_config


def TimeLimit(seconds: int) -> None:
    cfg = _get_grading_config()
    if cfg is None:
        raise RuntimeError("TimeLimit() must be called inside GradingConfig()")
    cfg.time_limit = seconds


def MemoryLimit(mb: int) -> None:
    cfg = _get_grading_config()
    if cfg is None:
        raise RuntimeError("MemoryLimit() must be called inside GradingConfig()")
    cfg.memory_limit = mb


# ---------------------------------------------------------------------------
# StyleConfig
# ---------------------------------------------------------------------------

@dataclass
class StyleConfig:
    evaluator: str = 'batch'          # 'batch' or 'interactive'
    has_output: bool = True           # False → NoOutput(), skip solution run in generate
    scorer_command: Optional[str] = None  # None → use diff; path → custom scorer binary


def _set_style_config(cfg: Optional[StyleConfig]) -> None:
    _style_ctx.config = cfg


def _get_style_config() -> Optional[StyleConfig]:
    return getattr(_style_ctx, 'config', None)


def BatchEvaluator() -> None:
    cfg = _get_style_config()
    if cfg is not None:
        cfg.evaluator = 'batch'


def InteractiveEvaluator() -> None:
    cfg = _get_style_config()
    if cfg is not None:
        cfg.evaluator = 'interactive'


def CustomScorer(path: str = './scorer') -> None:
    cfg = _get_style_config()
    if cfg is not None:
        cfg.scorer_command = path


def NoOutput() -> None:
    cfg = _get_style_config()
    if cfg is not None:
        cfg.has_output = False


# ---------------------------------------------------------------------------
# MultipleTestCasesConfig
# ---------------------------------------------------------------------------

@dataclass
class MultipleTestCasesConfig:
    counter_var: Optional[str] = None   # variable name that holds the TC count
    output_prefix: Optional[str] = None  # e.g. "Case #%d: "


def _set_multi_config(cfg: Optional[MultipleTestCasesConfig]) -> None:
    _multi_ctx.config = cfg


def _get_multi_config() -> Optional[MultipleTestCasesConfig]:
    return getattr(_multi_ctx, 'config', None)


def Counter(var) -> None:
    """Declare which variable holds the test-case count.

    Call inside MultipleTestCasesConfig() as Counter(self.X).
    `var` is a VarRef (recording mode enabled by build helper) or a string.
    """
    cfg = _get_multi_config()
    if cfg is None:
        return
    if hasattr(var, '_name'):
        cfg.counter_var = var._name
    elif isinstance(var, str):
        cfg.counter_var = var


def OutputPrefix(prefix: str) -> None:
    """Set the per-TC output prefix, e.g. 'Case #%d: '."""
    cfg = _get_multi_config()
    if cfg is not None:
        cfg.output_prefix = prefix
