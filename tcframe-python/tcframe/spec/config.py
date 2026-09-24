import threading
from dataclasses import dataclass
from typing import Optional

_ctx = threading.local()

DEFAULT_TIME_LIMIT = 2    # seconds
DEFAULT_MEMORY_LIMIT = 64  # MB


@dataclass
class GradingConfig:
    time_limit: int = DEFAULT_TIME_LIMIT
    memory_limit: int = DEFAULT_MEMORY_LIMIT


def _set_config(cfg: Optional['GradingConfig']) -> None:
    _ctx.config = cfg


def _get_config() -> Optional['GradingConfig']:
    return getattr(_ctx, 'config', None)


def TimeLimit(seconds: int) -> None:
    cfg = _get_config()
    if cfg is None:
        raise RuntimeError("TimeLimit() must be called inside GradingConfig()")
    cfg.time_limit = seconds


def MemoryLimit(mb: int) -> None:
    cfg = _get_config()
    if cfg is None:
        raise RuntimeError("MemoryLimit() must be called inside GradingConfig()")
    cfg.memory_limit = mb
