import time
from collections import defaultdict, deque

# A small in-memory limiter: "at most N hits per key in the last W seconds". It is per server
# process, which is enough to stop casual scraping and spam; it is not a hard security boundary.

_hits = defaultdict(deque)


def allow(key: str, limit: int, window_seconds: int) -> bool:
    now = time.monotonic()
    hits = _hits[key]
    while hits and now - hits[0] > window_seconds:
        hits.popleft()
    if len(hits) >= limit:
        return False
    hits.append(now)
    return True


def reset() -> None:
    _hits.clear()
