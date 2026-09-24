import random as _random


class Random:
    def __init__(self):
        self._rng = _random.Random(0)

    def setSeed(self, seed: int) -> None:
        self._rng.seed(seed)

    def nextInt(self, lo_or_max: int, hi: int = None) -> int:
        """nextInt(lo, hi) → [lo, hi]; nextInt(maxEx) → [0, maxEx-1]."""
        if hi is None:
            return self._rng.randint(0, lo_or_max - 1)
        return self._rng.randint(lo_or_max, hi)

    def nextLongLong(self, lo_or_max: int, hi: int = None) -> int:
        """nextLongLong(lo, hi) → [lo, hi]; nextLongLong(maxEx) → [0, maxEx-1]."""
        if hi is None:
            return self._rng.randint(0, lo_or_max - 1)
        return self._rng.randint(lo_or_max, hi)

    def nextDouble(self, lo_or_max: float, hi: float = None) -> float:
        """nextDouble(lo, hi) → [lo, hi]; nextDouble(max) → [0, max]."""
        if hi is None:
            return self._rng.uniform(0.0, lo_or_max)
        return self._rng.uniform(lo_or_max, hi)

    def shuffle(self, lst: list) -> None:
        """Shuffle list in-place using the seeded RNG."""
        self._rng.shuffle(lst)


rnd = Random()
